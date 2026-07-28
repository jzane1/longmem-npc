# From Recall to Forgetting: Benchmarking Long-Term Memory for Personalized Agents (Memora / FAMA)

- **Authors / venue / year:** Md Nayem Uddin, Kumar Shubham, Eduardo Blanco, Chitta Baral, Gengyu Wang (Arizona State, Genies, U. Arizona) — 2026, ACL 2026 Findings (per the arXiv listing).
- **arXiv / DOI:** arXiv:2604.20006v1 — https://arxiv.org/abs/2604.20006
- **Source:** discovered
- **Overall relevance to longmem-npc:** High — this is an evaluation-harness paper whose central metric (FAMA) is defined as "penalizing reliance on obsolete or invalidated memory," which is exactly the property our bi-temporal `invalid_at` design is supposed to produce and which we currently have no eval harness to measure.
- **Core contribution (2-3 sentences):** Memora is a long-term-memory benchmark spanning weekly/monthly/quarterly synthetic conversation histories with heavy "memory mutation" (updates/deletions), evaluated on three tasks (Remembering, Reasoning, Recommending). It introduces Forgetting-Aware Memory Accuracy (FAMA), a metric that separately scores whether a response includes currently-valid memory (memory presence accuracy) and whether it excludes invalidated/deleted memory (forgetting absence accuracy), combining them so that correct-looking answers built on stale memory are penalized rather than rewarded.

### Mechanisms relevant to us
- Evaluation design that explicitly tracks a full memory trace (add/update/delete operations per entity) and derives two independent criteria sets per question: **memory presence criteria** (valid info that must appear) and **forgetting absence criteria** (invalidated info that must NOT appear) (§3.5).
- The FAMA formula: `FAMA = max(0, MPA − λ·(1 − FAA))`, where λ = `N_forget / (N_presence + N_forget)` is a per-question weight — so questions that stress invalidation more heavily penalize forgetting failures more heavily (§4.2).
- Empirical finding directly diagnostic for our architecture: standard "memory presence" accuracy *overestimates* performance, and the size of the forgetting-aware reduction *grows* with history length for memory agents (18.2 → 29.5 points weekly→quarterly), i.e., agents increasingly reuse memory that "should have been revised or discarded" as memory scales (§5, Table 5).

### Mechanisms relevant to us
(see above — table format not needed twice)

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none — this is an eval-harness paper; it does not propose a storage/retrieval/decay mechanism that competes with ours)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** End-to-end evaluation harness for long-term memory correctness (baseline gap: "No end-to-end evaluation harness. Only a structural pytest suite exists — no LongMemEval-style accuracy/recall benchmark... no memory-conflict or staleness eval").
- **What the paper does:** Builds simulated multi-session user histories with ground-truth memory traces (every add/update/delete event recorded), then derives per-question binary criteria split into "must include" (valid) and "must exclude" (invalidated) sets, scored by 3-judge LLM majority vote (88.3% human agreement, κ 0.86–0.90) — *evidence:* §3.5–4.2, "FAMA rewards correct use of valid memory while explicitly penalizing reliance on obsolete memory."
- **Why worth adopting for an NPC memory service:** This is close to a template for the eval harness our own architecture is missing, and it targets precisely the invariant we care most about — that superseded content (`invalid_at` set) must not leak back into character output. A longmem-npc-flavored FAMA could be built directly from our own bi-temporal ledger: for any scene, we already know (from `memory_details`/`memory_fact_versions` head history) which facts are "current" vs "superseded" at any `as_of`; the same presence/absence-criteria design could be pointed at NPC dialogue output to check that a corrected/decayed/gist-only fact doesn't leak verbatim outdated detail. It would also give us a metric for the reconstruction mechanism specifically: does a reconstructed telling drift into re-asserting content that was authorial-corrected away?
- **Adoption cost/risk in our stack:** Moderate. We'd need (a) a synthetic long-horizon scenario generator (weeks-to-months of NPC observations with corrections/scene boundaries), (b) LLM-judge scoring against our known ground truth (cheap since we already track validity server-side, unlike this paper which had to reconstruct traces from scratch), (c) a decision on whether judged-eval belongs in the pytest suite (structural-only) or a separate harness — this is squarely the "no end-to-end evaluation harness" gap already logged, not a new one.
- **Docs it would touch:** A new `docs/eval-harness.md` (or extending `test-suite.md`); referenced from `status.md`'s "Sequenced-later ledger" research track (judged-drift / Bartlett-style evals) since this is evaluation, not a build target.
- **Confidence:** High — the metric definition and worked example are concrete and directly portable; the main uncertainty is scenario-generation cost for an NPC/game domain rather than a user-assistant domain.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none — purely evaluation methodology, no storage/retrieval mechanism proposed)*

### Quotable lines / citations for positioning (optional)
- "This overlooks memory misuse, where obsolete information is retrieved and used. As long as the final answer appears correct, reliance on invalidated memory is not penalized." (§1) — useful for framing why byte-identical-but-stale output is a failure mode distinct from wrong retrieval, which is exactly the distinction our reconstruction-vs-decay-vs-invalidation separation is designed to make legible.
- "long-term memory is not a single capability: agents that retrieve well do not necessarily reason well over temporally distributed memory" (§5) — supports treating retrieval quality and reconstruction/dialogue-reasoning quality as separately measurable, consistent with our layered floor-verification discipline.

### Verdict
P2 worth-piloting: not a build target on its own, but the FAMA presence/absence-criteria design is the strongest available template for the eval harness explicitly flagged as missing in our own docs, and it is cheap to adapt because our schema already carries the ground-truth validity state this paper had to simulate.
