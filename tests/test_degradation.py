"""Degradation cases (docs\\test-suite.md): every ruled ladder row,
asserted structurally. Marked `nlp` where the scenario CALLS the write pass
at the service level; the retrieval/gate/dialogue rows are unmarked.

The escalation hard-stop case asserts the CURRENT build-phase stance (ruled
2026-07-13; the production re-rule is owed before the demo ships — when it
lands, exactly this test changes). The suite does not settle that question.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from conftest import GATE_CONFIG, NOW, V1_CONFIG, by_id, item_ids, run_structural

from app.schemas import DialogueInitRequest, ObserveEvent

T_OBS = "Mara sharpened my blade at the forge while John watched."
T_BRIDGE = (
    "The miller raised his toll at the bridge and the carters grumbled "
    "about the price of crossing all week."
)
T_FERRY = T_BRIDGE + " Aldous waited by the far bank."
T_QUARRY = (
    "Flood water filled the eastern quarry pits and the winch ropes "
    "rotted where they hung."
)

FALLBACK_LINE = "[fallback] The keeper stares into the ford."
DIALOGUE_CONFIG = {
    **V1_CONFIG,
    "action_vocabulary": ["greet", "warn"],
    "dialogue_fallback_line": FALLBACK_LINE,
}


def observe(agent_id, **overrides) -> ObserveEvent:
    base = dict(
        agent_id=agent_id,
        observation_text=T_OBS,
        phase_tag="suite",
        client_timestamp=NOW,
        provenance="lived",
    )
    base.update(overrides)
    return ObserveEvent(**base)


def read_request(agent_id, **overrides) -> DialogueInitRequest:
    base = dict(agent_id=agent_id, query_text=T_OBS, as_of=NOW)
    base.update(overrides)
    return DialogueInitRequest(**base)


@pytest.mark.nlp
def test_scoring_failure_still_lands(scene):
    """Importance-scorer failure: the write lands with neutral importance
    and scoring_failed = true — never rejected."""

    async def scenario(ctx):
        from app.providers import FailingWriteProvider

        agent = await ctx.make_agent("g-scoring", V1_CONFIG)
        degraded = await ctx.ingest(write=FailingWriteProvider()).ingest_observation(
            observe(agent)
        )
        row = await ctx.fetchrow(
            "SELECT importance_raw, scoring_failed FROM memories WHERE memory_id = %s",
            degraded.memory_id,
        )
        assert row is not None
        assert abs(row[0] - 0.5) < 1e-6 and row[1] is True

    run_structural(scene, scenario)


@pytest.mark.nlp
def test_unknown_decay_class_lands_flagged(scene):
    """An unknown decay_class label lands with the agent's default class and
    decay_class_unknown = true (ruled 2026-07-13); a known label is
    unflagged."""

    async def scenario(ctx):
        agent = await ctx.make_agent("g-decay", V1_CONFIG)
        ingest = ctx.ingest()
        unknown = await ingest.ingest_observation(
            observe(agent, decay_class="bogus-label")
        )
        row = await ctx.fetchrow(
            "SELECT decay_class, decay_class_unknown FROM memories "
            "WHERE memory_id = %s",
            unknown.memory_id,
        )
        assert row == ("episodic", True)
        known = await ingest.ingest_observation(observe(agent, decay_class="semantic"))
        assert (known.decay_class, known.decay_class_unknown) == ("semantic", False)

    run_structural(scene, scenario)


@pytest.mark.nlp
def test_observe_embed_failure_lands_null(scene):
    """Embedding failure at observe: the write lands; the queryable signal
    is the live fact head's NULL embedding (freeze ruling 2026-07-18); the
    payload carries embedding_failed; the row is vector-unreachable but
    rides the degraded path."""

    async def scenario(ctx):
        from conftest import embed_text
        from app import db
        from app.providers import FailingEmbeddingProvider

        agent = await ctx.make_agent("g-embed", V1_CONFIG)
        failed = await ctx.ingest(
            embedding=FailingEmbeddingProvider()
        ).ingest_observation(observe(agent))
        assert failed.embedding_failed is True
        row = await ctx.fetchrow(
            "SELECT embedding IS NULL FROM memory_fact_versions "
            "WHERE memory_id = %s AND invalid_at IS NULL",
            failed.memory_id,
        )
        assert row[0] is True
        probe = embed_text(T_OBS)
        vector_rows = await db.fetch_vector_candidates(ctx.pool, agent, probe, 10)
        assert failed.memory_id not in {r.memory_id for r in vector_rows}
        degraded_rows = await db.fetch_live_candidates(ctx.pool, agent)
        assert failed.memory_id in {r.memory_id for r in degraded_rows}

    run_structural(scene, scenario)


@pytest.mark.nlp
def test_correction_embed_failure_all_or_nothing(scene):
    """Embedding failure during an authorial correction: ALL-OR-NOTHING
    (ruled 2026-07-18) — nothing written on either chain, cache intact,
    loud error. The deliberate contrast with observe's land-with-NULL."""

    async def scenario(ctx):
        from app import db
        from app.ingest import CorrectionEmbedFailedError
        from app.providers import FailingEmbeddingProvider
        from app.schemas import CorrectionRequest

        agent = await ctx.make_agent("g-correct-embed", V1_CONFIG)
        ingest = ctx.ingest()
        seeded = await ingest.ingest_observation(observe(agent))
        m = seeded.memory_id
        await db.insert_cache_row(ctx.pool, m, "vhash|b1", "cached")
        chain_before = await ctx.chain(m)
        facts_before = await ctx.fact_chain(m)

        failing = ctx.ingest(embedding=FailingEmbeddingProvider())
        with pytest.raises(CorrectionEmbedFailedError):
            await failing.correct(
                m,
                CorrectionRequest(
                    content="A corrected telling that must not land.",
                    client_timestamp=NOW + timedelta(hours=1),
                ),
            )
        assert await ctx.chain(m) == chain_before
        assert await ctx.fact_chain(m) == facts_before
        assert await ctx.cache_rows(m) == {"vhash|b1": "cached"}

    run_structural(scene, scenario)


