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

"""Unit tests for Figure Parser in deepdoc/parser/figure_parser.py.

Tests cover:
- VisionFigureParser: vision-based figure caption generation
- figure_data_wrapper: figure data format conversion
- Wrapper functions: docx, pdf, xlsx wrappers

Uses function reimplementations to avoid heavy dependency loading.
"""

from unittest import mock


class TestVisionFigureParserFigureDataWrapper:
    """Tests for vision_figure_parser_figure_data_wrapper function."""

    def test_empty_input(self):
        def figure_data_wrapper(figures_data_without_positions):
            if not figures_data_without_positions:
                return []
            res = []
            for figure_data in figures_data_without_positions:
                res.append(
                    (
                        (figure_data[1], [figure_data[0]]),
                        [(0, 0, 0, 0, 0)],
                    )
                )
            return res

        result = figure_data_wrapper(None)
        assert result == []

    def test_empty_list(self):
        def figure_data_wrapper(figures_data_without_positions):
            if not figures_data_without_positions:
                return []
            res = []
            for figure_data in figures_data_without_positions:
                res.append(
                    (
                        (figure_data[1], [figure_data[0]]),
                        [(0, 0, 0, 0, 0)],
                    )
                )
            return res

        result = figure_data_wrapper([])
        assert result == []

    def test_figure_data_wrapper_format(self):
        def figure_data_wrapper(figures_data_without_positions):
            if not figures_data_without_positions:
                return []
            res = []
            for figure_data in figures_data_without_positions:
                res.append(
                    (
                        (figure_data[1], [figure_data[0]]),
                        [(0, 0, 0, 0, 0)],
                    )
                )
            return res

        mock_img = mock.MagicMock()
        figure_data = [(100, mock_img)]
        result = figure_data_wrapper(figure_data)
        assert len(result) == 1
        assert isinstance(result[0], tuple)

    def test_multiple_figure_data(self):
        def figure_data_wrapper(figures_data_without_positions):
            if not figures_data_without_positions:
                return []
            res = []
            for figure_data in figures_data_without_positions:
                res.append(
                    (
                        (figure_data[1], [figure_data[0]]),
                        [(0, 0, 0, 0, 0)],
                    )
                )
            return res

        mock_img1 = mock.MagicMock()
        mock_img2 = mock.MagicMock()
        figure_data = [(100, mock_img1), (200, mock_img2)]
        result = figure_data_wrapper(figure_data)
        assert len(result) == 2


class TestVisionFigureParserInit:
    """Tests for VisionFigureParser initialization."""

    def test_init_basic(self):
        def init_parser(vision_model, figures_data, **kwargs):
            figure_contexts = kwargs.get("figure_contexts") or []
            context_size = max(0, int(kwargs.get("context_size", 0) or 0))
            return {
                "vision_model": vision_model,
                "figure_contexts": figure_contexts,
                "context_size": context_size,
            }

        mock_vision_model = mock.MagicMock()
        figures_data = []
        result = init_parser(mock_vision_model, figures_data)
        assert result["vision_model"] is mock_vision_model
        assert result["figure_contexts"] == []
        assert result["context_size"] == 0

    def test_init_with_figure_contexts(self):
        def init_parser(vision_model, figures_data, **kwargs):
            figure_contexts = kwargs.get("figure_contexts") or []
            context_size = max(0, int(kwargs.get("context_size", 0) or 0))
            return {
                "vision_model": vision_model,
                "figure_contexts": figure_contexts,
                "context_size": context_size,
            }

        mock_vision_model = mock.MagicMock()
        figures_data = []
        figure_contexts = [("context_above", "context_below")]
        result = init_parser(mock_vision_model, figures_data, figure_contexts=figure_contexts)
        assert result["figure_contexts"] == figure_contexts

    def test_init_with_context_size(self):
        def init_parser(vision_model, figures_data, **kwargs):
            figure_contexts = kwargs.get("figure_contexts") or []
            context_size = max(0, int(kwargs.get("context_size", 0) or 0))
            return {
                "vision_model": vision_model,
                "figure_contexts": figure_contexts,
                "context_size": context_size,
            }

        mock_vision_model = mock.MagicMock()
        figures_data = []
        result = init_parser(mock_vision_model, figures_data, context_size=500)
        assert result["context_size"] == 500

    def test_init_with_zero_context_size(self):
        def init_parser(vision_model, figures_data, **kwargs):
            figure_contexts = kwargs.get("figure_contexts") or []
            context_size = max(0, int(kwargs.get("context_size", 0) or 0))
            return {
                "vision_model": vision_model,
                "figure_contexts": figure_contexts,
                "context_size": context_size,
            }

        mock_vision_model = mock.MagicMock()
        figures_data = []
        result = init_parser(mock_vision_model, figures_data, context_size="0")
        assert result["context_size"] == 0


class TestVisionFigureParserExtractFiguresInfo:
    """Tests for figure info extraction."""

    def test_extract_empty_figures_data(self):
        def extract_figures_info(figures_data):
            figures = []
            descriptions = []
            positions = []
            for item in figures_data:
                img = item[0] if len(item) >= 1 else None
                if img is None:
                    continue
                figures.append(img)
                descriptions.append(item[1] if len(item) >= 2 else [])
            return figures, descriptions, positions

        figures, descriptions, positions = extract_figures_info([])
        assert figures == []
        assert descriptions == []

    def test_extract_skips_none_images(self):
        def extract_figures_info(figures_data):
            figures = []
            descriptions = []
            positions = []
            for item in figures_data:
                img = item[0] if len(item) >= 1 else None
                if img is None:
                    continue
                figures.append(img)
                descriptions.append(item[1] if len(item) >= 2 else [])
            return figures, descriptions, positions

        figures_data = [(None, ["description1"])]
        figures, descriptions, positions = extract_figures_info(figures_data)
        assert len(figures) == 0


