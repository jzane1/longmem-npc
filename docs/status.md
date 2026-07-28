# longmem-npc — Status

**Last updated:** 2026-07-28
**Phase:** **immediate-queue item 2 is BUILT end to end — backend, C# client, Unity scene, and
The Ledger all stand.** Stages 0–3 landed 2026-07-27 across four sessions: the three ruled-in
routes (SSE `POST /v1/dialogue/turn/stream` over the SAME async-generator seam, `POST /v1/agents`
provisioning, and the two unscored inspector reads), then `client\NpcMemory.Core` + the console
harness (**interop gate 21/21**), then the Unity adapter + gray-box set (**Play-mode gate 8/8**,
chunk callbacks on the main thread), then The Ledger at `GET /ledger`, which rendered a real
corrected chain in the browser — original greyed → correction greyed → reconstruction live.
Schema frozen at migrations 001–005 throughout. **Eighteen floors stand verified**
(`docs\floors.md`).

**2026-07-28 — full-repo audit + remediation.** Seven read-only dimension auditors plus an
adversarial verification pass over their findings; four refuted (two because the "problem" was an
existing dated ruling of Jack's). The audit's own verdict on the codebase was that it is in good
shape — zero prose assertions across the suite and walkers, every UPDATE/DELETE sanctioned, `.env`
never in any git ref, the C# client mirroring all 30 wire models field-for-field. The pass fixed
one real defect and a systematic layer of drift:

- **The SSE consumer stalled the Unity main thread.** `NpcMemoryClient` drove its SSE loop off
  `StreamReader.EndOfStream` — a synchronous read — on a client that deliberately has no
  `ConfigureAwait(false)`, so it blocked between chunks on exactly the path the <1 s
  perceived-first-word beat runs on. Fake-mode streaming is fast enough that the Play-mode gate
  passed 8/8 with it present.
- **Verification gaps closed:** `PUT /pin` and `POST /events/scene-boundary` had no HTTP test at
  all; the SSE `reconstructing` and `error` events had none; `CorrectionNlpFailedError` → 502 was
  ruled and built with neither a test nor a spec row. Suite 49 → 53, keyless subset 46.
- **Gates now match the rules that claim them:** `ruff` was unpinned (the one mechanically-enforced
  tool — and already drifted), `ruff check` had never run as a gate, the `.env` deny covered one
  tool, and floor-verifier's allowlist excluded the Unity MCP.
- **Propagation caught up:** `architecture.md` knew nothing of the five routes shipped 2026-07-27;
  the IDs-and-scores invariant was false as written for the two unscored inspector reads; the
  register still called a closed decision open. This file was split three ways (below).

Remaining before recording: an independent floor-verifier pass over stages 2–3's re-runnable
halves, demo choreography + the demo corpus, the B1/B2 latency experiments, and the judged eval
harness (item 3).

**Prior phases:** the stacked phase blocks moved to `docs\session-log.md` ("Archived phase headers") on 2026-07-28 — they are era summaries, not live state.

This is the *living* file — update it at the end of every working session. `architecture.md` changes
only when design changes; `decisions.md` is append-only.

## Deadline & framing

Single-call demo video: **mid-to-late August 2026**. Do **not** sacrifice vital features or quality
for the deadline — flag deadline pressure when relevant, but never let it drive a decision without
Jack's explicit confirmation. Portfolio target: tier-1 embodied-agent / game-AI employers. Artifact
roles are distinct: the demo video gets the introduction; the instrumentation table, the test suite,
and the structured behavior output survive the interview. Research publication comes after the demo.

## Build discipline

- **Vertical slice before depth; CLI before Unity.** First end-to-end path — event in → memory
  stored → dialogue out — is a console harness: no gate, no caching, no reflection. The CLI is the
  product surface (main file readable as documentation; debug mode exposes retrieved memory IDs,
  scores, parsed structured output, token counts). Unity is the demo; the gray-box scene recorded is
  the fallback video.
- **Staged verification:** each layer verifies against a known-good layer beneath it, so failures
  have a single cause. Anything renamed or ported is re-verified before it counts as a floor.
- **Storage before cognition. Instrument at the seam.** Framework choices must survive the
  interview; ceremony scores below absence.

## Verified floors

**Eighteen floors stand verified.** The full table — layer, what it was verified against, and
the date — moved to **`docs\floors.md`** on 2026-07-28 so this living file stays small enough
to auto-load. That file states the counting convention; cite it rather than a number in prose.

A row lands there only after an independent floor-verifier pass returns **pass**. Floors are
re-openable: re-verifying one is a step, never an argument against a design improvement.

## Open questions needing Jack's ruling

*One open. Closed items move to the "Recently closed" note below rather than staying at the top
of this list (tidied 2026-07-28: the escalation item had led this section since it closed on
2026-07-23).*

- **R7 — the self-referential drift budget (logged 2026-07-22 from the external-persona audit).** The
  reconstruction drift budget is cosine candidate-vs-anchor < 0.35; it cannot catch a retelling that
  stays under budget while dropping or contradicting a gist fact, or fabricating a never-observed
  detail. Challenges the 2026-07-17 drift-metric/threshold ruling. **Deferred to the Unity/eval build
  phase (ruled 2026-07-22)** — not acted on now; the fixed-gist-constraint ON/OFF ablation (in the
  pre-demo judged-eval work) produces the deciding data, and any metric/threshold change waits on it.

**Recently closed** (kept as pointers so the trail is short, not gone):

- **Escalation failure path + trigger set / thresholds — CLOSED 2026-07-22 / 2026-07-23.** The
  failure path became a soft-degrade (migration 005). The trigger half was measured, then ruled:
  the fire rate is **productive** (85% of fires add real gist content, ~$0.15/100 observes), the
  shipped defaults stand, and a sixth **thin_gist** span-floor trigger closed the measured
  zero-gist hole (16/80 observes had landed with no gist spans). See "Escalation trigger tuning"
  in `decisions.md`.
- **Reconstruction flagged shapes — confirmed 2026-07-17.** See "Reconstruction flagged-shapes
  confirmations" in `decisions.md`.

## Session log

Moved to **`docs\session-log.md`** on 2026-07-28 — ~19.4k tokens of narrative history that
rode into every session's context. Append one entry per session there, at the end, in the
honest landed/blocked/abandoned wording `/wrap-up` asks for.

## Immediate queue

**Pre-demo build path — re-planned 2026-07-22 from the external-persona audit**
(`external-audit-2026-07-22.md` + `external-audit-2026-07-22-solutions.md`; three rulings in the dated
`decisions.md` entry). The audit's #1 finding, confirmed against source: **`app\api.py` has no HTTP
dialogue-turn route** — the cognition layer is REPL-only, and Unity is C# over HTTP. *(CLOSED
2026-07-23 — item 1 below is built and floor-verified; the route is live.)*

