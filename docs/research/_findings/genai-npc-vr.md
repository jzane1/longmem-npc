# Dialogs with GenAI NPCs: Exploring Player Interactions with Speech Agents in a VR Game

- **Authors / venue / year:** Zargham, Tonini, Alexandrovsky, Ruthven, Friehs, Dratzidis, Danekas,
  Bikas, Nacke, Zebel, Malaka — *International Journal of Human–Computer Interaction*, 2026.
- **arXiv / DOI:** DOI 10.1080/10447318.2026.2620647 (no arXiv; open-access journal article).
- **Source:** folder
- **Overall relevance to longmem-npc:** Low-Medium — this is an HCI user study (N=48) of a VR
  speech game built on the closed-source InWorld AI middleware. No memory/retrieval/identity
  architecture is disclosed (InWorld is a black box behind a "Core Description" + attribute
  prompt). Its value to us is entirely in the player-facing believability/immersion findings,
  not in any adoptable mechanism.
- **Core contribution (2-3 sentences):** An exploratory two-site user study (Canada + Netherlands)
  of "Office Whispers," a VR adventure/puzzle game with four InWorld-powered GenAI NPCs players
  address via open speech instead of dialogue trees. Players reported strong immersion, novelty,
  and freedom of expression, but recurring hallucinations, contradictory answers between NPCs, and
  lack of context-awareness broke immersion and caused frustration/distrust. The paper argues
  GenAI NPCs function as "dynamic and partially unpredictable social actors" whose perceived
  believability depends as much on interactional reliability as on narrative/visual design.

### Mechanisms relevant to us
- None disclosed at the architecture level. NPCs are configured via InWorld's "Core Description"
  (motivations/flaws/actions) + attributes (name, pronouns, role, interests) — a single persistent
  character prompt, no described retrieval, decay, or versioning. This is the "static persistent
  prompt" baseline our retrieval/reconstruction pipeline already structurally exceeds; there is
  nothing here to compare against our decay/reconstruction/correction/gate components technically.
- The paper is useful only for its **player-facing findings about believability, memory
  expectations, and dialogue quality** (§5.4, §5.5, §6), which is why it was assigned.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none — no competing mechanism is described in enough detail to compare)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** Cross-NPC shared world-fact consistency — a mechanism ensuring multiple NPCs
  give non-contradictory answers about the same in-world event/fact.
- **What the paper does:** Players frequently received contradictory or evasive answers from
  different NPCs about the same puzzle facts, and read this as intentional dishonesty rather than
  a system limitation — *evidence:* §5.3.2/§5.4.2, "Six felt certain characters were withholding
  information... 'They did not answer questions they were meant to know' (P20)"; §5.4.2, "This
  inconsistency led to players receiving contradictory answers from different NPCs, which caused
  confusion and made players speculate about which character could be trusted." Also §5.4.2:
  "Three players hoped for more context-aware NPCs, wishing them to know about past and present
  events by the player **and other NPCs**."
- **Why worth adopting for an NPC memory service:** longmem-npc's schema is scoped per-agent
  (each NPC has its own memory/fact/reputation rows); nothing in the baseline names a shared,
  cross-agent event ledger that multiple NPCs could consistently draw on for the same world fact.
  This paper is direct evidence that inconsistent cross-character knowledge is a top believability
  complaint in a real multi-NPC deployment, which is exactly the failure mode a shared,
  bi-temporally-versioned ground-truth event layer (as opposed to per-agent-only memory) would
  prevent.
- **Adoption cost/risk in our stack:** Would require a genuinely new schema concept — a
  world-scoped (not agent-scoped) fact table that multiple `agents` rows can read from, distinct
  from each NPC's private `memories`/`memory_fact_versions` chain. Non-trivial: needs its own
  migration, its own retrieval path decision (do NPCs still confabulate their *own telling* of a
  shared fact, or is the shared layer immune to per-NPC drift?), and is out of scope for any single
  currently-queued target. Does not conflict with any invariant on its own.
- **Docs it would touch:** `docs\architecture.md` (a new §, likely adjacent to identity/gist),
  a new migration spec if pursued.
- **Confidence:** Medium — the finding is well-evidenced in the paper, but longmem-npc's
  single-player, per-NPC design may make this genuinely out of current scope rather than a gap to
  close soon.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none — no destructive storage, ORM, gate-LLM, or embedding-dimension proposal appears in this
paper)*

**Honest note (not a strict invariant conflict, worth flagging anyway):** several players
attributed unintentional hallucinations/misrecognitions to the *character's* personality ("he was
lying," "maybe he had a bad day," an NPC misheard as a "ship captain" and improvised a whole
pirate persona from the error — §5.4.2/§5.5) rather than to the underlying system. This is a real
risk for longmem-npc's confabulation thesis specifically: if players can't reliably distinguish an
*accidental* model error from our *deliberately designed* controlled-drift/telling divergence, the
research contribution (intentional, tracked infidelity) could read to a player exactly like the
unintentional failure mode this paper documents as immersion-breaking. Not an architecture defect,
but a demo-legibility risk worth carrying into Unity choreography (the debug view distinguishing
ground truth from told version is the mitigation already in place).

### Quotable lines / citations for positioning (optional)
- "It seemed so real... You just felt part of the game" (P29) vs. "It feels less like I'm having a
  conversation with a human being, but rather with just a response machine" (P2) — the same study,
  same NPCs, opposite immersion outcomes depending on whether the system happened to fail that
  session.
- "Did he lie? Did he not lie?" (P8) — players actively theorize about NPC honesty even when no
  honesty mechanism exists; motivates that a *designed* ground-truth-vs-telling distinction (our
  thesis) is filling a gap players already probe for on their own.
- "The characters should have a more natural response to my behavior... know about past and
  present events by the player and other NPCs" (P33) — direct player articulation of the
  memory-grounding expectation longmem-npc is built to satisfy (context of past events), plus the
  cross-NPC consistency gap noted above.

### Verdict
P3 note-only for architecture — nothing here is adoptable as a mechanism. P2 worth-piloting as
**demo-risk and positioning evidence**: this paper is good citable support for why a persistent,
retrieval-grounded, ground-truth-backed memory service (vs. a static character-prompt middleware)
should reduce exactly the complaints (contradiction, "doesn't remember," generic non-answers) this
study surfaces — and it's a caution to make the debug/ground-truth view demo-legible so designed
drift doesn't read as the same failure mode as accidental hallucination.
