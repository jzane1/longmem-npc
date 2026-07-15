"""load_driver.py — the synthetic load driver: scripted sessions at volume.

A first-class artifact co-built with the CLI harness (architecture §11: "no
distribution exists without it"). It drives observe events, utterances, and
scene boundaries through the SAME shared session-runner core the REPL uses
(app\\session.py) — no divergent second path, no timing of its own: every
number below is read off the seams' instrumentation payloads.

    PowerShell:  python -m app.load_driver [--sessions 5] [--turns 10]
                     [--script path.json] [--seed 0] [--agent <uuid>]
                     [--database-uri <uri>] [--json out.json]

Runs offline and keyless on the deterministic fake providers by default
(LONGMEM_PROVIDER_MODE=fake); the real providers back a keyed smoke moment
ahead of demo choreography. Without --agent it creates a fresh driver agent
in the target database — point --database-uri at a scratch DB for clean
runs (verification uses longmem_test); the product DB stays untouched unless
you aim at it deliberately.

Script format (--script): a JSON list of sessions; each session is a list of
events: {"kind": "observe", "text": ...} | {"kind": "utterance", "text": ...,
"vocabulary": [types...]} | {"kind": "scene"}. Omitted, a seeded built-in
generator produces a deterministic mix (same seed -> same script -> same fake
outputs, byte for byte).

Emits the §11 aggregates: the latency histogram (p50/p95 — retrieval SQL,
query embed, first token, dialogue total, turn total; no gate term in the
slice) and the itemized per-100-turn cost table (tokens per model role,
unconditionally; USD only for roles priced via LONGMEM_PRICE_* — build
ruling 2026-07-15).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
from dataclasses import replace
from pathlib import Path
from uuid import UUID

from psycopg.types.json import Jsonb

from app.config import Settings, load_settings
from app.db import build_pool
from app.providers import build_providers
from app.schemas import DialogueTurnResult, IngestResult
from app.session import SessionRunner

# The generator is a stand-in integrator: callers own the action vocabulary,
# so the driver supplying one is contract-correct (nothing in the service
# defaults to it).
_GENERATOR_VOCABULARY = ["greet", "warn", "trade"]
_GENERATOR_TOPICS = [
    "the forge",
    "the north road",
    "the baron's tax",
    "the storm",
    "the market",
]

DRIVER_AGENT_CONFIG = {
    "decay_classes": {"episodic": 86400.0, "semantic": 604800.0},
    "decay_class_default": "episodic",
}


def generate_script(sessions: int, turns: int, seed: int) -> list[list[dict]]:
    """Deterministic synthetic sessions: same seed, same script."""
    rng = random.Random(seed)
    script: list[list[dict]] = []
    for s in range(sessions):
        events: list[dict] = []
        for t in range(turns):
            topic = rng.choice(_GENERATOR_TOPICS)
            if rng.random() < 0.4:
                events.append(
                    {
                        "kind": "observe",
                        "text": f"[s{s}t{t}] Something happened near {topic}.",
                    }
                )
            events.append(
                {
                    "kind": "utterance",
                    "text": f"[s{s}t{t}] Tell me about {topic}.",
                    "vocabulary": list(_GENERATOR_VOCABULARY),
                }
            )
            if t and t % 5 == 0:
                events.append({"kind": "scene"})
        script.append(events)
    return script


def percentile(values: list[float], q: float) -> float:
    """Linear-interpolated percentile; 0.0 on an empty series."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lo, hi = math.floor(index), math.ceil(index)
    if lo == hi:
        return round(ordered[lo], 2)
    return round(ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo), 2)


async def _create_driver_agent(pool) -> UUID:
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO agents (name, seed_identity, reputation, rigidity, "
            "reputation_sensitivity, diagnosticity_goal, config) "
            "VALUES (%s, %s, 0, 1.0, 1.0, %s, %s) RETURNING agent_id",
            (
                "load-driver",
                "A synthetic NPC standing in for load measurement.",
                "what matters to a load test",
                Jsonb(DRIVER_AGENT_CONFIG),
            ),
        )
        return (await cur.fetchone())[0]


async def run_driver(
    settings: Settings,
    *,
    sessions: int,
    turns: int,
    script: list[list[dict]] | None = None,
    seed: int = 0,
    agent_id: UUID | None = None,
) -> dict:
    """Drive the script through the seams; return the §11 aggregates.

    Separable from main() so the structural walker can run it in-process on
    an injected scratch Settings.
    """
    script = script if script is not None else generate_script(sessions, turns, seed)
    pool = build_pool(settings.database_uri)
    await pool.open()
    providers = build_providers(settings)
    turn_results: list[DialogueTurnResult] = []
    ingest_results: list[IngestResult] = []
    try:
        if agent_id is None:
            agent_id = await _create_driver_agent(pool)
        for events in script:
            runner = await SessionRunner.create(
                agent_id,
                settings=settings,
                providers=providers,
                pool=pool,
                phase_tag="load-driver",
                # Warm the NLP stack before the first measured event so model
                # load never lands inside a turn's numbers.
                warm_nlp=any(e["kind"] == "observe" for e in events),
            )
            for event in events:
                if event["kind"] == "observe":
                    ingest_results.append(await runner.observe(event["text"]))
                elif event["kind"] == "utterance":
                    turn_results.append(
                        await runner.utterance(
                            event["text"],
                            action_vocabulary=event.get("vocabulary"),
                        )
                    )
                elif event["kind"] == "scene":
                    await runner.scene()
                else:
                    raise ValueError(f"unknown script event kind {event['kind']!r}")
            await runner.close()  # pool is driver-owned; close is a no-op
    finally:
        await pool.close()
    report = _aggregate(settings, agent_id, turn_results, ingest_results)
    report["sessions"] = len(script)
    return report


