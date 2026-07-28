"""Repo-hygiene assertions — structural, pure, no database, no NLP.

These exist because a rule stated only in a comment is a rule that drifts. Each
test here makes one already-written rule mechanically enforceable, and each was
added because the rule had already been broken once.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIRS = ("app", "db", "tests")

# The oldest interpreter whose grammar our source must still parse under.
# Not a support commitment — a canary. See the test docstring.
GRAMMAR_FLOOR = (3, 13)


def _python_files() -> list[Path]:
    files: list[Path] = []
    for folder in SOURCE_DIRS:
        for path in sorted((REPO_ROOT / folder).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            files.append(path)
    return files


def test_no_version_gated_syntax_rewrites():
    """No source file uses syntax newer than the grammar floor.

    The canary this catches: ruff's formatter applies PEP 758 when
    `target-version` is py314, silently rewriting `except (A, B):` into
    `except A, B:` across the tree — valid on 3.14, a syntax error before it,
    and an unrequested rewrite of floor-verified files. `ruff.toml` leaves
    `target-version` unset precisely to prevent that, and says so in a comment.

    On 2026-07-28 that comment was committed in the SAME change as two files
    the hazard had already rewritten. One was caught by eye in the diff; the
    other (`app\\ingest.py`) shipped and was found by the floor-verifier.
    Neither `ruff check` nor `ruff format --check` flags it, so nothing would
    ever have caught the next one.

    This test would have. It is not a claim that the project supports 3.13 —
    it is a claim that the formatter is not quietly changing our syntax.
    """
    offenders: list[str] = []
    for path in _python_files():
        source = path.read_text(encoding="utf-8")
        try:
            ast.parse(source, feature_version=GRAMMAR_FLOOR)
        except SyntaxError as exc:
            rel = path.relative_to(REPO_ROOT)
            offenders.append(f"{rel}:{exc.lineno}: {exc.msg}")

    assert not offenders, (
        "source uses syntax newer than the grammar floor "
        f"{'.'.join(map(str, GRAMMAR_FLOOR))} — almost certainly a formatter "
        "rewrite, not something anyone typed. Check that ruff.toml still "
        "leaves `target-version` unset, then revert the rewrite:\n  "
        + "\n  ".join(offenders)
    )


def test_no_sql_outside_the_db_module():
    """`app\\db.py` is the only module in `app\\` that writes SQL.

    A stack constant (CLAUDE.md: hand-written SQL, no ORM) and the reason the
    injection surface is auditable in one file. `app\\load_driver.py` violated
    it with a hand-rolled agents INSERT — literals baked into the statement —
    until 2026-07-28.
    """
    statements = ("INSERT INTO", "UPDATE ", "DELETE FROM", "SELECT ")
    offenders: list[str] = []
    for path in sorted((REPO_ROOT / "app").rglob("*.py")):
        if path.name == "db.py" or "__pycache__" in path.parts:
            continue
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if any(token in line for token in statements):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{number}: {stripped}")

    assert not offenders, (
        "SQL found outside app\\db.py — move it there so the query surface "
        "stays auditable in one file:\n  " + "\n  ".join(offenders)
    )
