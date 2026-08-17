# dissonance.md — the dissonance path + diegetic-correction event (Phase C4)

**BUILT 2026-08-17, plan-to-floor in one session** — NO migration (the ruled scope fact;
the `corrections` table waited since 001), `app\dissonance.py`,
`POST /v1/events/diegetic-correction`, ruling 4 in the reconstruction path, the REPL
`:confront`, the chain inspector's corrections block, the C# mirror + interop beats
(32 → 36), suite Set N (23 scenarios, all unmarked — the Set A diegetic pair landed), the
eleventh walker (38 assertions), `verify_reconstruction` deliberately re-opened and
re-closed at 46. The eight C4 rulings are the dated 2026-08-17 build record in
`decisions.md`; the plan-mode fork batches settled them before a line was written. The
independent floor-verifier returned **pass** (floors row 28); believability shows no
regression vs the 2026-08-07 baseline (checks 6/0 both, gist 0.7667 → 0.825).

Design truth is `architecture.md` §8 (the threshold formula, the two verbs, the pin ruling)
and §7 (the anchor set, the eviction invariant, the drift-budget exemption for event-driven
writes). This doc consolidates them into the buildable target; it points, it does not
re-derive. The schema has waited since migration 001: the `corrections` table
(`migration-01.md`) and both diegetic `write_cause` values were carved day one with the
comment "the dissonance mechanism that writes these lands post-August" — C4 is that
mechanism. The suite's Set A diegetic pair (`test-suite.md`) has been the pre-written
acceptance shape since 2026-07-20. Automatic conflict/staleness detection is CUT (ruled
2026-08-04): this is **reaction machinery only** — the event supplies the target
`memory_id`; nothing discovers contradictions.

## The eight rulings (Jack, 2026-08-17; the dated C4 entry in `decisions.md`; settled at the plan-mode fork batches before a line was written)

1. **The decision is mechanical** — no model call decides.
   `resistance = importance_norm × typology_mult(memory.typology) × rigidity`;
   `challenge = challenge_weight × typology_mult(challenge.typology)`;
   `challenge > resistance` (strict) → `update_with_resentment`, else `rationalization` —
   **ties defend**. Every multiplier is a `SERVICE_DEFAULTS` knob, per-agent overridable.
   (The retrieval gate is the precedent for a pure non-LLM decision module.)
2. **The head text reuses the RECONSTRUCTION role** — the retelling role writes the
   confrontation prose. No new env var, no provider quartet, no judge-shaped machinery: the
   role is one of the six required real-mode vars, so it is always present. Token spend
   prices under the reconstruction price keys — stated here honestly; the result names its
   fields by function (`retell_ms`, `retell_*_tokens`).
