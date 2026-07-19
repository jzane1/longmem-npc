"""retrieval.py — THE retrieval service: the read path's single instrumented seam.

Both callers (the FastAPI route and the CLI harness) sit on this module;
neither duplicates the timing or token accounting recorded here (CLAUDE.md:
instrument at the seam; surface mirrors the write path's 2026-07-13 ruling;
spec: docs\\read-path.md, built 2026-07-14; gate stage:
docs\\mid-dialogue-gate.md, built 2026-07-19).

Pipeline per dialogue-init request:
  resolve agent + knobs -> embed the query probe (as-is; ONE embed per turn —
  it is also the gate's novelty basis and the fire probe) -> GATE (when the
  request carries the caller-held loaded set and gate_enabled != 0;
  otherwise the LOADER path, byte-identical to v1):
    LOADER: vector over-fetch -> score (relevance x recency x
    importance_norm; pin exemption) -> top-k;
    GATED:  fetch the loaded set by ID + the live identity components ->
    novelty check + entity tripwire + damper (app\\gate.py, pure) ->
    CLOSED: serve the loaded set (relevance recomputed free from the novelty
    distances; zero probe SQL) / FIRE: the standard over-fetch probe with
    loaded IDs excluded (or the entity-only lexical fetch off the partial
    GIN when the embedding is down), top gate_fetch_k NEW items appended and
    marked gate_fetched;
  -> SERVE via the reconstruction stage (app\\reconstruction.py, built
  2026-07-17): theta partition at the scene-frozen basis, cache keyed
  (memory_id, identity_version + decay band), batched retelling of the
  misses with drift-budgeted write-back, read_mode = "reconstructed" past
  theta — pinned and fresh rows serve their live heads verbatim. A blocking
  mid-scene serve fires the optional pre-serve callback (fork 5) and is
  recorded as reconstructing_blocked.

Retrieval (candidates + scoring) and serving (text assembly + read-mode
stamping) are deliberately separate stages: the reconstruction build swapped
the SERVING stage only; the gate build put a decision in FRONT of retrieval
without touching scoring — the loader path is byte-for-byte the read-path v1
logic. Since the reconstruction build this seam WRITES on read (chain
write-backs + cache rows) — architecture §7 mandates write-back on the read
path.

Degradation ladder (read, ruled 2026-07-14; reconstruction rows 2026-07-17;
gate rows 2026-07-19 — audit ruling #3 implementation-shaped):
  - query-embedding failure -> FAIL-QUIET fallback. Loader: rank ALL live
    candidates (NULL-embedding rows included) by recency x importance_norm;
    relevance null. Gated: the ENTITY-ONLY rung — the tripwire still
    evaluates (it is lexical); on fire, fetch off the partial entities GIN
    ranked recency x importance_norm, fetched relevance null.
  - no live components, or no entities coverage basis -> NOVELTY-ONLY rung
    (the tripwire cannot evaluate — it never fires for want of a basis).
  - both out -> gate CLOSED: serve the loaded set, fail-quiet, never an
    error, never a blank turn.
  - wholly-failed loaded-set fetch -> the loader path + degraded reason;
    unknown/foreign/dead loaded IDs are excluded by the live-head join and
    counted (loaded_missing_count).
  - empty/short store -> 0..k items, never an error (a valid young-NPC state).
  - reconstruction-stage failures degrade soft per reconstruction.md's
    ladder: affected items serve their live heads with honest read_mode.
"""

from __future__ import annotations

import asyncio
import math
import time
from dataclasses import replace
from datetime import datetime, timezone
from typing import Callable

from psycopg_pool import AsyncConnectionPool

from app import db, decay, gate
from app.config import Settings, agent_knob
from app.ingest import UnknownAgentError
from app.providers import ProviderCallError, Providers
from app.reconstruction import ReconstructionService, ServeOutcome
from app.schemas import (
    DialogueInitRequest,
    GateInstrumentation,
    RetrievalInstrumentation,
    RetrievalResult,
)


def _ms(seconds: float) -> float:
    return round(seconds * 1000.0, 2)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# The scored-tuple shape shared with the serving stage:
# (score, relevance | None, recency, importance_norm, importance_raw, row).
_Scored = tuple[float, float | None, float, float, float, db.CandidateRow]


def _sort_scored(scored: list[_Scored]) -> list[_Scored]:
    """Deterministic order: ties break on memory_id, so byte-identity holds
    across identical calls (within-scene stability invariant)."""
    return sorted(scored, key=lambda entry: (-entry[0], entry[5].memory_id))


