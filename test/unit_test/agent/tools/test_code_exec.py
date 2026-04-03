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
import base64
import json
from unittest.mock import patch

from agent.canvas import Canvas
from agent.tools.code_exec import CodeExec, CodeExecParam, CodeExecutionRequest, Language


class MockCanvas(Canvas):
    def __init__(self):
        dsl = json.dumps({"components": {}, "path": [], "history": []})
        super().__init__(dsl, tenant_id="test_tenant")
        self._references = []
        self._canceled = False

    def load(self):
        pass

    def is_canceled(self):
        return self._canceled

    def get_component_name(self, component_id):
        return "code_exec"

    def add_reference(self, chunks, aggs):
        self._references.extend(chunks)

    def get_variable_value(self, var_name):
        return self.variables.get(var_name)

    def set_variable_value(self, var_name, value):
        self.variables[var_name] = value

    def get_tenant_id(self):
        return self._tenant_id


class TestCodeExecutionRequest:
    """Tests for CodeExecutionRequest model."""

    def test_code_execution_request_valid(self):
        code = "def main(): return {}"
        code_b64 = base64.b64encode(code.encode()).decode()

        request = CodeExecutionRequest(code_b64=code_b64, language="python")

        assert request.code_b64 == code_b64
        assert request.language == "python"
        assert request.arguments == {}

    def test_code_execution_request_with_arguments(self):
        code = "def main(arg1): return {'result': arg1}"
        code_b64 = base64.b64encode(code.encode()).decode()

        request = CodeExecutionRequest(code_b64=code_b64, language="python", arguments={"arg1": "test"})

        assert request.arguments == {"arg1": "test"}

    def test_code_execution_request_invalid_base64(self):
        with pytest.raises(ValueError, match="Invalid base64 encoding"):
            CodeExecutionRequest(code_b64="not-valid-base64!!!", language="python")

    def test_code_execution_request_language_normalization(self):
        code = "def main(): return {}"
        code_b64 = base64.b64encode(code.encode()).decode()

        request = CodeExecutionRequest(code_b64=code_b64, language="python3")
        assert request.language == "python"

        request = CodeExecutionRequest(code_b64=code_b64, language="javascript")
        assert request.language == "nodejs"

    def test_code_execution_request_invalid_language(self):
        code = "def main(): return {}"
        code_b64 = base64.b64encode(code.encode()).decode()

        with pytest.raises(ValueError, match="Unsupported language"):
            CodeExecutionRequest(code_b64=code_b64, language="ruby")


class TestLanguage:
    """Tests for Language enum."""

    def test_language_values(self):
        assert Language.PYTHON.value == "python"
        assert Language.NODEJS.value == "nodejs"


class TestCodeExecParam:
    """Tests for CodeExecParam class."""

    def test_code_exec_param_init(self):
        param = CodeExecParam()

        assert param.meta["name"] == "execute_code"
        assert param.lang == "python"
        assert "def main" in param.script
        assert param.arguments == {}

    def test_code_exec_param_check_valid(self):
        param = CodeExecParam()
        param.check()

        assert param.lang == "python"

    def test_code_exec_param_check_invalid_language(self):
        param = CodeExecParam()
        param.lang = "ruby"

        with pytest.raises(ValueError):
            param.check()

    def test_code_exec_param_check_empty_script(self):
        param = CodeExecParam()
        param.script = ""

        with pytest.raises(ValueError):
            param.check()

    def test_code_exec_param_get_input_form(self):
        param = CodeExecParam()
        param.arguments = {"arg1": "value1", "arg2": "value2"}

        input_form = param.get_input_form()

        assert "arg1" in input_form
        assert "arg2" in input_form
        assert input_form["arg1"]["type"] == "line"

    def test_code_exec_param_outputs_structure(self):
        param = CodeExecParam()

        assert "result" in param.outputs
        assert param.outputs["result"]["type"] == "object"


