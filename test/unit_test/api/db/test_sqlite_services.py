#
#  Copyright 2026 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
"""
SQLite-based test approach for DB services.

This file demonstrates how to replace _FakeQuery and _FieldStub patterns
with in-memory SQLite for more realistic and maintainable tests.

Key benefits:
- Tests use real Peewee ORM queries instead of fakes
- Faster than integration tests with real MySQL/PostgreSQL
- Catches issues that fake mocks miss (e.g., field name typos)
- Schema is defined once, reused across fixtures
"""

import sys
import types
import warnings

import pytest
import peewee
from playhouse.sqlite_ext import SqliteExtDatabase

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
)


def _install_cv2_stub_if_unavailable():
    try:
        import cv2

        return
    except Exception:
        pass

    stub = types.ModuleType("cv2")
    stub.INTER_LINEAR = 1
    stub.INTER_CUBIC = 2
    stub.BORDER_CONSTANT = 0
    stub.BORDER_REPLICATE = 1

    def _missing(*_args, **_kwargs):
        raise RuntimeError("cv2 runtime call is unavailable in this test environment")

    def _module_getattr(name):
        if name.isupper():
            return 0
        return _missing

    stub.__getattr__ = _module_getattr
    sys.modules["cv2"] = stub


_install_cv2_stub_if_unavailable()


# =============================================================================
# SQLite Model Definitions (mirrors db_models.py Document model)
# =============================================================================


class _SqliteDocument(peewee.Model):
    """SQLite version of Document model for testing."""

    id = peewee.CharField(max_length=32, primary_key=True)
    thumbnail = peewee.TextField(null=True)
    kb_id = peewee.CharField(max_length=256, null=False, index=True)
    parser_id = peewee.CharField(max_length=32, null=False, default="naive", index=True)
    pipeline_id = peewee.CharField(max_length=32, null=True, index=True)
    parser_config = peewee.TextField(null=False, default='{"pages": [[1, 1000000]]}')
    source_type = peewee.CharField(max_length=128, null=False, default="local", index=True)
    type = peewee.CharField(max_length=32, null=False, index=True)
    created_by = peewee.CharField(max_length=32, null=False, default="system", index=True)
    name = peewee.CharField(max_length=255, null=True, index=True)
    location = peewee.CharField(max_length=255, null=True, index=True)
    size = peewee.IntegerField(default=0, index=True)
    token_num = peewee.IntegerField(default=0, index=True)
    chunk_num = peewee.IntegerField(default=0, index=True)
    progress = peewee.FloatField(default=0, index=True)
    progress_msg = peewee.TextField(null=True, default="")
    process_begin_at = peewee.DateTimeField(null=True, index=True)
    process_duration = peewee.FloatField(default=0)
    suffix = peewee.CharField(max_length=32, null=False, default="txt", index=True)
    content_hash = peewee.CharField(max_length=32, null=True, default="", index=True)
    run = peewee.CharField(max_length=1, null=True, default="0", index=True)
    status = peewee.CharField(max_length=1, null=True, default="1", index=True)
    create_time = peewee.DateTimeField(null=True)
    create_date = peewee.DateField(null=True, index=True)
    update_time = peewee.DateTimeField(null=True)
    update_date = peewee.DateField(null=True, index=True)

    class Meta:
        table_name = "document"
        database = None


class _SqliteUserCanvas(peewee.Model):
    """SQLite version of UserCanvas model."""

    id = peewee.CharField(max_length=32, primary_key=True)
    tenant_id = peewee.CharField(max_length=32, null=False, index=True)
    title = peewee.CharField(max_length=255, null=True)
    canvas_category = peewee.CharField(max_length=16, null=False, default="chat")

    class Meta:
        table_name = "user_canvas"
        database = None


class _SqliteFile2Document(peewee.Model):
    """SQLite version of File2Document model."""

    id = peewee.CharField(max_length=32, primary_key=True)
    file_id = peewee.CharField(max_length=32, null=True, index=True)
    document_id = peewee.CharField(max_length=32, null=True, index=True)

    class Meta:
        table_name = "file2document"
        database = None


class _SqliteFile(peewee.Model):
    """SQLite version of File model."""

    id = peewee.CharField(max_length=32, primary_key=True)
    parent_id = peewee.CharField(max_length=32, null=False, index=True)
    tenant_id = peewee.CharField(max_length=32, null=False, index=True)
    created_by = peewee.CharField(max_length=32, null=False, default="system", index=True)
    name = peewee.CharField(max_length=255, null=False, index=True)
    location = peewee.CharField(max_length=255, null=True, index=True)
    size = peewee.IntegerField(default=0, index=True)
    type = peewee.CharField(max_length=32, null=False, index=True)
    source_type = peewee.CharField(max_length=128, null=False, default="", index=True)

    class Meta:
        table_name = "file"
        database = None


