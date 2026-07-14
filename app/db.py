"""db.py — async connection pool + hand-written SQL for the write and read paths.

psycopg v3 with AsyncConnectionPool (stack constant; no ORM, no query
builder). The observe insert is ONE transaction: memories row + `original`
memory_details head + memory_gist_spans + any new identity_components land
together or not at all (write-path.md §pipeline step d). Nothing here ever
UPDATEs stored content or DELETEs rows; `set_pin` flips the runtime `pinned`
flag only.

Read-path candidate queries (read-path.md, 2026-07-14) are read-only: live
memories (`memories.invalid_at IS NULL`) joined to the unique live detail
head (`memory_details.invalid_at IS NULL`; uniqueness guaranteed by the
one-live-head index). Invalidation excludes rows here, in SQL — decay never
does (the two mechanisms stay distinct).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from pgvector.psycopg import register_vector_async
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from app.providers import NewComponent


async def _configure(conn) -> None:
    await register_vector_async(conn)


def build_pool(database_uri: str) -> AsyncConnectionPool:
    """Pool is opened by the caller (await pool.open()) so startup is explicit."""
    return AsyncConnectionPool(
        database_uri, configure=_configure, open=False, min_size=1, max_size=8
    )


async def fetch_agent(pool: AsyncConnectionPool, agent_id: UUID) -> dict | None:
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "SELECT agent_id, diagnosticity_goal, config FROM agents WHERE agent_id = %s",
            (agent_id,),
        )
        row = await cur.fetchone()
    if row is None:
        return None
    return {"agent_id": row[0], "diagnosticity_goal": row[1], "config": row[2] or {}}


async def fetch_live_components(
    pool: AsyncConnectionPool, agent_id: UUID
) -> list[dict]:
    """The agent's live identity components (invalid_at IS NULL)."""
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "SELECT component_id, canonical, aliases, category FROM identity_components "
            "WHERE agent_id = %s AND invalid_at IS NULL",
            (agent_id,),
        )
        rows = await cur.fetchall()
    return [
        {
            "component_id": r[0],
            "canonical": r[1],
            "aliases": r[2] or [],
            "category": r[3],
        }
        for r in rows
    ]


@dataclass
class SpanPlan:
    """A gist span ready for insert. component_ref is a UUID string for an
    existing component, an int index into InsertPlan.new_components for a
    component created in this same transaction, or None (category-only hit)."""

    start_char: int
    end_char: int
    component_ref: str | int | None
    matched_category: str | None


@dataclass
class InsertPlan:
    """Everything the atomic observe insert writes — all write-time facts."""

    agent_id: UUID
    observation_text: str
    rendered_content: str  # the `original` detail head (render seam ruling)
    valid_at: datetime
    importance_raw: float
    scoring_failed: bool
    typology: str
    typology_confidence: float
    typology_source: str
    provenance: str
    pinned: bool
    decay_class: str
    decay_class_unknown: bool
    embedding: list[float] | None  # None = embedding-failure degradation
    location_name: str | None = None
    location_embedding: list[float] | None = None
    entities: list[str] | None = None
    event_time: datetime | None = None
    affect_valence: float | None = None
    affect_arousal: float | None = None
    affect_detail: dict | None = None
    new_components: list[NewComponent] = field(default_factory=list)
    spans: list[SpanPlan] = field(default_factory=list)


@dataclass(frozen=True)
class InsertOutcome:
    memory_id: UUID
    detail_id: UUID
    gist_span_ids: list[UUID]
    new_component_ids: list[UUID]


def _vector(values: list[float] | None):
    if values is None:
        return None
    from pgvector import Vector

    return Vector(values)


