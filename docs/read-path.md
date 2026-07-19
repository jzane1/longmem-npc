# Read path — dialogue-init retrieval v1 build target

Third build target, on top of the migration-01 schema and write path v1. This specs the **retrieval
half of the read path** (*dialogue init → top-k memories with IDs + scores*), exposed as one
retrieval service. Design truth is [architecture.md](architecture.md) §4.2 + §6; the rulings behind
it are in [decisions.md](decisions.md); the schema it reads is frozen in
[migration-01.md](migration-01.md). This doc points, it does not re-derive.

> **Status: BUILT & floor-verified 2026-07-14.** Every `[SETTLE-AT-BUILD]` item below was ruled at
> build time (dated "Read-path build rulings" entry in `decisions.md`); the rulings are annotated
> inline. One build ruling supersedes a spec suggestion: **importance_norm is clamp + floor, not
> min-max** (min-max would have let an invalidated extreme row move other items' scores, breaking
> this spec's own Set B principle). **The build added no new DB migration — the migration-01
> schema stayed frozen.** Two scope forks had been ruled at spec time (dated "Read-path spec scope
> rulings" entry in `decisions.md`): query input = **text + reserved context**; v1 serving =
> **verbatim-only**. The surface was already fixed by the 2026-07-14 re-slating ruling:
> retrieval-only — the Sonnet dialogue call rides with the CLI harness (built 2026-07-15).
> Reconstruction **landed on this seam 2026-07-17** (`reconstruction.md` — the serving boundary
> below held; retrieval and scoring were untouched by the swap, as drawn).

## Principles this build honors

- **IDs + scores in every payload.** Every returned memory carries its `memory_id`, served
  `detail_id`, score + components, `read_mode`, and `pinned` alongside prose. Load-bearing: the
  test suite dies without it (architecture §6, `test-suite.md`).
- **Recency decay and bi-temporal invalidation are distinct mechanisms** — and this build makes the
  distinction *assertable*: decay moves score components without touching rows; invalidation
  excludes rows without touching other items' scores (Set B).
- **Importance vs relevance are independent axes.** Importance was scored once at write (stored
  raw); it is normalized here, at read. Relevance is computed per query.
- **Single instrumentation seam, two thin callers.** One retrieval service carries the timing and
  token accounting; the CLI (in-process) and the FastAPI route are thin callers, the route a
  pass-through — mirrors the write-path surface ruling (2026-07-13).
- **Nothing integrator-configurable is hardcoded** — top-k, decay knobs, scoring shapes: service
  defaults in `app\config.py`, per-agent overrides via `agents.config` (the existing `agent_knob`
  pattern).
- **Degradation is named per model call.** The one model call here (query embedding) has a stated
  fallback (ladder below).
- **Within-scene text stability.** Verbatim heads make byte-identity trivially hold in v1; the
  serving boundary must preserve the invariant when reconstruction attaches.
- **Instrument at the seam** — per-stage timings feed architecture §11's latency decomposition.

## Scope boundary — do NOT build

The mid-dialogue gate (and its degradation ladder); prompt caching; **reconstruction serving —
theta check, cache reads/writes, pre-warm, `reconstructed` read_mode** (landed on this seam
2026-07-17, `reconstruction.md`); the dialogue/Sonnet call, action directive, reputation
(CLI-harness target, built 2026-07-15);
correction endpoints; purge; reflection; the encoding-context scoring term (its request fields are
**reserved only**); per-call weight overrides (**slot reserved only**); and **any new DB schema or
migration**. If adjacent work looks necessary, **stop and report** rather than expand scope.

## The retrieval service (the seam)

One entry point, both callers sit on it:

```
retrieve_dialogue_init(request: DialogueInitRequest) -> RetrievalResult
```

- The **CLI harness** calls it in-process; the **FastAPI route** is a thin wrapper whose JSON
  response is exactly the serialized `RetrievalResult` (route-is-pass-through, as proven for the
  write path). Timing + token accounting recorded once, at the service seam.
- **This is where reconstruction attaches** (architecture §7: pre-warm at dialogue init):
  reconstruction (built 2026-07-17) wraps the *serving* stage below; retrieval and scoring were
  untouched by that swap, as promised here.

### Serving boundary *(ruled 2026-07-14: verbatim-only v1)*

Retrieval (candidates + scoring) is a separate stage from serving (text assembly + read-mode
stamping). **v1 serving:** the live `memory_details` head's `content`, verbatim;
`read_mode = "verbatim"` on every item; `pinned` mirrored from the row. The architecture's
three-state read-mode boundary (§6) collapses to one state in v1 because no reconstructor exists —
honest self-description, never a claimed mechanism. Reconstruction (built 2026-07-17) swaps
serving only: theta check
(reusing the decay math below), cache read keyed `(memory_id, identity_version)` *(refined
2026-07-17: the key's version component composes `identity_version` with the scene-frozen decay
band — `reconstruction.md`)*, batched
reconstruction on miss, `read_mode = "reconstructed"` past threshold.

## Request contract — `DialogueInitRequest`

| Field | Meaning |
|---|---|
| `agent_id` | target NPC (FK → agents). |
| `query_text` | **required** — the relevance probe, embedded **as-is** (ruled 2026-07-14: the integrator authors it — opening utterance or scene blurb; the service never composes prose; a template would be a hidden hardcoded authorial artifact). |
| `k` | optional; default = integrator knob (per-agent via `agents.config`, service default in `app\config.py`). |
| `location_name` / `entities[]` / `event_time` | **RESERVED** (ruled 2026-07-14): accepted and shape-validated, **not consumed by v1 scoring, not echoed** — slots for the post-August encoding-context term, mirroring three of the four write-side context stamps. **Affect is deliberately not reserved** (ruled 2026-07-14): a query-side affect field's shape — and whose affect it would carry — is undesigned; it gets its shape with the encoding-context term rather than as a guessed slot. Documented inert (hostile-integrator discipline: per-field behavior stated). |
| `weight_overrides` | **RESERVED** slot for per-call split-brain scoring overrides (post-August): accepted, not consumed, not echoed. `[SETTLE-AT-BUILD]` exact shape — **ruled 2026-07-14 as suggested:** `{relevance, recency, importance}` optional float multipliers. |
| `as_of` | optional world-time override for age computation (time-travel / Set B test surface). `[SETTLE-AT-BUILD]` — **ADOPTED as suggested (ruled 2026-07-14):** tz-aware timestamp, defaults to server now (UTC), surfaced in instrumentation as `as_of_effective`; `tests\CLAUDE.md`'s time-travel line carries the second mechanic. |

## `RetrievalResult` — the structured payload

Ranked items (≤ k), each carrying:

- **Identifiers** — `memory_id`; `detail_id` of the **served live head** (makes Set A's
  corrected-head-served assertion payload-visible).
- **Prose** — `content`: the live head's text, verbatim (v1 serving ruling).
- **Read-mode boundary** — `read_mode` (`verbatim` in v1) + `pinned`, per architecture §6's
  self-describing payload requirement.
- **Scores** — `score` plus its components: `relevance`, `recency`, `importance_norm` (and
  `importance_raw` for the debug view).

Result-level:

- **Instrumentation** — per-stage timing (`embed_ms`, `sql_ms`, `score_ms`, `total_ms`),
  query-embedding token count, `candidate_count`, effective `k`, `degraded` flag (+ reason), and
  the effective `as_of`. Feeds architecture §11's histogram decomposition; surfaced verbatim in
  the CLI debug view.

## Candidates & bi-temporal read semantics

- Candidates are the agent's **live memories** (`memories.invalid_at IS NULL`). Served text comes
  from the unique live head (`memory_details.invalid_at IS NULL` — the one-live-head index
  guarantees uniqueness).
- Invalidation **excludes** a row from candidacy; decay only moves the recency component. That is
  the Set B separation, assertable in payloads.
- Rows with **NULL embeddings** (the write path's ruled degradation) are unreachable by the vector
  probe — a documented consequence. They remain reachable via the degraded fallback below, and
  later via the gate's entity/GIN path (item 1 since the 2026-07-18 renumber). *(Fact-level correction built 2026-07-18,
  `fact-level-correction.md`: the probe joins the **live fact-version head** and orders by its
  embedding — this floor was deliberately re-opened and re-verified, walker 34 → 36 by addition;
  scoring inputs otherwise unchanged.)*

## Retrieval scoring

Per the register sketch (settled decision, shapes settle at build):

```
score = relevance × recency(decay class) × importance_norm
```

computed at read time, returned per item with all components.

- **Relevance** — cosine similarity via the HNSW index (`vector_cosine_ops`, locked 1536).
  `[SETTLE-AT-BUILD]` distance→similarity mapping — **ruled 2026-07-14 as suggested:**
  `clamp(1 − cosine_distance, 0, 1)`; SQL shape: over-fetch `max(k, ceil(factor × k))` candidates
  by vector distance over live rows with non-NULL embeddings, re-rank by full score; knob
  `retrieval_overfetch_factor`, default 4.0.
- **Recency** — reuses the decay math (architecture §4.2), one implementation later shared by the
  theta check: `tau_effective = tau_base(decay_class) × (1 + k_importance × importance_raw)`;
  `recency = exp(−age / tau_effective)`; `age = as_of − valid_at`. `tau_base` from the agent's
  `decay_classes` config map; rows flagged `decay_class_unknown` use the default class (same rule
  as write). `[SETTLE-AT-BUILD]` — **ruled 2026-07-14:** knob `decay_k_importance`, default 1.0;
  shared `tau_effective` **confirmed** — one formula, one implementation (`app\decay.py`, which
  the reconstruction theta check imports — landed 2026-07-17); age clamps at ≥ 0; a label resolving to neither the map nor
  a default class takes the `tau_fallback_seconds` knob (default 604800) — a read never fails on
  a resolvable row.
- **importance_norm** — normalized at read from stored raw. `[SETTLE-AT-BUILD]` method —
  **ruled 2026-07-14: clamp + floor, superseding this spec's min-max suggestion:**
  `clamp(importance_raw, importance_norm_floor, 1.0)`, floor default 0.05 (never zeroes a memory
  out of existence). Min-max over live rows was rejected at build: invalidating an extreme row
  would move *other* items' scores, breaking the Set B principle above; raw is already
  contractually 0..1 from the write call.
- **Pin exemption** — pinned rows take `recency = 1.0` (pin = decay exemption, architecture §8;
  pin's second meaning, reconstruction exclusion, landed 2026-07-17).
- **Normalization** — `[SETTLE-AT-BUILD]` — **ruled 2026-07-14 as suggested:** each component in
  [0,1] so the product is in [0,1]; no further rescaling. Ties in the final ordering break on
  `memory_id`, so repeated identical calls are byte-identical.
- **Reserved slots** — the encoding-context term multiplies in post-August; per-call
  `weight_overrides` apply under the split-brain topology. Neither is consumed in v1.
- **`scoring_failed` rows** flow through normally (importance was neutral at write; no read-time
  special case).

## Degradation ladder (read)

| Condition | Behavior |
|---|---|
| query-embedding call fails | `[SETTLE-AT-BUILD]` — **ruled 2026-07-14 as suggested: fail-quiet fallback** — rank all live candidates (including NULL-embedding rows) by `recency × importance_norm`, return with `degraded = true` + reason; the per-item `relevance` component is null on this path (none was computed). Precedent: the gate ladder's embeddings-down rung ranks by recency × importance; the read analog of never-lose-a-write is **never-blank-a-dialogue**. |
| stored row has NULL embedding | absent from vector candidates (documented consequence); reachable via the degraded path now and the gate's GIN path later. |
| fewer than k live memories (or none) | `[SETTLE-AT-BUILD]` — **ruled 2026-07-14 as suggested:** return what exists (0..k items), not an error; an empty store is a valid young-NPC state. |

## Model provider interfaces

Retrieval is **non-LLM** — no new model role, no new env var. The one model call is the **query
embedding**, which reuses the write path's embedding provider pair as-is: real
`text-embedding-3-small` at the locked 1536, and the **deterministic fake** (so the structural
suite runs offline, keyless, with stable scores). The probe embeds with the same model+dimension
that embedded the observations. (The gate, also non-LLM, arrives at item 1 — renumbered 2026-07-18; reconstruction's model
role, `LONGMEM_MODEL_RECONSTRUCTION`, landed 2026-07-17.)

## `[SETTLE-AT-BUILD]` — physical shapes, ruled at build (stop and report, never silently choose)

**All ruled 2026-07-14 with the build plan** (dated "Read-path build rulings" entry in
`decisions.md`; annotated inline above):

- **Wire shape** — ruled as suggested: `POST /v1/dialogue/init` (reconstruction's pre-warm hooks
  here — landed 2026-07-17), Pydantic models in `app\schemas.py`, route pass-through, unknown
  agent → 404.
- **Relevance mapping + SQL shape** — ruled as suggested: `clamp(1 − cosine_distance, 0, 1)`;
  over-fetch `retrieval_overfetch_factor` (4.0).
- **Recency knobs** — ruled: `decay_k_importance` (1.0); shared `tau_effective` confirmed
  (`app\decay.py`); `tau_fallback_seconds` (604800) for unresolvable labels.
- **importance_norm method** — ruled: **clamp + floor** (`importance_norm_floor`, 0.05) — the
  alternative won; min-max rejected for breaking the invalidation principle (see above).
- **k default** — ruled: `retrieval_top_k` = 8, same-name per-agent override key.
- **`as_of` override** — **ADOPTED**; `tests\CLAUDE.md`'s time-travel line carries the second
  mechanic.
- **`weight_overrides` reserved shape** — ruled as suggested: `{relevance?, recency?,
  importance?}` float multipliers.
- **Query-embedding failure fallback** — ruled: the suggested fail-quiet ladder row, with
  `relevance = null` per item on that path.
- **Empty/short-store behavior** — ruled as suggested: 0..k items, never an error.

## Done when

- **Happy path (fake provider).** Given seeded memories and a query, `retrieve_dialogue_init`
  returns ≤ k items ranked by descending `score`, each carrying `memory_id`, `detail_id`,
  `content`, `read_mode = verbatim`, `pinned`, and `score` with all three components;
  result-level instrumentation is non-null.
- **One seam, thin route.** For a single call, the FastAPI route's JSON is exactly the
  serialization of the service's `RetrievalResult` (adds and drops nothing); timing/token
  accounting recorded once at the seam.
- **Decay moves scores, not rows.** Re-scoring the same store with an older effective age (injected
  `valid_at` or later `as_of`) lowers recency components only — no item appears, disappears, or
  changes text.
- **Invalidation moves rows, not scores.** Given a candidate whose `memories.invalid_at` is set
  (fixture SQL), it is absent from results and no other item's scores change.
- **Live head served.** Given a chain whose head was superseded (fixture inserts a second detail
  row and invalidates the first), the served `content` and `detail_id` are the live head's — backs
  Set A's corrected-head-served assertion.
- **Pin exemption.** A pinned memory's recency component is 1.0; an identical unpinned twin of the
  same age scores strictly lower on recency.
- **Reserved fields inert.** Requests with and without `location_name`/`entities`/`event_time`/
  `weight_overrides` return identical items and scores (fake provider), and none of those fields
  is echoed.
- **Byte-identity.** Two identical calls (same store, same `as_of`, fake provider) return
  byte-identical `content` per memory_id and identical scores.
- **NULL-embedding exclusion.** A NULL-embedding row never appears via the vector path; under the
  ruled degradation fallback it can.
- **Degradation.** Per the ruled ladder row: a failing embedding provider still yields a ranked,
  non-empty result (store permitting) with `degraded = true`.
- **k honored.** `k` from the request, else the agent's config, else the service default; never
  more than k items returned.
- **Schema frozen.** No new migration; `db\migrate.py` no-arg is still a clean no-op on `longmem`.
- Every touched `[SETTLE-AT-BUILD]` was reported and confirmed before being built, and recorded in
  `decisions.md`.
