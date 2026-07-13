---
description: Scoped build task — scope boundary, stop-and-report, Gherkin done-when, staged verification
argument-hint: <task description or a docs\ spec name>
disable-model-invocation: true
---

# Build task: $ARGUMENTS

## Phase 1 — Orient (no file changes)
1. If the task names or implies a spec in docs\ (e.g. migration-01), read that file in full. Read
   the sections of docs/architecture.md this task touches. status.md is already loaded.
2. Present, in this order:
   - **Assumptions** — what layer this builds on, the known-good floor beneath it, and your
     reading of the task in two sentences.
   - **Scope boundary** — an explicit list of what this task does NOT build. Start from the
     spec's scope boundary if it has one; extend it with anything adjacent you might otherwise
     be tempted to touch.
   - **Done-when** — Gherkin-style criteria (Given / When / Then). Use the spec's "Done when"
     section verbatim where it exists, plus task-specific criteria. Every criterion must be
     checkable by running something and showing output — nothing subjective.
   - **Plan** — ordered steps, each small enough to verify before the next begins.
3. STOP. Do not create or edit any file until Jack explicitly approves the plan.

## Phase 2 — Build (after approval only)
- Follow the approved plan. Build only what the task names.
- Stop and report — never guess — on: ambiguity in the task or spec, any [SETTLE-AT-BUILD] tag,
  any conflict between the task and docs\, any failed check. A report = the problem, the options
  with tradeoffs, then wait.
- If the same check fails twice for the same cause, stop and report rather than iterating
  blindly.

## Phase 3 — Prove and close
- Walk the done-when list one criterion at a time: show the command run and its actual output
  for each.
- Staged verification: state what floor this layer was verified against and how.
- Execute the end-of-task protocol from CLAUDE.md (status.md update; decisions.md if Jack ruled
  on anything; commit, never push).
