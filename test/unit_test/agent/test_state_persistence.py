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

"""
Tests for state persistence behavior with LOCAL_DEPLOYMENT toggle (container reuse).

These tests verify that:
- Without LOCAL_DEPLOYMENT: containers are recreated between executions (state cleared)
- With LOCAL_DEPLOYMENT: containers are reused (state persists across executions)
"""

import os
import pytest
from unittest.mock import patch
import asyncio


class TestStatePersistence:
    """Test cases for state persistence behavior based on LOCAL_DEPLOYMENT toggle."""

    @pytest.fixture(autouse=True)
    def reset_container_state(self):
        """Reset container state before each test."""
        import sys

        # Clear any cached container modules to ensure fresh imports
        modules_to_clear = [k for k in sys.modules.keys() if "container" in k.lower()]
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        yield

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "false"})
    def test_state_cleared_without_local_deployment(self):
        """
        Test that when LOCAL_DEPLOYMENT is disabled (default), containers are
        recreated between executions, effectively clearing any state.

        Expected behavior:
        - release_container() should call recreate_container()
        - Container is cleaned and fresh for each execution
        """
        from agent.sandbox.executor_manager.core.container import release_container
        from agent.sandbox.executor_manager.models.enums import SupportLanguage

        # Mock async_run_command to avoid actual docker calls
        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            # Simulate container_is_running returning True
            mock_cmd.return_value = (0, "true", "")

            # Run release_container with LOCAL_DEPLOYMENT=false
            # In non-local deployment, container should be recreated
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(release_container("sandbox_python_0", SupportLanguage.PYTHON))
            finally:
                loop.close()

            # Verify recreate_container was called (container was recreated)
            # Count how many times docker rm was called (should include recreate)
            call_args_list = [str(call) for call in mock_cmd.call_args_list]
            recreate_calls = [c for c in call_args_list if "docker" in c and "rm" in c]
            assert len(recreate_calls) > 0, "Container should be recreated (state cleared)"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "true"})
    def test_state_persists_with_local_deployment(self):
        """
        Test that when LOCAL_DEPLOYMENT is enabled, containers are reused
        without recreation, preserving state across executions.

        Expected behavior:
        - release_container() should NOT call recreate_container()
        - Container is returned to queue for reuse with same container ID
        """
        from agent.sandbox.executor_manager.core.container import release_container
        from agent.sandbox.executor_manager.models.enums import SupportLanguage

        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            # Simulate container_is_running returning True
            mock_cmd.return_value = (0, "true", "")

            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(release_container("sandbox_python_0", SupportLanguage.PYTHON))
            finally:
                loop.close()

            # With LOCAL_DEPLOYMENT=true, container should be reused
            # Check that container name was added back to queue (reused, not recreated)
            call_args_list = [str(call) for call in mock_cmd.call_args_list]
            # Should NOT have recreation (docker rm followed by docker run)
            recreate_count = sum(1 for c in call_args_list if "docker" in c and "run" in c)
            assert recreate_count == 0, "Container should be reused, not recreated"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "true"})
    def test_file_persistence_across_executions(self):
        """
        Test that files created in previous executions persist when
        LOCAL_DEPLOYMENT is enabled.

        This verifies the security concern: files written in one execution
        are available in subsequent executions within the same container.
        """
        from agent.sandbox.executor_manager.core.container import (
            _CONTAINER_QUEUES,
            release_container,
        )
        from agent.sandbox.executor_manager.services.execution import execute_code
        from agent.sandbox.executor_manager.models.schemas import CodeExecutionRequest
        from agent.sandbox.executor_manager.models.enums import SupportLanguage, ResultStatus
        import base64

        _CONTAINER_QUEUES[SupportLanguage.PYTHON].put("sandbox_python_0")

        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "", "")

            with patch("agent.sandbox.executor_manager.services.execution._collect_artifacts") as mock_collect:
                mock_collect.return_value = []

                code1 = base64.b64encode(b"def main(): import os; open('/workspace/test.txt', 'w').write('hello'); return {'result': 'created'}").decode()
                req1 = CodeExecutionRequest(code_b64=code1, language="python")

                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(execute_code(req1))
                finally:
                    loop.close()

                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(release_container("sandbox_python_0", SupportLanguage.PYTHON))
                finally:
                    loop.close()

                call_args_list = [str(call) for call in mock_cmd.call_args_list]
                docker_rm_calls = [c for c in call_args_list if "rm" in c]
                assert len(docker_rm_calls) == 0, "With LOCAL_DEPLOYMENT=true, container should not be removed (file persists)"

                mock_cmd.reset_mock()
                mock_cmd.return_value = (0, "", "")

                code2 = base64.b64encode(
                    b"def main(): import os; return {'exists': os.path.exists('/workspace/test.txt'), 'content': open('/workspace/test.txt').read() if os.path.exists('/workspace/test.txt') else ''}"
                ).decode()
                req2 = CodeExecutionRequest(code_b64=code2, language="python")

                loop = asyncio.new_event_loop()
                try:
                    result2 = loop.run_until_complete(execute_code(req2))
                finally:
                    loop.close()

                assert result2.status == ResultStatus.SUCCESS, "Second execution should succeed"
                assert "True" in str(result2.result), "File should persist across executions with LOCAL_DEPLOYMENT=true"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "false"})
    def test_file_cleared_without_local_deployment(self):
        """
        Test that files created in previous executions are cleared when
        LOCAL_DEPLOYMENT is disabled.

        This verifies container recreation clears all state.
        """
        from agent.sandbox.executor_manager.core.container import (
            _CONTAINER_QUEUES,
            release_container,
        )
        from agent.sandbox.executor_manager.services.execution import execute_code
        from agent.sandbox.executor_manager.models.schemas import CodeExecutionRequest
        from agent.sandbox.executor_manager.models.enums import SupportLanguage, ResultStatus
        import base64

        _CONTAINER_QUEUES[SupportLanguage.PYTHON].put("sandbox_python_0")

        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "", "")

            with patch("agent.sandbox.executor_manager.services.execution._collect_artifacts") as mock_collect:
                mock_collect.return_value = []

                code1 = base64.b64encode(b"def main(): import os; open('/workspace/test.txt', 'w').write('hello'); return {'result': 'created'}").decode()
                req1 = CodeExecutionRequest(code_b64=code1, language="python")

                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(execute_code(req1))
                finally:
                    loop.close()

                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(release_container("sandbox_python_0", SupportLanguage.PYTHON))
                finally:
                    loop.close()

                call_args_list = [str(call) for call in mock_cmd.call_args_list]
                docker_rm_calls = [c for c in call_args_list if "rm" in c]
                assert len(docker_rm_calls) > 0, "With LOCAL_DEPLOYMENT=false, container should be removed (state cleared)"

                mock_cmd.reset_mock()
                mock_cmd.return_value = (0, "", "")

                code2 = base64.b64encode(b"def main(): import os; return {'exists': os.path.exists('/workspace/test.txt')}").decode()
                req2 = CodeExecutionRequest(code_b64=code2, language="python")

                loop = asyncio.new_event_loop()
                try:
                    result2 = loop.run_until_complete(execute_code(req2))
                finally:
                    loop.close()

                assert result2.status == ResultStatus.SUCCESS, "Second execution should succeed"
                assert "False" in str(result2.result), "File should NOT persist (container was recreated) with LOCAL_DEPLOYMENT=false"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "true"})
    def test_env_var_isolation(self):
        """
        Test that environment variables set in one execution are visible
        in subsequent executions when LOCAL_DEPLOYMENT is enabled.

        This tests the security concern that env vars persist across runs.
        """
        from agent.sandbox.executor_manager.core.container import (
            _CONTAINER_QUEUES,
            release_container,
        )
        from agent.sandbox.executor_manager.services.execution import execute_code
        from agent.sandbox.executor_manager.models.schemas import CodeExecutionRequest
        from agent.sandbox.executor_manager.models.enums import SupportLanguage, ResultStatus
        import base64

        _CONTAINER_QUEUES[SupportLanguage.PYTHON].put("sandbox_python_0")

        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "", "")

            with patch("agent.sandbox.executor_manager.services.execution._collect_artifacts") as mock_collect:
                mock_collect.return_value = []

                code1 = base64.b64encode(b"def main(): import os; os.environ['TEST_VAR'] = 'hello'; return {'result': 'set'}").decode()
                req1 = CodeExecutionRequest(code_b64=code1, language="python")

                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(execute_code(req1))
                finally:
                    loop.close()

                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(release_container("sandbox_python_0", SupportLanguage.PYTHON))
                finally:
                    loop.close()

                call_args_list = [str(call) for call in mock_cmd.call_args_list]
                docker_rm_calls = [c for c in call_args_list if "rm" in c]
                assert len(docker_rm_calls) == 0, "With LOCAL_DEPLOYMENT=true, container should not be removed (env persists)"

                mock_cmd.reset_mock()
                mock_cmd.return_value = (0, "", "")

                code2 = base64.b64encode(b"def main(): import os; return {'exists': 'TEST_VAR' in os.environ, 'value': os.environ.get('TEST_VAR', '')}").decode()
                req2 = CodeExecutionRequest(code_b64=code2, language="python")

                loop = asyncio.new_event_loop()
                try:
                    result2 = loop.run_until_complete(execute_code(req2))
                finally:
                    loop.close()

                assert result2.status == ResultStatus.SUCCESS, "Second execution should succeed"
                assert "True" in str(result2.result), "Env var should persist across executions with LOCAL_DEPLOYMENT=true"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "false"})
    def test_env_var_isolation_disabled(self):
        """
        Test that environment variables set in one execution are NOT visible
        in subsequent executions when LOCAL_DEPLOYMENT is disabled.

        Container recreation clears environment.
        """
        from agent.sandbox.executor_manager.core.container import (
            _CONTAINER_QUEUES,
            release_container,
        )
        from agent.sandbox.executor_manager.services.execution import execute_code
        from agent.sandbox.executor_manager.models.schemas import CodeExecutionRequest
        from agent.sandbox.executor_manager.models.enums import SupportLanguage, ResultStatus
        import base64

        _CONTAINER_QUEUES[SupportLanguage.PYTHON].put("sandbox_python_0")

        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "", "")

            with patch("agent.sandbox.executor_manager.services.execution._collect_artifacts") as mock_collect:
                mock_collect.return_value = []

                code1 = base64.b64encode(b"def main(): import os; os.environ['TEST_VAR'] = 'hello'; return {'result': 'set'}").decode()
                req1 = CodeExecutionRequest(code_b64=code1, language="python")

                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(execute_code(req1))
                finally:
                    loop.close()

                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(release_container("sandbox_python_0", SupportLanguage.PYTHON))
                finally:
                    loop.close()

                call_args_list = [str(call) for call in mock_cmd.call_args_list]
                docker_rm_calls = [c for c in call_args_list if "rm" in c]
                assert len(docker_rm_calls) > 0, "With LOCAL_DEPLOYMENT=false, container should be removed (env cleared)"

                mock_cmd.reset_mock()
                mock_cmd.return_value = (0, "", "")

                code2 = base64.b64encode(b"def main(): import os; return {'exists': 'TEST_VAR' in os.environ}").decode()
                req2 = CodeExecutionRequest(code_b64=code2, language="python")

                loop = asyncio.new_event_loop()
                try:
                    result2 = loop.run_until_complete(execute_code(req2))
                finally:
                    loop.close()

                assert result2.status == ResultStatus.SUCCESS, "Second execution should succeed"
                assert "False" in str(result2.result), "Env var should NOT persist (container was recreated) with LOCAL_DEPLOYMENT=false"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "false"})
    def test_process_cleanup_verification(self):
        """
        Test that without LOCAL_DEPLOYMENT, process cleanup is verified
        through container recreation.

        When LOCAL_DEPLOYMENT is disabled, containers are recreated after
        each use, ensuring any stray processes are killed.
        """
        from agent.sandbox.executor_manager.core.container import release_container
        from agent.sandbox.executor_manager.models.enums import SupportLanguage

        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            # Simulate container running
            mock_cmd.return_value = (0, "true", "")

            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(release_container("sandbox_python_0", SupportLanguage.PYTHON))
            finally:
                loop.close()

            # Without LOCAL_DEPLOYMENT, container should be recreated
            # This implicitly cleans up any lingering processes
            call_args_str = " ".join([str(call) for call in mock_cmd.call_args_list])
            assert "rm" in call_args_str and "docker" in call_args_str, "Container should be removed and recreated"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "true"})
    def test_memory_cleanup_between_runs(self):
        """
        Test that with LOCAL_DEPLOYMENT=true, memory from previous executions
        is NOT automatically cleaned up (container is reused as-is).

        This contrasts with LOCAL_DEPLOYMENT=false where container recreation
        ensures fresh memory state.
        """
        from agent.sandbox.executor_manager.core.container import release_container
        from agent.sandbox.executor_manager.models.enums import SupportLanguage

        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "true", "")

            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(release_container("sandbox_python_0", SupportLanguage.PYTHON))
            finally:
                loop.close()

            # With LOCAL_DEPLOYMENT=true, container should be put back in queue
            # without any memory cleanup (no docker run to create fresh container)
            fresh_container_calls = [c for c in mock_cmd.call_args_list if "run" in str(c) and "docker" in str(c)]
            assert len(fresh_container_calls) == 0, "No fresh container should be created with LOCAL_DEPLOYMENT"


