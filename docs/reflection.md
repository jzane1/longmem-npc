# Reflection — Phase C2 design dossier

Formed beliefs over lived episodes: reflection samples an agent's memories weighted by
importance × recency, writes conclusions **grounded in cited `memory_id`s**, folds
identity-relevant conclusions into the **rendered identity document**, and **prunes the
identity-components table**. A non-LLM **repetition detector** (RRR) guards the identity
revision against the named confabulation failure mode. Design truth being consolidated:
[architecture.md](architecture.md) §10 (plus §2, §4.2–4.3, §7), the primary rulings in
[decisions.md](decisions.md), the banked research findings
(`docs\research\FINDINGS.md` #4), and migration 001's `reflections` table. This doc
points, it does not re-derive.

> **Status: DESIGN DOSSIER — drafted 2026-08-15; forks 1–6 RULED 2026-08-15, all six
> recommended options taken first pass, plus the habituation rider (the dated C2 dossier
> entry in `decisions.md`).** Matures into the C2 build spec next session (the spec adds
> the build skeleton: `[SETTLE-AT-BUILD]` + Done-when; the settle ledger below feeds it).
> NO code, NO migration, NO tests land with this document.

## The ruled shape (collected — nothing here is re-asked)

1. **Endpoint + pressure gauge.** Reflection is a verb the integrator pulls; the store
   exposes reflection pressure as a readable gauge; no scheduler (primary ruling,
   `decisions.md` "Reflection: endpoint + pressure gauge"; architecture §10).
2. **Sampling is importance × recency, not recent-N** (same ruling).
3. **Rendered identity document** = seed prose + current identity-relevant reflections;
   `identity_version` = content hash of the rendered text; recompiled at scene edges
   under the caller-frozen-scene-state contract (`decisions.md` "Identity document:
   rendered + content-hashed"; architecture §4.3; `app\identity.py` docstring — the
   module was written to be extended exactly here).
4. **Reflection-time component trim** is the sole mechanism that removes a durable fact:
   it INVALIDATES (`invalid_at`), never deletes, with silent cache invalidation chosen
   deliberately (architecture §4.2 "Consequence to remember" + §4.3; 001's
   `identity_components` header comment).
5. **Haiku-class serves reflection**; the model role's env var arrives with reflection
   (architecture §3).
6. **Purge honesty:** reflections derived from purged episodes remain as aggregate
   work-product, and the docs say so (primary ruling; architecture §13 purge note).
7. **The `reflections` table exists since migration 001**, bi-temporal like memories:
   `reflection_id` PK, `agent_id` NOT NULL FK, `content`, `identity_relevant` boolean
   gate, `source_memory_ids uuid[]` — provenance only, **intentionally NOT foreign-keyed**
   (purge-honesty), `created_at`/`valid_at`/`invalid_at` (001:150–159). Zero code
   readers or writers today; already in the eval-runner's twelve-table census.
8. **The within-scene byte-identity invariant** has exactly three sanctioned text-change
   causes (diegetic event, authorial correction, deferred-enrichment completion); the
   third was added **by ruling** at C1 — the amendment pattern exists (CLAUDE.md
   invariants; architecture §7; the C1 fork-4 entry).
9. **C1's worker machinery exists for C2 to ride** — recorded in the C1 ruling itself:
   "reflection and purge stay endpoint-pulled … and C2's idle-time scheduling later
   rides it"; endpoint-pulled-only was *rejected* there partly because "C2 would have no
   machinery to ride" (`decisions.md` C1 ruling 3). The lifecycle contract: in-process
   asyncio worker, both construction sites, `stop()` before pool close,
   catch-log-continue, a deterministic `drain()`-style test entry, `SERVICE_DEFAULTS`
   knobs, default OFF (`deferred-writes.md`).
10. **The 2026-08-04 cut list stands**: graph/associative memory, recall-reinforced
    decay, automatic conflict/staleness detection, habituation, the Whisper hook, the
    dormant-agent overseer, the full modulator suite. The reflection → parameter
    compiler **survives as C3**; only the suite extension is cut.
11. **Non-destructive storage:** `agents.seed_identity` is written at insert and never
    UPDATEd (the sanctioned in-place writes are `pinned` and the C1 one-shot completion
    — `app\db.py` header). Any identity revision must land as new rows.
12. **Nothing integrator-configurable is hardcoded** — every new threshold, cadence, or
    kill-switch is a `SERVICE_DEFAULTS` knob under the `agent_knob` contract or a
    documented `agents.config` key.

Two more standing facts the design leans on: the typology vocabulary already admits
`'reflected'` on `memories` (001:66 — schema-now evidence, weighed in fork 2), and
"runtime state (reflection pressure, drift headroom) ships with its mechanism and needs
no backfill" (architecture §2) — the gauge is computed, never stored.

## The design areas

### 1. Scheduling: how the endpoint composes with idle-time work — FORK 1

Two recorded positions are in tension: §10's "no scheduler" (reaffirmed at C1:
"reflection and purge stay endpoint-pulled") and the roadmap's "idle-time scheduling
rides C1's machinery" (with C1's own rejection rationale expecting it). They compose
rather than conflict:

