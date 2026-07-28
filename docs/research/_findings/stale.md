## STALE: Can LLM Agents Know When Their Memories Are No Longer Valid?

- **Authors / venue / year:** Hanxiang Chao, Yihan Bai, Rui Sheng, Tianle Li, Yushi Sun — Wuhan
  University / CUHK / HKUST; Preprint, arXiv:2605.06527v1 [cs.CL], 2026-05-07.
- **arXiv / DOI:** arXiv:2605.06527v1
- **Source:** folder
- **Overall relevance to longmem-npc:** High — this paper's entire subject, "implicit conflict"
  (a later observation invalidates an earlier memory without explicit negation), is the exact
  capability our designed-but-unbuilt dissonance path and our operator/diegetic-only correction
  verbs currently lack: nothing in longmem-npc detects staleness on its own.
- **Core contribution (2-3 sentences):** STALE is a 400-scenario, 1,200-query benchmark (contexts
  to 150K tokens) that formalizes **Implicit Conflict** with two types — **Type I (co-referential):**
  two observations update the *same* attribute without explicit negation (e.g. Seattle → Portland
  lease); **Type II (propagated):** a new observation updates a *different* attribute that
  causally/logically invalidates a structurally-related older belief (e.g. a leg injury silently
  invalidates a "bikes to work" commute preference) — and probes three dimensions: **State
  Resolution** (explicit "is this still true?"), **Premise Resistance** (does the model reject a
  query that presupposes the stale state?), and **Implicit Policy Adaptation** (does the updated
  state get applied in ordinary downstream behavior with no conflict cue at all?). It also proposes
  **CUPMEM**, a prototype doing write-time state adjudication (KEEP/STALE/REPLACE/UNKNOWN) plus
  dependency-graph-based propagation search, which lifts overall accuracy from 8.7% to 68.0% on the
  same backbone.

### Mechanisms relevant to us
- **Type I / Type II implicit-conflict taxonomy** — directly analogous to our bi-temporal
  invalidation (Type I is what supersession handles once *told*) and to the (designed, unbuilt)
  dissonance path (Type II is the harder cascading case nothing in our system detects at all).
- **Three-dimensional probing (SR / PR / IPA)** — a template for a staleness-aware eval harness we
  don't have; directly reusable against our own retrieval + dialogue turn.
- **CUPMEM's write-side adjudication + typed state schema** — an explicit alternative design for
  automatic staleness detection at write time, with a bounded propagation search over "structurally
  affected state regions" rather than leaving cascading invalidation to incidental retrieval.
- **The "current-state adjudication gap" diagnostic (§4.4, p.8-9):** updated evidence is *retrieved*
  most of the time but rarely *judged as requiring an update* — i.e. retrieval succeeding is not the
  same as validity being resolved.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
- **Component touched:** Bi-temporal invalidation / correction (baseline invariant 1;
  `memory_details`/`memory_fact_versions` one-live-head chains).
- **Our current mechanism:** Superseded rows are structurally excluded from the live head — the
  candidate SQL "always joins the live head" (per the 2026-07-18 authorial-correction ruling), so
  once a correction *has been made*, the stale content is architecturally unreachable at read time,
  not merely deprioritized.
- **Paper's mechanism:** All six evaluated memory frameworks (Zep, A-mem, mem-0, LightMem,
  LiCoMemory) keep old and new evidence *co-resident* and rely on retrieval ranking + downstream
  reasoning to suppress the stale one — and largely fail to: "new evidence appears in retrieval
  results for 77.5% of SR/PR cases… [but] only 3.3% of these old entries are judged as requiring an
  update. Stale and updated memories therefore coexist without adjudication." (§4.4, p.8, Table 3).
- **Why strictly better:** For the subset of conflicts that *have* gone through one of our
  correction verbs, our design has already solved the problem this paper shows is unsolved for
  co-resident-memory architectures: there is no "old head that must be out-argued at query time,"
  because it isn't the live head anymore.
