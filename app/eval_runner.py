"""eval_runner.py — the eval harness runner (eval-harness.md stage 2).

Two verbs (PowerShell, from the repo root):

    python -m app.eval_runner run --scenarios data\\eval\\scenarios\\smoke.jsonl
    python -m app.eval_runner drift-validate --corpus data\\eval\\corpora\\drift-fixture.jsonl

`run` replays authored scenarios literally through `SessionRunner` — REPL
parity: `as_of` sets the session attribute, a decay-basis re-freeze is an
authored `scene` event, never magic — on a disposable pid-scoped scratch
database, scores each utterance's membership assertions against the raw
served items (the IDs+scores retrieval echo), reads the judge-free
reconstruction metrics per observed memory through the one service-side
assembly, and writes a run-artifact JSON under `data\\eval\\runs\\`
(gitignored; fork 7 — milestone numbers get quoted into dated doc entries).
Exit 0 = every expected-IDs check passed; 1 = any failed.

`drift-validate` replays a drift corpus (the scenario schema's observe/as_of
subset, same loader — fork 10), jumps the session `--age-days` past the last
authored moment, re-freezes the scene basis at the aged instant, and probes
once with k covering the corpus so every unpinned past-theta item is retold
and drift-checked. Per-item cosine distances arrive through the
`reconstruction.drift_observer` capture seam; the report carries p50/p95/max,
the over-budget count against the agent's resolved `drift_budget_threshold`,
and a self-check against the turn's `drift_refusals` counter (they diverge
only on the blind embed-failure path, which carries no distance). Exit 0 =
every item under budget; 1 = any over. Real provider mode is required — the
construct is real-retelling drift under real embeddings — unless `--plumbing`
runs the mechanics offline in fake mode with the report labeled
`plumbing_only: true` (the stage-3 `--judged` labeling pattern). Exit 2 =
refused mode gate.

Nothing eval-related persists in Postgres (ruled: no migration); scratch
databases are provisioned and dropped per invocation. Windows: both verbs run
under a SelectorEventLoop (psycopg's async pool cannot run on the default
ProactorEventLoop).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from psycopg_pool import AsyncConnectionPool

from app import db, reconstruction
from app.config import REPO_ROOT, Settings, agent_knob, load_settings
from app.db import build_pool
from app.eval_scenarios import (
    AsOfStep,
    ContextStep,
    CorrectStep,
    ObserveStep,
    PinStep,
    Scenario,
    SceneStep,
    UtteranceStep,
    assert_corpus_shape,
    check_expected,
    load_scenario_files,
    load_scenarios,
)
from app.load_driver import percentile
from app.providers import Providers, build_providers
from app.retrieval import RetrievalService
from app.schemas import DialogueTurnResult, IngestResult
from app.scratch_db import drop_scratch, pid_scoped_name, provision_scratch
from app.session import SessionRunner

DEFAULT_RUNS_DIR = REPO_ROOT / "data" / "eval" / "runs"
DEFAULT_PROBE = "Tell me about everything you remember."
METRIC_KEYS = (
    "gist_precision",
    "detail_recall",
    "fabrication_rate",
    "keyword_retention",
)


# ---------------------------------------------------------------------------
# Shared report blocks
# ---------------------------------------------------------------------------


def _latency_block(turns: list[DialogueTurnResult]) -> dict:
    series = {
        "perceived_first_word": [
            t.instrumentation.perceived_first_word_ms for t in turns
        ],
        "turn_total": [t.instrumentation.total_ms for t in turns],
    }
    return {
        name: {"p50": percentile(values, 0.5), "p95": percentile(values, 0.95)}
        for name, values in series.items()
    }


def _cost_totals(
    settings: Settings,
    turns: list[DialogueTurnResult],
    observes: list[IngestResult],
) -> dict:
    """Run-total tokens per model role; USD only when both prices are set
    (the prices-optional -> None pattern, load_driver shape)."""
    prices = settings.prices

    def usd(t_in: int, t_out: int, key_in: str, key_out: str) -> float | None:
        if key_in in prices and key_out in prices:
            return round((t_in * prices[key_in] + t_out * prices[key_out]) / 1e6, 6)
        return None

    dialogue_in = sum(t.instrumentation.sonnet_input_tokens for t in turns)
    dialogue_out = sum(t.instrumentation.sonnet_output_tokens for t in turns)
    write_in = sum(o.instrumentation.haiku_input_tokens for o in observes)
    write_out = sum(o.instrumentation.haiku_output_tokens for o in observes)
    esc_in = sum(o.instrumentation.escalation_input_tokens for o in observes)
    esc_out = sum(o.instrumentation.escalation_output_tokens for o in observes)
    recon_in = sum(
        t.instrumentation.retrieval.reconstruction_input_tokens for t in turns
    )
    recon_out = sum(
        t.instrumentation.retrieval.reconstruction_output_tokens for t in turns
    )
    embed_tokens = (
        sum(o.instrumentation.embedding_tokens for o in observes)
        + sum(t.instrumentation.retrieval.embedding_tokens for t in turns)
        + sum(t.instrumentation.retrieval.reconstruction_embed_tokens for t in turns)
    )
    return {
        "dialogue": {
            "input_tokens": dialogue_in,
            "output_tokens": dialogue_out,
            "usd": usd(dialogue_in, dialogue_out, "dialogue_in", "dialogue_out"),
        },
        "write": {
            "input_tokens": write_in,
            "output_tokens": write_out,
            "usd": usd(write_in, write_out, "write_in", "write_out"),
        },
        "escalation": {
            "input_tokens": esc_in,
            "output_tokens": esc_out,
            "usd": usd(esc_in, esc_out, "escalation_in", "escalation_out"),
        },
        "reconstruction": {
            "input_tokens": recon_in,
            "output_tokens": recon_out,
            "usd": usd(recon_in, recon_out, "reconstruction_in", "reconstruction_out"),
        },
        "embedding": {
            "tokens": embed_tokens,
            "usd": (
                round(embed_tokens * prices["embedding"] / 1e6, 6)
                if "embedding" in prices
                else None
            ),
        },
    }


def _metrics_summary(memory_payloads: list[dict]) -> dict:
    """Honest denominators: means over measured values only, with the
    measured/null split stated — a null is never coerced to a number."""
    summary: dict = {}
    for key in METRIC_KEYS:
        values = [m[key] for m in memory_payloads if m.get(key) is not None]
        summary[key] = {
            "mean": round(sum(values) / len(values), 4) if values else None,
            "measured": len(values),
            "null": sum(1 for m in memory_payloads if m.get(key) is None),
        }
    summary["fabricated_entities_total"] = sum(
        len(m.get("fabricated_entities") or []) for m in memory_payloads
    )
    return summary


def _write_artifact(report: dict, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out


def _default_artifact_path(verb: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return DEFAULT_RUNS_DIR / f"{verb}_{stamp}_{pid_scoped_name('pid')}.json"


# ---------------------------------------------------------------------------
# The `run` verb
# ---------------------------------------------------------------------------


async def _run_one_scenario(
    scenario: Scenario,
    *,
    pool: AsyncConnectionPool,
    providers: Providers,
    settings: Settings,
    retrieval: RetrievalService,
    k: int | None,
    all_turns: list[DialogueTurnResult],
    all_observes: list[IngestResult],
) -> dict:
    agent_id = await db.insert_agent(
        pool,
        name=scenario.agent.name,
        seed_identity=scenario.agent.seed_identity,
        rigidity=scenario.agent.rigidity,
        diagnosticity_goal=scenario.agent.diagnosticity_goal,
        config=scenario.agent.config,
    )
    runner = await SessionRunner.create(
        agent_id,
        settings=settings,
        providers=providers,
        pool=pool,
        phase_tag="eval-runner",
        warm_nlp=any(isinstance(e, ObserveStep) for e in scenario.events),
    )
    memory_ids: list[UUID] = []
    checks: list[dict] = []
    turns = 0
    degraded = 0
    event_counts: dict[str, int] = {}
    for index, event in enumerate(scenario.events):
        event_counts[event.kind] = event_counts.get(event.kind, 0) + 1
        if isinstance(event, ObserveStep):
            ingest = await runner.observe(event.text)
            memory_ids.append(ingest.memory_id)
            all_observes.append(ingest)
        elif isinstance(event, UtteranceStep):
            result = await runner.utterance(
                event.text, k=event.k if event.k is not None else k
            )
            all_turns.append(result)
            turns += 1
            if result.instrumentation.degraded:
                degraded += 1
            if event.expect is not None:
                outcome = check_expected(
                    event.expect,
                    [item.memory_id for item in result.items],
                    memory_ids,
                )
                checks.append({"event_index": index, **outcome})
        elif isinstance(event, SceneStep):
            await runner.scene(event.scene_type)
        elif isinstance(event, CorrectStep):
            await runner.correct(memory_ids[event.memory_ref], event.content)
        elif isinstance(event, PinStep):
            await runner.pin(memory_ids[event.memory_ref], event.pinned)
        elif isinstance(event, AsOfStep):
            runner.as_of = event.at
        elif isinstance(event, ContextStep):
            runner.context_location = event.location
            runner.context_entities = event.entities
            runner.context_event_time = event.event_time
    await runner.close()

    memories: list[dict] = []
    for ref, memory_id in enumerate(memory_ids):
        metrics = await retrieval.reconstruction_metrics(memory_id)
        memories.append({"memory_ref": ref, **metrics.model_dump(mode="json")})
    failed = sum(1 for c in checks if not c["passed"])
    return {
        "scenario_id": scenario.scenario_id,
        "held_out": scenario.held_out,
        "agent_id": str(agent_id),
        "event_counts": event_counts,
        "checks": checks,
        "checks_passed": len(checks) - failed,
        "checks_failed": failed,
        "turns": turns,
        "degraded_turns": degraded,
        "memories": memories,
    }


async def run_scenarios(
    settings: Settings,
    scenarios: list[Scenario],
    *,
    include_held_out: bool,
    k: int | None,
) -> dict:
    """The `run` core, separable so the suite can drive it in-process on an
    injected scratch Settings (the load_driver `run_driver` shape)."""
    included = [s for s in scenarios if include_held_out or not s.held_out]
    excluded = [s.scenario_id for s in scenarios if not include_held_out and s.held_out]
    pool = build_pool(settings.database_uri)
    await pool.open()
    providers = build_providers(settings)
    retrieval = RetrievalService(pool, providers, settings)
    all_turns: list[DialogueTurnResult] = []
    all_observes: list[IngestResult] = []
    scenario_reports: list[dict] = []
    started = datetime.now(timezone.utc)
    try:
        for scenario in included:
            scenario_reports.append(
                await _run_one_scenario(
                    scenario,
                    pool=pool,
                    providers=providers,
                    settings=settings,
                    retrieval=retrieval,
                    k=k,
                    all_turns=all_turns,
                    all_observes=all_observes,
                )
            )
    finally:
        await pool.close()
    memory_payloads = [m for report in scenario_reports for m in report["memories"]]
    return {
        "verb": "run",
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "provider_mode": settings.provider_mode,
        "excluded_held_out": excluded,
        "scenarios": scenario_reports,
        "turns": len(all_turns),
        "observes": len(all_observes),
        "degraded_turns": sum(1 for t in all_turns if t.instrumentation.degraded),
        "write_backs": sum(t.instrumentation.retrieval.write_backs for t in all_turns),
        "drift_refusals": sum(
            t.instrumentation.retrieval.drift_refusals for t in all_turns
        ),
        "cache_hits": sum(t.instrumentation.retrieval.cache_hits for t in all_turns),
        "metrics_summary": _metrics_summary(memory_payloads),
        "latency_ms": _latency_block(all_turns),
        "cost": _cost_totals(settings, all_turns, all_observes),
        "checks_passed_total": sum(r["checks_passed"] for r in scenario_reports),
        "checks_failed_total": sum(r["checks_failed"] for r in scenario_reports),
    }


def _print_run_report(report: dict) -> None:
    print(
        f"\neval run — {len(report['scenarios'])} scenario(s), "
        f"{report['turns']} turns, {report['observes']} observes, "
        f"{report['degraded_turns']} degraded "
        f"(provider mode: {report['provider_mode']})"
    )
    if report["excluded_held_out"]:
        print("held-out excluded by default: " + ", ".join(report["excluded_held_out"]))
    print(
        f"reconstruction: {report['write_backs']} write-backs, "
        f"{report['cache_hits']} cache hits, "
        f"{report['drift_refusals']} drift refusals"
    )

    def fmt(block: dict) -> str:
        mean = block["mean"]
        shown = f"{mean:.3f}" if mean is not None else "(null)"
        return f"{shown} ({block['measured']} measured/{block['null']} null)"

    print("\nscenario                     checks   gist_p   detail_r")
    for row in report["scenarios"]:
        summary = _metrics_summary(row["memories"])
        gist = summary["gist_precision"]["mean"]
        detail = summary["detail_recall"]["mean"]
        print(
            f"  {row['scenario_id']:<26} "
            f"{row['checks_passed']}/{row['checks_passed'] + row['checks_failed']:<6} "
            f"{gist if gist is not None else '(null)':>7}  "
            f"{detail if detail is not None else '(null)':>8}"
        )
    summary = report["metrics_summary"]
    print("\nrun metrics (honest denominators):")
    for key in METRIC_KEYS:
        print(f"  {key:<22} {fmt(summary[key])}")
    print(f"  fabricated entities    {summary['fabricated_entities_total']}")
    print("\nlatency (ms)                p50        p95")
    for name, row in report["latency_ms"].items():
        print(f"  {name:<24} {row['p50']:>8}   {row['p95']:>8}")
    print("\nrun-total cost              tokens (in/out)        USD")
    for role, row in report["cost"].items():
        if role == "embedding":
            tokens = f"{row['tokens']}"
        else:
            tokens = f"{row['input_tokens']}/{row['output_tokens']}"
        usd_val = row["usd"]
        usd_text = f"${usd_val}" if usd_val is not None else "(unpriced)"
        print(f"  {role:<24} {tokens:>20}   {usd_text}")
    print(
        f"\nchecks: {report['checks_passed_total']} passed, "
        f"{report['checks_failed_total']} failed"
    )


def _cmd_run(args: argparse.Namespace) -> int:
    settings = load_settings()
    base_uri = args.database_uri or settings.database_uri
    scenarios = load_scenario_files(args.scenarios)
    name = args.database_name or pid_scoped_name("longmem_eval")
    uri = provision_scratch(base_uri, name)
    try:
        report = asyncio.run(
            run_scenarios(
                replace(settings, database_uri=uri),
                scenarios,
                include_held_out=args.include_held_out,
                k=args.k,
            ),
            loop_factory=asyncio.SelectorEventLoop,
        )
    finally:
        if args.keep_db:
            print(f"scratch database kept: {name}")
        else:
            drop_scratch(base_uri, name)
    report["scenario_files"] = [str(p) for p in args.scenarios]
    report["database_name"] = name
    _print_run_report(report)
    out = _write_artifact(report, args.out or _default_artifact_path("run"))
    print(f"\nrun artifact: {out}")
    return 0 if report["checks_failed_total"] == 0 else 1


# ---------------------------------------------------------------------------
# The `drift-validate` verb
# ---------------------------------------------------------------------------


async def drift_validate(
    settings: Settings,
    corpus: list[Scenario],
    *,
    age_days: float,
    probe: str,
    max_items: int | None,
) -> dict:
    """The `drift-validate` core: replay each corpus scenario's observes,
    age the session past the last authored moment, re-freeze the basis, and
    probe once with the capture seam attached."""
    pool = build_pool(settings.database_uri)
    await pool.open()
    providers = build_providers(settings)
    all_turns: list[DialogueTurnResult] = []
    all_observes: list[IngestResult] = []
    scenario_reports: list[dict] = []
    started = datetime.now(timezone.utc)
    try:
        for scenario in corpus:
            agent_id = await db.insert_agent(
                pool,
                name=scenario.agent.name,
                seed_identity=scenario.agent.seed_identity,
                rigidity=scenario.agent.rigidity,
                diagnosticity_goal=scenario.agent.diagnosticity_goal,
                config=scenario.agent.config,
            )
            runner = await SessionRunner.create(
                agent_id,
                settings=settings,
                providers=providers,
                pool=pool,
                phase_tag="eval-runner",
                warm_nlp=True,
            )
            memory_ids: list[UUID] = []
            for event in scenario.events:
                if isinstance(event, ObserveStep):
                    ingest = await runner.observe(event.text)
                    memory_ids.append(ingest.memory_id)
                    all_observes.append(ingest)
                else:  # AsOfStep — assert_corpus_shape admits nothing else
                    runner.as_of = event.at
            last = runner.as_of if runner.as_of is not None else started
            runner.as_of = last + timedelta(days=age_days)
            await runner.scene()  # re-freeze the decay/theta basis, aged

            samples: list[tuple[UUID, float, bool]] = []

            def observer(
                memory_id: UUID,
                distance: float,
                refused: bool,
                _samples: list = samples,
            ) -> None:
                _samples.append((memory_id, distance, refused))

            k = (
                len(memory_ids)
                if max_items is None
                else min(len(memory_ids), max_items)
            )
            reconstruction.drift_observer = observer
            try:
                turn = await runner.utterance(probe, k=k)
            finally:
                reconstruction.drift_observer = None
            all_turns.append(turn)
            await runner.close()

            threshold = agent_knob(
                scenario.agent.config, "drift_budget_threshold", settings
            )
            ref_by_id = {mid: ref for ref, mid in enumerate(memory_ids)}
            items = sorted(
                (
                    {
                        "memory_ref": ref_by_id.get(memory_id),
                        "memory_id": str(memory_id),
                        "distance": round(distance, 6),
                        "over_budget": refused,
                    }
                    for memory_id, distance, refused in samples
                ),
                key=lambda row: -row["distance"],
            )
            observer_over = sum(1 for _, _, refused in samples if refused)
            turn_refusals = turn.instrumentation.retrieval.drift_refusals
            scenario_reports.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "agent_id": str(agent_id),
                    "observes": len(memory_ids),
                    "items_checked": len(samples),
                    "over_budget_count": observer_over,
                    "threshold": threshold,
                    "items": items,
                    # Equal unless an embed call failed blind — that refusal
                    # path carries no distance and never reaches the observer.
                    "self_check": {
                        "turn_drift_refusals": turn_refusals,
                        "observer_over_budget": observer_over,
                        "match": turn_refusals == observer_over,
                    },
                }
            )
    finally:
        await pool.close()

    distances = [
        row["distance"] for report in scenario_reports for row in report["items"]
    ]
    return {
        "verb": "drift-validate",
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "provider_mode": settings.provider_mode,
        "age_days": age_days,
        "probe": probe,
        "scenarios": scenario_reports,
        "items_checked_total": len(distances),
        "over_budget_count": sum(
            report["over_budget_count"] for report in scenario_reports
        ),
        "distance": {
            "p50": percentile(distances, 0.5),
            "p95": percentile(distances, 0.95),
            "max": max(distances) if distances else None,
        },
        "latency_ms": _latency_block(all_turns),
        "cost": _cost_totals(settings, all_turns, all_observes),
    }


def _print_drift_report(report: dict) -> None:
    plumbing = " [PLUMBING ONLY — fake providers]" if report["plumbing_only"] else ""
    print(
        f"\ndrift-validate — {report['items_checked_total']} item(s) checked, "
        f"{report['over_budget_count']} over budget{plumbing}"
    )
    dist = report["distance"]
    print(
        f"distance: p50 {dist['p50']}  p95 {dist['p95']}  "
        f"max {dist['max'] if dist['max'] is not None else '(none checked)'}"
    )
    for scenario in report["scenarios"]:
        check = scenario["self_check"]
        match_text = (
            "matches"
            if check["match"]
            else (
                f"DIVERGES (turn counted {check['turn_drift_refusals']} — "
                "a blind embed-failure refusal carries no distance)"
            )
        )
        print(
            f"\n  {scenario['scenario_id']} — {scenario['items_checked']}/"
            f"{scenario['observes']} items checked, threshold "
            f"{scenario['threshold']}, drift_refusals self-check: {match_text}"
        )
        for row in scenario["items"][:20]:
            flag = "OVER" if row["over_budget"] else "  ok"
            print(
                f"    {flag}  ref {row['memory_ref']}  "
                f"distance {row['distance']:.4f}  {row['memory_id']}"
            )
        if len(scenario["items"]) > 20:
            print(f"    … {len(scenario['items']) - 20} more (see artifact)")


def _cmd_drift_validate(args: argparse.Namespace) -> int:
    settings = load_settings()
    if settings.provider_mode != "real" and not args.plumbing:
        print(
            "drift-validate requires real provider mode — the construct is "
            "real-retelling drift under real embeddings. Pass --plumbing to "
            "run the mechanics offline in fake mode (report labeled "
            "plumbing_only).",
            file=sys.stderr,
        )
        return 2
    corpus = load_scenarios(args.corpus)
    for scenario in corpus:
        assert_corpus_shape(scenario)
    base_uri = args.database_uri or settings.database_uri
    name = args.database_name or pid_scoped_name("longmem_eval")
    uri = provision_scratch(base_uri, name)
    try:
        report = asyncio.run(
            drift_validate(
                replace(settings, database_uri=uri),
                corpus,
                age_days=args.age_days,
                probe=args.probe,
                max_items=args.max_items,
            ),
            loop_factory=asyncio.SelectorEventLoop,
        )
    finally:
        if args.keep_db:
            print(f"scratch database kept: {name}")
        else:
            drop_scratch(base_uri, name)
    report["corpus"] = str(args.corpus)
    report["database_name"] = name
    report["plumbing_only"] = settings.provider_mode != "real"
    _print_drift_report(report)
    if args.out is not None:
        print(f"\ndrift artifact: {_write_artifact(report, args.out)}")
    return 0 if report["over_budget_count"] == 0 else 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m app.eval_runner",
        description="longmem-npc eval runner (eval-harness.md stage 2)",
    )
    verbs = parser.add_subparsers(dest="verb", required=True)

    run_parser = verbs.add_parser(
        "run", help="replay scenario files; score expected-IDs checks + metrics"
    )
    run_parser.add_argument(
        "--scenarios",
        type=Path,
        action="append",
        required=True,
        help="scenario JSONL file (repeatable)",
    )
    run_parser.add_argument(
        "--out",
        type=Path,
        help="run-artifact path (default: data\\eval\\runs\\run_<utc>_<pid>.json)",
    )
    run_parser.add_argument(
        "--database-name",
        help="scratch database name (default: longmem_eval_<pid>)",
    )
    run_parser.add_argument("--database-uri", help="override .env DATABASE_URI")
    run_parser.add_argument(
        "--include-held-out",
        action="store_true",
        help="also run scenarios marked held_out (excluded by default)",
    )
    run_parser.add_argument(
        "--k", type=int, help="run-wide top-k for utterances without their own k"
    )
    run_parser.add_argument(
        "--keep-db",
        action="store_true",
        help="skip the scratch drop for post-mortem inspection",
    )
    run_parser.set_defaults(func=_cmd_run)

    drift_parser = verbs.add_parser(
        "drift-validate",
        help="per-item reconstruction drift vs drift_budget_threshold",
    )
    drift_parser.add_argument(
        "--corpus", type=Path, required=True, help="corpus JSONL (observe/as_of only)"
    )
    drift_parser.add_argument(
        "--age-days",
        type=float,
        default=30.0,
        help="how far past the last authored moment the probe ages (default 30)",
    )
    drift_parser.add_argument(
        "--probe",
        default=DEFAULT_PROBE,
        help="probe utterance (coverage comes from k, not wording)",
    )
    drift_parser.add_argument(
        "--max-items", type=int, help="cap the probe's k (default: every observe)"
    )
    drift_parser.add_argument("--out", type=Path, help="also write the report JSON")
    drift_parser.add_argument(
        "--database-name",
        help="scratch database name (default: longmem_eval_<pid>)",
    )
    drift_parser.add_argument("--database-uri", help="override .env DATABASE_URI")
    drift_parser.add_argument(
        "--keep-db",
        action="store_true",
        help="skip the scratch drop for post-mortem inspection",
    )
    drift_parser.add_argument(
        "--plumbing",
        action="store_true",
        help="allow fake provider mode; the report is labeled plumbing_only",
    )
    drift_parser.set_defaults(func=_cmd_drift_validate)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
