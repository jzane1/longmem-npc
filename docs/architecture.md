# longmem-npc — Architecture

This file is the current design truth. Edit it when a design decision changes. The *why* behind each
decision lives in `decisions.md` (append-only). Current state, build order, and task queues live in
`status.md`. The first build target is specced in `migration-01.md`. Test discipline is in
`test-suite.md`.

## 1. What this is

A generalizable long-term-memory service for game NPCs that others integrate into their own games or
applications: a self-hostable backend (FastAPI + PostgreSQL/pgvector) plus a Unity-embeddable client
package. We never host the backend; integrators run it themselves.

The system gives characters psychologically plausible memory: a bi-temporal, non-destructive record
underneath, with identity-conditioned reconstructive recall, believable decay, and dissonance-driven
defense above it.

**Thesis:** behavior → confabulated reason → stored → defended. *A psychology, not a database.* The
claim axis is **controlled infidelity above an immutable record** — the character's telling of a
memory can drift and be defended, while the ground-truth record underneath never lies.

## 2. Non-negotiable principles

- **Bi-temporal, non-destructive.** Every memory row carries `created_at` (when we wrote it),
  `valid_at` (when it happened in world time — wired to the client-sent timestamp, timezone-aware),
  and `invalid_at` (when it was superseded, if ever). Superseded rows survive and stay queryable.
  Reflections carry the same columns.
- **Recency decay and correction-override are structurally distinct mechanisms.** Decay is a
  read-time computation; correction is a bi-temporal invalidation. Never conflate them; the test
  suite proves the separation.
- **Importance vs relevance are independent axes.** Importance is scored once at write time (stored
  raw, normalized at read), anchored to a per-NPC, integrator-configured diagnosticity goal.
  Relevance is computed per-query at read time.
- **Write-time facts vs runtime state.** Facts about the event (typology, confidence, context
  components, decay class, provenance, gist/detail spans, importance) are populated from day one.
  Runtime state (reflection pressure, reputation accumulation, drift headroom) ships with its
  mechanism and needs no backfill. Rationale on record: importance is a write-time fact about the
  event; reconstruction drifts the *telling*, not the event's centrality, so defending by day-0
  importance is arguably correct. If dynamic salience ever enters, it enters as a separate runtime
  term.
- **Schema now, mechanism later.** Schema, caches, and pin behavior are live from day one even where
  the consuming mechanism lands later. Re-slated 2026-07-14: reconstruction ships **pre-demo**;
  dissonance and reflection land after the August demo.
- **Integrator-defined vocabulary everywhere.** Observation phase tags, diagnosticity goal, action
  vocabulary, context-match weights, scene-type vocabulary, model roles, rigidity, reputation
  sensitivity, decay knobs, drift threshold, habituation cap/decay — none is ever hardcoded.
  Violating this anywhere makes the config surface incoherent.
- **Instrument at the seam, not after.** Timing and token accounting are added to each layer as that
  layer is built.
- **Storage before cognition** build ordering.
- **Degradation behavior is named and tested per model call.** Importance-scoring failure → store
  the memory with neutral importance plus a `scoring_failed` flag; embedding failure → the write
  lands with a NULL embedding (`embedding IS NULL` is the queryable signal; ruled 2026-07-13);
  never lose a write because a model was flaky. **One recorded exception (build-phase stance,
  ruled 2026-07-13, must be re-ruled before the demo ships — see the open question in
  `status.md`):** a gist-escalation call that fails twice hard-stops the write, fail-loud, with
  nothing inserted. The retrieval gate degrades per its ladder (section 6), fail-quiet.
  Malformed-model-response cases live in the test suite.

## 3. Environment & stack

**Environment.** Windows 11 (25H2). Always PowerShell syntax and backslash paths — never bash.
Project root: `C:\Users\jacks\Projects\longmem-npc`. Unity 6, flatscreen 3D
(CharacterController + mouse-look, raycast-plus-key interactables); Unity's external script editor
is VS Code. Global Python 3.14.3 on PATH. Secrets live in `.env` at repo root, never in docs.
C# root namespace `NpcMemory`; Unity scripts under `Assets\Scripts\` until the package layout
(`com.jacksonzane.npc-memory`) is settled; Unity Package Manager packaging is deferred until after
the demo video.

**Backend.** FastAPI; psycopg v3 with `AsyncConnectionPool`; hand-written SQL (no ORM);
PostgreSQL 16 + pgvector in Docker (the `pgvector/pgvector` image); UUID primary keys minted
server-side; HNSW vector index (a cheaply reversible choice).

