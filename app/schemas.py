"""schemas.py — ingestion API v1 wire models (docs\\write-path.md).

The FastAPI routes are pass-throughs: for one ingest, the route's JSON is
exactly the serialized `IngestResult` the service returned. These models are
therefore both the wire shape and the service return shape.

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
