# longmem-npc — Decision register

Append-only log of settled design decisions. Reference decisions by their **bolded names**. Do not
reopen without cause. If a newer decision conflicts with an older one, the newer wins and the older
entry gets a *superseded* note — never delete entries. Mechanics live in `architecture.md`; this
file records what was chosen, what it beat, and why (where the rationale was recorded).

## Primary decisions

**Schema now, mechanism later.** All write-time schema and population ship day one, even where the
consuming mechanism (reconstruction, dissonance, reflection) is deferred past the August demo. Pin
was promoted from schema-only to working day-one behavior for the demo. Rationale: lock schema and
API surface early so mechanisms land without migrations, and so the structural test suite can assert
shape before cognition exists.

**Retrieval gate: non-LLM hybrid (novelty + entity tripwire).** Mid-dialogue fetches are gated by an
embedding-novelty check plus an identity-components entity tripwire. No LLM in the gate. A **novelty
kill-switch is reserved** — to be decided later from the per-signal fire logs, which is why every
gate event records which signal fired. The entity tripwire is the most demo-legible signal.

**Turn topology: single call ships August; split-brain is the committed target.** August: one
Sonnet-class call emits prose + structured output. Target: a Haiku-class behavior call with its own
retrieval weights chooses the action; the dialogue call sees it as observed world fact. Contracts
(especially the action directive) are written to survive the migration.

**Memory identity: permanent id + version chain (write-back).** One `memory_id` forever; retellings
insert new detail rows superseding the prior. This resolved the critical fork of the project —
view-only vs write-back reconstruction — as **write-back with a scoped drift budget**. Rationale:
repetition-breeds-commitment (Talk of the Town precedent) requires retellings to be stored; the
bi-temporal chain keeps ground truth intact underneath.

**Habituation guards: both cap and decay.** For the future encoding-context term; both exist as
integrator knobs; implementation deferred.

**Dissonance threshold: importance × evidence typology × per-NPC rigidity (0.5–2.0).** "I saw it"
resists harder than "I heard it," on both sides of a clash. The store records the truth either way;
the threshold only shapes the character's reaction.

**Vector index: HNSW.** Chosen as cheaply reversible.

**Retention: tested purge endpoint, no scheduler.** The tool provides the delete verb; the schedule
is the integrator's policy. Purge deletes the original, its chain, and its caches; reflections
derived from purged episodes remain as aggregate work-product, and the docs say so honestly.

**License: Apache-2.0.** Public flip deferred to an end-of-project sprint.

**Prompt caching: append within scene, rebuild at scene boundaries.** Gate-fetched memories append
after the cached head as a marked recollection block; the head rebuilds at scene edges, where the
cache is cold anyway.

## Downstream decisions

