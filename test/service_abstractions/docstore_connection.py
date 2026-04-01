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
Abstract DocStore Connection Interface.

Provides a unified interface for document store connections (Elasticsearch, Infinity, OceanBase)
that can be implemented by both mock and real service implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol


class AbstractDocStoreConnection(ABC):
    """
    Abstract base class for document store connections.
    
    This class defines the interface that both mock and real implementations
    must adhere to for document storage operations.
    """

    @abstractmethod
    def health(self) -> bool:
        """
        Check the health status of the document store.
        
        Returns:
            True if the document store is healthy, False otherwise.
        """
        ...


class DocStoreConnectionProtocol(Protocol):
    """Protocol for type checking docstore connections."""

    def health(self) -> bool: ...
