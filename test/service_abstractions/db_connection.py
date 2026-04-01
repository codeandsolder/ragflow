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
Abstract Database Connection Interface

Provides a unified interface for MySQL/PostgreSQL database operations
that can be implemented by both mock and real database connections.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union
from contextlib import contextmanager

T = TypeVar('T')


class AbstractDBConnection(ABC):
    """
    Abstract base class for database connection operations.
    
    This class defines the interface that both mock and real database
    implementations must adhere to. Supports MySQL and PostgreSQL.
    """
    
    @abstractmethod
    def health(self) -> bool:
        """
        Check the health status of the database connection.
        
        Returns:
            True if database is healthy, False otherwise.
        """
        ...
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if connection succeeded, False otherwise
        """
        ...
    
    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        ...
    
    @abstractmethod
    def execute(self, sql: str, parameters: Optional[tuple] = None) -> int:
        """
        Execute a SQL query.
        
        Args:
            sql: SQL query string
            parameters: Query parameters
            
        Returns:
            Number of affected rows
        """
        ...
    
    @abstractmethod
    def fetchone(
        self,
        sql: str,
        parameters: Optional[tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from query result.
        
        Args:
            sql: SQL query string
            parameters: Query parameters
            
        Returns:
            Dictionary representing the row, or None if not found
        """
        ...
    
    @abstractmethod
    def fetchall(
        self,
        sql: str,
        parameters: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all rows from query result.
        
        Args:
            sql: SQL query string
            parameters: Query parameters
            
        Returns:
            List of dictionaries representing rows
        """
        ...
    
    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a database transaction."""
        ...
    
    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        ...
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        ...
    
    @contextmanager
    @abstractmethod
    def transaction(self):
        """
        Context manager for database transactions.
        
        Yields:
            Database connection for use within transaction
            
        Example:
            >>> with db.transaction() as conn:
            ...     conn.execute("INSERT INTO users VALUES (%s, %s)", (id, name))
        """
        ...


class DBConnectionProtocol(Protocol):
    """Protocol for type checking database connections."""
    
    def health(self) -> bool: ...
    def connect(self) -> bool: ...
    def close(self) -> None: ...
    def execute(self, sql: str, parameters: Optional[tuple] = None) -> int: ...
    def fetchone(self, sql: str, parameters: Optional[tuple] = None) -> Optional[Dict[str, Any]]: ...
    def fetchall(self, sql: str, parameters: Optional[tuple] = None) -> List[Dict[str, Any]]: ...
    def begin_transaction(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
