#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
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
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class HybridWeightConfig(BaseModel):
    weights: str = Field(default="0.3,0.7", description="Hybrid search weights in format 'token_weight,vector_weight'")

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: str) -> str:
        try:
            parts = v.split(",")
            if len(parts) != 2:
                raise ValueError("Must contain exactly two values separated by comma")
            w1, w2 = float(parts[0]), float(parts[1])
            if not (0 <= w1 <= 1 and 0 <= w2 <= 1):
                raise ValueError("Weights must be between 0 and 1")
        except (ValueError, TypeError) as e:
            logging.warning(f"Invalid hybrid_weight format '{v}': {e}. Using default '0.3,0.7'.")
            return "0.3,0.7"
        return v


class RetrievalConfig(BaseModel):
    similarity_threshold: float = Field(default=0.2, ge=0.0, le=1.0)
    vector_similarity_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    top_k: int = Field(default=1024, ge=1)
    page_size: int = Field(default=30, ge=1)
    hybrid_weight: Optional[str] = None

    @field_validator("hybrid_weight", mode="before")
    @classmethod
    def validate_hybrid_weight(cls, v: Any) -> Any:
        if v is None or v == "":
            return "0.3,0.7"
        if isinstance(v, str):
            try:
                parts = v.split(",")
                if len(parts) != 2:
                    raise ValueError("Must contain exactly two values")
                w1, w2 = float(parts[0]), float(parts[1])
                if not (0 <= w1 <= 1 and 0 <= w2 <= 1):
                    raise ValueError("Weights must be between 0 and 1")
            except (ValueError, TypeError) as e:
                logging.warning(f"Invalid hybrid_weight '{v}': {e}. Using default.")
                return "0.3,0.7"
        return v


class ChunkingConfig(BaseModel):
    chunk_token_num: int = Field(default=128, ge=16, le=2048)
    delimiter: str = Field(default="\n")
    overlapped_percent: int = Field(default=0, ge=0, le=50)

    @field_validator("delimiter")
    @classmethod
    def validate_delimiter(cls, v: str) -> str:
        if not v:
            return "\n"
        return v


def validate_hybrid_weight(weight_str: Optional[str]) -> str:
    """Validate and normalize hybrid weight string.

    Args:
        weight_str: Weight string in format 'token_weight,vector_weight' or None

    Returns:
        Validated weight string, defaults to '0.3,0.7' if invalid
    """
    if not weight_str:
        return "0.3,0.7"
    try:
        parts = weight_str.split(",")
        if len(parts) != 2:
            raise ValueError("Must contain exactly two values")
        w1, w2 = float(parts[0]), float(parts[1])
        if not (0 <= w1 <= 1 and 0 <= w2 <= 1):
            raise ValueError("Weights must be between 0 and 1")
        return weight_str
    except (ValueError, TypeError) as e:
        logging.warning(f"Invalid hybrid_weight '{weight_str}': {e}. Using default '0.3,0.7'.")
        return "0.3,0.7"


def validate_similarity_threshold(threshold: float) -> float:
    """Validate similarity threshold value."""
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        logging.warning(f"Invalid threshold type {type(threshold)}. Using default 0.2.")
        return 0.2
    return max(0.0, min(1.0, float(threshold)))


def validate_page_size(page_size: int) -> int:
    """Validate and normalize page size."""
    if not isinstance(page_size, int):
        try:
            page_size = int(page_size)
        except (ValueError, TypeError):
            logging.warning(f"Invalid page_size type {type(page_size)}. Using default 30.")
            return 30
    return max(1, min(page_size, 1000))


def validate_parser_config(parser_config: Optional[dict]) -> dict:
    """Validate and normalize parser configuration.

    Args:
        parser_config: Parser configuration dict or None

    Returns:
        Validated parser configuration dict
    """
    if parser_config is None:
        parser_config = {}

    validated = {}

    chunk_token_num = parser_config.get("chunk_token_num", 128)
    if isinstance(chunk_token_num, (int, float)):
        chunk_token_num = int(chunk_token_num)
        validated["chunk_token_num"] = max(16, min(chunk_token_num, 2048))
    else:
        validated["chunk_token_num"] = 128

    validated["delimiter"] = parser_config.get("delimiter", "\n")
    if not validated["delimiter"]:
        validated["delimiter"] = "\n"

    overlapped_percent = parser_config.get("overlapped_percent", 0)
    if isinstance(overlapped_percent, (int, float)):
        overlapped_percent = int(overlapped_percent)
        validated["overlapped_percent"] = max(0, min(overlapped_percent, 50))
    else:
        validated["overlapped_percent"] = 0

    validated["auto_keywords"] = int(parser_config.get("auto_keywords", 0)) if isinstance(parser_config.get("auto_keywords"), (int, float, str)) else 0
    validated["auto_questions"] = int(parser_config.get("auto_questions", 0)) if isinstance(parser_config.get("auto_questions"), (int, float, str)) else 0
    validated["enable_metadata"] = bool(parser_config.get("enable_metadata", False))
    validated["metadata"] = parser_config.get("metadata")
    validated["filename_embd_weight"] = parser_config.get("filename_embd_weight", 0.1)
    validated["toc_extraction"] = bool(parser_config.get("toc_extraction", False))

    for key, value in parser_config.items():
        if key not in validated:
            validated[key] = value

    return validated


def validate_kb_parser_config(kb_parser_config: Optional[dict]) -> dict:
    """Validate and normalize knowledge base parser configuration.

    Args:
        kb_parser_config: KB parser configuration dict or None

    Returns:
        Validated KB parser configuration dict
    """
    if kb_parser_config is None:
        kb_parser_config = {}

    validated = {}

    validated["llm_id"] = kb_parser_config.get("llm_id")
    validated["tag_kb_ids"] = kb_parser_config.get("tag_kb_ids", [])
    if not isinstance(validated["tag_kb_ids"], list):
        validated["tag_kb_ids"] = []

    topn_tags = kb_parser_config.get("topn_tags", 3)
    if isinstance(topn_tags, (int, float)):
        validated["topn_tags"] = max(1, min(int(topn_tags), 10))
    else:
        validated["topn_tags"] = 3

    raptor = kb_parser_config.get("raptor", {})
    if isinstance(raptor, dict):
        validated["raptor"] = {
            "use_raptor": bool(raptor.get("use_raptor", False)),
            "prompt": raptor.get("prompt", "Please summarize the following paragraphs. Be careful with the numbers, do not make things up. Paragraphs as following:\n      {cluster_content}\nThe above is the content you need to summarize."),
            "max_token": max(64, min(int(raptor.get("max_token", 256)), 1024)),
            "threshold": max(0.0, min(float(raptor.get("threshold", 0.1)), 1.0)),
            "max_cluster": max(1, min(int(raptor.get("max_cluster", 64)), 256)),
            "random_seed": int(raptor.get("random_seed", 0)),
            "scope": raptor.get("scope", "file") if raptor.get("scope") in ["file", "kb"] else "file",
        }

    graphrag = kb_parser_config.get("graphrag", {})
    if isinstance(graphrag, dict):
        validated["graphrag"] = {
            "use_graphrag": bool(graphrag.get("use_graphrag", False)),
            "entity_types": graphrag.get("entity_types", ["organization", "person", "geo", "event", "category"]),
            "method": graphrag.get("method", "light") if graphrag.get("method") in ["light", "general"] else "light",
            "resolution": bool(graphrag.get("resolution", False)),
            "community": bool(graphrag.get("community", False)),
        }

    for key, value in kb_parser_config.items():
        if key not in validated:
            validated[key] = value

    return validated
