#
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
#
"""
Test Mode Detection and Configuration

This module provides utilities for detecting whether tests should run in
mock mode (fast, lightweight) or full mode (real services via Docker).

Usage:
    from test.mode_detection import get_test_mode, TestMode
    
    mode = get_test_mode()
    if mode == TestMode.MOCK:
        # Use mock services
    elif mode == TestMode.FULL:
        # Use real Docker services
"""

import os
from enum import Enum
from typing import Optional


class TestMode(Enum):
    """Enumeration of available test modes."""
    
    MOCK = "mock"  # Fast, lightweight mock services
    FULL = "full"  # Real Docker services
    
    def __str__(self) -> str:
        return self.value
    
    def is_mock(self) -> bool:
        """Check if this mode uses mocks."""
        return self == TestMode.MOCK
    
    def is_full(self) -> bool:
        """Check if this mode uses real services."""
        return self == TestMode.FULL


# Environment variable name for test mode configuration
TEST_MODE_ENV_VAR = "RAGFLOW_TEST_MODE"

# Default test mode
DEFAULT_TEST_MODE = TestMode.MOCK


class TestModeConfig:
    """
    Configuration container for test mode settings.
    
    This class manages the configuration for the two-tier testing system,
    allowing for environment-based or programmatic configuration.
    
    Attributes:
        mode: The current test mode (MOCK or FULL)
        auto_detect_services: Whether to auto-detect running services and switch to FULL mode
        fail_fast: Whether tests should fail fast on service errors
        verbose: Whether to enable verbose logging for debugging
    """
    
    _instance: Optional['TestModeConfig'] = None
    
    def __new__(cls) -> 'TestModeConfig':
        """Singleton pattern to ensure single configuration instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        mode: Optional[TestMode] = None,
        auto_detect_services: bool = True,
        fail_fast: bool = False,
        verbose: bool = False
    ):
        """
        Initialize test mode configuration.
        
        Args:
            mode: The test mode to use (overrides environment variable)
            auto_detect_services: Auto-detect running Docker services
            fail_fast: Fail tests fast on service errors
            verbose: Enable verbose debug logging
        """
        if self._initialized:
            return
            
        self._mode = mode
        self.auto_detect_services = auto_detect_services
        self.fail_fast = fail_fast
        self.verbose = verbose
        self._initialized = True
    
    @property
    def mode(self) -> TestMode:
        """Get current test mode."""
        if self._mode is None:
            self._mode = self._detect_mode()
        return self._mode
    
    @mode.setter
    def mode(self, value: Optional[TestMode]) -> None:
        """Set test mode."""
        self._mode = value
    
    def _detect_mode(self) -> TestMode:
        """
        Detect the test mode from environment or defaults.
        
        Returns:
            The detected test mode
        """
        # Check environment variable first
        env_value = os.environ.get(TEST_MODE_ENV_VAR, "").lower().strip()
        
        if env_value == "mock":
            return TestMode.MOCK
        elif env_value == "full":
            return TestMode.FULL
        
        # Auto-detect services if enabled
        if self.auto_detect_services and self._are_services_running():
            return TestMode.FULL
        
        return DEFAULT_TEST_MODE
    
    def _are_services_running(self) -> bool:
        """
        Check if Docker services are running.
        
        Returns:
            True if services are detected, False otherwise
        """
        # This is a lightweight check - we don't want to slow down imports
        # Full service validation happens in service factory
        docker_host = os.environ.get("DOCKER_HOST", "")
        if docker_host and "tcp" in docker_host:
            return True
        
        # Check for common Docker env hints
        if os.path.exists("/var/run/docker.sock"):
            return True
        
        return False
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._mode = None
        self._initialized = False


def get_test_mode() -> TestMode:
    """
    Get the current test mode.
    
    This is the primary function to use when determining test mode.
    It reads from environment variables and configuration.
    
    Environment Variables:
        RAGFLOW_TEST_MODE: Set to "mock" or "full". Defaults to "mock".
    
    Returns:
        The current test mode (TestMode.MOCK or TestMode.FULL)
        
    Examples:
        >>> from test.mode_detection import get_test_mode
        >>> mode = get_test_mode()
        >>> print(f"Running in {mode} mode")
    """
    config = TestModeConfig()
    return config.mode


def set_test_mode(mode: TestMode) -> None:
    """
    Programmatically set the test mode.
    
    Useful for tests that need to force a particular mode.
    
    Args:
        mode: The test mode to use
        
    Examples:
        >>> from test.mode_detection import set_test_mode, TestMode
        >>> set_test_mode(TestMode.MOCK)  # Force mock mode
    """
    config = TestModeConfig()
    config.mode = mode
    

def is_mock_mode() -> bool:
    """
    Check if running in mock mode.
    
    Returns:
        True if in mock mode, False otherwise
        
    Examples:
        >>> if is_mock_mode():
        ...     print("Using mock services")
    """
    return get_test_mode() == TestMode.MOCK


def is_full_mode() -> bool:
    """
    Check if running in full mode with real services.
    
    Returns:
        True if in full mode, False otherwise
    """
    return get_test_mode() == TestMode.FULL
