# longmem-npc — Status

**Last updated:** 2026-07-17
**Phase:** **the thesis mechanism is live** — *event in → memory stored → identity-conditioned
retelling out* runs end to end. Five floors stand verified: the migration-01 schema, write path v1
(`write-path.md`), read path v1 (`read-path.md`), CLI harness v1 (`cli-harness.md`), and
**reconstruction v1** (`reconstruction.md` — built & floor-verified 2026-07-17: the serving swap
with theta on the scene-frozen basis, the decay-band cache, drift-budgeted write-back, and the
scene-boundary identity recompile; all settle-shapes ruled in the dated `decisions.md` entry).
**One open decision owed before the demo ships:** the escalation hard-stop failure path re-rule
(build-phase stance, 2026-07-13). *(The `.env` DATABASE_URI deviation found during the
reconstruction build was resolved the same day — Jack pointed it back at `longmem`; no-arg
`db\migrate.py` verified a clean no-op again.)*
Next: **the authorial-correction endpoint** (immediate-queue item 1) — small target, the
correction-override demo beat; it inherits reconstruction's cache-eviction and re-anchoring
obligations.

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
| Migration 01 foundational schema — 9 tables, 7 CHECKs, HNSW cosine + GIN + one-live-head + FK indexes (`db\migrations\001_foundation.sql`, applied by `db\migrate.py`) | floor-verifier **pass** on live `longmem`: every done-when re-run (idempotent second run, CHECK rejection, server UUID defaults, smoke fixture) + `vector 0.8.5` enabled; DB left pristine (only `schema_migrations`) | 2026-07-13 |
| Write path v1 — ingest service seam (`app\ingest.py`) + thin FastAPI route (`app\api.py`, served via `python -m app.serve`) + real/deterministic-fake providers (`app\providers.py`) + NLP pass (`app\nlp.py`: spaCy lg + fastcoref + VADER + Warriner VAD) + atomic insert (`app\db.py`) | floor-verifier **pass** against the migration-01 floor: structural walker `tests\verify_write_path.py` re-run independently (35 assertions covering all 14 done-when criteria) on scratch `longmem_test`; `db\migrate.py` no-arg still a clean no-op on `longmem`; product `longmem` confirmed pristine via postgres MCP; independent spot-check of live head, span offsets, and degradation rows | 2026-07-13 |
| Read path v1 — retrieval service seam (`app\retrieval.py`) + shared decay math (`app\decay.py`) + thin `POST /v1/dialogue/init` route (`app\api.py`) + read-only candidate SQL (`app\db.py`) + wire models (`app\schemas.py`) + five knobs (`app\config.py`) | floor-verifier **pass** against the migration-01 + write-path floors: structural walker `tests\verify_read_path.py` re-run independently (34 assertions, done-when 1–11) on scratch `longmem_test`; `tests\verify_write_path.py` re-run (35 assertions — shared files touched, floor intact); `db\migrate.py` no-arg still a clean no-op on `longmem`; `longmem` confirmed pristine; independent read-only SQL spot-checks (live head, NULL-embedding row, one-live-head index); plus a live `python -m app.serve` route session with byte-identical repeated reads | 2026-07-14 |
| CLI harness v1 — dialogue-turn seam (`app\dialogue.py`: retrieval → prompt assembly → single dialogue call → directive validation → atomic in-place reputation apply) + shared session-runner core (`app\session.py`) + REPL (`python -m app.cli`, `app\cli.py`) + synthetic load driver (`python -m app.load_driver`, `app\load_driver.py`) + dialogue provider triad (`app\providers.py`) + turn wire models (`app\schemas.py`) + reputation SQL (`app\db.py`) + dialogue role/reputation/pricing config (`app\config.py`) | floor-verifier **pass** against the migration-01 + write-path + read-path floors: structural walker `tests\verify_cli_harness.py` re-run independently (36 assertions, every done-when criterion) on scratch `longmem_test`; both prior walkers re-run clean (35/35, 34/34 — shared files touched, floors intact); `db\migrate.py` no-arg still a clean no-op on `longmem` (schema frozen, `001` the only migration); `longmem` confirmed pristine **via the postgres MCP — the verifier's `mcp__postgres__*` tools worked this dispatch, resolving the 2026-07-14 flag**; an independent standalone load-driver run (offline, keyless); plus a live piped REPL session (observe → dialogue turns with debug view → scene-boundary snapshot refresh) | 2026-07-15 |
| Reconstruction v1 — serving-stage engine (`app\reconstruction.py`: theta partition at the scene-frozen basis → decay-band cache → batched retelling call → drift-budgeted atomic write-back → serve-only-persisted-text) + serving swap (`app\retrieval.py`, retrieval/scoring untouched) + identity-document plumbing (`app\identity.py` + scene-boundary recompile in `app\ingest.py` + caller-frozen scene state in `app\session.py`) + reconstruction provider triad and the **locality-sensitive fake embedding** (`app\providers.py`) + reconstruction SQL (`app\db.py`) + wire/instrumentation deltas (`app\schemas.py`) + knobs/role/pricing (`app\config.py`) + debug/aggregate surfacing (`app\cli.py`, `app\load_driver.py`) + 422 mapping (`app\api.py`) | floor-verifier **pass** against all four prior floors: structural walker `tests\verify_reconstruction.py` re-run independently (41 assertions, every done-when criterion) on fresh scratch `longmem_test`; all three prior walkers re-run clean (35/35, 34/34, 36/36 — the read-side pair pin `reconstruction_theta = 0` in fixture configs, assertion bodies untouched, verified against git); schema frozen (`001` the only migration; migrate **`--database-uri` on `/longmem`** → "Up to date, 0 pending" — no-arg blocked by the `.env` sandbox pointer, flagged); `longmem` confirmed pristine **via the postgres MCP (tools worked this dispatch)**; independent code spot-checks (atomic write-back, derivable anchor, scene-basis binding, retrieval byte-identical to HEAD); plus a live piped REPL drift beat (verbatim → 46-day jump → reconstructed write-back → call-free cache hit) and a standalone load-driver run with the reconstruction latency/cost rows | 2026-07-17 |

