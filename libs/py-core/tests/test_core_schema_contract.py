"""Schema contract: the Python SQLAlchemy mirror must match the live Prisma-managed database.

Prisma (apps/backend/prisma) is the single source of truth for the Postgres schema. The models
in ``docqa_core.db`` are a hand-maintained MIRROR used by the Python AI services. This test
runs against a database already migrated by Prisma (DOCQA_TEST_DATABASE_URL) and fails when
the mirror drifts: a missing table or column, a nullability mismatch, or a live NOT NULL column
without a server default that the model does not know about (Python inserts would fail).
"""

import os

import pytest
from sqlalchemy import Table, create_engine, inspect
from sqlalchemy.engine.reflection import Inspector

from docqa_core.db import Base

TEST_URL = os.environ.get("DOCQA_TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not TEST_URL, reason="DOCQA_TEST_DATABASE_URL not set"),
]

PREFIX = "Python mirror drifted from Prisma schema"


def _check_table(insp: Inspector, table: Table) -> list[str]:
    if not insp.has_table(table.name):
        return [f"{PREFIX}: table '{table.name}' is missing from the live database"]
    live = {c["name"]: c for c in insp.get_columns(table.name)}
    problems: list[str] = []
    for col in table.columns:
        if col.name not in live:
            problems.append(f"{PREFIX}: column '{table.name}.{col.name}' not in live database")
        elif bool(live[col.name]["nullable"]) != bool(col.nullable):
            problems.append(
                f"{PREFIX}: nullability of '{table.name}.{col.name}' differs "
                f"(model nullable={col.nullable}, live nullable={live[col.name]['nullable']})"
            )
    for name, info in live.items():
        if name not in table.columns and not info["nullable"] and info.get("default") is None:
            problems.append(
                f"{PREFIX}: live column '{table.name}.{name}' is NOT NULL without a server "
                "default but is missing from the model (Python inserts would fail)"
            )
    return problems


def test_python_mirror_matches_prisma_schema() -> None:
    assert TEST_URL
    engine = create_engine(TEST_URL)
    try:
        insp = inspect(engine)
        problems = [p for t in Base.metadata.sorted_tables for p in _check_table(insp, t)]
    finally:
        engine.dispose()
    assert not problems, "\n".join(problems)
