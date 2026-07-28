## Less Context, More Accuracy: A Bi-Temporal Memory Engine for LLM Agents Where a Lean Retrieved Context Beats the Full History

- **Authors / venue / year:** Liuyin Wang (independent researcher) — 2026 (arXiv preprint)
- **arXiv / DOI:** arXiv:2606.09900v1
- **Source:** folder
- **Overall relevance to longmem-npc:** High — a quantified, benchmarked validation of the exact philosophy our gate + retrieval-k + reconstruction thinning already commit to ("show less, curated, detail"), plus two concrete capability gaps (lexical/graph retrieval fusion, an explicit abstention gate) that we don't have.
- **Core contribution (2-3 sentences):** Engram is a dual-process (fast write / async consolidate) bi-temporal memory engine whose hybrid read path (dense + BM25 lexical + graph n-hop + recency + salience, fused by Reciprocal Rank Fusion) assembles a lean, provenance-tagged, ~9.6k-token context that scores 83.6% on the full 500-question LongMemEvalS benchmark under the official judge, versus 73.2% for stuffing the entire ~79k-token history into the prompt (+10.4 points, McNemar p < 10⁻⁶, 8x fewer tokens). A load-bearing ablation-style observation: a facts-only read path loses recall (extraction drops verbatim detail some questions need), so the winning configuration is hybrid facts *plus* raw retrieved chunks, not facts alone.

### Mechanisms relevant to us
- **Bi-temporal fact model** (`valid_at`/`invalid_at` + `created_at`/`expired_at` + a `supersedes` pointer, never hard-delete) — near-identical in shape to our `memory_fact_versions`/`memory_details` chains. Validation, not a new mechanism.
- **"Cheap-then-escalate" conflict resolution** (§3.4): exact slot match → embedding similarity → content subsumption → only genuinely ambiguous cases escalate to an LLM call. We have no analogous automatic contradiction *detection* today — our correction verbs are entirely operator/diegetic-triggered, never self-detected.
- **Hybrid multi-signal retrieval fusion** (dense + BM25 lexical + graph n-hop + recency + salience, combined via RRF) vs. our current `relevance × recency(decay class) × importance_norm` weighted-product score. We have no lexical (BM25) channel and no graph/multi-hop channel (baseline's own known-gaps list already names both: "No graph / associative structure over memories... No multi-hop retrieval").
- **Abstention gate**: the read path "passes an abstention gate that declines to answer when the evidence is absent" before assembling context — distinct from our fail-quiet-on-embed-failure path, which is about *failure*, not about *genuine absence of a matching memory*.
- **Neutral, reproducible eval-harness discipline** (§4, measurement-integrity notes: no truncated baseline, official judge not home-grown, full-context baseline in every table, raw per-question logs published) — directly relevant to the baseline's own named gap, "No end-to-end evaluation harness."

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none, presented honestly)* — The paper's one clean, ablation-backed claim is "lean/curated retrieval beats full-context" and "hybrid facts+chunks beats facts-only." Both *validate* mechanisms we already committed to (retrieval-k with over-fetch, the mid-dialogue gate keeping retrieval conditional/lean, reconstruction's time-thinned detail slice) rather than beating them — we never compare against a full-context baseline in the first place. The RRF multi-signal fusion formula is not ablated in the paper against a simple weighted-product scorer like ours, so claiming it as a proven strictly-better replacement for our `relevance × recency × importance_norm` would overclaim past the paper's actual evidence; it belongs below as a capability gap, not a proven win.

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** Lexical (BM25) + graph n-hop retrieval channels fused alongside our existing dense/cosine channel.
- **What the paper does:** Retrieves in parallel through four complementary channels and fuses ranked lists with Reciprocal Rank Fusion rather than a single weighted product — *evidence:* §3.5, "dense semantic, BM25 lexical, graph n-hop from the query's entities, and recency/salience... fuses the ranked lists with Reciprocal Rank Fusion."
- **Why worth adopting for an NPC memory service:** our retrieval is pure-vector; a lexical channel would catch exact-name/phrase hits that embeddings sometimes miss (proper nouns, exact quoted dialogue), and a graph channel over `identity_components`/`entities[]` would give the multi-hop retrieval the baseline lists as a flat-out gap today.
- **Adoption cost/risk in our stack:** Non-trivial — BM25 needs a Postgres full-text index (tsvector/GIN, hand-written SQL, no new dependency conflict) and is cheap; a real entity graph is a bigger schema/architecture lift (new edges/relations beyond `identity_components` + `entities[]`), explicitly called out already as "no graph / associative structure... no multi-hop retrieval" in the known-gaps list. Fusion weights would need to be per-agent-configurable per the "nothing integrator-configurable is hardcoded" invariant.
- **Docs it would touch:** `docs/architecture.md` §6 (retrieval scoring), `docs/read-path.md`, a new migration for a lexical index and/or graph edges.
- **Confidence:** Medium — genuinely not-yet-built and evidenced as valuable in this paper's benchmark, but the paper doesn't isolate RRF-fusion's own contribution from the facts+chunks hybridity finding, so the size of the win for *our* score formula specifically is speculative.

