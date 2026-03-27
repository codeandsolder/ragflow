"""
Unit tests for OCR functionality using golden sample images.

Tests cover actual OCR model accuracy using real test images with known text content.
These tests validate the end-to-end OCR pipeline instead of just logic components.
"""

import pytest
from PIL import Image
from deepdoc.vision.ocr import OCR


class TestOCRGoldenSamples:
    """Tests for OCR using golden sample images."""

    @pytest.fixture
    def ocr_instance(self):
        """Create OCR instance for testing."""
        return OCR()

    @pytest.fixture
    def sample_images(self):
        """Load golden sample test images."""
        # These images should be provided in test data directory
        return {
            "basic_text.png": Image.open("test_data/basic_text.png"),
            "multilingual_text.png": Image.open("test_data/multilingual_text.png"),
            "handwritten_text.png": Image.open("test_data/handwritten_text.png"),
            "low_quality_text.png": Image.open("test_data/low_quality_text.png"),
            "rotated_text.png": Image.open("test_data/rotated_text.png"),
        }

    def test_ocr_basic_text_extraction(self, ocr_instance, sample_images):
        """Test OCR on clean, high-quality text."""
        image = sample_images["basic_text.png"]
        expected_text = "This is a test of basic OCR functionality"

        result = ocr_instance.ocr(image)

        assert result["text"] == expected_text
        assert result["confidence"] > 0.95

    def test_ocr_multilingual_text(self, ocr_instance, sample_images):
        """Test OCR on multilingual text."""
        image = sample_images["multilingual_text.png"]
        expected_text = "中文 English 한구컬 العربية"  # Chinese English Korean Arabic

        result = ocr_instance.ocr(image)

        assert result["text"] == expected_text
        assert result["confidence"] > 0.90

    def test_ocr_handwritten_text(self, ocr_instance, sample_images):
        """Test OCR on handwritten text."""
        image = sample_images["handwritten_text.png"]
        expected_text = "Handwritten sample text"

        result = ocr_instance.ocr(image)

        assert result["text"] == expected_text
        assert result["confidence"] > 0.85

    def test_ocr_low_quality_image(self, ocr_instance, sample_images):
        """Test OCR on low-quality or noisy image."""
        image = sample_images["low_quality_text.png"]
        expected_text = "Low quality OCR test"

        result = ocr_instance.ocr(image)

        assert result["text"] == expected_text
        assert result["confidence"] > 0.80

    def test_ocr_rotated_image(self, ocr_instance, sample_images):
        """Test OCR on rotated text."""
        image = sample_images["rotated_text.png"]
        expected_text = "Rotated text OCR test"

        result = ocr_instance.ocr(image)

        assert result["text"] == expected_text
        assert result["confidence"] > 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
