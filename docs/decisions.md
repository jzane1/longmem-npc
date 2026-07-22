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
(especially the action directive) are written to survive the migration. *(Superseded in part
2026-07-21 by the "Latency slate + split-brain pull-forward rulings" entry: the split-brain
lands PRE-demo, the two calls run CONCURRENTLY, and the dialogue call sees only PAST actions
as world facts — never the current turn's. The contract-survival line stands, and held.)*

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
embedded via the same 1536 model. *(2026-07-19 gate-spec freeze: entities' home moves to the
fact chain at migration 003, the GIN with it — `mid-dialogue-gate.md`.)*

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
   *(2026-07-19 gate-spec freeze ruling: migration 003 moves the entities GIN to the live fact
   heads — the lexical fetch reads fact-head entities; `mid-dialogue-gate.md`.)*
4. **Within-scene text-stability invariant.** Absent a diegetic event on that memory, repeated reads
   within one scene return byte-identical text. Constrains any future async fallback. *(Amended
   2026-07-17: authorial correction added as the second sanctioned text-change cause — see the
   "Authorial-correction spec scope rulings" entry.)*
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
   path; vector backfill is future work. *(2026-07-19 gate-spec freeze: that reachability moves
   to the fact-head partial GIN at migration 003 — `mid-dialogue-gate.md`.)*
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

## Scope-limiter reframing — 2026-07-17

Ruled by Jack after he flagged a standing bias in brainstorm/spec sessions: rules written as
verification discipline had hardened into design pressure — correct-but-larger options arrived
pre-labeled "blocked", "deferred", or "would re-open a floor". Surfaced live in the
authorial-correction spec session (paused mid-forks; its four scope forks are owed a fair
re-presentation under this ruling). A full sweep of every instruction surface (CLAUDE.md,
docs\, tests\CLAUDE.md, .claude\ commands and agents) found four limiter families. Four standing
changes, applied to the living rule surfaces (CLAUDE.md, status.md, architecture.md §2/§10,
.claude\commands\build-task.md); built specs, prior register entries, and session logs stand as
history:

1. **The schema freeze is retired as a standing rule.** The schema evolves by numbered
   migration: when the correct design needs a column, table, or index, the target adds
   migration `NNN` via the `db\migrate.py` ledger (built for exactly this since 2026-07-13),
   updates the schema docs, and the floor re-verifies (migrate idempotency + walkers). "No new
   migration" may appear in a spec only as a per-target scope fact Jack explicitly ruled — never
   as an inherited default. (The freeze was never tooling; it was a per-target scope fact in
   `write-path.md` that three later specs inherited as law.) What stays locked on its own
   grounds: the 1536 embedding dimension and the non-destructive invariants. The freeze's
   recorded casualties — the idempotency/dedup column, the scene-boundary schema home, the
   reputation-history schema objection, VAD dominance in jsonb, the location-description
   column — become *eligible* for re-opening; each is its own future ruling when a target
   touches it, and none is re-opened by this entry.
2. **Sequencing, not veto.** `status.md`'s "Post-August ledger" is renamed **"Sequenced-later
   ledger (pull-forward eligible)"** with the standing rule: any sequenced item may be pulled
   into the immediate queue by a dated ruling when a current target shows it is architecturally
   load-bearing — the 2026-07-14 reconstruction re-slating is the template. Sequencing orders
   work; it never rules an option out of a design discussion. The "revisit only if demo latency
   demands" phrasing (prompt caching) is struck for "revisit when a target needs it or demo
   latency demands" — the old wording forbade revisiting for correctness reasons. The dated
   deferral rulings themselves stand; this entry changes what they mean going forward.
3. **Floors are re-openable.** Re-running walkers + the floor-verifier is the normal cost of a
   design improvement, never an argument against one; options must state re-verification as the
   step it is, not as a design cost. (Staged verification itself is untouched — it is what makes
   this rule safe.)
4. **Reports carry the correct option.** The stop-and-report contract (CLAUDE.md working
   discipline; `/build-task` Phase 2) now requires the architecturally correct option to appear
   in every report even when it exceeds the task's scope, with its real cost stated — "bigger
   than this task" is a sequencing note, never a rejection reason.

Kept deliberately: "the August deadline never drives a decision" (+ `status.md`'s deadline
framing), staged verification and the verifier/auditor agents, the invariants block, and
`tests\CLAUDE.md`'s structural-only discipline — the reframe makes these enforceable rather
than replacing them.

## Authorial-correction spec scope rulings — 2026-07-17

Authoring `authorial-correction.md` (the authorial-correction endpoint build target —
immediate-queue item 1, slated pre-demo by the 2026-07-14 re-slating) required four scope
rulings. **The first spec session run under the same-day scope-limiter reframing:** the forks
were presented twice — the pre-reframing presentation was paused by Jack (it became the trigger
for that ruling); the re-presentation priced the larger options fairly, and one recommendation
flipped as a direct result.

1. **Scope = chain content now; fact-level correction slated as its own target (explicit
   questions, two rulings).** This target writes the corrected telling head only. The honest
   gap it leaves — retrieval still ranks a corrected memory by the original observation's
   embedding, and gist spans still index the original text — is closed by a slated
   **fact-level correction target** (versioned memories-row facts + corrected embedding so
   retrieval follows the fix; migration-002-class design with its own spec pass). Slating
   position ruled by a second explicit question: **immediate queue, item 2, ahead of the
   gate** — closing the operator's wrong-data story outranks demo-queue focus. **Rejected:**
   full fact correction inside this target (the fact-versioning mechanism deserves its own
   design pass, not a rider); chain-only with no slated follow-up (leaves the
   retrieval-on-wrong-semantics gap unowned).
2. **The reconstructor's fixed constraint follows the drift anchor (the flipped
   recommendation).** On a chain whose derivable anchor is an `authorial_correction` head, the
   corrected head — not the stale observation gist — is the fixed constraint: one notion of
   ground truth per chain, with constraint and drift anchor deriving from the same
   `write_cause` rule. Original-anchored chains are unchanged; the `update_with_resentment`
   mapping is decided with the dissonance path. Deliberately re-opens the reconstruction floor
   at build (anchor-cause-aware `assemble_reconstruction_prompt` + walker updates +
   re-verification) — priced as the step it is. **Rejected:** drift-budget-defends
   (reconstruction untouched): the constraint and the anchor would disagree about ground truth,
   and every gist-contradicting reconstruction would burn a model call just to be refused. *(The
   pre-reframing recommendation had been drift-budget-defends, leaning on "re-opens the floor"
   as a deterrent — recorded here as the reframing entry intends.)*
3. **Surface = memory-scoped operator verb** (the `set_pin` pattern; suggested
   `POST /v1/memories/{memory_id}/correction`, exact shape `[SETTLE-AT-BUILD]`), plus a REPL
   `:correct` meta-command so the correction-override demo beat is drivable pre-Unity.
   `/v1/events/*` stays diegetic-only. **Rejected:** an `/v1/events/correction` event — it
   blurs operator tooling into the in-world namespace, and the future diegetic-correction event
   would sit beside a differently-shaped sibling.
4. **Immediate mid-scene effect + invariant amendment.** Eviction + supersession serve the
   corrected chain on the very next read, mid-scene included. The within-scene stability
   invariant's wording gains authorial correction as the **second sanctioned text-change
   cause** (amended in CLAUDE.md, architecture §7, and `test-suite.md` Set C). **Rejected:**
   defer-to-scene-boundary — fairly priced post-reframing (a migration could house the pending
   state) and rejected on the merits: it keeps wrong data serving longer to protect the
   character from a change the operator explicitly chose.

