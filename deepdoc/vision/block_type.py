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
from rag.nlp import rag_tokenizer

_BLOCK_TYPE_PATTERNS = [
    ("^(20|19)[0-9]{2}[年/-][0-9]{1,2}[月/-][0-9]{1,2}日*$", "Dt"),
    (r"^(20|19)[0-9]{2}年$", "Dt"),
    (r"^(20|19)[0-9]{2}[年-][0-9]{1,2}月*$", "Dt"),
    ("^[0-9]{1,2}[月-][0-9]{1,2}日*$", "Dt"),
    (r"^第*[一二三四1-4]季度$", "Dt"),
    (r"^(20|19)[0-9]{2}年*[一二三四1-4]季度$", "Dt"),
    (r"^(20|19)[0-9]{2}[ABCDE]$", "Dt"),
    ("^[0-9.,+%/ -]+$", "Nu"),
    (r"^[0-9A-Z/\._~-]+$", "Ca"),
    (r"^[A-Z]*[a-z' -]+$", "En"),
    (r"^[0-9.,+-]+[0-9A-Za-z/$￥%<>（）()' -]+$", "NE"),
    (r"^.{1}$", "Sg"),
]


def block_type(text: str) -> str:
    """
    Classify text block type based on content patterns.

    Returns:
        Dt: Date
        Nu: Numeric
        Ca: Alphanumeric code
        En: English text
        NE: Numeric with English
        Sg: Single character
        Tx: Short text (2-11 tokens)
        Lx: Long text (12+ tokens)
        Nr: Person name (single token, 'nr' tag)
        Ot: Other
    """
    if not text:
        return "Ot"

    stripped = text.strip()
    if not stripped:
        return "Ot"

    for p, n in _BLOCK_TYPE_PATTERNS:
        if re.search(p, stripped):
            return n

    tokens = [t for t in rag_tokenizer.tokenize(stripped).split() if len(t) > 1]
    if len(tokens) > 3:
        if len(tokens) < 12:
            return "Tx"
        else:
            return "Lx"

    if len(tokens) == 1 and rag_tokenizer.tag(tokens[0]) == "nr":
        return "Nr"

    return "Ot"


def block_type_for_dict(b: dict) -> str:
    """
    Classify a block dict with 'text' key.

    Args:
        b: dict with 'text' key

    Returns:
        Block type string (see block_type)
    """
    return block_type(b.get("text", ""))
