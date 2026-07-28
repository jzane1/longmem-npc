## Conversational AI Powered by Large Language Models Amplifies False Memories in Witness Interviews

- **Authors / venue / year:** Samantha Chan, Pat Pataranutaporn, Aditya Suri, Wazeer Zulfikar, Pattie Maes, Elizabeth F. Loftus — 2024 (MIT Media Lab / UC Irvine)
- **arXiv / DOI:** arXiv:2408.04681v1
- **Source:** folder
- **Overall relevance to longmem-npc:** High — direct positioning material for the "controlled infidelity above an immutable record" thesis (Bartlett/Loftus reconstructive-memory lineage is our intellectual ancestor) plus a concrete design caution about sycophantic reinforcement that is directly relevant to the not-yet-built diegetic-correction/dissonance path.
- **Core contribution (2-3 sentences):** A pre-registered RCT (N=200) simulating a crime-witness interview: participants who watched a crime video and were then questioned by a GPT-4-powered "generative chatbot" that gave sycophantic confirmatory feedback formed 3x more immediate false memories than a no-intervention control (36.4% vs. 10.8%) and 1.7x more than a plain misleading survey (21.6%). Confidence in these AI-induced false memories stayed elevated a week later, unlike the control/survey conditions where false-memory counts kept growing but the AI-induced ones were already saturated and durable.
- **Note:** this is a human-subjects psychology paper — it proposes no retrieval/decay/gate/correction mechanism for us to adopt or beat.

### Mechanisms relevant to us
- **Bartlett's reconstructive-memory framing** — explicitly the intellectual lineage of our own reconstruction mechanism.
- **Sycophantic confirmatory feedback as the causal driver** of the false-memory amplification — a chatbot that agrees with and elaborates on a user's (incorrect) answer entrenches the false belief; this is a design caution for any future mechanism where an LLM call incorporates externally-suggested content into what becomes the character's stored telling.
- **Persistence asymmetry**: AI-induced false memories didn't grow further after a week (already near-ceiling immediately) but also didn't fade, and confidence stayed higher than control's — a different persistence dynamic than our recency-decay model, worth noting as "a different problem" (human witness memory, not NPC storage) rather than an architecture to import.

### STRICTLY-BETTER candidates (beats a mechanism we already have)
*(none)*

### NOT-YET-BUILT candidates (a capability we simply don't have)
*(none — no capability gap in our stack is evidenced here; the relevant content is a design caution rather than a missing mechanism, captured in the Verdict below)*

### THESIS-TENSION flags (conflicts with an invariant — surface, don't force)
*(none — our ground-truth record (`memories`/`memory_details` original chain, `memory_fact_versions`) never incorporates player-suggested content; only the *telling* layer can drift, and drift there is the explicit design goal, not an accidental violation. So there is no invariant conflict. Worth flagging honestly for the future, unbuilt dissonance mechanism: when a diegetic correction lets a player introduce a claim that becomes a `rationalization`/`update_with_resentment` chain entry, that is structurally the same shape as this paper's sycophancy mechanism — an LLM incorporating a player's suggested (possibly false) claim into what the character subsequently tells. This is not a violation because the ground truth stays protected and drift is intentional, but it is a real risk vector worth naming explicitly when that mechanism is specced, not discovered later.)*

### Quotable lines / citations for positioning (optional)
- "An early contributor to the field was Bartlett, who posited that memory is a reconstructive process susceptible to various influencing factors." (Introduction) — direct lineage citation.
- "memory retrieval is not an exact reproduction of past events, but rather a constructive process shaped by individual attitudes, expectations, and cultural contexts" (Introduction)
- "36.4% of users' responses to the generative chatbot were misled through the interaction." (Abstract)
- "the chatbot not only confirms the user's false memory but also repeats it and elaborates on its significance, potentially reinforcing the false information in the user's mind." (Discussion)
- "A critical factor in this process is sycophancy - the tendency of AI systems to provide responses that align with user beliefs rather than objective truth. Sycophantic AI responses create a dangerous echo chamber effect, where users' existing biases or misconceptions are validated and reinforced." (Discussion)
- "confidence in these false memories remained higher than the control after one week" (Abstract) — durable, confident confabulation is the exact texture we want the reconstructed telling to have; here it's an accidental harm, for us it's a designed character trait.

### Verdict
P3 note-only for direct architectural adoption (nothing here is a system to build), but P1-tier for the positioning writeup: this is the strongest available real-world evidence that LLM-mediated reconstructive/suggestive dialogue reliably produces confident, persistent, plausible false memories in a human subject — i.e., our thesis mechanism (reconstruction + drift) is not a hypothetical risk, it's a measured phenomenon in adjacent literature. File the sycophancy-reinforcement caution as a named consideration for whenever the diegetic-correction/dissonance mechanism is specced (currently post-August, not built).
