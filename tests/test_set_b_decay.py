"""Set B — decay-only (docs\\test-suite.md): recency decay and bi-temporal
invalidation are structurally distinct mechanisms. Decay moves scores at read
time without touching rows; invalidation stamps rows without touching scores.

V1_CONFIG agents (reconstruction + gate FIXTURE-pinned off — see conftest) so
serving is v1 verbatim and every failure has a single cause. Time travel uses
both ruled mechanics: injected `valid_at` at seeding and the read path's
`as_of` override (adopted 2026-07-14). No sleeps, no wall clock.

Unmarked: seeding is db-layer (`ctx.seed`) — no write-pass call.
"""

from __future__ import annotations

import json
from datetime import timedelta

from conftest import NOW, V1_CONFIG, by_id, run_structural

from app.schemas import DialogueInitRequest

T_FRESH = "Mara sharpened my blade at the forge while John watched."
T_COIN = "A stranger paid in foreign coin at the market."
T_FIRE = "The forge fire went out during the storm."
T_ROAD = "I overheard talk of bandits on the north road."
T_TWIN = "The baron doubled the tax on iron."


def request(agent_id, **overrides) -> DialogueInitRequest:
    base = dict(agent_id=agent_id, query_text=T_FRESH, as_of=NOW)
    base.update(overrides)
    return DialogueInitRequest(**base)


async def _seed_store(ctx, agent):
    return {
        "fresh": (await ctx.seed(agent, T_FRESH, NOW - timedelta(hours=1))).memory_id,
        "coin": (await ctx.seed(agent, T_COIN, NOW - timedelta(hours=2))).memory_id,
        "fire": (await ctx.seed(agent, T_FIRE, NOW - timedelta(hours=26))).memory_id,
        "road": (await ctx.seed(agent, T_ROAD, NOW - timedelta(hours=3))).memory_id,
    }


def test_decay_moves_scores_not_rows(scene):
    """A later as_of lowers ONLY the recency component; no row is written,
    no item appears or disappears, text stays byte-identical."""

    async def scenario(ctx):
        agent = await ctx.make_agent("b-decay", V1_CONFIG)
        await _seed_store(ctx, agent)
        retrieval = ctx.retrieval()
        base = await retrieval.retrieve_dialogue_init(request(agent))
        later = await retrieval.retrieve_dialogue_init(
            request(agent, as_of=NOW + timedelta(days=7))
        )
        base_map, later_map = by_id(base), by_id(later)
        assert set(base_map) == set(later_map)
        for mid, b in base_map.items():
            after = later_map[mid]
            assert after.content == b.content
            assert after.relevance == b.relevance
            assert after.importance_norm == b.importance_norm
            assert after.recency < b.recency
        stamped = await ctx.fetchrow(
            "SELECT (SELECT count(*) FROM memories WHERE invalid_at IS NOT NULL) "
            "+ (SELECT count(*) FROM memory_details WHERE invalid_at IS NOT NULL)"
        )
        assert stamped[0] == 0

    run_structural(scene, scenario)


def test_invalidation_moves_rows_not_scores(scene):
    """Stamping invalid_at removes exactly that item; every survivor's score
    components and text are byte-identical — decay never enters."""

    async def scenario(ctx):
        agent = await ctx.make_agent("b-invalidate", V1_CONFIG)
        ids = await _seed_store(ctx, agent)
        retrieval = ctx.retrieval()
        before = await retrieval.retrieve_dialogue_init(request(agent))
        await ctx.execute(
            "UPDATE memories SET invalid_at = now() WHERE memory_id = %s",
            ids["road"],
        )
        after = await retrieval.retrieve_dialogue_init(request(agent))
        after_map = by_id(after)
        assert ids["road"] not in after_map
        survivors = {m: i for m, i in by_id(before).items() if m != ids["road"]}
        assert set(after_map) == set(survivors)
        for mid, b in survivors.items():
            a = after_map[mid]
            assert (a.score, a.relevance, a.recency, a.importance_norm, a.content) == (
                b.score,
                b.relevance,
                b.recency,
                b.importance_norm,
                b.content,
            )
        assert after.instrumentation.candidate_count == len(survivors)

    run_structural(scene, scenario)


def test_pin_recency_exemption(scene):
    """An identical twin pair differing only in `pinned`: the pinned twin's
    recency is exactly 1.0 and outranks; relevance and importance agree."""

    async def scenario(ctx):
        agent = await ctx.make_agent("b-pin", V1_CONFIG)
        pin = await ctx.seed(agent, T_TWIN, NOW - timedelta(hours=48), pinned=True)
        unpin = await ctx.seed(agent, T_TWIN, NOW - timedelta(hours=48))
        retrieval = ctx.retrieval()
        result = await retrieval.retrieve_dialogue_init(
            request(agent, query_text=T_TWIN)
        )
        twins = by_id(result)
        p, u = twins[pin.memory_id], twins[unpin.memory_id]
        assert p.recency == 1.0
        assert u.recency < p.recency
        assert p.relevance == u.relevance
        assert p.importance_norm == u.importance_norm
        assert p.score > u.score

    run_structural(scene, scenario)


