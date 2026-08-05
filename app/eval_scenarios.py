"""eval_scenarios.py — the eval runner's scenario schema + JSONL loader.

Eval-harness stage 2 (`docs\\eval-harness.md`). A scenario is one agent plus an
ordered event list replayed literally through `SessionRunner` — the same verbs
the REPL exposes: observe / utterance / scene / correct / pin / as_of /
context. `memory_ref` is the 0-based ordinal into the scenario's observe
events, resolved at replay time via each `IngestResult.memory_id`; the loader
rejects a ref that is out of range or points at an observe that has not
happened yet by the time the referencing event runs.

Strict on purpose (`extra="forbid"` everywhere): a typo'd field in an authored
fixture fails at load with file+line context, never a silently dropped
assertion. Timestamps must be timezone-aware — a naive datetime would
detonate deep inside decay's age math mid-run instead of at load.

Expected-IDs checks are membership-only by ruling (2026-08-05): `present` /
`absent` memory refs scored against the raw served items — the IDs+scores
retrieval echo, which weight re-ranking never changes membership of (the A1
seam contract). Ordering assertions are deliberately absent.

A drift-validate corpus is the same schema's subset — observe (+ as_of) only —
loaded by the same loader (fork 10: one loader), with `assert_corpus_shape`
stating the restriction rather than silently ignoring extra events.

Pure module: no db, no spaCy, no provider imports.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExpectedIds(_StrictModel):
    """Membership assertions for one utterance, as observe ordinals."""

    present: list[int] = Field(default_factory=list)
    absent: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def _disjoint_and_unique(self) -> ExpectedIds:
        for label, refs in (("present", self.present), ("absent", self.absent)):
            if len(refs) != len(set(refs)):
                raise ValueError(f"duplicate memory_ref in expect.{label}")
        overlap = set(self.present) & set(self.absent)
        if overlap:
            raise ValueError(
                f"memory_ref(s) {sorted(overlap)} appear in both expect.present "
                "and expect.absent — contradictory assertion"
            )
        return self


class ObserveStep(_StrictModel):
    kind: Literal["observe"]
    text: str = Field(min_length=1)


class UtteranceStep(_StrictModel):
    kind: Literal["utterance"]
    text: str = Field(min_length=1)
    k: int | None = Field(default=None, ge=1)
    expect: ExpectedIds | None = None


class SceneStep(_StrictModel):
    kind: Literal["scene"]
    scene_type: str | None = None


class CorrectStep(_StrictModel):
    kind: Literal["correct"]
    memory_ref: int = Field(ge=0)
    content: str = Field(min_length=1)


class PinStep(_StrictModel):
    kind: Literal["pin"]
    memory_ref: int = Field(ge=0)
    pinned: bool = True


class AsOfStep(_StrictModel):
    """Time travel: sets the runner's `as_of` (None clears it)."""

    kind: Literal["as_of"]
    at: datetime | None

    @field_validator("at")
    @classmethod
    def _tz_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class ContextStep(_StrictModel):
    """Sets the runner's soft retrieval context (cleared by `scene`)."""

    kind: Literal["context"]
    location: str | None = None
    entities: list[str] | None = None
    event_time: datetime | None = None

    @field_validator("event_time")
    @classmethod
    def _tz_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


ScenarioEvent = Annotated[
    ObserveStep
    | UtteranceStep
    | SceneStep
    | CorrectStep
    | PinStep
    | AsOfStep
    | ContextStep,
    Field(discriminator="kind"),
]


class ScenarioAgent(_StrictModel):
    """The scenario's fixture agent — the `db.insert_agent` field set.

    `config` carries explicit fixture facts (decay classes and any knob
    overrides); fixtures never lean on service defaults for values an
    assertion depends on.
    """

    name: str = Field(min_length=1)
    seed_identity: str = Field(min_length=1)
    diagnosticity_goal: str = Field(min_length=1)
    rigidity: float = Field(default=1.0, ge=0.5, le=2.0)
    config: dict = Field(default_factory=dict)


class Scenario(_StrictModel):
    scenario_id: str = Field(min_length=1)
    title: str | None = None
    held_out: bool = False
    agent: ScenarioAgent
    events: list[ScenarioEvent] = Field(min_length=1)

    @property
    def observe_count(self) -> int:
        return sum(1 for event in self.events if isinstance(event, ObserveStep))

    @model_validator(mode="after")
    def _refs_resolve(self) -> Scenario:
        total = self.observe_count
        observes_seen = 0
        for index, event in enumerate(self.events):
            if isinstance(event, (CorrectStep, PinStep)):
                refs = [event.memory_ref]
            elif isinstance(event, UtteranceStep) and event.expect is not None:
                refs = [*event.expect.present, *event.expect.absent]
            else:
                refs = []
            for ref in refs:
                if ref >= total:
                    raise ValueError(
                        f"events[{index}] references observe ordinal {ref}, but "
                        f"the scenario has only {total} observe event(s)"
                    )
                if ref >= observes_seen:
                    raise ValueError(
                        f"events[{index}] references observe ordinal {ref} "
                        "before that observe occurs in the event list"
                    )
            if isinstance(event, ObserveStep):
                observes_seen += 1
        return self


def load_scenarios(path: Path) -> list[Scenario]:
    """Load one JSONL file: one scenario object per non-empty line.

    Every failure is re-raised with `path:line` context so an authoring
    mistake names the exact fixture line.
    """
    scenarios: list[Scenario] = []
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
                scenarios.append(Scenario.model_validate(payload))
            except ValidationError as exc:
                raise ValueError(f"{path}:{number}: {exc}") from exc
    if not scenarios:
        raise ValueError(f"{path}: no scenarios found")
    return scenarios


def load_scenario_files(paths: Sequence[Path]) -> list[Scenario]:
    """Concatenate scenario files, rejecting duplicate scenario_ids."""
    scenarios: list[Scenario] = []
    seen: dict[str, Path] = {}
    for path in paths:
        for scenario in load_scenarios(path):
            prior = seen.get(scenario.scenario_id)
            if prior is not None:
                raise ValueError(
                    f"duplicate scenario_id {scenario.scenario_id!r} in {path} "
                    f"(first seen in {prior})"
                )
            seen[scenario.scenario_id] = path
            scenarios.append(scenario)
    return scenarios


CORPUS_EVENT_KINDS = frozenset({"observe", "as_of"})


def assert_corpus_shape(scenario: Scenario) -> None:
    """A drift corpus is the scenario schema's subset: observe (+ as_of) only."""
    offending = sorted({event.kind for event in scenario.events} - CORPUS_EVENT_KINDS)
    if offending:
        raise ValueError(
            f"corpus scenario {scenario.scenario_id!r} carries non-corpus event "
            f"kind(s) {offending}; a drift corpus is observes (+ as_of) only"
        )


def check_expected(
    expect: ExpectedIds,
    served_ids: Sequence[UUID],
    observed_ids: Sequence[UUID],
) -> dict:
    """Score one utterance's membership assertions against the served items.

    `served_ids` is the raw retrieval echo (`DialogueTurnResult.items`);
    `observed_ids` is the scenario's observe-ordinal resolution table.
    Returns `{"passed", "missing", "unexpected"}` with memory IDs as strings.
    """
    served = set(served_ids)
    missing = [
        str(observed_ids[ref])
        for ref in expect.present
        if observed_ids[ref] not in served
    ]
    unexpected = [
        str(observed_ids[ref]) for ref in expect.absent if observed_ids[ref] in served
    ]
    return {
        "passed": not missing and not unexpected,
        "missing": missing,
        "unexpected": unexpected,
    }
