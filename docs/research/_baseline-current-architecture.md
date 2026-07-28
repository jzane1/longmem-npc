# longmem-npc — current architecture baseline (yardstick for the research sweep)

**Purpose.** This is the *known-good* description of what longmem-npc is TODAY. When you read a
paper, judge every proposed mechanism against this. A finding is only "strictly better" if it beats
a mechanism described here; it is "not yet built" only if nothing here covers it. Cite the exact
component below that a finding touches.

**One-line thesis.** *A psychology, not a database.* The claim axis is **controlled infidelity
above an immutable record**: a character's *telling* of a memory can drift and be defended, while
the ground-truth record underneath never lies. Signature research pair: **identity-conditioned
reconstructive memory** + **information-asymmetric multi-call cognition** (confabulation via
information asymmetry).

**What this is.** A self-hostable long-term-memory *service* for game NPCs (FastAPI +
Postgres/pgvector) plus a Unity-embeddable client. Integrators run the backend themselves. It is a
generalizable library, disciplined by no shipped game — the docs supply the discipline.

---

## Non-negotiable invariants (a mechanism that violates one is a THESIS-TENSION flag, not an adoption)

1. **Bi-temporal, non-destructive storage.** Every memory/reflection/fact/detail row carries
   `created_at` (write time), `valid_at` (world time), `invalid_at` (supersession). Supersede by
   stamping `invalid_at`; **never UPDATE stored content in place; never DELETE** (purge endpoint is
   the sole exception). Superseded rows stay queryable. → Any *destructive* summarization/compression
   or in-place memory edit (much of Mem0/MemoryBank/MemGPT eviction) is a tension, not a drop-in.
   Two deliberate in-place scalars sit OUTSIDE this: `memories.pinned`, `agents.reputation`.
2. **Recency decay ≠ bi-temporal invalidation.** Decay is a read-time computation on detail
   strength; invalidation is a storage event. Never conflate. The test suite proves the separation.
3. **Importance vs relevance are independent axes.** Importance scored once at write time (stored
   raw, normalized at read), anchored to a per-NPC integrator "diagnosticity goal". Relevance is
   per-query at read time.
4. **Reconstruction is the mandatory read path** for unpinned memories past a decay threshold —
   the character never gets raw access except integrator-designated pins; ground truth lives in a
   debug view. Repeated reads within one scene are byte-identical absent a diegetic event or an
   authorial correction (within-scene text-stability invariant).
5. **Nothing integrator-configurable is hardcoded** — vocabularies, thresholds, model roles, knobs
   all live in `agents.config` / env vars. A hardcoded template/threshold is a defect.
6. **Read endpoints always return memory IDs + scores alongside prose** (makes behavior assertable).
7. **Degradation is named and tested per model call**, fail-quiet by default (write lands with NULL
   embedding on embed failure; neutral importance + `scoring_failed` on scoring failure). One
   fail-loud exception under re-rule: gist-escalation double-failure hard-stops the write.
8. **The retrieval gate is non-LLM.** No gate model, no gate env var.
9. **Instrument at the seam** — timing + token accounting added as each layer is built.

---

## Stack (do not propose substitutions as "improvements" — they're fixed constraints)

- FastAPI; **psycopg v3, AsyncConnectionPool, hand-written SQL — no ORM, no query builder.**
- PostgreSQL 16 + pgvector (Docker `pgvector/pgvector:pg16`). UUID PKs minted server-side.
- **Embeddings: OpenAI `text-embedding-3-small` @ 1536 dims, column dimension LOCKED.** Same model
  embeds observation text, location names, and gate utterances. (A second local embedding model
  collides with the locked dim — noted as a later/optional item.)
- **HNSW** vector index, cosine (`vector_cosine_ops`) — a cheaply reversible choice.
- Models per role, each its own env var (upgrades independently): importance, render, typology,
  escalation (Haiku-class); dialogue (Sonnet-class); reconstruction (Haiku-class). Post-August a
  reflection role + a behavior/"split-brain" role are planned.
