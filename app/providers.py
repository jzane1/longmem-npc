"""providers.py — model provider interfaces: real implementations + deterministic fakes.

Two write-path roles (write-path.md §Model provider interfaces) plus the
escalation call ruled into v1 (2026-07-13):
  - the single Haiku write call (render + importance + typology-when-absent),
  - the LLM-escalation gist call (hard cases, biased loose),
  - the embedding call (text-embedding-3-small @ 1536, locked).

Every fake is deterministic: same input -> byte-identical output, offline and
keyless, so the structural suite never asserts on prose and CI needs no keys.
Failure-injection fakes live here too — the degradation ladder is tested per
model call (architecture §2).

Error contract (the seam owns degradation policy, providers only signal):
  - ProviderCallError    — the call itself failed (network, API error).
  - MalformedOutputError — the call succeeded but structured output did not
    parse; carries token counts because the spend happened.
"""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass, field
from typing import Protocol

from app.config import EMBEDDING_DIM, EMBEDDING_MODEL, Settings


class ProviderCallError(RuntimeError):
    """The model call failed outright."""


class MalformedOutputError(RuntimeError):
    """The call returned, but its structured output did not parse."""

    def __init__(self, message: str, input_tokens: int = 0, output_tokens: int = 0):
        super().__init__(message)
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


# ---------------------------------------------------------------------------
# Result shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WriteCallResult:
    """Structured output of the single Haiku write call."""

    rendered_content: str
    importance_raw: float
    typology: str | None  # None when the client declared (call not asked)
    typology_confidence: float | None
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class GistSpanCandidate:
    """A half-open [start_char, end_char) span into observation_text."""

    start_char: int
    end_char: int
    matched_component_id: str | None = None  # UUID str of an existing component
    matched_category: str | None = None


@dataclass(frozen=True)
class NewComponent:
    """A novel entity to grow identity_components with."""

    canonical: str
    aliases: list[str] = field(default_factory=list)
    category: str | None = None


@dataclass(frozen=True)
class EscalationResult:
    """Structured output of the escalation gist call."""

    spans: list[GistSpanCandidate]
    new_components: list[NewComponent]
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class EmbedResult:
    vectors: list[list[float]]
    tokens: int


# ---------------------------------------------------------------------------
# Interfaces
# ---------------------------------------------------------------------------


class WriteProvider(Protocol):
    def render_and_score(
        self,
        *,
        observation_text: str,
        diagnosticity_goal: str,
        declared_typology: str | None,
    ) -> WriteCallResult: ...


class EscalationProvider(Protocol):
    def extract_gist(
        self,
        *,
        observation_text: str,
        known_components: list[dict],
        candidate_spans: list[GistSpanCandidate],
        candidate_components: list[NewComponent],
        triggers: list[str],
    ) -> EscalationResult: ...


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> EmbedResult: ...


# ---------------------------------------------------------------------------
# Deterministic fakes
# ---------------------------------------------------------------------------


