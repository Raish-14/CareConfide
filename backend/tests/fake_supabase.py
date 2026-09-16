"""
A minimal in-process stand-in for the real `supabase-py` client, used to
unit-test app/services/supabase_db.py without any network access or a
real Supabase project.

It implements just enough of the fluent Postgrest query-builder API that
SupabaseDatabase actually calls: .table(name).insert(...).execute(),
.select("*").eq(...).limit(...).order(...).execute(), and
.update(...).eq(...).execute().

Crucially, the backing `data` dict can be shared between two separate
FakeSupabaseClient instances. That lets a test simulate "the backend
process restarted" by throwing away a SupabaseDatabase instance and
creating a brand new one that points at the *same* backing dict (playing
the role of the real, durable Postgres database) — proving that nothing
required by persistence was actually being held in Python process
memory.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FakeResponse:
    def __init__(self, data: list[dict]):
        self.data = data


class FakeQuery:
    def __init__(self, table: "FakeTable", op: str, payload: Any = None):
        self.table = table
        self.op = op
        self.payload = payload
        self.filters: list[tuple[str, Any]] = []
        self.order_col: str | None = None
        self.limit_n: int | None = None

    def eq(self, col: str, val: Any) -> "FakeQuery":
        self.filters.append((col, val))
        return self

    def order(self, col: str) -> "FakeQuery":
        self.order_col = col
        return self

    def limit(self, n: int) -> "FakeQuery":
        self.limit_n = n
        return self

    def _matching_rows(self) -> list[dict]:
        rows = self.table.rows()
        for col, val in self.filters:
            rows = [r for r in rows if r.get(col) == val]
        return rows

    def execute(self) -> FakeResponse:
        if self.table.client.fail_tables.get(self.table.name):
            raise RuntimeError(f"simulated failure for table '{self.table.name}'")

        if self.op == "insert":
            row = dict(self.payload)
            row.setdefault("id", str(uuid.uuid4()))
            row.setdefault("created_at", _now())
            self.table.rows().append(row)
            return FakeResponse([row])

        if self.op == "select":
            results = self._matching_rows()
            if self.order_col:
                results = sorted(results, key=lambda r: r.get(self.order_col) or "")
            if self.limit_n is not None:
                results = results[: self.limit_n]
            return FakeResponse(list(results))

        if self.op == "update":
            matched = self._matching_rows()
            for row in matched:
                row.update(self.payload)
            return FakeResponse(list(matched))

        raise RuntimeError(f"unsupported fake op: {self.op}")


class FakeTable:
    def __init__(self, client: "FakeSupabaseClient", name: str):
        self.client = client
        self.name = name

    def rows(self) -> list[dict]:
        return self.client.data.setdefault(self.name, [])

    def insert(self, payload: dict) -> FakeQuery:
        return FakeQuery(self, "insert", payload)

    def select(self, *_args) -> FakeQuery:
        return FakeQuery(self, "select")

    def update(self, payload: dict) -> FakeQuery:
        return FakeQuery(self, "update", payload)


class FakeSupabaseClient:
    """
    `data` is the "durable Postgres database". Pass the SAME dict into
    two different FakeSupabaseClient instances to simulate two different
    backend process lifetimes reading/writing the same real database.
    """

    def __init__(self, data: dict[str, list[dict]] | None = None):
        self.data: dict[str, list[dict]] = data if data is not None else {}
        # table_name -> True means the next call against that table raises,
        # used to test DatabaseError surfacing.
        self.fail_tables: dict[str, bool] = {}

    def table(self, name: str) -> FakeTable:
        return FakeTable(self, name)


def make_supabase_database(shared_backing: dict | None = None):
    """
    Build a SupabaseDatabase instance wired to a FakeSupabaseClient,
    bypassing the real __init__ (which requires actual Supabase env vars
    and the `supabase` package's real client). Returns (db, client) so
    tests can also flip `client.fail_tables[...] = True`.
    """
    from app.services.supabase_db import SupabaseDatabase

    db = SupabaseDatabase.__new__(SupabaseDatabase)
    client = FakeSupabaseClient(shared_backing)
    db.client = client
    return db, client