class RetrievalService:
    """One instance per process; both callers share it."""

    def __init__(
        self, pool: AsyncConnectionPool, providers: Providers, settings: Settings
    ):
        self._pool = pool
        self._providers = providers
        self._settings = settings
        # The serving stage (reconstruction.md): constructed here so neither
        # caller (route, session-runner) changes its wiring. The gate stage
        # (app\gate.py) is pure functions — nothing to construct.
        self._reconstruction = ReconstructionService(pool, providers, settings)

    def _score_rows(
        self, candidates: list[db.CandidateRow], config: dict, as_of: datetime
    ) -> list[_Scored]:
        """The read-path v1 scoring loop, extracted verbatim at the gate
        build (a source-layout move only — the loader path's behavior, SQL,
        and payloads are byte-identical; the walkers prove it)."""
        k_importance = agent_knob(config, "decay_k_importance", self._settings)
        floor = agent_knob(config, "importance_norm_floor", self._settings)
        neutral = agent_knob(config, "importance_neutral", self._settings)
        scored: list[_Scored] = []
        for row in candidates:
            # The write path never stores NULL importance; fixture rows might.
            raw = row.importance_raw if row.importance_raw is not None else neutral
            # Recency: the shared decay math; pin = decay exemption (arch §8).
            if row.pinned:
                rec = 1.0
            else:
                tau_base = decay.resolve_tau_base(
                    row.decay_class, config, self._settings
                )
                tau_eff = decay.tau_effective(tau_base, k_importance, raw)
                rec = decay.recency((as_of - row.valid_at).total_seconds(), tau_eff)
            # importance_norm = clamp + floor (ruled 2026-07-14 over the
            # spec's min-max suggestion: store-relative bounds would let an
            # invalidated extreme row move OTHER items' scores, breaking
            # Set B's decay-vs-invalidation separation).
            imp = _clamp(raw, floor, 1.0)
            if row.distance is not None:
                rel: float | None = _clamp(1.0 - row.distance, 0.0, 1.0)
                score = rel * rec * imp
            else:  # no vector for this row — no relevance computed, honest null
                rel = None
                score = rec * imp
            scored.append((score, rel, rec, imp, raw, row))
        return scored

    async def retrieve_dialogue_init(
        self,
        request: DialogueInitRequest,
        *,
        on_reconstruct: Callable[[], None] | None = None,
    ) -> RetrievalResult:
        t_total = time.perf_counter()

        agent = await db.fetch_agent(self._pool, request.agent_id)
        if agent is None:
            raise UnknownAgentError(f"unknown agent_id {request.agent_id}")
        config: dict = agent["config"]

        # k resolution (ruled): request -> agents.config -> service default.
        k = (
            request.k
            if request.k is not None
            else int(agent_knob(config, "retrieval_top_k", self._settings))
        )
        # as_of (ruled): world-time override for age computation, default now.
        as_of = (
            request.as_of if request.as_of is not None else datetime.now(timezone.utc)
        )

        # --- query embedding (fail-quiet degradation; ONE embed per turn) --
        t0 = time.perf_counter()
        query_vector: list[float] | None = None
        embed_tokens = 0
        degraded_reason: str | None = None
        try:
            embed_result = await asyncio.to_thread(
                self._providers.embedding.embed, [request.query_text]
            )
            query_vector = embed_result.vectors[0]
            embed_tokens = embed_result.tokens
        except ProviderCallError as exc:
            degraded_reason = f"query embedding failed: {exc}"
        embed_ms = _ms(time.perf_counter() - t0)

        # --- gate stage (mid-dialogue-gate.md fork 1: the loaded set is
        # caller-held scene state; absent -> loader turn, v1 byte-parity;
        # gate_enabled 0 -> loader regardless, the fixture-pin/kill-switch
        # shape) --------------------------------------------------------------
        gate_active = (
            request.loaded_memory_ids is not None
            and agent_knob(config, "gate_enabled", self._settings) != 0.0
        )
        loaded_rows: list[db.GateRow] = []
        components: list[dict] = []
        gate_ms = 0.0
        if gate_active:
            t_gate = time.perf_counter()
            try:
                loaded_rows = await db.fetch_loaded_set(
                    self._pool, request.agent_id, request.loaded_memory_ids
                )
                components = await db.fetch_live_components(
                    self._pool, request.agent_id
                )
            except Exception as exc:  # noqa: BLE001 — ladder: fail-quiet to loader
                gate_active = False
                fetch_reason = f"loaded-set fetch failed: {exc}"
                degraded_reason = (
                    f"{degraded_reason}; {fetch_reason}"
                    if degraded_reason
                    else fetch_reason
                )

        if gate_active:
            (
                sql_ms,
                score_ms,
                candidate_count,
                gate_inst,
                outcome,
            ) = await self._gated(
                request=request,
                config=config,
                seed_identity=agent["seed_identity"],
                as_of=as_of,
                query_vector=query_vector,
                loaded_rows=loaded_rows,
                components=components,
                t_gate=t_gate,
                on_reconstruct=on_reconstruct,
            )
        else:
            # --- LOADER path: byte-identical to read-path v1 ----------------
            t0 = time.perf_counter()
            if query_vector is not None:
                overfetch = agent_knob(
                    config, "retrieval_overfetch_factor", self._settings
                )
                limit = max(k, math.ceil(overfetch * k))
                candidates = await db.fetch_vector_candidates(
                    self._pool, request.agent_id, query_vector, limit
                )
            else:  # degraded: every live candidate, NULL embeddings included
                candidates = await db.fetch_live_candidates(
                    self._pool, request.agent_id
                )
            sql_ms = _ms(time.perf_counter() - t0)
            t0 = time.perf_counter()
            serve_input = _sort_scored(self._score_rows(candidates, config, as_of))[:k]
            score_ms = _ms(time.perf_counter() - t0)
            candidate_count = len(candidates)
            gate_inst = GateInstrumentation()  # evaluated=False, all defaults
            outcome = await self._reconstruction.serve(
                request=request,
                config=config,
                seed_identity=agent["seed_identity"],
                scored_top=serve_input,
                as_of=as_of,
            )

        reasons = [r for r in (degraded_reason, outcome.degraded_reason) if r]
        return RetrievalResult(
            items=outcome.items,
            instrumentation=RetrievalInstrumentation(
                embed_ms=embed_ms,
                sql_ms=sql_ms,
                score_ms=score_ms,
                total_ms=_ms(time.perf_counter() - t_total),
                embedding_tokens=embed_tokens,
                candidate_count=candidate_count,
                k_effective=k,
                degraded=bool(reasons),
                degraded_reason="; ".join(reasons) if reasons else None,
                as_of_effective=as_of,
                reconstruction_ms=outcome.reconstruction_ms,
                reconstruction_input_tokens=outcome.input_tokens,
                reconstruction_output_tokens=outcome.output_tokens,
                reconstruction_embed_tokens=outcome.embed_tokens,
                cache_hits=outcome.cache_hits,
                cache_misses=outcome.cache_misses,
                write_backs=outcome.write_backs,
                drift_refusals=outcome.drift_refusals,
                identity_version_effective=outcome.identity_version,
                identity_bootstrapped=outcome.identity_bootstrapped,
                gate=gate_inst,
            ),
        )

    async def _gated(
        self,
        *,
        request: DialogueInitRequest,
        config: dict,
        seed_identity: str | None,
        as_of: datetime,
        query_vector: list[float] | None,
        loaded_rows: list[db.GateRow],
        components: list[dict],
        t_gate: float,
        on_reconstruct: Callable[[], None] | None,
    ) -> tuple[float, float, int, GateInstrumentation, ServeOutcome]:
        """The gated turn (mid-dialogue-gate.md mechanism steps 2-8).

        Returns (sql_ms, score_ms, candidate_count, gate_inst, outcome).
        Timing contract (ruled with the build): gate_ms = loaded-set fetch +
        components fetch + signal evaluation + decision; sql_ms = the fire
        probe / lexical fetch only (0.0 on closed turns — the zero-probe-SQL
        claim); the shared utterance embed stays in embed_ms."""
        loaded_ids = request.loaded_memory_ids or []
        loaded_missing = len(loaded_ids) - len(loaded_rows)

        # --- signal evaluation (pure, app\gate.py) ------------------------
        novelty_evaluable = query_vector is not None
        if novelty_evaluable:
            distances, null_count = gate.novelty_distances(query_vector, loaded_rows)
            min_distance = min(distances.values()) if distances else None
        else:
            distances = {}
            null_count = sum(1 for gr in loaded_rows if gr.embedding is None)
            min_distance = None
        basis = gate.coverage_basis(loaded_rows)
        tripwire_evaluable = bool(components) and bool(basis)
        mentions = (
            gate.detect_mentions(request.query_text, components)
            if tripwire_evaluable
            else []
        )
        uncovered = gate.uncovered_mentions(mentions, basis)
        damper_max = int(
            agent_knob(config, "gate_damper_fruitless_max", self._settings)
        )
        damper_active = request.gate_fruitless_streak >= damper_max
        decision = gate.decide(
            novelty_evaluable=novelty_evaluable,
            min_distance=min_distance,
            threshold=agent_knob(config, "gate_novelty_threshold", self._settings),
            tripwire_evaluable=tripwire_evaluable,
            uncovered=uncovered,
            damper_active=damper_active,
        )
        gate_ms = _ms(time.perf_counter() - t_gate)

        # --- the loaded set, scored under this turn's probe (relevance
        # recomputed FREE from the novelty distances — no probe SQL, no
        # second embed; NULL-embedding rows carry relevance null, the
        # read-path precedent) --------------------------------------------
        t_score = time.perf_counter()
        loaded_candidates = [
            replace(gr.row, distance=distances.get(gr.row.memory_id))
            for gr in loaded_rows
        ]
        loaded_scored = self._score_rows(loaded_candidates, config, as_of)
        score_ms = _ms(time.perf_counter() - t_score)

        # --- decision: fire (fetch + append) or closed (serve the set) ----
        sql_ms = 0.0
        fetched_rows: list[db.GateRow] = []
        fetched_top: list[_Scored] = []
        if decision.fired:
            t0 = time.perf_counter()
            if decision.rung == gate.GATE_RUNG_ENTITY_ONLY:
                # Embeddings down: the lexical fetch off the partial GIN,
                # ranked recency x importance_norm in Python (relevance
                # stays null — no vector existed to compute one).
                terms = [
                    term
                    for comp in uncovered
                    for term in (comp["canonical"], *(comp.get("aliases") or []))
                ]
                fetched_rows = await db.fetch_entity_candidates(
                    self._pool, request.agent_id, terms, loaded_ids
                )
            else:
                # The standard over-fetch probe, REUSING the turn's one
                # embedding; loaded IDs excluded in SQL (append-only).
                gk = int(agent_knob(config, "gate_fetch_k", self._settings))
                overfetch = agent_knob(
                    config, "retrieval_overfetch_factor", self._settings
                )
                limit = max(gk, math.ceil(overfetch * gk))
                fetched_rows = await db.fetch_gate_candidates(
                    self._pool, request.agent_id, query_vector, limit, loaded_ids
                )
            sql_ms = _ms(time.perf_counter() - t0)
            t_score = time.perf_counter()
            gk = int(agent_knob(config, "gate_fetch_k", self._settings))
            fetched_scored = self._score_rows(
                [gr.row for gr in fetched_rows], config, as_of
            )
            fetched_top = _sort_scored(fetched_scored)[:gk]
            score_ms = round(score_ms + _ms(time.perf_counter() - t_score), 2)

        fetched_ids = [entry[5].memory_id for entry in fetched_top]
        fetched_id_set = set(fetched_ids)
        new_count = len(fetched_ids)  # all new by SQL exclusion
        fruitless = decision.fired and new_count == 0

        # --- efficacy booleans (§11 comparators, ruled with the build) ----
        novelty_outscored: bool | None = None
        if gate.GATE_SIGNAL_NOVELTY in decision.signals and loaded_scored:
            min_loaded = min(entry[0] for entry in loaded_scored)
            novelty_outscored = bool(fetched_top) and fetched_top[0][0] > min_loaded
        entity_covered: bool | None = None
        if gate.GATE_SIGNAL_ENTITY in decision.signals:
            uncovered_terms = {
                term.lower()
                for comp in uncovered
                for term in (comp["canonical"], *(comp.get("aliases") or []))
            }
            entities_by_id = {
                gr.row.memory_id: gr.entities or [] for gr in fetched_rows
            }
            entity_covered = any(
                entity.lower() in uncovered_terms
                for memory_id in fetched_ids
                for entity in entities_by_id.get(memory_id, [])
            )

        # --- serve (the reconstruction stage; fork 5: the pre-serve
        # callback rides only gated turns — a blocking MID-SCENE serve is
        # the signal; the wrapper records it either way) -------------------
        blocked = False

        def _pre_serve() -> None:
            nonlocal blocked
            blocked = True
            if on_reconstruct is not None:
                on_reconstruct()

        serve_input = _sort_scored(loaded_scored + fetched_top)
        outcome = await self._reconstruction.serve(
            request=request,
            config=config,
            seed_identity=seed_identity,
            scored_top=serve_input,
            as_of=as_of,
            on_reconstruct=_pre_serve,
        )
        # Mark this turn's appends (fork 1: the caller appends these IDs to
        # its loaded set). Marking rides retrieval, not serve — the serving
        # stage never learns the flag.
        if fetched_id_set:
            for item in outcome.items:
                if item.memory_id in fetched_id_set:
                    item.gate_fetched = True

        gate_inst = GateInstrumentation(
            evaluated=True,
            fired=decision.fired,
            signals_fired=decision.signals,
            degraded_rung=decision.rung,
            novelty_min_distance=min_distance,
            null_embedding_loaded_count=null_count,
            loaded_missing_count=max(loaded_missing, 0),
            uncovered_entities=[comp["canonical"] for comp in uncovered],
            fetched_memory_ids=fetched_ids,
            fetched_new_count=new_count,
            fruitless=fruitless,
            damper_active=damper_active,
            novelty_outscored=novelty_outscored,
            entity_covered=entity_covered,
            gate_ms=gate_ms,
            reconstructing_blocked=blocked,
        )
        candidate_count = len(loaded_rows) + len(fetched_rows)
        return sql_ms, score_ms, candidate_count, gate_inst, outcome
