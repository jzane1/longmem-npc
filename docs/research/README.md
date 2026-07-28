# docs\research\ — the literature sweep

Moved into version control on 2026-07-28 (full-repo audit). These files are hand-and-agent-written
project work product that had been living, untracked, inside a gitignored `Research Papers\`
folder — 58 KB of curated writing plus the per-paper notes behind it, on exactly one machine,
referenced by eight tracked files that would have dangled on any fresh clone.

The **PDFs stay out of the tree** (45 papers, ~117 MB — the reason the folder was ignored in the
first place). Only the writing moved.

## What is here

- **`FINDINGS.md`** — the consolidated result of the 2026-07-20/21 sweep: 45 papers (31 curated +
  14 arXiv-discovered), read by map-reduce reader agents against a baseline brief. This is the
  document that concluded the two biggest gaps were already on the radar (no judged eval harness;
  no graph/associative retrieval) and surfaced one strictly-better mechanism with a slot already
  reserved — RaMem-style encoding-context re-ranking, which shipped as Target A.
- **`CHANGES-FROM-RESEARCH.md`** — the **provenance trace**: every landed and queued change mapped
  to the paper that motivated it. `status.md` describes this as material "for the future README",
  which is precisely why losing it would have hurt.
- **`_findings\`** — the per-paper reader notes (46 files) the consolidation was built from, plus
  `_TEMPLATE.md`. Raw intermediate material, kept because it is the evidence behind the citations
  in the two documents above. Not maintained; read `FINDINGS.md` first.
- **`_baseline-current-architecture.md`** — the brief the reader agents were given, describing the
  system as it stood at the sweep. A dated snapshot, **not** current design truth — for that, read
  `..\architecture.md`.

## A note on the links inside these files

The reader agents wrote **forward references** to specs that did not exist and mostly still do
not — `docs\eval-harness.md`, `docs\reflection.md`, `docs\graph-retrieval.md`,
`docs\memory-graph.md`. They read as citations but are proposals: "this belongs in a doc we have
not written." Sixteen such references were checked and left as written, because editing archival
notes to hide the fact that the work is queued would be worse than the dangling link. The queued
items themselves are tracked in `..\status.md`, which is the authority.

## Status

Point-in-time, like the external audits: these describe the literature as read in July 2026 and
are not kept current. The rulings they produced are in `..\decisions.md` (the dated
"Research-adoption slate" entry and the two build entries that followed); the queued items are in
`..\status.md`.