0. **Unblock real mode — DONE (verified 2026-07-22).** Jack fixed the malformed `.env` price line and
   `LONGMEM_MODEL_BEHAVIOR` is present (prior thread); verified via `config.load_settings` (no values
   printed): all eleven `LONGMEM_PRICE_*` keys parse, provider mode `real`, `load_settings()` OK. The
   2026-07-21 flagged crash is resolved; real mode is unblocked for the real-providers-only demo.
1. **HTTP dialogue-turn route + honest latency metric — DONE (built + floor-verified 2026-07-23).**
   `POST /v1/dialogue/turn` is live (stateless, non-streaming, 404/422, pass-through), with
   `perceived_first_word_ms` beside `first_word_ms` — the <1 s bar's field — surfaced in the CLI
   debug line + the driver series. SSE `/turn/stream` still rides later on the SAME generator (no
   rewrite). The thread-pool cap is ruled deferred post-demo. See `floors.md` +
   session log; the build target is now item 2.
2. **Unity project + reference scene + The Ledger** — **demo vehicle ruled 2026-07-27** (dated
   "Demo-vehicle ruling" entry in `decisions.md`: Unity gray-box over an established-game mod; the
   five-agent panel — four audit personas + a modding-landscape scout — weighed it — Skyrim
   declined on zero C# reuse, the
   Mantella comparison class, state-delta observes, and AGPL). Spec: **`unity-client.md`**. The ruled
   sequence: **(i) `NpcMemory.Core` first** — engine-agnostic C# client (plain .NET, HTTP + JSON, the
   `NpcSession` port of `_apply_turn_result` with directive + reputation callbacks, zero `UnityEngine`
   types, one flat client class), driven by a `dotnet run` **console harness playing every demo beat
   headless — the Unity↔backend interop go/no-go moves to Wk-1** (was Wk-2; zero `.cs` today).
   **(ii)** Unity = a thin MonoBehaviour adapter + the gray-box scene as the **intended**
   systems/dev-tool aesthetic (a set, not a game — art-risk stays off the critical path); connect MCP
   for Unity at this step (`mcp-setup.md`; verify the bridge early — scene-manipulation operations
   fail during Play mode). **(iii) The Ledger = a browser page** over the existing HTTP API (not Unity UI), composited
   in OBS: original vs current telling side by side + `read_mode`/scores/IDs + superseded rows
   greyed-but-present + a real gist/detail number on screen — bound to the same `DialogueTurnResult`
   fields the eval harness scores. **Off-camera cache warm-init** (fire `/v1/dialogue/init` at each
   scene basis during camera cuts) removes the 9–16 s cold stall with zero pre-warm code. Beats:
   **lead with correction-override**, then **reconstructive drift (constancy-first — gist flat,
   detail thinning)**; the split-brain divergence is a **separate interview clip** (ruled
   2026-07-22), not a main-video beat. The game-authored action-observe beat + async observes (old
   pre-ship (d)) ride here. **All seven spec forks ruled + stage 0 BUILT and floor-verified
   2026-07-27** (dated "Unity-client fork rulings + stage-0 build" register entry): SSE
   `/turn/stream`, `POST /v1/agents`, and the chain/index inspector reads are LIVE; Newtonsoft
   everywhere; netstandard2.1 core + net8 harness layout; static-HTML Ledger; MCP for Unity
   verified. **ALL FOUR BUILD STAGES LANDED 2026-07-27**: stage 1 (`NpcMemory.Core` + console
   harness — the Wk-1 interop gate 21/21, floor-verified; the C# null-vs-absent proof runs live
   in the gate), stage 2 (Unity adapter + gray-box set — Play-mode gate 8/8), stage 3 (The
   Ledger at `GET /ledger` — live browser beat, suite 49). Remaining for this item: the
   independent verifier pass over stages 2–3's re-runnable halves (next session's opener), then
   **demo choreography + the demo-corpus register** (shipped-game dialogue style + the held-out
   eval arm). The REPL still drives all beats today (`:as-of` jumps + scene boundaries + band
   crossings; `:correct` moves retrieval AND entities; the gate debug line + `(reconstructing…)`).

