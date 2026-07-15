"""verify_cli_harness.py — structural done-when walker for CLI-harness v1
(dialogue turn + reputation + load driver, docs\\cli-harness.md).

Runs the cli-harness done-when criteria against the SCRATCH database
(default: the .env DATABASE_URI with its database name swapped to
`longmem_test`), with deterministic fake providers — offline, keyless, and
structural-only per tests\\CLAUDE.md: assertions touch IDs, flags, score
components, reputation math, and byte-identity, never generated prose
content. The schema-frozen criterion (`db\\migrate.py` no-arg is a clean
no-op on `longmem`) runs outside this walker.

Seeding goes through the real IngestService (staged verification against the
write-path floor); retrieval rides the read-path floor; fixture SQL touches
only the agents fixture rows (reputation resets between determinism runs).

Prerequisite (PowerShell):
    python db\\migrate.py --database-uri <scratch-uri>
Run:
    python tests\\verify_cli_harness.py [--database-uri <scratch-uri>]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
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
from app.dialogue import DialogueService, assemble_system_prompt
from app.ingest import IngestService, UnknownAgentError
from app.load_driver import run_driver
from app.providers import (
    DialogueCallResult,
    FailingDialogueProvider,
    FakeDialogueProvider,
    FakeEmbeddingProvider,
    FakeEscalationProvider,
    FakeWriteProvider,
    MalformedDialogueProvider,
    Providers,
)
from app.retrieval import RetrievalService
from app.schemas import DialogueTurnRequest, ObserveEvent
from app.session import SessionRunner

NOW = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)

FALLBACK_LINE = "[fallback] The smith stares into the coals."
VOCAB = ["greet", "warn"]

AGENT_CONFIG = {
    "decay_classes": {"episodic": 86400, "semantic": 604800},
    "decay_class_default": "episodic",
    "action_vocabulary": VOCAB,
    "dialogue_fallback_line": FALLBACK_LINE,
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


def bundle(dialogue=None) -> Providers:
    return Providers(
        write=FakeWriteProvider(),
        escalation=FakeEscalationProvider(),
        embedding=FakeEmbeddingProvider(),
        dialogue=dialogue if dialogue is not None else FakeDialogueProvider(),
    )


# --- walker-local dialogue fakes (ladder rows the shipped fakes don't hit) --


class OffVocabDialogueProvider:
    """Emits a well-formed directive whose type is outside any vocabulary."""

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


class SalvagedDialogueProvider:
    """Prose parses; directive and delta are malformed (field-wise salvage)."""

    def generate(self, **_kwargs) -> DialogueCallResult:
        return DialogueCallResult(
            prose="[salvaged] line",
            directive_type=None,
            directive_params={},
            directive_error="malformed directive shape: 42",
            reputation_delta=None,
            delta_error="reputation_delta missing or non-numeric: None",
            input_tokens=1,
            output_tokens=1,
            first_token_ms=0.0,
        )


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

    def service_with(dialogue_provider) -> DialogueService:
        return DialogueService(pool, bundle(dialogue_provider), settings, retrieval)

    print(f"walker: scratch DB = {urlsplit(database_uri).path.lstrip('/')}")

    agent_a = await make_agent(pool, "cli-walker-npc-a", AGENT_CONFIG)
    await seed(ingest, agent_a, T_FORGE, NOW - timedelta(hours=1))
    await seed(ingest, agent_a, T_ROAD, NOW - timedelta(hours=3))
    await seed(ingest, agent_a, T_TAX, NOW - timedelta(hours=26))

    # ------------------------------------------------------------------ #
    print("\n[1] Turn happy path (fake provider)")
    r1 = await dialogue.run_dialogue_turn(request(agent_a))
    check(bool(r1.content), "turn returns content")
    check(
        r1.directive is not None
        and r1.directive.type == VOCAB[0]
        and isinstance(r1.directive.params, dict)
        and not r1.directive_dropped,
        "parsed directive from the agents.config vocabulary",
        f"type={r1.directive.type}",
    )
    check(
        isinstance(r1.reputation_delta, float)
        and r1.reputation_delta_source == "model",
        "reputation_delta emitted by the model call",
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
    for name in ("sonnet_ms", "sonnet_first_token_ms", "apply_ms", "total_ms"):
        if getattr(ins, name) is None or getattr(ins, name) < 0:
            fail("turn instrumentation", f"{name} = {getattr(ins, name)}")
    check(
        ins.retrieval.total_ms >= 0
        and ins.sonnet_input_tokens > 0
        and ins.sonnet_output_tokens > 0
        and ins.degraded is False,
        "instrumentation non-null: nested retrieval, dialogue timings, tokens",
    )
    check(ins.cost_usd is None, "cost_usd null when no LONGMEM_PRICE_* configured")
    try:
        await dialogue.run_dialogue_turn(request(uuid4()))
        fail("unknown agent", "no exception raised")
    except UnknownAgentError:
        ok("unknown agent_id raises UnknownAgentError")

    # ------------------------------------------------------------------ #
    print("\n[2] Prompt assembly: labeled blocks, deterministic bytes")
    p1 = assemble_system_prompt("Seed prose.", 0.25, -1.0, 1.0, r1.items, VOCAB)
    p2 = assemble_system_prompt("Seed prose.", 0.25, -1.0, 1.0, r1.items, VOCAB)
    check(p1 == p2, "identical inputs assemble byte-identical prompts")
    order = [
        p1.index(b) for b in ("[identity]", "[reputation]", "[memories]", "[output]")
    ]
    check(order == sorted(order), "blocks ride in spec order")
    check(
        all(str(item.memory_id) in p1 for item in r1.items),
        "retrieved memory IDs carried into the prompt block",
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
        r1.reputation_prev + r1.reputation_sensitivity * r1.reputation_delta,
        -1.0,
        1.0,
    )
    check(
        abs(r1.reputation_after - expected) < 1e-9,
        "after == clamp(prev + sensitivity x delta)",
    )
    r_ovr = await dialogue.run_dialogue_turn(
        request(agent_a, reputation_delta_override=0.25)
    )
    check(
        r_ovr.reputation_delta == 0.25
        and r_ovr.reputation_delta_source == "override"
        and abs(
            r_ovr.reputation_after
            - clamp(r_ovr.reputation_prev + r_ovr.reputation_sensitivity * 0.25, -1, 1)
        )
        < 1e-9,
        "client reputation_delta_override wins over the model delta",
    )
    await execute(
        pool, "UPDATE agents SET reputation = 0.95 WHERE agent_id = %s", agent_a
    )
    r_clamp = await dialogue.run_dialogue_turn(
        request(agent_a, reputation_delta_override=1.0)
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
    r_sens = await dialogue.run_dialogue_turn(
        request(agent_c, reputation_delta_override=0.1)
    )
    check(
        r_sens.reputation_sensitivity == 2.0
        and abs(r_sens.reputation_after - (r_sens.reputation_prev + 0.2)) < 1e-9,
        "NULL sensitivity column falls back to the agents.config knob",
    )

    # ------------------------------------------------------------------ #
    print("\n[4] One seam, thin caller: SessionRunner passthrough + frozen snapshot")
    await execute(pool, "UPDATE agents SET reputation = 0 WHERE agent_id = %s", agent_a)
    runner = await SessionRunner.create(
        agent_a, settings=settings, providers=providers, pool=pool, phase_tag="walker"
    )
    runner.as_of = NOW
    s0 = runner.reputation_snapshot
    check(s0 == 0.0, "scene-start snapshot read from the row", f"snapshot={s0}")
    t1 = await runner.utterance(UTTERANCE, reputation_delta_override=0.3)
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
    scene_result = await runner.scene()
    check(
        scene_result.accepted and runner.reputation_snapshot == t2.reputation_after,
        "scene boundary refreshes the snapshot to the accumulated value",
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
    d1 = await dialogue.run_dialogue_turn(request(agent_a))
    await execute(pool, "UPDATE agents SET reputation = 0 WHERE agent_id = %s", agent_a)
    d2 = await dialogue.run_dialogue_turn(request(agent_a))
    check(
        d1.content == d2.content
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
    print("\n[6] Action directive soft-fails (dropped, turn succeeds)")
    r_off = await service_with(OffVocabDialogueProvider()).run_dialogue_turn(
        request(agent_a)
    )
    check(
        r_off.directive is None
        and r_off.directive_dropped
        and "unknown directive type" in r_off.directive_dropped_reason
        and bool(r_off.content)
        and not r_off.instrumentation.degraded,
        "unknown directive type: dropped with reason, prose still returned",
    )
    agent_b = await make_agent(
        pool,
        "cli-walker-npc-b",
        {k: v for k, v in AGENT_CONFIG.items() if k != "action_vocabulary"},
    )
    r_novocab = await service_with(OffVocabDialogueProvider()).run_dialogue_turn(
        request(agent_b)
    )
    check(
        r_novocab.directive_dropped
        and r_novocab.directive_dropped_reason == "no vocabulary configured",
        "no vocabulary configured anywhere: directive dropped, turn succeeds",
    )
    r_pervocab = await service_with(OffVocabDialogueProvider()).run_dialogue_turn(
        request(agent_b, action_vocabulary=["brandish"])
    )
    check(
        r_pervocab.directive is not None and r_pervocab.directive.type == "brandish",
        "per-call vocabulary wins over the (absent) config vocabulary",
    )
    r_salvage = await service_with(SalvagedDialogueProvider()).run_dialogue_turn(
        request(agent_a)
    )
    check(
        r_salvage.content == "[salvaged] line"
        and r_salvage.directive_dropped
        and r_salvage.reputation_delta == 0.0
        and r_salvage.reputation_delta_source == "zeroed"
        and not r_salvage.instrumentation.degraded,
        "malformed directive+delta: prose salvaged, directive dropped, delta zeroed",
    )

    # ------------------------------------------------------------------ #
    print("\n[7] Never-blank-a-dialogue (failing + malformed providers)")
    before = float(
        await fetchval(
            pool, "SELECT reputation FROM agents WHERE agent_id = %s", agent_a
        )
    )
    r_fail = await service_with(FailingDialogueProvider()).run_dialogue_turn(
        request(agent_a)
    )
    check(
        r_fail.content == FALLBACK_LINE
        and r_fail.instrumentation.degraded
        and "dialogue call failed" in r_fail.instrumentation.degraded_reason,
        "failed call: configured fallback line + degraded flag, not an exception",
    )
    check(
        r_fail.reputation_delta == 0.0
        and r_fail.reputation_delta_source == "zeroed"
        and r_fail.reputation_after == before,
        "failed call: delta zeroed, row unchanged",
    )
    r_mal = await service_with(MalformedDialogueProvider()).run_dialogue_turn(
        request(agent_a)
    )
    check(
        r_mal.content == FALLBACK_LINE
        and r_mal.instrumentation.degraded
        and r_mal.instrumentation.sonnet_input_tokens == 7
        and r_mal.instrumentation.sonnet_output_tokens == 3,
        "unsalvageable output: fallback line; token spend still accounted",
    )

    # ------------------------------------------------------------------ #
    print("\n[8] Debug view surfaces IDs, scores, parsed output, counts")
    view = render_debug(r1)
    check(
        all(str(item.memory_id) in view for item in r1.items),
        "debug view carries every retrieved memory_id",
    )
    check(
        f"score={r1.items[0].score:.4f}" in view
        and str(r1.reputation_delta) in view
        and f"in={r1.instrumentation.sonnet_input_tokens}" in view,
        "debug view carries score components, delta, and token counts",
    )

    # ------------------------------------------------------------------ #
    print("\n[9] Per-turn cost populated when prices are configured")
    priced = Settings(
        database_uri=database_uri,
        provider_mode="fake",
        prices={"dialogue_in": 3.0, "dialogue_out": 15.0, "embedding": 0.02},
    )
    r_priced = await DialogueService(
        pool, providers, priced, RetrievalService(pool, providers, priced)
    ).run_dialogue_turn(request(agent_a))
    check(
        r_priced.instrumentation.cost_usd is not None
        and r_priced.instrumentation.cost_usd > 0,
        "cost_usd computed from configured prices",
        f"${r_priced.instrumentation.cost_usd}",
    )

    # ------------------------------------------------------------------ #
    print("\n[10] Load driver: scripted sessions offline, §11 aggregates")
    report = await run_driver(settings, sessions=2, turns=3, seed=1)
    check(
        report["sessions"] == 2 and report["turns"] == 6,
        "scripted N-session run completed offline and keyless",
        f"{report['turns']} turns, {report['observes']} observes",
    )
    for series in (
        "retrieval_sql",
        "query_embed",
        "first_token",
        "dialogue_total",
        "turn_total",
    ):
        row = report["latency_ms"].get(series)
        if row is None or row["p50"] < 0 or row["p95"] < row["p50"]:
            fail("latency aggregates", f"{series}: {row}")
    ok("latency p50/p95 emitted for every §11 series (no gate term)")
    check(
        report["per_100_turns"]["dialogue"]["input_tokens_per_100_turns"] > 0
        and report["per_100_turns"]["dialogue"]["usd_per_100_turns"] is None
        and report["degraded_turns"] == 0,
        "per-100-turn table itemized; tokens unconditional, USD unpriced -> null",
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
