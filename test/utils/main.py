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
"""Test utilities package."""

from test.utils.llm_mocks import (
    create_mock_embedding_response,
    create_mock_chat_response,
    create_mock_stream_chunk,
    patch_llm_client,
    patch_embedding_client,
    MockLLMClient,
    AsyncMockLLMClient,
    create_failing_llm_client,
)

from test.utils.assertions import (
    assert_response_success,
    assert_response_error,
    assert_valid_embedding,
    assert_valid_embeddings,
    assert_chunks_valid,
    assert_token_count_approx,
    assert_dict_contains,
    assert_status_code,
    ResponseAssertions,
    ChunkAssertions,
)

from test.utils.fixtures import (
    mock_env,
    mock_embedding_response,
    mock_chat_response,
    sample_texts,
    sample_chunks,
    temp_text_file,
    temp_json_file,
    mock_settings,
    mock_storage,
    mock_database,
    mock_redis,
    mock_es_client,
    disable_tiktoken,
    disable_openai,
    reset_circuit_breaker,
    mock_circuit_breaker,
)

from test.utils import (
    TestHelper,
    AsyncTestHelper,
    MockData,
    TestValidator,
    TestBuilder,
    TestScenario,
    TestMock,
    TEST_HELPER,
    ASYNC_TEST_HELPER,
    MOCK_DATA,
    TEST_VALIDATOR,
    TEST_BUILDER,
    TEST_SCENARIO,
    TEST_MOCK,
)

__all__ = [
    # LLM Mocks
    "create_mock_embedding_response",
    "create_mock_chat_response",
    "create_mock_stream_chunk",
    "patch_llm_client",
    "patch_embedding_client",
    "MockLLMClient",
    "AsyncMockLLMClient",
    "create_failing_llm_client",
    # Assertions
    "assert_response_success",
    "assert_response_error",
    "assert_valid_embedding",
    "assert_valid_embeddings",
    "assert_chunks_valid",
    "assert_token_count_approx",
    "assert_dict_contains",
    "assert_status_code",
    "ResponseAssertions",
    "ChunkAssertions",
    # Fixtures
    "mock_env",
    "mock_embedding_response",
    "mock_chat_response",
    "sample_texts",
    "sample_chunks",
    "temp_text_file",
    "temp_json_file",
    "mock_settings",
    "mock_storage",
    "mock_database",
    "mock_redis",
    "mock_es_client",
    "disable_tiktoken",
    "disable_openai",
    "reset_circuit_breaker",
    "mock_circuit_breaker",
    # Helpers
    "TestHelper",
    "AsyncTestHelper",
    "MockData",
    "TestValidator",
    "TestBuilder",
    "TestScenario",
    "TestMock",
    "TEST_HELPER",
    "ASYNC_TEST_HELPER",
    "MOCK_DATA",
    "TEST_VALIDATOR",
    "TEST_BUILDER",
    "TEST_SCENARIO",
    "TEST_MOCK",
]
