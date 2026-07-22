"""cli.py — the interactive console harness: the product surface of the
vertical slice (event in -> memory stored -> dialogue out), readable top to
bottom as documentation of the turn loop.

    PowerShell:  python -m app.cli --agent <uuid> [--debug]

Plain input is a player utterance: it drives dialogue-init retrieval, the
single Sonnet-class dialogue call, and the in-place reputation apply — one
`SessionRunner.utterance()` call on the shared session-runner core
(app\\session.py); the synthetic load driver drives the very same core.

Meta-commands (everything else is an utterance):

    :observe <text>    store an observation through the write seam
                       (the first :observe loads the NLP models — one-time cost)
    :scene [type]      scene boundary: emits the event (the handler recompiles
                       the identity document and returns its version), then
                       re-freezes the scene state — reputation snapshot,
                       identity version, and the scene basis time
    :pin <memory_id>   pin a memory (decay exemption)     :unpin undoes it
    :correct <memory_id> <text>
                       authorial correction: replace the live telling with
                       the operator's text byte-verbatim (supersede + cache
                       evict; takes effect immediately, mid-scene included)
    :as-of <iso8601>   drive the session at an injected world time
                       (retrieval age math + observe timestamps);  :as-of clear
    :context [loc=<name>] [entities=<a,b,c>] [time=<iso8601>]
                       set the scene context the encoding-context term reads
                       (caller-held; each turn passes it through; a scene
                       boundary clears it);  :context clear   :context  shows
    :debug [on|off]    toggle the full turn debug view (IDs + scores, parsed
                       structured output, reputation math, tokens + latency)
    :help              this text                          :quit  exit

Windows event-loop constraint: everything runs inside one
asyncio.run(..., loop_factory=SelectorEventLoop) — psycopg's async pool
cannot run on the default ProactorEventLoop (see app\\serve.py).
"""

from __future__ import annotations

import argparse
import asyncio
import shlex
import sys
from datetime import datetime, timezone
from uuid import UUID

from app.ingest import (
    CorrectionEmbedFailedError,
    EscalationHardStopError,
    UnknownAgentError,
    UnknownMemoryError,
)
from app.schemas import DialogueTurnResult, IngestResult
from app.session import SessionRunner

HELP = __doc__.split("Meta-commands", 1)[1]


# ---------------------------------------------------------------------------
# Rendering — pure functions over the structured payloads, so the structural
# walker can assert the debug view carries IDs, scores, and counts.
# ---------------------------------------------------------------------------


def render_turn_tail(result: DialogueTurnResult) -> str:
    """The post-prose lines: the action + the soft flags. Split off the content
    line so the REPL can stream the prose live and print this tail after
    (split-brain 2026-07-21)."""
    lines = []
    if result.directive is not None:
        lines.append(f"  [directive] {result.directive.type} {result.directive.params}")
    if result.directive_dropped:
        lines.append(f"  [directive dropped] {result.directive_dropped_reason}")
    if result.instrumentation.degraded:
        lines.append(f"  [degraded] {result.instrumentation.degraded_reason}")
    return "\n".join(lines)


def render_turn(result: DialogueTurnResult) -> str:
    """The normal (non-debug) view: the line, the action, the soft flags."""
    lines = [f"npc> {result.content}"]
    tail = render_turn_tail(result)
    if tail:
        lines.append(tail)
    return "\n".join(lines)