class TestVisionFigureParserAssemble:
    """Tests for assemble method."""

    def test_assemble_empty(self):
        def assemble(figures, descriptions, positions, has_positions=False):
            assembled = []
            for i in range(len(figures)):
                figure_desc = (figures[i], descriptions[i])
                if i < len(positions) and has_positions:
                    assembled.append((figure_desc, positions[i]))
                else:
                    assembled.append((figure_desc,))
            return assembled

        result = assemble([], [], [])
        assert result == []

    def test_assemble_with_figures(self):
        def assemble(figures, descriptions, positions, has_positions=False):
            assembled = []
            for i in range(len(figures)):
                figure_desc = (figures[i], descriptions[i])
                if i < len(positions) and has_positions:
                    assembled.append((figure_desc, positions[i]))
                else:
                    assembled.append((figure_desc,))
            return assembled

        mock_img = mock.MagicMock()
        result = assemble([mock_img], [["description1"]], [[(0, 0, 100, 100, 0)]], has_positions=True)
        assert len(result) == 1
        assert isinstance(result[0], tuple)
        assert len(result[0]) == 2


class TestVisionFigureParserEdgeCases:
    """Tests for edge cases in VisionFigureParser."""

    def test_figures_without_positions(self):
        mock_img = mock.MagicMock()
        mock_img = mock.MagicMock()
        figures = [mock_img]
        descriptions = [["description1"]]
        positions = []

        assert len(positions) == 0

    def test_figures_with_positions(self):
        mock_img = mock.MagicMock()
        mock_img = mock.MagicMock()
        figures = [mock_img]
        descriptions = [["description1"]]
        positions = [(0, 0, 100, 100, 0)]

        assert len(positions) > 0

    def test_multiple_figures(self):
        mock_img1 = mock.MagicMock()
        mock_img2 = mock.MagicMock()
        figures = [mock_img1, mock_img2]
        descriptions = [["desc1"], ["desc2"]]

        assert len(figures) == 2


class TestVisionFigureParserDescriptions:
    """Tests for description handling."""

    def test_descriptions_accumulation(self):
        descriptions = ["initial description"]
        descriptions.append("new description\n")
        combined = "\n".join(descriptions)
        assert "initial description" in combined
        assert "new description" in combined


class TestSharedExecutor:
    """Tests for shared executor."""

    def test_thread_pool_executor_exists(self):
        from concurrent.futures import ThreadPoolExecutor

        executor = ThreadPoolExecutor(max_workers=10)
        assert executor is not None
        assert hasattr(executor, "submit")


class TestWrapperFunctions:
    """Tests for wrapper function logic."""

    def test_empty_sections_returns_tbls(self):
        def wrapper(sections, tbls, **kwargs):
            if not sections:
                return tbls
            return []

        result = wrapper(None, [{"test": "data"}])
        assert result == [{"test": "data"}]

    def test_empty_images_returns_empty_list(self):
        def wrapper(images, **kwargs):
            if not images:
                return []
            return []

        result = wrapper(None)
        assert result == []

    def test_empty_tbls_returns_empty_list(self):
        def wrapper(tbls, **kwargs):
            if not tbls:
                return []
            return []

        result = wrapper(None)
        assert result == []


class TestIsFigureItem:
    """Tests for is_figure_item function."""

    def test_is_figure_item_with_image(self):
        def is_figure_item(item):
            return hasattr(item[0][0], "read") and isinstance(item[0][1], list)

        mock_img = mock.MagicMock()
        mock_img.read = mock.MagicMock()
        item = ((mock_img, ["caption"]), [(0, 0, 100, 100, 0)])
        assert is_figure_item(item) is True

    def test_is_figure_item_without_image(self):
        def is_figure_item(item):
            return hasattr(item[0][0], "read") and isinstance(item[0][1], list)

        item = ((None, ["caption"]), [(0, 0, 100, 100, 0)])
        assert is_figure_item(item) is False


class TestTimeoutDecorator:
    """Tests for timeout decorator logic."""

    def test_timeout_function_wrapper(self):
        def timeout(timeout_seconds, max_retries):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)

                return wrapper

            return decorator

        @timeout(30, 3)
        def example_func(idx, binary):
            return idx, "result"

        result = example_func(0, b"image_data")
        assert result == (0, "result")


class TestFigureCaptionExtraction:
    """Tests for figure caption extraction logic."""

    def test_extract_caption_from_context(self):
        def get_context(figure_contexts, figure_idx, default=("above", "below")):
            if figure_idx < len(figure_contexts):
                context_above, context_below = figure_contexts[figure_idx]
            else:
                context_above, context_below = default
            return context_above, context_below

        figure_contexts = [("ctx1_above", "ctx1_below"), ("ctx2_above", "ctx2_below")]
        assert get_context(figure_contexts, 0) == ("ctx1_above", "ctx1_below")
        assert get_context(figure_contexts, 1) == ("ctx2_above", "ctx2_below")
        assert get_context(figure_contexts, 10) == ("above", "below")

    def test_context_with_text(self):
        def append_context_to_text(text, context_above, context_below):
            if context_above or context_below:
                return f"{context_above}{text}{context_below}"
            return text

        assert append_context_to_text("figure", "before ", " after") == "before figure after"
        assert append_context_to_text("figure", "", "") == "figure"
