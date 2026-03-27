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

"""
Robust PDF metadata extraction module.

This module provides layout-aware and VLM-based extraction for PDF metadata
(title, authors, abstract) to replace brittle regex-based approaches.

Key features:
1. Layout-aware parsing using pdfplumber for accurate position detection
2. PDF native metadata extraction (XMP/Info dictionary)
3. VLM-based extraction as fallback for complex cases
4. Multi-pattern matching with confidence scoring
"""

import logging
import re
from io import BytesIO
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

# Section header patterns for different languages
SECTION_PATTERNS = {
    "en": [
        r"^\s*abstract\s*$",
        r"^\s*summary\s*$",
        r"^\s*introduction\s*$",
        r"^\s*keywords?\s*$",
    ],
    "zh": [
        r"^\s*摘要\s*$",
        r"^\s*概要\s*$",
        r"^\s*引言\s*$",
        r"^\s*关键词\s*$",
    ],
    "ja": [
        r"^\s*概要\s*$",
        r"^\s*要旨\s*$",
        r"^\s*keywords?\s*$",
    ],
}

# Compile patterns for efficiency
_COMPILED_PATTERNS: Dict[str, List[Tuple[str, re.Pattern]]] = {}
for lang, patterns in SECTION_PATTERNS.items():
    _COMPILED_PATTERNS[lang] = [(p, re.compile(p, re.IGNORECASE)) for p in patterns]