# =============================================================================
# Fixtures: Create in-memory SQLite with schema
# =============================================================================


@pytest.fixture
def sqlite_db():
    """Create in-memory SQLite database with schema."""
    db = SqliteExtDatabase(":memory:")

    _SqliteDocument._meta.database = db
    _SqliteUserCanvas._meta.database = db
    _SqliteFile2Document._meta.database = db
    _SqliteFile._meta.database = db

    db.create_tables(
        [
            _SqliteDocument,
            _SqliteUserCanvas,
            _SqliteFile2Document,
            _SqliteFile,
        ]
    )

    yield db

    db.close()


@pytest.fixture
def sample_documents(sqlite_db):
    """Insert sample documents into the test DB."""
    docs = [
        _SqliteDocument.create(
            id=f"doc-{i}",
            kb_id="kb-1",
            name=f"doc-{i}.txt",
            type="txt",
            created_by="user-1",
            run="1",
            status="1",
            size=100 * i,
            token_num=10 * i,
            chunk_num=i,
            progress=1.0 if i % 2 == 0 else 0.0,
        )
        for i in range(1, 6)
    ]
    return docs


@pytest.fixture
def sample_documents_multiple_kb(sqlite_db):
    """Documents across multiple KBs for testing multi-KB queries."""
    _SqliteDocument.create(id="doc-a1", kb_id="kb-a", name="doc-a1.txt", type="txt", created_by="user-1", run="1", status="1")
    _SqliteDocument.create(id="doc-a2", kb_id="kb-a", name="doc-a2.txt", type="txt", created_by="user-1", run="1", status="1")
    _SqliteDocument.create(id="doc-b1", kb_id="kb-b", name="doc-b1.txt", type="txt", created_by="user-1", run="0", status="1")
    _SqliteDocument.create(id="doc-c1", kb_id="kb-c", name="doc-c1.txt", type="txt", created_by="user-1", run="2", status="1")


@pytest.fixture
def sample_documents_with_files(sqlite_db):
    """Documents with associated files for join tests."""
    _SqliteFile.create(id="file-1", parent_id="root", tenant_id="tenant-1", created_by="user-1", name="test.txt", type="txt", size=100)
    _SqliteFile2Document.create(id="f2d-1", file_id="file-1", document_id="doc-1")
    _SqliteDocument.create(id="doc-1", kb_id="kb-1", name="test.txt", type="txt", created_by="user-1", run="1", status="1")


# =============================================================================
# Test Cases: Show how SQLite replaces FakeQuery/FieldStub
# =============================================================================


class TestSqliteDocumentQueries:
    """
    These tests demonstrate how SQLite replaces the old _FakeQuery pattern.

    OLD APPROACH (test_document_service_metadata_paging.py):
        class _FakeQuery:
            def __init__(self, docs): ...
            def join(self, *args, **kwargs): ...
            def where(self, *args, **kwargs): ...
            def count(self): ...
            def paginate(self, page, page_size): ...
            def dicts(self): ...

    NEW APPROACH: Real Peewee queries against SQLite
    """

    def test_simple_select_all(self, sqlite_db, sample_documents):
        """Basic query: select all documents for a KB."""
        query = _SqliteDocument.select().where(_SqliteDocument.kb_id == "kb-1")
        results = list(query.dicts())

        assert len(results) == 5
        assert all(r["kb_id"] == "kb-1" for r in results)

    def test_select_with_pagination(self, sqlite_db, sample_documents):
        """Pagination: similar to DocumentService.get_list."""
        page = 1
        page_size = 2
        offset = (page - 1) * page_size

        query = _SqliteDocument.select().where(_SqliteDocument.kb_id == "kb-1").order_by(_SqliteDocument.create_time.desc()).limit(page_size).offset(offset)
        results = list(query.dicts())

        assert len(results) == 2

    def test_select_with_filter_conditions(self, sqlite_db, sample_documents):
        """Filtering: apply multiple where conditions."""
        query = _SqliteDocument.select().where(_SqliteDocument.kb_id == "kb-1").where(_SqliteDocument.run == "0").where(_SqliteDocument.status == "1")
        results = list(query.dicts())

        assert len(results) == 0

    def test_aggregation_with_group_by(self, sqlite_db, sample_documents_multiple_kb):
        """Aggregation: group by KB and count (like get_parsing_status)."""
        from peewee import fn

        query = (
            _SqliteDocument.select(_SqliteDocument.kb_id, _SqliteDocument.run, fn.COUNT(_SqliteDocument.id).alias("cnt"))
            .where(_SqliteDocument.kb_id.in_(["kb-a", "kb-b", "kb-c"]))
            .group_by(_SqliteDocument.kb_id, _SqliteDocument.run)
        )
        results = list(query.dicts())

        assert len(results) == 3

    def test_join_with_related_tables(self, sqlite_db, sample_documents_with_files):
        """Joins: simulate DocumentService.get_list joins."""
        query = (
            _SqliteDocument.select(_SqliteDocument.id, _SqliteDocument.name, _SqliteFile.name.alias("file_name"))
            .join(_SqliteFile2Document, on=(_SqliteFile2Document.document_id == _SqliteDocument.id))
            .join(_SqliteFile, on=(_SqliteFile.id == _SqliteFile2Document.file_id))
            .where(_SqliteDocument.kb_id == "kb-1")
        )
        results = list(query.dicts())

        assert len(results) == 1
        assert results[0]["file_name"] == "test.txt"

    def test_count_query(self, sqlite_db, sample_documents):
        """Count: get total count without fetching rows."""
        count = _SqliteDocument.select().where(_SqliteDocument.kb_id == "kb-1").count()

        assert count == 5

    def test_in_clause_filter(self, sqlite_db, sample_documents):
        """IN clause: filter by multiple IDs."""
        query = _SqliteDocument.select().where(_SqliteDocument.id.in_(["doc-1", "doc-3"]))
        results = list(query.dicts())

        assert len(results) == 2
        ids = {r["id"] for r in results}
        assert ids == {"doc-1", "doc-3"}

    def test_not_in_clause_filter(self, sqlite_db, sample_documents):
        """NOT IN clause: exclude certain IDs."""
        query = _SqliteDocument.select().where((_SqliteDocument.kb_id == "kb-1") & (~_SqliteDocument.id.in_(["doc-1", "doc-2"])))
        results = list(query.dicts())

        assert len(results) == 3
        ids = {r["id"] for r in results}
        assert "doc-1" not in ids
        assert "doc-2" not in ids


