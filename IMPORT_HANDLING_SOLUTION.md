# Better Ways to Prevent Import Errors in Tests

**Summary**: Replace 400+ lines of fragile `sys.modules` stubbing with clean, maintainable marker-based test skipping.

---

## Current Problem

RAGFlow test conftest.py files (~441 lines in `test/unit_test/rag/conftest.py`) use aggressive `sys.modules` mocking to prevent import errors from missing optional dependencies (openai, tiktoken, elasticsearch, etc.).

### Issues with Current Approach

1. **Fragile** - Must manually maintain stubs as dependencies evolve
2. **Brittle** - Stubs are incomplete, masking real issues in actual libraries
3. **Hidden Bugs** - Tests pass with stubs but fail in production with real implementations
4. **Maintenance Hell** - 400+ lines just for import stubbing
5. **Debugging Nightmare** - Stubbed imports cause confusing errors downstream
6. **No Integration Testing** - Can't verify actual library behavior

### Example of Current Problem

```python
# Current: 441 lines of sys.modules hacks in test/unit_test/rag/conftest.py
if "openai" in sys.modules:
    class OpenAI:
        def __init__(self, *args, **kwargs):
            pass
        class embeddings:
            @staticmethod
            def create(*args, **kwargs):
                class MockResponse:
                    def __init__(self):
                        self.data = [type("MockData", (), {"embedding": [0.1, 0.2, 0.3]})()]
                        self.usage = type("MockUsage", (), {"total_tokens": 10})()
                return MockResponse()
    sys.modules["openai"].OpenAI = OpenAI
```

---

## Recommended Solution: Hybrid Marker-Based Approach

### Overview

1. **Skip tests** if optional dependencies aren't installed using pytest markers
2. **Detect imports** cleanly without sys.modules hacks
3. **Document dependencies** in `pyproject.toml` optional groups
4. **Run full tests** in CI with all dependencies installed

### Implementation: 80 Lines of Clean Code

```python
# test/unit_test/conftest.py (replaces 441-line conftest.py)

import pytest

def _check_import(module_name: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

# Create markers for each optional dependency
skipif_no_openai = pytest.mark.skipif(
    not _check_import("openai"),
    reason="openai not installed - install with: pip install openai"
)

skipif_no_tiktoken = pytest.mark.skipif(
    not _check_import("tiktoken"),
    reason="tiktoken not installed - install with: pip install tiktoken"
)

skipif_no_elasticsearch = pytest.mark.skipif(
    not _check_import("elasticsearch_dsl"),
    reason="elasticsearch-dsl not installed"
)

# ... more markers for other optional deps

@pytest.fixture
def optional_modules():
    """Fixture providing safe import helpers."""
    return {
        "check_import": _check_import,
        "safe_import": lambda m, d=None: __import__(m) if _check_import(m) else d,
    }
```

### Usage in Tests

```python
# Before: Assumptions, hidden failures
def test_openai():
    from openai import OpenAI  # ImportError if not installed
    client = OpenAI(api_key="test")
    assert client is not None

# After: Explicit, clear
@skipif_no_openai
def test_openai():
    from openai import OpenAI
    client = OpenAI(api_key="test")
    assert client is not None

# Output when openai not installed:
# SKIPPED test_openai: openai not installed - install with: pip install openai
```

---

## Configuration

### 1. Update pytest configuration

**Option A: pyproject.toml** (Recommended)

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["test"]
markers = [
    "unit: Fast unit tests",
    "integration: Tests requiring external services",
    "requires_openai: Tests that require openai",
    "requires_tiktoken: Tests that require tiktoken",
    "requires_elasticsearch: Tests that require elasticsearch",
    "slow: Slow tests",
]
addopts = "-v --strict-markers --tb=short"
```

**Option B: pytest.ini**

```ini
[pytest]
minversion = 7.0
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = test

markers =
    unit: Fast unit tests
    integration: Integration tests
    requires_openai: Tests requiring openai
    requires_tiktoken: Tests requiring tiktoken
    slow: Slow tests

addopts = -v --strict-markers --tb=short
```

### 2. Add Optional Dependency Groups to pyproject.toml

```toml
[project.optional-dependencies]
# Group by functionality for flexible installation
llm = [
    "openai>=1.0.0",
    "tiktoken>=0.5.0",
    "dashscope>=1.25.0",
    "zhipuai>=2.0.0",
    "ollama>=0.5.0",
    "litellm>=1.0.0",
]

search = [
    "elasticsearch-dsl>=8.12.0",
    "elastic-transport>=8.0.0",
    "opensearch-py>=2.7.1",
]

storage = [
    "boto3>=1.26.0",
    "azure-storage-blob>=12.16.0",
    "google-cloud-storage>=2.19.0",
]

# All optional deps for comprehensive testing
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-xdist>=3.0.0",
    # Include all optional deps
    "openai>=1.0.0",
    "tiktoken>=0.5.0",
    "dashscope>=1.25.0",
    "zhipuai>=2.0.0",
    "ollama>=0.5.0",
    "litellm>=1.0.0",
    "elasticsearch-dsl>=8.12.0",
    "elastic-transport>=8.0.0",
    "opensearch-py>=2.7.1",
]

