# longmem-npc — Test suite spec

Scenario suite in `tests\`: fixture + runner, runs in CI. The suite gets its own scoped build
session — it is a first-class deliverable, not an afterthought.

## The one rule

**Structural-only.** Assert on memory IDs, row types (`write_cause`, `read_mode`, typology), chain
shape, cache state, timestamps, and byte-identity of returned text — **never on generated prose.**
A model's wording is not a test surface. Judged evals (drift-toward-identity, Bartlett-style
distortion operators) belong to the eval story and the paper ablations, not this suite.

Corollary that makes this possible: read endpoints return memory IDs and scores alongside prose.
That contract is load-bearing; if an endpoint stops returning IDs, the suite is dead.

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
- Within-scene text stability: absent a diegetic event or an authorial correction on that memory
  (amended 2026-07-17), repeated reads within one scene are byte-identical.

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
- Escalation call fails twice → **HARD-STOP**, nothing inserted — structurally assertable as zero
  rows (build-phase stance ruled 2026-07-13; re-rule owed before the demo ships — see `status.md`).
- Gate degradation ladder: embeddings down → entity-only lexical fetch; no entities → novelty-only;
  both out → gate closed, loaded set served, fail-quiet.
- Malformed model responses (unparseable structured output, unknown action directive) → log, ignore,
  turn succeeds.
