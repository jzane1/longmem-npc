## Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents

- **Authors / venue / year:** Shuo Ji, Yibo Li, Bryan Hooi (National University of Singapore) —
  Proceedings of ICML 2026 (PMLR 306).
- **arXiv / DOI:** arXiv:2606.06036v1 [cs.AI], 4 Jun 2026.
- **Source:** folder.
- **Overall relevance to longmem-npc:** Medium-High, with an important caveat up front: **despite the
  title's near-verbatim echo of our thesis language, this paper's "reconstruction" is a different
  concept than ours.** Their reconstruction = an active, multi-turn, LLM-driven *retrieval/traversal*
  process over a graph (deciding what to fetch, adaptively, across several reasoning steps). It is not
  content-level rewriting, drift, identity-conditioning, or confabulation of what a memory *says* — no
  versioning, no anchor, no drift budget exists anywhere in this paper. It is directly comparable to
  our **read path / retrieval scoring** (`app\retrieval.py`), not to our **reconstruction engine**
  (`app\reconstruction.py`).
- **Core contribution (2-3 sentences):** MRAgent reframes memory access as an active, multi-step
  process (not one-shot top-k) over a heterogeneous Cue-Tag-Content graph, where an LLM iteratively
  selects traversal actions conditioned on evidence accumulated so far, pruning irrelevant branches
  instead of doing fixed N-hop graph expansion. It proves active (adaptive) retrieval policies are
  theoretically strictly more expressive than passive (query-only) ones for any budget ≥ 2, and shows
  large empirical gains (up to +23-32% relative) over flat-similarity and fixed-graph-expansion
  baselines on LOCOMO and LongMemEval, at lower token cost than several baselines.

### Mechanisms relevant to us
- **Cue-Tag-Content graph** (§3.1): cues = fine-grained keywords/entities; tags = associative
  relation labels bridging a cue to specific content; content = episodic/semantic/topic nodes. Tags
  let the LLM screen candidate directions *before* touching full content, avoiding combinatorial
  blowup from naive neighbor expansion.
- **Active/adaptive multi-turn retrieval loop** (§4.1-4.2): at each step the LLM selects traversal
  actions (forward: cue→tag→content; reverse: content→cue/tag) conditioned on accumulated state
  `H(t)`, and decides when to stop.
- **Multi-granular layers** (§3.2): episodic (event-specific + timeline-ordered), semantic (stable
  facts/attributes anchored to entity cues), topic/abstraction (recurring patterns across episodes) —
  a three-tier split, versus our two-tier gist (durable, identity-components-matched) / detail
  (decaying) split.
- **Theorem 4.1 / Theorem C.5:** for any retrieval budget T≥2, the passive (query-only) retrieval
  hypothesis class is *strictly* contained in the active (evidence-conditioned) one — a formal
  argument for why flat top-k similarity is fundamentally capped on multi-hop/compositional queries.
- Baselines directly comparable to our current mechanism: their "Similarity-based Retrieval" formula
  `sim(x) = TopK({sim(x,v)}, k)` (§2.2, Eq. 3) **is exactly our read path's shape** (one embed, top-k
  by cosine, no multi-hop, no query-time reasoning).

### STRICTLY-BETTER candidates (beats a mechanism we already have)
- **Component touched:** Read path / retrieval scoring (`app\retrieval.py` — single embed, vector
  top-k over-fetch ×4, re-rank by relevance × recency × importance_norm).
- **Our current mechanism:** One-shot: embed `query_text` as-is, fetch candidates by cosine distance,
  re-rank once. No multi-hop, no reasoning about intermediate evidence, no graph structure beyond the
  identity-components entity index.
- **Paper's mechanism:** Active reconstruction — LLM iteratively traverses a Cue-Tag-Content graph,
  revising its search direction based on what it has found so far — *evidence:* §5.2, Table 1/2: on
  LOCOMO (Gemini backbone) overall LLM-Judge score rises 68.31 → 84.21 (+23.3% relative); temporal
  queries in particular rise 49.22 → 80.37 (+63% relative); on LongMemEval, overall rises 54.65 → 72.95
  (Gemini) and to 86.76 using a stronger retrieval backbone (Table 2). Also cheaper: 118k tokens/sample
  vs. LangMem's 3,268k on LongMemEval (Table 3).
