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

*(Superseded in part 2026-07-14 by the re-slating ruling below: the reconstruction mechanism moves
into pre-demo scope. The schema-now stance itself and the dissonance and reflection deferrals
stand.)*

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

## Re-slating ruling — reconstruction moves pre-demo — 2026-07-14

A full pre-demo/post-demo scope audit (requested by Jack mid-session, aborting a read-path spec
attempt whose tentative scoping answers were discarded unrecorded) found that the demo as slated
demonstrated the immutable record — storage, decay, correction-override, gate-recollect — but not
the thesis: the reconstruction mechanism sat post-August, so every demo read would have been
`read_mode = verbatim`, no drift would exist, and the 60-day drift plot beat was explicitly
contingent ("when reconstruction ships"). Jack ruled:

1. **The reconstruction mechanism ships before the August demo.** In scope: identity-conditioned
   reconstruction as the mandatory read path past theta; the write-back version chain
   (`write_cause = reconstruction`); the `(memory_id × identity_version)` cache *[key refined at
   spec time — see the 2026-07-17 entry: the version component composes `identity_version` with a
   scene-frozen decay band]*; the drift budget
   with re-anchoring; batched serving with pre-warm and the block-with-"reconstructing"-signal
   miss path; a reconstruction model role (`LONGMEM_MODEL_RECONSTRUCTION`) behind a provider
   interface with a real implementation + a deterministic fake; the Set C suite scenarios.
   Rationale: the demo video is the introduction artifact and must demonstrate the claim axis —
   controlled infidelity above an immutable record — not just the record. The prior deferral
   traced to the deadline, and the standing rule is that the deadline never drives a decision.
   **Ruled with the schedule cost explicitly flagged:** pulling the largest mechanism into the
   August window may cost demo beats or the date; Jack accepted that trade. **Supersedes in
   part** the *Schema now, mechanism later* primary decision (its reconstruction clause only —
   the schema-now stance and the dissonance/reflection deferrals stand).
2. **Authorial-correction endpoint → pre-demo**, its own small build target after reconstruction
   lands. The correction-override demo beat and the Set A authorial pair require it, and it
   interacts with reconstruction (cache eviction, drift re-anchoring), so it builds on that floor.
3. **Scene-boundary consumers split:** the reputation snapshot lands with the dialogue turn
   (architecture §9's August single-call ship injects it); identity-document
   recompile-at-scene-edge lands with reconstruction (cache keying needs `identity_version`; the
   pre-demo document is **seed-prose-only**, rendered + content-hashed, since reflection stays
   deferred); **prompt-head rebuild / prompt caching → post-August** (no demo beat names it;
   revisit only if demo latency demands).
4. **Purge → post-August**, explicitly before the public flip (integrator surface; no demo beat).
5. **Reflection's "if not landed in August" hedge is resolved: explicitly post-August.**

Consequences propagated: `status.md` immediate queue re-slated (read path → CLI harness →
reconstruction → authorial correction → gate → suite session → Unity/demo); the post-August ledger
loses its reconstruction items and gains purge and prompt caching explicitly; the demo
choreography's 60-day drift plot is a planned beat, no longer contingent; `architecture.md` §2 and
§7 deferral markers updated. Docs only — no code changed with this ruling.

## Read-path spec scope rulings — 2026-07-14

Authoring `read-path.md` (the dialogue-init retrieval v1 build target) required two scope rulings.
The surface itself was already fixed by the re-slating ruling above: **retrieval-only** — one
retrieval service seam with a thin pass-through FastAPI route, mirroring the write-path surface
ruling; the Sonnet dialogue call rides with the CLI harness (immediate-queue item 2). Jack ruled:

1. **Query input = text + reserved context.** `query_text` is required and embedded **as-is** as
   the relevance probe — the integrator authors it (opening utterance or scene blurb).
   `location_name` / `entities[]` / `event_time` are accepted and shape-validated but **not
   consumed and not echoed** in v1 — reserved slots for the post-August encoding-context term,
   mirroring three of the four write-side context stamps (the phase_tag/event_id
   accept-now-consume-later precedent). **Affect is deliberately not reserved** (ruled same day,
   on a doc-auditor finding that the slot mirror was overstated): a query-side affect field's
   shape — and whose affect it would carry — is undesigned; it gets its shape with the
   encoding-context term rather than as a guessed slot, and the spec states the exclusion
   explicitly. **Rejected:** server-side composition of context into the
   probe — it would bake context into the relevance term and double-count it once the real
   encoding-context term ships (a separate weighted term is the committed design), and the
   composition template would be a hidden hardcoded authorial artifact colliding with
   nothing-hardcoded. The demo makes context matter by writing it into `query_text` explicitly —
   same effect, visible in the debug view.
2. **v1 serving = verbatim-only.** Retrieval (candidates + scoring) is specced as a separate stage
   from serving (text assembly + read-mode stamping). v1 serves the live `memory_details` head
   verbatim with `read_mode = "verbatim"` on every item — honest self-description; the three-state
   boundary collapses to one state because no reconstructor exists yet. The decay math is built
   now and surfaces as the **recency score component**, so Set B asserts decay-vs-invalidation
   distinctness through scores. The theta check, cache reads, and `reconstructed` read_mode land
   with reconstruction (immediate-queue item 3), which **swaps the serving stage only** —
   retrieval and scoring are untouched by that swap, and reconstruction's pre-warm hooks this same
   dialogue-init seam.

The spec consolidates the retrieval scoring function from the artifact queue
(relevance × recency(decay class) × importance_norm; pin exemption → recency = 1.0; reserved slots
for the context term and per-call `weight_overrides`) and tags the remaining physical shapes
`[SETTLE-AT-BUILD]` (wire shape, distance→similarity mapping + over-fetch, recency knobs +
shared-`tau_effective` confirmation, importance_norm method, k default, `as_of` override,
`weight_overrides` shape, empty/short-store behavior, query-embedding-failure fallback — suggested
fail-quiet recency × importance ranking with a `degraded` flag, the read analog of
never-lose-a-write). These are ruled at the read path's build, not now.

## Read-path build rulings — 2026-07-14

Every `[SETTLE-AT-BUILD]` shape in `read-path.md` was reported with the build plan and ruled by Jack
before being built. Two genuine forks plus one build-surfaced conflict were ruled explicitly; the
remaining shapes were approved with the plan (the write-path precedent). All knobs below are
service defaults in `app\config.py`, per-agent overridable via `agents.config` (`agent_knob`).

1. **`as_of` override — ADOPTED as specced.** Optional tz-aware timestamp on `DialogueInitRequest`;
   defaults to server now (UTC); echoed in instrumentation as `as_of_effective`. Consequence
   propagated: `tests\CLAUDE.md`'s time-travel line now names both mechanics (injected `valid_at`
   + `as_of`).
