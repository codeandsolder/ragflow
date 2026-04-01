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
Abstract MinIO Storage Interface.

Provides a unified interface for MinIO object storage operations that can be
implemented by both mock and real MinIO clients.
"""

from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any


class AbstractMinioStorage(ABC):
    """
    Abstract base class for MinIO object storage operations.
    
    This class defines the interface that both mock and real MinIO
    implementations must adhere to for object storage operations.
    """

    @abstractmethod
    def health(self) -> bool:
        """
        Check the health status of the MinIO connection.
        
        Returns:
            True if MinIO is healthy, False otherwise.
        """
        ...

    @abstractmethod
    def upload(
        self,
        bucket_name: str,
        object_name: str,
        data: BytesIO,
        length: int = -1
    ) -> bool:
        """
        Upload data to MinIO.
        
        Args:
            bucket_name: The name of the bucket.
            object_name: The name of the object.
            data: The data to upload as BytesIO.
            length: The length of data (-1 for auto-detect).
            
        Returns:
            True if upload succeeded, False otherwise.
        """
        ...

    @abstractmethod
    def download(self, bucket_name: str, object_name: str) -> BytesIO:
        """
        Download data from MinIO.
        
        Args:
            bucket_name: The name of the bucket.
            object_name: The name of the object.
            
        Returns:
            The downloaded data as BytesIO.
            
        Raises:
            Exception: If the object does not exist.
        """
        ...

    @abstractmethod
    def delete(self, bucket_name: str, object_name: str) -> bool:
        """
        Delete an object from MinIO.
        
        Args:
            bucket_name: The name of the bucket.
            object_name: The name of the object.
            
        Returns:
            True if deletion succeeded, False otherwise.
        """
        ...

    @abstractmethod
    def exists(self, bucket_name: str, object_name: str) -> bool:
        """
        Check if an object exists in MinIO.
        
        Args:
            bucket_name: The name of the bucket.
            object_name: The name of the object.
            
        Returns:
            True if the object exists, False otherwise.
        """
        ...

    @abstractmethod
    def get_object_info(
        self,
        bucket_name: str,
        object_name: str
    ) -> dict[str, Any] | None:
        """
        Get information about an object in MinIO.
        
        Args:
            bucket_name: The name of the bucket.
            object_name: The name of the object.
            
        Returns:
            A dictionary containing object metadata, or None if not found.
        """
        ...
