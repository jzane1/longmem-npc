"""db.py — async connection pool + hand-written SQL for the write and read paths.

psycopg v3 with AsyncConnectionPool (stack constant; no ORM, no query
builder). The observe insert is ONE transaction: memories row + `original`
memory_details head + `original` memory_fact_versions head (migration 002,
fact-level-correction.md) + memory_gist_spans + any new identity_components
land together or not at all (write-path.md §pipeline step d). Nothing here
ever UPDATEs stored content; the only in-place writes are the two agent-row
runtime scalars — `set_pinned` (`memories.pinned`, write-path v1) and
`apply_reputation_delta` (`agents.reputation`, CLI-harness build ruling
2026-07-15) — both outside the memory-content non-destructive invariant. The
only DELETE is `apply_authorial_correction`'s cache eviction — derived rows,
not memory content (the standing eviction invariant, authorial-correction.md).

Two chains under one memory_id since migration 002: the telling chain
(memory_details) and the fact chain (memory_fact_versions — basis text +
embedding). Freeze ruling (2026-07-18): observe no longer writes
memories.embedding; the fact head is the sole vector home for post-002 rows,
and `memory_fact_versions.embedding IS NULL` on the live head is the
queryable embed-degradation signal (the 2026-07-13 signal, moved homes).

Read-path candidate queries (read-path.md, 2026-07-14) are read-only: live
memories (`memories.invalid_at IS NULL`) joined to the unique live detail
head (`memory_details.invalid_at IS NULL`; uniqueness guaranteed by the
one-live-head index) — and, for the vector probe, to the unique live fact
head, whose embedding the `<=>` distance reads (fact-level-correction.md:
retrieval follows the fix through this join). Invalidation excludes rows
here, in SQL — decay never does (the two mechanisms stay distinct).

Reconstruction (reconstruction.md, built 2026-07-17) writes through
`write_back_reconstruction`: ONE transaction that supersedes the prior head
(sets invalid_at — ordinary non-destructive supersession, never an UPDATE of
content), inserts the new `reconstruction` head, and inserts the cache row —
the serve-only-persisted-text rule rides on this atomicity. The cache tables'
only writers live in the reconstruction path (the eviction invariant's
precondition); any other chain writer evicts — `apply_authorial_correction`
(authorial-correction.md) supersedes the live head with the operator's text
byte-verbatim and deletes every cache row for that memory in the same
transaction. `upsert_identity_document` is insert-if-absent (versions are
content-addressed and immutable once written).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
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
    fact_version_id: UUID  # the `original` fact head (migration 002)
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

                # 2. the memories row — write-time facts. The observation
                # embedding is NOT written here (freeze ruling 2026-07-18),
                # and neither is entities (freeze ruling 2026-07-19, the same
                # precedent): both live on the `original` fact head below.
                # memories.entities is frozen — pre-003 rows keep their
                # values; post-003 rows carry NULL here forever.
                await cur.execute(
                    "INSERT INTO memories (agent_id, observation_text, "
                    "importance_raw, scoring_failed, typology, typology_confidence, "
                    "typology_source, provenance, pinned, decay_class, "
                    "decay_class_unknown, valid_at, location_name, location_embedding, "
                    "event_time, affect_valence, affect_arousal, affect_detail) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                    "%s, %s, %s, %s) RETURNING memory_id",
                    (
                        plan.agent_id,
                        plan.observation_text,
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

                # 4. the `original` fact head (migration 002) — the semantic
                # basis retrieval ranks by: observation_text byte-verbatim +
                # the observation embedding (NULL = embed-failure degradation;
                # the queryable signal lives here since the freeze ruling) +
                # entities (migration 003, freeze ruling 2026-07-19 — the
                # gate's coverage/lexical basis, moved by corrections).
                await cur.execute(
                    "INSERT INTO memory_fact_versions (memory_id, basis_text, "
                    "embedding, entities, write_cause, valid_at) "
                    "VALUES (%s, %s, %s, %s, 'original', %s) RETURNING fact_version_id",
                    (
                        memory_id,
                        plan.observation_text,
                        _vector(plan.embedding),
                        plan.entities,
                        plan.valid_at,
                    ),
                )
                fact_version_id = (await cur.fetchone())[0]

                # 5. gist spans — offsets into the immutable observation_text
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
        fact_version_id=fact_version_id,
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
# The vector probe additionally joins the live FACT head — the embedding the
# <=> distance reads (fact-level-correction.md: retrieval follows the fix).
# `fv.invalid_at IS NULL` is stated verbatim so the planner matches the
# partial-HNSW predicate on memory_fact_versions.
#
# NAMED params (%(agent_id)s, not %s): the vector-probe queries below reference
# the 1536-dim query vector TWICE (SELECT distance + ORDER BY, the HNSW-index
# form). Positional %s sends that ~6 KB param on the wire once per placeholder;
# two large params cross a segment boundary into a ~44 ms Windows-loopback
# Nagle/delayed-ACK stall (server executes the query in ~1.3 ms). A named param
# is sent ONCE, referenced twice in SQL — measured 44 ms -> 1 ms per read, with
# the HNSW `ORDER BY embedding <=> ...` expression unchanged. So every consumer
# of this clause binds by name (all-named or all-positional, never mixed).
_VECTOR_CANDIDATE_FROM = (
    "FROM memories m JOIN memory_details d "
    "ON d.memory_id = m.memory_id AND d.invalid_at IS NULL "
    "JOIN memory_fact_versions fv "
    "ON fv.memory_id = m.memory_id AND fv.invalid_at IS NULL "
    "WHERE m.agent_id = %(agent_id)s AND m.invalid_at IS NULL"
)


async def fetch_vector_candidates(
    pool: AsyncConnectionPool, agent_id: UUID, embedding: list[float], limit: int
) -> list[CandidateRow]:
    """Over-fetched vector probe: live rows with live-fact-head embeddings,
    nearest first (partial HNSW cosine on memory_fact_versions). NULL-fact-
    embedding rows are unreachable here by design — the write path's ruled
    degradation consequence, its signal on the fact head since the freeze
    ruling; they stay reachable on the degraded path below and via the gate's
    GIN path later."""
    vec = _vector(embedding)
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            f"SELECT {_CANDIDATE_COLUMNS}, fv.embedding <=> %(qv)s AS distance "
            f"{_VECTOR_CANDIDATE_FROM} AND fv.embedding IS NOT NULL "
            "ORDER BY fv.embedding <=> %(qv)s LIMIT %(lim)s",
            {"qv": vec, "agent_id": agent_id, "lim": limit},
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


@dataclass(frozen=True)
class GateRow:
    """A candidate row plus its live fact head's gate-relevant facts
    (mid-dialogue-gate.md, built 2026-07-19). `embedding` rides only on the
    loaded-set fetch (the novelty basis; NULL = the embed-degradation row,
    excluded from the basis and counted); `entities` rides on all three gate
    fetchers (the coverage basis and the entity-covered efficacy check)."""

    row: CandidateRow
    embedding: list[float] | None
    entities: list[str] | None


async def fetch_loaded_set(
    pool: AsyncConnectionPool, agent_id: UUID, memory_ids: list[UUID]
) -> list[GateRow]:
    """The gate's keyed fetch of the caller-held loaded set (fork 1,
    2026-07-19): live rows joined to their live fact heads, by ID. Unknown,
    foreign, or invalidated IDs simply don't join — the live-head predicates
    are the filter; the service counts the drop-outs. NULL fact-head
    embeddings ride (they stay in the coverage basis and closed-gate serving,
    out of the novelty basis)."""
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            f"SELECT {_CANDIDATE_COLUMNS}, fv.embedding, fv.entities "
            f"{_VECTOR_CANDIDATE_FROM} AND m.memory_id = ANY(%(ids)s)",
            {"agent_id": agent_id, "ids": memory_ids},
        )
        rows = await cur.fetchall()
    return [
        GateRow(
            row=CandidateRow(*row[:8]),
            embedding=row[8].to_list() if row[8] is not None else None,
            entities=row[9],
        )
        for row in rows
    ]


async def fetch_gate_candidates(
    pool: AsyncConnectionPool,
    agent_id: UUID,
    embedding: list[float],
    limit: int,
    exclude_ids: list[UUID],
) -> list[GateRow]:
    """The gate's fire probe: the standard over-fetched vector probe with the
    loaded set excluded (append-only — a fetch never re-returns what the
    scene already holds) and the fact head's entities alongside (the
    entity-covered efficacy check reads them)."""
    vec = _vector(embedding)
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            f"SELECT {_CANDIDATE_COLUMNS}, fv.embedding <=> %(qv)s AS distance, "
            f"fv.entities {_VECTOR_CANDIDATE_FROM} AND fv.embedding IS NOT NULL "
            "AND NOT (m.memory_id = ANY(%(exclude)s)) "
            "ORDER BY fv.embedding <=> %(qv)s LIMIT %(lim)s",
            {"qv": vec, "agent_id": agent_id, "exclude": exclude_ids, "lim": limit},
        )
        rows = await cur.fetchall()
    return [
        GateRow(row=CandidateRow(*row[:9]), embedding=None, entities=row[9])
        for row in rows
    ]


async def fetch_entity_candidates(
    pool: AsyncConnectionPool,
    agent_id: UUID,
    terms: list[str],
    exclude_ids: list[UUID],
) -> list[GateRow]:
    """The gate ladder's entity-only rung (embeddings down): lexical fetch
    off the partial GIN over live fact heads — `fv.invalid_at IS NULL` is
    stated in the FROM verbatim so the planner matches the partial-index
    predicate (the 002 precedent). No LIMIT: the service ranks by
    recency x importance_norm in Python (the fetch_live_candidates
    precedent). The && overlap is byte-exact against stored entity strings —
    an accepted degraded-rung property (build ruling 2026-07-19)."""
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            f"SELECT {_CANDIDATE_COLUMNS}, fv.entities "
            f"{_VECTOR_CANDIDATE_FROM} AND fv.entities && %(terms)s::text[] "
            "AND NOT (m.memory_id = ANY(%(exclude)s))",
            {"agent_id": agent_id, "terms": terms, "exclude": exclude_ids},
        )
        rows = await cur.fetchall()
    return [
        GateRow(row=CandidateRow(*row[:8]), embedding=None, entities=row[8])
        for row in rows
    ]


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
    gist span offsets, and the drift anchor's content and cause (the latest
    chain row whose write_cause is in the anchor set — derivable, no
    pointer). The cause drives the constraint: on `authorial_correction`-
    anchored chains the corrected head replaces the gist constraint (ruled
    2026-07-17, authorial-correction.md)."""

    observation_text: str
    spans: list[tuple[int, int]]
    anchor_content: str
    anchor_cause: str


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
            "SELECT DISTINCT ON (memory_id) memory_id, content, write_cause "
            "FROM memory_details WHERE memory_id = ANY(%s) "
            "AND write_cause IN "
            "('original', 'authorial_correction', 'update_with_resentment') "
            "ORDER BY memory_id, created_at DESC",
            (memory_ids,),
        )
        anchors = {row[0]: (row[1], row[2]) for row in await cur.fetchall()}
    return {
        memory_id: ReconstructionSource(
            observation_text=texts[memory_id],
            spans=spans.get(memory_id, []),
            anchor_content=anchors[memory_id][0],
            anchor_cause=anchors[memory_id][1],
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


@dataclass(frozen=True)
class CorrectionApplied:
    """Row-level outcome of `apply_authorial_correction` — both chains'
    head swaps (fact fields since the fact-level build, 2026-07-18)."""

    detail_id: UUID
    superseded_detail_id: UUID
    fact_version_id: UUID
    superseded_fact_version_id: UUID
    evicted_cache_rows: int


class _StaleHeadError(Exception):
    """Internal: aborts (rolls back) the correction transaction on a failed
    compare-and-swap; surfaced to the caller as the "stale_head" outcome."""


async def apply_authorial_correction(
    pool: AsyncConnectionPool,
    *,
    memory_id: UUID,
    content: str,
    valid_at: datetime,
    embedding: list[float],
    entities: list[str] | None = None,
    expected_detail_id: UUID | None = None,
) -> CorrectionApplied | Literal["unknown_memory", "stale_head"]:
    """The operator's replace-model correction (authorial-correction.md;
    fact-following since the fact-level build, fact-level-correction.md): ONE
    transaction — supersede the live telling head at the correction's world
    time, insert the corrected `authorial_correction` head (valid_at = the
    same instant; the coherent-chain-timeline precedent), supersede the live
    fact head and insert the corrected fact row (basis_text byte-verbatim +
    the pre-computed embedding — the caller embeds BEFORE this transaction;
    no network call rides inside it — + the corrected entities since
    migration 003: the NER + operator-field merge, computed by the caller,
    so corrections move entities the way they move the embedding), and evict
    every cache row for the
    memory (the standing eviction invariant). `content` is the operator's
    text byte-verbatim in both chains. With `expected_detail_id` the telling
    supersede is a compare-and-swap: a head that moved since the operator
    read it reports "stale_head" and changes nothing — the fact supersede
    needs no CAS of its own (this verb is the fact chain's only post-observe
    writer, and the telling-head CAS already serializes racing corrections).
    "unknown_memory" = no live telling head, which by the one-live-head
    construction means no such memory."""
    try:
        async with pool.connection() as conn:
            async with conn.transaction():
                async with conn.cursor() as cur:
                    await cur.execute(
                        "UPDATE memory_details SET invalid_at = %s "
                        "WHERE memory_id = %s AND invalid_at IS NULL "
                        "RETURNING detail_id",
                        (valid_at, memory_id),
                    )
                    row = await cur.fetchone()
                    if row is None:
                        return "unknown_memory"
                    superseded = row[0]
                    if (
                        expected_detail_id is not None
                        and superseded != expected_detail_id
                    ):
                        raise _StaleHeadError
                    await cur.execute(
                        "INSERT INTO memory_details (memory_id, content, "
                        "write_cause, valid_at) VALUES "
                        "(%s, %s, 'authorial_correction', %s) "
                        "RETURNING detail_id",
                        (memory_id, content, valid_at),
                    )
                    detail_id = (await cur.fetchone())[0]
                    await cur.execute(
                        "UPDATE memory_fact_versions SET invalid_at = %s "
                        "WHERE memory_id = %s AND invalid_at IS NULL "
                        "RETURNING fact_version_id",
                        (valid_at, memory_id),
                    )
                    fact_row = await cur.fetchone()
                    if fact_row is None:
                        # Post-002 invariant: every memory carries exactly one
                        # live fact head (observe mints it; the backfill
                        # guarantees pre-002 rows). Absence is a broken store,
                        # not an operator error — fail loud, roll back.
                        raise RuntimeError(
                            f"no live fact head for {memory_id}; the store "
                            "violates the one-live-fact-head invariant"
                        )
                    superseded_fact = fact_row[0]
                    await cur.execute(
                        "INSERT INTO memory_fact_versions (memory_id, "
                        "basis_text, embedding, entities, write_cause, valid_at) "
                        "VALUES (%s, %s, %s, %s, 'authorial_correction', %s) "
                        "RETURNING fact_version_id",
                        (memory_id, content, _vector(embedding), entities, valid_at),
                    )
                    fact_version_id = (await cur.fetchone())[0]
                    await cur.execute(
                        "DELETE FROM reconstruction_cache WHERE memory_id = %s",
                        (memory_id,),
                    )
                    evicted = cur.rowcount
    except _StaleHeadError:
        return "stale_head"
    return CorrectionApplied(
        detail_id=detail_id,
        superseded_detail_id=superseded,
        fact_version_id=fact_version_id,
        superseded_fact_version_id=superseded_fact,
        evicted_cache_rows=evicted,
    )
