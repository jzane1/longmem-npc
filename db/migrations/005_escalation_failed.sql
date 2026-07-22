-- 005_escalation_failed.sql — the escalation soft-degrade signal
-- (ruled 2026-07-22: the escalation failure path retires the fail-loud
-- hard-stop and soft-degrades; docs\write-path.md carries the ladder row, and
-- the dedicated-column flag ruling is in docs\decisions.md, "Escalation
-- failure-path + pre-warm + R7 rulings").
--
-- A dedicated write-time degradation column on memories, mirroring
-- scoring_failed (migration 001). When the gist-escalation call fails twice on
-- a triggered observe, the write now proceeds with the base NLP-pass gist and
-- sets escalation_failed = true, so a degraded (base-only) gist is queryable
-- rather than a lost write. New column, DEFAULT false — existing rows read
-- false with no backfill.

ALTER TABLE memories
    ADD COLUMN IF NOT EXISTS escalation_failed boolean NOT NULL DEFAULT false;
