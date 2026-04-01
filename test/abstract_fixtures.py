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
Abstract Fixtures for Two-Tier Testing System.

This module provides abstract pytest fixtures that work in both mock and full modes.
"""

from typing import Any, Optional

import pytest

from test.mode_detection import get_test_mode, TestMode
from test.service_factory import ServiceFactory


class AbstractFixtures:
    """
    Abstract fixture container for two-tier testing.
    
    Provides common fixtures that automatically use mock or real services
    based on the current test mode.
    
    Usage:
        fixtures = AbstractFixtures()
        redis = fixtures.redis()  # Returns mock or real based on mode
    """
    
    _factory: Optional[ServiceFactory] = None
    
    @classmethod
    def get_factory(cls) -> ServiceFactory:
        """Get or create the service factory."""
        if cls._factory is None:
            cls._factory = ServiceFactory()
        return cls._factory
    
    @classmethod
    def set_factory(cls, factory: ServiceFactory) -> None:
        """Set a custom service factory (useful for testing)."""
        cls._factory = factory
    
    @pytest.fixture
    def mock_mode(self) -> bool:
        """
        Fixture indicating whether running in mock mode.
        
        Returns:
            True if in mock mode, False otherwise
        """
        return get_test_mode() == TestMode.MOCK
    
    @pytest.fixture
    def full_mode(self) -> bool:
        """
        Fixture indicating whether running in full mode.
        
        Returns:
            True if in full mode, False otherwise
        """
        return get_test_mode() == TestMode.FULL
    
    @pytest.fixture
    def test_mode(self) -> TestMode:
        """
        Fixture providing the current test mode.
        
        Returns:
            The current TestMode enum value
        """
        return get_test_mode()
    
    @pytest.fixture
    def docstore(self) -> Any:
        """
        Fixture providing a document store connection.
        
        Returns:
            Document store instance (mock or real based on mode)
        """
        return self.get_factory().create_docstore()
    
    @pytest.fixture
    def redis_db(self) -> Any:
        """
        Fixture providing a Redis DB connection.
        
        Returns:
            Redis DB instance (mock or real based on mode)
        """
        return self.get_factory().create_redis_db()
    
    @pytest.fixture
    def redis_msg(self) -> Any:
        """
        Fixture providing a Redis message handler.
        
        Returns:
            Redis message handler instance (mock or real based on mode)
        """
        return self.get_factory().create_redis_msg()
    
    @pytest.fixture
    def minio(self) -> Any:
        """
        Fixture providing a MinIO storage connection.
        
        Returns:
            MinIO instance (mock or real based on mode)
        """
        return self.get_factory().create_minio()
    
    @pytest.fixture
    def database(self) -> Any:
        """
        Fixture providing a database connection.
        
        Returns:
            Database instance (mock or real based on mode)
        """
        return self.get_factory().create_database()
    
    @pytest.fixture
    def all_services(self) -> dict[str, Any]:
        """
        Fixture providing all service connections.
        
        Returns:
            Dictionary with all service instances
        """
        factory = self.get_factory()
        return {
            "docstore": factory.create_docstore(),
            "redis_db": factory.create_redis_db(),
            "redis_msg": factory.create_redis_msg(),
            "minio": factory.create_minio(),
            "database": factory.create_database(),
        }


def get_abstract_fixtures() -> AbstractFixtures:
    """
    Get the abstract fixtures instance.
    
    Returns:
        AbstractFixtures singleton instance
    """
    return AbstractFixtures()


def get_service_factory() -> ServiceFactory:
    """
    Get the service factory instance.
    
    This is the main entry point for accessing services in tests.
    
    Returns:
        ServiceFactory instance
        
    Example:
        >>> from test.abstract_fixtures import get_service_factory
        >>> factory = get_service_factory()
        >>> redis = factory.create_redis_db()
    """
    return AbstractFixtures.get_factory()