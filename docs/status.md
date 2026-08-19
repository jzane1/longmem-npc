# longmem-npc — Status

**Last updated:** 2026-08-19
**Phase:** **Road to completion — Phases A–D DONE. Phase E (demo) IN PROGRESS: E1 ✅, next E2.**
**E1 landed 2026-08-19** (docs + data only, no code, no floor by ruling): the integrator
authoring guide **`docs\identity-authoring.md`** + the demo NPC **Branwen of the Waystone Inn**
(`data\eval\corpora\demo-waystone.jsonl` + 3 held-out probes in
`data\eval\scenarios\demo-waystone.jsonl`), validated on real providers — coverage
drift-validate 9/9 under budget (max 0.121 vs 0.35), beat-condition target certified (drovers,
0.082), held-out run 2/2 checks, fabrication 0.000. Phase E was scoped at plan approval to
**three sessions** (E1 authoring / E2 choreography + rehearsal / E3 record). Full record +
the five authoring lessons in `decisions.md`'s E1 entry.
D1 (optimization, 2026-08-19, no new code): perceived-first-word **p50 938 ms**, believability
no regression (gist_precision 0.823), **model slate LOCKED** (Haiku latency-bound; Opus 4.8
batch roles in `.env.example`), workers OFF per-agent, prompt caching DEFERRED — the D1 entry.
The system is BUILT end to end on the final A1 seam — backend, C# client + console harness,
Unity adapter + gray-box scene, The Ledger, eval-harness stages 1–4, deferred writes,
reflection, the parameter compiler, the dissonance path, the agent-state read + async observes,
the purge endpoint, the concurrency cap + scene-boundary pre-warm (C7) — schema at
migrations 001–008.
What is proven lives in
`docs\floors.md`, why in `decisions.md`, the narrative in `session-log.md`; this file
carries only what is live.

This is the *living* file — update it at the end of every working session. `architecture.md`
changes only when design changes; `decisions.md` is append-only. Size tripwire (ruled
2026-08-17): this file leaves every wrap-up at or under ~12 KB; anything past the line moves
verbatim into `session-log.md`'s archive — trimmed, never deleted.

## End products & framing (re-ruled 2026-08-04)

Three end products, nothing else: **the demo video**, **a Unity Package + one-command backend
spin-up**, and **the public GitHub repo** (Apache-2.0). The research track is scrapped — no
write-up, no submission. The mid-to-late-August demo date is **dropped by ruling**: quality
drives, and the demo lands after Phases A–D. Portfolio target unchanged: tier-1
embodied-agent / game-AI employers — the instrumentation table, the test suite, and the
on-screen eval numbers are what survive the interview. The demo records real-providers-only
(ruled 2026-07-22).

## Build discipline

- **Staged verification:** each layer verifies against a known-good layer beneath it, so failures
  have a single cause. Anything renamed or ported is re-verified before it counts as a floor.
- **Instrument at the seam:** when building a layer, its timing and token accounting land in the
  same task. Framework choices must survive the interview; ceremony scores below absence.
- Unity is the demo vehicle; the gray-box scene recorded is the fallback video. The CLI/REPL
  remains the debug product surface (memory IDs, scores, token counts exposed).

## Verified floors

The full table — layer, what it was verified against, and the date — lives in
**`docs\floors.md`** (moved there 2026-07-28 so this living file stays small enough to
auto-load). That file states the counting convention; cite it rather than a number in prose.

A row lands there only after an independent floor-verifier pass returns **pass**. Floors are
re-openable: re-verifying one is a step, never an argument against a design improvement.

## Open questions needing Jack's ruling

**Pending Jack (from the D1 landing, non-blocking):** (1) **ratify or redirect the
dissonance-multiplier defaults** — D1 found no objective metric to tune them against, so the
principled ordering was kept unchanged (an eyeball run of the defend/update beat is available on
request); (2) sync the live `.env` batch roles to Opus 4.8; (3) offline gold re-labeling if
calibrated judged-prose numbers are wanted on screen (kappa 0.37, unquotable — non-blocking; the
on-screen numbers are judge-free).