Consequences propagated: `authorial-correction.md` written (design lines: no model calls —
operator text byte-verbatim *[superseded in part 2026-07-18: at the fact-level build the verb
gains one embed call — see the fact-level entry below]*; no `corrections` row — diegetic-only
by CHECK; one supersede-guarded transaction with cache eviction; fail-loud operator surface;
remaining physical shapes `[SETTLE-AT-BUILD]`); the invariant wording amended in CLAUDE.md + architecture
§7 + `test-suite.md` Set C; architecture §7's reconstructor-input line and §8's authorial
bullet annotated; Set A's authorial pair gains the constraint-follows-anchor and
mid-scene-immediacy assertions; the immediate queue renumbered (fact correction → 2, gate → 3,
suite → 4, Unity → 5, pre-ship gates → 6) with stale gate/suite refs updated in `read-path.md`,
`cli-harness.md`, `reconstruction.md`. Docs only — no code, no floors changed.

## Authorial-correction build rulings — 2026-07-18

Authorial-correction v1 built and floor-verifier-passed the same day (structural walker
`tests\verify_authorial_correction.py`, 31 assertions; all four prior walkers re-run clean on
fresh scratch — 42/42 with the reconstruction walker grown by one corrected-item assertion
(addition only), 36/36, 34/34, 35/35; `longmem` confirmed pristine via the postgres MCP). Jack
ruled one criterion via an explicit question at a mid-build stop-and-report; the spec's
remaining settle-shapes were approved with the plan.

1. **Done-when "time travel coherent" re-ruled to stored bi-temporal coherence (explicit
   question).** The spec's wording — "`as_of` before t_c serves the prior telling" —
   over-claimed: the candidate SQL joins the live head unconditionally
   (`d.invalid_at IS NULL`), and `as_of` is an **age-computation override** by the 2026-07-14
   read-path ruling; invalidation excluding rows in SQL is what Set B's decay-vs-invalidation
   separation asserts through. Ruled: the walker asserts the **stored** guarantee — chain
   stamps coherent around t_c (superseded `invalid_at` = corrected `valid_at` = t_c) and a
   windowed SQL query re-derives which telling was live at any instant, with no gap or overlap.
   **Rejected (presented fairly priced, not adopted, not slated):** as_of-windowed chain
   serving — the fuller bi-temporal read would rewrite the ruled `as_of` semantics, re-open the
   read-path floor, and require re-thinking the reconstruction cache for superseded heads; no
   ruling or demo beat asks for it (drift and correction-override both want current-state
   serving). If ever wanted, it is its own spec-first target.

Approved-with-plan shapes, as built: route `POST /v1/memories/{memory_id}/correction` (POST —
each call mints a chain row); `CorrectionRequest { content min_length 1, client_timestamp
required tz-aware (the ObserveEvent naming) → t_c, expected_detail_id optional }` /
`CorrectionResult { memory_id, detail_id, superseded_detail_id, evicted_cache_rows, total_ms }`
(the PinResult naming; no token fields — no model calls *[superseded in part 2026-07-18: the
fact-level build widens `CorrectionResult` and adds the one embed call — see the fact-level
entry below]*); whitespace-only content invalid
(pydantic `min_length` + a stripped check in the seam → 422); **concurrency = the spec's 409
suggestion refined to an opt-in compare-and-swap** — the supersede targets the live head by
predicate (race-safe under row locking; the one-live-head index the backstop), and a supplied
`expected_detail_id` that no longer names the live head → `CorrectionConflictError` → **409**
with the transaction rolled back (never a silent correction of a telling the operator did not
see), while an omitted CAS (the REPL default) corrects the current live head; corrected-chain
prompt shape per the pure `build_reconstruction_item` (anchor cause `authorial_correction` →
the corrected anchor text in the constraint slot, empty detail — nothing observation-derived
re-injected — `current_telling` kept, `_SYSTEM_TASK` and the JSON shape unchanged;
original-anchored chains byte-identical to the prior stage; `ReconstructionSource` gains
`anchor_cause`); CLI `:correct <memory_id> <text…>` with t_c = the session's effective time
(`as_of` under time travel); error mapping 404 / 409 / 422 / 5xx raw (fail-loud); walker
`tests\verify_authorial_correction.py` on the scratch pattern.

Environment learning (recorded for the next session): the repo `.env` now runs
`LONGMEM_PROVIDER_MODE=real`, so piped-REPL smokes must set
`$env:LONGMEM_PROVIDER_MODE = "fake"` alongside the scratch `DATABASE_URI` override.

## Fact-level correction spec scope rulings — 2026-07-18

Authoring `fact-level-correction.md` (the fact-level correction target — immediate-queue item 1,
slated by fork 1 of the 2026-07-17 authorial-correction rulings) required four scope rulings.
Presented twice at Jack's request: the technical presentation, then a plain-prose
re-introduction of all four (mechanism, issue, options); ruled on the re-presentation, each on
the recommended option. Premise corrections were surfaced during pricing and verified in code
before presenting: `entities` is **write-only today** (the read-request slot is RESERVED-inert;
its first consumer is the gate's GIN path, queue item 2); **gist re-derivation on corrected
chains would have zero consumers** (the corrected-anchor prompt branch ignores
`observation_text` and spans); **purge is a docs-only contract** (no handler exists). The
stored embedding's sole consumer is the `fetch_vector_candidates` probe — the direct target of
"retrieval follows the fix."

1. **Fact scope = embedding only.** The corrected text is re-embedded (one embedding-provider
   call); importance, typology, decay class, entities, and affect stand as write-time facts
   about the *event* — consistent with the deliberately-disregarded 2026-07-12 staleness
   tension. Honest deferral recorded: a fact-corrected memory carries its original entities
   until an additive fact-chain column rides with the gate target. *(Closed 2026-07-19 —
   migration 003 specced at the gate target, and the correction verb re-derives entities;
   `mid-dialogue-gate.md`.)* **Rejected:** +mechanical
   NLP pass (entities/affect feed nothing readable today; gist re-derivation consumer-less;
   spaCy latency on the operator verb); +Haiku re-score (a second model call; importance moves
   to the fact head, widening the candidate-SQL delta and re-opening read-path scoring
   assertions); operator per-field overrides (no model calls, but the same candidate-SQL
   widening for importance — re-openable later if operator authority over scalar facts is ever
   wanted).
2. **Version shape = a fact-version child table** (suggested `memory_fact_versions`; exact
   names `[SETTLE-AT-BUILD]`): chain rows under the stable `memory_id` — basis text, embedding,
   `write_cause`, bi-temporal stamps — with a one-live-head partial unique index and a partial
   HNSW; the `memory_details` precedent applied to the semantic basis, the non-destructive
   invariant untouched. Migration 002 creates + backfills one `original` row per existing
   memory. Read-path and write-path floors re-open at build — re-verification steps.
   **Rejected:** history table + in-place-updated live columns (candidate SQL and HNSW
   untouched, but "never UPDATE stored content in place" would narrow — an invariant rewording
   propagated through every rule doc, the weaker architecture); self-chaining the memories row
   (`memory_id` is simultaneously PK and the stable FK target of four tables and every wire
   payload — a new anchor ID for identical semantics).
3. **Surface = one combined verb.** `POST /v1/memories/{memory_id}/correction` becomes
   fact-following: the operator's corrected text is both the telling head (byte-verbatim, the
   v1 contract) and the embedded fact basis, one transaction, CAS and eviction inherited.
   Verified coupling drove this: a fact-only correction leaves an original-anchored chain whose
   reconstructor keeps re-injecting the corrected-away data from stale gist spans. **Rejected:**
   a separate fact verb (needs a second ground-truth rule keyed on fact-version state — two
   truths per chain, against the 2026-07-17 one-ground-truth-per-chain ruling — and re-opens
   the reconstruction floor); a scope field (inherits the same problem in facts-only mode,
   triples the behavior matrix).
