# Test Mocking Issues Resolution Plan

This document outlines a comprehensive plan to address the inappropriate mocking patterns in the RAGFlow test suite. The goal is to improve test reliability, maintainability, and accuracy while preserving reasonable test execution times.

## Current Issues Identified

### 1. Unit Tests Mocking Entire Service Layer

**Location**: `test/unit_test/api/db/services/`

**Problem**: Tests mock entire service classes (e.g., `DocumentService`, `KnowledgebaseService`) hiding interaction bugs between components.

**Example** (`test_document_service_metadata_paging.py`):
```python
monkeypatch.setattr(document_service.DocumentService, "model", _SqliteDocument)
monkeypatch.setattr(document_service.DocMetadataService, "get_metadata_for_documents", ...)
```

**Impact**:
- Bugs in query construction go undetected
- Field name typos don't raise errors
- JOIN conditions cannot be validated
- Integration issues only surface in production

### 2. Web API Unit Tests with Deep-Mocking

**Location**: `test/testcases/test_web_api/test_kb_app/test_kb_routes_unit.py`

**Problem**: Tests mock at multiple layers including route handlers, services, and domain objects.

**Example**:
```python
monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: True)
monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: [...])
monkeypatch.setattr(module.DocumentService, "get_total_size_by_kb_id", lambda **_kwargs: 1024)
```

**Impact**:
- Tests verify mock behavior, not actual code
- Changes to service layer break tests unexpectedly
- No validation of actual database queries

### 3. Global sys.modules Stubbing

**Location**: `test/unit_test/conftest.py`, `test/unit_test/agent/conftest.py`

**Problem**: Global patching of modules like `tiktoken`, `openai`, `xgboost` using `sys.modules`.

**Example**:
```python
stub = types.ModuleType("cv2")
sys.modules["cv2"] = stub
```

**Impact**:
- Tests may pass with missing dependencies
- No distinction between "optional" and "broken" imports
- Environment-specific failures in CI

### 4. _FakeQuery and _FieldStub Patterns

**Location**: `test/unit_test/api/db/services/test_document_service_metadata_paging.py`

**Problem**: Mocking ORM internals (`_FakeQuery`, `_FieldStub`) instead of using the real database layer.

**Example**:
```python
class _FakeQuery:
    def __init__(self, docs):
        self._all = list(docs)
    def join(self, *args, **kwargs): return self
    def where(self, *args, **kwargs): return self
    def count(self): return len(self._all)
```

**Impact**:
- Field name typos silently ignored
- Query logic bugs undetected
- Must maintain parallel fake implementation

---

## 1. Architecture Proposal: Hybrid Testing Strategy

### Guiding Principle: Test at the Lowest Reasonable Level

| Test Type | When to Use | What to Mock | Example |
|-----------|-------------|--------------|---------|
| **Unit Test** | Pure logic, no I/O | External services, time, random | String utilities, validators |
| **Service Test** | Database queries | External APIs (LLM, search) | DocumentService.get_list |
| **Integration Test** | Full workflow | Only external infrastructure | End-to-end RAG pipeline |

### Decision Matrix

Use this matrix to determine the appropriate test level:

```
┌─────────────────────────────────────────────────────────────────┐
│  Does the test require actual database queries?                │
│  ├── YES → Use SQLite in-memory or mock at service level        │
│  └── NO  → Can you test without mocking services?              │
│       ├── YES → Use real service calls                          │
│       └── NO  → Consider if unit test is appropriate           │
└─────────────────────────────────────────────────────────────────┘
```

### Recommended Test Structure

```
test/
├── unit_test/
│   ├── api/
│   │   ├── utils/           # Pure functions → no DB mocking
│   │   ├── apps/            # Route validation (parse/validate only)
│   │   └── db/
│   │       ├── sqlite/      # SQLite-based ORM tests (NEW)
│   │       └── services/    # Service logic with real queries
│   ├── rag/                 # Pure RAG logic, no external APIs
│   └── agent/               # Component logic with mocked tools
│
├── testcases/
│   ├── test_web_api/       # Integration tests (real HTTP)
│   └── test_http_api/      # Full API integration tests
```

### Key Principles

1. **Never mock what you're testing**: If testing `DocumentService`, use real queries
2. **Mock at boundaries**: External APIs (LLM, search engine, file storage)
3. **Use SQLite for DB tests**: Fast, catches real ORM issues
4. **Integration tests for workflows**: End-to-end with real services

