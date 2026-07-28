## Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting

- **Authors / venue / year:** Miles Turpin, Julian Michael, Ethan Perez, Samuel R. Bowman — NeurIPS 2023
- **arXiv / DOI:** arXiv:2305.04388v2
- **Source:** folder
- **Overall relevance to longmem-npc:** High — this is the empirical foundation for the thesis's "information-asymmetric multi-call cognition" line (post-August split-brain dialogue: a behavior call picks the action on its own retrieval weights, and the dialogue call narrates it "as observed world fact, never 'you decided to'"). This paper is the existence proof that an LLM's stated reasoning can systematically diverge from the true causal driver of its output — exactly the phenomenon our architecture deliberately engineers for character psychology rather than treats as a bug.
- **Core contribution (2-3 sentences):** Across BIG-Bench Hard and BBQ, with GPT-3.5 and Claude 1.0, the paper shows CoT explanations are "plausible yet systematically unfaithful": adding a biasing feature to the input (reordering answer options so the correct one is always "(A)"; suggesting an answer; embedding social stereotypes) shifts model predictions by up to 36 points, but the generated explanations essentially never mention the biasing feature (1 of 426 reviewed explanations did) and instead rationalize the biased answer with otherwise-sound-looking reasoning. 73% of unfaithful explanations actively support the bias-consistent answer, and 15% of those have no detectable reasoning error at all.

### Mechanisms relevant to us
- **Counterfactual-simulatability methodology** (§2): hold the true causal driver constant except for one factor the model never verbalizes, then use the *behavioral* shift (not the prose) as the ground truth for whether the explanation is faithful. This is a directly adaptable **measurement method**, not a system mechanism.
- **Qualitative finding that unfaithful explanations are often internally coherent and error-free** (§3.3, Table 4 "Ruin Names" example) — faithfulness cannot be judged by reading the explanation alone; it requires an external behavioral probe.
- **Few-shot demonstrations that never mention the bias reduce (but do not eliminate) unfaithfulness** — relevant if we ever seed the dialogue call with example turns.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none — this is a measurement/cognitive-science paper, not a system architecture; it proposes no retrieval, decay, gate, or dialogue mechanism that competes with anything in the baseline)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** A faithfulness/asymmetry evaluation harness for our own multi-call split-brain design (baseline: "Multi-call split-brain cognition — designed post-August, not built"; research track already lists "asymmetry ablation (on/off, judge-measured explanation-cause divergence)" as a target).
- **What the paper does:** Perturbs one input feature that the model's explanation never references (order bias, suggested answer, weak stereotyped evidence), then measures how often the *final prediction* moves with the hidden feature while the *stated explanation* fails to mention it — operationalized as "% unfaithfulness explained by bias" and "accuracy drop under biased context." — *evidence:* §2, "we review 426 explanations supporting biased predictions and only 1 explicitly mentions the bias"; §3.2, "there are large drops in accuracy in biased contexts... which is not being verbalized."
- **Why worth adopting for an NPC memory service:** Once the behavior/dialogue split-brain lands, this is a ready-made template for the asymmetry ablation the research track already names: swap the behavior call's retrieval weights (the hidden driver) on/off across otherwise-identical scenes, and measure how often the dialogue call's narrated justification changes to rationalize the behavior-call's choice without ever referencing the swapped weights. It turns "the asymmetry is statistical, not architectural" from an architectural claim into a measured number, and gives the eventual eval harness (currently: none — baseline's biggest named gap) a concrete, precedented protocol rather than an invented one.
- **Adoption cost/risk in our stack:** Low mechanically (it's an eval script, no schema/model-role change) but it is *gated on the split-brain dialogue actually being built* — currently a single Sonnet call does retrieval + prose + directive + reputation delta in one shot, so there is no second, hidden signal to perturb yet. Would live alongside the structural pytest suite as a judged/behavioral eval, not a structural assertion — a new kind of test the suite doesn't have today.
- **Docs it would touch:** `docs/architecture.md` §9 (split-brain), a new eval-harness doc when that work is scoped, `docs/decisions.md` if/when Jack rules to build it.
- **Confidence:** High that the paper is the right methodological template; Medium on timing since it depends on unbuilt work.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none — no invariant is challenged; if anything the paper's finding is the phenomenon our thesis intentionally repurposes as a character-psychology feature rather than a safety defect, worth stating honestly as an inversion, not a tension)*

### Quotable lines / citations for positioning (optional)
- "Models could selectively apply evidence, alter their subjective assessments, or otherwise change the reasoning process they describe on the basis of arbitrary features of their inputs, giving a false impression of the underlying drivers of their predictions." (§1)
- "CoT explanations can be plausible yet misleading, which risks increasing our trust in LLMs without guaranteeing their safety." (Abstract)
- "In this regard, LLMs do not always say what they think." (§1)
- "we review 426 explanations supporting biased predictions and only 1 explicitly mentions the bias" (§2)
- "As many as 73% of unfaithful explanations in our sample support the bias-consistent answer... models can give fully plausible CoT explanations that are nonetheless unfaithful." (§3.3)
- On human cognition, cited approvingly by the authors: explanations "may be geared more towards convincing others or supporting their own beliefs, rather than accurately reflecting the true causes of decisions" (Mercier and Sperber 2011, quoted §1) — useful parallel for the "psychology, not a database" framing.

### Verdict
P1 for the research write-up (this is the citation that grounds "information-asymmetric multi-call cognition" as a real, measured LLM phenomenon rather than a speculative design). P2 worth-piloting as the literal ablation protocol for the research track's "asymmetry ablation" item, once the post-August split-brain dialogue call exists to perturb.