## Open questions needing Jack's ruling

- **Escalation failure path for production (owed before the demo publishes).** The v1 write path
  hard-stops a write when the gist-escalation call fails twice (fail-loud, build-phase tuning
  stance, ruled 2026-07-13). The production/demo behavior — hard-stop vs. some soft degradation —
  must be re-ruled before the demo ships. Not blocking current work. **Now the sole open
  question** — the reconstruction flagged shapes were all confirmed 2026-07-17 (see the
  "Reconstruction flagged-shapes confirmations" entry in `decisions.md`).

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
- **2026-07-13** — **Migration 01 built, verified, and committed.** Seven `[SETTLE-AT-BUILD]` forks
  ruled by Jack (see the dated `decisions.md` entry): `diagnosticity_goal` text; `decay_class`
  free-text + config map with a new `decay_class_unknown` degradation flag; `affect` as three columns
  (valence/arousal/jsonb); gist child table; `identity_relevant` boolean; HNSW cosine; Python runner
  with an atomic apply-and-record `schema_migrations` ledger. `db\migrations\001_foundation.sql` +
  `db\migrate.py` + `db\smoke_test.py` written; `requirements.txt` pins `psycopg[binary]==3.3.4`
  (global 3.14). floor-verifier returned **pass** on the live DB. **Flag:** floor-verifier couldn't
  call the postgres MCP tools (fell back to `psql`); its `mcpServers` directive isn't yet effective —
  revisit before the write path. **(Resolved 2026-07-13 — see the next entry.)**
