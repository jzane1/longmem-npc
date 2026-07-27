# longmem-npc — Status

**Last updated:** 2026-07-27
**Phase:** **unity-client stage 0 is LIVE — the C# client's full backend surface exists**
(2026-07-27, second task of the day; all seven `unity-client.md` forks ruled + **MCP for Unity
verified live** — read probe + cube round-trip + clean console). Three new routes beside the
existing six: **SSE `POST /v1/dialogue/turn/stream`** (the SAME async-generator seam over
text/event-stream — `chunk`/`reconstructing`/`result` events via a queue-bridged pump task;
pre-stream errors still map 404/422; chunk events byte-identical to the terminal content — the
<1 s perceived-first-word beat is now recordable), **`POST /v1/agents`** (server-minted UUID,
exact-fields storage, NULL knobs resolve config → `SERVICE_DEFAULTS`; the integrator's
minute-one gap closed), and **The Ledger's inspector reads** — `GET /v1/memories/{id}/chain`
(the immutable observation beside BOTH version chains, superseded rows present, gist spans;
**unscored by ruled contract** — no retrieval runs, IDs on every row) + `GET
/v1/agents/{id}/memories` (the index beside the live telling head, newest-first, `limit` a
caller arg). No migration (ledger 001–005); no new knobs or roles. **Fifteen floors stand
verified** — floor-verifier **pass** (walkers grown 46 → 51 / 48 → 56 / 62 → 67, four untouched
walkers green + byte-identical; suite 44 → 48 ×2 + keyless 37 → 41; migrate no-op; `longmem`
pristine; floor economy exactly nine files by git diff). The demo-vehicle ruling + the fork
rulings are the two dated 2026-07-27 `decisions.md` entries. **Same-day follow-on: stage 1 is
BUILT and the Wk-1 interop go/no-go is GREEN** (third task of the day) — `client\NpcMemory.Core`
(netstandard2.1, zero `UnityEngine` types, Newtonsoft everywhere, the flat `NpcMemoryClient` +
the `NpcSession` port of `_apply_turn_result`) + the `dotnet run` console harness passed **all
21 checks** live against the served API (fake mode, scratch `longmem_smoke`): provisioning →
time-travel observes → the **null-vs-`[]` tri-state proof on the wire** (null → loader;
populated → evaluated; explicit `[]` → evaluated) → SSE chunks byte-identical to content
(perceived > first_word > 0) → correction both-head swap + chain/index inspection → 46-day
reconstruction (write_backs 3) with a byte-identical within-scene cache-hit reread → a
mid-scene gate fire appending the unseen memory → warm-init then a pure cache-hit on-camera
turn (write_backs 0, cache_hits 4) → both scored views. floor-verifier **pass** (independent
re-run of the whole gate incl. server lifecycle; port fidelity verified side-by-side against
`app\session.py`; `client\` has no SQL and no hardcoded config; the stage-0 floor byte-untouched
— **sixteen floors stand verified**). **And stage 2 is BUILT with its Play-mode gate GREEN**
(fourth task of the day): the Unity project joins the repo (`unity\`, URP template; the embedded
MCP bridge package gitignored — the manifest git URL re-resolves it) with the thin adapter
(`Assets\Scripts\NpcMemoryNpc.cs` — one MonoBehaviour holding the flat client + `NpcSession`,
inspector config, zero blocking) + the gray-box demo surface (`NpcDemoDriver.cs` — IMGUI
dev-tool overlay, fork 7 settled at build; live streamed dialogue, directive flash,
gate/reputation readouts) + the set (floor, walls, Keeper capsule, nameplate, framed camera;
core DLL in `Assets\Plugins`, Newtonsoft via Unity's package). **Play-mode beats: 8/8 green** —
provisioned over the API from in-engine, streamed chunks byte-identical AND rendered live,
**chunk callbacks on the main thread (thread 1)**, session bookkeeping live in-engine, frames
pumping. Two build-surfaced fixes, both caught by the Play gate: the core client dropped every
`ConfigureAwait(false)` (continuations now honor the caller's SynchronizationContext — the
Unity main-thread contract; blocking is banned so the library-deadlock hazard doesn't apply;
console harness re-run 21/21 after the change) and the directive flash's re-entrancy color
capture. **And stage 3 is BUILT and live-verified (fifth task)** — The Ledger (`ledger\index.html`,
served by the API at `GET /ledger`; suite 48 → 49) rendered a real fixture agent's corrected
chain in the browser: original greyed → correction greyed → reconstruction live. **Item 2's
build stages are COMPLETE**; remaining before recording: demo choreography + the demo corpus,
the B1/B2 latency experiments, and the judged eval harness (item 3). Note: stages 2–3 carry
live receipts (Play-mode console transcript, browser beat, suite growth) — an independent
floor-verifier pass over their re-runnable halves is the next session's opening step.

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
`Research Papers\CHANGES-FROM-RESEARCH.md` traces provenance. **One open decision owed before
the demo ships:** the escalation failure-path re-rule — now widened by the data to cover the
trigger set/threshold too. **Same-day follow-on: the latency slate is ruled and the split-brain
topology is pulled forward + specced** (`split-brain-streaming.md`; viability bar **first word <
~1 s**; all four latency levers land pre-demo — see the queue and the dated register entry).

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

| Encoding-context read term v1 + gate-calibration utility — the research-adoption slate's Target A (ruled 2026-07-20 with the plan; RaMem arXiv 2606.22844 + TARG 2511.09803 — `Research Papers\CHANGES-FROM-RESEARCH.md` traces provenance): the formerly-reserved `DialogueInitRequest` context fields (`location_name`/`entities`/`event_time`) are **consumed** as client-supplied scene context — a soft multiplicative nudge `score ×= 1 + Σ w_i·match_i` (fact-head entity coverage, casefolded; `exp(−Δ/scale)` event-time kernel; casefold location match), **never a filter or penalty, ≥ 1 always**; a no-context request skips the term — **scoring byte-identical to v1** (the parity contract). Four knobs in `SERVICE_DEFAULTS` (per-agent overridable); applies on loader + gated (same context to loaded and fetched) + degraded paths; instrumentation-level surfacing (`context_active`/`context_components`) so the scored tuple and serving stage stay untouched. `CandidateRow`/`_CANDIDATE_COLUMNS` widened (+ `event_time`/`location_name`/`fact_entities`; degraded FROM gains a LEFT JOIN so legacy-shaped rows stay reachable); `DialogueTurnRequest` + session-runner scene context (scene-boundary reset) + REPL `:context`; `weight_overrides` **stays reserved**. A2: `--gate-budget` TARG-style calibration in the load driver — **report-only**, (1−rate)-quantile threshold recommendation off the run's novelty-distance CDF. **No migration** — schema frozen at 001+002+003. | floor-verifier **pass** against all eight prior floors (read-path floor deliberately re-opened — the one ruling-driven walker change): `tests\verify_read_path.py` re-run independently on fresh scratch (**42 assertions**, grown 36 → 42 — criterion [7] re-scoped from "reserved fields inert" to the context contract: no-context parity, exact ×1.75 / ×1.125 / ×1.0 factors casefolded both sides, factor-moves-score-only, never-echoed, weight_overrides-only still inert); the other six walkers **byte-identical to HEAD** and re-run green on fresh scratch (40/36/42/34/34/51); full suite **40 passed twice** (grown 38 → 40: Set B parity + exact factor, Set D gated-path factor with the gate decision proven untouched) + the keyless `-m "not nlp"` subset (33/33, API keys scrubbed in-process); `db\migrate.py` no-arg → "Up to date: 3 migration(s) applied, 0 pending"; `longmem` pristine via the postgres MCP (exact COUNT(*) on all ten product tables → 0; ledger exactly 001+002+003; no scratch residue); seven independent code spot-checks (context=None takes the v1 arithmetic path verbatim; `context_boost` pure, exactly 1.0 on no-match; same context to loaded+fetched; `gate.decide` inputs context-free; degraded LEFT JOIN proven with a live legacy-shaped row; `weight_overrides` consumer-free by grep; calibration writes nothing); plus a live piped REPL beat (stamped row score exactly ×1.75 under `:context entities=mara loc="the forge" time=<iso>`, bare row unchanged, `context: active (entities, event_time, location)` debug line, `:context clear`) and a standalone load-driver run with the `--gate-budget 0.3` calibration block | 2026-07-21 |

| Hybrid lexical retrieval channel v1 — the research-adoption slate's Target B (ruled 2026-07-20; survey 2604.01707 §7 + Engram 2606.09900): **migration 004** (`db\migrations\004_lexical_index.sql`, index-only — partial FTS GIN `to_tsvector('simple', basis_text)` over live fact heads, the 002/003 partial-index precedent) + the token-OR lexical candidate fetch (`lexical_tsquery`: casefolded ≥3-letter letter-runs, deduped, capped 16, OR-joined — the build-surfaced correction over websearch/plainto AND semantics, which would have made the channel inert; ts_rank + memory_id deterministic LIMIT) **unioned into the loader's vector over-fetch before scoring** — dedup by memory_id, scoring formula untouched, lexical hits carry their TRUE cosine distance (all-named params), NULL-embedding fact heads lexically reachable with relevance null (never a filter — exact-token recall softens the embed-degradation consequence). `lexical_fetch_k` knob (8.0; **0.0 = kill-switch**, pure-vector v1); `text_search_config` string knob ('simple' default baked into the index expression, the decay_classes plain-key precedent; overrides run unindexed, stated). Loader-scope v1 — the gate fire probe + entity-only rung are noted future consumers. Instrumentation `lexical_sql_ms` + `lexical_candidate_count`; CLI debug `lex=` field. | floor-verifier **pass** against all nine prior floors (read-path floor re-opened, re-verified; the gate walker's sole change is the mechanical ledger pin +004): `tests\verify_read_path.py` re-run independently on fresh scratch (**48 assertions**, 42 → 48 — new criterion [13]: lexical-only reach proven through the SERVED payload on a k=1/overfetch-1.0 agent, raw-2/union-2 exact dedup, unchanged formula, tokenless zero-SQL, kill-switch restores v1; criterion [9] **sharpened**: vector-path exclusion asserted on the probe itself + the honest lexical reach of an embed-degraded row); all seven walkers green on fresh scratch (40/48/36/42/34/34/51); migration 004 applied 001→004 in order on fresh scratch with an idempotent second run; **applied to `longmem`** — no-arg migrate → "Up to date: 4 migration(s) applied, 0 pending", index present with the exact expression + predicate (pg_indexes.indexdef); `longmem` pristine via the postgres MCP (exact COUNT(*) 0 on all ten product tables, ledger exactly 001..004, no scratch residue); full suite **41 passed twice** (40 → 41: the Set B lexical reach + kill-switch scenario) + keyless subset 34/34; floor economy by git-diff (reconstruction/gate/decay/ingest/dialogue/session/conftest and five walkers byte-identical to HEAD); seven independent code spot-checks (004 index-only; injection-safe tokenizer; additive-only union; v1-byte-identical when disabled/tokenless/gated/degraded; default-branch expression textually matches the index; all-named params; `_score_rows` zero hunks in this diff); plus the live REPL beat (k=1/overfetch-1.0: the pinned rare-name row served via lexical reach, `lex=2/3.63ms candidates=2 k=1`) | 2026-07-21 |

| Structural pytest suite v1 — `pytest.ini` (marker registration, `testpaths`, no cache residue) + `tests\conftest.py` (scratch **`longmem_suite`** session lifecycle: probe → create → migrate 001–003 → per-test TRUNCATE → drop; unreachable ⇒ loud skip, exit green; db-layer `InsertPlan` seeding with the pure fake embedding — the fast path never imports the NLP loaders; per-set configs with production-vs-fixture pins stated) + **38 scenarios** in five `test_*.py` files (Set A: authorial + fact chain incl. the db-layer distance-0 rank pair, CAS rollback, the pure constraint-follows-anchor test, and the marked route contract; Set B: decay-vs-invalidation incl. the two-time-travel-mechanics-agree and IDs-on-the-wire pairs; Set C: write-back chain shape, cache hit/frozen basis, band crossing, identity bump, correction eviction + re-anchor, drift refusal + refusal caching; Set D: loader parity, closed gate, novelty/tripwire/both fires, damper + reset, efficacy, runner append-only, marked entities-follow-correction; degradation: every ruled ladder row incl. the build-phase hard-stop, flagged as such in its docstring) + the Stop-hook subset edit (`-m "not nlp"`, ruled) + `pytest==9.1.1`/`httpx==0.28.1` pins | floor-verifier **pass** against all eight prior floors, standing by construction: `app\`, `db\`, and all seven walkers **byte-identical to HEAD** (the verifier's recorded git-diff proof — identical bytes need no re-run); full suite re-run twice independently (38/38, 38/38 — the determinism criterion), the subset re-run with API keys scrubbed (31/31 in ~14 s — the keyless + no-spaCy proof), the unreachable-skip beat (30 skipped + the one pure no-DB test, exit 0, loud warning), the hook contract both ways (green → exit 0; `stop_hook_active` guard short-circuits; red path + dormant guards read intact with the subset flag), a structural-only audit of all five files (no assertion touches model prose), no-arg migrate → "Up to date: 3 migration(s) applied, 0 pending", `longmem` pristine via the postgres MCP (ten product tables 0 rows, ledger 001+002+003, **no `longmem_suite` residue**), and pins == installed versions | 2026-07-20 |

| Split-brain streaming v1 — the dialogue seam re-shaped into two concurrent calls off one retrieval (`split-brain-streaming.md`, ruled topology; the reserved `WeightOverrides` slot goes live for the behavior view): the streaming **prose** call (`app\providers.py` `DialogueProvider.stream_prose` — a sync generator yielding chunks + a `ProseResult`; real streams raw text, no JSON) + the concurrent **behavior** call (`BehaviorProvider.decide` — directive + delta JSON, new `LONGMEM_MODEL_BEHAVIOR` role + `LONGMEM_PRICE_BEHAVIOR_IN/OUT`, hardened parse) + the async-generator seam (`app\dialogue.py` `run_dialogue_turn`: retrieval once → two views → concurrent legs via a worker-thread + `asyncio.Queue` bridge → validate/apply → terminal `DialogueTurnResult`; prompt split `assemble_prose_prompt`/`assemble_behavior_prompt` with a recent-actions block, prose prompt only; behavior view = `rank_behavior_view` exponent-form re-rank of the served set, `resolve_behavior_weights` clamp `[0,4]`) + caller-held recent-actions scene state + `stream_utterance`/`utterance` (`app\session.py`) + REPL live streaming + divergence debug view (`app\cli.py`) + `first_word`/`behavior` series + behavior cost row (`app\load_driver.py`) + wire deltas (`app\schemas.py`: `first_word_ms`/`prose_stream_ms`/`behavior_ms`/behavior tokens; `dialogue_view`/`behavior_view` `ScoredRef` divergence record; `RecentAction`; `weight_overrides` live on `DialogueTurnRequest`). No migration | verified inline this session against all eleven prior floors: **CLI-harness walker re-opened `tests\verify_cli_harness.py` (36 → 55 assertions** incl. concurrency proved with a slow behavior fake — first chunk 0.008 s vs behavior 300 ms; dialogue-view parity at 1.0 + exponent re-rank flip on crafted items; the divergence record; the recent-actions block appears iff scene actions and clears at `:scene`; all four degradation rows) on fresh scratch; read-path walker weight_overrides criterion re-scoped (48); gate walker `assemble_system_prompt` → `assemble_prose_prompt` rename-only (51); write/reconstruction/authorial/fact walkers **byte-identical to HEAD** and green (40/42/34/34); full suite **41 → 42 passed twice** (+ the split-brain divergence/parity scenario) + keyless subset 35; no-arg migrate → "Up to date: 4 migration(s) applied, 0 pending"; `longmem` pristine via the postgres MCP (ten product tables 0 rows, ledger 001–004, no scratch residue); live piped REPL streaming beat + a standalone driver run. **floor-verifier pass** (independent, fresh context — re-ran all ten done-when + all seven walkers on fresh scratch 55/48/51/40/42/34/34, full suite 42 ×2 + keyless subset 35, no-arg migrate "4 applied, 0 pending", `longmem` pristine via the postgres MCP, the ten untouched app files + four untouched walkers confirmed byte-identical to HEAD~1 by git-diff, no invariant violated — sole persisted write is the sanctioned `agents.reputation` UPDATE). | 2026-07-21 |

| Escalation soft-degrade v1 — **migration 005** (`db\migrations\005_escalation_failed.sql`: `memories.escalation_failed boolean NOT NULL DEFAULT false`, mirroring `scoring_failed`) + the observe-path soft-degrade (`app\ingest.py` `_escalate_with_retry` returns `None` on double failure instead of raising; the write proceeds with the base NLP-pass gist and sets `escalation_failed`; `EscalationHardStopError` + its observe-route 502 removed) + the flag on `InsertPlan` → the new column and `IngestResult` (`app\db.py`, `app\schemas.py`) + the `app\cli.py` consumer removed (import + REPL `except`, build-surfaced by the floor-verifier). Retires the 2026-07-13 fail-loud hard-stop (ruled 2026-07-22); the correction verb's own fail-loud embed/NER → 502 paths untouched. The trigger-set/threshold tuning (79%-fire) stays a separate open item. | floor-verifier **pass** (write-path floor re-opened, re-verified): `tests\verify_write_path.py` **42** on fresh scratch with the flipped [11] soft-degrade (write lands + `escalation_failed` True on the result AND the column); the two build-surfaced breakages fixed and re-verified — `verify_cli_harness.py` **55** (`app\cli.py` import/except removed) and `verify_gate.py` **51** (mechanical ledger pin +005, the 004 precedent); read/reconstruction/authorial/fact walkers green (48/42/34/34); full suite **42** + keyless subset **35**; migration 005 applied 001→005 on fresh scratch + idempotent second run + column DDL `boolean NOT NULL DEFAULT false`; **applied to `longmem`** (no-arg migrate → "5 migration(s) applied, 0 pending"); `longmem` pristine via the postgres MCP (ten product tables 0 rows, ledger 001–005, no scratch residue); invariants intact (non-destructive proceed — a row lands flagged, never a lost write; no in-place content UPDATE; sole DELETE remains the correction cache eviction). | 2026-07-22 |

| HTTP dialogue-turn route + perceived-TTFT v1 — the Unity/C# front door (audit-replan item 1): `POST /v1/dialogue/turn` (`app\api.py`; `DialogueService` joins the lifespan) drains `run_dialogue_turn`'s async generator to the terminal `DialogueTurnResult` — **stateless** (scene state caller-held on the request; runner bookkeeping stays client-side — the future C# `NpcSession` ports `_apply_turn_result`), non-streaming, `UnknownAgentError` → 404 / `UnknownIdentityVersionError` → 422 (the existing precedents), pass-through by ruling, `on_reconstruct=None` (no during-wait signal without SSE; the post-hoc fields carry it); a future SSE `/turn/stream` iterates the SAME generator + the honest latency metric `perceived_first_word_ms` (`app\schemas.py`; captured in `app\dialogue.py` at the same first-chunk instant as `first_word_ms`, clocked from `t_total` — retrieval-inclusive, sees the cold-reconstruction stall; 0.0 when no chunk arrives; the <1 s bar's field) surfaced in the CLI debug line (`app\cli.py`) + the `perceived_first_word` driver series (`app\load_driver.py`). Thread-pool cap ruled deferred post-demo. No migration; no new knobs or roles. | floor-verifier **pass** against all twelve prior floors (CLI-harness floor re-opened, re-verified): `tests\verify_cli_harness.py` **62** on fresh scratch (55 → 62 — new section [13]: route JSON == the drained seam result via ASGITransport + a capturing wrapper, 404 + 422; perceived > first_word > 0 in [1]; both-TTFT-zero on the pre-chunk-failure row in [9]; the driver series in [12]); six other walkers green on fresh scratch (48/51/42/42/34/34) and — with every other `app\` file, `conftest`, and the four other suite files — **byte-identical to HEAD by git-diff** (the floor-economy proof); full suite **43 ×2** + keyless subset **36** (the new unmarked Set D route-contract scenario); no-arg migrate → "Up to date: 5 migration(s) applied, 0 pending"; `longmem` pristine via the postgres MCP (ten product tables 0 rows, ledger 001–005, no scratch residue); independent code spot-checks (route adds/drops nothing; stateless — the sole persisted write of a turn remains the sanctioned `agents.reputation` UPDATE inside the seam; both TTFT fields one-instant captured from `t_prose` vs `t_total`; structural-only test additions); plus a live `python -m app.serve` HTTP beat (observe → turn with IDs + scores + both views + both TTFT fields → unknown-agent 404) and a standalone driver run emitting the `perceived_first_word` series. | 2026-07-23 |

| Escalation thin_gist trigger v1 — the trigger-tuning ruling's build (same day as the turn route; the dated "Escalation trigger tuning" entry in `decisions.md` carries the full measurement): a **sixth escalation trigger `thin_gist`** (`app\nlp.py` `evaluate_triggers`, appended LAST — the biased-loose add-only contract preserved) fires when the base NLP pass yields fewer gist spans than `escalation_min_base_spans` (new `SERVICE_DEFAULTS` knob, default 1.0 = fire on a zero-span base pass; 0.0 disables; per-agent overridable, fetched with the other escalation knobs in `app\ingest.py`). Closes the measured **zero-gist hole** — 16/80 realistic observes otherwise landed with NO gist spans, leaving reconstruction's fixed constraint empty on those rows (75% → 95% fire on the corpus, ~+$0.03/100 observes). The five original triggers + thresholds stand unchanged by ruling. No migration; no new model roles. | floor-verifier **pass** against all thirteen prior floors (write-path floor re-opened, re-verified): `tests\verify_write_path.py` **46** on fresh scratch (42 → 46 — [11b]: thin_gist fires ALONE on a zero-span pass at production knobs, the 0.0 kill-switch, floor-compares-the-COUNT, and the measured sexton fixture escalating with thin_gist as the SOLE trigger at the service level); six other walkers green on fresh scratch (62/48/51/42/34/34) and — with every other `app\` file — byte-identical to HEAD by git accounting; full suite **44 ×2** + keyless subset **37** (the new pure `test_thin_gist_trigger_pure` asserts over production `SERVICE_DEFAULTS`, no DB/NLP — it rides the Stop-hook subset); no-arg migrate → "Up to date: 5 migration(s) applied, 0 pending"; `longmem` pristine via the postgres MCP (ten product tables 0 rows, ledger 001–005, no scratch residue); code spot-checks (trigger add-only and appended last, the knob's floor value lives only in `SERVICE_DEFAULTS`, the 2026-07-22 soft-degrade path untouched and re-proved live, no new writes/UPDATE/DELETE); the predicted fake-mode consequence verified, not assumed (stored fixture rows byte-identical — only escalated/escalated_by/timing moved; no foreign assertion touched). | 2026-07-23 |

| Unity-client stage 0 v1 — the C# client's backend surface (unity-client.md forks 1–3, ruled 2026-07-27): **SSE `POST /v1/dialogue/turn/stream`** (`app\api.py` — iterates the SAME `run_dialogue_turn` async generator via a queue-bridged pump task; `chunk` events JSON-encoded, an optional `reconstructing` event off the pre-serve callback, terminal `result` = the seam result's serialization; the FIRST queue item awaited before the response starts so unknown-agent/version still map 404/422; in-stream failure → an `error` event; a task-reference set so a client disconnect never aborts the turn server-side) + **`POST /v1/agents`** (`db.insert_agent` + `IngestService.create_agent` + `CreateAgentRequest/Result` — server-minted UUID, exact-fields storage, NULL knobs resolve config → `SERVICE_DEFAULTS`; the build's only new write surface, an agents row outside the memory-content invariant's subject) + the **unscored inspector reads** (`GET /v1/memories/{id}/chain` + `GET /v1/agents/{id}/memories` — `db.fetch_memory_chain`/`fetch_agent_memories` + `RetrievalService.memory_chain`/`agent_memories` + chain/index wire models: both version chains ordered (valid_at, created_at) with superseded rows PRESENT, gist spans, `has_embedding` never the vector, `memories.entities` deliberately not echoed, the index LEFT JOINed to the live telling head, `limit` a caller arg 1–1000). No migration (ledger 001–005); no new knobs or model roles. | floor-verifier **pass** against all fourteen prior floors (write-path + read-path + CLI-harness floors re-opened, re-verified): `tests\verify_write_path.py` **51** on fresh scratch (46 → 51 — [15] provisioning: server-minted row with exact fields + NULL knobs, pass-through echo, the provisioned agent immediately a working write target, empty name 422); `tests\verify_read_path.py` **56** (48 → 56 — [14] inspector reads: superseded telling row PRESENT with coherent timeline after a db-layer correction, fact chain with `has_embedding` + entities, index newest-first beside the LIVE head, limit-vs-total_count, both 404s); `tests\verify_cli_harness.py` **67** (62 → 67 — [14] SSE: 200 text/event-stream, chunk-event count == the seam's, chunks concatenate BYTE-IDENTICALLY to the result's content, result event == the seam serialization, pre-stream 404); four untouched walkers green on fresh scratch (51/42/34/34) and byte-identical to HEAD by git diff; suite **48 ×2** + keyless subset **41** (four new unmarked route-contract scenarios in `test_set_d_gate.py`); no-arg migrate → "Up to date: 5 migration(s) applied, 0 pending"; `longmem` pristine via the postgres MCP (ledger 001–005, ten product tables 0 rows, no scratch residue); invariants (the only new write is the agents INSERT; inspector reads SELECT-only end to end; the turn's sole persisted write remains the sanctioned reputation UPDATE — `app\dialogue.py` byte-identical); floor economy exactly nine files. | 2026-07-27 |

| Unity-client stage 1 v1 — `NpcMemory.Core` + the console harness, the Wk-1 interop go/no-go (unity-client.md ruled shape; the project's first C#): `client\NpcMemory.Core\` (**netstandard2.1** — the Unity 6 compatibility profile; sole dependency Newtonsoft.Json 13.0.3; **zero `UnityEngine` types** — the engine-agnostic ruling) holding `NpcJson` (ONE serializer config: SnakeCaseNamingStrategy + `NullValueHandling.Include` + `DateParseHandling.None`/`DateTimeOffset` end-to-end — the null-vs-`[]` tri-state contract is load-bearing and never collapsed), `Models.cs` (a field-for-field mirror of every `app\schemas.py` wire model), the flat `NpcMemoryClient` (all ten routes 1:1, per-route settable timeouts, typed loud `NpcMemoryApiException`, the SSE consumer with chunk/reconstructing/result dispatch), and `NpcSession` (the field-for-field `_apply_turn_result` port: loader-seeds/gated-append/closed-untouched keyed on the SERVER's gate record; recent-actions cap; boundary resets; `as_of` time travel; boundary snapshot refresh from the last `reputation_after` — the documented single-client HTTP equivalence) + `client\NpcMemory.Harness\` (net8.0 console playing every demo beat headless). | verified by the live interop gate + independent floor-verifier **pass**: `dotnet build` 0 warnings; the harness ran **21/21 checks green** against a live `python -m app.serve` (fake mode, scratch `longmem_smoke`, port confirmed then dropped): provisioning, time-travel observes, the tri-state proof (null → loader / populated → evaluated / **explicit `[]` → evaluated**), SSE 7 chunks concatenating byte-identically to content with perceived > first_word > 0, correction both-head swap + chain (superseded PRESENT, coherent timeline) + index (live head, detail_count 2), 46-day reconstruction (write_backs 3) + byte-identical within-scene cache-hit reread, mid-scene gate fire (novelty) appending the unseen memory, warm-init → on-camera pure cache hit (0 write-backs, 4 hits), both scored views over one served set; verifier side-by-side port-fidelity review vs `app\session.py`; no SQL and no DB driver in `client\` (dependency closure exactly Newtonsoft); nothing hardcoded beyond documented overridable defaults; `git diff` empty vs HEAD `b490867` (the stage-0 floor byte-untouched); keyless subset re-run 41; `longmem` pristine via the postgres MCP. | 2026-07-27 |

## Open questions needing Jack's ruling

- **Escalation trigger set / thresholds — CLOSED 2026-07-23 (measured, then ruled).** The failure
  path closed 2026-07-22 (soft-degrade, migration 005). The trigger-set/threshold half closed
  2026-07-23: a per-observe real-mode measurement showed the high fire rate is **productive** (85%
  of fires add real gist content; ~$0.15/100 observes; latency off the dialogue path under async
  observes) and surfaced the **zero-gist hole** (16/80 observes landed with no gist spans). Jack
  ruled: defaults stand, a sixth **thin_gist** span-floor trigger added (built same day,
  floor-verified), and Engram-style deferred write enrichment queued to the sequenced-later ledger.
  See the dated "Escalation trigger tuning" entry in `decisions.md`. (The reconstruction flagged
  shapes were all confirmed 2026-07-17 — see the "Reconstruction flagged-shapes confirmations"
  entry in `decisions.md`.)

- **R7 — the self-referential drift budget (logged 2026-07-22 from the external-persona audit).** The
  reconstruction drift budget is cosine candidate-vs-anchor < 0.35; it cannot catch a retelling that
  stays under budget while dropping or contradicting a gist fact, or fabricating a never-observed
  detail. Challenges the 2026-07-17 drift-metric/threshold ruling. **Deferred to the Unity/eval build
  phase (ruled 2026-07-22)** — not acted on now; the fixed-gist-constraint ON/OFF ablation (in the
  pre-demo judged-eval work) produces the deciding data, and any metric/threshold change waits on it.

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
  `Research Papers\FINDINGS.md` — the folder is gitignored working material) found the two
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
  `Research Papers\CHANGES-FROM-RESEARCH.md` written (gitignored) tracing every landed and
  queued change to its source papers for the future README.
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
  `[npc-demo]` console transcript + `unity\Captures\graybox-stage2-receipt.png` (gitignored;
  sent to Jack); scene saved with `autoRun` off; server torn down, `longmem_smoke` dropped,
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

## Immediate queue

**Pre-demo build path — re-planned 2026-07-22 from the external-persona audit**
(`external-audit-2026-07-22.md` + `external-audit-2026-07-22-solutions.md`; three rulings in the dated
`decisions.md` entry). The audit's #1 finding, confirmed against source: **`app\api.py` has no HTTP
dialogue-turn route** — the cognition layer is REPL-only, and Unity is C# over HTTP. *(CLOSED
2026-07-23 — item 1 below is built and floor-verified; the route is live.)*

0. **Unblock real mode — DONE (verified 2026-07-22).** Jack fixed the malformed `.env` price line and
   `LONGMEM_MODEL_BEHAVIOR` is present (prior thread); verified via `config.load_settings` (no values
   printed): all eleven `LONGMEM_PRICE_*` keys parse, provider mode `real`, `load_settings()` OK. The
   2026-07-21 flagged crash is resolved; real mode is unblocked for the real-providers-only demo.
1. **HTTP dialogue-turn route + honest latency metric — DONE (built + floor-verified 2026-07-23).**
   `POST /v1/dialogue/turn` is live (stateless, non-streaming, 404/422, pass-through), with
   `perceived_first_word_ms` beside `first_word_ms` — the <1 s bar's field — surfaced in the CLI
   debug line + the driver series. SSE `/turn/stream` still rides later on the SAME generator (no
   rewrite). The thread-pool cap is ruled deferred post-demo. See the verified-floors table +
   session log; the build target is now item 2.
2. **Unity project + reference scene + The Ledger** — **demo vehicle ruled 2026-07-27** (dated
   "Demo-vehicle ruling" entry in `decisions.md`: Unity gray-box over an established-game mod; the
   five-agent panel — four audit personas + a modding-landscape scout — weighed it — Skyrim
   declined on zero C# reuse, the
   Mantella comparison class, state-delta observes, and AGPL). Spec: **`unity-client.md`**. The ruled
   sequence: **(i) `NpcMemory.Core` first** — engine-agnostic C# client (plain .NET, HTTP + JSON, the
   `NpcSession` port of `_apply_turn_result` with directive + reputation callbacks, zero `UnityEngine`
   types, one flat client class), driven by a `dotnet run` **console harness playing every demo beat
   headless — the Unity↔backend interop go/no-go moves to Wk-1** (was Wk-2; zero `.cs` today).
   **(ii)** Unity = a thin MonoBehaviour adapter + the gray-box scene as the **intended**
   systems/dev-tool aesthetic (a set, not a game — art-risk stays off the critical path); connect MCP
   for Unity at this step (`mcp-setup.md`; verify the bridge early — scene-manipulation operations
   fail during Play mode). **(iii) The Ledger = a browser page** over the existing HTTP API (not Unity UI), composited
   in OBS: original vs current telling side by side + `read_mode`/scores/IDs + superseded rows
   greyed-but-present + a real gist/detail number on screen — bound to the same `DialogueTurnResult`
   fields the eval harness scores. **Off-camera cache warm-init** (fire `/v1/dialogue/init` at each
   scene basis during camera cuts) removes the 9–16 s cold stall with zero pre-warm code. Beats:
   **lead with correction-override**, then **reconstructive drift (constancy-first — gist flat,
   detail thinning)**; the split-brain divergence is a **separate interview clip** (ruled
   2026-07-22), not a main-video beat. The game-authored action-observe beat + async observes (old
   pre-ship (d)) ride here. **All seven spec forks ruled + stage 0 BUILT and floor-verified
   2026-07-27** (dated "Unity-client fork rulings + stage-0 build" register entry): SSE
   `/turn/stream`, `POST /v1/agents`, and the chain/index inspector reads are LIVE; Newtonsoft
   everywhere; netstandard2.1 core + net8 harness layout; static-HTML Ledger; MCP for Unity
   verified. **Stage 1 BUILT + the Wk-1 interop gate GREEN + floor-verified (same day)** —
   `NpcMemory.Core` + the console harness; the C# null-vs-absent serialization proof landed (the
   tri-state beat runs live in the gate). Remaining carried item: the demo-corpus register
   (shipped-game dialogue style + the held-out eval arm). The REPL still drives all beats today (`:as-of` jumps + scene boundaries + band
   crossings; `:correct` moves retrieval AND entities; the gate debug line + `(reconstructing…)`).

**Pre-ship latency items** (2026-07-21 latency slate; **audit re-sequenced 2026-07-22** — the
   perceived-TTFT metric moved into item 1; pre-warm build proposed post-demo):
   - **(a) escalation failure path — BUILT 2026-07-22 (soft-degrade; migration 005).** The fail-loud
     hard-stop is retired: a gist-escalation double failure now proceeds with the base NLP-pass gist and
     sets the dedicated `memories.escalation_failed` flag — never a lost write (`EscalationHardStopError`
     + its observe-route 502 removed; suite 42 green). **Still open (separate, non-blocking):** the
     trigger-set/threshold tuning — escalation fires on **79% of realistic prose** (importance p50 0.61
     vs the 0.45 threshold; +1.4 s + ~$0.0021 per fire), a cost/latency item and latency lever **D**'s
     server half.
   - **(b) B1/B2 dialogue-latency experiments** against the <1 s first-word bar:
     haiku-dialogue A/B is a zero-code env swap; thinking-off variants on the sonnet-5 calls
     are one-liners needing a ruling. Measure, then rule.
   - **(c) C1 scene-boundary reconstruction pre-warm BUILD → CONFIRMED POST-demo (ruled 2026-07-22).**
     The demo's 9–16 s cold stall is removed by off-camera warm-init choreography (fire
     `/v1/dialogue/init` at each scene basis during a camera cut; within-scene byte-stability ⇒ identical
     on-camera bytes), so the full pre-warm build is not demo-blocking. This relaxes the latency slate's
     "all pre-demo" wording for C1. (The scene-frozen cache key still supports the full background build
     when it lands post-demo.)
   - **(d) D async observes** (client contract): the Unity client fires observe events
     without blocking dialogue — the 3.4 s real observe is throughput, not latency.
   *(Done 2026-07-21: the old **(b) real-provider smoke** and **(c) real-mode profiling
   re-run** — receipts + headline numbers in the session log; artifacts scratchpad-only.)*

*(Research-adoption queue — slated 2026-07-21 with the landed slate, each its own
spec/build session; ordering after the Unity/pre-ship items is Jack's to re-slate. Papers per
item are traced in `Research Papers\CHANGES-FROM-RESEARCH.md`.)*

3. **Judged eval harness v1 — PULLED PRE-DEMO (ruled 2026-07-22 with the Ledger scope).** Judge
   model role/env var + LLM-judged categories (judged signal real-mode-only — sequenced with that).
   **Audit additions:** (i) a judge-free gist-precision/detail-recall metric (from existing gist spans +
   spaCy, no judge call) feeding The Ledger's on-screen numbers; (ii) a small **hand-labeled gold set**
   so the judge has proven rigor (judge-agreement / meta-eval); (iii) the **fixed-gist-constraint ON/OFF
   ablation** — turns the self-referential drift-budget hole (R7) into a shown finding; (iv)
   **real-embedding drift validation** of the demo memory, run EARLY (Wk3, not Wk4).
   Starter categories: selective-forgetting single/multi-hop (MemoryAgentBench 2507.05257),
   abstention/premise (LongMemEval 2410.10813, LME-V2 2605.12493), reconstruction FactScore
   **retargeted** — gist-precision stays ~100%, detail-recall may decay (LoCoMo 2402.17753),
   FAMA stale-leakage (2604.20006), MemTrace trajectory probe + reach-vs-use attribution
   (2606.17328), and the judge-free keyword-retention check (2511.10277) which fits the
   structural suite today. Harness shape: Insert/Query over the existing session-runner loop;
   accuracy-vs-latency Pareto reporting.
4. **Graph/associative memory** — spec session with the de-risked design notes: Postgres-native,
   no graph DB (SPRIG 2602.23372 — app-side seeded PPR is sparse linear algebra);
   concept-mediated edges against `identity_components`, NOT raw entities (GAAMA 2603.27910 —
   entity graphs mega-hub, concept graphs stay ~30× sparser); bi-temporal edge supersession is
   our extension (edges from live heads only; corrections re-derive); the lexical channel
   (Target B) is the hybrid seeding base; graph term = a small additive nudge (GAAMA's 0.1
   ablation). Cheapest first step: HippoRAG's node-specificity IDF on the entity tripwire.
5. **Recall-reinforced decay** — spec session (ruled 2026-07-20: its own session). The "what
   counts as recall" fork + a migration; must not conflate decay with invalidation (invariant)
   nor break within-scene byte-identity. MemoryBank 2305.10250; survey 2512.13564 §5.2.3.
6. **Automatic conflict/staleness detection** — spec session; the write-time counterpart of the
   dissonance path. STALE 2605.06527 (CUPMEM-style adjudication riding `identity_components`);
   Nous 2606.22030 (trust provenance-capped, never content-inferred — maps to
   `typology`/`typology_source`); MemConflict 2605.20926 (taxonomy + near-floor SOTA = a
   differentiator). Non-destructive: detection routes through supersession, never delete.
7. Smaller queued notes: the reflection design dossier (ground reflective writes in cited
   memory_ids + an RRR repetition detector — honest-lying 2605.29463; periodic
   evidence-conditioned identity refresh — AI-YOU 2607.10539; persona-lensed retrieval routing
   — self-reports; idle-time scheduling — sleep-time 2504.13171); richer `seed_identity`
   authoring guidance (interview-depth beats a persona paragraph, self-reports study); the
   Whisper soft-steering hook + safe-default action fallback for the Unity C# API surface item
   (bounded-autonomy 2604.04703).

*(Done 2026-07-23: **HTTP dialogue-turn route + perceived-TTFT v1** — the Unity/C# front door +
the honest retrieval-inclusive latency metric; see the verified-floors table and session log.
Done 2026-07-21: **Split-brain streaming v1** — concurrent streaming-prose + behavior calls
off one retrieval, two scored views + the divergence record, the new `behavior` model role;
first word = prose TTFT. Also done 2026-07-21: **Encoding-context read term v1 +
gate-calibration utility** and **Hybrid lexical retrieval channel v1 (migration 004)** — the
research-adoption slate's two targets; see the verified-floors table and session log.
Done 2026-07-20: **Structural pytest suite v1** — 38 scenarios green, the Stop hook live
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
  normalization; slots for the future context term and per-call split-brain overrides *(both
  slots since ruled live: context landed 2026-07-20; behavior-view overrides **built**
  2026-07-21 — split-brain streaming)*. —
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
  reconstructing-signal hook, scene-boundary emission. *(Grown by the 2026-07-21 split-brain
  spec: the SSE streaming route + the game-authored action-observe contract land here.)*
  *(Shape ruled 2026-07-27: engine-agnostic `NpcMemory.Core` — zero `UnityEngine` types, one flat
  client class — + a thin Unity adapter; consolidated into `unity-client.md`.)*
  *(Stage-1 observation 2026-07-27: no HTTP agent-state read exists — the C# session refreshes its
  boundary reputation snapshot from the last turn's `reputation_after`, exact for a single-client
  session; a multi-client integration wants a small read route. Future surface item.)*
- Demo choreography: injected-timestamp time travel; decay + correction-override + gate-recollect
  beats; the 60-day drift plot — a planned beat since the 2026-07-14 re-slating (reconstruction is
  pre-demo). *(Grown 2026-07-21: the game-authored action-observe beat —
  `split-brain-streaming.md`.)*
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
"only if demo latency demands" wording); habituation *(the encoding-context read term itself
landed 2026-07-21 — Target A)*; **Engram-style deferred write cognition** (own spec target,
ruled onto the ledger 2026-07-23 — raw observe stored immediately, gist/enrichment at the
service's own timing; the existing degradation flags are the natural deferred-work queue; forks:
add-only gist annotation vs the frozen write-time facts, the un-enriched-window retrieval
contract, a new `write_cause` = a migration; Engram 2606.09900 + the sleep-time-compute family —
the async-observe client contract covers the latency motivation and the thin_gist trigger covers
correctness inline, so this is a cost/throughput optimization); **the established-game
integration clip** (ruled 2026-07-27 — post-demo, the split-brain interview-clip template: a
C#-moddable game reusing `NpcMemory.Core` — Stardew/SMAPI days-scale or RimWorld's rich event
stream — NOT Skyrim: zero C# reuse, the Mantella comparison class, AGPL on a published fork);
reflection → parameter compiler;
Unity Package Manager packaging; docs final + public flip
(Apache-2.0). *(Reconstruction — mechanism, drift budget, Set C scenarios — moved off this ledger
into the immediate queue by the 2026-07-14 re-slating ruling.)* *(Split-brain topology with per-call
weights — moved off this ledger into the immediate queue by the 2026-07-21 latency-slate
ruling, the second use of the pull-forward template; specced AND built same day,
`split-brain-streaming.md`.)*

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
