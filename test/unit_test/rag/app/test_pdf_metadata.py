"""
Unit tests for PDF metadata extraction module.

Tests cover:
- Native PDF metadata extraction
- Layout-aware parsing
- VLM-based extraction (mocked)
- Integration tests with various PDF formats
"""

import io
import pytest
from unittest.mock import Mock, patch, MagicMock

from rag.app.pdf_metadata import (
    extract_pdf_native_metadata,
    extract_metadata_by_layout,
    extract_metadata_with_vlm,
    extract_pdf_metadata,
    _check_section_header,
    _analyze_layout_blocks,
)


class TestCheckSectionHeader:
    """Tests for section header detection."""

    def test_abstract_english(self):
        assert _check_section_header("Abstract", "en") is True
        assert _check_section_header("ABSTRACT", "en") is True
        assert _check_section_header("  abstract  ", "en") is True

    def test_abstract_chinese(self):
        assert _check_section_header("摘要", "zh") is True
        assert _check_section_header("概要", "zh") is True

    def test_keywords(self):
        assert _check_section_header("Keywords", "en") is True
        assert _check_section_header("关键词", "zh") is True

    def test_non_header(self):
        assert _check_section_header("Introduction to Machine Learning", "en") is False
        assert _check_section_header("This is a regular paragraph.", "en") is False
        assert _check_section_header("", "en") is False
        assert _check_section_header(None, "en") is False

    def test_mixed_case(self):
        assert _check_section_header("INTRODUCTION", "en") is True
        assert _check_section_header("AbStRaCt", "en") is True


class TestAnalyzeLayoutBlocks:
    """Tests for layout block analysis."""

    def test_empty_blocks(self):
        result = _analyze_layout_blocks([], "en", 1)
        assert result["title"] is None
        assert result["authors"] is None
        assert result["abstract"] is None

    def test_title_extraction(self):
        blocks = [
            {"text": "Deep Learning for Natural Language Processing", "page": 0, "top": 0, "bottom": 20, "x0": 0, "x1": 500},
            {"text": "John Smith", "page": 0, "top": 30, "bottom": 50, "x0": 0, "x1": 100},
        ]
        result = _analyze_layout_blocks(blocks, "en", 1)
        assert result["title"] == "Deep Learning for Natural Language Processing"
        assert result["confidence"]["title"] > 0

    def test_author_extraction(self):
        blocks = [
            {"text": "Paper Title Here", "page": 0, "top": 0, "bottom": 20, "x0": 0, "x1": 500},
            {"text": "John Smith", "page": 0, "top": 30, "bottom": 50, "x0": 0, "x1": 100},
            {"text": "Jane Doe", "page": 0, "top": 60, "bottom": 80, "x0": 0, "x1": 100},
            {"text": "Abstract", "page": 0, "top": 100, "bottom": 120, "x0": 0, "x1": 100},
        ]
        result = _analyze_layout_blocks(blocks, "en", 1)
        assert result["title"] == "Paper Title Here"
        assert "John Smith" in result["authors"]

    def test_abstract_extraction(self):
        blocks = [
            {"text": "Paper Title", "page": 0, "top": 0, "bottom": 20, "x0": 0, "x1": 500},
            {"text": "Abstract", "page": 0, "top": 100, "bottom": 120, "x0": 0, "x1": 100},
            {"text": "This paper presents a novel approach to machine learning that achieves state-of-the-art results.", "page": 0, "top": 130, "bottom": 150, "x0": 0, "x1": 500},
            {"text": "Introduction", "page": 0, "top": 200, "bottom": 220, "x0": 0, "x1": 100},
        ]
        result = _analyze_layout_blocks(blocks, "en", 1)
        assert result["abstract"] is not None
        assert "novel approach" in result["abstract"]

    def test_stops_at_section_header(self):
        blocks = [
            {"text": "Paper Title", "page": 0, "top": 0, "bottom": 20, "x0": 0, "x1": 500},
            {"text": "Abstract", "page": 0, "top": 30, "bottom": 50, "x0": 0, "x1": 100},
        ]
        result = _analyze_layout_blocks(blocks, "en", 1)
        # Title should stop before "Abstract"
        assert result["title"] == "Paper Title"


class TestExtractPdfNativeMetadata:
    """Tests for native PDF metadata extraction."""

    def test_empty_bytes(self):
        result = extract_pdf_native_metadata(b"")
        assert result == {}

    def test_invalid_pdf(self):
        result = extract_pdf_native_metadata(b"not a pdf")
        assert result == {}

    @patch("pypdf.PdfReader")
    def test_valid_pdf_with_metadata(self, mock_pdf_reader):
        mock_reader = Mock()
        mock_reader.metadata = {
            "/Title": "Test Paper Title",
            "/Author": "John Doe",
            "/Subject": "Test Subject",
        }
        mock_pdf_reader.return_value = mock_reader

        with patch("rag.app.pdf_metadata.BytesIO"):
            result = extract_pdf_native_metadata(b"fake pdf content")

        assert result.get("title") == "Test Paper Title"
        assert result.get("author") == "John Doe"

    @patch("pypdf.PdfReader")
    def test_pdf_without_metadata(self, mock_pdf_reader):
        mock_reader = Mock()
        mock_reader.metadata = None
        mock_pdf_reader.return_value = mock_reader

        with patch("rag.app.pdf_metadata.BytesIO"):
            result = extract_pdf_native_metadata(b"fake pdf content")

        assert result == {}