- **Why strictly better:** Flat top-k similarity structurally cannot answer queries where the needed
  evidence isn't semantically close to the query's surface form — their running example (Fig. 2):
  answering a question about "Nate's video game tournaments" actually requires first inferring "July"
  as an intermediate temporal cue to find Caroline's unrelated-looking activity. This is exactly the
  shape of indirect-recall questions an NPC will face from a player ("what were you up to around when
  I last saw you fight with Marcus?").
- **Adoption cost/risk in our stack:** High. Would require: (a) a new migration adding cue/tag/content
  graph tables (permitted — schema evolves by migration); (b) a new write-time LLM extraction step
  (tags + cues per observation — a new model role, allowed under "every model role has its own env
  var," but adds LLM calls beyond the current NLP pass + single Haiku render); (c) most seriously, a
  **multi-turn LLM reasoning loop at read time** (their case study needed 5 turns) — this cuts directly
  against our design discipline of cheap, deterministic, single-embed retrieval (the mid-dialogue
  gate's whole premise is "one embed per turn IS the probe"). It doesn't violate the named "gate is
  non-LLM" invariant literally (that governs whether to fetch, not how candidates are ranked once
  fetched) but is in real tension with that same low-latency, low-cost philosophy, and would need its
  own p50/p95 instrumentation line.
- **Docs it would touch:** docs\read-path.md, docs\architecture.md §6.
- **Confidence:** Medium — the benchmark gains are strong and the theory is rigorous, but LOCOMO/
  LongMemEval are long-chat-history QA benchmarks, not validated on short-turn NPC dialogue recall,
  where the multi-hop problem may be smaller in practice.

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** Associative graph / cue-tag structure over memories for multi-hop retrieval — the
  baseline names this exact gap: "No graph / associative structure over memories (no entity graph, no
  linking beyond identity-components + gist spans + entities[]). No multi-hop retrieval."
- **What the paper does:** A Cue→Tag→Content graph where typed tags mediate between fine-grained cues
  and content nodes, letting the LLM screen candidate directions before paying for full content
  retrieval — *evidence:* §3.1, "By introducing tags as explicit associative intermediates, MRAgent
  enables guided and flexible reasoning over the memory graph... allowing the agent to evaluate and
  prune traversal branches to avoid incurring the computational cost of processing full episodic
  content."
- **Why worth adopting for an NPC memory service:** A *lightweight* version (cue/tag index only, no
  multi-turn LLM loop) could ride on structure we already half-have — `identity_components` is
  already a cue index (canonical + aliases + category) and `memory_fact_versions.entities` is already
  a per-memory cue set (migration 003). Adding a tag layer connecting them could improve multi-hop
  recall for the gate's entity-tripwire path without adopting the full active-reasoning-loop cost.
- **Adoption cost/risk in our stack:** Medium for a cue/tag-index-only version; High (as above) for
  the full active-traversal loop.
- **Docs it would touch:** docs\architecture.md §6, docs\read-path.md, docs\mid-dialogue-gate.md.
- **Confidence:** Medium.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none — directly)*. Explicitly answering the assignment's question: **this paper does not argue our
reconstruction/confabulation stance is wrong or incomplete.** It is silent on content-level drift,
identity-conditioning, and confabulation entirely — its "reconstruction" is scoped strictly to *how
memory is searched*, not *what a memory says once found*. The two mechanisms are orthogonal and could
in principle compose (a smarter graph-based fetch feeding into our identity-conditioned retelling), but
this paper offers no evidence for or against the retelling-drift half of our thesis.

One point worth surfacing as a *favorable* contrast rather than a tension: the paper's own admitted
limitation is exactly the problem our decay/invalidation/eviction machinery solves — *evidence:* §7
Conclusion, "our static construction does not update or consolidate memory over time, so the memory
graph grows monotonically as interactions accumulate, raising storage overhead in long-lived
deployments." Our bi-temporal invalidation + decay-driven reconstruction thinning + cache eviction is
a working answer to a problem this paper leaves as future work.

### Quotable lines / citations for positioning (optional)
- "Memory is Reconstructed, Not Retrieved" (title) — rhetorically aligned with our framing, but flag
  clearly in any citation that the mechanism differs (retrieval-time search vs. content-level
  confabulation), to avoid readers assuming this paper validates our specific mechanism.
- "cognitive neuroscience conceptualizes memory retrieval as an active and associative reconstruction
  process (Rugg & Renoult, 2025), rather than a passive readout of stored content." (§1) — usable as
  outside citation support for the general "retrieval-as-readout is the wrong model" framing, distinct
  from our specific claim about *content* drift.
- "our static construction does not update or consolidate memory over time, so the memory graph grows
  monotonically as interactions accumulate, raising storage overhead in long-lived deployments." (§7)
  — good contrast quote: their acknowledged gap vs. our decay/invalidation answer.

### Verdict
P2 worth-piloting for a *lightweight* cue/tag associative index (reusing `identity_components` +
`entities[]`) to improve multi-hop recall — but the full active LLM-traversal retrieval loop is P3
note-only given its tension with our single-embed, low-latency retrieval philosophy; Jack should decide
whether multi-hop recall quality is worth per-turn LLM cost before pulling this forward. Most
important non-technical action: if this paper is cited in any write-up, state the naming-collision
caveat explicitly — it is not evidence for our content-reconstruction/confabulation mechanism.