- **Write-time NLP (no LLM):** spaCy `en_core_web_lg` + `fastcoref` (intra-observation coref) +
  VADER (valence) + Warriner-2013 VAD lexicon (arousal; dominance in `affect_detail` jsonb). License
  gate is real: Apache-2.0 flip planned, so CC-BY / permissive only (NRC-VAD was rejected).

---

## Data model (schema, migrations 001–003 live)

- **agents** — one row/NPC: `seed_identity`, `reputation`, `rigidity` (0.5 pushover–2.0 zealot),
  `reputation_sensitivity`, `diagnosticity_goal` (text prose), `config` jsonb (all per-agent knobs +
  `decay_classes` label→tau_base map + `decay_class_default`).
- **identity_components** — entity/topic index (canonical + aliases + category); bi-temporal
  (invalidate, don't delete). Two uses: gist matching + entity-gate tripwire. Grown by LLM on novel
  entities; pruned at reflection (silently invalidates reconstruction caches). **This table is the
  ONLY control on long-term durable content** (gist never decays).
- **memories** — one row/observation. `observation_text` immutable. Columns: `importance_raw`,
  `scoring_failed`, `typology` (observed|told|inferred|reflected) + `typology_confidence` +
  `typology_source` (declared|inferred), `provenance` (lived|injected), `pinned`, `decay_class`
  (free-text label) + `decay_class_unknown`, bi-temporal trio, context stamps (`location_embedding`,
  `location_name`, `entities` text[], `event_time`, `affect_valence`, `affect_arousal`,
  `affect_detail` jsonb). NOTE: since the 2026-07-18 freeze, `memories.embedding` is no longer
  written — the vector lives on the fact head (below).
- **memory_gist_spans** — gist as immutable **span pointers into `observation_text`** (start/end
  char + matched component/category). Gist is NOT a rewritten summary.
- **memory_details** — the **telling** version chain under a stable `memory_id`; one live head
  (`invalid_at IS NULL`); `write_cause ∈ {original, reconstruction, rationalization,
  update_with_resentment, authorial_correction}`. Versioned confabulation over an immutable record.
- **memory_fact_versions** (migration 002) — the **semantic basis** chain: `basis_text` + `embedding`
  (1536) + `entities` text[] (migration 003) + `write_cause ∈ {original, authorial_correction}`;
  one live head; **partial HNSW over live heads**, **partial GIN over live-head entities**. Retrieval
  ranks by the live fact head's embedding; correction re-embeds so **retrieval follows the fix**.
- **corrections** — diegetic correction record (schema live; the dissonance mechanism that writes it
  is post-August).
- **reconstruction_cache** — keyed `(memory_id, identity_version)`; eviction in app code.
- **reflections** — bi-temporal; `identity_relevant` bool; `source_memory_ids` uuid[] NOT
  FK'd (purge honesty). Mechanism is post-August.
- **identity_documents** — rendered identity doc + `identity_version` (content hash).

---

## Built pipeline (the nine verified floors)

### Write path (`app\ingest.py`, `nlp.py`, `providers.py`, `db.py`)
Client event → NLP span/affect pass → **single Haiku call** (prose render + importance scoring +
typology when undeclared) → **atomic insert** populating all write-time facts + the `original` fact
head. **Gist matching:** NLP matches tokens/entities/noun-chunks vs the identity-components table;
hits → gist spans, else detail. **LLM escalation** for hard gist cases, **biased loose** (5 triggers,
any one fires): (1) importance ≥ `escalation_importance_threshold` 0.45; (2) identity/category hit +
|valence| ≥ `escalation_affect_threshold` 0.5; (3) novel entity (also grows the components table);
(4) unresolved pronoun/noun-chunk co-occurring with an identity hit; (5) low NLP confidence on an
already-flagged span (RESERVED — no confidence source yet). Cross-observation coref misses accepted
as graceful failure. Event types: observe + scene-boundary + pin/unpin. Diegetic-correction event +
purge are still to build.

### Read path (`app\retrieval.py`, `decay.py`)
Top-k retrieval (`retrieval_top_k` 8; over-fetch `×4` by distance then re-rank). **Score =
relevance × recency(decay class) × importance_norm.** `importance_norm = clamp(raw, floor 0.05, 1)`.
Pin exemption. Determinism sort `(−score, memory_id)`. `as_of` override = age-computation override
only (candidate SQL always joins the live head). Query = `query_text` embedded as-is; location/
entities/event_time accepted-but-reserved (future encoding-context term). Empty store / embed-failure
→ fail-quiet (per-item `relevance = null`).

### Decay (`app\decay.py` — THE decay math, shared)
`tau_effective = tau_base × (1 + k·importance_raw)` (k = `decay_k_importance` 1.0);
`decay = 1 − exp(−age / tau_effective)`. Applies to **non-gist detail only** (decays to hidden);
**gist never decays**. Read-time only; original stays on disk; past state re-derivable.

### Reconstruction (`app\reconstruction.py`, `identity.py`) — the thesis mechanism
Mandatory read path for unpinned memories past **theta** (`reconstruction_theta` 0.5; theta reuses
the decay math — reconstruct when decayed detail strength < theta). Reconstructor sees: full gist
span (fixed constraint) + time-thinned detail slice + **the current live head** ("how you currently
tell it") — conditioned on the rendered identity document. **Serving:** Haiku-class, **one structured
call batching all k cache misses**; pre-warm at dialogue init; mid-scene miss → **block + expose a
"reconstructing" signal** (latency = characterization). **Write-back version chain:** each retelling
inserts a new `memory_details` row, supersedes prior. **Drift budget** (`drift_budget_threshold` 0.35
cosine): embed candidate vs anchor; past threshold → refuse, keep prior head. Anchor = latest chain
row with `write_cause ∈ {original, authorial_correction, update_with_resentment}`; `rationalization`
never re-anchors ("the story has set"). **Cache** keyed `(memory_id × identity_version)` where the
version component **composes identity_version with a quantized scene-frozen decay band**
(`reconstruction_band_quantum` 0.25) — the band keys the cache AND sets thinning level (the pre-demo
drift driver while identity is seed-only static). Cache-eviction invariant: any non-reconstruction
writer (correction/diegetic/purge) must evict all cache rows for that memory_id.

### Correction verbs
- **Authorial** (operator fixes wrong data): **replace model** — supersede the drifted chain with a
  corrected head (`write_cause = authorial_correction`) at t_c; **fact-following** (migration 002):
  corrected text is BOTH telling head AND embedded fact basis in one transaction (+ entities via NER
  merge per migration 003) → retrieval + entities follow the fix. Optional `expected_detail_id`
  compare-and-swap (stale → 409). Takes effect immediately, mid-scene. Corrected head becomes the
  reconstructor's fixed constraint. Embed failure = all-or-nothing fail-loud (502). Only embedding +
  entities follow; importance/typology/decay/affect stand as write-time event facts.
- **Diegetic** (in-world confrontation, references a target memory_id): preserves chain, routes
  through the dissonance path; new head `rationalization | update_with_resentment` + a corrections
  row. **Mechanism is post-August (not built).**

### Dissonance (designed, mechanism post-August)
Dissonance threshold = importance × evidence typology × per-NPC **rigidity**. Store always records
truth; the fork only shapes the character's reaction. Habituation guards (cap + decay) for the future
context term.

### Mid-dialogue gate (`app\gate.py` — non-LLM hybrid) (migration 003)
Conditional retrieval mid-scene. **Novelty check:** embed utterance (the turn's one embed IS the
probe), min cosine distance vs loaded set ≥ `gate_novelty_threshold` 0.5 → fetch. **Entity tripwire:**
uncovered mention of an identity-components entry → fetch (most demo-legible). Fetch appends
`gate_fetch_k` 3 new items. **Damper:** 2 consecutive fruitless fetches (zero new IDs) suppress
novelty for scene remainder; tripwire stays live; scene boundary resets. Loaded set = caller-held
scene state, append-only within a scene. **Degradation ladder:** embeddings down → entity-only off
the fact-head GIN ranked by recency×importance; no entities → novelty-only; both out → gate closed,
serve loaded set, fail-quiet. Fire logs are instrumentation-only (no `gate_events` table).

### Dialogue turn / behavior output (`app\dialogue.py`, `session.py`, `cli.py`)
**August ship:** a **single Sonnet call** emitting prose + structured action directive + reputation
delta. **Action directive** from integrator-supplied vocabulary; unknown → log/ignore, turn still
succeeds. **Reputation:** scalar on agent row; call emits a delta (client override wins), per-NPC
sensitivity, hard clamp; in-place atomic UPDATE; injected from a scene-start snapshot.
**Post-August target: multi-call split-brain** — a behavior call (own retrieval weights) chooses the
action; the dialogue call sees it **as observed world fact, never "you decided to."** Asymmetry is
**statistical (per-call scoring weights), not architectural (no masks)** — this is the
information-asymmetry research line. Surface: CLI REPL + a **synthetic load driver** (scripted
sessions at volume; emits latency p50/p95 decomposed into gate/retrieval/first-token/total + itemized
per-100-turn token/USD cost).

### Reflection & parameter compiler (designed, mechanism post-August — NOT built)
Reflection is an **endpoint** (no scheduler); store exposes **reflection pressure as a readable
gauge**; integrator pulls the trigger. Sampling: episodes weighted by **importance × recency**, not
recent-N. Reflection revises seed identity → flows into the rendered identity doc (bumps
identity_version) AND prunes the identity-components table. **Parameter compiler (later):** one call
per (reflection × scene-type), cached; bundle = typed clamped core (retrieval-weight multipliers,
action-set biases, stance priors) + namespaced passthrough; consumed only upstream of the dialogue
call. PSI/MicroPsi lineage.

### Instrumentation (`app\load_driver.py`)
Latency histogram p50/p95 (gate check / retrieval SQL / first token / total); gate efficacy per
signal; itemized per-100-turn cost. Structural pytest suite (38 scenarios, Stop-hook gate on the
`not nlp` subset).

---

## Known gaps / open questions / not-yet-built (fertile ground for "not yet built" findings)

- **No end-to-end evaluation harness.** Only a structural pytest suite exists — no LongMemEval-style
  accuracy/recall benchmark, no judged-drift / Bartlett-style eval, no memory-conflict or staleness
  eval. (Research track lists these; none built.)
- **Reflection pipeline** — designed, not built (sampling, identity revision, components pruning).
- **Parameter compiler / reflection→params** — designed, not built.
- **Diegetic correction + dissonance mechanism** — schema live, mechanism not built.
- **Multi-call split-brain cognition** — designed post-August, not built (only single-call today).
- **Purge endpoint** — contract only.
- **Prompt caching / prompt-head rebuild** — deferred.
- **Encoding-context read term + habituation** — reserved slots only.
- **Reflection sampling strategy** beyond importance×recency — undesigned.
- **Cross-observation coreference** — accepted as graceful failure (detail just decays).
- **Identity document is seed-prose-only** until reflection lands (static; the decay band is the only
  drift driver pre-demo).
- **Gist escalation failure path for production** — the sole flagged open ruling (hard-stop vs soft
  degrade).
- **No graph / associative structure** over memories (no entity graph, no linking beyond
  identity-components + gist spans + entities[]). No multi-hop retrieval.
- **No hierarchical/schema memory** (episodic only; no consolidation into semantic summaries beyond
  reflection-as-endpoint).

---

## How to phrase a finding (so the reduce step can use it)

For each candidate, name (a) the exact component above it touches, (b) our current mechanism, (c) the
paper's mechanism with a page/section ref + a short quote, (d) *why* it is strictly better OR why it
is genuinely new, (e) adoption cost/risk in OUR stack (Postgres/no-ORM/1536-locked/non-destructive),
(f) which `docs\` file it would touch. If it conflicts with an invariant above, mark it
**THESIS-TENSION** and explain the conflict honestly rather than dropping or forcing it.
