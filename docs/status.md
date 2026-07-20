# longmem-npc — Status

**Last updated:** 2026-07-20
**Phase:** **the suite is green and its gate hook is live** — structural pytest suite v1
built & floor-verified 2026-07-20 (38 scenarios in `tests\test_*.py`: Sets A–D +
degradation; `docs\test-suite.md` was already the spec, so the session went straight to a
scoped build). **The suite-gate Stop hook is active for the first time since it was
written (2026-07-12):** every turn-end now runs the `-m "not nlp"` subset (31 scenarios,
~14 s — ruled 2026-07-20; the 7 `nlp`-marked scenarios call the write pass at the service
level, pay the lazy spaCy+fastcoref load, and run on demand + at floor verification),
Postgres unreachable ⇒ loud clean skip with a green exit, and the suite is CI-ready
(offline, keyless, self-managed scratch `longmem_suite`) with the CI workflow sequenced
later. `app\`, `db\`, and all seven walkers are byte-untouched — the eight prior floors
stand by construction; **nine floors now stand verified** (see the table). Jack ruled
three build shapes via explicit questions (hook subset; skip-clean on unreachable;
CI-ready-now, workflow later). **One open decision owed before the demo ships:** the
escalation hard-stop failure path re-rule (build-phase stance, 2026-07-13) — the suite
asserts the current stance and flags itself in that test's docstring.
Next: **Unity project + reference scene** (immediate-queue item 1 after the renumber).

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
| Authorial-correction v1 — memory-scoped operator verb (`POST /v1/memories/{id}/correction` in `app\api.py` → `IngestService.correct` in `app\ingest.py` → one-transaction `apply_authorial_correction` in `app\db.py`: predicate supersede + optional `expected_detail_id` compare-and-swap + corrected `authorial_correction` head at t_c + cache eviction with count) + the constraint-follows-anchor reconstruction delta (`app\reconstruction.py` `build_reconstruction_item`, anchor-cause-aware; `db.ReconstructionSource.anchor_cause`) + wire models (`app\schemas.py`) + REPL surface (`app\session.py` `runner.correct`, `app\cli.py` `:correct`) | floor-verifier **pass** against all five prior floors (reconstruction deliberately re-opened by the constraint-follows-anchor ruling, re-verified): structural walker `tests\verify_authorial_correction.py` re-run independently (31 assertions, every done-when criterion incl. the re-ruled stored-coherence time-travel criterion) on fresh scratch `longmem_test`; all four prior walkers re-run clean (42/42 — grown +1 by the corrected-item assertion, addition only; 36/36; 34/34; 35/35); `db\migrate.py` no-arg a clean no-op on `longmem` (no migration needed, as specced); `longmem` confirmed pristine via the postgres MCP; independent code spot-checks (transaction + CAS rollback, eviction inside the transaction, byte-verbatim no-model path, retrieval/scoring untouched vs HEAD); plus a live piped REPL correction-override beat (read verbatim → `:correct` head swap → corrected read, one scene) | 2026-07-18 |
| Reconstruction v1 — serving-stage engine (`app\reconstruction.py`: theta partition at the scene-frozen basis → decay-band cache → batched retelling call → drift-budgeted atomic write-back → serve-only-persisted-text) + serving swap (`app\retrieval.py`, retrieval/scoring untouched) + identity-document plumbing (`app\identity.py` + scene-boundary recompile in `app\ingest.py` + caller-frozen scene state in `app\session.py`) + reconstruction provider triad and the **locality-sensitive fake embedding** (`app\providers.py`) + reconstruction SQL (`app\db.py`) + wire/instrumentation deltas (`app\schemas.py`) + knobs/role/pricing (`app\config.py`) + debug/aggregate surfacing (`app\cli.py`, `app\load_driver.py`) + 422 mapping (`app\api.py`) | floor-verifier **pass** against all four prior floors: structural walker `tests\verify_reconstruction.py` re-run independently (41 assertions, every done-when criterion) on fresh scratch `longmem_test`; all three prior walkers re-run clean (35/35, 34/34, 36/36 — the read-side pair pin `reconstruction_theta = 0` in fixture configs, assertion bodies untouched, verified against git); schema frozen (`001` the only migration; migrate **`--database-uri` on `/longmem`** → "Up to date, 0 pending" — no-arg blocked by the `.env` sandbox pointer, flagged); `longmem` confirmed pristine **via the postgres MCP (tools worked this dispatch)**; independent code spot-checks (atomic write-back, derivable anchor, scene-basis binding, retrieval byte-identical to HEAD); plus a live piped REPL drift beat (verbatim → 46-day jump → reconstructed write-back → call-free cache hit) and a standalone load-driver run with the reconstruction latency/cost rows | 2026-07-17 |
| Fact-level correction v1 — **migration 002** (`db\migrations\002_fact_versions.sql`: `memory_fact_versions` fact chain + guarded backfill + one-live-head partial unique + **partial HNSW** over live heads + `memories_embedding_hnsw` **dropped**, ruled) + the fact-following verb (`app\db.py` `apply_authorial_correction` grown: fact supersede + insert in the same transaction; `app\ingest.py` embed-before-transaction + `CorrectionEmbedFailedError`; `app\api.py` 502) + the **freeze ruling** (`insert_observation` mints the `original` fact head — the sole vector home; `memories.embedding` no longer written; the embed-degradation signal moved to the live fact head) + the vector probe on the live fact head (`fetch_vector_candidates`) + wire deltas (`CorrectionResult` widened, `IngestResult.fact_version_id`) + REPL surfacing (`app\cli.py`) | floor-verifier **pass** against all six prior floors (read-path + write-path deliberately re-opened, re-verified): structural walker `tests\verify_fact_correction.py` re-run independently (32 assertions, every done-when criterion incl. db-layer distance-0 retrieval-follows-the-fix, the backfill guard via a legacy-shaped row, and all-or-nothing embed failure) on fresh scratch `longmem_test`; all five prior walkers re-run clean (38/38 — grown 35 → 38 incl. the one ruling-driven modification, the embed-signal query moved to the fact head; 36/36 read, 34 → 36 addition only; 33/33 authorial, 31 → 33 addition only; 42/42 reconstruction and 36/36 CLI harness **byte-untouched — the no-reconstruction-delta proof**, `app\retrieval.py`/`app\reconstruction.py` byte-identical to HEAD); migration 002 applied to `longmem`, no-arg migrate → **"Up to date: 2 applied, 0 pending"** (the criterion's new wording); `longmem` confirmed pristine via the postgres MCP (all product tables 0 rows, ledger = 001+002, old index absent, three fact indexes present); independent code spot-checks (one transaction with the embed outside it, CAS + broken-store rollbacks, sole DELETE still cache eviction, degraded path byte-identical); plus a live piped REPL beat: `:correct` prints both head swaps + embed timing, and the same query's relevance moved 0.4686 → 0.5637 across the correction | 2026-07-18 |

| Mid-dialogue gate v1 — **migration 003** (`db\migrations\003_fact_entities.sql`: `memory_fact_versions.entities` + guarded backfill + partial GIN on live fact heads + `memories_entities_gin` **dropped**, freeze ruled) + the gate stage (`app\gate.py` pure decision module: novelty + entity tripwire + damper, named signal constants; `app\retrieval.py` gated/loader branch — loader path v1-byte-parity, closed turns zero probe SQL, fires append `gate_fetch_k` new items via SQL-excluded probe or the GIN's entity-only rung) + the **entities freeze at observe** (`insert_observation` writes the fact head only) + the correction verb's NER + operator-field entities merge (`app\ingest.py`, `CorrectionNlpFailedError` → 502) + the fork-5 pre-serve callback (`app\reconstruction.py`, one defaulted param) + caller-held loaded-set/streak scene state (`app\session.py`) + the prompt recollection partition (`app\dialogue.py`) + `GateInstrumentation` wire deltas (`app\schemas.py`) + four knobs (`app\config.py`) + CLI gate line + load-driver `gate_check`/gate block | floor-verifier **pass** against all seven prior floors (write-path, retrieval, dialogue, session-runner, reconstruction, and both correction floors deliberately re-opened, re-verified): structural walker `tests\verify_gate.py` re-run independently (**51 assertions**, every done-when criterion incl. loader-parity, all ladder rungs, the blocking-callback beat, migration-003 legacy-row guard, and entities-follow-correction) on fresh scratch `longmem_test`; all seven prior walkers re-run clean, each on fresh scratch (40/40 write — 38 → 40 additive freeze pair; 36/36 read — **byte-untouched, the loader-parity proof**; 36/36 CLI harness — fixture pin + label edit only; 42/42 reconstruction — fixture pin only; 34/34 authorial — 33 → 34 additive; 34/34 fact — 32 → 34 additive); migration 003 applied to `longmem`, no-arg migrate → **"Up to date: 3 migration(s) applied, 0 pending"**; `longmem` pristine via the postgres MCP (ledger 001+002+003, all product tables 0 rows, new partial GIN present, old GIN absent); independent code spot-checks (loader path behavior-identical, callback-absent serve identical, one embed per turn, sole DELETE still cache eviction, no gate model role, reserved slots inert); plus the live piped REPL beat (loader → mid-scene novelty fetch → both-signal fire → `:correct` → **`(reconstructing…)` printed during the blocked turn**) and a standalone load-driver run with `gate_check` p50/p95 + the gate fire/efficacy block | 2026-07-19 |

| Structural pytest suite v1 — `pytest.ini` (marker registration, `testpaths`, no cache residue) + `tests\conftest.py` (scratch **`longmem_suite`** session lifecycle: probe → create → migrate 001–003 → per-test TRUNCATE → drop; unreachable ⇒ loud skip, exit green; db-layer `InsertPlan` seeding with the pure fake embedding — the fast path never imports the NLP loaders; per-set configs with production-vs-fixture pins stated) + **38 scenarios** in five `test_*.py` files (Set A: authorial + fact chain incl. the db-layer distance-0 rank pair, CAS rollback, the pure constraint-follows-anchor test, and the marked route contract; Set B: decay-vs-invalidation incl. the two-time-travel-mechanics-agree and IDs-on-the-wire pairs; Set C: write-back chain shape, cache hit/frozen basis, band crossing, identity bump, correction eviction + re-anchor, drift refusal + refusal caching; Set D: loader parity, closed gate, novelty/tripwire/both fires, damper + reset, efficacy, runner append-only, marked entities-follow-correction; degradation: every ruled ladder row incl. the build-phase hard-stop, flagged as such in its docstring) + the Stop-hook subset edit (`-m "not nlp"`, ruled) + `pytest==9.1.1`/`httpx==0.28.1` pins | floor-verifier **pass** against all eight prior floors, standing by construction: `app\`, `db\`, and all seven walkers **byte-identical to HEAD** (the verifier's recorded git-diff proof — identical bytes need no re-run); full suite re-run twice independently (38/38, 38/38 — the determinism criterion), the subset re-run with API keys scrubbed (31/31 in ~14 s — the keyless + no-spaCy proof), the unreachable-skip beat (30 skipped + the one pure no-DB test, exit 0, loud warning), the hook contract both ways (green → exit 0; `stop_hook_active` guard short-circuits; red path + dormant guards read intact with the subset flag), a structural-only audit of all five files (no assertion touches model prose), no-arg migrate → "Up to date: 3 migration(s) applied, 0 pending", `longmem` pristine via the postgres MCP (ten product tables 0 rows, ledger 001+002+003, **no `longmem_suite` residue**), and pins == installed versions | 2026-07-20 |

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
- **2026-07-17** — **Scope-limiter reframing (rules + docs; ruled by Jack).** The
  authorial-correction spec session was paused when Jack flagged a standing bias: rules written
  as verification discipline had hardened into design pressure — correct-but-larger options
  arrived pre-labeled "blocked", "deferred", or "would re-open a floor". A full sweep of every
  instruction surface (CLAUDE.md, docs\, tests\CLAUDE.md, .claude\) found four limiter families;
  Jack ruled the reframe (dated "Scope-limiter reframing" entry in `decisions.md`). Changes:
  CLAUDE.md gains the schema-evolves-by-migration rule, the floors-are-re-openable line, and the
  full-options report contract; this file's "Post-August ledger" renamed **"Sequenced-later
  ledger (pull-forward eligible)"** with the standing pull-forward rule, and "revisit only if
  demo latency demands" struck; architecture §2/§10 sequencing clauses became pointers to the
  queues; `/build-task` Phase 2's report contract amended. Kept deliberately: the
  deadline-never-drives rule, staged verification, the invariants, structural-only tests. Built
  specs, old register entries, and session logs stand as history. The freeze's recorded
  casualties (idempotency/dedup column, scene-boundary schema home, reputation history's schema
  objection, VAD dominance in jsonb, location description column) are now *eligible* for
  re-opening, each its own future ruling. **The authorial-correction spec resumes next — its
  four open forks re-presented fairly priced under the new framing.**
- **2026-07-17** — **Authorial-correction v1 build target specced** (`authorial-correction.md`)
  — the first spec session under the scope-limiter reframing (paused mid-forks by that ruling;
  resumed with all four forks re-presented fairly priced). Jack ruled four scope forks (dated
  "Authorial-correction spec scope rulings" entry in `decisions.md`): scope = **chain content
  now + a slated fact-level correction target** (ruled into the immediate queue as item 2,
  ahead of the gate — versioned memories-row facts + corrected embedding, migration-002-class,
  own spec session); the reconstructor's **fixed constraint follows the drift anchor** on
  corrected chains (the recommendation that flipped once floor re-verification was priced as a
  step — deliberately re-opens the reconstruction floor at build); surface = **memory-scoped
  operator verb** (the pin pattern; `/v1/events/*` stays diegetic-only) + a REPL `:correct`
  meta-command; **immediate mid-scene effect**, with the within-scene invariant's wording
  amended (CLAUDE.md, architecture §7, `test-suite.md` Set C — authorial correction is now the
  second sanctioned text-change cause). Endpoint design lines: no model calls (operator text
  byte-verbatim), no `corrections` row (diegetic-only by CHECK), one supersede-guarded
  transaction with cache eviction, fail-loud operator surface. No migration needed as a fact of
  this target. Remaining physical shapes tagged `[SETTLE-AT-BUILD]`. Queue renumbered (gate →
  3, suite → 4) with stale refs updated in `read-path.md`, `cli-harness.md`,
  `reconstruction.md`. Doc-auditor sweep: **no contradictions**; two residuals fixed and
  grep-verified — `reconstruction.md` gained the house-style constraint-follows-anchor
  annotations (scope boundary, reconstructor-input item 1, cache-contract band line — the last
  hedged as a `[SETTLE-AT-BUILD]` suggestion, not a ruling), and the register's 2026-07-12
  within-scene-invariant statement gained its amendment note per the annotation convention.
  Docs only — no code, no floors changed.
- **2026-07-18** — **Authorial-correction endpoint v1 built, verified, and committed — the
  correction-override beat is live.** Jack ruled one criterion via an explicit question at a
  mid-build stop-and-report: the spec's "time travel coherent" done-when **re-ruled to stored
  bi-temporal coherence** — its original "as_of before t_c serves the prior telling" wording
  over-claimed (`as_of` is an age-computation override by the 2026-07-14 read-path ruling; the
  candidate SQL always joins the live head); the walker asserts windowed-SQL re-derivation
  instead, and the alternative (as_of-windowed chain serving) was presented fairly priced and
  not adopted. The spec's remaining settle-shapes were approved with the plan, including the
  **compare-and-swap refinement** (optional `expected_detail_id`: stale → 409 with rollback;
  omitted → correct the live head — the REPL default). New: `apply_authorial_correction`
  (`app\db.py`, one transaction: predicate supersede + CAS + corrected head at t_c + cache
  eviction; the module's first sanctioned DELETE — derived cache rows only),
  `IngestService.correct` + `CorrectionConflictError` (`app\ingest.py`),
  `POST /v1/memories/{id}/correction` with 404/409/422 (`app\api.py`),
  `CorrectionRequest`/`CorrectionResult` (`app\schemas.py`), the anchor-cause-aware pure
  `build_reconstruction_item` + `ReconstructionSource.anchor_cause` (the constraint-follows-
  anchor delta — the reconstruction floor deliberately re-opened and re-verified, its walker
  grown 41 → 42 by addition only), `runner.correct` + the REPL `:correct` meta-command, and
  walker `tests\verify_authorial_correction.py` (31 assertions). Verification: all five walkers
  on fresh scratch (31/31, 42/42, 36/36, 34/34, 35/35); a live piped REPL correction-override
  beat (read verbatim → `:correct` head swap → corrected read, one scene; fake mode — note the
  REPL smoke now needs `$env:LONGMEM_PROVIDER_MODE = "fake"` since `.env` runs real mode);
  `db\migrate.py` no-arg a clean no-op; floor-verifier **pass** with working postgres MCP tools
  and independent code spot-checks. Queue renumbered (fact-level correction → item 1, gate → 2,
  suite → 3) with stale refs updated in `read-path.md`, `cli-harness.md`, `reconstruction.md`,
  `authorial-correction.md`.
- **2026-07-18** — **Fact-level correction v1 build target specced** (`fact-level-correction.md`)
  — immediate-queue item 1's own spec session, as slated. Consolidates the 2026-07-17 slating
  (versioned memories-row facts + corrected embedding so retrieval follows the fix) into a build
  spec; **migration 002 is a fact of the target — the first spec for which that is true** (the
  002 ledger seam designed 2026-07-13 finally gets its migration). Jack ruled four scope forks
  (dated "Fact-level correction spec scope rulings" entry in `decisions.md`), presented twice —
  technically, then re-introduced in plain prose at his request — and each ruled on the
  recommended option: **fact scope = embedding only** (importance/typology/decay/entities/affect
  stand as write-time event facts; the entities honest-deferral recorded — its first reader, the
  gate's GIN path, is queue item 2); **version shape = a fact-version child table** (the
  `memory_details` precedent applied to the semantic basis: one-live-head partial unique index +
  partial HNSW, `original` rows backfilled; read-path + write-path floors re-open at build as
  re-verification steps); **surface = one combined verb** (the correction endpoint becomes
  fact-following — corrected text is both telling head and embedded fact basis; verified
  coupling: a fact-only correction would leave reconstruction re-injecting corrected-away data
  from original-anchored gist spans); **embed failure = all-or-nothing fail-loud** (embed before
  the transaction; the honest price — an embedding outage blocks telling corrections too — was
  stated and accepted). Premise corrections verified in code before presenting: entities is
  write-only today; gist re-derivation on corrected chains has zero consumers; purge is a
  docs-only contract. Design lines: one model call stated honestly (v1's "no model calls"
  purity superseded, not silently dropped; the existing embedding role — no new model role or
  env var); the reconstruction delta is **none** (the drift check embeds text fresh; the
  corrected-anchor branch ignores spans) — `verify_reconstruction.py` re-running unmodified is
  the build's proof. Remaining physical shapes `[SETTLE-AT-BUILD]`. Propagated: CLAUDE.md
  invariant parenthetical (fact chain), architecture §4.4 (new) + §6 + §8 + §12,
  `authorial-correction.md` five annotations, `migration-01.md` 002 pointers, `test-suite.md`
  Set A fact assertions + the all-or-nothing degradation case. Docs only — no code, no floors
  changed.
- **2026-07-18** — **Fact-level correction v1 built, verified, and committed — retrieval
  follows the fix, and migration 002 is the ledger seam's first use.** Jack ruled two shapes
  via explicit questions at plan approval (dated "Fact-level correction build rulings" entry in
  `decisions.md`): **dual-write vs freeze = FREEZE** (against the dual-write recommendation —
  observe no longer writes `memories.embedding`; the `original` fact head is the sole vector
  home; the epoch split accepted; the queryable embed-degradation signal moved to the live fact
  head, and the write-path walker's signal assertion moved with it — the build's one
  non-additive walker change, ruling-driven) and **the old `memories_embedding_hnsw` dropped in
  002**; the eight mechanical shapes were approved as proposed. New:
  `db\migrations\002_fact_versions.sql` (fact chain + guarded backfill before the indexes +
  one-live-head partial unique + partial HNSW + the index drop), the fact-following verb
  (`apply_authorial_correction` grown — fact supersede + insert in the same transaction, embed
  BEFORE it; `CorrectionEmbedFailedError` → 502, the escalation precedent), the freeze at
  observe (`insert_observation` mints the fact head), the probe on the live fact head
  (`fetch_vector_candidates`; degraded path deliberately unjoined), wire deltas
  (`CorrectionResult` += fact IDs + embed_ms/embedding_tokens; `IngestResult` +=
  fact_version_id), REPL surfacing (both head swaps + embed timing), and walker
  `tests\verify_fact_correction.py` (32 assertions — incl. the db-layer distance-0
  retrieval-follows-the-fix pair, the backfill guard proven against a legacy-shaped row, and
  the correction-repairs-degraded-rows beat: correcting a NULL-fact-embedding memory re-embeds
  it into vector reach). Verification: all six walkers on fresh scratch (32/32, 38/38, 36/36,
  36/36, 42/42, 33/33 — reconstruction and CLI harness byte-untouched, `app\retrieval.py` and
  `app\reconstruction.py` byte-identical to HEAD: the no-reconstruction-delta proof); migration
  002 applied to `longmem`, no-arg migrate → "Up to date: 2 applied, 0 pending"; `longmem`
  pristine via the postgres MCP; floor-verifier **pass**; and a live piped REPL beat where the
  same query's relevance moved 0.4686 → 0.5637 across a `:correct` — the fix moving recall,
  visible in the debug view. Queue renumbered (gate → 1 and it inherits the entities fact-chain
  column, suite → 2, Unity → 3, pre-ship gates → 4).
- **2026-07-19** — **Mid-dialogue gate v1 build target specced** (`mid-dialogue-gate.md`) —
  immediate-queue item 1's own spec session. Consolidates architecture §6 (gate + degradation
  ladder + the prompt-caching boundary), §4.3 (the two identity structures), §7 (the mid-scene
  block-with-signal miss path deferred here by `reconstruction.md`), §11 (efficacy definitions
  + the reserved gate-check latency term), and the 2026-07-18 entities honest-deferral into a
  build spec; **migration 003 is a fact of the target — the second spec for which that is
  true**. Jack ruled five scope forks (dated "Mid-dialogue gate spec scope rulings" entry in
  `decisions.md`; forks 1/2/4/5 re-presented in plain prose at his request and ruled on the
  re-presentation): **loaded set = caller-held scene state** (reputation-style; absent fields ⇒
  loader turn ⇒ v1 byte-parity); **migration 003 entities = FREEZE** (fact head the sole home;
  guarded backfill; partial GIN on live heads; `memories_entities_gin` dropped;
  `memories.entities` frozen — the coverage-check-consistency argument was decisive);
  **correction entities = NLP pass + optional operator field** (observe's merge mirrored — the
  fact-level NLP-re-pass rejection's premise ends with this target); **per-signal fire logs =
  instrumentation-only** (`gate_events` stays pull-forward eligible); **reconstructing signal
  = post-hoc fields + an in-process pre-serve callback** (fields-only was un-recommended
  mid-session — it cannot show anything *during* the pause; the reconstruction floor re-opens
  at build for one defaulted parameter, a step priced as a step). The fruitless damper stays
  `[SETTLE-AT-BUILD]` with a full suggested mechanism, flagged promotable. Design lines: one
  embed per turn (the novelty embedding IS the probe); tripwire = live `identity_components`
  vs coverage = fact-head entities (keyed fetch) + degraded fetch = their partial GIN — never
  conflated; the reserved
  read-request slots stay inert; loaded set append-only within a scene; caller-side reset (no
  fourth scene-boundary server consumer); CLAUDE.md deliberately unchanged (which memories
  surface was never under the byte-identity guarantee). Propagated: architecture §4.4/§5/§6/§11
  annotations, register annotations (audit ruling #3 GIN home; fact-level fork-1 deferral
  closed), `fact-level-correction.md`, `reconstruction.md`, `read-path.md`, `cli-harness.md`,
  `authorial-correction.md`, `migration-01.md` 003 pointers, `test-suite.md` **Set D** (new,
  ~8–10 scenarios) + ladder-row pointer. Docs only — no code, no floors changed.
- **2026-07-19** — **Mid-dialogue gate v1 built, verified, and committed — retrieval is
  conditional, and the reserved §11 gate term is live.** Jack ruled two shapes via explicit
  questions at plan approval (dated "Mid-dialogue gate build rulings" entry in `decisions.md`):
  **damper = as suggested** (fruitless = zero new IDs; 2 consecutive suppress novelty for the
  scene remainder; tripwire live; scene reset — the spec's promotable flag closed) and
  **correction-path NER failure = clean loud error** (`CorrectionNlpFailedError` → 502, the
  embed precedent; nothing written). The remaining shapes were approved with the plan, incl.
  **`gate_enabled`** (fixture pin + kill-switch scaffold). New: `app\gate.py` (pure decision
  module — the decay.py precedent; named signal constants, the `TRIGGER_*` mirror),
  `db\migrations\003_fact_entities.sql` (entities fact-chain column + guarded backfill +
  partial GIN on live heads + old GIN dropped; applied to `longmem` — "001 + 002 + 003
  applied, 0 pending"), the gated/loader branch in `app\retrieval.py` (loader = v1
  byte-parity; closed = zero probe SQL; fire = SQL-excluded probe reusing the turn's one
  embed, or the GIN entity-only rung), the entities freeze at observe + `GateRow` + three
  gate fetchers (`app\db.py`), the correction NER merge (`app\ingest.py` + 502 in
  `app\api.py`), the fork-5 pre-serve callback (`app\reconstruction.py`, one defaulted
  param), caller-held loaded-set/streak state (`app\session.py`), the prompt recollection
  partition (`app\dialogue.py`), `GateInstrumentation` (`app\schemas.py`), four knobs
  (`app\config.py`), the CLI gate line + `(reconstructing…)` print, and the load-driver
  `gate_check` series + gate block. Walker `tests\verify_gate.py` (**51 assertions**); prior
  walkers 40/40 (write, +2 freeze), 36/36 (read, **byte-untouched** — the loader-parity
  proof), 36/36 (CLI, pin + label only), 42/42 (reconstruction, pin only), 34/34 (authorial,
  +1), 34/34 (fact, +2), each on fresh scratch; floor-verifier **pass** with working postgres
  MCP tools; live piped REPL beat with **`(reconstructing…)` printed during the blocked
  mid-scene turn**; standalone driver run with real gate fire/efficacy rows.
  **Build-surfaced learnings** (recorded in `decisions.md`): pgvector rows need `.to_list()`
  (the bug hid behind the fail-quiet ladder — the loader fallback worked as designed);
  fake-mode calibration corrected (ordinary distinct prose ~0.45–0.75, not ~1.0; the 0.5
  threshold stands; guaranteed-novel fixtures need trigram-rare wording — chosen by
  measurement). Queue renumbered (suite → 1, Unity → 2, pre-ship gates → 3); the gate
  pointers in prior specs gained "built" markers.
- **2026-07-20** — **Structural pytest suite v1 built, verified, and committed — the
  suite-gate Stop hook is live.** `docs\test-suite.md` was already the spec, so the session
  went plan-mode orient → three explicit-question rulings → scoped build (dated "Test-suite
  build rulings" entry in `decisions.md`): **the Stop hook runs the `-m "not nlp"` subset**
  (the 7 marked scenarios call the write pass at the service level and pay the lazy
  spaCy+fastcoref load — measured: full suite 82 s cold / ~30 s warm, subset ~14 s);
  **Postgres unreachable ⇒ loud clean skip, exit green** (the hook's dormant philosophy
  extended to the DB prerequisite; pure no-DB scenarios still run); **CI-ready now,
  workflow later** (public-flip-sprint home; until then regressions are caught
  on-machine — stated and accepted). New: `pytest.ini`, `tests\conftest.py` (scratch
  **`longmem_suite`** lifecycle, deliberately distinct from the walkers' `longmem_test`;
  db-layer `InsertPlan` seeding with the pure fake embedding so unmarked scenarios never
  trigger the loaders; per-set configs with production-vs-fixture pins stated), and 38
  scenarios across `test_set_a_correction.py` (8), `test_set_b_decay.py` (5),
  `test_set_c_reconstruction.py` (7), `test_set_d_gate.py` (9), `test_degradation.py` (9);
  `requirements.txt` pins pytest 9.1.1 + httpx 0.28.1 (closing the 2026-07-16 unpinned
  observation). `app\`, `db\`, and all seven walkers byte-untouched — the floors stand by
  construction. floor-verifier **pass** on all nine criteria (two independent full-suite
  runs, the keyless subset run, the unreachable beat, the hook contract both ways, the
  structural-only audit, migrate no-op, `longmem` pristine via the postgres MCP with no
  scratch residue). The escalation hard-stop test asserts the current build-phase stance
  and says so in its docstring — the owed re-rule changes exactly that test. Queue
  renumbered (Unity → 1, pre-ship gates → 2).

## Immediate queue

1. Unity project + reference scene — connect MCP for Unity first (`mcp-setup.md`) — then demo
   choreography incl. the 60-day drift beat, the correction-override beat, and the
   gate-recollect beat (all live in the REPL: `:as-of` jumps + scene boundaries + band
   crossings; `:correct` — which now moves retrieval AND entities; the gate debug line +
   `(reconstructing…)`).
2. Before the demo ships: re-rule the escalation failure path (see open questions; the
   suite's hard-stop test tracks the current stance) and pick a real-provider smoke moment
   (one live observe + one live dialogue turn + one live reconstruction with keys) ahead of
   demo choreography.

*(Done 2026-07-20: **Structural pytest suite v1** — 38 scenarios green, the Stop hook live
on the `-m "not nlp"` subset; see the verified-floors table and session log. Done 2026-07-19: **Mid-dialogue gate v1** — retrieval is conditional; migration 003
applied; see the verified-floors table and session log. Done 2026-07-18: **Fact-level correction v1** — retrieval follows the fix; migration 002
applied; see the verified-floors table and session log. Also done 2026-07-18:
**Authorial-correction endpoint v1** — the correction-override beat is live;
see the verified-floors table and session log. Done 2026-07-17: **Reconstruction v1** — the
thesis mechanism is live; see the verified-floors
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
- Gate threshold values + efficacy definitions wired to instrumentation. — **Consolidated into
  `mid-dialogue-gate.md` 2026-07-19 and now BUILT** (same day; thresholds ruled with the build
  plan; the efficacy comparators live in `GateInstrumentation` + the load-driver gate block;
  instrumentation-only fire logs as ruled).
- Unity client C# API surface: send event, open dialogue, directive callback, reputation read,
  reconstructing-signal hook, scene-boundary emission.
- Demo choreography: injected-timestamp time travel; decay + correction-override + gate-recollect
  beats; the 60-day drift plot — a planned beat since the 2026-07-14 re-slating (reconstruction is
  pre-demo).
- README destructive-compression counter-example pick.

## Sequenced-later ledger (pull-forward eligible)

*Sequencing orders work; it never rules an option out of a design discussion. Any item here may
be pulled into the immediate queue by a dated ruling when a current target shows it is
architecturally load-bearing — the 2026-07-14 reconstruction re-slating is the template.
(Reframed from "Post-August ledger" by the 2026-07-17 "Scope-limiter reframing" ruling in
`decisions.md`.)*

Reflection pipeline mechanism (sequenced post-August — hedge resolved 2026-07-14; the pre-demo
identity document is seed-prose-only); dissonance path + the diegetic suite pair; the purge
endpoint (before the public flip — ruled 2026-07-14); prompt caching / prompt-head rebuild
(revisit when a target needs it or demo latency demands — reframed 2026-07-17 from the ruled
"only if demo latency demands" wording); encoding-context read term +
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
