## MemConflict: Evaluating Long-Term Memory Systems Under Memory Conflicts

- **Authors / venue / year:** Zhen Tao, Jinxiang Zhao, Peng Liu, Dinghao Xi, Yanfang Chen, Wei Xu,
  Zhiyu Li — Renmin University of China et al.; J. ACM (formatted as Vol. 37, No. 4, Article 111 —
  arXiv metadata dates it 2026-05-20). arXiv:2605.20926v1 [cs.IR]
- **arXiv / DOI:** arXiv:2605.20926v1
- **Source:** folder
- **Overall relevance to longmem-npc:** Medium-High — it is a pure evaluation framework (no memory
  mechanism of its own to adopt), but its three-way conflict taxonomy and white-box retrieval/rank
  diagnostics map directly onto gaps in our built mechanisms: automatic contradiction/update
  detection (we have none) and conditional/context-bound memory validity (we have none).
- **Core contribution (2-3 sentences):** MemConflict is a diagnostic benchmark, not a memory
  system. It formalizes three conflict types over long-horizon multi-session user histories —
  **dynamic** (a later true state update should supersede an earlier one), **static** (a later
  false/contradictory mention should NOT overwrite a stable fact), and **conditional** (multiple
  values are all valid, each under a different context — e.g. "coffee in the morning, milk at
  night" — and only the query-matching one should be surfaced) — and evaluates six existing memory
  systems (A-Mem, LangMem, Letta, MemOS, Mem0, Memobase) both black-box (final-answer accuracy) and
  white-box (did the gold memory item get retrieved, and how highly ranked).

### Mechanisms relevant to us
- Three-way conflict taxonomy (dynamic / static / conditional) as a decomposition of "memory
  validity" — maps onto our bi-temporal invalidation (dynamic), our authorial/diegetic correction
  verbs (static), and a capability we don't have at all (conditional).
- White-box vs black-box separation: **Support Evidence Hit@K**, **Support Rank Score** (rank-
  discounted), **Conflict Recognition Score** (does the system even notice a contradiction
  exists?), **Update Order Consistency Score** (temporal ordering of superseding states), and the
  **Evidence Utilization Gap** = SEH@K − AA (gold memory retrieved but answer still wrong — isolates
  retrieval failure from downstream-use failure).
- Diagnostic finding (§4.5.2, p.111:27, Table 7/Fig.8): across all six systems, **retrieval
  failure dominates over utilization failure** (e.g. Mem0: 91.4% of dynamic-conflict errors are
  retrieval failures vs 8.6% utilization), but this reverses for some system/conflict-type
  combinations (LangMem dynamic: 46.1% retrieval vs 53.9% utilization — "it can surface relevant
  updated memories but does not always convert them into temporally valid answers").

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none)* — MemConflict is an eval harness over other systems' memory designs, not a mechanism we
could adopt. We have no automatic conflict-recognition or conditional-validity component today to
compare against, so nothing here "beats" a component in the baseline; the gaps below are properly
NOT-YET-BUILT.

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** Automatic detection that a new write conflicts with / supersedes an existing
  memory, without an external actor naming the target. Our bi-temporal invalidation (baseline
  invariant 1) is a mechanically sound *storage* mechanism, but every supersession we support is
  *operator-driven* (authorial correction names a `memory_id`) or *diegetic* (the caller supplies
  the target `memory_id` — mechanism itself still post-August/not built). Nothing in `app\ingest.py`
  inspects an incoming observation against the existing store to ask "does this contradict or
  update something already there?" — the write path's gist-matching against `identity_components`
  matches *entities/topics*, not *conflicting claims*.
  — *evidence:* §3.1 (p.111:8), "the system must return the memory content that is valid for that
  query" (framed as a retrieval-time burden precisely because *write-time* conflict resolution isn't
  assumed to exist in any of the six evaluated systems either); §4.6 (p.111:28), "memory
  representations should explicitly encode temporal state, source attribution, and applicability
  conditions, rather than storing extracted facts as isolated snippets."
  - **Why worth adopting for an NPC memory service:** Directly the same gap the STALE paper
    (companion finding) hits from the opposite angle. Worth flagging jointly rather than building
    twice.
  - **Adoption cost/risk in our stack:** High — this is a genuinely unsolved capability industry-wide
    (best CRS in Table 3 is 0.2501, i.e. even the strongest system recognizes a contradiction less
    than 1-in-4 times it's queried about it). Cheap partial version: an LLM-scored "does this
    observation plausibly conflict with entity X's known facts" check riding the existing gist-
    escalation LLM call (same seam, no new model role) — but this is a design decision for Jack, not
    a drop-in.
  - **Docs it would touch:** `docs\fact-level-correction.md`, `docs\mid-dialogue-gate.md` (entity
    tripwire is the closest existing analog), a future `dissonance.md`.
  - **Confidence:** Medium (the capability gap is clear; the adoption shape is speculative).

- **Capability:** Conditional/context-bound memory validity — multiple memory values for the same
  slot are all true, each applicable only under a specific context (time-of-day, location, social
  situation), and retrieval must select the context-matching one rather than the most recent or
  most semantically similar. We have no equivalent: our read path's context stamps
  (`location_embedding`, `location_name`, `entities`, `event_time`) are **accepted but reserved,
  not consumed** (baseline §"Read path"). Our importance/relevance/recency scoring has no notion of
  "this memory is valid only when condition C holds."
  — *evidence:* §3.3.4 (p.111:11-12), "A conditional conflict arises when multiple values for the
  same attribute are all valid under their respective conditions, but each value is applicable only
  under its associated condition." Table 3/4 show conditional conflicts are the most *polarized*
  across systems — some (MemOS, Letta) do reasonably (AA ~0.55, SEH@3 ~0.57-0.90) while others
  (LangMem, Memobase) score near-floor, "fail to preserve or retrieve condition-value associations
  reliably" (§4.3.2, p.111:19-20).
  - **Why worth adopting for an NPC memory service:** This is a natural fit for NPC dialogue — "the
    NPC likes tea when it's raining, coffee otherwise" is exactly the shape of preference an
    integrator would want, and it's a plausible next occupant of our reserved encoding-context read
    term (the same slot already flagged post-August).
  - **Adoption cost/risk in our stack:** Medium — the reserved context stamps are already there;
    this would need (a) a way to tag a memory with a condition-predicate at write time (schema
    addition — new migration, per CLAUDE.md's migration-evolution rule) and (b) a matching function
    at read time, which is exactly what the encoding-context term was scoped to become. Not
    hardcoded-vocabulary risk if the condition schema is itself integrator-configurable.
  - **Docs it would touch:** `docs\read-path.md` (encoding-context term), `architecture.md` §6.
  - **Confidence:** Medium.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none)* — MemConflict proposes no destructive or in-place mechanism; it's purely diagnostic.

### Quotable lines / citations for positioning (optional)
- "Long-term memory is therefore not merely a storage problem; it also requires validity
  assessment, memory selection, and conflict-aware ranking" (§1, p.111:2) — good framing line for
  why bi-temporal storage alone (what most competitors do) isn't sufficient.
- "A system may return the correct stable value without explicitly recognizing the underlying
  contradiction" (§4.3.1, p.111:19) — useful contrast: our correction verbs make the "recognition"
  step an explicit, auditable operator/diegetic act rather than an implicit black-box judgment,
  which is a genuine (if manual) robustness advantage worth naming in the README/write-up.

### Verdict
P3 note-only for direct adoption (it's an eval framework over *other* systems, not a mechanism),
but P2 worth-piloting as inspiration for our own future eval harness: adapting SEH@K / SRS / CRS /
UOCS-style metrics against our own retrieval would give us a first conflict-aware eval, which the
baseline explicitly lists as missing. The conditional-conflict gap is the more novel, buildable
finding here and pairs naturally with the already-reserved encoding-context read term.
