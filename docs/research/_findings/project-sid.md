# Project Sid: Many-agent simulations toward AI civilization

- **Authors / venue / year:** Altera.AL (Andrew Ahn, Nic Becker, Manuel Cortes, Arda Demirci,
  Melissa Du, Peter Y Wang, Guangyu Robert Yang, et al.) — arXiv technical report, 2024.
- **arXiv / DOI:** arXiv:2411.00114v1 [cs.AI], 31 Oct 2024.
- **Source:** folder (first ~40 pages extracted; paper's own body ends within that window, only
  references/appendix examples follow).
- **Overall relevance to longmem-npc:** Medium — this is a many-agent-scale systems paper (10 to
  1000+ concurrent Minecraft agents), not a memory-architecture paper: its "Memory" module is
  described in one sentence with no scoring/decay/persistence design. Its value to us is (a) a
  validated real-world precedent for the multi-stream-output coherence problem, directly relevant
  to our designed-but-unbuilt "multi-call split-brain" dialogue/behavior separation, and (b) a
  cross-agent relationship/sentiment-tracking technique at population scale, tangential to our
  (currently single-scalar, single-player) reputation mechanism.
- **Core contribution (2-3 sentences):** Introduces PIANO (Parallel Information Aggregation via
  Neural Orchestration), an agent architecture with concurrently-running modules (memory, social
  awareness, goal generation, talking, skill execution, etc.) bottlenecked through a single
  Cognitive Controller that broadcasts one high-level decision to keep multi-stream outputs
  coherent. Demonstrates civilizational-scale benchmarks — autonomous role specialization,
  democratic amendment of collective tax law, and spontaneous meme/religion propagation — in
  simulations up to 500-1000 Minecraft agents.

### Mechanisms relevant to us
- **Coherence via a bottlenecked broadcast decision-maker** (§2.2, "Cognitive Controller"): solves
  the same problem our post-August multi-call split-brain design names (a behavior call and a
  dialogue call risking divergence) but with the opposite philosophy — PIANO enforces agreement by
  having one module's decision strongly condition all others; our design deliberately wants
  *asymmetric* information flow (the dialogue call sees the behavior call's choice only "as
  observed world fact, never 'you decided to'"), achieved statistically (per-call scoring weights)
  rather than architecturally. Worth citing as the documented alternative when that design session
  happens.
- **Social awareness module**: agents track directed, per-relationship sentiment (0-10 scale)
  toward every other agent from LLM-judged summaries of their own conversation history, validated
  to scale to 50 agents with reasonable perceived-vs-true-likeability correlation (§4.1-4.2,
  Fig. 7B). This is a many-agent, many-dyad analog of our single-scalar `agents.reputation`
  (one NPC, one player) — only relevant if/when longmem-npc scope ever extends to NPC-NPC social
  state, which it currently does not (single-player game NPCs).
- **Goal/role sampling via rolling-window LLM summarization** (§5.1, Methods 8.2): social goals are
  regenerated every 5-10 seconds from a rolling window of the last 5 self-generated goals, then
  periodically classified into a "role" by an LLM. This is a **recent-N** sampling strategy — the
  exact approach our own reflection design explicitly rejected in favor of importance × recency
  (2026-07-19 gate ruling references the same principle for retrieval). Useful only as a
  documented worse-baseline contrast, not an improvement.
- **Hallucination-cascade framing** (§1.3, "Reason 1"/"Reason 2"): unintentional single-agent
  hallucination "poisons downstream agent behavior" once it re-enters the agent's own context, and
  independent output modules that disagree (their "Abby"/pickaxe example: chat module says "sure
  thing," action module does something else) cause group-level dysfunction. Good citable
  motivation for *why* an immutable ground-truth record beneath a drifting telling layer matters —
  their agents have no such record, so a hallucination becomes indistinguishable from truth and
  compounds; ours is architecturally prevented from doing that by the bi-temporal invariant.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none — no memory storage, retrieval-scoring, decay, correction, or gate mechanism is specified
in enough detail in this paper to compare against any baseline component)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** A validated concurrent-modules + single-bottleneck-decision architecture for
  keeping multiple simultaneous output streams (talk, action, in our future case a behavior
  directive) coherent in real time.
- **What the paper does:** Runs 10 distinct concurrent modules (memory, action awareness, goal
  generation, social awareness, talking, skill execution, etc.) at different timescales, with a
  Cognitive Controller module synthesizing a bottlenecked summary of agent state and broadcasting
  one decision that "strongly condition[s] the talk-related modules, which leads to higher
  coherence between verbal communication and other actions" — *evidence:* §2.2, p.5-6.
- **Why worth adopting for an NPC memory service:** Our baseline names the multi-call split-brain
  (behavior call + dialogue call) as designed but not built (gap noted). This paper is a real,
  measured existence proof that the coherence failure mode (talk and action disagreeing) is a
  genuine risk at production scale, and offers one concrete fix (broadcast bottleneck) to weigh
  against our own asymmetric-statistical-weights approach when that design session happens —
  useful as a documented alternative, not a drop-in adoption, since our stated research goal is the
  opposite (deliberate, non-architectural asymmetry rather than enforced agreement).
- **Adoption cost/risk in our stack:** Not directly portable — our thesis wants controlled
  asymmetry, PIANO's fix removes asymmetry entirely. Citing it costs nothing; adopting its literal
  mechanism would work against the information-asymmetry research line, so this is filed as
  reference material for the design discussion, not an implementation target.
- **Docs it would touch:** `docs\architecture.md` §9 (behavior output / split-brain), a future
  spec for the multi-call dialogue/behavior separation.
- **Confidence:** Medium — relevant as design-literature counterpoint, not as a mechanism to build.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none — no destructive summarization, ORM, gate-LLM, or embedding-dimension proposal appears)*

### Quotable lines / citations for positioning (optional)
- "Even a small rate of hallucinations can poison downstream agent behavior when agents
  continuously interact with the environment via LM calls" (§1.3) — motivates why an immutable
  ground-truth record beneath a drifting telling layer is a real safeguard, not just a design
  preference.
- "Actions from multiple output streams must therefore be bidirectionally influential. We define
  this quality as coherence." (§1.3) — names precisely the problem our post-August split-brain
  design must solve, with a documented but philosophically opposite solution (enforced broadcast
  agreement vs. our controlled statistical asymmetry).

### Verdict
P3 note-only for direct adoption (nothing here transfers into Postgres/pgvector retrieval,
decay, reconstruction, or correction). P2 worth-piloting as **design-literature counterpoint**:
before the post-August multi-call split-brain is specced, Jack should read PIANO's §2.2
(Cognitive Controller / coherence) as the documented "solve incoherence by enforcing agreement"
alternative to weigh explicitly against our "solve it via asymmetric per-call weights, no masks"
research line — the contrast is worth stating in the eventual spec's rationale.
