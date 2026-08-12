"""eval_judge.py — rubrics, verdict models, and agreement/Pareto arithmetic.

Eval-harness stage 3 (`docs\\eval-harness.md`). The judge layer's PURE half:
rubric constants with version tags, pydantic-validated verdict shapes, the
position-swap pairwise combiner, hand-rolled agreement arithmetic (raw % +
Cohen's kappa), Pareto non-domination, and the gold-set row model. The
provider half (Fake/Real judge) lives in app\\providers.py; the orchestration
(judged pass, emit-gold / agreement / compare verbs) in app\\eval_runner.py.

Four judged categories (ruled 2026-07-29): selective_forgetting and
abstention are fixture-authored per utterance (JudgedSpec,
app\\eval_scenarios.py); reconstruction_faithfulness rides the memory chain
(the runner assembles gist facts + the live telling); prose_pairwise is
compare-time over two arms' captured prose.

Honest denominators throughout (the harness principle): every ratio is None
on an empty or degenerate denominator, never 0.0 or 1.0 by fiat.

Pure module: no db, no spaCy, no provider imports.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

# ---------------------------------------------------------------------------
# Rubrics (fork 4, ruled 2026-08-07: module constants with rubric_version
# tags). System prompts end with the JSON-only output contract — the same
# "Return ONLY a JSON object ... No other text." shape every real provider
# prompt in this repo uses; the judge parses with the same lenient reader.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Rubric:
    category: str
    rubric_version: str
    system_prompt: str
    user_template: str  # str.format fields; the runner fills them


_SF_SYSTEM = (
    "You are grading a game NPC's dialogue reply for selective forgetting — "
    "whether the NPC speaks from its CURRENT memory state after corrections, "
    "never a superseded one. You get the player's question, the NPC's reply, "
    "the reference (what the NPC's current memories hold true), and possibly "
    "a superseded telling (what an earlier, since-corrected memory held). "
    "Grade pass when the reply is consistent with the reference and does not "
    "assert the superseded content as current truth; paraphrase of the "
    "reference counts. Grade fail when the reply asserts superseded content, "
    "contradicts the reference, or invents specifics absent from it. A reply "
    "that conveys only part of the reference still passes if nothing it "
    'asserts is wrong. Return ONLY a JSON object with keys: verdict ("pass" '
    'or "fail") and rationale (one sentence). No other text.'
)

_ABST_SYSTEM = (
    "You are grading a game NPC's dialogue reply for premise-awareness. You "
    "get the player's question, the NPC's reply, the reference (the true "
    "state in the NPC's memories), and the expected behavior. If expected "
    'behavior is "abstain", the question\'s premise is false or unanswerable '
    "from the NPC's memories: pass only if the reply declines, corrects the "
    "premise, or expresses not knowing — fail if it plays along with the "
    'false premise or invents an answer. If expected behavior is "answer", '
    "the premise is sound: pass only if the reply actually answers, "
    "consistently with the reference — fail if it wrongly refuses or "
    "contradicts the reference. Return ONLY a JSON object with keys: verdict "
    '("pass" or "fail") and rationale (one sentence). No other text.'
)

_RF_SYSTEM = (
    "You are grading a game NPC's reconstructed memory telling for "
    "faithfulness to its fixed gist. You get the current telling and a "
    "numbered list of gist facts from the original observation. For each "
    "fact, judge whether the telling semantically supports it — paraphrase "
    "counts as support; dropping, contradicting, or reversing it does not. "
    "Also list any concrete claims in the telling that are fabricated: "
    "specific people, objects, events, or quantities not derivable from the "
    "gist facts. Style drift and softened wording are NOT fabrication. "
    "Return ONLY a JSON object with keys: gist_supported (list of booleans, "
    "one per numbered fact, in order), fabricated_claims (list of strings, "
    "possibly empty), and rationale (one sentence). No other text."
)

_PP_SYSTEM = (
    "You are comparing two game NPC dialogue replies (A and B) to the same "
    "player question, produced by the same character. Score each reply 1-5 "
    "on four dimensions: naturalness (reads like in-character spoken "
    "dialogue, not exposition), character_consistency (voice and knowledge "
    "fit one coherent character), memory_grounding (specifics feel drawn "
    "from lived memory rather than generic filler), and brevity (says what "
    "it needs and stops). Then state which reply is better overall. Judge "
    "the writing, not factual correctness. Return ONLY a JSON object with "
    "keys: a (object with the four dimension keys, integers 1-5), b (same "
    'shape), preference ("a", "b", or "tie"), and rationale (one '
    "sentence). No other text."
)

RUBRICS: dict[str, Rubric] = {
    "selective_forgetting": Rubric(
        category="selective_forgetting",
        rubric_version="sf-v1",
        system_prompt=_SF_SYSTEM,
        user_template=(
            "Player question: {question}\n\nNPC reply: {reply}\n\n"
            "Reference (current truth in the NPC's memories): {reference}\n\n"
            "Superseded (must NOT be asserted as current): {superseded}"
        ),
    ),
    "abstention": Rubric(
        category="abstention",
        rubric_version="abst-v1",
        system_prompt=_ABST_SYSTEM,
        user_template=(
            "Player question: {question}\n\nNPC reply: {reply}\n\n"
            "Reference (true state in the NPC's memories): {reference}\n\n"
            "Expected behavior: {expected_behavior}"
        ),
    ),
    "reconstruction_faithfulness": Rubric(
        category="reconstruction_faithfulness",
        rubric_version="rf-v1",
        system_prompt=_RF_SYSTEM,
        user_template=("Current telling: {telling}\n\nGist facts:\n{facts}"),
    ),
    "prose_pairwise": Rubric(
        category="prose_pairwise",
        rubric_version="pp-v1",
        system_prompt=_PP_SYSTEM,
        user_template=(
            "Player question: {question}\n\nReply A: {reply_a}\n\nReply B: {reply_b}"
        ),
    ),
}


# ---------------------------------------------------------------------------
# Verdict models
# ---------------------------------------------------------------------------


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BinaryVerdict(_StrictModel):
    """selective_forgetting and abstention share the pass/fail shape."""

    verdict: str = Field(pattern="^(pass|fail)$")
    rationale: str = ""


class FaithfulnessVerdict(_StrictModel):
    gist_supported: list[bool]
    fabricated_claims: list[str] = Field(default_factory=list)
    rationale: str = ""


class ProseScores(_StrictModel):
    naturalness: int = Field(ge=1, le=5)
    character_consistency: int = Field(ge=1, le=5)
    memory_grounding: int = Field(ge=1, le=5)
    brevity: int = Field(ge=1, le=5)


class PairwiseVerdict(_StrictModel):
    a: ProseScores
    b: ProseScores
    preference: str = Field(pattern="^(a|b|tie)$")
    rationale: str = ""


PROSE_DIMENSIONS = (
    "naturalness",
    "character_consistency",
    "memory_grounding",
    "brevity",
)


def validate_verdict(category: str, payload: dict, *, n_facts: int = 0) -> BaseModel:
    """Validate a judge payload against its category's verdict model.

    Raises pydantic ValidationError (or ValueError for the faithfulness
    length check / an unknown category) — the runner records judge_failed on
    that item and continues; a bad verdict never kills a run.
    """
    if category in ("selective_forgetting", "abstention"):
        return BinaryVerdict.model_validate(payload)
    if category == "reconstruction_faithfulness":
        verdict = FaithfulnessVerdict.model_validate(payload)
        if len(verdict.gist_supported) != n_facts:
            raise ValueError(
                f"gist_supported has {len(verdict.gist_supported)} entries, "
                f"expected {n_facts} (one per numbered fact)"
            )
        return verdict
    if category == "prose_pairwise":
        return PairwiseVerdict.model_validate(payload)
    raise ValueError(f"unknown judge category: {category!r}")


def combine_pairwise(first: PairwiseVerdict, second_swapped: PairwiseVerdict) -> dict:
    """Combine the two position-swapped pairwise calls (spec: disagreement
    means tie).

    `first` judged (A, B) in true order; `second_swapped` judged (B, A), so
    its "a" scores belong to the true B and its preference is mirrored. The
    final preference stands only when both positions agree after un-swapping;
    a tie from either call, or a flip, is a tie. Per-arm per-dimension scores
    average the two calls (each true arm was judged once in each position).
    """
    mirror = {"a": "b", "b": "a", "tie": "tie"}
    second_pref = mirror[second_swapped.preference]
    agreed = first.preference == second_pref
    preference = first.preference if agreed else "tie"
    a_scores = {
        dim: (getattr(first.a, dim) + getattr(second_swapped.b, dim)) / 2.0
        for dim in PROSE_DIMENSIONS
    }
    b_scores = {
        dim: (getattr(first.b, dim) + getattr(second_swapped.a, dim)) / 2.0
        for dim in PROSE_DIMENSIONS
    }
    return {
        "preference": preference,
        "positions_agreed": agreed,
        "a": a_scores,
        "b": b_scores,
    }


# ---------------------------------------------------------------------------
# Agreement arithmetic (fork 5: quotability bar = Cohen's kappa >= 0.6 per
# category, shipped as the runner's --kappa-bar CLI default). Hand-rolled —
# no sklearn dependency; honest-None denominators.
# ---------------------------------------------------------------------------


def raw_agreement(a: Sequence[str], b: Sequence[str]) -> float | None:
    """Fraction of positions where the labels match; None on empty input."""
    if len(a) != len(b):
        raise ValueError(f"label sequences differ in length: {len(a)} vs {len(b)}")
    if not a:
        return None
    return sum(1 for x, y in zip(a, b) if x == y) / len(a)


def cohen_kappa(a: Sequence[str], b: Sequence[str]) -> float | None:
    """Cohen's kappa between two label sequences.

    None on an empty input OR degenerate marginals (chance agreement pe == 1,
    i.e. both raters used a single identical class — kappa is undefined
    there, and an undefined kappa honestly fails the quotability bar; the fix
    is class balance in the gold set, not a fabricated number).
    """
    po = raw_agreement(a, b)
    if po is None:
        return None
    n = len(a)
    classes = set(a) | set(b)
    counts_a = {c: sum(1 for x in a if x == c) for c in classes}
    counts_b = {c: sum(1 for x in b if x == c) for c in classes}
    pe = sum((counts_a[c] / n) * (counts_b[c] / n) for c in classes)
    if 1.0 - pe == 0.0:
        return None
    return (po - pe) / (1.0 - pe)


# ---------------------------------------------------------------------------
# Pareto (the compare table: accuracy max, p50/p95/USD-per-100-turns min)
# ---------------------------------------------------------------------------

_PARETO_KEYS = ("accuracy", "p50", "p95", "usd_per_100_turns")
_MAXIMIZE = frozenset({"accuracy"})


def _dominates(r1: dict, r2: dict) -> bool:
    """r1 dominates r2: at least as good on all four keys, strictly better on
    one. Any None in either row makes the pair incomparable (honest
    incomparability — an unpriced arm is never 'beaten' on cost)."""
    strict = False
    for key in _PARETO_KEYS:
        v1, v2 = r1.get(key), r2.get(key)
        if v1 is None or v2 is None:
            return False
        better = v1 > v2 if key in _MAXIMIZE else v1 < v2
        worse = v1 < v2 if key in _MAXIMIZE else v1 > v2
        if worse:
            return False
        if better:
            strict = True
    return strict


def pareto_non_dominated(rows: list[dict]) -> list[bool]:
    """Per-row flag: True when no other row dominates it."""
    return [
        not any(_dominates(other, row) for j, other in enumerate(rows) if j != i)
        for i, row in enumerate(rows)
    ]


# ---------------------------------------------------------------------------
# Gold rows (fork 12: ~20-30 items/category, emitted from the stage-3 real
# smoke; `label` fills blind — verdicts never appear in gold rows. Since the
# 2026-08-12 workaround ruling the labeler is a blind single-pass reference
# model; any row Jack relabels wins.)
# ---------------------------------------------------------------------------

GOLD_LABELS: dict[str, frozenset[str]] = {
    "selective_forgetting": frozenset({"pass", "fail"}),
    "abstention": frozenset({"pass", "fail"}),
    "reconstruction_faithfulness": frozenset({"supported", "unsupported"}),
    "prose_pairwise": frozenset({"a", "b", "tie"}),
}


class GoldItem(_StrictModel):
    """One gold-candidate row: everything a blind labeler needs, inline.

    Display fields vary by category (sf/abstention: question/reply/reference/
    superseded/expected_behavior; faithfulness: fact/telling; pairwise:
    question/reply_a/reply_b) — unused ones stay None and are omitted from
    the emitted line. `label` is null until hand-filled.
    """

    item_id: str = Field(min_length=1)
    category: str
    rubric_version: str = Field(min_length=1)
    label: str | None = None
    question: str | None = None
    reply: str | None = None
    reference: str | None = None
    superseded: str | None = None
    expected_behavior: str | None = None
    fact: str | None = None
    telling: str | None = None
    reply_a: str | None = None
    reply_b: str | None = None

    @model_validator(mode="after")
    def _label_vocab(self) -> GoldItem:
        allowed = GOLD_LABELS.get(self.category)
        if allowed is None:
            raise ValueError(f"unknown gold category: {self.category!r}")
        if self.label is not None and self.label not in allowed:
            raise ValueError(
                f"label {self.label!r} not in {sorted(allowed)} for "
                f"category {self.category}"
            )
        return self


def gold_line(item: GoldItem) -> str:
    """Serialize one gold row: None display fields dropped, `label` always
    present (it is the field the labeler fills — a missing key would hide
    the ask)."""
    payload = item.model_dump(exclude_none=True)
    payload["label"] = item.label
    return json.dumps(payload, ensure_ascii=False)


def load_gold(path: Path) -> list[GoldItem]:
    """Load a gold JSONL file with path:line failure context (the
    load_scenarios convention)."""
    items: list[GoldItem] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: not valid JSON — {exc}") from exc
            try:
                items.append(GoldItem.model_validate(payload))
            except ValidationError as exc:
                raise ValueError(f"{path}:{number}: {exc}") from exc
    if not items:
        raise ValueError(f"{path}: no gold rows found")
    return items
