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
        import cv2  # noqa: F401

        return
    except Exception:
        pass

    stub = types.ModuleType("cv2")

    stub.INTER_LINEAR = 1
    stub.INTER_CUBIC = 2
    stub.BORDER_CONSTANT = 0
    stub.BORDER_REPLICATE = 1
    stub.COLOR_BGR2RGB = 0
    stub.COLOR_BGR2GRAY = 1
    stub.COLOR_GRAY2BGR = 2
    stub.IMREAD_IGNORE_ORIENTATION = 128
    stub.IMREAD_COLOR = 1
    stub.RETR_LIST = 1
    stub.CHAIN_APPROX_SIMPLE = 2

    def _missing(*_args, **_kwargs):
        raise RuntimeError("cv2 runtime call is unavailable in this test environment")

    def _module_getattr(name):
        if name.isupper():
            return 0
        return _missing

    stub.__getattr__ = _module_getattr
    sys.modules["cv2"] = stub


_install_cv2_stub_if_unavailable()

from api.db.services.document_service import DocumentService  # noqa: E402
from common.constants import TaskStatus  # noqa: E402


class _SqliteDocument(peewee.Model):
    """SQLite version of Document model for testing parsing status aggregation."""

    id = peewee.CharField(max_length=32, primary_key=True)
    kb_id = peewee.CharField(max_length=256, null=False, index=True)
    run = peewee.CharField(max_length=1, null=True, default="0", index=True)
    create_time = peewee.BigIntegerField(null=True, index=True)

    class Meta:
        table_name = "document"
        database = None


@pytest.fixture
def sqlite_db():
    """Create in-memory SQLite database with schema."""
    db = SqliteExtDatabase(":memory:")
    _SqliteDocument._meta.database = db
    db.create_tables([_SqliteDocument])
    yield db
    db.close()


@pytest.fixture
def populate_documents(sqlite_db):
    """Insert sample documents into the test DB."""

    def _populate(rows):
        _SqliteDocument.delete().execute()
        for row in rows:
            _SqliteDocument.create(**row)
        return sqlite_db

    return _populate


@pytest.fixture()
def call_with_sqlite(sqlite_db, populate_documents, monkeypatch):
    """Return a helper that runs get_parsing_status_by_kb_ids with real SQLite queries."""

    def _call(rows, kb_ids):
        populate_documents(rows)
        monkeypatch.setattr(DocumentService, "model", _SqliteDocument)
        fn = DocumentService.get_parsing_status_by_kb_ids.__func__.__wrapped__
        return fn(DocumentService, kb_ids)

    return _call


_ALL_STATUS_FIELDS = frozenset(["unstart_count", "running_count", "cancel_count", "done_count", "fail_count"])


