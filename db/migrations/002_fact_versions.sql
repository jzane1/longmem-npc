-- 002_fact_versions.sql — the fact-version chain (fact-level-correction.md,
-- scope forks ruled 2026-07-18; build rulings same day).
--
-- The memories row's semantic basis — the text retrieval ranks by, and its
-- embedding — gains the memory_details chain shape under the stable
-- memory_id: supersede by invalid_at, one live head, write_cause
-- discrimination. Non-destructive: fact versions are never UPDATEd or
-- DELETEd; the superseded row keeps its embedding.
--
-- Backfill mints one 'original' fact head per existing memory BEFORE the
-- indexes, so the HNSW builds on the populated table. The WHERE NOT EXISTS
-- guard mirrors the IF NOT EXISTS defense-in-depth stance (the
-- schema_migrations ledger is the primary idempotency; this is the backstop).
--
-- Freeze ruling (2026-07-18): observe stops writing memories.embedding — the
-- fact head is the sole vector home for post-002 rows, and the queryable
-- embed-degradation signal moves to the live fact head
-- (memory_fact_versions.embedding IS NULL). memories_embedding_hnsw is
-- dropped (derived structure, zero readers once the probe moves); the
-- fact-table HNSW is partial (live heads only) so superseded vectors never
-- enter the probe. Candidate SQL must state fv.invalid_at IS NULL verbatim
-- to match the partial-index predicate.

CREATE TABLE IF NOT EXISTS memory_fact_versions (
    fact_version_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id        uuid NOT NULL REFERENCES memories (memory_id),
    basis_text       text NOT NULL,
    embedding        vector(1536),
    write_cause      text CHECK (write_cause IN ('original', 'authorial_correction')),
    created_at       timestamptz NOT NULL DEFAULT now(),
    valid_at         timestamptz NOT NULL,
    invalid_at       timestamptz
);

-- Backfill: one 'original' fact head per existing memory (embedding carried
-- as stored — NULL degradation rows stay honestly NULL).
INSERT INTO memory_fact_versions (memory_id, basis_text, embedding, write_cause, valid_at)
SELECT m.memory_id, m.observation_text, m.embedding, 'original', m.valid_at
FROM memories m
WHERE NOT EXISTS (
    SELECT 1 FROM memory_fact_versions f WHERE f.memory_id = m.memory_id
);

-- At most one live fact head per memory (the memory_details precedent).
CREATE UNIQUE INDEX IF NOT EXISTS memory_fact_versions_one_live_head
    ON memory_fact_versions (memory_id) WHERE invalid_at IS NULL;

-- The retrieval probe: partial HNSW over live fact heads, cosine.
CREATE INDEX IF NOT EXISTS memory_fact_versions_embedding_hnsw
    ON memory_fact_versions USING hnsw (embedding vector_cosine_ops)
    WHERE invalid_at IS NULL;

-- FK / lookup index.
CREATE INDEX IF NOT EXISTS memory_fact_versions_memory_id_idx
    ON memory_fact_versions (memory_id);

-- The old probe index: dropped (ruled 2026-07-18 — derived structure, no
-- readers after the probe moves to the fact head).
DROP INDEX IF EXISTS memories_embedding_hnsw;
