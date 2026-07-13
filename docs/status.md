# longmem-npc — Status

**Last updated:** 2026-07-13
**Phase:** pre-build (no application code yet), but the **DB + MCP floor is live** beneath the first
build target. All primary and downstream architecture decisions are settled (`decisions.md`). First
build target: `migration-01.md`, now unblocked with a running database to verify against.

This is the *living* file — update it at the end of every working session. `architecture.md` changes
only when design changes; `decisions.md` is append-only.

## Deadline & framing

Single-call demo video: **mid-to-late August 2026**. Do **not** sacrifice vital features or quality
for the deadline — flag deadline pressure when relevant, but never let it drive a decision without
Jack's explicit confirmation. Portfolio target: tier-1 embodied-agent / game-AI employers. Artifact
roles are distinct: the demo video gets the introduction; the instrumentation table, the test suite,
and the structured behavior output survive the interview. Research publication comes after the demo.

## Build discipline

- **Vertical slice before depth; CLI before Unity.** First end-to-end path — event in → memory
  stored → dialogue out — is a console harness: no gate, no caching, no reflection. The CLI is the
  product surface (main file readable as documentation; debug mode exposes retrieved memory IDs,
  scores, parsed structured output, token counts). Unity is the demo; the gray-box scene recorded is
  the fallback video.
- **Staged verification:** each layer verifies against a known-good layer beneath it, so failures
  have a single cause. Anything renamed or ported is re-verified before it counts as a floor.
- **Storage before cognition. Instrument at the seam.** Framework choices must survive the
  interview; ceremony scores below absence.

## Verified floors

| Layer | Verified against | Date |
|---|---|---|
| Postgres 16 + pgvector 0.8.5 container (`longmem-pg`) + read-only Postgres MCP | live: `docker` health `healthy`, `pg_available_extensions` → `vector 0.8.5`, `claude mcp list` → `postgres ✓ Connected` | 2026-07-13 |

## Open questions needing Jack's ruling

*(none — the authorial-correction seam was ruled 2026-07-12: replace model. See the dated entry in
`decisions.md`.)*

## Session log

- **2026-07-12** — Docs established as the in-repo source of truth. Authorial seam surfaced, ruled
  (replace model), and propagated into `decisions.md`, `test-suite.md`, `migration-01.md`.
- **2026-07-12** — Claude Code workflow stack completed: CLAUDE.md files, slash commands
  (/build-task, /log-decision, /wrap-up), plan-mode default, floor-verifier and doc-auditor
  subagents, format + suite-gate hooks, .env read-deny, and MCP go-live runbooks (`mcp-setup.md`).
  This repo is now self-sufficient; the Claude Chat Project is no longer load-bearing.
- **2026-07-12** — Full-tree doc-auditor sweep. Three schema-now gaps surfaced and ruled by Jack,
  then propagated into `migration-01.md`: `scoring_failed` column on `memories`, a schema-only
  `corrections` table (diegetic correction record; mechanism deferred), and removal of the stale
  `identity_components` pruning `[SETTLE-AT-BUILD]` tag. Dated ruling appended to `decisions.md`
  (also fixes the drift-anchor wording to "the corrected head"). Re-audit clean — migration 01 is
  unblocked with no known schema omissions.
- **2026-07-13** — DB + MCP floor stood up ahead of migration 01. Committed `docker-compose.yml`
  runs `pgvector/pgvector:pg16` as `longmem-pg` (secrets interpolated from the new gitignored
  `.env`, the connection-string source); pgvector 0.8.5 confirmed available (extension enable
  deferred to migration 01). Postgres MCP registered local-scope in restricted (read-only) mode and
  verified `✓ Connected`; floor-verifier given its `mcpServers: postgres` line + MCP-preference
  directive. **Runbook deviation:** `postgres-mcp`'s `pglast` dep has no Python 3.14 wheel and won't
  build on Windows, so the MCP runs in an isolated uv-managed Python 3.13 venv (project stays on
  3.14; recorded in `decisions.md`, and `mcp-setup.md` §1 wants a matching one-line note). Live
  in-session `/mcp` tool check still pending a Claude Code restart.

## Immediate queue

1. Migration 01 (`migration-01.md`) — schema in Postgres, verified by the floor-verifier subagent
   against the live DB + MCP floor (now in place). Six `[SETTLE-AT-BUILD]` forks await Jack's ruling.
2. Write path (NLP pass + Haiku render/importance + atomic insert).
3. Read path: dialogue-init top-k with IDs + scores.
4. CLI harness (vertical slice complete) + synthetic load driver alongside.
5. Unity project + reference scene — connect MCP for Unity first (`mcp-setup.md`).

*(Done 2026-07-13: connect the Postgres MCP + give floor-verifier its `mcpServers` line — see the
verified-floors table and session log.)*

## Open artifact queue (writing tasks against settled decisions — not decisions)

- Event-ingestion API contract: phase tag, the four optional context fields, client-timestamp
  semantics, idempotency, the explicit scene-boundary event, the diegetic-correction event
  referencing a target memory_id, pin/unpin, purge.
- Retrieval scoring function: relevance × recency(decay class) × importance_norm; pin exemption;
  normalization; slots for the future context term and per-call split-brain overrides.
- Reconstruction call spec: operator-structured prompt with gist as fixed constraint; determinism;
  batching shape.
- Reflection spec end-to-end.
- Gate threshold values + efficacy definitions wired to instrumentation.
- Unity client C# API surface: send event, open dialogue, directive callback, reputation read,
  reconstructing-signal hook, scene-boundary emission.
- Demo choreography: injected-timestamp time travel; decay + correction-override + gate-recollect
  beats now; the 60-day drift plot when reconstruction ships.
- README destructive-compression counter-example pick.

## Post-August ledger

Reflection pipeline mechanism (if not landed in August); reconstruction mechanism + drift budget +
remaining identity-conditioned-reconstruction suite scenarios; dissonance path + the diegetic suite
pair; encoding-context read term + habituation; split-brain topology with per-call weights and
re-run cost/latency instrumentation; reflection → parameter compiler; Unity Package Manager
packaging; docs final + public flip (Apache-2.0).

**Research track:** asymmetry ablation (on/off, judge-measured explanation-cause divergence); judged
drift / Bartlett-style evals; unified-thesis write-up (identity-conditioned reconstructive memory +
information-asymmetric cognition).

**Later / optional:** disclosure gate; full modulator suite for the parameter compiler;
faithful-vs-reconstructive dual read modes; the dormant-agent memory-injection overseer (next
project; wake trigger = context match); local-model packaging (note: a second embedding model
collides with the locked 1536 dimension).

## Repo conventions

Private GitHub; commit at least weekly; public flip is an end-of-project sprint. Secrets in `.env`
only. Always PowerShell, backslash paths.