def _stable_unit_float(text: str, salt: str) -> float:
    """Deterministic float in [0, 1) from text — stable across runs/platforms."""
    digest = hashlib.sha256(f"{salt}:{text}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


class FakeWriteProvider:
    """Echo render + hash-derived scores. Deterministic, keyless."""

    TYPOLOGIES = ("observed", "told", "inferred", "reflected")

    def render_and_score(
        self,
        *,
        observation_text: str,
        diagnosticity_goal: str,
        declared_typology: str | None,
    ) -> WriteCallResult:
        importance = round(_stable_unit_float(observation_text, "importance"), 4)
        typology: str | None = None
        confidence: float | None = None
        if declared_typology is None:
            index = int(_stable_unit_float(observation_text, "typology") * 4)
            typology = self.TYPOLOGIES[index]
            confidence = round(
                0.5 + _stable_unit_float(observation_text, "conf") / 2, 4
            )
        words = len(observation_text.split())
        return WriteCallResult(
            rendered_content=f"[fake render] {observation_text}",
            importance_raw=importance,
            typology=typology,
            typology_confidence=confidence,
            input_tokens=words,
            output_tokens=words,
        )


class FakeEscalationProvider:
    """Echoes the NLP pass's candidates unchanged — deterministic by construction."""

    def extract_gist(
        self,
        *,
        observation_text: str,
        known_components: list[dict],
        candidate_spans: list[GistSpanCandidate],
        candidate_components: list[NewComponent],
        triggers: list[str],
    ) -> EscalationResult:
        words = len(observation_text.split())
        return EscalationResult(
            spans=list(candidate_spans),
            new_components=list(candidate_components),
            input_tokens=words,
            output_tokens=len(candidate_spans) + len(candidate_components),
        )


class FakeEmbeddingProvider:
    """Stable pseudo-embedding: shake_256(text) -> 1536 floats in [-1, 1]."""

    def embed(self, texts: list[str]) -> EmbedResult:
        vectors: list[list[float]] = []
        tokens = 0
        for text in texts:
            raw = hashlib.shake_256(text.encode()).digest(EMBEDDING_DIM * 4)
            ints = struct.unpack(f">{EMBEDDING_DIM}I", raw)
            vectors.append([(i / 2**31) - 1.0 for i in ints])
            tokens += len(text.split())
        return EmbedResult(vectors=vectors, tokens=tokens)


# --- failure-injection fakes (degradation ladder tests) --------------------


class FailingWriteProvider:
    """Importance-scoring failure: the write must still land (scoring_failed)."""

    def render_and_score(self, **_kwargs) -> WriteCallResult:
        raise ProviderCallError("injected write-call failure")


class MalformedWriteProvider:
    """Call 'succeeds' but structured output is unparseable: neutral/default."""

    def render_and_score(self, **_kwargs) -> WriteCallResult:
        raise MalformedOutputError(
            "injected malformed output", input_tokens=7, output_tokens=3
        )


class FailingEmbeddingProvider:
    """Embedding failure: write lands with NULL embedding (ruled 2026-07-13)."""

    def embed(self, texts: list[str]) -> EmbedResult:
        raise ProviderCallError("injected embedding failure")


class FailingEscalationProvider:
    """Escalation failure: retry once, then HARD-STOP the write (build-phase stance)."""

    def __init__(self) -> None:
        self.calls = 0

    def extract_gist(self, **_kwargs) -> EscalationResult:
        self.calls += 1
        raise ProviderCallError(f"injected escalation failure (call {self.calls})")


# ---------------------------------------------------------------------------
# Real implementations (constructed only in real mode; SDKs imported lazily)
# ---------------------------------------------------------------------------

_WRITE_SYSTEM = (
    "You are the write-time memory scorer for a game NPC. Given an observation, "
    "return ONLY a JSON object with keys: rendered_content (a first-person prose "
    "telling of the observation), importance_raw (float 0..1, anchored to the "
    "NPC's diagnosticity goal){typology_clause}. No other text."
)
_TYPOLOGY_CLAUSE = (
    ", typology (one of observed|told|inferred|reflected), "
    "typology_confidence (float 0..1)"
)

_ESCALATION_SYSTEM = (
    "You are the gist-extraction escalation pass for a game NPC's memory. Gist "
    "spans are EXACT substrings of the observation tied to the NPC's identity "
    "components. Return ONLY a JSON object with keys: spans (list of objects "
    "{text: exact substring, component: canonical name of a known component or "
    "null, category: category label or null}) and new_components (list of "
    "objects {canonical, aliases, category} for entities central to the "
    "observation but absent from the known components). No other text."
)


class RealWriteProvider:
    """Anthropic Haiku-class call: render + importance (+ typology when absent)."""

    def __init__(self, settings: Settings):
        import anthropic

        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.model_write

    def render_and_score(
        self,
        *,
        observation_text: str,
        diagnosticity_goal: str,
        declared_typology: str | None,
    ) -> WriteCallResult:
        clause = _TYPOLOGY_CLAUSE if declared_typology is None else ""
        system = _WRITE_SYSTEM.format(typology_clause=clause)
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Diagnosticity goal: {diagnosticity_goal}\n\n"
                            f"Observation: {observation_text}"
                        ),
                    }
                ],
            )
        except Exception as exc:
            raise ProviderCallError(f"write call failed: {exc}") from exc
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        try:
            payload = json.loads(response.content[0].text)
            rendered = str(payload["rendered_content"])
            importance = float(payload["importance_raw"])
            typology = payload.get("typology") if declared_typology is None else None
            confidence = (
                payload.get("typology_confidence")
                if declared_typology is None
                else None
            )
        except (
            KeyError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
            IndexError,
        ) as exc:
            raise MalformedOutputError(
                f"write call output unparseable: {exc}",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            ) from exc
        return WriteCallResult(
            rendered_content=rendered,
            importance_raw=importance,
            typology=str(typology) if typology is not None else None,
            typology_confidence=float(confidence) if confidence is not None else None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


class RealEscalationProvider:
    """Anthropic Haiku-class gist escalation. Spans returned as exact substrings,
    mapped to half-open char offsets here; unlocatable substrings are dropped."""

    def __init__(self, settings: Settings):
        import anthropic

        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.model_escalation

    def extract_gist(
        self,
        *,
        observation_text: str,
        known_components: list[dict],
        candidate_spans: list[GistSpanCandidate],
        candidate_components: list[NewComponent],
        triggers: list[str],
    ) -> EscalationResult:
        known = [
            {
                "canonical": c["canonical"],
                "aliases": c.get("aliases") or [],
                "category": c.get("category"),
            }
            for c in known_components
        ]
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=_ESCALATION_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Known identity components: {json.dumps(known)}\n"
                            f"Escalation triggers: {triggers}\n\n"
                            f"Observation: {observation_text}"
                        ),
                    }
                ],
            )
        except Exception as exc:
            raise ProviderCallError(f"escalation call failed: {exc}") from exc
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        try:
            payload = json.loads(response.content[0].text)
            by_canonical = {c["canonical"]: c for c in known_components}
            spans: list[GistSpanCandidate] = []
            for item in payload["spans"]:
                text = str(item["text"])
                start = observation_text.find(text)
                if start < 0:
                    continue  # unlocatable substring: drop, offsets stay truthful
                component = by_canonical.get(item.get("component"))
                spans.append(
                    GistSpanCandidate(
                        start_char=start,
                        end_char=start + len(text),
                        matched_component_id=(
                            str(component["component_id"]) if component else None
                        ),
                        matched_category=item.get("category"),
                    )
                )
            new_components = [
                NewComponent(
                    canonical=str(item["canonical"]),
                    aliases=[str(a) for a in item.get("aliases") or []],
                    category=item.get("category"),
                )
                for item in payload["new_components"]
            ]
        except (
            KeyError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
            IndexError,
        ) as exc:
            raise MalformedOutputError(
                f"escalation output unparseable: {exc}",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            ) from exc
        return EscalationResult(
            spans=spans,
            new_components=new_components,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


class RealEmbeddingProvider:
    """OpenAI text-embedding-3-small @ 1536 (locked)."""

    def __init__(self, settings: Settings):
        import openai

        self._client = openai.OpenAI(api_key=settings.openai_api_key)

    def embed(self, texts: list[str]) -> EmbedResult:
        try:
            response = self._client.embeddings.create(
                model=EMBEDDING_MODEL, input=texts, dimensions=EMBEDDING_DIM
            )
        except Exception as exc:
            raise ProviderCallError(f"embedding call failed: {exc}") from exc
        vectors = [item.embedding for item in response.data]
        return EmbedResult(vectors=vectors, tokens=response.usage.total_tokens)


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Providers:
    write: WriteProvider
    escalation: EscalationProvider
    embedding: EmbeddingProvider


def build_providers(settings: Settings) -> Providers:
    """Provider selection by config; the ingest service is identical under either."""
    if settings.provider_mode == "real":
        return Providers(
            write=RealWriteProvider(settings),
            escalation=RealEscalationProvider(settings),
            embedding=RealEmbeddingProvider(settings),
        )
    return Providers(
        write=FakeWriteProvider(),
        escalation=FakeEscalationProvider(),
        embedding=FakeEmbeddingProvider(),
    )