---

## 2. SQLite Transition Plan

### Goal: Replace `_FakeQuery`/`_FieldStub` with Real In-Memory DB

### Phase 1: Establish SQLite Test Infrastructure

**Create shared fixture module**: `test/unit_test/api/db/sqlite_fixtures.py`

```python
"""Shared SQLite fixtures for database testing."""
import pytest
import peewee
from playhouse.sqlite_ext import SqliteExtDatabase


class SQLiteTestDatabase:
    """Manages in-memory SQLite for testing."""
    
    def __init__(self):
        self.db = SqliteExtDatabase(":memory:")
        self.models = []
    
    def register_model(self, model_class):
        """Register a model with the test database."""
        model_class._meta.database = self.db
        self.models.append(model_class)
        return model_class
    
    def create_tables(self):
        """Create all registered tables."""
        self.db.create_tables(self.models)
    
    def close(self):
        """Close database connection."""
        self.db.close()


# Base model classes for common entities
class SQLiteDocument(peewee.Model):
    id = peewee.CharField(max_length=32, primary_key=True)
    kb_id = peewee.CharField(max_length=256, index=True)
    name = peewee.CharField(max_length=255, index=True)
    type = peewee.CharField(max_length=32, index=True)
    # ... other fields
    
    class Meta:
        database = None
        table_name = "document"


@pytest.fixture
def sqlite_db():
    """In-memory SQLite database for testing."""
    db_manager = SQLiteTestDatabase()
    
    # Register models
    db_manager.register_model(SQLiteDocument)
    # ... register other models
    
    db_manager.create_tables()
    yield db_manager.db
    db_manager.close()
```

### Phase 2: Migrate Existing Tests

**Before** (`test_document_service_metadata_paging.py`):
```python
class _FakeQuery:
    def __init__(self, docs):
        self._all = list(docs)
    def where(self, *args, **kwargs): return self
    def count(self): return len(self._all)
```

**After**:
```python
@pytest.fixture
def sqlite_document_service(sqlite_db):
    """Document service configured for SQLite testing."""
    from api.db.services import document_service
    
    # Swap to SQLite model
    document_service.DocumentService.model = SQLiteDocument
    yield document_service.DocumentService
    
    # Restore (if needed)
    document_service.DocumentService.model = original_model
```

### Phase 3: Validate with Schema Errors

SQLite catches issues that `_FakeQuery` misses:

| Issue Type | _FakeQuery Behavior | SQLite Behavior |
|------------|---------------------|------------------|
| Typoed field name | Silently ignored | `AttributeError` |
| Invalid JOIN condition | Silently ignored | `OperationalError` |
| Wrong query operator | May work incorrectly | TypeError/ValueError |
| Pagination errors | May return wrong data | Correct pagination |

**Example test** (`test/unit_test/api/db/test_sqlite_services.py:393`):
```python
def test_field_name_typo_caught(sqlite_db, sample_documents):
    """Typoed field name should raise error in real ORM."""
    with pytest.raises(AttributeError):
        list(_SqliteDocument.select().where(
            _SqliteDocument.unknown_field == "value"
        ).dicts())
```

---

## 3. Fixture Improvements

### Goal: Replace `sys.modules` Patching with Proper Mocking

### Current Problem

```python
# conftest.py - BAD PATTERN
sys.modules["tiktoken"] = stub  # Hides missing dependency
sys.modules["openai"] = stub
```

### Recommended Approach

**Option A: Use pytest.mark.skipif for Optional Dependencies**

```python
# conftest.py
def check_import(module_name):
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

skipif_no_tiktoken = pytest.mark.skipif(
    not check_import("tiktoken"),
    reason="tiktoken not installed"
)
```

**Option B: Use unittest.mock.patch with autouse=False**

```python
# test_specific_feature.py - GOOD PATTERN
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_tiktoken():
    with patch.dict('sys.modules', {'tiktoken': MagicMock()}):
        yield

def test_tokenization(mock_tiktoken):
    # Only patched when explicitly requested
    from api.utils import tokenize
    assert tokenize("hello") == ["hello"]
```

**Option C: Use pytest-recording for External API Calls** (Future)

```python
# For expensive external API calls (LLM, embedding)
@pytest.fixture
def recorded_llm():
    """Use recorded responses instead of live API calls."""
    with open("test/fixtures/recordings/llm_response.json") as f:
        return json.load(f)
```