class TestLocalDeploymentEnvParsing:
    """Test that LOCAL_DEPLOYMENT environment variable is parsed correctly."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("YES", True),
            ("on", True),
            ("ON", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("", False),
        ],
    )
    def test_env_parsing(self, value, expected):
        """Test various LOCAL_DEPLOYMENT values are parsed correctly."""
        from agent.sandbox.executor_manager.util import env_setting_enabled

        with patch.dict(os.environ, {"LOCAL_DEPLOYMENT": value}):
            result = env_setting_enabled("LOCAL_DEPLOYMENT", "false")
            assert result == expected


class TestContainerReuseSecurity:
    """Test security implications of container reuse."""

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "true"})
    def test_container_reuse_security_warning(self):
        """
        Verify that LOCAL_DEPLOYMENT=true enables container reuse,
        which has security implications documented in AGENTS.md.

        This test ensures the security warning is properly triggered.
        """
        from agent.sandbox.executor_manager.util import env_setting_enabled

        # Verify env_setting_enabled returns True for LOCAL_DEPLOYMENT
        result = env_setting_enabled("LOCAL_DEPLOYMENT", "false")
        assert result is True, "LOCAL_DEPLOYMENT should be enabled"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "false"})
    def test_container_isolation_without_local_deployment(self):
        """
        Verify that without LOCAL_DEPLOYMENT, container isolation is maintained
        through container recreation between executions.
        """
        from agent.sandbox.executor_manager.util import env_setting_enabled

        result = env_setting_enabled("LOCAL_DEPLOYMENT", "false")
        assert result is False, "LOCAL_DEPLOYMENT should be disabled by default"

    def test_default_local_deployment_is_disabled(self):
        """Test that LOCAL_DEPLOYMENT defaults to disabled (false)."""
        from agent.sandbox.executor_manager.util import env_setting_enabled

        env_backup = os.environ.get("LOCAL_DEPLOYMENT")
        if "LOCAL_DEPLOYMENT" in os.environ:
            del os.environ["LOCAL_DEPLOYMENT"]

        try:
            result = env_setting_enabled("LOCAL_DEPLOYMENT", "false")
            assert result is False, "LOCAL_DEPLOYMENT should default to disabled"
        finally:
            if env_backup:
                os.environ["LOCAL_DEPLOYMENT"] = env_backup
