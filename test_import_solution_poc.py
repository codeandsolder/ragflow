"""
Proof of Concept: Better import handling for optional dependencies

This demonstrates the recommended hybrid approach:
1. Marker-based test skipping
2. Optional dependency detection
3. Clean pytest configuration

This replaces 400+ lines of sys.modules stubs with ~80 lines of clean code.
"""

import sys
import pytest
from typing import Any


def _check_import(module_name: str) -> bool:
    """
    Check if a module can be imported.
    
    Returns:
        True if module is available, False otherwise
    """
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def _safe_import(module_name: str, default=None) -> Any:
    """
    Safely import a module, returning default if not available.
    
    Returns:
        The imported module or default value if import fails
    """
    try:
        return __import__(module_name)
    except ImportError:
        return default


# === Optional Dependency Markers ===
# These should be used in test files to conditionally skip tests

skipif_no_openai = pytest.mark.skipif(
    not _check_import("openai"),
    reason="openai not installed - install with: pip install openai"
)

skipif_no_tiktoken = pytest.mark.skipif(
    not _check_import("tiktoken"),
    reason="tiktoken not installed - install with: pip install tiktoken"
)

skipif_no_dashscope = pytest.mark.skipif(
    not _check_import("dashscope"),
    reason="dashscope not installed"
)

skipif_no_zhipuai = pytest.mark.skipif(
    not _check_import("zhipuai"),
    reason="zhipuai not installed"
)

skipif_no_ollama = pytest.mark.skipif(
    not _check_import("ollama"),
    reason="ollama not installed"
)

skipif_no_elasticsearch = pytest.mark.skipif(
    not _check_import("elasticsearch_dsl"),
    reason="elasticsearch-dsl not installed"
)

skipif_no_httpx = pytest.mark.skipif(
    not _check_import("httpx"),
    reason="httpx not installed"
)

skipif_no_litellm = pytest.mark.skipif(
    not _check_import("litellm"),
    reason="litellm not installed"
)


# === Pytest Fixtures for Testing with Optional Dependencies ===

@pytest.fixture
def optional_modules():
    """Fixture providing access to optional module checking."""
    return {
        "check_import": _check_import,
        "safe_import": _safe_import,
    }


@pytest.fixture
def mock_openai_if_available():
    """
    Fixture providing OpenAI client if available, mock otherwise.
    
    This demonstrates the hybrid approach:
    - If openai is installed, use real client
    - Otherwise, provide a mock for testing code structure
    """
    if _check_import("openai"):
        import openai
        return openai.OpenAI(api_key="test-key-for-testing")
    else:
        # Return a mock object
        from unittest.mock import MagicMock
        mock = MagicMock()
        mock.ChatCompletion.create = MagicMock(return_value={
            "choices": [{"message": {"content": "test response"}}]
        })
        return mock


# === Usage Examples in Tests ===

class TestOptionalDependencies:
    """Example tests demonstrating the new approach."""
    
    @skipif_no_openai
    def test_with_openai_if_available(self):
        """This test only runs if openai is installed."""
        import openai
        assert openai is not None
    
    def test_conditional_import(self, optional_modules):
        """Test using the helper fixture."""
        assert optional_modules["check_import"]("sys") is True  # Always available
        assert optional_modules["check_import"]("nonexistent") is False
    
    def test_safe_import_usage(self, optional_modules):
        """Test safe import helper."""
        os_module = optional_modules["safe_import"]("os")
        assert os_module is not None
        
        fake_module = optional_modules["safe_import"]("nonexistent", default=None)
        assert fake_module is None


# === pytest.ini Configuration ===
"""
Recommended pytest.ini configuration to go with this approach:

[pytest]
minversion = 7.0
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Fast unit tests that don't require external services
    integration: Tests that require external services
    requires_openai: Tests that require OpenAI library
    requires_tiktoken: Tests that require tiktoken library
    requires_elasticsearch: Tests that require elasticsearch
    slow: Tests that take a long time to run

addopts =
    -v
    --strict-markers
    --tb=short
    -ra

testpaths = test
"""


# === pyproject.toml Configuration ===
"""
Recommended pyproject.toml configuration:

[project.optional-dependencies]
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

test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-xdist>=3.0.0",
    # Include all optional deps for comprehensive testing
    "openai>=1.0.0",
    "tiktoken>=0.5.0",
    "dashscope>=1.25.0",
    "zhipuai>=2.0.0",
    "ollama>=0.5.0",
    "litellm>=1.0.0",
    "elasticsearch-dsl>=8.12.0",
    "elastic-transport>=8.0.0",
]

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["test"]
pythonpath = ["."]
markers = [
    "unit: Fast unit tests",
    "integration: Integration tests",
    "requires_openai: Tests requiring OpenAI",
    "requires_tiktoken: Tests requiring tiktoken",
    "slow: Slow running tests",
]
"""


# === Migration Steps ===
"""
To migrate from sys.modules stubbing to this approach:

1. Replace test/unit_test/conftest.py with this file
2. Replace test/unit_test/rag/conftest.py with this file
3. Add pytest.ini or update pyproject.toml with [tool.pytest.ini_options]
4. Update test files to use @skipif_no_* markers instead of assuming imports work
5. Update CI configuration to install optional dependencies:
   - uv sync --all-extras  # Or pip install -e ".[test]"
6. Run tests: pytest --tb=short

Benefits:
- ✓ Removes 400+ lines of fragile stub code
- ✓ Clear, explicit dependency requirements
- ✓ Tests can use real implementations
- ✓ CI has full visibility into test requirements
- ✓ Developer-friendly skip messages
- ✓ Standard pytest practices
- ✓ Maintainable and scalable
"""

if __name__ == "__main__":
    print(__doc__)
    print("\n✓ This PoC demonstrates a better approach to handling optional dependencies")
    print("✓ Replaces 400+ lines of sys.modules stubbing with ~80 lines of clean code")
    print("✓ Run with: pytest test_import_solution_poc.py -v")