- **Capability:** An explicit abstention/"no memory of this" signal distinct from fail-quiet-on-error.
- **What the paper does:** "passes an abstention gate that declines to answer when the evidence is absent" — *evidence:* §3.5, Figure 1 caption; §5 reports 86.7% accuracy on the abstention category specifically, "the system declines when memory lacks the answer rather than hallucinating."
- **Why worth adopting for an NPC memory service:** today, when retrieval returns nothing relevant, the dialogue call still has to produce prose from whatever it gets — there's no structured "I genuinely don't know/remember this" signal fed into prompt assembly, only the failure-path `relevance = null`. An explicit low-max-score threshold feeding "the character has no memory of this" into the labeled prompt block would reduce confabulation-by-omission (the NPC inventing detail it was never given, as opposed to the *intentional* reconstruction drift).
- **Adoption cost/risk in our stack:** Low-to-medium — a new knob (threshold) in `app/config.py`, a new labeled prompt block in `app/dialogue.py`'s recollection partition; no schema change. Needs a scope ruling on how it interacts with reconstruction (an abstention-worthy score is different from a below-theta-decay score).
- **Docs it would touch:** `docs/read-path.md`, `docs/cli-harness.md` (prompt assembly), `architecture.md` §9.
- **Confidence:** Medium.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none — the paper's core invariant, "never hard-delete a contradicted fact--invalidate it... and keep the history," is the same non-destructive-storage commitment we already hold; no conflict)*

### Quotable lines / citations for positioning (optional)
- "a precisely retrieved slice that outperforms the noisy full window... turns memory from a cost optimization into a quality improvement" (Abstract/§7)
- "Engram's lean configuration... scores 83.6% versus 73.2% for the full-context baseline (+10.4 points, McNemar exact p < 10⁻⁶) while using 8× fewer tokens" (Abstract)
- "a facts-only read path... loses recall relative to the hybrid path, because extraction drops detail that some questions need verbatim" (§5) — directly supports why our reconstruction serves persisted retold text (not a bare fact) rather than fact-only summaries.
- "never hard-delete a contradicted fact--invalidate it (set invalid_at) and keep the history" (§3.1)

### Verdict
P2 worth-piloting for the two concrete capability gaps (lexical/graph retrieval fusion; an explicit abstention signal) — both are evidenced-elsewhere, not proven strictly-better substitutes for our current scoring, and both would be real, scoped, config-not-hardcoded additions. P3 note-only as validation: our "lean, curated, no full-context replay" retrieval philosophy (gate + retrieval-k + reconstruction thinning) is directionally exactly what this paper's headline result supports, and the paper's neutral-harness discipline is a good template for whenever the baseline's "no end-to-end evaluation harness" gap gets addressed.