class TestExtractMetadataByLayout:
    """Tests for layout-based metadata extraction."""

    def test_empty_bytes(self):
        result = extract_metadata_by_layout(b"")
        assert result["title"] is None
        assert result["authors"] is None

    def test_invalid_pdf(self):
        result = extract_metadata_by_layout(b"not a pdf")
        assert result["title"] is None

    @patch("pdfplumber.open")
    def test_basic_extraction(self, mock_pdfplumber_open):
        mock_page = Mock()
        mock_page.width = 600
        mock_page.height = 800
        mock_page.extract_words.return_value = [
            {"text": "Deep", "top": 10, "bottom": 30, "x0": 10, "x1": 50},
            {"text": "Learning", "top": 10, "bottom": 30, "x0": 55, "x1": 120},
            {"text": "Methods", "top": 50, "bottom": 70, "x0": 10, "x1": 80},
        ]
        mock_page.extract_text.return_value = None
        mock_page.extract_tables.return_value = []

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]

        mock_pdfplumber_open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_pdfplumber_open.return_value.__exit__ = Mock(return_value=False)

        result = extract_metadata_by_layout(b"fake pdf")

        assert result["title"] is not None


class TestExtractMetadataWithVlm:
    """Tests for VLM-based metadata extraction."""

    def test_missing_pdf2image(self):
        with patch.dict("sys.modules", {"pdf2image": None}):
            result = extract_metadata_with_vlm(b"fake pdf")
            assert result["title"] is None

    @patch("pdf2image.convert_from_bytes")
    def test_vlm_extraction(self, mock_convert_from_bytes):
        mock_vlm = Mock()
        mock_vlm.chat.return_value = '{"title": "VLM Paper Title", "authors": "Jane Smith", "abstract": "This is an abstract."}'

        mock_img = Mock()
        mock_convert_from_bytes.return_value = [mock_img]

        result = extract_metadata_with_vlm(b"fake pdf", vlm_model=mock_vlm)

        assert result["title"] == "VLM Paper Title"
        assert result["authors"] == "Jane Smith"


class TestExtractPdfMetadata:
    """Integration tests for the main metadata extraction function."""

    def test_returns_required_fields(self):
        result = extract_pdf_metadata(b"")
        assert "title" in result
        assert "authors" in result
        assert "abstract" in result
        assert "source" in result

    @patch("rag.app.pdf_metadata.extract_pdf_native_metadata")
    @patch("rag.app.pdf_metadata.extract_metadata_by_layout")
    def test_native_metadata_priority(self, mock_layout, mock_native):
        mock_native.return_value = {"title": "Native Title", "author": "Native Author"}
        mock_layout.return_value = {"title": "Layout Title", "authors": "Layout Author", "abstract": "Layout Abstract", "confidence": {"title": 0.5, "authors": 0.5, "abstract": 0.5}}

        result = extract_pdf_metadata(b"fake pdf")

        assert result["title"] == "Native Title"
        assert result["authors"] == "Native Author"
        assert result["abstract"] == "Layout Abstract"
        assert result["source"] == "native"

    @patch("rag.app.pdf_metadata.extract_pdf_native_metadata")
    @patch("rag.app.pdf_metadata.extract_metadata_by_layout")
    def test_layout_fallback(self, mock_layout, mock_native):
        mock_native.return_value = {}
        mock_layout.return_value = {
            "title": "Layout Title",
            "authors": "Layout Author",
            "abstract": "Layout Abstract",
            "confidence": {"title": 0.7, "authors": 0.6, "abstract": 0.7},
        }

        result = extract_pdf_metadata(b"fake pdf")

        assert result["title"] == "Layout Title"
        assert result["source"] == "layout"

    @patch("rag.app.pdf_metadata.extract_pdf_native_metadata")
    @patch("rag.app.pdf_metadata.extract_metadata_by_layout")
    @patch("rag.app.pdf_metadata.extract_metadata_with_vlm")
    def test_vlm_fallback(self, mock_vlm, mock_layout, mock_native):
        mock_native.return_value = {}
        mock_layout.return_value = {"title": None, "authors": None, "abstract": None, "confidence": {"title": 0.0, "authors": 0.0, "abstract": 0.0}}
        mock_vlm.return_value = {"title": "VLM Title", "authors": "VLM Author", "abstract": "VLM Abstract"}

        result = extract_pdf_metadata(b"fake pdf", use_vlm=True, vlm_model=Mock())

        assert result["title"] == "VLM Title"
        assert result["source"] == "vlm"

    def test_whitespace_cleanup(self):
        with patch("rag.app.pdf_metadata.extract_pdf_native_metadata") as mock_native:
            mock_native.return_value = {"title": "  Trimmed Title  ", "author": "  Trimmed Author  "}
            with patch("rag.app.pdf_metadata.extract_metadata_by_layout") as mock_layout:
                mock_layout.return_value = {"title": None, "authors": None, "abstract": None, "confidence": {}}

                result = extract_pdf_metadata(b"fake pdf")

                assert result["title"] == "Trimmed Title"
                assert result["authors"] == "Trimmed Author"
