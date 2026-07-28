> Read `_baseline\current-architecture.md` FIRST. Every judgment is relative to that yardstick.

---

## Fixed-Persona SLMs with Modular Memory: Scalable NPC Dialogue on Consumer Hardware

- **Authors / venue / year:** Martin Braas Andreasen, Lukas Esterle (Aarhus University); 2025
- **arXiv / DOI:** arXiv:2511.10277v1 [cs.AI]
- **Source:** folder
- **Overall relevance to longmem-npc:** Low-Medium — this paper's central concern (local Small Language Models on consumer GPUs, per-NPC fine-tuned personas, swappable memory stores) is explicitly out of scope for our stack: we use hosted Claude/OpenAI models via API per named role, not fine-tuned local models, and a second/local embedding model is already noted in our own docs as colliding with the locked 1536-dim column. Its memory system (two flat ChromaDB vector stores, top-k cosine, no decay/bi-temporal/versioning) is materially simpler than ours on every axis. Relevance is mainly in its **evaluation methodology**, which happens to be judge-free and structural — compatible with our testing discipline in a way the other two NPC papers in this batch are not.
- **Core contribution (2-3 sentences):** Proposes fine-tuning small open-source LMs (DistilGPT-2, TinyLlama-1.1B, Mistral-7B) via LoRA to encode a fixed NPC persona, then pairing each with a runtime-swappable pair of vector memory stores (conversational history + world knowledge) so one fine-tuned model can power many distinct NPC instances. Evaluates dialogue quality (factuality/context-retention/fluency), hardware efficiency (VRAM/disk/latency), and memory-swap/retrieval scalability on consumer hardware.

### Mechanisms relevant to us
- **Runtime-swappable per-instance memory decoupled from the model** (multiple NPCs of the same "type" share one fine-tuned model, each with its own ChromaDB memory pair) — architecturally analogous to (but far cruder than) our own `agents` table already decoupling one set of API-model roles from many NPC rows, each with its own memory/reputation/config.
- **Two-store split**: "Conversation memory stores prior interactions... World knowledge stores structured facts, background information, or narrative hooks" (Introduction, System Overview) — both flat vector stores, queried independently top-k, concatenated into the prompt. No decay, no importance, no versioning, no bi-temporal structure of any kind.
- **Context-retention evaluation via keyword recall**: "NPCs were tested on their ability to reference keywords introduced earlier, such as the player's name" across 30 multi-turn interactions (Dialogue Quality / Context Retention) — this is a **structural**, non-LLM-judged check (did the output contain/reference a specific token), not an LLM-as-judge score.
- **Hardware/scalability benchmarking**: memory swap time <0.03s and retrieval time <0.042s even at 1000 entries regardless of database size (Runtime Modularity Metrics) — infra numbers for local deployment, not applicable to our Postgres/pgvector + hosted-API stack.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none)* — the memory system here (flat two-bucket vector retrieval, no decay/importance/bi-temporal/versioning) is strictly less capable than our read path, decay math, and fact-version chain on every dimension the baseline names.

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** A cheap, judge-free structural test for whether a dialogue turn's output actually surfaces a specific previously-introduced fact (memory retention "worked"), as opposed to only verifying that retrieval *returned* the right memory IDs/scores.
- **What the paper does:** "NPCs were tested on their ability to reference keywords introduced earlier, such as the player's name" — scored as simple correct/incorrect keyword presence across 30 multi-turn probes, no LLM judge involved (Context Retention subsection, Fig. 3).
- **Why worth adopting for an NPC memory service:** Our structural pytest suite (38 scenarios) verifies that the *pipeline* does the right thing structurally (IDs, scores, decay math, gate fires, correction chains) but nothing currently checks that a live dialogue turn's *generated prose* actually surfaces a fact it retrieved — that gap sits between our structural suite and a full judged-drift eval (both named/considered elsewhere: see `memory-driven-roleplay.md`'s MREval finding for the judge-based version). A keyword/entity-presence check on the dialogue call's output is compatible with our "structural-only tests" discipline (test-suite.md) precisely because it needs no LLM judge — a deterministic string/entity-membership assertion.
- **Adoption cost/risk in our stack:** Low — no schema change; a new pytest scenario against the load-driver/dialogue-turn seam using deterministic-fake dialogue provider outputs (or a marked `nlp`-tier scenario using the real provider, mirroring how the suite already isolates model-calling tests). Cheap to pilot, additive only.
- **Docs it would touch:** `test-suite.md` (a new judge-free retention check, distinct from both the structural suite and any future LLM-judged eval).
- **Confidence:** Medium — a small, clearly-scoped, low-risk addition; not thesis-critical, but directly usable given our exact testing philosophy.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none)* — no destructive operation, no gate-LLM, no ORM; the local-SLM/fine-tuning angle is a stack mismatch (see below) rather than an invariant violation.

### Quotable lines / citations for positioning (optional)
- Useful contrast point for the README's "why hosted models + a real DB, not a local SLM stack" framing: "This limitation arises from their substantial hardware requirements, latency constraints, and the necessity to maintain clearly defined knowledge boundaries" (Abstract) — their solution (fine-tune small local models) versus ours (constrain via prompting/structure over a shared API model) trade the same problem off differently.

### Verdict
P3 note-only. The local-SLM/fine-tuning/consumer-hardware angle is explicitly out of scope for our fixed stack (already flagged in our own docs as a "later/optional" item colliding with the locked embedding dimension). The one transferable idea — a judge-free keyword/fact-presence retention check — is a cheap, low-priority pilot candidate for `test-suite.md`, not because this paper's memory system is sophisticated (it isn't, relative to ours), but because its evaluation habit happens to match our own structural-testing discipline better than the LLM-judge-heavy eval frameworks in the other two NPC papers this batch covered.