**Ruled (Jack, 2026-08-15) — both, worker default OFF.** The endpoint stays the verb
(`POST /v1/agents/{agent_id}/reflect` — an operator/integrator verb, not a diegetic
event). An optional sibling **`ReflectionWorker`** on C1's exact lifecycle contract
(both construction sites, `stop()` before pool close, catch-log-continue, a
deterministic no-timer entry for tests/walkers) polls for agents whose **pressure**
(area 7) crosses a knob threshold and pulls the same service seam the route calls.
Ships **default OFF** (`reflection_worker_enabled` 0.0 — kill-switch semantics, the
`deferred_writes_enabled` precedent); pressure threshold per-agent via `agent_knob`;
poll interval process-level. §10 is amended to record the composition: the endpoint is
the verb, the gauge is the trigger's evidence, the worker is optional automation of the
same pull. The agent-scan query per poll is cheap at NPC scale (spec latitude).

**Rejected would cost:** endpoint-only — contradicts the roadmap line and leaves C1's
recorded "machinery to ride" rationale dangling; worker-only — overturns the standing
endpoint ruling and removes integrator control; a generic `deferred_jobs` table with a
`work_type` column — a migration-006-rewrite-shaped change to a verified floor
(`EnrichmentClaim` is `memory_id`-keyed, `memory_enrichment_runs.memory_id` is NOT NULL
FK — the enrichment queue structurally cannot host agent-scoped jobs), paying off only
if a third work type ever arrives.

The un-reflected window mirrors C1's un-enriched window: with the worker off, nothing
changes for any integrator; with it on, the exposure semantics are area 5's.

### 2. Where reflective content lives — FORK 2

The storage decision decides retrieval visibility, citation mechanics, purge semantics,
and C3's feedstock.

**Ruled (Jack, 2026-08-15) — the `reflections` table is the sole durable home.** A reflection is
an identity ingredient and C3 feedstock, **not a retrievable memory**: identity-relevant
rows reach prompts through the rendered document (area 4); non-identity rows wait for
C3's compiler (until then they are inspectable but runtime-inert — that is this
option's real cost, stated plainly). Faithful to §10, which frames reflections as
identity + compiler material and never as retrieval candidates. Retrieval is untouched
— zero code changes, the C1 zero-perturbation precedent — so the post-landing
believability compare isolates the identity channel. Citations land in the existing
`source_memory_ids` column; supersession uses the ordinary bi-temporal verb (the C3
eviction contract). Purge honesty stays exactly as ruled.

**Rejected would cost:** `memories` rows with `typology='reflected'` — the CHECK admits
it today (genuine schema-now evidence this path was anticipated, not a strawman), and
beliefs would flow through ordinary retrieval with zero retrieval-code changes; but
`memories` has **no citation column** (its `provenance` is `lived|injected`, a
different concept — migration 007 would have to add one), §5's whole write-path
obligation set cascades onto belief text (importance scoring, gist spans, decay class,
provenance vocabulary for a row that is neither lived nor injected), the `reflections`
table stays a census corpse while C3's contract re-homes, and purge semantics fork (a
belief row purgeable while its citations dangle). **Dual-write** — two homes for one
content plus the purge divergence (the memories twin purgeable, the reflections twin
surviving). If retrieval-visible beliefs are ever wanted, that is a *separate later
ruling* layered on top of the table home, not a reason to fork the home now.

