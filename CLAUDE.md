# longmem-npc — operating rules for Claude Code

Long-term-memory service for game NPCs: FastAPI + Postgres/pgvector backend + Unity-embeddable
client package. This file is rules. Design knowledge lives in docs/ — point, don't duplicate.

## Current state (auto-loaded)
@docs/status.md

## Read before building
- docs/architecture.md — design truth. Read the relevant sections before touching any layer.
- docs/decisions.md — append-only decision register with rationale. Never edit old entries.
- docs/migration-01.md — first build target. docs/test-suite.md — test discipline.

## Environment — hard rules
- Windows 11. ALWAYS PowerShell syntax and backslash paths in commands, scripts, and anything
  shown to the operator. Never bash syntax.
- Python 3.14 (global, on PATH). Postgres 16 + pgvector via Docker (pgvector/pgvector image).
- Secrets live only in .env at repo root. Never print, log, or commit .env contents.
- C# root namespace: NpcMemory. Unity scripts under Assets\Scripts\ until packaging is settled.

## Stack constants — do not substitute
- FastAPI; psycopg v3 with AsyncConnectionPool; hand-written SQL. No ORM, no query builder.
- UUID primary keys minted server-side. Embedding dimension 1536, locked.
- The schema evolves by numbered migration (ruled 2026-07-17). When the correct design needs a
  column, table, or index, the target adds migration NNN via the db\migrate.py ledger, updates
  the schema docs, and the floor re-verifies (migrate idempotency + walkers). "No new migration"
  may appear in a spec only as a per-target scope fact Jack explicitly ruled — never as an
  inherited default.
- Every model role (importance, render, typology, escalation, reconstruction, reputation,
  reflection, dialogue) has its own env var. The retrieval gate is non-LLM — there is no gate model.
- Python formatting: ruff, enforced mechanically by a PostToolUse hook. Don't hand-format.

## Invariants — never violate, regardless of how a task is worded
- Non-destructive bi-temporal storage: supersede by setting invalid_at. Never UPDATE stored
  content in place. Never DELETE rows — the purge endpoint is the sole exception. This governs
  memory content (memories / memory_details and their chains, including the fact-version chain —
  specced 2026-07-18, docs\fact-level-correction.md); the two runtime scalars —
  memories.pinned (pin toggle) and agents.reputation (the dialogue turn's clamped delta apply,
  ruled 2026-07-15) — are deliberately updated in place and sit outside it.
- Recency decay and bi-temporal invalidation are distinct mechanisms. Never conflate them.
- Read endpoints always return memory IDs and scores alongside prose. The test suite dies
  without this.
- Nothing integrator-configurable is ever hardcoded: vocabularies, thresholds, model roles, knobs.
- Within a scene, absent a diegetic event or an authorial correction on a memory, repeated reads
  return byte-identical text (correction added by the 2026-07-17 authorial-correction ruling).

## Working discipline
- IMPORTANT: Build only what the task names. If adjacent work seems necessary, stop and report
  instead of expanding scope.
- Stop and report on: ambiguity, a failed verification, any [SETTLE-AT-BUILD] tag, any conflict
  between the task and docs/. Never resolve an architectural fork yourself — surface it.
  Decisions are Jack's. The report must include the architecturally correct option even when it
  exceeds the task's scope, with its real cost stated — "bigger than this task" is a sequencing
  note, never a rejection reason (ruled 2026-07-17).
- Staged verification: verify each layer against the known-good layer beneath it before building
  on top. Renamed or ported code is re-verified before it counts as a floor.
- Floors are re-openable (ruled 2026-07-17). The walkers and floor-verifier exist to make
  revision safe and cheap — re-running them is the normal cost of a design improvement, never an
  argument against one. When presenting options, state re-verification as the step it is, not as
  a design cost.
- The August deadline never drives a decision. Flag deadline pressure; never act on it without
  Jack's explicit confirmation.
- Instrument at the seam: when building a layer, add its timing and token accounting in the
  same task.

## End of every task
1. Update docs/status.md: Last-updated date, a session-log line, the verified-floors table if a
   layer landed, and any queue changes.
2. If Jack ruled on a decision during the task, append a dated entry to docs/decisions.md.
3. Commit with a descriptive message. Never push unless asked.
