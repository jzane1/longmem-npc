## Retrieval as a Decision: Training-Free Adaptive Gating for Efficient RAG (TARG)

- **Authors / venue / year:** Yufeng Wang, Lu Wei, Haibin Ling — Transactions on Machine Learning Research, 04/2026 (first posted 2025-11).
- **arXiv / DOI:** 2511.09803v2 — https://arxiv.org/abs/2511.09803
- **Source:** discovered
- **Overall relevance to longmem-npc:** High — this is the "when to retrieve" literature's most direct, recent, evidence-heavy entry, and it lands squarely on the design question behind our mid-dialogue gate (`app\gate.py`, invariant #8 "the retrieval gate is non-LLM").
- **Core contribution (2-3 sentences):** TARG decides whether to retrieve using only a short (k≈20 token), no-context draft decode from the *same* generator model, computing a scalar uncertainty score from the draft's prefix logits (mean entropy, a top-1/top-2 logit-margin signal, or small-N sampling variance) and retrieving only when the score crosses a threshold. Across five QA benchmarks it matches or beats Always-RAG's accuracy while cutting retrieval calls 70-90%, with entropy losing discriminative power on modern instruction-tuned models while the margin/variance signals stay robust.

### Mechanisms relevant to us
- A single-shot, threshold-gated retrieval decision computed from model-internal signals rather than embedding similarity (§3.1-3.2).
- Threshold calibration by matching the empirical CDF of the gate score to a target retrieval **budget** rather than hand-picking a raw score cutoff (§3.4, "Threshold calibration and budget control").
- An explicit dominance/"usefulness calibration" argument for why a well-calibrated gate provably matches-or-beats both Always-retrieve and Never-retrieve in expectation (§3.3).
- Head-to-head comparison against FLARE, Self-RAG-lite, CRAG-lite, and SKR under a matched 1-retrieval-call budget — TARG's margin gate matches or beats these heavier reflective/multi-step methods at a fraction of the retrieval rate and added latency (Table 3, e.g. NQ-Open: TARG-Margin 39.0 EM at 6.2% retrieval + 0.71s vs. Self-RAG-lite 39.0 EM at 19.8% + 2.19s).

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none — TARG's gate signal requires a generator decode step per candidate check; our gate is deliberately non-LLM for cost/latency/determinism, so this is not a drop-in replacement for the novelty/tripwire signals themselves — see THESIS-TENSION below)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** budget-calibrated gate threshold — picking `gate_novelty_threshold` by targeting a retrieval RATE on a fixture/validation set (via the empirical CDF of the gate's score distribution) rather than by hand-picking a fixed cosine-distance cutoff.
- **What the paper does:** "To hit a retrieval budget ρ ∈ [0,1], pick τ = F_U^{-1}(1-ρ). Alternatively, select τ that maximizes dev accuracy. Because U is scalar, calibration is fast and stable." (§3.4) — they report operating points at 5-20% retrieval budgets and show the accuracy-efficiency frontier this yields (Tables 1-2).
- **Why worth adopting for an NPC memory service:** our `gate_novelty_threshold` (default 0.5) and `gate_fetch_k` (3) are currently fixed defaults tuned by measurement/feel (per the 2026-07-19 session's fake-mode-calibration learning already recorded in `decisions.md`). A CDF-based calibration procedure would let an integrator target "fetch on roughly N% of turns" directly and reproducibly, which is a much more legible knob for a game designer than a raw cosine-distance number.
- **Adoption cost/risk in our stack:** small — this is an *offline calibration procedure* for an existing config knob, not a new mechanism. No schema change, no new model role, no invariant touched. It would live as a documented recipe (or an optional CLI/load-driver utility) rather than new runtime code.
- **Docs it would touch:** `docs\mid-dialogue-gate.md` (knob-tuning guidance), possibly `app\load_driver.py` if we want a computed calibration report alongside the existing gate efficacy block.
- **Confidence:** Medium — the calibration idea transfers cleanly; the exact CDF machinery would need to be re-derived for our novelty-distance signal rather than copied verbatim (TARG calibrates a logit-based score, we'd calibrate a cosine-distance score — same idea, different distribution shape).

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
- **Invariant challenged:** #8, "The retrieval gate is non-LLM. No gate model, no gate env var."
- **What the paper does that conflicts:** TARG's core mechanism is to decode a short prefix from the generator LLM for *every* gate check and read its logits — i.e., every retrieval decision costs an LLM forward pass, even though "tens to hundreds of draft tokens" is cheap relative to a full generation (§3.1, Algorithm 1). It is not a separate "gate model" (it reuses the dialogue model), but it is still an LLM call purely for gating.
- **Honest read:** this is a genuine, evidence-backed alternative design, not an apples-to-oranges mismatch — TARG is solving exactly our "when to retrieve" problem, just with a different signal source. Adopting its core mechanism as our gate signal would mean paying a real LLM decode on every turn purely to decide whether to fetch, which directly contradicts why we built a non-LLM gate in the first place (cost, latency, and determinism for a mid-scene check that must not become the bottleneck it's supposed to be gating). The paper's own finding that "unconditionally retrieving is not a safe default" and that prefix-entropy signals degrade on modern instruction-tuned models (§5-6) is useful ammunition *for* our embedding+entity-tripwire design being the more principled non-LLM choice — but the core TARG mechanism itself is not something we should adopt without accepting the LLM-per-check cost the invariant was written to avoid.

### Quotable lines / citations for positioning (optional)
- "Retrieving for every query often hurts quality while inflating tokens and latency." (Abstract) — supports the general case for a gate at all, independent of gate mechanism.
- "Unconditionally retrieving (Always) is not a safe default... the generator spends compute integrating irrelevant context." (§6, Discussion) — good positioning line for why our gate exists.
- "As instruction-tuned models become more peaked, prefix entropies compress and lose ranking power." (§6) — a concrete empirical caution against ever using raw model-confidence/entropy as a retrieval-decision signal, reinforcing why a semantic/structural signal (our novelty distance + entity tripwire) is more robust than a model-introspective one.

### Verdict
P2 worth-piloting: not an adoption of TARG's mechanism (it conflicts with the non-LLM-gate invariant), but its budget-calibration recipe for setting `gate_novelty_threshold` from a target fetch-rate is a cheap, low-risk improvement to how we tune the gate we already have, and its comparison data is useful ammunition for why a non-LLM gate is a defensible choice over model-confidence-based alternatives.
