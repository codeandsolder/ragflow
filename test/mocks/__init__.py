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
#  ruff: noqa
"""
Mock Service Implementations for Two-Tier Mocking System.

This module provides lightweight, fast mock implementations of external services
for use in local development and unit testing without Docker dependencies.
"""

from .mock_docstore import MockDocStoreConnection
from .mock_redis import MockRedisDB, MockRedisMsg
from .mock_minio import MockMinioStorage
from .mock_database import MockDatabaseConnection, MockQueryExecutor
from .factory import MockServiceFactory

__all__ = [
    "MockDocStoreConnection",
    "MockRedisDB",
    "MockRedisMsg",
    "MockMinioStorage",
    "MockDatabaseConnection",
    "MockQueryExecutor",
    "MockServiceFactory",
]