**Recently closed** (pointers only): the E1 forks — four ruled at plan approval 2026-08-19 (new
demo character; first-person paragraph seed; held-out run in E1; docs+data-only scope, no floors
row — the dated E1 entry); the D1 forks — three settled at plan approval 2026-08-19
(stronger batch roles; judge-free + judged believability; flip-in-D1-on-the-data → slate locked,
workers stay OFF per-agent, caching deferred — the dated D1 entry); the C7 forks — three ruled
2026-08-18; the C6 forks — four ruled 2026-08-18. Full history — C1–C5, the status.md size
tripwire, the C2/C3 lines, and earlier closures — lives in `decisions.md`'s index and the
`session-log.md` archive.

## The roadmap (re-planned 2026-08-04; ordering delegated to Claude on efficiency grounds)

Sizes are rough working-session counts, not dates — **~18–22 sessions to the finish line.**
Every build session keeps the standing discipline: settle forks at spec, build, walkers,
independent floor-verify, docs, commit. After each Phase C landing, a harness run checks
believability didn't regress (the point of doing Phase B first).

### Phases A + B — DONE

A1 (2026-08-04, floors rows 19/21) and B1–B3 (2026-08-05/07/12, floors rows 22–24). The
verbatim blocks moved to `session-log.md`'s archive at the E1 wrap-up (size tripwire).

### Phase C — Build the kept components (~7–8 sessions)

Ordered so shared machinery lands before its reusers.

- **C1–C6 ✅ ALL LANDED** (each plan-to-floor + floor-verified; full records in `floors.md`
  rows 25–30 + `decisions.md`): **C1** deferred writes (`deferred-writes.md`, migration 006,
  default OFF); **C2** reflection (`reflection.md`, migration 007, default OFF per agent,
  endpoint always live); **C3** parameter compiler (`parameter-compiler.md`, migration 008,
  default OFF per agent); **C4** dissonance path + diegetic-correction event (`dissonance.md`,
  no migration, always live — client-invoked); **C5** client contract completion (no spec doc,
  no migration — the agent-state read, the FOURTH unscored member, + fire-and-forget observes,
  drains at scene edges); **C6** purge endpoint (`architecture.md` §12, no migration — per-memory
  `DELETE /v1/memories/{id}`, reflections survive, no guard).
- **C7. Latency pair ✅ DONE** (plan-to-floor 2026-08-18): Stage A concurrency cap (floors row 31)
  + Stage B probe-driven scene-boundary reconstruction pre-warm (floors row 32); NO migration.
  Prompt caching was DEFERRED to Phase D (Haiku-4096 finding); D1 confirmed it stays deferred.

### Phase D — Optimization rounds (~1–2 sessions)

- **D1.** ✅ DONE 2026-08-19 (plan-to-landing, no new code — a measure→rule→tune→re-verify pass on
  the built rig). Latency CONFIRMED (938 ms p50), believability NO REGRESSION, **model slate
  LOCKED** (Haiku latency-bound + Opus 4.8 batch roles), workers stay OFF (per-agent opt-in),
  prompt caching DEFERRED confirmed. NO new floors row (built no layer). Full record in
  `decisions.md`. Exit criterion met: the on-screen latency + believability + cost numbers.

### Phase E — Demo (~3–4 sessions)

- **E1. Identity authoring guide + demo corpus.** ✅ DONE 2026-08-19 (docs + data only; no
  floors row by ruling). The guide (`identity-authoring.md`), Branwen of the Waystone Inn,
  the held-out arm, and the real-provider validation — coverage 9/9 under budget, the drovers
  memory certified as the beat-2 drift target in the beat's own condition. The un-driftable-
  memory tripwire fired for real: five authored revisions, each failure caught at authoring
  time (the E1 `decisions.md` entry has the lessons).
