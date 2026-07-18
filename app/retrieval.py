"""retrieval.py — THE retrieval service: the read path's single instrumented seam.

Both callers (the FastAPI route and, later, the CLI harness) sit on this
module; neither duplicates the timing or token accounting recorded here
(CLAUDE.md: instrument at the seam; surface mirrors the write path's
2026-07-13 ruling; spec: docs\\read-path.md, built 2026-07-14).

Pipeline per dialogue-init request:
  resolve agent + knobs -> embed the query probe (as-is) -> vector over-fetch
  -> score (relevance x recency x importance_norm; pin exemption) -> top-k
  -> SERVE via the reconstruction stage (app\\reconstruction.py, built
  2026-07-17): theta partition at the scene-frozen basis, cache keyed
  (memory_id, identity_version + decay band), batched retelling of the
  misses with drift-budgeted write-back, read_mode = "reconstructed" past
  theta — pinned and fresh rows serve their live heads verbatim.

Retrieval (candidates + scoring) and serving (text assembly + read-mode
stamping) are deliberately separate stages: the reconstruction build swapped
the SERVING stage only; retrieval and scoring are byte-for-byte the
read-path v1 logic, and scores are unchanged by the swap. Since that build
this seam WRITES on read (chain write-backs + cache rows) — architecture §7
mandates write-back on the read path; read-v1's read-only SQL was a scope
fact of verbatim-only serving, not a principle.

Degradation ladder (read, ruled 2026-07-14; reconstruction rows 2026-07-17):
  - query-embedding failure -> FAIL-QUIET fallback: rank ALL live candidates
    (NULL-embedding rows included) by recency x importance_norm; the item
    relevance component is null (none was computed); degraded = true +
    reason. The read analog of never-lose-a-write is never-blank-a-dialogue.
  - empty/short store -> 0..k items, never an error (a valid young-NPC state).
  - reconstruction-stage failures (call, drift embed, persistence) degrade
    soft per reconstruction.md's ladder: affected items serve their live
    heads with honest read_mode; degraded = true + reason.
"""

from __future__ import annotations

import asyncio
import math
import time
from datetime import datetime, timezone

from psycopg_pool import AsyncConnectionPool

from app import db, decay
from app.config import Settings, agent_knob
from app.ingest import UnknownAgentError
from app.providers import ProviderCallError, Providers
from app.reconstruction import ReconstructionService
from app.schemas import (
    DialogueInitRequest,
    RetrievalInstrumentation,
    RetrievalResult,
)


def _ms(seconds: float) -> float:
    return round(seconds * 1000.0, 2)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


class RetrievalService:
    """One instance per process; both callers share it."""

    def __init__(
        self, pool: AsyncConnectionPool, providers: Providers, settings: Settings
    ):
        self._pool = pool
        self._providers = providers
        self._settings = settings
        # The serving stage (reconstruction.md): constructed here so neither
        # caller (route, session-runner) changes its wiring.
        self._reconstruction = ReconstructionService(pool, providers, settings)

    async def retrieve_dialogue_init(
        self, request: DialogueInitRequest
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

        # --- query embedding (fail-quiet degradation) ---------------------
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

        # --- candidates ----------------------------------------------------
        t0 = time.perf_counter()
        if query_vector is not None:
            overfetch = agent_knob(config, "retrieval_overfetch_factor", self._settings)
            limit = max(k, math.ceil(overfetch * k))
            candidates = await db.fetch_vector_candidates(
                self._pool, request.agent_id, query_vector, limit
            )
        else:  # degraded: every live candidate, NULL embeddings included
            candidates = await db.fetch_live_candidates(self._pool, request.agent_id)
        sql_ms = _ms(time.perf_counter() - t0)

        # --- scoring ---------------------------------------------------------
        t0 = time.perf_counter()
        k_importance = agent_knob(config, "decay_k_importance", self._settings)
        floor = agent_knob(config, "importance_norm_floor", self._settings)
        neutral = agent_knob(config, "importance_neutral", self._settings)
        scored: list[
            tuple[float, float | None, float, float, float, db.CandidateRow]
        ] = []
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
            else:  # degraded path: no relevance was computed — honest null
                rel = None
                score = rec * imp
            scored.append((score, rel, rec, imp, raw, row))
        # Deterministic order: ties break on memory_id, so byte-identity
        # holds across identical calls (within-scene stability invariant).
        scored.sort(key=lambda entry: (-entry[0], entry[5].memory_id))
        top = scored[:k]
        score_ms = _ms(time.perf_counter() - t0)

        # --- serving: the reconstruction stage (reconstruction.md, built
        # 2026-07-17) — swapped in over verbatim-only v1; retrieval and
        # scoring above are untouched.
        outcome = await self._reconstruction.serve(
            request=request,
            config=config,
            seed_identity=agent["seed_identity"],
            scored_top=top,
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
                candidate_count=len(candidates),
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
            ),
        )