3. **Tellings-only; NO new migration** — the explicit per-target scope fact, ruled for this
   target (the standing `fact-level-correction.md` boundary — "diegetic fact-writes need
   their own ruling" — is hereby ruled: they do not happen). The fact basis and embedding
   never move; retrieval keeps matching the original account; a game that wants the
   confronter's account retrievable observes the confrontation as an ordinary event. The
   fact-chain CHECK keeps REJECTING the diegetic verbs, and the walker probes the rejection.
4. **`update_with_resentment` anchors get the authorial treatment** — the head is the
   reconstructor's FIXED constraint; observation-derived gist is not re-injected (closes the
   fork the 2026-07-17 authorial spec explicitly deferred "decided with the dissonance
   path"). Later retellings stay inside the accepted account; original gist cannot resurrect
   details the character conceded. `rationalization` anchors nothing (§7: never re-anchors).
5. **Route: `POST /v1/events/diegetic-correction`** — the third route in the in-world
   namespace, beside observe and scene-boundary (`/v1/events/*` stays diegetic, the
   correction-route precedent).
6. **Full surface in the one session**: the C# mirror + interop beats, the REPL `:confront`
   meta-command, and the chain inspector's corrections block.
7. **The formula is §8 verbatim** — no `typology_confidence` term. Scaling the memory side
   by stored confidence is a coherent refinement and was consciously declined (revisitable
   in Phase D with measurements, never adopted untested).
8. **Two stale `architecture.md` lines ride this doc pass** — the `write_cause` enum list
   and the drift-anchor set, both missing `enrichment` since C1 (verified against migration
   006 and the anchor SQL).

## What it is

An in-world confrontation reaches the backend as an API event referencing a target
`memory_id`: someone challenged the NPC's account of a remembered event. The dissonance
path decides mechanically whether the character defends or folds, has the reconstruction
role write the character's new telling in that stance, and extends the telling chain —
never replacing it: prior tellings stay queryable, the confrontation lands as a
`corrections` row, and the reconstruction cache for that memory is evicted. "Either way the
store records the truth; the fork only shapes the character's reaction" (§8) — under
ruling 3 the recorded truth (the fact chain) is literally untouched.

The two outcomes, both writing exactly one new head + one correction record:

- **`rationalization`** — the challenge lost. The new head is a defensive retelling that
  explains the challenge away. It NEVER becomes the drift anchor, so it spends drift
  headroom without being blocked (event-driven writes are budget-exempt): a heavily
  defended memory crystallizes — "the story has set."
- **`update_with_resentment`** — the challenge won. The new head accepts the confronter's
  account, resentfully. It BECOMES the drift anchor (already in the anchor SQL since the
  authorial build) and, per ruling 4, the reconstructor's fixed constraint.

## The decision (ruling 1 — pure functions, no IO)

In `app\dissonance.py`, unit-assertable without a database:

- `typology_mult(typology, config, settings)` — knob lookup `dissonance_typology_<value>`
  over the standing vocabulary (`observed | told | inferred | reflected`). A memory-side
  NULL typology (an un-enriched deferred row) resolves first via the `resolve_typology`
  tail: `config.get("typology_default", TYPOLOGY_FALLBACK)`.
- `decide_dissonance(...)` — resolves every input, computes both sides, returns the verb
  plus all resolved terms (they ride the response):
  - `importance_norm = clamp(importance_raw, importance_norm_floor, 1.0)` — the read-path
    clamp verbatim; NULL `importance_raw` (deferred window / scoring_failed) resolves to
    `importance_neutral` first.
  - `rigidity` — the `agents.rigidity` column (schema CHECK 0.5–2.0, no column default by
    design); NULL resolves to `dissonance_rigidity_default`, then clamps to [0.5, 2.0]
    mirroring the CHECK as defense.
  - `challenge_weight` — request field; absent resolves to
    `dissonance_challenge_weight_default`, clamped [0.0, 1.0].
  - `resistance = importance_norm × typology_mult(memory) × rigidity`;
    `challenge = challenge_weight × typology_mult(challenge)`;
    strict `challenge > resistance` updates, anything else defends.

"I saw it" resists harder than "I heard it," on both sides of the clash: the same
typology-multiplier table serves memory and challenge. A multiplier set to 0.0 is the
kill-switch shape per side (memory-side 0.0 → that evidence class always folds;
challenge-side 0.0 → that evidence class never wins).

## The retell (ruling 2 — the reconstruction role's second consumer)

One single-item call through `providers.reconstruction.reconstruct` (the existing protocol:
seam-assembled `system_prompt` + `user_content`, `items` riding structurally so the
deterministic fake derives stable output). Assembly, owned by `app\dissonance.py`:

- **system prompt** — the live identity document, the decided verb's stance instruction
  (defend-and-explain-away vs accept-with-resentment), and the JSON output contract the
  provider's parse side already enforces.
- **user content** — the challenge block: the confronter's account (`challenge_text`) and
  its declared evidence class.
- **the item** — the live head as `current_telling`; full detail (no decay thinning — a
  confrontation is not a decay retell); NO gist block (consistent with ruling 4: the
  constraint is the current telling + the challenge, never re-injected observation gist).

The call runs BEFORE the transaction (the `ingest.correct` all-or-nothing rule: network
calls never span the transaction). Failure or malformed output → `DissonanceCallError` →
502, **nothing written**. In fake mode the provider's deterministic echo makes the new head
non-empty, distinct from the prior head, and verb-distinguishable — the structural surface
the suite needs; prose is never asserted.

The retell-then-transaction race (the head moving between prompt assembly and the
supersede) is the same accepted shape as authorial's NER/embed-before-transaction; the
opt-in `expected_detail_id` CAS is the guard for callers who care.

## The transaction — `db.apply_diegetic_correction` (all SQL in `app\db.py`)

ONE transaction beside `apply_authorial_correction`, chain-preserving:

1. Supersede the live telling head (`UPDATE … SET invalid_at … WHERE memory_id … AND
   invalid_at IS NULL RETURNING detail_id`) — no row → `unknown_memory` → 404; an
   `expected_detail_id` mismatch → `_StaleHeadError` → rollback → 409, nothing written.
2. Insert the new head, `write_cause` = the decided verb (001's CHECK admits both since
   day one).
3. Insert the `corrections` row — `memory_id`, `detail_id` (the step-2 head; FK ordering
   forces 2-before-3), `verb`, `source_event` (via `Jsonb`, nullable), `valid_at`.
4. Evict: `DELETE FROM reconstruction_cache WHERE memory_id = %s` — rowcount rides the
   response (the standing invariant: any non-reconstruction chain writer evicts).

Stamping: prior head `invalid_at` == new head `valid_at` == `corrections.valid_at` == the
event's `client_timestamp` (world time of the confrontation) — the coherent-chain-timeline
precedent; windowed SQL re-derives the pre-event telling with no gap or overlap at t_e.
`created_at` everywhere is server `now()`.

**What is deliberately absent**: no pin check (§8 final ruling — both correction verbs
outrank pin; the new head inherits it structurally since pin lives on `memories.pinned`,
untouched; a pinned memory then serves the new head verbatim and never grows
reconstruction rows). No drift check (event-driven writes are exempt — the exemption is
the absence of code). No fact-chain statements (ruling 3). No `memories`-row writes.

**The deferred window** (C1 interaction, zero new code): confronting an un-enriched row is
legal — NULLs resolve via the neutral/default ladder above, and the raw head IS the
un-enriched head, superseded like any other. If enrichment completes after the event, the
completion's already-moved guard (`deferred-writes.md`: "a retelling or correction
superseded the raw head first → SKIP, facts-only") leaves the diegetic head standing.

## Wire

**`DiegeticCorrectionEvent`** — `agent_id`; `memory_id`; `challenge_text` (min length 1);
`challenge_typology` (REQUIRED — client declaration wins, no hardcoded default);
`challenge_weight` float|None in [0, 1]; `client_timestamp` (tz-aware); `source_event`
dict|None (stored verbatim); `expected_detail_id` UUID|None (opt-in CAS);
`event_id` str|None (idempotency key: accepted, not enforced — the namespace convention).

**`DiegeticCorrectionResult`** — flat, instrumentation rides the response (the
`CorrectionResult` no-runs-table precedent; the `corrections` row is the persistent
record): `memory_id`, `agent_id`, `verb`, `correction_id`, `detail_id`,
`superseded_detail_id`, `pinned`, `content` (the new head), `resistance`, `challenge`,
the resolved inputs (`importance_norm`, `rigidity_effective`, `typology_mult_memory`,
`typology_mult_challenge`, `challenge_weight_effective`), `evicted_cache_rows`,
`retell_ms`, `retell_input_tokens`, `retell_output_tokens`, `total_ms`.

**Error ladder** (the authorial fail-loud shape): 404 unknown memory OR memory not owned
by the event's `agent_id` (from that agent's world it does not exist) · 409 CAS conflict,
rollback proven · 422 validation (naive timestamp, unknown typology literal, out-of-range
weight, empty challenge) · 502 retell failed/malformed, nothing written.

