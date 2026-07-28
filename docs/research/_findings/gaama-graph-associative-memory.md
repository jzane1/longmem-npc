# GAAMA: Graph Augmented Associative Memory for Agents

- **Authors / venue / year:** Swarna Kamal Paul, Shubhendu Sharma, Nitin Sareen (Nagarro) — preprint, 2026.
- **arXiv / DOI:** 2603.27910v2
- **Source:** discovered (second-wave sweep, Lane A)
- **Overall relevance to longmem-npc:** High — the single most schema-specific answer found to our own baseline's named gap ("No graph / associative structure over memories... No multi-hop retrieval"), and it gives a concrete node/edge typology that maps almost node-for-node onto tables we already have.
- **Core contribution (2-3 sentences):** GAAMA builds a typed knowledge graph over conversational memory with four node types (episode/fact/reflection/concept) and five structural edge types, explicitly using topic-level **concept** nodes instead of entity nodes to avoid the "mega-hub" problem that dilutes PPR-based retrieval in entity-centric graphs (HippoRAG-style) — person entities in their data accumulated 400-500+ edges each; concept-mediated graphs come out ~30x sparser. Retrieval is a low-LLM-cost additive fusion of cosine similarity + edge-type-aware Personalized PageRank (PPR), plus GRAFT, a post-retrieval repair layer that inserts (never deletes) missing facts/concept-links when a sufficiency judge flags a retrieval gap.

### Mechanisms relevant to us

- Four-node / five-edge typed graph schema (§3.2, Table 1): `episode --NEXT--> episode`, `fact --DERIVED_FROM--> episode`, `reflection --DERIVED_FROM_FACT--> fact`, `episode --HAS_CONCEPT--> concept`, `fact --ABOUT_CONCEPT--> concept`.
- Concept nodes (not entities) as the traversal substrate, specifically because entity-centric graphs mega-hub in conversational data (§1, §5.4).
- Edge-type-aware PPR with per-type base weights, hub dampening, and a **deliberately small** graph-score weight in an additive fusion score (§3.3, Eq. 5) — ablation-proven: PPR weight 1.0 performed *worse* than pure semantic search on the same graph (§5.4).
- GRAFT: a post-retrieval, insertion-only graph-repair layer (§3.5) — six phases ending in "surviving edits are inserted with near-duplicate rejection... GRAFT-created facts receive a lower belief weight."
- "Verbatim episode preservation... no LLM... no summarization or modification" as node-construction step 1 (§3.1) — stated as "critical to ensure no loss of information."

### STRICTLY-BETTER candidates (beats a mechanism we already have)

*(none — GAAMA is a not-yet-built capability, not a replacement for anything we currently do)*

### NOT-YET-BUILT candidates (a capability we simply don't have)

