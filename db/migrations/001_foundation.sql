-- 001_foundation.sql — longmem-npc foundational schema (migration 01).
--
-- Schema only: tables, CHECK constraints, and indexes. No seed data, no mechanism.
-- Principles honored here (see docs\architecture.md §2, docs\migration-01.md):
--   * Bi-temporal, non-destructive: created_at (server write time), valid_at (world
--     time, NOT NULL), invalid_at (NULL until superseded). Supersede by stamping
--     invalid_at; never UPDATE content in place, never DELETE (purge is the sole,
--     separate exception).
--   * UUID primary keys minted server-side via gen_random_uuid() (PostgreSQL 16 core;
--     no pgcrypto needed).
--   * Embedding dimension 1536, locked.
--   * All write-time fact columns exist now even where the consuming mechanism is
--     deferred (typology, provenance, context stamps, decay class, gist, importance,
--     pin, degradation flags).
--
-- Every statement is IF NOT EXISTS as defense-in-depth; the migrate.py schema_migrations
-- ledger is the primary idempotency mechanism.

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- agents — one row per NPC.
-- reputation / rigidity / reputation_sensitivity are per-NPC config supplied at
-- agent creation; no hardcoded column DEFAULT (nothing integrator-configurable is
-- hardcoded). diagnosticity_goal is text: the Haiku importance prompt consumes prose.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agents (
    agent_id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    text,
    seed_identity           text,
    reputation              numeric,
    rigidity                numeric CHECK (rigidity BETWEEN 0.5 AND 2.0),
    reputation_sensitivity  numeric,
    diagnosticity_goal      text,
    config                  jsonb
);

-- ---------------------------------------------------------------------------
-- identity_components — entity/topic index: gist matching + entity-gate tripwire.
-- Reflection-time pruning INVALIDATES (sets invalid_at), never deletes.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS identity_components (
    component_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id      uuid NOT NULL REFERENCES agents (agent_id),
    canonical     text NOT NULL,
    aliases       text[],
    category      text,
    created_at    timestamptz NOT NULL DEFAULT now(),
    invalid_at    timestamptz
);

-- ---------------------------------------------------------------------------
-- memories — one row per observation. observation_text is immutable after insert.
-- affect is three columns (valence + arousal + jsonb detail). decay_class is a
-- free-text label (the label -> tau_base map lives in agents.config); decay_class_unknown
-- is a write-time degradation flag mirroring scoring_failed (validation lands with the
-- write path).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS memories (
    memory_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id             uuid NOT NULL REFERENCES agents (agent_id),
    observation_text     text NOT NULL,
    embedding            vector(1536),
    importance_raw       real,
    scoring_failed       boolean NOT NULL DEFAULT false,
    typology             text CHECK (typology IN ('observed', 'told', 'inferred', 'reflected')),
    typology_confidence  real CHECK (typology_confidence >= 0 AND typology_confidence <= 1),
    typology_source      text CHECK (typology_source IN ('declared', 'inferred')),
    provenance           text CHECK (provenance IN ('lived', 'injected')),
    pinned               boolean NOT NULL DEFAULT false,
    decay_class          text,
    decay_class_unknown  boolean NOT NULL DEFAULT false,
    -- bi-temporal
    created_at           timestamptz NOT NULL DEFAULT now(),
    valid_at             timestamptz NOT NULL,
    invalid_at           timestamptz,
    -- context stamps (all optional API fields)
    location_embedding   vector(1536),
    location_name        text,
    entities             text[],
    event_time           timestamptz,
    affect_valence       real,
    affect_arousal       real,
    affect_detail        jsonb
);

