"""Set D — mid-dialogue gate (docs\\test-suite.md; mid-dialogue-gate.md,
built 2026-07-19). GATE_CONFIG agents: gate at PRODUCTION defaults;
reconstruction FIXTURE-pinned inert (see conftest).

Unmarked except the entities-follow-correction pair (the correction verb's
NER merge is service-level). Seeding is db-layer with explicit entities —
the fact-head coverage basis is a fixture fact here, exactly as observe
would have written it.

Fixture texts are the gate walker's measured corpus (fake-mode distances:
echo ~0; these trigram-distinct texts ~>= 0.73 apart — over the 0.5 novelty
threshold; a FIXTURE property of the pure fake embedding).
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from conftest import (
    GATE_CONFIG,
    NOW,
    V1_CONFIG,
    by_id,
    drain_turn,
    item_ids,
    run_structural,
)

from app.gate import GATE_SIGNAL_ENTITY, GATE_SIGNAL_NOVELTY
from app.schemas import DialogueInitRequest, GateInstrumentation

T_CHAPEL = (
    "Mara left the chapel before the harvest bells and the sexton counted "
    "the silver twice by candlelight."
)
T_BRIDGE = (
    "The miller raised his toll at the bridge and the carters grumbled "
    "about the price of crossing all week."
)
T_STORM = (
    "A late storm flattened the barley on the south slope and the gleaners "
    "worked until dusk to save what remained."
)
T_QUARRY = (
    "Flood water filled the eastern quarry pits and the winch ropes "
    "rotted where they hung."
)
T_FERRY = T_BRIDGE + " Aldous waited by the far bank."
T_OLD_DEBT = "Nine grey herons circled the weir at dawn, quarrelling over eels."

COMPONENTS = (("Mara", ["the blacksmith"]), ("Aldous", ["the ferryman"]))


def request(agent_id, query_text, *, loaded=None, streak=0, k=None):
    return DialogueInitRequest(
        agent_id=agent_id,
        query_text=query_text,
        k=k,
        as_of=NOW,
        scene_started_at=NOW,
        loaded_memory_ids=loaded,
        gate_fruitless_streak=streak,
    )


async def _base_store(ctx, agent):
    """Three loaded-set memories, entities on the fact heads."""
    m1 = await ctx.seed(agent, T_CHAPEL, NOW - timedelta(hours=3), entities=["Mara"])
    m2 = await ctx.seed(agent, T_BRIDGE, NOW - timedelta(hours=2))
    m3 = await ctx.seed(agent, T_STORM, NOW - timedelta(hours=1))
    return [m1.memory_id, m2.memory_id, m3.memory_id]


def test_loader_parity(scene):
    """A request without loaded fields is the loader turn: the gate is not
    evaluated (all-default instrumentation), nothing is gate_fetched, the
    store is served. gate_enabled = 0 keeps the loader path even with
    loaded IDs (the kill-switch pin shape)."""

    async def scenario(ctx):
        agent = await ctx.make_agent("d-loader", GATE_CONFIG, COMPONENTS)
        off_agent = await ctx.make_agent(
            "d-loader-off", {**GATE_CONFIG, "gate_enabled": 0.0}, COMPONENTS
        )
        ids = await _base_store(ctx, agent)
        retrieval = ctx.retrieval()
        loader = await retrieval.retrieve_dialogue_init(request(agent, T_BRIDGE))
        assert loader.instrumentation.gate == GateInstrumentation()
        assert not any(item.gate_fetched for item in loader.items)
        assert set(item_ids(loader)) == set(ids)

        off_ids = await _base_store(ctx, off_agent)
        off = await ctx.retrieval().retrieve_dialogue_init(
            request(off_agent, T_QUARRY, loaded=off_ids)
        )
        assert not off.instrumentation.gate.evaluated

    run_structural(scene, scenario)


def test_closed_gate_serves_loaded_set(scene):
    """A covered, near-loaded utterance: gate closed, zero probe SQL,
    exactly the loaded IDs served deterministically; a NULL-fact-embedding
    loaded row is counted out of the novelty basis and served with
    relevance null."""

    async def scenario(ctx):
        agent = await ctx.make_agent("d-closed", GATE_CONFIG, COMPONENTS)
        ids = await _base_store(ctx, agent)
        retrieval = ctx.retrieval()
        closed = await retrieval.retrieve_dialogue_init(
            request(agent, T_CHAPEL, loaded=ids)
        )
        g = closed.instrumentation.gate
        assert g.evaluated and not g.fired and g.signals_fired == []
        assert set(item_ids(closed)) == set(ids)
        assert closed.instrumentation.sql_ms == 0.0  # zero probe SQL
        assert all(item.relevance is not None for item in closed.items)

        again = await retrieval.retrieve_dialogue_init(
            request(agent, T_CHAPEL, loaded=ids)
        )
        assert item_ids(again) == item_ids(closed)
        assert [i.content for i in again.items] == [i.content for i in closed.items]

        null_row = await ctx.seed(
            agent,
            "Someone left a lantern burning overnight.",
            NOW - timedelta(minutes=30),
            embedding=None,
        )
        with_null = await retrieval.retrieve_dialogue_init(
            request(agent, T_CHAPEL, loaded=ids + [null_row.memory_id])
        )
        g = with_null.instrumentation.gate
        assert g.null_embedding_loaded_count == 1
        null_items = [i for i in with_null.items if i.memory_id == null_row.memory_id]
        assert null_items and null_items[0].relevance is None

    run_structural(scene, scenario)


def test_novelty_fire_appends_only_new(scene):
    """A far utterance fires novelty alone; the fetch is SQL-excluded (only
    NEW ids), exactly this turn's appends are marked gate_fetched, and a
    gate-fetched item's text is byte-stable on the next serve."""

    async def scenario(ctx):
        agent = await ctx.make_agent("d-novelty", GATE_CONFIG, COMPONENTS)
        ids = await _base_store(ctx, agent)
        cold = await ctx.seed(agent, T_QUARRY, NOW - timedelta(minutes=20))
        retrieval = ctx.retrieval()
        novel = await retrieval.retrieve_dialogue_init(
            request(agent, T_QUARRY, loaded=ids)
        )
        g = novel.instrumentation.gate
        assert g.fired and g.signals_fired == [GATE_SIGNAL_NOVELTY]
        assert cold.memory_id in g.fetched_memory_ids
        assert not set(g.fetched_memory_ids) & set(ids)
        assert all(
            item.gate_fetched == (item.memory_id in set(g.fetched_memory_ids))
            for item in novel.items
        )
        assert set(item_ids(novel)) == set(ids) | set(g.fetched_memory_ids)

        fetched_text = by_id(novel)[cold.memory_id].content
        served_again = await retrieval.retrieve_dialogue_init(
            request(agent, T_QUARRY, loaded=ids + list(g.fetched_memory_ids))
        )
        assert by_id(served_again)[cold.memory_id].content == fetched_text

    run_structural(scene, scenario)


