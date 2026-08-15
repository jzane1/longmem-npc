# longmem-npc — Test suite spec

**BUILT 2026-07-20 — 128 pytest scenarios today** in `tests\test_*.py` (Sets A–D + degradation +
hygiene + eval metrics + eval runner + judge + ablation + deferred writes + reflection; the
Set A diegetic pair still lands with the dissonance mechanism). Count as of 2026-08-15: Set A 8,
Set B 7, Set C 7, Set D 20, degradation 12, hygiene 2, Set G eval metrics 8, **Set H eval
runner 9** (stage 2, 2026-08-05), **Set I judge 16** (stage 3, 2026-08-07; +2 with the
2026-08-12 workaround session; the reflection role's load-rule amendment rides the existing
config scenarios, 2026-08-15), **Set J ablation 6** (stage 4, 2026-08-12 — its section is
`eval-harness.md`'s stage-4 block), **Set K deferred writes 13** (Phase C1, 2026-08-12),
**Set L reflection 20** (Phase C2, 2026-08-15) — grown from the 38 built on 2026-07-20 by the
route-contract scenarios that arrived with each later route, by the gap-closing and guard
scenarios from the full-repo audit, and by the eval harness stages 1–4. **Fourteen carry the
`nlp` marker** (Set L adds none), so the turn-end subset runs **114**. *(Counts corrected
2026-08-12 with the Set K landing — the 2026-08-07 header had drifted again by the stage-4 and
workaround-session scenarios.)* Build rulings 2026-07-20
(dated `decisions.md` entry): the suite-gate Stop hook runs the `-m "not nlp"` subset (the 7
`nlp`-marked scenarios call the write pass at the service level and pay the lazy
spaCy+fastcoref load; the full suite runs on demand + at floor verification); Postgres
unreachable ⇒ loud clean skip, exit green; **CI-ready now** (offline, keyless, deterministic,
self-managed scratch `longmem_suite`) with the CI workflow itself sequenced later — "runs in
CI" below reads as that readiness until the workflow lands.

Scenario suite in `tests\`: fixture + runner, runs in CI. The suite gets its own scoped build
session — it is a first-class deliverable, not an afterthought.

## The one rule

**Structural-only.** Assert on memory IDs, row types (`write_cause`, `read_mode`, typology), chain
shape, cache state, timestamps, and byte-identity of returned text — **never on generated prose.**
A model's wording is not a test surface. Judged evals (drift-toward-identity, Bartlett-style
distortion operators) belong to the eval story and the paper ablations, not this suite.

Corollary that makes this possible: read endpoints that run retrieval return memory IDs and scores
alongside prose. That contract is load-bearing; if an endpoint stops returning IDs, the suite is
dead. *(The three unscored-by-contract reads — `/chain` and `/agents/{id}/memories`, ruled
2026-07-27, and `/memories/{id}/reconstruction-metrics`, the third member 2026-07-29 — run no
retrieval and are unscored by contract; they still carry IDs and structured fields on every row,
which is what their scenarios assert.)*

## Set A — correction-override (~15 scenarios)

Forked into **structural pairs by correction verb**, keyed on `write_cause` — no fixture mode.

- **Authorial pair (replace model, ruled 2026-07-12):** prior head superseded (`invalid_at` set);
  exactly one new head row typed `authorial_correction`; cache rows for the memory_id evicted; the
  memory ID **present** in retrieval candidates, serving the corrected head; the drift anchor now
  resolves to that head; post-correction reconstruction takes the corrected head as its **fixed
  constraint** (pure prompt-assembly assertion — ruled 2026-07-17); a mid-scene correction changes
  served text immediately (the amended invariant's sanctioned cause); no `corrections` row.
  **Fact chain (specced & built 2026-07-18, `fact-level-correction.md`):** prior fact head superseded;
  one corrected fact head with `basis_text` byte-identical to the operator input and the
  corrected embedding; the superseded fact row still carries the original embedding; **the
  memory ranks by the corrected embedding** *(asserted at the db layer, where order is pure
  distance — a service-level rank assertion would hang on hash-derived fake importance; see the
  spec's done-when)* — assertable via the fake-mode distance-0 mechanic (the deterministic fake
  embedding is a pure function of text, so probe text == stored basis ⇒ cosine distance 0; a
  *fixture* property — production uses real embeddings).
- **Diegetic pair:** chain intact; new head row typed `rationalization` or
  `update_with_resentment`; correction record present; cache evicted. *(Lands when the dissonance
  mechanism ships.)*

## Set B — decay-only (~5 scenarios)

Exercise injected `valid_at` timestamps (time travel) to prove **recency decay and bi-temporal
invalidation are structurally distinct mechanisms**: decay hides detail at read time without
touching rows; invalidation stamps rows without touching decay. *(Per the 2026-07-14 read-path
serving ruling, the pre-reconstruction assertable surface is the recency score component — decay
moves scores, not rows; detail-hiding assertions land with reconstruction.)*

## Set C — identity-conditioned reconstruction (~7–9 scenarios)

- Gist span rows are immutable.
- A write-back inserts a new head and supersedes the prior row **under the same memory_id**.
- Identity-version bump ⇒ cache miss; stable identity **+ same decay band** ⇒ cache hit *(ruled
  2026-07-17: the cache key's version component composes `identity_version` with the scene-frozen
  thinning band — `reconstruction.md`)*.
- Same `(memory_id, composed cache key)` returns **byte-identical text**.
- Pinned memories never grow reconstruction chain rows and always read verbatim.
- Correction verbs evict caches, and cascade or preserve the chain per the two-verb ruling.
- The drift bound is enforced (over-threshold candidate write is refused; prior head kept).
- Within-scene text stability: absent a diegetic event, an authorial correction on that memory
  (amended 2026-07-17), or a deferred-enrichment completion (the third sanctioned cause, amended
  2026-08-12 — `deferred-writes.md`), repeated reads within one scene are byte-identical.

## Set D — mid-dialogue gate (~8–10 scenarios) *(specced & built 2026-07-19, `mid-dialogue-gate.md` — the 51-assertion walker covers these)*

- **Loader-parity:** a request without `loaded_memory_ids` behaves byte-identically to v1
  (payload shape and SQL).
- **Closed gate:** a covered, near-loaded utterance serves exactly the loaded IDs — zero probe
  SQL, `signals_fired == []`, relevance non-null on every embedded item (a NULL-embedding
  loaded row carries `relevance = null`), deterministic order.
- **Novelty fire:** a far utterance fetches, appends only new IDs marked `gate_fetched`, logs
  exactly `["novelty"]` *(the deterministic fake's locality is a fixture property — production
  uses real embeddings)*.
- **Tripwire fire + covered suppression:** an uncovered live-component mention fires
  `["entity_tripwire"]` and the fetch contains the entity; the same mention covered by a loaded
  item's fact-head entities does not fire.
- **Both-signal logging:** far + uncovered logs both constants; every fire event carries
  non-empty `signals_fired`.
- **Append + byte-stability:** the loaded set is append-only within a scene; a gate-fetched
  item's text is byte-stable from its first mid-scene serving onward (the invariant governs
  served *text* — which memories surface was never under it).
- **Damper + reset:** the ruled max of consecutive fruitless fetches suppresses novelty (the
  tripwire stays live); a scene boundary resets streak and suppression.
- **Efficacy booleans:** `novelty_outscored` / `entity_covered` populate per the ruled
  comparators on fire events.
- **Entities-follow-correction pair (migration 003):** a correction moves the fact head's
  entities (NER + optional operator field, merged); windowed SQL re-derives entity liveness at
  any instant; superseded fact rows keep their entities.

## Set E — dialogue-turn topology *(built 2026-07-21 as the split-brain set; REWRITTEN by the
A1 re-shape 2026-08-04 — the behavior/reputation/recent-actions claims died with their
mechanisms)*

*Landed as scenarios inside `test_set_d_gate.py` and `test_degradation.py` rather than a file of
its own — the weights and degradation claims share Set D's fixtures. The CLI-harness walker
(rewritten to 51 assertions) carries the seam-level proofs.*

- **Weights-on-speech parity:** at default weights `dialogue_view` is byte-identical to the
  (id, score) projection of `items` (loader turn — the parity contract).
- **Weights-on-speech re-rank:** an override re-scores the SAME served set; the seam's view
  equals a recomputation through the pure weight functions, and the prose prompt's `[memories]`
  block renders in the re-ranked order (asserted by ID extraction — structural, never prose).
- **Raw-echo invariance:** `items` stays the untouched retrieval echo under any override —
  the read path has no weights surface.
- **Zero persistence:** a dialogue turn writes nothing; `agents.reputation` stays NULL through
  provisioning and every turn.
- **Degradation rows:** prose-fail pre-token -> fallback line + degraded, the served view still
  on the result; mid-stream drop -> partial kept (ruled 2026-07-21); never-blank holds.

## Set F — repo hygiene *(added 2026-07-28 with the full-repo audit)*

Two pure scenarios in `tests\test_repo_hygiene.py` — no database, no NLP, ~0.1 s, so they ride the
turn-end subset. Each makes an already-written rule mechanically enforceable, and each exists
because the rule had already been broken once:

- **`test_no_version_gated_syntax_rewrites`** — no file under `app\`, `db\` or `tests\` uses
  syntax newer than the grammar floor. The canary: ruff's formatter applies PEP 758 when
  `target-version` is py314 and silently rewrites `except (A, B):` across the tree.
  `ruff.toml` leaves `target-version` unset to prevent exactly that — and on 2026-07-28 that
  comment was committed alongside a file the hazard had already rewritten. Neither `ruff check`
  nor `ruff format --check` flags it.
- **`test_no_sql_outside_the_db_module`** — `app\db.py` is the only module in `app\` containing
  SQL (a stack constant, and what keeps the injection surface auditable in one file).
  `app\load_driver.py` had violated it with a hand-rolled INSERT.

## Set G — judge-free eval metrics *(added 2026-07-29 with eval-harness.md stage 1)*

Eight scenarios in `tests\test_eval_metrics.py`, two layers matching the build:

- **Pure arithmetic (5, unmarked, no database — the Set F precedent):** anchor-cause-aware gist
  facts (merged-span slices; correction anchors sentence-split and owe no detail); the
  `metric_gist_match_threshold` presence rule; **honest denominators** — empty/unmeasurable
  denominators return `None`, never a flattering 1.0; whole-word fabrication grounding + rate;
  keyword retention; the composed-cache-key band parser round-trips `compose_cache_key`.
- **Route contract (3, `nlp`-marked — any 200 runs the spaCy lemma/NER block):** 200 payload with
  exact ratios against fixture tellings (db-layer writes, never model prose — the values are
  byte-known, so asserting them IS structural); zero-span memory reports `gist_precision: null`;
  404 unknown memory; the anchor-cause contract end to end (correction → gist IS the corrected
  head; a reconstruction head on top → anchor unchanged, cache band parsed, never-observed entity
  flagged fabricated, gist violation reads 0.0); and the **non-perturbation pair** — a metrics
  read leaves `/chain` identical (per-call `total_ms` timing field excluded) and the telling
  chain / reconstruction cache / identity documents count-stable (the identity render is pure,
  never the `ensure_` upsert).

Judged and LLM-graded evals still do NOT live in this folder — they arrive with the eval
*runner* (eval-harness.md stages 2–3) as a separate surface. This set is the metric
*arithmetic* and the route, which are structural.

## Set H — eval runner *(added 2026-08-05 with eval-harness.md stage 2; section written
2026-08-07 clearing the propagation debt)*

Nine scenarios in `tests\test_eval_runner.py` (8 unmarked + 1 `nlp`): the committed fixture
census canary (fixture drift fails here, not at demo time); scenario-loader strictness
(`extra="forbid"`, backward-only refs, tz-aware timestamps, `path:line` context, duplicate-id
rejection); `check_expected` membership arithmetic; the product-DB hard refusal by NAME against
a TEST-NET host (no dial-out) + the `scratch_uri` shim identity; the provision/drop round-trip
(migrated to exactly the ledger's five); the `drift_observer` seam (default `None`, happy path,
refusal path — attaching it perturbs nothing the Set C floor asserts); and the `run_scenarios`
end-to-end in-process on scratch settings (`nlp` — drives the real write pass): report
structure, honest-`None` ratios, keyless USD `None`, JSON-serializable artifact, and the
no-eval-tables proof. Never asserts on prose.

## Set I — the judge layer *(added 2026-08-07 with eval-harness.md stage 3)*

Sixteen scenarios in `tests\test_set_i_judge.py` (15 unmarked + 1 `nlp`) — the stage-3
MECHANICS with the deterministic fake judge, never judged signal (which is real-mode-only and
quotable only past the agreement bar):

- **The ruling as a regression test:** real mode loads WITHOUT `LONGMEM_MODEL_JUDGE` (never in
  the required-roles list); both modes load it when present; judge prices and the
  `LONGMEM_JUDGE_MAX_TOKENS` knob parse with loud `ConfigError`s.
- **The thinking knob:** value validation (`""`/`"disabled"` only), the exact request-kwargs
  shapes (`""` ⇒ `{}` — the pre-B2 call byte-for-byte), and the process-env override allowlist
  for all three new keys.
- **Fake-judge determinism** (byte-identical payloads, all four categories validate under the
  verdict models); **verdict validation + per-item `judge_failed` degradation** (Malformed
  carries its 7/3 token spend, Failing carries zero, the run continues); **rubric constants**
  (four categories, unique version tags, the JSON-only output contract).
- **Position-swap tie arithmetic** (un-swap, disagreement ⇒ tie, score averaging);
  **hand-computed Cohen's kappa** (po 0.7 / pe 0.5 ⇒ exactly 0.4; perfect ⇒ 1.0; degenerate
  marginals and empty inputs ⇒ honest `None`); **Pareto non-domination** incl. `None`-metric
  incomparability.
- **The `--judged` fake-mode gate** (exit 2 BEFORE any provisioning or file access);
  **arm-overlay loading** (env-dict merge through `load_settings`; mode/database/key/judge
  overrides refused; committed arm files as a canary); **the gold emit → label → agreement
  round trip** (verdicts stripped — labels are blind; `judge_failed` skipped; hand-filled
  labels reproduce the hand-computed kappa and the bar's exit codes); **judged fixture census**
  (`judged.jsonl`: 8 scenarios, 24 sf + 24 abstention, every abstention trio carrying a
  true-premise control for kappa balance).
- **The compare plumbing end-to-end** (`nlp` — scratch settings, fake providers + fake judge):
  stamped arm blocks, judged summaries incl. reconstruction-faithfulness on the aged probe's
  retellings, deterministic pairwise verdicts, the Pareto table with honest-`None` USD,
  `plumbing_only` label, JSON-serializable report. Never asserts on prose.

## Set K — deferred write processing *(added 2026-08-12 with Phase C1, `deferred-writes.md`)*

Thirteen scenarios in `tests\test_deferred_writes.py` (12 unmarked + 1 `nlp`). Unmarked
scenarios seed pending rows at the db layer (`Ctx.seed_pending`: NULL write-call scalars, raw
text as the `original` head, persisted trigger names) and exercise the worker through
`drain()` — the deterministic entry, no timers, no spaCy:

- **Completion happy path:** one-shot NULL→value scalar fill, the raw head superseded by the
  `'enrichment'` head, cache evicted, a `completed` run row — and a **re-drain is a 0-row
  no-op with the chain byte-stable** (idempotency by the `enrichment_pending` guard).
- **COALESCE proof:** a declared typology stored at insert survives completion untouched.
- **Escalation novelty:** a novel component grows `identity_components` + its mention appends
  as an add-only span; **no fact supersede** (sync parity — novels become components, never
  memory entities).
- **Retry-later:** a failed write call records a `failed` run row and leaves the row pending;
  the next drain completes it. **Terminal:** the budget-spending attempt fills the row
  byte-equivalent to the sync scoring-failed end-state (neutral importance + `scoring_failed`
  + default typology; raw head stays live). **Orphan sweep:** a pending row with a spent
  budget terminal-fills without model calls.
- **Facts-only:** a retelling that superseded the raw head first → scalars fill, prose
  supersede SKIPPED, cache still evicted, `completed_facts_only`.
- **Embedding repair:** a NULL-embedding pending row gains an `'enrichment'` fact version
  carrying the vector; the superseded original stays honestly NULL, `basis_text` byte-verbatim.
- **Anchor set:** post-completion `fetch_reconstruction_sources` anchors on the enrichment
  head. **/chain contract:** pending flag + attempts + the run log surface on the unscored
  inspector read (wording untouched). **Window reachability:** a pending row is
  vector-reachable with true relevance, scores under the neutral fallback, serves raw text
  verbatim.
- **`salvage_confidence` semantics** (the 2026-08-12 parse-seat ruling): non-numeric/NaN →
  None, out-of-range → clamped, in-range untouched.
- **End-to-end** (`nlp`): an enabled agent's observe lands pending with honest zero LLM
  instrumentation → drain → enriched.

The eighth walker `tests\verify_deferred_writes.py` (51 criteria) covers the migration-006
shape, kill-switch parity, the full ladder at service level, and the worker lifecycle at both
construction sites; the write-path walker staying byte-identical at 53/53 is the deferred-OFF
parity evidence.

## Set L — reflection *(added 2026-08-15 with Phase C2, `reflection.md`)*

Twenty scenarios in `tests\test_reflection.py`, ALL unmarked. Memories and prior beliefs seed
at the db layer (`Ctx.seed` / `Ctx.seed_reflection`); the seam runs through
`ReflectionService.reflect` and the worker through `sweep()` — deterministic, no timers, no
spaCy. The pipeline's time basis is the request's `client_timestamp`, so the clock freezes by
freezing the request (the `as_of` precedent):

- **Happy path:** grounded bi-temporal rows at the request's `valid_at` (citations non-empty
  and ⊆ the sampled ids), pressure before/after served, honest instrumentation, the
  re-rendered document carrying the identity-relevant belief byte-for-byte; the endpoint
  writes NO run row (the C1 endpoint/worker split).
- **Sampling:** deterministic top-k by importance_norm × recency, ties on `memory_id`; a
  pinned ancient row takes the PLAIN decay score (pin keeps exactly two meanings — reflection
  is neither) and falls out of the sample a `rec = 1.0` arm would have topped.
- **Grounding:** a partial drop stores the valid subset (`dropped_ungrounded` counts);
  all-ungrounded is the 502 class with zero rows; call-failure and malformed land the same
  way; a genuinely empty conclusion list is a VALID outcome.
- **The floor:** below `reflection_min_episodes` the 409 class, zero rows; unknown agent 404.
- **RRR:** a near-duplicate repeat blocks consolidation (even under a `consolidate=true`
  override) while the reflections still store; the threshold pins inert (>1) in the scenario
  that isolates the override arm (the fixture-pin discipline).
- **Consolidation:** absorbs bi-temporally (`invalid_at`, rows stay queryable), provenance =
  the source union, the version bumps, the document carries the belief and not the absorbed
  rows; `consolidate=false` suppresses when due; a consolidation-call failure is SOFT — the
  step-7 writes stand.
- **Trim:** the 3-clause mechanical rule under the frozen clock (a component with all-stale
  span evidence prunes by `invalid_at`, never DELETE); the authored (zero-span) and
  active-evidence exemptions hold; 0.0 disables the trim entirely; eviction is
  per-affected-memory only; `fetch_live_components` shrinks; `fetch_reconstruction_sources`
  drops the pruned spans; no-trim byte parity.
- **The dialogue seam:** zero reflections ⇒ seed-verbatim render, the pre-C2 version and a
  byte-identical prose prompt; after a belief + recompile the `[identity]` block carries it;
  an unknown `identity_version` stays the loud 422 class.
- **The worker:** sweep determinism, the per-agent kill-switch (gates auto-pull only), at
  most one reflect per agent per sweep, pressure consumed by the reflect event, `failed` run
  rows + natural retry (NO attempts ledger — the deliberate contrast with enrichment), the
  below-floor skip writes no row, idempotent start/stop.
- **Pressure math:** exact masses incl. the NULL-importance neutral fallback and
  absorbed-rows-still-mark-the-last-event; the zero-norm guard is loud, never a clamp.
- **Role shape:** real mode loads WITHOUT `LONGMEM_MODEL_REFLECTION` (the Set I load-rule
  amendment asserts `load_settings`); the first real reflect raises `ConfigError` naming the
  var, nothing written. **Route contracts:** 200/404/409/422/502 via the ASGI-transport
  pattern.

The ninth walker `tests\verify_reflection.py` (60 criteria, lettered sections A–F) covers the
migration-007 shape, the reflect verb ladder, render/consolidation/dialogue-seam parity, trim
+ liveness + eviction, the worker lifecycle at both construction sites, and the judge-shaped
role surface; the write- and read-path walkers staying byte-identical at 53/56 are the
zero-retrieval-change evidence.

## Route contracts *(added as each route shipped; consolidated here 2026-07-28)*

Every route in `app\api.py` has at least one HTTP-level scenario asserting its success payload,
and most also assert their mapped error statuses — the C# client depends on both. They live
wherever their fixtures do: mostly `tests\test_set_d_gate.py` (via `httpx.ASGITransport`), with
init in `test_set_b_decay.py`, correction in `test_set_a_correction.py`, the NER-502 row in
`test_degradation.py`, and the walkers' own route sections.

**Known gap:** `POST /v1/dialogue/init`'s 404 / 422 mappings are the one pair asserted nowhere —
its HTTP coverage is the byte-identity read pair and the walker's pass-through check. Listed here
rather than quietly implied by "every route", because that is what this section is for.

- `POST /v1/dialogue/init` · `POST /v1/dialogue/turn` (route JSON == the drained seam result;
  404/422) · `POST /v1/dialogue/turn/stream` (200 `text/event-stream`; chunk events concatenate
  **byte-identically** to the result's content; `reconstructing` fires once before any chunk on a
  gated turn with a blocking retelling; a post-first-chunk failure arrives as an `error` EVENT,
  since a 200 stream cannot change status; pre-stream 404)
- `POST /v1/events/observe` · `POST /v1/events/scene-boundary` (accepted + identity_version; 404)
- `PUT /v1/memories/{id}/pin` (row moves both directions; 404) ·
  `POST /v1/memories/{id}/correction` (404/409/422/502)
- `POST /v1/agents` (server-minted UUID, NULL knobs resolve; 422 on empty name)
- `GET /v1/memories/{id}/chain` · `GET /v1/agents/{id}/memories` (unscored by contract; superseded
  rows present; 404) · `GET /ledger`
- `GET /v1/memories/{id}/reconstruction-metrics` (IDs + counts + ratios, honest-`None`
  denominators, zero writes; 404) — `tests\test_eval_metrics.py`

## Degradation cases

- Importance-scoring model failure → the write still lands, with neutral importance and a
  `scoring_failed` flag.
- Unknown `decay_class` label → the write still lands, with the agent's default class and
  `decay_class_unknown = true` — never rejected (ruled 2026-07-13; mirrors `scoring_failed`).
- Embedding-call failure → the write still lands with a NULL embedding; `embedding IS NULL` is the
  queryable signal and the payload carries `embedding_failed` (ruled 2026-07-13; since the
  2026-07-18 freeze ruling the signal's home is the live fact head —
  `memory_fact_versions.embedding IS NULL`).
- Embedding-call failure during an **authorial correction** → **all-or-nothing**: nothing written
  on either chain, cache intact, loud error (ruled 2026-07-18 — the deliberate contrast with the
  observe path's land-with-NULL degradation; `fact-level-correction.md`).
- **NER failure during an authorial correction** → **all-or-nothing**, same shape: the NER runs
  before the embed and before the transaction, so nothing lands on either chain and the cache is
  untouched; `CorrectionNlpFailedError` → **502** (ruled 2026-07-19 with the gate build, taking
  the embed precedent's shape). *(Row added 2026-07-28: the path was ruled and built but had no
  spec row and no test — closed by `test_correction_nlp_failure_all_or_nothing`.)*
- Escalation call fails twice → **SOFT-DEGRADE**: the write lands with the base NLP-pass gist and
  `escalation_failed = true` (result + the dedicated column, migration 005) — structurally assertable
  as a row present + the flag set (re-ruled 2026-07-22, retiring the 2026-07-13 hard-stop).
- Gate degradation ladder: embeddings down → entity-only lexical fetch; no entities → novelty-only;
  both out → gate closed, loaded set served, fail-quiet. *(Specced & built 2026-07-19: the lexical fetch
  reads the post-003 fact-head entities GIN — `mid-dialogue-gate.md`.)*
- Malformed model responses → log, ignore, turn succeeds. *(The unknown-action-directive case
  died with the directive — A1 re-shape, 2026-08-04.)*
