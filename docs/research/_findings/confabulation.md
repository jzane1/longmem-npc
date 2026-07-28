## Confabulation: The Surprising Value of Large Language Model Hallucinations

- **Authors / venue / year:** Peiqi Sui, Eamon Duede, Sophie Wu, Richard Jean So (McGill / Harvard) —
  Proceedings of the 62nd Annual Meeting of the ACL (Volume 1: Long Papers), 2024, pp. 14274-14284.
- **arXiv / DOI:** Not stated in the extracted text (ACL Anthology 2024, ACL Volume 1 Long Papers).
- **Source:** folder.
- **Overall relevance to longmem-npc:** High — this is the single most directly thesis-supporting
  paper of the three assigned. It is an empirical + theoretical defense of "confabulation" (rather than
  "hallucination") as a valuable, narrative-rich cognitive resource, closely paralleling our claim axis
  of "controlled infidelity above an immutable record." It offers no build mechanism, but strong
  positioning ammunition and one adoptable instrumentation idea.
- **Core contribution (2-3 sentences):** Argues LLM "hallucination" is better understood through the
  lens of clinical/psychological "confabulation" — a narrative impulse to schematize available
  information into self-consistent stories, mirroring a normal human tendency in memory reconstruction.
  Empirically shows, across three dialogue hallucination benchmarks (FaithDial, BEGIN, HaluEval), that
  hallucinated/confabulated outputs have significantly *higher* narrativity and discourse coherence than
  their truthful/edited counterparts, and that narrativity is a significant positive predictor of both
  the hallucination label and the coherence score.

### Mechanisms relevant to us
- The narrative-centric definition of confabulation (§2.2): "a latent narrative impulse to generate
  more substantive and coherent outputs... a characteristic of LLM textual outputs that closely mirrors
  the human predisposition to storytelling as a cognitive resource for sense-making."
- The clinically-informed NLP definition they cite in Table 1 (Smith et al., 2023): "The generation of
  narrative details that, while incorrect, are not recognized as such... mistaken reconstructions of
  information which are influenced by existing knowledge, experiences, expectations, and context" —
  this is close to a plain-language description of what our reconstruction engine deliberately does
  (identity-conditioned retelling that can drift from the underlying record).
- Empirical narrativity/coherence measurement methodology (§3.1, §4.0.1): a fine-tuned ELECTRA-large
  narrative-detection classifier (narrativity score ∈ [0,1]) and the DEAM coherence metric, with a beta
  regression showing narrativity positively predicts coherence (coefficient 0.372, p<0.01, Table 4).
- Fisher's narrative-paradigm distinction (§4.1.1) between **narrative coherence** (internal
  self-consistency of a story) and **narrative fidelity** (how well a story aligns with the receiver's
  existing understanding of reality) — a useful vocabulary pairing for our drift-budget (a fidelity
  bound) vs. reconstruction-quality (a coherence property) distinction.
- Clinical/psychological legitimation that confabulation is not pathological: "everyday memory
  reconstruction often involves some degree of confabulation... equally common for healthy individuals
  to inadvertently fictionalize details of stories without the intention to deceive" (§2.1, citing
  French et al., 2009; Riesthuis et al., 2023).

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none — this is an empirical/positioning paper about the value of confabulation broadly; it proposes
no retrieval, decay, gate, correction, reflection, or storage mechanism to compare against anything in
the baseline)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** Narrativity / discourse-coherence instrumentation for reconstruction output quality —
  none / gap noted in baseline as "No end-to-end evaluation harness... no judged-drift / Bartlett-style
  eval."
- **What the paper does:** Uses a fine-tuned ELECTRA-large classifier to score narrativity (AUC
  0.83-0.85 against two held-out test sets) and the DEAM RoBERTa-large metric to score dialogue
  coherence, then statistically links the two — *evidence:* §3.1 "Modeling Narrativity," §4.0.1, Table
  2 (narrativity summary stats per benchmark), Table 4 (narrativity → coherence regression).
