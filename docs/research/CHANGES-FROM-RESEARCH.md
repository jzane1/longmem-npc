# Changes from research — the paper trail

**Purpose.** When the README (and any research write-up) gets written, this file is the lookup:
every change that landed from the 2026-07-20 research sweep, and every queued item, mapped to the
papers it came from. *(Tracked since 2026-07-28 under `docs\research\`; it was gitignored with
the rest of `Research Papers\` until then, which is why the line below used to call it working
material. The source PDFs stay out of the tree.)* Settled history lives in `docs\decisions.md`;
current state in `docs\status.md`.

**Corpus:** 45 papers — 31 curated + 14 arXiv-discovered (`_discovered\`). Consolidated analysis:
[FINDINGS.md](FINDINGS.md). Per-paper detail with quotes + page refs: `_findings\<slug>.md`.

---

## LANDED 2026-07-21 — commit 80ea085 (Target A)

### Encoding-context read term v1
**What changed:** the read path's reserved request fields (`location_name`/`entities`/`event_time`)
are now consumed as client-supplied scene context — a soft multiplicative score nudge
(`score ×= 1 + Σ w_i·match_i`: fact-head entity coverage + `exp(−Δ/scale)` event-time kernel +
casefold location match; ≥ 1 always, never a filter/penalty; byte-identical v1 scoring when absent).
Files: `app\retrieval.py` (`context_boost`, `_QueryContext`), `app\db.py` (CandidateRow widened),
`app\config.py` (4 knobs), `app\schemas.py`/`app\dialogue.py`/`app\session.py`/`app\cli.py`
(passthrough + `:context` + debug). No migration.

| Paper | arXiv | Findings file | What it contributed |
|---|---|---|---|
| **RaMem: Contextual Reinstatement for Long-term Agentic Memory** | 2606.22844 | `_findings\ramem-contextual-reinstatement.md` | The mechanism: "context collapse" failure mode; episodic anchoring; soft-priority compatibility filtering with selective activation + content fallback (+10 F1; halves wrong-episode-ranked-first). We adopted the *client-supplied-fields* variant (their LLM query decomposition was ruled out — the 2026-07-14 query-as-is ruling stands). |
| Position: Episodic Memory is the Missing Piece | 2502.06975 | `_findings\episodic-missing-piece.md` | Priority justification: "contextual relations" is a *defining* episodic-memory property, not a nice-to-have — it's what elevated the reserved slot to a build target. |
| MemConflict | 2605.20926 | `_findings\memconflict.md` | Forward pointer: conditional/context-bound validity is the natural next occupant of the same slot (queued, not built). |

### TARG gate-calibration utility (`--gate-budget`)
**What changed:** `python -m app.load_driver --gate-budget <rate>` reports the
`gate_novelty_threshold` at the (1−rate) quantile of a run's novelty min-distance CDF — a
designer-legible "fire on ~N% of turns" target. Report-only; never sets the knob.

| Paper | arXiv | Findings file | What it contributed |
|---|---|---|---|
| **TARG: Training-Free Adaptive Gating** | 2511.09803 | `_findings\targ-adaptive-retrieval-gating.md` | §3.4's budget-calibration recipe (empirical-CDF threshold selection). TARG's *gate mechanism* (LLM draft-logit uncertainty) was NOT adopted — it conflicts with the non-LLM-gate invariant; its finding that model-confidence signals degrade on instruction-tuned models is ammunition *for* our structural gate. |

## LANDED 2026-07-21 — commit edf9820 (Target B)

### Hybrid lexical retrieval channel v1 (migration 004)
**What changed:** `db\migrations\004_lexical_index.sql` — partial FTS GIN over live fact heads
(`to_tsvector('simple', basis_text) WHERE invalid_at IS NULL`); a token-OR lexical candidate
fetch (`lexical_tsquery` — the build-surfaced correction over AND-semantics
websearch/plainto, which would have made the channel inert for utterances) unioned into the
loader's vector over-fetch before scoring — dedup exact, scoring formula untouched, lexical hits
carry true cosine relevance, NULL-embedding rows lexically reachable (relevance null).
`lexical_fetch_k` (0 = kill-switch) + `text_search_config` knobs.

| Paper | arXiv | Findings file | What it contributed |
|---|---|---|---|
| **Memory in the LLM Era (survey)** | 2604.01707 | `_findings\survey-llm-era.md` | §7: the lexical/semantic complementarity case — lexical is best for names/entities/exact phrases (NPC dialogue's bread and butter); the only strictly-better retrieval candidate the survey corpus produced. |
| **Less Context, More Accuracy (Engram)** | 2606.09900 | `_findings\less-context-more-accuracy.md` | Dense+BM25(+graph) fusion evidence: lean hybrid retrieval beats full-context +10.4pts at 8× fewer tokens; also validates our gate/retrieval-k/thinning philosophy wholesale. |
| SPRIG | 2602.23372 | `_findings\sprig-democratizing-graphrag.md` | Sequencing rationale: the lexical/dense hybrid base is the *seeding prerequisite* for any future graph term (graph-only underperforms dense; hybrid seeding is where gains appear). |

---

## QUEUED (immediate queue 3–7, slated 2026-07-21 — each its own spec/build session)

### 3. Judged eval harness v1 (ruled: judged categories + judge model role from v1)
| Paper | arXiv | Findings file | Contribution |
|---|---|---|---|
| MemoryAgentBench | 2507.05257 | `_findings\incremental-multi-turn.md` | FactConsolidation selective-forgetting construction (single/multi-hop; all systems ≤28% multi-hop — the field-validated gap our correction stack targets) |
| LongMemEval | 2410.10813 | `_findings\longmemeval.md` | 5-ability taxonomy; knowledge-update + abstention categories; 4-tuple + LLM-judge @97% human agreement |
| LongMemEval-V2 | 2605.12493 | `_findings\longmemeval-v2.md` | Insert/Query harness shape; premise-awareness rubric (penalize false-premise-following AND generic non-answers); accuracy-vs-latency Pareto |
| LoCoMo | 2402.17753 | `_findings\very-long-term-conv-memory.md` | FactScore atomic-fact decomposition, **retargeted**: gist-precision ~100%, detail-recall allowed to decay; adversarial wrong-speaker category |
| Memora/FAMA | 2604.20006 | `_findings\memora-forgetting-aware-benchmark.md` | Presence + absence criteria (stale content must NOT appear) — cheap for us, validity is already server-tracked |
| MemTrace | 2606.17328 | `_findings\memtrace-knowledge-point-probing.md` | Trajectory probe ("how did this fact change over time" — our version chain is uniquely suited); reach-vs-use failure attribution; abstention/conflict as separate axes |
| MemSyco-Bench | 2607.01071 | `_findings\memsyco-bench-sycophancy.md` | Memory-*use* correctness (61–62% of errors are post-retrieval misuse); VALID-MEMORY-SELECTION maps to "retrieval follows the fix" end-to-end |
| Fixed-Persona SLMs | 2511.10277 | `_findings\fixed-persona-slm.md` | The judge-free keyword-retention check — fits the structural discipline today, ahead of any judge |
| MemGPT | 2310.08560 | `_findings\memgpt.md` | DMR judge-prompt pattern |
| Beyond a Million Tokens | 2510.27246 | `_findings\beyond-million-tokens.md` | Nugget-based scoring; corroboration that contradiction-resolution is near-floor industry-wide |
| Confabulation (ACL 2024) | — | `_findings\confabulation.md` | Narrativity + coherence metrics as the reconstruction-quality axis beside the drift budget |
| Unfaithful CoT (Turpin) | 2305.04388 | `_findings\unfaithful-cot.md` | The counterfactual-simulatability protocol for the research track's asymmetry ablation (gated on the split-brain build) |

### 4. Graph/associative memory (de-risked by the second-wave scout)
| Paper | arXiv | Findings file | Contribution |
|---|---|---|---|
| **GAAMA** | 2603.27910 | `_findings\gaama-graph-associative-memory.md` | The schema: 4-node/5-edge typed graph where 3 node types are tables we have; **concept-mediation via `identity_components`** dodges entity mega-hubs (400–500+ edges/entity vs ~30× sparser); graph term = small additive nudge (0.1 ablation); GRAFT insertion-only repair |
| **SPRIG** | 2602.23372 | `_findings\sprig-democratizing-graphrag.md` | Proof of no-graph-DB mechanism: PPR = app-side sparse linear algebra, CPU-only, zero LLM; honest tempering — hybrid seeding required |
| HippoRAG | 2405.14831 | `_findings\hipporag.md` | KG+PPR evidence (+20pt R@5 multi-hop); node-specificity IDF (the cheap first step on the entity tripwire); additive non-destructive growth |
| HippoRAG-2 | 2502.14802 | `_findings\rag-to-memory.md` | How to add graph retrieval *without* regressing factual recall (dense-sparse integration + recognition filter) |
| PhaseGraph | 2603.28886 | `_findings\phasegraph-calibrated-fusion.md` | Percentile-rank score calibration for fusing a graph term (fusion-math half only — its own system is Neo4j) |
| A-MEM | 2502.12110 | `_findings\a-mem.md` | Link-generation-only slice ablation (recovers most of the multi-hop gain without destructive "evolution") |
| AdaMem | 2603.16496 | `_findings\adamem-adaptive-user-memory.md` | Typed-edge graph = largest single ablation effect; deterministic cue-detection routing (the LLM-refiner half stays out of the gate) |
| SEEM | 2601.06411 | `_findings\structured-episodic-event-memory.md` | Reverse Provenance Expansion (cross-observation linking); its fusion-corruption admission is README counter-example material |
| MRAgent | 2606.06036 | `_findings\memory-reconstructed-graph.md` | Cue/tag lightweight index idea; the full LLM-traversal loop stays out (latency philosophy); title-collision caveat for citations |
| Mem0/Mem0g | 2504.19413 | `_findings\mem0.md` | Graph value concentrates on temporal reasoning; soft-invalidated edges validate bi-temporal edge design |

### 5. Recall-reinforced decay
| Paper | arXiv | Findings file | Contribution |
|---|---|---|---|
| MemoryBank | 2305.10250 | `_findings\memorybank.md` | The Ebbinghaus recall-reinforcement mechanism (`R=e^{−t/S}`, S++ on recall) — the missing usage axis in `tau_effective` |
| Memory in the Age of AI Agents (survey) | 2512.13564 | `_findings\survey-ai-agents.md` | Frequency-based forgetting as an orthogonal axis (LRU/LFU/counting-Bloom exemplars) |

### 6. Automatic conflict/staleness detection
| Paper | arXiv | Findings file | Contribution |
|---|---|---|---|
| STALE | 2605.06527 | `_findings\stale.md` | Implicit-conflict taxonomy (Type I co-referential / Type II propagated); CUPMEM write-time adjudication riding an `identity_components`-shaped index; SR/PR/IPA eval; the "current-state adjudication gap" our live-head design already closes once corrected |
| Nous | 2606.22030 | `_findings\nous-belief-based-memory.md` | Trust must be provenance-capped, never content-inferred (maps to `typology`/`typology_source`); arbitration only pays off under genuine reliability variance (the diegetic regime) |
| MemConflict | 2605.20926 | `_findings\memconflict.md` | Dynamic/static/conditional taxonomy; SOTA <25% conflict recognition = differentiator headroom |
| Mem0 | 2504.19413 | `_findings\mem0.md` | Write-time ADD/UPDATE/DELETE detection shape (DELETE branch redesigned around supersession) |
| survey-ai-agents | 2512.13564 | `_findings\survey-ai-agents.md` | Zep's auto soft-invalidation as the field's mature endpoint (= our supersede pattern, auto-triggered) |

### 7. Smaller queued notes
| Item | Paper(s) | Findings file(s) |
|---|---|---|
| Reflection dossier: ground writes in cited memory_ids + RRR repetition detector | Honest Lying 2605.29463 | `_findings\honest-lying-confabulation.md` |
| Reflection dossier: periodic evidence-conditioned identity refresh (+0.87 fidelity ablation) | AI YOU Town 2607.10539 | `_findings\ai-you-town-digital-twin.md` |
| Reflection dossier: persona-lensed retrieval routing; interview-depth `seed_identity` (0.83 vs 0.71) | Self-Reports (Park et al.) | `_findings\self-reports-simulation.md` |
| Reflection dossier: idle-time (sleep-time) scheduling (~5× cheaper at equal accuracy) | Sleep-time Compute 2504.13171 | `_findings\sleep-time-compute.md` |
| Unity API: Whisper soft-steering hook + safe-default action fallback | Bounded Autonomy 2604.04703 | `_findings\bounded-autonomy.md` |
| MemTree online hierarchical consolidation (version nodes, never overwrite) | MemTree 2410.14052 | `_findings\dynamic-tree-memory.md` |
| Cross-NPC shared world-fact layer (likely out of scope; believability evidence) | GenAI NPCs in VR (DOI 10.1080/10447318.2026.2620647) | `_findings\genai-npc-vr.md` |

---

## README / write-up citation bank (no code change — positioning)

- **Lead thesis support:** Confabulation ACL 2024 (`_findings\confabulation.md`) — "hallucinations
  make them more like us than we would like to admit"; our drift-budget/gist/immutable-record is
  the governance layer it lacks. Turpin 2305.04388 — "LLMs do not always say what they think"
  (1/426 explanations mention the bias). False-memories RCT 2408.04681 (Loftus) — LLM sycophancy
  induced 3× durable false memories; Bartlett lineage + the diegetic-path sycophancy caution.
  survey-ai-agents §7.8 — names "generative reconstruction" as the frontier our thesis claims.
- **Non-destructive-storage validation (measured costs of the alternative):** HippoRAG-2 Table 2
  (summarization memories collapse to F1 1.6–11.6); survey-llm-era Exp.4 + Lesson L5 (our
  invariant verbatim); SEEM's own "can permanently corrupt the structured memory store" —
  the README destructive-compression counter-example candidates (with MemoryBank's hierarchical
  summary and MemGPT's `working_context.replace()`).
- **Demo-legibility caution:** GenAI-NPCs-in-VR — players read accidental hallucination as
  character dishonesty; make the debug/ground-truth view demo-legible so designed drift never
  reads as the accidental failure mode.
- **Gate positioning:** TARG's own finding (model-confidence signals degrade on instruction-tuned
  models) defends the non-LLM structural gate.

## What was deliberately NOT adopted (with the reason)
- LLM query decomposition (RaMem's own front-end) — ruled out; client fields instead.
- TARG's LLM-draft gate signal; AdaMem's LLM route refiner; fast-slow retrieval timing — the
  non-LLM-gate invariant.
- MRAgent's multi-turn LLM traversal — single-embed low-latency retrieval philosophy.
- A-MEM's memory "evolution", MemTree's node overwrite, Mem0's DELETE branch, SEEM's fusion
  mutation, Personalized-NPC's node pruning, LIGHT's scratchpad compression — destructive;
  invariant #1. Adoptable spirits noted per-item under queue entries.
- Parametric consolidation / per-NPC fine-tuning (Episodic-position §5, MemOS, Fixed-Persona,
  Personalized-NPC) — the never-fine-tune API-model stack; a scope boundary for the limitations
  section.
- Outcome-linked dynamic importance (Memory-Worth 2604.12007) — fragile under policy-coupled
  retrieval (its own experiments); at most an advisory reflection-time signal later.
