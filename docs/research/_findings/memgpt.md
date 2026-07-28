# MemGPT: Towards LLMs as Operating Systems

- **Authors / venue / year:** Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G.
  Patil, Ion Stoica, Joseph E. Gonzalez — UC Berkeley, 2023/2024.
- **arXiv / DOI:** arXiv:2310.08560v2 [cs.AI]
- **Source:** folder
- **Overall relevance to longmem-npc:** Medium — it is the architectural ancestor of the whole
  "memory-as-tiered-storage" line (and even uses Postgres+pgvector for archival storage, our exact
  infra), but its core mechanism (LLM self-directed paging + recursive-summary eviction) is a worse
  fit for a *service* than for a chat-window-bound single agent, and several of its moves conflict
  with our invariants.
- **Core contribution (2-3 sentences):** MemGPT gives a fixed-context LLM the illusion of unbounded
  context via an OS-style memory hierarchy: "main context" (system instructions + editable working
  context + a FIFO message queue) is what the model actually sees; "external context" (archival +
  recall storage, DB-backed) holds everything else. The LLM itself issues function calls to move
  data between tiers — writing to working context, searching archival storage, paginating results —
  and a queue manager evicts overflowing FIFO messages into a recursive summary once a token
  threshold is crossed.

### Mechanisms relevant to us
- Two-tier memory (main context vs. external archival/recall storage), moved by LLM function calls
  (§2.1–2.3).
- Queue eviction: once prompt tokens cross a "flush token count," the manager evicts a chunk of
  messages and folds them into a recursive summary that is reinserted as the first queue slot (§2.2).
  The evicted originals remain in recall storage (a DB), retrievable but no longer in-context.
- Multi-hop, LLM-directed retrieval: function chaining lets the model issue several searches in one
  turn and page through results (`archival_storage.search(..., page=2)`), demonstrated on a nested
  key-value lookup task requiring up to 4 sequential hops (§3.2.2, Fig. 8).
- Working context: a small, unstructured, freely-LLM-editable text block for persona/user facts,
  edited via function call, e.g. `working_context.replace("Boyfriend named James", "Ex-boyfriend
  named James")` (Fig. 4).
- Archival storage in their implementation is literally Postgres + pgvector with an HNSW index
  (§3.2.1: "MemGPT's default storage settings which uses PostgreSQL for archival memory storage with
  vector search enabled via the pgvector extension... an HNSW index"). Same DB choice as us — not a
  finding, but worth noting as independent validation of the stack.
- Evaluation: "Deep Memory Retrieval" (DMR) task + an LLM-as-judge grading rubric with worked
  CORRECT/WRONG examples (§3.1.1, Appendix 6.1.2).

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none — MemGPT's storage/decay/retrieval mechanisms are all coarser than what's already built;
see decay math, gist-span mechanism, and gated retrieval in the baseline, which are each more
structured than anything here)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** LLM-directed, multi-hop/iterative retrieval within a single turn (agent pages
  through search results and chains multiple queries to resolve a compound lookup).
