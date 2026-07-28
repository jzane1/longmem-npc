## Beyond a Million Tokens: Benchmarking and Enhancing Long-Term Memory in LLMs

- **Authors / venue / year:** Mohammad Tavakoli, Alireza Salemi, Carrie Ye, Mohamed Abdalla, Hamed
  Zamani, J. Ross Mitchell — University of Alberta / UMass Amherst; ICLR 2026.
- **arXiv / DOI:** arXiv:2510.27246v2 [cs.CL]
- **Source:** folder
- **Overall relevance to longmem-npc:** Medium — primarily a scale/coherence benchmark (single
  coherent conversations to 10M tokens, not concatenated sessions) plus a context-management
  enhancement (LIGHT: episodic + working + scratchpad memory). Only 2 of its 10 probed abilities
  (Contradiction Resolution, Knowledge/Information Update) and 1 (Abstention) bear on this batch's
  conflict/staleness focus, but the Contradiction Resolution results are independently corroborating
  evidence for the STALE paper's central claim.
- **Core contribution (2-3 sentences):** Introduces BEAM, a benchmark of 100 automatically-generated,
  narratively-coherent single-user conversations (100K-10M tokens) with 2,000 human-validated probing
  questions across ten memory abilities, scored via nugget-based LLM-judge decomposition. Proposes
  LIGHT, a three-part memory architecture (vector-indexed episodic recall of per-turn key-value
  extractions; a sliding-window working memory of recent turns; a periodically-compressed
  "scratchpad" of salient facts) that improves over long-context and RAG baselines by 3.5-12.69%
  on average, with the gap widening sharply as conversation length grows (+107-155% at 10M tokens
  vs. long-context baselines).

### Mechanisms relevant to us
- **Contradiction Resolution** and **Information/Knowledge Update** as two of ten formally-scored
  memory abilities — the closest overlap with this batch's conflict/staleness focus.
- **Abstention** ability — "evaluates whether a model withholds answers when evidence is missing" —
  loosely maps to our fail-quiet degradation philosophy, but at the *dialogue-output* layer rather
  than the *retrieval-signal* layer.
- **LIGHT's scratchpad-with-periodic-compression** — an explicit-memory-consolidation mechanism
  (merge → compress at a 30K-token threshold → 15K-token summary) that is the closest thing in this
  paper to our reflection/consolidation gap, though built for a very different problem (compressing
  raw dialogue turns to fit a prompt, not producing a versioned identity document).
- **Nugget-based evaluation methodology** (atomic, self-contained criteria decomposed from a
  reference answer, scored 0/0.5/1 by an LLM judge) — a reusable evaluation-harness pattern, not
  specific to conflict/staleness but directly reusable for our own future eval.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none)* — LIGHT solves a different problem (fitting/using enormous raw conversational context
within one chatbot session) than our architecture (a persistent, queryable, non-destructive store
serving many scenes over the life of an NPC). Nothing here beats a baseline mechanism on its own
terms; see THESIS-TENSION for the one place a naive transplant would actively regress us.

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** Any automated accuracy/recall eval harness at all — baseline states we have "no
  LongMemEval-style accuracy/recall benchmark… no memory-conflict or staleness eval." BEAM's 10-
  ability, nugget-scored protocol (and specifically its Contradiction Resolution / Knowledge Update
  / Abstention subsets) is a second independent template alongside STALE's (see that finding) and
  MemConflict's (see that finding) — three converging designs for the same gap.
  - **What the paper does:** §2.4 (p.5), each probing question decomposed into "atomic,
    self-contained" nuggets, scored 0/0.5/1 by an LLM judge, averaged per-ability; Event Ordering
    scored separately via Kendall tau-b for sequence fidelity (§2.4, p.5).
  - **Why worth adopting for an NPC memory service:** Cheap methodological borrow — doesn't require
    adopting LIGHT itself, just the scoring pattern.
  - **Adoption cost/risk in our stack:** Medium — needs an LLM-judge role (a new model-role env var,
    per our "every model role gets its own env var" rule) if adopted.
  - **Docs it would touch:** `docs\test-suite.md`.
  - **Confidence:** Medium.

