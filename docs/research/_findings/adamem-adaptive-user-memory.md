## AdaMem: Adaptive User-Centric Memory for Long-Horizon Dialogue Agents

- **Authors / venue / year:** Shannan Yan, Jingchen Ni, Leqi Zheng, Jiajun Zhang, Peixi Wu, Dacheng Yin, Jing LYU, Chun Yuan, Fengyun Rao (Tsinghua / WeChat Vision, Tencent) — 2026 (arXiv, v2 2026-04-29).
- **arXiv / DOI:** 2603.16496v2 — https://arxiv.org/abs/2603.16496
- **Source:** discovered
- **Overall relevance to longmem-npc:** High — touches three of our lanes at once: question-conditioned retrieval strategy selection (our gate's problem), graph/associative memory (a gap named explicitly in our baseline), and a distinct persona-memory layer (our reflection/identity gap).
- **Core contribution (2-3 sentences):** AdaMem organizes dialogue history into four memory types (working, episodic, persona, graph) and, at query time, uses deterministic keyword-cue detection to decide not just *whether* to expand retrieval but *how* — whether to invoke relation-aware graph expansion, how many hops, which edge-type priors, and how to fuse graph evidence with semantic evidence — reserving an LLM refinement step only for low-confidence route decisions, clipped to narrow ranges. It reaches SOTA on LoCoMo and PERSONAMEM, and ablation shows the graph-memory component contributes the single largest performance drop when removed.

### Mechanisms relevant to us
- **Question-conditioned route planning** (§3.3, §B.2): deterministic cue detection over temporal/relational/attribute/single-hop keyword patterns decides route shape (`use_graph`, hop depth, seed count, edge-type priors, fusion weights); an LLM refiner only fires when rule confidence < 0.75, and its output is clipped to narrow bounded ranges "so the planner remains conservative."
- **Graph memory as a fourth, distinct memory type**: a heterogeneous graph with typed edges (`mentions`, `supports`, `same_topic`, `temporal_next`, `speaker_related`), bounded multi-hop expansion with a fixed hop-decay factor (§3.3, §C.1).
- **Persona memory as a distinct, periodically-distilled layer**: "clustered attributes are merged into aspect-based persona summaries" separate from raw episodic facts (§3.2, "Topic regrouping, persona refresh, and graph synchronization").
- **Additive score fusion**: `score(m|q) = α·s_base + β·s_graph + γ·s_recency + δ·s_fact`, with weights fixed before evaluation and only narrowly LLM-adjustable (§3.3 Eq. 3, §B.6).
- Ablation (Table 3): removing graph memory drops overall F1 from 44.65 → 42.63 (the largest single-component effect, larger than removing the fusion module or the multi-agent pipeline).

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none — AdaMem addresses a different, larger problem shape (multi-participant long-horizon dialogue with a heavier multi-agent pipeline) than our single-NPC gate; its individual mechanisms are additions, not direct replacements of anything we have)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** graph/associative structure over memories, with multi-hop retrieval expansion — named explicitly in our baseline as a gap ("No graph / associative structure over memories... No multi-hop retrieval").
- **What the paper does:** builds a typed-edge heterogeneous graph over messages/topics/facts/attributes/events and performs bounded multi-hop propagation (`s_{d+1}(v) = s_d(u) · w_e · λ`) seeded from semantic matches (§3.3 Eq. 2, §C). Ablation: "Disabling graph memory produces the largest drop, reducing overall F1 from 44.65 to 42.63... relation-aware memory is important for recovering cross-turn dependencies and temporally linked evidence that may be missed by semantic retrieval alone" (§4.4).
- **Why worth adopting for an NPC memory service:** our `identity_components` table already plays a partial associative role (entity/topic index for gist matching + the gate's entity tripwire), but it has no edge structure and no multi-hop expansion — a query can't currently pull in a memory it doesn't directly match because that memory is *linked* to something the query does match (e.g. "the innkeeper's brother" → a memory that never mentions the brother by name but is linked via a `same_topic`/`mentions` edge). This is exactly the kind of cross-turn coherence gap that would matter for an NPC recalling multi-session relationship history.
- **Adoption cost/risk in our stack:** substantial but tractable — this is new-migration territory per our schema-evolves-by-migration rule (a typed edge table over existing memory/entity primary keys, hand-written recursive SQL for bounded-hop traversal, no ORM needed). It would also need its own gate-style conditional-fire logic to stay compliant with "nothing hardcoded" (edge-type priors, hop depth, hop-decay factor all belong in `agents.config`, not literals). The *optional LLM route refiner* AdaMem uses to choose graph parameters is the one piece that would need to stay out of our gate specifically (see THESIS-TENSION) — but the deterministic cue-detection layer is non-LLM and directly portable.
- **Docs it would touch:** a new migration doc + `architecture.md` §4.4 (fact-chain/entity home) and §6 (gate), `docs\mid-dialogue-gate.md` if the graph expansion becomes a new gate rung on the existing degradation ladder.
- **Confidence:** High (the mechanism is clearly described and ablation-validated) / Medium on cost estimate (graph traversal SQL complexity is nontrivial to keep index-friendly at scale).

- **Capability:** a distinct, periodically-refreshed persona-memory layer (attribute distillation), separate from write-time episodic facts.
- **What the paper does:** "clustered attributes are merged into aspect-based persona summaries" by a separate LLM prompt at indexing time, kept apart from episodic fact/event memory (§3.2).
- **Why worth adopting for an NPC memory service:** this is a more concrete instantiation of our own sequenced-later reflection pipeline ("revises seed identity... flows into the rendered identity doc") — AdaMem shows a lighter-weight, always-on version of the same idea (per-attribute clustering + summary refresh) that could inform how reflection eventually distills `identity_components`/`identity_documents`.
- **Adoption cost/risk in our stack:** low as a *design reference* (reflection is already slated, sequenced, not yet built); the persona-refresh prompt shapes in Appendix E are directly reusable as a starting point when reflection is specced.
- **Docs it would touch:** the eventual reflection spec (currently sequenced-later, mechanism undesigned).
- **Confidence:** Medium.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
- **Invariant challenged:** #8, "The retrieval gate is non-LLM."
- **What the paper does that conflicts:** the route planner's optional LLM refinement step ("When the question remains uncertain, an optional LLM refinement step can revise the plan" §3.3) is an LLM call inside the retrieval-decision path, gated only by a confidence threshold.
- **Honest read:** this is not a direct conflict *today* because AdaMem's route planner operates at a different seam than our mid-dialogue gate (it's choosing retrieval STRATEGY for a fixed query, not deciding IF/WHEN to fetch mid-scene) — but if we ever imported AdaMem's route-planning idea directly into `app\gate.py`, the LLM-refiner half would have to be dropped or kept permanently disabled, since even a low-frequency, confidence-gated LLM call inside the gate violates the letter of the invariant. The deterministic cue-detection layer (85%+ of AdaMem's own decisions per their conservative-default design) is the portable, compliant part.

### Quotable lines / citations for positioning (optional)
- "Different questions require different memory structures and retrieval strategies... overly coarse memories may introduce substantial irrelevant context, while overly fine-grained fragments can obscure dependencies." (§1) — a clean articulation of why a single flat retrieval score (our current `relevance × recency × importance`) has a ceiling that structural/associative signals can raise.

### Verdict
P2 worth-piloting: the graph/associative-memory gap is real, named in our own baseline, and AdaMem gives ablation-quantified evidence it's worth the migration cost (largest single ablation effect among their four components) — but it's a genuinely new build target (own spec session, own migration), not a drop-in. The persona-memory-distillation idea is a useful forward reference for when reflection is specced, at P3 note-only priority until that's in the queue.
