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

import sys
import importlib
from pathlib import Path

import pytest

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
