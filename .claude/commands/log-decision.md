---
description: Append a dated ruling from Jack to docs/decisions.md and flag propagation targets
argument-hint: <the ruling; include what it beat and why, if Jack stated them>
disable-model-invocation: true
---

Record this ruling from Jack in docs/decisions.md: $ARGUMENTS

Rules:
1. Append only, at the end of the file. Never edit or delete existing entries.
2. Entry format: `## <Short decision name> — <today's date>`, then: what was decided; what was
   rejected (only if stated); rationale (only what Jack actually said — never invent a why);
   consequences to propagate (which docs\ files or code currently state the old position).
3. If the ruling supersedes an existing entry, add one line under the OLD entry:
   `*Superseded <date> — see <new entry name>.*` That is the only permitted touch to old entries.
4. Search docs\ (and code, once any exists) for statements of the old position. List every spot
   needing propagation with its exact current wording. Ask before editing any of them.
5. Add a session-log line to docs/status.md.
6. If the ruling is ambiguous, or seems to conflict with an invariant in CLAUDE.md, stop and ask
   before writing anything.
