# longmem-npc

Self-hostable long-term-memory service for game NPCs — FastAPI + PostgreSQL/pgvector backend plus a
Unity-embeddable client package. Characters get psychologically plausible memory: an immutable
bi-temporal record underneath; identity-conditioned reconstructive recall, believable decay, and
dissonance-driven defense above it. *A psychology, not a database.*

The claim it is built to defend: **memory should be reconstructed at recall time, not replayed.**
The record underneath is never edited — corrections supersede, they do not overwrite — while what
the character *tells you* is re-told through who they currently are, and drifts as time passes.
Both halves are inspectable side by side.

## Repository layout

| Path | What it is |
|---|---|
| `app\` | the service — ingest, retrieval, reconstruction, the gate, the dialogue seam, the HTTP routes |
| `db\` | numbered migrations (001–005) and the transactional migration runner |
| `tests\` | the pytest suite + seven structural done-when walkers |
| `client\` | `NpcMemory.Core` — the engine-agnostic C# client — and a console harness |
| `unity\` | the Unity 6 gray-box demo project: a thin adapter over the client, plus the set |
| `ledger\` | The Ledger — a browser inspector for the record, served by the API at `/ledger` |
| `docs\` | design truth, build specs, and the append-only registers — start at `docs\README.md` |

## Getting started

**`docs\SETUP.md`** takes a fresh clone to a running system. Short version, PowerShell:

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env    # then edit it
docker compose up -d
python db\migrate.py
python -m app.serve
```

It runs offline and keyless by default (`LONGMEM_PROVIDER_MODE=fake`) — no API key needed to
explore. Then open `http://127.0.0.1:8000/ledger`, or drive a character from the REPL with
`python -m app.cli --agent <uuid> --debug`.

## Where to read next

- **`docs\README.md`** — the index: what every doc is for, and the reading order
- **`docs\architecture.md`** — the design truth, in thirteen sections
- **`docs\status.md`** — where the project stands right now, and what is queued
- **`docs\decisions.md`** — every ruling, what it beat, and why
- **`docs\floors.md`** — what has actually been verified, and against what

## Status

Private during development; the demo video is the introduction this is being built toward.
License: **Apache-2.0** (`LICENSE`; third-party inventory in `NOTICE`) — public flip at
end-of-project sprint.

*This README will be rewritten for the public flip, when the demo footage and the real-mode
instrumentation table exist to carry it.*
