"""api.py — thin FastAPI routes over the ingest service.

Pass-through by ruling (2026-07-13): for one ingest, the route's JSON response
is exactly the serialization of the `IngestResult` the service returned — the
route adds and drops nothing, and records no timing or tokens of its own (the
seam is `app\\ingest.py`).

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
    EscalationHardStopError,
    IngestService,
    UnknownAgentError,
    UnknownMemoryError,
)
from app.nlp import warm_pipelines
from app.providers import build_providers
from app.schemas import (
    IngestResult,
    ObserveEvent,
    PinRequest,
    PinResult,
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
    app.state.service = IngestService(pool, build_providers(settings), settings)
    try:
        yield
    finally:
        await pool.close()


app = FastAPI(title="longmem-npc ingestion API", version="1", lifespan=_lifespan)


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