**Pre-ship latency items** (2026-07-21 latency slate; **audit re-sequenced 2026-07-22** — the
   perceived-TTFT metric moved into item 1; pre-warm build proposed post-demo):
   - **(a) escalation failure path — BUILT 2026-07-22 (soft-degrade; migration 005).** The fail-loud
     hard-stop is retired: a gist-escalation double failure now proceeds with the base NLP-pass gist and
     sets the dedicated `memories.escalation_failed` flag — never a lost write (`EscalationHardStopError`
     + its observe-route 502 removed; suite 42 green). **Still open (separate, non-blocking):** the
     trigger-set/threshold tuning — escalation fires on **79% of realistic prose** (importance p50 0.61
     vs the 0.45 threshold; +1.4 s + ~$0.0021 per fire), a cost/latency item and latency lever **D**'s
     server half.
   - **(b) B1/B2 dialogue-latency experiments** against the <1 s first-word bar:
     haiku-dialogue A/B is a zero-code env swap; thinking-off variants on the sonnet-5 calls
     are one-liners needing a ruling. Measure, then rule.
   - **(c) C1 scene-boundary reconstruction pre-warm BUILD → CONFIRMED POST-demo (ruled 2026-07-22).**
     The demo's 9–16 s cold stall is removed by off-camera warm-init choreography (fire
     `/v1/dialogue/init` at each scene basis during a camera cut; within-scene byte-stability ⇒ identical
     on-camera bytes), so the full pre-warm build is not demo-blocking. This relaxes the latency slate's
     "all pre-demo" wording for C1. (The scene-frozen cache key still supports the full background build
     when it lands post-demo.)
   - **(d) D async observes** (client contract): the Unity client fires observe events
     without blocking dialogue — the 3.4 s real observe is throughput, not latency.
   *(Done 2026-07-21: the old **(b) real-provider smoke** and **(c) real-mode profiling
   re-run** — receipts + headline numbers in the session log; artifacts scratchpad-only.)*

