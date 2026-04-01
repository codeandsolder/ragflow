# Test Data Factories Plan for RAGFlow

This document outlines a comprehensive plan to implement test data factories in the RAGFlow test suite.

---

## 1. Dependency Decision: factory_boy vs Custom Factory Pattern

### Option A: factory_boy

| Pros | Cons |
|------|------|
| Industry-standard, well-documented | External dependency |
| Rich features: lazy attributes, sequences, callbacks, subfactories | Additional learning curve |
| Extensive community support and maintenance | May have version compatibility issues |
| Built-in Faker integration for realistic data | Slight overhead for simple use cases |
| Works well with pytest fixtures | Can be overkill for simple projects |

### Option B: Custom Factory Pattern

| Pros | Cons |
|------|------|
| No external dependencies | Reinventing the wheel |
| Full control over behavior | More boilerplate code |
| Simpler for basic use cases | Harder to maintain consistency |
| Can be tailored to RAGFlow's specific needs | Missing advanced features |

### Recommendation: **factory_boy**

**Rationale:**
- The project already uses external testing dependencies (pytest, pytest-asyncio, etc.)
- factory_boy is the de facto standard for test factories in Python
- Rich feature set matches the complexity of RAGFlow's data models
- Easy integration with Faker for realistic test data
- Well-understood by other developers

**Alternative:** If avoiding new dependencies is critical, implement a lightweight custom pattern in `test/utils/factories.py`.

---

## 2. Factory Structure

### Directory Location

```
test/
├── factories/                    # New: Factory modules
│   ├── __init__.py              # Exports all factories
│   ├── base.py                  # Base factory class
│   ├── user.py                  # User factory
│   ├── tenant.py                # Tenant factory
│   ├── knowledgebase.py         # Knowledgebase factory
│   ├── document.py              # Document factory
│   ├── chunk.py                 # Chunk factory
│   ├── dialog.py                # Dialog factory
│   ├── conversation.py          # Conversation factory
│   ├── file.py                  # File factory
│   ├── task.py                  # Task factory
│   └── agents.py                # Agent/Canvas factories
```

### Naming Conventions

- **Factory class name**: `{ModelName}Factory` (e.g., `UserFactory`)
- **Factory file**: `{model_name}.py` (e.g., `user.py`)
- **Base class**: `BaseFactory` in `base.py`

---

## 3. Model Coverage

### Priority 1: Core Models (Most Used)

| Model | Factory | Fields to Generate |
|-------|---------|---------------------|
| `User` | `UserFactory` | id, email, nickname, password, tenant_id |
| `Tenant` | `TenantFactory` | id, name, llm_id, embd_id |
| `Knowledgebase` | `KnowledgebaseFactory` | id, tenant_id, name, embd_id, created_by |
| `Document` | `DocumentFactory` | id, kb_id, name, type, created_by, parser_id |
| `Conversation` | `ConversationFactory` | id, dialog_id, user_id, name |

### Priority 2: Supporting Models

| Model | Factory | Notes |
|-------|---------|-------|
| `Dialog` | `DialogFactory` | Requires tenant_id, llm_id |
| `File` | `FileFactory` | Parent/child relationships |
| `Task` | `TaskFactory` | Document processing tasks |
| `UserTenant` | `UserTenantFactory` | User-tenant association |
| `TenantLLM` | `TenantLLMFactory` | Per-tenant LLM configs |
| `APIToken` | `APITokenFactory` | API authentication tokens |

### Priority 3: Extended Models

| Model | Factory | Notes |
|-------|---------|-------|
| `UserCanvas` | `CanvasFactory` | Agent canvas DSL |
| `CanvasTemplate` | `CanvasTemplateFactory` | Canvas templates |
| `Memory` | `MemoryFactory` | Memory configurations |
| `MCPServer` | `MCPServerFactory` | MCP server configs |
| `Search` | `SearchFactory` | Saved searches |
| `Connector` | `ConnectorFactory` | Data connectors |

### Not Needed for Factories

- `BaseModel` (abstract base)
- `LLMFactories`, `LLM` (seed data)
- `InvitationCode` (system admin)
- `SyncLogs` (runtime data)
- Evaluation models (rarely tested in isolation)

---

## 4. Factory Features

### Base Factory Implementation