- **Important caveat (read honestly):** This advantage is conditional on a correction/invalidation
  event having *already happened* — which today requires an operator (authorial) or an explicit
  diegetic reference to a `memory_id` (mechanism still unbuilt). For a genuinely *implicit* conflict
  that nobody flags (the paper's whole subject), our system has the **identical** gap: the stale
  memory is still the live head, still retrievable, and our dialogue call faces the same
  premise-resistance problem the paper measures. So this is strictly-better only on the narrow slice
  "conflicts we already know about," not on implicit staleness generally — see NOT-YET-BUILT below,
  which is the more consequential finding.
- **Adoption cost/risk in our stack:** N/A (already built); the caveat is the actual finding.
- **Docs it would touch:** none needed — worth a clarifying note in `docs\authorial-correction.md`
  or `fact-level-correction.md` distinguishing "solved once corrected" from "detecting the need to
  correct."
- **Confidence:** High (on the narrow claim), but read together with the caveat.

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** Automatic implicit-conflict detection at write time — flagging (or auto-
  superseding) an existing memory when a *new*, unrelated-looking observation makes it stale, with
  no explicit correction event from operator or game logic. This is the write-time counterpart of
  our designed-but-unbuilt dissonance path, except dissonance (per baseline) is triggered by an
  explicit diegetic event that *already names* the target memory — STALE's Type II conflicts never
  name anything; the invalidation is a pure inference over world knowledge.
  — *evidence:* §3.2 (p.3), formal Axiom 1/2 definition of implicit conflict requiring "no later
  utterance... explicitly negates, corrects, or marks the obsolescence"; §1 (p.1), the canonical
  example: leg injury implicitly invalidates a cycling-commute memory though "the second utterance
  neither mentions cycling nor explicitly contradicts the first."
  - **Why worth adopting for an NPC memory service:** This is precisely the shape of thing a
    long-running NPC needs — a player telling an NPC about an injury, a breakup, a job change,
    should silently color how the NPC treats *other*, previously-stored beliefs about the player,
    without the player or game logic having to explicitly say "and also, forget that I bike to
    work." Directly strengthens the "psychology, not a database" thesis: an NPC that only updates
    beliefs it's explicitly told to update reads as mechanical, not as someone who reasons about you.
  - **Adoption cost/risk in our stack:** High. Genuinely hard even in SOTA (best-of-six memory
    frameworks manage 17.8% overall STALE accuracy vs. plain-GPT-4o-mini's 8.7% — "only LightMem…
    outperforms the plain model"; most frameworks show "limited or inconsistent gains"). CUPMEM's
    own limitations section (Appendix A) concedes it "depends on a predefined state schema… [which]
    constrains the system to limited attribute domains" — collides with our "nothing
    integrator-configurable is hardcoded" invariant unless that schema is itself made
    per-agent-configurable. **Mitigating note:** our `identity_components` table (entity/topic index,
    LLM-grown on novel entities, already the substrate for the gate's entity tripwire) is
    structurally similar to CUPMEM's "state domains and local slots" — a propagation-search-style
    mechanism could plausibly ride that existing index rather than requiring an entirely new schema,
    lowering the adoption cost from "new subsystem" to "new consumer of an existing table."
  - **Docs it would touch:** a future `dissonance.md` (currently only in `architecture.md` as
    designed-not-built), `docs\mid-dialogue-gate.md` (entity tripwire precedent), possibly a new
    migration for storing adjudication status (KEEP/STALE/REPLACE/UNKNOWN-style) if adopted.
  - **Confidence:** Medium — the gap and the analogy to `identity_components` are solid; whether a
    CUPMEM-style schema is the right shape for us is a genuine open design question, not a
    recommendation to build as-is.

- **Capability:** Premise-resistant dialogue behavior — actively rejecting a player utterance that
  presupposes a stale/superseded state, as opposed to passively not retrieving the stale memory.
  We have no such check in `app\dialogue.py`; retrieval simply won't surface an invalidated row, but
  nothing inspects the *player's utterance itself* for an embedded false premise about a *decayed-
  but-not-yet-reconstructed* or *never-corrected* belief.
  — *evidence:* §3.5 (p.6), "Premise Resistance (Adversarial Probing)... A successful model must
  reject the false premise and ground its response in the updated belief." Finding 2 (§4.2, p.7):
  "PR exposes a pervasive vulnerability: it is the weakest dimension even for models with strong SR
  performance… Gemini-3.1-pro obtains 92.0% on Type I-SR but only 30.0% on Type I-PR."
  - **Why worth adopting for an NPC memory service:** Same rationale as above, at the dialogue-call
    level rather than the write-time level — a smaller, cheaper-to-pilot version of the same
    capability (no schema/migration needed, just a prompt-and-eval addition to the existing single
    Sonnet call).
  - **Adoption cost/risk in our stack:** Low-medium to *pilot* as an eval-only probe (no schema
    change); higher if it becomes a hard behavioral requirement, since even the strongest evaluated
    model+method combination here only reaches 30-78% on PR.
  - **Docs it would touch:** `docs\test-suite.md` (a new probing dimension), `cli-harness.md`.
  - **Confidence:** Medium.

- **Capability:** A staleness-aware evaluation harness at all (SR/PR/IPA-style, or STALE's own
  benchmark methodology directly). Baseline states plainly: "no LongMemEval-style accuracy/recall
  benchmark, no judged-drift / Bartlett-style eval, no memory-conflict or staleness eval." STALE's
  three-dimension protocol (plus its finding that recognition ≠ application: "Qwen3.5-27B achieves
  76.0% on Type I-SR but only 39.0% on Type I-IPA") is a ready-made template.
  - **Adoption cost/risk in our stack:** Medium — would need synthetic scenario generation (their
    LLM-pipeline + human validation, §3.4) adapted to our NPC/agent schema.
  - **Docs it would touch:** `docs\test-suite.md`.
  - **Confidence:** Medium.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none)* — CUPMEM's KEEP/STALE/REPLACE marking is conceptually compatible with our non-destructive
bi-temporal invariant (STALE-marking ≈ our `invalid_at` stamp; nothing is deleted or edited
in-place). No genuine conflict found.

### Quotable lines / citations for positioning (optional)
- "A robust memory system must not simply cache dialogue snippets but build a coherent
  representation of an evolving latent user state" (§1, p.2) — strong framing line for the
  reconstruction/identity thesis.
- "Updated evidence can be stored and retrieved, but it does not reliably become the basis that
  governs subsequent answers. We term this the current-state adjudication gap." (§4.4, p.8) —
  precisely names the failure mode our bi-temporal live-head design *structurally* avoids once a
  correction has been made (see STRICTLY-BETTER above), which is a genuinely good positioning
  contrast for the README.
- "Even the strongest model, Gemini-3.1-pro, achieves only 55.2% overall accuracy" (§4.2, p.7) —
  useful citation for "this is an open, hard problem," not a solved one we're behind on.

### Verdict
P2 worth-piloting: the SR/PR/IPA eval template is cheap to adapt and would give us our first
staleness-aware assertions, closing a baseline-flagged gap. The write-time automatic implicit-
conflict detector (CUPMEM-style, riding `identity_components`) is the higher-value, higher-cost
idea — genuinely on-thesis ("a psychology, not a database" implies an NPC that reasons about
staleness, not just one that stores corrections when told to) but should be scoped as its own spec
session rather than folded into a smaller task, given it is a new subsystem, not an extension of an
existing one.
