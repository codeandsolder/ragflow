#
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
Test data factories for creating consistent test data.

This module provides factory classes for generating test data following
the Factory Boy pattern, enabling consistent and reusable test data creation.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional


class BaseFactory:
    """Base class for all test data factories."""

    _counter = 0

    @classmethod
    def reset_counter(cls):
        """Reset the factory counter."""
        cls._counter = 0

    @classmethod
    def _generate_id(cls, prefix: str = "") -> str:
        """Generate a unique ID."""
        cls._counter += 1
        return f"{prefix}{cls._counter}_{uuid.uuid4().hex[:8]}"

    @classmethod
    def build(cls, **kwargs) -> dict:
        """Build a single instance with overrides."""
        raise NotImplementedError

    @classmethod
    def create_batch(cls, count: int, **kwargs) -> list:
        """Create multiple instances."""
        return [cls.build(**kwargs) for _ in range(count)]


class UserFactory(BaseFactory):
    """Factory for creating user test data."""

    @classmethod
    def build(
        cls,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
        status: str = "active",
        created_at: Optional[datetime] = None,
        **kwargs
    ) -> dict:
        """Build a user data object."""
        return {
            "id": user_id or cls._generate_id("u"),
            "tenant_id": tenant_id or cls._generate_id("t"),
            "email": email or f"user_{cls._counter}@example.com",
            "name": name or f"Test User {cls._counter}",
            "status": status,
            "created_at": created_at or datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **kwargs,
        }


class KnowledgeBaseFactory(BaseFactory):
    """Factory for creating knowledge base test data."""

    @classmethod
    def build(
        cls,
        kb_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        name: Optional[str] = None,
        description: str = "Test knowledge base",
        embd_id: str = "default-embedding",
        parser_method: str = "naive",
        chunk_method: str = "naive",
        status: str = "1",
        **kwargs
    ) -> dict:
        """Build a knowledge base data object."""
        return {
            "id": kb_id or cls._generate_id("kb"),
            "tenant_id": tenant_id or cls._generate_id("t"),
            "name": name or f"Knowledge Base {cls._counter}",
            "description": description,
            "embd_id": embd_id,
            "parser_method": parser_method,
            "chunk_method": chunk_method,
            "status": status,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **kwargs,
        }


class DocumentFactory(BaseFactory):
    """Factory for creating document test data."""

    @classmethod
    def build(
        cls,
        doc_id: Optional[str] = None,
        kb_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        name: Optional[str] = None,
        size: int = 1024,
        type: str = "docx",
        status: str = "1",
        char_length: int = 1000,
        chunk_count: int = 10,
        created_at: Optional[datetime] = None,
        **kwargs
    ) -> dict:
        """Build a document data object."""
        return {
            "id": doc_id or cls._generate_id("doc"),
            "kb_id": kb_id or cls._generate_id("kb"),
            "tenant_id": tenant_id or cls._generate_id("t"),
            "name": name or f"document_{cls._counter}.{type}",
            "size": size,
            "type": type,
            "status": status,
            "char_length": char_length,
            "chunk_count": chunk_count,
            "created_at": (created_at or datetime.utcnow()).isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "created_by": cls._generate_id("u"),
            **kwargs,
        }


class ChunkFactory(BaseFactory):
    """Factory for creating chunk test data."""

    @classmethod
    def build(
        cls,
        chunk_id: Optional[str] = None,
        doc_id: Optional[str] = None,
        content: Optional[str] = None,
        offset: int = 0,
        length: int = 512,
        page_idx: int = 0,
        positions: Optional[list] = None,
        **kwargs
    ) -> dict:
        """Build a chunk data object."""
        text_content = content or f"This is test chunk content number {cls._counter}. " * 10
        return {
            "id": chunk_id or cls._generate_id("chunk"),
            "doc_id": doc_id or cls._generate_id("doc"),
            "content": text_content,
            "content_length": length,
            "offset": offset,
            "page_idx": page_idx,
            "positions": positions or [[0, 100], [100, 200]],
            "vector": [0.1] * 768,
            "token_length": len(text_content.split()),
            **kwargs,
        }