def render_debug(result: DialogueTurnResult) -> str:
    """The full turn debug view (status.md requirement): retrieved memory IDs
    with score components, the parsed structured output, the reputation math,
    and the token + latency accounting — all straight off the payload."""
    ins = result.instrumentation
    ret = ins.retrieval
    lines = ["-- retrieved memories (IDs + score components) --"]
    if not result.items:
        lines.append("  (none)")
    for item in result.items:
        rel = f"{item.relevance:.4f}" if item.relevance is not None else "null"
        lines.append(
            f"  {item.memory_id}  score={item.score:.4f}  rel={rel}  "
            f"rec={item.recency:.4f}  imp={item.importance_norm:.4f}  "
            f"mode={item.read_mode}"
            f"{'  [pinned]' if item.pinned else ''}"
        )
    lines.append("-- structured output --")
    lines.append(f"  prose:     {result.content}")
    if result.directive is not None:
        lines.append(f"  directive: {result.directive.type} {result.directive.params}")
    elif result.directive_dropped:
        lines.append(f"  directive: DROPPED ({result.directive_dropped_reason})")
    else:
        lines.append("  directive: none")
    lines.append(
        f"  delta:     {result.reputation_delta} ({result.reputation_delta_source})"
    )
    # Divergence record (split-brain 2026-07-21): the two concurrent calls'
    # scored views, short-id ranked — re-ordering here is the split brain.
    lines.append("-- split-brain views (dialogue | behavior) --")
    lines.append(f"  dialogue:  {[str(r.memory_id)[:8] for r in result.dialogue_view]}")
    lines.append(f"  behavior:  {[str(r.memory_id)[:8] for r in result.behavior_view]}")
    lines.append("-- reputation --")
    lines.append(
        f"  snapshot={result.reputation_snapshot}  prev={result.reputation_prev}  "
        f"sensitivity={result.reputation_sensitivity}  after={result.reputation_after}"
    )
    lines.append("-- timing / tokens --")
    lines.append(
        f"  retrieval: embed={ret.embed_ms}ms sql={ret.sql_ms}ms "
        f"lex={ret.lexical_candidate_count}/{ret.lexical_sql_ms}ms "
        f"score={ret.score_ms}ms total={ret.total_ms}ms "
        f"candidates={ret.candidate_count} k={ret.k_effective}"
        f"{'  [degraded: ' + str(ret.degraded_reason) + ']' if ret.degraded else ''}"
    )
    if ret.context_active:
        lines.append(f"  context:   active ({', '.join(ret.context_components)})")
    if ret.gate.evaluated:
        g = ret.gate
        lines.append(
            f"  gate:      fired={g.signals_fired if g.fired else 'no'} "
            f"min_dist={g.novelty_min_distance} "
            f"fetched={g.fetched_new_count} fruitless={'yes' if g.fruitless else 'no'} "
            f"damper={'on' if g.damper_active else 'off'} "
            f"rung={g.degraded_rung or '-'} "
            f"blocked={'yes' if g.reconstructing_blocked else 'no'} {g.gate_ms}ms"
        )
    else:
        lines.append("  gate:      (loader turn)")
    lines.append(
        f"  recon:     hits={ret.cache_hits} misses={ret.cache_misses} "
        f"write_backs={ret.write_backs} refusals={ret.drift_refusals} "
        f"total={ret.reconstruction_ms}ms  tokens "
        f"in={ret.reconstruction_input_tokens} "
        f"out={ret.reconstruction_output_tokens} "
        f"drift_embed={ret.reconstruction_embed_tokens}"
        f"{'  [bootstrapped]' if ret.identity_bootstrapped else ''}"
    )
    lines.append(
        f"  prose:     first_word={ins.first_word_ms}ms "
        f"stream={ins.prose_stream_ms}ms  tokens in={ins.sonnet_input_tokens} "
        f"out={ins.sonnet_output_tokens}"
    )
    lines.append(
        f"  behavior:  {ins.behavior_ms}ms  tokens "
        f"in={ins.behavior_input_tokens} out={ins.behavior_output_tokens}"
        + (f"  cost=${ins.cost_usd}" if ins.cost_usd is not None else "")
    )
    lines.append(f"  apply={ins.apply_ms}ms  turn_total={ins.total_ms}ms")
    if ins.degraded:
        lines.append(f"  [turn degraded] {ins.degraded_reason}")
    return "\n".join(lines)


