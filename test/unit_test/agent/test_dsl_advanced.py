# Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import pytest

from agent.canvas import Canvas


class TestDSLVariableResolution:
    """Tests for variable resolution in DSL parsing."""

    def _create_dsl_with_variables(self) -> dict:
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
            "globals": {"sys.query": "initial query", "custom_var": "value"},
            "variables": {"var1": {"type": "string", "value": "test"}},
        }

    def test_globals_initialization_from_dsl(self):
        dsl = self._create_dsl_with_variables()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert canvas.globals["sys.query"] == "initial query"
        assert canvas.globals["custom_var"] == "value"

    def test_variables_initialization_from_dsl(self):
        dsl = self._create_dsl_with_variables()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert "var1" in canvas.variables

    def test_missing_globals_defaults(self):
        dsl = {
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
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        assert "sys.query" in canvas.globals
        assert canvas.globals["sys.query"] == ""
        assert "sys.history" in canvas.globals


class TestDSLSerialization:
    """Tests for DSL serialization back to JSON."""

    def test_serialize_to_json(self):
        dsl = self._create_minimal_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        serialized = str(canvas)
        parsed = json.loads(serialized)
        assert "components" in parsed
        assert "begin" in parsed["components"]

    def test_serialize_preserves_history(self):
        dsl = self._create_minimal_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        canvas.history.append(("user", "test message"))
        serialized = str(canvas)
        parsed = json.loads(serialized)
        assert parsed["history"] == [("user", "test message")]

    def test_serialize_preserves_path(self):
        dsl = self._create_minimal_dsl()
        canvas = Canvas(json.dumps(dsl), tenant_id="test_tenant")
        canvas.path.append("new_component")
        serialized = str(canvas)
        parsed = json.loads(serialized)
        assert "new_component" in parsed["path"]