## Surfaces (ruling 6)

- **REPL `:confront`** (`app\session.py` + `app\cli.py`, the `:correct` shape, session
  effective time): prints the verb, both sides of the decision with their resolved terms,
  the IDs, and the eviction count — the CLI stays the debug product surface.
- **Chain inspector**: `GET /v1/memories/{id}/chain` gains a `corrections` block
  (`db.fetch_memory_chain` grows the SELECT; `MemoryChainResult.corrections` defaulted, so
  the read stays additive). The Ledger and the demo can show the confrontation record
  without SQL. The inspector remains unscored *by contract* (no retrieval runs).
- **C# mirror**: `Models.cs` record pair (+ the chain-result corrections mirror),
  `NpcMemoryClient.DiegeticCorrectAsync`, an `NpcSession` wrapper stamping session
  effective time, and new console-harness interop beats. The committed Unity DLL goes
  stale as usual; its staleness check stays Phase F's.

## Knobs (all in `SERVICE_DEFAULTS`, floats, `agent_knob` contract)

| Knob | Default | Meaning |
| --- | --- | --- |
| `dissonance_typology_observed` | 1.0 | "I saw it" — the reference class, both sides of a clash. |
| `dissonance_typology_told` | 0.6 | Hearsay folds easier and pushes weaker. |
| `dissonance_typology_inferred` | 0.4 | The weakest evidence class. |
| `dissonance_typology_reflected` | 0.5 | Derived belief (C2 output typology). |
| `dissonance_rigidity_default` | 1.0 | Only when `agents.rigidity` IS NULL (the column has no default by design); clamped [0.5, 2.0]. |
| `dissonance_challenge_weight_default` | 1.0 | When the event omits `challenge_weight`: a full-strength confrontation. |

Defaults are starting points for Phase D tuning, not measurements. **No
`dissonance_enabled` kill-switch, consciously declined**: unlike the background workers,
the event is client-invoked — not sending it is the off state (the asymmetry vs
`*_worker_enabled` is deliberate and recorded here). `agents.rigidity` stays the one
schema-level dissonance knob.

## Scope boundary — do NOT build

