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
import warnings

import pytest
import peewee
from playhouse.sqlite_ext import SqliteExtDatabase

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message="\\[Errno 13\\] Permission denied\\.  joblib will operate in serial mode",
    category=UserWarning,
)

import api.db.services.document_service as document_service


class _SqliteDocument(peewee.Model):
    """SQLite version of Document model for testing get_list and get_by_kb_id."""

    id = peewee.CharField(max_length=32, primary_key=True)
    kb_id = peewee.CharField(max_length=256, null=False, index=True)
    name = peewee.CharField(max_length=255, null=True, index=True)
    suffix = peewee.CharField(max_length=32, null=False, default="txt", index=True)
    run = peewee.CharField(max_length=1, null=True, default="0", index=True)
    type = peewee.CharField(max_length=32, null=False, index=True)
    created_by = peewee.CharField(max_length=32, null=False, default="system", index=True)
    pipeline_id = peewee.CharField(max_length=32, null=True, index=True)
    create_time = peewee.BigIntegerField(null=True, index=True)

    class Meta:
        table_name = "document"
        database = None

    @classmethod
    def getter_by(cls, field_name):
        return getattr(cls, field_name)


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


class _SqliteFile2Document(peewee.Model):
    """SQLite version of File2Document model."""

    id = peewee.CharField(max_length=32, primary_key=True)
    file_id = peewee.CharField(max_length=32, null=True, index=True)
    document_id = peewee.CharField(max_length=32, null=True, index=True)

    class Meta:
        table_name = "file2document"
        database = None


class _SqliteUserCanvas(peewee.Model):
    id = peewee.CharField(max_length=32, primary_key=True)
    title = peewee.CharField(max_length=255, null=True)
    canvas_category = peewee.CharField(max_length=32, null=True, index=True)

    class Meta:
        table_name = "user_canvas"
        database = None


class _SqliteUser(peewee.Model):
    id = peewee.CharField(max_length=32, primary_key=True)
    nickname = peewee.CharField(max_length=255, null=True)

    class Meta:
        table_name = "user"
        database = None


@pytest.fixture
def sqlite_db():
    """Create in-memory SQLite database with schema."""
    db = SqliteExtDatabase(":memory:")
    _SqliteDocument._meta.database = db
    _SqliteFile._meta.database = db
    _SqliteFile2Document._meta.database = db
    _SqliteUserCanvas._meta.database = db
    _SqliteUser._meta.database = db
    db.create_tables([_SqliteDocument, _SqliteFile, _SqliteFile2Document, _SqliteUserCanvas, _SqliteUser])
    yield db
    db.close()


@pytest.fixture
def sample_documents(sqlite_db):
    """Insert sample documents into the test DB."""
    _SqliteUser.create(id="user-1", nickname="User One")
    docs = [
        _SqliteDocument.create(
            id=f"doc-{i}",
            kb_id="kb-1",
            name=f"doc-{i}.txt",
            type="txt",
            created_by="user-1",
            run="1",
            pipeline_id=None,
            create_time=1000 - i,
        )
        for i in range(1, 6)
    ]
    for i in range(1, 6):
        _SqliteFile.create(
            id=f"file-{i}",
            parent_id="kb-1",
            tenant_id="tenant-1",
            created_by="user-1",
            name=f"doc-{i}.txt",
            location=f"/tmp/doc-{i}.txt",
            size=100,
            type="txt",
            source_type="",
        )
        _SqliteFile2Document.create(id=f"f2d-{i}", file_id=f"file-{i}", document_id=f"doc-{i}")
    return docs


@pytest.fixture
def metadata_calls():
    """Track calls to get_metadata_for_documents."""
    calls = []

    def _fake_get_metadata_for_documents(cls, doc_ids, kb_id):
        calls.append((doc_ids, kb_id))
        return {doc_id: {"source_url": f"url-{doc_id}"} for doc_id in (doc_ids or [])}

    return calls, _fake_get_metadata_for_documents


@pytest.fixture
def setup_document_service(sqlite_db, sample_documents, metadata_calls, monkeypatch):
    """Setup DocumentService to use SQLite models."""
    calls, fake_metadata = metadata_calls

    monkeypatch.setattr(document_service.DB, "connect", lambda *args, **kwargs: None)
    monkeypatch.setattr(document_service.DB, "close", lambda *args, **kwargs: None)
    monkeypatch.setattr(document_service.DocumentService, "model", _SqliteDocument)
    monkeypatch.setattr(document_service, "UserCanvas", _SqliteUserCanvas)
    monkeypatch.setattr(document_service, "User", _SqliteUser)
    monkeypatch.setattr(
        document_service.DocumentService,
        "get_cls_model_fields",
        classmethod(lambda cls: [cls.model.id, cls.model.kb_id, cls.model.name, cls.model.create_time]),
    )
    monkeypatch.setattr(
        document_service.DocMetadataService,
        "get_metadata_for_documents",
        classmethod(fake_metadata),
    )

    return calls


@pytest.mark.p2
def test_get_list_fetches_metadata_for_page_document_ids(setup_document_service, sample_documents):
    calls = setup_document_service
    docs, count = document_service.DocumentService.get_list(
        "kb-1",
        1,
        2,
        "create_time",
        True,
        "",
        None,
        None,
    )

    assert count == 5
    assert [doc["id"] for doc in docs] == ["doc-1", "doc-2"]
    assert docs[0]["meta_fields"]["source_url"] == "url-doc-1"
    assert calls == [(["doc-1", "doc-2"], "kb-1")]


def test_get_by_kb_id_fetches_metadata_for_page_document_ids(setup_document_service, sample_documents):
    calls = setup_document_service
    docs, count = document_service.DocumentService.get_by_kb_id(
        "kb-1",
        2,
        1,
        "create_time",
        True,
        "",
        [],
        [],
        [],
        return_empty_metadata=False,
    )

    assert count == 5
    assert [doc["id"] for doc in docs] == ["doc-2"]
    assert docs[0]["meta_fields"]["source_url"] == "url-doc-2"
    assert calls == [(["doc-2"], "kb-1")]


@pytest.mark.p2
def test_get_by_kb_id_return_empty_metadata_keeps_dataset_wide_lookup(setup_document_service, sample_documents, monkeypatch):
    calls = setup_document_service

    def _fake_get_metadata_for_documents(cls, doc_ids, kb_id):
        calls.append((doc_ids, kb_id))
        return {"doc-1": {"source_url": "url-doc-1"}} if doc_ids is None else {}

    monkeypatch.setattr(
        document_service.DocMetadataService,
        "get_metadata_for_documents",
        classmethod(_fake_get_metadata_for_documents),
    )

    docs, count = document_service.DocumentService.get_by_kb_id(
        "kb-1",
        1,
        2,
        "create_time",
        True,
        "",
        [],
        [],
        [],
        return_empty_metadata=True,
    )

    assert count == 4
    assert docs[0]["meta_fields"] == {}
    assert calls == [(None, "kb-1")]