```python
# test/factories/base.py
from typing import Any, Generic, TypeVar
import factory
from factory.alchemy import SQLAlchemyModelFactory
from api.db.db_models import DB

T = TypeVar('T')

class BaseFactory(SQLAlchemyModelFactory, Generic[T]):
    """Base factory for all RAGFlow models."""
    
    class Meta:
        abstract = True
        sqlalchemy_session = DB
        sqlalchemy_session_persistence = "commit"
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to handle custom ID generation."""
        # Auto-generate ID if not provided
        if 'id' in kwargs and kwargs['id'] is None:
            kwargs.pop('id')
        return super()._create(model_class, *args, **kwargs)
```

### Lazy Attributes

```python
# Example: Lazy attribute for auto-generated unique values
class UserFactory(BaseFactory[User]):
    class Meta:
        model = User
    
    id = factory.Sequence(lambda n: f"user-{n:04d}")
    email = factory.LazyAttribute(lambda o: f"user{o.id}@example.com")
    nickname = factory.LazyAttribute(lambda o: f"User {o.id}")
    password = factory.LazyFunction(lambda: "hashed_password")
```

### Sequences

```python
# Example: Unique sequences for different models
class KnowledgebaseFactory(BaseFactory[Knowledgebase]):
    class Meta:
        model = Knowledgebase
    
    id = factory.Sequence(lambda n: f"kb-{n:04d}")
    name = factory.Sequence(lambda n: f"Knowledge Base {n}")
    tenant_id = factory.Sequence(lambda n: f"tenant-{n % 3}")
```

### Related Objects (SubFactory)

```python
# Example: SubFactory for related objects
class DocumentFactory(BaseFactory[Document]):
    class Meta:
        model = Document
    
    id = factory.Sequence(lambda n: f"doc-{n:04d}")
    kb_id = factory.LazyAttribute(lambda o: None)  # Set via parent
    name = factory.Sequence(lambda n: f"document_{n}.pdf")
    type = "pdf"
    created_by = factory.LazyAttribute(lambda o: None)
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Handle kb_id from parent factory
        if kwargs.get('kb_id') is None and kwargs.get('kb'):
            kwargs['kb_id'] = kwargs.pop('kb').id
        if kwargs.get('created_by') is None and kwargs.get('created_by_user'):
            kwargs['created_by'] = kwargs.pop('created_by_user').id
        return super()._create(model_class, *args, **kwargs)


class KnowledgebaseFactory(BaseFactory[Knowledgebase]):
    # ...
    documents = factory.RelatedFactoryList(DocumentFactory, 'kb', count=3)
```

### Callbacks and Hooks

```python
# Example: Post-generation callbacks
class UserFactory(BaseFactory[User]):
    # ...
    
    @factory.post_generation
    def tenants(self, create, extracted, **kwargs):
        """Create default tenant association."""
        if not create:
            return
        if not extracted:
            # Auto-create tenant if not provided
            tenant = TenantFactory()
            UserTenantFactory(user_id=self.id, tenant_id=tenant.id, role="owner")
```

### Default Values

```python
# Example: Complex default values via LazyFunction
import random
from datetime import datetime

class DocumentFactory(BaseFactory[Document]):
    class Meta:
        model = Document
    
    parser_id = "naive"
    parser_config = factory.LazyFunction(lambda: {
        "pages": [[1, 1000000]],
        "table_context_size": 0,
        "image_context_size": 0
    })
    source_type = "local"
    status = "1"
    run = "0"
    size = factory.LazyFunction(lambda: random.randint(1000, 1000000))
```

---

## 5. Migration Plan

### Phase 1: Setup (Week 1)

1. **Add factory_boy to dependencies**
   ```toml
   # pyproject.toml
   [project.optional-dependencies]
   dev = [
       "factory-boy>=3.3.0",
       "faker>=20.0.0",
   ]
   ```

2. **Create base factory class**
   - Location: `test/factories/base.py`
   - Handle database session management
   - Set up ID generation strategy

3. **Create factory modules**
   - Implement Priority 1 models first
   - Ensure all factories pass basic tests

### Phase 2: Migration (Weeks 2-3)

1. **Identify test patterns to replace**
   
   ```python
   # BEFORE: Creating test data inline
   def test_something():
       user = User.create(
           id="user-123",
           email="test@example.com",
           nickname="Test User"
       )
       kb = Knowledgebase.create(
           id="kb-123",
           name="Test KB",
           tenant_id="tenant-123",
           created_by="user-123"
       )
   ```

   ```python
   # AFTER: Using factories
   def test_something():
       user = UserFactory()
       tenant = TenantFactory(id=user.tenant_id)
       kb = KnowledgebaseFactory(tenant_id=tenant.id, created_by=user.id)
   ```

