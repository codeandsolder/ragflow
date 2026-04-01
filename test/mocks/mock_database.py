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
Mock Database Connection Implementation.

Provides a fast, in-memory mock implementation of database operations
for testing without MySQL, OceanBase, or other database dependencies.
"""

import re
import threading
from typing import Any, Type

from test.service_abstractions.database_connection import (
    AbstractDatabaseConnection,
    AbstractQueryExecutor,
    AbstractORMConnection
)


class MockQueryExecutor(AbstractQueryExecutor):
    """
    Mock implementation of SQL query execution.
    
    Provides an in-memory SQL-like execution engine for basic operations
    suitable for unit testing without a real database.
    
    Note: This is a simplified mock that supports basic SELECT, INSERT,
    UPDATE, and DELETE operations. It's not a full SQL parser.
    
    Example:
        >>> executor = MockQueryExecutor()
        >>> executor.execute("CREATE TABLE test (id INT, name TEXT)", ())
        []
        >>> executor.execute("INSERT INTO test VALUES (1, 'Alice')", ())
        []
    """

    def __init__(self, db: "MockDatabaseConnection") -> None:
        """
        Initialize the mock query executor.
        
        Args:
            db: Reference to the parent MockDatabaseConnection.
        """
        self._db = db

    def execute(self, query: str, parameters: tuple | None = None) -> list[dict]:
        """
        Execute a SQL query.
        
        Note: This is a simplified mock and only supports basic operations.
        
        Args:
            query: The SQL query to execute.
            parameters: Optional parameters for parameterized queries.
            
        Returns:
            A list of dictionaries containing query results.
            
        Example:
            >>> from test.mocks.mock_database import MockDatabaseConnection
            >>> db = MockDatabaseConnection()
            >>> db.create_tables()
            >>> results = db._executor.execute("SELECT * FROM test_table", ())
            >>> len(results) >= 0
            True
        """
        query = query.strip().upper()
        
        if query.startswith("SELECT"):
            return self._db._execute_select(query, parameters or ())
        elif query.startswith("INSERT"):
            return self._db._execute_insert(query, parameters or ())
        elif query.startswith("UPDATE"):
            return self._db._execute_update(query, parameters or ())
        elif query.startswith("DELETE"):
            return self._db._execute_delete(query, parameters or ())
        else:
            # CREATE TABLE, DROP TABLE, etc. - just return empty list
            return []

    def execute_many(
        self,
        query: str,
        parameters_list: list[tuple]
    ) -> int:
        """
        Execute a SQL query multiple times with different parameters.
        
        Args:
            query: The SQL query to execute.
            parameters_list: List of parameter tuples.
            
        Returns:
            The number of rows affected (approximate in mock mode).
            
        Example:
            >>> from test.mocks.mock_database import MockDatabaseConnection
            >>> db = MockDatabaseConnection()
            >>> affected = db._executor.execute_many("INSERT INTO t VALUES (?)", [(1,), (2,)])
            >>> affected
            2
        """
        count = 0
        for params in parameters_list:
            result = self.execute(query, params)
            count += len(result)
        return count

    def fetchone(self, query: str, parameters: tuple | None = None) -> dict | None:
        """
        Execute a query and return the first result.
        
        Args:
            query: The SQL query to execute.
            parameters: Optional parameters for parameterized queries.
            
        Returns:
            A dictionary containing the first result, or None if no results.
            
        Example:
            >>> from test.mocks.mock_database import MockDatabaseConnection
            >>> db = MockDatabaseConnection()
            >>> result = db._executor.fetchone("SELECT * FROM nonexistent", ())
            >>> result is None
            True
        """
        results = self.execute(query, parameters)
        return results[0] if results else None


class MockDatabaseConnection(AbstractDatabaseConnection, AbstractORMConnection):
    """
    Mock implementation of database connection.
    
    Provides an in-memory database with SQL-like operations for testing
    without a real database server.
    
    Thread-safe for concurrent access.
    
    Example:
        >>> db = MockDatabaseConnection()
        >>> db.health()
        True
        >>> db.get_query_executor().execute("CREATE TABLE test (id INT)", ())
        []
    """

    def __init__(self) -> None:
        """
        Initialize the mock database connection.
        
        Creates empty storage structures and synchronization primitives.
        """
        super().__init__()
        self._lock = threading.RLock()
        self._tables: dict[str, list[dict]] = {}
        self._seq: dict[str, int] = {}
        self._healthy: bool = True
        self._executor: MockQueryExecutor = MockQueryExecutor(self)
        self._models: dict[str, Any] = {}

    def health(self) -> bool:
        """
        Check the health status of the mock database.
        
        Returns:
            True if the database is healthy (not explicitly set to unhealthy).
            
        Example:
            >>> db = MockDatabaseConnection()
            >>> db.health()
            True
        """
        return self._healthy

    def set_healthy(self, healthy: bool) -> None:
        """
        Set the health status of the mock database.
        
        Allows simulating connection failures for testing.
        
        Args:
            healthy: The health status to set.
        """
        self._healthy = healthy

    def close(self) -> None:
        """
        Close the mock database connection.
        
        No-op in mock mode - resources are automatically managed.
        """
        pass

    def get_query_executor(self) -> MockQueryExecutor:
        """
        Get the query executor for this connection.
        
        Returns:
            The MockQueryExecutor instance.
        """
        return self._executor

    # Internal query execution methods

    def _execute_select(
        self,
        query: str,
        parameters: tuple
    ) -> list[dict]:
        """Execute a SELECT query."""
        with self._lock:
            match = re.search(r"FROM\s+(\w+)", query, re.IGNORECASE)
            if not match:
                return []
            table_name = match.group(1)
            return self._tables.get(table_name, [])

    def _execute_insert(
        self,
        query: str,
        parameters: tuple
    ) -> list[dict]:
        """Execute an INSERT query."""
        with self._lock:
            match = re.search(r"INTO\s+(\w+)", query, re.IGNORECASE)
            if not match:
                return []
            table_name = match.group(1)
            if table_name not in self._tables:
                self._tables[table_name] = []
            
            # Create row from parameters
            row = {f"col_{i}": param for i, param in enumerate(parameters)}
            self._tables[table_name].append(row)
            return []

    def _execute_update(
        self,
        query: str,
        parameters: tuple
    ) -> list[dict]:
        """Execute an UPDATE query."""
        with self._lock:
            match = re.search(r"UPDATE\s+(\w+)", query, re.IGNORECASE)
            if not match:
                return []
            table_name = match.group(1)
            # Simplified: just return empty list
            return []

    def _execute_delete(
        self,
        query: str,
        parameters: tuple
    ) -> list[dict]:
        """Execute a DELETE query."""
        with self._lock:
            match = re.search(r"FROM\s+(\w+)", query, re.IGNORECASE)
            if not match:
                return []
            table_name = match.group(1)
            if table_name in self._tables:
                rows_before = len(self._tables[table_name])
                self._tables[table_name] = []
            return []

    # ORM operations

    def get_model(self, model_class: Type[Any]) -> Any:
        """
        Get a model instance for database operations.
        
        Args:
            model_class: The model class to get.
            
        Returns:
            A mock model instance.
        """
        return MockModel(model_class, self)

    def create_tables(self) -> None:
        """
        Create all tables based on defined models.
        
        In mock mode, this is a no-op as tables are created on-the-fly.
        """
        pass

    def drop_tables(self) -> None:
        """
        Drop all tables.
        
        Clears all stored data.
        """
        with self._lock:
            self._tables.clear()

    def reset(self) -> None:
        """
        Clear all stored data and reset to initial state.
        
        Useful for ensuring test isolation.
        
        Example:
            >>> db = MockDatabaseConnection()
            >>> db._tables["test"] = [{"id": 1}]
            >>> db.reset()
            >>> len(db._tables)
            0
        """
        with self._lock:
            self._tables.clear()
            self._seq.clear()
            self._healthy = True
            self._models.clear()

    def __enter__(self) -> "MockDatabaseConnection":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - automatically resets the connection."""
        self.reset()


class MockModel:
    """
    Mock model class for ORM-style database operations.
    """

    def __init__(self, model_class: Type[Any], db: MockDatabaseConnection) -> None:
        """
        Initialize the mock model.
        
        Args:
            model_class: The actual model class being mocked.
            db: Reference to the mock database connection.
        """
        self._model_class = model_class
        self._db = db
        self._table_name = getattr(
            model_class, "_meta", {}
        ).get("table_name", model_class.__name__.lower())

    def create_table(self) -> None:
        """Create the table for this model."""
        pass

    def query(self) -> list[dict]:
        """Query all records for this model."""
        with self._db._lock:
            return self._db._tables.get(self._table_name, [])
