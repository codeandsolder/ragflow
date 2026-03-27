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
"""Test utilities for common testing patterns."""

import asyncio
import base64
import json
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock


class TestHelper:
    """Helper class for common test operations."""

    @staticmethod
    def create_temp_file(content, suffix=""):
        """Create a temporary file with content.

        Args:
            content: File content.
            suffix: File suffix.

        Returns:
            Path to temporary file.
        """
        file_path = Path(os.path.join(os.path.dirname(__file__), "temp_files", f"test_{suffix}"))
        file_path.parent.mkdir(exist_ok=True)
        file_path.write_text(content)
        return file_path

    @staticmethod
    def create_temp_json(data, suffix=""):
        """Create a temporary JSON file.

        Args:
            data: Data to write as JSON.
            suffix: File suffix.

        Returns:
            Path to temporary JSON file.
        """
        file_path = Path(os.path.join(os.path.dirname(__file__), "temp_files", f"test_{suffix}.json"))
        file_path.parent.mkdir(exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(data, f)
        return file_path

    @staticmethod
    def create_mock_container(language="python"):
        """Create a mock container for testing.

        Args:
            language: Language type ("python" or "nodejs").

        Returns:
            Mock container name.
        """
        return f"sandbox_{language}_{TestHelper._get_next_container_id()}"

    @staticmethod
    def _get_next_container_id():
        """Get next container ID."""
        if not hasattr(TestHelper, "_container_counter"):
            TestHelper._container_counter = 0
        TestHelper._container_counter += 1
        return TestHelper._container_counter

    @staticmethod
    def create_mock_execution_request(code, language="python", args=None):
        """Create a mock execution request.

        Args:
            code: Code to execute (string or bytes).
            language: Programming language.
            args: Arguments for the code.

        Returns:
            Mock CodeExecutionRequest.
        """
        from agent.sandbox.executor_manager.models.schemas import CodeExecutionRequest
        from agent.sandbox.executor_manager.models.enums import SupportLanguage

        if isinstance(code, str):
            code = code.encode()

        return CodeExecutionRequest(code_b64=base64.b64encode(code).decode(), language=SupportLanguage.PYTHON if language == "python" else SupportLanguage.NODEJS, arguments=args)

    @staticmethod
    def create_mock_result(status="success", stdout="", stderr="", exit_code=0):
        """Create a mock execution result.

        Args:
            status: Result status.
            stdout: Standard output.
            stderr: Standard error.
            exit_code: Exit code.

        Returns:
            Mock CodeExecutionResult.
        """
        from agent.sandbox.executor_manager.models.schemas import CodeExecutionResult
        from agent.sandbox.executor_manager.models.enums import ResultStatus

        return CodeExecutionResult(status=getattr(ResultStatus, status.upper()), stdout=stdout, stderr=stderr, exit_code=exit_code)


class AsyncTestHelper:
    """Helper class for async test operations."""

    @staticmethod
    async def run_with_timeout(coro, timeout=5):
        """Run coroutine with timeout.

        Args:
            coro: Coroutine to run.
            timeout: Timeout in seconds.

        Returns:
            Result of coroutine.
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            pytest.fail(f"Coroutine timed out after {timeout} seconds")

    @staticmethod
    async def create_mock_container_and_queue(language="python"):
        """Create mock container and add to queue.

        Args:
            language: Language type.

        Returns:
            Mock container name.
        """
        from agent.sandbox.executor_manager.core.container import _CONTAINER_QUEUES
        from agent.sandbox.executor_manager.models.enums import SupportLanguage

        container = TestHelper.create_mock_container(language)
        _CONTAINER_QUEUES[SupportLanguage.PYTHON if language == "python" else SupportLanguage.NODEJS].put(container)
        return container

    @staticmethod
    async def mock_docker_command(side_effect=None):
        """Create mock for docker commands.

        Args:
            side_effect: Side effect for mock.

        Returns:
            Context manager for patching.
        """
        return patch("agent.sandbox.executor_manager.utils.common.async_run_command", side_effect=side_effect)


class MockData:
    """Class for creating mock data."""

    @staticmethod
    def create_mock_user(user_id="user-1", tenant_id="tenant-1"):
        """Create mock user object.

        Args:
            user_id: User ID.
            tenant_id: Tenant ID.

        Returns:
            Mock user object.
        """
        user = MagicMock()
        user.id = user_id
        user.tenant_id = tenant_id
        return user

    @staticmethod
    def create_mock_dialog(dialog_id="dialog-1", tenant_id="tenant-1"):
        """Create mock dialog object.

        Args:
            dialog_id: Dialog ID.
            tenant_id: Tenant ID.

        Returns:
            Mock dialog object.
        """
        dialog = MagicMock()
        dialog.id = dialog_id
        dialog.tenant_id = tenant_id
        dialog.icon = "avatar.png"
        dialog.prompt_config = {"prologue": "hello"}
        dialog.llm_id = ""
        dialog.llm_setting = {}
        return dialog

    @staticmethod
    def create_mock_conversation(conv_id="conv-1", dialog_id="dialog-1"):
        """Create mock conversation object.

        Args:
            conv_id: Conversation ID.
            dialog_id: Dialog ID.

        Returns:
            Mock conversation object.
        """
        conv = MagicMock()
        conv.id = conv_id
        conv.dialog_id = dialog_id
        conv.message = []
        conv.reference = []
        return conv

    @staticmethod
    def create_mock_api_response(data=None, code=0, message="success"):
        """Create mock API response.

        Args:
            data: Response data.
            code: Response code.
            message: Response message.

        Returns:
            Mock API response dict.
        """
        return {"code": code, "data": data, "message": message}


class TestValidator:
    """Class for validating test results."""

    @staticmethod
    def validate_embedding(embedding, expected_length=None):
        """Validate embedding vector.

        Args:
            embedding: Embedding vector.
            expected_length: Expected length of embedding.

        Raises:
            AssertionError: If validation fails.
        """
        import numpy as np

        assert embedding is not None, "Embedding should not be None"
        assert len(embedding) > 0, "Embedding should have non-zero length"

        if isinstance(embedding, np.ndarray):
            assert embedding.ndim == 1, f"Embedding should be 1D, got {embedding.ndim}D"
        else:
            assert isinstance(embedding, (list, tuple)), f"Embedding should be list/tuple/ndarray, got {type(embedding)}"

        if expected_length is not None:
            assert len(embedding) == expected_length, f"Expected embedding length {expected_length}, got {len(embedding)}"

    @staticmethod
    def validate_chunks(chunks, min_count=1, max_count=None):
        """Validate chunks list.

        Args:
            chunks: List of chunks.
            min_count: Minimum expected chunks.
            max_count: Maximum expected chunks.

        Raises:
            AssertionError: If validation fails.
        """
        assert chunks is not None, "Chunks should not be None"
        assert len(chunks) >= min_count, f"Expected at least {min_count} chunks, got {len(chunks)}"

        if max_count is not None:
            assert len(chunks) <= max_count, f"Expected at most {max_count} chunks, got {len(chunks)}"

        for i, chunk in enumerate(chunks):
            assert "text" in chunk, f"Chunk {i} missing 'text' field"
            assert chunk["text"], f"Chunk {i} has empty text"

    @staticmethod
    def validate_token_count(actual, expected, tolerance=0.2):
        """Validate token count with tolerance.

        Args:
            actual: Actual token count.
            expected: Expected token count.
            tolerance: Tolerance as fraction.

        Raises:
            AssertionError: If validation fails.
        """
        lower = expected * (1 - tolerance)
        upper = expected * (1 + tolerance)
        assert lower <= actual <= upper, f"Token count {actual} outside range [{lower:.0f}, {upper:.0f}]"


class TestBuilder:
    """Class for building test data structures."""

    @staticmethod
    def build_mock_api_response(data=None, code=0, message="success"):
        """Build mock API response.

        Args:
            data: Response data.
            code: Response code.
            message: Response message.

        Returns:
            Mock API response dict.
        """
        return MockData.create_mock_api_response(data, code, message)

    @staticmethod
    def build_mock_chat_message(content, role="user", id="m-1"):
        """Build mock chat message.

        Args:
            content: Message content.
            role: Message role (user/assistant/system).
            id: Message ID.

        Returns:
            Mock chat message dict.
        """
        return {"role": role, "content": content, "id": id}

    @staticmethod
    def build_mock_request_json(payload):
        """Build mock request JSON.

        Args:
            payload: Payload data.

        Returns:
            Mock request JSON.
        """
        return MagicMock(return_value=AsyncMock(return_value=payload))


class TestScenario:
    """Class for common test scenarios."""

    @staticmethod
    def create_ratelimit_scenario(model, max_retries=3):
        """Create a rate limit scenario.

        Args:
            model: Model instance.
            max_retries: Number of retries before success.

        Returns:
            Side effect for mocking.
        """

        class RateLimitSideEffect:
            def __init__(self):
                self.call_count = 0

            def __call__(self, *args, **kwargs):
                self.call_count += 1
                if self.call_count <= max_retries:
                    raise Exception("Rate limit exceeded: 429")
                return "success"

        return RateLimitSideEffect()

    @staticmethod
    def create_server_error_scenario(model, max_retries=3):
        """Create a server error scenario.

        Args:
            model: Model instance.
            max_retries: Number of retries before success.

        Returns:
            Side effect for mocking.
        """

        class ServerErrorSideEffect:
            def __init__(self):
                self.call_count = 0

            def __call__(self, *args, **kwargs):
                self.call_count += 1
                if self.call_count <= max_retries:
                    raise Exception("Server error: 500 Internal Server Error")
                return "success"

        return ServerErrorSideEffect()

    @staticmethod
    def create_timeout_scenario(model, max_retries=3):
        """Create a timeout scenario.

        Args:
            model: Model instance.
            max_retries: Number of retries before success.

        Returns:
            Side effect for mocking.
        """

        class TimeoutSideEffect:
            def __init__(self):
                self.call_count = 0

            def __call__(self, *args, **kwargs):
                self.call_count += 1
                if self.call_count <= max_retries:
                    raise Exception("Request timed out after 30 seconds")
                return "success"

        return TimeoutSideEffect()


class TestMock:
    """Class for creating mock objects."""

    @staticmethod
    def create_mock_openai_client():
        """Create mock OpenAI client.

        Returns:
            Mock client object.
        """
        return MagicMock()

    @staticmethod
    def create_mock_ollama_client():
        """Create mock Ollama client.

        Returns:
            Mock client object.
        """
        return MagicMock()

    @staticmethod
    def create_mock_chat_model():
        """Create mock chat model.

        Returns:
            Mock chat model object.
        """
        return MagicMock()

    @staticmethod
    def create_mock_embedding_model():
        """Create mock embedding model.

        Returns:
            Mock embedding model object.
        """
        return MagicMock()


# Global test utilities
TEST_HELPER = TestHelper()
ASYNC_TEST_HELPER = AsyncTestHelper()
MOCK_DATA = MockData()
TEST_VALIDATOR = TestValidator()
TEST_BUILDER = TestBuilder()
TEST_SCENARIO = TestScenario()
TEST_MOCK = TestMock()
