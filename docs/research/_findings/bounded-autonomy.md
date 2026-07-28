> Read `_baseline\current-architecture.md` FIRST. Every judgment is relative to that yardstick.

---

## Bounded Autonomy: Controlling LLM Characters in Live Multiplayer Games

- **Authors / venue / year:** Yunjia Guo, Siyu Wang, Jinghan Zhu, Haixin Qiao (Kotoko AI / Biibit Ltd); 2026
- **arXiv / DOI:** arXiv:2604.04703v2 [cs.HC]
- **Source:** folder
- **Overall relevance to longmem-npc:** Medium — this is a runtime *control* architecture for player-owned LLM characters in a live multiplayer social game (autonomy/steering/action-grounding), not a memory-storage system. It has no persistence, decay, or correction mechanism at all, so it doesn't compete with most of our baseline. It is relevant specifically to our **action-directive** and **reputation/steering** design (dialogue turn output → game-world effect).
- **Core contribution (2-3 sentences):** Frames "bounded autonomy" as a distinct control problem for LLM-driven NPCs in live multiplayer play, organized around three interfaces: agent-agent (Converge: relationship-biased reply targeting + probabilistic reply-chain decay), agent-world (Ground: embedding-based mapping of free-text LLM intent onto a fixed pool of 378 executable "behavior bundles," with confidence-thresholded safe fallback), and player-agent (Whisper: a soft natural-language steering signal that biases—but doesn't dictate—a character's next action/dialogue). Evaluated live in a deployed game plus controlled probes.

### Mechanisms relevant to us
- **Ground**: LLM emits free-text behavior intent → embedded (Sentence-BERT `all-mpnet-base-v2`) → cosine-matched against a fixed executable-action pool → execute top-1 match if similarity ≥ threshold, else safe default fallback action (§5, Figure 4).
- **Whisper**: player-issued short NL phrase that *conditions* the character's next bundle-selection + dialogue generation without replacing the model's own choice — Priority-A stimulus, distinct from full override (§6).
- **Reply-chain decay / priority arbitration**: for NPC-NPC dialogue chains only — depth-sensitive probabilistic continuation (§4). Not applicable to us; we have no autonomous NPC-NPC interaction loop, only a player-driven single-NPC dialogue turn.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none)* — Our dialogue turn already emits the action directive as **structured output constrained to the integrator's vocabulary** (baseline: "Action directive from integrator-supplied vocabulary"), which is a stronger guarantee than Ground's post-hoc embedding-match approach. Ground's own evaluation shows its embedding-grounding step is lossy (87% top-1 on the talk pool, only 63% on the non-talk pool, §7.2) — evidence that free-text-then-embed is *worse* than constrained structured output for the same problem, not an improvement on it.

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** A middle-ground, per-turn "soft steering" hook — an integrator/operator nudge that biases the next dialogue turn's content/action without overriding the model's own generation or writing anything to storage.
- **What the paper does:** Whisper — "a lightweight interaction technique that gives players structured entry into emergent character interaction... The character then produces its next action and dialogue through the standard selection, grounding, and response-generation stack, while retaining room to interpret or express the intent in its own way" (§6). Measured 86.7% intervention-aligned rate on a 30-case controlled benchmark (§7.3), with a causal check (swapping the whisper text flips the resulting action/dialogue direction in 5/5 cases).
- **Why worth adopting for an NPC memory service:** Our architecture has no analog — the reputation delta and action directive are model-authored outputs, and authorial correction only touches *stored* memory content, not a live turn's generation. A Whisper-equivalent (e.g., an optional per-call field injected into the dialogue prompt as a soft directive, distinct from a hardcoded template) would give the Unity integrator a lightweight live-directing tool that doesn't touch the non-destructive record at all — pure prompt-conditioning, no schema change.
- **Adoption cost/risk in our stack:** Low schema risk (no migration — it's a request-scoped prompt-assembly addition, not stored). Must not be hardcoded (per our "nothing integrator-configurable is hardcoded" invariant) — the field and its prompt template slot would need to be an explicit, documented per-call parameter, not silently baked into `dialogue.py`'s block assembly.
- **Docs it would touch:** `architecture.md` §9 (behavior output & turn topology), `cli-harness.md` (prompt-assembly block), Unity C# API surface queue item.
- **Confidence:** Medium — genuinely novel relative to baseline, but it's a UX/control feature, not core to the memory thesis; worth noting rather than urgent.

- **Capability:** Confidence-thresholded fallback for unrecognized/low-confidence action output (vs. our current silent drop).
- **What the paper does:** "If the top similarity score falls below a confidence threshold, the pipeline falls back to a designated safe default action rather than executing a low-confidence match" (§5).
- **Why worth adopting for an NPC memory service:** Our baseline's current behavior on an unrecognized directive is "log/ignore, turn still succeeds" — i.e., the NPC takes no action that turn. A designated safe-default action (itself part of the integrator-supplied vocabulary) would preserve in-world legibility instead of a silent no-op, at the cost of occasionally executing an action the model didn't actually intend.
- **Adoption cost/risk in our stack:** Cheap — a config-level default (`agents.config`), no schema change. Real cost: it can put words/actions in the NPC's mouth the model didn't choose, so it's a genuine design tradeoff, not a strict win — flagging honestly rather than as free lunch.
- **Docs it would touch:** `cli-harness.md` (action-vocabulary source / fallback), `architecture.md` §9.
- **Confidence:** Low-Medium — plausible improvement, not clearly superior, priced as a tradeoff.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none)* — no storage, no destructive operations, no gate-LLM claims in this paper.

### Quotable lines / citations for positioning (optional)
- On why consistency matters to players (useful for README framing): P2's interview quote, "the personality must remain consistent," because changing it made the character feel like "this ain't my original bibbit" (§7.4) — strong anecdotal support for our within-scene text-stability invariant and the cost of *unauthorized* drift, as distinct from our controlled/authored drift.
- "richer cognitive architectures could be layered beneath the control mechanisms described here" (§8) — the paper explicitly disclaims the cognition/memory layer, positioning longmem-npc as complementary rather than competing.

### Verdict
P3 note-only. Whisper is a genuinely novel, cheap-to-adopt UX idea (soft per-turn steering) worth a line in the Unity API-surface queue item, but nothing here challenges or improves the memory/retrieval/reconstruction core — this paper solves a different layer (runtime control) than longmem-npc (long-term memory).
