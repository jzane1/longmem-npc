# tests\ — structural-only discipline

These rules load whenever work touches this folder. Full spec: docs/test-suite.md — read it
before writing or changing any test.

## The one rule
Assert ONLY on structure: memory IDs, row types (write_cause, read_mode, typology), chain shape
(which rows are live vs invalidated), cache presence/absence, timestamps, and byte-identity of
returned text.

NEVER assert on generated prose: no substring matches, no regex over model output, no semantic
similarity checks. A model's wording is not a test surface.

## Mechanics
- Time travel = injected valid_at timestamps, plus the read path's `as_of` request override
  (adopted 2026-07-14). Tests never sleep() and never depend on wall clock.
- No fixture modes. Correction scenarios are verb-forked structural pairs keyed on write_cause.
- Deterministic: the suite must pass every run, and must stay CI-ready — offline, keyless,
  self-managing its scratch DB. The CI workflow itself lands in the public-flip sprint (ruled
  2026-07-20: "CI-ready now, workflow later"); until then the Stop hook is the on-machine gate.
- Judged or LLM-graded evals do not live in this folder — they belong to the separate eval story.

## When blocked
If an assertion seems to require checking prose, stop and report. The gap is usually in the
endpoint contract — IDs + scores for endpoints that RUN RETRIEVAL, IDs + structured fields for the
three unscored-by-contract reads (`/chain` and `/agents/{id}/memories`, ruled 2026-07-27;
`/memories/{id}/reconstruction-metrics`, the third member 2026-07-29). That is a
design conversation, not a test workaround.
