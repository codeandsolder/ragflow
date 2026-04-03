"""
Unit tests for OCR functionality using golden sample images.

Tests cover actual OCR model accuracy using real test images with known text content.
These tests validate the end-to-end OCR pipeline instead of just logic components.

Setup:
    Create test/unit_test/deepdoc/test_data/ directory with the following images:
    - basic_text.png: Clean, high-quality text image
    - multilingual_text.png: Image with mixed language text
    - handwritten_text.png: Handwritten text sample
    - low_quality_text.png: Noisy or low-resolution text image
    - rotated_text.png: Rotated text sample
"""

from pathlib import Path

import pytest
from PIL import Image

try:
    from deepdoc.vision import OCR
except ImportError:
    OCR = None


def _get_test_data_dir():
    """Get the test data directory path."""
    return Path(__file__).parent / "test_data"


@pytest.mark.filterwarnings("ignore:.*local_dir_use_symlinks.*:UserWarning")
@pytest.mark.filterwarnings("ignore:.*deprecated.*:DeprecationWarning")
class TestOCRGoldenSamples:
    """Tests for OCR using golden sample images."""

    @pytest.fixture
    def ocr_instance(self):
        """Create OCR instance for testing."""
        return OCR()

    @pytest.fixture
    def sample_images(self):
        """Load golden sample test images.

        Skips tests if test_data directory is not available.
        """
        test_data_dir = _get_test_data_dir()
        if not test_data_dir.exists():
            pytest.skip(f"Test data directory not found: {test_data_dir}")

        images = {}
        for filename in ["basic_text.png", "multilingual_text.png", "handwritten_text.png", "low_quality_text.png", "rotated_text.png"]:
            filepath = test_data_dir / filename
            if not filepath.exists():
                pytest.skip(f"Test image not found: {filepath}")
            images[filename] = Image.open(filepath)
        return images

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
        expected_text = "Chinese English Korean Arabic"

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
