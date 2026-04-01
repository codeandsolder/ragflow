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
Abstract Database Connection Interface.

Provides a unified interface for database operations that can be implemented
by both mock and real database connections (MySQL, OceanBase, etc.).
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Type


T = TypeVar('T')


class AbstractDatabaseConnection(ABC):
    """
    Abstract base class for database connections.
    
    This class defines the interface that both mock and real database
    implementations must adhere to for database operations.
    """

    @abstractmethod
    def health(self) -> bool:
        """
        Check the health status of the database connection.
        
        Returns:
            True if the database is healthy, False otherwise.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """
        Close the database connection.
        """
        ...


class AbstractQueryExecutor(ABC):
    """
    Abstract base class for database query execution.
    """

    @abstractmethod
    def execute(self, query: str, parameters: tuple | None = None) -> list[dict]:
        """
        Execute a SQL query.
        
        Args:
            query: The SQL query to execute.
            parameters: Optional parameters for parameterized queries.
            
        Returns:
            A list of dictionaries containing query results.
        """
        ...

    @abstractmethod
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
            The number of rows affected.
        """
        ...

    @abstractmethod
    def fetchone(self, query: str, parameters: tuple | None = None) -> dict | None:
        """
        Execute a query and return the first result.
        
        Args:
            query: The SQL query to execute.
            parameters: Optional parameters for parameterized queries.
            
        Returns:
            A dictionary containing the first result, or None if no results.
        """
        ...


class AbstractORMConnection(ABC):
    """
    Abstract base class for ORM-style database connections.
    """

    @abstractmethod
    def get_model(self, model_class: Type[T]) -> T:
        """
        Get a model instance for database operations.
        
        Args:
            model_class: The model class to get.
            
        Returns:
            An instance of the model class configured for this database.
        """
        ...

    @abstractmethod
    def create_tables(self) -> None:
        """
        Create all tables based on defined models.
        """
        ...

    @abstractmethod
    def drop_tables(self) -> None:
        """
        Drop all tables.
        """
        ...
