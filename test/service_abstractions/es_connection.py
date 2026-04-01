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
Abstract Elasticsearch Connection Interface

Provides a unified interface for Elasticsearch operations that can be implemented
by both mock and real Elasticsearch connections.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypedDict


class ESSearchResult(TypedDict):
    """Type definition for ES search results."""
    hits: Dict[str, Any]
    total: int


class AbstractESConnection(ABC):
    """
    Abstract base class for Elasticsearch connection operations.
    
    This class defines the interface that both mock and real Elasticsearch
    implementations must adhere to.
    """
    
    @abstractmethod
    def health(self) -> bool:
        """
        Check the health status of the Elasticsearch cluster.
        
        Returns:
            True if ES is healthy, False otherwise.
        """
        ...
    
    @abstractmethod
    def search(
        self,
        index_names: List[str],
        query: Dict[str, Any],
        track_total_hits: bool = True
    ) -> ESSearchResult:
        """
        Execute a search query against Elasticsearch.
        
        Args:
            index_names: List of index names to search
            query: Query DSL dictionary
            track_total_hits: Whether to track total hits
            
        Returns:
            Search result dictionary
        """
        ...
    
    @abstractmethod
    def create_index(
        self,
        index_name: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create an Elasticsearch index.
        
        Args:
            index_name: Name of the index to create
            settings: Optional index settings
            
        Returns:
            True if creation succeeded, False otherwise
        """
        ...
    
    @abstractmethod
    def delete_index(self, index_name: str) -> bool:
        """
        Delete an Elasticsearch index.
        
        Args:
            index_name: Name of the index to delete
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        ...
    
    @abstractmethod
    def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists.
        
        Args:
            index_name: Name of the index to check
            
        Returns:
            True if index exists, False otherwise
        """
        ...
    
    @abstractmethod
    def insert(
        self,
        index_name: str,
        doc_id: str,
        document: Dict[str, Any]
    ) -> bool:
        """
        Insert a document into an index.
        
        Args:
            index_name: Name of the index
            doc_id: Document ID
            document: Document data
            
        Returns:
            True if insertion succeeded, False otherwise
        """
        ...
    
    @abstractmethod
    def update(
        self,
        index_name: str,
        doc_id: str,
        document: Dict[str, Any]
    ) -> bool:
        """
        Update a document in an index.
        
        Args:
            index_name: Name of the index
            doc_id: Document ID
            document: Document update data
            
        Returns:
            True if update succeeded, False otherwise
        """
        ...
    
    @abstractmethod
    def delete(
        self,
        index_name: str,
        doc_id: str
    ) -> bool:
        """
        Delete a document from an index.
        
        Args:
            index_name: Name of the index
            doc_id: Document ID
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        ...
    
    @abstractmethod
    def get(
        self,
        index_name: str,
        doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            index_name: Name of the index
            doc_id: Document ID
            
        Returns:
            Document dictionary or None if not found
        """
        ...


class ESConnectionProtocol(Protocol):
    """Protocol for type checking ES connections."""
    
    def health(self) -> bool: ...
    def search(self, index_names: List[str], query: Dict[str, Any], 
               track_total_hits: bool = True) -> ESSearchResult: ...
    def create_index(self, index_name: str, 
                     settings: Optional[Dict[str, Any]] = None) -> bool: ...
    def delete_index(self, index_name: str) -> bool: ...
    def index_exists(self, index_name: str) -> bool: ...
    def insert(self, index_name: str, doc_id: str, 
               document: Dict[str, Any]) -> bool: ...
    def update(self, index_name: str, doc_id: str, 
               document: Dict[str, Any]) -> bool: ...
    def delete(self, index_name: str, doc_id: str) -> bool: ...
    def get(self, index_name: str, doc_id: str) -> Optional[Dict[str, Any]]: ...