def _aggregate(
    settings: Settings,
    agent_id: UUID,
    turns: list[DialogueTurnResult],
    observes: list[IngestResult],
) -> dict:
    prices = settings.prices
    series = {
        "retrieval_sql": [t.instrumentation.retrieval.sql_ms for t in turns],
        "query_embed": [t.instrumentation.retrieval.embed_ms for t in turns],
        "first_token": [t.instrumentation.sonnet_first_token_ms for t in turns],
        "dialogue_total": [t.instrumentation.sonnet_ms for t in turns],
        "turn_total": [t.instrumentation.total_ms for t in turns],
    }
    latency = {
        name: {"p50": percentile(values, 0.5), "p95": percentile(values, 0.95)}
        for name, values in series.items()
    }

    n_turns = max(len(turns), 1)

    def per_100(count: int) -> float:
        return round(count * 100.0 / n_turns, 1)

    def usd(tokens_in: int, tokens_out: int, key_in: str, key_out: str) -> float | None:
        if key_in in prices and key_out in prices:
            return round(
                (tokens_in * prices[key_in] + tokens_out * prices[key_out]) / 1e6, 6
            )
        return None

    dialogue_in = sum(t.instrumentation.sonnet_input_tokens for t in turns)
    dialogue_out = sum(t.instrumentation.sonnet_output_tokens for t in turns)
    write_in = sum(o.instrumentation.haiku_input_tokens for o in observes)
    write_out = sum(o.instrumentation.haiku_output_tokens for o in observes)
    esc_in = sum(o.instrumentation.escalation_input_tokens for o in observes)
    esc_out = sum(o.instrumentation.escalation_output_tokens for o in observes)
    embed_tokens = sum(o.instrumentation.embedding_tokens for o in observes) + sum(
        t.instrumentation.retrieval.embedding_tokens for t in turns
    )
    embed_usd = (
        round(embed_tokens * prices["embedding"] / 1e6, 6)
        if "embedding" in prices
        else None
    )
    cost = {
        "dialogue": {
            "input_tokens_per_100_turns": per_100(dialogue_in),
            "output_tokens_per_100_turns": per_100(dialogue_out),
            "usd_per_100_turns": usd(
                dialogue_in, dialogue_out, "dialogue_in", "dialogue_out"
            ),
        },
        "write": {
            "input_tokens_per_100_turns": per_100(write_in),
            "output_tokens_per_100_turns": per_100(write_out),
            "usd_per_100_turns": usd(write_in, write_out, "write_in", "write_out"),
        },
        "escalation": {
            "input_tokens_per_100_turns": per_100(esc_in),
            "output_tokens_per_100_turns": per_100(esc_out),
            "usd_per_100_turns": usd(
                esc_in, esc_out, "escalation_in", "escalation_out"
            ),
        },
        "embedding": {
            "tokens_per_100_turns": per_100(embed_tokens),
            "usd_per_100_turns": embed_usd,
        },
    }
    # Scale the USD table to per-100-turns too, when priced at all.
    for row in ("dialogue", "write", "escalation"):
        if cost[row]["usd_per_100_turns"] is not None:
            cost[row]["usd_per_100_turns"] = round(
                cost[row]["usd_per_100_turns"] * 100.0 / n_turns, 6
            )
    if cost["embedding"]["usd_per_100_turns"] is not None:
        cost["embedding"]["usd_per_100_turns"] = round(
            cost["embedding"]["usd_per_100_turns"] * 100.0 / n_turns, 6
        )
    return {
        "agent_id": str(agent_id),
        "turns": len(turns),
        "observes": len(observes),
        "latency_ms": latency,
        "per_100_turns": cost,
        "degraded_turns": sum(1 for t in turns if t.instrumentation.degraded),
    }


def _print_report(report: dict) -> None:
    print(
        f"\nagent {report['agent_id']} — {report['turns']} turns, "
        f"{report['observes']} observes, {report['degraded_turns']} degraded"
    )
    print("\nlatency (ms)                p50        p95")
    for name, row in report["latency_ms"].items():
        print(f"  {name:<24} {row['p50']:>8}   {row['p95']:>8}")
    print("\nper-100-turn cost           tokens (in/out)        USD")
    for role, row in report["per_100_turns"].items():
        if role == "embedding":
            tokens = f"{row['tokens_per_100_turns']}"
        else:
            tokens = (
                f"{row['input_tokens_per_100_turns']}/"
                f"{row['output_tokens_per_100_turns']}"
            )
        usd_val = row["usd_per_100_turns"]
        usd_text = f"${usd_val}" if usd_val is not None else "(unpriced)"
        print(f"  {role:<24} {tokens:>20}   {usd_text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="longmem-npc synthetic load driver")
    parser.add_argument("--sessions", type=int, default=5)
    parser.add_argument("--turns", type=int, default=10, help="turns per session")
    parser.add_argument("--script", type=Path, help="JSON script (see module doc)")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--agent", type=UUID, help="existing agent (else create one)")
    parser.add_argument("--database-uri", help="override .env DATABASE_URI")
    parser.add_argument("--json", type=Path, help="also write the report as JSON")
    args = parser.parse_args()

    settings = load_settings()
    if args.database_uri:
        settings = replace(settings, database_uri=args.database_uri)
    script = None
    if args.script:
        script = json.loads(args.script.read_text(encoding="utf-8"))

    report = asyncio.run(
        run_driver(
            settings,
            sessions=args.sessions,
            turns=args.turns,
            script=script,
            seed=args.seed,
            agent_id=args.agent,
        ),
        loop_factory=asyncio.SelectorEventLoop,
    )
    _print_report(report)
    if args.json:
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nreport written to {args.json}")


if __name__ == "__main__":
    main()
