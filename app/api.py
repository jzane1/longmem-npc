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

from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException

from app.config import load_settings
from app.db import build_pool
from app.ingest import (
    CorrectionConflictError,
    CorrectionEmbedFailedError,
    CorrectionNlpFailedError,
    EscalationHardStopError,
    IngestService,
    UnknownAgentError,
    UnknownMemoryError,
)
from app.nlp import warm_pipelines
from app.providers import build_providers
from app.reconstruction import UnknownIdentityVersionError
from app.retrieval import RetrievalService
from app.schemas import (
    CorrectionRequest,
    CorrectionResult,
    DialogueInitRequest,
    IngestResult,
    ObserveEvent,
    PinRequest,
    PinResult,
    RetrievalResult,
    SceneBoundaryEvent,
    SceneResult,
)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings = load_settings()
    pool = build_pool(settings.database_uri)
    await pool.open()
    import asyncio

    await asyncio.to_thread(warm_pipelines)  # model load is startup cost
    providers = build_providers(settings)
    app.state.service = IngestService(pool, providers, settings)
    app.state.retrieval = RetrievalService(pool, providers, settings)
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


@app.post("/v1/events/observe", response_model=IngestResult)
async def observe(event: ObserveEvent) -> IngestResult:
    try:
        return await app.state.service.ingest_observation(event)
    except UnknownAgentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EscalationHardStopError as exc:
        # Build-phase fail-loud stance (re-rule before the demo): nothing was
        # inserted; the client may safely resend.
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
    all-or-nothing rulings, 2026-07-18 / 2026-07-19 — the
    escalation-hard-stop precedent); nothing partial."""
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