- **E2. Choreography + rehearsal.** Final beat script (correction-override lead →
  constancy-first drift on the certified drovers memory; the game-authored action-observe
  beat — first-person observes, per the E1 render-voice finding), the Ledger live-feed
  decision + small Ledger polish, rehearsal on the demo DB. E2 owns the code gaps: the
  corpus→demo-DB loader (same agent fields + worker-enable flags), the C# `PrewarmContext`
  field, the `NpcMemoryNpc` ObserveAndForget/Drain passthroughs. Rehearsal guard: inspect the
  provisioned roll (importance/spans/retell take) and re-provision until good — the take then
  pins by the constancy invariant. (With C7 landed, the off-camera warm-init trick is
  unnecessary.)
- **E3. Record + edit** — Unity + The Ledger split-screen in OBS; real providers only.

### Phase F — Release (~3 sessions)

- **F1. Full README build** — incl. the destructive-compression counter-example and the honest
  "what this is not" paragraph (no auth, no rate limiting; loopback-bound by default).
- **F2. Packaging** — the ruled end product: the Unity Package Manager package + the one-command
  backend spin-up (compose: Postgres/pgvector + API + migrations).
- **F3. Release hygiene + the public flip** — the Unity MCP pin fix + manifest/lockfile
  reconciliation, the committed-DLL staleness check, a sweep of the minor audit leftovers (F3
  check-8 teeth, CRLF renormalization, `~\.claude.json` duplicate keys, the Unity-gate
  session-ordering note — swept or consciously dropped), docs finalization, Apache-2.0 flip.

**The finish line: repo public + video published + package downloadable.**

### Phase G — Optional epilogue (time-permitting, explicitly droppable)

- **G1.** The real-game plug-in clip: a C#-moddable game reusing `NpcMemory.Core`
  (Stardew/SMAPI or RimWorld — not Skyrim; see the 2026-07-27 demo-vehicle entry).

## Cut from scope (ruled 2026-08-04)

The full list (research track, split-brain behavior side, graph memory, the stretch list, the
August date) moved verbatim to `session-log.md`'s archive at the E1 wrap-up (size tripwire);
the ruling itself is `decisions.md` 2026-08-04. Nothing has been added back.

## Session log

In **`docs\session-log.md`** — append one entry per session there, at the end of the entry list
(before the archive section), in the honest landed/blocked/abandoned wording `/wrap-up` asks
for. The pre-2026-08-04 status narrative and superseded queues live in that file's archive.

## Repo conventions

Public GitHub (ruled 2026-08-13, the flip pulled ahead of Phase F — the interim-README entry
in `decisions.md`; the v1 *release* still exits through Phase F, purge included). Commit at
least weekly. Secrets in `.env` only
(`.env.example` is the tracked template). Always PowerShell, backslash paths.

Mechanically enforced since 2026-07-28: `ruff format` **and** `ruff check` on every edit (pinned
version, rules in `ruff.toml`); the `-m "not nlp"` suite subset at every turn end;
`.gitattributes` normalizing line endings to LF. Licensing is settled — `LICENSE` (Apache-2.0)
and `NOTICE` (the third-party inventory; psycopg is the one copyleft dependency, LGPL-3.0-only,
not vendored).

**Carried, not fixed** (deliberately unscheduled, awaiting its own ruling):

- **The walkers (fifteen since C7-B) share a fixed-name scratch DB** (`longmem_test`) they neither
  create, migrate, nor drop, and some walker assertions are DB-global counts. The right fix —
  the suite's pid-scoped mechanism plus a `tests\run-walkers.ps1` runner — is a medium refactor
  of the verification apparatus itself, so it wants its own scoped task rather than riding an
  audit. THREE documented bites (the first two verbatim in the session-log archive, moved
  2026-08-17): 2026-08-12 (the DB found MISSING; psycopg_pool masked it as a 30 s
  `PoolTimeout`), 2026-08-17 (`verify_reflection` is non-re-runnable on the persistent
  scratch — a fresh pid-scoped scratch is that walker's documented precondition), and
  2026-08-17 again at the C4 landing (the elder correction walkers' DB-global
  corrections-emptiness asserts vs the re-opened `verify_reconstruction` — sweeps must run
  fresh + serial, elder walkers first; the C4 build record has the detail). *(The other
  2026-07-28 carried items — the auth honesty paragraph, the Unity MCP pin, the DLL
  staleness check — are scheduled: Phase F.)*
