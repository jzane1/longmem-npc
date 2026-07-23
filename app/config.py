"""config.py — environment + integrator-knob loading for the write and read paths.

Secrets and connection strings live only in the gitignored repo-root .env
(same manual parse as db\\migrate.py — no dotenv dependency). Never print or
log values loaded from .env.

Model roles (architecture §3): every role has its own env var. The v1 write
call serves render + importance + typology in ONE Haiku call, so at startup
in real mode the three role vars must name the same model — divergence is a
loud config error, never a silent pick (ruled with the write-path plan,
2026-07-13). The dialogue role (LONGMEM_MODEL_DIALOGUE, cli-harness build
2026-07-15) is the Sonnet-class call; since the split-brain build (2026-07-21)
it streams PURE PROSE only. The reconstruction role
(LONGMEM_MODEL_RECONSTRUCTION, reconstruction build 2026-07-17) is the
Haiku-class batched retelling call (reconstruction.md). The behavior role
(LONGMEM_MODEL_BEHAVIOR, split-brain build 2026-07-21) is the concurrent
Haiku-class call that emits the action directive + reputation delta while the
prose streams (split-brain-streaming.md).

Service-level defaults below are integrator-overridable per agent via
`agents.config` keys of the same name (nothing integrator-configurable is
hardcoded). `agents.config` additionally carries:
  - "decay_classes": {label: tau_base_seconds, ...}  (migration-01 ruling)
  - "decay_class_default": the label applied when an event omits or supplies
    an unknown decay_class label.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"

# Locked constants — not knobs (decisions.md: embedding dimension 1536, locked;
# model text-embedding-3-small).
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# Env var names — one per model role (architecture §3).
ENV_MODEL_IMPORTANCE = "LONGMEM_MODEL_IMPORTANCE"
ENV_MODEL_RENDER = "LONGMEM_MODEL_RENDER"
ENV_MODEL_TYPOLOGY = "LONGMEM_MODEL_TYPOLOGY"
ENV_MODEL_ESCALATION = "LONGMEM_MODEL_ESCALATION"
ENV_MODEL_DIALOGUE = "LONGMEM_MODEL_DIALOGUE"
ENV_MODEL_RECONSTRUCTION = "LONGMEM_MODEL_RECONSTRUCTION"
# The split-brain BEHAVIOR call's role (split-brain-streaming.md, built
# 2026-07-21): the concurrent Haiku-class call that chooses the action
# directive and emits the reputation delta while the prose call streams.
# Its own env var (ruled: a new `behavior` role, not a reuse of `reputation`).
ENV_MODEL_BEHAVIOR = "LONGMEM_MODEL_BEHAVIOR"
ENV_PROVIDER_MODE = "LONGMEM_PROVIDER_MODE"

# Optional per-Mtok USD prices (CLI-harness build ruling, 2026-07-15): cost
# fields carry token counts unconditionally; USD appears only when these are
# set. No model pricing is ever hardcoded. Maps env var -> Settings.prices key.
PRICE_ENV_KEYS: dict[str, str] = {
    "LONGMEM_PRICE_DIALOGUE_IN": "dialogue_in",
    "LONGMEM_PRICE_DIALOGUE_OUT": "dialogue_out",
    "LONGMEM_PRICE_BEHAVIOR_IN": "behavior_in",
    "LONGMEM_PRICE_BEHAVIOR_OUT": "behavior_out",
    "LONGMEM_PRICE_WRITE_IN": "write_in",
    "LONGMEM_PRICE_WRITE_OUT": "write_out",
    "LONGMEM_PRICE_ESCALATION_IN": "escalation_in",
    "LONGMEM_PRICE_ESCALATION_OUT": "escalation_out",
    "LONGMEM_PRICE_RECONSTRUCTION_IN": "reconstruction_in",
    "LONGMEM_PRICE_RECONSTRUCTION_OUT": "reconstruction_out",
    "LONGMEM_PRICE_EMBEDDING": "embedding",
}

# Service-level defaults, each overridable per agent via the same key in
# agents.config (write-path plan rulings, 2026-07-13).
SERVICE_DEFAULTS: dict[str, float] = {
    # Neutral importance applied when the scoring model fails (scoring_failed).
    "importance_neutral": 0.5,
    # Escalation trigger (1): importance_raw >= this.
    "escalation_importance_threshold": 0.45,
    # Escalation trigger (2): identity/category hit co-occurring with
    # |valence| >= this.
    "escalation_affect_threshold": 0.5,
    # Escalation trigger (6), thin_gist (ruled 2026-07-23): fire when the base
    # NLP pass yields fewer gist spans than this floor — protects the gist
    # (reconstruction's fixed constraint) directly; 16/80 realistic observes
    # otherwise land with zero spans. 0.0 disables the trigger.
    "escalation_min_base_spans": 1.0,
    # Escalation trigger (5) threshold — RESERVED, not consulted in v1: neither
    # fastcoref's predict API nor en_core_web_lg's greedy NER exposes per-span
    # confidence, so every coref-derived span counts as low-confidence outright
    # (over-call only; see app\nlp.py). Becomes live when a confidence source exists.
    "nlp_confidence_threshold": 0.5,
    # Default per-typology confidence when the client declares a typology
    # without a confidence (architecture §5: a default table exists; single
    # scalar default until the table earns per-typology entries).
    "typology_confidence_default": 0.9,
    # --- read path (read-path.md; build rulings 2026-07-14) -----------------
    # Default top-k for dialogue-init retrieval.
    "retrieval_top_k": 8,
    # Vector over-fetch: fetch ceil(factor * k) candidates by distance, then
    # re-rank by the full score.
    "retrieval_overfetch_factor": 4.0,
    # k in tau_effective = tau_base * (1 + k * importance_raw) — shared by the
    # recency score component and, at reconstruction, the theta check
    # (one formula, one implementation: app\decay.py).
    "decay_k_importance": 1.0,
    # importance_norm = clamp(importance_raw, floor, 1.0): the floor keeps the
    # multiplicative score from zeroing a memory out of existence.
    "importance_norm_floor": 0.05,
    # tau_base when neither the stored decay-class label nor the agent's
    # default class resolves in agents.config — a read never fails on a
    # resolvable row.
    "tau_fallback_seconds": 604800.0,
    # --- dialogue turn (cli-harness.md; build rulings 2026-07-15) -----------
    # Reputation scale + apply defaults. The agents.reputation /
    # reputation_sensitivity columns carry no DEFAULT by migration-01 ruling;
    # these service defaults (per-agent overridable, like every key here)
    # supply the neutral point and clamp bounds the apply formula needs.
    "reputation_scale_min": -1.0,
    "reputation_scale_max": 1.0,
    "reputation_neutral": 0.0,
    "reputation_sensitivity_default": 1.0,
    # --- reconstruction (reconstruction.md; build rulings 2026-07-17) -------
    # Reconstruct when decayed detail strength (= decay.recency at the
    # scene-frozen basis) falls below theta. Pinned rows are exempt.
    "reconstruction_theta": 0.5,
    # Band quantum: band_index = floor((1 - strength) / quantum). The band
    # composes the cache key with identity_version AND sets the thinning
    # level (the band's midpoint strength), so same key => same input.
    "reconstruction_band_quantum": 0.25,
    # Drift budget: refuse a reconstruction write-back whose embedding's
    # cosine distance from the anchor exceeds this (ruled 2026-07-17).
    "drift_budget_threshold": 0.35,
    # --- mid-dialogue gate (mid-dialogue-gate.md; build rulings 2026-07-19) --
    # Non-LLM: no gate model role, no pricing entry. All floats (agent_knob
    # contract); integer-valued knobs are cast at the call site.
    # Novelty fires when the min cosine distance from the utterance embedding
    # to the loaded set's fact-head embeddings is >= this. Calibration split
    # honestly (measured at build): fake-provider echoes ~0.04, near-copies
    # ~0.08, ordinary distinct prose ~0.45-0.75 (fixture property — shared
    # English trigrams keep unrelated sentences under the naive ~1.0);
    # real-provider paraphrase ~0.05-0.25; 0.5 sits above the 0.35 drift
    # line's "left the neighborhood".
    "gate_novelty_threshold": 0.5,
    # New items appended per gate fetch (a full retrieval_top_k re-fetch
    # would swamp the loaded set).
    "gate_fetch_k": 3.0,
    # Damper (ruled 2026-07-19): after this many CONSECUTIVE fruitless
    # fetches (zero new IDs appended), the novelty signal is suppressed for
    # the scene remainder; the entity tripwire stays live; scene boundary
    # resets.
    "gate_damper_fruitless_max": 2.0,
    # Whole-gate switch: 0.0 => every request is a loader turn (v1 behavior).
    # The fixture-pin shape (the reconstruction_theta = 0 precedent) and the
    # integrator kill-switch scaffold — the reserved per-signal kill-switch
    # decision may later grow its own knobs (see decisions.md).
    "gate_enabled": 1.0,
    # --- encoding-context read term (read-path.md; ruled 2026-07-20) --------
    # The formerly-reserved DialogueInitRequest context fields become a soft
    # multiplicative nudge: score *= (1 + sum(w_i * match_i)) over the
    # components the REQUEST supplies (client-supplied fields, ruled — no LLM
    # query decomposition; the 2026-07-14 query-embedded-as-is ruling stands).
    # A request with no context fields skips the term entirely — scores stay
    # byte-identical to v1 (the loader-parity precedent). Never a hard filter:
    # a non-matching row loses no score (match floors at 0).
    "context_weight_entities": 0.25,
    "context_weight_event_time": 0.25,
    "context_weight_location": 0.25,
    # Time-proximity kernel scale: match = exp(-|event_time - query|/scale).
    "context_time_scale_seconds": 86400.0,
    # --- hybrid lexical channel (read-path.md; ruled 2026-07-20) ------------
    # Lexical candidates unioned into the vector over-fetch before scoring
    # (dedup by memory_id; the scoring formula is untouched — lexical-only
    # hits carry their TRUE cosine relevance where the fact head has an
    # embedding). 0.0 disables the channel (the gate_enabled kill-switch
    # shape): pure-vector candidates, v1-byte-identical.
    "lexical_fetch_k": 8.0,
    # --- split-brain streaming (split-brain-streaming.md; built 2026-07-21) --
    # The behavior view re-ranks the SAME served top-k the dialogue view got,
    # with resolved per-call weights (the reserved WeightOverrides slot goes
    # live for the behavior view; the dialogue view keeps byte-parity). Weights
    # apply as exponents on the product score component-wise
    # (behavior_score = item.score * rel^(w_rel-1) * rec^(w_rec-1) *
    # imp^(w_imp-1)) — so 1.0 reproduces the dialogue-view order exactly (the
    # parity contract) and any other value genuinely re-ranks. Resolution is
    # request field -> agents.config -> these defaults, then clamped to
    # [BEHAVIOR_WEIGHT_MIN, BEHAVIOR_WEIGHT_MAX].
    "behavior_weight_relevance": 1.0,
    "behavior_weight_recency": 1.0,
    "behavior_weight_importance": 1.0,
    # Caller-held recent-actions scene block cap: the prose prompt carries at
    # most this many most-recent resolved directives as world-fact context
    # (integer-valued; cast at the call site, the gate_fetch_k precedent).
    "recent_actions_cap": 8.0,
}

# Behavior-view weight clamp bounds (split-brain-streaming.md settle-tag,
# ruled at build): a soft de-/re-emphasis range, never a mask. 0.0 zeroes a
# component's exponent contribution to +1 (pow(x, -1)); the ceiling bounds
# runaway emphasis. Module constants, not knobs — the range itself is not
# integrator policy (the EMBEDDING_DIM precedent for a fixed structural bound).
BEHAVIOR_WEIGHT_MIN = 0.0
BEHAVIOR_WEIGHT_MAX = 4.0

# The lexical channel's text-search config: a string knob, so it follows the
# decay_classes precedent (a plain agents.config key + a module default)
# rather than the float-only SERVICE_DEFAULTS/agent_knob contract. The
# migration-004 index expression bakes this default; an agent override still
# works but runs unindexed (correct, slower — stated in the migration).
TEXT_SEARCH_CONFIG_DEFAULT = "simple"


def text_search_config(agent_config: dict) -> str:
    """Per-agent text_search_config override, else the service default."""
    value = agent_config.get("text_search_config")
    return str(value) if value else TEXT_SEARCH_CONFIG_DEFAULT


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    """Parse the repo-root .env into a dict. Values are never logged.

    A process environment variable of the same name overrides the .env value
    (lets verification point at the scratch DB without touching .env).
    """
    if not path.exists():
        sys.exit(f"ERROR: {path} not found; .env is required.")
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    overridable = (
        set(values)
        | {
            "DATABASE_URI",
            ENV_PROVIDER_MODE,
            ENV_MODEL_IMPORTANCE,
            ENV_MODEL_RENDER,
            ENV_MODEL_TYPOLOGY,
            ENV_MODEL_ESCALATION,
            ENV_MODEL_DIALOGUE,
            ENV_MODEL_RECONSTRUCTION,
            ENV_MODEL_BEHAVIOR,
        }
        | set(PRICE_ENV_KEYS)
    )
    for key in overridable:
        if key in os.environ:
            values[key] = os.environ[key]
    return values


@dataclass(frozen=True)
class Settings:
    """Resolved runtime configuration. Secrets stay off __repr__."""

    database_uri: str = field(repr=False)
    provider_mode: str = "fake"  # "real" | "fake"; fake is the offline default
    model_write: str = ""  # the single write-call model (render+importance+typology)
    model_escalation: str = ""
    model_dialogue: str = ""  # the streaming prose role (dialogue call; split-brain)
    model_reconstruction: str = ""  # the batched retelling role (reconstruction.md)
    model_behavior: str = ""  # the concurrent behavior call (directive + delta)
    anthropic_api_key: str = field(default="", repr=False)
    openai_api_key: str = field(default="", repr=False)
    defaults: dict[str, float] = field(default_factory=lambda: dict(SERVICE_DEFAULTS))
    # Optional USD-per-Mtok prices (PRICE_ENV_KEYS); empty = cost in tokens only.
    prices: dict[str, float] = field(default_factory=dict)


class ConfigError(RuntimeError):
    """Loud startup configuration failure (never a silent fallback)."""


def load_settings(env: dict[str, str] | None = None) -> Settings:
    """Build Settings from .env; validate loudly per the v1 rulings."""
    if env is None:
        env = load_env()

    database_uri = env.get("DATABASE_URI", "")
    if not database_uri:
        raise ConfigError("DATABASE_URI not set in .env.")

    mode = env.get(ENV_PROVIDER_MODE, "fake").lower()
    if mode not in ("real", "fake"):
        raise ConfigError(
            f"{ENV_PROVIDER_MODE} must be 'real' or 'fake', got {mode!r}."
        )

    model_write = ""
    model_escalation = ""
    model_dialogue = ""
    model_reconstruction = ""
    model_behavior = ""
    anthropic_key = ""
    openai_key = ""
    if mode == "real":
        importance = env.get(ENV_MODEL_IMPORTANCE, "")
        render = env.get(ENV_MODEL_RENDER, "")
        typology = env.get(ENV_MODEL_TYPOLOGY, "")
        escalation = env.get(ENV_MODEL_ESCALATION, "")
        dialogue = env.get(ENV_MODEL_DIALOGUE, "")
        reconstruction = env.get(ENV_MODEL_RECONSTRUCTION, "")
        behavior = env.get(ENV_MODEL_BEHAVIOR, "")
        missing = [
            name
            for name, value in (
                (ENV_MODEL_IMPORTANCE, importance),
                (ENV_MODEL_RENDER, render),
                (ENV_MODEL_TYPOLOGY, typology),
                (ENV_MODEL_ESCALATION, escalation),
                (ENV_MODEL_DIALOGUE, dialogue),
                (ENV_MODEL_RECONSTRUCTION, reconstruction),
                (ENV_MODEL_BEHAVIOR, behavior),
            )
            if not value
        ]
        if missing:
            raise ConfigError(
                f"real mode requires model role env vars: {', '.join(missing)}."
            )
        # One call serves render+importance+typology in v1: the three role
        # vars must agree (documented limitation; error, never a silent pick).
        if not (importance == render == typology):
            raise ConfigError(
                "v1's single write call requires "
                f"{ENV_MODEL_IMPORTANCE} == {ENV_MODEL_RENDER} == {ENV_MODEL_TYPOLOGY}; "
                "they diverge in .env."
            )
        model_write = importance
        model_escalation = escalation
        model_dialogue = dialogue
        model_reconstruction = reconstruction
        model_behavior = behavior
        anthropic_key = env.get("ANTHROPIC_API_KEY", "")
        openai_key = env.get("OPENAI_API_KEY", "")
        if not anthropic_key:
            raise ConfigError("real mode requires ANTHROPIC_API_KEY in .env.")
        if not openai_key:
            raise ConfigError("real mode requires OPENAI_API_KEY in .env.")

    prices: dict[str, float] = {}
    for env_key, price_key in PRICE_ENV_KEYS.items():
        raw = env.get(env_key, "")
        if not raw:
            continue
        try:
            prices[price_key] = float(raw)
        except ValueError as exc:
            raise ConfigError(f"{env_key} must be a number, got {raw!r}.") from exc

    return Settings(
        database_uri=database_uri,
        provider_mode=mode,
        model_write=model_write,
        model_escalation=model_escalation,
        model_dialogue=model_dialogue,
        model_reconstruction=model_reconstruction,
        model_behavior=model_behavior,
        anthropic_api_key=anthropic_key,
        openai_api_key=openai_key,
        prices=prices,
    )


def agent_knob(agent_config: dict, key: str, settings: Settings) -> float:
    """Per-agent override from agents.config, else the service default."""
    value = agent_config.get(key)
    if value is None:
        return settings.defaults[key]
    return float(value)