# Or install everything for development
all = [
    "ragflow[llm]",
    "ragflow[search]",
    "ragflow[storage]",
    "ragflow[test]",
]
```

### 3. Update Installation Instructions

**For Development**:
```bash
# Install everything for development
uv sync --all-extras

# Or selectively
uv sync --extra llm  # Just LLM providers
uv sync --extra test  # For running tests
```

**For CI/CD**:
```bash
# Install everything for comprehensive testing
uv sync --all-extras

# Run all tests (with all dependencies)
pytest
```

---

## Migration Path

### Phase 1: Add New conftest.py (Low Risk)

1. Create new `test/unit_test/conftest_new.py` with marker-based approach
2. Test that it works: `pytest test/ -v`
3. Verify skip messages appear for uninstalled deps

### Phase 2: Update Test Files (Medium Risk)

Add markers to test files:
```python
from conftest import skipif_no_openai, skipif_no_tiktoken

@skipif_no_openai
def test_openai_client():
    import openai
    # Test with real openai
```

### Phase 3: Remove Old conftest.py (Low Risk)

Delete the 441-line `test/unit_test/rag/conftest.py` and move to new approach

### Phase 4: Update CI (Low Risk)

Update CI to install all optional deps:
```yaml
# .github/workflows/test.yml (example)
- name: Install dependencies
  run: uv sync --all-extras

- name: Run tests
  run: pytest test/ -v
```

---

## Comparison: Before vs After

### Before (Current Approach)

**File**: `test/unit_test/rag/conftest.py`
- 441 lines of code
- Fragile sys.modules stubbing
- Manual stub class definitions
- Hard to debug when stubs conflict
- Tests pass with stubs, fail with real libs

### After (Recommended)

**File**: `test/unit_test/conftest.py`
- ~80 lines of code
- Simple marker-based skipping
- Real library behavior in tests
- Clear skip messages
- Standard pytest practices

---

## Key Benefits

✅ **Simpler Code**: 80 lines vs 441 lines  
✅ **Better Testing**: Tests use real libraries when available  
✅ **Clearer Intent**: Explicit about what's required  
✅ **Standard Practices**: Follows pytest conventions  
✅ **Maintainable**: Easy to add new optional deps  
✅ **Better DX**: Skip messages tell developers what to install  
✅ **Flexible Installation**: Users choose what to install  
✅ **CI Transparency**: Clear test requirements  

---

## Examples

### Example 1: Simple Test Requiring Optional Dep

```python
# test/unit_test/test_llm.py

from conftest import skipif_no_openai

@skipif_no_openai
def test_openai_embedding():
    """Only runs if openai is installed."""
    from openai import OpenAI
    
    client = OpenAI(api_key="test-key")
    # Real integration test with actual openai library
    assert client is not None
```

When openai is not installed:
```
test/unit_test/test_llm.py::test_openai_embedding SKIPPED
[reason: openai not installed - install with: pip install openai]
```

### Example 2: Conditional Test with Fallback

```python
# test/unit_test/test_search.py

def test_search_with_optional_features(optional_modules):
    """Works with or without elasticsearch."""
    
    # Check if elasticsearch is available
    if optional_modules["check_import"]("elasticsearch_dsl"):
        from elasticsearch_dsl import Document
        # Test elasticsearch-specific features
    else:
        # Test fallback behavior
        from rag.search import DefaultSearch
        assert DefaultSearch is not None
```

---

## FAQ

**Q: What if CI needs all tests to run?**  
A: Install optional dependencies in CI: `uv sync --all-extras`

**Q: What about developers without all dependencies?**  
A: Tests gracefully skip. They can install selectively: `uv sync --extra llm`

**Q: How do I know what tests were skipped?**  
A: Run pytest with `-v` flag: `pytest -v` shows SKIPPED reason

**Q: Can I run only tests for installed dependencies?**  
A: Yes, pytest automatically skips tests with unmet markers

**Q: What about tests that use multiple optional deps?**  
A: Use multiple markers:
```python
@skipif_no_openai
@skipif_no_tiktoken
def test_tokenization_with_openai():
    ...
```

---

## Next Steps

1. **Review** the proof-of-concept: `test_import_solution_poc.py`
2. **Test** the approach with your project
3. **Update** `test/unit_test/conftest.py` to use new approach
4. **Gradually** add markers to test files
5. **Remove** old sys.modules stub code
6. **Update** CI to install optional dependencies
7. **Document** in CONTRIBUTING.md

---

## Resources

- [pytest markers documentation](https://docs.pytest.org/en/stable/how-to/mark.html)
- [pytest skipif documentation](https://docs.pytest.org/en/stable/how-to/skipping.html)
- [Python packaging optional dependencies](https://packaging.python.org/tutorials/installing-packages/#installing-extras)
- [PEP 508 - Dependency specification](https://peps.python.org/pep-0508/)
