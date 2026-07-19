"""dialogue.py — THE dialogue-turn service: the CLI harness's single instrumented seam.

Both callers (the interactive REPL and the synthetic load driver, via the
shared session-runner) sit on this module; neither duplicates the timing or
token accounting recorded here (CLAUDE.md: instrument at the seam; spec:
docs\\cli-harness.md, build rulings 2026-07-15). There is no HTTP route in
this build — the dialogue-turn route rides with the Unity client surface.

Pipeline per turn (the vertical slice's last leg):
  resolve agent + vocabulary -> retrieval (retrieve_dialogue_init, built) ->
  prompt assembly (seed identity + frozen reputation snapshot + retrieved
  memories + output contract) -> single Sonnet-class call -> validate the
  directive against the vocabulary -> apply the reputation delta IN PLACE
  (atomic clamped UPDATE of the agents.reputation runtime scalar — outside
  the memory-content non-destructive invariant, same class as set_pinned) ->
  DialogueTurnResult.

Scene state lives in the caller: the frozen `reputation_snapshot` arrives on
every request and is refreshed by the caller only at a scene boundary, so
"snapshot frozen within a scene" is a property of the seam contract.

Degradation ladder (never-blank-a-dialogue, the behavior analog of
never-lose-a-write and the read path's fail-quiet):
  - dialogue call fails          -> fallback line, no directive, zeroed delta,
                                    degraded = true + reason; the turn returns.
  - structured output malformed  -> prose salvaged when present (the provider
    parses field-wise); an unsalvageable response serves the fallback line;
    token spend is accounted either way.
  - unknown / unparseable action directive -> logged, dropped
    (`directive_dropped` + reason), the turn succeeds.
  - retrieval degraded           -> inherited: the turn proceeds on the
    degraded candidate set; the retrieval flag rides in the nested
    instrumentation.
  - delta would exceed the scale -> clamped in SQL; never throws.

A client `reputation_delta_override` wins over the model's delta (§9) — it is
client-authoritative, so it applies even on the degraded path (the ladder's
zeroed delta describes the no-override default).
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable
from uuid import UUID

from psycopg_pool import AsyncConnectionPool

from app import db
from app.config import Settings, agent_knob
from app.ingest import UnknownAgentError
from app.providers import (
    DialogueCallResult,
    MalformedOutputError,
    ProviderCallError,
    Providers,
)
from app.retrieval import RetrievalService
from app.schemas import (
    ActionDirective,
    DialogueInitRequest,
    DialogueTurnInstrumentation,
    DialogueTurnRequest,
    DialogueTurnResult,
    RetrievedMemory,
)

logger = logging.getLogger(__name__)

# Never-blank fallback (build ruling 2026-07-15): a neutral beat, not a canned
# apology — overridable per agent via agents.config "dialogue_fallback_line"
# (the TYPOLOGY_FALLBACK precedent; nothing integrator-configurable is
# hardcoded).
DIALOGUE_FALLBACK_LINE = "..."

# Prompt blocks (build ruling 2026-07-15): labeled, in spec order — identity,
# reputation snapshot, memories (rank order, IDs carried), output contract.
# The user message is the raw player utterance. Identical inputs assemble
# byte-identical prompts (memories arrive in the read path's deterministic
# rank order).
_BLOCK_IDENTITY = "[identity]\n{seed}"
_BLOCK_REPUTATION = (
    "[reputation]\nThe player's standing with you is {snapshot} on a scale "
    "from {scale_min} (worst) to {scale_max} (best)."
)
_BLOCK_MEMORIES_HEADER = "[memories]\nWhat you remember, most salient first:"
_MEMORY_LINE = "- ({memory_id}) {content}"
# Gated turns (mid-dialogue-gate.md, built 2026-07-19): the [memories] block
# becomes the scene's loaded set in the caller's append-only order — a
# byte-stable prefix across the scene, the structure prompt caching later
# attaches to — with this turn's gate fetches under a marked sub-header
# inside the same block (bracket labels stay top-level-block-only). The
# payload's item order is unchanged (deterministic score order).
_MEMORY_RECOLLECTION_SUBHEADER = "Recalled just now, mid-conversation:"
_BLOCK_CONTRACT_WITH_VOCAB = (
    "[output]\nReturn ONLY a JSON object with keys: prose (your spoken line, "
    'in character), directive (an object {{"type": <one of {vocabulary}>, '
    '"params": <object>}} or null when no action fits), reputation_delta '
    "(a float in [-1, 1]: how this exchange moves the player's standing with "
    "you). No other text."
)
_BLOCK_CONTRACT_NO_VOCAB = (
    "[output]\nReturn ONLY a JSON object with keys: prose (your spoken line, "
    "in character), directive (always null), reputation_delta (a float in "
    "[-1, 1]: how this exchange moves the player's standing with you). "
    "No other text."
)


def _ms(seconds: float) -> float:
    return round(seconds * 1000.0, 2)


def assemble_system_prompt(
    seed_identity: str | None,
    snapshot: float,
    scale_min: float,
    scale_max: float,
    items: list[RetrievedMemory],
    vocabulary: list[str],
    *,
    loaded_order: list[UUID] | None = None,
) -> str:
    """The prompt prefix, seed-prose-only (identity recompile rides with
    reconstruction). Exposed as a function so the walker can assert block
    order and byte-stability without a model call.

    `loaded_order` (gate build 2026-07-19): on gated turns the caller's
    append-only loaded-set order shapes the [memories] block — loaded items
    in that order, then any gate-fetched items under the recollection
    sub-header. None (loader turns, pre-gate callers) => the v1 rendering,
    byte-identical: items in payload rank order."""
    blocks: list[str] = []
    if seed_identity:
        blocks.append(_BLOCK_IDENTITY.format(seed=seed_identity))
    blocks.append(
        _BLOCK_REPUTATION.format(
            snapshot=snapshot, scale_min=scale_min, scale_max=scale_max
        )
    )
    if items:
        if loaded_order is None:
            ordered = list(items)
            fetched: list[RetrievedMemory] = []
        else:
            order_index = {memory_id: i for i, memory_id in enumerate(loaded_order)}
            loaded_items = [item for item in items if not item.gate_fetched]
            # Defensive: items outside the caller's list (shouldn't happen —
            # closed-gate serving is the loaded set) append after, payload order.
            ordered = sorted(
                loaded_items,
                key=lambda item: order_index.get(item.memory_id, len(order_index)),
            )
            fetched = [item for item in items if item.gate_fetched]
        lines = [
            _MEMORY_LINE.format(memory_id=item.memory_id, content=item.content)
            for item in ordered
        ]
        if fetched:
            lines.append(_MEMORY_RECOLLECTION_SUBHEADER)
            lines.extend(
                _MEMORY_LINE.format(memory_id=item.memory_id, content=item.content)
                for item in fetched
            )
        blocks.append(_BLOCK_MEMORIES_HEADER + "\n" + "\n".join(lines))
    if vocabulary:
        blocks.append(_BLOCK_CONTRACT_WITH_VOCAB.format(vocabulary=vocabulary))
    else:
        blocks.append(_BLOCK_CONTRACT_NO_VOCAB)
    return "\n\n".join(blocks)


def _turn_cost_usd(
    prices: dict[str, float], input_tokens: int, output_tokens: int, embed_tokens: int
) -> float | None:
    """USD per turn, only from the prices actually configured; None when
    nothing is priced (tokens are the unconditional unit — ruled 2026-07-15)."""
    total = 0.0
    priced = False
    if "dialogue_in" in prices and "dialogue_out" in prices:
        total += (
            input_tokens * prices["dialogue_in"]
            + output_tokens * prices["dialogue_out"]
        ) / 1e6
        priced = True
    if "embedding" in prices:
        total += embed_tokens * prices["embedding"] / 1e6
        priced = True
    return round(total, 6) if priced else None


class DialogueService:
    """One instance per process; both callers share it via the session-runner."""

    def __init__(
        self,
        pool: AsyncConnectionPool,
        providers: Providers,
        settings: Settings,
        retrieval: RetrievalService,
    ):
        self._pool = pool
        self._providers = providers
        self._settings = settings
        self._retrieval = retrieval

    async def run_dialogue_turn(
        self,
        request: DialogueTurnRequest,
        *,
        on_reconstruct: Callable[[], None] | None = None,
    ) -> DialogueTurnResult:
        t_total = time.perf_counter()

        state = await db.fetch_dialogue_agent_state(self._pool, request.agent_id)
        if state is None:
            raise UnknownAgentError(f"unknown agent_id {request.agent_id}")
        config = state.config

        # --- vocabulary resolution (ruled 2026-07-15): per-call wins, then
        # agents.config; neither -> every emitted directive drops (no
        # hardcoded default vocabulary).
        if request.action_vocabulary is not None:
            vocabulary = [str(v) for v in request.action_vocabulary]
            vocabulary_configured = True
        else:
            configured = config.get("action_vocabulary")
            vocabulary = [str(v) for v in configured] if configured else []
            vocabulary_configured = configured is not None

        # --- retrieval: the built read seam, passed through unreinterpreted
        # (incl. the caller-frozen scene state — reconstruction build
        # 2026-07-17 — and the caller-held loaded set + damper streak —
        # gate build 2026-07-19; past-theta items reconstruct inside this
        # call, and a blocking mid-scene serve fires on_reconstruct).
        retrieval = await self._retrieval.retrieve_dialogue_init(
            DialogueInitRequest(
                agent_id=request.agent_id,
                query_text=request.utterance,
                k=request.k,
                as_of=request.as_of,
                identity_version=request.identity_version,
                scene_started_at=request.scene_started_at,
                loaded_memory_ids=request.loaded_memory_ids,
                gate_fruitless_streak=request.gate_fruitless_streak,
            ),
            on_reconstruct=on_reconstruct,
        )

        # --- prompt assembly + the single dialogue call -------------------
        scale_min = agent_knob(config, "reputation_scale_min", self._settings)
        scale_max = agent_knob(config, "reputation_scale_max", self._settings)
        system_prompt = assemble_system_prompt(
            state.seed_identity,
            request.reputation_snapshot,
            scale_min,
            scale_max,
            retrieval.items,
            vocabulary,
            # The append-only prompt order applies only when the gate
            # actually evaluated (a gate-disabled agent with loaded IDs took
            # the loader path — its prompt stays byte-identical to v1).
            loaded_order=(
                request.loaded_memory_ids
                if retrieval.instrumentation.gate.evaluated
                else None
            ),
        )

        t0 = time.perf_counter()
        call: DialogueCallResult | None = None
        degraded_reason: str | None = None
        sonnet_in = sonnet_out = 0
        first_token_ms = 0.0
        try:
            call = await asyncio.to_thread(
                self._providers.dialogue.generate,
                system_prompt=system_prompt,
                utterance=request.utterance,
                vocabulary=vocabulary,
            )
            sonnet_in = call.input_tokens
            sonnet_out = call.output_tokens
            first_token_ms = call.first_token_ms
        except ProviderCallError as exc:
            degraded_reason = f"dialogue call failed: {exc}"
        except MalformedOutputError as exc:
            degraded_reason = f"dialogue output malformed: {exc}"
            sonnet_in = exc.input_tokens  # the spend happened; account it
            sonnet_out = exc.output_tokens
        sonnet_ms = _ms(time.perf_counter() - t0)

        # --- content: never-blank-a-dialogue -------------------------------
        if call is not None:
            content = call.prose
        else:
            content = str(config.get("dialogue_fallback_line", DIALOGUE_FALLBACK_LINE))
            logger.warning(
                "never-blank fallback served for agent %s: %s",
                request.agent_id,
                degraded_reason,
            )

        # --- action directive: validate against the vocabulary, soft-fail --
        directive: ActionDirective | None = None
        directive_dropped = False
        dropped_reason: str | None = None
        if call is not None:
            if call.directive_error is not None:
                directive_dropped = True
                dropped_reason = call.directive_error
            elif call.directive_type is not None:
                if not vocabulary_configured:
                    directive_dropped = True
                    dropped_reason = "no vocabulary configured"
                elif call.directive_type not in vocabulary:
                    directive_dropped = True
                    dropped_reason = f"unknown directive type {call.directive_type!r}"
                else:
                    directive = ActionDirective(
                        type=call.directive_type, params=call.directive_params
                    )
        if directive_dropped:
            logger.warning(
                "directive dropped for agent %s: %s", request.agent_id, dropped_reason
            )

        # --- reputation delta: override wins; degraded/absent -> zeroed ----
        if request.reputation_delta_override is not None:
            delta = request.reputation_delta_override
            delta_source = "override"
        elif call is not None and call.reputation_delta is not None:
            delta = call.reputation_delta
            delta_source = "model"
        else:
            delta = 0.0
            delta_source = "zeroed"
            if call is not None and call.delta_error is not None:
                logger.warning(
                    "reputation delta zeroed for agent %s: %s",
                    request.agent_id,
                    call.delta_error,
                )

        # --- apply in place (atomic clamp; the one persisted state change) -
        sensitivity = (
            state.reputation_sensitivity
            if state.reputation_sensitivity is not None
            else agent_knob(config, "reputation_sensitivity_default", self._settings)
        )
        neutral = agent_knob(config, "reputation_neutral", self._settings)
        t0 = time.perf_counter()
        applied = await db.apply_reputation_delta(
            self._pool,
            request.agent_id,
            addend=sensitivity * delta,
            neutral=neutral,
            scale_min=scale_min,
            scale_max=scale_max,
        )
        apply_ms = _ms(time.perf_counter() - t0)
        if applied is None:  # agents row vanished mid-turn: loud, not silent
            raise UnknownAgentError(f"unknown agent_id {request.agent_id}")
        reputation_prev, reputation_after = applied

        return DialogueTurnResult(
            agent_id=request.agent_id,
            content=content,
            directive=directive,
            directive_dropped=directive_dropped,
            directive_dropped_reason=dropped_reason,
            reputation_snapshot=request.reputation_snapshot,
            reputation_prev=reputation_prev,
            reputation_delta=delta,
            reputation_delta_source=delta_source,
            reputation_sensitivity=sensitivity,
            reputation_after=reputation_after,
            items=retrieval.items,
            instrumentation=DialogueTurnInstrumentation(
                retrieval=retrieval.instrumentation,
                sonnet_ms=sonnet_ms,
                sonnet_first_token_ms=first_token_ms,
                apply_ms=apply_ms,
                total_ms=_ms(time.perf_counter() - t_total),
                sonnet_input_tokens=sonnet_in,
                sonnet_output_tokens=sonnet_out,
                cost_usd=_turn_cost_usd(
                    self._settings.prices,
                    sonnet_in,
                    sonnet_out,
                    retrieval.instrumentation.embedding_tokens,
                ),
                degraded=degraded_reason is not None,
                degraded_reason=degraded_reason,
            ),
        )
