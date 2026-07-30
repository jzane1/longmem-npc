"""eval_metrics.py — the judge-free metric layer (eval-harness.md stage 1).

Pure arithmetic over sets and strings: one implementation consumed by the
reconstruction-metrics route (The Ledger's on-screen numbers), the eval
runner (stage 2+), and the suite. No model call, no database, and no spaCy
at module import — lemma/NER sets arrive as inputs (`nlp.lemma_content_set`
/ `nlp.extract_entities` are the canonical producers), so the metric unit
tests run unmarked.

The honest-denominator rule (ruled with the spec, 2026-07-29): every ratio
returns None on an empty denominator — a memory with zero measurable gist
facts reports null, never a flattering 1.0 (the thin-gist lesson).
"""

from __future__ import annotations

import re

from app.reconstruction import merge_spans, split_gist_detail

# The reconstruction thinning splitter's pattern (app\reconstruction.py):
# deterministic, dependency-free sentence boundaries — correction-anchored
# gist facts split with the same rule the constraint itself is built on.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# The composed reconstruction cache key is f"{identity_version}|b{band}"
# (reconstruction.compose_cache_key) — this parses the band back out.
_BAND_TAIL = re.compile(r"\|b(\d+)$")


def gist_fact_texts(
    observation_text: str,
    spans: list[tuple[int, int]],
    anchor_cause: str | None,
    anchor_content: str,
) -> list[str]:
    """The gist facts the live telling is measured against — anchor-cause-
    aware, mirroring `build_reconstruction_item` exactly so the metric
    measures the same constraint reconstruction enforced: on an
    `authorial_correction`-anchored chain the corrected head IS the fixed
    facts (sentence-split); otherwise one fact per MERGED gist span, sliced
    verbatim from the immutable observation text."""
    if anchor_cause == "authorial_correction":
        return [s.strip() for s in _SENTENCE_SPLIT.split(anchor_content) if s.strip()]
    return [observation_text[start:end] for start, end in merge_spans(spans)]


def detail_segment_texts(
    observation_text: str,
    spans: list[tuple[int, int]],
    anchor_cause: str | None,
) -> list[str]:
    """The non-gist remainders detail-recall is measured over. Empty on a
    correction-anchored chain — no observation detail was re-injected there
    (build_reconstruction_item passes ""), so none is owed."""
    if anchor_cause == "authorial_correction":
        return []
    return split_gist_detail(observation_text, spans)[1]


def gist_precision(
    fact_lemma_sets: list[set[str]],
    telling_lemmas: set[str],
    threshold: float,
) -> tuple[float | None, list[bool | None]]:
    """(precision, per-fact presence flags), aligned with the input facts.

    A fact is PRESENT when at least `threshold` of its content lemmas appear
    in the telling's lemma set. A fact with an empty lemma set (e.g. a bare
    pronoun coref span) is UNMEASURABLE — flagged None and excluded from
    both sides of the ratio. None precision at zero measurable facts."""
    flags: list[bool | None] = []
    for fact in fact_lemma_sets:
        if not fact:
            flags.append(None)
            continue
        flags.append(len(fact & telling_lemmas) / len(fact) >= threshold)
    measurable = [f for f in flags if f is not None]
    if not measurable:
        return None, flags
    return sum(measurable) / len(measurable), flags


def detail_recall(detail_lemmas: set[str], telling_lemmas: set[str]) -> float | None:
    """Fraction of detail content lemmas still present in the telling.
    The caller subtracts the gist lemma union first (detail never gets
    credit for words the gist already carries). None on empty detail."""
    if not detail_lemmas:
        return None
    return len(detail_lemmas & telling_lemmas) / len(detail_lemmas)


def fabricated_entities(
    telling_entities: list[str], ground_texts: list[str]
) -> list[str]:
    """Telling entities found (case-insensitive whole-word) in NONE of the
    ground texts — the never-observed-detail detector. Order-preserving,
    deduped case-insensitively; empty ground strings are skipped."""
    from app.nlp import find_term_spans  # regex-only helper; no spaCy load

    grounds = [g for g in ground_texts if g]
    fabricated: list[str] = []
    seen: set[str] = set()
    for entity in telling_entities:
        key = entity.lower()
        if not entity.strip() or key in seen:
            continue
        seen.add(key)
        if not any(find_term_spans(ground, entity) for ground in grounds):
            fabricated.append(entity)
    return fabricated


def fabrication_rate(
    telling_entities: list[str], fabricated: list[str]
) -> float | None:
    """fabricated / distinct telling entities; None at zero entities."""
    distinct = {e.lower() for e in telling_entities if e.strip()}
    if not distinct:
        return None
    return len(fabricated) / len(distinct)


def keyword_retention(
    observation_entities: list[str], telling_text: str
) -> float | None:
    """The 2511.10277 retention check: fraction of the observation's NER
    entities still present (case-insensitive whole-word) in the telling.
    None at zero observation entities."""
    from app.nlp import find_term_spans  # regex-only helper; no spaCy load

    distinct: list[str] = []
    seen: set[str] = set()
    for entity in observation_entities:
        key = entity.lower()
        if entity.strip() and key not in seen:
            seen.add(key)
            distinct.append(entity)
    if not distinct:
        return None
    present = sum(1 for e in distinct if find_term_spans(telling_text, e))
    return present / len(distinct)


def band_from_composed_key(key: str) -> int | None:
    """Invert compose_cache_key: the decay band from a composed cache key,
    None for a key without the |b<N> tail (never a guess)."""
    match = _BAND_TAIL.search(key)
    return int(match.group(1)) if match else None
