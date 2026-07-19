# Migration 01 — Foundational schema

First build target. Fully unblocked. Everything here is **schema only**: hand-written SQL against
PostgreSQL 16 + pgvector (Docker, `pgvector/pgvector` image), UUIDs minted server-side.

> **Built & verified 2026-07-13.** All seven `[SETTLE-AT-BUILD]` forks ruled (dated entry in
> `decisions.md`); tables, CHECKs, and indexes are live in `longmem` and the floor-verifier passed.
> Applied by `db\migrate.py`. The `[SETTLE-AT-BUILD]` tags below are resolved inline for the record.

**Scope boundary — do NOT build:** API endpoints, the write path, the NLP pass, any model calls,
seed content beyond a minimal smoke-test fixture, Unity anything, the retrieval gate.

Items tagged `[SETTLE-AT-BUILD]` are physical shapes never explicitly decided. Each carries a
suggested default. The builder must **stop and report** on any it touches rather than silently
choosing — confirm with Jack, then record the choice in `decisions.md`.

## Principles this migration must honor

- Bi-temporal everywhere it applies: `created_at` (server write time), `valid_at` (world time, from
  the client timestamp, timezone-aware, NOT NULL), `invalid_at` (NULL until superseded).
- Non-destructive: supersession is setting `invalid_at`, never UPDATE-in-place of content, never
  DELETE (the purge endpoint is the sole, explicit exception, and it is not part of this migration).
- All **write-time fact** columns exist now, even where the consuming mechanism is deferred:
  typology + confidence + typology_source, provenance, context components, decay class, gist spans,
  importance, pin, scoring_failed.

## Tables

### agents
One row per NPC.
- `agent_id` UUID PK, server default.
- `name` text.
- `seed_identity` text — the seed prose; revised by reflection later.
- `reputation` numeric — runtime scalar; starts at the scale's neutral point.
- `rigidity` numeric, CHECK between 0.5 and 2.0 — dissonance scalar (pushover → zealot).
- `reputation_sensitivity` numeric.
- `diagnosticity_goal` text — anchor for importance scoring; the Haiku importance prompt consumes
  prose. *(Ruled 2026-07-13: text.)*
- `config` jsonb — remaining integrator knobs (decay constants, drift threshold, habituation
  cap/decay, etc.) until any of them earns a typed column.

### memories
One row per observation. **`observation_text` is immutable after insert.**
- `memory_id` UUID PK, server default.
- `agent_id` FK → agents.
- `observation_text` text NOT NULL.
- `embedding` vector(1536) — dimension locked. *(Fact-level correction specced 2026-07-18,
  `fact-level-correction.md`: at migration 002 the retrieval probe moves to the live
  fact-version head; this column remains the write-time event fact under that spec's suggested
  dual-write default — dual-write vs freeze is `[SETTLE-AT-BUILD]` there.)*
- `importance_raw` real — stored raw; normalized at read.
- `scoring_failed` boolean NOT NULL default false — set true when the importance-scoring model
  fails; the write still lands with neutral importance (never lose a write). See architecture §2.
- `typology` text CHECK in (`observed`, `told`, `inferred`, `reflected`).
- `typology_confidence` real CHECK 0–1.
- `typology_source` text CHECK in (`declared`, `inferred`).
- `provenance` text CHECK in (`lived`, `injected`).
- `pinned` boolean NOT NULL default false.
- `decay_class` text — integrator vocabulary label; selects the base decay constant. The
  label→`tau_base` map lives in `agents.config`. *(Ruled 2026-07-13: free-text column + config map.)*
- `decay_class_unknown` boolean NOT NULL default false — write-time degradation flag (mirrors
  `scoring_failed`): on an unrecognized decay-class label the write lands with a default class and
  this flag set, never rejected. Validation is write-path (deferred). *(Ruled 2026-07-13.)*
- `created_at` / `valid_at` / `invalid_at` per the bi-temporal rules above.
- Context stamps (all four nullable — optional API fields):
  - `location_embedding` vector(1536) and `location_name` text.
  - `entities` text[] — with a **GIN index** (serves the entity gate now, context boost later).
  - `event_time` timestamptz.
  - `affect_valence` real, `affect_arousal` real, `affect_detail` jsonb (all nullable) — from the
    VADER-class write pass. *(Ruled 2026-07-13: three columns — valence + arousal + jsonb detail.)*

### memory_gist_spans
Gist as **span pointers into `observation_text`** — never rewritten text. Child table so spans are
individually assertable rows (the suite asserts gist rows are immutable).
*(Ruled 2026-07-13: child table.)*
- `span_id` UUID PK, server default.
- `memory_id` FK → memories.
- `start_char` int, `end_char` int (half-open, into `observation_text`).
- `matched_component_id` FK → identity_components, nullable.
- `matched_category` text, nullable — for category hits without a named entity.
- `created_at`.

### memory_details
The version chain under a stable `memory_id`. The **head** is the row with `invalid_at IS NULL`.
- `detail_id` UUID PK, server default.
- `memory_id` FK → memories.
- `content` text NOT NULL.
- `write_cause` text CHECK in (`original`, `reconstruction`, `rationalization`,
  `update_with_resentment`, `authorial_correction`).