def extract_pdf_native_metadata(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Extract metadata from PDF native metadata (XMP, Info dictionary).

    Args:
        pdf_bytes: PDF file bytes

    Returns:
        Dictionary containing native PDF metadata
    """
    metadata = {
        "title": None,
        "author": None,
        "subject": None,
        "creator": None,
        "producer": None,
        "creation_date": None,
        "modification_date": None,
    }

    try:
        import pypdf

        with BytesIO(pdf_bytes) as f:
            reader = pypdf.PdfReader(f)
            if reader.metadata:
                metadata["title"] = reader.metadata.get("/Title")
                metadata["author"] = reader.metadata.get("/Author")
                metadata["subject"] = reader.metadata.get("/Subject")
                metadata["creator"] = reader.metadata.get("/Creator")
                metadata["producer"] = reader.metadata.get("/Producer")
                metadata["creation_date"] = reader.metadata.get("/CreationDate")
                metadata["modification_date"] = reader.metadata.get("/ModDate")
    except Exception as e:
        logger.debug(f"Failed to extract native PDF metadata: {e}")

    return {k: v for k, v in metadata.items() if v is not None}


def _check_section_header(text: str, lang: str = "en") -> bool:
    """
    Check if text is a section header (abstract, keywords, etc.).

    Args:
        text: Text to check
        lang: Language pattern set to use

    Returns:
        True if text matches a section header pattern
    """
    if not isinstance(text, str):
        return False

    text_lower = text.lower().strip()
    patterns = _COMPILED_PATTERNS.get(lang, _COMPILED_PATTERNS["en"])

    for _, pattern in patterns:
        if pattern.match(text_lower):
            return True
    return False


def extract_metadata_by_layout(
    pdf_bytes: bytes,
    lang: str = "en",
    max_pages: int = 5,
) -> Dict[str, Any]:
    """
    Extract metadata using layout-aware parsing with pdfplumber.

    Uses position-based detection to find title, authors, and abstract
    by analyzing the visual layout of the first few pages.

    Args:
        pdf_bytes: PDF file bytes
        lang: Language for pattern matching
        max_pages: Maximum number of pages to scan

    Returns:
        Dictionary with extracted metadata
    """
    result = {
        "title": None,
        "authors": None,
        "abstract": None,
        "confidence": {
            "title": 0.0,
            "authors": 0.0,
            "abstract": 0.0,
        },
    }

    try:
        import pdfplumber

        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            pages_to_scan = min(max_pages, len(pdf.pages))
            all_blocks = []

            for page_idx in range(pages_to_scan):
                page = pdf.pages[page_idx]
                width = page.width or 600

                # Extract words with position info
                words = page.extract_words(keep_blank_chars=False, use_text_flow=True)

                if not words:
                    # Fallback to text extraction
                    text = page.extract_text()
                    if text:
                        lines = text.split("\n")
                        for line_idx, line in enumerate(lines):
                            if line.strip():
                                all_blocks.append(
                                    {
                                        "text": line.strip(),
                                        "page": page_idx,
                                        "top": line_idx * 12,
                                        "bottom": (line_idx + 1) * 12,
                                        "x0": 0,
                                        "x1": width,
                                        "is_heading": False,
                                    }
                                )
                    continue

                # Group words into lines
                line_threshold = 5
                current_line = [words[0]]

                for word in words[1:]:
                    word_top = word.get("top", 0)
                    line_top = current_line[0].get("top", 0)
                    if abs(word_top - line_top) <= line_threshold:
                        current_line.append(word)
                    else:
                        # Process current line
                        if current_line:
                            line_text = " ".join(w.get("text", "") for w in current_line).strip()
                            if line_text:
                                all_blocks.append(
                                    {
                                        "text": line_text,
                                        "page": page_idx,
                                        "top": min(w.get("top", 0) for w in current_line),
                                        "bottom": max(w.get("bottom", 0) for w in current_line),
                                        "x0": min(w.get("x0", 0) for w in current_line),
                                        "x1": max(w.get("x1", 0) for w in current_line),
                                        "is_heading": False,
                                    }
                                )
                        current_line = [word]

                # Process last line
                if current_line:
                    line_text = " ".join(w.get("text", "") for w in current_line).strip()
                    if line_text:
                        all_blocks.append(
                            {
                                "text": line_text,
                                "page": page_idx,
                                "top": min(w.get("top", 0) for w in current_line),
                                "bottom": max(w.get("bottom", 0) for w in current_line),
                                "x0": min(w.get("x0", 0) for w in current_line),
                                "x1": max(w.get("x1", 0) for w in current_line),
                                "is_heading": False,
                            }
                        )

            # Analyze blocks to extract metadata
            if all_blocks:
                result = _analyze_layout_blocks(all_blocks, lang, pages_to_scan)

    except Exception as e:
        logger.debug(f"Layout-based metadata extraction failed: {e}")

    return result


def _analyze_layout_blocks(
    blocks: List[Dict],
    lang: str,
    total_pages: int,
) -> Dict[str, Any]:
    """
    Analyze layout blocks to extract title, authors, and abstract.

    Args:
        blocks: List of text blocks with position info
        lang: Language for pattern matching
        total_pages: Total number of pages scanned

    Returns:
        Dictionary with extracted metadata and confidence scores
    """
    result = {
        "title": None,
        "authors": None,
        "abstract": None,
        "confidence": {
            "title": 0.0,
            "authors": 0.0,
            "abstract": 0.0,
        },
    }

    if not blocks:
        return result

    # Find title: First large text block on first page, not a section header
    first_page_blocks = [b for b in blocks if b["page"] == 0]
    for block in first_page_blocks[:10]:  # Check first 10 blocks
        text = block["text"]
        if _check_section_header(text, lang):
            break

        # Title heuristics: not too long, not containing special chars
        if text and 3 < len(text) < 200:
            if not re.search(r"[:;]\s*\d", text):  # Avoid page numbers
                result["title"] = text
                result["confidence"]["title"] = 0.7
                break

    # Find authors: Look for blocks after title with name patterns
    if result["title"]:
        title_idx = None
        for i, b in enumerate(first_page_blocks):
            if b["text"] == result["title"]:
                title_idx = i
                break

        if title_idx is not None:
            # Check following blocks for author-like content
            author_parts = []
            for block in first_page_blocks[title_idx + 1 : title_idx + 6]:
                text = block["text"]
                # Skip if it's a section header or contains email separator
                if _check_section_header(text, lang):
                    break
                if "@" in text and "email" in text.lower():
                    break
                # Check for common name patterns
                if text and len(text) < 100:
                    if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", text):
                        author_parts.append(text)
                    elif re.match(r"^[A-Z]\.\s*[A-Z][a-z]+", text):
                        author_parts.append(text)

            if author_parts:
                result["authors"] = ", ".join(author_parts[:3])  # Max 3 authors
                result["confidence"]["authors"] = 0.6

    # Find abstract: Look for section header "abstract" and collect following text
    abstract_blocks = []
    abstract_start = None

    for i, block in enumerate(blocks):
        text = block["text"]
        if _check_section_header(text, lang):
            if "abstract" in text.lower() or "摘要" in text:
                abstract_start = i
                break

    if abstract_start is not None:
        # Collect blocks until next section header or end
        for block in blocks[abstract_start + 1 : abstract_start + 20]:
            text = block["text"]
            if _check_section_header(text, lang):
                break
            if text and len(text) > 30:  # Filter noise
                abstract_blocks.append(text)

        if abstract_blocks:
            result["abstract"] = " ".join(abstract_blocks[:10])  # Limit to ~10 blocks
            result["confidence"]["abstract"] = 0.7

    return result


def extract_metadata_with_vlm(
    pdf_bytes: bytes,
    vlm_model: Any = None,
    max_pages: int = 3,
) -> Dict[str, Any]:
    """
    Extract metadata using Vision-Language Model.

    This is a more robust approach that can handle complex layouts
    and non-standard PDF structures.

    Args:
        pdf_bytes: PDF file bytes
        vlm_model: VLM model instance (optional, will use default if not provided)
        max_pages: Number of first pages to analyze

    Returns:
        Dictionary with extracted metadata
    """
    result = {
        "title": None,
        "authors": None,
        "abstract": None,
    }

    try:
        import pdf2image

        # Convert PDF pages to images
        images = pdf2image.convert_from_bytes(pdf_bytes, first_page=1, last_page=max_pages)

        if not images:
            return result

        # Analyze first page for title and authors
        first_page_img = images[0]

        # Use VLM if available, otherwise skip
        if vlm_model is not None:
            prompt = """Analyze this scientific/academic paper first page.
            Extract and return ONLY the following information in JSON format:
            {"title": "...", "authors": "...", "abstract": "..."}

            - title: The paper title
            - authors: The author names (comma separated)
            - abstract: The abstract text (if visible on first page)

            If any field is not visible or unclear, use null.
            Only return valid JSON, nothing else."""

            try:
                response = vlm_model.chat(first_page_img, prompt)
                # Parse response - this depends on VLM implementation
                result = _parse_vlm_response(response)
            except Exception as e:
                logger.debug(f"VLM metadata extraction failed: {e}")

    except ImportError as e:
        logger.debug(f"Missing dependency for VLM extraction: {e}")
    except Exception as e:
        logger.debug(f"VLM metadata extraction failed: {e}")

    return result


def _parse_vlm_response(response: Any) -> Dict[str, Any]:
    """Parse VLM response to extract metadata."""
    result = {
        "title": None,
        "authors": None,
        "abstract": None,
    }

    try:
        # Try to parse as JSON
        if isinstance(response, str):
            import json

            # Find JSON in response
            json_start = response.find("{")
            if json_start >= 0:
                json_end = response.rfind("}") + 1
                if json_end > json_start:
                    data = json.loads(response[json_start:json_end])
                    result["title"] = data.get("title")
                    result["authors"] = data.get("authors")
                    result["abstract"] = data.get("abstract")
    except Exception:
        pass

    return result


def extract_pdf_metadata(
    pdf_bytes: bytes,
    use_vlm: bool = False,
    vlm_model: Any = None,
    lang: str = "en",
    max_pages: int = 5,
) -> Dict[str, Any]:
    """
    Main entry point for robust PDF metadata extraction.

    Tries multiple methods in order of reliability:
    1. Native PDF metadata (XMP/Info)
    2. Layout-aware parsing
    3. VLM-based extraction (if enabled)

    Args:
        pdf_bytes: PDF file bytes
        use_vlm: Whether to use VLM as fallback
        vlm_model: VLM model instance (required if use_vlm is True)
        lang: Language for pattern matching
        max_pages: Maximum pages to scan

    Returns:
        Dictionary containing extracted metadata
    """
    result = {
        "title": None,
        "authors": None,
        "abstract": None,
        "source": None,
    }

    # Step 1: Try native PDF metadata
    native_meta = extract_pdf_native_metadata(pdf_bytes)
    if native_meta.get("title"):
        result["title"] = native_meta["title"]
        result["source"] = "native"
    if native_meta.get("author"):
        result["authors"] = native_meta["author"]

    # Step 2: Try layout-based extraction
    layout_meta = extract_metadata_by_layout(pdf_bytes, lang, max_pages)

    # Use layout-based results if native is missing or has low confidence
    if not result["title"] and layout_meta.get("title"):
        result["title"] = layout_meta["title"]
        result["source"] = "layout"

    if not result["authors"] and layout_meta.get("authors"):
        result["authors"] = layout_meta["authors"]

    if layout_meta.get("abstract"):
        result["abstract"] = layout_meta["abstract"]

    # Step 3: Try VLM if enabled and previous methods insufficient
    if use_vlm and vlm_model is not None:
        vlm_meta = extract_metadata_with_vlm(pdf_bytes, vlm_model, max_pages=3)

        if not result["title"] and vlm_meta.get("title"):
            result["title"] = vlm_meta["title"]
            result["source"] = "vlm"

        if not result["authors"] and vlm_meta.get("authors"):
            result["authors"] = vlm_meta["authors"]

        if not result["abstract"] and vlm_meta.get("abstract"):
            result["abstract"] = vlm_meta["abstract"]

    # Clean up results
    if result["title"]:
        result["title"] = result["title"].strip()
    if result["authors"]:
        result["authors"] = result["authors"].strip()
    if result["abstract"]:
        result["abstract"] = result["abstract"].strip()

    return result


# Backward compatibility: provide function matching old interface
def extract_metadata(
    pdf_bytes: bytes,
    use_vlm: bool = False,
    vlm_model: Any = None,
    lang: str = "en",
) -> Dict[str, Any]:
    """
    Backward-compatible metadata extraction.

    Args:
        pdf_bytes: PDF file bytes
        use_vlm: Whether to use VLM as fallback
        vlm_model: VLM model instance
        lang: Language for pattern matching

    Returns:
        Dictionary containing extracted metadata
    """
    return extract_pdf_metadata(pdf_bytes, use_vlm, vlm_model, lang)
