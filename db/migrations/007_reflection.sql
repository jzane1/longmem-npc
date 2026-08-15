-- 007_reflection.sql — reflection run accounting (Phase C2;
-- docs\reflection.md; the C2 rulings dated 2026-08-15 in docs\decisions.md).
--
-- (a) reflection_runs — the WORKER's persisted per-run instrumentation home
--     (the memory_enrichment_runs precedent: a background seam has no
--     response payload to ride, so instrument-at-the-seam persists here).
--     Endpoint reflect calls ride the response payload and write NO row —
--     the C1 endpoint/worker split exactly. Column types copy 006's idioms
--     per class: counts int NOT NULL DEFAULT 0, flags boolean NOT NULL
--     DEFAULT false, timings/pressures real. rrr is nullable by contract —
--     None when the agent has no prior live reflections to compare against;
--     pressure/timing columns are nullable because a `failed` run may die
--     before a stage produces its number.
-- (b) No other schema change: the `reflections` table (001, dormant until
--     this build) carries the mechanism as designed — bi-temporal rows,
--     provenance in source_memory_ids (intentionally un-FK'd, the
--     purge-honesty ruling), invalidation by invalid_at only. Every
--     statement below is IF NOT EXISTS as defense-in-depth; the ledger
--     remains the primary idempotency mechanism.

CREATE TABLE IF NOT EXISTS reflection_runs (
    run_id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id                     uuid NOT NULL REFERENCES agents (agent_id),
    outcome                      text NOT NULL CHECK (outcome IN (
                                     'completed', 'failed')),
    error                        text,
    reflections_written          int NOT NULL DEFAULT 0,
    dropped_ungrounded           int NOT NULL DEFAULT 0,
    consolidation_ran            boolean NOT NULL DEFAULT false,
    consolidation_failed         boolean NOT NULL DEFAULT false,
    rrr                          real,
    rrr_blocked                  boolean NOT NULL DEFAULT false,
    pruned_components            int NOT NULL DEFAULT 0,
    evicted_cache_rows           int NOT NULL DEFAULT 0,
    pressure_before              real,
    pressure_after               real,
    reflect_ms                   real,
    consolidation_ms             real,
    insert_ms                    real,
    total_ms                     real,
    reflect_input_tokens         int NOT NULL DEFAULT 0,
    reflect_output_tokens        int NOT NULL DEFAULT 0,
    consolidation_input_tokens   int NOT NULL DEFAULT 0,
    consolidation_output_tokens  int NOT NULL DEFAULT 0,
    created_at                   timestamptz NOT NULL DEFAULT now()
);

-- FK / lookup index (the worker's retry semantics and C5's agent-state read
-- both look up runs by agent — the memory_enrichment_runs index precedent).
CREATE INDEX IF NOT EXISTS reflection_runs_agent_id_idx
    ON reflection_runs (agent_id);
