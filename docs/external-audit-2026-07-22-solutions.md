# External-persona audit — Solutions round (2026-07-22)

**Companion to `external-audit-2026-07-22.md`** (the critique + prioritized problem set R1–R8 + the
split-brain fork). This file is the *construction* half: the same four read-only personas, resumed with
full context, shifted from critique to concrete, creative solutions; the lead synthesized this forward
playbook. Same rules — advisory only; **(A)** = actionable within the current direction, **(B)** =
challenges a settled ruling → Jack's to rule; architectural decisions are Jack's alone.

*Verification note:* the load-bearing structural facts (no HTTP turn route; `run_dialogue_turn` is an
async generator yielding chunks then a terminal `DialogueTurnResult`; `DialogueTurnRequest` already
carries caller-held scene state; behavior view is byte-parity at default weights) were confirmed against
source in the critique note and this session. The **exact line numbers and code sketches below are the
personas' proposals to validate at build**, not lead-verified line-by-line.

---

## The headline: the whole forward plan is ~2 weeks of plumbing, then choreography

The four lenses converged on a plan whose surprising property is how *little new backend* it needs. The
cognition already exists; it just has no front door, and its demo beats are hollow at default config.
Close those two gaps and the rest is choreography, not code.

**One unified build order (reconciles all four personas):**

| # | Move | Tag | Effort | Owner-note |
|---|---|---|---|---|
| 0 | **R6 — fix the `.env` load crash** (malformed price line + add `LONGMEM_MODEL_BEHAVIOR`) | A / operator | minutes | First thing a hostile integrator hits; gates real mode |
| 1 | **R1 — `POST /v1/dialogue/turn` (non-streaming)** wrapping the existing async generator | A | ~½–1 day backend | The true critical path; loop already exists in `session.utterance` |
| 2 | **R2 — perceived-TTFT metric** (add `perceived_first_word_ms = now − t_total`) | A | ~½ day | Do it while in the seam; interview-credibility fix |
| 3 | **Minimal `NpcMemory` C# client + `NpcSession`** (ports `_apply_turn_result` bookkeeping) | A | ~week (Unity interop = the risk) | **Week-2 go/no-go gate** (zero `.cs` today) |
| 4 | **R3 — "The Ledger": ground-truth-vs-telling panel as a real judge-free measurement** | A | ~3–4 days | Reuses existing read payload (IDs/scores/`read_mode`) + immutable text; **no new backend** |
| 5 | **R5 — author non-default demo config + validate real-embedding drift EARLY** | A | ~1–2 days | Validate in Week 3, not Week 4 (late-discovery landmine) |
| 6 | **Demo choreography + off-camera cache warm-init** (kills the 16s stall, zero pre-warm code) | A | scripting | See below |
| — | R7 drift-budget fix; C1 pre-warm build; thread-pool async rewrite; judged harness; SSE | defer | post-demo | SSE and pre-warm are *additive*, never blocking |

**Skeptic's week-by-week:** Wk1 R6 + turn route + metric + real-mode smoke · **Wk2 (THE risk week)** C#
client + gray-box scene renders the full loop — *Unity↔backend HTTP interop is the single highest-risk
dependency; treat end-of-Wk2 as go/no-go* · Wk3 Ledger panel + **early real-embedding drift validation**
+ choreography · Wk4 record beats + guards + Wk2-slip buffer · Wk5 edit, fallback recording, interview
artifacts.

---

## Demo choreography (75s, split-screen: game left / **The Ledger** right)

Reconciles ceo's beat sequence, researcher's constancy-first framing, skeptic's per-beat guards, and
engineer's warm-init.

- **0–8s — Frame.** Positioning line on screen. *"Left: what the character says. Right: what they
  actually remember — and how."*
- **8–30s — BEAT 1: Correction-override (LEAD — the buyable beat, R4).** NPC holds a wrong belief; the
  designer corrects it. The Ledger shows the old fact **superseded, not deleted** (greyed, auditable),
  the embedding move, and the **next retrieval visibly pulling the corrected memory** (score jump; live
  proof reproduces the 0.4686→0.5637 move). *Guard:* rehearse the exact `:correct` on the demo DB; assert
  the relevance move reproduces.
