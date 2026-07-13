# Write path & ingestion API — v1 build target

Second build target, on top of migration 01. This specs the **write half of the vertical slice**
(*event in → memory stored*), exposed as one ingest service. Design truth is
[architecture.md](architecture.md) §4–§5; the rulings behind it are in [decisions.md](decisions.md);
the schema it writes into is frozen in [migration-01.md](migration-01.md). This doc points, it does
not re-derive.

> **Status: spec, not built.** Scope, the ingestion contract, and Gherkin done-when are fixed here;
> the `[SETTLE-AT-BUILD]` items are physical shapes still to be ruled at build time (stop-and-report,
> then record in `decisions.md`). **This build adds no new DB migration — the migration-01 schema is
> frozen.**

## Principles this build honors

- **Atomic, bi-temporal, non-destructive insert.** One observe event lands as one transaction:
  never a partial write. `valid_at` is the client's world time (tz-aware, NOT NULL); `created_at` is
  server write time. No UPDATE-in-place, no DELETE.
- **All write-time facts populated day one** (architecture §2) — typology + confidence + source,
  provenance, context stamps, decay class, gist spans, importance, pin — even where the consuming
  mechanism is deferred.
- **Single instrumentation seam.** Exactly one function — the ingest service — carries the timing and
  token accounting. The CLI (in-process) and the FastAPI route are both thin callers of it; neither
  duplicates the seam. (CLAUDE.md: *instrument at the seam*.)
- **Structured return, not just prose.** The service returns memory IDs **and** the computed
  scores/facts as structured data, so the CLI debug view and the scenario suite assert on structure,
  never on generated prose ([test-suite.md](test-suite.md)). This extends the read-path invariant
  (IDs + scores in every payload) to the write path.
- **Nothing integrator-configurable is hardcoded** — model roles (per-role env var), decay-class
  map, thresholds, vocabularies.
- **Degradation is named and tested per model call** (architecture §2) — a flaky model never loses a
  write.

## Scope boundary — do NOT build

Read/dialogue path & retrieval scoring; the retrieval gate; prompt caching; the reconstruction
mechanism; reflection; the diegetic-correction mechanism; purge; reputation-delta emission; Unity;
and **any new DB schema or migration**. The diegetic-correction and purge verbs are *documented*
in the contract below but their handlers are out of scope. If adjacent work looks necessary, **stop
and report** rather than expand scope.

## The ingest service (the seam)

One entry point, both callers sit on it:

```
ingest_observation(event: ObserveEvent) -> IngestResult      # observation ingestion
scene_boundary(event: SceneBoundaryEvent) -> SceneResult      # accept + instrument only (v1)
set_pin(memory_id, pinned: bool) -> PinResult                 # toggle memories.pinned
```

- The **CLI harness** calls these in-process; the **FastAPI routes** are thin wrappers over the same
  functions. The route serializes the service's result and adds nothing: for one ingest, the route's
  JSON response is exactly the `IngestResult` the service returned, and the timing + token accounting
  is recorded once, at the service seam. (Two *separate* ingests differ — each mints fresh UUIDs and
  records its own timings — so the equivalence asserted is route-is-pass-through, not two calls
  matching.)

### `IngestResult` — the structured payload

Returned by `ingest_observation`, surfaced verbatim in the CLI debug view and asserted by the suite:

- **Identifiers** — `memory_id`, `detail_id` (the `original` head), `gist_span_ids[]`,
  `new_component_ids[]` (identity components grown by this write).
- **Computed facts / scores** — `importance_raw`; `typology` + `typology_confidence` +
  `typology_source`; `provenance`; `affect` (`valence`, `arousal`, `detail`); `entities[]`;
  `decay_class` + `decay_class_unknown`; `scoring_failed`; `pinned`.
- **Instrumentation** — per-stage timing (`nlp_ms`, `embed_ms`, `haiku_ms`, `insert_ms`, `total_ms`)
  and token accounting (`haiku_input_tokens`, `haiku_output_tokens`; embedding token count).

## Event contract (ingestion API v1)

### `observe` — the core event