@pytest.mark.nlp
def test_escalation_hard_stop_zero_rows(scene):
    """Escalation fails twice => HARD-STOP, nothing inserted (BUILD-PHASE
    stance ruled 2026-07-13; the production re-rule is owed — see module
    docstring). Structurally assertable as zero rows."""

    async def scenario(ctx):
        from app.ingest import EscalationHardStopError
        from app.providers import FailingEscalationProvider

        agent = await ctx.make_agent("g-hardstop", V1_CONFIG)
        failing = FailingEscalationProvider()
        service = ctx.ingest(escalation=failing)
        counts_sql = (
            "SELECT (SELECT count(*) FROM memories WHERE agent_id = %s), "
            "(SELECT count(*) FROM identity_components WHERE agent_id = %s)"
        )
        before = await ctx.fetchrow(counts_sql, agent, agent)
        with pytest.raises(EscalationHardStopError):
            await service.ingest_observation(observe(agent))
        assert failing.calls == 2  # retried exactly once
        assert await ctx.fetchrow(counts_sql, agent, agent) == before

    run_structural(scene, scenario)


def test_retrieval_fail_quiet_fallback(scene):
    """Query-embedding failure at read time (ruled ladder row): degraded
    flag + reason, every relevance null, score = recency x importance_norm,
    still ranked and non-empty, NULL-embedding rows reachable, no tokens."""

    async def scenario(ctx):
        from app.providers import FailingEmbeddingProvider

        agent = await ctx.make_agent("g-readfall", V1_CONFIG)
        await ctx.seed(agent, T_OBS, NOW - timedelta(hours=1))
        await ctx.seed(agent, T_BRIDGE, NOW - timedelta(hours=2))
        null_row = await ctx.seed(
            agent, T_QUARRY, NOW - timedelta(hours=3), embedding=None
        )
        degraded = ctx.retrieval(embedding=FailingEmbeddingProvider())
        r = await degraded.retrieve_dialogue_init(read_request(agent))
        instr = r.instrumentation
        assert instr.degraded is True and bool(instr.degraded_reason)
        assert len(r.items) == 3
        assert null_row.memory_id in by_id(r)
        for item in r.items:
            assert item.relevance is None
            assert item.score == item.recency * item.importance_norm
        assert all(
            r.items[i].score >= r.items[i + 1].score for i in range(len(r.items) - 1)
        )
        assert instr.embedding_tokens == 0

    run_structural(scene, scenario)