**Drift budget: embedding distance from anchor; refuse-write past threshold.** Scoped to
reconstruction-driven write-backs only; event-driven (diegetic) writes are exempt. Re-anchoring by
cause: authorial → the corrected original; update-with-resentment → the new head; rationalization →
never (spends headroom without being blocked; a heavily defended memory crystallizes — "the story
has set"). The anchor is derivable, no pointer: the latest chain row with `write_cause` in
{original, authorial_correction, update_with_resentment}.

**Two correction verbs.** Authorial (operator fixes wrong data) is **replace-model**: it supersedes
the drifted chain with a corrected head row typed `authorial_correction`; the memory stays
retrievable with corrected content, and that head becomes the drift anchor. Diegetic (in-world
confrontation referencing a target memory) extends the chain through the dissonance path
(`rationalization` or `update_with_resentment` head, plus a correction record). Any correction
evicts caches. *(Authorial semantics ruled 2026-07-12 — dated entry below.)*

**Identity document: rendered + content-hashed.** Seed prose + identity-relevant reflections
rendered into the exact prompt block; `identity_version` = content hash; recompiled at scene edges.

**Reconstruction serving: batched Haiku, pre-warm, block-with-signal.** One structured call batches
all k cache misses per retrieval; pre-warm at dialogue init; a mid-scene miss blocks and exposes a
"reconstructing" signal (latency becomes characterization). The reconstruction threshold reuses the
decay math. Async serve-verbatim-then-cache was explicitly rejected; any future async must be
explicit state, never silent text mutation (within-scene text-stability invariant).

**Reflection: endpoint + pressure gauge.** No scheduler; the integrator pulls the trigger. Sampling
weighted by importance × recency, not recent-N.

**Scene-type parameter bundles: typed core + namespaced passthrough.** Integrator-owned scene-type
vocabulary; unknown types log-and-continue against a default bundle; compiled params consumed only
upstream of the dialogue call.

**Typology & confidence: client wins.** Optional client-declared typology; Haiku classifies when
absent; `typology_source` records declared vs inferred. Confidence 0–1 from a default per-typology
table with per-event client override.

**Context stamps: four optional fields, typed columns.** Location, entities, time, affect; per-field
degradation stated; typed column per component (per-component read weights require it); location
embedded via the same 1536 model.

**Reputation: model-emitted delta.** Haiku emits a delta by default; client override wins; per-NPC
sensitivity scalar; hard clamp on a defined scale; injected from a scene-start snapshot.

**Test suite scope: structural-only.** Assertions on memory IDs, row types, and structure — never on
generated prose. Judged evals (drift-toward-identity, Bartlett-style distortion) belong to the eval
story / paper ablations, not the suite.

**Read-mode boundary: self-describing three-state.** Every payload carries `read_mode` and `pinned`.
Pin/unpin are endpoints; pinning freezes the current head; restoration is a correction verb, not
pin; unpinning resumes from the frozen head.

## Audit rulings

1. **Both correction verbs outrank pin; the new head inherits the pin.** Pin means exactly two
   things: decay exemption + reconstruction exclusion. (Final ruling — supersedes a stale earlier
   summary claiming pin blocks the diegetic verb. It does not.)
2. **Generalized cache-eviction invariant.** Cache writes happen only in the reconstruction path;
   any other writer to a chain — correction, diegetic write, purge — must evict all cache rows for
   that memory_id.
3. **Gate degradation ladder** (replaces a dead "gate parse failure" clause): embeddings down →
   entity-only lexical fetch off the GIN index ranked by recency × importance; no entities →
   novelty-only; both out → gate closed, serve the loaded set, fail-quiet. Which-signal-fired is
   logged per event; the entity gate's lookup table *is* the identity components table.
4. **Within-scene text-stability invariant.** Absent a diegetic event on that memory, repeated reads
   within one scene return byte-identical text. Constrains any future async fallback.
5. **`typology_source` is a distinct field from provenance** (`lived | injected`).
6. **Write-time facts vs runtime state.** Facts populate day one; runtime state rides with its
   mechanism. The `write_cause` enum
   (`original | reconstruction | rationalization | update_with_resentment | authorial_correction`)
   lives on detail rows; the drift anchor is derivable from it.

## Tension log (summary)

Four early tensions were closed by, respectively, the gate design, the turn-topology decision, the
prompt-caching policy, and the schema-now stance. One tension (does stored importance go stale as
the telling drifts?) was **deliberately disregarded**, rationale documented under write-time facts
vs runtime state in `architecture.md`. One tension was resolved as a documentation obligation
rather than a code change. One tension (how can the suite test correction behavior before the
dissonance mechanism exists?) was closed by **verb-forked structural test pairs keyed on
`write_cause`** — no fixture mode; the diegetic half of each pair lands when the dissonance
mechanism ships.

## Decay & gist session — 2026-07-12 (latest word; refines the migration spec)

Gist = span pointer into immutable observation text. Identity components table with canonical +
aliases + category. NLP write pass with loose LLM escalation (importance threshold / ambiguous
entity hit / novel entity — novel entities grow the table). VADER-class lexicon affect at write.
`tau_effective` decay on details only, down to fully hidden; gist never decays. Cross-observation
coreference misses accepted. Coreference via fastcoref or coreferee. Reflection-time component trim
silently invalidates caches. A spam gate on novel-entity growth is deferred.

*(Superseded in part 2026-07-13 by the write-path build rulings below: escalation grew from the
three triggers sketched here to five; coreference settled on fastcoref; affect settled on VADER +
Warriner 2013 VAD.)*

## Authorial-correction ruling — 2026-07-12

**Replace model adopted.** Authorial correction writes a corrected head row
(`write_cause = authorial_correction`) that supersedes the drifted chain and becomes the new drift
anchor; the memory_id stays in retrieval candidates, serving corrected content. **Rejected:**
erase-model (invalidate everything, re-ingest the fix as a new memory) — it would have left the
`authorial_correction` enum value and the authorial re-anchor branch dead.

Consequences propagated: the one-live-head index in migration 01 is confirmed compatible; the Set A
authorial assertions in `test-suite.md` now assert presence-with-corrected-head instead of absence;
no voided-marker column on prior rows — the new head's `write_cause` is the sole verb discriminator
(revisit only if the debug view ever needs retracted-vs-past-telling rendering).

## Schema-gap rulings — 2026-07-12

A doc-auditor sweep found three schema-now omissions where `architecture.md` described a mechanism
the schema doc (`migration-01.md`) never gave a home. Jack ruled:

1. **`scoring_failed` is a day-one column on `memories`.** `boolean NOT NULL default false`; set true
   when the importance-scoring model fails and the write lands with neutral importance (architecture
   §2, `test-suite.md` degradation case). It is a write-time fact — omitting it would force exactly
   the later migration **Schema now, mechanism later** exists to prevent.
2. **The diegetic "correction record" lives in a separate `corrections` table**, added to migration
   01 as schema only (the dissonance mechanism that writes it lands post-August). Columns:
   `correction_id`, `memory_id` → memories, `detail_id` → memory_details (the new head), `verb`
   CHECK in `{rationalization, update_with_resentment}` (the diegetic subset of the `write_cause`
   enum), nullable `source_event` jsonb, and bi-temporal `created_at`/`valid_at`. Chosen over
   folding it onto the head detail row so the confrontation reference and target have an explicit
   home. Backs the Set A diegetic pair's "correction record present" assertion.
3. **The `identity_components` pruning `[SETTLE-AT-BUILD]` tag is removed** — already answered by the
   non-destructive invariant (never DELETE except purge) and the decay/gist decision (component trim
   silently invalidates caches). The body text was already correct; only the confirm-tag was stale.

**Drift-anchor wording (standing phrasing):** the re-anchoring line above ("authorial → the
corrected original") reads, correctly and consistently with `architecture.md` §7, as **authorial →
the corrected head (the `authorial_correction` row)**. Same row under the derivable-anchor
definition; this entry fixes the phrasing without editing the append-only original.

## Local DB + MCP infra — 2026-07-13

The migration-01 database floor is a **committed `docker-compose.yml`** (not a bare `docker run`):
`pgvector/pgvector:pg16` as container `longmem-pg`, named volume `longmem-pgdata`, host port 5432.
All credentials interpolate from the gitignored `.env`, the single source for `DATABASE_URI`
(superuser `postgres`, db `longmem`). One full-access connection string; the Postgres MCP enforces
read-only itself via `--access-mode=restricted`, registered at **local scope** so no secret is
committed. Rationale: compose is reproducible, holds no secrets, and becomes the seam migration 02+
and the app pool reuse. pgvector 0.8.5 confirmed available; `CREATE EXTENSION` is deferred to
migration 01, not this floor.

**Runbook deviation (recorded so a rebuild reproduces it):** `postgres-mcp` → `pglast==7.2` has no
wheel for Python 3.14 and fails to build from source on Windows (no C toolchain). The MCP therefore
runs in an isolated **uv-managed Python 3.13** tool venv (`uv tool install postgres-mcp --python
3.13`). This does not touch the project's Python 3.14 stack constant — the MCP is a standalone
server process, never imported by project code. `mcp-setup.md` §1 should gain a one-line note to
this effect until `pglast` ships a 3.14 wheel (flagged to Jack; not yet applied).

## Migration 01 build — fork rulings & schema deltas — 2026-07-13

Migration 01 built and floor-verifier-passed against the live `longmem` DB. Jack ruled the seven
`[SETTLE-AT-BUILD]` forks from `migration-01.md` (status.md had said "six"; the doc carried seven):

1. **`agents.diagnosticity_goal` = `text`.** The Haiku importance prompt consumes prose.
2. **`memories.decay_class` = free-text label + config map.** The label→`tau_base` map lives in
   `agents.config`. **New column `memories.decay_class_unknown boolean NOT NULL default false`** — a
   write-time degradation flag mirroring `scoring_failed`: on an unrecognized decay-class label the
   write lands with a default class and this flag set, never rejected. Validation is write-path
   (deferred). This column was not in the original migration-01 spec; it is a consequence of the
   ruling and is now built.
3. **`memories.affect` = three columns:** `affect_valence real`, `affect_arousal real`,
   `affect_detail jsonb` (all nullable), fed by the VADER-class write pass. Richer than the suggested
   valence+jsonb default.
4. **Gist spans = child table** `memory_gist_spans` (not an int-range array on `memories`) — backs
   the suite's per-row gist-immutability assertions.
5. **`reflections.identity_relevant` = `boolean`.**
6. **HNSW distance op = cosine** (`vector_cosine_ops`), for `text-embedding-3-small`.
7. **Migration runner = Python** (`db\migrate.py`) with a `schema_migrations` bookkeeping table.
   **Atomic apply-and-record:** each migration's DDL and its ledger row commit in one transaction, so
   a half-applied migration can never be logged complete. Idempotency rides on the ledger (a second
   run is a no-op); DDL also carries `IF NOT EXISTS` as defense-in-depth.

**Schema strengthening beyond the doc's literal column lists (recorded for transparency).** Owner
foreign keys (`memories.agent_id`, `identity_components.agent_id`, `memory_gist_spans.memory_id`,
`memory_details.memory_id`, `corrections.memory_id`/`detail_id`, `reflections.agent_id`) and gist
offsets (`start_char`/`end_char`) are **NOT NULL** — a row cannot exist without its owner, nor a span
without its offsets. `valid_at` is NOT NULL per the bi-temporal invariant; `invalid_at` nullable. Per
*nothing-hardcoded*, `reputation`, `rigidity`, `reputation_sensitivity`, `diagnosticity_goal`,
`decay_class`, and `config` carry **no column default** — the write path supplies them from
integrator config (reputation → the config scale's neutral point at agent creation).

**Dependency management (backend's first Python dep).** Ruled **global Python 3.14** install (matches
the stack constant) plus a repo-root **`requirements.txt`** manifest, pinning `psycopg[binary]==3.3.4`
(a `cp314` Windows wheel exists — unlike `pglast`, no isolation was forced). The Postgres MCP keeps
its separate uv/3.13 venv.

**Infra note (flagged, not yet fixed).** The `floor-verifier` subagent could not call the `postgres`
MCP tools despite its `mcpServers: postgres` frontmatter; it verified against the same live container
via `psql` instead. Verification is sound, but the MCP-preference directive isn't yet effective for
that subagent — worth revisiting before the write-path build. *(Resolved 2026-07-13 — the fix was the
`tools` allowlist, not `mcpServers`; recorded in `status.md`.)*

## Write-path spec scope rulings — 2026-07-13

Authoring `write-path.md` (the write path & ingestion API v1 build target) required three scope
rulings; Jack ruled:

1. **Surface = one ingest service, two thin callers.** The write path is a single ingest service that
   is **the sole instrumentation seam**; the CLI harness calls it in-process and a thin FastAPI route
   wraps it — neither duplicates the seam. Its return is a **structured `IngestResult` (memory IDs +
   computed scores/facts, not just prose)**, extending the read-path "IDs + scores in every payload"
   invariant to writes so the CLI debug view and the scenario suite both assert on structure. The
   FastAPI route is a pass-through: for one ingest, its JSON is exactly the service's `IngestResult`.

2. **v1 event set = observe + scene-boundary + pin/unpin.** The observe pipeline (NLP → single Haiku
   call → embedding → atomic insert) is the meat. Scene-boundary is **accepted + instrumented only**
   in v1 — its three consumers (prompt-head rebuild, identity recompile, reputation snapshot) are
   deferred and it needs **no new schema**. Pin/unpin toggle `memories.pinned`. Diegetic-correction
   and purge are written into the contract but their handlers are **deferred** (out of v1 scope).

3. **Models = provider interfaces with real + deterministic fake.** The Haiku
   render/importance/typology call and the OpenAI 1536-d embedding are each behind a
   per-role-env-var provider interface with **both** a real implementation (drives the demo) and a
   **deterministic fake** (so the structural suite / CI run offline, keyless, and never assert on
   prose).

The spec tags the remaining physical shapes `[SETTLE-AT-BUILD]` (NLP stack, LLM-escalation
thresholds, idempotency — constrained to no-new-schema, embedding-failure degradation, wire shape)
and surfaces open flags (scene-boundary needs no migration-02; the render seam — raw
`observation_text` vs. rendered `original` detail content; VADER lacks an arousal axis). These are
ruled at the write path's build, not now.

## Write-path build — fork rulings & build notes — 2026-07-13

Write path v1 built and floor-verifier-passed (verification on scratch DB `longmem_test`; product
`longmem` confirmed untouched). Jack ruled the four majors up front; the minor shapes were approved
with the build plan.

1. **Render seam — confirmed as specced.** Raw client text → `memories.observation_text`
   (immutable); the Haiku render → the `original` detail head's `content`; gist spans point into
   `observation_text`. On write-call failure the head falls back to the raw observation text
   (never a lost write).
2. **Embedding failure → the write lands with a NULL embedding.** `embedding IS NULL` is the
   queryable degradation signal (frozen schema allows no flag column); mirrored in the payload as
   `IngestResult.embedding_failed` — a payload-only extension of the spec's field list, added so
   the degradation is assertable without a DB peek. Memory stays reachable via the entity/GIN
   path; vector backfill is future work.
3. **NLP stack: spaCy `en_core_web_lg` + fastcoref + VADER + Warriner 2013 VAD lexicon.**
   - **License gate outcome:** NRC-VAD **rejected** — non-commercial-research-only, incompatible
     with the planned Apache-2.0 flip. The pre-ruled fallback **Warriner et al. 2013** is CC-BY
     4.0 (per its NoRaRe database entry) and is bundled, slimmed to Word/V/A/D columns, at
     `data\lexicons\warriner_2013_vad.csv` with `ATTRIBUTION.md`.
   - Affect: VADER compound → `affect_valence`; Warriner lemma-lookup means (1–9 normalized to
     0–1) → `affect_arousal`; **dominance lives in `affect_detail` jsonb** (frozen schema has no
     dominance column) alongside the raw VADER + Warriner breakdowns. Arousal is therefore
     populated in v1 — the spec's open flag is closed.
   - **Environment facts (recorded so a rebuild reproduces them):** fastcoref 2.1.6 is
     incompatible with transformers 5.x at runtime → `requirements.txt` pins `transformers<5`
     (4.57.6 verified). fastcoref internally requires `en_core_web_sm` (its tokenizer), installed
     alongside `en_core_web_lg`. spaCy model downloads must use the pip wheel URLs pinned in
     `requirements.txt`, NOT `spacy download` — spaCy's downloader shells out to uv on this
     machine (installed for the Postgres MCP) and dies outside a venv. psycopg async cannot run
     on Windows' ProactorEventLoop → the API runs via `python -m app.serve` (SelectorEventLoop
     runner), never bare `uvicorn app.api:app`; the walker passes `loop_factory` to
     `asyncio.run`.
   - Coref/NER confidence: fastcoref's public predict API exposes no per-span probability and
     `en_core_web_lg`'s greedy NER exposes none either, so v1 treats every coref-derived identity
     span as low-confidence — over-calls only (biased loose), never suppresses.
4. **LLM escalation: full in v1, gist correctness over speed/cost.** Separate provider + its own
   env var (`LONGMEM_MODEL_ESCALATION`). Five triggers, any one fires (all integrator-tunable via
   `agents.config`, defaults in `app\config.py::SERVICE_DEFAULTS`): (1) importance ≥ 0.45;
   (2) identity/category hit with |valence| ≥ 0.5; (3) any novel entity; (4) unresolved
   pronoun/noun-chunk co-occurring with an identity/category hit; (5) low NLP confidence on an
   already-flagged span. `escalated_by` + escalation token counts recorded per write in
   `IngestResult.instrumentation` (feeds the per-100-turn cost table).
   **Failure path — BUILD-PHASE STANCE, MUST BE RE-RULED BEFORE THE DEMO PUBLISHES:** retry once,
   then HARD-STOP the write (fail-loud; nothing inserted — escalation precedes the insert, so a
   client resend is safe pre-idempotency). This is deliberately not a production posture; the
   production/demo failure behavior for escalation is an **open decision** owed before the demo
   video ships.
5. **Minor shapes (approved with the plan):** wire shape `POST /v1/events/observe`,
   `POST /v1/events/scene-boundary`, `PUT /v1/memories/{memory_id}/pin`; idempotency stays
   accept-not-enforce (spec default; needs schema); `phase_tag` and `event_id` are accepted but
   have no schema home in v1 (not stored, not echoed); per-role env vars retained with a loud
   startup check that the three write-call roles (importance/render/typology) name the same model
   (one call serves all three in v1); provider selection `LONGMEM_PROVIDER_MODE = real | fake`
   (fake = offline default); process env vars override same-named `.env` keys (lets verification
   target the scratch DB without touching `.env`); verification runs on a scratch DB
   `longmem_test` created/dropped around the walker via the new `db\migrate.py --database-uri`
   flag (floor re-verified: no-arg run on `longmem` still a clean no-op); no agent-creation
   endpoint in v1 — fixtures insert agents via SQL.
