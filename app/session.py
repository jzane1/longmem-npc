"""session.py — the shared session-runner core beneath both drive surfaces.

The interactive REPL (app\\cli.py) and the synthetic load driver
(app\\load_driver.py) both drive sessions through this class, calling the
three built seams in-process (ingest, retrieval via the dialogue service,
dialogue) — one runner core, two thin callers, so the paths cannot drift
apart (spec-time ruling 2026-07-14). No timing or token accounting happens
here; the seams record it.

Scene state lives here, per the seam contract (cli-harness.md): the runner
freezes the reputation snapshot read at the last scene boundary and passes it
into every turn; mid-scene deltas accumulate on the agents.reputation row but
the injected snapshot does not change until `scene()` re-reads it. The
scene-boundary reputation-snapshot consumer (deferred in write-v1) lands
here, per the 2026-07-14 re-slating.

`as_of` is the session's time-travel surface: when set, it rides retrieval's
age computation AND becomes the client_timestamp of `observe()` events, so a
whole session can be driven at an injected world time (tests\\CLAUDE.md).

Callers on Windows must run this under a SelectorEventLoop (psycopg's async
pool cannot run on the default ProactorEventLoop) — see app\\serve.py; both
drive surfaces use asyncio.run(..., loop_factory=asyncio.SelectorEventLoop).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID

from psycopg_pool import AsyncConnectionPool

from app import db
from app.config import Settings, agent_knob, load_settings
from app.db import build_pool
from app.dialogue import DialogueService
from app.ingest import IngestService, UnknownAgentError
from app.nlp import warm_pipelines
from app.providers import Providers, build_providers
from app.retrieval import RetrievalService
from app.schemas import (
    DialogueTurnRequest,
    DialogueTurnResult,
    IngestResult,
    ObserveEvent,
    PinResult,
    SceneBoundaryEvent,
    SceneResult,
)


class SessionRunner:
    """One NPC session: frozen scene state + the seams. Build with `create`."""

    def __init__(
        self,
        *,
        pool: AsyncConnectionPool,
        owns_pool: bool,
        settings: Settings,
        ingest: IngestService,
        dialogue: DialogueService,
        agent_id: UUID,
        phase_tag: str,
    ):
        self._pool = pool
        self._owns_pool = owns_pool
        self._settings = settings
        self._ingest = ingest
        self._dialogue = dialogue
        self.agent_id = agent_id
        self.phase_tag = phase_tag  # passthrough label on observe events
        self.reputation_snapshot: float = 0.0  # set by _refresh_snapshot
        self.as_of: datetime | None = None  # session time-travel override
        self.debug: bool = False  # rendering hint; inert to the seams

    @classmethod
    async def create(
        cls,
        agent_id: UUID,
        *,
        settings: Settings | None = None,
        providers: Providers | None = None,
        pool: AsyncConnectionPool | None = None,
        phase_tag: str = "cli",
        warm_nlp: bool = False,
    ) -> SessionRunner:
        """Bootstrap the seams and read the scene-start snapshot. Injection
        points (settings/providers/pool) exist for the load driver and the
        structural walker; the REPL uses the defaults. `warm_nlp` front-loads
        the spaCy/fastcoref model cost (the load driver warms so warm-up never
        lands inside a measured turn; the REPL pays it lazily on the first
        `:observe` instead)."""
        settings = settings if settings is not None else load_settings()
        owns_pool = pool is None
        if pool is None:
            pool = build_pool(settings.database_uri)
            await pool.open()
        providers = providers if providers is not None else build_providers(settings)
        if warm_nlp:
            await asyncio.to_thread(warm_pipelines)
        ingest = IngestService(pool, providers, settings)
        retrieval = RetrievalService(pool, providers, settings)
        dialogue = DialogueService(pool, providers, settings, retrieval)
        runner = cls(
            pool=pool,
            owns_pool=owns_pool,
            settings=settings,
            ingest=ingest,
            dialogue=dialogue,
            agent_id=agent_id,
            phase_tag=phase_tag,
        )
        await runner._refresh_snapshot()  # loud UnknownAgentError at startup
        return runner

    def _now(self) -> datetime:
        return self.as_of if self.as_of is not None else datetime.now(timezone.utc)

    async def _refresh_snapshot(self) -> float:
        """Read the reputation scalar into the frozen snapshot (NULL row value
        -> the agent's neutral point; nothing hardcoded)."""
        state = await db.fetch_dialogue_agent_state(self._pool, self.agent_id)
        if state is None:
            raise UnknownAgentError(f"unknown agent_id {self.agent_id}")
        self.reputation_snapshot = (
            state.reputation
            if state.reputation is not None
            else agent_knob(state.config, "reputation_neutral", self._settings)
        )
        return self.reputation_snapshot

    async def utterance(
        self,
        text: str,
        *,
        reputation_delta_override: float | None = None,
        action_vocabulary: list[str] | None = None,
        k: int | None = None,
    ) -> DialogueTurnResult:
        """One dialogue turn through the seam, under the frozen snapshot."""
        return await self._dialogue.run_dialogue_turn(
            DialogueTurnRequest(
                agent_id=self.agent_id,
                utterance=text,
                reputation_snapshot=self.reputation_snapshot,
                reputation_delta_override=reputation_delta_override,
                action_vocabulary=action_vocabulary,
                k=k,
                as_of=self.as_of,
                debug=self.debug,
            )
        )

    async def observe(self, text: str) -> IngestResult:
        """One observe event through the write seam, at the session's time."""
        return await self._ingest.ingest_observation(
            ObserveEvent(
                agent_id=self.agent_id,
                observation_text=text,
                phase_tag=self.phase_tag,
                client_timestamp=self._now(),
                provenance="lived",
            )
        )

    async def scene(self, scene_type: str | None = None) -> SceneResult:
        """Scene boundary: emit the event (accept + instrument), then refresh
        the frozen snapshot — the next scene's prompt sees the accumulated
        reputation; within the ending scene it never moved."""
        result = await self._ingest.scene_boundary(
            SceneBoundaryEvent(
                agent_id=self.agent_id,
                client_timestamp=self._now(),
                scene_type=scene_type,
            )
        )
        await self._refresh_snapshot()
        return result

    async def pin(self, memory_id: UUID, pinned: bool) -> PinResult:
        return await self._ingest.set_pin(memory_id, pinned)

    async def close(self) -> None:
        if self._owns_pool:
            await self._pool.close()
