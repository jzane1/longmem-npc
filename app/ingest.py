"""ingest.py — THE ingest service: the write path's single instrumented seam.

Both callers (the FastAPI route and, later, the CLI harness) sit on this
module; neither duplicates the timing or token accounting recorded here
(CLAUDE.md: instrument at the seam).

Pipeline per observe event (write-path.md §pipeline):
  NLP pass -> single Haiku write call -> (escalation when triggered) ->
  embedding -> atomic insert -> IngestResult.

Degradation ladder (write):
  soft — the write always lands:
    - write-call failure / malformed output -> neutral importance +
      scoring_failed = true (+ default typology when undeclared; the head
      content falls back to the raw observation text since no render exists);
    - unknown decay_class label -> default class + decay_class_unknown = true;
    - embedding failure -> NULL embedding on the `original` FACT head
      (embedding_failed in the payload; the queryable signal moved to the
      fact head with the 2026-07-18 freeze ruling — observe no longer writes
      memories.embedding at all).
  hard — build-phase stance, re-rule before the demo (2026-07-13):
    - escalation failure: retry once, then HARD-STOP with nothing inserted
      (the insert happens after escalation, so no rows exist to roll back;
      a client resend is safe pre-idempotency).

The authorial correction (fact-following since the fact-level build,
fact-level-correction.md) is the deliberate CONTRAST: all-or-nothing,
fail-loud — an embed failure there writes nothing (CorrectionEmbedFailedError
-> 502), because the operator surface has no soft paths and a NULL corrected
embedding would make the memory vanish from the vector probe.
"""

from __future__ import annotations

import asyncio
import time
from uuid import UUID

from psycopg_pool import AsyncConnectionPool

from app import db, identity, nlp
from app.config import Settings, agent_knob
from app.db import InsertPlan, SpanPlan
from app.providers import (
    EscalationResult,
    GistSpanCandidate,
    MalformedOutputError,
    NewComponent,
    ProviderCallError,
    Providers,
    WriteCallResult,
)
from app.schemas import (
    AffectOut,
    CorrectionRequest,
    CorrectionResult,
    IngestResult,
    Instrumentation,
    ObserveEvent,
    PinResult,
    SceneBoundaryEvent,
    SceneResult,
)

# Sentinel decay class when the agent's config supplies neither a map entry
# nor a default label: the write is never rejected, only flagged unknown.
DECAY_CLASS_SENTINEL = "unclassified"
TYPOLOGY_FALLBACK = "observed"  # overridable per agent: config key "typology_default"


class UnknownAgentError(LookupError):
    """The event references an agent_id with no agents row."""


class UnknownMemoryError(LookupError):
    """set_pin / correct references a memory_id with no memories row."""


class CorrectionConflictError(RuntimeError):
    """The correction's expected_detail_id no longer names the live head —
    the operator's read is stale; nothing was changed (409, never a silent
    retry against a telling the operator did not see)."""


class CorrectionEmbedFailedError(RuntimeError):
    """The correction's embed call failed: nothing was written on either
    chain (all-or-nothing, ruled 2026-07-18 — the embed runs BEFORE the
    transaction opens). 502 at the route, the escalation-hard-stop precedent;
    the operator retries."""


class CorrectionNlpFailedError(RuntimeError):
    """The correction's NER pass failed (broken/missing spaCy install):
    nothing was written — the NER runs before the embed, before the
    transaction (fail-loud, ruled 2026-07-19 with the gate build; the embed
    precedent's shape). 502 at the route; the operator fixes the environment
    and retries."""


def _ms(seconds: float) -> float:
    return round(seconds * 1000.0, 2)


def _resolve_decay_class(label: str | None, config: dict) -> tuple[str, bool]:
    """Validate against the agent's decay-class map (never reject)."""
    decay_map = config.get("decay_classes") or {}
    default_label = config.get("decay_class_default")
    if label is not None and label in decay_map:
        return label, False
    if label is not None:  # supplied but unknown -> default + flag
        return (default_label or DECAY_CLASS_SENTINEL), True
    if default_label is not None:  # omitted -> default, not an unknown label
        return default_label, False
    return DECAY_CLASS_SENTINEL, True


