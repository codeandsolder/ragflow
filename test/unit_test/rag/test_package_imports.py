#
#  Copyright 2026 The InfiniFlow Authors. All Rights Reserved.
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

def test_common_package_exports():
    from common import file_utils
    from common.misc_utils import get_uuid

    assert file_utils is not None
    assert callable(get_uuid)


def test_rag_nlp_package_exports():
    from rag.nlp import naive_merge, concat_img, find_codec

    assert callable(naive_merge)
    assert callable(concat_img)
    assert callable(find_codec)


def test_rag_llm_package_exports():
    from rag.llm import embedding_model, rerank_model

    assert isinstance(embedding_model, dict)
    assert isinstance(rerank_model, dict)


def test_agent_tools_package_exports():
    from agent.tools import RetrievalParam

    assert RetrievalParam is not None