2. **Refactor conftest.py fixtures**
   
   ```python
   # test/unit_test/api/apps/conftest.py - BEFORE
   @pytest.fixture
   def mock_user():
       user = Mock()
       user.id = "user-123"
       user.email = "test@example.com"
       user.nickname = "Test User"
       user.tenant_id = "tenant-123"
       user.is_active = "1"
       return user
   
   # AFTER (if using factories for real DB tests)
   @pytest.fixture
   def user_factory(db):
       return UserFactory
   ```

3. **Update test files incrementally**
   - Start with unit tests using SQLite
   - Then integration tests
   - Keep backward compatibility during transition

### Phase 3: Adoption (Week 4)

1. **Document factory usage patterns**
2. **Add factory helpers for common scenarios**
3. **Remove hardcoded test data where possible**

---

## 6. Fixture Integration

### With pytest Fixtures

```python
# test/unit_test/api/db/services/conftest.py
import pytest
from test.factories import UserFactory, TenantFactory, KnowledgebaseFactory

@pytest.fixture
def tenant(db):
    """Create a test tenant."""
    return TenantFactory()

@pytest.fixture
def user(db, tenant):
    """Create a test user associated with a tenant."""
    return UserFactory(tenant_id=tenant.id)

@pytest.fixture
def knowledgebase(db, user, tenant):
    """Create a test knowledgebase."""
    return KnowledgebaseFactory(
        tenant_id=tenant.id,
        created_by=user.id
    )

# For session-scoped fixtures
@pytest.fixture(scope="session")
def session_tenant():
    """Create a tenant shared across session."""
    return TenantFactory(id="session-tenant")
```

### With Database Transactions

```python
# Use transaction rollback for test isolation
@pytest.fixture
def db_with_rollback(db):
    """Provide database with automatic rollback."""
    with db.atomic() as transaction:
        yield db
        transaction.rollback()  # Cleanup after test
```

### Factory with Faker Integration

```python
# test/factories/user.py
import factory
from faker import Faker
from api.db.db_models import User

fake = Faker()

class UserFactory(BaseFactory[User]):
    class Meta:
        model = User
    
    id = factory.Sequence(lambda n: f"user-{n:04d}")
    email = factory.LazyAttribute(lambda _: fake.unique.email())
    nickname = factory.LazyAttribute(lambda _: fake.name())
    password = factory.LazyAttribute(lambda _: fake.sha256())
    avatar = factory.LazyAttribute(lambda _: fake.image_url())
    language = "English"
    color_schema = "Bright"
    timezone = "UTC+8"
    is_active = "1"
    is_superuser = False
```

---

## 7. Code Examples: Before/After

### Example 1: User Creation

**BEFORE** (inline creation in test):
```python
# test/unit_test/api/apps/test_user_app.py
def test_user_query():
    # Create test data inline
    User.insert(
        id="user-001",
        email="test@example.com",
        nickname="Test User",
        password="hashed_password",
        is_active="1"
    )
    User.insert(
        id="user-002", 
        email="test2@example.com",
        nickname="Test User 2",
        password="hashed_password2",
        is_active="1"
    )
    
    # Run test
    result = User.query(email="test@example.com")
    assert len(result) == 1
    assert result[0].nickname == "Test User"
```

**AFTER** (using factory):
```python
# Using factory directly
def test_user_query():
    user1 = UserFactory(
        id="user-001",
        email="test@example.com",
        nickname="Test User"
    )
    user2 = UserFactory(
        id="user-002",
        email="test2@example.com",
        nickname="Test User 2"
    )
    
    result = User.query(email="test@example.com")
    assert len(result) == 1
    assert result[0].nickname == "Test User"
```

**AFTER** (using factory with fixtures):
```python
# test/testcases/test_web_api/conftest.py
@pytest.fixture
def test_user(db):
    return UserFactory(email="test@example.com")

# In test
def test_user_query(test_user):
    result = User.query(email="test@example.com")
    assert len(result) == 1
    assert result[0].nickname == test_user.nickname
```

### Example 2: Knowledgebase with Documents

