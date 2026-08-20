"""The corpus -> demo-DB loader (E2, ruled 2026-08-19; docs\\test-suite.md).

One pure test (corpus shape — no DB, no NLP) and one nlp-marked end-to-end
(the real demo corpus through `load_demo` on the suite scratch — the
test_run_scenarios_end_to_end precedent). Structural asserts only: stored
agent fields, row counts, worker-flag presence/absence. The destructive
provision path (drop + recreate) is scratch_db's contract, already covered
by its own callers — `load_demo` runs on injected Settings and never touches
database lifecycle.
"""

from __future__ import annotations

import asyncio

import pytest
from conftest import run_structural

from app.demo_loader import DEMO_CORPUS, WORKER_FLAGS, load_demo
from app.eval_scenarios import ObserveStep, assert_corpus_shape, load_scenarios


def test_demo_corpus_is_a_single_loadable_corpus():
    """The demo corpus parses, is corpus-shaped (observe + as_of only), and
    holds exactly the one scenario the loader provisions."""
    scenarios = load_scenarios(DEMO_CORPUS)
    assert len(scenarios) == 1
    scenario = scenarios[0]
    assert_corpus_shape(scenario)
    assert scenario.agent.name
    assert scenario.agent.seed_identity
    assert scenario.agent.diagnosticity_goal
    # The worker flags are the LOADER's divergence, never the corpus's (the
    # runner needs deterministic replay — the E1 record).
    assert not set(WORKER_FLAGS) & set(scenario.agent.config)
    assert sum(1 for e in scenario.events if isinstance(e, ObserveStep)) == 9


@pytest.mark.nlp
def test_load_demo_end_to_end(scene):
    """`load_demo` on the suite scratch: the agent row carries the corpus
    block's five fields verbatim; every observe lands with a rolled
    importance and its memory row; the worker flags are merged in AFTER the
    replay on the default path and absent with enable_workers=False."""
    scenario = load_scenarios(DEMO_CORPUS)[0]

    flagged = asyncio.run(
        load_demo(scene.settings, scenario),
        loop_factory=asyncio.SelectorEventLoop,
    )
    bare = asyncio.run(
        load_demo(scene.settings, scenario, enable_workers=False),
        loop_factory=asyncio.SelectorEventLoop,
    )

    assert len(flagged["memories"]) == 9
    for row in flagged["memories"]:
        assert row["memory_id"]
        assert row["importance_raw"] is not None
        assert isinstance(row["gist_spans"], int)
        assert row["decay_class"] == scenario.agent.config["decay_class_default"]
        assert row["flags"] == []
    # The returned config is the stored end state on both paths.
    assert flagged["config"] == {**scenario.agent.config, **WORKER_FLAGS}
    assert bare["config"] == scenario.agent.config

    async def checker(ctx):
        for report, expect_flags in ((flagged, True), (bare, False)):
            row = await ctx.fetchrow(
                "SELECT name, seed_identity, rigidity, diagnosticity_goal, "
                "config FROM agents WHERE agent_id = %s",
                report["agent_id"],
            )
            assert row[0] == scenario.agent.name
            assert row[1] == scenario.agent.seed_identity
            assert float(row[2]) == scenario.agent.rigidity
            assert row[3] == scenario.agent.diagnosticity_goal
            stored_config = row[4]
            if expect_flags:
                assert stored_config == {**scenario.agent.config, **WORKER_FLAGS}
            else:
                assert stored_config == scenario.agent.config
            (count,) = await ctx.fetchrow(
                "SELECT COUNT(*) FROM memories WHERE agent_id = %s",
                report["agent_id"],
            )
            assert count == 9

    run_structural(scene, checker)