def test_gate_degradation_ladder(scene):
    """The gate's ruled ladder: embeddings down => entity-only lexical rung
    off the fact-head GIN; no coverage basis => novelty-only; both out =>
    gate closed, loaded set served, fail-quiet; foreign loaded IDs drop out
    of the join, counted, turn intact."""

    async def scenario(ctx):
        from uuid import uuid4

        from app.gate import (
            GATE_RUNG_CLOSED,
            GATE_RUNG_ENTITY_ONLY,
            GATE_RUNG_NOVELTY_ONLY,
            GATE_SIGNAL_ENTITY,
            GATE_SIGNAL_NOVELTY,
        )
        from app.providers import FailingEmbeddingProvider

        agent = await ctx.make_agent(
            "g-ladder",
            GATE_CONFIG,
            (("Mara", ["the blacksmith"]), ("Aldous", ["the ferryman"])),
        )
        chapel = await ctx.seed(
            agent,
            "Mara left the chapel before the harvest bells rang out.",
            NOW - timedelta(hours=3),
            entities=["Mara"],
        )
        bridge = await ctx.seed(agent, T_BRIDGE, NOW - timedelta(hours=2))
        ferry = await ctx.seed(
            agent, T_FERRY, NOW - timedelta(minutes=10), entities=["Aldous"]
        )
        # The coverage basis is the LOADED items' fact-head entities: the
        # chapel row supplies one ("Mara") while "Aldous" stays uncovered.
        loaded = [chapel.memory_id, bridge.memory_id]

        def gate_request(query, *, loaded_ids):
            return DialogueInitRequest(
                agent_id=agent,
                query_text=query,
                as_of=NOW,
                scene_started_at=NOW,
                loaded_memory_ids=loaded_ids,
            )

        failing = ctx.retrieval(embedding=FailingEmbeddingProvider())
        entity_only = await failing.retrieve_dialogue_init(
            gate_request(T_FERRY, loaded_ids=loaded)
        )
        g = entity_only.instrumentation.gate
        assert g.degraded_rung == GATE_RUNG_ENTITY_ONLY
        assert g.signals_fired == [GATE_SIGNAL_ENTITY]
        assert entity_only.instrumentation.degraded
        fetched = [i for i in entity_only.items if i.gate_fetched]
        assert any(i.memory_id == ferry.memory_id for i in fetched)
        assert all(i.relevance is None for i in fetched)
        assert g.novelty_min_distance is None

        # Loaded rows carry no entities => no coverage basis: novelty-only.
        bare_loaded = [bridge.memory_id]
        retrieval = ctx.retrieval()
        no_basis = await retrieval.retrieve_dialogue_init(
            gate_request(T_QUARRY, loaded_ids=bare_loaded)
        )
        g = no_basis.instrumentation.gate
        assert g.degraded_rung == GATE_RUNG_NOVELTY_ONLY
        assert g.signals_fired == [GATE_SIGNAL_NOVELTY]

        # Both signals out: embeddings down + no coverage basis => closed.
        both_out = await failing.retrieve_dialogue_init(
            gate_request(T_QUARRY, loaded_ids=bare_loaded)
        )
        g = both_out.instrumentation.gate
        assert g.degraded_rung == GATE_RUNG_CLOSED and not g.fired
        assert both_out.instrumentation.degraded
        assert set(item_ids(both_out)) == set(bare_loaded)

        foreign = await retrieval.retrieve_dialogue_init(
            gate_request(T_BRIDGE, loaded_ids=loaded + [uuid4()])
        )
        assert foreign.instrumentation.gate.loaded_missing_count == 1
        assert set(item_ids(foreign)) == set(loaded)

    run_structural(scene, scenario)


