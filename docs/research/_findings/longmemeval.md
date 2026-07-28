# LongMemEval, Benchmarking Chat Assistants on Long-Term Interactive Memory

- **Authors / venue / year:** Di Wu, Hongwei Wang, Wenhao Yu, Yuwei Zhang, Kai-Wei Chang, Dong Yu — ICLR 2025
- **arXiv / DOI:** arXiv:2410.10813v2
- **Source:** folder
- **Overall relevance to longmem-npc:** High — it is the canonical accuracy/recall benchmark design for exactly the gap our baseline names: "No end-to-end evaluation harness... no LongMemEval-style accuracy/recall benchmark." Its task taxonomy and construction pipeline are close to directly portable onto our observe → retrieve → dialogue pipeline.
- **Core contribution (2-3 sentences):** A 500-question benchmark testing five core long-term memory abilities (information extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention) embedded in freely-scalable synthetic chat histories (115k–1.5M tokens), built via a needle-in-haystack pipeline with human-curated questions and LLM-simulated indirect evidence sessions. It also proposes a unified indexing/retrieval/reading framework and shows concrete design levers (value granularity, key expansion, time-aware query expansion, Chain-of-Note reading) that measurably improve recall and QA accuracy.

### Mechanisms relevant to us
- Five-ability task taxonomy (IE, multi-session reasoning, temporal reasoning, knowledge updates, abstention) — a ready-made organizing structure for an eval suite.
- Needle-in-haystack history construction: evidence statements are conveyed *indirectly* (self-chat instructed to reveal facts incidentally, not declaratively) and distributed across sessions/positions, then diluted with non-conflicting distractor sessions and timestamped.
- "Knowledge-update" question type: an evidence statement is later contradicted/updated (e.g., "Hawaii last month" → "actually Paris last week"), and the system must answer with the *current* truth, not the stale one.
- Time-aware indexing + query-time range extraction for temporal-reasoning questions (index events with inferred dates; extract a time range from the query to restrict search).
- Retrieval metrics: Recall@k and NDCG@k reported directly against human-annotated answer-location labels.
- QA correctness via an LLM judge (prompt-engineered GPT-4o), independently meta-evaluated at >97% agreement with human experts, with per-question-type judging prompts (e.g., off-by-one tolerance for date-math questions, "contains the correct answer" tolerance for verbose responses).
- Reading-strategy findings: Chain-of-Note (extract-then-reason) + structured JSON presentation of retrieved items improves QA accuracy up to 10 absolute points over natural-language dumps, even under *oracle* retrieval.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none — this is an evaluation-methodology paper; the memory mechanisms it studies are conventional RAG/summarization baselines, not architectures that outperform reconstruction, decay, or bi-temporal correction)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** Judged accuracy/recall eval harness with a fixed question taxonomy, an LLM-judge scoring protocol, and Recall@k/NDCG@k retrieval metrics.
- **What the paper does:** Defines a 4-tuple (session sequence, question, question time, answer/rubric); streams sessions into the system under test; asks the question in a fresh session; scores with an LLM judge whose prompt is tuned per question type. — *evidence:* §3.1 "The evaluation of LONGMEMEVAL requires an instance of 4-tuple (S, q, tq, a)"; §3.3 "we prompt-engineer the gpt-4o-2024-08-06 model... more than 97% agreement with human experts."
- **Why worth adopting for an NPC memory service:** Our baseline has zero accuracy measurement — the structural pytest suite proves shapes and formulas, never "did retrieval actually surface the right memory" or "did the dialogue turn actually reflect the corrected fact." An LLM-judge harness closes exactly that gap and is cheap to bootstrap since our fake-mode providers already give deterministic embeddings for scripted scenarios.
- **Adoption cost/risk in our stack:** Low-to-medium. Needs a new `tests`-adjacent (or separate) eval harness that drives `run_dialogue_turn`/retrieval over scripted event sequences and scores with a judge call — a new instrumentation surface, not a schema change. Judge-model cost is a new line item (per CLAUDE.md, would need its own env var/role — "every model role... has its own env var").
- **Docs it would touch:** A new `docs\eval-harness.md`; `docs\status.md` open-questions/queue.
- **Confidence:** High