### Improved conftest.py Structure

```python
# test/unit_test/conftest.py
import pytest
import sys
from types import ModuleType
from unittest.mock import MagicMock


class DependencyChecker:
    """Check and conditionally mock optional dependencies."""
    
    OPTIONAL_MODULES = {
        "tiktoken": "Tokenizer for token counting",
        "openai": "OpenAI client for LLM calls",
        "xgboost": "Gradient boosting library",
    }
    
    @classmethod
    def is_available(cls, module_name: str) -> bool:
        if module_name not in cls.OPTIONAL_MODULES:
            return True
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False
    
    @classmethod
    def create_stub(cls, module_name: str) -> ModuleType:
        """Create a stub for missing optional modules."""
        stub = ModuleType(module_name)
        stub.__getattr__ = lambda name: cls._missing_attr(module_name, name)
        return stub
    
    @classmethod
    def _missing_attr(cls, module: str, name: str):
        def _missing(*args, **kwargs):
            raise AttributeError(
                f"Module '{module}' is not available. "
                f"This is an optional dependency."
            )
        return _missing


def pytest_configure(config):
    """Configure pytest with dependency markers."""
    for module, description in DependencyChecker.OPTIONAL_MODULES.items():
        if not DependencyChecker.is_available(module):
            pytest.mark.skipif(
                f"Optional dependency '{module}' not installed"
            )
```

---

## 4. Migration Strategy

### Incremental Refactoring Approach

### Phase 1: Categorize Existing Tests (Week 1)

Create a test inventory:

```
test/
├── unit_test/api/db/services/
│   ├── test_document_service_metadata_paging.py  # PRIORITY: High (has _FakeQuery)
│   ├── test_document_service_get_parsing_status.py  # PRIORITY: High
│   ├── test_dialog_service_use_sql_source_columns.py  # PRIORITY: Medium
│   └── test_file_service_upload_document.py  # PRIORITY: Medium
```

Classification criteria:
- **P0 (Critical)**: Tests with `_FakeQuery`, `_FieldStub`, or deep mocking
- **P1 (High)**: Tests that mock entire service classes
- **P2 (Medium)**: Tests with some mocking but clear boundaries
- **P3 (Low)**: Tests that already follow best practices

### Phase 2: Create Shared Fixtures (Week 2)

Establish common fixtures that all tests can use:

```python
# test/unit_test/api/db/fixtures.py
@pytest.fixture
def sqlite_db():
    """In-memory SQLite database."""
    ...

@pytest.fixture
def sample_knowledgebase(sqlite_db):
    """Sample knowledgebase for testing."""
    ...

@pytest.fixture
def sample_documents(sqlite_db, sample_knowledgebase):
    """Sample documents for testing."""
    ...
```

### Phase 3: Migrate P0 Tests (Weeks 3-4)

Start with the most problematic tests:

1. `test_document_service_metadata_paging.py`
2. `test_document_service_get_parsing_status.py`

**Migration checklist**:
- [ ] Remove `_FakeQuery` class definition
- [ ] Remove `_FieldStub` class definition
- [ ] Add `sqlite_db` fixture
- [ ] Add `sample_documents` fixture
- [ ] Replace service model monkeypatch with real SQLite model
- [ ] Verify test still passes
- [ ] Verify test catches schema errors (add negative test)

### Phase 4: Migrate P1-P2 Tests (Weeks 5-8)

Continue with service-level tests:

1. Reduce deep mocking
2. Use SQLite for database interactions
3. Mock only external services (LLM, search)

### Phase 5: Validate and Document (Week 9)

1. Run full test suite
2. Measure test coverage
3. Document lessons learned
4. Update testing guidelines

---

## 5. Success Criteria

### How to Verify Mocking is Appropriate

### Criterion 1: Test Authenticity Score

**Definition**: Percentage of test that exercises real code vs. mocked code.

**Calculation**:
```
Authenticity Score = (Real Code Lines) / (Total Code Lines) * 100
```

**Target**:
- Unit tests: >70% real code
- Service tests: >50% real code
- Integration tests: >90% real code

### Criterion 2: Bug Detection Rate

**Definition**: Number of real bugs caught by tests in production vs. test environment.

