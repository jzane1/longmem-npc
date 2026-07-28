# Calibrated Fusion for Heterogeneous Graph-Vector Retrieval in Multi-Hop QA (PhaseGraph)

- **Authors / venue / year:** Andre Bacellar — preprint, 2026.
- **arXiv / DOI:** 2603.28886v2
- **Source:** discovered (second-wave sweep, Lane A — supporting/adjacent, not a standalone answer)
- **Overall relevance to longmem-npc:** Medium — the *technique* is directly useful if we ever add a graph/PPR term to our retrieval score (per GAAMA/SPRIG in this same wave), but the *paper's own system* runs Neo4j for its graph store, so it does not itself answer Lane A's "without a dedicated graph DB" question. Flagged honestly rather than oversold.
- **Core contribution (2-3 sentences):** Dense-vector similarity scores and graph-based relevance scores (e.g., Personalized PageRank) live on incommensurable scales — cosine similarities cluster in a narrow Gaussian while PPR scores follow a power-law. PhaseGraph shows that calibrating both to a common unit-free scale via percentile-rank normalization (the probability integral transform, equivalent to each score's empirical CDF) *before* fusing them is the first-order fix; once calibrated, the exact fusion operator (their Boltzmann weighting vs. plain linear combination) matters much less.

### Mechanisms relevant to us

- Percentile-rank / PIT normalization (§3.2, Eq. 1): `p̂ᵢᵏ = |{j : sⱼᵏ ≤ sᵢᵏ}| / Nᵏ` — map each retriever's own score list to its empirical CDF, giving a [0,1] value that preserves within-system ranking while making cross-system magnitudes comparable. No training, no external calibration data, computed per-query from the candidate batch itself.
- Boltzmann-energy fusion as one optional operator on top of the calibrated scores (§3.3-3.4) — but the paper's own ablation says this is the *less* important half: "percentile-based calibration is directionally more robust than min-max normalization... the exact post-calibration operator appears to matter less" (Abstract).
- A named condition for *why* naive fusion fails at corpus scale: "pool explosion and entity fragmentation" (§Contributions, Section 7) — i.e., simply concatenating a large graph-reachable pool with a small vector pool without capping/calibration degrades results; pool capping + synonym/alias linking restores clean behavior (8W/0L, p=0.008).

### STRICTLY-BETTER candidates (beats a mechanism we already have)

*(none directly — we have no graph score today to fuse; this is a technique in reserve, not a drop-in improvement on our current relevance×recency×importance formula by itself)*

### NOT-YET-BUILT candidates (a capability we simply don't have)

- **Capability:** A calibrated way to combine a future graph/PPR relevance signal with our existing cosine-similarity relevance term, without one distribution swamping the other.
- **What the paper does:** Percentile-rank calibration before fusion — *evidence:* §3.2 Eq. 1; Table 1 shows the calibrated method (`PHASEGRAPH`) confirms significance where raw RRF does not (MuSiQue: PHASEGRAPH 8W/1L p=.039 vs RRF 15W/6L p=.078; 2Wiki: PHASEGRAPH 11W/2L p=.023 vs RRF 11W/5L p=.210).
- **Why worth adopting for an NPC memory service:** *If and only if* we build our own app-side graph/PPR term (per the SPRIG/GAAMA findings from this same wave), this is the cheapest available way to fold it into our existing multiplicative relevance×recency×importance_norm score without the graph term's heavy-tailed distribution dominating or being drowned out — no training data, no new model role, a pure per-query computation over the retrieved batch.
- **Adoption cost/risk in our stack:** Low computationally (a rank computation over the candidate list, same cost class as our existing over-fetch + re-rank step) — but genuinely **not yet relevant** until a graph term exists; adopting it now would be building calibration machinery for a signal we don't have. The honest caveat that must travel with this finding: **PhaseGraph's own system architecture uses PostgreSQL+pgvector for the vector store but Neo4j for the knowledge graph** (§4.2, "a knowledge graph (Neo4j with LLM-extracted entities)") — it is not evidence for a single-store, no-graph-DB design; it only demonstrates a store-agnostic *scoring* technique, useful regardless of where the PPR number comes from (Neo4j, or an app-side SPRIG/GAAMA-style computation over Postgres-stored edges). Effect sizes are also modest and only barely significant (+1.4pp and +1.9pp LASTHOP@5, both p just under .05 on n≈491 held-out queries) — a real but small lift, not transformative.
- **Docs it would touch:** Would only touch `read-path.md`/`architecture.md` §6 *if and when* a graph term is specced — otherwise it's a technique to hold in reserve, not a doc change today.
- **Confidence:** Medium (the technique is sound and cheap; its relevance to us is entirely conditional on a graph build happening first).

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)

*(none)* — pure scoring math; any weight introduced (mixing λ, consensus boost γ) would naturally be a config knob per invariant #5, not hardcoded.

### Quotable lines / citations for positioning (optional)

- "cosine similarities cluster in a narrow Gaussian (μ≈0.09, σ≈0.02), while PPR scores follow a power-law (most values <0.001, rare peaks >0.3)" (§1) — a crisp, quotable statement of exactly why naively adding a graph score into our existing formula would be unsafe without calibration, useful for framing a future graph-spec session's scoring section.

### Verdict

**P3, note-only for now / conditional P2 later** — this is not itself an answer to Lane A's "non-destructive, Postgres-native, no-graph-DB" question (its own system runs Neo4j), so it should not be read as corroborating evidence for that path. It is, however, the cheapest available fix for a real problem we would *hit* the moment we did add a graph term per GAAMA/SPRIG: file this alongside those two findings as "step 3, when you get to scoring fusion," not as a priority on its own.