- **Capability:** "Knowledge-update" question construction pattern (a fact is asserted, then later contradicted/updated, and the system is graded on answering with the *current* value while tolerating mention of the stale value).
- **What the paper does:** — *evidence:* Fig. 1 knowledge-update example: "Where did I go on my most recent family trip?" evidence updates Hawaii → Paris; judge prompt (Appendix A.4): "the response should be considered as correct as long as the updated answer is the required answer."
- **Why worth adopting for an NPC memory service:** This is a direct, reusable template for judged evaluation of our fact-level correction (migration 002) and authorial correction — we currently only structurally assert that the DB head flips and the embedding follows; we have never judged whether a downstream dialogue *answer* reflects the corrected fact when the query has to compete against the stale version's residual vector similarity in a populated store.
- **Adoption cost/risk in our stack:** Low. Reuses existing `:correct` / correction endpoint; only new work is the QA harness + judge prompt.
- **Docs it would touch:** `docs\fact-level-correction.md`, `docs\authorial-correction.md` (eval appendix), new eval-harness doc.
- **Confidence:** High

- **Capability:** Time-aware query expansion for temporal-reasoning questions (extract an explicit time range from the query, restrict candidate search to it) — measured to improve recall 6.8–11.3%.
- **What the paper does:** — *evidence:* §5.4, "values are additionally indexed by the dates of the events they contain. During retrieval, an LLM MT extracts a time range for time-sensitive queries."
- **Why worth adopting for an NPC memory service:** Our `event_time` context stamp is currently "accepted-but-reserved" on the query side (baseline: "location/entities/event_time accepted-but-reserved (future encoding-context term)"). This is a concrete, validated design for the eventual encoding-context term, and — separately — a concrete *judged* temporal-reasoning eval category we could run against our decay math and `as_of` mechanic today (currently proven only via structural/formula assertions, never via "did the character answer '5 months' correctly").
- **Adoption cost/risk in our stack:** Medium if adopted as a live query-time feature (new LLM call = new model role, config-not-hardcoded per CLAUDE.md); low if adopted only as an eval-construction pattern (no code change, just test data design).
- **Docs it would touch:** `docs\read-path.md` (reserved-slot note), new eval-harness doc.
- **Confidence:** Medium (as a live feature); High (as an eval-construction pattern)

- **Capability:** Abstention (ABS) as a first-class, separately-measured question type: 30 questions deliberately built with a false premise (e.g., asking about a "30-gallon tank" the user never mentioned), requiring the system to recognize the premise is unsupported and decline rather than confabulate an answer.
- **What the paper does:** — *evidence:* §3.2, "we draw 30 questions from the previous question types and modify them into 'false premise' questions, testing whether the model can correctly abstain"; Fig. 1 example: "You did not mention that you have a 30-gallon tank."
- **Why worth adopting for an NPC memory service:** longmem-npc's whole thesis is *controlled* infidelity — drift is licensed only above an immutable record, never fabrication of facts that were never observed. We have no eval that checks the boundary: does reconstruction (or the dialogue call) ever answer confidently about something that was never in the store, versus correctly reporting "no such memory"? This is the sharpest available test of whether "controlled infidelity" is actually staying controlled.
- **Adoption cost/risk in our stack:** Low as an eval addition (no code change — construct scripted scenes with a false-premise query and judge whether the dialogue output fabricates vs. correctly indicates absence). Note our system has no explicit "I don't know" instruction/directive today; the eval would first have to establish a baseline behavior before it could be called pass/fail.
- **Docs it would touch:** New eval-harness doc; possibly `docs\architecture.md` §9 (dialogue output) if a "no matching memory" behavior needs to become an explicit contract.
- **Confidence:** High

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none — this is an evaluation paper; it proposes no storage/eviction mechanism that conflicts with non-destructive bi-temporal storage or any other invariant)*

### Quotable lines / citations for positioning (optional)
- "existing long-term memory benchmarks including recent ones such as LoCoMo also fail to evaluate recall of information provided by the assistant or reasoning with updated user information" (§1) — useful to cite when positioning our fact-level-correction eval as filling a gap the field itself has flagged.
- Commercial-system finding: "ChatGPT tended to overwrite crucial information as the chat continues" (§3.4) — a real-world example of *destructive* update-in-place failing, a positioning contrast for our non-destructive bi-temporal design.

### Verdict
P1 adopt-soon: build a small judged QA eval harness modeled on LongMemEval's 4-tuple formulation + LLM-judge protocol, seeded first with a knowledge-update category (tests fact-level/authorial correction) and an abstention category (tests the confabulation boundary) — these two categories map most directly onto what makes longmem-npc's design distinctive and are currently completely unverified end-to-end.