| Field | Meaning |
|---|---|
| `agent_id` | target NPC (FK → agents). |
| `observation_text` | the raw observation. Stored immutable; NLP + embedding run on it. |
| `phase_tag` | integrator observation-phase vocabulary (passthrough; not interpreted in v1). |
| `client_timestamp` | world time → `valid_at` (tz-aware, required). |
| `provenance` | `lived` \| `injected`. |
| `typology` / `typology_confidence` | optional client declaration — **client wins**; when absent, Haiku classifies and `typology_source = inferred`. |
| `decay_class` | integrator label; validated against the agent's `config` map. |
| context (all optional) | `location_name` (stored) + its embedding → `location_embedding`; `entities[]`; `event_time`; `affect` override. A longer location *description*, if supplied, is embed-only (no raw column in the frozen schema). |
| `pinned` | optional; sets `memories.pinned` at insert. |
| `event_id` | optional idempotency key; **accepted but not enforced in v1** (dedup needs schema — see forks). |

### `scene-boundary`

The explicit, client-sent scene edge (architecture §6). Its three consumers — prompt-head rebuild,
identity-document recompile, reputation snapshot — are **all deferred**. **v1 accepts the event and
instruments it (timing), and does nothing else; it writes no schema.** The contract exists now so the
demo choreography and the eventual mechanisms hook a stable, tested event.

### `pin` / `unpin`

Toggle `memories.pinned` for a `memory_id`. Pin means exactly two things (architecture §8), both
honored later at read: decay exemption + reconstruction exclusion. **Freezing the head** and
restoration-as-a-correction-verb are read/reconstruction concerns and are deferred; v1 sets the flag.

### Deferred, documented only

- **diegetic-correction** — an in-world confrontation event referencing a target `memory_id`; routes
  through the dissonance path (post-August). Contract noted; **no handler in v1**.
- **purge** — the GDPR delete verb (architecture §12). Contract noted; **no handler in v1**.

## Write pipeline (`observe`)

Client event → NLP pass → single Haiku call → embedding → atomic insert (architecture §5).

**a. NLP pass (no LLM).** Tokenize + NER + noun-chunk extraction; match tokens/entities/noun-chunks
against the agent's `identity_components` (canonical + aliases + category) → **gist spans as
half-open char offsets into `observation_text`** (never rewritten text); a category hit counts even
without a named entity. Affect via a cheap lexicon pass → `affect_valence` / `affect_arousal` /
`affect_detail`. Intra-observation coreference. A **novel entity grows** `identity_components`
(new row). Cross-observation coreference misses are accepted (the detail just decays) — architecture
§4.1.

An **LLM-escalation pass** exists for hard cases, **biased loose** (over-call — a wasted call is
cheap, a lost gist breaks the product): triggers on importance-above-threshold, an identity hit
co-occurring with high affect/importance, or a novel entity.

**b. Single Haiku call.** Prose render + importance scoring + typology classification **only when the
client did not declare it**. Structured output → `{ rendered_content, importance_raw, typology?,
typology_confidence? }`. **Degradation:** on scoring failure the write **still lands** with neutral
importance and `scoring_failed = true` (architecture §2); on unparseable structured output → log,
apply neutral/default, the turn succeeds.

**c. Embedding.** OpenAI `text-embedding-3-small` at **1536** (locked) for `observation_text` →
`embedding`, and for the location name/description → `location_embedding`. The frozen schema stores
the location **name** + its embedding only; a longer description is embed-only (no new column).

**d. Atomic insert (one transaction).** `memories` (all write-time facts) + the `original`
`memory_details` head (`write_cause = original`) + `memory_gist_spans` + any new
`identity_components`. Validate `decay_class` against the agent `config` map; **unknown label →
default class + `decay_class_unknown = true`** (never reject — mirrors `scoring_failed`). Commit,
then return `IngestResult`.

### The render seam *(stated as design; flag for confirmation)*

`observation_text` = the client's **raw** observation, immutable forever (architecture §2, §4.1). The
Haiku render produces the **`original` detail row's `content`** (the initial telling that
reconstruction later supersedes). Gist spans point into `observation_text`, not the rendered detail.
This is the natural reading of architecture §4.1/§5 — flagged below for an explicit ruling.

## Degradation ladder (write)

