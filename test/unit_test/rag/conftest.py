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
Pytest marker-based approach for optional dependency handling.

Tests are skipped if optional dependencies are not installed.
"""

import pytest


def _check_import(module_name: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True
    except (ImportError, SyntaxError):
        return False


skipif_no_openai = pytest.mark.skipif(not _check_import("openai"), reason="openai not installed - install with: pip install openai")

skipif_no_tiktoken = pytest.mark.skipif(not _check_import("tiktoken"), reason="tiktoken not installed - install with: pip install tiktoken")

skipif_no_dashscope = pytest.mark.skipif(not _check_import("dashscope"), reason="dashscope not installed - install with: pip install dashscope")

skipif_no_zhipuai = pytest.mark.skipif(not _check_import("zhipuai"), reason="zhipuai not installed - install with: pip install zhipuai")

skipif_no_ollama = pytest.mark.skipif(not _check_import("ollama"), reason="ollama not installed - install with: pip install ollama")

skipif_no_litellm = pytest.mark.skipif(not _check_import("litellm"), reason="litellm not installed - install with: pip install litellm")

skipif_no_elasticsearch_dsl = pytest.mark.skipif(not _check_import("elasticsearch_dsl"), reason="elasticsearch_dsl not installed - install with: pip install elasticsearch-dsl")

skipif_no_httpx = pytest.mark.skipif(not _check_import("httpx"), reason="httpx not installed - install with: pip install httpx")


@pytest.fixture
def optional_modules():
    """Fixture providing safe import helpers."""
    return {
        "check_import": _check_import,
        "safe_import": lambda m, d=None: __import__(m) if _check_import(m) else d,
    }
