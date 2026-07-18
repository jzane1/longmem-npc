"""providers.py — model provider interfaces: real implementations + deterministic fakes.

Two write-path roles (write-path.md §Model provider interfaces) plus the
escalation call ruled into v1 (2026-07-13), plus the dialogue role (the
CLI-harness build, 2026-07-15), plus the reconstruction role (the
reconstruction build, 2026-07-17):
  - the single Haiku write call (render + importance + typology-when-absent),
  - the LLM-escalation gist call (hard cases, biased loose),
  - the embedding call (text-embedding-3-small @ 1536, locked),
  - the single Sonnet-class dialogue call (prose + action directive +
    reputation delta in one structured output; cli-harness.md),
  - the batched Haiku-class reconstruction call (all cache misses of one
    retrieval in one structured call; reconstruction.md).

Every fake is deterministic: same input -> byte-identical output, offline and
keyless, so the structural suite never asserts on prose and CI needs no keys.
The fake embedding is LOCALITY-SENSITIVE (ruled 2026-07-17): similar texts
get similar vectors, so fake-mode retrieval relevance and reconstruction
drift distances are meaningful, not hash noise.
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
import math
import time
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


@dataclass(frozen=True)
class DialogueCallResult:
    """Parsed structured output of the single dialogue call.

    Tolerant parse (cli-harness.md degradation ladder): prose is required — a
    response with no parseable prose raises MalformedOutputError; a malformed
    directive or delta degrades field-wise (None + the reason captured) and
    the call still counts as succeeded. Vocabulary validation of a well-formed
    directive happens at the seam, not here.
    """

    prose: str
    directive_type: str | None
    directive_params: dict
    directive_error: str | None  # shape-level parse issue; the seam drops it
    reputation_delta: float | None  # None = missing/non-numeric; seam zeroes it
    delta_error: str | None
    input_tokens: int
    output_tokens: int
    first_token_ms: float  # 0.0 on the fake; measured on the streaming real call


@dataclass(frozen=True)
class ReconstructionItem:
    """One cache-missed memory prepared for the batched retelling call
    (reconstruction.md call contract): the fixed gist, the band-thinned
    original detail, and the current live telling. memory_id is the UUID
    string — the JSON key of the batched output contract."""

    memory_id: str
    gist: str
    thinned_detail: str
    current_telling: str


@dataclass(frozen=True)
class ReconstructionCallResult:
    """Parsed batched output: memory_id -> retelling. Per-item salvage
    (reconstruction.md ladder): an entry that is missing, empty, or not a
    string simply has no key here, and that item alone degrades at the seam;
    the call still counts as succeeded and its spend is accounted."""

    retellings: dict[str, str]
    input_tokens: int
    output_tokens: int


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


class DialogueProvider(Protocol):
    """`system_prompt` is fully assembled at the seam (app\\dialogue.py owns
    the block shape); `vocabulary` rides separately so the deterministic fake
    can draw its fixed directive from it."""

    def generate(
        self, *, system_prompt: str, utterance: str, vocabulary: list[str]
    ) -> DialogueCallResult: ...


class ReconstructionProvider(Protocol):
    """`system_prompt` and `user_content` are fully assembled at the seam
    (app\\reconstruction.py's pure assembly owns the block shape, the dialogue
    precedent); `items` rides separately so the deterministic fake can derive
    stable retellings from the structured inputs."""

    def reconstruct(
        self,
        *,
        system_prompt: str,
        user_content: str,
        items: list[ReconstructionItem],
    ) -> ReconstructionCallResult: ...


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
    """Locality-sensitive deterministic pseudo-embedding (ruled 2026-07-17,
    superseding the original shake_256 hash vectors): lowercased character
    trigrams hashed into the 1536 buckets, counted, L2-normalized. Similar
    texts get similar vectors, so fake-mode retrieval relevance and the
    reconstruction drift check are meaningful — the hash fake made any two
    texts nearly orthogonal, which would have refused every fake-mode
    write-back at any sane drift threshold."""

    def embed(self, texts: list[str]) -> EmbedResult:
        vectors: list[list[float]] = []
        tokens = 0
        for text in texts:
            counts = [0.0] * EMBEDDING_DIM
            lowered = text.lower()
            grams = (
                [lowered[i : i + 3] for i in range(len(lowered) - 2)]
                if len(lowered) >= 3
                else [lowered]
            )
            for gram in grams:
                digest = hashlib.sha256(gram.encode()).digest()
                counts[int.from_bytes(digest[:4], "big") % EMBEDDING_DIM] += 1.0
            norm = math.sqrt(sum(c * c for c in counts)) or 1.0
            vectors.append([c / norm for c in counts])
            tokens += len(text.split())
        return EmbedResult(vectors=vectors, tokens=tokens)


class FakeDialogueProvider:
    """Deterministic dialogue: stable prose echo, the vocabulary's first
    directive, hash-derived delta in [-1, 1) — byte-identical structured
    output for identical turns (cli-harness.md done-when)."""

    def generate(
        self, *, system_prompt: str, utterance: str, vocabulary: list[str]
    ) -> DialogueCallResult:
        prose = f"[fake dialogue] {utterance}"
        delta = round(_stable_unit_float(utterance, "reputation") * 2 - 1, 4)
        return DialogueCallResult(
            prose=prose,
            directive_type=vocabulary[0] if vocabulary else None,
            directive_params={},
            directive_error=None,
            reputation_delta=delta,
            delta_error=None,
            input_tokens=len(system_prompt.split()) + len(utterance.split()),
            output_tokens=len(prose.split()),
            first_token_ms=0.0,
        )


class FakeReconstructionProvider:
    """Deterministic retelling: the current telling plus a short marker hashed
    from every input (identity document via the system prompt, gist, thinned
    detail, telling) — so an identity bump or a band crossing changes the
    output, byte-identical inputs reproduce it, and the echo shape keeps the
    candidate NEAR the anchor under the trigram fake embedding (the happy
    path passes the default drift budget; compounding markers slowly spend
    it, which is the drift dynamic in miniature)."""

    def reconstruct(
        self,
        *,
        system_prompt: str,
        user_content: str,
        items: list[ReconstructionItem],
    ) -> ReconstructionCallResult:
        retellings: dict[str, str] = {}
        input_tokens = len(system_prompt.split()) + len(user_content.split())
        output_tokens = 0
        for item in items:
            marker = hashlib.sha256(
                f"{system_prompt}|{item.gist}|{item.thinned_detail}"
                f"|{item.current_telling}".encode()
            ).hexdigest()[:8]
            text = f"{item.current_telling} [retold {marker}]"
            retellings[item.memory_id] = text
            output_tokens += len(text.split())
        return ReconstructionCallResult(
            retellings=retellings,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


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


class FailingDialogueProvider:
    """Dialogue-call failure: never-blank — the turn returns the fallback line."""

    def generate(self, **_kwargs) -> DialogueCallResult:
        raise ProviderCallError("injected dialogue-call failure")


class MalformedDialogueProvider:
    """Call 'succeeds' but nothing parses (no prose): fallback line, spend accounted."""

    def generate(self, **_kwargs) -> DialogueCallResult:
        raise MalformedOutputError(
            "injected malformed dialogue output", input_tokens=7, output_tokens=3
        )


class FailingReconstructionProvider:
    """Reconstruction-call failure: fail-quiet — the affected items serve
    their live heads with honest read_mode; nothing is written."""

    def reconstruct(self, **_kwargs) -> ReconstructionCallResult:
        raise ProviderCallError("injected reconstruction-call failure")


class MalformedReconstructionProvider:
    """Call 'succeeds' but the batched output is unparseable: every item
    degrades, token spend accounted."""

    def reconstruct(self, **_kwargs) -> ReconstructionCallResult:
        raise MalformedOutputError(
            "injected malformed reconstruction output", input_tokens=7, output_tokens=3
        )


class DriftingReconstructionProvider:
    """Emits a retelling with no trigram overlap with any English fixture —
    cosine distance from the anchor ~1.0 under the fake embedding, so the
    drift budget must refuse the write-back at the default threshold."""

    def reconstruct(
        self,
        *,
        system_prompt: str,
        user_content: str,
        items: list[ReconstructionItem],
    ) -> ReconstructionCallResult:
        text = "xyzzq plughz " * 12
        return ReconstructionCallResult(
            retellings={item.memory_id: text.strip() for item in items},
            input_tokens=len(system_prompt.split()) + len(user_content.split()),
            output_tokens=len(text.split()) * len(items),
        )


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


class RealDialogueProvider:
    """Anthropic Sonnet-class single dialogue call (cli-harness.md). Streams so
    first-token latency is measurable; usage comes from the final message.

    Structured-output contract (build ruling 2026-07-15, JSON-in-text per the
    write/escalation precedent): ONLY a JSON object
    {"prose": str, "directive": {"type": str, "params": object} | null,
     "reputation_delta": float}. The instructions telling the model this live
    in the seam-assembled system prompt; this class enforces the parse side.
    """

    def __init__(self, settings: Settings):
        import anthropic

        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.model_dialogue

    def generate(
        self, *, system_prompt: str, utterance: str, vocabulary: list[str]
    ) -> DialogueCallResult:
        t0 = time.perf_counter()
        first_token_ms = 0.0
        chunks: list[str] = []
        try:
            with self._client.messages.stream(
                model=self._model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": utterance}],
            ) as stream:
                for text in stream.text_stream:
                    if not chunks:
                        first_token_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                    chunks.append(text)
                final = stream.get_final_message()
        except Exception as exc:
            raise ProviderCallError(f"dialogue call failed: {exc}") from exc
        input_tokens = final.usage.input_tokens
        output_tokens = final.usage.output_tokens
        try:
            payload = json.loads("".join(chunks))
            prose = payload["prose"]
            if not isinstance(prose, str) or not prose:
                raise ValueError("prose missing, empty, or not a string")
        except (
            KeyError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ) as exc:
            raise MalformedOutputError(
                f"dialogue output unparseable: {exc}",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            ) from exc

        # Field-wise salvage below the required prose (degradation ladder).
        directive_type: str | None = None
        directive_params: dict = {}
        directive_error: str | None = None
        directive = payload.get("directive")
        if directive is not None:
            params = (
                directive.get("params", {}) if isinstance(directive, dict) else None
            )
            if (
                isinstance(directive, dict)
                and isinstance(directive.get("type"), str)
                and isinstance(params, dict)
            ):
                directive_type = directive["type"]
                directive_params = params
            else:
                directive_error = f"malformed directive shape: {directive!r}"

        delta: float | None = None
        delta_error: str | None = None
        raw_delta = payload.get("reputation_delta")
        if isinstance(raw_delta, (int, float)) and not isinstance(raw_delta, bool):
            delta = float(raw_delta)
        else:
            delta_error = f"reputation_delta missing or non-numeric: {raw_delta!r}"

        return DialogueCallResult(
            prose=prose,
            directive_type=directive_type,
            directive_params=directive_params,
            directive_error=directive_error,
            reputation_delta=delta,
            delta_error=delta_error,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            first_token_ms=first_token_ms,
        )


class RealReconstructionProvider:
    """Anthropic Haiku-class batched retelling call (reconstruction.md).

    Output contract (build ruling 2026-07-17, JSON-in-text per the
    write/escalation/dialogue precedent): ONLY a JSON object mapping each
    memory_id to its retelling string. The instructions live in the
    seam-assembled system prompt; this class enforces the parse side with
    per-item salvage (a non-string entry drops; the object-level shape must
    parse). max_tokens scales with the batch (1024 per item, capped at 8192 —
    a fixed 1024 would truncate large batches)."""

    def __init__(self, settings: Settings):
        import anthropic

        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.model_reconstruction

    def reconstruct(
        self,
        *,
        system_prompt: str,
        user_content: str,
        items: list[ReconstructionItem],
    ) -> ReconstructionCallResult:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=min(1024 * max(len(items), 1), 8192),
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
        except Exception as exc:
            raise ProviderCallError(f"reconstruction call failed: {exc}") from exc
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        try:
            payload = json.loads(response.content[0].text)
            if not isinstance(payload, dict):
                raise ValueError("batched output is not a JSON object")
        except (ValueError, TypeError, json.JSONDecodeError, IndexError) as exc:
            raise MalformedOutputError(
                f"reconstruction output unparseable: {exc}",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            ) from exc
        retellings = {
            str(key): value
            for key, value in payload.items()
            if isinstance(value, str) and value
        }
        return ReconstructionCallResult(
            retellings=retellings,
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
    # `dialogue` and `reconstruction` default to their fakes so pre-existing
    # constructions (the earlier structural walkers) stand unchanged;
    # build_providers always sets them explicitly.
    write: WriteProvider
    escalation: EscalationProvider
    embedding: EmbeddingProvider
    dialogue: DialogueProvider = field(default_factory=FakeDialogueProvider)
    reconstruction: ReconstructionProvider = field(
        default_factory=FakeReconstructionProvider
    )


def build_providers(settings: Settings) -> Providers:
    """Provider selection by config; the services are identical under either."""
    if settings.provider_mode == "real":
        return Providers(
            write=RealWriteProvider(settings),
            escalation=RealEscalationProvider(settings),
            embedding=RealEmbeddingProvider(settings),
            dialogue=RealDialogueProvider(settings),
            reconstruction=RealReconstructionProvider(settings),
        )
    return Providers(
        write=FakeWriteProvider(),
        escalation=FakeEscalationProvider(),
        embedding=FakeEmbeddingProvider(),
        dialogue=FakeDialogueProvider(),
        reconstruction=FakeReconstructionProvider(),
    )
