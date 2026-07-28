# LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues

- **Authors / venue / year:** Di Wu, Zixiang Ji, Asmi Kawatkar, Bryan Kwan, Jia-Chen Gu, Nanyun Peng, Kai-Wei Chang — UCLA, preprint 2026
- **arXiv / DOI:** arXiv:2605.12493v1
- **Source:** folder
- **Overall relevance to longmem-npc:** Medium — the domain (web agents accumulating environment experience from task trajectories) is a poor match for an NPC dialogue memory, but the evaluation *formulation* (Insert/Query context-gathering harness, accuracy-vs-latency Pareto reporting) and one of its five memory abilities (premise awareness) are directly reusable ideas for our missing eval harness.
- **Core contribution (2-3 sentences):** LME-V2 evaluates whether a memory system can turn accumulated web-agent trajectories (up to 115M tokens) into "experienced colleague" knowledge, across five abilities: static state recall, dynamic state tracking, workflow knowledge, environment gotchas, and premise awareness. It formulates evaluation as a context-gathering task (Insert(trajectory)/Query(question) API, truncate to a token budget, fixed reader answers) and benchmarks two baseline memory designs — a pooled-RAG method and a coding-agent-as-memory-controller method — finding the coding-agent approach wins on accuracy (72.5%) but at far higher latency, advancing rather than solving the accuracy-latency frontier.

### Mechanisms relevant to us
- Context-gathering evaluation formulation: `Insert(h)` / `Query(q)` as the only two contract points a memory system must expose, with a fixed downstream reader model that never sees anything but the returned, budget-truncated context (§3.3).
- Five-ability taxonomy: static state recall, dynamic state tracking (a "world model" — given states+actions, predict/explain how the environment changed), workflow knowledge, environment gotchas (recurring failure modes), premise awareness (recognizing an assumption valid elsewhere but wrong here) (§3.1).
- Accuracy-vs-latency Pareto reporting as the primary comparison axis between memory designs (§5.2, Fig. 6), not accuracy alone.
- Question sanitization discipline: goal descriptions are rewritten to strip step-by-step navigational hints so that questions test learned experience rather than leaked procedure text (§A.1, Table 3) — a data-hygiene lesson for constructing our own eval scenarios so the "answer" isn't trivially present in the setup text.
- Pilot-study discipline: verifying (a) frontier LLMs can't answer from parametric knowledge alone, and (b) oracle-evidence-only access is still not sufficient without good evidence framing, before trusting the main benchmark numbers (§3.4).

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none — the two proposed memory methods, AgentRunbook-R and AgentRunbook-C, are RAG-pool and coding-agent-sandbox designs built for web-agent trajectory data; neither is a general memory-service mechanism that outperforms our retrieval scoring, decay, reconstruction, or correction machinery, and the domain mismatch — file/screenshot trajectories vs. episodic NPC observations — makes direct comparison apples-to-oranges)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** Context-gathering harness contract (Insert/Query, fixed reader, truncation budget) as the skeleton of an eval harness.
- **What the paper does:** — *evidence:* §3.3, "The system must support two APIs, Insert(h) and Query(q)... A fixed reader model R answers from the question and a bounded memory context."
- **Why worth adopting for an NPC memory service:** This is close to a direct description of our own write path (`ingest.py`) / read path (`retrieval.py`) / dialogue call, minus the evaluation loop around it. Adopting the *pattern* — feed a scripted event sequence through observe, call retrieval/dialogue with a probe question, hand the truncated result to a judge-comparable fixed reader, score — gives us the skeleton for the eval harness the baseline says we lack, with almost no new mechanism, only new test scaffolding.
- **Adoption cost/risk in our stack:** Low. Our CLI harness and load driver already drive this loop manually; this is "wrap it for judged scoring," not new architecture.
- **Docs it would touch:** New `docs\eval-harness.md`.
- **Confidence:** High

- **Capability:** "Premise awareness" as a distinct memory ability — recognizing that a query's embedded assumption is false *for this specific instance* (e.g., "what field appears when X happens" when in fact no such field appears here) — evaluated with a strict LLM-judge rubric that penalizes both silently following the false premise and giving a generic non-answer that doesn't name the flaw.
- **What the paper does:** — *evidence:* §3.1 "Premise Awareness. An experienced colleague can recognize assumptions that are valid in another environment but wrong in the current one"; Table 5 judge rubric: "Label 0 if the model follows the flawed premise... Label 0 for generic UNKNOWN/insufficient-info replies that do not identify a flaw."
- **Why worth adopting for an NPC memory service:** This is a stricter, better-specified version of the abstention idea (see the LongMemEval finding) — it requires *identifying why* the premise is wrong, not just declining. For longmem-npc this maps to testing whether reconstruction/dialogue can distinguish "this event never happened" from "this event happened but differently than the query assumes" — the second case is exactly the confabulation-boundary territory the thesis cares about (controlled infidelity vs. inventing a wrong-but-plausible answer to a leading question).
- **Adoption cost/risk in our stack:** Low as an eval-construction technique (no code change); the judge-rubric design (penalize both false-premise-following AND generic non-answers) is a reusable pattern worth copying verbatim into our own judge prompts.
- **Docs it would touch:** New eval-harness doc.
- **Confidence:** Medium

- **Capability:** Accuracy-vs-latency Pareto-frontier reporting as the standard comparison shape for memory-design tradeoffs, rather than accuracy alone.
- **What the paper does:** — *evidence:* §5.2, "An ideal memory method should support both accurate and efficient querying... AgentRunbook-C moves the accuracy and latency frontier upward." (Fig. 6)
- **Why worth adopting for an NPC memory service:** Our `load_driver.py` already reports latency p50/p95 and gate efficacy separately from any accuracy signal; once a judged-accuracy eval exists, pairing it with the existing latency instrumentation into one Pareto view would let Jack compare, e.g., theta/band-quantum settings or gate thresholds on both axes at once — directly useful for tuning `reconstruction_theta`, `gate_novelty_threshold`, etc. against real behavior quality, not just speed.
- **Adoption cost/risk in our stack:** Low — combines two things we'll already have (load-driver latency, new judged eval) into one report; no new mechanism.
- **Docs it would touch:** New eval-harness doc; `docs\architecture.md` §11 instrumentation note.
- **Confidence:** Medium

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none)*

### Quotable lines / citations for positioning (optional)
- "A high-quality memory makes an agent an experienced colleague in a specialized environment" (§1) — a clean one-line framing device, though it's the opposite emphasis from our thesis (we want a *psychology*, not competence-accumulation); useful as a contrast line in a research write-up distinguishing "memory as accumulated competence" from "memory as identity-conditioned reconstructive narrative."

### Verdict
P3 note-only for direct adoption (domain mismatch is real — web-agent trajectory memory is a different problem from NPC episodic/dialogue memory), but P2 worth-piloting for two specific, cheap-to-borrow ideas: the Insert/Query context-gathering harness shape as eval scaffolding, and the premise-awareness judge-rubric design as a sharper version of an abstention/confabulation-boundary test category.