- **30–55s — BEAT 2: Reconstructive drift (the thesis, made legible).** `:as-of +60 days` + scene
  boundary; same memory retold. **Constancy-first (researcher's reframe):** lead with the **gist line flat
  green ~1.0** ("the NPC is never wrong about what matters"), *then* reveal non-gist detail thinning
  (amber) with the R3 numbers on screen; `read_mode` flips to `reconstructed`. *"Not a hallucination —
  the record underneath is intact; the telling drifted, on a budget, on purpose."* *Guards:* off-camera
  warm-init (below) so no 16s freeze; real-embedding-validate that *this specific memory* actually drifts
  and does not refuse at the 0.35 budget.
- **55–72s — BEAT 3: Split-brain divergence (labeled "two brains" segment; see fork).** With authored
  `weight_overrides`, the NPC **says** something conciliatory (prose) but **acts** guarded (directive);
  the Ledger shows the two divergent rankings + the divergence record.
- **72–75s — Close.** Flash the real instrumentation table (perceived-TTFT / cost per 100 turns) +
  *"self-hostable: your Postgres, your models."*

---

## The four standout creative moves (the "be creative" ask paid off here)

1. **"The Ledger" (ceo) — turn the debug view into the product.** Reframe the legibility panel from a
   *crutch* (needed so drift ≠ bug) into the **hero surface**: a designer-facing memory inspector styled
   as a case file. It IS R3 and the on-screen legibility layer as the *same object* — and it's a tool a
   studio QA lead would pay for, which Convai/Inworld don't offer. Weakness → most buyable artifact.
2. **"The fallback is secretly the primary" (skeptic).** `CLAUDE.md` frames gray-box as the *fallback*
   video — invert it: ship gray-box as the *intended* systems/dev-tool aesthetic. To tier-1 game-AI
   reviewers a clean gray-box + a live ground-truth panel reads as infra maturity, and it removes all
   art/animation risk from the critical path.
3. **Turn the paper-killer (R7) into the thesis (skeptic + researcher).** Add a beat where the operator
   corrects a drift the *cosine budget could not have caught* (a silently-dropped gist fact). Framing:
   "reconstruction can drift inside budget in ways cosine can't see — which is *exactly why* the record
   underneath is immutable and the operator holds a correction verb." The hole becomes the reason the
   architecture exists — with zero eval harness built.
4. **Warm the cache during the camera cut (engineer) — C1's benefit, zero code.** Reconstruction already
   writes cache rows at dialogue-init and the cache key is scene-frozen. On each `:as-of`/`:scene` jump in
   the demo script, fire one throwaway `/v1/dialogue/init` at that exact basis off-camera; the on-camera
   first utterance then hits the ~3.7ms path and, by within-scene byte-stability, serves identical bytes.
   Honest (the cache holds genuine retellings) and the 16s never touches the recording.

*(Runner-up: researcher's **version chain as its own judge** — a gist fact present at retelling *t* and
absent at *t+1* is a timestamped, side-by-side contradiction event via pure set-diff over the write-cause
chain; the MemTrace trajectory probe almost no benchmark tests, and this architecture is uniquely built
to answer it — zero new dependencies.)*

---

## Concrete engineering spec (engineer — validate at build)

- **`POST /v1/dialogue/turn`:** because the seam already puts scene state in the caller, the route is
  **stateless** — body = the existing `DialogueTurnRequest` verbatim, response = `DialogueTurnResult`
  verbatim. Handler = the drain loop from `session.utterance` minus the runner bookkeeping (which moves
  client-side): `async for item in dialogue.run_dialogue_turn(req): if isinstance(item,
  DialogueTurnResult): result = item`. Add a `DialogueService` beside `RetrievalService` in the API
  lifespan; `UnknownAgentError → 404` (existing precedent).
- **SSE later, zero rewrite:** `run_dialogue_turn` is already an async generator yielding `str` chunks
  then the terminal result. A future `POST /v1/dialogue/turn/stream` iterates the *same* generator —
  `event: chunk` per str, `event: result` for the terminal JSON. One seam, two thin HTTP shapes: the
  payoff of the async-generator decision.
- **C# surface:** stateless `NpcMemoryClient` (DialogueTurn / Observe / SceneBoundary / Correct) + a
  stateful `NpcSession` holding the six scene-state fields, exposing `SayAsync(text)`,
  `OnDirective(ActionDirective)`, `OnReputationChanged(prev, after)`. The `(reconstructing…)` hook needs
  SSE — until then surface `reconstructing_blocked` post-hoc from the result; don't fake a during-wait
  signal.
- **Perceived-TTFT:** at the first-chunk site, capture one timestamp and compute **both** `first_word_ms
  = now − t_prose` (keep for series continuity) and `perceived_first_word_ms = now − t_total` (turn
  start, before agent fetch + retrieval). Measure the <1s bar against the new field. One schema field,
  one line.
- **Thread-pool cap (cheapest correct fix):** both legs share the default executor and the prose thread
  is held for the whole ~2s stream (caps concurrent NPCs ~6). Build one named
  `ThreadPoolExecutor(max_workers = 2 × maxConcurrentNPCs)` in lifespan and pass it explicitly to both
  `run_in_executor` calls. The real fix (async-native streaming client, zero threads held) is post-demo.

---

## Measurement / thesis (researcher — runnable now, real embeddings)

- **Judge-free gist-precision / detail-recall, no LLM extractor:** gist atomic facts are already
  structurally delimited (gist spans point into the immutable `observation_text`; spaCy lemmas already in
  `app/nlp.py`). *Gist-precision* = fraction of gist atomic facts present in the current chain-head text
  (the 2511.10277 retention check — fits the structural suite as-is). *Detail-recall* = fraction of
  non-gist content lemmas present. Bin by decay band using the cache's existing composed version key.
  **Control:** gist-precision flat ~1.0 across bands. **Infidelity:** detail-recall declines monotonically
  as the band deepens.
- **The R7-closer (fixed-gist-constraint ON/OFF ablation):** `assemble_reconstruction_prompt` is a pure
  function — run the same seeded set / bands / model / drift budget with the gist-constraint block **IN**
  vs **REMOVED**; measure gist-precision + **fabrication rate** (retelling entities absent from both the
  observation text and the identity doc — judge-free set diff). *Proves:* gist-precision ≈1.0 ON, drops
  OFF, **while cosine drift is near-identical in both arms** → demonstrates with data that the
  self-referential budget is blind and the *constraint* is the governance mechanism. *Kills:* gist drops
  even with the constraint ON → "controlled" infidelity is uncontrolled.
- **The one figure = demo panel = paper Figure 1:** x = decay band; two lines — gist-precision (flat
  green ~1.0) and detail-recall (monotone decline) — with fabrication-rate pinned near zero and cosine
  drift overlaid on a secondary axis showing it flat/uninformative. Fisher narrative-fidelity (gist
  bound) vs coherence, quantified.
- **Deferred to research phase:** a small off-the-shelf NLI model on gist sentences only
  (`contradict` on a gist span = governance failure) — targets R7's "contradicted fact" cheaply; the
  presence + chain-diff floor is enough for the demo.

---

## Split-brain fork — now largely reconciled

The critique framed this as CUT vs STAGE. The solutions round narrowed it:

- **Everyone agrees the main demo is coherent by construction at default weights** — `behavior_score` at
  1.0 returns `item.score` unchanged, so `behavior_view == dialogue_view`. The incoherence liability is
  **off by default with no revert needed**.
- **The remaining decision is small:** whether the *labeled* "two brains" divergence (authored
  `weight_overrides`, already live on `DialogueTurnRequest`) is (i) a beat inside the recorded video —
  ceo/engineer, staged with the Ledger and demotable to a 5s teaser if runway slips — or (ii) a separate
  ~20s interview clip / the paper's asymmetry ablation — skeptic/researcher. **Both keep the built floor;
  neither raw-ships it.** Recommendation to Jack: default the video to coherent single-call; treat the
  divergence as an *optional labeled segment* gated on Week-4 runway. **Jack's call.**

---

## Still needs Jack's ruling (unchanged from the critique)

- **(B) R7 — the self-referential drift budget.** The ON/OFF ablation above would turn it into a shown
  finding, but changing the metric/threshold challenges the 2026-07-17 ruling. Surfaced, not acted on.
- **Record the demo in real vs fake mode** (ceo strongly recommends real — the cost/latency table must be
  real to survive the interview; fake as fallback). Depends on R6.
- **The Ledger's presentation** — dev-overlay styled as a designer tool (ceo's rec) vs in-fiction UI.
- **The split-brain segment placement** (video beat vs separate clip), per the fork above.

