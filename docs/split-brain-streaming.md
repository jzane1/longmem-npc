# Split-brain streaming — build target (specced 2026-07-21)

> **Status: SPECCED, not built.** Pulled forward off the sequenced-later ledger by the
> 2026-07-21 latency slate ruling (dated "Latency slate + split-brain pull-forward rulings"
> entry in `decisions.md`; the 2026-07-14 reconstruction re-slating is the template). The
> real-mode profiling session measured the player-facing turn at p50 ~4.1 s with first token
> 1.4–2.2 s, against Jack's ruled viability bar of **first word < ~1 s**. This target makes
> perceived latency ≈ prose time-to-first-token and lands the whole §9 split-brain topology —
> **with a ruled alteration** (below). The companion pre-ship levers (B1/B2 model/thinking
> experiments, C1 scene-boundary pre-warm, D async observes + the escalation trigger re-rule)
> are separate queue items; this spec deliberately does not absorb them.

## The ruled topology alteration (supersedes-in-part §9's serial sketch)

§9 as written sketched: behavior call first, then the dialogue call sees *that turn's* chosen
action as observed world fact. Ruled 2026-07-21 (Jack): **the prose call never needs the
current turn's action — it sees PAST behaviors as world facts** ("why did you do that a
minute ago / a week ago"). Therefore the two calls run **concurrently within a turn**, and
the current turn's action enters the world record for *subsequent* turns via two mechanisms
(both ruled):

1. **Durable ("a week ago") — game-authored action observes.** The integrator reports what
   *actually happened* as an ordinary observe event (the endpoint exists; the directive is an
   intent — only the game knows whether the warn landed or was interrupted). The store never
   records unresolved intent. This is a documented integrator contract, not code.
2. **Within-scene ("a minute ago") — the caller-held recent-actions block.** The session
   runner appends each turn's resolved directive to caller-held scene state (the
   reputation-snapshot trust class), renders it as a labeled block in the prose prompt, and
   resets it at scene boundaries. Never stored server-side.

