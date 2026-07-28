# Evaluating Very Long-Term Conversational Memory of LLM Agents (LOCOMO)

- **Authors / venue / year:** Adyasha Maharana, Dong-Ho Lee, Sergey Tulyakov, Mohit Bansal, Francesco Barbieri, Yuwei Fang — ACL 2024
- **arXiv / DOI:** arXiv:2402.17753v1
- **Source:** folder
- **Overall relevance to longmem-npc:** High — LOCOMO's event-summarization task and its FactScore-based precision/recall metric are the closest thing in this batch to a ready-made evaluation of *reconstruction fidelity*, which is our thesis mechanism and currently has zero judged evaluation (only cosine-distance drift-budget checks and structural pytest assertions).
- **Core contribution (2-3 sentences):** LOCOMO is a dataset of 50 very-long (avg. 300 turns / 9K tokens / up to 35 sessions) human-edited, LLM-generated multimodal dialogues, each agent grounded on a persona and a causally-linked temporal event graph. It evaluates three tasks — QA (five reasoning types), event-graph summarization (measuring factual precision/recall against the ground-truth event graph), and multimodal dialogue generation — and finds long-context LLMs and RAG both substantially lag human performance, with long-context models specifically failing on adversarial questions (hallucinating, misattributing events to the wrong speaker) and RAG doing best when memory is stored as discrete "observations" about the speaker rather than raw dialogue or summaries.

