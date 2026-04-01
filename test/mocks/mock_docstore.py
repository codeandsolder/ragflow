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
Mock DocStore Connection Implementation.

Provides a fast, in-memory mock implementation of document storage operations
for testing without Elasticsearch, Infinity, or OceanBase dependencies.
"""

import threading
from typing import Any

from test.service_abstractions.docstore_connection import AbstractDocStoreConnection


class MockDocStoreConnection(AbstractDocStoreConnection):
    """
    Mock implementation of a document store connection.
    
    This class provides an in-memory document store for fast testing.
    All operations are stored in memory and lost when the instance is destroyed.
    
    Thread-safe for concurrent access.
    
    Example:
        >>> docstore = MockDocStoreConnection()
        >>> docstore.health()
        True
    """

    def __init__(self) -> None:
        """
        Initialize the mock docstore connection.
        
        Creates empty storage dictionaries and synchronization primitives.
        """
        super().__init__()
        self._lock = threading.RLock()
        self._healthy: bool = True
        self._indices: dict[str, dict[str, Any]] = {}

    def health(self) -> bool:
        """
        Check the health status of the mock document store.
        
        Returns:
            Always returns True in mock mode.
            
        Example:
            >>> docstore = MockDocStoreConnection()
            >>> docstore.health()
            True
        """
        return self._healthy

    def set_healthy(self, healthy: bool) -> None:
        """
        Set the health status of the mock document store.
        
        This allows simulating connection failures for testing.
        
        Args:
            healthy: The health status to set.
            
        Example:
            >>> docstore = MockDocStoreConnection()
            >>> docstore.set_healthy(False)
            >>> docstore.health()
            False
        """
        self._healthy = healthy

    def reset(self) -> None:
        """
        Clear all stored data and reset to initial state.
        
        This is useful for ensuring test isolation between test cases.
        
        Example:
            >>> docstore = MockDocStoreConnection()
            >>> docstore._indices["test"] = {"key": "value"}
            >>> docstore.reset()
            >>> len(docstore._indices)
            0
        """
        with self._lock:
            self._indices.clear()
            self._healthy = True

    def __enter__(self) -> "MockDocStoreConnection":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - automatically resets the connection."""
        self.reset()
