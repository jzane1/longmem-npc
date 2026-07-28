# LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals

- **Authors / venue / year:** Joon Sung Park, Carolyn Q. Zou, Jonne Kamphorst, Niles Egan, Aaron
  Shaw, Benjamin Mako Hill, Carrie Cai, Meredith Ringel Morris, Percy Liang, Robb Willer, Michael
  S. Bernstein (Stanford / Northwestern / U. Washington / Google DeepMind / Sciences Po). Preprint
  / working paper style manuscript (PNAS-track formatting: Abstract, Significance Statement,
  numbered SM appendix); no arXiv ID or DOI is present anywhere in the extracted text.
- **arXiv / DOI:** Not stated in the extracted text.
- **Source:** folder (full document read, ~5,300 lines incl. supplementary material).
- **Overall relevance to longmem-npc:** High — this paper is squarely about **identity/persona
  grounding technique quality** (self-report-grounded vs. demographic-only vs. short "persona
  paragraph" agents), which is one half of our signature research pair
  (identity-conditioned reconstructive memory). It gives strong, quantified evidence that grounding
  depth/format matters far more than model choice, directly bearing on how `agents.seed_identity` /
  `identity_documents` should be authored and revised.
- **Core contribution (2-3 sentences):** Building on the Park et al. (2023) "generative agents"
  lineage, the authors ground 1,052 individually-modeled agents in either (a) a 2-hour, AI-conducted
  semi-structured life interview, (b) structured surveys (General Social Survey + Big Five), or (c)
  both, and show these predict the real individual's held-out attitudes, personality, and
  incentivized-game behavior far better than demographic-only or short "persona paragraph" agents —
  reaching 82-86% of participants' own two-week test-retest reliability ceiling, vs. 71-74% for the
  shallow baselines.

### Mechanisms relevant to us
- **Identity-grounding-depth ablation** (identity/persona component): demographic-only (0.74
  normalized accuracy on GSS) < persona-paragraph (0.71) < interview-only (0.83) ≈ survey-only
  (0.82) < interview+survey (0.86). Directly comparable to our `seed_identity`/`identity_documents`.
- **"Expert Reflection" module** (SM3, pp.11-12): from the raw self-report data, the system
  generates four *persona-lensed* reflection sets once — up to 20 bullet observations each, written
  from the stance of a psychologist, behavioral economist, political scientist, and demographer —
  and stores them as the agent's durable "memory." At prediction time, an LLM classifies which
  expert lens best matches the incoming question, retrieves only that expert's reflections, and
  appends them to the raw self-report data before a final chain-of-thought answer. This is a
  concrete precedent for our designed-but-unbuilt reflection pipeline, and specifically for a
  **routing-by-type retrieval layer** (choose which precomputed lens applies) that sits alongside
  vector-similarity retrieval rather than replacing it.
- **Bounded-context rolling reflection inside one long interaction** (SM2, pp.5-6): the AI
  interviewer itself avoids feeding its follow-up-question generator the whole (unboundedly
  growing) transcript; instead it periodically regenerates a compact structured summary
  (`{"place of birth": "New Hampshire", "outdoorsy vs. indoorsy": "outdoorsy..."}`) and conditions
  only on that summary plus the last 5,000 characters. Critically, the **full transcript is still
  retained** for downstream agent-grounding — the rolling summary is a transient reasoning aid for
  the interviewer's next turn, not a destructive replacement of the source data.
- **Ablation robustness** (SM section "Random Lesion Interview Agents" / "Summary Agents", ~line
  593-604): removing 80% of the interview transcript only dropped normalized GSS accuracy from
  0.82 to 0.79; converting the transcript to bullet-point summaries (discarding linguistic surface
  form, keeping factual content) scored 0.81 vs. 0.82 raw — i.e., *informational content* of the
  grounding data drives accuracy far more than verbatim wording or sheer volume, once a sufficient
  depth is reached.
- **Bias/parity**: richer self-report grounding narrows (not eliminates) accuracy gaps across
  political-ideology and racial subgroups relative to demographic-only prompting (Fig. 3, e.g. GSS
  DPD 13.75% demographic → 6.22-8.60% interview/survey) — relevant if NPC behavior should avoid
  defaulting to stereotype under thin identity specs.
- **"Direct retrieval" vs. "inference"** (main text Discussion + SM "Why do interview-based
  generative agents work?", ~line 615-756): the model sometimes locates a fact stated verbatim
  elsewhere in the transcript ("direct retrieval") and sometimes combines a stated fact with
  general world knowledge to deduce something never stated ("inference" — e.g. inferring "no
  workplace supervisor" from "I'm a full-time student"). Removing questions specifically
  answerable-by-inference hurts interview-grounded agents in particular (demographic/persona
  agents are unaffected either way), showing the grounding data does real inferential work rather
  than pure lookup.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
- **Component touched:** Identity structures / `agents.seed_identity` + `identity_documents`
  (baseline: currently "seed-prose-only" — a static, author-written prose bio, functionally a
  short persona description until the reflection pipeline lands).
- **Our current mechanism:** A hand-authored prose `seed_identity`, rendered once into
  `identity_documents`, unrevised pre-reflection.
- **Paper's mechanism:** Ground identity instead in a much richer, structured self-report (a
  2-hour semi-structured life-interview transcript, optionally plus structured survey-style items)
  — a tier of grounding depth well above a short persona paragraph — *evidence:* main text, "For
  the `persona-based' generative agents, we asked participants to write a brief paragraph about
  themselves... persona-based agents reached 0.71" vs. "the interview-based generative agents
  predicted participants' responses with an average normalized accuracy of 0.83"; ANOVA confirms
  interview/survey/survey+interview agents each significantly outperform persona agents (all
  p < .001).
- **Why strictly better:** A "persona paragraph" in this study is methodologically the closest
  analog to a hand-authored `seed_identity` prose bio — both are short, author-composed self/other
  descriptions. The paper shows this exact class of input underperforms richer self-report grounding
  by a large, statistically significant margin on predicting the real individual's actual attitudes
  and behavior, and the advantage survives removing 80% of the richer transcript.
- **Adoption cost/risk in our stack:** Low — no schema change. `agents.seed_identity` /
  `identity_documents` already accept arbitrary prose; a richer input is just a longer,
  interview-structured document (or literally an in-character semi-structured interview an
  integrator conducts with their own writer/design doc) instead of a short bio. Real cost is
  authorial effort per NPC and token budget when rendering/reflecting over a much longer document —
  no invariant is touched.
- **Docs it would touch:** `docs\architecture.md` §4.3 (identity structures), a future reflection
  spec (identity revision / grounding-depth guidance).
- **Confidence:** Medium — the paper measures predicting a real person's *survey answers*, not
  player-perceived NPC dialogue believability; the transfer from "predicts GSS responses more
  accurately" to "reads as a more consistent, less generic game character" is plausible and
  consistent with the paper's own framing, but not directly tested in an NPC/dialogue setting.

### NOT-YET-BUILT candidates (a capability we simply don't have)
- **Capability:** Persona-lensed reflection retrieval routing (typed reflection sets selected by
  LLM classification of query/situation type, layered on top of vector-similarity retrieval).
- **What the paper does:** Generates four fixed domain-expert reflection sets once per person, then
  at query time classifies which expert best answers the current question and retrieves only that
  expert's notes — *evidence:* SM3 ~p.11, "we first classified, by prompting the language model,
  which domain expert...would best answer the question. We then retrieved all reflections generated
  by that particular expert."
- **Why worth adopting for an NPC memory service:** Our reflection pipeline is designed but not
  built (gap noted in baseline: "Reflection pipeline — designed, not built"). This is a concrete,
  cheap pattern: precompute a handful of typed "lenses" over an NPC's identity/memory at reflection
  time (e.g., relationship-lens, grievance-lens, goal-lens) and route dialogue-turn recollection to
  whichever lens matches the situation, as a complement to — not a replacement for — cosine-distance
  retrieval. Could sharpen reconstruction's identity-conditioning cheaply once reflection exists.
- **Adoption cost/risk in our stack:** Needs a new reflection role/model call (already sequenced
  post-August) plus a lightweight classification step (one more model call, its own env var per our
  per-role-config rule). No conflict with bi-temporal/non-destructive storage — whatever table holds
  the lensed reflections would follow the same invalidate-don't-delete discipline as everything else.
- **Docs it would touch:** A future `reflection.md` spec; `architecture.md` §10 (reflection /
  parameter compiler).
- **Confidence:** Medium — validated for survey-answer prediction at population scale, not tested
  for dialogue generation, retrieval latency, or interaction with our existing gate/reconstruction
  stages.

- **Capability:** Bounded-context rolling reflection for a single long-running interaction
  (working-memory compression that never touches the persisted source).
- **What the paper does:** The AI interviewer conditions its next-question generation on a
  periodically regenerated compact summary plus only the last 5,000 characters of transcript,
  rather than the whole growing conversation, while the full transcript is separately retained for
  downstream agent-building — *evidence:* SM2 pp.5-6, "instead of including the full interview
  transcript, we included the much more concise but descriptive reflection notes... and the most
  recent 5,000 characters."
- **Why worth adopting for an NPC memory service:** A precedent for keeping a single very long,
  uninterrupted dialogue scene's prompt-assembly bounded without discarding anything from storage —
  relevant only if a scene runs long enough that the recollection partition in `app\dialogue.py`
  risks unbounded growth within one scene (today, scenes are explicitly bounded by scene-boundary
  events, so this is a low-urgency, speculative fit).
- **Adoption cost/risk in our stack:** Low if ever needed — a prompt-assembly policy change in
  `app\dialogue.py`, no schema impact.
- **Docs it would touch:** `docs\cli-harness.md` / a future dialogue spec, only if scene length
  becomes a demonstrated problem.
- **Confidence:** Low — speculative; no evidence yet that our scenes run long enough to require it.

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none — no destructive summarization, ORM, gate-LLM, or embedding-dimension proposal appears.
Note: the paper's framing — "memories, stored in a database (or 'memory stream') in text form, are
retrieved as needed," citing Park et al. 2023 — is compatible with, not in tension with, our
bi-temporal non-destructive design; it simply says nothing about persistence/versioning semantics,
so there is nothing to compare against on that specific axis.)*

### Quotable lines / citations for positioning (optional)
- "the quality of individual simulation depends far less on model scale or synthetic persona
  engineering than on the depth and reliability of the data an agent is built from" (Discussion) —
  strong, directly citable line for arguing that identity-grounding depth (not swapping dialogue
  models) is what should drive believable, consistent NPC character simulation.
- "`direct retrieval`, in which the model locates an answer already embedded in a transcript even
  when the original question was on a different topic, and `inference`, in which the model
  combines what a participant reports with its general knowledge of the world to deduce a likely
  answer that is never stated" — useful vocabulary for describing what our reconstruction/dialogue
  call is doing when it "fills in" from gist + world knowledge.
- "self-report-grounded agents generally outperformed demographic and persona baselines" — a
  one-line summary worth citing verbatim if the README ever argues for grounding depth over
  shallow character bios.

### Verdict
P2 worth-piloting: the identity-grounding-depth finding is well-evidenced, statistically strong,
and cheap to test in our stack (no schema change — just a richer `seed_identity` document). Jack
should consider authoring `seed_identity` more like a structured self-report/interview than a short
character bio, and the "expert reflection" persona-lensed retrieval-routing pattern is worth
explicitly weighing when the (currently sequenced-later) reflection pipeline is actually specced.
Priority is elevated by this paper's direct relevance to the identity-conditioning half of the
project's stated thesis.