- **What the paper does:** Function chaining with a `request_heartbeat` flag lets the model
  immediately re-invoke itself after a function call completes, so it can issue a follow-up search
  instead of yielding; demonstrated on a "nested KV retrieval" task needing up to 4 sequential hops
  where fixed single-shot retrieval baselines hit 0% accuracy by 2-3 nesting levels while MemGPT (GPT-4)
  stays unaffected (§2.4, §3.2.2, Fig. 7-8: "MemGPT is the only approach that is able to consistently
  complete the nested KV task beyond 2 nesting levels").
- **Why worth adopting for an NPC memory service:** the baseline explicitly names "No graph /
  associative structure over memories... No multi-hop retrieval" as an open gap. This is direct
  evidence that a single fixed top-k retrieval (our current read path) cannot answer compound
  questions ("who introduced you to the person who gave you the birthday cake") that require chaining.
- **Adoption cost/risk in our stack:** meaningful — this pattern is an *LLM deciding when/what to
  retrieve*, which is exactly the shape the baseline's invariant #8 rules out for the gate ("The
  retrieval gate is non-LLM"). Any adoption would need to be scoped as a capability the **dialogue
  call** can invoke on top of the existing non-LLM gate (e.g., a bounded follow-up retrieval tool
  available to the single Sonnet call), never as a replacement for `app\gate.py`'s heuristics — this
  distinction should be surfaced to Jack rather than assumed.
- **Docs it would touch:** docs\architecture.md §6 (retrieval), a new spec if pursued (post mid-
  dialogue-gate — currently in the "no multi-hop retrieval" gap list).
- **Confidence:** Medium (the task is synthetic/UUID-chase, not obviously representative of NPC-style
  compound recall — but the mechanism itself is real and the gap it fills is one we've named).

- **Capability:** A worked LLM-as-judge evaluation rubric for long-term-memory recall (Deep Memory
  Retrieval), with a concrete prompt template that generously scores paraphrase-equivalent answers.
- **What the paper does:** §3.1.1 + Appendix 6.1.2 give the full DMR question-generation prompt and
  judge prompt ("as long as it touches on the same topic as the gold answer, it should be counted as
  CORRECT" with worked CORRECT/WRONG examples).
- **Why worth adopting for an NPC memory service:** baseline names "No end-to-end evaluation
  harness... no LongMemEval-style accuracy/recall benchmark" as an open gap. This is a directly
  reusable prompt pattern for building that harness (generate a question that can only be answered
  from a specific stored memory, then LLM-judge the dialogue turn's answer against it).
- **Adoption cost/risk in our stack:** low — it's a prompting pattern, no infra change; would need a
  new eval-role env var per the "every model role has its own env var" rule if used at eval time.
- **Docs it would touch:** a new eval-harness spec (currently just a bullet in "known gaps").
- **Confidence:** Medium.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
- **Invariant challenged:** #1, Non-destructive bi-temporal storage.
- **What the paper does that conflicts:** the queue manager, on overflow, "generates a new recursive
  summary using the existing recursive summary and evicted messages" (§2.2) — a destructive,
  irreversible compression of prior turns into a single rewritten paragraph that becomes the model's
  only recent-context view once evicted. Separately, working-context edits are literal in-place
  string replacement — `working_context.replace("Boyfriend named James", "Ex-boyfriend named
  James")` (Fig. 4) — overwriting the old fact with no trace kept in main context (it is retained in
  the underlying recall-storage DB, but the *served* representation is destructively overwritten).
- **Honest read:** this is the same family of tension the baseline already anticipates ("much of
  Mem0/MemoryBank/MemGPT eviction"). It's a genuine weakness relative to our design, not an
  apples-to-oranges mismatch: MemGPT is solving "stay under a token budget," which recursive
  summarization does cheaply, while we solve "never let the record itself become unreliable," which
  costs us the reconstruction machinery MemGPT doesn't need. Not adoptable as a mechanism, but a fair
  positioning contrast for the README.

### Quotable lines / citations for positioning (optional)
- "We allow the LLM to manage what is placed in its own context (analogous to physical memory) via
  an `LLM OS`" (§1) — useful contrast for "a psychology, not a database": MemGPT manages memory as a
  *resource-scheduling* problem, we manage it as a *narrative-fidelity* problem.
- Working-context edit example (Fig. 4) is a clean, citable instance of destructive in-place
  correction — good counter-example material alongside MemoryBank for the open README task
  "destructive-compression counter-example pick."

### Verdict
P3 note-only for direct adoption (its storage/decay mechanisms are strictly cruder than ours), but
P2 worth-piloting for two narrow, separable ideas: (a) an LLM-directed bounded multi-hop
follow-up-retrieval tool for the dialogue call (not the gate) to close the "no multi-hop retrieval"
gap, and (b) reusing its DMR + LLM-judge prompt pattern as a starting point for the still-missing
eval harness.
