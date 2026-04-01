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
Service Factory for Two-Tier Testing System.

This module provides a factory pattern for creating service instances
based on the current test mode (mock or full).
"""

from typing import Any

from test.mode_detection import get_test_mode, TestMode


class ServiceFactory:
    """
    Factory for creating service instances in mock or full mode.
    
    This factory creates either mock implementations or real service connections
    based on the current test mode configuration.
    
    Usage:
        factory = ServiceFactory()
        
        # Get document store (mock or real)
        docstore = factory.create_docstore()
        
        # Get Redis
        redis = factory.create_redis_db()
        
        # Get MinIO
        minio = factory.create_minio()
        
        # Get all services at once
        services = factory.create_all()
    
    Environment Variables:
        RAGFLOW_TEST_MODE: Set to "mock" or "full" to control test mode
    """
    
    def __init__(self) -> None:
        """Initialize the service factory."""
        self._mock_services: dict[str, Any] = {}
        self._real_services: dict[str, Any] = {}
    
    @property
    def mode(self) -> TestMode:
        """Get the current test mode (dynamically from config)."""
        return get_test_mode()
    
    @property
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode."""
        return self.mode == TestMode.MOCK
    
    @property
    def is_full_mode(self) -> bool:
        """Check if running in full mode."""
        return self.mode == TestMode.FULL
    
    def _get_mock_service(self, name: str, creator: Any) -> Any:
        """
        Get or create a mock service instance.
        
        Args:
            name: Service name/key
            creator: Function to create the mock service
            
        Returns:
            Mock service instance
        """
        if name not in self._mock_services:
            self._mock_services[name] = creator()
        return self._mock_services[name]
    
    def _get_real_service(self, name: str, creator: Any) -> Any:
        """
        Get or create a real service instance.
        
        Args:
            name: Service name/key
            creator: Function to create the real service
            
        Returns:
            Real service instance
        """
        if name not in self._real_services:
            self._real_services[name] = creator()
        return self._real_services[name]
    
    def create_docstore(self) -> Any:
        """
        Create a document store connection.
        
        Returns:
            Document store instance (mock or real based on mode)
        """
        if self.is_mock_mode:
            from test.mocks.mock_docstore import MockDocStoreConnection
            return self._get_mock_service(
                "docstore",
                MockDocStoreConnection
            )
        else:
            from rag.utils.es_conn import ESConnection
            return self._get_real_service(
                "docstore",
                ESConnection
            )
    
    def create_redis_db(self) -> Any:
        """
        Create a Redis DB connection.
        
        Returns:
            Redis DB instance (mock or real based on mode)
        """
        if self.is_mock_mode:
            from test.mocks.mock_redis import MockRedisDB
            return self._get_mock_service(
                "redis_db",
                MockRedisDB
            )
        else:
            from rag.utils.redis_conn import RedisDB
            return self._get_real_service(
                "redis_db",
                RedisDB
            )
    
    def create_redis_msg(self) -> Any:
        """
        Create a Redis message handler.
        
        Note: Real Redis message requires additional context (consumer, queue, etc.)
        For full mode, this returns a wrapper that creates messages on demand.
        
        Returns:
            Redis message handler instance
        """
        if self.is_mock_mode:
            from test.mocks.mock_redis import MockRedisDB
            return self._get_mock_service(
                "redis_msg",
                MockRedisDB
            )
        else:
            from rag.utils.redis_conn import RedisDB
            return self._get_real_service(
                "redis_msg",
                RedisDB
            )
    
    def create_minio(self) -> Any:
        """
        Create a MinIO storage connection.
        
        Returns:
            MinIO instance (mock or real based on mode)
        """
        if self.is_mock_mode:
            from test.mocks.mock_minio import MockMinioStorage
            return self._get_mock_service(
                "minio",
                MockMinioStorage
            )
        else:
            from rag.utils.minio_conn import RAGFlowMinio
            return self._get_real_service(
                "minio",
                RAGFlowMinio
            )
    
    def create_database(self) -> Any:
        """
        Create a database connection.
        
        Returns:
            Database instance (mock or real based on mode)
        
        Note: For full mode, this uses the existing database connection
        from api.db.db_models.DB
        """
        if self.is_mock_mode:
            from test.mocks.mock_database import MockDatabaseConnection
            return self._get_mock_service(
                "database",
                MockDatabaseConnection
            )
        else:
            from api.db.db_models import DB
            return self._get_real_service(
                "database",
                lambda: DB
            )
    
    def create_all(self) -> dict[str, Any]:
        """
        Create all service instances at once.
        
        Returns:
            Dictionary with all service instances
        """
        return {
            "docstore": self.create_docstore(),
            "redis_db": self.create_redis_db(),
            "redis_msg": self.create_redis_msg(),
            "minio": self.create_minio(),
            "database": self.create_database(),
        }
    
    def reset(self) -> None:
        """
        Reset all mock service instances.
        
        Useful for test isolation - call between tests to ensure clean state.
        """
        for service in self._mock_services.values():
            if hasattr(service, 'reset'):
                service.reset()
        self._mock_services.clear()
    
    def reset_real(self) -> None:
        """Reset all real service instances (closes connections)."""
        for service in self._real_services.values():
            if hasattr(service, 'close'):
                service.close()
        self._real_services.clear()
    
    def reset_all(self) -> None:
        """Reset both mock and real services."""
        self.reset()
        self.reset_real()


def get_service_factory() -> ServiceFactory:
    """
    Get the service factory singleton.
    
    Returns:
        ServiceFactory instance
        
    Example:
        >>> from test.service_factory import get_service_factory
        >>> factory = get_service_factory()
        >>> services = factory.create_all()
    """
    return ServiceFactory()