@pytest.mark.p2
class TestGetParsingStatusByKbIds:
    def test_empty_kb_ids_returns_empty_dict(self, call_with_sqlite):
        result = call_with_sqlite([], [])
        assert result == {}

    def test_single_kb_id_no_documents(self, call_with_sqlite):
        result = call_with_sqlite(rows=[], kb_ids=["kb-1"])

        assert set(result.keys()) == {"kb-1"}
        assert set(result["kb-1"].keys()) == _ALL_STATUS_FIELDS
        assert all(v == 0 for v in result["kb-1"].values())

    def test_single_kb_id_all_five_statuses(self, call_with_sqlite):
        rows = [
            {"id": f"doc-{i}", "kb_id": "kb-1", "run": TaskStatus.UNSTART.value}
            for i in range(3)
        ] + [
            {"id": f"doc-running-{i}", "kb_id": "kb-1", "run": TaskStatus.RUNNING.value}
            for i in range(1)
        ] + [
            {"id": f"doc-cancel-{i}", "kb_id": "kb-1", "run": TaskStatus.CANCEL.value}
            for i in range(2)
        ] + [
            {"id": f"doc-done-{i}", "kb_id": "kb-1", "run": TaskStatus.DONE.value}
            for i in range(10)
        ] + [
            {"id": f"doc-fail-{i}", "kb_id": "kb-1", "run": TaskStatus.FAIL.value}
            for i in range(4)
        ]
        result = call_with_sqlite(rows=rows, kb_ids=["kb-1"])

        assert result["kb-1"]["unstart_count"] == 3
        assert result["kb-1"]["running_count"] == 1
        assert result["kb-1"]["cancel_count"] == 2
        assert result["kb-1"]["done_count"] == 10
        assert result["kb-1"]["fail_count"] == 4

    def test_multiple_kb_ids_aggregated_separately(self, call_with_sqlite):
        rows = (
            [{"id": f"doc-a-done-{i}", "kb_id": "kb-a", "run": TaskStatus.DONE.value} for i in range(5)]
            + [{"id": f"doc-a-fail-{i}", "kb_id": "kb-a", "run": TaskStatus.FAIL.value} for i in range(1)]
            + [{"id": f"doc-b-unstart-{i}", "kb_id": "kb-b", "run": TaskStatus.UNSTART.value} for i in range(7)]
            + [{"id": f"doc-b-done-{i}", "kb_id": "kb-b", "run": TaskStatus.DONE.value} for i in range(2)]
        )
        result = call_with_sqlite(rows=rows, kb_ids=["kb-a", "kb-b"])

        assert set(result.keys()) == {"kb-a", "kb-b"}

        assert result["kb-a"]["done_count"] == 5
        assert result["kb-a"]["fail_count"] == 1
        assert result["kb-a"]["unstart_count"] == 0
        assert result["kb-a"]["running_count"] == 0
        assert result["kb-a"]["cancel_count"] == 0

        assert result["kb-b"]["unstart_count"] == 7
        assert result["kb-b"]["done_count"] == 2
        assert result["kb-b"]["fail_count"] == 0

    def test_unknown_run_value_ignored(self, call_with_sqlite):
        rows = [
            {"id": "doc-1", "kb_id": "kb-1", "run": "9"},
            {"id": "doc-2", "kb_id": "kb-1", "run": TaskStatus.DONE.value},
        ]
        result = call_with_sqlite(rows=rows, kb_ids=["kb-1"])

        assert result["kb-1"]["done_count"] == 1
        assert all(result["kb-1"][f] == 0 for f in _ALL_STATUS_FIELDS - {"done_count"})

    def test_row_with_unrequested_kb_id_is_filtered_out(self, call_with_sqlite):
        rows = [
            {"id": "doc-1", "kb_id": "kb-requested", "run": TaskStatus.DONE.value},
            {"id": "doc-2", "kb_id": "kb-unexpected", "run": TaskStatus.DONE.value},
        ]
        result = call_with_sqlite(rows=rows, kb_ids=["kb-requested"])

        assert "kb-unexpected" not in result
        assert result["kb-requested"]["done_count"] == 1

    def test_cnt_is_cast_to_int(self, call_with_sqlite):
        rows = [
            {"id": "doc-1", "kb_id": "kb-1", "run": TaskStatus.RUNNING.value},
        ]
        result = call_with_sqlite(rows=rows, kb_ids=["kb-1"])

        assert result["kb-1"]["running_count"] == 1
        assert isinstance(result["kb-1"]["running_count"], int)

    def test_run_value_as_integer_is_handled(self, call_with_sqlite):
        rows = [
            {"id": "doc-1", "kb_id": "kb-1", "run": str(int(TaskStatus.DONE.value))},
        ]
        result = call_with_sqlite(rows=rows, kb_ids=["kb-1"])

        assert result["kb-1"]["done_count"] == 1

    def test_all_five_fields_initialised_to_zero(self, call_with_sqlite):
        result = call_with_sqlite(rows=[], kb_ids=["kb-empty"])

        assert result["kb-empty"] == {
            "unstart_count": 0,
            "running_count": 0,
            "cancel_count": 0,
            "done_count": 0,
            "fail_count": 0,
        }

    def test_requested_kb_ids_all_present_in_result(self, call_with_sqlite):
        rows = [
            {"id": "doc-1", "kb_id": "kb-with-data", "run": TaskStatus.DONE.value},
        ]
        result = call_with_sqlite(rows=rows, kb_ids=["kb-with-data", "kb-empty-1", "kb-empty-2"])

        assert set(result.keys()) == {"kb-with-data", "kb-empty-1", "kb-empty-2"}
        assert result["kb-empty-1"] == {f: 0 for f in _ALL_STATUS_FIELDS}
        assert result["kb-empty-2"] == {f: 0 for f in _ALL_STATUS_FIELDS}

    def test_schedule_status_is_not_mapped(self, call_with_sqlite):
        rows = [
            {"id": "doc-1", "kb_id": "kb-1", "run": TaskStatus.SCHEDULE.value},
            {"id": "doc-2", "kb_id": "kb-1", "run": TaskStatus.DONE.value},
        ]
        result = call_with_sqlite(rows=rows, kb_ids=["kb-1"])

        assert result["kb-1"]["done_count"] == 1
        assert "schedule_count" not in result["kb-1"]
        assert all(result["kb-1"][f] == 0 for f in _ALL_STATUS_FIELDS - {"done_count"})
