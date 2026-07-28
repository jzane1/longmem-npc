# External-persona audit — 2026-07-22

**Method.** Four read-only external-lens personas (simulated, not real individuals) explored the repo,
docs, and `docs/research/` and debated over a 3-round protocol — independent Round 1 positions,
Round 2 adversarial cross-examination, Round 3 lead synthesis (this note). The personas ran with
`tools: Read, Grep, Glob` only (no write access); the lead orchestrated the debate and is the sole
author of this file. Personas:

- **ceo** — founder/CEO of a Convai/Inworld competitor; market/differentiation/demo/portfolio lens.
- **engineer** — senior engineer at Convai/Inworld; latency/robustness/Unity-integration lens.
- **researcher** — memory/cognition researcher; thesis-novelty/eval-rigor/publication lens.
- **skeptic** — devil's advocate; complexity/scope/deadline-risk lens.

**How to read this.** Every recommendation is tagged **(A) actionable within the current direction**
or **(B) challenges a settled ruling → surface to Jack, do not act**. This is external critique — it is
advisory, and per `CLAUDE.md` architectural decisions are Jack's alone. Two items directly contest
prior rulings; they are flagged (B) and are **not** acted on.

**Lead verification of load-bearing claims (checked against source, not relayed on faith):**
- ✅ `app/api.py` exposes exactly five routes — `POST /v1/dialogue/init` (retrieval → `RetrievalResult`,
  memories+scores, *not* a spoken line), `POST /v1/events/observe`, `POST /v1/events/scene-boundary`,
  `PUT /v1/memories/{id}/pin`, `POST /v1/memories/{id}/correction`. **No route invokes
  `run_dialogue_turn`** (grep: zero matches). The cognition layer is reachable only in-process via
  `app/session.py` / `app/cli.py`.
- ✅ `app/dialogue.py`: `first_word_ms = _ms(time.perf_counter() - t_prose)` — the headline latency
  clock starts at the prose call, i.e. *after* retrieval. `rank_behavior_view` is exponent-form and its
  own docstring notes all-1.0 weights collapse to parity with the dialogue view.

---

## Executive summary

