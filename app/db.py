"""db.py — async connection pool + hand-written SQL for the write and read paths.

psycopg v3 with AsyncConnectionPool (stack constant; no ORM, no query
builder). The observe insert is ONE transaction: memories row + `original`
memory_details head + memory_gist_spans + any new identity_components land
together or not at all (write-path.md §pipeline step d). Nothing here ever
UPDATEs stored content or DELETEs rows; the only in-place writes are the two
agent-row runtime scalars — `set_pinned` (`memories.pinned`, write-path v1)
and `apply_reputation_delta` (`agents.reputation`, CLI-harness build ruling
2026-07-15) — both outside the memory-content non-destructive invariant.

Read-path candidate queries (read-path.md, 2026-07-14) are read-only: live
memories (`memories.invalid_at IS NULL`) joined to the unique live detail
head (`memory_details.invalid_at IS NULL`; uniqueness guaranteed by the
one-live-head index). Invalidation excludes rows here, in SQL — decay never
does (the two mechanisms stay distinct).

Reconstruction (reconstruction.md, built 2026-07-17) writes through
`write_back_reconstruction`: ONE transaction that supersedes the prior head
(sets invalid_at — ordinary non-destructive supersession, never an UPDATE of
content), inserts the new `reconstruction` head, and inserts the cache row —
the serve-only-persisted-text rule rides on this atomicity. The cache tables'
only writers live in the reconstruction path (the eviction invariant's
precondition); `upsert_identity_document` is insert-if-absent (versions are
content-addressed and immutable once written).
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
            "SELECT agent_id, diagnosticity_goal, config, seed_identity "
            "FROM agents WHERE agent_id = %s",
            (agent_id,),
        )
        row = await cur.fetchone()
    if row is None:
        return None
    return {
        "agent_id": row[0],
        "diagnosticity_goal": row[1],
        "config": row[2] or {},
        "seed_identity": row[3],
    }


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
    """One live memory joined to its live detail head, as retrieval reads it.
    `write_cause` (added at the reconstruction build) feeds read-mode honesty:
    a served head that is itself a reconstruction row reads as such."""

    memory_id: UUID
    detail_id: UUID
    content: str
    importance_raw: float | None
    pinned: bool
    decay_class: str | None
    valid_at: datetime
    write_cause: str
    distance: float | None = None  # cosine distance; None on the degraded path


_CANDIDATE_COLUMNS = (
    "m.memory_id, d.detail_id, d.content, m.importance_raw, m.pinned, "
    "m.decay_class, m.valid_at, d.write_cause"
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


@dataclass(frozen=True)
class DialogueAgentState:
    """The agent facts the dialogue turn consumes (cli-harness.md): seed
    identity prose for the prompt prefix, the reputation runtime scalars, and
    config for knob resolution. Numeric columns arrive as float, not Decimal."""

    agent_id: UUID
    seed_identity: str | None
    reputation: float | None  # NULL = never set; neutral is a config knob
    reputation_sensitivity: float | None  # NULL -> config default
    config: dict


async def fetch_dialogue_agent_state(
    pool: AsyncConnectionPool, agent_id: UUID
) -> DialogueAgentState | None:
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "SELECT agent_id, seed_identity, reputation, reputation_sensitivity, "
            "config FROM agents WHERE agent_id = %s",
            (agent_id,),
        )
        row = await cur.fetchone()
    if row is None:
        return None
    return DialogueAgentState(
        agent_id=row[0],
        seed_identity=row[1],
        reputation=float(row[2]) if row[2] is not None else None,
        reputation_sensitivity=float(row[3]) if row[3] is not None else None,
        config=row[4] or {},
    )


async def apply_reputation_delta(
    pool: AsyncConnectionPool,
    agent_id: UUID,
    *,
    addend: float,
    neutral: float,
    scale_min: float,
    scale_max: float,
) -> tuple[float, float] | None:
    """Apply one turn's reputation change in a single atomic statement
    (cli-harness build ruling 2026-07-15):

        reputation = clamp(COALESCE(reputation, neutral) + addend, min, max)

    `addend` is sensitivity x delta, computed by the seam. An in-place UPDATE
    of an agent-row runtime scalar — deliberately outside the memory-content
    non-destructive invariant (same class as `set_pinned`). Returns
    (prev_effective, after) as floats, or None when the agent is unknown.
    The clamp lives in SQL so the value can never leave the scale, even under
    concurrent turns.
    """
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "UPDATE agents a "
            "SET reputation = GREATEST(%s::numeric, LEAST(%s::numeric, "
            "COALESCE(a.reputation, %s::numeric) + %s::numeric)) "
            "FROM (SELECT agent_id, reputation FROM agents "
            "      WHERE agent_id = %s FOR UPDATE) old "
            "WHERE a.agent_id = old.agent_id "
            "RETURNING COALESCE(old.reputation, %s::numeric), a.reputation",
            (scale_min, scale_max, neutral, addend, agent_id, neutral),
        )
        row = await cur.fetchone()
    if row is None:
        return None
    return float(row[0]), float(row[1])


# ---------------------------------------------------------------------------
# Reconstruction (reconstruction.md, built 2026-07-17): identity documents,
# the (memory_id x composed-key) cache, retelling sources, and the write-back.
# ---------------------------------------------------------------------------


async def upsert_identity_document(
    pool: AsyncConnectionPool, agent_id: UUID, rendered_text: str, identity_version: str
) -> bool:
    """Insert-if-absent (versions are content-addressed and immutable once
    written). Returns True when this call created the row."""
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO identity_documents (agent_id, rendered_text, "
            "identity_version) VALUES (%s, %s, %s) "
            "ON CONFLICT (agent_id, identity_version) DO NOTHING",
            (agent_id, rendered_text, identity_version),
        )
        return cur.rowcount == 1


async def fetch_identity_document(
    pool: AsyncConnectionPool, agent_id: UUID, identity_version: str
) -> str | None:
    """rendered_text for a caller-passed version; None = unknown version
    (a loud contract error at the seam, never a silent fallback)."""
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "SELECT rendered_text FROM identity_documents "
            "WHERE agent_id = %s AND identity_version = %s",
            (agent_id, identity_version),
        )
        row = await cur.fetchone()
    return row[0] if row is not None else None


async def fetch_cache_rows(
    pool: AsyncConnectionPool, pairs: list[tuple[UUID, str]]
) -> dict[tuple[UUID, str], str]:
    """Batched cache lookup: {(memory_id, composed_key): rendered_text}. The
    stored identity_version column carries the composed reconstruction key
    (identity_version + decay band — spec ruling 2026-07-17)."""
    if not pairs:
        return {}
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "SELECT c.memory_id, c.identity_version, c.rendered_text "
            "FROM reconstruction_cache c "
            "JOIN unnest(%s::uuid[], %s::text[]) AS t(memory_id, identity_version) "
            "ON c.memory_id = t.memory_id "
            "AND c.identity_version = t.identity_version",
            ([m for m, _ in pairs], [k for _, k in pairs]),
        )
        rows = await cur.fetchall()
    return {(row[0], row[1]): row[2] for row in rows}


async def insert_cache_row(
    pool: AsyncConnectionPool, memory_id: UUID, composed_key: str, rendered_text: str
) -> None:
    """Refusal caching (spec ruling 2026-07-17): the served prior-head text is
    cached under the current key so subsequent same-key reads are stable and
    call-free. No chain write rides with this one."""
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO reconstruction_cache (memory_id, identity_version, "
            "rendered_text) VALUES (%s, %s, %s) "
            "ON CONFLICT (memory_id, identity_version) DO NOTHING",
            (memory_id, composed_key, rendered_text),
        )


@dataclass(frozen=True)
class ReconstructionSource:
    """Per-memory retelling inputs: the immutable observation text, ordered
    gist span offsets, and the drift anchor's content (the latest chain row
    whose write_cause is in the anchor set — derivable, no pointer)."""

    observation_text: str
    spans: list[tuple[int, int]]
    anchor_content: str


async def fetch_reconstruction_sources(
    pool: AsyncConnectionPool, memory_ids: list[UUID]
) -> dict[UUID, ReconstructionSource]:
    if not memory_ids:
        return {}
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "SELECT memory_id, observation_text FROM memories "
            "WHERE memory_id = ANY(%s)",
            (memory_ids,),
        )
        texts = {row[0]: row[1] for row in await cur.fetchall()}
        await cur.execute(
            "SELECT memory_id, start_char, end_char FROM memory_gist_spans "
            "WHERE memory_id = ANY(%s) ORDER BY memory_id, start_char, end_char",
            (memory_ids,),
        )
        spans: dict[UUID, list[tuple[int, int]]] = {}
        for row in await cur.fetchall():
            spans.setdefault(row[0], []).append((row[1], row[2]))
        # The drift anchor: latest chain row with an anchoring write_cause
        # (original | authorial_correction | update_with_resentment);
        # rationalization and reconstruction rows never re-anchor.
        await cur.execute(
            "SELECT DISTINCT ON (memory_id) memory_id, content "
            "FROM memory_details WHERE memory_id = ANY(%s) "
            "AND write_cause IN "
            "('original', 'authorial_correction', 'update_with_resentment') "
            "ORDER BY memory_id, created_at DESC",
            (memory_ids,),
        )
        anchors = {row[0]: row[1] for row in await cur.fetchall()}
    return {
        memory_id: ReconstructionSource(
            observation_text=texts[memory_id],
            spans=spans.get(memory_id, []),
            anchor_content=anchors[memory_id],
        )
        for memory_id in texts
        if memory_id in anchors
    }


async def write_back_reconstruction(
    pool: AsyncConnectionPool,
    *,
    memory_id: UUID,
    prior_detail_id: UUID,
    content: str,
    basis: datetime,
    composed_key: str,
) -> UUID | None:
    """The retelling write-back: ONE transaction — supersede the prior head at
    the scene basis (world time; ordinary non-destructive supersession),
    insert the new `reconstruction` head (valid_at = the same basis, so the
    chain timeline is coherent under as_of time travel), and insert the cache
    row. Serve-only-persisted-text rides on this atomicity. Returns the new
    detail_id, or None when the prior head was already superseded (a
    concurrent writer won; nothing is changed)."""
    async with pool.connection() as conn:
        async with conn.transaction():
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE memory_details SET invalid_at = %s "
                    "WHERE detail_id = %s AND invalid_at IS NULL",
                    (basis, prior_detail_id),
                )
                if cur.rowcount != 1:
                    return None
                await cur.execute(
                    "INSERT INTO memory_details (memory_id, content, write_cause, "
                    "valid_at) VALUES (%s, %s, 'reconstruction', %s) "
                    "RETURNING detail_id",
                    (memory_id, content, basis),
                )
                detail_id = (await cur.fetchone())[0]
                await cur.execute(
                    "INSERT INTO reconstruction_cache (memory_id, identity_version, "
                    "rendered_text) VALUES (%s, %s, %s) "
                    "ON CONFLICT (memory_id, identity_version) DO NOTHING",
                    (memory_id, composed_key, content),
                )
    return detail_id
