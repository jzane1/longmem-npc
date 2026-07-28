---
description: End-of-session close-out — status update, decision sweep, commit (never push)
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git add:*), Bash(git commit:*)
disable-model-invocation: true
---

## Current repo state
- Working tree: !`git status --short`
- Last commits: !`git log --oneline -5`

## Close out this session
1. Update the living record — three files since the 2026-07-28 split:
   - **docs/status.md** — Last-updated date; the phase header if the phase moved; queue changes
     (remove finished items, add discovered work). LIVE STATE ONLY — history goes below.
   - **docs/session-log.md** — append one entry at the END saying what actually happened
     (landed, blocked, or abandoned — be honest).
   - **docs/floors.md** — append a row only if a layer was floor-verified **pass** this session.
2. Decision sweep: scan this session for any ruling Jack made that is not yet in
   docs/decisions.md. If found, record it following the /log-decision rules and say so.
3. If any [SETTLE-AT-BUILD] tag was resolved this session, confirm the resolution is reflected
   in both migration-01.md and decisions.md.
4. Stage and commit everything with a descriptive message. Never push.
5. Report back in four lines: what landed / what's verified / what's blocked / what's next in
   the queue.