*(Research-adoption queue — slated 2026-07-21 with the landed slate, each its own
spec/build session; ordering after the Unity/pre-ship items is Jack's to re-slate. Papers per
item are traced in `docs\research\CHANGES-FROM-RESEARCH.md`.)*

3. **Judged eval harness v1 — PULLED PRE-DEMO (ruled 2026-07-22 with the Ledger scope).** Judge
   model role/env var + LLM-judged categories (judged signal real-mode-only — sequenced with that).
   **Audit additions:** (i) a judge-free gist-precision/detail-recall metric (from existing gist spans +
   spaCy, no judge call) feeding The Ledger's on-screen numbers; (ii) a small **hand-labeled gold set**
   so the judge has proven rigor (judge-agreement / meta-eval); (iii) the **fixed-gist-constraint ON/OFF
   ablation** — turns the self-referential drift-budget hole (R7) into a shown finding; (iv)
   **real-embedding drift validation** of the demo memory, run EARLY (Wk3, not Wk4).
   Starter categories: selective-forgetting single/multi-hop (MemoryAgentBench 2507.05257),
   abstention/premise (LongMemEval 2410.10813, LME-V2 2605.12493), reconstruction FactScore
   **retargeted** — gist-precision stays ~100%, detail-recall may decay (LoCoMo 2402.17753),
   FAMA stale-leakage (2604.20006), MemTrace trajectory probe + reach-vs-use attribution
   (2606.17328), and the judge-free keyword-retention check (2511.10277) which fits the
   structural suite today. Harness shape: Insert/Query over the existing session-runner loop;
   accuracy-vs-latency Pareto reporting.
4. **Graph/associative memory** — spec session with the de-risked design notes: Postgres-native,
   no graph DB (SPRIG 2602.23372 — app-side seeded PPR is sparse linear algebra);
   concept-mediated edges against `identity_components`, NOT raw entities (GAAMA 2603.27910 —
   entity graphs mega-hub, concept graphs stay ~30× sparser); bi-temporal edge supersession is
   our extension (edges from live heads only; corrections re-derive); the lexical channel
   (Target B) is the hybrid seeding base; graph term = a small additive nudge (GAAMA's 0.1
   ablation). Cheapest first step: HippoRAG's node-specificity IDF on the entity tripwire.
5. **Recall-reinforced decay** — spec session (ruled 2026-07-20: its own session). The "what
   counts as recall" fork + a migration; must not conflate decay with invalidation (invariant)
   nor break within-scene byte-identity. MemoryBank 2305.10250; survey 2512.13564 §5.2.3.
6. **Automatic conflict/staleness detection** — spec session; the write-time counterpart of the
   dissonance path. STALE 2605.06527 (CUPMEM-style adjudication riding `identity_components`);
   Nous 2606.22030 (trust provenance-capped, never content-inferred — maps to
   `typology`/`typology_source`); MemConflict 2605.20926 (taxonomy + near-floor SOTA = a
   differentiator). Non-destructive: detection routes through supersession, never delete.