def _merge_spans(
    base: list[GistSpanCandidate], extra: list[GistSpanCandidate]
) -> list[GistSpanCandidate]:
    merged = list(base)
    seen = {
        (s.start_char, s.end_char, s.matched_component_id, s.matched_category)
        for s in base
    }
    for span in extra:
        key = (
            span.start_char,
            span.end_char,
            span.matched_component_id,
            span.matched_category,
        )
        if key not in seen:
            seen.add(key)
            merged.append(span)
    return merged


def _merge_components(
    base: list[NewComponent], extra: list[NewComponent]
) -> list[NewComponent]:
    merged = list(base)
    seen = {c.canonical.lower() for c in base}
    for comp in extra:
        if comp.canonical.lower() not in seen:
            seen.add(comp.canonical.lower())
            merged.append(comp)
    return merged


class IngestService:
    """One instance per process; both callers share it."""

    def __init__(
        self, pool: AsyncConnectionPool, providers: Providers, settings: Settings
    ):
        self._pool = pool
        self._providers = providers
        self._settings = settings

    # ------------------------------------------------------------------ #
    # observe
    # ------------------------------------------------------------------ #

    async def ingest_observation(self, event: ObserveEvent) -> IngestResult:
        t_total = time.perf_counter()

        agent = await db.fetch_agent(self._pool, event.agent_id)
        if agent is None:
            raise UnknownAgentError(f"unknown agent_id {event.agent_id}")
        config: dict = agent["config"]
        components = await db.fetch_live_components(self._pool, event.agent_id)

        # --- NLP pass (no LLM) ------------------------------------------
        t0 = time.perf_counter()
        nlp_result = await asyncio.to_thread(
            nlp.run_write_pass, event.observation_text, components
        )
        nlp_ms = _ms(time.perf_counter() - t0)

        # --- single Haiku write call (soft degradation) ------------------
        t0 = time.perf_counter()
        scoring_failed = False
        haiku_in = haiku_out = 0
        rendered_content = event.observation_text  # fallback head when no render exists
        importance = agent_knob(config, "importance_neutral", self._settings)
        call_typology: str | None = None
        call_confidence: float | None = None
        try:
            write_result: WriteCallResult = await asyncio.to_thread(
                self._providers.write.render_and_score,
                observation_text=event.observation_text,
                diagnosticity_goal=agent["diagnosticity_goal"] or "",
                declared_typology=event.typology,
            )
            rendered_content = write_result.rendered_content
            importance = write_result.importance_raw
            call_typology = write_result.typology
            call_confidence = write_result.typology_confidence
            haiku_in = write_result.input_tokens
            haiku_out = write_result.output_tokens
        except ProviderCallError:
            scoring_failed = True
        except MalformedOutputError as exc:
            scoring_failed = True
            haiku_in = exc.input_tokens
            haiku_out = exc.output_tokens
        haiku_ms = _ms(time.perf_counter() - t0)

        # --- typology: client declaration wins ---------------------------
        if event.typology is not None:
            typology = event.typology
            typology_source = "declared"
            typology_confidence = (
                event.typology_confidence
                if event.typology_confidence is not None
                else agent_knob(config, "typology_confidence_default", self._settings)
            )
        elif call_typology is not None:
            typology = call_typology
            typology_source = "inferred"
            typology_confidence = (
                call_confidence
                if call_confidence is not None
                else agent_knob(config, "typology_confidence_default", self._settings)
            )
        else:  # write call degraded and nothing declared: default, flagged by
            # scoring_failed above — never a lost write.
            typology = str(config.get("typology_default", TYPOLOGY_FALLBACK))
            typology_source = "inferred"
            typology_confidence = agent_knob(
                config, "typology_confidence_default", self._settings
            )

        # --- escalation (biased loose; hard-stop on double failure) ------
        knobs = {
            key: agent_knob(config, key, self._settings)
            for key in (
                "escalation_importance_threshold",
                "escalation_affect_threshold",
                "escalation_min_base_spans",
                "nlp_confidence_threshold",
            )
        }
        triggers = nlp.evaluate_triggers(nlp_result, importance, knobs)
        spans = list(nlp_result.spans)
        new_components = list(nlp_result.novel_components)
        escalation_ms = 0.0
        esc_in = esc_out = 0
        escalation_failed = False
        if triggers:
            t0 = time.perf_counter()
            escalation = await self._escalate_with_retry(
                event, components, nlp_result, triggers
            )
            escalation_ms = _ms(time.perf_counter() - t0)
            if escalation is None:
                # Soft-degrade (ruled 2026-07-22): the gist-escalation call
                # failed twice; proceed with the base NLP-pass spans/components
                # (no merge) and flag it. A degraded gist is never a lost write.
                escalation_failed = True
            else:
                esc_in = escalation.input_tokens
                esc_out = escalation.output_tokens
                spans = _merge_spans(spans, escalation.spans)
                new_components = _merge_components(
                    new_components, escalation.new_components
                )

        # --- embedding (soft degradation: NULL embedding) -----------------
        t0 = time.perf_counter()
        embedding: list[float] | None = None
        location_embedding: list[float] | None = None
        embedding_failed = False
        embed_tokens = 0
        location_text = event.location_description or event.location_name
        texts = [event.observation_text] + ([location_text] if location_text else [])
        try:
            embed_result = await asyncio.to_thread(
                self._providers.embedding.embed, texts
            )
            embedding = embed_result.vectors[0]
            if location_text:
                location_embedding = embed_result.vectors[1]
            embed_tokens = embed_result.tokens
        except ProviderCallError:
            embedding_failed = True
        embed_ms = _ms(time.perf_counter() - t0)

        # --- assemble facts -----------------------------------------------
        decay_class, decay_class_unknown = _resolve_decay_class(
            event.decay_class, config
        )

        valence = nlp_result.affect_valence
        arousal = nlp_result.affect_arousal
        affect_detail = nlp_result.affect_detail
        if event.affect is not None:  # client override wins per field
            if event.affect.valence is not None:
                valence = event.affect.valence
            if event.affect.arousal is not None:
                arousal = event.affect.arousal
            if event.affect.detail is not None:
                affect_detail = {**(affect_detail or {}), "client": event.affect.detail}

        entities: list[str] = []
        for name in [*nlp_result.entities, *(event.entities or [])]:
            if name and name.lower() not in {e.lower() for e in entities}:
                entities.append(name)

        span_plans = self._plan_spans(event.observation_text, spans, new_components)

        # --- atomic insert -------------------------------------------------
        t0 = time.perf_counter()
        outcome = await db.insert_observation(
            self._pool,
            InsertPlan(
                agent_id=event.agent_id,
                observation_text=event.observation_text,
                rendered_content=rendered_content,
                valid_at=event.client_timestamp,
                importance_raw=importance,
                scoring_failed=scoring_failed,
                escalation_failed=escalation_failed,
                typology=typology,
                typology_confidence=typology_confidence,
                typology_source=typology_source,
                provenance=event.provenance,
                pinned=event.pinned,
                decay_class=decay_class,
                decay_class_unknown=decay_class_unknown,
                embedding=embedding,
                location_name=event.location_name,
                location_embedding=location_embedding,
                entities=entities or None,
                event_time=event.event_time,
                affect_valence=valence,
                affect_arousal=arousal,
                affect_detail=affect_detail,
                new_components=new_components,
                spans=span_plans,
            ),
        )
        insert_ms = _ms(time.perf_counter() - t0)

        return IngestResult(
            memory_id=outcome.memory_id,
            detail_id=outcome.detail_id,
            fact_version_id=outcome.fact_version_id,
            gist_span_ids=outcome.gist_span_ids,
            new_component_ids=outcome.new_component_ids,
            importance_raw=importance,
            typology=typology,
            typology_confidence=typology_confidence,
            typology_source=typology_source,
            provenance=event.provenance,
            affect=AffectOut(valence=valence, arousal=arousal, detail=affect_detail),
            entities=entities,
            decay_class=decay_class,
            decay_class_unknown=decay_class_unknown,
            scoring_failed=scoring_failed,
            escalation_failed=escalation_failed,
            embedding_failed=embedding_failed,
            pinned=event.pinned,
            instrumentation=Instrumentation(
                nlp_ms=nlp_ms,
                embed_ms=embed_ms,
                haiku_ms=haiku_ms,
                insert_ms=insert_ms,
                total_ms=_ms(time.perf_counter() - t_total),
                haiku_input_tokens=haiku_in,
                haiku_output_tokens=haiku_out,
                embedding_tokens=embed_tokens,
                escalated=bool(triggers),
                escalated_by=triggers,
                escalation_ms=escalation_ms,
                escalation_input_tokens=esc_in,
                escalation_output_tokens=esc_out,
            ),
        )

    async def _escalate_with_retry(
        self,
        event: ObserveEvent,
        components: list[dict],
        nlp_result: nlp.NlpResult,
        triggers: list[str],
    ) -> EscalationResult | None:
        """Retry once; on a second failure return None so the write soft-degrades
        to the base NLP-pass gist (ruled 2026-07-22 — the fail-loud hard-stop was
        a temporary build-phase stance; a failed escalation must not halt a live
        write). The degraded gist is flagged (escalation_failed) rather than
        aborting the write."""
        for _attempt in (1, 2):
            try:
                return await asyncio.to_thread(
                    self._providers.escalation.extract_gist,
                    observation_text=event.observation_text,
                    known_components=components,
                    candidate_spans=list(nlp_result.spans),
                    candidate_components=list(nlp_result.novel_components),
                    triggers=triggers,
                )
            except (ProviderCallError, MalformedOutputError):
                continue
        return None

    @staticmethod
    def _plan_spans(
        observation_text: str,
        spans: list[GistSpanCandidate],
        new_components: list[NewComponent],
    ) -> list[SpanPlan]:
        """Convert candidates to insert-ready plans; novel-entity mentions become
        spans referencing the component row created in the same transaction."""
        plans = [
            SpanPlan(
                start_char=s.start_char,
                end_char=s.end_char,
                component_ref=s.matched_component_id,
                matched_category=s.matched_category,
            )
            for s in spans
        ]
        occupied = {(p.start_char, p.end_char) for p in plans}
        for index, comp in enumerate(new_components):
            for start, end in nlp._find_term_spans(observation_text, comp.canonical):
                if (start, end) not in occupied:
                    occupied.add((start, end))
                    plans.append(
                        SpanPlan(
                            start_char=start,
                            end_char=end,
                            component_ref=index,
                            matched_category=comp.category,
                        )
                    )
        return plans

    # ------------------------------------------------------------------ #
    # scene boundary — accept + instrument only (v1)
    # ------------------------------------------------------------------ #

    async def scene_boundary(self, event: SceneBoundaryEvent) -> SceneResult:
        """Scene edge. Since the reconstruction build (2026-07-17) this
        handler carries its first server-side consumer: the identity-document
        recompile (render seed prose -> content hash -> upsert), returning
        identity_version for the caller to freeze as scene state (the hybrid
        plumbing ruling; the reputation snapshot stays caller-side in the
        session-runner, and the prompt-head rebuild remains post-August)."""
        t_total = time.perf_counter()
        agent = await db.fetch_agent(self._pool, event.agent_id)
        if agent is None:
            raise UnknownAgentError(f"unknown agent_id {event.agent_id}")
        version, _rendered, created = await identity.ensure_identity_document(
            self._pool, event.agent_id, agent["seed_identity"]
        )
        return SceneResult(
            agent_id=event.agent_id,
            accepted=True,
            total_ms=_ms(time.perf_counter() - t_total),
            identity_version=version,
            identity_document_new=created,
        )

    # ------------------------------------------------------------------ #
    # pin / unpin
    # ------------------------------------------------------------------ #

    async def set_pin(self, memory_id: UUID, pinned: bool) -> PinResult:
        t_total = time.perf_counter()
        updated = await db.set_pinned(self._pool, memory_id, pinned)
        if not updated:
            raise UnknownMemoryError(f"unknown memory_id {memory_id}")
        return PinResult(
            memory_id=memory_id,
            pinned=pinned,
            total_ms=_ms(time.perf_counter() - t_total),
        )

    # ------------------------------------------------------------------ #
    # authorial correction — the operator's replace-model fix
    # ------------------------------------------------------------------ #

    async def correct(
        self, memory_id: UUID, request: CorrectionRequest
    ) -> CorrectionResult:
        """Authorial correction (authorial-correction.md; fact-following
        since the fact-level build, fact-level-correction.md): the operator's
        text byte-verbatim into BOTH chains — the corrected telling head and
        the corrected fact row with its re-derived embedding AND re-derived
        entities (fork 3, 2026-07-19: mechanical NER over the corrected text
        merged with the optional operator field, the observe-path merge
        mirrored) — in one supersede-guarded transaction with cache eviction.
        The NER and embed calls run BEFORE the transaction (never a network
        call inside one); each failure is all-or-nothing fail-loud: nothing
        written, CorrectionNlpFailedError / CorrectionEmbedFailedError -> 502,
        the operator retries. The operator surface has no soft paths."""
        t_total = time.perf_counter()
        if not request.content.strip():
            raise ValueError("corrected content must be non-empty")
        t0 = time.perf_counter()
        try:
            ner_entities = await asyncio.to_thread(
                nlp.extract_entities, request.content
            )
        except Exception as exc:  # noqa: BLE001 — any NLP-stack failure is the same operator story
            raise CorrectionNlpFailedError(
                f"correction NER failed for {memory_id}; nothing was "
                f"written — fix the NLP install and retry: {exc}"
            ) from exc
        nlp_ms = _ms(time.perf_counter() - t0)
        # The observe-path merge, byte-for-byte (ingest_observation): NER
        # first, then operator-supplied, case-insensitive dedup.
        entities: list[str] = []
        for name in [*ner_entities, *(request.entities or [])]:
            if name and name.lower() not in {e.lower() for e in entities}:
                entities.append(name)
        t0 = time.perf_counter()
        try:
            embed_result = await asyncio.to_thread(
                self._providers.embedding.embed, [request.content]
            )
        except ProviderCallError as exc:
            raise CorrectionEmbedFailedError(
                f"correction embed failed for {memory_id}; nothing was "
                f"written — retry: {exc}"
            ) from exc
        embed_ms = _ms(time.perf_counter() - t0)
        outcome = await db.apply_authorial_correction(
            self._pool,
            memory_id=memory_id,
            content=request.content,
            valid_at=request.client_timestamp,
            embedding=embed_result.vectors[0],
            entities=entities or None,
            expected_detail_id=request.expected_detail_id,
        )
        if outcome == "unknown_memory":
            raise UnknownMemoryError(f"unknown memory_id {memory_id}")
        if outcome == "stale_head":
            raise CorrectionConflictError(
                f"live head moved for {memory_id}; re-read and re-issue"
            )
        return CorrectionResult(
            memory_id=memory_id,
            detail_id=outcome.detail_id,
            superseded_detail_id=outcome.superseded_detail_id,
            fact_version_id=outcome.fact_version_id,
            superseded_fact_version_id=outcome.superseded_fact_version_id,
            evicted_cache_rows=outcome.evicted_cache_rows,
            entities=entities,
            embed_ms=embed_ms,
            embedding_tokens=embed_result.tokens,
            nlp_ms=nlp_ms,
            total_ms=_ms(time.perf_counter() - t_total),
        )
