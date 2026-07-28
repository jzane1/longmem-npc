# MemoryBank: Enhancing Large Language Models with Long-Term Memory

- **Authors / venue / year:** Wanjun Zhong, Lianghong Guo, Qiqi Gao, He Ye, Yanlin Wang — AAAI 2024
  (Sun Yat-Sen University et al.).
- **arXiv / DOI:** arXiv:2305.10250v3 [cs.CL]
- **Source:** folder
- **Overall relevance to longmem-npc:** Medium — most of MemoryBank (dense dual-tower retrieval,
  hierarchical LLM summarization, a persona-summary profile) is strictly cruder than mechanisms we
  already have (our fact-chain retrieval, gist-as-spans, and reconstruction). Its one genuinely new
  idea is the Ebbinghaus-forgetting-curve memory-strength model, where *recall itself* slows decay —
  an axis our decay math doesn't have at all.
- **Core contribution (2-3 sentences):** MemoryBank gives an LLM chatbot ("SiliconFriend") a memory
  store of raw dialogue logs + LLM-written hierarchical event summaries (daily → global) + an
  evolving LLM-written user-personality profile, retrieved via dense dual-tower search (DPR-style).
  Its distinguishing mechanism is a forgetting-curve-based memory-strength model: each memory has a
  strength `S` (initialized to 1) that governs retention `R = e^(-t/S)`; recalling a memory increments
  `S` and resets elapsed time `t` to 0, so frequently-recalled memories decay more slowly (§2.3).

### Mechanisms relevant to us
- **Memory storage:** raw timestamped multi-turn logs, retained in full, *plus* an LLM-generated
  hierarchical summary (per-day → global) and an LLM-generated evolving personality profile
  (per-day → global), both used to construct the chatbot's prompt (§2.1, Fig. 1).
- **Retrieval:** dual-tower dense retrieval (DPR-style), conversation turns and event summaries both
  pre-encoded and FAISS-indexed; current-turn context is the query (§2.2). No importance/recency/
  pin scoring layered on top — plain nearest-neighbor.
- **Memory updating (the one novel mechanism):** Ebbinghaus forgetting curve, `R = e^{-t/S}`, with
  `S` a discrete counter: "We increase S by 1 and reset t to 0" every time a memory is recalled in
  conversation, "hence forget it with a lower probability" (§2.3, direct quote).
- **Evaluation:** simulated 10-day/15-persona memory store, 194 hand-written probing questions,
  human-annotated Retrieval Accuracy / Response Correctness / Contextual Coherence / cross-model
  Ranking (§4.2, Table 2) — a smaller, more manual precursor to LOCOMO-style eval; low reuse value
  for our missing eval harness compared to MemGPT/Mem0's LLM-judge approach.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none.* Retrieval is unweighted dense similarity — strictly less structured than our
`relevance × recency(decay class) × importance_norm` score. The hierarchical summary mechanism is a
cruder, one-shot version of what our gist-spans + reconstruction already do in a more disciplined,
per-query, drift-budgeted way — see positioning note below rather than a tension flag, since
MemoryBank does retain the raw logs and isn't a strict invariant violation, just a weaker design.)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** Recall-reinforced decay — a memory's forgetting rate slows every time it's
  actually retrieved and used, instead of decay being a pure function of age and importance alone.
- **What the paper does:** `R = e^{-t/S}`; `S` starts at 1 and is incremented by 1 (with `t` reset to
  0) on every recall — "This mechanism permits the AI to forget and reinforce memory based on time
  elapsed and the relative significance of the memory" (Abstract); "When a memory item is recalled
  during conversations, it will persist longer in memory" (§2.3).
- **Why worth adopting for an NPC memory service:** our `decay.py` computes `tau_effective` from
  `tau_base × (1 + k·importance_raw)` and age alone — it never reflects how often or how recently a
  detail has actually been surfaced back to the player. A memory the player keeps bringing up in
  dialogue currently decays exactly as fast as one that's never mentioned again, which sits oddly
  against the "psychology, not a database" thesis (spaced-repetition / testing-effect is well-attested
  human-memory literature, same genre as the Warriner-VAD and decay-class choices already in the
  stack).
- **Adoption cost/risk in our stack:** needs a new per-detail counter (times-recalled) and last-
  recalled timestamp, likely on `memory_details` or the fact-version row — a schema addition (new
  migration, per the "schema evolves by numbered migration" rule). Must be threaded carefully against
  invariant #2 ("recency decay ≠ bi-temporal invalidation — never conflate"): recall-count would need
  to enter as an *additional decay input* (e.g., another multiplicative/additive term next to
  `importance_raw` in `tau_effective`), not as a new invalidation trigger, to keep that separation
  clean. Also interacts with the within-scene text-stability invariant — "recall" would need a precise
  definition (a gate fetch? a reconstruction serve? a pin?) so that merely reading a memory once
  within a scene doesn't cause a same-scene decay recompute that breaks byte-identical repeated
  reads.
- **Docs it would touch:** docs\architecture.md (decay math section), `app\decay.py`, a migration
  for the new counter/timestamp column(s), `docs\test-suite.md` Set B (decay).
- **Confidence:** Medium — the psychological grounding is a good thesis fit, but the exact
  integration point (what counts as "recalled," how it composes with the existing tau formula
  without conflating decay/invalidation) is a real design question, not a drop-in.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none clearly demonstrated in the extracted text — MemoryBank's storage explicitly retains raw
logs alongside its summaries ("detailed record... aids in precise memory retrieval" §2.1), so unlike
MemGPT's queue eviction or Mem0's DELETE branch, nothing in the extracted sections shows content
being destroyed or overwritten in place. See positioning note below for the closest related
comparison, which is a design-quality gap rather than a rule violation.)*

### Quotable lines / citations for positioning (optional)
- The hierarchical event summary ("We condense verbose dialogues into a concise daily event summary,
  which is further synthesized into a global summary," §2.1) is a clean, citable instance of the
  *destructive-compression counter-example* the open README task is looking for: a static,
  once-computed LLM paraphrase fed directly to the model as if it were the character's understanding,
  with no per-query drift budget, no identity-conditioning, and no debug/ground-truth split at serve
  time — the exact contrast our reconstruction mechanism (theta/band/drift-budget/write-back) is
  built to avoid. Good candidate quote for that queue item even though it doesn't rise to a formal
  invariant violation (raw logs are retained elsewhere).
- "a more human-like memory mechanism" (Abstract) — same rhetorical territory as our "a psychology,
  not a database" framing; useful contrast in that MemoryBank's psychology is bolted onto retrieval
  strength only, while ours spans decay, typology, affect, importance, and reconstruction.

### Verdict
P2 worth-piloting for recall-reinforced decay specifically (a small, well-scoped addition to
`decay.py` + a migration) — genuinely on-thesis and currently absent. Everything else in the paper
(dense retrieval, hierarchical summarization, personality profile) is P3 note-only: each is a cruder
version of a mechanism longmem-npc already has built more rigorously.
