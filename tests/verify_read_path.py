"""verify_read_path.py — structural done-when walker for read-path v1
(dialogue-init retrieval, docs\\read-path.md).

Runs read-path done-when criteria 1-11 against the SCRATCH database
(default: the .env DATABASE_URI with its database name swapped to
`longmem_test`), with deterministic fake providers — offline, keyless, and
structural-only per tests\\CLAUDE.md: assertions touch IDs, row shapes,
flags, score components, and byte-identity, never generated prose. Criterion
12 (schema frozen: `db\\migrate.py` no-arg is a clean no-op on `longmem`)
runs outside this walker.

Time travel here uses both ruled mechanics: injected `valid_at` timestamps
at seeding and the read path's `as_of` override (adopted 2026-07-14).

Seeding goes through the real IngestService (staged verification against the
write-path floor); fixture SQL is used only where the spec says so
(invalidation, chain supersession).

Prerequisite (PowerShell):
    python db\\migrate.py --database-uri <scratch-uri>
Run:
    python tests\\verify_read_path.py [--database-uri <scratch-uri>]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from psycopg.types.json import Jsonb

from app import api as api_module
from app.config import Settings
from app.db import build_pool
from app.ingest import IngestService
from app.providers import (
    FailingEmbeddingProvider,
    FakeEmbeddingProvider,
    FakeEscalationProvider,
    FakeWriteProvider,
    Providers,
)
from app.retrieval import RetrievalService
from app.schemas import (
    DialogueInitRequest,
    ObserveEvent,
    RetrievalResult,
    WeightOverrides,
)

NOW = datetime(2026, 7, 14, 12, 0, 0, tzinfo=timezone.utc)

AGENT_CONFIG = {
    "decay_classes": {"episodic": 86400, "semantic": 604800},
    "decay_class_default": "episodic",
}

# Seed corpus: text -> injected valid_at age. TWIN_* share one text so their
# embeddings, importances, and taus are identical; only `pinned` differs.
T_FRESH = "Mara sharpened my blade at the forge while John watched."
T_COIN = "A stranger paid in foreign coin at the market."
T_FIRE = "The forge fire went out during the storm."
T_ROAD = "I overheard talk of bandits on the north road."
T_TWIN = "The baron doubled the tax on iron."
T_TUNNEL = "A merchant whispered about a hidden tunnel under the keep."

PASSED: list[str] = []


def ok(criterion: str, detail: str = "") -> None:
    PASSED.append(criterion)
    print(f"  PASS  {criterion}" + (f"  ({detail})" if detail else ""))


def fail(criterion: str, detail: str) -> None:
    print(f"  FAIL  {criterion}: {detail}")
    sys.exit(1)


def check(condition: bool, criterion: str, detail: str = "") -> None:
    if not condition:
        fail(criterion, detail or "condition false")
    ok(criterion, detail)


def scratch_uri_from_env() -> str:
    from app.config import load_env

    parts = urlsplit(load_env()["DATABASE_URI"])
    return urlunsplit(parts._replace(path="/longmem_test"))


def fake_providers(**overrides) -> Providers:
    return Providers(
        write=overrides.get("write", FakeWriteProvider()),
        escalation=overrides.get("escalation", FakeEscalationProvider()),
        embedding=overrides.get("embedding", FakeEmbeddingProvider()),
    )


async def make_agent(pool, name: str, config: dict):
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO agents (name, seed_identity, reputation, rigidity, "
            "reputation_sensitivity, diagnosticity_goal, config) "
            "VALUES (%s, %s, 0, 1.0, 1.0, %s, %s) RETURNING agent_id",
            (name, "A verification NPC.", "what threatens the forge", Jsonb(config)),
        )
        agent_id = (await cur.fetchone())[0]
        await cur.execute(
            "INSERT INTO identity_components (agent_id, canonical, aliases, category) "
            "VALUES (%s, 'Mara', %s, 'person')",
            (agent_id, ["the blacksmith"]),
        )
    return agent_id


async def fetchrow(pool, sql: str, *params):
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(sql, params)
        return await cur.fetchone()


async def execute(pool, sql: str, *params) -> None:
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(sql, params)


async def seed(ingest: IngestService, agent_id, text: str, valid_at, **kw):
    """One observation through the real write path (the verified floor)."""
    result = await ingest.ingest_observation(
        ObserveEvent(
            agent_id=agent_id,
            observation_text=text,
            phase_tag="scene.action",
            client_timestamp=valid_at,
            provenance="lived",
            **kw,
        )
    )
    return result.memory_id


def request(agent_id, **overrides) -> DialogueInitRequest:
    base = dict(agent_id=agent_id, query_text=T_FRESH, as_of=NOW)
    base.update(overrides)
    return DialogueInitRequest(**base)


def items_by_id(result: RetrievalResult) -> dict:
    return {item.memory_id: item for item in result.items}


def items_json(result: RetrievalResult) -> list:
    return json.loads(result.model_dump_json())["items"]


async def main(database_uri: str) -> None:
    settings = Settings(database_uri=database_uri, provider_mode="fake")
    pool = build_pool(database_uri)
    await pool.open()
    ingest = IngestService(pool, fake_providers(), settings)
    retrieval = RetrievalService(pool, fake_providers(), settings)
    print(f"walker: scratch DB = {urlsplit(database_uri).path.lstrip('/')}")

    # Fixture store A: five distinct texts + a pinned/unpinned twin pair,
    # ages injected via client_timestamp -> valid_at (time-travel mechanic 1).
    agent_a = await make_agent(pool, "read-walker-npc-a", AGENT_CONFIG)
    ids = {
        "fresh": await seed(ingest, agent_a, T_FRESH, NOW - timedelta(hours=1)),
        "coin": await seed(ingest, agent_a, T_COIN, NOW - timedelta(hours=2)),
        "fire": await seed(ingest, agent_a, T_FIRE, NOW - timedelta(hours=26)),
        "road": await seed(ingest, agent_a, T_ROAD, NOW - timedelta(hours=3)),
        "twin_pin": await seed(
            ingest, agent_a, T_TWIN, NOW - timedelta(hours=48), pinned=True
        ),
        "twin_unpin": await seed(ingest, agent_a, T_TWIN, NOW - timedelta(hours=48)),
    }

    # ------------------------------------------------------------------ #
    print("\n[1] Happy path (fake provider)")
    r1 = await retrieval.retrieve_dialogue_init(request(agent_a))
    check(len(r1.items) <= 8 and len(r1.items) == 6, "<= k items returned", "6 of 6")
    check(
        all(
            r1.items[i].score >= r1.items[i + 1].score for i in range(len(r1.items) - 1)
        ),
        "items ranked by descending score",
    )
    for item in r1.items:
        if item.read_mode != "verbatim" or not item.content:
            fail("per-item payload", f"{item.memory_id}: bad read_mode/content")
        if item.relevance is None or not (
            0.0 <= item.relevance <= 1.0
            and 0.0 < item.recency <= 1.0
            and 0.0 < item.importance_norm <= 1.0
        ):
            fail("per-item payload", f"{item.memory_id}: component out of range")
    ok(
        "every item carries memory_id, detail_id, content, read_mode=verbatim, "
        "pinned, and score with all three components"
    )
    check(
        r1.items[0].memory_id == ids["fresh"] and r1.items[0].relevance > 0.99,
        "query identical to a stored observation ranks it first, relevance ~1",
        f"relevance={r1.items[0].relevance:.4f}",
    )
    instr = r1.instrumentation
    for name in ("embed_ms", "sql_ms", "score_ms", "total_ms"):
        value = getattr(instr, name)
        if value is None or value < 0:
            fail("instrumentation", f"{name} = {value}")
    ok("per-stage timings non-null and non-negative")
    check(
        instr.embedding_tokens > 0
        and instr.candidate_count == 6
        and instr.k_effective == 8
        and instr.degraded is False
        and instr.as_of_effective == NOW,
        "instrumentation: tokens, candidate_count, k_effective, degraded, as_of",
    )
    default_as_of = await retrieval.retrieve_dialogue_init(
        DialogueInitRequest(agent_id=agent_a, query_text=T_FRESH)
    )
    check(
        default_as_of.instrumentation.as_of_effective.tzinfo is not None,
        "as_of omitted -> tz-aware server default surfaced in instrumentation",
    )

    # ------------------------------------------------------------------ #
    print("\n[11] k honored: request -> agents.config -> service default")
    r_k2 = await retrieval.retrieve_dialogue_init(request(agent_a, k=2))
    check(
        len(r_k2.items) == 2 and r_k2.instrumentation.k_effective == 2,
        "request k=2 -> exactly 2 items",
    )
    agent_b = await make_agent(
        pool, "read-walker-npc-b", {**AGENT_CONFIG, "retrieval_top_k": 3}
    )
    for i, text in enumerate(
        (
            "Bandits raided the granary.",
            "The miller repaid his debt.",
            "A wolf was seen by the river.",
            "The chapel bell cracked in the frost.",
        )
    ):
        await seed(ingest, agent_b, text, NOW - timedelta(hours=i + 1))
    r_bcfg = await retrieval.retrieve_dialogue_init(request(agent_b))
    check(
        len(r_bcfg.items) == 3 and r_bcfg.instrumentation.k_effective == 3,
        "agents.config retrieval_top_k=3 -> 3 items when request omits k",
    )
    r_breq = await retrieval.retrieve_dialogue_init(request(agent_b, k=2))
    check(len(r_breq.items) == 2, "request k beats agents.config")
    check(
        r1.instrumentation.k_effective == 8,
        "service default (8) applies when both request and config omit k",
    )

    # ------------------------------------------------------------------ #
    print("\n[3] Decay moves scores, not rows (as_of time travel)")
    base = await retrieval.retrieve_dialogue_init(request(agent_a))
    later = await retrieval.retrieve_dialogue_init(
        request(agent_a, as_of=NOW + timedelta(days=7))
    )
    base_map, later_map = items_by_id(base), items_by_id(later)
    check(
        set(base_map) == set(later_map),
        "no item appears or disappears under a later as_of",
    )
    for mid, b in base_map.items():
        l = later_map[mid]
        if b.content != l.content:
            fail("decay vs rows", f"{mid}: content changed")
        if b.relevance != l.relevance or b.importance_norm != l.importance_norm:
            fail("decay vs rows", f"{mid}: non-recency component moved")
        if b.pinned:
            if not (b.recency == 1.0 and l.recency == 1.0):
                fail("decay vs rows", f"{mid}: pinned recency != 1.0")
        elif not l.recency < b.recency:
            fail("decay vs rows", f"{mid}: recency did not strictly drop")
    ok("older effective age lowers recency components only; text byte-identical")

    # ------------------------------------------------------------------ #
    print("\n[4] Invalidation moves rows, not scores (fixture SQL)")
    before = await retrieval.retrieve_dialogue_init(request(agent_a))
    await execute(
        pool,
        "UPDATE memories SET invalid_at = now() WHERE memory_id = %s",
        ids["road"],
    )
    after = await retrieval.retrieve_dialogue_init(request(agent_a))
    after_map = items_by_id(after)
    check(ids["road"] not in after_map, "invalidated memory absent from results")
    survivors = {m: i for m, i in items_by_id(before).items() if m != ids["road"]}
    check(set(after_map) == set(survivors), "exactly the survivors remain")
    for mid, b in survivors.items():
        a = after_map[mid]
        if (b.score, b.relevance, b.recency, b.importance_norm, b.content) != (
            a.score,
            a.relevance,
            a.recency,
            a.importance_norm,
            a.content,
        ):
            fail("invalidation vs scores", f"{mid}: a component moved")
    ok("no other item's scores or text changed")
    check(
        after.instrumentation.candidate_count == 5,
        "candidate_count reflects exclusion",
    )

    # ------------------------------------------------------------------ #
    print("\n[5] Live head served (fixture chain supersession)")
    old_head = await fetchrow(
        pool,
        "SELECT detail_id FROM memory_details "
        "WHERE memory_id = %s AND invalid_at IS NULL",
        ids["coin"],
    )
    corrected = "The stranger's coin was local after all. (fixture corrected head)"
    async with pool.connection() as conn:
        async with conn.transaction():
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE memory_details SET invalid_at = now() WHERE detail_id = %s",
                    (old_head[0],),
                )
                await cur.execute(
                    "INSERT INTO memory_details (memory_id, content, write_cause, "
                    "valid_at) VALUES (%s, %s, 'authorial_correction', %s) "
                    "RETURNING detail_id",
                    (ids["coin"], corrected, NOW),
                )
                new_head = (await cur.fetchone())[0]
    r5 = await retrieval.retrieve_dialogue_init(request(agent_a))
    coin_item = items_by_id(r5)[ids["coin"]]
    check(
        coin_item.detail_id == new_head and coin_item.detail_id != old_head[0],
        "served detail_id is the new live head",
    )
    check(
        coin_item.content == corrected,
        "served content is the live head's, byte-identical",
    )

    # ------------------------------------------------------------------ #
    print("\n[6] Pin exemption (identical twin pair)")
    twins = items_by_id(r5)
    pin, unpin = twins[ids["twin_pin"]], twins[ids["twin_unpin"]]
    check(pin.recency == 1.0, "pinned recency component is exactly 1.0")
    check(
        unpin.recency < pin.recency,
        "identical unpinned twin scores strictly lower on recency",
        f"{unpin.recency:.6f} < 1.0",
    )
    check(
        pin.relevance == unpin.relevance
        and pin.importance_norm == unpin.importance_norm
        and pin.score > unpin.score,
        "twins differ only through recency; pin outranks",
    )

    # ------------------------------------------------------------------ #
    print("\n[7] Reserved fields inert, never echoed")
    plain = await retrieval.retrieve_dialogue_init(request(agent_a))
    loaded = await retrieval.retrieve_dialogue_init(
        request(
            agent_a,
            location_name="the forge",
            entities=["Mara", "John"],
            event_time=NOW,
            weight_overrides=WeightOverrides(relevance=9.0, recency=0.1),
        )
    )
    check(
        items_json(plain) == items_json(loaded),
        "identical items and scores with and without reserved fields",
    )
    payload = json.loads(loaded.model_dump_json())
    check(
        set(payload) == {"items", "instrumentation"}
        and not any(
            key in json.dumps(payload)
            for key in ("location_name", "event_time", "weight_overrides")
        ),
        "no reserved field is echoed in the result",
    )

    # ------------------------------------------------------------------ #
    print("\n[8] Byte-identity across identical calls")
    again = await retrieval.retrieve_dialogue_init(request(agent_a))
    check(
        items_json(plain) == items_json(again),
        "same store + same as_of + fake provider -> byte-identical items "
        "(content and scores)",
    )

    # ------------------------------------------------------------------ #
    print("\n[9] NULL-embedding exclusion (vector path) and reachability")
    null_embed_ingest = IngestService(
        pool, fake_providers(embedding=FailingEmbeddingProvider()), settings
    )
    tunnel_result = await null_embed_ingest.ingest_observation(
        ObserveEvent(
            agent_id=agent_a,
            observation_text=T_TUNNEL,
            phase_tag="scene.action",
            client_timestamp=NOW - timedelta(hours=4),
            provenance="lived",
        )
    )
    check(tunnel_result.embedding_failed, "fixture row landed with NULL embedding")
    r9 = await retrieval.retrieve_dialogue_init(request(agent_a))
    check(
        tunnel_result.memory_id not in items_by_id(r9),
        "NULL-embedding row never appears via the vector path",
    )

    # ------------------------------------------------------------------ #
    print("\n[10] Degradation: fail-quiet fallback (ruled ladder row)")
    degraded_retrieval = RetrievalService(
        pool, fake_providers(embedding=FailingEmbeddingProvider()), settings
    )
    r10 = await degraded_retrieval.retrieve_dialogue_init(request(agent_a))
    check(
        r10.instrumentation.degraded is True
        and bool(r10.instrumentation.degraded_reason),
        "degraded flag + reason set",
        r10.instrumentation.degraded_reason or "",
    )
    check(
        len(r10.items) == 6,
        "ranked, non-empty result from a failing embedding provider",
        "6 live candidates incl. the NULL-embedding row",
    )
    check(
        tunnel_result.memory_id in items_by_id(r10),
        "NULL-embedding row reachable under the degraded fallback",
    )
    for item in r10.items:
        if item.relevance is not None:
            fail("degraded scoring", f"{item.memory_id}: relevance not null")
        if item.score != item.recency * item.importance_norm:
            fail("degraded scoring", f"{item.memory_id}: score != recency*importance")
    ok("degraded items score recency x importance_norm with relevance null")
    check(
        all(
            r10.items[i].score >= r10.items[i + 1].score
            for i in range(len(r10.items) - 1)
        )
        and r10.instrumentation.embedding_tokens == 0,
        "degraded result still ranked; no tokens spent",
    )

    # ------------------------------------------------------------------ #
    print("\n[2] One seam, thin route (route JSON == service RetrievalResult)")

    class CapturingRetrieval:
        def __init__(self, inner: RetrievalService):
            self._inner = inner
            self.last: RetrievalResult | None = None

        async def retrieve_dialogue_init(
            self, req: DialogueInitRequest
        ) -> RetrievalResult:
            self.last = await self._inner.retrieve_dialogue_init(req)
            return self.last

    import httpx

    capturing = CapturingRetrieval(retrieval)
    api_module.app.state.retrieval = capturing
    transport = httpx.ASGITransport(app=api_module.app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://walker"
    ) as client:
        payload = json.loads(request(agent_a, k=3).model_dump_json())
        response = await client.post("/v1/dialogue/init", json=payload)
    check(response.status_code == 200, "route returned 200")
    check(
        response.json() == json.loads(capturing.last.model_dump_json()),
        "route JSON is exactly the serialized service RetrievalResult",
        f"{len(response.json()['items'])} items",
    )

    await pool.close()
    print(f"\nALL CHECKS PASSED ({len(PASSED)} assertions)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-uri", default=None)
    args = parser.parse_args()
    # psycopg async cannot run on Windows' default ProactorEventLoop.
    asyncio.run(
        main(args.database_uri or scratch_uri_from_env()),
        loop_factory=asyncio.SelectorEventLoop,
    )
