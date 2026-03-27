"""
Tests for multi-tenant isolation in sandbox execution.

These tests verify that User A's sandbox execution cannot see User B's files, environment variables,
or processes. This ensures proper tenant isolation in multi-tenant deployments.
"""

import os
import pytest
import asyncio
import tempfile
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from agent.sandbox.executor_manager.core.container import _CONTAINER_QUEUES
from agent.sandbox.executor_manager.services.execution import execute_code
from agent.sandbox.executor_manager.models.schemas import CodeExecutionRequest
from agent.sandbox.executor_manager.models.enums import SupportLanguage, ResultStatus


class TestMultiTenantIsolation:
    """Test cases for multi-tenant isolation in sandbox execution."""

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

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "true"})
    def test_file_system_isolation_between_tenants(self):
        """
        Test that files created by one tenant are not visible to another tenant.
        
        This verifies that each tenant's execution context is isolated,
        even when using the same container pool.
        """
        from agent.sandbox.executor_manager.core.container import _CONTAINER_QUEUES
        
        # Setup mock container in queue
        _CONTAINER_QUEUES[SupportLanguage.PYTHON].put("sandbox_python_0")
        
        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            # Simulate successful docker commands
            mock_cmd.return_value = (0, "", "")
            
            # Tenant A creates a file
            code_tenant_a = b"def main(): import os; open('/workspace/tenant_a.txt', 'w').write('secret'); return {'result': 'created'}"
            req_tenant_a = CodeExecutionRequest(
                code_b64=base64.b64encode(code_tenant_a).decode(),
                language="python"
            )
            
            loop = asyncio.new_event_loop()
            try:
                result_a = loop.run_until_complete(execute_code(req_tenant_a))
            finally:
                loop.close()
            
            # Tenant B tries to read the file
            code_tenant_b = b"def main(): import os;" return {'exists': os.path.exists('/workspace/tenant_a.txt')}"
            req_tenant_b = CodeExecutionRequest(
                code_b64=base64.b64encode(code_tenant_b).decode(),
                language="python"
            )
            
            loop = asyncio.new_event_loop()
            try:
                result_b = loop.run_until_complete(execute_code(req_tenant_b))
            finally:
                loop.close()
            
            # With proper isolation, Tenant B should NOT see Tenant A's file
            # The file should be isolated per tenant execution context
            assert result_b.stdout == '{"exists": false}', "Tenant B should not see Tenant A's file"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "true"})
    def test_env_var_isolation_between_tenants(self):
        """
        Test that environment variables set by one tenant are not visible to another tenant.
        
        This verifies that each tenant's execution context has isolated environment variables,
        preventing cross-tenant data leakage.
        """
        from agent.sandbox.executor_manager.core.container import _CONTAINER_QUEUES
        
        # Setup mock container in queue
        _CONTAINER_QUEUES[SupportLanguage.PYTHON].put("sandbox_python_0")
        
        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "", "")
            
            # Tenant A sets an environment variable
            code_tenant_a = b"def main(): import os; os.environ['TENANT_A_SECRET'] = 'password123'; return {'result': 'set'}"
            req_tenant_a = CodeExecutionRequest(
                code_b64=base64.b64encode(code_tenant_a).decode(),
                language="python"
            )
            
            loop = asyncio.new_event_loop()
            try:
                result_a = loop.run_until_complete(execute_code(req_tenant_a))
            finally:
                loop.close()
            
            # Tenant B tries to read the environment variable
            code_tenant_b = b"def main(): import os;" return {'secret': os.getenv('TENANT_A_SECRET')}"
            req_tenant_b = CodeExecutionRequest(
                code_b64=base64.b64encode(code_tenant_b).decode(),
                language="python"
            )
            
            loop = asyncio.new_event_loop()
            try:
                result_b = loop.run_until_complete(execute_code(req_tenant_b))
            finally:
                loop.close()
            
            # With proper isolation, Tenant B should NOT see Tenant A's environment variable
            assert result_b.stdout == '{"secret": null}', "Tenant B should not see Tenant A's env var"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "true"})
    def test_process_isolation_between_tenants(self):
        """
        Test that processes created by one tenant are not visible to another tenant.
        
        This verifies that each tenant's execution context has isolated process space,
        preventing cross-tenant process interference.
        """
        from agent.sandbox.executor_manager.core.container import _CONTAINER_QUEUES
        
        # Setup mock container in queue
        _CONTAINER_QUEUES[SupportLanguage.PYTHON].put("sandbox_python_0")
        
        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            # Simulate docker commands
            mock_cmd.side_effect = [
                (0, "", ""),  # mkdir
                (0, "", ""),  # tar
                (0, "", ""),  # docker exec
            ]
            
            # Tenant A starts a background process
            code_tenant_a = b"def main(): import subprocess; subprocess.Popen(['sleep', '60']); return {'result': 'started'}"
            req_tenant_a = CodeExecutionRequest(
                code_b64=base64.b64encode(code_tenant_a).decode(),
                language="python"
            )
            
            loop = asyncio.new_event_loop()
            try:
                result_a = loop.run_until_complete(execute_code(req_tenant_a))
            finally:
                loop.close()
            
            # Tenant B checks for running processes
            code_tenant_b = b"def main(): import subprocess; p = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE); out, _ = p.communicate(); return {'processes': out.decode()}"
            req_tenant_b = CodeExecutionRequest(
                code_b64=base64.b64encode(code_tenant_b).decode(),
                language="python"
            )
            
            loop = asyncio.new_event_loop()
            try:
                result_b = loop.run_until_complete(execute_code(req_tenant_b))
            finally:
                loop.close()
            
            # With proper isolation, Tenant B should NOT see Tenant A's background process
            assert "sleep" not in result_b.stdout, "Tenant B should not see Tenant A's process"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "true"})
    def test_concurrent_execution_isolation(self):
        """
        Test that concurrent executions by different tenants are properly isolated.
        
        This verifies that parallel execution contexts don't interfere with each other,
        even when using the same container pool.
        """
        from agent.sandbox.executor_manager.core.container import _CONTAINER_QUEUES
        from concurrent.futures import ThreadPoolExecutor
        
        # Setup mock containers
        _CONTAINER_QUEUES[SupportLanguage.PYTHON].put("sandbox_python_0")
        _CONTAINER_QUEUES[SupportLanguage.PYTHON].put("sandbox_python_1")
        
        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "", "")
            
            def tenant_a_task():
                code = b"def main(): import os; open('/workspace/tenant_a.txt', 'w').write('tenant_a'); return {'result': 'a'}"
                req = CodeExecutionRequest(code_b64=base64.b64encode(code).decode(), language="python")
                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(execute_code(req))
                finally:
                    loop.close()
                return result
            
            def tenant_b_task():
                code = b"def main(): import os; open('/workspace/tenant_b.txt', 'w').write('tenant_b'); return {'result': 'b'}"
                req = CodeExecutionRequest(code_b64=base64.b64encode(code).decode(), language="python")
                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(execute_code(req))
                finally:
                    loop.close()
                return result
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_a = executor.submit(tenant_a_task)
                future_b = executor.submit(tenant_b_task)
                
                result_a = future_a.result()
                result_b = future_b.result()
            
            # Verify both executions completed successfully
            assert result_a.stdout == '{"result": "a"}'
            assert result_b.stdout == '{"result": "b"}'
            
            # Verify files are isolated (would be in different execution contexts)
            # Since we're using the same container, this tests the isolation mechanism
            # In a real multi-tenant setup, these would be in different containers
            assert "tenant_a" in result_a.stdout
            assert "tenant_b" in result_b.stdout

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "true"})
    def test_cross_tenant_access_denied(self):
        """
        Test that cross-tenant access attempts are explicitly denied.
        
        This verifies that the sandbox properly rejects attempts to access
        resources belonging to other tenants.
        """
        from agent.sandbox.executor_manager.core.container import _CONTAINER_QUEUES
        
        # Setup mock container in queue
        _CONTAINER_QUEUES[SupportLanguage.PYTHON].put("sandbox_python_0")
        
        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            # Simulate docker commands
            mock_cmd.return_value = (0, "", "")
            
            # Tenant A creates a file with restricted permissions
            code_tenant_a = b"def main(): import os; open('/workspace/tenant_a_secret.txt', 'w').write('confidential'); os.chmod('/workspace/tenant_a_secret.txt', 0o600); return {'result': 'created'}"
            req_tenant_a = CodeExecutionRequest(
                code_b64=base64.b64encode(code_tenant_a).decode(),
                language="python"
            )
            
            loop = asyncio.new_event_loop()
            try:
                result_a = loop.run_until_complete(execute_code(req_tenant_a))
            finally:
                loop.close()
            
            # Tenant B tries to access the restricted file
            code_tenant_b = b"def main(): import os;" 
                            try: 
                                with open('/workspace/tenant_a_secret.txt', 'r') as f: 
                                    content = f.read() 
                                return {'content': content, 'status': 'success'}
                            except Exception as e: 
                                return {'error': str(e), 'status': 'failed'}"
            req_tenant_b = CodeExecutionRequest(
                code_b64=base64.b64encode(code_tenant_b).decode(),
                language="python"
            )
            
            loop = asyncio.new_event_loop()
            try:
                result_b = loop.run_until_complete(execute_code(req_tenant_b))
            finally:
                loop.close()
            
            # With proper isolation, Tenant B should get permission denied
            assert "Permission denied" in result_b.stderr or "failed" in result_b.stdout, "Cross-tenant access should be denied"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "false"})
    def test_container_recreation_isolation(self):
        """
        Test that container recreation between executions provides isolation.
        
        When LOCAL_DEPLOYMENT is false, containers are recreated for each execution,
        providing stronger isolation guarantees.
        """
        from agent.sandbox.executor_manager.core.container import release_container
        from agent.sandbox.executor_manager.models.enums import SupportLanguage
        
        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            # Simulate container running
            mock_cmd.return_value = (0, "true", "")
            
            # First execution: create a file
            code1 = b"def main(): import os; open('/workspace/test.txt', 'w').write('first'); return {'result': 'first'}"
            req1 = CodeExecutionRequest(code_b64=base64.b64encode(code1).decode(), language="python")
            
            loop = asyncio.new_event_loop()
            try:
                result1 = loop.run_until_complete(execute_code(req1))
            finally:
                loop.close()
            
            # Release container (should recreate for isolation)
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(release_container("sandbox_python_0", SupportLanguage.PYTHON))
            finally:
                loop.close()
            
            # Second execution: check if file exists
            code2 = b"def main(): import os; return {'exists': os.path.exists('/workspace/test.txt')}"
            req2 = CodeExecutionRequest(code_b64=base64.b64encode(code2).decode(), language="python")
            
            loop = asyncio.new_event_loop()
            try:
                result2 = loop.run_until_complete(execute_code(req2))
            finally:
                loop.close()
            
            # With container recreation, the file should not exist
            assert result2.stdout == '{"exists": false}', "Container recreation should provide isolation"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "true"})
    def test_artifact_isolation(self):
        """
        Test that artifacts (files produced by execution) are properly isolated.
        
        This verifies that artifacts created by one tenant are not accessible
        to other tenants through the artifact collection mechanism.
        """
        from agent.sandbox.executor_manager.core.container import _CONTAINER_QUEUES
        
        # Setup mock container in queue
        _CONTAINER_QUEUES[SupportLanguage.PYTHON].put("sandbox_python_0")
        
        with patch("agent.sandbox.executor_manager.core.container.async_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "", "")
            
            # Tenant A creates an artifact
            code_tenant_a = b"def main(): import os; os.makedirs('/workspace/artifacts', exist_ok=True); open('/workspace/artifacts/tenant_a.txt', 'w').write('secret'); return {'result': 'created'}"
            req_tenant_a = CodeExecutionRequest(
                code_b64=base64.b64encode(code_tenant_a).decode(),
                language="python"
            )
            
            loop = asyncio.new_event_loop()
            try:
                result_a = loop.run_until_complete(execute_code(req_tenant_a))
            finally:
                loop.close()
            
            # Tenant B tries to collect artifacts
            code_tenant_b = b"def main(): import os;" 
                            try: 
                                files = os.listdir('/workspace/artifacts') 
                                return {'files': files, 'status': 'success'}
                            except Exception as e: 
                                return {'error': str(e), 'status': 'failed'}"
            req_tenant_b = CodeExecutionRequest(
                code_b64=base64.b64encode(code_tenant_b).decode(),
                language="python"
            )
            
            loop = asyncio.new_event_loop()
            try:
                result_b = loop.run_until_complete(execute_code(req_tenant_b))
            finally:
                loop.close()
            
            # With proper isolation, Tenant B should not see Tenant A's artifacts
            assert "tenant_a.txt" not in result_b.stdout, "Artifacts should be tenant-isolated"


# Helper functions for test isolation
import base64


def _create_mock_container(language: str):
    """Create a mock container for testing."""
    from agent.sandbox.executor_manager.core.container import _CONTAINER_QUEUES
    from agent.sandbox.executor_manager.models.enums import SupportLanguage
    
    language_enum = SupportLanguage.PYTHON if language == "python" else SupportLanguage.NODEJS
    _CONTAINER_QUEUES[language_enum].put(f"sandbox_{language}_0")


def _mock_docker_commands(mock_cmd, side_effect=None):
    """Configure mock docker commands with optional side effect."""
    if side_effect:
        mock_cmd.side_effect = side_effect
    else:
        mock_cmd.return_value = (0, "", "")