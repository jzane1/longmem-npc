# The demo beat script (E2, 2026-08-19)

The final choreography for the E3 recording: three beats + a close, ~75 seconds, split-screen
(Unity gray-box left, The Ledger right in a browser, composited in OBS). Beat order is ruled
(the 2026-07-22 audit's R4): **correction-override leads** — studios buy NPCs that remember
correctly before they buy controlled drift. The drift beat is framed constancy-first (gist
holds, texture drifts, on a budget, on purpose). The old beat 3 (split-brain divergence) is
dead (scrapped 2026-08-04); its slot is the game-authored action-observe beat.

Everything here runs on the demo DB (`longmem_demo`), real providers only (ruled 2026-07-22),
agent **Branwen of the Waystone Inn** (`data\eval\corpora\demo-waystone.jsonl`, authored and
validated in E1 — `identity-authoring.md` §8). On-screen text obeys the em-dash ban
(2026-08-13).

## The rig

- Backend: `.env` pointing `DATABASE_URI` at `longmem_demo`, `LONGMEM_PROVIDER_MODE=real`,
  the six live roles per the D1 slate (Haiku latency-bound) **plus the two batch roles synced
  to Opus 4.8 — the demo agent's workers are ON, so the pending-Jack `.env` sync binds here**
  (C3's first real compile is the worker's; a missing `LONGMEM_MODEL_COMPILER` lands a
  `failed` run row on camera).
- `python -m app.serve`, then The Ledger at `http://127.0.0.1:8000/ledger?agent=<agent-id>`
  with **poll ON** (the 2 s poll drives the index, the chain view, the identity pane, and the
  live turn feed).
- Unity: `SampleScene` — the adapter is committed attach-mode (`autoProvision` off);
  paste the loader's printed agent id into `agentIdOverride` before Play. The driver's
  inspector carries the beat controls: `correctionMemoryId` (paste ref 0's memory id),
  `correctionText` (below), `prewarmContext` (the drovers question), `sayK = 3`
  (the certified beat condition is the utterance's, not the agent's), `jumpDays = 60`.
- OBS frame (0–8 s): left "what the character says", right "what they actually remember,
  and how". The Ledger's identity pane shows Branwen's seed identity on camera (E1 ruling).

## Timeline

The corpus's June runs 2026-06-02 → 2026-06-24T21:00Z (nine observes). The demo session:

| Step | Session as_of |
|---|---|
| Scene 1 (beats 0–1) | 2026-06-25T19:00Z |
| Scene 2 (beat 2) | +60 days = 2026-08-24T19:00Z |
| Scene 3 (beat 3 recall) | same evening, after the beat-3 boundary |

## BEAT 1 — Correction-override (~8–30 s, the lead)

The wrong belief is authored: ref 0 has Halvard settling his account **in full** (eleven
shillings, a round for the room). The designer knows he only paid six.

1. Set as_of to 2026-06-25T19:00Z ("+N days" is not needed; set before Play or via the
   session default — rehearsal pins the exact mechanism), **Scene boundary** (freezes the
   June basis).
2. Say (k=3): **"Did Halvard settle his account before he rode north?"** → Branwen answers
   from the wrong belief. Ledger turn panel: ref 0 served, `read_mode` verbatim, its score
   on screen.
3. **Correct** (the driver button; `correctionMemoryId` = ref 0's id) with the probe-certified
   override text:
   > Halvard paid only six of the eleven shillings before riding north; the other five stand
   > as debt against his return.
4. Ledger chain view on ref 0 (a scene cut can deep-link `&memory=<id>`): the original
   telling **greyed but present**, the `authorial_correction` head live — superseded, never
   deleted.
5. Say (k=3): **"How much does Halvard still owe the house?"** → the corrected answer.
   Retrieval follows the fix (the fact chain moved with the correction).

Guard (owed since the 2026-07-22 script): rehearse the exact correction on the demo DB and
confirm the served score/rank of ref 0 moves across the fix on the money question.

## BEAT 2 — Constancy-first drift (~30–55 s)

The certified target: ref 3, the turned-away drovers — her OWN action, first person, drifted
on 6 of 7 E1 rolls, certified in the beat's own condition (k=3, 60 days, distance 0.082,
inside the 0.05–0.30 useful window). The chimney fire stays the fallback take only.

1. **+60 days** → 2026-08-24T19:00Z. **Scene boundary** — the boundary carries
   `prewarm_context` = the beat utterance (C7-B), so the retellings roll during the scene
   cut, off the turn's latency. (The old off-camera warm-init trick is retired.)
2. Say (k=3): **"Do you remember the two drovers you turned away at the door in June?"**
   → the retelling. Ledger: `read_mode` flips to `reconstructed` (amber), gist precision
   green at the top ("the NPC is never wrong about what matters"), the chain view shows the
   retold telling beside the immutable observation, gist spans marked.
3. The line: not a hallucination — the record underneath is intact; the telling drifted, on
   a budget, on purpose.
4. Say the same question again → **byte-identical text** (the constancy invariant; the cache
   serves the pinned take).

## BEAT 3 — The game authors her actions (~55–72 s)

The action-observe contract (2026-08-04): the NPC's own deeds arrive as ordinary observes,
first person (the E1 render-voice rule — first person renders owned; third person renders
witnessed). Fire-and-forget, so gameplay never blocks on the write path; the drain is the
explicit join at the scene edge (no verb auto-drains, by ruling).

1. On-camera action beats (typed into the driver input, or scripted):
   - **Observe (async):** "I put old Fenn's cart under the lean-to when the rain came, and
     stabled his gray mare with a feed of oats."
   - **Observe (async):** "I chalked the well rope onto the repair slate myself, so Piers
     cannot claim he was never told."
   The overlay's `pending observes: 2` readout is the fire-and-forget proof on screen.
2. **Drain** at the scene edge, then **Scene boundary**.
3. Say (k=3): **"What did you do for Fenn when the rain came?"** → owned, first-person
   recall of an action the game authored moments ago. Ledger index (live poll) already shows
   the two new memories.

(Both observe texts follow `identity-authoring.md` §5: first person, existing cast only —
Fenn, Piers, the well rope are corpus entities — no new proper nouns.)

## CLOSE (~72–75 s)

The instrumentation close, all judge-free numbers already earned:

- perceived-first-word **p50 938 ms / p95 1516 ms** (D1, on this slate)
- **~$0.12 per 100 turns** all-in
- believability: gist_precision **0.823**, fabrication_rate 0.043 (D1 run); held-out demo
  corpus: fabricated entities **0**, keyword retention **0.979** (E1)
- the tagline: self-hostable — your Postgres, your models.

## Rehearsal checklist (E2's guard; re-run until the take is good)

0. `.env`: batch roles synced to Opus 4.8 (Jack's pending action — binds now), real mode,
   `DATABASE_URI` → `longmem_demo`.
1. **Play-mode gate BEFORE any retarget/paste** (ordering: after the agent id is pasted,
   autoRun would replay scripted observes INTO the pinned demo agent): fake-mode serve on a
   scratch DB, `autoProvision` temporarily ON + `autoRun` ON → `[npc-demo] ALL PLAY-MODE
   BEATS PASSED` in the console → flip both back.
2. `python -m app.demo_loader --fresh` (real providers). The printed roll is the guard's
   input:
   - ref 3 (drovers): importance high enough for k=3 membership on the beat question, gist
     spans low (a saturated roll is un-driftable — E1 lesson 1);
   - ref 0 (Halvard) present with sane importance;
   - no `scoring_failed` / `escalation_failed` / `embedding_failed` flags anywhere.
   Re-run `--fresh` until the roll is good. **After a good take is pinned, never run the
   loader again** — `--fresh` is the only destructive path and it is deliberate.
3. Paste the printed agent id into the Unity inspector (`agentIdOverride`) and the Ledger
   deep link; paste ref 0's memory id into `correctionMemoryId`.
4. Start the real serve; workers settle (the demo agent's reflection/compiler flags are ON —
   let any auto-reflection land BEFORE rolling the beat-2 take: a reflect evicts affected
   reconstruction caches, the fourth sanctioned text-change cause, and would re-roll a
   pinned take).
5. Dry-run the beats in order. Beat-1 guard: ref 0's served score/rank moves across the
   correction. Beat-2 guard: the retelling is a real retell (visibly edited, not an echo)
   and not a refusal (the chain shows a new `reconstruction` head, not the prior text) —
   if it echoed or refused, re-provision (step 2) and re-roll. The take then pins by
   constancy: repeat reads are byte-identical.
6. Record timings per beat for the E3 edit; confirm the Ledger turn feed rendered every
   turn live (poll ON) and the identity pane shows the seed identity.

## What E2 built for this script (pointers)

The corpus→demo-DB loader (`app\demo_loader.py`, `--fresh`-guarded, prints the provisioned
roll + hand-off ids, merges the two worker flags after replay); the Ledger live turn feed
(`GET /v1/ledger/turns`, an in-memory tee at the two dialogue routes — the E2 ruling) + the
identity/state pane + the em-dash label sweep; C# `SceneBoundaryEvent.PrewarmContext` /
`SceneResult.Prewarm` (+ the 13-field `ScenePrewarmInstrumentation` DTO) and the
`NpcMemoryNpc` ObserveAndForget / DrainObservesAsync / PendingObserves passthroughs; the
driver beat controls; the Unity scene retarget to Branwen. Verification: the 17-beat console
harness (the new prewarm beat mirrors `tests\verify_prewarm.py` A/B/C), the suite's
`test_ledger_feed.py` + `test_demo_loader.py`, and this checklist's rehearsal.