def test_time_travel_mechanics_agree(scene):
    """The two ruled time-travel mechanics compute the same effective age:
    (valid_at NOW-9d, as_of NOW-7d) and (valid_at NOW-2d, as_of NOW) yield
    equal recency for the same class and importance."""

    async def scenario(ctx):
        agent_a = await ctx.make_agent("b-tt-a", V1_CONFIG)
        agent_b = await ctx.make_agent("b-tt-b", V1_CONFIG)
        m_a = await ctx.seed(agent_a, T_COIN, NOW - timedelta(days=9))
        m_b = await ctx.seed(agent_b, T_COIN, NOW - timedelta(days=2))
        retrieval = ctx.retrieval()
        r_a = await retrieval.retrieve_dialogue_init(
            request(agent_a, query_text=T_COIN, as_of=NOW - timedelta(days=7))
        )
        r_b = await retrieval.retrieve_dialogue_init(
            request(agent_b, query_text=T_COIN, as_of=NOW)
        )
        rec_a = by_id(r_a)[m_a.memory_id].recency
        rec_b = by_id(r_b)[m_b.memory_id].recency
        assert rec_a == rec_b
        assert rec_a < 1.0

    run_structural(scene, scenario)


def test_ids_and_scores_ride_the_wire(scene):
    """The load-bearing corollary (tests\\CLAUDE.md): the read endpoint
    returns memory IDs and score components alongside prose, and identical
    calls return byte-identical JSON."""

    async def scenario(ctx):
        import httpx

        import app.api as api_module

        agent = await ctx.make_agent("b-wire", V1_CONFIG)
        await _seed_store(ctx, agent)
        api_module.app.state.retrieval = ctx.retrieval()
        transport = httpx.ASGITransport(app=api_module.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://suite"
        ) as client:
            payload = json.loads(request(agent).model_dump_json())
            first = await client.post("/v1/dialogue/init", json=payload)
            second = await client.post("/v1/dialogue/init", json=payload)
        assert first.status_code == 200
        body = first.json()
        assert body["items"]
        for item in body["items"]:
            for key in (
                "memory_id",
                "detail_id",
                "content",
                "read_mode",
                "score",
                "relevance",
                "recency",
                "importance_norm",
            ):
                assert key in item
        # Byte-identity governs the served items; instrumentation carries
        # wall-clock timings and legitimately differs per call.
        assert body["items"] == second.json()["items"]

    run_structural(scene, scenario)


T_CTX = "Mara reforged the ceremonial hinge before dusk."
T_BARE = "A dull grey drizzle settled over the empty stalls."


def test_context_term_parity_and_exact_factor(scene):
    """Encoding-context term (built 2026-07-20): a no-context request stays
    byte-identical to v1 scoring (the parity contract); supplied context
    multiplies EXACTLY (1 + sum w_i * match_i) into score — never any other
    component, never a penalty on an unstamped row, casefolded both sides."""

    async def scenario(ctx):
        agent = await ctx.make_agent("b-context", V1_CONFIG)
        stamped = (
            await ctx.seed(
                agent,
                T_CTX,
                NOW - timedelta(hours=4),
                entities=["Mara"],
                event_time=NOW,
                location_name="The Forge",
            )
        ).memory_id
        bare = (await ctx.seed(agent, T_BARE, NOW - timedelta(hours=4))).memory_id
        retrieval = ctx.retrieval()
        plain = await retrieval.retrieve_dialogue_init(request(agent))
        assert plain.instrumentation.context_active is False
        assert plain.instrumentation.context_components == []
        full = await retrieval.retrieve_dialogue_init(
            request(
                agent,
                entities=["mara"],
                event_time=NOW,
                location_name="the forge",
            )
        )
        assert full.instrumentation.context_active is True
        assert full.instrumentation.context_components == [
            "entities",
            "event_time",
            "location",
        ]
        p, c = by_id(plain), by_id(full)
        assert c[stamped].score == p[stamped].score * 1.75
        assert c[bare].score == p[bare].score
        assert c[stamped].relevance == p[stamped].relevance
        assert c[stamped].recency == p[stamped].recency
        assert c[stamped].importance_norm == p[stamped].importance_norm
        half = await retrieval.retrieve_dialogue_init(
            request(agent, entities=["mara", "zz-unknown-name"])
        )
        assert by_id(half)[stamped].score == p[stamped].score * 1.125
        assert by_id(half)[bare].score == p[bare].score
        assert by_id(half)[stamped].content == p[stamped].content

    run_structural(scene, scenario)
