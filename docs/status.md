# longmem-npc — Status

**Last updated:** 2026-08-17
**Phase:** **Road to completion — Phases A, B, C1, C2, and C3 are DONE.** (The roadmap
below, consolidated 2026-08-04.) The 2026-08-17 session landed **PHASE C3 — the parameter
compiler**, plan-to-floor in one session. The seven C3 rulings settled at the plan-mode
fork batches BEFORE any file changed: feedstock = ALL live beliefs; typed core = the three
prose-view weight multipliers only (§10's dead "action-set biases" corrected with the
build); scheduling = the STANDALONE third background worker — Jack took the larger option
over the recommended reflect-pipeline stage, with the follow-up fork ruling it lands
WITHOUT the generic jobs table (that unification stays its own later task) — no endpoint,
no route; the all-mechanical staleness guard (the K-window at discovery AND consume +
liveness-by-join + hard clamps); the judge-shaped `LONGMEM_MODEL_COMPILER` (the THIRD such
var); the multiplier clamp **[0.25, 4.0]** frozen into migration 008's CHECK; and
`:compile` = sweep semantics. Landed: migration 008 (`compiled_bundles` append-only,
liveness DERIVED by join + `compiler_runs`), `app\compiler.py` (service + worker + the
pure consume functions), the dialogue-seam consume splice (`scene_type` on the turn
request; composed multiplier products over the untouched weight resolver; zero-bundle
byte parity walker-asserted), the session/CLI surface, suite Set M (21 scenarios, ALL
unmarked — subset 114 → 135, total 128 → 149), the TENTH walker (48/48), the C# mirror +
interop beats [13] (28 → 32), and the docs sweep incl. `parameter-compiler.md` and the
§12 stale-count corrections. The independent floor-verifier returned **PASS** (floors row
27); believability shows no regression (real-mode smoke vs the 2026-08-07 baseline:
checks 6/0 both, gist 0.7667 → 0.85, keyword retention equal). **Applying migrations
007 + 008 to the product `longmem` DB is Jack's action** (builds touch scratches only;
the product ledger sits at 001–006 with zero reflection or bundle rows). **NEXT UP: C4 —
dissonance path + diegetic-correction event.**
The system is BUILT end to end on the final A1 seam — backend, C# client + console harness,
Unity adapter + gray-box scene, The Ledger, eval-harness stages 1–4, deferred writes,
reflection, the parameter compiler — schema at migrations 001–008. What is proven lives in
`docs\floors.md`, why in `decisions.md`, the narrative in `session-log.md`; this file
carries only what is live.

This is the *living* file — update it at the end of every working session. `architecture.md`
changes only when design changes; `decisions.md` is append-only.

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

**Twenty-six floors stand verified.** The full table — layer, what it was verified against,
and the date — lives in **`docs\floors.md`** (moved there 2026-07-28 so this living file stays
small enough to auto-load). That file states the counting convention; cite it rather than a
number in prose.

A row lands there only after an independent floor-verifier pass returns **pass**. Floors are
re-openable: re-verifying one is a step, never an argument against a design improvement.

## Open questions needing Jack's ruling

*None open.*