**BEFORE** (complex setup):
```python
def test_kb_document_count():
    # Create tenant
    Tenant.insert(
        id="tenant-001",
        name="Test Tenant",
        llm_id="glm-4",
        embd_id="bge-small"
    )
    
    # Create user
    User.insert(
        id="user-001",
        email="owner@test.com",
        nickname="Owner",
        tenant_id="tenant-001"
    )
    
    # Create knowledgebase
    Knowledgebase.insert(
        id="kb-001",
        tenant_id="tenant-001",
        name="Test KB",
        created_by="user-001",
        embd_id="bge-small"
    )
    
    # Create documents
    for i in range(5):
        Document.insert(
            id=f"doc-{i:03d}",
            kb_id="kb-001",
            name=f"doc_{i}.pdf",
            type="pdf",
            created_by="user-001",
            run="1"
        )
    
    # Test
    kb = Knowledgebase.get(Knowledgebase.id == "kb-001")
    assert kb.doc_num == 5
```

**AFTER** (using factories):
```python
def test_kb_document_count():
    tenant = TenantFactory(id="tenant-001")
    user = UserFactory(id="user-001", tenant_id=tenant.id)
    kb = KnowledgebaseFactory(
        id="kb-001",
        tenant_id=tenant.id,
        created_by=user.id
    )
    
    # Create documents using RelatedFactory
    docs = DocumentFactory.create_batch(5, kb_id=kb.id, created_by=user.id)
    
    # Verify
    kb = Knowledgebase.get(Knowledgebase.id == "kb-001")
    assert kb.doc_num == 5
```

**AFTER** (with nested factory):
```python
class KnowledgebaseFactory(BaseFactory[Knowledgebase]):
    class Meta:
        model = Knowledgebase
    
    id = factory.Sequence(lambda n: f"kb-{n:04d}")
    tenant_id = factory.LazyAttribute(lambda o: None)
    name = factory.Sequence(lambda n: f"Test KB {n}")
    created_by = factory.LazyAttribute(lambda o: None)
    
    documents = factory.RelatedFactoryList(
        DocumentFactory,
        factory_related_name='kb',
        count=5
    )
```

### Example 3: Hardcoded Credentials Replacement

**BEFORE** (hardcoded in testcases/conftest.py):
```python
# test/testcases/conftest.py
def login():
    url = HOST_ADDRESS + f"/{VERSION}/user/login"
    login_data = {"email": EMAIL, "password": PASSWORD}  # Hardcoded
    response = requests.post(url=url, json=login_data)
    ...
```

**AFTER** (with test user factory):
```python
# test/testcases/conftest.py
@pytest.fixture(scope="session")
def auth():
    # Use factory to create test user if needed
    try:
        register()
    except Exception:
        pass
    
    # Or create via API then cache
    auth = login()
    return auth

@pytest.fixture
def test_user_credentials():
    """Provide test user credentials consistently."""
    return {
        "email": "qa@test.example.com", 
        "password": "test_password_123"
    }
```

---

## 8. Implementation Checklist

- [ ] Add `factory-boy` and `faker` to `pyproject.toml` dev dependencies
- [ ] Create `test/factories/` directory structure
- [ ] Implement `BaseFactory` class with proper database session handling
- [ ] Implement Priority 1 factories (User, Tenant, Knowledgebase, Document, Conversation)
- [ ] Implement Priority 2 factories (Dialog, File, Task, UserTenant, TenantLLM)
- [ ] Add factory fixtures to relevant `conftest.py` files
- [ ] Refactor existing tests to use factories (start with unit tests)
- [ ] Run linting and verify tests pass
- [ ] Document factory patterns in test README or wiki

---

## 9. Anti-Patterns to Avoid

1. **Don't create factories for every field**: Start with sensible defaults
2. **Don't use factories in performance-critical test setup**: Prefer simple fixtures
3. **Don't ignore cleanup**: Use `factory.Traverse` or pytest fixtures for cleanup
4. **Don't mix factory creation with API calls**: Choose one approach per test
5. **Don't hardcode IDs**: Use sequences or LazyAttribute for uniqueness

---

## 10. Files to Modify

1. `pyproject.toml` - Add factory_boy dependency
2. Create `test/factories/` directory and files
3. `test/unit_test/api/apps/conftest.py` - Add factory fixtures
4. `test/testcases/conftest.py` - Add test user factory
5. Various test files (incremental migration)
