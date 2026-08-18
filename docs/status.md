# longmem-npc — Status

**Last updated:** 2026-08-18
**Phase:** **Road to completion — Phases A, B, and C1–C6 are DONE. NEXT UP: C7 — the latency
trio (concurrency cap + scene-boundary reconstruction pre-warm; then prompt caching).** C6 (the
purge endpoint — the ruled release-blocker and the sole sanctioned content DELETE) landed
2026-08-18, plan-to-floor in one session — floors row 30; the dated C6 build record carries the
four plan-batch rulings (per-memory scope, the DELETE verb, no guard, NO migration by ruling)
and closes the `parameter-compiler.md` C6 note as "purge does not reach reflections". **No
operator action stands.**
The system is BUILT end to end on the final A1 seam — backend, C# client + console harness,
Unity adapter + gray-box scene, The Ledger, eval-harness stages 1–4, deferred writes,
reflection, the parameter compiler, the dissonance path, the agent-state read + async observes,
the purge endpoint — schema at migrations 001–008.
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

*None open.*

**Recently closed** (pointers only): the C6 forks — four ruled 2026-08-18, all recommended
options taken (the dated build record); the C5 forks — seven ruled 2026-08-17, all recommended
(the build record). Full history — C1–C4, the status.md size tripwire, the C2/C3 lines, and the
earlier closures — lives in `decisions.md`'s index and the `session-log.md` archive.

## The roadmap (re-planned 2026-08-04; ordering delegated to Claude on efficiency grounds)

Sizes are rough working-session counts, not dates — **~18–22 sessions to the finish line.**
Every build session keeps the standing discipline: settle forks at spec, build, walkers,
independent floor-verify, docs, commit. After each Phase C landing, a harness run checks
believability didn't regress (the point of doing Phase B first).

### Phase A — Re-shape the dialogue seam — DONE

- **A1. Split-brain removal + weights-on-speech.** ✅ LANDED 2026-08-04, floor-verified
  (floors row 21; Play-mode re-run closed 2026-08-05 — floors rows 19/21).

### Phase B — Finish the measurement rig — DONE

- **B1. Eval-harness stage 2.** ✅ LANDED 2026-08-05, floor-verified (floors row 22).
- **B2. Eval-harness stage 3.** ✅ LANDED 2026-08-07, floor-verified (floors row 23; first
  real use 2026-08-12).
- **B3. Eval-harness stage 4.** ✅ LANDED 2026-08-12, floor-verified (floors row 24; its
  first real run decided R7).

### Phase C — Build the kept components (~7–8 sessions)

Ordered so shared machinery lands before its reusers.

- **C1. Deferred write processing** (Engram-style). ✅ LANDED 2026-08-12, floor-verified
  2026-08-13 (floors row 25; the three dated C1 entries; spec: `deferred-writes.md`,
  migration 006). Ships default OFF — the flip is a Phase D question.
- **C2. Reflection** — the biggest item. ✅ LANDED 2026-08-15, floor-verified the same date
  (floors row 26; the three dated C2 entries; spec: `reflection.md`, migration 007). Ships
  default OFF per agent (the endpoint is always live); the flip is a Phase D question.
- **C3. Reflection → parameter compiler.** ✅ LANDED 2026-08-17, floor-verified the same
  date (floors row 27; the dated C3 build record; spec: `parameter-compiler.md`, migration
  008). Ships default OFF per agent (the full modulator suite stays cut); the flip is a
  Phase D question.
- **C4. Dissonance path + diegetic-correction event.** ✅ LANDED 2026-08-17 in the ruled
  ONE session, floor-verified the same date (floors row 28; the dated C4 build record;
  spec: `dissonance.md`; NO migration — the `corrections` table waited since 001). Always
  live (no kill-switch by ruling — the event is client-invoked; not sending it is the off
  state).
- **C5. Client contract completion.** ✅ LANDED 2026-08-17 plan-to-floor in one session
  (floors row 29; the dated C5 build record; NO spec doc by design — the contract lives in
  `unity-client.md` + `architecture.md`; NO migration by ruling). The agent-state read
  (`GET /v1/agents/{id}/state`, the FOURTH unscored member) + fire-and-forget observes
  (`NpcSession`: fire + pending + drain + failure event; no auto-drain — "drain at scene
  edges" is integrator guidance, E2 places the drains).
- **C6. Purge endpoint** — the ruled release-blocker; the sole sanctioned content DELETE. ✅
  LANDED 2026-08-18 plan-to-floor in one session (floors row 30; the dated C6 build record; NO
  spec doc — the contract lives in `architecture.md` §12; NO migration by ruling — ledger stays
  at 008). Per-memory `DELETE /v1/memories/{id}`; reflections survive (the C6 note closed); no
  guard by ruling.
- **C7. Latency trio** (~2 sessions): concurrency cap + scene-boundary reconstruction pre-warm;
  then prompt caching / prompt-head rebuild. Last in the phase so Phase D measures them fresh.

### Phase D — Optimization rounds (~1–2 sessions)

- **D1.** Full-system latency + believability passes: the driver's latency series + the
  harness's compare/Pareto runs; knob tuning; final model-slate confirmation. Exit criterion:
  the numbers that go on screen in the demo.

### Phase E — Demo (~3–4 sessions)

- **E1. Identity authoring guide + demo corpus.** Write the guide, then prove it by authoring
  the demo NPC with it — identity + memories in shipped-game dialogue register, with a held-out
  arm for the harness. **Immediately `drift-validate` the demo memories** so an un-driftable
  demo memory is caught at authoring time, not recording time.
- **E2. Choreography + rehearsal.** Final beat script (correction-override lead →
  constancy-first drift; the game-authored action-observe beat), the Ledger live-feed decision +
  small Ledger polish, rehearsal of the exact beats on the demo DB. (With C7 landed, the
  off-camera warm-init trick is unnecessary.)
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

- The research track entirely: write-up, submission, asymmetry ablation, Bartlett-style judged
  evals. (The stage-4 gist ablation SURVIVES — it answers R7, an engineering question.)
- The behavior/action side of split-brain: the action directive, the reputation system whole,
  the divergence record + its interview clip. NPC actions are the game developer's domain; the
  NPC's own actions arrive as ordinary observes.
- Graph/associative memory (too large a task for not enough benefit), recall-reinforced decay,
  automatic conflict/staleness detection, habituation, the Whisper soft-steering hook +
  safe-default action fallback.
- The optional/stretch list: disclosure gate, faithful-vs-reconstructive dual read modes,
  local-model packaging, the dormant-agent overseer (next project), the full modulator suite.
- The mid-to-late-August demo date (see framing above).

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

- **The walkers (thirteen since C6) share a fixed-name scratch DB** (`longmem_test`) they neither
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
