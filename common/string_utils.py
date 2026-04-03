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

import re


def remove_redundant_spaces(txt: str):
    """
    Remove redundant spaces around punctuation marks while preserving meaningful spaces.

    This function performs two main operations:
    1. Remove spaces after left-boundary characters (opening brackets, etc.)
    2. Remove spaces before right-boundary characters (closing brackets, punctuation, etc.)

    Args:
        txt (str): Input text to process

    Returns:
        str: Text with redundant spaces removed
    """
    txt = re.sub(r"([(\[<]) +", r"\1", txt, flags=re.IGNORECASE)

    txt = re.sub(r"(\d) +\. +(\d)", r"\1.\2", txt, flags=re.IGNORECASE)
    txt = re.sub(r"(\d) +: +(\d)", r"\1:\2", txt, flags=re.IGNORECASE)

    # Normalize common email and URL patterns.
    txt = re.sub(r"([A-Za-z0-9._%+-]+)\s*@\s*([A-Za-z0-9.-]+)\s*\.\s*([A-Za-z]{2,})", r"\1@\2.\3", txt)
    txt = re.sub(r"\bhttps?\s*:\s*//", lambda m: m.group(0).replace(" ", ""), txt, flags=re.IGNORECASE)
    txt = re.sub(r"(https?://[^\s/]+)\s*/\s*", r"\1/", txt, flags=re.IGNORECASE)

    # Trim spaces only inside quotes, keeping outside spacing intact.
    txt = re.sub(r'(["\'])\s+(\S)', r"\1\2", txt)
    txt = re.sub(r'(\S)\s+(["\'])(?=[\s\.,!?;:\)]|$)', r"\1\2", txt)

    txt = re.sub(r" +([!?])", r"\1", txt, flags=re.IGNORECASE)
    txt = re.sub(r"([!?]) +([!?])", r"\1\2", txt, flags=re.IGNORECASE)

    txt = re.sub(r"([a-zA-Z0-9\]\"']) +\.", r"\1.", txt, flags=re.IGNORECASE)
    # Keep behavior for nested / non-ASCII parentheses, but tighten simple "(word) ." => "(word)."
    txt = re.sub(r"([A-Za-z0-9]\)) +\.", r"\1.", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\(([A-Za-z0-9 _-]+)\) +\.", r"(\1).", txt)
    txt = re.sub(r" +([,;:\)])", r"\1", txt, flags=re.IGNORECASE)
    txt = re.sub(r" +([>])", r"\1", txt, flags=re.IGNORECASE)

    txt = re.sub(r"([a-zA-Z]) +, +([a-zA-Z])", r"\1, \2", txt, flags=re.IGNORECASE)
    # Keep tabs/newlines untouched; only normalize regular spaces after comma.
    txt = re.sub(r", +", ", ", txt)

    return txt


def clean_markdown_block(text):
    """
    Remove Markdown code block syntax from the beginning and end of text.

    This function cleans Markdown code blocks by removing:
    - Opening ```Markdown tags (with optional whitespace and newlines)
    - Closing ``` tags (with optional whitespace and newlines)

    Args:
        text (str): Input text that may be wrapped in Markdown code blocks

    Returns:
        str: Cleaned text with Markdown code block syntax removed, and stripped of surrounding whitespace

    """
    # Remove opening ```Markdown tag with optional whitespace and newlines
    # Matches: optional whitespace + ```markdown + optional whitespace + optional newline
    text = re.sub(r"^\s*```markdown\s*\n?", "", text)

    # Remove closing ``` tag with optional whitespace and newlines
    # Matches: optional newline + optional whitespace + ``` + optional whitespace at end
    text = re.sub(r"\n?\s*```\s*$", "", text)

    # Return text with surrounding whitespace removed
    return text.strip()