- **Why worth adopting for an NPC memory service:** Gives a cheap, non-LLM-judge, offline way to
  quantify "does this reconstructed retelling read as a good, coherent story" — a quality-side metric
  that pairs naturally with the drift-budget's cosine-distance check (a fidelity-side metric). Together
  they'd give the reconstruction engine two independent, measurable axes (fidelity bound vs. coherence
  floor) instead of just one, directly feeding the research track's planned judged-drift eval.
- **Adoption cost/risk in our stack:** Low-to-medium — purely an offline evaluation add-on (could run
  against `memory_details` reconstruction rows as a research-track script); touches no runtime
  invariant, no schema, no read/write path. Risk: their exact fine-tuned models/datasets aren't
  necessarily reusable off-the-shelf; the *method* (fine-tune a narrative classifier, apply a coherence
  metric, regress one on the other) is reproducible but would need our own labeled data or a
  general-purpose off-the-shelf narrativity model.
- **Docs it would touch:** docs\test-suite.md (if/when an eval harness beyond the structural suite is
  specced), docs\status.md research track.
- **Confidence:** Medium.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none)*. Explicitly answering the assignment's question: **no, this paper does not argue our
reconstruction/confabulation stance is wrong or incomplete — it is the strongest available support for
it among this batch.** It provides independent empirical and clinical grounding for treating narrative
drift as a feature rather than strictly a defect.

One honest caveat worth naming (not a tension with an invariant, but a gap in *their* argument that we
should note we've already closed): the paper defends confabulation's value **unconditionally** — it
never proposes a bounding, verification, or governance mechanism for it, and flags this itself as
future work ("the extent to which these affordances generalize to human-AI interactions... needs to be
further validated with human-based evaluations," §5). Our drift-budget threshold, fixed-gist-constraint,
non-destructive underlying record, and debug view exposing ground truth are precisely the governance
layer this paper leaves unaddressed — worth stating plainly in any write-up as *our* contribution on
top of their finding, not something they solved for us.

### Quotable lines / citations for positioning (optional)
- "We argue and empirically demonstrate that measurable semantic characteristics of LLM confabulations
  mirror a human propensity to utilize increased narrativity as a cognitive resource for sense-making
  and communication." (Abstract) — strong citation-support sentence.
- Clinical definition (Table 1, citing Smith et al., 2023): "The generation of narrative details that,
  while incorrect, are not recognized as such... mistaken reconstructions of information which are
  influenced by existing knowledge, experiences, expectations, and context." — near-verbatim
  description of identity-conditioned reconstructive drift; strong candidate epigraph.
- "confabulation's narrative-rich properties should not be viewed as a flaw but a hallmark for LLM
  alignment with a well-established human tendency to use narratives as a versatile tool for
  persuasion, identity construction, and social negotiation." (§4)
- "hallucinations make them more like us than we would like to admit." (§6) — strong closing pull-quote
  for a README or talk.
- "everyday memory reconstruction often involves some degree of confabulation... equally common for
  healthy individuals to inadvertently fictionalize details of stories without the intention to
  deceive." (§2.1) — clinical legitimation for "controlled infidelity above an immutable record."
- Narrative coherence vs. narrative fidelity (Fisher, 2021, §4.1.1) — useful vocabulary: "narrative
  coherence, the internal consistency of a story that allows it to make sense in its own context," vs.
  "narrative fidelity, the degree to which a story aligns or resonates with the receiver's existing
  understanding of reality."

### Verdict
P1 for citation/positioning value — this is the paper to lead with when justifying the
reconstruction/confabulation thesis to a skeptical reader, since it supplies independent empirical and
clinical grounding rather than just our own architectural argument. P2 worth-piloting on the one
concrete build idea: adopt a narrativity + coherence instrumentation pair as an offline eval metric for
reconstruction quality, complementing the drift-budget's fidelity check, as part of the eventual
judged-drift eval harness.