4. **Embed failure = all-or-nothing, fail-loud.** Embed before the transaction opens (never
   hold a transaction across a network call — the reconstruction precedent); on provider
   failure nothing is written, loud 5xx-class error, operator retries. Honest price recorded:
   during an embedding outage, telling corrections are blocked too — v1 needed no model.
   **Rejected:** land-with-NULL-embedding (the memory vanishes from the vector probe — worse
   than stale — and needs a nonexistent retry verb); land-with-stale-embedding (retrieval keeps
   following the old semantics, the target's own problem statement).

Consequences propagated: `fact-level-correction.md` written (design lines: one model call
stated honestly — v1's "no model calls" purity superseded, not silently dropped; the existing
embedding role, no new model role or env var; the fact chain's `write_cause` vocabulary reuses
`original | authorial_correction`; **migration 002 is a fact of the target — the first spec for
which that is true**; remaining physical shapes `[SETTLE-AT-BUILD]`). CLAUDE.md's
non-destructive parenthetical grows the fact chain; architecture gains §4.4 + the §6 probe
marker + the §8 fact-following annotation + §12 purge prose ("its chains — telling and fact
versions"); `authorial-correction.md` annotated at five spots (fork 1 closed, no-model-calls
superseded-in-part, scope boundary, mechanism, instrumentation); `migration-01.md` 002 pointers
(embedding column, HNSW index, mechanics); `test-suite.md` Set A authorial pair grows the
fact-chain assertions + a new all-or-nothing degradation case. Docs only — no code, no floors
changed.

## Fact-level correction build rulings — 2026-07-18

Fact-level correction v1 built and floor-verifier-passed the same day as its spec (new
structural walker `tests\verify_fact_correction.py`, 32 assertions; all five prior walkers
re-run green on fresh scratch — 38/38 write (35 → 38), 36/36 read (34 → 36), 36/36 CLI harness
(untouched), 42/42 reconstruction (**untouched — the proof of the spec's no-reconstruction-delta
claim**; `app\retrieval.py` and `app\reconstruction.py` byte-identical to HEAD), 33/33 authorial
(31 → 33); `longmem` pristine via the postgres MCP; migration 002 applied to `longmem` with the
floor criterion now reading **"001 + 002 applied, 0 pending"**). Jack ruled two shapes via
explicit questions at plan approval; the remaining eight mechanical shapes were approved as
proposed.

1. **Dual-write vs freeze = FREEZE (explicit question, against the dual-write
   recommendation).** Observe no longer writes `memories.embedding` — the `original` fact head
   on `memory_fact_versions` is the sole vector home for post-002 rows. The recommendation had
   been dual-write (the 001 all-write-time-facts principle holding for every row); Jack chose
   one storage home, accepting the epoch split (pre-002 rows keep their column values — now
   also backfilled into the fact chain — post-002 rows carry NULL there forever). **Stated
   consequence, implemented with the ruling:** the queryable embed-degradation signal (ruled
   2026-07-13 as `memories.embedding IS NULL`) moves to the **live fact head**; the write-path
   walker's [14] signal assertion moved with it — the one non-additive walker change of this
   build, ruling-driven and recorded. Signal-home annotations propagated to architecture §2,
   `test-suite.md`, `write-path.md` §c, and the `app\schemas.py`/`app\ingest.py` docstrings.
2. **The old `memories_embedding_hnsw` index = DROPPED in 002 (explicit question, as
   recommended).** An index is derived structure, not stored content; after the probe moves it
   has zero readers. Reversal, if ever wanted, is one CREATE INDEX in a later migration.

Approved-with-plan shapes, as built: names `memory_fact_versions` / `fact_version_id` /
`basis_text` + index names per the spec sketch; `write_cause CHECK IN ('original',
'authorial_correction')` (column shape otherwise mirroring `memory_details`); **partial HNSW**
over live fact heads (`WHERE invalid_at IS NULL`, stated verbatim in the candidate SQL so the
planner matches); degraded-path `fetch_live_candidates` deliberately unjoined (no distance is
computed there; byte-identical to v1); backfill `INSERT…SELECT` with the `WHERE NOT EXISTS`
backstop before the indexes (the walker proves the guard by re-running the 002 file against a
legacy-shaped row); wire deltas `CorrectionResult += fact_version_id,
superseded_fact_version_id, embed_ms, embedding_tokens` and `IngestResult += fact_version_id`;
REPL `:correct` prints both head swaps + embed timing, and `CorrectionEmbedFailedError` prints
loudly (the hard-stop pattern); embed failure → **502** (the escalation-hard-stop route
precedent); the correction embeds **before** the transaction opens and a missing live fact head
inside it raises as a broken-store invariant (rollback, 5xx). A build-observed bonus recorded
by walker assertion: **correcting an embed-degraded memory re-embeds it** — the correction verb
is the sanctioned repair path for NULL-fact-embedding rows (closing the retry-verb gap the
rejected land-with-NULL option would have needed).

Verification also included a live piped REPL beat on scratch (fake mode): the `:correct` line
prints both head swaps, and the same chapel query's relevance moved 0.4686 → 0.5637 across the
correction — retrieval following the fix, visible in the debug view.

## Mid-dialogue gate spec scope rulings — 2026-07-19

Authoring `mid-dialogue-gate.md` (the mid-dialogue gate — immediate-queue item 1 since the
2026-07-18 fact-level build) required five scope rulings. Presentation mode, recorded per the
house convention: forks 1, 2, 4, and 5 were re-presented in plain prose at Jack's request
(fork 1 after distinguishing the loaded set from a per-turn top-k and detailing the
server-side option; fork 2 after a refresher on the two-chain split — retellings compound on
the telling chain while the fact chain is the ground-truth basis reconstructions never touch)
and ruled on the re-presentation, each on the recommended option; fork 3 was ruled on the
first presentation. **Fork 5's recommendation was reversed between presentations, recorded
honestly** (see below). Premises verified in code before presenting: the loaded set has **no
state home anywhere** (the session runner holds only scene-frozen scalars — no turn counter,
no last-retrieval, no history); retrieval fires **unconditionally on every turn**
(`app\dialogue.py`); `memories.entities` and its GIN index have **zero readers**; the
read-request `entities` slot is RESERVED-inert and is not the gate's input.

1. **Loaded-set home = caller-held scene state, reputation-style.** The session runner (Unity
   client in production) keeps loaded memory IDs as scene state — reset at scene boundaries,
   populated by the loader turn, appended on gate fetches — and passes them per request; the
   server fetches those rows by ID each turn (one keyed SQL on live fact heads) for the
   novelty basis, coverage check, and closed-gate serving. Absent fields ⇒ loader semantics ⇒
   v1 byte-parity. Third use of the ruled caller-freezes-scene-state contract (reputation
   snapshot 2026-07-15, `identity_version` 2026-07-17). **Rejected:** server-side scene state
   (a scene-state table invents a persistent scene object + a per-turn write + lifecycle
   questions in a no-DELETE store; an in-process cache breaks under the REPL-in-process +
   route-over-HTTP dual-caller topology and dies on restart); per-turn approximation (runs
   the probe to decide whether to run the probe; already-recalled entities re-fire on every
   mention; contradicts architecture §6).
2. **Migration 003 entities = FREEZE — the fact head is the sole entities home.** The 002
   embedding precedent applied to entities: `memory_fact_versions.entities` added; observe
   writes the fact head only; guarded backfill from `memories.entities` before the index;
   partial GIN over live fact heads; `memories_entities_gin` dropped; `memories.entities`
   frozen (the epoch split accepted, same as the embedding's). Decisive argument: the gate's
   coverage check and degraded fetch *read* entities — one home makes "corrections move
   entities" true everywhere they're read. **Sanctioned shape, explicitly:** the backfill is
   an UPDATE of a brand-new never-populated column on existing fact rows — schema-evolution
   backfill in the 002 spirit, not a content mutation. **Rejected:** dual-home (two homes
   drift; the gate would read the home corrections cannot move — the exact debt 003 closes).
3. **Correction entities = mechanical NLP pass + optional operator field.** The corrected
   fact head's entities mirror observe's merge exactly: spaCy NER over the corrected text +
   optional `CorrectionRequest.entities`, case-insensitive dedup; absent field ⇒ NER alone.
   Non-LLM. The fact-level fork-1 rejection of an NLP re-pass rested on "entities feed
   nothing readable today" — a premise this target ends; the price (the write path's NLP
   stack enters the correction path) restated and accepted. **Rejected:** NER-only (drops the
   client-supplied merge observe has); operator-field-only (fieldless corrections don't move
   entities); copy-forward-only (the deferral's stated purpose would defer again).
4. **Per-signal fire logs = instrumentation-only.** `signals_fired` rides the turn
   instrumentation (the write path's `escalated_by` precedent) + load-driver per-100-turn
   aggregates; the reserved novelty kill-switch decision reads run artifacts. Zero schema,
   zero per-turn DB writes; a persisted `gate_events` table stays pull-forward eligible if
   the kill-switch ruling later demands cross-session data. **Rejected:** persisted rows
   riding 003 (a write per gate evaluation — base rates need non-fire rows; purge-contract
   growth; more schema before any long-running real usage exists).
5. **Reconstructing signal = post-hoc response fields + a pre-serve callback.** The reply
   carries the pause info AND an optional in-process callback fires as a blocking mid-scene
   serve begins — the REPL prints `(reconstructing…)` during the wait; the queued Unity hook
   maps onto the same seam; no HTTP transport change. **Recommendation reversed at the
   plain-prose pass, recorded honestly:** fields-only had been recommended (it keeps
   `app\reconstruction.py` byte-untouched), but fields-only cannot show anything *during*
   the pause — it cannot deliver §7's "latency becomes characterization" intent, the
   signal's entire purpose. Price accepted: one defaulted parameter touches the serving
   path; the reconstruction floor re-opens at build and re-verifies — a step, not a cost.
   **Rejected:** fields-only (the during-the-wait effect is unreachable); SSE/streaming now
   (a new transport class before Unity, its only consumer, exists).

The **fruitless-retrieval damper** was deliberately not forked: its mechanism stays
`[SETTLE-AT-BUILD]` with a full suggested default in the spec, **flagged promotable** for a
ruling before the build if Jack wants it settled.

Consequences propagated: `mid-dialogue-gate.md` written (design lines: non-LLM with the one
embed reused as the probe — one embed per turn; the two identity structures kept distinct —
tripwire = live `identity_components`, coverage = post-003 fact-head entities via the keyed
fetch, degraded fetch = their partial GIN; the reserved read-request slots stay inert; loader
turn ungated with absent-fields
byte-parity; the loaded set append-only within a scene; caller-side reset — no fourth
scene-boundary server consumer; **migration 003 is a fact of the target — the second spec for
which that is true**; remaining physical shapes `[SETTLE-AT-BUILD]`). Architecture §6 specced
marker + ladder GIN-home annotation, §5 freeze annotation, §4.4 entities-now-follows
amendment note, §11 lands-with markers; audit ruling #3 GIN-home annotation + the 2026-07-18
fact-level fork-1 deferral-closure annotation (this register); `fact-level-correction.md`
closure annotations; `reconstruction.md` wire-shape-settled + no-gate-term annotations;
`write-path.md` entities-freeze + GIN-reachability annotations (+ this register's
context-stamps and write-path-ruling annotations); `read-path.md` + `cli-harness.md` specced
pointers; `authorial-correction.md`
`CorrectionRequest` optional-entities annotation; `migration-01.md` 003 pointers;
`test-suite.md` Set D + ladder-row pointer; CLAUDE.md deliberately unchanged (the
within-scene invariant needs no amendment — which memories surface was never under the
byte-identity guarantee). Docs only — no code, no floors changed.

## Mid-dialogue gate build rulings — 2026-07-19

Mid-dialogue gate v1 built and floor-verifier-passed the same day as its spec (new structural
walker `tests\verify_gate.py`, **51 assertions** — grown past the plan's ~34 estimate by
addition; all seven prior walkers re-run green, each on fresh scratch — 40/40 write (38 → 40,
the additive entities-freeze pair), 36/36 read (**byte-untouched — the loader-parity proof**),
36/36 CLI harness (fixture `gate_enabled` pin + one ok-label edit, assertion bodies untouched),
42/42 reconstruction (fixture pin only), 34/34 authorial (33 → 34 additive), 34/34
fact-correction (32 → 34 additive); migration 003 applied to `longmem`, no-arg migrate →
**"Up to date: 3 migration(s) applied, 0 pending"**; `longmem` pristine via the postgres MCP).
Jack ruled two shapes via explicit questions at plan approval; the remaining shapes were
approved with the plan.

1. **Damper = as suggested (explicit question; the spec's promotable flag closed).**
   Fruitless = a gate fetch appending zero new memory IDs; after
   `gate_damper_fruitless_max` (default 2) consecutive, the **novelty signal** is suppressed
   for the scene remainder; the entity tripwire stays live (near-ground-truth); a scene
   boundary resets streak and suppression; the streak is caller-held wire state
   (`gate_fruitless_streak`, the reputation_snapshot trust class). **Rejected:** suppressing
   both signals (silences the demo-legible near-ground-truth signal for economy); no damper
   in v1 (unlimited fruitless probes).
2. **Correction-path NER failure = clean loud error, nothing written (explicit question).**
   `CorrectionNlpFailedError` → 502 at the route, the embed-failure precedent's exact shape;
   the NER runs before the embed, before the transaction. **Rejected:** unwrapped 500 (a
   stack trace instead of guidance); degrade-with-copy-forward (silently violates
   "corrections move entities" — the freeze ruling's own target).

Approved-with-plan shapes, as built: knobs `gate_novelty_threshold` 0.5 / `gate_fetch_k` 3 /
`gate_damper_fruitless_max` 2 / **`gate_enabled` 1** (the fixture-pin shape — the
`reconstruction_theta = 0` precedent — doubling as the integrator kill-switch scaffold; the
reserved per-signal kill-switch may later grow its own knobs); signal constants
`"novelty"` / `"entity_tripwire"` + rungs `entity_only | novelty_only | closed` (the
`TRIGGER_*` precedent); `app\gate.py` as a PURE decision module (the decay.py precedent) with
retrieval owning all IO and `cosine_distance` imported from reconstruction (one
implementation); coverage semantics (component covered iff any term, canonical or alias,
case-insensitive, appears in any loaded fact-head's entities; **coverage-basis-absent ⇒
novelty_only**, never fire-on-every-mention; empty loaded set ⇒ trivially novel); timing
contract `gate_ms` = loaded/components fetch + evaluation, `sql_ms` = probe only (0.0 closed);
wire deltas (`loaded_memory_ids` + `gate_fruitless_streak` on both requests,
`RetrievedMemory.gate_fetched`, nested defaulted `GateInstrumentation`,
`CorrectionRequest.entities`, `CorrectionResult += entities, nlp_ms`); efficacy comparators
(`novelty_outscored` = top fetched score > min loaded score under the turn's probe;
`entity_covered` = any fetched fact-head's entities ∩ the uncovered terms); prompt sub-header
`"Recalled just now, mid-conversation:"` inside the single `[memories]` block, loaded items in
the caller's append-only order (payload order stays `(−score, memory_id)`); the callback as
function params only (never Pydantic fields), forwarded on gated turns, fired once before the
blocking retelling call; runner bookkeeping keyed on the server's `gate.evaluated`.

Accepted properties, recorded: the degraded GIN `&&` overlap is byte-exact against stored
entity strings (aliases never sit in entities arrays — the Python coverage check has no such
limit); gated payloads may exceed k (append-only, damper-bounded); fire-turn scores mix
Python cosine (loaded) with SQL `<=>` (fetched) — not under byte-identity;
`fetch_entity_candidates` has no LIMIT (Python-scored, the fetch_live_candidates precedent);
the damper streak is caller-trusted wire state.

Build-surfaced learnings, recorded honestly: (a) **pgvector rows need `.to_list()`** — a
selected `vector` column returns a `Vector` object, not an iterable (the first walker run
caught the loaded-set fetch failing quiet into the ladder's loader fallback — the fail-quiet
rung worked as designed while the bug hid behind it); (b) **fake-mode calibration
corrected**: under the trigram fake, ordinary distinct English prose lands ~0.45–0.75 cosine
distance (shared trigrams), not the estimated ~1.0 — echoes ~0.04, near-copies ~0.08; the 0.5
default STANDS (echoes/near-copies vs distinct prose separate cleanly), but guaranteed-novel
walker fixtures need trigram-rare wording chosen by measurement (the damper text's min
distance ≥ 0.73); the spec's calibration parenthetical and `app\config.py` comment were
corrected (comment-only). Verification also included the live piped REPL beat (loader turn →
mid-scene novelty fetch → both-signal fire with `fruitless=yes` → `:correct` →
**`(reconstructing…)` printed DURING the blocked turn**, `blocked=yes` — the
latency-becomes-characterization beat live, with the corrected fact basis also making the old
wording read as novel: retrieval-follows-the-fix visible in the gate's min-distance) and a
standalone load-driver run emitting `gate_check` p50/p95 + the gate block with real
fire/efficacy data.

## Test-suite build rulings — 2026-07-20

Structural pytest suite v1 built and floor-verifier-passed (immediate-queue item 1;
`docs\test-suite.md` was already the spec — no separate spec session). 38 scenarios in
`tests\test_*.py`: Sets A (authorial pair incl. the fact chain; the diegetic pair still lands
with the dissonance mechanism), B, C, D, + the degradation cases. `app\`, `db\`, and all
seven `verify_*.py` walkers byte-identical to HEAD — the eight floors stand by construction
(the verifier's recorded reasoning; re-running identical bytes proves nothing new). Jack
ruled three shapes via explicit questions at plan time; the remaining shapes were approved
with the plan.

1. **Stop-hook budget = fast subset (explicit question).** Scenarios that CALL the write
   pass at the service level (observe, or the correction verb with its NER merge) carry the
   pytest marker `nlp` — they trigger the lazy spaCy+fastcoref load (~75 s cold on this
   machine for the first call; the load, not the scenarios, dominates) — and
   `run-suite.ps1` now runs `python -m pytest tests -x -q -m "not nlp"` (31 scenarios,
   ~14 s). The FULL suite (38) runs on demand, at floor verification, and before any commit
   touching `app\`. **Rejected:** full suite at every turn-end (a multi-minute cold-start
   tax on every future session, docs-only ones included); measure-first-then-re-rule (the
   measurement happened at build anyway — cold 82 s / warm 30 s full, 14 s subset — and
   confirms the split).
2. **Postgres unreachable at the hook = skip cleanly, loud notice (explicit question).**
   A conftest session-fixture probe: unreachable ⇒ every DB-backed test SKIPS, a visible
   `STRUCTURAL SUITE SKIPPED: postgres unreachable` warning prints, exit code 0 — the
   hook's existing dormant-when-prerequisites-missing philosophy extended to the DB
   prerequisite. Pure no-DB scenarios still run. **Rejected:** go-red (docs-only sessions
   could not end a turn cleanly without Docker running).
3. **CI = CI-ready now, workflow later (explicit question).** The suite is one-command,
   offline, keyless (fake providers pinned in fixtures regardless of `.env`), deterministic
   (two consecutive full runs asserted), and scratch-DB self-managing; no `.github\`
   workflow this session — it lands as its own later item (natural home: the public-flip
   sprint). **Rejected:** workflow-this-session (an extra build-and-debug chunk — pgvector
   service container + ~2 GB model caching — on top of 38 scenarios). Until it lands,
   regressions are caught only on-machine; stated and accepted.

Approved-with-plan shapes, as built: runner = pytest 9.1.1 with NO pytest-asyncio — each
scenario is a sync `def` wrapping `asyncio.run(..., loop_factory=asyncio.SelectorEventLoop)`
via `conftest.run_structural` (the walker idiom; the Windows psycopg constraint);
`requirements.txt` += `pytest==9.1.1`, `httpx==0.28.1` (the latter closing the 2026-07-16
unpinned-httpx audit observation — the suite is its fifth consumer); scratch DB =
**`longmem_suite`**, deliberately distinct from the walkers' `longmem_test` so a Stop-hook
run never collides with a walker loop (session fixture: DROP IF EXISTS → CREATE → migrate
001–003 by subprocess → tests → DROP; per-test TRUNCATE of product tables — fixture reset of
a disposable scratch store, outside the memory-content invariant exactly as the walkers'
DB drops are); unmarked scenarios seed at the db layer through the real
`db.insert_observation` (`InsertPlan` with explicit fixture facts + the pure fake embedding
— no NLP import path); per-set configs mirror the walker pins with production-vs-fixture
stated per key (Sets A/B: theta 0 + gate off; Set C: PRODUCTION theta, gate off; Set D:
PRODUCTION gate, theta 0); fixture texts reuse the walkers' measured trigram corpus;
`pytest.ini` registers the marker + `testpaths` + `-p no:cacheprovider` (no repo-tree
cache residue); the escalation hard-stop degradation test asserts the CURRENT build-phase
stance and says so in its docstring — the owed production re-rule changes exactly that test.

Measured at build (recorded for hook-budget honesty): full suite 82 s cold-cache /
~30 s warm; `-m "not nlp"` subset ~14 s; unreachable-skip ~3 s.

## Latency-fix + suite-concurrency rulings — 2026-07-20

Jack ordered a fake-mode latency/compute pass (offline profiling before any real-mode run),
then, on the findings, ruled: **apply the two identified pits' fixes and harden the suite
concurrency gap** ("go ahead and complete both (a) and (b)"). All measurement lived in the
scratchpad (harness + EXPLAIN ANALYZE + cProfile + a psycopg micro-benchmark); the fixes
touch three files and no floor's behavior — re-verified: full suite 38/38, all seven walkers
green (40/36/36/42/34/34/51), migrate a clean no-op, `longmem` pristine.

**Fake-mode caveat (why these are worth fixing before real mode):** fake providers make model
CALLS ~0, so the profiled costs are pure infrastructure/local-compute underneath the eventual
LLM round-trips — both pits are removable waste, not model latency.

1. **Pit #2 — the vector probe sent the query vector as a param TWICE (44 ms wire stall) →
   named param.** `fetch_vector_candidates` / `fetch_gate_candidates` (and, for the shared
   `_VECTOR_CANDIDATE_FROM` clause, `fetch_loaded_set` / `fetch_entity_candidates`) bound the
   1536-dim query vector with positional `%s` in both the SELECT-distance and ORDER-BY slots.
   Two ~6 KB params cross a segment boundary into a Windows-loopback Nagle/delayed-ACK stall:
   **server executes in ~1.3 ms (EXPLAIN ANALYZE, HNSW index used), client observed ~46 ms,
   flat across 100/1k/5k rows.** Micro-benchmark: positional-twice 44 ms, `binary`/`prepare`
   no effect, **named `%(qv)s` referenced twice → sent once on the wire → 1 ms.** Fix: those
   four queries bind by name (all-named per query; the HNSW `ORDER BY embedding <=> ...`
   expression is unchanged). Measured end-to-end: retrieval ~54 ms → ~5–10 ms; a gate fire
   ~55 ms → ~7 ms; a reconstruction cache-hit read 54 ms → 7.6 ms. **Rejected:** `TCP_NODELAY`
   alone (treats the symptom, still ships the vector twice); query rewrite to alias the
   distance in ORDER BY (breaks HNSW index use — pgvector needs the literal expression).

2. **Pit #1 — fastcoref re-fingerprints its dataset every observe (~90 ms) → tame the
   `datasets` fingerprint.** cProfile: ~90 ms of a ~136–194 ms write pass is `FCoref.predict`
   → `datasets.Dataset.map()` deriving a content fingerprint by dill-pickling the transform's
   closure, which reaches fastcoref's internal spaCy model (the `datasets` spaCy dill-reducer
   serializes the whole pipeline) — all to name a cache file never read. Lever measurements:
   `datasets.disable_caching()` alone ≈ no change (it doesn't skip fingerprint COMPUTATION);
   short-circuiting the fingerprint `Hasher.hash` → **136 ms → 48 ms (3×)**; batching amortizes
   (24 ms/text at 16) but observe is one-at-a-time. Fix (`app\nlp.py` `_tame_datasets_fingerprint`,
   called from the `_coref()` loader): `disable_caching()` + replace `Hasher.hash` with a
   constant. **Safe** because caching is off (constant fingerprints can't collide on a cache
   file) and the fingerprint otherwise only sets an ephemeral dataset's `_fingerprint`; coref
   OUTPUT is unchanged (the walkers' assertion surface — all seven still green). **Guarded:**
   wrapped so any `datasets`-internals drift is swallowed, leaving the slow-but-correct path —
   the worst case loses the optimization, never breaks a write. Measured end-to-end:
   write pass ~215 ms → ~63 ms. This is the one **library-internal monkeypatch** among the
   fixes — flagged as a version-fragility cost (benign failure mode), easy to revert.
   **Rejected:** `disable_caching()` alone (ineffective); a write-pass batching redesign
   (architectural, doesn't help single-observe latency — the demo's actual shape).

3. **Suite concurrency (b) — per-process scratch DB name.** The suite's session fixture
   DROP/CREATEs a fixed-name `longmem_suite`; the Stop hook fires a run at every turn-end, so
   rapid consecutive turns overlapped two runs and one's `DROP ... WITH (FORCE)` force-killed
   the other's live connections (`psycopg.errors.AdminShutdown` — a false-RED surfaced during
   the profiling turns). Fix (`tests\conftest.py`): `SUITE_DB = f"longmem_suite_{os.getpid()}"`
   so overlapping runs never share a DB. A hard-killed run leaks an empty `longmem_suite_<pid>`
   (dropped by the next same-pid run; never collides with a live run). **Rejected:** a global
   lockfile (serializes runs, slower, another failure mode); sweeping all `longmem_suite_*` at
   startup (would drop a concurrently-running suite's DB — reintroduces the collision).

Not fixed (secondary, recorded for later): connection-per-query churn (~5–10 `pool.connection()`
acquisitions per turn, plus one write-back transaction per aged memory) — minor next to the two
pits, a batching candidate. And a real-mode COST flag (not a latency pit): escalation fired on
24/40 observes (60%) with realistic prose — each is an extra LLM call in real mode; eyeball the
trigger thresholds before the real run.

## Research-adoption slate + encoding-context build rulings — 2026-07-20

**Context.** The research sweep (45 papers; consolidated in `Research Papers\FINDINGS.md`, a
gitignored working folder) produced a prioritized shortlist. Jack ruled the adoption slate at
plan approval, then the encoding-context term (Target A) was built and floor-verified the same
session. Source papers per change are traced in `Research Papers\CHANGES-FROM-RESEARCH.md`.

**Slate rulings (Jack, at plan approval — four explicit questions):**

1. **Slate scope = two build targets now, rest queued.** Target A: the encoding-context read
   term + a TARG-style gate-calibration utility. Target B: a hybrid lexical retrieval channel
   (migration 004). Each lands and floor-verifies separately. Queued as their own future
   sessions: the judged eval harness, graph/associative memory, recall-reinforced decay, and
   automatic conflict/staleness detection (see the status.md queue). **Rejected:** one-target
   minimal (leaves the cheap lexical win unbuilt); three-targets-incl-eval-harness (session
   too large for the one-floor-per-session discipline).
2. **Encoding-context source = client-supplied fields.** The reserved
   `DialogueInitRequest.location_name/entities/event_time` are consumed AS SUPPLIED — the game
   client knows the scene's place/cast/time. **Rejected:** RaMem-style LLM query decomposition
   (a new model role + per-turn call, and it would supersede the 2026-07-14
   query-embedded-as-is ruling, which stands).
3. **Eval harness (queued) = v1 includes LLM-judged categories** (judge model role + env var)
   alongside structural scenarios, with the honest constraint stated: judged signal is only
   meaningful in real provider mode. **Rejected:** structural-first-judge-later (Jack wants the
   judge surface designed in from v1).
4. **Recall-reinforced decay = its own later spec session.** It needs a migration plus a real
   ruling on what counts as "recall" (gate fetch? reconstruction serve? dialogue surface?) and
   careful handling against invariant #2 (decay ≠ invalidation) and within-scene byte-identity.
   **Rejected:** folding it into this slate.

**Encoding-context build shapes (approved with the plan; the walker + suite assert them):**

- **Soft multiplicative nudge:** `score ×= 1 + Σ w_i·match_i` over the components the request
  supplies — entity coverage (|query ∩ live-fact-head entities| / |query|, casefolded both
  sides; fact-head entities so the match follows correction, migration 003), event-time
  proximity (`exp(−|Δ|/context_time_scale_seconds)`), casefold location equality. Factor ≥ 1
  always: never a filter, never a penalty; NULL row fields contribute 0. Applies on loader,
  gated (loaded + fetched, same context), and degraded paths (the term is lexical/structural,
  not a vector dependency).
- **The parity contract:** a request with no context fields skips the term entirely — zero
  extra float ops, scoring byte-identical to v1 (the loader-parity precedent). Walker
  criterion [7] asserts the exact factors (×1.75 full match at default knobs, ×1.125 half
  entity coverage, ×1.0 bare row).
- **Knobs:** `context_weight_entities` / `context_weight_event_time` /
  `context_weight_location` (0.25 each) + `context_time_scale_seconds` (86400.0), all
  SERVICE_DEFAULTS, per-agent overridable. Conservative defaults; a build-level choice, not a
  ruling.
- **Instrumentation-level surfacing** (`context_active` + `context_components`): the scored
  tuple and the serving stage are deliberately untouched — `app\reconstruction.py` is
  byte-identical to HEAD (the fact-level build's no-delta precedent). Per-item factor
  visibility deferred until something needs it.
- **CandidateRow widening:** `_CANDIDATE_COLUMNS` + `CandidateRow` grew
  `event_time`/`location_name`/`fact_entities` (defaulted, before `distance`); every fetcher's
  positional construction moved with it; the degraded path's FROM gained a **LEFT JOIN** to
  live fact heads so a legacy-shaped row (no live fact head) stays reachable — the never-blank
  ruling outranks the join.
- **Caller surface:** `DialogueTurnRequest` gained the three passthrough fields (the k/as_of
  precedent); the session runner holds scene context (fourth application of the
  caller-holds-scene-state contract; scene boundary resets it); REPL `:context` meta-command
  (shlex-split key=value: loc/entities/time; quoted values carry spaces).
- **The one ruling-driven walker change:** read-path criterion [7] ("reserved fields inert")
  asserted the superseded contract and was re-scoped to the context contract; walker 36 → 42.
  `weight_overrides` stays reserved-inert, asserted as before. Suite 38 → 40 (Set B parity +
  exact factor; Set D gated-path factor with the gate decision proven untouched — context
  nudges scores, never opens or closes the gate).
- **TARG calibration = report-only** (`--gate-budget <rate>`): recommends the
  `gate_novelty_threshold` at the (1−rate) quantile of a run's novelty min-distance CDF;
  trivially-novel turns counted separately; reads the service default only (stated in the
  report); never writes a knob.

**Paper provenance (Target A):** RaMem (arXiv 2606.22844) — the mechanism; Position: Episodic
Memory (2502.06975) — context as a defining episodic property; TARG (2511.09803 §3.4) — the
budget-calibration recipe. Full trace: `Research Papers\CHANGES-FROM-RESEARCH.md`.

## Hybrid lexical channel build rulings — 2026-07-20

**Context.** Target B of the research-adoption slate (scope ruled in the slate entry above).
Built & floor-verified the same session as Target A. Mechanism sources: the lexical/semantic
complementarity finding (Memory in the LLM Era survey, arXiv 2604.01707 §7) and Engram's
dense+lexical fusion evidence (arXiv 2606.09900); trace in
`Research Papers\CHANGES-FROM-RESEARCH.md`.

**Build shapes (approved with the plan; one design correction surfaced at build):**

1. **Token-OR tsquery, not websearch/plainto AND semantics — the build-surfaced correction.**
   The plan sketched `websearch_to_tsquery`; at build it surfaced that websearch/plainto AND
   semantics would make the channel inert (a real utterance never full-AND-matches a stored
   memory). Shape built: `lexical_tsquery` — casefolded word tokens of ≥ 3 letters (letter-runs
   only: to_tsquery syntax injection-safe by construction), deduped in order, capped 16,
   OR-joined; ts_rank + memory_id orders the deterministic LIMIT cut; the read-path scoring
   formula does the real ranking after the union. The 3-letter minimum and 16-token cap are
   module constants — flagged by the floor-verifier as future knob candidates if an integrator
   ever needs them tunable.
2. **Migration 004 = index-only.** A partial GIN over live fact heads,
   `to_tsvector('simple', basis_text) WHERE invalid_at IS NULL` (the 002/003 partial-index
   precedent). No table/column changes, no data DML.
3. **The string knob follows the decay_classes precedent.** `text_search_config` is a plain
   agents.config key with `TEXT_SEARCH_CONFIG_DEFAULT = "simple"` in `app\config.py` (the
   float-only SERVICE_DEFAULTS/agent_knob contract doesn't fit a string). 'simple' is baked
   into the index expression (an expression index binds one config); the default-config SQL
   branch bakes the same literal so the planner matches the partial GIN; an override
   parameterizes `::regconfig` and runs the same predicate unindexed — correct, slower, stated
   in the migration header.
4. **Union is additive-only, scoring untouched.** Lexical candidates union into the vector
   over-fetch before scoring, dedup by memory_id (vector row kept); lexical hits carry their
   TRUE cosine distance (the all-named-params wire convention). `lexical_fetch_k` (default 8.0;
   **0.0 = the kill-switch**, pure-vector v1 — the gate_enabled shape).
5. **NULL-embedding fact heads are lexically reachable, relevance null — designed.** The fetch
   deliberately omits the `embedding IS NOT NULL` filter: exact-token recall softens the
   embed-degradation consequence (never a filter). This sharpened read-path walker criterion
   [9]: the vector-path exclusion is now asserted ON THE PROBE itself, and the healthy-path
   lexical reach of a degraded row is asserted honestly (relevance null).
6. **Loader-scope v1.** The gate's fire probe and the degradation ladder's entity-only rung are
   noted future consumers of the channel, deliberately not built (scope discipline). Degraded
   loader turns skip it (the fallback already fetches every live row).
7. **The mechanical ledger-pin update:** `verify_gate.py`'s exact-ledger assertion grew
   001+002+003 → +004 (the per-migration precedent); nothing else in that walker changed.
   Read-path walker 42 → 48 (criterion [13] + the sharpened [9]); suite 40 → 41.

## Real-mode parse hardening ruling — 2026-07-21

**Context.** The real-mode testing session (pre-ship gates b + c — the first session ever to
construct the real providers) broke on its first live smoke, in two independent ways, both
parse-side; the models' actual output was valid in every captured sample:

1. **sonnet-5 emits a leading `thinking` content block** (thinking-on-by-default model
   family), so `response.content[0].text` — the shape every real provider had used since the
   write-path build (2026-07-13, pre-dating that model behavior) — raised `AttributeError`
   on `RealReconstructionProvider`, an exception NOT in its catch tuple: the whole dialogue
   turn crashed rather than degrading. Diagnostic: content[0] = thinking block, content[1] =
   flawless JSON.
2. **haiku-4.5 wraps its escalation JSON in markdown code fences** despite the prompt's
   "No other text" (3/3 samples in the raw-response diagnostic; the write prompt on the same
   model returned bare JSON). Both parse attempts fail identically, so the seam's
   retry-once-then-hard-stop made EVERY escalating observe hard-stop in real mode.

**Ruled (Jack, via explicit question): parse-side hardening only.** Two helpers in
`app\providers.py` — `_first_text_block()` (first text-type block, "" when none => the
existing JSONDecodeError path) and `_lenient_json_text()` (strip markdown fences before
`json.loads`) — applied at the four JSON-in-text parse sites (write, escalation,
reconstruction, dialogue-accumulated-stream). Prompts, fakes, and every seam byte-untouched.
Alternatives presented and not adopted: prompt-only fence fix (relies on per-call model
obedience; one fenced reply is another hard-stopped write) and a model swap off sonnet-5
(leaves the escalation defect and the latent thinking-block fragility). Commit `1388bf6`;
re-verified suite 41/41 + all seven walkers green (40/48/36/42/34/34/51) + the gate-b smoke
end-to-end.

**Carried observations (no ruling asked):** the hardcoded `max_tokens=1024` (2026-07-16
observation) now also bounds sonnet-5's adaptive-thinking spend inside dialogue calls — no
observed truncation (30/30 turns parsed; out-tokens p50 well under budget), but it is the
first place to look if real-mode `MalformedOutputError` ever appears; a
`thinking: {"type": "disabled"}` request-side knob is a possible future lever for the
non-streaming reconstruction call (cost/latency, quality tradeoff — Jack's call if raised).

## Latency slate + split-brain pull-forward rulings — 2026-07-21

**Context.** The real-mode session's numbers put the player-facing turn at p50 ~4.1 s (first
token 1.4–2.2 s; a cold-scene reconstruction adds 9–16 s; our own layer costs ~190 ms of it —
the rest is model inference). Jack reviewed the table and ruled the latency work now.

**Rulings (Jack, via explicit questions + plain-prose gray-area review):**

1. **The viability bar: first word < ~1 s.** The product latency metric is prose
   time-to-first-token at the seam, not turn total.
2. **All four levers land before the demo ships:** A — split-brain streaming (specced this
   session, `split-brain-streaming.md`); B1/B2 — dialogue-call latency experiments
   (thinking-off one-liners + a haiku-dialogue env A/B, measured before committing); C1 —
   scene-boundary reconstruction pre-warm (background-reconstruct at scene start so first
   turns hit the ~4 ms cache; the scene-frozen cache key already supports it); D — async
   game-side observes + folding the measured 79% escalation fire rate into the owed
   escalation re-rule. Unchosen-now ≠ dropped: each is an immediate-queue pre-ship item.
3. **Split-brain pulled forward WHOLE — with a ruled topology alteration.** §9's serial
   sketch (behavior call, then prose sees that turn's action) would put ~0.8–1.5 s of
   behavior call in front of the first prose token. Jack re-read the asymmetry: the prose
   call needs **past** behaviors as world facts ("why did you do that a minute / a week
   ago"), never the current turn's — so the calls run **concurrently** and the current
   action enters the record for later turns. §9 amended (supersedes-in-part its serial
   wording).
4. **Gray area 1 — same-turn incoherence: accepted, and instrumented.** Concurrent calls
   mean one turn's words and action are chosen independently; occasional mismatch is the
   split-brain character (bounded by shared retrieval + the action vocabulary; self-aware
   from the next turn). Ruled with instrumentation from day one: the turn result records
   both calls' ranked scored views + the directive — §13's explanation-cause divergence
   measurable structurally.
5. **Gray area 2 — the world record is game-authored + a scene block.** Durable: the
   integrator reports *resolved* actions as ordinary observe events (the store never
   records unresolved intent; the endpoint exists — a documented contract, zero code).
   Within-scene: a caller-held recent-actions block in the prose prompt, reset at
   boundaries. The seam-auto-write alternative was rejected (records intent as fact even
   when the game contradicts it).
6. **Per-call weights go LIVE now, behavior view only** — the reserved `WeightOverrides`
   slot is consumed via a second scoring pass over the same candidate set; dialogue-view
   scoring stays byte-identical when no overrides ride (the context-term parity precedent).
   The read-path walker's inertness criterion re-scopes at build (ruling-driven).
7. **Streaming surface = seam + REPL + driver this slice.** The SSE/HTTP route rides with
   the Unity client item, where its consumer exists.

**Honest prices stated with the rulings:** this spec alone makes first word = TTFT
(1.4–2.2 s today) — the <1 s bar additionally needs the B-levers; the serial full-§9 shape
was presented fairly (lands the asymmetric same-turn framing, costs ~+0.8–1.5 s before the
first word) and not adopted; the single-call prose-first restructure was presented (cheapest,
no asymmetry landed) and not adopted.

## Split-brain streaming build rulings — 2026-07-21

**Context.** Immediate-queue item 1 (`split-brain-streaming.md`), built the same day it was
specced. The seam was split into two concurrent calls off one retrieval: a streaming pure-prose
call and a behavior call (directive + delta). Four forks were ruled via explicit questions at
plan approval; the mechanical settle-tags were approved with the plan (annotated onto the spec).

**Rulings (Jack, via explicit questions):**

1. **Behavior model role = a new `behavior` role.** `LONGMEM_MODEL_BEHAVIOR` +
   `LONGMEM_PRICE_BEHAVIOR_IN/OUT`; added to the CLAUDE.md role list; real-mode config validates
   it like the other roles. (Reuse of the `reputation` role name was the alternative — declined
   as under-descriptive, since the call also chooses the action.)
2. **Seam shape = async generator.** `run_dialogue_turn` yields prose chunks, then the terminal
   `DialogueTurnResult`; `first_word_ms` = time to the first yielded chunk. The chunk-callback
   alternative was presented and not adopted.
3. **Mid-stream prose drop = keep the partial + degraded flag** (partial prose is non-blank).
   Discard-and-fallback was the alternative.
4. **Behavior view = re-rank the served top-k set** (not the full over-fetch pool). Same served
   memories re-scored with resolved weights → a different salience order; reuses served text,
   zero extra SQL/model calls; divergence = order/score over the shared set. The full-pool
   variant (behavior-only items serving verbatim live heads) was presented with its plumbing
   cost and not adopted.

**Build resolutions (settle-tags, stated for the record):**

- **Exponent-form weighting.** The reserved `WeightOverrides {relevance, recency, importance}`
  applies as component-wise exponents on the product score:
  `behavior_score = item.score · rel^(w_rel−1) · rec^(w_rec−1) · imp^(w_imp−1)` (zero-component
  guard). At all-1.0 the exponents vanish so `behavior_score == item.score` — the dialogue-view
  parity contract — and any other value genuinely re-ranks. A plain per-component multiplier was
  rejected (a uniform scalar cannot re-rank a product); a weighted sum was rejected (it breaks
  product-form parity). Weights resolve request → `agents.config` → 1.0, clamped `[0.0, 4.0]`
  (module constants, not knobs). The behavior view is computed in the dialogue seam from the
  served `RetrievedMemory` fields, so retrieval stays byte-untouched; `DialogueInitRequest`
  `weight_overrides` stays inert (the read-path parity contract holds).
- **Identity in BOTH prompts.** The behavior prompt shares identity + reputation snapshot with
  the prose prompt (the §9 spec diagram omitted it; resolved to include it) so the asymmetry
  stays STATISTICAL not architectural — same character + same candidates, only the memory
  weights and the call type differ. The recent-actions block is the one ruled information
  difference and is prose-only (the behavior call chooses a new action, it does not explain a
  past one).
- **Prompt split.** `assemble_system_prompt` split into `assemble_prose_prompt` (identity +
  reputation + dialogue-view memories + recent-actions + a pure-prose instruction) and
  `assemble_behavior_prompt` (identity + reputation + behavior-view memories + the directive/delta
  JSON contract + vocabulary). The gate walker's sole change is the mechanical
  `assemble_system_prompt` → `assemble_prose_prompt` rename (its `[]` sixth positional arg is now
  `recent_actions`, so its [memories]-structure assertions stand).
- **Recent-actions block** = caller-held scene state (the fifth application of the
  caller-holds-scene-state contract): each turn's resolved directive appended as world-fact
  context for later turns' prose prompts, capped at `recent_actions_cap` (default 8), reset at
  scene boundaries, never stored server-side. `session.utterance` drains the seam and applies the
  bookkeeping in one place (`_apply_turn_result`); `session.stream_utterance` yields chunks for
  the REPL.

**Concurrency mechanism.** The behavior leg runs as an `asyncio.create_task(to_thread(...))`; the
prose leg's sync generator runs in a worker thread pushing chunks onto an `asyncio.Queue` via
`loop.call_soon_threadsafe`, drained by the async generator. Done-when 1 is proven with a
deliberately slow behavior fake: the first prose chunk arrives in ~8 ms while the behavior call
sleeps 300 ms (walker [7]).

**Environment note (flagged, NOT fixed — operator-owned `.env`).** `.env` carries a malformed
consolidated price line — `LONGMEM_PRICE_DIALOGUE_IN=3.00 / _OUT=15.00, _RECONSTRUCTION_IN=…` —
which `config.load_settings` cannot parse as a float, so any run that reads `.env` prices
(real mode, or fake mode without overriding that var) crashes at startup. The 2026-07-21
real-mode session sidestepped it by env-injecting clean prices. Jack's `.env` to fix; surfaced
for the pre-ship gates.

**Verification.** CLI-harness walker re-opened 36 → 55; read-path walker weight_overrides
criterion re-scoped (48); gate walker rename-only (51); write/reconstruction/authorial/fact
walkers byte-untouched and green (40/42/34/34); full suite 41 → 42 (twice) + keyless subset 35;
no-arg migrate "4 applied, 0 pending"; `longmem` pristine via the postgres MCP (ten product
tables 0 rows, ledger 001–004, no scratch residue); live piped REPL streaming beat + a standalone
driver run with the `first_word` + `behavior` series and the behavior cost row. No migration.
