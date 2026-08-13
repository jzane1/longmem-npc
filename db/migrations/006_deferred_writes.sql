-- 006_deferred_writes.sql — deferred write processing (Phase C1;
-- docs\deferred-writes.md; the C1 spec rulings dated 2026-08-12 in
-- docs\decisions.md).
--
-- (a) BOTH write_cause CHECKs widen to admit 'enrichment' — the deferred
--     worker's completion cause. 001 and 002 are applied and therefore
--     immutable, so the constraints are dropped and re-added here under
--     their auto-generated names. ADD CONSTRAINT has no IF NOT EXISTS; the
--     DROP IF EXISTS + ADD pair is re-runnable as a unit, and the ledger
--     remains the primary idempotency mechanism. Re-adding validates
--     existing rows, which pass (the new sets are supersets).
-- (b) memories gains the pending/attempt bookkeeping scalars and the
--     persisted trigger names. The completion scalars themselves
--     (importance_raw, typology, typology_confidence, typology_source) are
--     001 columns, already NULL-able — no column change. No backfill: the
--     new columns default false/0/NULL and pre-006 rows were never deferred.
-- (c) memory_enrichment_runs — the per-attempt instrumentation home. A
--     background worker has no response payload to ride, so
--     instrument-at-the-seam persists here (surfaced on the unscored
--     /chain read).

ALTER TABLE memory_details
    DROP CONSTRAINT IF EXISTS memory_details_write_cause_check;
ALTER TABLE memory_details
    ADD CONSTRAINT memory_details_write_cause_check
    CHECK (write_cause IN (
        'original', 'reconstruction', 'rationalization',
        'update_with_resentment', 'authorial_correction', 'enrichment'));

ALTER TABLE memory_fact_versions
    DROP CONSTRAINT IF EXISTS memory_fact_versions_write_cause_check;
ALTER TABLE memory_fact_versions
    ADD CONSTRAINT memory_fact_versions_write_cause_check
    CHECK (write_cause IN ('original', 'authorial_correction', 'enrichment'));

-- Pending marker + attempt counter: worker bookkeeping scalars, updated in
-- place under the one-shot completion sanction (ruled 2026-08-12) — the
-- pinned precedent's class, not memory content.
ALTER TABLE memories
    ADD COLUMN IF NOT EXISTS enrichment_pending boolean NOT NULL DEFAULT false;
ALTER TABLE memories
    ADD COLUMN IF NOT EXISTS enrichment_attempts smallint NOT NULL DEFAULT 0;
-- Write-time fact: the non-importance escalation trigger names the NLP pass
-- raised at observe time (their raw material is not recoverable from the
-- DB). NULL on non-deferred rows; the worker reads it, never clears it.
ALTER TABLE memories
    ADD COLUMN IF NOT EXISTS enrichment_pending_triggers text[];

CREATE TABLE IF NOT EXISTS memory_enrichment_runs (
    run_id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id                uuid NOT NULL REFERENCES memories (memory_id),
    attempt                  int NOT NULL,
    outcome                  text NOT NULL CHECK (outcome IN (
                                 'completed', 'completed_facts_only',
                                 'failed', 'terminal_degraded')),
    error                    text,
    triggers                 text[],
    escalation_failed        boolean NOT NULL DEFAULT false,
    embedding_repaired       boolean NOT NULL DEFAULT false,
    write_ms                 real,
    escalation_ms            real,
    embed_ms                 real,
    insert_ms                real,
    total_ms                 real,
    write_input_tokens       int NOT NULL DEFAULT 0,
    write_output_tokens      int NOT NULL DEFAULT 0,
    escalation_input_tokens  int NOT NULL DEFAULT 0,
    escalation_output_tokens int NOT NULL DEFAULT 0,
    embedding_tokens         int NOT NULL DEFAULT 0,
    created_at               timestamptz NOT NULL DEFAULT now()
);

-- The claim probe: partial over pending rows, ordered oldest-first. Claim
-- SQL must state WHERE enrichment_pending verbatim to match this predicate.
CREATE INDEX IF NOT EXISTS memories_enrichment_pending_idx
    ON memories (created_at) WHERE enrichment_pending;

-- FK / lookup index (the /chain surface reads runs by memory).
CREATE INDEX IF NOT EXISTS memory_enrichment_runs_memory_id_idx
    ON memory_enrichment_runs (memory_id);