7. Smaller queued notes: the reflection design dossier (ground reflective writes in cited
   memory_ids + an RRR repetition detector — honest-lying 2605.29463; periodic
   evidence-conditioned identity refresh — AI-YOU 2607.10539; persona-lensed retrieval routing
   — self-reports; idle-time scheduling — sleep-time 2504.13171); richer `seed_identity`
   authoring guidance (interview-depth beats a persona paragraph, self-reports study); the
   Whisper soft-steering hook + safe-default action fallback for the Unity C# API surface item
   (bounded-autonomy 2604.04703).

*(Done 2026-07-23: **HTTP dialogue-turn route + perceived-TTFT v1** — the Unity/C# front door +
the honest retrieval-inclusive latency metric; see `floors.md` and `session-log.md`.
Done 2026-07-21: **Split-brain streaming v1** — concurrent streaming-prose + behavior calls
off one retrieval, two scored views + the divergence record, the new `behavior` model role;
first word = prose TTFT. Also done 2026-07-21: **Encoding-context read term v1 +
gate-calibration utility** and **Hybrid lexical retrieval channel v1 (migration 004)** — the
research-adoption slate's two targets; see `floors.md` and `session-log.md`.
Done 2026-07-20: **Structural pytest suite v1** — 38 scenarios green, the Stop hook live
on the `-m "not nlp"` subset; see `floors.md` and `session-log.md`. Done 2026-07-19: **Mid-dialogue gate v1** — retrieval is conditional; migration 003
applied; see `floors.md` and `session-log.md`. Done 2026-07-18: **Fact-level correction v1** — retrieval follows the fix; migration 002
applied; see `floors.md` and `session-log.md`. Also done 2026-07-18:
**Authorial-correction endpoint v1** — the correction-override beat is live;
see `floors.md` and `session-log.md`. Done 2026-07-17: **Reconstruction v1** — the
thesis mechanism is live; see the verified-floors
table and session log. Done 2026-07-15: **CLI harness v1 + synthetic load driver** — the vertical
slice completed. Done 2026-07-14: **Read path v1**. Done 2026-07-13: **Write path v1**; earlier
same day: **Migration 01 foundational schema**; connect the Postgres MCP + floor-verifier MCP
access.)*

## Open artifact queue (writing tasks against settled decisions — not decisions)

- Event-ingestion API contract — **v1 subset specced in `write-path.md` and now BUILT** (observe +
  scene-boundary + pin/unpin; phase tag and event_id accepted without a schema home; idempotency
  accepted-not-enforced). Still to spec/build: the diegetic-correction event (references a target
  memory_id; mechanism post-August) and purge (post-August, before the public flip — ruled
  2026-07-14). Scene-boundary's consumers were slated 2026-07-14: reputation snapshot → the
  dialogue turn (**landed 2026-07-15** — the session-runner re-reads `agents.reputation` at each
  boundary), identity recompile → reconstruction (**landed 2026-07-17** — the handler recompiles
  server-side and returns `identity_version`), prompt-head rebuild → post-August.
- Retrieval scoring function: relevance × recency(decay class) × importance_norm; pin exemption;
  normalization; slots for the future context term and per-call split-brain overrides *(both
  slots since ruled live: context landed 2026-07-20; behavior-view overrides **built**
  2026-07-21 — split-brain streaming)*. —
  **Consolidated into `read-path.md` 2026-07-14 and now BUILT** (shapes ruled at build; dated
  `decisions.md` entry).
- Reconstruction call spec: operator-structured prompt with gist as fixed constraint; determinism;
  batching shape. — **Consolidated into `reconstruction.md` 2026-07-17 and now BUILT** (built &
  floor-verified the same day; shapes ruled at build; dated `decisions.md` entry).
- Reflection spec end-to-end (mechanism explicitly post-August — ruled 2026-07-14).
- Gate threshold values + efficacy definitions wired to instrumentation. — **Consolidated into
  `mid-dialogue-gate.md` 2026-07-19 and now BUILT** (same day; thresholds ruled with the build
  plan; the efficacy comparators live in `GateInstrumentation` + the load-driver gate block;
  instrumentation-only fire logs as ruled).
