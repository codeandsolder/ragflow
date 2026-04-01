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
Mock MinIO Storage Implementation.

Provides a fast, in-memory mock implementation of MinIO object storage
for testing without MinIO server dependencies.
"""

import threading
from io import BytesIO
from typing import Any
from datetime import datetime

from test.service_abstractions.minio_connection import AbstractMinioStorage


class MockMinioStorage(AbstractMinioStorage):
    """
    Mock implementation of MinIO object storage.
    
    Provides an in-memory object store with bucket and object management
    for testing without a MinIO server.
    
    Thread-safe for concurrent access.
    
    Example:
        >>> minio = MockMinioStorage()
        >>> data = BytesIO(b"test content")
        >>> minio.upload("bucket1", "object1", data, 12)
        True
        >>> minio.exists("bucket1", "object1")
        True
    """

    def __init__(self) -> None:
        """
        Initialize the mock MinIO storage.
        
        Creates empty bucket and object storage dictionaries.
        """
        super().__init__()
        self._lock = threading.RLock()
        self._buckets: dict[str, dict[str, bytes]] = {}
        self._metadata: dict[str, dict[str, dict[str, Any]]] = {}
        self._healthy: bool = True

    def health(self) -> bool:
        """
        Check the health status of the mock MinIO.
        
        Returns:
            True if MinIO is healthy (not explicitly set to unhealthy).
            
        Example:
            >>> minio = MockMinioStorage()
            >>> minio.health()
            True
        """
        return self._healthy

    def set_healthy(self, healthy: bool) -> None:
        """
        Set the health status of the mock MinIO.
        
        Allows simulating connection failures for testing.
        
        Args:
            healthy: The health status to set.
        """
        self._healthy = healthy

    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """Create bucket if it doesn't exist."""
        if bucket_name not in self._buckets:
            self._buckets[bucket_name] = {}
            self._metadata[bucket_name] = {}

    def upload(
        self,
        bucket_name: str,
        object_name: str,
        data: BytesIO,
        length: int = -1
    ) -> bool:
        """
        Upload data to the mock MinIO.
        
        Args:
            bucket_name: The name of the bucket.
            object_name: The name of the object.
            data: The data to upload as BytesIO.
            length: The length of data (ignored in mock).
            
        Returns:
            True if upload succeeded.
            
        Example:
            >>> minio = MockMinioStorage()
            >>> data = BytesIO(b"test content")
            >>> minio.upload("bucket1", "object1", data, 12)
            True
        """
        with self._lock:
            self._ensure_bucket_exists(bucket_name)
            content = data.read()
            self._buckets[bucket_name][object_name] = content
            self._metadata[bucket_name][object_name] = {
                "size": len(content),
                "last_modified": datetime.now().isoformat(),
                "etag": f"mock-{hash(content)}"
            }
            return True

    def download(self, bucket_name: str, object_name: str) -> BytesIO:
        """
        Download data from the mock MinIO.
        
        Args:
            bucket_name: The name of the bucket.
            object_name: The name of the object.
            
        Returns:
            The downloaded data as BytesIO.
            
        Raises:
            Exception: If the object does not exist.
            
        Example:
            >>> minio = MockMinioStorage()
            >>> data = BytesIO(b"test content")
            >>> minio.upload("bucket1", "object1", data, 12)
            >>> result = minio.download("bucket1", "object1")
            >>> result.read()
            b'test content'
        """
        with self._lock:
            if bucket_name not in self._buckets:
                raise Exception(f"Bucket '{bucket_name}' does not exist")
            if object_name not in self._buckets[bucket_name]:
                raise Exception(f"Object '{object_name}' does not exist in bucket '{bucket_name}'")
            return BytesIO(self._buckets[bucket_name][object_name])

    def delete(self, bucket_name: str, object_name: str) -> bool:
        """
        Delete an object from the mock MinIO.
        
        Args:
            bucket_name: The name of the bucket.
            object_name: The name of the object.
            
        Returns:
            True if deletion succeeded.
            
        Example:
            >>> minio = MockMinioStorage()
            >>> data = BytesIO(b"test content")
            >>> minio.upload("bucket1", "object1", data, 12)
            >>> minio.delete("bucket1", "object1")
            True
            >>> minio.exists("bucket1", "object1")
            False
        """
        with self._lock:
            if bucket_name not in self._buckets:
                return False
            if object_name not in self._buckets[bucket_name]:
                return False
            del self._buckets[bucket_name][object_name]
            del self._metadata[bucket_name][object_name]
            return True

    def exists(self, bucket_name: str, object_name: str) -> bool:
        """
        Check if an object exists in the mock MinIO.
        
        Args:
            bucket_name: The name of the bucket.
            object_name: The name of the object.
            
        Returns:
            True if the object exists, False otherwise.
            
        Example:
            >>> minio = MockMinioStorage()
            >>> minio.exists("bucket1", "object1")
            False
            >>> data = BytesIO(b"test")
            >>> minio.upload("bucket1", "object1", data, 4)
            >>> minio.exists("bucket1", "object1")
            True
        """
        with self._lock:
            return (
                bucket_name in self._buckets and
                object_name in self._buckets[bucket_name]
            )

    def get_object_info(
        self,
        bucket_name: str,
        object_name: str
    ) -> dict[str, Any] | None:
        """
        Get information about an object in the mock MinIO.
        
        Args:
            bucket_name: The name of the bucket.
            object_name: The name of the object.
            
        Returns:
            A dictionary containing object metadata, or None if not found.
            
        Example:
            >>> minio = MockMinioStorage()
            >>> data = BytesIO(b"test content")
            >>> minio.upload("bucket1", "object1", data, 12)
            >>> info = minio.get_object_info("bucket1", "object1")
            >>> info["size"]
            12
        """
        with self._lock:
            if bucket_name not in self._metadata:
                return None
            return self._metadata[bucket_name].get(object_name)

    def reset(self) -> None:
        """
        Clear all stored data and reset to initial state.
        
        Useful for ensuring test isolation.
        
        Example:
            >>> minio = MockMinioStorage()
            >>> data = BytesIO(b"test")
            >>> minio.upload("bucket1", "object1", data, 4)
            >>> minio.reset()
            >>> minio.exists("bucket1", "object1")
            False
        """
        with self._lock:
            self._buckets.clear()
            self._metadata.clear()
            self._healthy = True

    def __enter__(self) -> "MockMinioStorage":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - automatically resets the connection."""
        self.reset()