def test_dialogue_never_blank(scene):
    """Malformed model responses at the dialogue seam: log, ignore, the
    turn succeeds. Failing call => the configured fallback line + degraded
    + delta zeroed, reputation row unchanged; malformed output => fallback
    with token spend accounted; an off-vocabulary directive is dropped with
    a reason while prose survives."""

    async def scenario(ctx):
        from app.dialogue import DialogueService
        from app.providers import (
            DialogueCallResult,
            FailingDialogueProvider,
            MalformedDialogueProvider,
        )
        from app.schemas import DialogueTurnRequest

        class OffVocabDialogueProvider:
            def generate(self, **_kwargs) -> DialogueCallResult:
                return DialogueCallResult(
                    prose="[off-vocab] line",
                    directive_type="brandish",
                    directive_params={},
                    directive_error=None,
                    reputation_delta=0.1,
                    delta_error=None,
                    input_tokens=1,
                    output_tokens=1,
                    first_token_ms=0.0,
                )

        agent = await ctx.make_agent("g-dialogue", DIALOGUE_CONFIG)
        await ctx.seed(agent, T_OBS, NOW - timedelta(hours=1))
        retrieval = ctx.retrieval()

        def service(provider) -> DialogueService:
            return DialogueService(
                ctx.pool, ctx.providers(dialogue=provider), ctx.settings, retrieval
            )

        def turn():
            return DialogueTurnRequest(
                agent_id=agent,
                utterance="Tell me about the forge.",
                reputation_snapshot=0.0,
                as_of=NOW,
            )

        rep_before = await ctx.fetchrow(
            "SELECT reputation FROM agents WHERE agent_id = %s", agent
        )
        r_fail = await service(FailingDialogueProvider()).run_dialogue_turn(turn())
        assert r_fail.content == FALLBACK_LINE
        assert r_fail.instrumentation.degraded
        assert "dialogue call failed" in r_fail.instrumentation.degraded_reason
        assert r_fail.reputation_delta == 0.0
        assert r_fail.reputation_delta_source == "zeroed"
        rep_after = await ctx.fetchrow(
            "SELECT reputation FROM agents WHERE agent_id = %s", agent
        )
        assert rep_after == rep_before

        r_mal = await service(MalformedDialogueProvider()).run_dialogue_turn(turn())
        assert r_mal.content == FALLBACK_LINE
        assert r_mal.instrumentation.degraded
        assert r_mal.instrumentation.sonnet_input_tokens == 7
        assert r_mal.instrumentation.sonnet_output_tokens == 3

        r_off = await service(OffVocabDialogueProvider()).run_dialogue_turn(turn())
        assert r_off.directive is None
        assert r_off.directive_dropped
        assert "unknown directive type" in r_off.directive_dropped_reason
        assert bool(r_off.content)
        assert not r_off.instrumentation.degraded

    run_structural(scene, scenario)


def test_reconstruction_fail_quiet(scene):
    """Reconstruction-call failure and malformed batched output both degrade
    soft: live heads served under honest read_mode, nothing written, no
    cache row pinned, token spend accounted on the malformed path."""

    async def scenario(ctx):
        from conftest import RECON_CONFIG
        from app.providers import (
            FailingReconstructionProvider,
            MalformedReconstructionProvider,
        )

        agent = await ctx.make_agent("g-recon", RECON_CONFIG)
        old = await ctx.seed(
            agent, T_BRIDGE, NOW - timedelta(days=10), decay_class="semantic"
        )
        failing = ctx.retrieval(reconstruction=FailingReconstructionProvider())
        r = await failing.retrieve_dialogue_init(
            read_request(agent, query_text=T_BRIDGE, scene_started_at=NOW)
        )
        assert r.instrumentation.degraded
        assert "reconstruction call failed" in (r.instrumentation.degraded_reason or "")
        chain = await ctx.chain(old.memory_id)
        assert len(chain) == 1
        item = by_id(r)[old.memory_id]
        assert item.read_mode == "verbatim" and item.content == chain[0][1]
        assert await ctx.cache_rows(old.memory_id) == {}

        malformed = ctx.retrieval(reconstruction=MalformedReconstructionProvider())
        r_mal = await malformed.retrieve_dialogue_init(
            read_request(agent, query_text=T_BRIDGE, scene_started_at=NOW)
        )
        assert r_mal.instrumentation.degraded
        assert r_mal.instrumentation.reconstruction_input_tokens == 7
        assert len(await ctx.chain(old.memory_id)) == 1

    run_structural(scene, scenario)
