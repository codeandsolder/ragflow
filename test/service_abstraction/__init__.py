"""
Abstract Service Interfaces for RAGFlow Testing Framework

This module defines abstract base classes for all external services used in RAGFlow.
These interfaces enable the two-tier mocking system by providing a common contract
for both mock and real service implementations.

Service Categories:
- Document Storage Services (Elasticsearch, Infinity, OceanBase, OpenSearch)
- Cache Services (Redis)
- Object Storage Services (MinIO, S3, Azure, OSS, GCS)
- Database Services (MySQL, PostgreSQL, OceanBase)
- LLM Services
- External API Services
"""

import abc
from typing import Any, Dict, List, Optional, Union, AsyncGenerator, TypeVar
import logging

logger = logging.getLogger(__name__)


class BaseService(abc.ABC):
    """Base interface for all services"""
    
    @abc.abstractmethod
    async def connect(self) -> None:
        """Connect to the service"""
        pass
    
    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the service"""
        pass
    
    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Check service health"""
        pass


class DocumentStorageService(BaseService):
    """Interface for document storage services"""
    
    @abc.abstractmethod
    async def index_document(self, index: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """Index a document"""
        pass
    
    @abc.abstractmethod
    async def get_document(self, index: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document"""
        pass
    
    @abc.abstractmethod
    async def search(self, index: str, query: Dict[str, Any], 
                    size: int = 10, from_: int = 0) -> List[Dict[str, Any]]:
        """Search documents"""
        pass
    
    @abc.abstractmethod
    async def bulk_index(self, index: str, documents: List[Dict[str, Any]]) -> bool:
        """Bulk index documents"""
        pass
    
    @abc.abstractmethod
    async def delete_document(self, index: str, doc_id: str) -> bool:
        """Delete a document"""
        pass


class CacheService(BaseService):
    """Interface for cache services"""
    
    @abc.abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a key-value pair"""
        pass
    
    @abc.abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value by key"""
        pass
    
    @abc.abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key"""
        pass
    
    @abc.abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abc.abstractmethod
    async def hset(self, name: str, key: str, value: Any) -> bool:
        """Set hash field"""
        pass
    
    @abc.abstractmethod
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field"""
        pass


class ObjectStorageService(BaseService):
    """Interface for object storage services"""
    
    @abc.abstractmethod
    async def upload_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """Upload a file"""
        pass
    
    @abc.abstractmethod
    async def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        """Download a file"""
        pass
    
    @abc.abstractmethod
    async def list_objects(self, bucket: str, prefix: str = "") -> List[str]:
        """List objects in a bucket"""
        pass
    
    @abc.abstractmethod
    async def delete_object(self, bucket: str, object_name: str) -> bool:
        """Delete an object"""
        pass
    
    @abc.abstractmethod
    async def create_bucket(self, bucket: str) -> bool:
        """Create a bucket"""
        pass
    
    @abc.abstractmethod
    async def bucket_exists(self, bucket: str) -> bool:
        """Check if bucket exists"""
        pass


class DatabaseService(BaseService):
    """Interface for database services"""
    
    @abc.abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query"""
        pass
    
    @abc.abstractmethod
    async def execute_update(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute an update query"""
        pass
    
    @abc.abstractmethod
    async def execute_transaction(self, queries: List[Dict[str, Any]]) -> bool:
        """Execute a transaction"""
        pass
    
    @abc.abstractmethod
    async def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        pass
    
    @abc.abstractmethod
    async def create_table(self, table_name: str, schema: Dict[str, Any]) -> bool:
        """Create a table"""
        pass


class LLMService(BaseService):
    """Interface for LLM services"""
    
    @abc.abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], 
                 model: Optional[str] = None, 
                 **kwargs) -> Dict[str, Any]:
        """Chat with LLM"""
        pass
    
    @abc.abstractmethod
    async def embeddings(self, texts: List[str], 
                        model: Optional[str] = None) -> List[List[float]]:
        """Generate embeddings"""
        pass
    
    @abc.abstractmethod
    async def completion(self, prompt: str, 
                        model: Optional[str] = None, 
                        **kwargs) -> str:
        """Generate text completion"""
        pass
    
    @abc.abstractmethod
    async def get_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        pass


class ExternalAPIService(BaseService):
    """Interface for external API services"""
    
    @abc.abstractmethod
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, 
                 headers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """HTTP GET request"""
        pass
    
    @abc.abstractmethod
    async def post(self, url: str, data: Optional[Dict[str, Any]] = None, 
                  json: Optional[Dict[str, Any]] = None, 
                  headers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """HTTP POST request"""
        pass
    
    @abc.abstractmethod
    async def put(self, url: str, data: Optional[Dict[str, Any]] = None, 
                 json: Optional[Dict[str, Any]] = None, 
                 headers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """HTTP PUT request"""
        pass
    
    @abc.abstractmethod
    async def delete(self, url: str, params: Optional[Dict[str, Any]] = None, 
                    headers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """HTTP DELETE request"""
        pass


class ServiceFactory(abc.ABC):
    """Factory interface for creating service instances"""
    
    @abc.abstractmethod
    def create_document_storage_service(self, service_type: str, config: Dict[str, Any]) -> DocumentStorageService:
        """Create document storage service"""
        pass
    
    @abc.abstractmethod
    def create_cache_service(self, service_type: str, config: Dict[str, Any]) -> CacheService:
        """Create cache service"""
        pass
    
    @abc.abstractmethod
    def create_object_storage_service(self, service_type: str, config: Dict[str, Any]) -> ObjectStorageService:
        """Create object storage service"""
        pass
    
    @abc.abstractmethod
    def create_database_service(self, service_type: str, config: Dict[str, Any]) -> DatabaseService:
        """Create database service"""
        pass
    
    @abc.abstractmethod
    def create_llm_service(self, service_type: str, config: Dict[str, Any]) -> LLMService:
        """Create LLM service"""
        pass
    
    @abc.abstractmethod
    def create_external_api_service(self, service_type: str, config: Dict[str, Any]) -> ExternalAPIService:
        """Create external API service"""
        pass


class ServiceConfig:
    """Service configuration holder"""
    
    def __init__(self, service_type: str, config: Dict[str, Any]):
        self.service_type = service_type
        self.config = config
        self.mode = config.get("mode", "mock")  # "mock" or "real"
    
    @property
    def is_mock_mode(self) -> bool:
        return self.mode.lower() == "mock"
    
    @property
    def is_real_mode(self) -> bool:
        return self.mode.lower() == "real"


class ServiceRegistry:
    """Registry for service instances"""
    
    _instances = {}
    
    @classmethod
    def register(cls, service_name: str, service_instance: BaseService) -> None:
        """Register a service instance"""
        cls._instances[service_name] = service_instance
    
    @classmethod
    def get(cls, service_name: str) -> Optional[BaseService]:
        """Get a registered service instance"""
        return cls._instances.get(service_name)
    
    @classmethod
    def unregister(cls, service_name: str) -> None:
        """Unregister a service instance"""
        cls._instances.pop(service_name, None)


class ServiceModeDetector:
    """Detects the current service mode"""
    
    @staticmethod
    def detect_mode(config: Dict[str, Any]) -> str:
        """Detect mode from configuration"""
        mode = config.get("mode", "mock")
        if mode.lower() in ["mock", "real"]:
            return mode.lower()
        
        # Fallback to environment variables
        env_mode = os.getenv("RAGFLOW_TEST_MODE", "mock")
        return env_mode.lower()


class ServiceContextManager:
    """Context manager for service lifecycle"""
    
    def __init__(self, service: BaseService):
        self.service = service
    
    async def __aenter__(self):
        await self.service.connect()
        return self.service
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.service.disconnect()


__all__ = [
    "BaseService", "DocumentStorageService", "CacheService", "ObjectStorageService",
    "DatabaseService", "LLMService", "ExternalAPIService", "ServiceFactory",
    "ServiceConfig", "ServiceRegistry", "ServiceModeDetector", "ServiceContextManager"
]