class TestSqlitePerformance:
    """Verify SQLite approach remains fast."""

    def test_query_performance(self, sqlite_db, sample_documents_multiple_kb):
        """Queries should complete quickly even with more data."""
        import time

        start = time.perf_counter()
        for _ in range(100):
            list(_SqliteDocument.select().where(_SqliteDocument.kb_id == "kb-a").dicts())
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"100 queries took {elapsed:.2f}s, expected < 1s"


class TestSqliteSchemaValidation:
    """
    These tests show how SQLite catches issues that _FakeQuery misses.

    For example, if you typo a field name in a query:
    - _FakeQuery silently ignores it
    - SQLite raises FieldDoesNotExist
    """

    def test_field_name_typo_caught(self, sqlite_db, sample_documents):
        """Typoed field name should raise error in real ORM."""
        with pytest.raises(AttributeError):
            list(_SqliteDocument.select().where(_SqliteDocument.unknown_field == "value").dicts())

    def test_join_on_invalid_field_caught(self, sqlite_db, sample_documents_with_files):
        """Invalid join field should raise error."""
        with pytest.raises(AttributeError):
            list(_SqliteDocument.select().join(_SqliteFile2Document, on=(_SqliteFile2Document.invalid_field == _SqliteDocument.id)))


# =============================================================================
# Migration Guide: Converting existing tests
# =============================================================================

"""
MIGRATION STEPS from FakeQuery/FieldStub to SQLite:

1. DEFINE MODELS:
   Create SQLite versions of the Peewee models you need.
   Copy field definitions from db_models.py but use SQLite-compatible types.

2. CREATE FIXTURE:
   @pytest.fixture
   def sqlite_db():
       db = SqliteExtDatabase(":memory:")
       # Set model databases and create tables
       yield db
       db.close()

3. REPLACE MOCKS:
   OLD: monkeypatch.setattr(DocumentService, "model", fake_model)
   NEW: Use real _SqliteDocument model in queries

4. REPLACE QUERY CONSTRUCTION:
   OLD: _FakeQuery(rows) with manual .where(), .paginate()
   NEW: Real peewee query chain: .select().where().order_by().limit()

5. UPDATE ASSERTIONS:
   Results are now real dicts from SQLite - same assertions work.

EXAMPLE CONVERSION:

OLD (test_document_service_metadata_paging.py):
    class _FakeField:
        def __eq__(self, other): return self
        def in_(self, other): return self
        def not_in(self, other): return self

    class _FakeQuery:
        def __init__(self, docs):
            self._all = list(docs)
            self._current = list(docs)
        def join(self, *args, **kwargs): return self
        def where(self, *args, **kwargs): return self
        def count(self): return len(self._all)
        def paginate(self, page, page_size): ...
        def dicts(self): return list(self._current)

NEW:
    @pytest.fixture
    def sqlite_db():
        db = SqliteExtDatabase(":memory:")
        _SqliteDocument._meta.database = db
        db.create_tables([_SqliteDocument])
        yield db
        db.close()

    def test_example(sqlite_db):
        _SqliteDocument.create(id="doc-1", kb_id="kb-1", ...)
        query = _SqliteDocument.select().where(_SqliteDocument.kb_id == "kb-1")
        assert query.count() == 1
"""