---

## Appendix — per-persona solution summaries

- **ceo:** "The Ledger" hero surface; 75s split-screen choreography leading with correction-override;
  positioning line ("Convai/Inworld give an NPC a transcript it summarizes and forgets; longmem-npc gives
  it a psychology — auditable, correctable, drifts on purpose, never lies underneath"); ~2 weeks plumbing
  then Unity; STAGE split-brain conditionally, demote to teaser if runway slips; record in real mode.
- **engineer:** stateless `POST /v1/dialogue/turn` draining the existing generator; SSE bolts on with no
  rewrite; minimal `NpcMemoryClient`/`NpcSession` C# surface; dual TTFT fields; named thread-pool;
  off-camera cache warm-init as C1-via-choreography; STAGE (default-coherent).
- **researcher:** judge-free gist/detail presence metric from existing gist spans; fixed-gist ON/OFF
  ablation as the decisive R7-closer; the one figure = demo panel = paper Fig 1; version-chain-as-judge
  (set-diff trajectory) and an optional NLI proxy; constancy-first framing; CUT from the recorded video,
  keep as second paper eval.
- **skeptic:** MVP cut line (R1+R6+R3-as-render+R4+R5, plus cheap R2); week-by-week with Wk2 Unity interop
  as go/no-go; per-beat failure guards; "gray-box as the intended aesthetic"; "R7 hole as the thesis";
  risk-audit (don't over-build R3; validate real-embedding drift in Wk3); CUT split-brain to a separate
  clip.

---

*Generated by the 4-persona read-only agent audit (solutions round). Advisory only. To revert: delete
this file — no existing doc was modified; the original `external-audit-2026-07-22.md` is untouched.*
