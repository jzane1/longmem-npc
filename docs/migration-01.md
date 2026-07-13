# Migration 01 — Foundational schema

First build target. Fully unblocked. Everything here is **schema only**: hand-written SQL against
PostgreSQL 16 + pgvector (Docker, `pgvector/pgvector` image), UUIDs minted server-side.

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
  importance, pin.

## Tables

### agents
One row per NPC.
- `agent_id` UUID PK, server default.
- `name` text.
- `seed_identity` text — the seed prose; revised by reflection later.
- `reputation` numeric — runtime scalar; starts at the scale's neutral point.
- `rigidity` numeric, CHECK between 0.5 and 2.0 — dissonance scalar (pushover → zealot).
- `reputation_sensitivity` numeric.
- `diagnosticity_goal` — anchor for importance scoring. `[SETTLE-AT-BUILD: numeric target vs short
  text description; suggested default: text, since the Haiku importance prompt consumes it]`
- `config` jsonb — remaining integrator knobs (decay constants, drift threshold, habituation
  cap/decay, etc.) until any of them earns a typed column.

### memories
One row per observation. **`observation_text` is immutable after insert.**
- `memory_id` UUID PK, server default.
- `agent_id` FK → agents.
- `observation_text` text NOT NULL.
- `embedding` vector(1536) — dimension locked.
- `importance_raw` real — stored raw; normalized at read.
- `typology` text CHECK in (`observed`, `told`, `inferred`, `reflected`).
- `typology_confidence` real CHECK 0–1.
- `typology_source` text CHECK in (`declared`, `inferred`).
- `provenance` text CHECK in (`lived`, `injected`).
- `pinned` boolean NOT NULL default false.
- `decay_class` text — integrator vocabulary; selects the base decay constant.
  `[SETTLE-AT-BUILD: free text vs lookup table; suggested default: free text + config-defined map]`
- `created_at` / `valid_at` / `invalid_at` per the bi-temporal rules above.
- Context stamps (all four nullable — optional API fields):
  - `location_embedding` vector(1536) and `location_name` text.
  - `entities` text[] — with a **GIN index** (serves the entity gate now, context boost later).
  - `event_time` timestamptz.
  - `affect` — `[SETTLE-AT-BUILD: single valence real (−1..1) vs valence+arousal pair vs VADER
    compound struct; suggested default: valence real + jsonb detail column]`

### memory_gist_spans
Gist as **span pointers into `observation_text`** — never rewritten text. Child table so spans are
individually assertable rows (the suite asserts gist rows are immutable).
`[SETTLE-AT-BUILD: child table (suggested) vs int-range array column on memories]`
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

### reconstruction_cache
- `memory_id` FK → memories.
- `identity_version` text — content hash of the rendered identity document.
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
  `[SETTLE-AT-BUILD: boolean flag (suggested) vs classification enum]`
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
  `[SETTLE-AT-BUILD: confirm invalidate-not-delete for pruning]`

### identity_documents
- `agent_id` FK → agents.
- `rendered_text` text NOT NULL — the exact prompt block.
- `identity_version` text NOT NULL — content hash of `rendered_text`.
- `created_at`.
- PK `(agent_id, identity_version)`; current document = latest `created_at` per agent.

## Indexes

- **HNSW** on `memories.embedding`. `[SETTLE-AT-BUILD: distance op — cosine suggested for
  text-embedding-3-small]`
- **GIN** on `memories.entities`.
- FK/lookup indexes: `memories(agent_id)`, `memory_details(memory_id)`,
  `memory_gist_spans(memory_id)`, `reflections(agent_id)`, `identity_components(agent_id)`.

## Mechanics

- Numbered SQL file(s) under `db\migrations\` (e.g. `001_foundation.sql`) plus a minimal runner.
  `[SETTLE-AT-BUILD: plain psql invocation vs a ~50-line Python runner with a migrations bookkeeping
  table; suggested default: the Python runner — it becomes the seam where migration 02+ lands]`
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