### 3. The reflection call: sampling, citations, the repetition detector

The call itself (all shapes below are dossier recommendations settled at spec unless
marked as fork 5):

- **Sampling pool:** the agent's live memories, drawn by importance × recency (ruled).
  Weights reuse the existing normalization and decay math (`app\decay.py` — one recency
  formula in the system, never two). NULL-importance pending rows take the
  `importance_neutral` fallback (the C1 window precedent). **Pinned rows are included**
  — pin means exactly two things (decay exemption, reconstruction exclusion) and
  reflection is neither. Pool size `reflection_sample_k` + a minimum-episode floor
  knob (below the floor the verb 409s or no-ops loud — spec choice).
- **Sampled text:** the **live telling head** — the character's current story, not
  `observation_text`. Reflection is the character concluding from how they remember
  it, thesis-consistent with reconstruction's prior-head-input precedent. (The
  operator-facing ground truth stays available to the eval harness, which can diff
  belief against record.)
- **Citations:** the model must ground each conclusion in the sampled `memory_id`s;
  `source_memory_ids` stores them. Enforcement is mechanical and non-LLM: cited ⊆
  sampled, checked at the seam; a conclusion citing nothing or citing unknown IDs is
  rejected (logged, not stored) — grounding is the point, an ungrounded belief is the
  named failure mode, not a degraded success.
