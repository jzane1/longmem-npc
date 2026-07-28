---
description: End-of-session close-out — status update, decision sweep, commit (never push)
allowed-tools: Read, Edit, Write, Grep, Glob, Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git add:*), Bash(git commit:*)
disable-model-invocation: true
---

## Current repo state
- Working tree: !`git status --short`
- Last commits: !`git log --oneline -5`

## Close out this session
1. Update docs/status.md: Last-updated date; one session-log line saying what actually happened
   (landed, blocked, or abandoned — be honest); the verified-floors table if a layer was
   verified this session; queue changes (remove finished items, add discovered work).
2. Decision sweep: scan this session for any ruling Jack made that is not yet in
   docs/decisions.md. If found, record it following the /log-decision rules and say so.
3. If any [SETTLE-AT-BUILD] tag was resolved this session, confirm the resolution is reflected
   in both migration-01.md and decisions.md.
4. Stage and commit everything with a descriptive message. Never push.
5. Report back in four lines: what landed / what's verified / what's blocked / what's next in
   the queue.