2. **Query-embedding failure — FAIL-QUIET fallback** (the spec's suggested ladder row): rank ALL
   live candidates (NULL-embedding rows included) by `recency × importance_norm`;
   `degraded = true` + reason in instrumentation. Sub-shape ruled with it: the per-item
   `relevance` component is **null** on this path — honest self-description, none was computed
   (the field is `float | None`). Never-blank-a-dialogue, the read analog of never-lose-a-write.
   **Rejected:** fail-loud — a dead embedding provider would silence every NPC.
3. **`importance_norm` = clamp + floor, superseding the spec's min-max suggestion.**
   `importance_norm = clamp(importance_raw, importance_norm_floor, 1.0)`, floor default **0.05**.
   Ruled on a conflict surfaced at build: min-max bounds over the agent's live rows would let
   invalidating an extreme row move *other* items' scores, breaking the spec's own Set B principle
   ("invalidation excludes rows without touching other items' scores"). `importance_raw` is
   already contractually 0..1 from the write call, so read-time normalization is honestly a
   floor + clamp, and the invalidation principle now holds exactly, for every row. Tradeoff
   accepted: a compressed importance distribution is not stretched to full [0,1]. NULL
   `importance_raw` (fixture-only; the write path never stores it) takes the `importance_neutral`
   knob before clamping.
4. **Wire shape:** `POST /v1/dialogue/init`, `response_model = RetrievalResult`, route
   pass-through; unknown agent → 404 (mirrors the write path). Models in `app\schemas.py`;
   reconstruction's pre-warm hooks this endpoint at item 3.
5. **Relevance mapping + SQL shape:** `relevance = clamp(1 − cosine_distance, 0, 1)`; over-fetch
   `max(k, ceil(retrieval_overfetch_factor × k))` candidates by `<=>` over live rows with
   non-NULL embeddings joined to the live detail head, re-ranked in Python by the full score.
   Knob `retrieval_overfetch_factor` default **4.0**.
6. **Recency knobs:** shared `tau_effective` **CONFIRMED** — one formula, one implementation
   (`app\decay.py`), which the reconstruction theta check imports at item 3. Knob
   `decay_k_importance` default **1.0** (named for the shared decay math, not retrieval-only).
   `age = as_of − valid_at`, clamped at ≥ 0 so a future-dated `valid_at` caps at recency 1.0.
   Label → tau resolution mirrors the write path's rule (stored label if mapped → the agent's
   default class → new knob `tau_fallback_seconds`, default **604800** — a read never fails on a
   resolvable row).
7. **k default:** knob `retrieval_top_k` = **8**; resolution order request `k` (≥ 1) →
   `agents.config` → service default; the effective value surfaces as `k_effective`.
