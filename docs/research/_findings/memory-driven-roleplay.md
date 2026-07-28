> Read `_baseline\current-architecture.md` FIRST. Every judgment is relative to that yardstick.

---

## Memory-Driven Role-Playing: Evaluation and Enhancement of Persona Knowledge Utilization in LLMs

- **Authors / venue / year:** Kai Wang, Haoyang You, Yang Zhang, Zhongjie Wang (Harbin Institute of Technology / Macquarie University); 2026
- **arXiv / DOI:** arXiv:2603.19313v1 [cs.CL]
- **Source:** folder
- **Overall relevance to longmem-npc:** High for evaluation methodology (fills a named baseline gap), Medium for persona-representation design; Low for anything about episodic memory storage/retrieval — this paper's "LTM" is a **static persona-knowledge store rendered whole into the prompt**, evaluated single-turn, with no retrieval-over-time, no decay, no write path. Its own stated limitation: "we evaluate MDRP in an episodic, single-turn setting... it has not yet addressed interactive scenarios where persona memory is gradually accumulated, revised, or negotiated over time" (Limitations). That gap is exactly our domain.
- **Core contribution (2-3 sentences):** Formalizes Memory-Driven Role-Playing (MDRP): treat persona knowledge as an LLM's long-term memory (LTM) and dialogue context as short-term memory (STM), requiring the model to retrieve/apply persona facts from context alone (no scene-description crutch). Contributes MREval, a four-stage diagnostic eval (Anchoring/Selecting/Bounding/Enacting, 8 calibrated Likert metrics via LLM-judge); MRPrompt, a prompting architecture (structured "Narrative Schema" persona + an explicit "Magic-If Protocol" retrieval/bounding procedure); and MRBench, a bilingual benchmark. Shows MRPrompt lets small open models (Qwen3-8B) match much larger closed models on persona fidelity.

### Mechanisms relevant to us
- **MREval's four-stage decomposition** (§3.2, Table 1): Memory-Anchoring (persona grounding beyond name priors), Memory-Selecting (retrieving the *right* facet given dialogue cues), Memory-Bounding (respecting temporal/epistemic knowledge limits — no leaking "future plot" info), Memory-Enacting (natural surface realization). Each scored 1-10 via an LLM-judge calibrated against human ratings.
- **MB-AL ("Answer Leakage") metric specifically**: "Scores the model's ability to avoid generating a forbidden reference answer... when presented with an out-of-scope prompt (e.g., a future plot spoiler)" — rubric anchor: "1: Frequently leaks future plot points or out-of-book information, effectively using an omniscient view instead of the character's current-time perspective... 10: Always answers strictly from the current time point, only using available memories and never revealing future or out-of-scope facts" (Table 1, Appendix N rubric).
- **Narrative Schema** (§3.3, Appendix C/Table 7): persona LTM structured as identity fields + global summary + core traits + cue-addressable "scene facets," each facet carrying cue keys (`situation`, `cue_phrases`), enactment signals (`social_role`, `emotional_state`, `behavior_pattern`, `thinking_pattern`), and boundary anchors (`time_scope`, `conflict_with_core`).
- **Magic-If Protocol**: an explicit four-step inference-time instruction sequence — ground in core traits → select facet from STM cues → apply boundary anchors → enact — turning "memory use" into an auditable, stage-attributable procedure rather than implicit prompting (§3.3).

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none)* — this paper doesn't touch storage, decay, retrieval-over-time, or correction; there's no mechanism here that outperforms a *named* component of our built pipeline. (Its persona-as-static-LTM design is architecturally shallower than our bi-temporal fact-chain system, not deeper.)

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** A staged, judged evaluation harness for persona/memory-consistency — baseline names this as a known gap: "No end-to-end evaluation harness... no judged-drift / Bartlett-style eval."
- **What the paper does:** MREval decomposes character-consistency failure into four independently-scored, causally-ordered stages with 8 calibrated LLM-judge metrics, validated against human ratings (Pearson/Spearman/Kendall correlations reported, §4.5) — "MREval provides an eight-dimensional diagnostic profile for MDRP... enables stage-wise attribution of failures... rather than relying on a single holistic quality score" (§3.2).
- **Why worth adopting for an NPC memory service:** Directly answers the open baseline gap. Most transferable single piece: the **MB-AL / epistemic-boundary metric** — does a reconstructed/retold memory (or a dialogue response drawing on retrieval) leak facts the character shouldn't yet know (not-yet-`valid_at`, or superseded-by-correction, or beyond decay/gate visibility)? This is a directly testable judged-eval analog to our bi-temporal + reconstruction machinery that we currently only verify structurally, never semantically.
- **Adoption cost/risk in our stack:** Real — this requires LLM-judge scoring, which sits outside our "structural-only tests" discipline (test-suite.md). It would be a *new* evaluation surface (a judged eval harness, run on demand, not part of the Stop-hook gate), not a replacement for the structural suite. No schema change; needs its own scoring pipeline + a judge model role/env var (consistent with "every model role has its own env var").
- **Docs it would touch:** `test-suite.md` (new section: judged eval, distinct from the structural suite), `architecture.md` §11 (instrumentation), open artifact queue (currently lists only the research-track evals as aspirational).
- **Confidence:** High — clean gap-fill, evidence-backed methodology (human-calibrated judge), directly reusable rubric structure.

- **Capability:** A structured, cue-addressable identity-document schema (fields aligned to specific consistency failure modes) — our identity document is currently "seed-prose-only until reflection lands" (baseline gap).
- **What the paper does:** Narrative Schema's scene-facet fields (`time_scope`, `conflict_with_core`, `cue_phrases`, etc.) are explicitly designed so each field maps to one of the four diagnosed failure modes (Appendix C/Table 7: "fields are designed to align with our diagnostic abilities... boundary anchors support MB").
- **Why worth adopting for an NPC memory service:** When reflection eventually restructures the identity document beyond seed prose, this gives a concrete, evaluation-linked target schema rather than an undesigned free-text blob — e.g., an explicit `boundary`/`time_scope` field could encode what an NPC's identity doc claims it currently knows, directly relevant to the reconstruction anchor and the gate's entity tripwire.
- **Adoption cost/risk in our stack:** Low urgency (reflection is sequenced-later); if pulled forward, no invariant conflict — this is prompt-content structuring, not storage.
- **Docs it would touch:** Sequenced-later ledger (reflection pipeline), `architecture.md` §4.3/§7.
- **Confidence:** Medium — useful design reference, not urgent since reflection isn't built yet.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none)* — no storage or destructive-edit mechanism is proposed; the paper's own limitations section explicitly excludes the regime (persistent, revisable memory over time) that our invariants govern, so there's no apples-to-apples conflict to flag.

### Quotable lines / citations for positioning (optional)
- Self-scoped limitation, useful to cite as "prior work punts on exactly what we build": "it has not yet addressed interactive scenarios where persona memory is gradually accumulated, revised, or negotiated over time" (Limitations).
- On why holistic single-score eval hides failure modes (supports our own read-endpoint-transparency invariant framing): "Coarse Error Diagnosis: Holistic scoring aggregates performance into a single metric, obscuring failure modes and hindering attribution" (§1).

### Verdict
P2 worth-piloting. The MREval staged-diagnostic methodology (esp. the epistemic/temporal-boundary-leakage metric) is the single most transferable idea in this batch for closing our named "no judged-drift eval" gap, and the Narrative Schema is a decent future reference for the reflection-era identity document. Neither is urgent; both are cleanly additive (new eval surface, future schema reference) with no floor re-verification required to pilot.