**Models.** Haiku-class for importance scoring, description rendering, typology classification,
gist escalation, reconstruction, reputation-delta emission, and reflection. Sonnet-class for
dialogue. Every model role is an integrator knob with its own env var, so each upgrades
independently (the escalation role's var is `LONGMEM_MODEL_ESCALATION`, ruled 2026-07-13). The
retrieval gate is **non-LLM** — there is no gate model and no gate env var.

**Embeddings.** OpenAI `text-embedding-3-small` at 1536 dimensions; the column dimension is locked.
The same model embeds location names/descriptions and gate-time utterances.

**Write-time NLP (no LLM).** Ruled 2026-07-13: spaCy `en_core_web_lg` + `fastcoref` for
intra-observation coreference (never `neuralcoref` — abandonware); affect via VADER (compound →
valence) + the bundled Warriner 2013 VAD lexicon (arousal, normalized 1–9 → 0–1; dominance lives in
`affect_detail` jsonb). NRC-VAD was rejected at the license gate — research-only, incompatible with
the planned Apache-2.0 flip; Warriner is CC-BY 4.0 (`data\lexicons\` with attribution).

## 4. Data model

### 4.1 Gist and detail

Gist is a **span pointer into the immutable on-disk observation text** — not a rewritten summary.
At write time, the NLP pass matches tokens/entities/noun-chunks against the NPC's **identity
components table** (entries: canonical name + aliases + category, e.g. friend names, job title; a
category hit counts even without a named entity). Hits become gist spans; everything else is detail.

An LLM escalation pass exists for hard cases, **biased loose** (over-call — a wasted call is cheap,
a lost gist breaks the product). Five triggers, any one fires (ruled 2026-07-13; all
integrator-tunable via `agents.config`, defaults in `app\config.py`): (1) importance above
threshold; (2) an identity/category hit co-occurring with |valence| above threshold; (3) a **novel
entity** — which is also how the identity components table grows; (4) an unresolved
pronoun/noun-chunk co-occurring with an identity/category hit; (5) low NLP confidence on an
already-flagged span (confidence only ever *adds* calls, never suppresses one).
Cross-observation coreference misses are accepted as graceful failure (the detail just decays).

### 4.2 Decay

`tau_effective = tau_base × (1 + k × importance)`; `decay = 1 − exp(−age / tau_effective)`.

Decay applies to **non-gist detail only**, which decays to fully hidden; **gist never decays**.
Decay is computed at read time; the original observation stays intact on disk forever — decay only
controls how much detail the reconstructor is shown, and any past state is re-derivable (debugging,
eval harness). Each memory carries a **decay class** (the differential-lambda class): an
integrator-vocabulary label selecting which base time-constant applies, used by both detail decay
and the recency term in retrieval scoring.

**Consequence to remember:** the identity components table is the *only* control on long-term
durable content. Its reflection-time trim (with silent cache invalidation — chosen deliberately) is
the sole mechanism that removes a durable fact.

### 4.3 Two identity structures — never conflate

1. **Identity components table** — an entity/topic index (canonical + aliases + category). Used for
   gist matching and as the entity-gate tripwire; grown by the LLM on novel entities; pruned at
   reflection time, silently invalidating reconstruction caches.
2. **Rendered identity document** — seed prose plus current identity-relevant reflections, rendered
   into the exact prompt block. `identity_version` = a content hash of the rendered document.
   Recompiled at scene edges.

## 5. Write path

Client event → NLP span/affect pass → **single Haiku call** (prose render + importance scoring;
typology classification only when the client didn't declare it) → **atomic insert**, populating all
write-time facts from day one.

- **Evidence typology** — `observed | told | inferred | reflected`, with a 0–1 confidence. A default
  per-typology confidence table exists; the client may override per event; **client declaration
  wins**. `typology_source` records `declared | inferred` (distinct from provenance).
- **Provenance** — `lived | injected` (injected = operator-seeded backstory).
- **Context stamps** — location, entities, time, affect. All four are optional API fields with
  stated per-field degradation when absent. Stored as typed columns per component (per-component
  read weights require it); location is embedded via the same 1536 model. **Entities are captured
  at write from day one:** the entities column + GIN index serve the gate now and the planned
  encoding-context read boost later.

## 6. Read path

**Dialogue initialization:** top-k retrieval. Endpoints return **memory IDs and scores alongside
prose** — this is load-bearing; it is what makes the test suite assertable.

**Retrieval scoring** (specced in `read-path.md`, 2026-07-14; physical shapes settle at build):
`relevance × recency(decay class) × importance_norm`; pin exemption; normalization; reserved slots
for a future encoding-context term and per-call overrides under the split-brain topology.

**Mid-dialogue gate (non-LLM hybrid):**
- **Novelty check** — embed the utterance; measure distance against the loaded set; far from all →
  fetch.
- **Entity tripwire** — an uncovered mention of an identity-components entry → fetch. (Most
  demo-legible signal.)
- A fruitless-retrieval damper limits accumulation. Every gate event logs **which signal fired** —
  this feeds the reserved novelty kill-switch decision (see `decisions.md`).

**Degradation ladder:** embeddings down → entity-only, fetching lexically off the GIN index ranked
by recency × importance; no entities supplied → novelty-only; both out → gate closed, serve the
loaded set, **fail-quiet**.

**Prompt caching:** within a scene, gate-fetched memories are **appended after the cached head** as
a marked recollection block; the head is **rebuilt at scene boundaries**, where the cache is cold
anyway. The **scene boundary is a load-bearing, explicit client-sent API event** with three
consumers: prompt-head rebuild, identity-document recompile, reputation snapshot. Scene edges settle
prefix, identity version, and reputation in one heartbeat. *(Consumer slating ruled 2026-07-14:
reputation snapshot lands with the dialogue turn; identity recompile with reconstruction — both
pre-demo; prompt-head rebuild / prompt caching is post-August.)*

**Read-mode boundary (self-describing, not just documented):** every returned memory carries
`read_mode` (`verbatim | reconstructed`) and `pinned`, in payloads and the debug view. Three states:
pinned → verbatim always; unpinned fresher than the reconstruction threshold → verbatim for now;
unpinned past the threshold → reconstructed. A fourth enum value, `reconstruction_pending`, exists
only if an async fallback is ever adopted. **Docs purity claim:** no raw access through the
character read path, except integrator-designated pins; ground truth lives in the debug view.

## 7. Reconstruction (pre-demo scope, ruled 2026-07-14; schema, caches, and pin behavior already live)

Identity-conditioned reconstruction is the **mandatory read path** for unpinned memories past a
threshold theta, where **theta reuses the decay math** (reconstruct when decayed detail strength
falls below theta). The reconstructor sees the **full gist span as a fixed constraint** plus the
time-thinned detail slice, conditioned on the rendered identity document.

**Write-back with a version chain:** one permanent `memory_id` forever; each retelling inserts a new
detail row and stamps the prior one superseded — **versioned confabulation over an immutable
record**. Chain rows carry a `write_cause` enum:
`original | reconstruction | rationalization | update_with_resentment | authorial_correction`.

**Serving:** Haiku-class; **one structured call batching all k cache misses per retrieval**;
pre-warm at dialogue init; on a mid-scene miss, **block and expose a "reconstructing" signal**
(latency becomes characterization). Async serve-verbatim-then-cache is **not** the design — if
latency ever forces async, the swap must be explicit state (a `reconstruction_pending` read mode),
never silent text mutation, because of the **within-scene text-stability invariant**: absent a
diegetic event on that memory, repeated reads within one scene return byte-identical text.

**Cache:** keyed `(memory_id × identity_version)`. **Cache-eviction invariant (generalized):** cache
writes happen only in the reconstruction path; **any other writer to a chain — correction, diegetic
write, purge — must evict all cache rows for that memory_id.**

**Drift budget:** on each reconstruction-driven write-back, embed the candidate and measure distance
from the anchor; past threshold, **refuse the write and keep the prior head**. Event-driven writes
(both diegetic paths) are exempt from the budget. **The anchor needs no pointer:** it is the latest
chain row whose `write_cause` is `original`, `authorial_correction`, or `update_with_resentment`.
Re-anchoring by cause: authorial → the corrected head (the authorial-correction row);
update-with-resentment → the new head;
rationalization → **never** (it spends headroom without being blocked, so a heavily defended memory
crystallizes — "the story has set"). On-camera demo artifact: one memory drifting across 60 days.

## 8. Dissonance and correction verbs

**Dissonance threshold** = importance × evidence typology × per-NPC **rigidity** scalar
(0.5 pushover → 2.0 zealot). "I saw it" resists harder than "I heard it," on both sides of a clash.
Either way **the store records the truth**; the fork only shapes the character's reaction.
Habituation guards for the future context term: **both a cap and a decay**, as integrator knobs.

**Two correction verbs, semantically distinct:**
- **Authorial** (operator fixes wrong data): **replace model (ruled 2026-07-12)** — supersedes the
  drifted chain with a corrected head row, `write_cause = authorial_correction`. The memory stays
  retrievable under the same memory_id, now serving corrected content, and the corrected head
  becomes the drift anchor. Prior rows are invalidated by ordinary supersession; the verbs are
  discriminated by the new head's `write_cause`, not by any marker on prior rows.
- **Diegetic** (in-world confrontation; an API event referencing a target `memory_id`): preserves
  the chain and routes through the dissonance path; the new head row is typed `rationalization` or
  `update_with_resentment`, and a correction record is present.

**Pin semantics (final ruling — supersedes any earlier note saying pin blocks diegetic):** both
correction verbs **outrank pin**, and the resulting new head **inherits the pin**. Pin means exactly
two things: exemption from decay, and exclusion from the reconstruction process. "No reconstructed
chains" does not mean "no chains" — event-driven corrections proceed at the normal dissonance
frequency. Pin/unpin are endpoints; pinning **freezes the current head** (restoration is a
correction verb, not pin); unpinning resumes the chain from the frozen head.

## 9. Behavior output & turn topology

**August ship:** a single Sonnet-class call emitting prose + structured output.

**Committed target topology (post-August): multi-call split-brain.** A behavior call (Haiku-class,
with its own retrieval weights) chooses the action; the dialogue call then sees that action **as
observed world fact — never "you decided to."** The asymmetry is **statistical, not architectural**
(per-call scoring weights, no masks). Write the action-directive contract so it survives this
migration unchanged.

**Action directive:** per-turn, from an **integrator-supplied vocabulary** (free type + params);
unknown or unparseable directives → log, ignore, the turn still succeeds.

**Reputation:** a scalar on the NPC row. The Haiku call emits a delta by default; a client override
wins; per-NPC sensitivity scalar; hard clamp on a defined scale. Injected into the prompt prefix
from a **scene-start snapshot**.

## 10. Reflection & parameter bundles (mechanism deferred)

Reflection is an **endpoint** (the verb) — no scheduler. The store exposes **reflection pressure as
a readable gauge** and the integrator pulls the trigger. Sampling: episodes weighted by
**importance × recency** (the existing diagnosticity axis), not recent-N.

Reflection revises the **seed identity** (which lives in Postgres); identity-relevant changes flow
into the rendered identity document and bump `identity_version` via content hash. Reflection also
**prunes the identity components table** (silent cache invalidation).

**Parameter compiler (later):** one call per (reflection × scene-type), cached. Bundle = a fixed
**typed core** (retrieval-weight multipliers, action-set biases, stance priors; typed and clamped)
+ **namespaced passthrough**. Scene-type vocabulary is integrator-owned; unknown types
log-and-continue against a default bundle. Compiled params are consumed **only upstream of the
dialogue call** — the dialogue call sees only their consequences. Bi-temporal reflection
invalidation doubles as compiler-cache eviction.

## 11. Instrumentation & load driver

- **Latency histogram:** p50/p95, decomposed into gate check, retrieval SQL, first token, total.
- **Gate efficacy, per signal:** novelty metric = fraction of fires where the fetched memory
  out-scores the loaded set; entity metric = near-ground-truth "did the retrieval contain that
  entity." Log which signal fired per gate event.
- **Cost:** itemized per 100-turn session.
- **Synthetic load driver:** Python, scripted sessions at volume; a first-class artifact co-built
  with the CLI harness. **No distribution exists without it.**

## 12. Integrator surface requirements

Docs are written as though a **hostile integrator** is reading them, answering ownership questions
before they're asked: Whose Postgres is this? What happens on schema migration? What is the
retention policy? Can a player's memories be deleted?

- **Retention:** a tested **purge endpoint/script, no scheduler** — the tool provides the delete
  verb, the schedule is the integrator's policy (this is the GDPR surface). Purge completeness
  stated honestly: the endpoint deletes the original, its chain, and its caches; reflections
  previously derived from purged episodes are aggregate work-product, and the docs say so.
- Docs must draw the **verbatim/reconstructive read-mode boundary** (self-describing payloads carry
  it too), state per-field degradation for optional context fields, state the gate degradation
  ladder, and include a **"what this is not"** section.
- The service is disciplined by no real shipped game; the docs supply the discipline the absent
  consumer would have.

## 13. Positioning & research angle

**README positioning:** non-destructive bi-temporal storage vs destructive LLM compression, citing a
real counter-example system (still unpicked — see the artifact queue in `status.md`).

**Citations on record:** compressive-RAG framing (Spens & Burgess); the CoALA supersede-vs-decay gap
is answered by bi-temporal invalidation + differential decay classes; Talk of the Town's
repetition-breeds-commitment validates write-back; PSI/MicroPsi lineage for the parameter compiler;
Turpin (unfaithful chain-of-thought) and Gazzaniga (confabulated reasons) for the asymmetric-
cognition line. Cite **encoding specificity as a phenomenon family, not the diving study** (its 2021
replication attempt failed, ~0.25 SD).

**Research track (post-demo):** the signature pair is **identity-conditioned reconstructive memory**
and **information-asymmetric multi-call cognition** (confabulation via information asymmetry); they
compose into one paper-shaped thesis about character psychology. The demo video comes before the
research pursuit.