- Unity client C# API surface: send event, open dialogue, directive callback, reputation read,
  reconstructing-signal hook, scene-boundary emission. *(Grown by the 2026-07-21 split-brain
  spec: the SSE streaming route + the game-authored action-observe contract land here.)*
  *(Shape ruled 2026-07-27: engine-agnostic `NpcMemory.Core` — zero `UnityEngine` types, one flat
  client class — + a thin Unity adapter; consolidated into `unity-client.md`.)*
  *(Stage-1 observation 2026-07-27: no HTTP agent-state read exists — the C# session refreshes its
  boundary reputation snapshot from the last turn's `reputation_after`, exact for a single-client
  session; a multi-client integration wants a small read route. Future surface item.)*
- Demo choreography: injected-timestamp time travel; decay + correction-override + gate-recollect
  beats; the 60-day drift plot — a planned beat since the 2026-07-14 re-slating (reconstruction is
  pre-demo). *(Grown 2026-07-21: the game-authored action-observe beat —
  `split-brain-streaming.md`.)*
- README destructive-compression counter-example pick.

## Sequenced-later ledger (pull-forward eligible)

*Sequencing orders work; it never rules an option out of a design discussion. Any item here may
be pulled into the immediate queue by a dated ruling when a current target shows it is
architecturally load-bearing — the 2026-07-14 reconstruction re-slating is the template.
(Reframed from "Post-August ledger" by the 2026-07-17 "Scope-limiter reframing" ruling in
`decisions.md`.)*

Reflection pipeline mechanism (sequenced post-August — hedge resolved 2026-07-14; the pre-demo
identity document is seed-prose-only); dissonance path + the diegetic suite pair; the purge
endpoint (before the public flip — ruled 2026-07-14); prompt caching / prompt-head rebuild
(revisit when a target needs it or demo latency demands — reframed 2026-07-17 from the ruled
"only if demo latency demands" wording); habituation *(the encoding-context read term itself
landed 2026-07-21 — Target A)*; **Engram-style deferred write cognition** (own spec target,
ruled onto the ledger 2026-07-23 — raw observe stored immediately, gist/enrichment at the
service's own timing; the existing degradation flags are the natural deferred-work queue; forks:
add-only gist annotation vs the frozen write-time facts, the un-enriched-window retrieval
contract, a new `write_cause` = a migration; Engram 2606.09900 + the sleep-time-compute family —
the async-observe client contract covers the latency motivation and the thin_gist trigger covers
correctness inline, so this is a cost/throughput optimization); **the established-game
integration clip** (ruled 2026-07-27 — post-demo, the split-brain interview-clip template: a
C#-moddable game reusing `NpcMemory.Core` — Stardew/SMAPI days-scale or RimWorld's rich event
stream — NOT Skyrim: zero C# reuse, the Mantella comparison class, AGPL on a published fork);
reflection → parameter compiler;
Unity Package Manager packaging; docs final + public flip
(Apache-2.0). *(Reconstruction — mechanism, drift budget, Set C scenarios — moved off this ledger
into the immediate queue by the 2026-07-14 re-slating ruling.)* *(Split-brain topology with per-call
weights — moved off this ledger into the immediate queue by the 2026-07-21 latency-slate
ruling, the second use of the pull-forward template; specced AND built same day,
`split-brain-streaming.md`.)*

**Research track:** asymmetry ablation (on/off, judge-measured explanation-cause divergence); judged
drift / Bartlett-style evals; unified-thesis write-up (identity-conditioned reconstructive memory +
information-asymmetric cognition).

**Later / optional:** disclosure gate; full modulator suite for the parameter compiler;
faithful-vs-reconstructive dual read modes; the dormant-agent memory-injection overseer (next
project; wake trigger = context match); local-model packaging (note: a second embedding model
collides with the locked 1536 dimension).

## Repo conventions

Private GitHub; commit at least weekly; public flip is an end-of-project sprint. Secrets in `.env`
only. Always PowerShell, backslash paths.