async def insert_observation(
    pool: AsyncConnectionPool, plan: InsertPlan
) -> InsertOutcome:
    """The atomic insert: one transaction, never a partial write."""
    async with pool.connection() as conn:
        async with conn.transaction():
            async with conn.cursor() as cur:
                # 1. grow identity_components first so spans can reference them
                new_component_ids: list[UUID] = []
                for comp in plan.new_components:
                    await cur.execute(
                        "INSERT INTO identity_components (agent_id, canonical, aliases, "
                        "category) VALUES (%s, %s, %s, %s) RETURNING component_id",
                        (plan.agent_id, comp.canonical, comp.aliases, comp.category),
                    )
                    new_component_ids.append((await cur.fetchone())[0])

                # 2. the memories row — all write-time facts
                await cur.execute(
                    "INSERT INTO memories (agent_id, observation_text, embedding, "
                    "importance_raw, scoring_failed, typology, typology_confidence, "
                    "typology_source, provenance, pinned, decay_class, "
                    "decay_class_unknown, valid_at, location_name, location_embedding, "
                    "entities, event_time, affect_valence, affect_arousal, affect_detail) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                    "%s, %s, %s, %s, %s) RETURNING memory_id",
                    (
                        plan.agent_id,
                        plan.observation_text,
                        _vector(plan.embedding),
                        plan.importance_raw,
                        plan.scoring_failed,
                        plan.typology,
                        plan.typology_confidence,
                        plan.typology_source,
                        plan.provenance,
                        plan.pinned,
                        plan.decay_class,
                        plan.decay_class_unknown,
                        plan.valid_at,
                        plan.location_name,
                        _vector(plan.location_embedding),
                        plan.entities,
                        plan.event_time,
                        plan.affect_valence,
                        plan.affect_arousal,
                        Jsonb(plan.affect_detail)
                        if plan.affect_detail is not None
                        else None,
                    ),
                )
                memory_id = (await cur.fetchone())[0]

                # 3. the `original` detail head (write_cause = original)
                await cur.execute(
                    "INSERT INTO memory_details (memory_id, content, write_cause, valid_at) "
                    "VALUES (%s, %s, 'original', %s) RETURNING detail_id",
                    (memory_id, plan.rendered_content, plan.valid_at),
                )
                detail_id = (await cur.fetchone())[0]

                # 4. gist spans — offsets into the immutable observation_text
                gist_span_ids: list[UUID] = []
                for span in plan.spans:
                    if isinstance(span.component_ref, int):
                        component_id = new_component_ids[span.component_ref]
                    elif span.component_ref is not None:
                        component_id = UUID(span.component_ref)
                    else:
                        component_id = None
                    await cur.execute(
                        "INSERT INTO memory_gist_spans (memory_id, start_char, end_char, "
                        "matched_component_id, matched_category) "
                        "VALUES (%s, %s, %s, %s, %s) RETURNING span_id",
                        (
                            memory_id,
                            span.start_char,
                            span.end_char,
                            component_id,
                            span.matched_category,
                        ),
                    )
                    gist_span_ids.append((await cur.fetchone())[0])

    return InsertOutcome(
        memory_id=memory_id,
        detail_id=detail_id,
        gist_span_ids=gist_span_ids,
        new_component_ids=new_component_ids,
    )


@dataclass(frozen=True)
class CandidateRow:
    """One live memory joined to its live detail head, as retrieval reads it."""

    memory_id: UUID
    detail_id: UUID
    content: str
    importance_raw: float | None
    pinned: bool
    decay_class: str | None
    valid_at: datetime
    distance: float | None = None  # cosine distance; None on the degraded path


_CANDIDATE_COLUMNS = (
    "m.memory_id, d.detail_id, d.content, m.importance_raw, m.pinned, "
    "m.decay_class, m.valid_at"
)
_CANDIDATE_FROM = (
    "FROM memories m JOIN memory_details d "
    "ON d.memory_id = m.memory_id AND d.invalid_at IS NULL "
    "WHERE m.agent_id = %s AND m.invalid_at IS NULL"
)


async def fetch_vector_candidates(
    pool: AsyncConnectionPool, agent_id: UUID, embedding: list[float], limit: int
) -> list[CandidateRow]:
    """Over-fetched vector probe: live rows with embeddings, nearest first
    (HNSW cosine). NULL-embedding rows are unreachable here by design — the
    write path's ruled degradation consequence; they stay reachable on the
    degraded path below and via the gate's GIN path later."""
    vec = _vector(embedding)
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            f"SELECT {_CANDIDATE_COLUMNS}, m.embedding <=> %s AS distance "
            f"{_CANDIDATE_FROM} AND m.embedding IS NOT NULL "
            "ORDER BY m.embedding <=> %s LIMIT %s",
            (vec, agent_id, vec, limit),
        )
        rows = await cur.fetchall()
    return [CandidateRow(*row) for row in rows]


async def fetch_live_candidates(
    pool: AsyncConnectionPool, agent_id: UUID
) -> list[CandidateRow]:
    """Degraded-path candidates: every live memory, NULL embeddings included
    (ruled 2026-07-14: never-blank-a-dialogue). Unordered — the service ranks
    by recency x importance_norm."""
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(f"SELECT {_CANDIDATE_COLUMNS} {_CANDIDATE_FROM}", (agent_id,))
        rows = await cur.fetchall()
    return [CandidateRow(*row) for row in rows]


async def set_pinned(pool: AsyncConnectionPool, memory_id: UUID, pinned: bool) -> bool:
    """Flip the runtime pinned flag. Returns False when the memory is unknown."""
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "UPDATE memories SET pinned = %s WHERE memory_id = %s", (pinned, memory_id)
        )
        return cur.rowcount == 1