def test_entity_tripwire_and_covered_suppression(scene):
    """An uncovered live-component mention fires the tripwire alone; the
    fetch contains the entity (efficacy true); the same mention covered by
    a loaded item's fact-head entities does not fire."""

    async def scenario(ctx):
        agent = await ctx.make_agent("d-tripwire", GATE_CONFIG, COMPONENTS)
        ids = await _base_store(ctx, agent)
        ferry = await ctx.seed(
            agent, T_FERRY, NOW - timedelta(minutes=10), entities=["Aldous"]
        )
        retrieval = ctx.retrieval()
        trip = await retrieval.retrieve_dialogue_init(
            request(agent, T_FERRY, loaded=ids)
        )
        g = trip.instrumentation.gate
        assert g.fired and g.signals_fired == [GATE_SIGNAL_ENTITY]
        assert g.uncovered_entities == ["Aldous"]
        assert ferry.memory_id in g.fetched_memory_ids
        assert g.entity_covered is True

        covered = await retrieval.retrieve_dialogue_init(
            request(agent, T_FERRY, loaded=ids + [ferry.memory_id])
        )
        assert not covered.instrumentation.gate.fired
        assert covered.instrumentation.gate.signals_fired == []

    run_structural(scene, scenario)


def test_both_signals_logged(scene):
    """Far + uncovered logs both named constants; every fire event carries
    non-empty signals_fired."""

    async def scenario(ctx):
        agent = await ctx.make_agent("d-both", GATE_CONFIG, COMPONENTS)
        ids = await _base_store(ctx, agent)
        await ctx.seed(agent, T_FERRY, NOW - timedelta(minutes=10), entities=["Aldous"])
        both = await ctx.retrieval().retrieve_dialogue_init(
            request(agent, T_QUARRY + " Aldous waited.", loaded=ids)
        )
        g = both.instrumentation.gate
        assert g.signals_fired == [GATE_SIGNAL_NOVELTY, GATE_SIGNAL_ENTITY]
        assert g.fired and len(g.signals_fired) > 0

    run_structural(scene, scenario)


