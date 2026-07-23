"""dialogue.py — THE dialogue-turn service: the split-brain streaming seam.

All callers — the interactive REPL and the synthetic load driver (via the
shared session-runner), and the stateless HTTP route (`POST /v1/dialogue/turn`
in app\\api.py, 2026-07-23) — sit on this module; none duplicates the timing
or token accounting recorded here (CLAUDE.md: instrument at the seam; specs:
docs\\cli-harness.md 2026-07-15, docs\\split-brain-streaming.md 2026-07-21).
The streaming SSE route rides later with the Unity client surface and
iterates this same generator.

Split-brain pipeline per turn (split-brain-streaming.md, ruled topology):
  resolve agent + vocabulary -> retrieval ONCE (retrieve_dialogue_init, built)
  -> two scored views off the SAME served set:
       dialogue view  = the served ranking (dialogue weights, byte-identical)
       behavior view  = the same served memories re-ranked with resolved
                        per-call weights (exponent-form on the product score,
                        so all-1.0 reproduces the dialogue order — parity)
  -> assemble the prose prompt (identity + reputation snapshot + dialogue-view
     memories + recent-actions block + prose instruction) and the behavior
     prompt (identity + reputation snapshot + behavior-view memories + the
     directive/delta contract)
  -> fire the two calls CONCURRENTLY:
       prose call (dialogue role) STREAMS pure prose — its first chunk is the
         product metric (first_word_ms); chunks yield through this seam
       behavior call (behavior role) returns {directive|null, delta} as JSON
  -> on both legs settled: validate the directive against the vocabulary
     (drop-soft), apply the reputation delta IN PLACE (atomic clamped UPDATE
     of the agents.reputation runtime scalar — outside the memory-content
     non-destructive invariant, same class as set_pinned)
  -> yield the terminal DialogueTurnResult (both views recorded — the
     divergence record for §13).

The two calls run concurrently, so one turn's WORDS and ACTION are chosen
independently: occasional same-turn incoherence is the split-brain character
(ruled 2026-07-21), bounded by the shared retrieval inputs + the vocabulary,
self-correcting from the next turn via the caller-held recent-actions block,
and instrumented from day one (dialogue_view + behavior_view + directive on
the result). The current turn's action never feeds the prose call — the prose
call sees PAST actions as world facts (the recent-actions block within a
scene; game-authored action observes across scenes).

`run_dialogue_turn` is an ASYNC GENERATOR (ruled seam shape): it yields prose
chunks (str) as they arrive, then yields the terminal DialogueTurnResult. The
sync streaming SDK is bridged into the async side through a worker thread + an
asyncio.Queue (the asyncio.to_thread + SelectorEventLoop precedent).

Scene state lives in the caller: the frozen `reputation_snapshot` and the
caller-held `recent_actions` arrive on every request and are refreshed by the
caller only at a scene boundary, so "snapshot / actions frozen within a scene"
is a property of the seam contract.

Degradation ladder (never-blank-a-dialogue, split-brain rows):
  - prose call fails BEFORE the first chunk -> fallback line, degraded flag.
  - prose stream DROPS mid-stream            -> KEEP the partial prose (it is
    non-blank) + degraded flag (ruled 2026-07-21).
  - behavior call fails / JSON malformed     -> no directive, zeroed delta,
    degraded flag; the prose stream is unaffected.
  - both fail                                -> fallback line + zeroed delta +
    flags (never-blank holds).
  - unknown / unparseable directive          -> logged, dropped, turn succeeds.
  - retrieval degraded                       -> inherited in nested instrumentation.
  - delta would exceed the scale             -> clamped in SQL; never throws.

A client `reputation_delta_override` wins over the behavior model's delta
(§9) — client-authoritative, so it applies even on the degraded path (the
ladder's zeroed delta describes the no-override default).
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from typing import Callable
from uuid import UUID

from psycopg_pool import AsyncConnectionPool

from app import db
from app.config import (
    BEHAVIOR_WEIGHT_MAX,
    BEHAVIOR_WEIGHT_MIN,
    Settings,
    agent_knob,
)
from app.ingest import UnknownAgentError
from app.providers import (
    BehaviorCallResult,
    MalformedOutputError,
    ProseResult,
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
    RecentAction,
    RetrievedMemory,
    ScoredRef,
    WeightOverrides,
)

logger = logging.getLogger(__name__)

# Never-blank fallback (build ruling 2026-07-15): a neutral beat, not a canned
# apology — overridable per agent via agents.config "dialogue_fallback_line".
DIALOGUE_FALLBACK_LINE = "..."

# Prompt blocks. Labeled, in spec order. Identical inputs assemble
# byte-identical prompts (memories arrive in a deterministic rank order).
_BLOCK_IDENTITY = "[identity]\n{seed}"
_BLOCK_REPUTATION = (
    "[reputation]\nThe player's standing with you is {snapshot} on a scale "
    "from {scale_min} (worst) to {scale_max} (best)."
)
_BLOCK_MEMORIES_HEADER = "[memories]\nWhat you remember, most salient first:"
_MEMORY_LINE = "- ({memory_id}) {content}"
# Gated turns (mid-dialogue-gate.md, 2026-07-19): the [memories] block renders
# the scene's loaded set in the caller's append-only order (a byte-stable
# prefix — the structure prompt caching later attaches to), with this turn's
# gate fetches under a marked sub-header. This shaping is a DIALOGUE-view /
# prose-prompt concern (prompt-cache stability of the streaming call); the
# behavior prompt renders its view in plain behavior-rank order (loaded_order
# None).
_MEMORY_RECOLLECTION_SUBHEADER = "Recalled just now, mid-conversation:"
# Recent-actions block (split-brain-streaming.md): world-fact phrasing, never
# "you decided to." Prose prompt only.
_BLOCK_RECENT_ACTIONS_HEADER = (
    "[recent actions]\nEarlier in this conversation you were seen to:"
)
_RECENT_ACTION_LINE = "- {type} {params}"
# The prose call's output contract: PURE PROSE, no JSON envelope (the directive
# + delta live on the concurrent behavior call now).
_BLOCK_PROSE_INSTRUCTION = (
    "[output]\nReply with ONLY your spoken line, in character. Prose only — no "
    "JSON, no labels, no surrounding quotation marks."
)
# The behavior call's output contract: directive + delta as JSON, no prose.
_BLOCK_BEHAVIOR_CONTRACT_WITH_VOCAB = (
    "[output]\nReturn ONLY a JSON object with keys: directive (an object "
    '{{"type": <one of {vocabulary}>, "params": <object>}} or null when no '
    "action fits), reputation_delta (a float in [-1, 1]: how this exchange "
    "moves the player's standing with you). No other text."
)
_BLOCK_BEHAVIOR_CONTRACT_NO_VOCAB = (
    "[output]\nReturn ONLY a JSON object with keys: directive (always null), "
    "reputation_delta (a float in [-1, 1]: how this exchange moves the "
    "player's standing with you). No other text."
)


def _ms(seconds: float) -> float:
    return round(seconds * 1000.0, 2)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _render_memories(
    items: list[RetrievedMemory], loaded_order: list[UUID] | None
) -> str:
    """The [memories] block. `loaded_order` (gate build): loaded items in the
    caller's append-only order, then gate-fetched items under the recollection
    sub-header. None => plain payload rank order, byte-identical to v1."""
    if loaded_order is None:
        ordered = list(items)
        fetched: list[RetrievedMemory] = []
    else:
        order_index = {memory_id: i for i, memory_id in enumerate(loaded_order)}
        loaded_items = [item for item in items if not item.gate_fetched]
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
    return _BLOCK_MEMORIES_HEADER + "\n" + "\n".join(lines)


def _render_recent_actions(recent_actions: list[RecentAction]) -> str:
    """The recent-actions block, world-fact phrasing. Rendered only when the
    caller holds scene actions — the prose prompt carries it iff non-empty."""
    lines = [
        _RECENT_ACTION_LINE.format(type=action.type, params=action.params)
        for action in recent_actions
    ]
    return _BLOCK_RECENT_ACTIONS_HEADER + "\n" + "\n".join(lines)


def assemble_prose_prompt(
    seed_identity: str | None,
    snapshot: float,
    scale_min: float,
    scale_max: float,
    items: list[RetrievedMemory],
    recent_actions: list[RecentAction],
    *,
    loaded_order: list[UUID] | None = None,
) -> str:
    """The streaming prose call's system prompt: identity + reputation snapshot
    + dialogue-view memories + recent-actions (iff any) + the pure-prose
    instruction. Exposed so the walker can assert block order + byte-stability
    without a model call. The prose call never sees the vocabulary or the JSON
    contract — it speaks."""
    blocks: list[str] = []
    if seed_identity:
        blocks.append(_BLOCK_IDENTITY.format(seed=seed_identity))
    blocks.append(
        _BLOCK_REPUTATION.format(
            snapshot=snapshot, scale_min=scale_min, scale_max=scale_max
        )
    )
    if items:
        blocks.append(_render_memories(items, loaded_order))
    if recent_actions:
        blocks.append(_render_recent_actions(recent_actions))
    blocks.append(_BLOCK_PROSE_INSTRUCTION)
    return "\n\n".join(blocks)


def assemble_behavior_prompt(
    seed_identity: str | None,
    snapshot: float,
    scale_min: float,
    scale_max: float,
    items: list[RetrievedMemory],
    vocabulary: list[str],
) -> str:
    """The concurrent behavior call's system prompt: identity + reputation
    snapshot + behavior-view memories (plain behavior-rank order) + the
    directive/delta JSON contract. Identity is shared with the prose prompt so
    the asymmetry stays STATISTICAL, not architectural (§9): same character,
    same candidates, different weights — the recent-actions block is the one
    ruled information difference and it is prose-only (the behavior call
    chooses a new action, it does not explain a past one)."""
    blocks: list[str] = []
    if seed_identity:
        blocks.append(_BLOCK_IDENTITY.format(seed=seed_identity))
    blocks.append(
        _BLOCK_REPUTATION.format(
            snapshot=snapshot, scale_min=scale_min, scale_max=scale_max
        )
    )
    if items:
        blocks.append(_render_memories(items, None))
    if vocabulary:
        blocks.append(_BLOCK_BEHAVIOR_CONTRACT_WITH_VOCAB.format(vocabulary=vocabulary))
    else:
        blocks.append(_BLOCK_BEHAVIOR_CONTRACT_NO_VOCAB)
    return "\n\n".join(blocks)


def resolve_behavior_weights(
    config: dict, overrides: WeightOverrides | None, settings: Settings
) -> tuple[float, float, float]:
    """The behavior view's per-call weights: request field -> agents.config ->
    1.0 defaults, each clamped to [BEHAVIOR_WEIGHT_MIN, BEHAVIOR_WEIGHT_MAX].
    Pure, module-level: the walker asserts it without a service."""

    def pick(key: str, override_value: float | None) -> float:
        if override_value is not None:
            value = float(override_value)
        else:
            value = agent_knob(config, key, settings)
        return _clamp(value, BEHAVIOR_WEIGHT_MIN, BEHAVIOR_WEIGHT_MAX)

    return (
        pick("behavior_weight_relevance", overrides.relevance if overrides else None),
        pick("behavior_weight_recency", overrides.recency if overrides else None),
        pick(
            "behavior_weight_importance",
            overrides.importance if overrides else None,
        ),
    )


def behavior_score(
    item: RetrievedMemory, w_rel: float, w_rec: float, w_imp: float
) -> float:
    """Exponent-form re-weighting of an already-scored served item: start from
    its dialogue-view score (which folds in the encoding-context factor) and
    adjust each component by its weight minus one. At all-1.0 the exponents are
    zero, so behavior_score == item.score — the parity contract. A zero base
    component is skipped (pow(0, negative) is undefined), never a divide."""
    score = item.score
    if item.relevance is not None and item.relevance > 0.0:
        score *= item.relevance ** (w_rel - 1.0)
    if item.recency > 0.0:
        score *= item.recency ** (w_rec - 1.0)
    if item.importance_norm > 0.0:
        score *= item.importance_norm ** (w_imp - 1.0)
    return score


def rank_behavior_view(
    items: list[RetrievedMemory], weights: tuple[float, float, float]
) -> list[tuple[float, RetrievedMemory]]:
    """The behavior view: the SAME served items re-scored with the resolved
    weights, in deterministic order (ties break on memory_id — the retrieval
    _sort_scored convention, so identical inputs reproduce byte-identically)."""
    w_rel, w_rec, w_imp = weights
    scored = [(behavior_score(item, w_rel, w_rec, w_imp), item) for item in items]
    scored.sort(key=lambda entry: (-entry[0], entry[1].memory_id))
    return scored


def _turn_cost_usd(
    prices: dict[str, float],
    prose_in: int,
    prose_out: int,
    behavior_in: int,
    behavior_out: int,
    embed_tokens: int,
) -> float | None:
    """USD per turn, only from the prices actually configured; None when
    nothing is priced (tokens are the unconditional unit — ruled 2026-07-15).
    The behavior call has its own price pair (split-brain build)."""
    total = 0.0
    priced = False
    if "dialogue_in" in prices and "dialogue_out" in prices:
        total += (
            prose_in * prices["dialogue_in"] + prose_out * prices["dialogue_out"]
        ) / 1e6
        priced = True
    if "behavior_in" in prices and "behavior_out" in prices:
        total += (
            behavior_in * prices["behavior_in"] + behavior_out * prices["behavior_out"]
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
    ) -> AsyncIterator[str | DialogueTurnResult]:
        """The split-brain streaming seam (async generator): yields prose
        chunks (str) as they arrive, then the terminal DialogueTurnResult.
        Non-streaming callers drain to the terminal item (session.utterance);
        the REPL yields the chunks live (session.stream_utterance)."""
        t_total = time.perf_counter()

        state = await db.fetch_dialogue_agent_state(self._pool, request.agent_id)
        if state is None:
            raise UnknownAgentError(f"unknown agent_id {request.agent_id}")
        config = state.config

        # --- vocabulary resolution (ruled 2026-07-15): per-call wins, then
        # agents.config; neither -> every emitted directive drops.
        if request.action_vocabulary is not None:
            vocabulary = [str(v) for v in request.action_vocabulary]
            vocabulary_configured = True
        else:
            configured = config.get("action_vocabulary")
            vocabulary = [str(v) for v in configured] if configured else []
            vocabulary_configured = configured is not None

        # --- retrieval: the built read seam, run ONCE, passed through
        # unreinterpreted (scene state + gate loaded set + on_reconstruct).
        retrieval = await self._retrieval.retrieve_dialogue_init(
            DialogueInitRequest(
                agent_id=request.agent_id,
                query_text=request.utterance,
                k=request.k,
                as_of=request.as_of,
                location_name=request.location_name,
                entities=request.entities,
                event_time=request.event_time,
                identity_version=request.identity_version,
                scene_started_at=request.scene_started_at,
                loaded_memory_ids=request.loaded_memory_ids,
                gate_fruitless_streak=request.gate_fruitless_streak,
            ),
            on_reconstruct=on_reconstruct,
        )

        # --- two scored views off the SAME served set --------------------
        scale_min = agent_knob(config, "reputation_scale_min", self._settings)
        scale_max = agent_knob(config, "reputation_scale_max", self._settings)
        # dialogue view = the served ranking; behavior view = re-rank with the
        # resolved weights (behavior view only — the dialogue view keeps parity).
        weights = resolve_behavior_weights(
            config, request.weight_overrides, self._settings
        )
        behavior_scored = rank_behavior_view(retrieval.items, weights)
        behavior_items = [item for _score, item in behavior_scored]
        dialogue_view = [
            ScoredRef(memory_id=item.memory_id, score=item.score)
            for item in retrieval.items
        ]
        behavior_view = [
            ScoredRef(memory_id=item.memory_id, score=score)
            for score, item in behavior_scored
        ]

        # The append-only prompt order applies only when the gate actually
        # evaluated (a gate-disabled agent with loaded IDs took the loader path
        # — its prose prompt stays byte-identical to v1).
        loaded_order = (
            request.loaded_memory_ids
            if retrieval.instrumentation.gate.evaluated
            else None
        )
        prose_prompt = assemble_prose_prompt(
            state.seed_identity,
            request.reputation_snapshot,
            scale_min,
            scale_max,
            retrieval.items,
            request.recent_actions,
            loaded_order=loaded_order,
        )
        behavior_prompt = assemble_behavior_prompt(
            state.seed_identity,
            request.reputation_snapshot,
            scale_min,
            scale_max,
            behavior_items,
            vocabulary,
        )

        # --- fire both calls CONCURRENTLY --------------------------------
        loop = asyncio.get_running_loop()

        async def _run_behavior() -> tuple[str, object, float]:
            t0 = time.perf_counter()
            try:
                res = await asyncio.to_thread(
                    self._providers.behavior.decide,
                    system_prompt=behavior_prompt,
                    utterance=request.utterance,
                    vocabulary=vocabulary,
                )
                return "ok", res, _ms(time.perf_counter() - t0)
            except ProviderCallError as exc:
                return "error", exc, _ms(time.perf_counter() - t0)
            except MalformedOutputError as exc:
                return "malformed", exc, _ms(time.perf_counter() - t0)

        behavior_task = asyncio.create_task(_run_behavior())

        # Prose leg: run the sync stream generator in a worker thread, bridge
        # its chunks onto an asyncio.Queue, yield them from this async
        # generator. StopIteration.value carries the ProseResult (tokens +
        # provider-side first-token latency); an exception mid-iteration is a
        # mid-stream drop (partial chunks already yielded), before any chunk a
        # pre-first-chunk failure.
        queue: asyncio.Queue = asyncio.Queue()

        def _produce() -> None:
            gen = self._providers.dialogue.stream_prose(
                system_prompt=prose_prompt, utterance=request.utterance
            )
            try:
                while True:
                    try:
                        chunk = next(gen)
                    except StopIteration as stop:
                        loop.call_soon_threadsafe(
                            queue.put_nowait, ("done", stop.value)
                        )
                        return
                    loop.call_soon_threadsafe(queue.put_nowait, ("chunk", chunk))
            except Exception as exc:  # noqa: BLE001 — signalled to the seam
                loop.call_soon_threadsafe(queue.put_nowait, ("error", exc))

        producer = loop.run_in_executor(None, _produce)

        content_parts: list[str] = []
        prose_result: ProseResult | None = None
        prose_error: Exception | None = None
        first_word_ms = 0.0
        perceived_first_word_ms = 0.0
        t_prose = time.perf_counter()
        while True:
            kind, payload = await queue.get()
            if kind == "chunk":
                if not content_parts:
                    now = time.perf_counter()
                    first_word_ms = _ms(now - t_prose)
                    # Perceived TTFT: same instant, clocked from turn start —
                    # retrieval-inclusive (the honest metric, audit 2026-07-22).
                    perceived_first_word_ms = _ms(now - t_total)
                content_parts.append(payload)
                yield payload
            elif kind == "done":
                prose_result = payload
                break
            else:  # "error"
                prose_error = payload
                break
        await producer  # let the worker thread finish cleanly
        prose_stream_ms = _ms(time.perf_counter() - t_prose)

        # --- behavior leg: settle (it ran concurrently) ------------------
        behavior_status, behavior_payload, behavior_ms = await behavior_task
        behavior_result: BehaviorCallResult | None = None
        behavior_in = behavior_out = 0
        behavior_degraded_reason: str | None = None
        if behavior_status == "ok":
            behavior_result = behavior_payload  # type: ignore[assignment]
            behavior_in = behavior_result.input_tokens
            behavior_out = behavior_result.output_tokens
        elif behavior_status == "malformed":
            behavior_degraded_reason = f"behavior output malformed: {behavior_payload}"
            behavior_in = behavior_payload.input_tokens  # type: ignore[attr-defined]
            behavior_out = behavior_payload.output_tokens  # type: ignore[attr-defined]
        else:  # "error"
            behavior_degraded_reason = f"behavior call failed: {behavior_payload}"

        # --- content: never-blank-a-dialogue (keep-partial on mid-drop) --
        prose_text = "".join(content_parts)
        prose_degraded_reason: str | None = None
        if prose_error is not None:
            prose_degraded_reason = (
                f"prose stream dropped mid-stream: {prose_error}"
                if content_parts
                else f"prose call failed: {prose_error}"
            )
        if prose_text:
            content = prose_text  # full, or partial kept (ruled 2026-07-21)
        else:
            content = str(config.get("dialogue_fallback_line", DIALOGUE_FALLBACK_LINE))
            if prose_degraded_reason is None:
                prose_degraded_reason = "prose produced no text"
            logger.warning(
                "never-blank fallback served for agent %s: %s",
                request.agent_id,
                prose_degraded_reason,
            )

        prose_in = prose_result.input_tokens if prose_result else 0
        prose_out = prose_result.output_tokens if prose_result else 0

        # --- action directive: validate against the vocabulary, soft-fail --
        directive: ActionDirective | None = None
        directive_dropped = False
        dropped_reason: str | None = None
        if behavior_result is not None:
            if behavior_result.directive_error is not None:
                directive_dropped = True
                dropped_reason = behavior_result.directive_error
            elif behavior_result.directive_type is not None:
                if not vocabulary_configured:
                    directive_dropped = True
                    dropped_reason = "no vocabulary configured"
                elif behavior_result.directive_type not in vocabulary:
                    directive_dropped = True
                    dropped_reason = (
                        f"unknown directive type {behavior_result.directive_type!r}"
                    )
                else:
                    directive = ActionDirective(
                        type=behavior_result.directive_type,
                        params=behavior_result.directive_params,
                    )
        if directive_dropped:
            logger.warning(
                "directive dropped for agent %s: %s", request.agent_id, dropped_reason
            )

        # --- reputation delta: override wins; degraded/absent -> zeroed ----
        if request.reputation_delta_override is not None:
            delta = request.reputation_delta_override
            delta_source = "override"
        elif (
            behavior_result is not None and behavior_result.reputation_delta is not None
        ):
            delta = behavior_result.reputation_delta
            delta_source = "model"
        else:
            delta = 0.0
            delta_source = "zeroed"
            if behavior_result is not None and behavior_result.delta_error is not None:
                logger.warning(
                    "reputation delta zeroed for agent %s: %s",
                    request.agent_id,
                    behavior_result.delta_error,
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

        reasons = [r for r in (prose_degraded_reason, behavior_degraded_reason) if r]
        degraded_reason = "; ".join(reasons) if reasons else None

        yield DialogueTurnResult(
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
            dialogue_view=dialogue_view,
            behavior_view=behavior_view,
            instrumentation=DialogueTurnInstrumentation(
                retrieval=retrieval.instrumentation,
                sonnet_ms=prose_stream_ms,
                sonnet_first_token_ms=first_word_ms,
                apply_ms=apply_ms,
                total_ms=_ms(time.perf_counter() - t_total),
                sonnet_input_tokens=prose_in,
                sonnet_output_tokens=prose_out,
                first_word_ms=first_word_ms,
                perceived_first_word_ms=perceived_first_word_ms,
                prose_stream_ms=prose_stream_ms,
                behavior_ms=behavior_ms,
                behavior_input_tokens=behavior_in,
                behavior_output_tokens=behavior_out,
                cost_usd=_turn_cost_usd(
                    self._settings.prices,
                    prose_in,
                    prose_out,
                    behavior_in,
                    behavior_out,
                    retrieval.instrumentation.embedding_tokens,
                ),
                degraded=degraded_reason is not None,
                degraded_reason=degraded_reason,
            ),
        )
