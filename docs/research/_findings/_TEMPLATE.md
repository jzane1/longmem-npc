# Findings template (copy this structure for EACH paper)

> Read `_baseline\current-architecture.md` FIRST. Every judgment is relative to that yardstick.
> One file per paper, named `<short-slug>.md`, written into `Research Papers\_findings\`.
> Be specific and traceable: page/section refs + short quotes. Terse is fine; evidence is not
> optional. If a paper has nothing relevant to us, say so in one line and stop — do not invent
> findings.

---

## <Paper Title>

- **Authors / venue / year:** …
- **arXiv / DOI:** …
- **Source:** folder | discovered
- **Overall relevance to longmem-npc:** High | Medium | Low — one sentence why.
- **Core contribution (2-3 sentences):** …

### Mechanisms relevant to us
Bullet the specific mechanisms/designs this paper introduces that map onto a component in the
baseline (retrieval scoring, decay, reconstruction, gate, correction, reflection, dialogue/reputation,
storage, eval, dissonance/faithfulness). Skip everything irrelevant.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
For each — use this block:
- **Component touched:** <name from baseline, e.g. "Read path / retrieval scoring">
- **Our current mechanism:** <one line, from baseline>
- **Paper's mechanism:** <what they do> — *evidence:* §/p. X, "<short quote>"
- **Why strictly better:** <concrete: accuracy, cost, latency, robustness, expressiveness…>
- **Adoption cost/risk in our stack:** <Postgres/no-ORM/1536-locked/non-destructive/config-not-hardcoded>
- **Docs it would touch:** <e.g. docs\read-path.md, architecture.md §6>
- **Confidence:** High | Medium | Low

*(none, if none)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
Same block shape, but "Our current mechanism" = "none / gap noted in baseline as …":
- **Capability:** …
- **What the paper does:** … — *evidence:* §/p. X, "<short quote>"
- **Why worth adopting for an NPC memory service:** …
- **Adoption cost/risk in our stack:** …
- **Docs it would touch:** …
- **Confidence:** High | Medium | Low

*(none, if none)*

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
- **Invariant challenged:** <which one>
- **What the paper does that conflicts:** … — *evidence:* §/p. X
- **Honest read:** is this a genuine weakness in our design, a positioning counter-example, or an
  apples-to-oranges (different problem)? Explain.

*(none, if none)*

### Quotable lines / citations for positioning (optional)
Short quotes useful for the README / research write-up (esp. confabulation, reconstruction,
non-destructive vs destructive-compression framing, encoding specificity).

### Verdict
One or two sentences: what, if anything, should Jack seriously consider from this paper, and at what
priority (P1 adopt-soon / P2 worth-piloting / P3 note-only).
