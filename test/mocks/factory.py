#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance of the License.
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
Mock Service Factory.

Provides a factory for creating mock service instances with consistent
configuration and lifecycle management.
"""

from typing import TypeVar, Type

from test.mocks.mock_docstore import MockDocStoreConnection
from test.mocks.mock_redis import MockRedisDB
from test.mocks.mock_minio import MockMinioStorage
from test.mocks.mock_database import MockDatabaseConnection


T = TypeVar("T")


class MockServiceFactory:
    """
    Factory for creating mock service instances.
    
    Provides a centralized way to create and configure mock service
    instances for testing. Ensures consistent configuration and
    provides utilities for batch operations.
    
    This factory is typically used in conjunction with ServiceFactory
    to provide the actual service implementations when running in
    mock mode.
    
    Example:
        >>> factory = MockServiceFactory()
        >>> docstore = factory.create_docstore()
        >>> redis = factory.create_redis()
        >>> minio = factory.create_minio()
        >>> db = factory.create_database()
    """

    @staticmethod
    def create_docstore() -> MockDocStoreConnection:
        """
        Create a new mock document store connection.
        
        Returns:
            A fresh MockDocStoreConnection instance.
            
        Example:
            >>> docstore = MockServiceFactory.create_docstore()
            >>> docstore.health()
            True
        """
        return MockDocStoreConnection()

    @staticmethod
    def create_redis() -> MockRedisDB:
        """
        Create a new mock Redis connection.
        
        Returns:
            A fresh MockRedisDB instance.
            
        Example:
            >>> redis = MockServiceFactory.create_redis()
            >>> redis.health()
            True
        """
        return MockRedisDB()

    @staticmethod
    def create_minio() -> MockMinioStorage:
        """
        Create a new mock MinIO connection.
        
        Returns:
            A fresh MockMinioStorage instance.
            
        Example:
            >>> minio = MockServiceFactory.create_minio()
            >>> minio.health()
            True
        """
        return MockMinioStorage()

    @staticmethod
    def create_database() -> MockDatabaseConnection:
        """
        Create a new mock database connection.
        
        Returns:
            A fresh MockDatabaseConnection instance.
            
        Example:
            >>> db = MockServiceFactory.create_database()
            >>> db.health()
            True
        """
        return MockDatabaseConnection()

    @staticmethod
    def create_all_services() -> dict[str, object]:
        """
        Create all mock services at once.
        
        Returns:
            A dictionary mapping service names to mock instances.
            Dictionary keys are: 'docstore', 'redis', 'minio', 'database'.
            
        Example:
            >>> services = MockServiceFactory.create_all_services()
            >>> sorted(services.keys())
            ['database', 'docstore', 'minio', 'redis']
            >>> all(service.health() for service in services.values())
            True
        """
        return {
            "docstore": MockServiceFactory.create_docstore(),
            "redis": MockServiceFactory.create_redis(),
            "minio": MockServiceFactory.create_minio(),
            "database": MockServiceFactory.create_database(),
        }

    @staticmethod
    def reset_all_services(services: dict[str, object]) -> None:
        """
        Reset all mock services in a dictionary.
        
        Args:
            services: Dictionary of service instances to reset.
            
        Example:
            >>> services = MockServiceFactory.create_all_services()
            >>> services["redis"].set("key", "value")
            >>> services["redis"].get("key")
            'value'
            >>> MockServiceFactory.reset_all_services(services)
            >>> services["redis"].get("key")
            None
        """
        for service in services.values():
            if hasattr(service, "reset"):
                service.reset()
