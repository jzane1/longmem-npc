# Democratizing GraphRAG: Linear, CPU-Only Graph Retrieval for Multi-Hop QA (SPRIG)

- **Authors / venue / year:** Qizhi Wang (PingCAP, Data & AI-Innovation Lab) — preprint, 2026.
- **arXiv / DOI:** 2602.23372v1
- **Source:** discovered (second-wave sweep, Lane A)
- **Overall relevance to longmem-npc:** High — directly answers Lane A's core question ("can Personalized PageRank / multi-hop graph retrieval be computed app-side over ordinary structured data, without a dedicated graph DB, without an LLM in the construction loop") with a working, ablated recipe, though its own numbers are an honest tempering, not a slam dunk.
- **Core contribution (2-3 sentences):** SPRIG (Seeded Propagation for Retrieval In Graphs) builds an entity-document bipartite co-occurrence graph using only lightweight NER (spaCy or a regex heuristic) — no LLM, no GPU — and runs Personalized PageRank as sparse matrix-vector iteration (power iteration or a push-based approximation), entirely in application code, over a 4GB CPU budget. It evaluates when this CPU-only graph retrieval helps multi-hop recall versus when strong lexical/dense hybrids (RRF) are already sufficient.

### Mechanisms relevant to us

- Entity-document bipartite graph, TF-IDF edge weighting (§3.2): `w_{e,d} = tf(e,d) · (log((N+1)/df(e)) + 1)`, row-normalized to a transition matrix — this is exactly "entity-linking computed app-side over a store," with no graph database involved at all.
- PPR as plain sparse linear algebra (§3.3): `r = αs + (1-α)Pr`, run by power iteration or push-based approximation with a residual threshold — no LLM calls, no GPU, deterministic, CPU-only, linear in corpus size (§3.4).
- Hub downweighting/pruning as a config knob, not a hardcoded cutoff: edges scaled by `df(e)^{-p}`; optional top-x% hub removal or per-entity outdegree cap (§3.2) — reduces query time 16-28% with negligible recall change (§6.1).
- Seed mixing for hybrid variants (GraphHybrid/GraphDense): entity seeds mixed with top-k BM25/dense-retrieval seeds via an adaptive, Laplace-smoothed mixing ratio (§3.3) — graph-only retrieval underperforms; seeded-hybrid retrieval is where the gains appear.

### STRICTLY-BETTER candidates (beats a mechanism we already have)

*(none — this is a not-yet-built capability question, not a replacement for an existing mechanism)*

### NOT-YET-BUILT candidates (a capability we simply don't have)

- **Capability:** Multi-hop / associative retrieval computed without a dedicated graph database (our baseline's named gap, and the exact question Lane A was scoped to answer).
- **What the paper does:** Builds the graph from NER co-occurrence only (no LLM triple extraction, unlike HippoRAG's OpenIE step), and computes PPR as sparse power iteration in the application process — *evidence:* §1 "a CPU-only, linear-time, token-free GraphRAG pipeline that replaces LLM graph building with lightweight NER-driven co-occurrence graphs"; §3.4 "Graph construction is O(M)... Each PPR query costs O(T·E) using sparse matrix-vector multiplication... does not invoke LLMs."
- **Why worth adopting for an NPC memory service:** It is direct existence-proof that the mechanism Lane A asked about is implementable in exactly our stack shape: entities are already stored (our `entities` text[] / `identity_components` table), an adjacency can be a plain relational table or even computed on the fly from co-occurrence counts fetched by hand-written SQL, and PPR itself needs nothing beyond sparse-matrix code in the app process — no Neo4j, no Apache AGE, no recursive-CTE traversal even, since PPR is iterative linear algebra rather than a path-following graph query. Complementary to GAAMA's finding (also in this second wave): SPRIG independently used the *same* no-LLM-construction, app-side-PPR shape and reports concrete complexity/latency numbers we can budget against (per-query graph-only latency at their corpus scale is worse than dense retrieval; see caveat below).
- **Adoption cost/risk in our stack — the honest caveat:** SPRIG's own results are a *tempering*, not an endorsement of graph-only retrieval: pure entity-seeded `Graph` retrieval **underperforms plain dense retrieval** on both benchmarks (Table 1: HotpotQA R@10 = 0.464 for `Graph` vs 0.811 for `Dense`; 2Wiki R@10 = 0.357 vs 0.609) and even underperforms BM25. The wins only appear in the *hybrid* variants (`GraphHybrid`/`GraphDense`, which seed PPR from vector/lexical top-k results) — and even there, gains over RRF are modest and dataset-dependent (GraphHybrid beats RRF on 2Wiki R@10 but not on HotpotQA; §5). The paper's own discussion (§8) states plainly: "the results characterize when CPU-friendly graph retrieval helps... and when strong lexical hybrids (RRF) are sufficient" — i.e., graph structure is a second-order refinement on top of a strong retrieval baseline, not a standalone win. Latency: at their corpus scale (tens of thousands of passages) query time for graph variants runs into the hundreds of seconds aggregate (Table 1, `QTime` column) — this is a general-corpus multi-hop-QA setting, not our per-NPC memory store, so absolute numbers don't transfer, but the *shape* (query cost scales with graph density and PPR iteration count, and hub pruning is the practical lever) does, and would need budget-testing against our latency targets. Not a schema/migration paper — it says nothing about non-destructive versioning of the graph, since it operates over a static corpus; adapting to our bi-temporal, ever-superseding memory store (co-occurrence would need to be computed from live fact/detail heads only, mirroring the one-live-head pattern) is our own extension to design, not something SPRIG addresses.
- **Docs it would touch:** `architecture.md` §4.4/§6 (graph gap), `read-path.md`, a future graph spec — as a complexity/latency-budgeting reference and a "graph-only is not enough, plan the hybrid seeding" caution, alongside GAAMA's schema.
- **Confidence:** High (the mechanism works and needs no graph DB) / Medium (the retrieval-quality case for adopting it, given graph-only's weak standalone showing).

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)

*(none)*

### Quotable lines / citations for positioning (optional)

- "a realistic path to democratizing GraphRAG without token costs or GPU requirements" (Abstract) — useful shorthand if a graph section of the README wants to preempt "doesn't this need Neo4j" questions.
- "The TF-IDF graph baseline performs poorly relative to entity graphs, suggesting that explicit entity co-occurrence provides a more effective topology for multi-hop navigation than term-level edges" (§8) — supports building the edge substrate from `identity_components`/`entities[]` rather than raw token co-occurrence, consistent with GAAMA's concept-node argument.

### Verdict

**P2, worth-piloting as a complexity/latency reference**, not as a retrieval-quality slam dunk on its own — the paper's honest finding is that graph-only PPR underperforms dense retrieval, and gains require hybrid seeding. Its real contribution to our Lane A question is proof-of-mechanism: PPR over an entity co-occurrence graph is plain sparse linear algebra computable app-side with zero LLM calls and zero graph database, which is the concrete "yes, this is buildable in our stack" answer the corpus was missing. Pair with GAAMA's schema and PhaseGraph's fusion technique before speccing a graph build.
