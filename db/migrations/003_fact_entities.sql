-- 003_fact_entities.sql — the entities fact-chain column (mid-dialogue-gate.md,
-- scope forks ruled 2026-07-19; closes the 2026-07-18 embedding-only ruling's
-- honest deferral).
--
-- The gate is entities' first read consumer (coverage check + the degraded
-- lexical fetch). Freeze ruling (2026-07-19, the 002 embedding precedent):
-- entities moves to the fact chain — observe writes the fact head only,
-- corrections move entities with the fact supersede, memories.entities is
-- frozen (pre-003 rows keep their values, never written again; the accepted
-- epoch split, same as the embedding's).
--
-- Backfill populates the brand-new column from the canonical write-time
-- record BEFORE the index, so the GIN builds on populated data. This is an
-- UPDATE of a never-populated column on existing fact rows — sanctioned
-- schema-evolution backfill (fork 2, 2026-07-19), not a content mutation;
-- the guard (entities IS NULL) mirrors the WHERE NOT EXISTS stance (the
-- schema_migrations ledger is the primary idempotency; this is the backstop).

ALTER TABLE memory_fact_versions ADD COLUMN IF NOT EXISTS entities text[];

-- Backfill: carry each memory's write-time entities onto its fact rows
-- (superseded rows included — they are facts about the same event; the
-- correction verb is what moves entities from here on).
UPDATE memory_fact_versions f
SET entities = m.entities
FROM memories m
WHERE f.memory_id = m.memory_id
  AND f.entities IS NULL
  AND m.entities IS NOT NULL;

-- The gate's degraded lexical fetch: partial GIN over live fact heads.
-- Querying SQL must state invalid_at IS NULL verbatim to match the
-- partial-index predicate (the 002 partial-HNSW precedent).
CREATE INDEX IF NOT EXISTS memory_fact_versions_entities_gin
    ON memory_fact_versions USING gin (entities)
    WHERE invalid_at IS NULL;

-- The old entities index: dropped (ruled 2026-07-19 — derived structure,
-- zero readers; the gate's reads land on the fact head).
DROP INDEX IF EXISTS memories_entities_gin;