**Recently closed** (pointers; full trail in `decisions.md`): **the C3 forks — seven
ruled 2026-08-16/17 at the plan-mode batches** (feedstock; typed core; the standalone
third worker — the one larger-than-recommended pick, with the jobs-table follow-up ruled
standalone; the mechanical staleness guard; the judge-shaped role; the [0.25, 4.0] clamp
frozen pre-migration; `:compile` sweep semantics — the dated build record); **the C2
build-plan forks —
four ruled 2026-08-15 at the build session, all recommended options taken** (post-commit
re-render; the tri-state REPL surface; the keyword-only provider test seam; the real-mode
believability run), with the spec's `[SETTLE-AT-BUILD]` ledger resolved by the approved
plan (the dated build record); **the C2 spec forks — the
four ruled 2026-08-15 at the spec sitting** (consolidation auto-threshold + override;
trim PURELY MECHANICAL — against the recommendation, the one divergence in the C2 line;
per-affected eviction; C# mirror at build; the dated entry); **the C2 dossier forks — all
six + the habituation rider ruled 2026-08-15 at the dossier session** (scheduling
composition; belief home; the identity package incl. the dialogue-seam move; trim teeth +
the fourth sanctioned cause; the RRR guard; the judge-shaped role; the dated entry);
**the interim public README +
the early public flip — ruled 2026-08-13** (repo public ahead of Phase F; F1's demo-time
rewrite unchanged; the dated entry); **em-dashes banned from public-facing prose — ruled
2026-08-13, recorded at the 2026-08-15 wrap-up** (zero U+2014 in Jack's-voice deliverables,
F1 included; en-dashes and hyphens stay; the dated entry); **the C1 spec forks + the
`typology_confidence` seat — all five ruled 2026-08-12 at the C1 spec** (defer-LLM-calls-only;
supersession via chains + the one-shot scalar sanction; worker default OFF; the byte-identity
third cause; confidence salvage); **the dialogue model — HAIKU
re-ruled 2026-08-12 on the first real compares** (perceived first word is decisive: 943 ms p50
vs sonnet-5's 2626/2086 ms against the 1 s bar; sonnet's 46–7 / 41–9 prose preference on the
record and rejected as not justifying the latency; the thinking-off variant measured and
closed the same way); **R7 — resolved 2026-08-12 on the stage-4 ablation's data** (the drift
budget keeps its mechanism and 0.35 threshold and is re-scoped as a TOPIC guard — wholesale
nonsense/topic-swaps; factual faithfulness is policed by gist-precision (fact survival) and
the judged faithfulness category; nothing changes at runtime, the claim is corrected in
`architecture.md` §7, `reconstruction.md`, the `drift_budget_threshold` knob comment, and the
stage-4 banner); the 2026-08-04 scope rulings (below); haiku ships as the dialogue role +
quote embargo lifted (2026-07-29); reconstruction's model class — Haiku stands (2026-07-28;
re-measured on Haiku 2026-07-29); escalation failure path + trigger tuning (2026-07-22/23).

## The roadmap (re-planned 2026-08-04; ordering delegated to Claude on efficiency grounds)

Sizes are rough working-session counts, not dates — **~18–22 sessions to the finish line.**
Every build session keeps the standing discipline: settle forks at spec, build, walkers,
independent floor-verify, docs, commit. After each Phase C landing, a harness run checks
believability didn't regress (the point of doing Phase B first).

### Phase A — Re-shape the dialogue seam — DONE

- **A1. Split-brain removal + weights-on-speech.** ✅ **LANDED 2026-08-04, floor-verified**
  (the twenty-first floor row; the dated A1 entry in `decisions.md` records the spec rulings,
  the seam contracts, and the full strip list; the Unity Play-mode re-run closed 2026-08-05 —
  dated resolution notes on floors rows 19/21). *Why first: every later measurement, client
  byte, and demo beat targets the final seam.*

### Phase B — Finish the measurement rig (~3 sessions)

- **B1. Eval-harness stage 2.** ✅ **LANDED 2026-08-05, floor-verified** (the twenty-second
  floor row; the dated stage-2 entry in `decisions.md` records the session rulings and build
  latitude; spec: `eval-harness.md`).
- **B2. Eval-harness stage 3.** ✅ **LANDED 2026-08-07, floor-verified** (the twenty-third
  floor row; the dated stage-3 entry in `decisions.md` records the session rulings and build
  latitude). The real judged smoke emitted the 78-row blind gold file. The deferred first real
  use ran 2026-08-12 under the workaround ruling: `agreement` (sf 0.75 / abst 1.0 / rf
  degenerate-then-fixed-by-construction), the constructed-truth round (judge discrimination
  kappa 1.0/1.0), and both queued compares.
