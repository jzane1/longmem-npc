"""Set P — purge, the sole sanctioned content DELETE
(docs\\test-suite.md; the C6 rulings 2026-08-18 — per-memory scope, the DELETE
verb, no guard, NO migration). Structural-only per tests\\CLAUDE.md: row
presence/absence and the honest per-table counts, never prose.

The seam is `db.purge_memory` / `IngestService.purge_memory` (behind
DELETE /v1/memories/{memory_id}). Every scenario seeds a full-chain memory at
the db layer (no write pass — unmarked, no NLP loaders), then proves the purge
erases exactly that memory's seven tables and nothing else: a co-resident
memory, the agent, its identity components, and a reflection whose
source_memory_ids still names the purged memory (dangling by design — purge
honesty, migration-01.md:132) all survive. The `scene` fixture truncates
between tests, so counts here are exact, not id-scoped like the walker's.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from conftest import NOW, V1_CONFIG, run_structural

from app import db
from app.ingest import UnknownMemoryError

# The six memory-child tables the purge clears before the memories row.
CHILD_TABLES = (
    "memory_details",
    "memory_fact_versions",
    "memory_gist_spans",
    "corrections",
    "reconstruction_cache",
    "memory_enrichment_runs",
)

# Per-memory row counts after a seed + _add_children: the two insert_observation
# heads each gain a superseding partner, and one row lands in every other table.
EXPECTED = {
    "memory_details": 2,
    "memory_fact_versions": 2,
    "memory_gist_spans": 1,
    "corrections": 1,
    "reconstruction_cache": 1,
    "memory_enrichment_runs": 1,
}


async def _add_children(ctx, memory_id, component_id) -> None:
    """One extra row in every purge-scoped child table beyond the
    insert_observation heads: a superseding detail + fact head, a gist span
    bound to a surviving identity_component, a corrections record, an enrichment
    run, and a cache row. Post-condition counts are EXPECTED."""
    async with ctx.pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO memory_gist_spans (memory_id, start_char, end_char, "
            "matched_component_id) VALUES (%s, 0, 5, %s)",
            (memory_id, component_id),
        )
        # Seeded superseded (invalid_at set) so insert_observation's original
        # stays the SOLE live head — the one-live-head partial unique index on
        # memory_details / memory_fact_versions forbids a second live head.
        await cur.execute(
            "INSERT INTO memory_details (memory_id, content, write_cause, "
            "valid_at, invalid_at) VALUES (%s, %s, 'authorial_correction', %s, %s) "
            "RETURNING detail_id",
            (memory_id, "[set-p] corrected telling", NOW, NOW),
        )
        detail_id = (await cur.fetchone())[0]
        await cur.execute(
            "INSERT INTO memory_fact_versions (memory_id, basis_text, "
            "write_cause, valid_at, invalid_at) "
            "VALUES (%s, %s, 'authorial_correction', %s, %s)",
            (memory_id, "[set-p] corrected basis", NOW, NOW),
        )
        await cur.execute(
            "INSERT INTO corrections (memory_id, detail_id, verb, valid_at) "
            "VALUES (%s, %s, 'rationalization', %s)",
            (memory_id, detail_id, NOW),
        )
        await cur.execute(
            "INSERT INTO memory_enrichment_runs (memory_id, attempt, outcome) "
            "VALUES (%s, 1, 'completed')",
            (memory_id,),
        )
        await cur.execute(
            "INSERT INTO reconstruction_cache (memory_id, identity_version, "
            "rendered_text) VALUES (%s, %s, %s)",
            (memory_id, "v-set-p", "[set-p] cached render"),
        )


async def _scoped_counts(ctx, memory_id) -> dict:
    out = {}
    for t in ("memories",) + CHILD_TABLES:
        row = await ctx.fetchrow(
            f"SELECT count(*) FROM {t} WHERE memory_id = %s", memory_id
        )
        out[t] = row[0]
    return out


async def _seed_full_memory(ctx, agent_id, text: str):
    component = await ctx.add_component(agent_id, f"crossing-{text[:6]}")
    out = await ctx.seed(agent_id, text, NOW)
    await _add_children(ctx, out.memory_id, component)
    return out.memory_id, component


def test_purge_seeds_then_erases_every_table(scene):
    async def scenario(ctx):
        agent = await ctx.make_agent("purge-erase", V1_CONFIG)
        memory_id, _ = await _seed_full_memory(ctx, agent, "the lantern shattered")
        assert await _scoped_counts(ctx, memory_id) == {"memories": 1, **EXPECTED}
        outcome = await db.purge_memory(ctx.pool, memory_id)
        assert outcome is not None
        post = await _scoped_counts(ctx, memory_id)
        assert all(v == 0 for v in post.values()), post

    run_structural(scene, scenario)


def test_purge_returns_honest_per_table_counts(scene):
    async def scenario(ctx):
        agent = await ctx.make_agent("purge-counts", V1_CONFIG)
        memory_id, _ = await _seed_full_memory(ctx, agent, "a cart crossed at dawn")
        outcome = await db.purge_memory(ctx.pool, memory_id)
        assert outcome.memory_id == memory_id
        assert outcome.details_deleted == EXPECTED["memory_details"]
        assert outcome.fact_versions_deleted == EXPECTED["memory_fact_versions"]
        assert outcome.gist_spans_deleted == EXPECTED["memory_gist_spans"]
        assert outcome.corrections_deleted == EXPECTED["corrections"]
        assert outcome.cache_rows_evicted == EXPECTED["reconstruction_cache"]
        assert outcome.enrichment_runs_deleted == EXPECTED["memory_enrichment_runs"]

    run_structural(scene, scenario)


def test_purge_leaves_a_co_resident_memory_untouched(scene):
    async def scenario(ctx):
        agent = await ctx.make_agent("purge-coresident", V1_CONFIG)
        target, _ = await _seed_full_memory(ctx, agent, "the target memory")
        control, _ = await _seed_full_memory(ctx, agent, "the control memory")
        await db.purge_memory(ctx.pool, target)
        assert all(v == 0 for v in (await _scoped_counts(ctx, target)).values())
        assert await _scoped_counts(ctx, control) == {"memories": 1, **EXPECTED}

    run_structural(scene, scenario)


def test_purge_leaves_agent_and_identity_intact(scene):
    async def scenario(ctx):
        agent = await ctx.make_agent("purge-agent", V1_CONFIG)
        memory_id, _ = await _seed_full_memory(ctx, agent, "a lantern at the ford")
        before = (
            await ctx.fetchrow(
                "SELECT count(*) FROM identity_components WHERE agent_id = %s", agent
            )
        )[0]
        await db.purge_memory(ctx.pool, memory_id)
        agent_row = await ctx.fetchrow(
            "SELECT count(*) FROM agents WHERE agent_id = %s", agent
        )
        after = (
            await ctx.fetchrow(
                "SELECT count(*) FROM identity_components WHERE agent_id = %s", agent
            )
        )[0]
        assert agent_row[0] == 1
        # the component whose only referencing gist span was purged still stands
        assert after == before and before >= 1

    run_structural(scene, scenario)


def test_reflection_survives_purge_with_dangling_provenance(scene):
    async def scenario(ctx):
        agent = await ctx.make_agent("purge-reflection", V1_CONFIG)
        target, _ = await _seed_full_memory(ctx, agent, "the purged episode")
        control, _ = await _seed_full_memory(ctx, agent, "a surviving episode")
        reflection = await ctx.seed_reflection(
            agent, "a derived belief", NOW, source_memory_ids=(target, control)
        )
        await db.purge_memory(ctx.pool, target)
        row = await ctx.fetchrow(
            "SELECT source_memory_ids FROM reflections WHERE reflection_id = %s",
            reflection,
        )
        assert row is not None, "the derived reflection must survive the purge"
        # provenance is intentionally un-FK'd: the purged id still dangles here
        assert target in row[0] and control in row[0]

    run_structural(scene, scenario)


def test_purge_unknown_memory_returns_none_and_deletes_nothing(scene):
    async def scenario(ctx):
        agent = await ctx.make_agent("purge-unknown", V1_CONFIG)
        bystander, _ = await _seed_full_memory(ctx, agent, "an untouched memory")
        result = await db.purge_memory(ctx.pool, uuid4())
        assert result is None
        # the unknown-id purge is a pure no-op: the bystander keeps every row
        assert await _scoped_counts(ctx, bystander) == {"memories": 1, **EXPECTED}

    run_structural(scene, scenario)


def test_service_purge_returns_result_and_raises_on_unknown(scene):
    async def scenario(ctx):
        agent = await ctx.make_agent("purge-service", V1_CONFIG)
        memory_id, _ = await _seed_full_memory(ctx, agent, "a service-layer purge")
        svc = ctx.ingest()
        result = await svc.purge_memory(memory_id)
        assert result.memory_id == memory_id
        assert result.details_deleted == EXPECTED["memory_details"]
        assert result.fact_versions_deleted == EXPECTED["memory_fact_versions"]
        assert result.gist_spans_deleted == EXPECTED["memory_gist_spans"]
        assert result.corrections_deleted == EXPECTED["corrections"]
        assert result.cache_rows_evicted == EXPECTED["reconstruction_cache"]
        assert result.enrichment_runs_deleted == EXPECTED["memory_enrichment_runs"]
        assert result.total_ms >= 0.0
        assert all(v == 0 for v in (await _scoped_counts(ctx, memory_id)).values())
        with pytest.raises(UnknownMemoryError):
            await svc.purge_memory(uuid4())

    run_structural(scene, scenario)