- **The repetition detector (RRR) — FORK 5.** `SequenceMatcher` similarity against the
  agent's recent live reflections, threshold knob (paper default 0.85), computed
  non-LLM at reflect time, always recorded in instrumentation.
  **Ruled (Jack, 2026-08-15) — teeth, not just telemetry:** at/above threshold the new
  reflection still stores (it is honest evidence of the agent's state), but the
  **identity-consolidation step is blocked/flagged** — "budget a staleness check before
  an identity revision is trusted" is the corpus's most important reflection caution.
  **Rejected would cost:** log-only — the named failure mode (a stale belief reinforced
  into identity) ships unguarded, which is precisely what the source paper measured
  going wrong.
  **Boundary, stated explicitly:** RRR is *self-repetition among the agent's own
  reflections*. It is NOT the cut "automatic conflict/staleness detection" item
  (cross-memory, write-time contradiction detection) — that stays cut.
- **Degradation:** the reflect call failing (provider error, malformed output) writes
  **nothing** and fails **loud** (502) — reflection is derived work; never-lose-a-write
  protects observes, and no write is lost by refusing to store a failed derivation.
  The worker's failures are catch-log-continue plus a persisted run row (area 8).

### 4. Identity refresh and the dialogue seam — FORK 3

Three coupled sub-rulings, one fork — **ruled as a package (Jack, 2026-08-15)**:

**(i) The render stays model-free.** `render_identity_document` extends
concatenatively: seed prose + the agent's live identity-relevant reflections, in a
deterministic order. Pure and walker-assertable exactly as today; the scene-edge
recompile stays non-LLM; `identity_version` moves the way the hash contract always
said it would. With zero reflections the render is seed-verbatim — **byte-identical to
today, so every existing floor holds** (the parity contract).

**(ii) The periodic evidence-conditioned refresh is a consolidation product of
reflection itself.** When it runs (cadence knob / pressure-coupled — spec latitude), an
LLM rewrite conditioned on the *prior* document + the live identity-relevant
reflections + the immutable seed produces a **new identity-relevant reflection that
bi-temporally absorbs the ones it consolidates** (they get `invalid_at`; it cites their
sources). The render stays deterministic, the document stays bounded instead of growing
without limit, `identity_documents` gains rows and never mutations, and
`agents.seed_identity` is never touched. This is the ai-you-town anchor-refresh shape
(+0.87 fidelity ablation) built out of our existing plumbing.

**(iii) The dialogue prompt moves off raw seed onto the rendered document.** Found this
session: `assemble_prose_prompt` takes `state.seed_identity` raw
(`app\dialogue.py:311-315`), while reconstruction renders `[identity]` from the
document fetched by the caller-frozen `identity_version` — invisible today because the
render is passthrough. The moment reflections join the render, **NPC speech would never
see them**: the headline feature would be inaudible in dialogue. The dialogue request
already carries `identity_version` (`app\dialogue.py:281`), so the move is fetching the
document by that frozen version instead of the raw column — same parity argument as
(i). This re-opens the dialogue-seam floors; re-verifying them is a step, not a cost.

**Rejected would cost:** LLM-render-at-scene-edge — a model call in the
latency-sensitive boundary heartbeat and a non-deterministic `identity_version`;
refresh-as-mutation of seed or of a document row — violates non-destructive storage;
leaving the dialogue seam on raw seed — a permanent speech/reconstruction identity
split.

**Consequence to plan for:** C2 unfreezes `identity_version` for the first time. Every
version bump is a reconstruction-cache miss *by key construction* — expect mass
re-reconstruction after each identity change. The decay band was explicitly built as
the pre-reflection stand-in for this drift driver; the composed key
(`identity_version|b{band}`) absorbs the unfreeze with no cache-code change.

### 5. Component trim and scene safety — FORK 4

**The premise, verified this session:** the gate side already follows liveness — the
tripwire set is `db.fetch_live_components` (`invalid_at IS NULL`), so a trim shrinks
the gate's lookup set with zero gate changes (`mid-dialogue-gate.md`'s "the lookup set
only grows" note expires at C2). But **reconstruction does not**:
`fetch_reconstruction_sources` reads gist spans with no component-liveness join
(`app\db.py:916-923`), so today a trimmed component's spans would keep constraining
retellings — the trim would remove **nothing** durable at the reconstruction seam, and
the ruled §4.2 sentence ("the sole mechanism that removes a durable fact") would be
mechanically vacuous.

**Ruled (Jack, 2026-08-15):** (i) **constraint-follows-liveness** — spans whose
`matched_component_id` is invalidated drop out of the gist constraint at build (the
mechanism reading that makes the ruled sentence true); unmatched spans
(`matched_component_id IS NULL`) are untouched. (ii) Because the trim's cache eviction
then genuinely changes what a re-reconstruction can say, **reflection-driven eviction
becomes the FOURTH sanctioned cause** of mid-scene text change (the C1 amendment
pattern), with integrator guidance stated in the spec: pull reflection at scene edges
and the window vanishes — mid-scene exposure exists only if the integrator (or the
worker) reflects mid-scene. Eviction scope (per-affected-memory vs agent-wide) is spec
latitude under this ruling.

**Rejected would cost:** a scene-boundary-only constraint — **unenforceable
server-side**: scene state is caller-held by ruled design (the caller-frozen contract);
the server keeps no active-scene registry and the worker can't see scenes either;
trim-without-eviction — stale caches keep serving the trimmed fact, the trim stops
removing durable content; no-liveness-filter — the trim is a no-op on tellings and the
ruled consequence stays false in practice. Which components get trimmed (criteria,
model-proposed vs mechanical) is spec latitude.

### 6. The model role — FORK 6

`LONGMEM_MODEL_REFLECTION` arrives with C2 (the standing sentence in CLAUDE.md and
architecture §3 anticipates the edit).

**Ruled (Jack, 2026-08-15) — the judge shape, not a seventh required var:** read outside the
real-mode required block, required by neither mode at load, with a standalone
`build_reflection_provider` factory that raises `ConfigError` at the **first real
reflect call** without the var. Since reflection ships default-OFF and
endpoint-pulled, an integrator who never reflects never needs the var: every existing
real-mode `.env` keeps loading, and the Set I load-rule pins stay true as written
(amended for the new role's shape, not broken). Haiku-class per the ruled slate.
Pricing rows (`LONGMEM_PRICE_REFLECTION_IN/OUT`) and the full add-a-role checklist
(constants, `load_env` allowlist, `Settings` field, providers triad, `.env.example`,
conftest fakes) run at build.

**Rejected would cost:** seventh-required — breaks every current real-mode `.env` for a
verb many integrators never call, and contradicts the logic the judge precedent
already established for roles outside the serving path's hot loop.

### 7. The pressure gauge (recommendation recorded; settled at spec)

**Definition:** computed on demand, never stored (architecture §2's runtime-state
rule): the importance-weighted mass of the agent's live memories created since the
agent's latest live reflection (all memories, agent lifetime, when none exists),
normalized by a knob so integrators can tune what "1.0 = reflect now" means. NULL
importance takes `importance_neutral`. One SQL aggregate; non-LLM.

**Surfaces:** the reflect response carries pressure-before and pressure-after; the
worker's threshold check computes the same number (one implementation). **No new read
route at C2** — the unscored inspector-read carve-out has exactly three members *by
contract*, and the gauge's natural standing surface is C5's agent-state read route,
where that carve-out ruling belongs. The C5 dependency is recorded here so the gauge
doesn't silently acquire a route ahead of its ruling.

### 8. Instrumentation and wire (recommendations recorded; settled at spec)

- **The reflect response** (instrument-at-the-seam, riding the payload like every
  foreground seam): the written `reflection_id`s with content, `identity_relevant`,
  and `source_memory_ids`; the sampled pool's `memory_id`s (grounding is auditable at
  the seam); the RRR value and whether the guard fired; pressure before/after; the new
  `identity_version` when consolidation ran; per-stage timings and token counts.
  The reflect verb is a **write endpoint** — the IDs+scores invariant binds read
  endpoints that run retrieval; the weighted sampling draw is not the retrieval seam
  and produces no relevance scores. Cited and sampled IDs are carried as grounding
  evidence, unscored by nature.
- **If the worker lands (fork 1):** a background seam has no payload to ride, so
  per-attempt accounting persists — a `reflection_runs` table keyed on `agent_id`
  (nullable reflection linkage; `memory_enrichment_runs` cannot host it — its
  `memory_id` is NOT NULL FK), mirroring the 006 column shape (attempt, outcome CHECK,
  error, per-stage `*_ms`, token columns). This is what makes migration 007
  worker-contingent, and it bumps the eval-runner table census 12 → 13.
- **Inspector surface:** reflections join the `/chain`-class inspector reads and The
  Ledger **later** — any reflections read route is unscored-by-contract territory and
  waits for its own ruling (C5's neighborhood). Nothing in C2 adds a read route.
- **Client mirror:** the house precedent is verbs mirrored 1:1 in `NpcMemory.Core`
  (the eval fork-1 "Mirror" ruling). The reflect verb + result model mirror at build —
  small — or take a dated exemption to C5; settled at spec.

## Scope boundary — do NOT build

- The cut list, by name (2026-08-04): graph/associative memory, recall-reinforced
  decay, **automatic conflict/staleness detection** (see fork 5's boundary — RRR is not
  this), habituation, the Whisper hook + safe-default action fallback, the
  **dormant-agent overseer** (idle scheduling rides C1's worker pattern and must not
  drag the overseer in — no wake triggers, no cross-agent orchestration), the full
  modulator suite.
- Banked, not committed (FINDINGS #4): persona-lensed retrieval routing, hierarchical/
  online consolidation, calibrated trait uncertainty. None enters C2.
- **C3 is not built here.** C2 leaves the compiler's contract standing (below) and
  nothing more.
- No new judged-eval category, no eval-harness changes (its spec scope-bounds "no
  reflection"); the scenario schema gains a `reflect` event kind only if the Set L
  design at build needs it.
- Nothing ships default-ON. No retrieval-path changes of any kind.

## The C3 contract (what C2 must leave standing)

Stable, addressable formed beliefs: `reflection_id` is the compiler's cache-key
component (one call per reflection × scene-type); **bi-temporal reflection invalidation
doubles as compiler-cache eviction** (so supersession/consolidation must set
`invalid_at`, never delete); `content` + `identity_relevant` + `source_memory_ids` are
the compilable surface. One recorded caution carries forward: a compiled parameter
layer has the same amplification shape as a confabulated rule library (the
honest-lying paper's ExpeL note) — C3's spec should budget its own staleness guard;
RRR at C2 is the upstream half of that defense.

## Contradictions and stale spots this dossier registers

1. **§10's heading** read "(mechanism sequenced later — see status.md)" — amended this
   session: §10 now records the ruled composition (fork 1); the build-time consequences
   (§7's fourth cause, §4.2's liveness mechanics) land with the build.
2. **"No scheduler" vs "idle-time scheduling"** — the fork-1 tension described in area
   1; resolved by the 2026-08-15 ruling; §10 amended, and the primary register entry
   ("Reflection: endpoint + pressure gauge") carries the dated amendment note.
3. **The dialogue-seam asymmetry** (raw seed vs rendered document) — found this
   session, resolved by fork 3(iii).
4. **Constraint ignores component liveness** (`app\db.py:916-923`) — found this
   session; resolved by fork 4(i); until built, the §4.2 "sole mechanism" sentence is
   true only prospectively.
5. **Habituation was still worded live** in architecture §2 (knob list) and §8 though
   cut 2026-08-04 — the rider was ruled ANNOTATE NOW (2026-08-15); both spots carry the
   cut-parentheticals as of this session.
6. **`mid-dialogue-gate.md`'s "the tripwire's lookup set only grows"** — expires at C2
   build (the gate follows liveness already; the trim is what shrinks it).
7. **`sleep-time-compute.md` cites "§12"** for reflection — it is §10. Archival
   research note: pointed at, never edited (the research-notes convention).

## Verification preview (nothing here is built by the dossier)

- **Suite Set L** (reflection scenarios) + the **ninth walker**
  `tests\verify_reflection.py` (the Set K / eighth-walker template: lettered sections,
  fail-fast `check()`, worker-lifecycle section cloned from `verify_deferred_writes.py`
  section D). The walkers' shared fixed-name scratch DB stays a carried item — the
  ninth walker inherits the limitation, it does not fix it.
- **Migration 007 is contingent**, not assumed: the `reflections` table exists; 007
  carries only what the rulings require (a `reflection_runs` table iff the worker
  lands; any belief-citation column iff fork 2 goes the memories-row way). If 007
  lands, the three mechanical pins bump: the gate walker's ledger list, the
  eval-runner migration count, the table census (12 → 13 iff a new table).
- **Touched floors re-verify** (a step, never an argument): fork 3(iii) re-opens the
  dialogue-seam floors (prose-prompt assembly); fork 4(i) re-opens reconstruction's
  (constraint inputs change shape). Their walkers re-run at build; parity contracts
  (zero reflections ⇒ byte-identical prompts and constraints) are the evidence the
  re-verification asserts.
- **The standing Phase C check:** after the C2 landing, a harness believability run
  confirms no regression (the point of doing Phase B first). With fork 2 as
  recommended, retrieval is untouched, so the compare isolates the identity channel.

## Settle ledger

**[SETTLE-AT-SPEC]** (each with the dossier's recorded recommendation):
migration 007 exact scope (worker-contingent `reflection_runs`; nothing else expected)
· wire shapes (`POST /v1/agents/{agent_id}/reflect` request/response models; the C#
mirror-vs-C5-exemption call) · knob names and defaults (`reflection_worker_enabled`
0.0, `reflection_poll_seconds`, `reflection_pressure_threshold`,
`reflection_sample_k`, a min-episode floor, `reflection_rrr_threshold` 0.85,
consolidation cadence) · the reflect prompt shape (JSON-in-text, the reconstruction
precedent; pure assembly function, walker-assertable) · consolidation trigger
mechanics (cadence vs pressure-coupled) · trim criteria (model-proposed with
citations vs mechanical) · eviction scope (per-affected-memory vs agent-wide) ·
render ordering for identity-relevant reflections (deterministic order definition) ·
Set L composition + the walker's section plan · the eval-runner `reflect` event kind
(iff Set L needs it).

**[SETTLE-AT-BUILD]** (stop-and-report discipline as always): exact field and column
names, walker assertion counts, SQL shapes, the worker's scan query, error-string
taxonomy.

## This dossier is done when

Forks 1–6 presented and ruled; the rulings recorded as a dated `decisions.md` entry
(with its Index line and count); this document finalized to the rulings; `docs\README.md`,
`status.md`, and `session-log.md` propagated; **no code, no migration, no test written**.
The C2 spec session then turns this into the build target.