def test_damper_suppresses_novelty_not_tripwire(scene):
    """A fire that appends nothing is fruitless; at the ruled streak the
    damper suppresses novelty for the scene remainder while the tripwire
    stays live."""

    async def scenario(ctx):
        agent = await ctx.make_agent("d-damper", GATE_CONFIG, COMPONENTS)
        ids = await _base_store(ctx, agent)
        ferry = await ctx.seed(
            agent, T_FERRY, NOW - timedelta(minutes=10), entities=["Aldous"]
        )
        all_ids = ids + [ferry.memory_id]
        retrieval = ctx.retrieval()
        fruitless = await retrieval.retrieve_dialogue_init(
            request(agent, T_OLD_DEBT, loaded=all_ids)
        )
        g = fruitless.instrumentation.gate
        assert g.fired and g.fetched_new_count == 0 and g.fruitless

        damped = await retrieval.retrieve_dialogue_init(
            request(agent, T_OLD_DEBT, loaded=all_ids, streak=2)
        )
        g = damped.instrumentation.gate
        assert g.damper_active and not g.fired and g.signals_fired == []

        damped_trip = await retrieval.retrieve_dialogue_init(
            request(agent, T_FERRY, loaded=ids, streak=2)
        )
        g = damped_trip.instrumentation.gate
        assert g.damper_active and g.signals_fired == [GATE_SIGNAL_ENTITY]

    run_structural(scene, scenario)


def test_novelty_outscored_efficacy(scene):
    """The novelty-efficacy boolean populates on fire events per the ruled
    comparator: a fetched distance-0 echo out-scores a far loaded row."""

    async def scenario(ctx):
        agent = await ctx.make_agent("d-efficacy", GATE_CONFIG, COMPONENTS)
        bridge = await ctx.seed(agent, T_BRIDGE, NOW - timedelta(hours=2))
        await ctx.seed(agent, T_QUARRY, NOW - timedelta(minutes=20))
        outscored = await ctx.retrieval().retrieve_dialogue_init(
            request(agent, T_QUARRY, loaded=[bridge.memory_id])
        )
        assert outscored.instrumentation.gate.novelty_outscored is True

    run_structural(scene, scenario)


def test_runner_append_only_and_scene_reset(scene):
    """The caller-held contract end-to-end: the loader turn's served IDs
    become the scene's loaded set; gate fetches append in order; a scene
    boundary resets the loaded set and the damper streak (caller-side)."""

    async def scenario(ctx):
        from app.session import SessionRunner

        agent = await ctx.make_agent("d-runner", GATE_CONFIG, COMPONENTS)
        await _base_store(ctx, agent)
        await ctx.seed(agent, T_OLD_DEBT, NOW - timedelta(minutes=5))
        runner = await SessionRunner.create(
            agent, settings=ctx.settings, providers=ctx.providers(), pool=ctx.pool
        )
        try:
            runner.as_of = NOW
            turn1 = await runner.utterance(T_BRIDGE)
            assert runner.loaded_memory_ids == item_ids(turn1)
            assert not turn1.instrumentation.retrieval.gate.evaluated

            turn2 = await runner.utterance(T_OLD_DEBT + " Nobody forgave it.")
            g2 = turn2.instrumentation.retrieval.gate
            assert g2.evaluated
            assert runner.loaded_memory_ids == item_ids(turn1) + list(
                g2.fetched_memory_ids
            )

            runner.gate_fruitless_streak = 2
            await runner.scene()
            assert runner.loaded_memory_ids is None
            assert runner.gate_fruitless_streak == 0
        finally:
            await runner.close()

    run_structural(scene, scenario)