8. **`weight_overrides` reserved shape:** optional `{relevance?, recency?, importance?}` float
   multipliers; shape-validated, not consumed, not echoed (as suggested).
9. **Empty/short store:** 0..k items, never an error — a valid young-NPC state (as suggested);
   `candidate_count` in instrumentation.

Approved with the plan, cross-cutting: component normalization as suggested (each component in
[0,1], product in [0,1], no further rescaling), and a determinism shape — final ordering
`(−score, memory_id)` so ties are stable and within-scene byte-identity holds across identical
calls.

## CLI-harness spec scope rulings — 2026-07-14

Authoring `cli-harness.md` (the CLI harness & synthetic load driver v1 build target — the remaining
piece of the vertical slice, *retrieved memories → dialogue out*, consolidating architecture §9 + §11
over the frozen schema) required two scope rulings. The surface was already fixed by prior rulings:
the harness composes the two built seams (ingest, retrieval) in-process and adds the single Sonnet
call; the reputation-snapshot scene-boundary consumer lands here per the 2026-07-14 re-slating. Jack
ruled:

1. **Reputation delta = persist in-place.** The single Sonnet call emits a per-turn
   `reputation_delta`; the harness applies
   `clamp(reputation_prev + reputation_sensitivity × delta, scale_min, scale_max)` and **UPDATEs
   `agents.reputation` in place** (a client-supplied delta override wins over the model's delta, per
   §9). The scene-start snapshot is read at the scene boundary and frozen into the prompt prefix for
   that scene; mid-scene deltas accumulate on the row but the injected snapshot does not change until
   the next boundary (freezing is a property of the seam contract — scene state lives in the caller,
   which passes the snapshot in and refreshes it only at a boundary). **Invariant note:** this is an
   in-place **UPDATE** of an agent-row *runtime scalar* — the same class of operation as the existing
   pin-flag toggle (`set_pinned` flips `memories.pinned` in place, shipped write-path v1), and
   likewise **outside** the memory-content non-destructive invariant (which governs `memories` /
   `memory_details` content; never DELETE except purge). Reputation is runtime state, not stored
   memory content (architecture §9: "a scalar on the NPC row"; the migration-01 schema gave it a
   single mutable column with no default, not a version chain). The `CLAUDE.md` invariant clarification for
   the reputation scalar rides with the *build* (when the UPDATE lands), not the spec. **Rejected:**
   compute-and-return-only (mirroring write-v1's accept-and-instrument scene-boundary) — it would
   leave the reputation-drift demo beat inoperative and the scene-start snapshot static; and
   non-destructive reputation history — it needs new schema this spec forbids (the frozen migration-01
   schema stands). The scale neutral/min/max and the sensitivity default remain integrator config
   (`agents.config` / `SERVICE_DEFAULTS`), never hardcoded.

2. **Drive surface = interactive REPL over a shared session-runner core.** The CLI is a
   human-drivable console (typed utterances + meta-commands) with a `--debug` view exposing retrieved
   memory IDs + scores, the parsed structured output (prose / action directive / reputation delta),
   and token + latency counts — the product surface whose "main file reads as documentation"
   (`status.md`). A **session-runner core beneath it is reused by the synthetic load driver**, which
   drives scripted sessions at volume through the same seams to emit §11's latency histogram and
   per-100-turn cost table. **Rejected:** scripted-transcript-replay-only (no hand-drivable product
   surface for the demo) and interactive-REPL-only with a separate load-driver script (the two paths
   would drift apart — architecture §11 makes the driver first-class, "no distribution exists without
   it").

**Reconciliation baked into the spec (a doc tension, not a new fork).** §9 reads both "August ship: a
single Sonnet-class call" and "the Haiku call emits a delta by default." The 2026-07-14 re-slating
governs the slice: the reputation snapshot injection lands with "architecture §9's August
**single-call** ship," so the **one Sonnet call** carries prose + action directive + reputation delta
together; the "Haiku call" wording describes the *post-August split-brain* behavior call. The spec
states this explicitly so no one wires a second Haiku behavior call into the vertical slice.

The spec tags the remaining physical shapes `[SETTLE-AT-BUILD]` (the `LONGMEM_MODEL_DIALOGUE` env-var
name; the dialogue structured-output schema + parse/validation; the reputation apply shape — scale
bounds/neutral/sensitivity defaults + config keys; the action-directive vocabulary source; the
prompt-assembly block shape; the never-blank fallback line; the CLI meta-command surface + entry
point + `--debug` rendering; the load-driver script format + scale knobs + aggregate output; whether
the turn payloads are Pydantic models or dataclasses). These are ruled at the harness's build, not
now. The dialogue call is a new model role behind a provider interface with a real implementation + a
deterministic fake, following the write-path triad; every retrieved memory is served **verbatim** (no
reconstruction in the slice).

## CLI-harness build rulings — 2026-07-15

*[Count correction, 2026-07-16 audit: the spec carried **ten** settle-tags (the nine-item list plus
the `reputation_snapshot`-plumbing tag inline in the request contract), and "cost units" was a
plan-raised choice implicit in the instrumentation contract, not a spec tag — so the tallies below
("nine shapes", "two genuine forks" among them) miscount; the itemized rulings themselves are the
authoritative, complete record: one spec tag ruled via explicit question (action-vocabulary
source), nine spec tags approved with the plan, plus the cost-units question.]*

The harness build (spec: `cli-harness.md`) settled the nine `[SETTLE-AT-BUILD]` shapes. Jack ruled
the two genuine forks via explicit questions at plan approval; the remaining shapes were approved
with the plan. Floor-verified the same day (structural walker `tests\verify_cli_harness.py`,
36 assertions; both prior walkers re-run clean; `longmem` pristine via the postgres MCP — **the
floor-verifier's `mcp__postgres__*` tools worked this dispatch**, resolving the 2026-07-14 flag for
this dispatch).

1. **Action-vocabulary source = per-call field → `agents.config` fallback (ruled).** A per-call
   `action_vocabulary` on `DialogueTurnRequest` wins when supplied; else
   `agents.config["action_vocabulary"]`; when neither exists, every emitted directive is dropped
   (`directive_dropped`, reason `"no vocabulary configured"`) and the turn succeeds. **No hardcoded
   default vocabulary** (nothing integrator-configurable is hardcoded). Vocabulary shape: a JSON
   array of directive `type` strings; `params` rides as a free object, unvalidated (architecture §9:
   "free type + params"). **Rejected:** config-only (no per-call variation without a config write)
   and per-call-required (boilerplate in every caller; a missing field becomes a hard error).

2. **Per-turn cost units = tokens always; USD only when priced via env (ruled).** Cost fields carry
   token counts unconditionally. USD populates only when the optional `LONGMEM_PRICE_*` env vars are
   set (USD per Mtok: `DIALOGUE_IN/OUT`, `WRITE_IN/OUT`, `ESCALATION_IN/OUT`, `EMBEDDING`); otherwise
   USD fields are null and the load-driver table reads "(unpriced)". **No model pricing is ever
   hardcoded.** **Rejected:** hardcoded price defaults (volatile vendor data in code; pricing is not
   per-agent config) and tokens-only (loses the demo's per-100-turn dollar figure).

Approved-with-plan shapes, as built:

- **Env var** — `LONGMEM_MODEL_DIALOGUE`, alongside the four existing roles in `app\config.py`;
  required in real mode; `Settings.model_dialogue`.
- **Structured output** — JSON-in-text per the write/escalation precedent: ONLY
  `{"prose": str, "directive": {"type": str, "params": object} | null, "reputation_delta": float}`.
  Parse policy: prose is required — no parseable prose → `MalformedOutputError` (token spend still
  accounted) → the seam serves the fallback line, `degraded = true`. Below prose the parse is
  field-wise (the ladder's salvage row): a malformed directive drops with `directive_dropped` +
  reason; a missing/non-numeric delta zeroes with `reputation_delta_source = "zeroed"`. Vocabulary
  validation of a well-formed directive happens at the seam, not the provider.
- **Reputation apply** — one atomic SQL statement (`app\db.py apply_reputation_delta`):
  `reputation = GREATEST(min, LEAST(max, COALESCE(reputation, neutral) + sensitivity × delta))`
  with `FOR UPDATE` old-value capture, `RETURNING (prev, after)` — the clamp lives in SQL so the
  scalar can never leave the scale even under concurrent turns. New `SERVICE_DEFAULTS` keys
  (per-agent overridable, the `agent_knob` pattern): `reputation_scale_min = -1.0`,
  `reputation_scale_max = 1.0`, `reputation_neutral = 0.0`, `reputation_sensitivity_default = 1.0`;
  the `agents.reputation_sensitivity` column wins over the knob when non-NULL. The result carries
  `reputation_delta_source` (`model | override | zeroed`) so override-wins and the degradation paths
  are structurally assertable.
- **Prompt assembly** — labeled blocks in spec order: `[identity]` (seed prose; omitted when NULL)
  → `[reputation]` (frozen snapshot + scale bounds) → `[memories]` (rank order, one line per item,
  memory_id carried) → `[output]` (the JSON contract + the turn's vocabulary; a no-vocabulary turn
  instructs `directive: null`). User message = the raw utterance. Identical inputs assemble
  byte-identical prompts; exposed as `assemble_system_prompt` so the walker asserts block order and
  byte-stability without a model call.
- **Never-blank fallback** — `DIALOGUE_FALLBACK_LINE = "..."` (a neutral beat), module constant in
  `app\dialogue.py`, overridable per agent via `agents.config["dialogue_fallback_line"]` (the
  `TYPOLOGY_FALLBACK` precedent).
- **Snapshot plumbing** — `reputation_snapshot` is a **required request field**, not a session
  handle: scene state lives in the caller (`app\session.py` freezes it; refreshes only at
  `scene()`), making "frozen within a scene" a seam-contract property the walker asserts directly.
- **CLI surface** — `python -m app.cli --agent <uuid> [--debug]` (`app\cli.py`, written to read as
  documentation). Meta-commands: `:observe`, `:scene [type]`, `:pin`/`:unpin <memory_id>`,
  `:as-of <iso8601|clear>`, `:debug [on|off]`, `:help`, `:quit`; anything else is an utterance.
  Debug rendering is a pure function (`render_debug`) over the payload so the suite can assert it.
- **Load driver** — `python -m app.load_driver --sessions N --turns M [--script p.json] [--seed S]
  [--agent <uuid>] [--database-uri <uri>] [--json out.json]` (`app\load_driver.py`), reusing
  `SessionRunner`. Script = JSON list of sessions, each a list of
  `{"kind": "observe" | "utterance" | "scene", ...}` events; omitted, a seeded deterministic
  generator supplies the mix (the generator passes its own vocabulary — callers own vocabulary).
  Emits latency p50/p95 (retrieval SQL, query embed, first token, dialogue total, turn total — no
  gate term) + the itemized per-100-turn token/USD table. Without `--agent` it creates a driver
  agent in the target DB.
- **Wire models** — Pydantic in `app\schemas.py` (`DialogueTurnRequest` / `ActionDirective` /
  `DialogueTurnResult` / `DialogueTurnInstrumentation`, the latter nesting
  `RetrievalInstrumentation`), mirroring the write/read payloads for the eventual Unity route.

**Build-surfaced interpretation (noted, not separately asked):** a client
`reputation_delta_override`, being client-authoritative and independent of the model call, **still
applies on the degraded (never-blank) path** — the ladder's "zero reputation delta" describes the
no-override default. Flagged to Jack in the build report. *(Confirmed by Jack 2026-07-16 — see the
audit-rulings entry below.)*

**Environment learnings:** (1) Windows decodes piped stdin with the ANSI codepage, so a PowerShell
here-string pipe delivers its UTF-8 BOM as mojibake — the REPL reconfigures non-tty stdin to
`utf-8-sig` (interactive consoles untouched). (2) `Providers.dialogue` carries a
`FakeDialogueProvider` default so pre-harness `Providers(...)` constructions (the write/read
walkers) stand unchanged. (3) `RealDialogueProvider` streams (the anthropic SDK `messages.stream`)
so first-token latency is measurable; the fake reports 0.0.

## Full-project audit rulings — 2026-07-16

A three-lane audit (doc-auditor full-tree sweep + code-vs-rulings review + operational checks) ran
the day after the CLI-harness build. Code and operations came back clean; the doc sweep found six
findings, all in the 2026-07-15 wrap-up prose. Jack ruled:

1. **Mechanical doc fixes applied (five findings).** The missed reconstruction renumber ref in
   `read-path.md` §Serving boundary ("Item 3" → "Item 1"); the `write-path.md` scene-boundary
   consumer note annotated with the 2026-07-15 landing (caller-side in the session-runner; the
   handler itself still writes nothing); the settle-shape count correction annotated onto the
   2026-07-15 entry above (the register's annotation convention — no ruling was rewritten); the
   CLAUDE.md invariant carve-out rewording ("the two runtime scalars" — `memories.pinned` is a
   memory-row flag, not an agent-row scalar); and the status.md known-nit sentence corrected to
   name all four stale-comment files.

2. **Override-on-degraded-path CONFIRMED.** The 2026-07-15 build-surfaced interpretation stands as
   built: a client `reputation_delta_override` is client-authoritative and applies even when the
   dialogue call fails (the never-blank path); the degradation ladder's "zero reputation delta"
   describes the no-override default. The flag is closed; no code change.

3. **Stale queue-number code comments fixed, floors re-verified.** The four comments citing
   reconstruction as "item 3" (`app\api.py`, `app\decay.py`, `app\retrieval.py`, `app\schemas.py`)
   were corrected to item 1 — comment-only changes to floor-verified files, so all three structural
   walkers were re-run on fresh scratch databases: 35/35, 34/34, 36/36, `db\migrate.py` no-arg
   still a clean no-op, scratch dropped.

Audit observations recorded without a ruling (carry as-is): `httpx` is imported directly by two
walkers but rides transitively (unpinned in `requirements.txt`); `max_tokens=1024` is hardcoded in
the three real providers (a write-path-era pattern — arguably provider implementation detail, not
integrator config); the suite-gate Stop hook stays dormant by design until `test_*.py` files land
with the pytest suite (immediate-queue item 4).

## Reconstruction spec scope rulings — 2026-07-17

Authoring `reconstruction.md` (the reconstruction v1 build target — immediate-queue item 1,
pre-demo since the 2026-07-14 re-slating; consolidates architecture §7 + §4.2/§4.3/§6 over the
frozen migration-01 schema, attaching to the read path's reserved serving stage) required three
scope rulings. Jack ruled via explicit questions:

1. **Reconstructor input = the prior head is included.** The reconstruction call sees the full
   gist spans (fixed constraint, verbatim from `observation_text`) + the time-thinned original
   detail slice + **the current live head as "how you currently tell it,"** conditioned on the
   rendered identity document. Rationale: retellings compound (the Talk-of-the-Town
   repetition-breeds-commitment precedent that motivated write-back; the Bartlett drift dynamic),
   and the drift budget gets real work — without the prior telling in the prompt, candidates stay
   near the anchor and the refuse-write threshold rarely binds. **Rejected:** original-only (the
   literal §7 reading — each reconstruction independent of the last, tellings recorded but never
   compounding) and prior-head-as-the-detail-source (gist/detail offsets exist only for
   `observation_text`; reconstructed text has no span structure to thin against §4.2's
   definition).

2. **Pre-demo drift driver = a decay band composed into the cache key.** Spec-surfaced tension:
   the identity document is seed-prose-only pre-demo, so `identity_version` is static and the
   ruled `(memory_id × identity_version)` cache would reconstruct each memory exactly **once** —
   the 60-day drift plot beat would be a single step, then flat until reflection ships
   post-August. Ruled: the cache key's version component **composes `identity_version` with a
   quantized thinning band** (the decayed detail strength, bucketed by an integrator quantum knob)
   — no schema change, the column is text. Deeper decay crosses a band edge → new key →
   re-reconstruction on thinner detail → a progressive drift trajectory under a static identity.
   The band is **frozen per scene** (caller-frozen scene state, with theta and the thinning level
   computed at the same scene basis) so within-scene byte-identity holds by construction, and the
   band **both keys the cache and sets the thinning level** so same-key ⇒ byte-identical text
   holds across scenes. Consequence: Set C's "stable identity ⇒ cache hit" refines to "stable
   identity **+ same band** ⇒ cache hit" (`test-suite.md` updated). **Rejected:**
   accept-single-step (faithful to the key as written, but the demo's drift beat loses its
   trajectory) and retell-per-scene (evict/bypass at scene edges — contradicts Set C's
   stable-identity⇒hit as written and multiplies reconstruction call volume).

3. **Identity-document plumbing = hybrid, reputation-style.** The scene-boundary handler
   recompiles **server-side** (render seed prose verbatim → content hash → upsert
   `identity_documents`) and **returns `identity_version`** in its response; the caller freezes it
   as scene state and passes it on each read request — exactly the ruled `reputation_snapshot`
   contract, making "frozen within a scene" a seam-contract property. Lazy bootstrap when no
   boundary has fired (a bare read ensures a current document and flags it); a request naming an
   unknown version is a loud contract error. This is the scene-boundary handler's **first real
   server-side consumer** (the 2026-07-14 slating's identity-recompile landing). **Rejected:**
   fully server-side (retrieval reads the latest document row per call — the effective version
   can shift mid-scene, making stability an implementation accident) and fully caller-side (every
   future client, Unity included, would reimplement rendering + hashing, and the server would no
   longer own the version its cache is keyed on).

The spec restates the settled mechanics by pointer (batched pre-warm serving,
block-with-signal deferred to the gate, the eviction invariant, the derivable drift anchor +
re-anchoring rules, `LONGMEM_MODEL_RECONSTRUCTION` behind the provider triad) and adds two derived
design lines: **serve only persisted text** (a model response that failed to persist is never
served — unpersisted text breaks within-scene stability on the next read) and **the dialogue-init
route becomes a writing endpoint** (write-back on read is §7's design; read-path v1's read-only
SQL was a scope fact of verbatim-only serving, not a principle). Remaining physical shapes are
tagged `[SETTLE-AT-BUILD]` (theta knob, band quantum + key composition, thinning function, prompt
+ batched output schema, retry policy, drift metric + threshold default, write-back `valid_at`,
refusal caching, scene-state request fields, scene-boundary response shape, hash algorithm /
NULL-seed / unknown-version shapes, wire-model + instrumentation deltas, walker shape). These are
ruled at reconstruction's build, not now. Docs only — no code, no floors changed.

## Reconstruction build rulings — 2026-07-17

Reconstruction v1 built and floor-verifier-passed the same day (structural walker
`tests\verify_reconstruction.py`, 41 assertions; all three prior walkers re-run clean on fresh
scratch — 35/35, 34/34, 36/36; `longmem` confirmed pristine via the postgres MCP, whose tools
worked this dispatch). Jack ruled the two genuine forks via explicit questions at plan approval;
the spec's remaining settle-shapes were approved with the plan.

1. **Fake-mode drift = locality-sensitive fake embedding (ruled, explicit question).**
   `FakeEmbeddingProvider` was rewritten from shake_256 hash vectors to **lowercased character
   trigrams hashed into the 1536 buckets, L2-normalized** — still deterministic, offline, keyless,
   but similar texts now get similar vectors, so fake-mode retrieval relevance and reconstruction
   drift distances are meaningful. Build-surfaced fork: the hash fake made ANY two texts nearly
   orthogonal (~1.0 cosine distance), so every fake-mode reconstruction would have been refused at
   any sane threshold — offline dev, the load driver, and the walker happy path would never
   exercise write-back at default knobs. **Rejected:** keep-orthogonal (drift observable only in
   real mode) and a provider-mode-conditional drift check (violates the cli-harness principle that
   the service is identical under either provider). Empirically: an echo-style retelling lands
   ~0.04 from its anchor; unrelated text ~1.0.
2. **`drift_budget_threshold` default = 0.35 (ruled, explicit question).** Cosine distance,
   per-agent overridable (`agents.config`, the `agent_knob` pattern; migration 01 slotted the
   drift threshold there from day one). Paraphrase-level retellings (~0.05–0.25 on real
   embeddings) pass; candidates that left the event's semantic neighborhood refuse. **Rejected:**
   0.25 (crystallizes early — flattens the 60-day beat) and 0.5 (the budget becomes a backstop
   only).

Approved-with-plan shapes, as built: knobs `reconstruction_theta` **0.5** /
`reconstruction_band_quantum` **0.25** (band = `floor((1−strength)/quantum)` capped at the last
band; thinning level = the band's midpoint strength; composed key `{identity_version}|b{index}`
in the cache's existing text column); deterministic dependency-free thinning
(sentence-split on `(?<=[.!?])\s+`, per-segment prefix retention `ceil(level × n)`, min 1 — no
spaCy on the read path); batched JSON-in-text call (system = optional `[identity]` block +
`[task]`; user = a JSON list of `{memory_id, gist, detail, current_telling}` sorted by memory_id;
response = ONLY a JSON object memory_id → retelling; per-item salvage; pure
`assemble_reconstruction_prompt`); single attempt, fail-quiet; drift check embeds candidate +
anchor **at check time** in one batched embed call (chain rows have no embedding column;
`memories.embedding` embeds the observation, not the render); write-back supersedes and inserts
**at the scene basis** (prior head `invalid_at` = new head `valid_at` = basis — a coherent chain
timeline under `as_of` time travel, and the precedent the authorial endpoint inherits); refusal
caches the served prior text under the current key; scene-state request fields
`identity_version` + `scene_started_at` (both optional; absent → basis falls back to
`as_of_effective` and the identity document lazy-bootstraps, flagged); unknown version →
`UnknownIdentityVersionError` → **422** at the route; `SceneResult` gains `identity_version` +
`identity_document_new` (additive defaults); sha256 full hex; NULL seed renders the empty string
(hashed) with the identity block omitted; `RealReconstructionProvider` max_tokens
`min(1024 × batch, 8192)` (batch-safe variant of the provider-internal 1024 pattern);
`read_mode` literal widens to `verbatim | reconstructed` (`reconstruction_pending` stays
unadopted); instrumentation deltas all defaulted (`reconstruction_ms` / input / output /
embed tokens, `cache_hits/misses`, `write_backs`, `drift_refusals`,
`identity_version_effective`, `identity_bootstrapped`); load-driver aggregates gain the
reconstruction latency + cost rows (drift-check embeds ride the embedding price); walker
`tests\verify_reconstruction.py` on the scratch pattern.

**Build-surfaced shapes (flagged for Jack's confirmation, built as follows):** *[All confirmed
as built/written 2026-07-17 — see "Reconstruction flagged-shapes confirmations" below.]*

- **Prior walkers pin `reconstruction_theta = 0.0` in their fixture agent configs** (one config
  key + comment each; assertion bodies untouched — verified by the floor-verifier against git).
  Their fixtures age past the default theta, so without the pin the swap would change what they
  serve; theta = 0 knob-disables the stage per agent, so they still assert the v1 serving
  contract byte-for-byte — which doubles as proof the swap is transparent when disabled. The
  swapped behavior is the new walker's floor.
- **Blind-check refusals are not cached:** a drift-check **embedding failure** refuses the
  write-back (fail-closed) but does NOT cache the served prior text — a transient embedding
  outage never permanently pins a key. True over-threshold refusals do cache, as ruled.
- **Cache-hit `detail_id` corner (documented):** after backwards time travel a cached telling can
  predate the current live head; the cache row is still served (same key ⇒ byte-identical text),
  `detail_id` identifies the live chain head, `content` the key's telling.
- **Pin-after-reconstruction read_mode (floor-verifier observation, spec-compliant):** a memory
  reconstructed in an earlier scene and pinned afterward serves its `reconstruction`-cause head
  as `read_mode = "verbatim"` — the spec's "pinned → verbatim, always" wins as written; noted as
  the one spot where read-mode names the pin rule rather than the served row's cause.

**Environment deviation found during verification (operational, not a ruling — needs Jack):**
`.env`'s `DATABASE_URI` now names a database `longmem_sandbox` that does not exist on the server
(the server has `longmem`, intact and pristine, and `postgres` only) — an operator-side edit some
time after the 2026-07-16 audit. Consequence: `python db\migrate.py` **no-arg** fails to connect;
the schema-frozen criterion was verified the equivalent way (`--database-uri` with the path
swapped to `/longmem` → "Up to date, 0 pending"). `.env` was not modified; whether to point it
back at `longmem` or create the sandbox DB is Jack's call. *[Resolved same day: Jack pointed the
URI back at `longmem`; no-arg `db\migrate.py` re-verified as a clean no-op — see the status.md
wrap-up entry.]*

## Reconstruction flagged-shapes confirmations — 2026-07-17

A dedicated confirmation session: Jack walked the three open reconstruction flags (the two
build-surfaced shapes plus the floor-verifier observation from the 2026-07-17 build-rulings
entry) and ruled on each. All three **confirmed as built/written — no code, no spec, no walker
changes.** The escalation hard-stop failure-path re-rule is now the sole open question.

1. **Prior-walker theta pin — CONFIRMED as built.** `tests\verify_read_path.py` and
   `tests\verify_cli_harness.py` keep `reconstruction_theta = 0.0` in their fixture agent
   configs. Ruled after a correction of understanding, recorded because the register keeps the
   why: Jack initially read the pin as "reconstruction is dormant in v1" and provisionally ruled
   rewrite-the-walkers + activate-the-knob; on review, reconstruction is **already
   production-active** (default `reconstruction_theta = 0.5` in `app\config.py`, per-agent
   overridable; the 0.0 pin exists only in the two older walkers' fixture NPCs), proven live at
   the 2026-07-17 verification (REPL drift beat with a real write-back and cache hit), and
   reconstruction owns its own dedicated 41-assertion walker. With that corrected, confirmed as
   built: staged-verification layer isolation — each walker guards one layer so a failure has a
   single cause, and the pinned pair doubles as proof the serving swap is transparent when
   knob-disabled. **Rejected:** rewriting the old walkers to run under default theta (duplicates
   `tests\verify_reconstruction.py`'s coverage, touches floor-verified assertion bodies, re-opens
   the read-path and CLI-harness floors, and blurs failure attribution).
2. **Blind-check refusals not cached — CONFIRMED as built.** A drift-check **embedding failure**
   (a blind check — no distance computable) refuses the write-back fail-closed but does NOT
   cache the served prior text (`app\reconstruction.py`), so a transient embedding outage never
   permanently pins a key — the next read retries. True over-threshold refusals cache, as ruled
   at build. **Rejected:** uniform refusal caching (an outage would pin the served text under
   that key until the identity version or decay band moved).
3. **Pin-after-reconstruction read_mode — CONFIRMED, keep as written.** Ruled after a requested
   review of pin mechanics (pins are integrator-designated only, via the observe event's flag or
   `PUT /v1/memories/{id}/pin`; §8: pin freezes the *current* head — restoration is a correction
   verb, not pin). A memory reconstructed in an earlier scene and pinned afterward serves its
   `reconstruction`-cause head as `read_mode = "verbatim"` — §6's "pinned → verbatim, always"
   holds as written: "verbatim" is the serving-stage claim (served exactly as stored, stage not
   applied, frozen from here on), and `pinned` rides alongside `read_mode` in every payload, so
   consumers retain ground truth. Floor-verifier observation closed; no spec amendment.
   **Rejected:** relabeling pinned drifted heads via `_head_mode` (a §6 amendment plus a
   serving-stage change re-opening the reconstruction floor, for a label carrying no information
   the `pinned` flag doesn't already carry).