**Measurement**:
1. Track bugs discovered in each environment
2. Calculate ratio: `Production Bugs / Test Bugs`

**Target**: <5% of bugs only discovered in production

### Criterion 3: Schema Error Detection

**Definition**: Tests should catch ORM schema errors.

**Verification Test**:
```python
def test_sqlite_catches_field_typos(sqlite_db):
    """Verify SQLite detects field name typos."""
    with pytest.raises(AttributeError):
        # This should fail - typo in field name
        _SqliteDocument.select().where(
            _SqliteDocument.nmae == "test"  # Typo: "nmae" not "name"
        )
```

**Target**: All new DB tests must include at least one schema validation test

### Criterion 4: Test Maintenance Burden

**Definition**: Time spent maintaining tests vs. adding features.

**Measurement**:
- Track test-related PR changes (lines added/removed for tests)
- Track feature-related PR changes

**Target**: Test maintenance <20% of total development time

### Criterion 5: CI Reliability

**Definition**: Tests should reliably pass/fail based on code quality.

**Metrics**:
- Flaky test rate: <1%
- Test retry rate: <2%
- False positive rate: <1%

---

## Implementation Checklist

### Immediate Actions (This Week)

- [ ] Create `test/unit_test/api/db/sqlite_fixtures.py` with shared SQLite fixtures
- [ ] Add `DependencyChecker` class to `test/unit_test/conftest.py`
- [ ] Document existing `_FakeQuery` usages

### Short-Term (1-2 Months)

- [ ] Migrate all P0 tests to SQLite
- [ ] Reduce sys.modules patching in agent tests
- [ ] Add schema validation tests
- [ ] Establish mock boundaries policy

### Long-Term (3-6 Months)

- [ ] Migrate all P1 tests to appropriate mocking levels
- [ ] Implement test recording for expensive operations
- [ ] Add test authenticity metrics to CI
- [ ] Update developer documentation

---

## Appendix: Migration Examples

### Example 1: Converting _FakeQuery Test

**Before**:
```python
# test_document_service_metadata_paging.py
class _FakeField:
    def __eq__(self, other): return self
    def in_(self, other): return self

class _FakeQuery:
    def __init__(self, docs):
        self._all = list(docs)
    def join(self, *args, **kwargs): return self
    def where(self, *args, **kwargs): return self
    def count(self): return len(self._all)
    def paginate(self, page, page_size): ...
    def dicts(self): return list(self._current)

def test_get_list(self):
    fake = _FakeQuery(sample_docs)
    result = fake.where(kb_id="kb-1").paginate(1, 2).dicts()
    assert len(result) == 2
```

**After**:
```python
# Using real SQLite
@pytest.fixture
def sqlite_db():
    db = SqliteExtDatabase(":memory:")
    _SqliteDocument._meta.database = db
    db.create_tables([_SqliteDocument])
    yield db
    db.close()

@pytest.fixture
def sample_documents(sqlite_db):
    for i in range(1, 6):
        _SqliteDocument.create(id=f"doc-{i}", kb_id="kb-1", name=f"doc-{i}.txt")
    return _SqliteDocument

def test_get_list(sqlite_db, sample_documents):
    # Real query with real pagination
    query = (_SqliteDocument
             .select()
             .where(_SqliteDocument.kb_id == "kb-1")
             .order_by(_SqliteDocument.create_time.desc())
             .limit(2)
             .offset(0))
    result = list(query.dicts())
    assert len(result) == 2
```

### Example 2: Converting sys.modules Stub

**Before**:
```python
# conftest.py
if "cv2" not in sys.modules:
    sys.modules["cv2"] = types.ModuleType("cv2")
```

**After**:
```python
# conftest.py
class DependencyChecker:
    @classmethod
    def is_available(cls, module_name):
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

# In test that needs cv2
import pytest
skipif_no_cv2 = pytest.mark.skipif(
    not DependencyChecker.is_available("cv2"),
    reason="cv2 not installed"
)

@skipif_no_cv2
def test_image_processing():
    # Real test using actual cv2
    from api.utils import process_image
    assert process_image("test.jpg") is not None
```

---

## References

- Existing SQLite implementation: `test/unit_test/api/db/test_sqlite_services.py`
- Current unit test structure: `test/unit_test/api/db/services/`
- Web API test examples: `test/testcases/test_web_api/test_kb_app/`
- Peewee testing documentation: https://docs.peewee-orm.com/