def test_split_brain_views_parity_and_rerank(scene):
    """Split-brain (split-brain-streaming.md, 2026-07-21): one retrieval, two
    scored views. The divergence record rides the turn result over the served
    set; at default weights the behavior view is byte-identical to the dialogue
    view (parity); a weight override re-scores the behavior view over the SAME
    set while the dialogue view is unaffected. The seam streams prose ==
    content."""

    async def scenario(ctx):
        from app.dialogue import DialogueService
        from app.schemas import DialogueTurnRequest, WeightOverrides

        config = {**V1_CONFIG, "action_vocabulary": ["greet", "warn"]}
        agent = await ctx.make_agent("d-split", config)
        await ctx.seed(agent, T_BRIDGE, NOW - timedelta(hours=1), importance=0.9)
        await ctx.seed(agent, T_STORM, NOW - timedelta(hours=20), importance=0.3)
        await ctx.seed(agent, T_QUARRY, NOW - timedelta(hours=2), importance=0.6)
        service = DialogueService(
            ctx.pool, ctx.providers(), ctx.settings, ctx.retrieval()
        )

        def turn(**over):
            base = dict(
                agent_id=agent,
                utterance="Tell me the news.",
                reputation_snapshot=0.0,
                as_of=NOW,
            )
            base.update(over)
            return DialogueTurnRequest(**base)

        prose, r = await drain_turn(service.run_dialogue_turn(turn()))
        assert prose and r.content == prose  # the seam streamed
        served = {i.memory_id for i in r.items}
        assert (
            served
            == {v.memory_id for v in r.dialogue_view}
            == {v.memory_id for v in r.behavior_view}
        )
        # parity at default weights: byte-identical order AND scores.
        assert [v.memory_id for v in r.dialogue_view] == [
            v.memory_id for v in r.behavior_view
        ]
        assert [v.score for v in r.dialogue_view] == [v.score for v in r.behavior_view]

        # a weight override re-scores the behavior view over the SAME set;
        # the dialogue view stays byte-identical (the parity contract).
        _p, rw = await drain_turn(
            service.run_dialogue_turn(
                turn(weight_overrides=WeightOverrides(relevance=0.0))
            )
        )
        assert {v.memory_id for v in rw.behavior_view} == served
        assert [v.score for v in rw.dialogue_view] != [
            v.score for v in rw.behavior_view
        ]
        assert [v.memory_id for v in rw.dialogue_view] == [
            v.memory_id for v in r.dialogue_view
        ]
        assert [v.score for v in rw.dialogue_view] == [v.score for v in r.dialogue_view]

    run_structural(scene, scenario)


def test_dialogue_turn_route_contract(scene):
    """The HTTP turn route (turn-route build, 2026-07-23): POST
    /v1/dialogue/turn drains the split-brain seam to its terminal result —
    response JSON == the seam result's serialization (the pass-through
    ruling), scene state entirely caller-held on the request (stateless).
    Both TTFT fields ride the wire, the perceived (retrieval-inclusive)
    field strictly above the seam-clocked first_word. 404 unknown agent;
    422 unknown identity_version (the init-route precedent)."""

    async def scenario(ctx):
        import json

        import httpx

        import app.api as api_module
        from app.dialogue import DialogueService
        from app.schemas import DialogueTurnRequest

        config = {**V1_CONFIG, "action_vocabulary": ["greet", "warn"]}
        agent = await ctx.make_agent("d-route", config)
        await ctx.seed(agent, T_BRIDGE, NOW - timedelta(hours=1))
        await ctx.seed(agent, T_STORM, NOW - timedelta(hours=2))
        service = DialogueService(
            ctx.pool, ctx.providers(), ctx.settings, ctx.retrieval()
        )

        class CapturingDialogue:
            def __init__(self, inner):
                self._inner = inner
                self.last = None

            async def run_dialogue_turn(self, req, *, on_reconstruct=None):
                async for item in self._inner.run_dialogue_turn(
                    req, on_reconstruct=on_reconstruct
                ):
                    if not isinstance(item, str):
                        self.last = item
                    yield item

        capturing = CapturingDialogue(service)
        api_module.app.state.dialogue = capturing
        transport = httpx.ASGITransport(app=api_module.app)

        def payload(**over):
            base = dict(
                agent_id=agent,
                utterance="Tell me the news.",
                reputation_snapshot=0.0,
                as_of=NOW,
            )
            base.update(over)
            return json.loads(DialogueTurnRequest(**base).model_dump_json())

        async with httpx.AsyncClient(
            transport=transport, base_url="http://suite"
        ) as client:
            ok = await client.post("/v1/dialogue/turn", json=payload())
            assert ok.status_code == 200
            assert ok.json() == json.loads(capturing.last.model_dump_json())
            body = ok.json()
            assert [i["memory_id"] for i in body["items"]]
            assert all(i["score"] is not None for i in body["items"])
            ins = body["instrumentation"]
            assert ins["perceived_first_word_ms"] > ins["first_word_ms"] > 0.0

            r404 = await client.post(
                "/v1/dialogue/turn", json=payload(agent_id=uuid4())
            )
            assert r404.status_code == 404

            r422 = await client.post(
                "/v1/dialogue/turn",
                json=payload(identity_version="no-such-version"),
            )
            assert r422.status_code == 422

    run_structural(scene, scenario)


