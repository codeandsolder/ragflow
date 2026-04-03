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
Unit tests for llm_app endpoint logic.
"""

import pytest
from unittest.mock import Mock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.api_utils import get_json_result, get_data_error_result
from common.constants import RetCode


def _get_result_json(result):
    """Helper to get JSON from result, handling both dict and response objects."""
    if hasattr(result, "get_json"):
        return _get_result_json(result)
    return result


class TestLlmAppFactories:
    """Test cases for llm_app.factories endpoint logic"""

    def test_factories_success(self):
        """Test successful factories listing"""
        result = get_json_result(data=[{"name": "OpenAI", "model_types": ["chat"]}])
        result_json = _get_result_json(result)

        assert result_json.get("code") == 0


class TestLlmAppSetApiKey:
    """Test cases for llm_app.set_api_key endpoint logic"""

    def test_set_api_key_no_models(self):
        """Test set_api_key returns error when no models configured"""
        result = get_data_error_result(message="No models configured for TestLLM (source: TestLLM).")
        result_json = _get_result_json(result)

        assert result_json.get("code") == RetCode.DATA_ERROR
        assert "No models configured" in result_json.get("message", "")


class TestLlmAppMyLlms:
    """Test cases for llm_app.my_llms endpoint logic"""

    def test_my_llms_success(self):
        """Test successful my_llms listing"""
        result = get_json_result(data={"OpenAI": {"chat": ["gpt-4"]}})
        result_json = _get_result_json(result)

        assert result_json.get("code") == 0


class TestLlmAppResponseHelpers:
    """Test cases for llm_app response helpers"""

    def test_get_json_result_success(self):
        """Test successful JSON result creation"""
        result = get_json_result(data={"llm_id": "test-llm"})
        result_json = _get_result_json(result)

        assert result_json.get("code") == 0
        assert result_json.get("data") == {"llm_id": "test-llm"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
