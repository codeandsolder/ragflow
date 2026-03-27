#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
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

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_tenant():
    tenant = Mock()
    tenant.tenant_id = "tenant-123"
    tenant.name = "Test Tenant"
    return tenant


@pytest.fixture
def mock_user():
    user = Mock()
    user.id = "user-123"
    user.email = "test@example.com"
    user.nickname = "Test User"
    user.tenant_id = "tenant-123"
    user.is_active = "1"
    return user


@pytest.fixture
def mock_knowledgebase():
    kb = Mock()
    kb.id = "kb-123"
    kb.name = "Test Knowledge Base"
    kb.tenant_id = "tenant-123"
    kb.parser_id = "naive"
    kb.parser_config = {"chunk_token_num": 512}
    kb.created_by = "user-123"
    kb.create_time = datetime.now()
    kb.update_time = datetime.now()
    kb.to_dict.return_value = {
        "id": "kb-123",
        "name": "Test Knowledge Base",
        "tenant_id": "tenant-123",
        "parser_id": "naive",
        "parser_config": {"chunk_token_num": 512},
    }
    return kb


@pytest.fixture
def mock_document():
    doc = Mock()
    doc.id = "doc-123"
    doc.name = "test.pdf"
    doc.kb_id = "kb-123"
    doc.type = "pdf"
    doc.status = "1"
    doc.size = 1024
    doc.chunk_num = 0
    doc.token_num = 0
    doc.run = "1"
    doc.to_dict.return_value = {
        "id": "doc-123",
        "name": "test.pdf",
        "kb_id": "kb-123",
        "type": "pdf",
    }
    return doc
