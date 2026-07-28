# longmem-npc — literature sweep: consolidated findings

**Date:** 2026-07-20 · **Corpus:** 31 curated PDFs (`Research Papers\`) + 14 discovered via arXiv
(`Research Papers\_discovered\`) = 45 papers (10 first-wave + a 4-paper second wave de-risking the
graph-memory recommendation). Per-paper detail: `Research Papers\_findings\<slug>.md`.
Yardstick: `Research Papers\_baseline\current-architecture.md`.

**Scope of this doc.** Search-and-report only. Nothing in `docs\`, `app\`, `db\`, `tests\` was
touched. Every claim below is traceable to a per-paper findings file (which carries the section/page
refs + quotes). Adoption is Jack's call, in a later session. Per the ruling, findings are split into
**invariant-compatible improvements** (Tables 1–2) and **thesis-tensions** (§4), kept separate.

**How to read the priority tags.** P1 = adopt-soon, high value, low invariant risk. P2 =
worth-piloting / its own spec session. P3 = note-only / future / positioning.

---

## 0. The headline

Two things dominate the corpus, and both are things longmem-npc's *own baseline already names as a
gap*:

1. **There is no judged evaluation harness, and almost every paper points at one.** 15+ papers supply
   ready-made task taxonomies, construction methods, and metrics. This is the single highest-value,
   lowest-invariant-risk move available — it turns the project's distinctive claims (retrieval follows
   the fix; controlled infidelity; decay) from *structurally asserted* into *measured*. **This is
   the #1 recommendation.**
2. **There is no associative/graph structure or multi-hop retrieval, and it is the single
   most-corroborated capability gap** — hit independently, with ablation evidence, by HippoRAG,
   HippoRAG-2, A-MEM, Mem0g, MRAgent, AdaMem, SEEM, Personalized-NPC, and both surveys. It is a real
   build (migration + subsystem), and several papers implement it *destructively* — so the lesson is
   "adopt the capability, keep edges bi-temporal." **The second-wave scout de-risked this materially**
   (GAAMA + SPRIG): it's buildable natively on Postgres/pgvector with no graph DB, and our
   `identity_components` table is already the *concept-mediated* node type that dodges the entity
   mega-hub failure the other papers hit — see Appendix A #4.

Beyond those two, the strongest single *strictly-better* mechanism is **RaMem's encoding-context
re-ranking**, because it fills a slot our read path already reserved, using columns we already store,
with no migration.

The corpus is also strongly **thesis-affirming**: Confabulation (ACL 2024), Turpin/unfaithful-CoT,
the false-memories RCT, and both surveys independently validate "controlled infidelity above an
immutable record," and multiple papers *measure the cost* of the destructive designs our
non-destructive invariant rules out (HippoRAG-2 Table 2; survey-llm-era Exp.4; SEEM's own Limitations).

---

## 1. Prioritized shortlist (start here)

| # | Recommendation | Type | Priority | Why now |
|---|---|---|---|---|
| 1 | **Judged eval harness** (separate from the structural suite) — seed with selective-forgetting, abstention/premise, reconstruction-FactScore, stale-leakage (FAMA) — **QUEUED 2026-07-21** (immediate queue #3; ruled: judged categories from v1) | not-yet-built | **P1** | Biggest named gap; 15+ papers converge; low invariant risk; makes the thesis measurable |
| 2 | **Encoding-context re-ranking (RaMem)** — temporal/participant compatibility as a soft prior over the reserved `event_time`/`entities`/`location` slots — **LANDED 2026-07-21** (commit 80ea085, floor-verified; client-supplied fields ruled) | strictly-better | **P1** | Fills a slot already reserved; columns already stored; no migration; +10 F1 evidence |
| 3 | **Hybrid lexical+vector retrieval** — Postgres `tsvector`/GIN alongside HNSW — **LANDED 2026-07-21** (commit edf9820, migration 004, floor-verified; token-OR shape) | strictly-better | **P2** | Cheap, additive, Postgres-native; helps proper-name recall (NPC dialogue is full of them) |
| 4 | **Associative/graph memory + multi-hop** — non-destructive edge table; start lightweight — **QUEUED 2026-07-21** (immediate queue #4, with the GAAMA/SPRIG de-risked notes) | not-yet-built | **P2** | Most-corroborated gap; ablation-backed; but own spec + migration |
| 5 | **Recall/frequency-reinforced decay** — a usage term next to age+importance in `tau_effective` — **QUEUED 2026-07-21** (immediate queue #5; own spec session ruled) | augmentation | **P2** | On-thesis ("a well-worn story resists decay"); migration + careful invariant-2 handling |
| 6 | **Automatic conflict/staleness detection at write time** — the write-time counterpart of the dissonance path — **QUEUED 2026-07-21** (immediate queue #6) | not-yet-built | **P2** | On-thesis; hard (industry-wide unsolved → a differentiator); reuses entities GIN + fact-head embedding + typology/provenance |
| 7 | **Richer `seed_identity` grounding** — author it like a structured interview, not a short bio — **QUEUED 2026-07-21** (immediate queue #7 notes) | strictly-better | **P2** | Cheap now, no schema change; grounding depth beats model choice (self-reports) |
| 8 | **Gate threshold budget-calibration (TARG recipe)** — set `gate_novelty_threshold` from a target fetch-rate — **LANDED 2026-07-21** (commit 80ea085, `--gate-budget`, report-only) | tuning | **P2** | Cheap; more legible knob for a game designer; no invariant touched |
| 9 | **Reflection design dossier** — bank the reflection-specific findings for the sequenced-later spec — **QUEUED 2026-07-21** (immediate queue #7 notes) | future-input | **P2** | When reflection is specced, four papers give concrete, ablation-backed design + a named failure mode to avoid |
| 10 | **Positioning/citation bank** (§5) + **demo-legibility mitigation** — **banked in `CHANGES-FROM-RESEARCH.md`** for the README session | writing/demo | **P1/P2** | Confabulation + Turpin + false-memories ground the thesis; make the debug view demo-legible so designed drift ≠ accidental hallucination |

---

## 2. Table 1 — STRICTLY-BETTER (beats a mechanism we already have)

| Component | Our current mechanism | Proposed (paper) | Evidence | Cost/risk in our stack | Docs |
|---|---|---|---|---|---|
| Read path / retrieval scoring | `query_text` embedded as-is; `location`/`entities`/`event_time` accepted-but-**reserved**, never consumed | **Session-overlap temporal + participant compatibility as a soft prior** over distance-retrieved candidates, activated only when grounded, content fallback retained (RaMem) | `ramem` §3.3 Eq.4; +10 F1 avg over strongest structured baseline; "context shuffle" ablation confirms it's binding, not metadata volume; cuts wrong-episode-ranked-first from ~44-54% by half | Low-mod: columns already exist; a scoring-function term (config-weighted, per invariant #5); **no migration**; non-destructive; matches fail-quiet (soft prior, not hard filter) | `read-path.md`, `architecture.md` §6 |
| Read path / candidate query | Pure vector (cosine over live fact-head HNSW); server-side query composition deliberately rejected | **Hybrid lexical (BM25/`tsvector`) + vector**, fused | `survey-llm-era` §7 (lexical best for names/entities/exact phrases); `less-context` §3.5 (dense+BM25+graph+recency via RRF; lean beats full-context +10.4pts) | Low: Postgres native FTS + GIN alongside HNSW, hand-written SQL, no new dep; new fusion-weight knob + a FTS-index migration | `read-path.md`, `architecture.md` §6 |
| Decay (`app\decay.py`) | `tau_effective = tau_base·(1+k·importance_raw)` — age + write-time importance only | **Recall/frequency-reinforced decay** — recall increments a strength counter, resetting the clock (Ebbinghaus); a usage axis orthogonal to time | `memorybank` §2.3 (`R=e^{-t/S}`, S++ on recall); `survey-ai-agents` §5.2.3 (frequency-based forgetting as orthogonal axis: LRU/LFU/counting-Bloom) | Mod: new counter+timestamp column (migration); must enter as a decay *input*, never a new invalidation trigger (invariant #2); define "recall" precisely so a same-scene read doesn't break within-scene byte-identity | `read-path.md`/decay §, `architecture.md` §6, `test-suite.md` Set B |
| Identity (`agents.seed_identity` / `identity_documents`) | Hand-authored **short prose bio**, static until reflection | **Ground identity in a much richer structured self-report** (interview-depth), not a persona paragraph | `self-reports-simulation`: interview-grounded 0.83 vs persona-paragraph 0.71 (p<.001); survives removing 80% of the transcript (0.82→0.79) — depth beats model choice | Low: no schema change; cost is authorial effort + token budget per NPC | `architecture.md` §4.3, future reflection spec |
| Correction / dissonance (auto side) | Supersession is **only** operator-triggered (authorial) or diegetic-with-explicit-`memory_id` (unbuilt) | **Auto-triggered soft invalidation** when a new fact contradicts a live head (Zep pattern) | `survey-ai-agents` §5.2.2 ("shift from hard replacement to soft, time-aware updating"); `less-context` §3.4 cheap-then-escalate | (See §3 not-yet-built #6 — this is really a new capability; listed here because it's *strictly better than our operator-only supersede*, same non-destructive machinery) | `fact-level-correction.md`, `mid-dialogue-gate.md`, future `dissonance.md` |

> Note: **MRAgent** (active LLM graph-traversal retrieval) shows a genuine strictly-better read-path
> result (+23–32% on LoCoMo/LongMemEval) but at a multi-turn LLM-per-read cost that's in tension with
> our single-embed, low-latency retrieval philosophy — it lives under §3 #4 (graph) and §4 #3
> (tension), not as a recommended drop-in.

---

## 3. Table 2 — NOT-YET-BUILT (a capability we don't have)

### #1 — Judged evaluation harness  · **P1**  · (the biggest named gap)
- **What:** A judged accuracy/recall/behavior harness, *separate* from the structural pytest suite,
  driving scripted event streams through observe → retrieve → dialogue and scoring the output.
- **Ready-made pieces from the corpus (pick a starter set):**
  - **Selective forgetting / knowledge-update** — assert a fact, later contradict it, grade whether
    the answer reflects current truth; single- **and multi-hop** variants. Tests fact-level +
    authorial correction ("retrieval follows the fix" — today proven only structurally, in small
    fixtures). `memoryagentbench` (FactConsolidation; *all* systems ≤28% on multi-hop),
    `longmemeval` (knowledge-update category), `stale` (SR/PR/IPA).
  - **Abstention / premise-awareness** — false-premise queries; correct behavior is to decline / name
    the flaw, not confabulate a never-observed fact. This is the sharpest test of whether "controlled
    infidelity" stays *controlled*. `longmemeval` (30 ABS questions), `longmemeval-v2` (premise-aware
    rubric: penalize both false-premise-following AND generic non-answers), `locomo` (adversarial /
    wrong-speaker misattribution).
  - **Reconstruction fidelity (FactScore, retargeted)** — atomic-fact precision/recall of a
    *retelling* vs ground truth, **retargeted** so gist-precision stays ~100% while non-gist
    detail-recall is *allowed to decay* (the point of reconstruction). `locomo` §4.2; pair with
    Confabulation's narrativity+coherence metrics (`confabulation`) as a quality axis beside the
    cosine drift-budget.
  - **Stale-memory non-leakage (FAMA)** — score presence-of-valid AND absence-of-invalidated; cheap
    for us because we already track validity server-side (unlike the paper, which had to reconstruct
    traces). `memora-forgetting-aware-benchmark`.
  - **Memory *use* correctness (sycophancy)** — VALID-MEMORY-SELECTION / MEMORY-EVIDENCE-CONFLICT;
    61–62% of memory-system errors are *post-retrieval misuse*, untested by retrieval-only checks.
    `memsyco-bench`.
  - **Judged persona-drift (Answer Leakage)** — does a retold memory leak facts the character
    shouldn't yet know (not-yet-`valid_at`, superseded, beyond decay/gate)? `memory-driven-roleplay`
    (MREval MB-AL).
  - **Cheap judge-free retention check** — deterministic keyword/entity-presence on the dialogue
    turn's prose (does the generated text actually surface a fact it retrieved). Fits the existing
    **structural-only** discipline; needs no judge. `fixed-persona-slm`.
- **Method scaffolding:** 4-tuple + LLM-judge @97% human agreement (`longmemeval`); Insert/Query
  harness shape + accuracy-vs-latency Pareto (`longmemeval-v2`); nugget-based scoring
  (`beyond-million-tokens`); DMR judge-prompt pattern (`memgpt`); neutral-harness discipline —
  always include a full-context baseline, use the official judge (`less-context`); watch the ~27pt
  token-F1-vs-LLM-judge gap (`nous`); **a "trajectory" probe** ("how did this fact change over time")
  our version-chain is unusually suited to answer, a **reach-vs-use replay** that attributes a failure
  to gate/retrieval vs the dialogue call, and **abstention-vs-conflict as two separate axes**
  (`memtrace-knowledge-point-probing`).
- **Cost/risk:** New eval surface, not schema; a judge model role (its own env var). Judged eval sits
  *beside* the Stop-hook structural suite, not inside it.
- **Docs:** new `docs\eval-harness.md`; `status.md` research track. **Confidence: High.**

### #2 — Associative / graph memory + multi-hop retrieval  · **P2**  · (most-corroborated gap)
- **What:** Edges between entities/memories + a traversal/expansion retrieval path, so a query can
  reach a memory it doesn't directly match because it's *linked* to one it does ("the innkeeper's
  brother"). Named in our own baseline as a gap.
- **Evidence (convergent, ablation-backed):** `hipporag` (KG + Personalized PageRank; +20pt R@5 on
  2WikiMultiHop; **additive/non-destructive** — new docs just add edges; node-specificity IDF weight
  is cheap and could sharpen the gate tripwire alone); `rag-to-memory`/HippoRAG-2 (how to add graph
  retrieval *without* regressing plain factual recall — dense-sparse integration + recognition-memory
  filter); `a-mem` (link-generation alone recovers most of a 27→9 multi-hop F1 gap — the cleanly
  separable slice); `adamem` (typed-edge graph is the *largest* single ablation effect, 44.65→42.63);
  `memory-reconstructed-graph`/MRAgent (Cue-Tag-Content graph; a **lightweight cue/tag index reusing
  `identity_components` + `entities[]`** is the cheap partial adoption); `structured-episodic-event-memory`
  (Reverse Provenance Expansion — link scattered passages of one event); `mem0` (Mem0g graph mainly
  helps *temporal* reasoning).
- **Cost/risk:** New migration (edge table over `memories`/`memory_fact_versions` PKs), app-side
  traversal (recursive CTE or in-process graph; "no ORM" governs the relational layer, not an
  in-process graph), likely a write-time extraction/link model role. **Must be non-destructive** —
  several implementations delete/mutate (see §4 #1); edges must be bi-temporal rows.
- **Sequencing:** Big enough for its own spec session. Cheapest first step: node-specificity IDF on the
  existing entity tripwire, or a provenance/cue-tag index, before full PPR/traversal.
- **Docs:** `architecture.md` §4.4/§6, `read-path.md`, `mid-dialogue-gate.md`, new spec + migration.
  **Confidence: High (gap) / Medium (our-stack cost).**

### #3 — Automatic conflict / staleness detection at write time  · **P2**  · (on-thesis)
- **What:** Notice, without an operator or explicit `memory_id`, that a new observation contradicts or
  silently invalidates an existing belief — the write-time counterpart of the designed-but-unbuilt
  dissonance path. Includes STALE's **Type II "propagated"** case (a leg injury silently invalidates a
  "bikes to work" memory).
- **Evidence:** `stale` (implicit-conflict taxonomy; CUPMEM write-time KEEP/STALE/REPLACE adjudication
  + dependency propagation lifts 8.7%→68%; **CUPMEM's state slots resemble our `identity_components`**,
  lowering cost from "new subsystem" to "new consumer of an existing table"); `memconflict` (even SOTA
  recognizes an explicit contradiction <25% of the time; three-way dynamic/static/conditional
  taxonomy); `survey-ai-agents` (Zep auto-soft-invalidation); `mem0` (write-time ADD/UPDATE/DELETE —
  but DELETE is destructive); `beyond-million-tokens` (corroborates: contradiction resolution is
  near-floor industry-wide → a real differentiator opportunity); `nous` (crucial design principle:
  reliability must be **provenance-capped, not content-inferred** — maps to our `typology`/
  `typology_source`; and arbitration only pays off when genuine reliability variance exists, i.e. the
  diegetic/dissonance regime, not authorial).
- **Cost/risk:** High (genuinely unsolved), but reuses migration-003 entities GIN + fact-head
  embedding for candidate-conflict detection, and `typology`/`provenance` for trust. Non-destructive
  (still supersede via `invalid_at`). Needs its own ruling: heuristic vs an escalation-style LLM judge;
  what threshold counts as "conflict."
- **Docs:** future `dissonance.md`, `fact-level-correction.md`, `mid-dialogue-gate.md`.
  **Confidence: Medium-High (gap) / speculative (shape).**

### #4 — Reflection pipeline design dossier  · **P2 (future-input)**  · (bank for the sequenced-later spec)
When reflection is specced, four papers give concrete, ablation-backed design — and one gives a named
failure mode to design against:
- **Ground reflective writes in cited evidence, add a staleness detector.** `honest-lying-confabulation`:
  Reflexion-style self-generated memory confabulates (0/121 reflections mention the correct object in
  16 "frozen" envs; wiping memory solves 2 of them *faster*). Fix = quote specific trace steps + an
  RRR repetition detector. Our reflection write step should ground conclusions in specific
  `memory_id`s (cheap — invariant #6 already returns IDs) and budget a staleness check before an
  identity revision is trusted. **This is the most important reflection caution in the corpus.**
- **Periodic, evidence-conditioned identity refresh** (current-anchor + recent-window + constraints →
  new doc) beats both static prompting and full-history stuffing — ablation-quantified. `ai-you-town`
  (+0.87 fidelity, less drift). Our `identity_documents`/`identity_version` plumbing already exists;
  the refresh must still write a *new* row (bump version), not mutate.
- **Persona-lensed retrieval routing** — precompute a few typed "lenses" (relationship/grievance/goal),
  classify the situation, retrieve that lens alongside vector similarity. `self-reports-simulation`
  (expert-reflection routing); `adamem` (aspect-based persona distillation).
- **Idle-time scheduling** — turn reflection from an integrator-pulled endpoint into a sleep-time
  compute pass (and the basis for the dormant-agent overseer). `sleep-time-compute` (~5× cheaper at
  equal accuracy; caveat: only pays off for *anticipatable* work).
- **Hierarchical/online consolidation** — organize episodes into a schema tree incrementally, no batch
  rebuild. `dynamic-tree-memory`/MemTree (but its node-overwrite is destructive → version tree nodes);
  `survey-ai-agents` (Consolidation as a distinct operation; also names **Experiential memory** —
  case/strategy/skill — as a whole function class we don't touch).
- **Docs:** the future reflection spec. **Confidence: High (as design input).**

### #5 — Recall/frequency-reinforced decay  · **P2**  · (also in Table 1 as augmentation) — see above.

### #6 — Conditional / context-bound memory validity  · **P3**
Multiple values for one slot, each valid under a context ("tea when raining, coffee otherwise"); a
natural NPC preference shape and a natural occupant of the reserved encoding-context term.
`memconflict` §3.3.4. Needs a write-time condition tag (migration) + a read-time match. Pairs with #2
in Table 1 (RaMem) and the encoding-context slot. **Confidence: Medium.**

### #7 — Soft per-turn steering + action fallback  · **P2/P3**  · (Unity API surface)
`bounded-autonomy`: **Whisper** — an optional per-call NL nudge that biases the next dialogue turn
without overriding generation or touching storage (86.7% intervention-aligned); and a
confidence-thresholded **safe-default action** instead of our silent drop on an unrecognized directive
(priced honestly as a tradeoff — it can put unchosen words in the NPC's mouth). Cheap, no schema, no
invariant touched. **Docs:** `architecture.md` §9, `cli-harness.md`, Unity C# API queue.

### #8 — Explicit abstention / "no memory of this" signal  · **P3**  · (mild thesis tension)
A structured low-max-score branch feeding "the character has no memory of this" into prompt assembly,
distinct from fail-quiet-on-error. `less-context` (abstention gate, 86.7%), `beyond-million-tokens`
(abstention is the *most* tractable ability). **Tension:** cuts against confabulation-is-the-point —
must fire on genuine *absence* (never-observed), not on decayed detail. A values question, not just a
technical one. **Confidence: Low (thesis tension noted).**

### #9 — Cross-NPC shared world-fact layer  · **P3**  · (likely out of current scope)
Players read contradictory answers from different NPCs about the same event as *dishonesty*.
`genai-npc-vr` §5.4.2. A world-scoped (not agent-scoped) bi-temporal fact table multiple NPCs read
from. Genuinely new schema concept; out of scope for the single-player, per-NPC design today, but a
real believability finding. **Confidence: Medium.**

---

## 4. Thesis-tension log (surface honestly — Jack's call, not silently adopted or dropped)

**#1 — Destructive summarization / in-place update vs invariant #1 (non-destructive).**
Offenders: MemGPT (recursive-summary eviction + `working_context.replace()`), Mem0 (DELETE branch),
A-MEM (memory-evolution overwrite), MemTree (node-aggregate overwrite), Personalized-NPC (KG node
deletion), LIGHT/`beyond-million` (scratchpad compression), SEEM (fusion mutation — its own Limitations
admits "can permanently corrupt the structured memory store"), Nous (unimodal Bayesian posterior,
lossy by default). **Honest read:** mostly *genuine weaknesses* relative to our design, not
apples-to-oranges — and the field measures the cost: HippoRAG-2 Table 2 (summarization-based memory
collapses to F1 1.6–11.6 on plain factual QA), survey-llm-era Exp.4 ("dynamic memory revisions
overwrite earlier evidence"). A few are apples-to-oranges (LIGHT/MemGPT solve token-budget in a single
session with no backing store). **Consequence:** if graph/consolidation memory (§3 #2/#4) is ever
built, edges/nodes must be bi-temporal rows, not deleted/mutated. Several of these are also the
README's **destructive-compression counter-example** candidates (open task in `status.md`) — SEEM's
self-admission and MemoryBank's hierarchical summary are the cleanest.

**#2 — LLM-assisted / model-based gate vs invariant #8 (non-LLM gate).**
Offenders: survey-llm-era (LLM-Assisted Retrieval), survey-ai-agents (ComoRAG/PRIME fast-slow, MemGen
latent triggers), `targ` (draft-logit uncertainty gate), `adamem` (LLM route refiner), `memory-reconstructed-graph`
(multi-turn LLM traversal). **Honest read:** genuine, evidence-backed alternatives — plausibly more
precise, but they cost an LLM call per gate check and break the gate's determinism/testability (the
51-assertion walker depends on the gate being a pure function). This is a trade-off we already made and
documented. **Ammunition *for* our choice:** TARG's own finding that model-confidence/entropy signals
*degrade* on modern instruction-tuned models argues a semantic/structural non-LLM signal is more
robust. **Non-conflicting extraction:** TARG's budget-calibration recipe (Table 1 shortlist #8) —
improves how we tune the gate we have, no invariant touched.

**#3 — Multi-hop LLM traversal at read time vs our single-embed low-latency retrieval philosophy
(not a named invariant).** `memory-reconstructed-graph`/MRAgent (+23–32%, but ~5-turn LLM loop).
**Honest read:** the *lightweight cue/tag or provenance index* (reusing `identity_components`/
`entities[]`) is the compatible extraction; the full active-traversal loop is the tension. Favorable
note: MRAgent's own admitted limitation (monotonic graph growth) is exactly what our
decay/invalidation/cache-eviction already solves.

**#4 — Parametric consolidation / fine-tuning vs our API-model, never-fine-tune stack.**
`episodic-missing-piece` §5 (external-memory-only is "insufficient" without consolidating into weights),
`memos` (cross-substrate parameter/KV memory), `fixed-persona-slm` + `personalized-npc` (per-NPC LoRA).
**Honest read:** apples-to-oranges by design — we treat the model as a swappable per-role API call. A
scope boundary, not a flaw; worth one honest sentence in a limitations section. (Our storage-side
answer to their "forgetting requirement" is decay + reflection's identity-components pruning —
a different, deliberate mechanism.)

**#5 — Outcome-linked dynamic importance vs the write-time-importance / independent-axes invariant.**
`memory-worth-governance` (MW revises a memory's assessed quality post-write from outcomes). **Honest
read:** a genuine positioning tension, but MW's *own* failure experiments show it goes directionally
wrong (−0.33) exactly under policy-coupled, non-uniform retrieval like our gate/decay create — so it's
not evidence we're wrong, it's evidence that adding it needs care (an *advisory reflection-time* signal,
never replacing write-time importance). Nearly free to prototype given our existing memory-ID +
reputation-delta logging. P3.

**#6 — Abstain-when-uncertain vs confabulation-is-the-point** (see §3 #8). Mild values tension; the
resolution is the abstention *boundary* — fabricating never-observed facts is the failure, drifting the
telling of observed ones is the feature.

**Demo-legibility risk (not an invariant tension, but flag for August):** players can't reliably tell
*accidental* model hallucination from *designed* controlled drift (`genai-npc-vr`: an NPC misheard as a
"ship captain" improvised a pirate persona; players theorized "did he lie?"). Our debug/ground-truth
view is the mitigation — make it **demo-legible** in the Unity choreography so the research
contribution reads as intentional.

---

## 5. Positioning / citation bank (for the README + research write-up)

**Thesis-affirming (lead with these):**
- `confabulation` (ACL 2024) — **the lead citation.** Empirically, confabulated dialogue outputs score
  *higher* on narrativity + coherence than truthful ones across 3 benchmarks. "hallucinations make them
  more like us than we would like to admit." Clinical definition of confabulation ≈ a description of
  identity-conditioned reconstruction. Note: it defends confabulation *unconditionally* — our
  drift-budget + fixed-gist + immutable record + debug view are the governance layer it lacks (our
  contribution on top).
- `unfaithful-cot` (Turpin, NeurIPS 2023) — grounds "information-asymmetric multi-call cognition":
  biasing features shift predictions up to 36pts while explanations essentially never mention them
  (1/426). "LLMs do not always say what they think." The counterfactual-simulatability method is the
  ready template for the research track's **asymmetry ablation** (gated on the post-August split-brain).
- `false-memories-witness` (Loftus et al.) — LLM sycophancy induced 3× more durable false memories in
  humans (36.4% vs 10.8%, confident a week later). Bartlett/Loftus reconstructive lineage. Also a
  **design caution** for the diegetic-correction/dissonance path (sycophantic reinforcement is
  structurally the same shape).
- `survey-ai-agents` §7.8 — "agents possess a veridical record of the past, [but] lack the biological
  capacity for memory distortion, abstraction, and the dynamic remodeling of history" — a near-direct
  description of the gap our reconstruction mechanism closes; names "generative reconstruction" as the
  frontier.
- `survey-llm-era` — Lesson L5 ("keep old info, mark its status, don't delete") is our invariant #1
  verbatim; Opportunity O3 (bidirectional consolidation↔reconstruction) names as open future-work what
  our reconstruction already does.

**Non-destructive-storage validation (the cost of the alternative, measured):**
- `rag-to-memory`/HippoRAG-2 Table 2 — summarization-based memories collapse on factual recall.
- `survey-llm-era` Exp.4 — destructive revision makes early-session info vulnerable.
- `structured-episodic-event-memory` Limitations — fusion "can permanently corrupt the structured
  memory store" (a paper's own admission — strong README counter-example).
- `stale` — "current-state adjudication gap": co-resident stale+fresh memories, retrieved but not
  adjudicated (77.5% retrieved, 3.3% judged as needing update); our live-head design structurally
  avoids this *once a correction has been made*.

**Vocabulary worth borrowing:** narrative coherence vs narrative fidelity (Fisher, via `confabulation`)
maps to reconstruction-quality vs drift-budget; "a memory can be related to the query while still being
invalid evidence for it" (`ramem`) sharpens relevance-vs-validity; episodic-memory's five properties
(`episodic-missing-piece`) as a completeness checklist.

---

## 6. Per-paper coverage index (all 41, so nothing is lost)

**Memory systems:** memgpt (multi-hop-as-dialogue-tool P2; DMR judge pattern; destructive tension),
mem0 (auto conflict-detection P2; Mem0g graph; DELETE tension), a-mem (link-gen graph slice P2;
evolution-overwrite tension), memorybank (recall-reinforced decay P2; summary counter-example), memos
(eval methodology P3; parametric tension), hipporag (KG+PPR graph P2, non-destructive), rag-to-memory
(HippoRAG-2 graph-without-regression; factual-collapse citation), dynamic-tree-memory (online
hierarchical consolidation P3; overwrite tension).

**Surveys:** survey-llm-era (hybrid retrieval P2; graph/hierarchy gaps; L5/O3 citations; LLM-gate
tension), survey-ai-agents (auto-conflict + frequency-decay strictly-better; experiential/consolidation
gaps; §7.8 citation; fast-slow-gate tension).

**Episodic/reconstruction/cognition:** episodic-missing-piece (encoding-context = defining property;
parametric tension), memory-reconstructed-graph/MRAgent (active graph traversal — naming-collision
caveat; lightweight cue/tag P2; latency tension), confabulation (**P1 lead citation**; narrativity+
coherence eval metric).

**NPC/game:** bounded-autonomy (Whisper + action fallback P2), memory-driven-roleplay (MREval /
Answer-Leakage eval P2), personalized-npc (KG graph gap; AMR query parsing; node-deletion tension),
fixed-persona-slm (judge-free retention check P2; fine-tune tension), project-sid (PIANO coherence
counterpoint for split-brain P3), self-reports-simulation (**identity-grounding depth P2**; expert-lens
routing), genai-npc-vr (cross-NPC consistency gap P3; **demo-legibility risk**).

**Evaluation:** longmemeval (**P1** — taxonomy + knowledge-update + abstention), longmemeval-v2
(Insert/Query harness + premise-awareness rubric + Pareto), very-long-term-conv-memory/LoCoMo (**P1** —
FactScore-retargeted reconstruction eval; adversarial/wrong-speaker), incremental-multi-turn/
MemoryAgentBench (**P1** — FactConsolidation selective-forgetting), memconflict (conflict taxonomy +
metrics; conditional-validity gap), stale (**implicit-conflict detection P2**; SR/PR/IPA eval;
live-head strictly-better-once-corrected), beyond-million-tokens (nugget eval; contradiction-unsolved
corroboration).

**Cognition/faithfulness/efficiency:** unfaithful-cot (**P1 research citation** + asymmetry-ablation
protocol), false-memories-witness (**P1 positioning** + diegetic-path caution), less-context-more-accuracy
(hybrid retrieval + abstention gate P2; validates lean-retrieval philosophy), sleep-time-compute
(idle-time reflection scheduling P2; validates reconstruction pre-warm).

**Discovered (arXiv):** ramem-contextual-reinstatement (**P1 encoding-context re-ranking**),
memora-forgetting-aware-benchmark (FAMA stale-leakage eval P2), memsyco-bench-sycophancy (memory-use
correctness eval P2), nous-belief-based-memory (provenance-capped arbitration for dissonance P3;
posterior-lossy tension), memory-worth-governance (outcome-linked signal P3; static-importance tension),
targ-adaptive-retrieval-gating (**gate budget-calibration P2**; LLM-gate tension), adamem-adaptive-user-memory
(typed-edge graph — largest ablation effect P2; LLM-refiner tension), structured-episodic-event-memory/SEEM
(Reverse Provenance Expansion graph P2; fusion-corruption tension + citation), ai-you-town-digital-twin
(periodic identity refresh + calibrated uncertainty P2), honest-lying-confabulation (**reflection
confabulation caution + RRR detector P2**).

**Discovered — second wave (graph-memory de-risking + eval specifics):** gaama-graph-associative-memory
(**concept-mediated Postgres-native graph P2** — 3/4 node types already ours; `identity_components` =
concept node dodges mega-hubs), sprig-democratizing-graphrag (**app-side CPU-only PPR, no graph DB** —
but graph-only underperforms dense; needs hybrid seeding), phasegraph-calibrated-fusion (percentile-rank
score calibration for graph-term fusion; own system is Neo4j — fusion-math half only), memtrace-knowledge-point-probing
(**trajectory probe our version-chain is uniquely suited to answer**; reach-vs-use failure attribution;
separate abstention/conflict axes — eval-harness input).

---

## 7. What the corpus does NOT threaten

Worth stating plainly: nothing in 41 papers argues the core thesis is wrong. The one paper whose title
most resembles it (`memory-reconstructed-graph`) is about *retrieval-time search*, not content drift —
orthogonal, not opposing. The strongest challenges are the parametric-consolidation view
(`episodic-missing-piece` — apples-to-oranges for our no-fine-tune stack) and the destructive-update
family (which the field itself increasingly abandons, and whose cost is now measured). The
non-destructive bi-temporal design, the reconstruction thesis, and the non-LLM gate all come out of the
sweep *validated*, with named third-party evidence — while the two biggest actionable gaps (a judged
eval harness; associative/graph retrieval) were already on the project's own radar.

---

## Appendix A — adoption notes & open forks (where each top finding lands; what Jack would rule)

*This is reporting, not design: each item names the seam it touches and the decisions Jack would have
to rule — it does not resolve them. "Bigger than a bolt-on" is a sequencing note, never a rejection.*

**#2 Encoding-context re-ranking (RaMem) — the cleanest P1.** Lands entirely in `_score_rows`
(`app\retrieval.py:115`) as an added term over fields **that already exist on both sides**: the
request carries `location_name`/`entities`/`event_time` as `# RESERVED — inert in v1`
(`app\schemas.py:255-257`) and the rows store them (`memories` cols, migration 001; entities also on
the fact head, migration 003). **No migration, no wire-contract change** — only read-time consumption.
Forks to rule: (a) **source of the recall-condition** — client-supplied structured fields (the game
already knows current location/scene participants) vs RaMem's LLM query-decomposition (the latter
collides with the 2026-07-14 "query embedded as-is; service never composes prose" ruling → its own
model role + a ruling); (b) soft-prior **weight** as an `agents.config` knob (invariant #5); (c) what
"mention time" is (almost certainly `memories.created_at`). Keep it a *soft prior with content
fallback* (matches fail-quiet), never a hard filter.

**#1 Judged eval harness.** The loop already exists: `app\session.py` + `app\load_driver.py` drive
observe→retrieve→dialogue turn-by-turn (LME-V2's Insert/Query harness shape maps onto exactly this).
The missing piece is a **judge** and scored scenarios, sitting *beside* the Stop-hook structural suite
(which stays structural-only), not inside it. Forks: judge model role (its own env var per the
role-config rule); starter category set (recommend: selective-forgetting + abstention +
reconstruction-FactScore-retargeted); home (`docs\eval-harness.md` + a `tests`-adjacent or separate
runner). The cheap **judge-free keyword-retention check** (Fixed-Persona SLM) can land inside the
existing structural discipline immediately, ahead of any judge.

**#3 Hybrid lexical+vector.** A second candidate channel in `app\db.py` — a Postgres `tsvector`/GIN
index over `memory_fact_versions.basis_text` (a migration) fused with the existing vector over-fetch
*before* `_score_rows`. Forks: fusion method (RRF vs union-into-over-fetch vs a lexical term in the
product score); fusion-weight knob; whether the lexical channel also serves the gate's degraded rung.

**#4 Associative/graph memory.** Biggest build; own spec + migration. Reuses `identity_components`
(canonical+aliases) and `memory_fact_versions.entities` as a proto-cue-index. Forks: edge source
(a write-time extraction model role vs deriving edges from co-occurring entities with no new call);
traversal (recursive CTE in hand-written SQL vs an in-process graph built per-agent); **non-destructive
edges** (bi-temporal rows — several source papers delete/mutate, §4 #1); which retrieval rung consumes
it. Cheapest first step with real payoff: HippoRAG's **node-specificity IDF weight** on the existing
entity tripwire (one count, no graph).

**#4 — de-risked by the second-wave scout (GAAMA + SPRIG): yes, buildable natively, and our schema is
already unusually well-positioned.**
- **It does NOT need a graph DB.** `sprig-democratizing-graphrag` (2602.23372) proves Personalized
  PageRank is plain sparse linear algebra — an adjacency from co-occurrence counts (hand-written SQL) +
  power-iteration in the app process, CPU-only, zero LLM calls at build or query. No Neo4j, no Apache
  AGE, not even a recursive CTE.
- **Our schema already occupies the design.** `gaama-graph-associative-memory` (2603.27910) gives a
  4-node/5-edge typed graph where three node types are tables we already have (`memories`≈episode —
  their "verbatim, no-LLM episode" step *is* our `observation_text` immutability; `memory_fact_versions`
  ≈fact; `reflections`≈reflection). Critically, **`identity_components` is already a concept-style node**
  (canonical+aliases+category), not an entity node — and GAAMA's central empirical finding is that
  entity-centric graphs *mega-hub* (400–500+ edges/entity, diluting PPR — the exact failure that sank
  HippoRAG/Mem0g/AdaMem in our corpus) while concept-mediated graphs stay ~30× sparser. So building the
  graph against `identity_components` rather than raw `entities[]` **already dodges the most-corroborated
  failure mode.** Both papers confirm the graph term should be a *small additive nudge* on the existing
  relevance×recency×importance score (GAAMA's ablation: PPR weight 0.1; weight 1.0 was *worse* than
  semantic-only), and both non-destructively (GAAMA's GRAFT repair is insertion-only).
- **Honest tempering (SPRIG):** graph-only retrieval *underperforms* plain dense; the gains appear only
  when PPR is **seeded from vector/lexical hits (hybrid)** — so #3 (hybrid lexical+vector) is the
  prerequisite base, and graph is a second-order refinement on top, not a standalone win.
- **The one thing neither paper solves — our extension to design:** bi-temporal **edge supersession**.
  Co-occurrence must be computed from *live* fact/detail heads only (mirroring one-live-head), and an
  authorial correction must re-derive/invalidate that memory's concept edges. Non-destructive by our
  rule; unaddressed by them (both operate over static corpora).
- **Revised build ordering:** #3 hybrid base → node-specificity IDF on the tripwire (cheap, no graph) →
  concept-mediated edge table (bi-temporal) + app-side seeded-PPR as a 0.1-weight additive term.
  `phasegraph-calibrated-fusion` (2603.28886) supplies percentile-rank score calibration for the fusion
  math (its own system uses Neo4j — only the fusion half transfers).

**#5 Recall/frequency-reinforced decay.** A term in `decay.tau_effective` (`app\decay.py:42`) + a
counter/last-recalled column (migration). Forks: **what counts as "recall"** (a gate fetch? a
reconstruction serve? a dialogue surface?) — this is the crux, because it must (a) not conflate decay
with invalidation (invariant #2, which `decay.py`'s own docstring guards) and (b) not let a same-scene
read trigger a decay recompute that breaks the within-scene byte-identity invariant.

**#6 Automatic conflict/staleness detection.** Reuses the migration-003 entities GIN + live fact-head
embedding for candidate-conflict lookup, and `typology`/`typology_source`/`provenance` for the
Nous **provenance-cap** trust principle. Forks: heuristic vs an escalation-style LLM judge (the
escalation seam already exists); the conflict threshold; whether it writes an auto-supersede or only
*flags* for the (unbuilt) dissonance path. It is the write-time counterpart of dissonance — likely its
own spec session, and honestly hard (industry-wide unsolved → a differentiator, not a quick win).

**#8 Gate budget-calibration (TARG).** No runtime change — an offline recipe/utility (optionally in
`app\load_driver.py`) that sets `gate_novelty_threshold` from a target fetch-rate via the empirical
CDF of the novelty-distance signal. `gate.decide` already compares `min_distance >= threshold`
(`app\gate.py:133`); this only changes how that threshold is *chosen*. Essentially fork-free.

## Appendix B — code-grounding verification (baseline checked against the actual code, not just docs)

All five load-bearing "our current mechanism" claims were confirmed against `app\` source — the
docs-derived baseline matched the code exactly (no findings required correction):

- **Query embedded as-is; context slots reserved-not-consumed** — `retrieval.py:175-184` embeds only
  `query_text`; `_score_rows` uses none of `location_name`/`entities`/`event_time`; `schemas.py:255-257`
  marks them `RESERVED — inert in v1`. (Grounds #2 RaMem, #3 hybrid.)
- **Score = relevance × recency × importance_norm, clamp+floor, pin exemption** — `retrieval.py:129-147`
  verbatim. (Grounds every read-path finding.)
- **Decay is age + write-time importance only, no usage term** — `decay.py:42-50`; docstring explicitly
  separates decay from invalidation. (Grounds #5 recall-decay.)
- **Gate threshold is a fixed cosine cutoff, pure/non-LLM** — `gate.py:133` (`min_distance >= threshold`),
  threshold = `gate_novelty_threshold` knob (default 0.5). (Grounds #8 TARG + the §4 #2 gate-LLM tensions.)
- **Identity is seed-prose-verbatim, no refresh mechanism, version-bump plumbing exists** —
  `identity.py:26-43`. (Grounds #7 self-reports grounding-depth + the AI-YOU periodic-refresh finding.)

Source PDFs were also spot-checked for the headline quantitative claims (RaMem context-collapse/
encoding-specificity/Tulving; HippoRAG Personalized-PageRank/"20 points"; Confabulation's pull-quote;
MemoryAgentBench "Selective Forgetting"/"28%") — all present in the original text.
