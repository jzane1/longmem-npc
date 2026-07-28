# From RAG to Memory: Non-Parametric Continual Learning for Large Language Models (HippoRAG 2)

- **Authors / venue / year:** Jiménez Gutiérrez, Shu, Qi, Zhou, Su — ICML 2025
- **arXiv / DOI:** arXiv:2502.14802v2
- **Source:** folder
- **Overall relevance to longmem-npc:** High — this is HippoRAG's direct successor, refining the same KG+PPR associative-retrieval mechanism (see sibling finding `hipporag.md`) specifically to fix the failure mode where structure-augmented retrieval hurts plain factual recall. That robustness fix, plus a striking result about summarization-based memory methods, both matter for our design.
- **Core contribution (2-3 sentences):** The authors show that existing structure-augmented RAG methods (HippoRAG, RAPTOR, GraphRAG, LightRAG) all trade away simple factual-QA accuracy for their gains on multi-hop/associative or sense-making tasks. HippoRAG 2 fixes this by integrating passage nodes directly into the same KG as entity/phrase nodes ("dense-sparse integration"), linking queries to whole KG triples rather than just NER'd entities ("deeper contextualization"), and adding an LLM-based "recognition memory" filter over candidate triples before running PPR — achieving the best score across factual, associative, *and* sense-making benchmarks simultaneously (Fig. 1, Table 2).

### Mechanisms relevant to us
- **Dense-sparse graph integration:** passage nodes are added to the KG alongside entity/phrase nodes, joined by a `"contains"` context edge, so vector-level (passage) and symbolic (entity/relation) signals live in one graph rather than being combined by post-hoc score aggregation (§3.2, p.4-5).
- **Query-to-triple linking:** instead of extracting named entities from the query and matching them to KG nodes (HippoRAG's approach), the whole query embedding is matched against KG *triples* directly — a like-for-like granularity match that recovers 12.5% more Recall@5 on average than NER-to-node (§3.3, Table 4, p.8: *"query-to-triple improves Recall@5 by 12.5% compared to NER-to-node"*).
- **Recognition memory (triple filtering):** an LLM pass filters the top-k retrieved triples down to only the relevant ones before they seed PPR — modeled explicitly on the recall/recognition distinction in human memory retrieval (§3.4, p.5-6).
- **Robustness result validating non-destructive gist storage:** structure-augmented methods that *rewrite* content into summaries (RAPTOR, GraphRAG, LightRAG) score dramatically worse than plain dense retrieval on simple factual QA — e.g. PopQA F1 drops to 2.4 (RAPTOR) / 1.6 (GraphRAG) / 11.6 (LightRAG) vs. 55-62 for large embedding models and 51.7-53.8 for HippoRAG/HippoRAG 2 (Table 2, p.7). The paper attributes this directly to "the noise introduced into the retrieval corpora by [the] LLM summarization mechanism" (§1, p.2).

### STRICTLY-BETTER candidates
*(none — like its predecessor, this is a new capability rather than an improvement on an existing scoring/decay/reconstruction mechanism we already have)*

### NOT-YET-BUILT candidates

- **Capability:** The same graph-based associative retrieval channel named in `hipporag.md`, but engineered so it doesn't regress plain single-fact recall — relevant because any pilot of graph retrieval in our read path would need to run *alongside* (not instead of) our existing vector-similarity scoring, and this paper is the evidence for how to do that without a quality regression.
- **What the paper does:** Keeps passages as first-class nodes in the same graph as entities (§3.2) and uses an LLM filter to drop irrelevant candidate triples before they can dilute PPR's seed set (§3.4) — the two refinements responsible for HippoRAG 2 showing *"no deterioration and even slight improvements in factual memory and sense-making tasks"* while still gaining 7 points average on associativity (Abstract; Table 2 confirms HippoRAG 2 ≥ NV-Embed-v2 on NQ/PopQA).
- **Why worth adopting for an NPC memory service:** If graph-based multi-hop retrieval (the `hipporag.md` finding) is ever piloted, this paper is the direct evidence that a naive KG-only retrieval channel will hurt ordinary single-fact recall unless passages/relevance are integrated the way HippoRAG 2 does it — i.e., this is the "how to not regress the read path" companion finding, not a separate capability.
- **Adoption cost/risk in our stack:** Same graph/PPR infra cost as `hipporag.md`, plus one additional LLM call per retrieval turn for the recognition-memory filter — a real latency/cost line item against our per-seam instrumentation discipline (the read path and gate are both timing-budgeted; an extra LLM round-trip on every graph-assisted fetch is a cost that would need its own env var and its own p50/p95 line, per our instrument-at-the-seam rule).
- **Docs it would touch:** Same as `hipporag.md` — `docs\architecture.md` §4.4, `docs\read-path.md`, a future graph-retrieval spec; the recognition-memory filter would additionally touch `docs\architecture.md`'s model-role list (a new role, or overload of an existing Haiku-class role) and instrumentation docs.
- **Confidence:** Medium — the mechanism is well-evidenced for general QA corpora, but our per-NPC memory corpus is much smaller and more entity-dense than Wikipedia-scale QA benchmarks, so the magnitude of the "recognition memory" fix's necessity here is untested for our use case (flagged, not assumed).

### THESIS-TENSION flags
*(none directly — additive KG growth stays compatible with non-destructive storage; the one real friction is a cost/latency tradeoff, not an invariant violation, so it's noted as an adoption-cost line above rather than a tension)*

### Quotable lines / citations for positioning
- Abstract: *"their performance on more basic factual memory tasks drops considerably below standard RAG"* — sharp, citable evidence that structure/summarization-heavy memory systems pay a real accuracy tax, useful ammunition for our non-destructive/span-pointer-gist design choice (we store gist as pointers into `observation_text`, never a rewritten summary — precisely the failure mode this paper measures in RAPTOR/GraphRAG/LightRAG).
- §1, p.2: attributes RAPTOR's regression to *"the noise introduced into the retrieval corpora by its LLM summarization mechanism"* — direct empirical support for treating LLM-rewritten memory as lossy/risky, worth a line in a README positioning section contrasting our approach against summarization-based competitors.

### Verdict
P3 note-only for now (companion evidence to the `hipporag.md` P2 finding) — don't pilot this independently of the graph-retrieval capability itself, but if that capability is ever built, this paper's dense-sparse integration and recognition-memory filter should be read as required engineering, not optional polish, given the demonstrated regression risk on plain factual recall.
