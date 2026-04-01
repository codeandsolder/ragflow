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
Mock Redis Implementation.

Provides a fast, in-memory mock implementation of Redis operations
for testing without Redis server dependencies.
"""

import json
import threading
import time
from typing import Any

from test.service_abstractions.redis_connection import AbstractRedisDB, AbstractRedisMsg


class MockRedisMsg(AbstractRedisMsg):
    """
    Mock implementation of a Redis message.
    
    Simulates message acknowledgment and content retrieval for stream operations.
    
    Example:
        >>> msg = MockRedisMsg("consumer1", "queue1", "group1", "msg1", {"message": '{"data": "test"}'}, MockRedisDB())
        >>> msg.get_message()
        {'data': 'test'}
    """

    def __init__(
        self,
        consumer: str,
        queue_name: str,
        group_name: str,
        msg_id: str,
        message: dict,
        redis_instance: "MockRedisDB"
    ) -> None:
        """
        Initialize a mock Redis message.
        
        Args:
            consumer: The consumer identifier.
            queue_name: The name of the queue/stream.
            group_name: The name of the consumer group.
            msg_id: The message ID.
            message: The raw message data.
            redis_instance: Reference to the parent MockRedisDB instance.
        """
        self._consumer = consumer
        self._queue_name = queue_name
        self._group_name = group_name
        self._msg_id = msg_id
        self._message_data = message
        self._redis = redis_instance
        self._acked = False

    def ack(self) -> bool:
        """
        Acknowledge the message.
        
        Marks the message as acknowledged in the mock system.
        
        Returns:
            True if acknowledgment succeeded.
            
        Example:
            >>> msg = MockRedisMsg("c1", "q1", "g1", "m1", {"message": "{}"}, MockRedisDB())
            >>> msg.ack()
            True
            >>> msg._acked
            True
        """
        self._acked = True
        return True

    def get_message(self) -> dict:
        """
        Get the message content.
        
        Returns:
            The message content as a dictionary.
            
        Example:
            >>> msg = MockRedisMsg("c1", "q1", "g1", "m1", {"message": '{"key": "value"}'}, MockRedisDB())
            >>> msg.get_message()
            {'key': 'value'}
        """
        if "message" in self._message_data:
            return json.loads(self._message_data["message"])
        return self._message_data

    def get_msg_id(self) -> str:
        """
        Get the message ID.
        
        Returns:
            The message ID as a string.
        """
        return self._msg_id


class MockRedisDB(AbstractRedisDB):
    """
    Mock implementation of Redis database operations.
    
    Provides an in-memory key-value store with TTL support and stream operations
    for testing without a Redis server.
    
    Thread-safe for concurrent access.
    
    Example:
        >>> redis = MockRedisDB()
        >>> redis.set("key", "value")
        True
        >>> redis.get("key")
        'value'
    """

    def __init__(self) -> None:
        """
        Initialize the mock Redis database.
        
        Creates empty storage dictionaries and synchronization primitives.
        """
        super().__init__()
        self._lock = threading.RLock()
        self._data: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}
        self._healthy: bool = True
        self._streams: dict[str, list[dict]] = {}

    def health(self) -> bool:
        """
        Check the health status of the mock Redis.
        
        Returns:
            True if Redis is healthy (not explicitly set to unhealthy).
            
        Example:
            >>> redis = MockRedisDB()
            >>> redis.health()
            True
        """
        return self._healthy

    def set_healthy(self, healthy: bool) -> None:
        """
        Set the health status of the mock Redis.
        
        Allows simulating connection failures for testing.
        
        Args:
            healthy: The health status to set.
        """
        self._healthy = healthy

    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired."""
        if key not in self._expiry:
            return False
        return time.time() > self._expiry[key]

    def _cleanup_expired(self) -> None:
        """Remove expired keys."""
        expired_keys = [
            key for key in self._expiry if self._is_expired(key)
        ]
        for key in expired_keys:
            self._data.pop(key, None)
            del self._expiry[key]

    def get(self, key: str) -> Any | None:
        """
        Get a value from the mock Redis by key.
        
        Args:
            key: The key to retrieve.
            
        Returns:
            The value associated with the key, or None if not found or expired.
            
        Example:
            >>> redis = MockRedisDB()
            >>> redis.set("key", "value")
            >>> redis.get("key")
            'value'
            >>> redis.get("nonexistent")
            None
        """
        with self._lock:
            self._cleanup_expired()
            if self._is_expired(key):
                return None
            return self._data.get(key)

    def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None
    ) -> bool:
        """
        Set a key-value pair in the mock Redis.
        
        Args:
            key: The key to set.
            value: The value to associate.
            expire: Optional expiration time in seconds.
            
        Returns:
            True if the operation succeeded.
            
        Example:
            >>> redis = MockRedisDB()
            >>> redis.set("key", "value")
            True
        """
        with self._lock:
            self._data[key] = value
            if expire is not None:
                self._expiry[key] = time.time() + expire
            else:
                self._expiry.pop(key, None)
            return True

    def delete(self, key: str) -> bool:
        """
        Delete a key from the mock Redis.
        
        Args:
            key: The key to delete.
            
        Returns:
            True if the key was deleted (existed), False otherwise.
            
        Example:
            >>> redis = MockRedisDB()
            >>> redis.set("key", "value")
            >>> redis.delete("key")
            True
            >>> redis.delete("key")
            False
        """
        with self._lock:
            self._expiry.pop(key, None)
            return self._data.pop(key, None) is not None

    def reset(self) -> None:
        """
        Clear all stored data and reset to initial state.
        
        Useful for ensuring test isolation.
        
        Example:
            >>> redis = MockRedisDB()
            >>> redis.set("key", "value")
            >>> redis.reset()
            >>> redis.get("key")
            None
        """
        with self._lock:
            self._data.clear()
            self._expiry.clear()
            self._streams.clear()
            self._healthy = True

    def __enter__(self) -> "MockRedisDB":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - automatically resets the connection."""
        self.reset()