class TestCodeExec:
    """Tests for CodeExec class."""

    def test_code_exec_init(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        assert code_exec._canvas == canvas
        assert code_exec._id == "test_id"
        assert code_exec.component_name == "CodeExec"

    def test_code_exec_thoughts(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)
        thoughts = code_exec.thoughts()

        assert "script" in thoughts.lower() or "Running" in thoughts


class TestCodeExecProcessExecutionResult:
    """Tests for _process_execution_result method."""

    def test_process_execution_result_stderr_only(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)
        code_exec._process_execution_result("", "Error message", "source")

        assert code_exec.output("_ERROR") == "Error message"

    def test_process_execution_result_stdout_dict(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)
        stdout_json = json.dumps({"result": "success", "value": 42})

        code_exec._process_execution_result(stdout_json, None, "test_source")

        assert code_exec.output("result") == "success"
        assert code_exec.output("value") == 42

    def test_process_execution_result_stdout_list(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)
        stdout_json = json.dumps(["item1", "item2", "item3"])

        code_exec._process_execution_result(stdout_json, None, "test_source")

        output = code_exec.output("content")
        assert output is not None

    def test_process_execution_result_stdout_string(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        code_exec._process_execution_result("plain text output", None, "test_source")

        output = code_exec.output("content")
        assert "plain text output" in output

    def test_process_execution_result_with_artifacts(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        artifacts = [{"name": "chart.png", "content_b64": "iVBORw0KGg==", "mime_type": "image/png", "size": 100}]

        with patch.object(code_exec, "_upload_artifacts", return_value=[{"name": "chart.png", "url": "/v1/document/artifact/abc.png"}]):
            code_exec._process_execution_result('{"result": "ok"}', None, "test", artifacts)

        assert code_exec.output("_ATTACHMENT_CONTENT") is not None


class TestCodeExecDeserialization:
    """Tests for stdout deserialization methods."""

    def test_deserialize_stdout_json(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._deserialize_stdout('{"key": "value"}')
        assert result == {"key": "value"}

    def test_deserialize_stdout_literal_eval(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._deserialize_stdout("{'key': 'value'}")
        assert result == {"key": "value"}

    def test_deserialize_stdout_plain_string(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._deserialize_stdout("plain text")
        assert result == "plain text"

    def test_deserialize_stdout_empty(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._deserialize_stdout("")
        assert result == ""


class TestCodeExecOutputCoercion:
    """Tests for output value coercion."""

    def test_coerce_string(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._coerce_output_value(123, "string")
        assert result == "123"

    def test_coerce_number_from_string(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._coerce_output_value("42.5", "number")
        assert result == 42.5

    def test_coerce_boolean_from_string(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        assert code_exec._coerce_output_value("true", "boolean") is True
        assert code_exec._coerce_output_value("false", "boolean") is False
        assert code_exec._coerce_output_value("yes", "boolean") is True

    def test_coerce_array_string(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._coerce_output_value(["a", "b", "c"], "array<string>")
        assert result == ["a", "b", "c"]

    def test_coerce_array_number(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._coerce_output_value([1, 2, 3], "array<number>")
        assert result == [1.0, 2.0, 3.0]

    def test_coerce_object(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._coerce_output_value('{"a": 1}', "object")
        assert result == {"a": 1}

    def test_coerce_no_type(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._coerce_output_value({"test": "value"}, None)
        assert result == {"test": "value"}


class TestCodeExecPathResolution:
    """Tests for _get_by_path method."""

    def test_get_by_path_nested_dict(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        data = {"a": {"b": {"c": "deep_value"}}}
        result = code_exec._get_by_path(data, "a.b.c")
        assert result == "deep_value"

    def test_get_by_path_list_index(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        data = {"items": ["first", "second", "third"]}
        result = code_exec._get_by_path(data, "items.1")
        assert result == "second"

    def test_get_by_path_empty_path(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._get_by_path({"key": "value"}, "")
        assert result is None


class TestCodeExecBuildContent:
    """Tests for content building methods."""

    def test_build_content_text_string(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._build_content_text("plain text")
        assert result == "plain text"

    def test_build_content_text_dict(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._build_content_text({"key": "value"})
        assert "key" in result
        assert "value" in result

    def test_build_content_text_list(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec._build_content_text(["a", "b", "c"])
        assert "a" in result
        assert "b" in result


class TestCodeExecAttachmentHandling:
    """Tests for attachment handling methods."""

    def test_normalize_attachment_type_image(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        assert code_exec._normalize_attachment_type("image.png", "image/png") == "image"
        assert code_exec._normalize_attachment_type("photo.jpg", "image/jpeg") == "image"

    def test_normalize_attachment_type_pdf(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        assert code_exec._normalize_attachment_type("document.pdf", "application/pdf") == "pdf"

    def test_normalize_attachment_type_csv(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        assert code_exec._normalize_attachment_type("data.csv", "text/csv") == "csv"

    def test_normalize_attachment_type_json(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        assert code_exec._normalize_attachment_type("data.json", "application/json") == "json"

    def test_normalize_attachment_type_by_extension(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        assert code_exec._normalize_attachment_type("data.txt", "") == "txt"
        assert code_exec._normalize_attachment_type("", "") == "file"


class TestCodeExecEncodeCode:
    """Tests for code encoding."""

    def test_encode_code(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        code = "def main():\n    return 'hello'"
        encoded = code_exec._encode_code(code)

        assert encoded == base64.b64encode(code.encode()).decode()

        decoded = base64.b64decode(encoded).decode()
        assert decoded == code


class TestCodeExecPopulateOutputs:
    """Tests for _populate_outputs method."""

    def test_populate_outputs_dict(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        code_exec._populate_outputs({"result": "success", "count": 42}, '{"result": "success", "count": 42}')

        assert code_exec.output("result") == "success"
        assert code_exec.output("count") == 42

    def test_populate_outputs_list(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        code_exec._populate_outputs(["item1", "item2"], '["item1", "item2"]')

        assert code_exec.output("content") == "item1"

    def test_populate_outputs_scalar(self):
        canvas = MockCanvas()
        param = CodeExecParam()

        code_exec = CodeExec(canvas, "test_id", param)

        code_exec._populate_outputs("just a string", "just a string")

        assert code_exec.output("content") == "just a string"


class TestCodeExecEdgeCases:
    """Tests for edge cases."""

    def test_invoke_with_cancel(self):
        canvas = MockCanvas()
        canvas._canceled = True

        param = CodeExecParam()
        code_exec = CodeExec(canvas, "test_id", param)

        result = code_exec.invoke(lang="python", script="def main(): return {}")

        assert result is None
