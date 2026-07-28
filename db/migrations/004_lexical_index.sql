-- 004_lexical_index.sql — the hybrid lexical retrieval channel's index
-- (research-adoption slate Target B, ruled 2026-07-20; docs\read-path.md
-- carries the annotated contract; provenance in
-- docs\research\CHANGES-FROM-RESEARCH.md).
--
-- A partial GIN full-text index over LIVE fact heads (the 002/003
-- partial-index precedent — `invalid_at IS NULL` stated verbatim so the
-- planner matches the predicate): the lexical candidate fetch matches a
-- mechanical token-OR tsquery over the utterance against
-- to_tsvector('simple', basis_text), giving exact-name/phrase recall that
-- does not depend on embedding neighborhoods. The fetch unions into the
-- vector over-fetch BEFORE scoring; the scoring formula is untouched.
--
-- 'simple' (no stemming, no stopword removal) is the SERVICE-DEFAULT
-- text-search config, baked into the index expression because an expression
-- index necessarily binds one config. The per-agent `text_search_config`
-- override (agents.config) still works — the query-side expression follows
-- the agent's config — but a non-default config runs the same predicate
-- unindexed (correct, slower; stated per-field behavior). Nothing
-- integrator-configurable is hardcoded: the default lives in app\config.py,
-- the override in agents.config; only the index's own expression is fixed,
-- as any expression index must be.

CREATE INDEX IF NOT EXISTS memory_fact_versions_basis_tsv_gin
    ON memory_fact_versions
    USING gin (to_tsvector('simple', basis_text))
    WHERE invalid_at IS NULL;
