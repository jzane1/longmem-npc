"""schemas.py — ingestion + retrieval API v1 wire models (docs\\write-path.md,
docs\\read-path.md).

The FastAPI routes are pass-throughs: for one call, the route's JSON is
exactly the serialized result the service returned (`IngestResult` /
`RetrievalResult`). These models are therefore both the wire shape and the
service return shape.

Structural notes tied to the frozen migration-01 schema:
- `phase_tag` and `event_id` are accepted but have no schema home in v1
  (passthrough / idempotency-not-enforced per the spec); they are not stored
  and not echoed in results.
- `location_description`, when supplied, is embed-only (no raw column).
- `embedding_failed` reflects the 2026-07-13 ruling that an embedding-call
  failure lands the write with a NULL embedding (`embedding IS NULL` is the
  queryable signal; this field is its payload mirror).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

Typology = Literal["observed", "told", "inferred", "reflected"]
Provenance = Literal["lived", "injected"]


class AffectOverride(BaseModel):
    """Optional client-supplied affect; overrides the lexicon pass per field."""

    valence: float | None = Field(default=None, ge=-1.0, le=1.0)
    arousal: float | None = Field(default=None, ge=0.0, le=1.0)
    detail: dict | None = None


class ObserveEvent(BaseModel):
    """The core `observe` event (write-path.md event contract)."""

    agent_id: UUID
    observation_text: str = Field(min_length=1)
    phase_tag: str  # integrator vocabulary; passthrough, not interpreted in v1
    client_timestamp: datetime  # world time -> valid_at; must be tz-aware
    provenance: Provenance
    typology: Typology | None = None  # client declaration wins when present
    typology_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    decay_class: str | None = None  # validated against the agent's config map
    location_name: str | None = None
    location_description: str | None = None  # embed-only; no raw column
    entities: list[str] | None = None
    event_time: datetime | None = None
    affect: AffectOverride | None = None
    pinned: bool = False
    event_id: str | None = None  # idempotency key: accepted, not enforced in v1

    @field_validator("client_timestamp", "event_time")
    @classmethod
    def _tz_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class SceneBoundaryEvent(BaseModel):
    """Scene edge: accepted + instrumented only in v1; all consumers deferred."""

    agent_id: UUID
    client_timestamp: datetime
    scene_type: str | None = None  # integrator vocabulary; passthrough
    event_id: str | None = None

    @field_validator("client_timestamp")
    @classmethod
    def _tz_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class PinRequest(BaseModel):
    """Body of PUT /v1/memories/{memory_id}/pin."""

    pinned: bool


class AffectOut(BaseModel):
    """Stored affect facts (valence/arousal columns + jsonb detail)."""

    valence: float | None
    arousal: float | None
    detail: dict | None


class Instrumentation(BaseModel):
    """Per-stage timing + token accounting, recorded once at the seam.

    All timings and Haiku token counts are non-null (done-when 8). Escalation
    fields stay at their zero-values when no escalation fired.
    """

    nlp_ms: float
    embed_ms: float
    haiku_ms: float
    insert_ms: float
    total_ms: float
    haiku_input_tokens: int
    haiku_output_tokens: int
    embedding_tokens: int
    escalated: bool = False
    escalated_by: list[str] = Field(default_factory=list)
    escalation_ms: float = 0.0
    escalation_input_tokens: int = 0
    escalation_output_tokens: int = 0


class IngestResult(BaseModel):
    """Structured return of `ingest_observation` — IDs + computed facts.

    Surfaced verbatim by the route and the CLI debug view; the suite asserts
    on this structure, never on prose.
    """

    # Identifiers
    memory_id: UUID
    detail_id: UUID  # the `original` head
    gist_span_ids: list[UUID]
    new_component_ids: list[UUID]
    # Computed facts / scores
    importance_raw: float
    typology: Typology
    typology_confidence: float
    typology_source: Literal["declared", "inferred"]
    provenance: Provenance
    affect: AffectOut
    entities: list[str]
    decay_class: str
    decay_class_unknown: bool
    scoring_failed: bool
    embedding_failed: bool
    pinned: bool
    # Instrumentation
    instrumentation: Instrumentation


class SceneResult(BaseModel):
    """Accept + instrument only (v1): no schema is written."""

    agent_id: UUID
    accepted: bool
    total_ms: float


class PinResult(BaseModel):
    """Result of toggling memories.pinned."""

    memory_id: UUID
    pinned: bool
    total_ms: float


# ---------------------------------------------------------------------------
# Read path — dialogue-init retrieval (docs\read-path.md, built rulings
# 2026-07-14)
# ---------------------------------------------------------------------------


class WeightOverrides(BaseModel):
    """RESERVED (ruled 2026-07-14): per-call split-brain scoring multipliers.

    Accepted and shape-validated, NOT consumed by v1 scoring, not echoed.
    Becomes live with the post-August split-brain topology.
    """

    relevance: float | None = None
    recency: float | None = None
    importance: float | None = None


class DialogueInitRequest(BaseModel):
    """Dialogue-init retrieval request (read-path.md request contract).

    `query_text` is embedded AS-IS (ruled 2026-07-14: the integrator authors
    the probe; the service never composes prose). `location_name`/`entities`/
    `event_time` are RESERVED slots for the post-August encoding-context term:
    accepted + shape-validated, not consumed, not echoed. Affect is
    deliberately NOT reserved (ruled 2026-07-14) — its query-side shape
    arrives with the encoding-context term. `as_of` is the world-time
    override for age computation (Set B / time-travel surface).
    """

    agent_id: UUID
    query_text: str = Field(min_length=1)
    k: int | None = Field(default=None, ge=1)
    location_name: str | None = None  # RESERVED — inert in v1
    entities: list[str] | None = None  # RESERVED — inert in v1
    event_time: datetime | None = None  # RESERVED — inert in v1
    weight_overrides: WeightOverrides | None = None  # RESERVED — inert in v1
    as_of: datetime | None = None  # defaults to server now (UTC)

    @field_validator("event_time", "as_of")
    @classmethod
    def _tz_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class RetrievedMemory(BaseModel):
    """One ranked item: IDs + scores alongside prose (load-bearing — the test
    suite asserts on this structure, never on prose)."""

    memory_id: UUID
    detail_id: UUID  # the served live head (Set A's corrected-head surface)
    content: str  # the live head's text, verbatim (v1 serving ruling)
    read_mode: Literal["verbatim"]  # widens when reconstruction lands (item 1)
    pinned: bool
    score: float  # relevance x recency x importance_norm
    relevance: float | None  # null on the degraded (no-vector) path
    recency: float
    importance_norm: float
    importance_raw: float  # the debug view's raw axis (as fed to the formula)


class RetrievalInstrumentation(BaseModel):
    """Per-stage timing + token accounting, recorded once at the seam.

    Feeds architecture §11's latency decomposition; surfaced verbatim in the
    CLI debug view. `degraded` mirrors the ruled fail-quiet embedding
    fallback; `as_of_effective` is the age-computation timestamp actually
    used.
    """

    embed_ms: float
    sql_ms: float
    score_ms: float
    total_ms: float
    embedding_tokens: int
    candidate_count: int
    k_effective: int
    degraded: bool = False
    degraded_reason: str | None = None
    as_of_effective: datetime


class RetrievalResult(BaseModel):
    """Structured return of `retrieve_dialogue_init`; the route serves it
    verbatim (route-is-pass-through). Reserved request fields are never
    echoed here."""

    items: list[RetrievedMemory]  # ranked, <= k
    instrumentation: RetrievalInstrumentation


# ---------------------------------------------------------------------------
# Dialogue turn — the CLI-harness seam (docs\cli-harness.md, build rulings
# 2026-07-15). No HTTP route consumes these in v1 — the REPL and the load
# driver call the seam in-process; Pydantic by ruling, mirroring the
# write/read payloads (the Unity route will reuse them).
# ---------------------------------------------------------------------------


class ActionDirective(BaseModel):
    """One emitted action: free `type` from the integrator-supplied vocabulary
    plus a free params object (architecture §9). Written as observed world
    fact so the contract survives the split-brain migration unchanged."""

    type: str
    params: dict = Field(default_factory=dict)


class DialogueTurnRequest(BaseModel):
    """One dialogue turn (cli-harness.md request contract).

    Scene state lives in the caller: `reputation_snapshot` is the scene-start
    value the caller froze at the last scene boundary — a required explicit
    field (build ruling 2026-07-15) so "snapshot frozen within a scene" is a
    property of the seam contract. `action_vocabulary` per-call wins over
    `agents.config["action_vocabulary"]`; with neither configured, every
    emitted directive is dropped (never a hardcoded default vocabulary).
    `k` / `as_of` pass through to retrieval unreinterpreted; `debug` is a
    caller-side rendering hint, inert to the seam's computation.
    """

    agent_id: UUID
    utterance: str = Field(min_length=1)
    reputation_snapshot: float
    reputation_delta_override: float | None = None  # client override wins (§9)
    action_vocabulary: list[str] | None = None
    k: int | None = Field(default=None, ge=1)
    as_of: datetime | None = None
    debug: bool = False

    @field_validator("as_of")
    @classmethod
    def _tz_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class DialogueTurnInstrumentation(BaseModel):
    """Per-turn timing + token accounting, recorded once at the seam.

    Feeds architecture §11's latency histogram (no gate term in the slice)
    and the per-100-turn cost table. Token counts are unconditional;
    `cost_usd` is populated only when LONGMEM_PRICE_* env vars are set
    (build ruling 2026-07-15 — no hardcoded model pricing), covering the
    dialogue call plus the priced share of the query embedding.
    """

    retrieval: RetrievalInstrumentation
    sonnet_ms: float
    sonnet_first_token_ms: float
    apply_ms: float  # the reputation UPDATE
    total_ms: float
    sonnet_input_tokens: int
    sonnet_output_tokens: int
    cost_usd: float | None = None
    degraded: bool = False  # the never-blank path was taken
    degraded_reason: str | None = None


class DialogueTurnResult(BaseModel):
    """Structured return of `run_dialogue_turn` — surfaced verbatim in the
    CLI debug view; the suite asserts on this structure, never on prose.

    `content` is the only unassertable field. `reputation_after` equals the
    persisted `agents.reputation` scalar; `reputation_delta` is the delta
    actually applied (pre-sensitivity), with `reputation_delta_source`
    making override-wins and the zeroed degradation paths assertable.
    """

    agent_id: UUID
    content: str
    directive: ActionDirective | None
    directive_dropped: bool = False
    directive_dropped_reason: str | None = None
    reputation_snapshot: float  # what the prompt actually saw
    reputation_prev: float  # row value the apply started from
    reputation_delta: float
    reputation_delta_source: Literal["model", "override", "zeroed"]
    reputation_sensitivity: float
    reputation_after: float
    items: list[RetrievedMemory]  # retrieval echo: IDs + scores invariant
    instrumentation: DialogueTurnInstrumentation
