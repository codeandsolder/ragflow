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

import pytest
import importlib

import sqlglot
from sqlglot import exp as sqlglot_exp

if not hasattr(sqlglot, "Expression"):
    sqlglot.Expression = sqlglot_exp.Expression

try:
    import rag.llm.chat_model  # noqa: F401
    import rag.llm.embedding_model  # noqa: F401
    import rag.llm.rerank_model  # noqa: F401

    import rag.llm

    rag.llm.chat_model = importlib.import_module("rag.llm.chat_model")
    rag.llm.embedding_model = importlib.import_module("rag.llm.embedding_model")
    rag.llm.rerank_model = importlib.import_module("rag.llm.rerank_model")

    _llm_import_ok = True
except (ImportError, ModuleNotFoundError, SyntaxError):
    _llm_import_ok = False

skipif_no_llm = pytest.mark.skipif(not _llm_import_ok, reason="rag.llm module cannot be imported due to dependency issues")