def render_observe(result: IngestResult) -> str:
    """Write-seam receipt: IDs + computed facts, never prose assertions."""
    flags = [
        name
        for name, on in (
            ("scoring_failed", result.scoring_failed),
            ("embedding_failed", result.embedding_failed),
            ("decay_class_unknown", result.decay_class_unknown),
            ("escalated", result.instrumentation.escalated),
            ("pinned", result.pinned),
        )
        if on
    ]
    return (
        f"stored {result.memory_id}  importance={result.importance_raw}  "
        f"typology={result.typology}({result.typology_source})  "
        f"decay_class={result.decay_class}"
        + (f"  [{', '.join(flags)}]" if flags else "")
    )


# ---------------------------------------------------------------------------
# The REPL loop
# ---------------------------------------------------------------------------


def _parse_as_of(text: str) -> datetime:
    """ISO-8601; a naive timestamp is taken as UTC (stated, not silent)."""
    value = datetime.fromisoformat(text)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def _apply_context_args(runner: SessionRunner, raw: str) -> None:
    """Parse `:context` key=value pairs onto the runner's caller-held scene
    context (encoding-context build 2026-07-20). Keys: loc / entities / time;
    unset keys keep their current value (set-what-you-name). shlex-split so
    quoted values carry spaces (:context loc="Rusty Anchor")."""
    for token in shlex.split(raw):
        key, sep, value = token.partition("=")
        if not sep or not value:
            raise ValueError(f"expected key=value, got {token!r} (see :help)")
        if key == "loc":
            runner.context_location = value
        elif key == "entities":
            runner.context_entities = [e for e in value.split(",") if e]
        elif key == "time":
            runner.context_event_time = _parse_as_of(value)
        else:
            raise ValueError(f"unknown context key {key!r} (loc|entities|time)")


def _render_context(runner: SessionRunner) -> str:
    """The current caller-held scene context, honestly including 'none'."""
    parts = []
    if runner.context_location is not None:
        parts.append(f"loc={runner.context_location}")
    if runner.context_entities is not None:
        parts.append(f"entities={','.join(runner.context_entities)}")
    if runner.context_event_time is not None:
        parts.append(f"time={runner.context_event_time.isoformat()}")
    return f"context: {' '.join(parts)}" if parts else "context: (none)"


