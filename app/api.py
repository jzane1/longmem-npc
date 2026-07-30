"""api.py — thin FastAPI routes over the ingest and retrieval services.

Pass-through by ruling (2026-07-13, mirrored for reads 2026-07-14): for one
call, the route's JSON response is exactly the serialization of the result
the service returned — the route adds and drops nothing, and records no
timing or tokens of its own (the seams are `app\\ingest.py` and
`app\\retrieval.py`).

    PowerShell:  python -m app.serve
(not bare `uvicorn app.api:app` — see app\\serve.py for the Windows
event-loop constraint)
"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from uuid import UUID

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from app.config import load_settings
from app.db import build_pool
from app.dialogue import DialogueService
from app.ingest import (
    CorrectionConflictError,
    CorrectionEmbedFailedError,
    CorrectionNlpFailedError,
    IngestService,
    UnknownAgentError,
    UnknownMemoryError,
)
from app.nlp import warm_pipelines
from app.providers import build_providers
from app.reconstruction import UnknownIdentityVersionError
from app.retrieval import RetrievalService
from app.schemas import (
    AgentMemoriesResult,
    CorrectionRequest,
    CorrectionResult,
    CreateAgentRequest,
    CreateAgentResult,
    DialogueInitRequest,
    DialogueTurnRequest,
    DialogueTurnResult,
    IngestResult,
    MemoryChainResult,
    ObserveEvent,
    PinRequest,
    PinResult,
    ReconstructionMetricsResult,
    RetrievalResult,
    SceneBoundaryEvent,
    SceneResult,
)

# Running SSE pump tasks hold a reference here so a client disconnect can
# never garbage-collect a mid-turn task — the turn always completes
# server-side (the reputation apply is atomic inside the seam).
_stream_tasks: set[asyncio.Task] = set()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings = load_settings()
    pool = build_pool(settings.database_uri)
    await pool.open()
    await asyncio.to_thread(warm_pipelines)  # model load is startup cost
    providers = build_providers(settings)
    app.state.service = IngestService(pool, providers, settings)
    app.state.retrieval = RetrievalService(pool, providers, settings)
    app.state.dialogue = DialogueService(pool, providers, settings, app.state.retrieval)
    try:
        yield
    finally:
        await pool.close()


app = FastAPI(title="longmem-npc API", version="1", lifespan=_lifespan)


@app.post("/v1/dialogue/init", response_model=RetrievalResult)
async def dialogue_init(request: DialogueInitRequest) -> RetrievalResult:
    """Dialogue-init retrieval (read-path.md wire shape, ruled 2026-07-14) —
    since the reconstruction build (2026-07-17) this endpoint also serves the
    pre-warm: past-theta items reconstruct (write-back + cache) before the
    response returns. An unknown caller-passed identity_version is a broken
    contract, not a flaky model -> 422 (the unknown-agent 404 precedent)."""
    try:
        return await app.state.retrieval.retrieve_dialogue_init(request)
    except UnknownAgentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnknownIdentityVersionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/v1/dialogue/turn", response_model=DialogueTurnResult)
async def dialogue_turn(request: DialogueTurnRequest) -> DialogueTurnResult:
    """One dialogue turn over HTTP (the audit's #1 gap, built 2026-07-23) —
    the Unity/C# front door to the split-brain seam. STATELESS: all scene
    state (reputation snapshot, identity version, scene basis, loaded set,
    context, recent actions) rides on the request, and the runner bookkeeping
    (`session._apply_turn_result`) is the CLIENT'S job — the future C#
    NpcSession ports it. Non-streaming: drains `run_dialogue_turn`'s async
    generator to the terminal result (first_word_ms/perceived_first_word_ms
    ride in the instrumentation, so no chunk consumption is needed); the SSE
    route below iterates the SAME generator — no rewrite, as designed.
    `on_reconstruct` stays None here (no during-wait signal without SSE; the
    result's post-hoc reconstruction fields carry it). Pass-through by ruling:
    the response is exactly the seam result's serialization."""
    try:
        result: DialogueTurnResult | None = None
        async for item in app.state.dialogue.run_dialogue_turn(request):
            if isinstance(item, DialogueTurnResult):
                result = item
        if result is None:  # the seam always yields a terminal result
            raise RuntimeError("dialogue turn produced no result")
        return result
    except UnknownAgentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnknownIdentityVersionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/v1/dialogue/turn/stream")
async def dialogue_turn_stream(request: DialogueTurnRequest) -> StreamingResponse:
    """The SSE turn route (unity-client.md fork 1, ruled 2026-07-27) — the
    streaming twin of /v1/dialogue/turn, iterating the SAME async-generator
    seam (the 2026-07-23 no-rewrite payoff). Wire shape, text/event-stream:
    `event: chunk` per prose str (JSON-encoded so newlines survive SSE
    framing), optional `event: reconstructing` fired at the pre-serve
    callback DURING a blocking mid-scene retelling (the REPL's
    "(reconstructing…)" over HTTP), then `event: result` carrying the
    terminal DialogueTurnResult JSON — byte-identical serialization to the
    non-streaming route's body (pass-through by ruling). The seam runs in a
    pump task bridged through an asyncio.Queue because the callback fires
    inside the awaited chain; the FIRST queue item is awaited before the
    response starts, so UnknownAgentError → 404 / UnknownIdentityVersionError
    → 422 still map to real status codes. After streaming begins a failure
    becomes `event: error` (a 200 stream cannot change its status). A client
    disconnect never aborts the turn server-side."""
    queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue()

    async def _pump() -> None:
        try:
            async for item in app.state.dialogue.run_dialogue_turn(
                request,
                on_reconstruct=lambda: queue.put_nowait(("reconstructing", None)),
            ):
                if isinstance(item, DialogueTurnResult):
                    queue.put_nowait(("result", item))
                else:
                    queue.put_nowait(("chunk", item))
            queue.put_nowait(("done", None))
        except Exception as exc:  # forwarded: mapped pre-stream, event after
            queue.put_nowait(("error", exc))

    task = asyncio.create_task(_pump())
    _stream_tasks.add(task)
    task.add_done_callback(_stream_tasks.discard)

    first = await queue.get()
    if first[0] == "error":
        exc = first[1]
        if isinstance(exc, UnknownAgentError):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if isinstance(exc, UnknownIdentityVersionError):
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        raise exc  # type: ignore[misc]  # a genuine 500

    def _sse(name: str, data: str) -> str:
        return f"event: {name}\ndata: {data}\n\n"

    async def _events():
        item = first
        while True:
            kind, payload = item
            if kind == "chunk":
                yield _sse("chunk", json.dumps(payload))
            elif kind == "reconstructing":
                yield _sse("reconstructing", "{}")
            elif kind == "result":
                yield _sse("result", payload.model_dump_json())
            elif kind == "error":
                yield _sse("error", json.dumps(str(payload)))
                break
            else:  # "done" — the terminal result already streamed
                break
            item = await queue.get()

    return StreamingResponse(
        _events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@app.post("/v1/events/observe", response_model=IngestResult)
async def observe(event: ObserveEvent) -> IngestResult:
    try:
        return await app.state.service.ingest_observation(event)
    except UnknownAgentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/v1/events/scene-boundary", response_model=SceneResult)
async def scene_boundary(event: SceneBoundaryEvent) -> SceneResult:
    try:
        return await app.state.service.scene_boundary(event)
    except UnknownAgentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/v1/memories/{memory_id}/pin", response_model=PinResult)
async def set_pin(memory_id: UUID, body: PinRequest) -> PinResult:
    try:
        return await app.state.service.set_pin(memory_id, body.pinned)
    except UnknownMemoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/v1/memories/{memory_id}/correction", response_model=CorrectionResult)
async def correct_memory(memory_id: UUID, body: CorrectionRequest) -> CorrectionResult:
    """Authorial correction (authorial-correction.md; fact-following since
    the fact-level build): memory-scoped operator verb — /v1/events/* stays
    diegetic. Fail-loud: 404 unknown memory, 409 stale expected_detail_id,
    422 invalid content, 502 embed or NER failure with nothing written (the
    all-or-nothing correction rulings, 2026-07-18 / 2026-07-19); nothing
    partial. (The observe-path escalation call soft-degrades since 2026-07-22 —
    it no longer hard-stops; these correction paths stay fail-loud.)"""
    try:
        return await app.state.service.correct(memory_id, body)
    except UnknownMemoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CorrectionConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CorrectionEmbedFailedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except CorrectionNlpFailedError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/v1/agents", response_model=CreateAgentResult)
async def create_agent(request: CreateAgentRequest) -> CreateAgentResult:
    """Agent provisioning (unity-client.md fork 2, ruled 2026-07-27) — the
    integrator's minute-one verb; before this route the demo agent was
    hand-SQL. UUID minted server-side (stack constant); no model calls; the
    identity document compiles at the first scene boundary / session start
    as before. Pass-through by ruling."""
    return await app.state.service.create_agent(request)


@app.get("/v1/memories/{memory_id}/chain", response_model=MemoryChainResult)
async def memory_chain(memory_id: UUID) -> MemoryChainResult:
    """The Ledger's ground-truth-vs-telling read (unity-client.md fork 3,
    ruled 2026-07-27): the immutable observation beside BOTH version chains
    (superseded rows present — greyed client-side, never dropped) + gist
    spans. Read-only and unscored: no retrieval ran, so no scores exist;
    IDs + structured fields on every row keep the read-payload discipline.
    404 on unknown memory (the pin-route precedent)."""
    try:
        return await app.state.retrieval.memory_chain(memory_id)
    except UnknownMemoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get(
    "/v1/memories/{memory_id}/reconstruction-metrics",
    response_model=ReconstructionMetricsResult,
)
async def reconstruction_metrics(memory_id: UUID) -> ReconstructionMetricsResult:
    """The judge-free metric read (eval-harness.md stage 1, ruled
    2026-07-29): gist-precision / detail-recall / fabrication / keyword
    retention against the live telling head, The Ledger's on-screen numbers.
    Runs no retrieval (no scores exist — the invariant does not bind) and
    performs ZERO writes; the two inspector reads' unscored-by-contract
    wording is untouched. 404 on unknown memory (the /chain shape);
    pass-through by ruling."""
    try:
        return await app.state.retrieval.reconstruction_metrics(memory_id)
    except UnknownMemoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


_LEDGER_PATH = Path(__file__).resolve().parent.parent / "ledger" / "index.html"


@app.get("/ledger", include_in_schema=False)
async def ledger_page() -> FileResponse:
    """The Ledger (unity-client.md stage 3, ruled 2026-07-27) — the static
    designer-facing inspector page, served BY the API so it ships with the
    service and shares the origin of the two read routes it polls (no CORS
    surface, no second server). The page itself is `ledger\\index.html` —
    vanilla JS, no build step (fork 6)."""
    return FileResponse(_LEDGER_PATH, media_type="text/html")


@app.get("/v1/agents/{agent_id}/memories", response_model=AgentMemoriesResult)
async def agent_memories(
    agent_id: UUID, limit: int = Query(default=100, ge=1, le=1000)
) -> AgentMemoriesResult:
    """The Ledger's per-agent index (unity-client.md fork 3): each memory
    beside its live telling head, newest valid_at first; `limit` is a caller
    argument (the k precedent), never a config knob. 404 on unknown agent."""
    try:
        return await app.state.retrieval.agent_memories(agent_id, limit)
    except UnknownAgentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
