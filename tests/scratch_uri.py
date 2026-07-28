"""scratch_uri.py — the one safe way to point a fixture at a scratch database.

Shared by `conftest.py` (the pytest suite) and all seven `verify_*.py`
walkers. Every one of those callers goes on to run something destructive
against whatever URI it is handed — `DROP DATABASE`, `TRUNCATE ... CASCADE`,
or a migration — so getting this wrong once is a lost product database.

Why not `urlsplit(uri)._replace(path=f"/{name}")` on its own (the shape every
caller used before 2026-07-28): **libpq honors a `dbname` query parameter over
the URI path.** A `DATABASE_URI` of the form

    postgresql://user:pw@host:5432/postgres?dbname=longmem

survives a path-only swap with its `dbname` intact, so the "scratch" URI still
resolves to the product database. Demonstrated with libpq's own parser:

    path-only swap -> dbname='longmem'      <- the product DB
    this function  -> dbname='longmem_test'

So: strip every `dbname` key from the query (keeping the rest — `sslmode` and
friends must survive), rewrite the path, then **prove** the result by parsing
it back through `psycopg.conninfo.conninfo_to_dict` and refusing loudly if the
resolved database is not the one asked for. A guard that only holds for the
URI shapes we happen to use today is not a guard.

Never prints or returns any part of the credential.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from psycopg.conninfo import conninfo_to_dict


class ScratchUriError(RuntimeError):
    """The rewritten URI does not resolve to the requested scratch database."""


def scratch_uri(base_uri: str, name: str) -> str:
    """Rewrite `base_uri` to point at database `name`, verified.

    Raises ScratchUriError (never returning a usable URI) if the result
    resolves anywhere else. The message names only database names, never the
    URI.
    """
    if not name or not name.replace("_", "").isalnum():
        raise ScratchUriError(f"unsafe scratch database name: {name!r}")

    parts = urlsplit(base_uri)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key != "dbname"
    ]
    swapped = urlunsplit(parts._replace(path=f"/{name}", query=urlencode(query)))

    resolved = conninfo_to_dict(swapped).get("dbname")
    if resolved != name:
        raise ScratchUriError(
            f"refusing to proceed: rewritten URI resolves to database "
            f"{resolved!r}, not the requested scratch database {name!r}"
        )
    return swapped