| Condition | Behavior |
|---|---|
| importance-scoring model fails | write lands; neutral importance; `scoring_failed = true`. |
| unknown `decay_class` label | write lands; default class; `decay_class_unknown = true`. |
| malformed Haiku structured output | log, ignore, apply neutral/default; the write succeeds. |
| embedding call fails | `[SETTLE-AT-BUILD]` — fail the write vs. store null embedding + a flag. |

## Model provider interfaces

Each model role is an integrator knob with its own env var (architecture §3). The write path depends
on two provider interfaces — the **Haiku call** (render + importance + typology) and the **embedding**
(OpenAI 1536). Each ships with:

- a **real implementation** (drives the demo), and
- a **deterministic fake** (stable pseudo-embedding, fixed importance, echo render, deterministic
  typology) so the **structural suite and CI run offline, without keys, and never assert on prose**.

The provider is selected by config; the ingest service is identical under either.

## `[SETTLE-AT-BUILD]` — physical shapes to rule at build time

- **NLP stack** — spaCy model choice; coreference library (`fastcoref` vs `coreferee` — never
  `neuralcoref`); affect lexicon (VADER vs an emotion wordlist) and its mapping to
  `affect_valence`/`affect_arousal`/`affect_detail`. *(Suggested: spaCy + `fastcoref`; VADER
  compound → valence, `affect_detail` = raw scores. **VADER has no native arousal → `affect_arousal`
  null in v1** unless a second source is chosen — see flags.)*
- **LLM-escalation** — the importance threshold value, the structural-ambiguity proxy definition, and
  novel-entity growth (the spam gate on growth is deferred).
- **Idempotency** — **none in v1** (the frozen schema has no dedup column). A client `event_id` +
  dedup window would need schema this build forbids, so it is deferred to a future migration unless
  Jack rules otherwise; v1 accepts `event_id` but does not enforce it.
- **Embedding-failure degradation** — fail the write vs. null embedding + flag.
- **Wire shape** — the `observe` request/response Pydantic models and the FastAPI route path/verb.

*(Settled, not a fork: importance is stored **raw** at write and normalized at read — architecture §2,
`memories.importance_raw`.)*

## Open flags — surface, do not resolve

- **scene-boundary has no persistent schema home** and all three consumers are deferred → v1 accepts
  + instruments only. Confirms **no migration-02 is needed** for this build.
- **render seam** — raw `observation_text` vs. rendered `original` detail (above): confirm the
  mapping.
- **arousal** — VADER (the likely lexicon) has no arousal axis; `affect_arousal` may stay null in v1.

## Done when

- **Atomic happy path (fake provider).** Given an `observe` event and the deterministic fake
  providers, when `ingest_observation` runs, then exactly one `memories` row, one `original`
  `memory_details` head, and the expected `memory_gist_spans` rows exist **after a single committed
  transaction**, and the returned `IngestResult` carries their IDs + the computed scores/facts.
- **One seam, thin route.** For a single ingest, the FastAPI route's JSON response is exactly the
  serialization of the `IngestResult` the service produced (the route adds and drops nothing), and
  the timing/token accounting is recorded once at the service seam — proving both callers sit on one
  instrumented seam.
- **Importance degradation.** Given a provider that fails importance scoring, the write still lands
  with neutral importance and `scoring_failed = true`.
- **Unknown decay class.** Given a `decay_class` absent from the agent's config map, the write lands
  with the default class and `decay_class_unknown = true` (not rejected).
- **Client typology wins.** Given a client-declared `typology`, the stored row has that value and
  `typology_source = declared`; given none, Haiku classifies and `typology_source = inferred`.
- **Novel entity grows the index.** Given an observation naming an entity absent from
  `identity_components`, a new component row exists and its id appears in `new_component_ids`.
- **Pin.** `set_pin(memory_id, true)` sets `memories.pinned = true`; the `IngestResult`/read reflects
  it.
- **Instrumentation present.** Every `IngestResult` carries non-null per-stage timings and Haiku
  token counts.
- **Gist immutability holds.** Gist spans reference `observation_text` offsets; `observation_text` is
  never rewritten by the write path.
- Every touched `[SETTLE-AT-BUILD]` was reported and confirmed before being built, and recorded in
  `decisions.md`.