-- ---------------------------------------------------------------------------
-- memory_gist_spans — gist as span pointers into memories.observation_text.
-- Child table so spans are individually assertable, immutable rows.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS memory_gist_spans (
    span_id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id             uuid NOT NULL REFERENCES memories (memory_id),
    start_char            int NOT NULL,
    end_char              int NOT NULL,
    matched_component_id  uuid REFERENCES identity_components (component_id),
    matched_category      text,
    created_at            timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- memory_details — the version chain under a stable memory_id.
-- The head is the row with invalid_at IS NULL (at most one live head per memory).
-- Verb discrimination lives on the head's write_cause; supersession is ordinary.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS memory_details (
    detail_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id    uuid NOT NULL REFERENCES memories (memory_id),
    content      text NOT NULL,
    write_cause  text CHECK (write_cause IN (
                     'original', 'reconstruction', 'rationalization',
                     'update_with_resentment', 'authorial_correction')),
    created_at   timestamptz NOT NULL DEFAULT now(),
    valid_at     timestamptz NOT NULL,
    invalid_at   timestamptz
);

-- ---------------------------------------------------------------------------
-- corrections — diegetic correction record; one row per in-world confrontation
-- that superseded a chain head. verb is the diegetic subset of the write_cause enum.
-- Schema now; the dissonance mechanism that writes these lands post-August.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corrections (
    correction_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id      uuid NOT NULL REFERENCES memories (memory_id),
    detail_id      uuid NOT NULL REFERENCES memory_details (detail_id),
    verb           text CHECK (verb IN ('rationalization', 'update_with_resentment')),
    source_event   jsonb,
    created_at     timestamptz NOT NULL DEFAULT now(),
    valid_at       timestamptz NOT NULL
);

-- ---------------------------------------------------------------------------
-- reconstruction_cache — keyed (memory_id, identity_version).
-- Eviction is by the generalized invariant, enforced in application code (not triggers).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reconstruction_cache (
    memory_id         uuid NOT NULL REFERENCES memories (memory_id),
    identity_version  text NOT NULL,
    rendered_text     text NOT NULL,
    created_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (memory_id, identity_version)
);

-- ---------------------------------------------------------------------------
-- reflections — bi-temporal like memories. source_memory_ids is provenance only
-- and intentionally NOT foreign-keyed (purge-honesty: purging an episode leaves the
-- derived reflection intact). identity_relevant is a boolean gate.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reflections (
    reflection_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id           uuid NOT NULL REFERENCES agents (agent_id),
    content            text NOT NULL,
    identity_relevant  boolean,
    source_memory_ids  uuid[],
    created_at         timestamptz NOT NULL DEFAULT now(),
    valid_at           timestamptz NOT NULL,
    invalid_at         timestamptz
);

-- ---------------------------------------------------------------------------
-- identity_documents — current document = latest created_at per agent.
-- identity_version is a content hash of rendered_text.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS identity_documents (
    agent_id          uuid NOT NULL REFERENCES agents (agent_id),
    rendered_text     text NOT NULL,
    identity_version  text NOT NULL,
    created_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (agent_id, identity_version)
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

-- At most one live head per memory chain.
CREATE UNIQUE INDEX IF NOT EXISTS memory_details_one_live_head
    ON memory_details (memory_id) WHERE invalid_at IS NULL;

-- HNSW on memories.embedding, cosine distance (text-embedding-3-small).
CREATE INDEX IF NOT EXISTS memories_embedding_hnsw
    ON memories USING hnsw (embedding vector_cosine_ops);

-- GIN on memories.entities (entity gate now, encoding-context boost later).
CREATE INDEX IF NOT EXISTS memories_entities_gin
    ON memories USING gin (entities);

-- FK / lookup indexes.
CREATE INDEX IF NOT EXISTS memories_agent_id_idx
    ON memories (agent_id);
CREATE INDEX IF NOT EXISTS memory_details_memory_id_idx
    ON memory_details (memory_id);
CREATE INDEX IF NOT EXISTS memory_gist_spans_memory_id_idx
    ON memory_gist_spans (memory_id);
CREATE INDEX IF NOT EXISTS corrections_memory_id_idx
    ON corrections (memory_id);
CREATE INDEX IF NOT EXISTS reflections_agent_id_idx
    ON reflections (agent_id);
CREATE INDEX IF NOT EXISTS identity_components_agent_id_idx
    ON identity_components (agent_id);