@pytest.mark.nlp
def test_entities_follow_correction(scene):
    """Migration 003's behavior pair through the real verb: the corrected
    fact head carries the merged NER + operator-field entities; the
    superseded fact row keeps its own; windowed SQL re-derives entity
    liveness at any instant."""

    async def scenario(ctx):
        from app.schemas import CorrectionRequest, ObserveEvent

        agent = await ctx.make_agent("d-entities", GATE_CONFIG, COMPONENTS)
        ingest = ctx.ingest()
        seeded = await ingest.ingest_observation(
            ObserveEvent(
                agent_id=agent,
                observation_text=T_CHAPEL,
                phase_tag="suite",
                client_timestamp=NOW - timedelta(hours=3),
                provenance="lived",
                entities=["Mara"],
            )
        )
        m = seeded.memory_id
        correction = await ingest.correct(
            m,
            CorrectionRequest(
                content="The silver was counted once, in the vestry, by Mara herself.",
                client_timestamp=NOW + timedelta(hours=1),
                entities=["the vestry"],
            ),
        )
        facts = await ctx.fact_chain(m)
        assert facts[1][0] == "authorial_correction"
        assert facts[1][5] == correction.entities
        assert "the vestry" in correction.entities
        assert facts[0][5] == seeded.entities  # superseded keeps ITS entities
        assert facts[0][3] == facts[1][2]  # coherent chain timeline

        t_before = NOW - timedelta(hours=2)
        live_before = await ctx.fetchall(
            "SELECT write_cause FROM memory_fact_versions WHERE memory_id = %s "
            "AND valid_at <= %s AND (invalid_at IS NULL OR invalid_at > %s)",
            m,
            t_before,
            t_before,
        )
        assert [row[0] for row in live_before] == ["original"]

    run_structural(scene, scenario)


def test_context_term_applies_on_gated_turns(scene):
    """The encoding-context term (built 2026-07-20) rides the gated path
    too: on a closed gate the loaded set's scores carry the same exact
    factor, and the gate decision itself is untouched by context fields
    (context nudges scores; it never opens or closes the gate)."""

    async def scenario(ctx):
        agent = await ctx.make_agent("d-context", GATE_CONFIG, COMPONENTS)
        stamped = await ctx.seed(
            agent,
            T_CHAPEL,
            NOW - timedelta(hours=3),
            entities=["Mara"],
            event_time=NOW,
            location_name="The Chapel",
        )
        other = await ctx.seed(agent, T_BRIDGE, NOW - timedelta(hours=2))
        ids = [stamped.memory_id, other.memory_id]
        retrieval = ctx.retrieval()
        no_ctx = await retrieval.retrieve_dialogue_init(
            request(agent, T_CHAPEL, loaded=ids)
        )
        with_ctx = await retrieval.retrieve_dialogue_init(
            DialogueInitRequest(
                agent_id=agent,
                query_text=T_CHAPEL,
                as_of=NOW,
                scene_started_at=NOW,
                loaded_memory_ids=ids,
                entities=["mara"],
                event_time=NOW,
                location_name="the chapel",
            )
        )
        for result in (no_ctx, with_ctx):
            g = result.instrumentation.gate
            assert g.evaluated and not g.fired and g.signals_fired == []
        assert with_ctx.instrumentation.context_active is True
        p, c = by_id(no_ctx), by_id(with_ctx)
        assert c[stamped.memory_id].score == p[stamped.memory_id].score * 1.75
        assert c[other.memory_id].score == p[other.memory_id].score

    run_structural(scene, scenario)