The four lenses started far apart on *what to do next* (cut scope / build the latency pre-warm / build
the eval / choreograph legibility) and **converged, under cross-examination, on one diagnosis**: the
project's largest risk is not a missing mechanism — it is that **the demo has no network surface, and
the beats it would show are hollow or un-credible at the shipped default configuration.** Twelve
verified floors, and none of them is the demo; the entire cognition layer sits behind an in-process
REPL that Unity (C# over HTTP) cannot reach.

The debate's most useful single insight (engineer, confirmed against code): the missing floor is
**topology-agnostic**. Cutting split-brain does *not* shorten the path to a demo, because the older
single-call topology is *also* in-process only. What is missing is a **plain HTTP dialogue-turn route
plus a minimal C# client** — plumbing over cognition that already exists, made cheaper by the fact that
`session.utterance` already drains the async generator to a terminal result.

The debate's most useful convergence (researcher + ceo): **the demo-legibility artifact and the
faithfulness eval are the same artifact.** An on-screen "ground truth vs. what the NPC now tells" panel
is only legible if it separates the facts held constant (gist) from those allowed to drift (detail) —
which is exactly the gist-precision/detail-recall measurement the thesis needs. Build it once, on real
embeddings, and it serves the demo, the credibility problem, and the future paper.

---

## Prioritized recommendations

### R1 — Build the HTTP dialogue-turn route + a minimal C# client (the true critical path) · (A)
The blocker is not "make a Unity scene," it is "build the product's network surface." `app/api.py` has
no turn route, so no HTTP client can reach a dialogue turn today (verified above). Ship a **non-streaming
request/response `POST /v1/dialogue/turn`** first — `session.utterance` already produces the terminal
`DialogueTurnResult`, so this is plumbing, not new cognition. SSE streaming is a nice-to-have, **not** a
gate for a recorded demo. *(Raised by skeptic; confirmed and reframed by engineer + ceo. This is the
concrete content of immediate-queue item 1, which currently bundles ~4 unbuilt pieces: turn route, C#
client, SSE route, action-observe contract.)*

### R2 — Fix the `first_word_ms` metric honesty · (A)
The headline latency clock starts at `t_prose`, *after* retrieval, so it is blind to the cold batched
reconstruction stall (real-mode **16.3 s** for 8 items, `status.md`). A cold scene reports ~2.2 s while
the player waited ~18 s. For a tier-1 interviewer this reads as a massaged number. Add a
**retrieval-inclusive perceived-TTFT** (utterance-received → first prose chunk) as the reported headline.
Cheap instrumentation change; pure credibility protection. *(engineer; endorsed by all four.)* Note: this
corrects an instrumentation claim, not an architectural ruling — but it does move the number `status.md`
currently headlines, so record it as a measurement correction.

### R3 — Make the marquee beat legible *and* credible with one artifact · (A)
Build an on-screen **"ground truth vs. what the NPC now believes/tells" panel** that is a *real*,
judge-free, **real-embedding** measurement: gist-atomic-facts shown **preserved** (the control) vs.
non-gist detail shown **drifting with the decay band** (the infidelity). This is the researcher+ceo
"same artifact from two ends" convergence: without the gist/detail split, designed drift reads as
hallucination (`FINDINGS.md` §4). Start with the judge-free keyword/gist-retention check the research
queue already notes "fits the structural suite today" (2511.10277); **defer** the heavyweight judged
harness (LLM-judge role, LoCoMo-scale, reach-vs-use) to the post-demo research phase. *(researcher #1,
ceo #1, engineer's "judge-free check now" all land here.)*

### R4 — Lead the story with the correction-override beat, not the drift beat · (A, positioning)
The unambiguously buyable / legible wedge is **editable memory where "retrieval follows the fix"**
(proven live: relevance 0.4686 → 0.5637 across a `:correct`). "Controlled infidelity" is commercially
ambivalent — studios want NPCs that remember *correctly*. Order the demo beats: **correction-override →
60-day drift → (if kept) staged split-brain divergence.** *(ceo + skeptic converge.)*

### R5 — Author non-default demo config before relying on the split-brain or drift beats · (A)
At shipped defaults the marquee beats are **hollow**: behavior weights default to 1.0, so
`rank_behavior_view` is byte-parity with the dialogue view (verified) — the "divergence record" is then
just sampling noise between two draws of the same model on near-identical prompts. And the fake-mode
60-day drift trajectory is an **artifact of the locality-sensitive fake embedding** that was calibrated
to the mechanism (`reconstruction.md`, `providers.py`); real mode shows only 16 retellings, max drift
0.244 < 0.35 — the budget never binds. So: author non-default behavior weights and a decay band that
visibly drifts detail, and validate on **real embeddings**, or the beats are empty/un-credible on camera.
*(researcher's + skeptic's sharpest technical catches; ceo amplified.)*

### R6 — Unblock real mode (prerequisite for R3/R5) · (A, operator-owned)
Real mode currently crashes on load: the malformed `LONGMEM_PRICE_DIALOGUE_IN=…` line in `.env` plus the
missing `LONGMEM_MODEL_BEHAVIOR` (already flagged in `status.md`). One-line operator fix — but it gates
every real-mode run, and R3/R5 both require real embeddings. Elevate it from a background flag to a
prerequisite. *(skeptic; Jack's `.env` to fix.)*

### R7 — Register the drift-budget hole as a claim-level risk · (B) — surface to Jack, not acted on
The drift budget is **self-referential cosine** (candidate-vs-anchor < 0.35). It cannot detect a
retelling that stays < 0.35 while **dropping or contradicting a gist fact**, nor one that **fabricates a
never-observed detail** near the anchor vector. That is an unmeasured failure mode inside the core
"immutable record + controlled infidelity" mechanism, and it is the strongest paper/interview risk.
This **challenges the 2026-07-17 drift-metric/threshold ruling**, so it is surfaced, not acted on. The
R3 gist-precision measurement is the natural place to close it — but changing the metric or threshold is
Jack's call. *(researcher #1 risk; skeptic elevated.)*

### R8 — Defer (don't drop) pre-warm and the concurrency fix; guardrail them · (A, post-demo)
- **C1 scene-boundary pre-warm:** the 16.3 s cold stall and the 60-day drift beat are the *same* code
  path, so the marquee beat risks an on-camera freeze — but the fix for a *recorded* demo is
  **choreography** (pin the memories or trigger a scene-boundary pre-roll off-camera), not a build
  session now. When pre-warm *is* built, put a gist-precision check at the cache write so it doesn't bake
  in unmeasured drift (researcher's coupling to R3). *(engineer wanted it first; skeptic + ceo + researcher
  re-sequenced it to post-demo.)*
- **Thread-pool exhaustion:** both split-brain legs use the default `ThreadPoolExecutor` and the prose
  thread is held for the whole stream, capping concurrent streaming NPCs at ~6 — a real *production*
  multi-NPC concern, irrelevant to a single-NPC demo video. Post-demo. *(engineer; ceo + skeptic
  de-scoped for the demo.)*

---

## Open fork for Jack (the one the team could not — and should not — settle)

**Split-brain in the *recorded* demo: CUT vs. STAGE.** All four agree that **raw-shipping it is off the
table** — same-turn word/action incoherence (the prose call cannot see the current turn's action, by
design) reads as a bug to someone scrubbing a portfolio video at 1.5×.

- **CUT (skeptic, researcher):** drop split-brain from the demo path. Reinforced by R5 — at default
  weights the divergence is a near-no-op, so you "forfeit nothing visible" and you kill the incoherence
  risk. Keep it as an **interview/architecture/paper** artifact; it is already floor-verified (sunk
  cost), and the asymmetry ablation (Turpin-style, `unfaithful-cot.md`) is a natural post-demo paper beat.
- **STAGE (ceo):** keep it as an *optional, authored-weights, on-screen-ground-truth* beat so the
  divergence reads as designed — preserving the one genuinely novel differentiator vs. Convai/Inworld.
  Cost: more Unity work (SSE route + C# client + a debug overlay).
- **Either way (engineer):** the coherent **single-call topology** (`run_dialogue_turn`, floor-verified
  2026-07-15) should be the demo's default/fallback, and the code stays regardless of the demo choice.

This is a scope-vs-differentiation trade with real cost on both sides — Jack's call.

---

## Consensus & dissent map

| Claim | ceo | engineer | researcher | skeptic |
|---|---|---|---|---|
| No HTTP turn route is the real blocker | ✅ | ✅ (code-confirmed) | (implicit) | ✅ (originated) |
| `first_word_ms` is blind to the cold stall → fix the metric | ✅ | ✅ (originated) | ✅ | ✅ |
| Split-brain divergence is empty at default weights | ✅ | ✅ (code-confirmed) | ✅ (originated) | ✅ |
| 60-day drift beat rests on a fake-embedding artifact | (agree) | — | ✅ (originated) | ✅ (originated) |
| Legibility panel == minimal faithfulness eval | ✅ | (compatible) | ✅ (originated) | partial |
| Lead with correction-override, not drift | ✅ (originated) | — | ✅ | ✅ |
| Build pre-warm / eval *before* the demo | ❌ | ↩ conceded post-demo | ↩ conceded (guardrail) | ❌ |
| Drift budget is self-referential (claim-level hole) | (agree) | ✅ confirmed | ✅ (originated) | ✅ elevated |
| Split-brain in demo | STAGE | keep code, ship route | CUT | CUT |

---

## Appendix — persona positions (condensed)

- **ceo** — Wedge vs. Convai/Inworld is editable memory + non-destructive audit trail + cost/latency
  instrumentation, all *under-hyped* relative to the risky drift beat. The demo, which "gets the
  introduction," doesn't exist and demo-legibility is unsolved. Updated #1: thin HTTP turn route → author
  non-default demo config → on-screen ground-truth panel + choreograph the 16 s stall → single-call as
  default, split-brain as an optional staged beat, freeze new cognition depth.
- **engineer** — Split-brain correctly takes behavior off the critical path; degradation ladders and
  infra floor are genuinely proven. But the headline TTFT metric hides the cold-reconstruction stall,
  the <1 s bar isn't met even warm, and the concurrency model caps streaming NPCs at ~6. Updated #1: the
  true critical path is a non-streaming HTTP turn route + C# client; attach pre-warm + honest perceived-TTFT
  to that route.
- **researcher** — Substrate is a named research frontier and the version chain is a rare untested eval
  asset (MemTrace trajectory). But the thesis is structurally asserted, never semantically measured; the
  drift budget is self-referential cosine; the asymmetry pillar is a config no-op at default weights.
  Updated #1: build the ground-truth-vs-telling legibility panel as a *real* measurement on real
  embeddings — it de-risks demo and paper at once; defer the heavyweight judged harness.
- **skeptic** — The demo's foundation is unbuilt (no turn route; cognition only in-process) and "verified
  floor" proves shapes, not the thesis; the drift beat runs on a fake embedding. Updated #1: freeze the
  backend at HEAD; the vertical Unity slice (turn route + C# client + gray-box scene) is the sole critical
  path; force split-brain to CUT-vs-STAGE; adopt the perceived-TTFT metric; log the drift-budget hole as a
  pre-customer/pre-paper risk, not a pre-August one.

---

*Generated by a 4-persona read-only agent audit. Advisory only. (A)-tagged items are actionable within
the current direction; (B)-tagged items and the open fork are Jack's to rule. To revert: delete this
file — no existing doc was modified.*
