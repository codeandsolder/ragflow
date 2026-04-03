# Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import pytest

from agent.canvas import Canvas


class TestDSLParsing:
    """Tests for DSL JSON parsing and component graph conversion."""

    def _create_minimal_dsl(self) -> dict:
        return {
            "components": {
                "begin": {
                    "obj": {"component_name": "Begin", "params": {}},
                    "downstream": [],
                    "upstream": [],
                }
            },
            "history": [],
            "path": ["begin"],
            "retrieval": {"chunks": [], "doc_aggs": []},
        }

    def test_parse_minimal_dsl(self):
        minimal_dsl = self._create_minimal_dsl()
        canvas = Canvas(json.dumps(minimal_dsl), tenant_id="test_tenant")
        assert "begin" in canvas.components
        assert canvas.components["begin"]["obj"].component_name == "Begin"

    def test_parse_dsl_with_globals(self):
        dsl = self._create_minimal_dsl()
        dsl["globals"] = {
            "sys.query": "test query",
            "sys.user_id": "user123",
            "sys.conversation_turns": 5,
        }
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert canvas.globals["sys.query"] == "test query"
        assert canvas.globals["sys.user_id"] == "user123"

    def test_parse_dsl_with_history(self):
        dsl = self._create_minimal_dsl()
        dsl["history"] = [
            ("user", "Hello"),
            ("assistant", "Hi there!"),
        ]
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert len(canvas.history) == 2
        assert list(canvas.history[0]) == ["user", "Hello"]

    def test_parse_dsl_invalid_json_raises_error(self):
        with pytest.raises((json.JSONDecodeError, ValueError)):
            Canvas("{invalid json}", tenant_id="test_tenant")

    def test_parse_dsl_missing_components_raises_error(self):
        dsl = {"history": [], "path": [], "retrieval": {}}
        with pytest.raises(KeyError):
            Canvas(json.dumps(dsl), tenant_id="test_tenant")
