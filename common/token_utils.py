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

import logging
import os
from functools import lru_cache
from typing import Any

import tiktoken

from common.file_utils import get_project_base_directory

logger = logging.getLogger(__name__)

# Initialize tiktoken encoder with caching
tiktoken_cache_dir = get_project_base_directory()
os.environ["TIKTOKEN_CACHE_DIR"] = tiktoken_cache_dir
encoder = tiktoken.get_encoding("cl100k_base")


@lru_cache(maxsize=4096)
def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string using tiktoken.

    Args:
        string: The text string to encode.

    Returns:
        Number of tokens in the string, or 0 if encoding fails.
    """
    if not string:
        return 0
    try:
        code_list = encoder.encode(string)
        return len(code_list)
    except Exception as e:
        logger.warning(f"Token encoding error for string (first 50 chars): '{string[:50]}': {e}")
        return 0


def _get_attribute_value(obj: Any, *attrs: str) -> Any:
    """Safely get a nested attribute from an object.

    Args:
        obj: The object to get attributes from.
        *attrs: Sequence of attribute names to traverse.

    Returns:
        The attribute value if found, otherwise None.
    """
    current = obj
    for attr in attrs:
        try:
            current = getattr(current, attr)
        except Exception:
            return None
    return current


def total_token_count_from_response(resp: Any) -> int:
    """Extract token count from LLM response in various formats.

    Handles different response structures from various LLM providers.
    Returns 0 if token count cannot be determined.

    Args:
        resp: The LLM response object (can be None, dict, or object with attributes).

    Returns:
        Total token count from the response, or 0 if not available.
    """
    if resp is None:
        return 0

    # Try various attribute-based response formats
    token_count = _get_attribute_value(resp, "usage", "total_tokens")
    if token_count is not None:
        return token_count

    token_count = _get_attribute_value(resp, "usage_metadata", "total_tokens")
    if token_count is not None:
        return token_count

    token_count = _get_attribute_value(resp, "meta", "billed_units", "input_tokens")
    if token_count is not None:
        return token_count

    # Try dictionary-based response formats
    if isinstance(resp, dict):
        if "usage" in resp:
            usage = resp["usage"]
            if isinstance(usage, dict):
                if "total_tokens" in usage:
                    return usage["total_tokens"]
                if "input_tokens" in usage and "output_tokens" in usage:
                    return usage["input_tokens"] + usage["output_tokens"]

        if "meta" in resp:
            meta = resp["meta"]
            if isinstance(meta, dict) and "tokens" in meta:
                tokens = meta["tokens"]
                if isinstance(tokens, dict) and "input_tokens" in tokens and "output_tokens" in tokens:
                    return tokens["input_tokens"] + tokens["output_tokens"]

    return 0


def truncate(string: str, max_len: int) -> str:
    """Truncate text to a maximum number of tokens.

    Args:
        string: The text to truncate.
        max_len: Maximum number of tokens.

    Returns:
        Truncated text that does not exceed max_len tokens.
    """
    return encoder.decode(encoder.encode(string)[:max_len])