- `created_at` / `valid_at` / `invalid_at`.
- Partial unique index: at most one live head per memory —
  `UNIQUE (memory_id) WHERE invalid_at IS NULL`. (Confirmed compatible with the authorial
  replace-model ruling of 2026-07-12: authorial supersedes to a single corrected live head.)
- Verb discrimination lives on the new head's `write_cause`; prior-row invalidation is ordinary
  supersession — no voided-marker column.

### corrections
The diegetic correction record — one row per in-world confrontation that superseded a chain head.
Schema now; the dissonance mechanism that writes these lands post-August (the diegetic half of the
Set A test pair, `test-suite.md`, asserts a correction record is present).
- `correction_id` UUID PK, server default.
- `memory_id` FK → memories — the target of the diegetic correction.
- `detail_id` FK → memory_details — the new head row this correction produced.
- `verb` text CHECK in (`rationalization`, `update_with_resentment`) — the diegetic subset of the
  `memory_details.write_cause` enum.
- `source_event` jsonb — the client-supplied in-world confrontation reference. Nullable.
- `created_at` / `valid_at` per the bi-temporal rules (world time of the confrontation).

### reconstruction_cache
- `memory_id` FK → memories.
- `identity_version` text — content hash of the rendered identity document. *(Ruled 2026-07-17,
  `reconstruction.md`: at reconstruction this column stores the composed reconstruction key —
  `identity_version` ⊕ the scene-frozen decay band; column type and PK unchanged.)*
- `rendered_text` text NOT NULL.
- `created_at`.
- PK `(memory_id, identity_version)`.
- Eviction is by the generalized invariant (any non-reconstruction writer to a chain evicts all rows
  for that memory_id) — enforced in application code, not triggers, for now.

### reflections
- `reflection_id` UUID PK, server default.
- `agent_id` FK → agents.
- `content` text NOT NULL.
- `identity_relevant` boolean — gates flow into the rendered identity document.
  *(Ruled 2026-07-13: boolean.)*
- `source_memory_ids` UUID[] — provenance only; intentionally NOT foreign-keyed, so purging an
  episode leaves the derived reflection intact (purge-honesty stance).
- `created_at` / `valid_at` / `invalid_at` — bi-temporal like memories; invalidation of a reflection
  later doubles as parameter-compiler cache eviction.

### identity_components
The entity/topic index: gist matching + entity-gate tripwire.
- `component_id` UUID PK, server default.
- `agent_id` FK → agents.
- `canonical` text NOT NULL.
- `aliases` text[].
- `category` text.
- `created_at` / `invalid_at` — reflection-time pruning **invalidates** rather than deletes,
  consistent with non-destructive storage; pruning silently invalidates reconstruction caches.

### identity_documents
- `agent_id` FK → agents.
- `rendered_text` text NOT NULL — the exact prompt block.
- `identity_version` text NOT NULL — content hash of `rendered_text`.
- `created_at`.
- PK `(agent_id, identity_version)`; current document = latest `created_at` per agent.

## Indexes

- **HNSW** on `memories.embedding`, `vector_cosine_ops`. *(Ruled 2026-07-13: cosine, for
  text-embedding-3-small. Fact-level correction specced 2026-07-18: the probe index moves to the
  fact-version chain at migration 002; this index's fate — drop vs dormant — is
  `[SETTLE-AT-BUILD]` in `fact-level-correction.md`.)*
- **GIN** on `memories.entities`.
- FK/lookup indexes: `memories(agent_id)`, `memory_details(memory_id)`,
  `memory_gist_spans(memory_id)`, `corrections(memory_id)`, `reflections(agent_id)`,
  `identity_components(agent_id)`.

## Mechanics

- Numbered SQL file(s) under `db\migrations\` (e.g. `001_foundation.sql`) plus `db\migrate.py`, a
  minimal Python runner. *(Ruled 2026-07-13: Python runner with a `schema_migrations` bookkeeping
  table — the seam migration 02+ lands on; each migration's DDL and its ledger row commit in one
  transaction, so a half-applied migration can never be logged complete. Migration 002 — the
  fact-version chain — specced 2026-07-18, `fact-level-correction.md`.)*
- Docker: `pgvector/pgvector` for Postgres 16; connection string from `.env`.

## Done when

- Given a fresh Postgres 16 + pgvector container, when the migration runs, then every table, check
  constraint, and index above exists (verifiable by query, not by eyeball).
- Running the migration a second time is a no-op, not an error.
- Given an insert violating a CHECK (bad typology value, rigidity out of 0.5–2.0, confidence out of
  0–1), the insert is rejected.
- Given inserts omitting `memory_id` / `detail_id` / etc., server-side UUID defaults fill them.
- A smoke-test fixture (one agent, one memory with one original detail row, one gist span, one
  identity component) inserts cleanly and reads back.
- Every `[SETTLE-AT-BUILD]` item touched was reported and confirmed before being built, and the
  choice recorded in `decisions.md`.
