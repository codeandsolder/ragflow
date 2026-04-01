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
Abstract Redis Connection Interface.

Provides a unified interface for Redis operations that can be implemented
by both mock and real Redis connections.
"""

from abc import ABC, abstractmethod
from typing import Any


class AbstractRedisDB(ABC):
    """
    Abstract base class for Redis database operations.
    
    This class defines the interface that both mock and real Redis
    implementations must adhere to.
    """

    @abstractmethod
    def health(self) -> bool:
        """
        Check the health status of the Redis connection.
        
        Returns:
            True if Redis is healthy, False otherwise.
        """
        ...

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """
        Get a value from Redis by key.
        
        Args:
            key: The key to retrieve.
            
        Returns:
            The value associated with the key, or None if not found.
        """
        ...

    @abstractmethod
    def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None
    ) -> bool:
        """
        Set a key-value pair in Redis.
        
        Args:
            key: The key to set.
            value: The value to associate with the key.
            expire: Optional expiration time in seconds.
            
        Returns:
            True if the operation succeeded, False otherwise.
        """
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key: The key to delete.
            
        Returns:
            True if the key was deleted, False otherwise.
        """
        ...


class AbstractRedisMsg(ABC):
    """
    Abstract base class for Redis message operations.
    """

    @abstractmethod
    def ack(self) -> bool:
        """
        Acknowledge the message.
        
        Returns:
            True if acknowledgment succeeded, False otherwise.
        """
        ...

    @abstractmethod
    def get_message(self) -> dict:
        """
        Get the message content.
        
        Returns:
            The message content as a dictionary.
        """
        ...
