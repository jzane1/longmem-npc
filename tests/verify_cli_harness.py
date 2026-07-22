"""verify_cli_harness.py — structural done-when walker for the dialogue-turn
seam (docs\\cli-harness.md 2026-07-15, RE-OPENED by the split-brain build
docs\\split-brain-streaming.md 2026-07-21).

Since the split-brain build the seam is an ASYNC GENERATOR: `run_dialogue_turn`
yields prose chunks, then the terminal DialogueTurnResult. Two concurrent calls
run off one retrieval — a streaming prose call and a behavior call (directive +
delta) — with two scored views (dialogue view = the served ranking; behavior
view = the same served set re-ranked with resolved weights). This walker
asserts the ruled done-when: concurrency, first_word_ms, dialogue-view parity +
behavior re-rank, the divergence record, the recent-actions block, and all four
degradation rows — plus the unchanged reputation math and vocabulary contract.

Structural-only per tests\\CLAUDE.md: assertions touch IDs, flags, score
components, reputation math, byte-identity, and prompt block structure, never
generated prose content.

Prerequisite (PowerShell):
    python db\\migrate.py --database-uri <scratch-uri>
Run:
    python tests\\verify_cli_harness.py [--database-uri <scratch-uri>]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time as _time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from psycopg.types.json import Jsonb

from app.cli import render_debug
from app.config import Settings
from app.db import build_pool
from app.dialogue import (
    DialogueService,
    assemble_behavior_prompt,
    assemble_prose_prompt,
    behavior_score,
    rank_behavior_view,
    resolve_behavior_weights,
)
from app.ingest import IngestService, UnknownAgentError
from app.load_driver import run_driver
from app.providers import (
    BehaviorCallResult,
    FailingBehaviorProvider,
    FailingProseProvider,
    FakeBehaviorProvider,
    FakeEmbeddingProvider,
    FakeEscalationProvider,
    FakeProseProvider,
    FakeWriteProvider,
    MalformedBehaviorProvider,
    MidStreamDropProseProvider,
    Providers,
    SlowBehaviorProvider,
)
from app.retrieval import RetrievalService
from app.schemas import (
    DialogueTurnRequest,
    DialogueTurnResult,
    ObserveEvent,
    RecentAction,
    RetrievedMemory,
    WeightOverrides,
)
from app.session import SessionRunner

NOW = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)

FALLBACK_LINE = "[fallback] The smith stares into the coals."
VOCAB = ["greet", "warn"]

AGENT_CONFIG = {
    "decay_classes": {"episodic": 86400, "semantic": 604800},
    "decay_class_default": "episodic",
    "action_vocabulary": VOCAB,
    "dialogue_fallback_line": FALLBACK_LINE,
    # theta = 0 knob-disables the reconstruction serving stage; gate_enabled = 0
    # knob-disables the mid-dialogue gate — this walker keeps the v1
    # every-turn-retrieves / verbatim-serving contract (their swapped behaviors
    # are verify_reconstruction.py / verify_gate.py floors). FIXTURE-ONLY.
    "reconstruction_theta": 0.0,
    "gate_enabled": 0.0,
}

T_FORGE = "Mara sharpened my blade at the forge while John watched."
T_ROAD = "I overheard talk of bandits on the north road."
T_TAX = "The baron doubled the tax on iron."
UTTERANCE = "Tell me about the forge."

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


def bundle(dialogue=None, behavior=None) -> Providers:
    return Providers(
        write=FakeWriteProvider(),
        escalation=FakeEscalationProvider(),
        embedding=FakeEmbeddingProvider(),
        dialogue=dialogue if dialogue is not None else FakeProseProvider(),
        behavior=behavior if behavior is not None else FakeBehaviorProvider(),
    )


# --- walker-local behavior fakes (ladder rows the shipped fakes don't hit) ---


class OffVocabBehaviorProvider:
    """Emits a well-formed directive whose type is outside any vocabulary."""

    def decide(self, **_kwargs) -> BehaviorCallResult:
        return BehaviorCallResult(
            directive_type="brandish",
            directive_params={},
            directive_error=None,
            reputation_delta=0.1,
            delta_error=None,
            input_tokens=1,
            output_tokens=1,
        )


class SalvagedBehaviorProvider:
    """Behavior call succeeds; directive and delta are field-wise malformed
    (the parse salvages: directive dropped, delta zeroed, NOT degraded)."""

    def decide(self, **_kwargs) -> BehaviorCallResult:
        return BehaviorCallResult(
            directive_type=None,
            directive_params={},
            directive_error="malformed directive shape: 42",
            reputation_delta=None,
            delta_error="reputation_delta missing or non-numeric: None",
            input_tokens=1,
            output_tokens=1,
        )


async def run_turn(gen) -> tuple[str, DialogueTurnResult]:
    """Drain the async-generator seam to (streamed_prose, terminal_result)."""
    chunks: list[str] = []
    result: DialogueTurnResult | None = None
    async for item in gen:
        if isinstance(item, DialogueTurnResult):
            result = item
        else:
            chunks.append(item)
    if result is None:
        raise AssertionError("seam yielded no terminal result")
    return "".join(chunks), result


async def make_agent(pool, name: str, config: dict, *, reputation=0.0, sensitivity=1.0):
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO agents (name, seed_identity, reputation, rigidity, "
            "reputation_sensitivity, diagnosticity_goal, config) "
            "VALUES (%s, %s, %s, 1.0, %s, %s, %s) RETURNING agent_id",
            (
                name,
                "A verification NPC who tends the forge.",
                reputation,
                sensitivity,
                "what threatens the forge",
                Jsonb(config),
            ),
        )
        return (await cur.fetchone())[0]


async def fetchval(pool, sql: str, *params):
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(sql, params)
        return (await cur.fetchone())[0]


async def execute(pool, sql: str, *params) -> None:
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(sql, params)


async def seed(ingest: IngestService, agent_id, text: str, valid_at):
    result = await ingest.ingest_observation(
        ObserveEvent(
            agent_id=agent_id,
            observation_text=text,
            phase_tag="walker",
            client_timestamp=valid_at,
            provenance="lived",
        )
    )
    return result.memory_id


def request(agent_id, **overrides) -> DialogueTurnRequest:
    base = dict(
        agent_id=agent_id,
        utterance=UTTERANCE,
        reputation_snapshot=0.0,
        as_of=NOW,
    )
    base.update(overrides)
    return DialogueTurnRequest(**base)


def crafted_item(memory_id, score, relevance, recency, importance_norm):
    """A synthetic served item for the pure re-rank tests (score is consistent
    with rel*rec*imp so parity is exact)."""
    return RetrievedMemory(
        memory_id=memory_id,
        detail_id=uuid4(),
        content="x",
        read_mode="verbatim",
        pinned=False,
        score=score,
        relevance=relevance,
        recency=recency,
        importance_norm=importance_norm,
        importance_raw=importance_norm,
    )


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


async def main(database_uri: str) -> None:
    settings = Settings(database_uri=database_uri, provider_mode="fake")
    pool = build_pool(database_uri)
    await pool.open()
    providers = bundle()
    ingest = IngestService(pool, providers, settings)
    retrieval = RetrievalService(pool, providers, settings)
    dialogue = DialogueService(pool, providers, settings, retrieval)

    def service_with(dialogue=None, behavior=None) -> DialogueService:
        return DialogueService(pool, bundle(dialogue, behavior), settings, retrieval)

    print(f"walker: scratch DB = {urlsplit(database_uri).path.lstrip('/')}")

    agent_a = await make_agent(pool, "cli-walker-npc-a", AGENT_CONFIG)
    await seed(ingest, agent_a, T_FORGE, NOW - timedelta(hours=1))
    await seed(ingest, agent_a, T_ROAD, NOW - timedelta(hours=3))
    await seed(ingest, agent_a, T_TAX, NOW - timedelta(hours=26))

    # ------------------------------------------------------------------ #
    print("\n[1] Turn happy path (streaming seam, fake providers)")
    prose1, r1 = await run_turn(dialogue.run_dialogue_turn(request(agent_a)))
    check(
        bool(prose1) and r1.content == prose1, "seam streams prose; content == chunks"
    )
    check(
        r1.directive is not None
        and r1.directive.type == VOCAB[0]
        and isinstance(r1.directive.params, dict)
        and not r1.directive_dropped,
        "behavior call directive from the agents.config vocabulary",
        f"type={r1.directive.type}",
    )
    check(
        isinstance(r1.reputation_delta, float)
        and r1.reputation_delta_source == "model",
        "reputation_delta emitted by the behavior call",
        f"delta={r1.reputation_delta}",
    )
    check(
        len(r1.items) == 3
        and all(
            item.memory_id and item.score is not None and item.recency is not None
            for item in r1.items
        ),
        "retrieval echo: memory_ids + score components ride in the result",
    )
    ins = r1.instrumentation
    for name in (
        "sonnet_ms",
        "sonnet_first_token_ms",
        "first_word_ms",
        "prose_stream_ms",
        "behavior_ms",
        "apply_ms",
        "total_ms",
    ):
        if getattr(ins, name) is None or getattr(ins, name) < 0:
            fail("turn instrumentation", f"{name} = {getattr(ins, name)}")
    check(
        ins.first_word_ms == ins.sonnet_first_token_ms
        and ins.prose_stream_ms == ins.sonnet_ms,
        "first_word_ms == prose TTFT; prose_stream_ms == prose total",
    )
    check(
        ins.retrieval.total_ms >= 0
        and ins.sonnet_input_tokens > 0
        and ins.sonnet_output_tokens > 0
        and ins.behavior_input_tokens > 0
        and ins.behavior_output_tokens > 0
        and ins.degraded is False,
        "instrumentation non-null: retrieval, prose + behavior timings + tokens",
    )
    check(ins.cost_usd is None, "cost_usd null when no LONGMEM_PRICE_* configured")
    try:
        await run_turn(dialogue.run_dialogue_turn(request(uuid4())))
        fail("unknown agent", "no exception raised")
    except UnknownAgentError:
        ok("unknown agent_id raises UnknownAgentError")

    # ------------------------------------------------------------------ #
    print("\n[2] Prompt split: prose prompt vs behavior prompt")
    p1 = assemble_prose_prompt("Seed prose.", 0.25, -1.0, 1.0, r1.items, [])
    p2 = assemble_prose_prompt("Seed prose.", 0.25, -1.0, 1.0, r1.items, [])
    check(p1 == p2, "identical inputs assemble byte-identical prose prompts")
    order = [
        p1.index(b) for b in ("[identity]", "[reputation]", "[memories]", "[output]")
    ]
    check(order == sorted(order), "prose prompt blocks ride in spec order")
    check(
        all(str(item.memory_id) in p1 for item in r1.items),
        "retrieved memory IDs carried into the prose prompt",
    )
    check(
        "reputation_delta" not in p1 and "directive" not in p1,
        "prose prompt is pure-prose: no directive/delta JSON contract",
    )
    bp = assemble_behavior_prompt("Seed prose.", 0.25, -1.0, 1.0, r1.items, VOCAB)
    check(
        "[identity]" in bp and "[reputation]" in bp and "[memories]" in bp,
        "behavior prompt shares identity + reputation + memories (asymmetry statistical)",
    )
    check(
        "directive" in bp and "reputation_delta" in bp and all(v in bp for v in VOCAB),
        "behavior prompt carries the directive+delta JSON contract + vocabulary",
    )
    # done-when 5: the recent-actions block rides the PROSE prompt iff present,
    # and NEVER the behavior prompt.
    ra = [RecentAction(type="warn", params={}, at=NOW)]
    p_with = assemble_prose_prompt("Seed prose.", 0.0, -1.0, 1.0, r1.items, ra)
    check(
        "[recent actions]" in p_with and "warn" in p_with,
        "prose prompt carries the recent-actions block when scene actions exist",
    )
    check(
        "[recent actions]" not in p1
        and "[recent actions]"
        not in assemble_behavior_prompt("S", 0.0, -1.0, 1.0, r1.items, VOCAB),
        "recent-actions block absent with no actions and never in the behavior prompt",
    )

    # ------------------------------------------------------------------ #
    print("\n[3] Reputation persists in-place; math + clamp; override wins")
    row_value = await fetchval(
        pool, "SELECT reputation FROM agents WHERE agent_id = %s", agent_a
    )
    check(
        float(row_value) == r1.reputation_after,
        "agents.reputation row equals reputation_after",
        f"row={float(row_value)}",
    )
    expected = clamp(
        r1.reputation_prev + r1.reputation_sensitivity * r1.reputation_delta, -1.0, 1.0
    )
    check(
        abs(r1.reputation_after - expected) < 1e-9,
        "after == clamp(prev + sensitivity x delta)",
    )
    _p, r_ovr = await run_turn(
        dialogue.run_dialogue_turn(request(agent_a, reputation_delta_override=0.25))
    )
    check(
        r_ovr.reputation_delta == 0.25
        and r_ovr.reputation_delta_source == "override"
        and abs(
            r_ovr.reputation_after
            - clamp(r_ovr.reputation_prev + r_ovr.reputation_sensitivity * 0.25, -1, 1)
        )
        < 1e-9,
        "client reputation_delta_override wins over the behavior delta",
    )
    await execute(
        pool, "UPDATE agents SET reputation = 0.95 WHERE agent_id = %s", agent_a
    )
    _p, r_clamp = await run_turn(
        dialogue.run_dialogue_turn(request(agent_a, reputation_delta_override=1.0))
    )
    check(
        r_clamp.reputation_after == 1.0,
        "delta exceeding the scale clamps to scale_max, never throws",
    )
    agent_c = await make_agent(
        pool,
        "cli-walker-npc-c",
        {**AGENT_CONFIG, "reputation_sensitivity_default": 2.0},
        sensitivity=None,
    )
    _p, r_sens = await run_turn(
        dialogue.run_dialogue_turn(request(agent_c, reputation_delta_override=0.1))
    )
    check(
        r_sens.reputation_sensitivity == 2.0
        and abs(r_sens.reputation_after - (r_sens.reputation_prev + 0.2)) < 1e-9,
        "NULL sensitivity column falls back to the agents.config knob",
    )

    # ------------------------------------------------------------------ #
    print("\n[4] SessionRunner passthrough + frozen snapshot + recent-actions")
    await execute(pool, "UPDATE agents SET reputation = 0 WHERE agent_id = %s", agent_a)
    mem_before = await fetchval(
        pool, "SELECT count(*) FROM memories WHERE agent_id = %s", agent_a
    )
    runner = await SessionRunner.create(
        agent_a, settings=settings, providers=providers, pool=pool, phase_tag="walker"
    )
    runner.as_of = NOW
    s0 = runner.reputation_snapshot
    check(s0 == 0.0, "scene-start snapshot read from the row", f"snapshot={s0}")
    t1 = await runner.utterance(UTTERANCE, reputation_delta_override=0.3)
    check(
        len(runner.recent_actions) == 1 and runner.recent_actions[0].type == VOCAB[0],
        "resolved directive appended to the caller-held recent-actions block",
    )
    t2 = await runner.utterance(UTTERANCE, reputation_delta_override=0.2)
    check(
        t1.reputation_snapshot == s0 and t2.reputation_snapshot == s0,
        "snapshot frozen within the scene while deltas accumulate",
    )
    check(
        t2.reputation_prev == t1.reputation_after,
        "mid-scene deltas accumulate on the row",
        f"prev={t2.reputation_prev}",
    )
    mem_after = await fetchval(
        pool, "SELECT count(*) FROM memories WHERE agent_id = %s", agent_a
    )
    check(
        int(mem_before) == int(mem_after),
        "recent-actions are caller-held: turns write no memory rows",
    )
    scene_result = await runner.scene()
    check(
        scene_result.accepted
        and runner.reputation_snapshot == t2.reputation_after
        and runner.recent_actions == [],
        "scene boundary refreshes the snapshot and RESETS recent-actions",
        f"snapshot={runner.reputation_snapshot}",
    )
    t3 = await runner.utterance(UTTERANCE, reputation_delta_override=0.0)
    check(
        t3.reputation_snapshot == t2.reputation_after,
        "next scene's prompt sees the accumulated reputation",
    )

    # ------------------------------------------------------------------ #
    print("\n[5] Deterministic fake: byte-identical structured output")
    await execute(pool, "UPDATE agents SET reputation = 0 WHERE agent_id = %s", agent_a)
    p_d1, d1 = await run_turn(dialogue.run_dialogue_turn(request(agent_a)))
    await execute(pool, "UPDATE agents SET reputation = 0 WHERE agent_id = %s", agent_a)
    p_d2, d2 = await run_turn(dialogue.run_dialogue_turn(request(agent_a)))
    check(
        p_d1 == p_d2
        and d1.directive.model_dump() == d2.directive.model_dump()
        and d1.reputation_delta == d2.reputation_delta,
        "two identical turns: byte-identical prose / directive / delta",
    )
    check(
        d1.reputation_prev == d2.reputation_prev
        and d1.reputation_after == d2.reputation_after,
        "two identical turns: identical reputation math",
    )
    check(
        [i.memory_id for i in d1.items] == [i.memory_id for i in d2.items]
        and [i.content for i in d1.items] == [i.content for i in d2.items],
        "repeated reads byte-identical within the scene (served items)",
    )

    # ------------------------------------------------------------------ #
    print("\n[6] Two scored views: dialogue-view parity + behavior re-rank")
    # done-when 7: the divergence record rides the result (same served set).
    check(
        {r.memory_id for r in d1.dialogue_view} == {i.memory_id for i in d1.items}
        and {r.memory_id for r in d1.behavior_view} == {i.memory_id for i in d1.items},
        "divergence record: dialogue_view + behavior_view over the served set",
    )
    # done-when 6 parity: no overrides => behavior view order == dialogue order,
    # scores byte-identical (the reserved slot stays inert at 1.0).
    check(
        [r.memory_id for r in d1.dialogue_view]
        == [r.memory_id for r in d1.behavior_view]
        and [r.score for r in d1.dialogue_view] == [r.score for r in d1.behavior_view],
        "no overrides: behavior view is byte-identical to the dialogue view (parity)",
    )
    # Pure re-rank proof on crafted items (deterministic, no model call):
    id_hi, id_lo = uuid4(), uuid4()
    # A: score 0.5 (rel .5, rec 1.0);  B: score 0.6 (rel .9, rec .6667).
    item_a = crafted_item(id_lo, 0.5, 0.5, 1.0, 1.0)
    item_b = crafted_item(id_hi, 0.6, 0.9, 2.0 / 3.0, 1.0)
    parity = rank_behavior_view([item_b, item_a], (1.0, 1.0, 1.0))
    check(
        [it.memory_id for _s, it in parity] == [id_hi, id_lo],
        "parity: weights (1,1,1) keep the dialogue score order",
    )
    # w_rel = 0 removes relevance emphasis => A (0.5/0.5=1.0) outranks B (0.6/0.9):
    reranked = rank_behavior_view([item_b, item_a], (0.0, 1.0, 1.0))
    check(
        [it.memory_id for _s, it in reranked] == [id_lo, id_hi],
        "re-rank: a relevance-de-emphasis weight flips the behavior view order",
    )
    check(
        abs(behavior_score(item_a, 0.0, 1.0, 1.0) - 1.0) < 1e-9
        and abs(behavior_score(item_a, 1.0, 1.0, 1.0) - 0.5) < 1e-9,
        "behavior_score is exponent-form: 1.0 reproduces the score, else re-weights",
    )
    check(
        resolve_behavior_weights({}, None, settings) == (1.0, 1.0, 1.0)
        and resolve_behavior_weights(
            {}, WeightOverrides(relevance=99.0, recency=-5.0), settings
        )
        == (4.0, 0.0, 1.0),
        "weight resolution: 1.0 defaults, request wins, clamped to [0, 4]",
    )

    # ------------------------------------------------------------------ #
    print("\n[7] Concurrency: prose streams before the behavior call completes")
    slow = service_with(behavior=SlowBehaviorProvider())
    t_start = _time.perf_counter()
    first_chunk_at = None
    r_slow = None
    async for item in slow.run_dialogue_turn(request(agent_a)):
        if isinstance(item, DialogueTurnResult):
            r_slow = item
        elif first_chunk_at is None:
            first_chunk_at = _time.perf_counter() - t_start
    check(
        first_chunk_at is not None
        and first_chunk_at < SlowBehaviorProvider.SLEEP_SECONDS,
        "first prose chunk arrives BEFORE the slow behavior completes (done-when 1)",
        f"first_chunk={first_chunk_at:.3f}s < {SlowBehaviorProvider.SLEEP_SECONDS}s",
    )
    check(
        r_slow.instrumentation.behavior_ms
        >= SlowBehaviorProvider.SLEEP_SECONDS * 1000 * 0.9
        and r_slow.instrumentation.first_word_ms < r_slow.instrumentation.behavior_ms,
        "behavior_ms captures the slow leg; first_word_ms precedes it",
        f"first_word={r_slow.instrumentation.first_word_ms} beh={r_slow.instrumentation.behavior_ms}",
    )

    # ------------------------------------------------------------------ #
    print("\n[8] Action directive soft-fails (dropped, turn succeeds)")
    _p, r_off = await run_turn(
        service_with(behavior=OffVocabBehaviorProvider()).run_dialogue_turn(
            request(agent_a)
        )
    )
    check(
        r_off.directive is None
        and r_off.directive_dropped
        and "unknown directive type" in r_off.directive_dropped_reason
        and bool(r_off.content)
        and not r_off.instrumentation.degraded,
        "unknown directive type: dropped with reason, prose still streamed",
    )
    agent_b = await make_agent(
        pool,
        "cli-walker-npc-b",
        {k: v for k, v in AGENT_CONFIG.items() if k != "action_vocabulary"},
    )
    _p, r_novocab = await run_turn(
        service_with(behavior=OffVocabBehaviorProvider()).run_dialogue_turn(
            request(agent_b)
        )
    )
    check(
        r_novocab.directive_dropped
        and r_novocab.directive_dropped_reason == "no vocabulary configured",
        "no vocabulary configured anywhere: directive dropped, turn succeeds",
    )
    _p, r_pervocab = await run_turn(
        service_with(behavior=OffVocabBehaviorProvider()).run_dialogue_turn(
            request(agent_b, action_vocabulary=["brandish"])
        )
    )
    check(
        r_pervocab.directive is not None and r_pervocab.directive.type == "brandish",
        "per-call vocabulary wins over the (absent) config vocabulary",
    )
    prose_s, r_salvage = await run_turn(
        service_with(behavior=SalvagedBehaviorProvider()).run_dialogue_turn(
            request(agent_a)
        )
    )
    check(
        r_salvage.content == prose_s
        and bool(prose_s)
        and r_salvage.directive_dropped
        and r_salvage.reputation_delta == 0.0
        and r_salvage.reputation_delta_source == "zeroed"
        and not r_salvage.instrumentation.degraded,
        "malformed directive+delta: prose survives, directive dropped, delta zeroed",
    )

    # ------------------------------------------------------------------ #
    print("\n[9] Never-blank ladder: the four split-brain degradation rows")
    before = float(
        await fetchval(
            pool, "SELECT reputation FROM agents WHERE agent_id = %s", agent_a
        )
    )
    # row 1: behavior fails -> prose survives, directive None, delta zeroed.
    prose_bf, r_bf = await run_turn(
        service_with(behavior=FailingBehaviorProvider()).run_dialogue_turn(
            request(agent_a)
        )
    )
    check(
        bool(prose_bf)
        and r_bf.content == prose_bf
        and r_bf.content != FALLBACK_LINE
        and r_bf.directive is None
        and r_bf.reputation_delta == 0.0
        and r_bf.reputation_after == before
        and r_bf.instrumentation.degraded
        and "behavior call failed" in r_bf.instrumentation.degraded_reason,
        "behavior fails: prose kept, directive None, delta zeroed, row unchanged",
    )
    # row 2: prose fails BEFORE the first chunk -> fallback line, behavior lands.
    _p, r_pf = await run_turn(
        service_with(dialogue=FailingProseProvider()).run_dialogue_turn(
            request(agent_a)
        )
    )
    check(
        r_pf.content == FALLBACK_LINE
        and r_pf.instrumentation.degraded
        and "prose call failed" in r_pf.instrumentation.degraded_reason
        and r_pf.directive is not None,
        "prose fails pre-chunk: fallback line, but the behavior directive lands",
    )
    # row 3: prose drops mid-stream -> keep the partial (ruled 2026-07-21).
    prose_md, r_md = await run_turn(
        service_with(dialogue=MidStreamDropProseProvider()).run_dialogue_turn(
            request(agent_a)
        )
    )
    check(
        prose_md == "partial prose"
        and r_md.content == prose_md
        and r_md.content != FALLBACK_LINE
        and r_md.instrumentation.degraded
        and "mid-stream" in r_md.instrumentation.degraded_reason,
        "prose drops mid-stream: the partial is kept + degraded flag",
    )
    # row 4: both legs fail -> fallback + zeroed + flags (never-blank holds).
    _p, r_both = await run_turn(
        service_with(
            dialogue=FailingProseProvider(), behavior=FailingBehaviorProvider()
        ).run_dialogue_turn(request(agent_a))
    )
    check(
        r_both.content == FALLBACK_LINE
        and r_both.directive is None
        and r_both.reputation_delta == 0.0
        and r_both.instrumentation.degraded,
        "both legs fail: fallback line + zeroed delta + degraded",
    )
    # malformed behavior spend still accounted.
    _p, r_malb = await run_turn(
        service_with(behavior=MalformedBehaviorProvider()).run_dialogue_turn(
            request(agent_a)
        )
    )
    check(
        r_malb.directive is None
        and r_malb.instrumentation.degraded
        and r_malb.instrumentation.behavior_input_tokens == 7
        and r_malb.instrumentation.behavior_output_tokens == 3,
        "malformed behavior: no directive, spend accounted",
    )

    # ------------------------------------------------------------------ #
    print("\n[10] Debug view surfaces IDs, scores, split-brain views + counts")
    view = render_debug(r1)
    check(
        all(str(item.memory_id) in view for item in r1.items),
        "debug view carries every retrieved memory_id",
    )
    check(
        f"score={r1.items[0].score:.4f}" in view
        and str(r1.reputation_delta) in view
        and f"first_word={r1.instrumentation.first_word_ms}" in view
        and f"in={r1.instrumentation.behavior_input_tokens}" in view,
        "debug view carries scores, delta, first_word, behavior token counts",
    )
    check(
        "split-brain views" in view and str(r1.dialogue_view[0].memory_id)[:8] in view,
        "debug view carries the divergence record (both scored views)",
    )

    # ------------------------------------------------------------------ #
    print("\n[11] Per-turn cost populated when prices are configured")
    priced = Settings(
        database_uri=database_uri,
        provider_mode="fake",
        prices={
            "dialogue_in": 3.0,
            "dialogue_out": 15.0,
            "behavior_in": 1.0,
            "behavior_out": 5.0,
            "embedding": 0.02,
        },
    )
    _p, r_priced = await run_turn(
        DialogueService(
            pool, providers, priced, RetrievalService(pool, providers, priced)
        ).run_dialogue_turn(request(agent_a))
    )
    check(
        r_priced.instrumentation.cost_usd is not None
        and r_priced.instrumentation.cost_usd > 0,
        "cost_usd computed from configured prose + behavior + embedding prices",
        f"${r_priced.instrumentation.cost_usd}",
    )

    # ------------------------------------------------------------------ #
    print("\n[12] Load driver: scripted sessions offline, §11 aggregates")
    report = await run_driver(settings, sessions=2, turns=3, seed=1)
    check(
        report["sessions"] == 2 and report["turns"] == 6,
        "scripted N-session run completed offline and keyless",
        f"{report['turns']} turns, {report['observes']} observes",
    )
    for series in (
        "retrieval_sql",
        "query_embed",
        "first_word",
        "behavior",
        "dialogue_total",
        "turn_total",
    ):
        row = report["latency_ms"].get(series)
        if row is None or row["p50"] < 0 or row["p95"] < row["p50"]:
            fail("latency aggregates", f"{series}: {row}")
    ok(
        "latency p50/p95 emitted for every §11 series incl. first_word + behavior "
        "(the gate term is asserted in verify_gate.py)"
    )
    check(
        report["per_100_turns"]["dialogue"]["input_tokens_per_100_turns"] > 0
        and report["per_100_turns"]["behavior"]["input_tokens_per_100_turns"] > 0
        and report["per_100_turns"]["dialogue"]["usd_per_100_turns"] is None
        and report["degraded_turns"] == 0,
        "per-100-turn table itemized incl. the behavior cost row; USD unpriced -> null",
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
