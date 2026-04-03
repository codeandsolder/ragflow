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

# CRITICAL: Set flag BEFORE any other imports happen
import os

os.environ["RAGFLOW_TESTING"] = "1"

import sys
import types
import importlib
from pathlib import Path

import pytest

# Mock scholarly package to avoid SyntaxError in broken dependency
# This must be done early before any agent.tools imports happen
scholarly_stub = types.ModuleType("scholarly")
scholarly_stub.search_pubs = lambda *args, **kwargs: []
sys.modules["scholarly"] = scholarly_stub

# Pre-import rag.graphrag packages BEFORE any test file can create stub modules.
# This prevents stub modules from breaking subsequent imports.
_graphrag_packages = [
    "rag.graphrag",
    "rag.graphrag.general",
    "rag.graphrag.general.mind_map_extractor",
    "rag.graphrag.general.extractor",
    "rag.graphrag.entity_resolution",
    "rag.graphrag.utils",
    "rag.graphrag.memory",
    "rag.graphrag.llm_protocol",
    "rag.graphrag.entity_resolution_prompt",
]
for _pkg in _graphrag_packages:
    try:
        importlib.import_module(_pkg)
    except Exception:
        pass

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _patch_sqlglot_compatibility():
    """Patch sqlglot to support older code importing Expression from it."""
    # Must patch before importing any modules that depend on pyobvector
    # which then imports sqlglot with the broken import
    try:
        import sqlglot

        if not hasattr(sqlglot, "Expression"):
            # Need to import from sqlglot.exp to get Expression class
            from sqlglot import exp as sqlglot_exp

            sqlglot.Expression = sqlglot_exp.Expression
    except Exception:
        pass


# Apply the patch immediately at module load time, before any other imports
_patch_sqlglot_compatibility()


def _check_import(module_name: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True
    except (ImportError, SyntaxError):
        return False


skipif_no_openai = pytest.mark.skipif(not _check_import("openai"), reason="openai not installed - install with: pip install openai")

skipif_no_tiktoken = pytest.mark.skipif(not _check_import("tiktoken"), reason="tiktoken not installed - install with: pip install tiktoken")

skipif_no_elasticsearch = pytest.mark.skipif(not _check_import("elasticsearch_dsl"), reason="elasticsearch-dsl not installed")

unit = pytest.mark.unit
integration = pytest.mark.integration


def _patch_sqlglot_compatibility():
    """Patch sqlglot to support older code importing Expression from it."""
    try:
        import sqlglotc
        from sqlglotc import exp

        if not hasattr(sqlglotc, "Expression"):
            sqlglotc.Expression = exp.Expression
    except Exception:
        try:
            import sqlglot
            from sqlglot import exp

            if not hasattr(sqlglot, "Expression"):
                sqlglot.Expression = exp.Expression
        except Exception:
            pass


@pytest.fixture
def optional_modules():
    """Fixture providing safe import helpers."""
    return {
        "check_import": _check_import,
    }


def pytest_configure(config):
    """pytest hook that runs before test collection."""
    _patch_sqlglot_compatibility()


def pytest_collection_modifyitems(session, config, items):
    """Pre-import packages before test collection to prevent stub modules from breaking imports."""
    _pre_import_critical_packages()
    # Compat: this suite historically used pytest-asyncio marks.
    # In environments running only anyio plugin, treat asyncio-marked tests as anyio tests.
    for item in items:
        if item.get_closest_marker("asyncio") and not item.get_closest_marker("anyio"):
            item.add_marker(pytest.mark.anyio)


def _pre_import_critical_packages():
    """Pre-import critical packages to ensure they are real packages, not stub modules."""
    critical_packages = [
        "rag.graphrag",
        "rag.graphrag.general",
        "rag.graphrag.general.mind_map_extractor",
        "rag.graphrag.entity_resolution",
        "rag.graphrag.utils",
        "rag.graphrag.memory",
        "rag.graphrag.llm_protocol",
        "rag.graphrag.entity_resolution_prompt",
    ]

    for pkg in critical_packages:
        if pkg not in sys.modules:
            try:
                importlib.import_module(pkg)
            except Exception:
                pass
