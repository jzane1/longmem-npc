"""smoke_test.py — migration-01 fixture smoke test.

Inserts the "Done when" fixture (one agent; one memory with one 'original' detail
row; one gist span; one identity component) inside a single transaction, reads it
back asserting the server-minted UUIDs returned and the live head resolves, then
ROLLS BACK so the database stays pristine for later layers.

No model or embedding calls: the embedding is a 1536-d zero vector built server-side
(array_fill(0::real, ARRAY[1536])::vector).

    PowerShell:  python db\\smoke_test.py
"""

from __future__ import annotations

from psycopg.types.json import Jsonb

import psycopg

from migrate import load_database_uri  # same db\ directory on sys.path[0]

# Server-side zero embedding — keeps the fixture free of any model call.
ZERO_VEC = "array_fill(0::real, ARRAY[1536])::vector"


def main() -> None:
    uri = load_database_uri()
    with psycopg.connect(uri, autocommit=False) as conn, conn.cursor() as cur:
        # agent
        cur.execute(
            "INSERT INTO agents (name, seed_identity, reputation, rigidity, "
            "reputation_sensitivity, diagnosticity_goal, config) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING agent_id",
            ("Smoke NPC", "A test seed identity.", 0, 1.0, 1.0,
             "what this NPC finds diagnostic", Jsonb({})),
        )
        agent_id = cur.fetchone()[0]
        assert agent_id is not None, "agent_id not returned by server default"

        # identity component
        cur.execute(
            "INSERT INTO identity_components (agent_id, canonical, aliases, category) "
            "VALUES (%s, %s, %s, %s) RETURNING component_id",
            (agent_id, "Mara", ["Mara the smith", "the blacksmith"], "person"),
        )
        component_id = cur.fetchone()[0]
        assert component_id is not None, "component_id not returned by server default"

        # memory — world time supplied, embedding a server-built zero vector
        cur.execute(
            "INSERT INTO memories (agent_id, observation_text, embedding, importance_raw, "
            "typology, typology_confidence, typology_source, provenance, decay_class, "
            "valid_at, entities, affect_valence, affect_arousal, affect_detail) "
            f"VALUES (%s, %s, {ZERO_VEC}, %s, %s, %s, %s, %s, %s, now(), %s, %s, %s, %s) "
            "RETURNING memory_id",
            (agent_id, "Mara sharpened my blade at the forge.", 0.5,
             "observed", 0.9, "inferred", "lived", "episodic",
             ["Mara"], 0.2, 0.4, Jsonb({"pos": 0.2})),
        )
        memory_id = cur.fetchone()[0]
        assert memory_id is not None, "memory_id not returned by server default"

        # original detail head
        cur.execute(
            "INSERT INTO memory_details (memory_id, content, write_cause, valid_at) "
            "VALUES (%s, %s, %s, now()) RETURNING detail_id",
            (memory_id, "Mara sharpened my blade at the forge.", "original"),
        )
        detail_id = cur.fetchone()[0]
        assert detail_id is not None, "detail_id not returned by server default"

        # gist span into observation_text — "Mara" occupies chars [0, 4)
        cur.execute(
            "INSERT INTO memory_gist_spans (memory_id, start_char, end_char, "
            "matched_component_id, matched_category) VALUES (%s, %s, %s, %s, %s) "
            "RETURNING span_id",
            (memory_id, 0, 4, component_id, "person"),
        )
        span_id = cur.fetchone()[0]
        assert span_id is not None, "span_id not returned by server default"

        # read back — the live head resolves, and exactly one gist span exists
        cur.execute(
            "SELECT detail_id, write_cause FROM memory_details "
            "WHERE memory_id = %s AND invalid_at IS NULL",
            (memory_id,),
        )
        head = cur.fetchone()
        assert head == (detail_id, "original"), f"unexpected live head: {head}"

        cur.execute(
            "SELECT count(*) FROM memory_gist_spans WHERE memory_id = %s", (memory_id,)
        )
        assert cur.fetchone()[0] == 1, "expected exactly one gist span"

        print("Smoke fixture OK (read back before rollback):")
        print(f"  agent_id     = {agent_id}")
        print(f"  memory_id    = {memory_id}")
        print(f"  detail_id    = {detail_id}  (write_cause=original, live head)")
        print(f"  span_id      = {span_id}  (chars [0,4) -> component {component_id})")
        print(f"  component_id = {component_id}")

        conn.rollback()
        print("Rolled back — database left pristine.")


if __name__ == "__main__":
    main()