class DialogSessionFactory(BaseFactory):
    """Factory for creating dialog session test data."""

    @classmethod
    def build(
        cls,
        dialog_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        name: str = "New Chat",
        messages: Optional[list] = None,
        **kwargs
    ) -> dict:
        """Build a dialog session data object."""
        return {
            "id": session_id or cls._generate_id("sess"),
            "dialog_id": dialog_id or cls._generate_id("d"),
            "tenant_id": tenant_id or cls._generate_id("t"),
            "user_id": user_id or cls._generate_id("u"),
            "name": name,
            "messages": messages or [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **kwargs,
        }


class MessageFactory(BaseFactory):
    """Factory for creating message test data."""

    @classmethod
    def build(
        cls,
        message_id: Optional[str] = None,
        session_id: Optional[str] = None,
        role: str = "user",
        content: Optional[str] = None,
        citation: Optional[list] = None,
        agent_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        **kwargs
    ) -> dict:
        """Build a message data object."""
        return {
            "id": message_id or cls._generate_id("msg"),
            "session_id": session_id or cls._generate_id("sess"),
            "role": role,
            "content": content or f"Test message content {cls._counter}",
            "citation": citation or [],
            "agent_id": agent_id,
            "created_at": (created_at or datetime.utcnow()).isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **kwargs,
        }


class AgentFactory(BaseFactory):
    """Factory for creating agent test data."""

    @classmethod
    def build(
        cls,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        name: str = "Test Agent",
        description: str = "Test agent description",
        llm_id: str = "default-llm",
        prompt: str = "You are a helpful assistant.",
        **kwargs
    ) -> dict:
        """Build an agent data object."""
        return {
            "id": agent_id or cls._generate_id("agent"),
            "tenant_id": tenant_id or cls._generate_id("t"),
            "name": name,
            "description": description,
            "llm_id": llm_id,
            "prompt": prompt,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **kwargs,
        }


class EmbeddingFactory(BaseFactory):
    """Factory for creating embedding test data."""

    @classmethod
    def build(
        cls,
        chunk_id: Optional[str] = None,
        vector: Optional[list] = None,
        dimension: int = 768,
        model: str = "default-embedding",
        **kwargs
    ) -> dict:
        """Build an embedding data object."""
        import random

        return {
            "chunk_id": chunk_id or cls._generate_id("chunk"),
            "vector": vector or [random.random() for _ in range(dimension)],
            "dimension": dimension,
            "model": model,
            "created_at": datetime.utcnow().isoformat(),
            **kwargs,
        }


class ApiResponseFactory(BaseFactory):
    """Factory for creating API response test data."""

    @classmethod
    def build(
        cls,
        code: int = 0,
        message: str = "success",
        data: Any = None,
        **kwargs
    ) -> dict:
        """Build an API response data object."""
        return {
            "code": code,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs,
        }

    @classmethod
    def build_error(cls, message: str = "error", code: int = 400, **kwargs) -> dict:
        """Build an error API response."""
        return cls.build(code=code, message=message, **kwargs)

    @classmethod
    def build_success(cls, data: Any = None, message: str = "success", **kwargs) -> dict:
        """Build a success API response."""
        return cls.build(code=0, message=message, data=data, **kwargs)


class FileFactory(BaseFactory):
    """Factory for creating file test data."""

    @classmethod
    def build(
        cls,
        filename: Optional[str] = None,
        content_type: str = "application/octet-stream",
        size: int = 1024,
        **kwargs
    ) -> dict:
        """Build a file data object."""
        return {
            "filename": filename or f"file_{cls._counter}.txt",
            "content_type": content_type,
            "size": size,
            "created_at": datetime.utcnow().isoformat(),
            **kwargs,
        }


class ConfigFactory(BaseFactory):
    """Factory for creating configuration test data."""

    @classmethod
    def build(
        cls,
        key: Optional[str] = None,
        value: Any = None,
        category: str = "general",
        description: str = "",
        **kwargs
    ) -> dict:
        """Build a config data object."""
        return {
            "key": key or f"config_key_{cls._counter}",
            "value": value,
            "category": category,
            "description": description,
            "updated_at": datetime.utcnow().isoformat(),
            **kwargs,
        }