### Mechanisms relevant to us
- Temporal event graph as the ground-truth substrate: each persona has a causally-linked sequence of dated life events; conversation is generated *from* the graph, and the graph itself (not the dialogue text) is the answer key for the summarization task (§3.2).
- Event-graph summarization task + FactScore metric: reference and generated summaries are each decomposed into atomic facts; precision = fraction of generated atomic facts that match the reference graph; recall = fraction of reference atomic facts recovered; F1 reported (§4.2).
- Five QA reasoning categories: single-hop, multi-hop, temporal, open-domain/commonsense, and **adversarial** (questions "designed to trick the agent into providing wrong answers, with the expectation that the agent will correctly identify them as unanswerable") (§4.1).
- RAG value-representation finding: storing memory as discrete "observations" (assertions about the speaker's life/persona) outperforms storing raw dialogue turns or session summaries, and more retrieved observations doesn't monotonically help — signal-to-noise in the retrieved set matters more than recall volume (§6.1).
- Long-context adversarial failure mode: GPT-3.5-turbo-16k's adversarial-question score collapses to 2.1% (vs. 70.2% for 4K-context GPT-4-turbo), specifically because it "misassigns dialogs or events to the wrong speaker" under long context (§1, finding 2).

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none — LOCOMO is a benchmark + baseline-evaluation paper; the "observations as memory value" and event-graph designs are conventional RAG/generation-pipeline choices, not a mechanism that outperforms our bi-temporal storage, decay, reconstruction, or gate)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** FactScore-style atomic-fact precision/recall decomposition applied to a *retelling*, judged against ground truth, rather than only a cosine-distance drift-budget gate.
- **What the paper does:** — *evidence:* §4.2, "we adapt the metric to measure (1) precision of the summarized content by counting the number of atomic facts within the content that correspond with those in G; (2) recall of the summarized content by determining how comprehensively the atomic facts of G are represented."
- **Why worth adopting for an NPC memory service:** This is the natural judged counterpart to our reconstruction mechanism. Our current safeguard (`drift_budget_threshold` = 0.35 cosine distance between candidate retelling and anchor) is a single scalar proxy for "did the retelling stay faithful enough" — it has never been checked against what a human/LLM judge would call factual precision. Critically, our thesis wants an *asymmetric* target that LOCOMO's framing doesn't anticipate: precision against the **gist span** (fixed constraint — the immutable record) should stay ~100% always, while recall against the full **non-gist detail** should be allowed and expected to *decay* over time (that's the point of reconstruction, not a bug). Adopting the atomic-fact decomposition method — while deliberately re-purposing the target values away from LOCOMO's "always maximize both" — gives us a real, judged way to test whether the confabulation stays "controlled" (gist-precision near 100%) as opposed to drifting into fabrication of the immutable content itself.
- **Adoption cost/risk in our stack:** Medium. Needs an atomic-fact extraction pass (a judge/LLM call decomposing both the gist span and the current retelling into atomic facts) plus a comparison step; this is a new evaluation-only model call (own env var per CLAUDE.md's model-role rule), not a runtime mechanism change.
- **Docs it would touch:** New `docs\eval-harness.md`; cross-reference from `docs\reconstruction.md`-equivalent section of `architecture.md` §7.
- **Confidence:** High

- **Capability:** Adversarial QA category — questions built to trick the agent, correct behavior is to recognize unanswerability rather than hallucinate a wrong-speaker or wrong-event answer.
- **What the paper does:** — *evidence:* §4.1, "(5) Adversarial questions are designed to trick the agent into providing wrong answers, with the expectation that the agent will correctly identify them as unanswerable"; §6.1 finding that long-context models drop to 2.1% here specifically via wrong-speaker/wrong-event misattribution.
- **Why worth adopting for an NPC memory service:** Same family as LongMemEval's abstention and LME-V2's premise-awareness (see those findings) but with a distinctive failure mode called out — misattribution across entities/speakers rather than plain fabrication. For an NPC with an entity-gate tripwire and identity-components table, this is a specific, testable risk: does the gate/reconstruction ever attribute a fact to the wrong tracked entity under retrieval pressure? Worth a dedicated eval category distinct from generic abstention.
- **Adoption cost/risk in our stack:** Low as eval-construction (scripted scenes with near-duplicate entities); no code change.
- **Docs it would touch:** New eval-harness doc.
- **Confidence:** Medium

- **Capability:** Temporal-reasoning QA over a dated event graph (e.g., "how many months since my last museum visit with a friend") as a judged eval of time-sensitive recall, distinct from structural decay-formula assertions.
- **What the paper does:** — *evidence:* §1 finding, "LLMs exhibit challenges in understanding lengthy conversations and comprehending long-range temporal and causal dynamics"; §6.1, "(1) LLMs face challenges in understanding time concepts within dialogues."
- **Why worth adopting for an NPC memory service:** Our decay math and `as_of` override are proven structurally (the pytest suite asserts the formulas and separation from bi-temporal invalidation) but never proven behaviorally — i.e., does the dialogue call actually reason correctly about elapsed time when recalling a decayed/reconstructed memory? A LOCOMO-style dated-event-graph QA construction is directly reusable as the data-generation pattern for this.
- **Adoption cost/risk in our stack:** Low (eval-construction only).
- **Docs it would touch:** New eval-harness doc.
- **Confidence:** Medium

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
- **Invariant challenged:** None of the storage/destructiveness invariants directly — but LOCOMO's implicit success criterion (maximize both precision *and* recall of the full event graph, always, as memory ages) is the opposite optimization target from ours (non-gist detail is *supposed* to decay/thin under reconstruction; only gist is supposed to stay perfectly faithful).
- **What the paper does that conflicts:** — *evidence:* §4.2 FactScore is defined to reward comprehensive, accurate recall of the entire event graph regardless of how much time/how many sessions have passed; there is no concept of an intentionally-lossy "telling" layered over a preserved ground truth.
- **Honest read:** This is an apples-to-oranges framing difference, not a weakness in either design — LOCOMO is built to evaluate assistants whose job is faithful long-term recall (a secretary), while longmem-npc's stated thesis is a *psychology*, where selective forgetting/drift of non-gist detail is the point. The adoption above (FactScore decomposition) is explicitly reusing LOCOMO's *measurement technique* while rejecting its *target values* — worth stating plainly in any write-up so a reviewer doesn't mistake "we score worse on LOCOMO-style full recall" for a defect.

### Quotable lines / citations for positioning (optional)
- "long-context LLMs demonstrate significant difficulty with adversarial questions... They are especially prone to misassigning dialogs or events to the wrong speaker" (§1) — useful contrast when positioning entity-gate-tripwire + gist-span-as-fixed-constraint as a structural defense against exactly this failure mode.
- "RAG offers a balanced compromise... and does particularly well when dialogues are transformed into a database of assertions (observations) about each speaker's life and persona" (§1) — a real-world validation that discrete, structured "observation" memory (which is structurally close to our `memories` table) outperforms raw-transcript or summary-only storage for a chat agent.

### Verdict
P1 adopt-soon: the FactScore atomic-fact precision/recall decomposition, retargeted to check gist-precision-stays-high / detail-recall-is-allowed-to-decay, is the single best-fitting piece of methodology in this batch for judging our reconstruction mechanism specifically — it directly operationalizes "controlled infidelity above an immutable record" into a measurable, judged eval rather than a cosine-distance proxy alone.