async def repl(agent_id: UUID, debug: bool) -> None:
    runner = await SessionRunner.create(agent_id)
    runner.debug = debug
    # Fork 5 (mid-dialogue-gate.md): the pre-serve callback prints DURING a
    # blocking mid-scene retelling — the pause reads as recall, not lag (it
    # fires just before the retelling call blocks the turn).
    runner.on_reconstruct = lambda: print("(reconstructing…)", flush=True)
    nlp_warm = False
    print(
        f"longmem-npc CLI — agent {agent_id}  "
        f"(reputation snapshot {runner.reputation_snapshot}; :help for commands)"
    )
    try:
        while True:
            try:
                line = (await asyncio.to_thread(input, "you> ")).strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not line:
                continue
            try:
                # -- meta-commands ------------------------------------------
                if line in (":quit", ":q"):
                    break
                elif line == ":help":
                    print(HELP)
                elif line.startswith(":observe"):
                    text = line[len(":observe") :].strip()
                    if not text:
                        print("usage: :observe <text>")
                        continue
                    if not nlp_warm:
                        print("(loading NLP pipelines — first observe only)")
                        nlp_warm = True
                    print(render_observe(await runner.observe(text)))
                elif line.startswith(":scene"):
                    scene_type = line[len(":scene") :].strip() or None
                    result = await runner.scene(scene_type)
                    version = (
                        f"{result.identity_version[:12]}…"
                        if result.identity_version
                        else "none"
                    )
                    print(
                        f"scene boundary accepted ({result.total_ms}ms); "
                        f"reputation snapshot -> {runner.reputation_snapshot}; "
                        f"identity {version}"
                        f"{' (new document)' if result.identity_document_new else ''}"
                    )
                elif line.startswith((":pin", ":unpin")):
                    command, _, raw_id = line.partition(" ")
                    result = await runner.pin(
                        UUID(raw_id.strip()), pinned=(command == ":pin")
                    )
                    print(f"{result.memory_id} pinned={result.pinned}")
                elif line.startswith(":correct"):
                    rest = line[len(":correct") :].strip()
                    raw_id, _, text = rest.partition(" ")
                    text = text.strip()
                    if not raw_id or not text:
                        print("usage: :correct <memory_id> <corrected text>")
                        continue
                    correction = await runner.correct(UUID(raw_id), text)
                    print(
                        f"corrected {correction.memory_id}: head "
                        f"{correction.superseded_detail_id} -> "
                        f"{correction.detail_id}; fact "
                        f"{correction.superseded_fact_version_id} -> "
                        f"{correction.fact_version_id}; "
                        f"{correction.evicted_cache_rows} cache row(s) "
                        f"evicted (embed {correction.embed_ms}ms/"
                        f"{correction.embedding_tokens}tok, "
                        f"{correction.total_ms}ms total)"
                    )
                elif line.startswith(":as-of"):
                    raw = line[len(":as-of") :].strip()
                    if raw in ("", "clear"):
                        runner.as_of = None
                        print("as-of cleared (live world time)")
                    else:
                        runner.as_of = _parse_as_of(raw)
                        print(f"session time set to {runner.as_of.isoformat()}")
                elif line.startswith(":context"):
                    raw = line[len(":context") :].strip()
                    if raw == "clear":
                        runner.context_location = None
                        runner.context_entities = None
                        runner.context_event_time = None
                        print("context cleared")
                    elif raw:
                        _apply_context_args(runner, raw)
                        print(_render_context(runner))
                    else:
                        print(_render_context(runner))
                elif line.startswith(":debug"):
                    raw = line[len(":debug") :].strip()
                    runner.debug = raw == "on" if raw else not runner.debug
                    print(f"debug {'on' if runner.debug else 'off'}")
                elif line.startswith(":"):
                    print(f"unknown command {line.split()[0]!r} — :help lists them")
                # -- everything else is a player utterance ------------------
                else:
                    # Stream the prose live (split-brain 2026-07-21): "npc> "
                    # is printed lazily on the first chunk, so a mid-scene
                    # "(reconstructing…)" (fired during retrieval, before any
                    # chunk) stays on its own line above the streamed line.
                    result: DialogueTurnResult | None = None
                    streamed = False
                    async for item in runner.stream_utterance(line):
                        if isinstance(item, DialogueTurnResult):
                            result = item
                        else:
                            if not streamed:
                                print("npc> ", end="", flush=True)
                                streamed = True
                            print(item, end="", flush=True)
                    if streamed:
                        print()  # newline after the streamed prose
                    elif result is not None:  # no chunks (fallback line)
                        print(f"npc> {result.content}")
                    if result is not None:
                        tail = render_turn_tail(result)
                        if tail:
                            print(tail)
                        if runner.debug:
                            print(render_debug(result))
            except (ValueError, UnknownMemoryError) as exc:
                print(f"error: {exc}")
            except EscalationHardStopError as exc:
                # Build-phase fail-loud stance (re-rule before the demo):
                # nothing was inserted; the observe may be resent safely.
                print(f"write hard-stopped: {exc}")
            except CorrectionEmbedFailedError as exc:
                # All-or-nothing (ruled 2026-07-18): nothing was written on
                # either chain; the :correct may be re-issued safely.
                print(f"correction failed: {exc}")
    finally:
        await runner.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="longmem-npc interactive console harness"
    )
    parser.add_argument("--agent", required=True, type=UUID, help="agent UUID")
    parser.add_argument(
        "--debug", action="store_true", help="render the full turn debug view"
    )
    args = parser.parse_args()
    if not sys.stdin.isatty():
        # Piped scripts arrive as UTF-8, typically with a BOM (PowerShell
        # here-strings); utf-8-sig decodes them correctly and strips it.
        # Interactive consoles are untouched.
        sys.stdin.reconfigure(encoding="utf-8-sig")
    try:
        asyncio.run(
            repl(args.agent, args.debug), loop_factory=asyncio.SelectorEventLoop
        )
    except UnknownAgentError as exc:
        raise SystemExit(f"ERROR: {exc}")


if __name__ == "__main__":
    main()
