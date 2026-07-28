# longmem-npc — Session log

Split out of `status.md` on 2026-07-28 (full-repo audit). Entries are moved **verbatim**.

This is the project's narrative record: what actually happened each session — landed,
blocked, or abandoned — in the honest wording the `/wrap-up` protocol asks for. It lived
inside the auto-loaded living file, where ~19.4k tokens of history rode into every session's
context whether or not the session needed it. It is history, and history is worth keeping and
worth not re-reading every time.

**Append-only.** Add one entry per session at the END. Never edit a past entry except to add
a dated correction note. The living state — current phase, queues, open questions — is in
`status.md`; the evidence table is in `floors.md`.

---

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
- **2026-07-20** — **Fake-mode latency/compute pass + two measured perf fixes + a
  suite-concurrency fix (Jack ordered the profiling, then ruled "apply both").** A
  scratchpad-only profiler (load-driver instrumentation + `EXPLAIN ANALYZE` + a cProfile of
  the NLP pass + a psycopg vector-param micro-benchmark) found two big, corpus-independent
  pits — full write-up in the dated "Latency-fix + suite-concurrency rulings" entry in
  `decisions.md`. Fixes (three files, no floor behavior changed): **(pit #2)** `app\db.py` —
  the four vector-probe queries bind the 1536-dim query vector as a **named** param so it
  rides the wire once instead of twice, killing a ~44 ms Windows-loopback Nagle/delayed-ACK
  stall (server did the query in 1.3 ms; EXPLAIN confirms HNSW used); **reads ~54 ms →
  ~5–10 ms, a gate fire ~55 ms → ~7 ms** (measured). **(pit #1)** `app\nlp.py`
  `_tame_datasets_fingerprint()` (called from the `_coref()` loader) — `disable_caching()` +
  a guarded short-circuit of the `datasets` fingerprint Hasher, which otherwise dill-pickles
  fastcoref's internal spaCy model every observe; coref output unchanged; **writes ~215 ms →
  ~63 ms** (measured). **(b)** `tests\conftest.py` — scratch DB is now `longmem_suite_<pid>`
  so two overlapping suite runs (the Stop hook fires one per turn-end) can't force-drop each
  other (the `AdminShutdown` false-RED seen during the profiling turns). Re-verified: full
  suite **38/38**, all seven walkers green (40/36/36/42/34/34/51 on fresh scratch), migrate a
  clean no-op, `longmem` pristine, no scratch residue. The pit #1 fix is the one library
  monkeypatch — guarded to degrade to the slow-but-correct path; flagged as a version-fragility
  cost, trivially revertible. Deferred (recorded in the decisions entry): connection-per-query
  churn (secondary); and a real-mode COST flag — escalation fired 24/40 (60%) on realistic
  prose, each an extra LLM call in real mode. **Next: a real-mode smoke run to confirm the
  end-to-end picture, then the demo work.**

- **2026-07-20 → 21** — **Research sweep + adoption slate: Target A (encoding-context term)
  built, floor-verified, and committed.** A 45-paper literature sweep (31 curated + 14
  arXiv-discovered; map-reduce reader agents against a baseline brief; consolidated in
  `docs\research\FINDINGS.md` — *at the time, gitignored working material under
  `Research Papers\`; tracked and moved 2026-07-28*) found the two
  biggest gaps already on our radar (no judged eval harness; no graph/associative retrieval)
  and one strictly-better mechanism with a slot already reserved: RaMem-style encoding-context
  re-ranking. Jack ruled the adoption slate via four explicit questions (dated
  "Research-adoption slate + encoding-context build rulings" entry in `decisions.md`): two
  targets now (A: context term + TARG calibration; B: hybrid lexical channel), context =
  client-supplied fields (no LLM decomposition — the 2026-07-14 as-is ruling stands), the
  queued eval harness includes judged categories from v1, recall-reinforced decay gets its own
  future session. **Target A landed:** the three reserved request fields are consumed as a
  soft multiplicative score nudge (entity coverage on live fact heads + event-time kernel +
  location match; ≥ 1 always, never a filter), byte-identical v1 scoring when absent (the
  parity contract), knobs per-agent overridable, instrumentation-level surfacing so
  `app\reconstruction.py`/`app\gate.py`/`app\decay.py` stay byte-identical to HEAD; plus the
  report-only `--gate-budget` calibration recipe. Read-path walker 36 → 42 (criterion [7]
  re-scoped — the one ruling-driven change); suite 38 → 40; floor-verifier **pass** with
  working postgres MCP tools; live REPL `:context` beat (exact ×1.75). No migration. A
  mid-session laptop crash cost nothing: the working tree survived and every check re-ran
  green post-crash.
- **2026-07-21** — **Target B (hybrid lexical channel) built, floor-verified, and committed —
  the research-adoption slate is landed.** Migration 004 (index-only: partial FTS GIN over
  live fact heads) + a token-OR lexical candidate fetch unioned into the loader's vector
  over-fetch before scoring — dedup exact, scoring formula untouched, lexical hits carrying
  true cosine relevance, NULL-embedding rows lexically reachable with relevance null (the
  embed-degradation consequence honestly softened; read walker criterion [9] sharpened to
  assert the vector-path exclusion on the probe itself). **Build-surfaced correction:**
  websearch/plainto AND semantics would have made the channel inert for utterances — the
  token-OR shape (casefolded ≥3-letter runs, capped 16) was built instead, recorded in the
  dated "Hybrid lexical channel build rulings" entry. `lexical_fetch_k` kill-switch (0.0 =
  pure-vector v1); `text_search_config` string knob ('simple' baked into the index expression,
  overrides run unindexed — stated). Read walker 42 → 48; gate walker's ledger pin +004 (its
  sole change); suite 40 → 41 + keyless subset 34/34; 004 applied to `longmem` ("4 applied,
  0 pending", idempotent); floor-verifier **pass**; live k=1/overfetch-1.0 REPL beat (the
  pinned rare-name row served via lexical-only reach, `lex=2 candidates=2 k=1`). Session end:
  the research queue items slated (immediate queue 3–6), and
  `docs\research\CHANGES-FROM-RESEARCH.md` written (*gitignored then; tracked 2026-07-28*)
  tracing every landed and queued change to its source papers for the future README.
- **2026-07-21** — **Real-mode testing session: pre-ship gates (b) and (c) closed — real mode
  proven end-to-end, after a build-surfaced parse fix (the first session ever to construct
  the real providers).** Env preflight: real mode requires all six model vars —
  `LONGMEM_MODEL_RECONSTRUCTION` was missing from `.env`; Jack ruled it **`claude-sonnet-5`**
  (env-injected this session; the `.env` line is his to add) and ruled the run **priced at
  standard rates** (the nine `LONGMEM_PRICE_*` per-Mtok: sonnet-5 3.00/15.00,
  haiku-4.5 1.00/5.00, embedding 0.02 — intro pricing declined so the cost table stays honest
  after 2026-08-31). **The first smoke FAILED and surfaced a real defect:** sonnet-5 emits a
  leading thinking block, so `content[0].text` crashed reconstruction with an uncaught
  AttributeError; haiku-4.5 wrapped its escalation JSON in markdown fences 3/3 despite
  "No other text" — every escalating observe hard-stopped. **Jack ruled parse-side
  hardening** (dated "Real-mode parse hardening ruling" entry in `decisions.md`; commit
  `1388bf6`): `_first_text_block` + `_lenient_json_text` at the four JSON-in-text parse
  sites in `app\providers.py`; fakes/prompts/seams untouched; re-verified suite 41/41 ×2 +
  all seven walkers green (40/48/36/42/34/34/51) + floor-verifier **pass** (diff exactly the
  two helpers + four sites; helper edge cases proven in-process; `longmem` pristine, zero
  scratch residue). **Gate (b) receipts** (piped REPL on scratch `longmem_smoke`, production
  knobs, no pins): live observe `[escalated]` with real render + tokens; one batched
  sonnet-5 reconstruction — 6 misses → **5 write-backs + 1 honest drift refusal**
  (in 856/out 853 tok, drift-embed 441); streaming dialogue first_token 2.9 s with a
  `recall` directive carrying memory IDs and the model delta applied 0.0 → 0.02; call-free
  cache-hit reread (recon 3.4 ms, turn 4.3 s vs 17.6 s cold); gate evaluated + closed with
  **zero probe SQL** (min_dist 0.408); `lex=` + `context: active` debug lines live.
  **Gate (c)** (staged scratchpad probe on `longmem_real`, diffed vs the surviving fake
  baseline; artifacts scratchpad-only/gitignored: `latency_report_real.json`,
  `diff_summary.txt`, `driver_report_real.json`, `explain_real.txt`): every infra series
  FLAT; the real numbers are the phase-header headline set. **Escalation re-measured:
  63/80 = 79% on realistic prose** (real haiku importance p50 0.61 vs the 0.45 threshold;
  triggers: importance 43, unresolved_reference 31, novel_entity 11, low_confidence 9,
  identity_affect 6; ~1.4 s + ~$0.0021 per fire ⇒ ~+$0.17/100 observes) **vs 0/26 on the
  driver's synthetic prose** — the rate is prose-distribution-dependent; 0 hard-stops in 80
  observes post-fix (feeds open question (a)). **Gate under real embeddings:** all four
  fixture scenarios reproduce exactly (closed 0/20 echo dist 0.0; novelty 20/20 at 0.64;
  tripwire 20/20; both 20/20); novelty CDF class p50s echo 0.00 / paraphrase 0.15 /
  related 0.50 / unrelated 0.70 — the current 0.5 threshold ≈ a 40% fire budget;
  recommendations (report-only): budget 0.2 → 0.65, 0.3 → 0.59, 0.4 → 0.50 on realistic
  prose vs the driver's 0.3 → 0.33 on its generator prose — calibration must run on real
  game prose. **Drift budget well-placed:** 16 live retellings re-embedded vs original
  anchors: p50 0.157 / p95 0.239 / max 0.244 — all under 0.35; observed refusals (1 smoke +
  1 probe) are the tail working. **Lexical channel:** EXPLAIN proves the 004 partial GIN is
  chosen (Bitmap Index Scan); the cost is ts_rank over the match set — the ≥3-letter
  tokenizer admits "the"/"did" and 'simple' keeps stopwords, so common words match ~every
  row: ~77 ms p50 at 5 k rows (3 ms on the 7-row smoke), linear in matches — watch-item
  with report-only options (tokenizer stoplist / min length 4); kill-switch verified =
  byte-shape v1. **Context term: ~0.03 ms** (score p50 0.08 → 0.11, active 50/50).
  **Stock driver (6×10 turns, priced): $0.44/100 turns** (dialogue $0.41 of it), turn p50
  2.9 s, gate 15 fires/100 with novelty efficacy 0.857, 2 fruitless, 3 damper-active turns.
  Spend for the whole session: order $2 (~205 haiku-class + ~110 sonnet-class calls,
  ~1 200 embeds). `longmem` pristine via the postgres MCP; zero scratch residue.
- **2026-07-21** — **Latency review + split-brain spec session (same day): the latency slate
  is ruled and the split-brain topology is pulled forward — specced.** Jack reviewed the
  real-mode table and ruled the viability bar (**first word < ~1 s** — perceived latency =
  prose TTFT, the honest decomposition being ~190 ms of our layer inside a ~4 s
  LLM-dominated turn) and that **all four latency levers land pre-demo** (dated "Latency
  slate + split-brain pull-forward rulings" entry in `decisions.md`): A split-brain
  streaming (specced now), B1/B2 dialogue-call experiments, C1 scene-boundary pre-warm, D
  async observes + the trigger fold-in. **Topology altered by ruling:** §9's serial sketch
  would put ~0.8–1.5 s of behavior call before the first prose token; Jack re-read the
  asymmetry — the prose call sees PAST behaviors as world facts ("why did you do that a
  minute / a week ago"), never the current turn's — so the calls run **concurrently** and
  the action enters the record for later turns. Two gray areas were surfaced at his request
  and ruled: same-turn word/action incoherence **accepted as an instrumented design fact**
  (the turn result records both calls' ranked views + directive — §13's explanation-cause
  divergence measurable from day one), and the world record is **game-authored action
  observes + the caller-held recent-actions block** (seam auto-write rejected — it would
  record unresolved intent as fact). Also ruled: the reserved `WeightOverrides` slot goes
  **live on the behavior view** via a second scoring pass (dialogue-view byte-parity kept);
  streaming = **seam + REPL + driver** this slice (SSE rides with Unity).
  `split-brain-streaming.md` written (ruled topology, scope boundary, mechanism,
  settle-tags, ten done-when criteria); architecture §9 amended (supersedes-in-part its
  serial wording); queue restructured (split-brain build → item 1; the pre-ship item grown
  by the slate; research items renumbered 4–8); the ledger's split-brain entry moved off —
  the second use of the pull-forward template. Docs only — no code, no floors changed.
- **2026-07-21** — **Split-brain streaming v1 built, verified, and committed — the latency
  topology is live, specced and built the same day.** Jack ruled four forks via explicit
  questions at plan approval (dated "Split-brain streaming build rulings" entry in
  `decisions.md`): **behavior model role = a new `behavior` role** (`LONGMEM_MODEL_BEHAVIOR` +
  `LONGMEM_PRICE_BEHAVIOR_IN/OUT`); **seam shape = async generator** (yields prose chunks then
  the terminal result; `first_word_ms` = time to the first yielded chunk); **mid-stream prose
  drop = keep the partial + degraded flag**; **behavior view = re-rank the served top-k set**
  (not the full pool — reuses served text, zero extra SQL/model calls). Build resolutions:
  exponent-form weighting (`behavior_score = item.score · rel^(w−1) · rec^(w−1) · imp^(w−1)`,
  so all-1.0 is dialogue-view parity and any other value re-ranks; clamp `[0,4]`); identity
  shared by BOTH prompts so the asymmetry stays statistical not architectural (§9), the
  recent-actions block the one ruled prose-only info difference. New: the prose streamer +
  behavior provider + fakes/failure-injection (`app\providers.py`), the async-generator
  split-brain seam with the worker-thread + `asyncio.Queue` bridge and the prompt split
  (`app\dialogue.py`), the `behavior` role + knobs (`app\config.py`), the divergence record +
  split-brain instrumentation + `RecentAction` + live `weight_overrides` (`app\schemas.py`),
  caller-held recent-actions + `stream_utterance`/`utterance` (`app\session.py`), the live
  streaming REPL + divergence debug view (`app\cli.py`), the `first_word`/`behavior` series +
  behavior cost row (`app\load_driver.py`). Verification inline: CLI-harness walker re-opened
  36 → 55 (concurrency proved — first chunk 0.008 s vs behavior 300 ms), read-path
  weight_overrides criterion re-scoped (48), gate walker rename-only (51), four walkers
  byte-untouched and green (40/42/34/34), suite 41 → 42 ×2 + keyless subset 35, migrate no-op,
  `longmem` pristine via the postgres MCP, live REPL streaming beat + driver run. No migration.
  **floor-verifier pass** — independent fresh-context re-run of all ten done-when + all seven
  walkers on fresh scratch (55/48/51/40/42/34/34), suite 42 ×2 + keyless 35, migrate no-op,
  `longmem` pristine, the ten untouched app files + four untouched walkers git-diff
  byte-identical, no invariant violated. **Flagged (operator-owned
  `.env`):** a malformed consolidated `LONGMEM_PRICE_DIALOGUE_IN=…` note-line crashes
  `load_settings` on any run reading `.env` prices — Jack's to fix (the fix: one `KEY=NUMBER`
  per line + add `LONGMEM_MODEL_BEHAVIOR` for real mode). Queue renumbered (Unity →
  item 1, pre-ship → 2, research → 3–7).

- **2026-07-22** — **External-persona agent-team audit + pre-demo replan (docs only — no code, no
  floors, no migration).** Ran a four-persona read-only Claude Code agent team (Convai/Inworld-type
  founder/CEO, senior runtime engineer, memory/cognition researcher, skeptic) through a 3-round
  critique + a solutions round; findings in `external-audit-2026-07-22.md` +
  `external-audit-2026-07-22-solutions.md`; persona defs in `.claude\agents\audit-*.md`. Lead-verified
  the load-bearing findings against source: **`app\api.py` has no HTTP dialogue-turn route** (cognition
  is REPL-only; Unity can't reach it), `first_word_ms` clocks after retrieval (blind to the 16.3 s cold
  stall), and the behavior view is byte-parity at default weights (the divergence record is a near-no-op
  until non-default weights). Jack ruled three forks (dated `decisions.md` entry): split-brain
  divergence → a **separate interview clip**; the demo records **real-providers-only** (the `.env` fix
  is now a hard prerequisite); the **judged eval harness is pulled pre-demo** (+ a judge-free demo
  panel, a hand-labeled gold set, and the fixed-gist ON/OFF ablation). Immediate queue restructured to
  the pre-demo build path (`.env` fix → `POST /v1/dialogue/turn` + perceived-TTFT → Unity + The Ledger →
  judged eval); C1 pre-warm BUILD proposed post-demo (off-camera warm-init covers the demo — flagged for
  confirmation); R7 self-referential drift budget logged as an open question. The build target is now
  **immediate-queue item 1: the HTTP dialogue-turn route.**

- **2026-07-22** — **Escalation failure path handled — soft-degrade built + floor-verified (migration
  005).** The first pre-ship item taken off the queue after the audit replan. Jack ruled the escalation
  fail-loud hard-stop retired (a failed gist-escalation must not halt a live write) and, at build,
  ruled the degraded-gist signal a **dedicated queryable column** (`memories.escalation_failed`,
  migration 005 — over a wire-only flag or reusing `scoring_failed`). Build (`decisions.md` "Escalation
  soft-degrade build"): `_escalate_with_retry` returns `None` on double failure; the observe path
  proceeds with the base NLP-pass gist + sets the flag; `EscalationHardStopError` + its 502 removed; the
  flag rides `InsertPlan` → the column + `IngestResult`. Scope observe-path only — the correction verb's
  fail-loud paths untouched. Suite `test_escalation_hard_stop_zero_rows` →
  `test_escalation_failure_soft_degrades`; walker [11] flipped. **The floor-verifier caught two misses
  in the first pass** — an `EscalationHardStopError` consumer left in `app\cli.py` (would have broken
  the CLI at import) and the gate walker's ledger pin not bumped for 005 — both fixed and re-verified →
  **pass** (write-path 42, cli-harness 55, gate 51, read/recon/authorial/fact 48/42/34/34, suite 42 +
  keyless 35, migrate 005 idempotent, `longmem` pristine 001–005). Trigger-set/threshold tuning
  (79%-fire) stays a separate open item.

- **2026-07-23** — **HTTP dialogue-turn route + perceived-TTFT metric built, floor-verified, and
  committed — the audit's #1 blocker is closed; Unity has a front door.** Plan-as-spec session (the
  design was pre-stated by the queue entry + the audit solutions doc's engineering spec — the
  test-suite precedent); Jack ruled one fork via explicit question at plan approval: the
  **thread-pool cap is deferred post-demo** (dated "HTTP turn route + perceived-TTFT build rulings"
  entry in `decisions.md` records it + the build shapes). New: `POST /v1/dialogue/turn`
  (`app\api.py` — `DialogueService` joins the lifespan; stateless non-streaming drain of the
  async-generator seam to the terminal `DialogueTurnResult`; 404/422 per the existing precedents;
  pass-through; a future SSE `/turn/stream` iterates the same generator) and
  `perceived_first_word_ms` on `DialogueTurnInstrumentation` (captured at the same first-chunk
  instant as `first_word_ms`, clocked from turn start — retrieval-inclusive; 0.0 when no chunk
  arrives; the <1 s bar is measured against it), surfaced in the CLI debug line + the
  `perceived_first_word` driver series. No migration; no new knobs or roles. Verification:
  CLI-harness walker 55 → 62 on fresh scratch; six walkers byte-untouched and green
  (48/51/42/42/34/34); suite 42 → 43 ×2 + keyless subset 35 → 36 (the new route-contract scenario
  is unmarked, so it rides the Stop-hook subset); migrate no-op ("5 applied, 0 pending"); `longmem`
  pristine via the postgres MCP; live serve HTTP beat (observe → turn → unknown-agent 404;
  perceived 22.87 ms vs first_word 0.42 ms on the fake-mode smoke — the retrieval-inclusive gap
  visible) + a standalone driver run. floor-verifier **pass** (independent re-run of all eight
  done-when criteria + all seven walkers + the suite ×2 + the keyless subset; no invariant
  concerns — the sole persisted write of a turn remains the sanctioned reputation UPDATE inside
  the seam). The build target is now **immediate-queue item 2: Unity + reference scene + The
  Ledger**.

- **2026-07-23** — **Escalation trigger tuning: measured, ruled, and the thin_gist trigger built +
  floor-verified (second task of the day) — the last escalation open question is CLOSED.** The
  "measure, then rule" item taken off the queue at Jack's direction before the Unity phase. A
  report-only real-mode probe (scratch `longmem_esc`, the 2026-07-21 corpus construction reproduced
  exactly, ~$0.25) recorded the per-observe RAW trigger inputs the old probe aggregated away. The
  findings (full table in the dated "Escalation trigger tuning" `decisions.md` entry): the fire rate
  reproduced (75% vs 79%) and is **productive, not runaway** — 85% of escalations add net gist
  spans/components; the importance threshold is a weak lever (real scores cluster ≥0.60, and its p50
  moved 0.61 → 0.47 between runs — decimal-tuning would be false precision); ~$0.15/100 observes,
  latency off the dialogue path under async observes; and the **zero-gist hole** — 16/80 observes
  landed with NO gist spans because no trigger fires on an empty base gist, leaving reconstruction's
  fixed constraint empty on exactly those rows. Jack ruled three ways: **the shipped defaults
  stand** (trims declined — gist capture is load-bearing for the thesis); **a sixth `thin_gist`
  trigger** protects the gist floor directly (fire when base spans < `escalation_min_base_spans`,
  new knob, default 1.0 = fire on zero, 0.0 disables — 75% → 95% on the corpus, +$0.03/100
  observes, the zero-gist class eliminated); **Engram-style deferred write cognition → the
  sequenced-later ledger** as its own spec target (viability assessed: the degradation flags are the
  natural deferred-work queue; the async-observe contract covers the latency motivation; frozen
  write-time facts + a new `write_cause` migration are the spec's real forks). Build: the trigger +
  knob + knob-fetch across `app\nlp.py`/`app\config.py`/`app\ingest.py`; write-path walker 42 → 46;
  suite 43 → 44 ×2 + keyless 36 → 37; six walkers byte-untouched and green; migrate no-op;
  `longmem` pristine. floor-verifier **pass** (all eight criteria; the fake-mode
  stored-rows-byte-identical prediction verified, not assumed). **Known nit left in place**
  (verifier observation, pre-existing at HEAD): the `app\ingest.py:234` comment still says
  "hard-stop on double failure" — stale since the 2026-07-22 soft-degrade, comment-only; fix when
  that file next opens. Next: **Unity + reference scene + The Ledger (immediate-queue item 2)**.

- **2026-07-27** — **Demo-vehicle fork weighed and ruled + item 2 specced (docs only — no code, no
  floors, no migration).** At the state review, Jack re-opened the vehicle question: custom Unity
  scene vs modding the NPC into an established game (Skyrim named), his premise being that Unity
  scene-building has been a time-sink in past projects. A five-agent read-only panel — the four
  audit personas + a web-research scout on the mid-2026 LLM-NPC modding landscape — weighed it;
  findings + the ruling in the dated "Demo-vehicle ruling" `decisions.md` entry. **Ruled: Unity
  gray-box with three de-riskers** — `NpcMemory.Core` built engine-agnostic first (plain .NET,
  zero `UnityEngine` types, one flat client class; a `dotnet run` console harness plays every
  demo beat headless, moving the interop go/no-go Wk-2 → Wk-1), **the Ledger as a browser page**
  (not Unity UI), and the established-game integration deferred to a **post-demo clip on a
  C#-moddable game** (not Skyrim: zero C# reuse, the Mantella comparison class, state-delta
  observes, AGPL on a published fork); the week-3 fallback deliberately NOT pre-ruled.
  **`unity-client.md` written** (the item-2 spec): mechanism per stage (core client + `NpcSession`
  port + console harness + Unity adapter + gray-box set + browser Ledger + choreography hooks)
  and seven open forks for Jack's rulings at plan approval — the headline three: SSE
  `/turn/stream` scope (the <1 s perceived-first-word beat is unrecordable without it; recommended
  in), an agent-provisioning route (`POST /v1/agents` does not exist — the demo agent is hand-SQL;
  recommended in, small), and the Ledger's data source (direct read-only SQL vs a read-only
  `GET /v1/memories/{id}/chain` route — the product-surface option recommended). Queue item 2
  reshaped to the ruled sequence; the artifact-queue Unity entry annotated; the established-game
  clip added to the sequenced-later ledger.

- **2026-07-27** — **Unity-client fork rulings + stage 0 built and floor-verified (second task of
  the day) — the C# client's full backend surface exists.** Jack completed the operator steps
  (Unity 6 project at `unity\`, uv + .NET SDK verified) and **MCP for Unity went live** (read
  probe found the scene camera; `McpVerificationCube` created at origin and deleted;
  console clean — the spec's early-verification step done). All seven `unity-client.md` forks
  ruled via explicit questions (dated "Unity-client fork rulings + stage-0 build" entry in
  `decisions.md`): SSE **in**, `POST /v1/agents` **in**, Ledger data = **the chain read route**,
  Newtonsoft everywhere, targets/layout as proposed, static-HTML Ledger, render shape at build.
  Stage 0 built: the SSE stream route (queue-bridged pump task; pre-stream 404/422 preserved;
  chunk events byte-identical to the terminal content), agent provisioning (server-minted UUID;
  the only new write surface — an agents row, outside the memory-content invariant's subject),
  and the two **unscored** inspector reads (superseded rows present, `has_embedding` never the
  vector, `memories.entities` deliberately not echoed). No migration; no new knobs or roles.
  Verification: walkers 46 → **51** (write, [15] provisioning), 48 → **56** (read, [14]
  inspector), 62 → **67** (CLI, [14] SSE); four untouched walkers green (51/42/34/34) and
  byte-identical to HEAD; suite 44 → **48** ×2 + keyless 37 → **41**; migrate no-op ("5 applied,
  0 pending"); `longmem` pristine via the postgres MCP; floor-verifier **pass** (floor economy:
  exactly nine files). Next: **stage 1 — `NpcMemory.Core` + console harness (the Wk-1 interop
  go/no-go)**.

- **2026-07-27** — **Unity-client stage 1 built and the Wk-1 interop gate is GREEN (third task of
  the day) — the project's first C# is live end-to-end.** `client\NpcMemory.Core\` (netstandard2.1,
  sole dep Newtonsoft 13.0.3, zero `UnityEngine` types): `NpcJson` (the ONE serializer config —
  snake_case naming, `NullValueHandling.Include`, `DateTimeOffset` end-to-end; the null-vs-`[]`
  tri-state never collapsed), `Models.cs` (field-for-field mirror of every wire model), the flat
  `NpcMemoryClient` (ten routes 1:1, per-route settable timeouts, loud typed errors, the SSE
  consumer), `NpcSession` (the `_apply_turn_result` port keyed on the server's gate record;
  boundary snapshot refresh from the last `reputation_after` — exact for a single-client session;
  a multi-client integration would want an agent-state read route, noted in the artifact queue) +
  `client\NpcMemory.Harness\` (net8.0). **The harness ran 21/21 checks green** against a live
  served backend (fake mode, scratch `longmem_smoke`): provisioning → time-travel observes → the
  tri-state wire proof → SSE byte-identity → correction/chain/index → 46-day drift + byte-identical
  reread → gate fire → warm-init pure cache hit → both views; 9 directives resolved through the
  callback path. One build-surfaced fixture fix: the harness config's episodic tau lengthened
  (1 → 7 days) so the fresh-read beat sits inside theta — the first run honestly caught the
  arithmetic (a 2-day-old memory on a 1-day tau serves reconstructed, as designed). floor-verifier
  **pass** (independent full-gate re-run incl. server lifecycle + port-fidelity review;
  interrupted once by a session limit and resumed to completion — the criterion-6d pristine query
  re-ran identically). A NuGet source was absent on the fresh .NET SDK; nuget.org added
  (machine-level, one-time). **Sixteen floors stand verified.** Next: **stage 2 — the Unity
  adapter + gray-box set** (MCP for Unity already verified), then the browser Ledger (stage 3).

- **2026-07-27** — **Unity-client stage 2 built — the adapter + gray-box set, Play-mode gate
  GREEN (fourth task of the day).** The Unity 6 project (URP template, `unity\`) joins the repo
  (79 files; the embedded third-party MCP bridge package + generated solution/caches
  gitignored — the manifest git URL re-resolves the bridge on a fresh clone). New:
  `Assets\Scripts\NpcMemoryNpc.cs` (the thin MonoBehaviour adapter — flat client + `NpcSession`,
  inspector config incl. auto-provision agent fields and decay taus, thin async passthroughs,
  directive/reputation events, zero blocking) and `NpcDemoDriver.cs` (the gray-box demo
  surface — **fork 7 settled at build: an IMGUI dev-tool overlay**, the intended systems
  aesthetic; live streamed dialogue, directive flash on the capsule, gate/reputation readouts,
  a +46d time-jump button; `autoRun` plays scripted Play-mode verification beats with
  `[npc-demo]` console receipts + `Application.runInBackground` so unattended runs keep
  pumping). The set: floor + three walls + Keeper capsule + nameplate + framed camera, built
  via MCP for Unity; the core DLL in `Assets\Plugins` (Release build), Newtonsoft via
  `com.unity.nuget.newtonsoft-json` 3.2.2. **Play-mode gate 8/8**: in-engine provisioning,
  injected-time observes, boundary freeze, loader turn, live streamed chunks byte-identical to
  content, **chunk callbacks ON the main thread (thread 1)**, session bookkeeping live
  in-engine, +9 frames pumped through both turns. **Two build-surfaced fixes, both caught by
  the Play gate:** (1) the core client had `ConfigureAwait(false)` throughout (the standard
  library idiom) — chunk callbacks landed on thread-pool thread 731; ALL removed so
  continuations honor the caller's SynchronizationContext (blocking is banned by the adapter
  contract, so the deadlock hazard the idiom guards against does not apply; documented in
  `NpcMemoryClient`; the console harness re-ran **21/21** after the change); (2) overlapping
  directive flashes captured each other's yellow as "original" — the true color is now
  captured once. One environment fix en route: a PowerShell text edit mojibake'd the core
  files' UTF-8 (ANSI round-trip); restored from git and re-edited UTF-8-safely. Receipts: the
  `[npc-demo]` console transcript + `unity\Captures\graybox-stage2-receipt.png` (*tracked since
  2026-07-28 — it was cited as evidence while gitignored, so the citation pointed at nothing on
  any other machine*); scene saved with `autoRun` off; server torn down, `longmem_smoke` dropped,
  port 8000 free, `longmem` pristine. Next: **stage 3 — the browser Ledger.**

- **2026-07-27** — **Unity-client stage 3 built — The Ledger is live (fifth task of the day;
  item 2's build stages are COMPLETE).** `ledger\index.html` — one static file, vanilla JS, no
  build step (fork 6 as ruled), dev-tool dark aesthetic — **served BY the API at `GET /ledger`**
  (a build-settled shape: same origin as the two inspector routes it polls, so no CORS surface
  and no second server; the inspector ships WITH the service, completing fork 3's
  product-surface logic). Renders: the per-agent index (newest-first, live telling head +
  version count + pinned badges), and per memory the full record — the immutable observation
  with **gist spans marked from the stored offsets**, the current telling, the telling chain
  with **superseded rows greyed-but-present**, the fact chain with embedded/degraded badges +
  entities, and the honest counts (gist spans / telling versions / superseded-kept / fact
  versions; item 3's gist-precision & detail-recall bind here later, stated in the page
  footer). **Turn-feed v1 settled at build:** paste/drop a `DialogueTurnResult` JSON renders
  read_mode/scores/IDs per served item + both scored views + the TTFT line; a live feed rides
  the demo choreography. All text renders via textContent (no injection surface). Verification:
  suite 48 → **49** ×(full) + keyless 41 → **42** (the `/ledger` route contract); a live beat —
  server on scratch `longmem_smoke`, the console harness populated a real fixture agent
  (21/21), then the Ledger in a real browser rendered 4/4 memories and the corrected memory's
  chain read **original (greyed) → authorial_correction (greyed) → reconstruction (live)** —
  the 46-day retelling visibly built ON the corrected content, the record's whole story on one
  screen; the crafted turn-JSON drop rendered the score table + views. Teardown clean (port
  free, smoke dropped, `longmem` pristine). Next: **demo choreography + the pre-ship latency
  items (B1/B2 measure-then-rule) + the judged eval harness (item 3).**

- **2026-07-28** — **Full-repo audit + remediation (Jack's request: audit everything, plan, then
  implement on approval).** Seven read-only dimension auditors, each dimension's findings then
  handed to an adversarial verifier told to refute them: 107 raw findings, 4 refuted, ~20
  downgraded, 64 surviving. Two refutations were because the "problem" was an existing dated
  ruling (CI-later; the gate's cosine import) — the register defending itself. **The audit's
  verdict on the codebase was that it is sound**: zero prose assertions across suite and walkers,
  every UPDATE/DELETE sanctioned, `.env` never in any git ref, all thirty C# wire models
  field-for-field with the tri-state intact, all SQL parameterized. Four rulings and the full
  finding set: the dated "Full-repo audit rulings" entry in `decisions.md`. Eight commits:
  - **Phase 1 — code defects.** The one real defect: `NpcMemoryClient` drove its SSE loop off
    `StreamReader.EndOfStream`, a **synchronous** read, on a client deliberately built without
    `ConfigureAwait(false)` — so it stalled the **Unity main thread** between chunks, on the path
    the <1 s perceived-first-word beat runs on. *The Play-mode gate had passed 8/8 with it
    present* (fake-mode streaming masks the stall), and the verifier later confirmed the blocking
    call was compiled into the shipped DLL. Also: `tests\scratch_uri.py` (one shared, verified URI
    rewrite — the old path-only swap let a `?dbname=` query parameter survive and point the
    suite's TRUNCATE at the product database, proven with libpq's own parser); three dead symbols
    removed (`span_sources` was not merely unread — it was built parallel to `spans` and never
    deduped alongside them, so it was already misaligned); `MalformedWriteProvider` **wired into**
    the write walker rather than deleted, closing the ladder's malformed-output row (51 → 53);
    `load_driver`'s hand-written agents INSERT replaced by `db.insert_agent`; stale comments
    describing the retired escalation hard-stop and the "future" SSE route.
  - **Phase 2 — the mechanical gates.** CLAUDE.md says formatting is "enforced mechanically"; only
    `ruff format` was, `ruff check` had never run as a gate, and **`ruff` was not pinned at all**
    (already drifted — one test file had been out of format since `edf9820`). Pinned; `ruff.toml`
    added with the walkers' deliberate E402 ignored so the two real findings stop drowning in 65;
    `ruff check` joined the edit hook. floor-verifier's allowlist gained the Unity MCP (its
    absence would have reproduced the exact 2026-07-13 incident its own runbook documents);
    doc-auditor's reading list named 5 of 17 docs, omitting every build spec; the `.env` deny
    covered one tool; the Unity `.gitignore` block was unanchored at repo root (the hazard that
    already forced rescue commit `ae54af8`).
  - **Phase 3 — coverage.** Enumerating every route against every test found `PUT /pin` and
    `POST /events/scene-boundary` with **no HTTP test anywhere**, the SSE `reconstructing` and
    `error` events untested, and `CorrectionNlpFailedError` → 502 ruled and built with neither a
    test nor a spec row. Writing the SSE test surfaced a design fact worth recording: the
    pre-serve callback rides **gated turns only** (the signal that earns a spinner is a pause
    appearing mid-scene, not a scene's first read) — the first draft used a loader turn and
    correctly failed. Suite 49 → 53.
  - **Phase 4 — propagation.** The four 2026-07-27 build sessions had propagated into `status.md`
    only. `architecture.md` — self-declared design truth — knew nothing of the five routes shipped
    that day; the IDs-and-scores invariant was **false as written** for the two unscored inspector
    reads, in three files including auto-loaded CLAUDE.md; the model-role claim was wrong in two
    ways (seven vars, not nine roles; three cannot diverge); the register still called the
    escalation hard-stop an open decision owed before the demo, and stopped at stage 0. Fixed,
    plus a 42-entry index for `decisions.md`. `client_total_ms` was **built** rather than struck —
    `unity-client.md` asserted the client recorded it and no C# file did.
  - **Phase 5 — the split** (ruled). `status.md` 1294 → 319 lines, 145,787 → 24,728 chars: roughly
    **30k tokens off every future session's baseline**, history moved not lost.
  - **Phase 6 — onboarding.** LICENSE (canonical text, not recalled), NOTICE (licences read from
    installed metadata — psycopg is LGPL-3.0-only and was unremarked anywhere), `.env.example`,
    `docs\SETUP.md` (the clone-to-running path, including the DLL refresh procedure that existed
    nowhere), `docs\README.md` (the index, and the first definition of "walker" vs "suite" vs
    "floor" — vocabulary used 150+ times and defined nowhere).
  - **Phase 7 — research writing into version control** (ruled), and the stage-2 Play-mode receipt
    PNG un-ignored: `session-log.md` cited it as verification evidence while `.gitignore` excluded
    it.
  - **`.gitattributes` + a self-inflicted repair.** My own phase-7 path rewrite used
    `docs\research\` in a non-raw Python string, so `\r` became a literal CR in six docs. That
    stray CR also made git decline to normalize those files, which is how a two-line edit rendered
    as a 971-line rewrite. Repaired at the byte level; `.gitattributes` now pins `* text=auto
    eol=lf` so it cannot recur. Found by checking the diff rather than trusting it — and the
    grep primitive I first reached for was itself lying (same count for a pure-LF control as for
    CRLF), which is why the first look seemed fine.
  - **floor-verifier: FAIL, then fixed.** The first pass returned **fail** on one real point: a
    `ruff format` run with `target-version` briefly set had stripped the parentheses from
    `except (A, B):` in `app\ingest.py` — the exact hazard `ruff.toml`'s own comment describes,
    shipped in the same commit as the comment. Behaviour on 3.14 was unchanged (the forms are
    AST-identical, which is why every test passed and an AST-level diff showed nothing); the
    verifier found it with a token-stream diff. Restored, and `tests\test_repo_hygiene.py` now
    guards it plus the SQL-only-in-db.py stack constant — both pure, both on the turn-end subset.
    Suite 53 → **55**, keyless **48**. Walkers unchanged at 53/56/67/51/42/34/34.
  - **Not claimed:** the Unity **Play-mode gate** was not re-run — its MCP tools were not exposed
    to this session, so it is an operator step and is reported blocked, not passed. It matters
    more than usual here because the DLL Unity loads was rebuilt twice.


---

## Archived phase headers

*Moved here from `status.md` on 2026-07-28. These were the "Prior phase" blocks stacked
at the top of the living file — each a snapshot of what the current phase was when it was
written. Kept verbatim: they are the most readable summary of each build era, and the
session-log entries below them carry the detail. Newest first, as they were.*

**Prior phase:** **the HTTP dialogue-turn route is LIVE — Unity's front door exists** (2026-07-23,
immediate-queue item 1, the audit's #1 blocker closed; plan-as-spec session). `POST
/v1/dialogue/turn` (`app\api.py`; `DialogueService` joins the lifespan) drains the split-brain
seam's async generator to the terminal `DialogueTurnResult` — **stateless** (all scene state rides
the request; the runner bookkeeping is the CLIENT'S job — the future C# `NpcSession` ports
`_apply_turn_result`), non-streaming, `UnknownAgentError` → 404 / `UnknownIdentityVersionError` →
422, pass-through by ruling, `on_reconstruct=None`; a future SSE `/turn/stream` iterates the SAME
generator — no rewrite. Beside it the **honest latency metric**: `perceived_first_word_ms` clocks
the same first-chunk instant from TURN START (retrieval-inclusive — it sees the cold-reconstruction
stall `first_word_ms` is blind to; 0.0 when no chunk arrives); the **<1 s bar is measured against
it**; surfaced in the CLI debug line + a `perceived_first_word` driver series. Ruled at plan
approval: the audit engineer's **thread-pool cap is deferred post-demo** (the build is exactly the
queue item; dated `decisions.md` entry). No migration (ledger 001–005); no new knobs or roles.
**Fourteen floors stand verified** — floor-verifier **pass** twice today (CLI-harness walker 55 →
62; suite 42 → 43 ×2 + keyless subset 36; migrate no-op; `longmem` pristine; live serve HTTP beat —
perceived 22.87 ms vs first_word 0.42 ms on the smoke — + a standalone driver run). **Same-day
follow-on: the escalation trigger-tuning open question is CLOSED** (measured, then ruled): the fire
rate is productive (85% of escalations add real gist content), the defaults stand, and a sixth
**thin_gist** span-floor trigger closes the measured zero-gist hole (16/80 observes had landed with
no gist spans — reconstruction's fixed constraint empty on those rows); Engram-style deferred write
cognition is queued to the ledger; write-path walker 42 → 46, suite 43 → 44, floor-verifier
**pass**. Next: **Unity project + reference scene + The Ledger** (immediate-queue item 2) — **the
demo vehicle is ruled 2026-07-27** (Unity gray-box, not an established-game mod; engine-agnostic
`NpcMemory.Core` + a console harness first with the interop gate moved to Wk-1; the Ledger a
browser page; the established-game clip deferred post-demo to a C# game — dated "Demo-vehicle
ruling" entry in `decisions.md`, specced in `unity-client.md`) — then the pre-ship gates.

**Prior phase:** **external-persona audit landed — the pre-demo path is re-planned** (2026-07-22). A
four-persona read-only agent-team audit (critique + solutions; `external-audit-2026-07-22.md` +
`external-audit-2026-07-22-solutions.md`; rulings in the dated `decisions.md` entry) surfaced the
true blocker, confirmed against source: **`app\api.py` has no HTTP dialogue-turn route**, so Unity/C#
cannot reach a dialogue turn today. Three rulings: split-brain divergence → a **separate interview
clip** (not a main-video beat); the demo records **real-providers-only** (so the `.env` fix is now a
hard prerequisite); the **judged eval harness is pulled pre-demo** (with a judge-free demo panel + a
hand-labeled gold set + the fixed-gist ON/OFF ablation). Build order: `.env` fix → `POST
/v1/dialogue/turn` + honest perceived-TTFT → Unity + **The Ledger** → judged eval. First pre-ship item
since taken off the queue: the **escalation soft-degrade** (migration 005, floor-verifier **pass** —
the 2026-07-13 fail-loud hard-stop retired). **Prior phase: split-brain streaming is BUILT — the latency topology is
live** (2026-07-21,
immediate-queue item 1, specced and built the same day). The dialogue seam is now an async
generator: a streaming **pure-prose** call and a concurrent **behavior** call (directive +
delta, a new model role) fire off one retrieval; **first word = prose TTFT** (`first_word_ms`,
the headline latency term). Two scored views ride one candidate set — the dialogue view (served
ranking) and the behavior view (same served set re-ranked with the now-live `WeightOverrides`,
exponent-form so all-1.0 is byte-parity with the dialogue view) — and the turn result carries
both as the **divergence record** (§13's raw data). A caller-held **recent-actions** block feeds
past actions to later prose prompts as world facts; the four split-brain degradation rows
(behavior fail, prose-fail-pre-chunk, mid-stream keep-partial, both-fail) all landed. No
migration. **Twelve floors stand verified.** Verification (this session, inline): CLI-harness
walker re-opened 36 → 55; read-path walker weight_overrides criterion re-scoped (48); gate
walker rename-only (51); write/reconstruction/authorial/fact walkers byte-untouched and green
(40/42/34/34); full suite 41 → 42 (twice) + keyless subset 35; no-arg migrate "4 applied, 0
pending"; `longmem` pristine via the postgres MCP; live piped REPL streaming beat + a driver run
with the `first_word` + `behavior` series and the behavior cost row. **Flagged (operator-owned
`.env`, not fixed):** a malformed consolidated `LONGMEM_PRICE_DIALOGUE_IN=…` line crashes
`load_settings` on any run that reads `.env` prices — Jack's to fix before real-mode demo runs
*(fixed and verified 2026-07-22 — queue item 0)*.

**Prior phase:** **real mode is proven — pre-ship gates (b) and (c) are closed** (2026-07-21, the
first-ever real-provider session, run with live ANTHROPIC + OPENAI keys). The smoke's
live observe/reconstruction/dialogue receipts are on record, and the real-mode profiling is
diffed against the 2026-07-20 fake baseline: **every infra series flat** (sql, nlp, insert,
gate, correction txn, degraded scan, connection floor — the fake-mode fixes held), with the
true picture LLM-dominated as predicted — observe p50 3.4 s (haiku 1.7 s + escalation 1.4 s
when it fires), dialogue turn p50 4.1 s (first-token 2.2 s), loader read ~180 ms (real query
embed ~175 ms), cold 8-item reconstruction 16.3 s, cache-hit reread 3.7 ms call-free,
**$0.44/100 priced turns** (standard rates). **A build-surfaced defect was ruled, fixed, and
floor-verified same-session** (commit `1388bf6`, `app\providers.py` parse hardening —
sonnet-5's leading thinking block crashed reconstruction and haiku's markdown-fenced JSON
hard-stopped every escalating observe; suite 41/41 ×2, all seven walkers green,
floor-verifier **pass**). **Report-only calibration findings now await rulings:** escalation
fires **79% on realistic prose** (0% on synthetic driver prose — prose-dependent; feeds the
owed failure-path re-rule, now with real data and 0 hard-stops in 80 observes); the gate
novelty CDF separates cleanly under real embeddings (0.3 fire-budget ⇒ threshold ~0.59 on
realistic prose); the 0.35 drift budget is well-placed (max observed accepted drift 0.244);
the lexical channel's ts_rank cost is a linear-in-matches watch-item (the 004 GIN is proven
by EXPLAIN). **Prior phase:** the research-adoption slate landed 2026-07-21 (Target A
encoding-context term + Target B hybrid lexical channel, migration 004);
`docs\research\CHANGES-FROM-RESEARCH.md` traces provenance. **One open decision owed before
the demo ships:** the escalation failure-path re-rule — now widened by the data to cover the
trigger set/threshold too. **Same-day follow-on: the latency slate is ruled and the split-brain
topology is pulled forward + specced** (`split-brain-streaming.md`; viability bar **first word <
~1 s**; all four latency levers land pre-demo — see the queue and the dated register entry).
