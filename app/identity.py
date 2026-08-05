"""identity.py — the rendered identity document (architecture §4.3, item 2).

Pre-demo rendering is seed prose VERBATIM (reconstruction.md: a template
would be a hidden hardcoded authorial artifact); reflections join the render
post-August by extending render_identity_document — the version hash and the
plumbing stay put. identity_version = sha256 hex of the rendered text.

Plumbing (spec-time ruling 2026-07-17, the caller-frozen-scene-state
precedent):
the scene-boundary handler recompiles server-side via ensure_identity_document
and returns identity_version; the caller freezes it as scene state and passes
it on each read request. A read arriving without a version lazy-bootstraps
through the same ensure. A NULL seed renders as the empty string (hashed like
any document); the reconstruction prompt omits the identity block for it.
"""

from __future__ import annotations

import hashlib
from uuid import UUID

from psycopg_pool import AsyncConnectionPool

from app import db


def render_identity_document(seed_identity: str | None) -> tuple[str, str]:
    """(rendered_text, identity_version) — pure, so the walker asserts the
    hash contract without a database."""
    rendered = seed_identity if seed_identity is not None else ""
    version = hashlib.sha256(rendered.encode()).hexdigest()
    return rendered, version


async def ensure_identity_document(
    pool: AsyncConnectionPool, agent_id: UUID, seed_identity: str | None
) -> tuple[str, str, bool]:
    """Render, hash, and upsert the current document. Returns
    (identity_version, rendered_text, created) — created is False when this
    exact version already existed (recompiling an unchanged seed is a no-op
    row-wise; the version is stable because the content hash is)."""
    rendered, version = render_identity_document(seed_identity)
    created = await db.upsert_identity_document(pool, agent_id, rendered, version)
    return version, rendered, created
