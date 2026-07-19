"""gate.py — THE mid-dialogue gate decision (mid-dialogue-gate.md, built
2026-07-19; scope forks ruled at spec, remaining shapes at build).

Pure decision module, the decay.py precedent: no IO, no model calls, no
state — retrieval owns the fetches and the one utterance embed (which
doubles as the fire probe; one embed per turn, never two). The gate is
non-LLM by stack constant: no gate model, no gate env var, no pricing row.

Two identity structures, never conflated (architecture §4.3):
  - the ENTITY TRIPWIRE matches the utterance against the agent's live
    identity_components (canonical + aliases) — mechanical word-boundary
    string work (nlp.find_term_spans), no spaCy on the read path;
  - the COVERAGE basis is the loaded set's live fact-head `entities`
    (migration 003) — a mentioned component already covered by what the
    scene holds does not fire.

Signals are named module constants (the write path's TRIGGER_* precedent);
every gate event logs which signal fired (instrumentation-only by fork 4 —
these feed the reserved novelty kill-switch decision via run artifacts).

Degradation ladder (audit ruling #3, implementation-shaped in the spec):
utterance embedding down -> entity_only (tripwire alone; lexical fetch off
the partial GIN); no live components or no entities coverage basis ->
novelty_only (the tripwire cannot evaluate — it never fires on every
mention); both out -> closed (serve the loaded set, fail-quiet). The
fruitless-retrieval damper (ruled 2026-07-19) suppresses the NOVELTY signal
only, for the scene remainder, after the ruled max of consecutive fruitless
fetches; the tripwire stays live; scene boundaries reset (caller-held
streak, the reputation_snapshot trust class).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
from uuid import UUID

from app.db import GateRow
from app.nlp import find_term_spans
from app.reconstruction import cosine_distance

GATE_SIGNAL_NOVELTY = "novelty"
GATE_SIGNAL_ENTITY = "entity_tripwire"

GATE_RUNG_ENTITY_ONLY = "entity_only"
GATE_RUNG_NOVELTY_ONLY = "novelty_only"
GATE_RUNG_CLOSED = "closed"


@dataclass(frozen=True)
class GateDecision:
    """The gate's per-turn verdict: fire (fetch) or stay closed, which
    signals fired, and the degradation rung taken (None = full evaluation)."""

    fired: bool
    signals: list[str] = field(default_factory=list)
    rung: str | None = None


def detect_mentions(utterance: str, components: list[dict]) -> list[dict]:
    """Live identity components mentioned in the utterance — canonical or
    any alias, case-insensitive whole-word (the promoted tripwire atom).
    Returns the component dicts themselves so coverage can weigh every term."""
    mentioned: list[dict] = []
    for comp in components:
        terms = [comp["canonical"], *(comp.get("aliases") or [])]
        if any(find_term_spans(utterance, term) for term in terms):
            mentioned.append(comp)
    return mentioned


def coverage_basis(loaded: Iterable[GateRow]) -> set[str]:
    """The lowercase set of every entity carried by the loaded set's live
    fact heads — what the scene already holds, entity-wise."""
    basis: set[str] = set()
    for gate_row in loaded:
        for entity in gate_row.entities or []:
            basis.add(entity.lower())
    return basis


def uncovered_mentions(mentions: list[dict], basis: set[str]) -> list[dict]:
    """Mentioned components not covered by the loaded set: a component is
    covered iff ANY of its terms (canonical or alias, case-insensitive)
    appears in the coverage basis."""
    uncovered: list[dict] = []
    for comp in mentions:
        terms = [comp["canonical"], *(comp.get("aliases") or [])]
        if not any(term.lower() in basis for term in terms):
            uncovered.append(comp)
    return uncovered


def novelty_distances(
    query_vector: list[float], loaded: list[GateRow]
) -> tuple[dict[UUID, float], int]:
    """Cosine distance from the utterance embedding to each loaded row's
    non-NULL fact-head embedding, plus the count of NULL-embedding rows
    excluded from the basis (they stay in coverage and closed-gate serving;
    the exclusion is counted honestly in instrumentation)."""
    distances: dict[UUID, float] = {}
    null_count = 0
    for gate_row in loaded:
        if gate_row.embedding is None:
            null_count += 1
        else:
            distances[gate_row.row.memory_id] = cosine_distance(
                query_vector, gate_row.embedding
            )
    return distances, null_count


def decide(
    *,
    novelty_evaluable: bool,
    min_distance: float | None,
    threshold: float,
    tripwire_evaluable: bool,
    uncovered: list[dict],
    damper_active: bool,
) -> GateDecision:
    """Assemble the verdict from the evaluated signals.

    `novelty_evaluable` = the utterance embedding exists; with it, an empty
    novelty basis (min_distance None — empty loaded set or all-NULL
    embeddings) is TRIVIALLY novel ("far from all" of nothing).
    `tripwire_evaluable` = live components exist AND the coverage basis is
    non-empty (the ladder's novelty_only rung otherwise — the tripwire never
    fires on every mention for want of a basis). The damper suppresses the
    novelty signal only."""
    signals: list[str] = []
    if novelty_evaluable and not damper_active:
        if min_distance is None or min_distance >= threshold:
            signals.append(GATE_SIGNAL_NOVELTY)
    if tripwire_evaluable and uncovered:
        signals.append(GATE_SIGNAL_ENTITY)

    if novelty_evaluable and tripwire_evaluable:
        rung = None
    elif tripwire_evaluable:
        rung = GATE_RUNG_ENTITY_ONLY
    elif novelty_evaluable:
        rung = GATE_RUNG_NOVELTY_ONLY
    else:
        rung = GATE_RUNG_CLOSED

    return GateDecision(fired=bool(signals), signals=signals, rung=rung)