Automatic conflict/staleness detection (CUT 2026-08-04 — no scanning, no worker, no runs
table, no discovery of un-named contradictions). Fact-chain writes of any kind (ruling 3).
A new model role or env var (ruling 2). Habituation guards (CUT). A drift-budget check in
the event path (exempt by design). Migration 009 (ruling 3; applied migrations 001–008 are
immutable). Persisted decision numbers (the response carries them; the `corrections` row is
the record — widening it would be a migration). The DLL staleness fix (Phase F's). If
adjacent work looks necessary, stop and report — with the correct option and its real cost
stated.

## Test surface

**Set N** (`tests\test_set_n_dissonance.py`, ~20 structural scenarios, ALL unmarked — seed
at the db layer, never the NLP write pass): the Set A diegetic pair lands here (chain
intact; new head typed by verb; correction record present; cache evicted) — both verbs as
a structural pair keyed on `write_cause`, no fixture modes. Plus: chain preservation
(observation text, gist spans, fact chain byte-untouched; superseded tellings still
present); coherent timeline under windowed SQL; `source_event` round-trip; CAS 409 with
rollback proven by row counts; 404 unknown/foreign memory; pin outranked + inherited with
verbatim serve; anchor semantics both verbs; drift exemption; the decision unit rows with
hand math; NULL-rigidity resolution; a per-agent knob override flipping the verdict;
mid-scene text change then restored byte-identity; retrieval untouched (candidates still
rank by the original basis); route pass-through + the ladder over the wire (ASGITransport);
`event_id` accepted-not-enforced; failing/malformed reconstruction provider → 502 nothing
written; the deferred-window interaction (pending row confronted → drain → diegetic head
stands, completion facts-only); two sequential events stacking heads and corrections rows.

**The eleventh walker** (`tests\verify_dissonance.py`, the `verify_compiler.py` skeleton,
target ~40–48 assertions, re-runnable on the persistent scratch — unique agent names per
run): A. schema probe — corrections columns/FKs/index, CHECK teeth by junk-insert
rollback, the fact CHECK REJECTING the diegetic verbs, the ledger still 001–008 ·
B. the verb ladder — extremes, the exact tie, NULL rigidity, a config-override verdict
flip, hand-recomputed numbers in the response · C. chain/eviction/anchor — preservation,
the corrections row, the coherent timeline, update re-anchors / rationalization never,
drift exemption · D. the read-path effect — pre-theta new-head serve, post-theta
reconstruction under the ruling-4 constraint, pinned verbatim, mid-scene change then
byte-identical re-reads · E. pin/CAS/error ladder — rollback row-count proof, ownership
404, 502 nothing-written.

**Deliberately re-opened floor**: `verify_reconstruction.py` grows the ruling-4 assertions
(an `update_with_resentment` anchor takes the fixed-constraint branch) and re-closes
before the build proceeds past that stage.

## Done-when (what the independent floor-verifier re-checks)

1. The no-migration scope fact holds: `db\migrate.py` no-arg is a clean no-op ("Up to
   date: 8 applied, 0 pending"); corrections CHECK teeth probed; the fact CHECK still
   rejects the diegetic verbs (walker A).
2. The decision end to end: both extremes, the exact tie defending, NULL-rigidity
   resolution, a per-agent override flipping the verdict — hand math matches the
   response's resolved inputs (walker B).
3. Both verbs' chain shape: prior head superseded, new head typed by verb, corrections row
   present with `source_event` round-trip, cache evicted, coherent timeline — atomically
   (walker C; the Set A diegetic pair lands).
4. Anchor semantics: update re-anchors, rationalization never; no drift-budget code in the
   event path (walker C).
5. The read-path effect: the sanctioned mid-scene change then restored byte-identity; pin
   outranked and inherited with verbatim serve; post-event reconstruction under the
   ruling-4 fixed constraint; `verify_reconstruction` re-closed at its grown count
   (walker D).
6. The error ladder loud: 404 unknown/foreign, 409 with rollback proof, 422 shapes, 502
   with nothing written (walker E).
7. The surfaces live: `:confront` prints verb/numbers/IDs; the chain read carries the
   corrections block; the interop gate green at its new pinned count; both C# builds
   0-error/0-warning.
8. Suite green both modes at the pinned counts; the eleven walkers green serially on a
   fresh `longmem_test` (`verify_reflection` on its own fresh scratch); the ten prior
   walkers byte-untouched at their criteria EXCEPT the deliberately re-opened
   `verify_reconstruction`; the product `longmem` DB pristine (ledger 001–006, zero
   corrections rows).
9. Believability: an explicit no-regression verdict vs the 2026-08-07 baseline.
10. The eight rulings recorded in `decisions.md`; floors row 28 only on the verifier's
    pass.