- **Capability:** Convergent, independent evidence that contradiction/conflict detection is
  unsolved even under heavy retrieval-augmentation — corroborates the STALE paper's central finding
  from an entirely different benchmark and method.
  - **What the paper does:** Table 1 (p.8) shows Contradiction Resolution scores near floor across
    *every* model and *every* method (long-context, RAG, and their own LIGHT) at every conversation
    length — e.g. Qwen2.5 at 100K: 0.031 (vanilla) / 0.025 (RAG) / 0.037 (LIGHT); at 10M: 0.050 /
    0.000 / 0.012. §4.2 (p.8-9) states it directly: "all methods—including ours—perform strongest in
    abstention and weakest in contradiction resolution, indicating that contradiction detection
    remains a challenging open problem." Notably, LIGHT's own big per-ability wins are elsewhere
    (summarization +160.6%, multi-hop +27.2%, preference-following +76.5%) — contradiction
    resolution isn't even in that list, meaning their retrieval+scratchpad architecture essentially
    doesn't move this needle.
  - **Why worth adopting for an NPC memory service:** Not something to "adopt" — it's a risk-framing
    finding. It tells us that if Jack wants automatic conflict detection as a demo/thesis
    differentiator (see STALE and MemConflict findings), no existing retrieval-augmentation
    architecture — including a well-resourced one purpose-built for huge contexts — has solved it
    either. Lowers the bar for "good enough to be notable" but raises the bar for "actually solving
    it well."
  - **Adoption cost/risk in our stack:** N/A (a risk/positioning finding, not a mechanism).
  - **Docs it would touch:** could inform a future `dissonance.md` risk section.
  - **Confidence:** High (numbers are explicit and consistent across four models × three lengths).

- **Capability:** Explicit dialogue-level abstention ("I don't have information about that") tied
  to retrieval/gate confidence, as opposed to our current design where a degraded read just returns
  `relevance = null` per item but the dialogue call still always produces prose.
  - **What the paper does:** §2.2 (p.3), "Abstention evaluates whether a model withholds answers
    when evidence is missing" — treated as a first-class, separately-scored ability; it is in fact
    the ability every model/method scores *highest* on (Table 1), suggesting it's comparatively
    tractable.
  - **Why worth adopting for an NPC memory service:** Minor character-consistency win (an NPC that
    says "I don't recall" rather than confabulating when retrieval genuinely came back empty) — but
    tension-worth-noting: our thesis explicitly wants *controlled infidelity* (confident-but-drifted
    telling) as a feature, not a bug, so "abstain when uncertain" cuts somewhat against the
    confabulation-is-the-point design. Low priority.
  - **Adoption cost/risk in our stack:** Low technically (a prompt-assembly branch keyed on
    `relevance IS NULL for all items` or empty retrieval), but a values/thesis question, not a
    technical one.
  - **Docs it would touch:** `docs\cli-harness.md` (prompt assembly).
  - **Confidence:** Low (tension with thesis noted above).

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
- **Invariant challenged:** Non-destructive bi-temporal storage (baseline invariant 1) — "never
  UPDATE stored content in place."
- **What the paper does that conflicts:** LIGHT's scratchpad is explicitly destructive
  consolidation: "once content exceeds a 30K-token threshold... it is compressed into a 15K-token
  summary by GPT-4.1-nano" (§3.2, p.7) — the pre-compression content is not retained anywhere; the
  scratchpad *is* the memory going forward for anything folded into that summarization pass.
- **Honest read:** This is an apples-to-oranges case, not a genuine weakness in our design. LIGHT
  is built for a single long-lived chat session with no persistent backing store — the scratchpad
  *is* its entire long-term memory, so lossy compression is the only way to keep it bounded at all.
  Our architecture already has a non-destructive answer to the same underlying problem their
  scratchpad solves (bounding what's carried forward as "current understanding" without losing the
  original): gist spans (immutable pointers into `observation_text`, never decay) + the reconstructed
  telling (versioned, superseded not overwritten) + the decay-banded reconstruction cache. If we ever
  wanted a LIGHT-style "scratchpad" of accumulated salient facts for prompt economy, it would need
  to be a *derived, evictable, re-derivable* serving-layer artifact (same class as
  `reconstruction_cache`), never the system of record — which is in fact closer to what we already
  do than to what LIGHT does. Worth naming in the README as a deliberate contrast: destructive
  summarization vs. non-destructive reconstruction-from-an-immutable-gist.

### Quotable lines / citations for positioning (optional)
- "Most extend conversation length by artificially concatenating short sessions of different
  users, producing dialogues with abrupt topic shifts and weak narrative coherence" (§1, p.2) — a
  fair critique of prior benchmarks that also applies to justifying why our own future eval
  (if built) should use continuous in-scene histories, not concatenated synthetic sessions.
- "all methods—including ours—perform strongest in abstention and weakest in contradiction
  resolution, indicating that contradiction detection remains a challenging open problem" (§4.2,
  p.8-9) — strong corroborating citation alongside STALE for the README/research write-up's framing
  of conflict/staleness as the open frontier.

### Verdict
P3 note-only. Not a mechanism to adopt (LIGHT solves a different problem than our persistent
non-destructive store already solves better for our use case), but its Contradiction Resolution
numbers are a useful second data point (alongside STALE) that automatic conflict detection is
industry-wide unsolved — good citation weight for positioning, and its nugget-eval methodology is a
cheap, reusable pattern if/when Jack builds our own eval harness.
