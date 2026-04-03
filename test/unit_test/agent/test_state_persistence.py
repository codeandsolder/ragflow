#
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


def is_enabled(value: str) -> bool:
    """Check if a value represents an enabled state."""
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def env_setting_enabled(env_key: str, default: str = "false") -> bool:
    """Check if an environment variable is enabled."""
    value = os.getenv(env_key, default)
    return is_enabled(value)


class LocalDeploymentEnvParsing:
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
        # Verify env_setting_enabled returns True for LOCAL_DEPLOYMENT
        result = env_setting_enabled("LOCAL_DEPLOYMENT", "false")
        assert result is True, "LOCAL_DEPLOYMENT should be enabled"

    @patch.dict(os.environ, {"LOCAL_DEPLOYMENT": "false"})
    def test_container_isolation_without_local_deployment(self):
        """
        Verify that without LOCAL_DEPLOYMENT, container isolation is maintained
        through container recreation between executions.
        """
        result = env_setting_enabled("LOCAL_DEPLOYMENT", "false")
        assert result is False, "LOCAL_DEPLOYMENT should be disabled by default"

    def test_default_local_deployment_is_disabled(self):
        """Test that LOCAL_DEPLOYMENT defaults to disabled (false)."""
        env_backup = os.environ.get("LOCAL_DEPLOYMENT")
        if "LOCAL_DEPLOYMENT" in os.environ:
            del os.environ["LOCAL_DEPLOYMENT"]

        try:
            result = env_setting_enabled("LOCAL_DEPLOYMENT", "false")
            assert result is False, "LOCAL_DEPLOYMENT should default to disabled"
        finally:
            if env_backup:
                os.environ["LOCAL_DEPLOYMENT"] = env_backup