- **2026-07-13** — **Floor-verifier MCP access fixed and verified.** Root cause was the verifier's
  explicit `tools: Read, Grep, Glob, Bash` allowlist, which filters out every `mcp__postgres__*` tool
  (the `mcpServers: postgres` line authorizes the server connection but does not override the
  allowlist — the sub-agents docs use that exact `tools` line as their canonical "can't use any MCP
  tools" example). Added the `mcp__postgres` pattern to the allowlist in
  `.claude\agents\floor-verifier.md`. Agent definitions load at Claude Code startup, so the fix took
  effect only after a restart; a read-only probe then confirmed the floor-verifier can call
  `mcp__postgres__execute_sql` (`SELECT 1` → ok). Verification is now MCP-driven as intended.
- **2026-07-13** — **Write-path v1 build target specced** (`write-path.md`). Consolidates
  architecture §4–§5 into a build spec over the frozen migration-01 schema (no new migration). Jack
  ruled three scope forks (dated entry in `decisions.md`): surface = one ingest service (the sole
  instrumentation seam) with a thin FastAPI route and a structured `IngestResult` (IDs + scores);
  v1 events = observe + scene-boundary (accept+instrument only) + pin/unpin, with correction/purge
  deferred; models = per-role provider interfaces with a real impl + a deterministic fake. doc-auditor
  run clean after fixing one unsatisfiable done-when (byte-identical two-caller payload →
  route-is-pass-through) and three schema-alignment nits. Remaining physical shapes tagged
  `[SETTLE-AT-BUILD]` for the build.
- **2026-07-13** — **Write path v1 built, verified, and committed.** Jack ruled the four major
  build forks up front (render seam confirmed; embedding failure → NULL embedding; NLP stack =
  spaCy lg + fastcoref + VADER + **Warriner VAD** — NRC-VAD failed the Apache-2.0 license gate;
  full five-trigger escalation with fail-loud hard-stop as a **build-phase stance to re-rule
  before the demo**); minor shapes approved with the plan (dated `decisions.md` entry has all of
  it). New: `app\` (config, schemas, providers, nlp, db, ingest, api, serve),
  `data\lexicons\warriner_2013_vad.csv` (CC-BY 4.0, attributed), `tests\verify_write_path.py`
  (35-assertion structural walker), `db\migrate.py --database-uri` flag (floor re-verified).
  Environment learnings recorded in `decisions.md`: `transformers<5` pin for fastcoref;
  `en_core_web_sm` needed by fastcoref internally; spaCy model installs must use pip wheel URLs
  (spaCy's downloader hits uv and dies outside a venv); psycopg async needs a SelectorEventLoop on
  Windows → serve via `python -m app.serve`. Verification ran on scratch DB `longmem_test`
  (created/migrated/dropped around the walker); floor-verifier **pass** — walker re-run
  independently, `longmem` confirmed pristine via the postgres MCP, plus an independent
  spot-check. Route pass-through proven twice: ASGITransport JSON-equality in the walker and a
  live `python -m app.serve` HTTP session (observe + pin + scene-boundary).
- **2026-07-13** — **Full-project audit (build paused at Jack's request) + remediation.** Three
  lanes: a doc-auditor full-tree sweep, a code-vs-decisions review of the write path, and
  operational/toolchain checks. **Code verdict: clean** — the implementation matches every dated
  ruling; installed deps match the `requirements.txt` pins; live `longmem` re-confirmed pristine
  (9 tables + ledger, pgvector 0.8.5, product tables empty; the container had been down only
  because Docker Desktop wasn't started). **Fixed:** (1) the ruff format hook had been silently
  dormant since it was written — ruff is module-installed, not on PATH — `format-on-edit.ps1` now
  falls back to `python -m ruff`; proven live, and the accumulated drift was normalized
  (`python -m ruff format .`, 7 files, formatting only, imports re-verified). (2) Eleven doc
  findings (4 contradictions, 7 unpropagated rulings) + 2 re-audit residuals propagated:
  `write-path.md` (BUILT banner, settle-tag/flag ruling annotations, five triggers, hard-stop
  ladder row + principles exception, IngestResult `embedding_failed`/escalation fields, the four
  build-ruled done-when bullets), `architecture.md` (five triggers, hard-stop exception in §2,
  ruled NLP stack, escalation model role), `CLAUDE.md` (escalation in the role list),
  `mcp-setup.md` (uv `--python 3.13` pglast note — closes the flagged follow-up; floor-verifier
  runbook now prescribes the `tools: mcp__postgres` allowlist, the proven fix), `test-suite.md`
  (unknown-decay-class, embedding-failure, and hard-stop degradation cases), and a
  superseded-in-part note on the 2026-07-12 decay/gist entry in `decisions.md` (the register
  header's own convention). (3) `app\config.py`'s unused `nlp_confidence_threshold` comment now
  reads RESERVED (not consulted in v1 — no confidence source exists). **No floor changed; no new
  decisions ruled** — the escalation failure-path re-rule remains the open question. Doc-auditor
  re-audit clean apart from the two residuals, which were fixed and grep-verified.
- **2026-07-14** — **Full pre/post-demo scope audit + re-slating ruling.** A read-path spec attempt
  was aborted mid-scoping at Jack's request (its tentative scoping answers discarded, nothing
  recorded). The audit found the demo as slated demonstrated the record — storage, decay,
  correction-override, gate-recollect — but not the thesis: reconstruction, the claim-axis
  carrier, sat post-August, and the 60-day drift plot beat was contingent. **Jack ruled:
  reconstruction moves pre-demo** (dated entry in `decisions.md`, superseding-in-part *Schema
  now, mechanism later*), with the schedule cost explicitly flagged and accepted. Four gap
  slatings ruled with it: authorial-correction endpoint pre-demo (after reconstruction);
  scene-boundary consumers split (reputation snapshot → dialogue turn; identity recompile →
  reconstruction, seed-prose-only document pre-demo; prompt caching → post-August); purge →
  post-August, before the public flip; reflection's August hedge resolved to explicitly
  post-August. Immediate queue re-slated; `architecture.md` §2/§7 markers updated. Doc-auditor
  re-audit: **no contradictions**; two residual annotations for the scene-boundary consumer split
  (`write-path.md`, `architecture.md` §6) fixed and grep-verified. Docs only — no code, no floors
  changed.
- **2026-07-14** — **Read-path v1 build target specced** (`read-path.md`). Consolidates
  architecture §4.2 + §6 (and the artifact queue's retrieval scoring function) into a build spec
  over the frozen migration-01 schema (no new migration). Surface was pre-fixed by the re-slating
  ruling (retrieval-only; the Sonnet dialogue call rides with the CLI harness); Jack ruled two
  scope forks at spec time (dated entry in `decisions.md`): query input = **text + reserved
  context** (`query_text` embedded as-is; location/entities/event_time accepted-not-consumed —
  slots for the post-August encoding-context term; server-side composition rejected as
  double-counting + a hidden hardcoded template), and v1 serving = **verbatim-only**
  (`read_mode = verbatim` on every item; decay math lands now as the recency score component so
  Set B asserts through scores; theta/cache/`reconstructed` land with reconstruction, which swaps
  the serving stage only — retrieval and scoring untouched, pre-warm hooks this seam). Remaining
  physical shapes tagged `[SETTLE-AT-BUILD]` for the build (wire shape, relevance mapping +
  over-fetch, recency knobs, importance_norm method, k default, `as_of` override,
  `weight_overrides` shape, empty-store behavior, embedding-failure fallback). Doc-auditor run:
  one wording contradiction — the reserved-slot mirror overstated (three of four context stamps);
  Jack ruled **affect deliberately not reserved** (query-side shape undesigned; it arrives with
  the encoding-context term), exclusion now stated in the spec — plus three residuals fixed
  (architecture §6 spec-pending marker, Set B score-surface note, empty-store settle-tag);
  grep-verified.
- **2026-07-14** — **Read path v1 built, verified, and committed.** Jack ruled the two genuine
  settle-forks at plan approval (`as_of` **adopted**; query-embedding failure → **fail-quiet
  fallback** with per-item `relevance = null`) and one build-surfaced conflict
  (**importance_norm = clamp + floor, superseding the spec's min-max suggestion** — min-max
  bounds over live rows would let an invalidated extreme row move *other* items' scores, breaking
  Set B's decay-vs-invalidation separation); the remaining shapes were approved with the plan
  (dated "Read-path build rulings" entry in `decisions.md` records all nine + the
  `(−score, memory_id)` determinism sort). New: `app\retrieval.py` (the retrieval seam),
  `app\decay.py` (THE decay implementation — the reconstruction theta check imports it at
  item 3), read wire models in `app\schemas.py`, read-only candidate SQL in `app\db.py`,
  `POST /v1/dialogue/init` in `app\api.py`, five knobs in `app\config.py`,
  `tests\verify_read_path.py` (34-assertion structural walker), and the `as_of` mechanic added to
  `tests\CLAUDE.md`'s time-travel line. Verification ran on scratch `longmem_test`
  (created/migrated/dropped around the walkers); `tests\verify_write_path.py` re-run clean
  (35/35 — shared files touched, floor intact); a live `python -m app.serve` session returned
  byte-identical items across repeated reads. floor-verifier **pass** — both walkers re-run
  independently, `longmem` confirmed pristine, independent read-only SQL spot-checks. **Flag:**
  the floor-verifier dispatch again had no `mcp__postgres__*` tools (it fell back to equivalent
  read-only `docker exec psql` checks) — the 2026-07-13 allowlist fix did not hold for this
  dispatch; revisit before the next verification. Docs propagated: BUILT banner + inline ruling
  annotations in `read-path.md`, architecture §6 built marker, dated `decisions.md` entry.
- **2026-07-14** — **CLI-harness v1 build target specced** (`cli-harness.md`). Consolidates
  architecture §9 (behavior output & turn topology) + §11 (instrumentation & load driver) into a
  build spec over the frozen migration-01 schema (no new migration). The surface was pre-fixed: the
  harness composes the two built seams (ingest, retrieval) in-process via one `run_dialogue_turn`
  seam + the single Sonnet call; no HTTP route (that rides with Unity). Jack ruled two scope forks
  at spec time (dated entry in `decisions.md`): **reputation delta = persist in-place** (UPDATE
  `agents.reputation` with clamp + sensitivity, client override wins; scene-start snapshot frozen in
  the prompt prefix until the next boundary — an in-place UPDATE of an agent-row runtime scalar, the
  same class as the existing pin-flag toggle (`set_pinned`) and likewise outside the memory-content
  non-destructive invariant;
  compute-and-return-only and non-destructive-history both rejected), and **drive surface = an
  interactive REPL over a shared session-runner core** the synthetic load driver reuses (scripted-
  only and divergent-paths rejected). The single-Sonnet reconciliation is baked in (one call carries
  prose + action directive + reputation delta; §9's "Haiku call emits a delta" is the post-August
  split-brain, not this slice). Remaining physical shapes tagged `[SETTLE-AT-BUILD]` for the build
  (`LONGMEM_MODEL_DIALOGUE` name, structured-output schema, reputation apply shape, action-vocabulary
  source, prompt-assembly block, never-blank fallback, CLI meta-command surface, load-driver shape,
  wire-model form). Docs only — no code, no floors changed. Doc-auditor sweep: **no contradictions**;
  two fixes propagated + grep-verified — the "first in-place UPDATE" wording (the `set_pinned` pin
  toggle is precedent for a runtime-scalar UPDATE) and a stale queue number (reconstruction feeds
  immediate-queue item 2, not 3), the latter also renumbered in `read-path.md`'s two reconstruction
  references at Jack's request.
- **2026-07-15** — **CLI harness v1 built, verified, and committed — the vertical slice is
  complete.** Jack ruled two forks via explicit questions at plan approval (action-vocabulary
  source = **per-call field → `agents.config` fallback**, neither → directives drop soft with
  reason, no hardcoded default vocabulary; cost units = **tokens unconditionally, USD only via
  optional `LONGMEM_PRICE_*` env vars** — pricing never hardcoded, a plan-raised choice implicit in
  the spec's instrumentation contract); the spec's remaining nine settle-tags were approved with
  the plan (dated "CLI-harness build rulings" entry in `decisions.md`; count annotation added by
  the 2026-07-16 audit).
  New: `app\dialogue.py` (the `run_dialogue_turn` seam: retrieval → labeled-block prompt assembly →
  single dialogue call → vocabulary validation → atomic clamped in-place `agents.reputation`
  UPDATE), `app\session.py` (session-runner core owning frozen-snapshot scene state — the
  scene-boundary reputation-snapshot consumer landed), `app\cli.py` (REPL,
  `python -m app.cli --agent <uuid> [--debug]`), `app\load_driver.py` (deterministic seeded
  generator or JSON script; emits §11's latency p50/p95 + itemized per-100-turn cost table),
  `tests\verify_cli_harness.py` (36-assertion structural walker), the dialogue provider triad
  (streaming real + deterministic fake + failure-injection fakes), turn wire models, reputation
  SQL, and the dialogue-role/reputation/pricing config. The CLAUDE.md invariant clarification for
  agent-row runtime scalars landed with the UPDATE, as ruled. **Build-surfaced interpretation
  flagged for Jack:** a client `reputation_delta_override` still applies on the never-blank
  degraded path (client-authoritative; the ladder's zero delta is the no-override default).
  Verification ran on scratch `longmem_test` (created/migrated/dropped around the walkers); both
  prior walkers re-run clean (35/35, 34/34); live piped REPL session + standalone load-driver run;
  floor-verifier **pass** — and its `mcp__postgres__*` tools **worked this dispatch** (the
  2026-07-14 MCP-allowlist flag resolved). Environment learnings in `decisions.md`: Windows decodes
  piped stdin with the ANSI codepage (PowerShell here-string pipes deliver a mojibake UTF-8 BOM) —
  the REPL reconfigures non-tty stdin to `utf-8-sig`. Docs propagated: BUILT banner + inline ruling
  annotations in `cli-harness.md`, architecture §6/§9/§11 built markers, queue renumbered
  (reconstruction → item 1) with refs updated in `read-path.md`/`cli-harness.md` — including
  read-path refs already stale from the prior renumber. **Known nit left in place:** stale code
  comments citing reconstruction as "item 3" — the 2026-07-16 audit found **four** such files
  (`app\api.py`, `app\decay.py`, `app\retrieval.py`, `app\schemas.py`), not the two named here
  originally; comment-only, left untouched at build time to keep the floors byte-identical.
  *(Fixed 2026-07-16 by audit ruling; walkers re-run — see that entry.)*
- **2026-07-16** — **Full-project audit + remediation (at Jack's request).** Three lanes: a
  doc-auditor full-tree sweep, a code-vs-rulings review, and operational/toolchain checks.
  **Code verdict: clean** — the only write surfaces are the atomic observe insert and the two
  ruled runtime-scalar UPDATEs; the auditor's independent spot-checks (schema SQL vs.
  migration-01.md, config knobs vs. rulings, the reputation-apply SQL shape, the dialogue seam
  vs. its rulings) all passed. **Operations: clean** — container healthy, migrate no-arg a no-op,
  `longmem` pristine, all `requirements.txt` pins match installed versions, ruff hook live,
  suite-gate hook correctly dormant until the pytest suite lands. **Docs: six findings, all in
  the 2026-07-15 wrap-up prose; Jack ruled on all of them** (dated "Full-project audit rulings"
  entry in `decisions.md`): five mechanical fixes applied and grep-verified (the missed "Item 3"
  renumber ref in `read-path.md`; the `write-path.md` scene-boundary landing annotation; the
  settle-count correction annotated onto the 2026-07-15 decisions entry; the CLAUDE.md
  "agent-row" → "runtime scalars" rewording; this log's nit sentence corrected to four files);
  the **override-on-degraded-path interpretation CONFIRMED as built** (flag closed, no code
  change); and the four stale "item 3" code comments **fixed** with all three walkers re-run on
  fresh scratch (35/35, 34/34, 36/36 — floors intact, comment-only diffs). Observations carried
  without ruling: `httpx` unpinned but used directly by two walkers; `max_tokens=1024` hardcoded
  in the three real providers (write-path-era pattern). Also this session: a CLI-harness usage
  guide was written up for Jack (operator prerequisites incl. the no-agent-provisioning-surface
  gap, the turn pipeline, meta-commands, reputation semantics, fake/real modes, load driver).
- **2026-07-17** — **Reconstruction v1 build target specced** (`reconstruction.md`). Consolidates
  architecture §7 (+ §4.2/§4.3/§6) and the 2026-07-14 re-slating scope into a build spec over the
  frozen migration-01 schema (no new migration — `reconstruction_cache`, `identity_documents`, and
  the `write_cause` enum are already live); it swaps the read path's reserved serving stage only.
  Jack ruled three scope forks at spec time (dated "Reconstruction spec scope rulings" entry in
  `decisions.md`): reconstructor input **includes the current live head** ("how you currently tell
  it" — retellings compound, the drift budget gets real work); the cache key's version component
  **composes `identity_version` with a quantized, scene-frozen decay band** (the pre-demo drift
  driver — spec-surfaced tension: a seed-only identity is static, so the plain key would
  reconstruct each memory exactly once and flatten the 60-day beat; the band both keys the cache
  and sets the thinning level); and identity-document plumbing is **hybrid, reputation-style**
  (scene-boundary handler recompiles server-side and returns `identity_version`; the caller
  freezes it as scene state and passes it per request — the handler's first real server-side
  consumer). Two derived design lines stated in the spec: **serve only persisted text** and **the
  dialogue-init route becomes a writing endpoint**. Remaining physical shapes tagged
  `[SETTLE-AT-BUILD]` for the build (theta knob, band quantum + key composition, thinning
  function, prompt + batched output schema, retry policy, drift metric + threshold, write-back
  `valid_at`,
  refusal caching, scene-state request fields, scene-boundary response shape, hash/NULL-seed/
  unknown-version shapes, wire deltas, walker shape). Propagated: architecture §7 input/cache/
  marker + §4.3/§6 plumbing notes; `test-suite.md` Set C cache-hit clause refined to "stable
  identity + same band." Doc-auditor sweep: one contradiction (the `migration-01.md` cache-column
  line still read pure-content-hash — annotated with the ruling) + five propagation residuals
  fixed and grep-verified (`read-path.md` serving-boundary key note, the register's annotation
  convention on the 2026-07-14 re-slating entry, `write-path.md` scene-boundary specced marker,
  this log's settle-tag list + the phase header's stale "nine" count). **Known nit left in
  place:** `app\retrieval.py`'s module comment still sketches the plain
  `(memory_id, identity_version)` cache key — comment-only in a floor-verified file, and the
  reconstruction build rewrites that comment when it swaps the serving stage; left untouched to
  keep this session docs-only. Docs only — no code, no floors changed.
- **2026-07-17** — **Reconstruction v1 built, verified, and committed — the thesis mechanism is
  live.** Jack ruled two forks via explicit questions at plan approval (**fake-mode drift =
  locality-sensitive fake embedding** — the drift budget surfaced that the shake_256 hash fake
  made any two texts ~orthogonal, so every fake-mode write-back would have been refused;
  `FakeEmbeddingProvider` is now trigram-bucket + L2-normalized; and **`drift_budget_threshold`
  default = 0.35** cosine distance); the spec's remaining settle-shapes were approved with the
  plan (dated "Reconstruction build rulings" entry in `decisions.md` records all of them + three
  build-surfaced shapes flagged for confirmation). New: `app\reconstruction.py` (the
  serving-stage engine: theta/band/thinning bound to the scene-frozen basis; batched retelling
  call; drift check embedding candidate + anchor at check time; atomic supersede+insert+cache
  transaction; serve-only-persisted-text), `app\identity.py` (seed-verbatim render + sha256
  version + upsert), `tests\verify_reconstruction.py` (41-assertion walker incl. the band-crossing
  and identity-bump drift drivers), the reconstruction provider triad + failure/drifting fakes,
  reconstruction SQL (identity docs, cache batch fetch, retelling sources + derivable anchor,
  write-back), wire deltas (`read_mode` three-state real; scene-state request fields;
  reconstruction counters), scene-boundary recompile (the handler's first server-side consumer),
  session-runner frozen `identity_version` + `scene_started_at`, CLI debug + load-driver
  aggregate rows, the 422 unknown-version mapping, and the `LONGMEM_MODEL_RECONSTRUCTION` role +
  three knobs. The prior read-side walkers pin `reconstruction_theta = 0` in fixture configs
  (assertion bodies untouched — the v1 serving contract holds with the stage knob-disabled;
  flagged). The 2026-07-17 known-nit (stale plain-key comment in `app\retrieval.py`) closed with
  the rewritten module docstring. Verification: all four walkers on fresh scratch (41/41, 35/35,
  34/34, 36/36); live piped REPL drift beat (verbatim → 46-day `:as-of` jump + `:scene` →
  reconstructed with write-back → call-free cache hit); standalone load-driver run; floor-verifier
  **pass** with working postgres MCP tools and independent code spot-checks. **Environment
  deviation found and flagged (not fixed):** `.env`'s DATABASE_URI names a nonexistent
  `longmem_sandbox` DB — no-arg migrate can't connect; the no-op criterion was verified against
  `/longmem` explicitly. *(Resolved the same day — see the wrap-up entry below.)*
- **2026-07-17** — **Wrap-up: the `.env` deviation is closed.** Jack restored `DATABASE_URI` to
  `longmem`; no-arg `db\migrate.py` re-verified as a clean no-op ("Up to date, 0 pending") — the
  schema-frozen criterion reads exactly as recorded for every prior floor again. The two
  build-surfaced reconstruction shapes (prior walkers' `reconstruction_theta = 0` pin;
  blind-check refusals not cached) remain flagged for confirmation in open questions.
- **2026-07-17** — **Flagged-shapes confirmation session (docs only).** Jack walked the three
  open reconstruction flags and confirmed all three as built/written (dated "Reconstruction
  flagged-shapes confirmations" entry in `decisions.md`): the prior walkers' fixture-only
  `reconstruction_theta = 0` pin (confirmed after correcting a misread — reconstruction is
  **production-active** at default theta 0.5 and has its own 41-assertion walker; the pin exists
  only in the two older walkers' fake NPCs, preserving single-cause layer isolation); blind-check
  refusals staying uncached (a transient embedding outage never pins a key); and
  pin-after-reconstruction `read_mode = "verbatim"` kept as written ("verbatim" is the
  serving-stage claim; `pinned` rides in every payload — observation closed, no spec amendment).
  No code, no floors touched. **The escalation hard-stop failure-path re-rule is now the sole
  open question.**

## Immediate queue

1. Authorial-correction endpoint (small target; the correction-override demo beat; inherits
   reconstruction's cache-eviction + re-anchoring obligations, both stated in
   `reconstruction.md`).
2. Mid-dialogue gate + threshold values, efficacy definitions, per-signal fire logging (the
   block-with-"reconstructing"-signal miss path binds here).
3. Test-suite scoped session (Sets A-authorial, B, C + degradation cases now runnable).
4. Unity project + reference scene — connect MCP for Unity first (`mcp-setup.md`) — then demo
   choreography incl. the 60-day drift beat (its mechanics — `:as-of` jumps + scene boundaries +
   band crossings — are live in the REPL).
5. Before the demo ships: re-rule the escalation failure path (see open questions) and pick a
   real-provider smoke moment (one live observe + one live dialogue turn + one live
   reconstruction with keys) ahead of demo choreography.

*(Done 2026-07-17: **Reconstruction v1** — the thesis mechanism is live; see the verified-floors
table and session log. Done 2026-07-15: **CLI harness v1 + synthetic load driver** — the vertical
slice completed. Done 2026-07-14: **Read path v1**. Done 2026-07-13: **Write path v1**; earlier
same day: **Migration 01 foundational schema**; connect the Postgres MCP + floor-verifier MCP
access.)*

## Open artifact queue (writing tasks against settled decisions — not decisions)

- Event-ingestion API contract — **v1 subset specced in `write-path.md` and now BUILT** (observe +
  scene-boundary + pin/unpin; phase tag and event_id accepted without a schema home; idempotency
  accepted-not-enforced). Still to spec/build: the diegetic-correction event (references a target
  memory_id; mechanism post-August) and purge (post-August, before the public flip — ruled
  2026-07-14). Scene-boundary's consumers were slated 2026-07-14: reputation snapshot → the
  dialogue turn (**landed 2026-07-15** — the session-runner re-reads `agents.reputation` at each
  boundary), identity recompile → reconstruction (**landed 2026-07-17** — the handler recompiles
  server-side and returns `identity_version`), prompt-head rebuild → post-August.
- Retrieval scoring function: relevance × recency(decay class) × importance_norm; pin exemption;
  normalization; slots for the future context term and per-call split-brain overrides. —
  **Consolidated into `read-path.md` 2026-07-14 and now BUILT** (shapes ruled at build; dated
  `decisions.md` entry).
- Reconstruction call spec: operator-structured prompt with gist as fixed constraint; determinism;
  batching shape. — **Consolidated into `reconstruction.md` 2026-07-17 and now BUILT** (built &
  floor-verified the same day; shapes ruled at build; dated `decisions.md` entry).
- Reflection spec end-to-end (mechanism explicitly post-August — ruled 2026-07-14).
- Gate threshold values + efficacy definitions wired to instrumentation.
- Unity client C# API surface: send event, open dialogue, directive callback, reputation read,
  reconstructing-signal hook, scene-boundary emission.
- Demo choreography: injected-timestamp time travel; decay + correction-override + gate-recollect
  beats; the 60-day drift plot — a planned beat since the 2026-07-14 re-slating (reconstruction is
  pre-demo).
- README destructive-compression counter-example pick.

## Post-August ledger

Reflection pipeline mechanism (explicitly post-August — hedge resolved 2026-07-14; the pre-demo
identity document is seed-prose-only); dissonance path + the diegetic suite pair; the purge
endpoint (before the public flip — ruled 2026-07-14); prompt caching / prompt-head rebuild
(revisit only if demo latency demands — ruled 2026-07-14); encoding-context read term +
habituation; split-brain topology with per-call weights and re-run cost/latency instrumentation;
reflection → parameter compiler; Unity Package Manager packaging; docs final + public flip
(Apache-2.0). *(Reconstruction — mechanism, drift budget, Set C scenarios — moved off this ledger
into the immediate queue by the 2026-07-14 re-slating ruling.)*

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