**Accepted design fact (ruled, instrumented):** with concurrency, one turn's words and action
are chosen independently — occasional same-turn incoherence is the split-brain character, not
a bug. It is bounded by the shared retrieval inputs and the action vocabulary, self-corrects
from the next turn via the recent-actions block, and is **instrumented from day one** so
explanation-cause divergence (§13's research angle) is measurable: the turn result records
both calls' scored views and the directive, structurally.

## Principles this build honors

- **First word is the product metric.** The seam yields prose incrementally; `first_word_ms`
  (prose TTFT at the seam) joins §11's histogram as the headline latency term. This spec gets
  first word = TTFT; pushing TTFT under 1 s is the B-lever queue items' job.
- **One retrieval, two scored views.** The existing retrieval pipeline (gate/loader, lexical
  union, context term, reconstruction serving) runs exactly once per turn, untouched. The
  behavior call's view re-scores the *same candidate set* with resolved per-call weights —
  the reserved `WeightOverrides` slot goes **live for the behavior view** (ruled: now, via a
  second scoring pass). Dialogue-view scoring stays byte-identical to today when no overrides
  are supplied (the context-term parity precedent).
- **Asymmetry statistical, not architectural** (§9): same candidates, different weights, no
  masks. The behavior call carries its own model role env var; the dialogue call sees only
  past actions, never the behavior call's rationale.
- **The action-directive contract survives unchanged** — it was written for this migration
  (`cli-harness.md`): `{type, params}` as observed world fact, per-call vocabulary wins over
  `agents.config`, unknown/unparseable directives drop soft, the turn still succeeds.
- **Reputation semantics unchanged.** The behavior call emits the delta (§9's shape, now
  live); the atomic clamped in-place UPDATE, client-override-wins, sensitivity, and the
  scene-start snapshot are untouched. The delta applies when the behavior call returns —
  mid-stream is fine; the prompt snapshot is scene-frozen.
- **Never-blank extends to both calls.** Behavior-call failure or malformed output → no
  directive + zero delta + a degradation flag; the prose turn still returns. Prose failure
  before the first chunk → the existing fallback-line path.
- **Streaming stays in-process this slice** (ruled): the seam exposes the stream, the REPL
  prints it live (the demo-visible beat), the driver aggregates `first_word_ms`. The SSE/HTTP
  route rides with the Unity client item, where its consumer exists.
- **Nothing integrator-configurable is hardcoded:** the behavior model role env var, its
  optional pricing vars, weight resolution and clamps, the recent-actions block cap — service
  defaults + `agents.config` overrides via the existing knob patterns.
- **No schema need identified at spec time.** Recent-actions is caller state; action observes
  use the existing write path; the behavior call stores nothing. If the build surfaces a
  schema need, the path is migration NNN + re-verification — stop and report, per CLAUDE.md.

## Scope boundary — do NOT build

The SSE/HTTP streaming route (Unity item); seam auto-writing of actions (rejected — records
intent as fact); dialogue/behavior model
or thinking experiments (B1/B2, separate pre-ship items); scene-boundary reconstruction
pre-warm (C1, separate); prompt caching / prompt-head rebuild (sequenced-later ledger — not
part of the ruled slate); weight overrides on the **dialogue** view (stays inert there — the
read-path parity contract holds); the reflection parameter compiler (§10); any new migration
absent a build-surfaced need.

## Mechanism

### Turn pipeline

```
utterance ─ retrieval (once: gate/loader + lexical + context + reconstruction serving)
              ├─ dialogue view  = today's scored ranking (byte-identical, no overrides)
              └─ behavior view  = same candidates, second scoring pass w/ resolved weights
        ┌───────────────┴───────────────────┐   (fired concurrently)
   prose call (dialogue role, streams        behavior call (behavior role: directive +
   PURE PROSE; prompt = identity + dialogue  delta as JSON; prompt = utterance + behavior
   view + reputation snapshot + recent-      view + reputation snapshot + vocabulary)
   actions block + utterance)                      │
        │ chunks yield through the seam            │ on completion: validate directive
        ▼                                          ▼ (drop-soft), apply clamped delta
   first_word_ms at first chunk              behavior_ms, divergence record
```

- The prose call's output contract becomes **prose only** — no JSON envelope. Its stream is
  the player-facing text; `_lenient_json_text` parsing leaves the dialogue provider with the
  behavior provider.
- The behavior call's output contract is the JSON pair `{directive|null, reputation_delta}`
  (exact schema `[SETTLE-AT-BUILD]`), parsed with the hardened first-text-block + fence-
  tolerant helpers (2026-07-21 ruling).
- Turn completion = both concurrent legs settled (prose stream closed + behavior applied);
  the result carries everything today's `DialogueTurnResult` carries plus the new fields.

### Recent-actions block

Caller-held scene state: an ordered list of this scene's resolved directives
(`type`, `params`, turn timestamp), appended by the session runner from each behavior result,
reset at scene boundaries, size-capped (`[SETTLE-AT-BUILD]`, suggest last N=8). Rendered as a
labeled prompt block in the prose call only — world-fact phrasing, never "you decided to."

### Game-authored action observes (integrator contract, docs-only)

The integrator reports resolved actions as observe events in world-fact phrasing; the write
path treats them as ordinary observations (render, importance, entities, embedding — so past
actions are retrievable "a week ago" through the normal read path, decay and all). The demo
choreography gains this beat; the Unity client surface item inherits the contract.

### Weights (the reserved slot goes live, behavior view only)

`WeightOverrides {relevance, recency, importance}` resolves per call: request field →
`agents.config` → 1.0 defaults; clamp bounds `[SETTLE-AT-BUILD]`. Applied as a second scoring
pass over the same candidate rows (same context factor), producing the behavior view's
ranking. The read-path walker's "weight_overrides inert" assertion re-scopes to "inert for
the dialogue view; consumed for the behavior view" — a ruling-driven walker change to state
at build (the context-term criterion [7] precedent).

### Instrumentation (instrument at the seam)

- `first_word_ms` (prose TTFT at the seam), `prose_stream_ms` (total), `behavior_ms`,
  behavior token counts + optional priced cost row (its own `LONGMEM_PRICE_*` pair).
- **Divergence record** (ruled): both views' ranked `(memory_id, score)` tuples + the emitted
  directive + delta on the turn result — structural, prose-free, the §13 ablation's raw data.
- Driver: `first_word` series joins the histogram; behavior series + split cost rows; the
  suite/walkers assert structure only, as ever.

### Degradation ladder (new rows)

| Failure | Behavior |
|---|---|
| Behavior call fails / malformed twice-soft | No directive, zero delta, flag; prose unaffected |
| Prose fails before first chunk | Existing never-blank fallback line |
| Prose stream drops mid-prose | `[SETTLE-AT-BUILD]` — suggest: keep the partial + degraded flag (partial prose is non-blank); alternative: discard + fallback line |
| Both fail | Fallback line + zero delta + flags (never-blank holds) |

## `[SETTLE-AT-BUILD]`

Behavior model role env var name (CLAUDE.md's role list already names `reputation` — adopt or
add a `behavior` role; one env var either way) + its pricing var names; the behavior call's
prompt + output schema; weight resolution clamps; recent-actions cap + block format; the
mid-stream failure row; the seam's streaming shape (async iterator vs the `on_reconstruct`
callback precedent); fake providers (chunked deterministic prose fake + behavior fake +
failure-injection variants); walker/suite shape (the CLI-harness walker re-opens — the seam
changes; the read-path walker's weight_overrides criterion re-scopes; reconstruction/gate
walkers expected byte-untouched — the retrieval pipeline is not touched).

## Done-when (the build's floor)

1. The seam yields the first prose chunk **before** the behavior call completes — proven with
   a deliberately slow behavior fake (concurrency, not sequencing).
2. `first_word_ms` ≈ prose TTFT; the REPL prints prose incrementally (live piped beat).
3. The behavior call's directive validates against the vocabulary with drop-soft semantics
   unchanged; the delta applies via the existing atomic clamped UPDATE (override wins,
   sensitivity, snapshot semantics — existing assertions still pass).
4. `ActionDirective` on the wire is byte-shape-identical to today.
5. The prose prompt carries the recent-actions block exactly when scene state has actions;
   reset at `:scene`; never stored server-side (no new writes proven).
6. Behavior view = same candidate set re-scored with resolved weights; dialogue-view scoring
   byte-identical to v1 with no overrides (the parity contract, walker-asserted).
7. The divergence record rides the turn result: both ranked views + directive + delta,
   structural.
8. All four degradation rows behave as specced — the settle-tagged mid-stream row as ruled
   at build (failure-injection fakes).
9. Schema untouched: no-arg migrate stays a clean no-op at 4 applied (or stop-and-report if
   the build surfaces a schema need).
10. Suite + all re-opened walkers green on fresh scratch; untouched walkers byte-identical;
    driver emits `first_word` + behavior series + split cost rows; floor-verifier pass.