- **B3. Eval-harness stage 4.** ✅ **LANDED 2026-08-12, floor-verified** (the twenty-fourth
  floor row; the dated workaround + build-record entries in `decisions.md`; stage-4 BUILT
  banner in `eval-harness.md`). The fixed-gist ablation's first real run delivered R7's
  deciding data, and **R7 was ruled the same day** (topic-guard re-scope; no tuning follow-up —
  the ruling changed documentation, not the metric).

*Why before components: three cheap sessions, additive forever after (new components just add
scenario files), before/after believability numbers for every Phase C landing, and R7 settled
before reflection and deferred writes build on reconstruction.*

### Phase C — Build the kept components (~7–8 sessions)

Ordered so shared machinery lands before its reusers.

- **C1. Deferred write processing** (Engram-style). ✅ **LANDED 2026-08-12, floor-verified
  2026-08-13** (the twenty-fifth floor row; the three dated C1 entries in `decisions.md`
  record the spec rulings and build latitude; spec: `deferred-writes.md`, migration 006).
  Ships default OFF — the flip is a Phase D question. The deferred-work machinery C2 rides
  now exists.
- **C2. Reflection** — the biggest item. ✅ **LANDED 2026-08-15, floor-verified the same
  date** (floors row 26; the three dated C2 entries in `decisions.md` — dossier, spec,
  build record): `app\reflection.py` + migration 007 + the judge-shaped role + the
  dialogue-seam move + Set L + the ninth walker + the C# mirror; the believability run
  confirmed no regression. Ships default OFF per agent (the endpoint is always live);
  the flip is a Phase D question alongside C1's.
- **C3. Reflection → parameter compiler.** ✅ **LANDED 2026-08-17, floor-verified the
  same date** (floors row 27; the dated C3 build record in `decisions.md` — the seven
  plan-batch rulings): migration 008 + `app\compiler.py` (the standalone third worker —
  no endpoint, no jobs table by ruling) + the judge-shaped `LONGMEM_MODEL_COMPILER` +
  the dialogue-seam consume splice + Set M + the tenth walker + the C# mirror; the
  believability run confirmed no regression. Ships default OFF per agent (the full
  modulator suite stays cut); the flip is a Phase D question alongside C1's and C2's.
- **C4. Dissonance path + diegetic-correction event** (ONE session, ruled).
- **C5. Client contract completion** (one session): the agent-state read route (backend + C#) +
  async observes (fire-and-forget client observes; ruled in explicitly 2026-08-04).
- **C6. Purge endpoint** — the ruled release-blocker; the sole sanctioned DELETE.
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

- **The walkers (ten since C3) share a fixed-name scratch DB** (`longmem_test`) they neither create,
  migrate, nor drop, and three assertions in `verify_fact_correction.py` are DB-global counts.
  Giving them the suite's pid-scoped mechanism plus a `tests\run-walkers.ps1` runner is the
  right fix; it is a medium refactor of the verification apparatus itself, so it wants its own
  scoped task rather than riding an audit. *(Bite recorded 2026-08-12: the DB was found
  MISSING — dropped at some point since the 2026-08-07 audit — and psycopg_pool masked
  "database does not exist" as a 30 s `PoolTimeout`; recreated + migrated 001–005 in-session.)*
  *(SECOND bite recorded 2026-08-17 at the C3 floor-verify: `verify_reflection`'s B6/E9
  DB-global counts make that walker non-re-runnable on the persistent scratch once its own
  prior green run has landed rows — it needed a fresh pid-scoped scratch to pass 60/60; the
  C3 walker ships a persistent-scratch rule in its docstring to stay out of this class.)*
  *(The other three 2026-07-28 carried items — the auth honesty paragraph, the Unity MCP pin,
  the DLL staleness check — are now scheduled: Phase F.)*
- *(The `typology_confidence` parse seat flagged earlier on 2026-08-12 was **ruled SALVAGE
  and closed the same day inside C1** — the dated entry in `decisions.md`; the typology gap
  itself was ruled CLAMP and built that morning. Neither is carried any longer.)*