- **Capability:** Associative/graph-structured multi-hop retrieval over memory (our baseline's own named gap: "No graph / associative structure over memories... No multi-hop retrieval").
- **What the paper does:** A concept-mediated typed graph (episode/fact/reflection/concept nodes; NEXT/DERIVED_FROM/DERIVED_FROM_FACT/HAS_CONCEPT/ABOUT_CONCEPT edges) with edge-type-aware PPR fused additively (weight 0.1) with cosine similarity — *evidence:* §3.2 Table 1, §3.3 Eq. 5 (`score(n) = b(n)·w_ppr·ppr(n) + w_sim·sim(n,q)`, w_ppr=0.1, w_sim=1.0); "the low PPR weight ensures graph structure augments semantic relevance rather than overriding it." Results: +4.2pp mean reward over the strongest RAG baseline on LoCoMo-10 (79.1% vs 74.9%), with the *pure graph contribution* (PPR=0.1 vs the same graph's semantic-only baseline) isolated at +1.2pp overall, concentrated on temporal (+4.0pp) and largely neutral-to-slightly-negative on multi-hop (-1.6pp, attributed to LLM-generation variance on counting questions, not retrieval failure — §5.3).
- **Why worth adopting for an NPC memory service — the concrete schema match:** Our existing tables already occupy three of GAAMA's four node types almost exactly: `memories` ≈ episode (their "verbatim, no LLM, no summarization" step is *literally* our `observation_text` immutability invariant), `memory_fact_versions` ≈ fact (their `DERIVED_FROM` fact→episode provenance edge is already implicit in our schema via the fact chain's origin), and our (unbuilt) `reflections` table ≈ reflection. Most importantly: **`identity_components` is already a concept-style node, not an entity-style node** — it's canonical+aliases+category, distinct from the raw `entities` text[] column. GAAMA's central empirical finding (entity nodes mega-hub; concept nodes stay ~30x sparser) is direct evidence that our schema, if we build the graph against `identity_components` rather than raw `entities[]`, is *already positioned to avoid* the exact failure mode that HippoRAG/HippoRAG-2/Mem0g/AdaMem/Personalized-NPC all hit (per our own corpus's Table 2 #2) — sharper and more actionable than that entry's generic "reuse identity_components + entities[]" phrasing.
- **Adoption cost/risk in our stack:** Lower than our existing Table 2 #2 estimate suggests, because most of the "node" surface already exists. The real new surface is edges: `HAS_CONCEPT`/`ABOUT_CONCEPT` (memory ↔ identity_components — largely already implicit in gist-span matching / the entity-gate tripwire hits, migration-003 entities), `NEXT` (computable from `event_time`/`created_at` ordering without a stored edge at all), `DERIVED_FROM_FACT` (moot until reflection is built). A genuinely new migration is only needed for an edge table (bi-temporal rows, non-destructive by construction — new edges only ever get added, old ones stamped `invalid_at` on supersession, never deleted/mutated) plus app-side PPR (sparse adjacency fetched via hand-written SQL, power-iterated in Python — no ORM, no graph DB, "no LLM calls at query time" per §1 contribution 2). GRAFT's insertion-only repair (near-duplicate rejection via cosine >0.90, no deletion) is compatible with our non-destructive invariant as designed. One real gap GAAMA does *not* solve: it has no notion of edge supersession/invalidation — a memory that gets authorial-corrected would need its `HAS_CONCEPT`/`ABOUT_CONCEPT` edges re-derived, an extension we'd have to design (their own open item, "Memory consolidation and contradiction resolution," is explicitly future work, §6).
- **Docs it would touch:** `architecture.md` §4.4/§6 (the graph gap), `read-path.md`, `mid-dialogue-gate.md` (entity tripwire could reuse the same concept-edge structure), a new spec + migration session.
- **Confidence:** High.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)

*(none)* — GAAMA's own design choices (verbatim episode preservation, insertion-only repair, no destructive graph mutation) are compatible with, not in tension with, invariant #1. Its unsolved "contradiction resolution" gap is the same gap already logged in our own Table 2 #3, not a new tension.

### Quotable lines / citations for positioning (optional)

- "recurring person entities accumulate hundreds of edges, creating mega-hubs that dilute PPR precision" (§2.1) — good citation for *why* concept/component-mediated graphs beat entity-centric ones, if the graph work ever gets written up.
- "The low PPR weight ensures graph structure augments semantic relevance rather than overriding it — a principle validated by our ablation analysis" (§3.3) — useful precedent for treating any future graph term as a small additive nudge on our existing relevance×recency×importance score, not a replacement.

### Verdict

**P2, worth-piloting**, and the strongest single schema-level answer this second wave found to the graph gap: it gives a node/edge typology where three of four node types are tables we already have, names the exact mechanism (concept-mediation) that avoids the specific failure our own corpus flagged as most-corroborated, and its repair layer (GRAFT) is insertion-only by construction. The remaining design work is genuinely new (an edge table + app-side PPR + edge invalidation on correction) and still merits its own spec session, but the cost is smaller than previously scoped.
