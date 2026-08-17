-- 008_parameter_compiler.sql — the C3 parameter compiler (Phase C3;
-- docs\parameter-compiler.md; the C3 rulings dated 2026-08-17 in
-- docs\decisions.md).
--
-- (a) compiled_bundles — one row per compile call: one live belief
--     (a reflections row) compiled for one scene type. APPEND-ONLY: consume
--     reads the newest row per (reflection_id, scene_type); a re-compile
--     appends, nothing is ever rewritten. Liveness is DERIVED, not stored —
--     a bundle applies only while its source reflection has
--     invalid_at IS NULL, so bi-temporal belief invalidation (supersession,
--     consolidation absorb) doubles as compiler-cache eviction with no
--     bundle write at all (the §10 contract; the reconstruction-cache
--     eviction-by-key-construction precedent). The multiplier CHECK bounds
--     mirror app\config.py's MULTIPLIER_MIN / MULTIPLIER_MAX module
--     constants, frozen here by ruling (2026-08-17): one belief may move a
--     prose-view weight axis by at most x4 in either direction and can
--     never zero it — zeroing stays the caller's explicit weight-override
--     privilege. passthrough carries the integrator-namespaced keys; the
--     server stores them and never interprets them (the C5 agent-state
--     read is the recorded future surface). reflection_id is a real FK:
--     reflections rows are invalidated, never deleted, so the reference
--     cannot dangle today; if C6's purge verb is ever ruled to reach
--     reflections, bundle purge semantics are settled there (recorded
--     dependency in docs\parameter-compiler.md).
-- (b) compiler_runs — the WORKER's persisted per-agent-per-sweep
--     instrumentation home (the reflection_runs precedent). C3 has no
--     endpoint verb at all (ruled 2026-08-16/17: standalone worker, no new
--     route), so every run row is worker-written. A row lands only when a
--     sweep ATTEMPTED the agent (at least one compile call, or a run-level
--     failure such as a missing model role in real mode); a skip — the
--     kill-switch, or no missing pairs — writes nothing. Column types copy
--     007's idioms per class: counts int NOT NULL DEFAULT 0, timings real
--     (nullable — a failed run may die before a stage produces its number).
-- (c) Every statement below is IF NOT EXISTS as defense-in-depth; the
--     ledger remains the primary idempotency mechanism.

CREATE TABLE IF NOT EXISTS compiled_bundles (
    bundle_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id       uuid NOT NULL REFERENCES agents (agent_id),
    reflection_id  uuid NOT NULL REFERENCES reflections (reflection_id),
    scene_type     text NOT NULL,
    w_relevance    real NOT NULL CHECK (w_relevance BETWEEN 0.25 AND 4.0),
    w_recency      real NOT NULL CHECK (w_recency BETWEEN 0.25 AND 4.0),
    w_importance   real NOT NULL CHECK (w_importance BETWEEN 0.25 AND 4.0),
    passthrough    jsonb NOT NULL DEFAULT '{}',
    input_tokens   int NOT NULL DEFAULT 0,
    output_tokens  int NOT NULL DEFAULT 0,
    compile_ms     real,
    created_at     timestamptz NOT NULL DEFAULT now()
);

-- The pair index serves both compiler sides: work discovery's
-- missing-pair probe and consume's newest-row-per-(reflection, scene_type)
-- pick.
CREATE INDEX IF NOT EXISTS compiled_bundles_pair_idx
    ON compiled_bundles (reflection_id, scene_type, created_at);

-- FK / lookup index (walkers and C5's agent-state read look up bundles by
-- agent — the reflection_runs index precedent).
CREATE INDEX IF NOT EXISTS compiled_bundles_agent_id_idx
    ON compiled_bundles (agent_id);

CREATE TABLE IF NOT EXISTS compiler_runs (
    run_id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id                  uuid NOT NULL REFERENCES agents (agent_id),
    outcome                   text NOT NULL CHECK (outcome IN (
                                  'completed', 'failed')),
    error                     text,
    pairs_compiled            int NOT NULL DEFAULT 0,
    pairs_failed              int NOT NULL DEFAULT 0,
    passthrough_keys_dropped  int NOT NULL DEFAULT 0,
    input_tokens              int NOT NULL DEFAULT 0,
    output_tokens             int NOT NULL DEFAULT 0,
    total_ms                  real,
    created_at                timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS compiler_runs_agent_id_idx
    ON compiler_runs (agent_id);
