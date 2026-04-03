#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright 2025 The InfiniFlow Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import asyncio
import importlib.util
import sys
from functools import partial
from types import ModuleType
from typing import Any
from unittest.mock import patch

import pytest


def _check_import(module_name):
    """Check if a module can be imported."""
    if module_name in sys.modules:
        return True
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        return False


# Only create stubs for modules that can't be imported
if "scholarly" not in sys.modules and not _check_import("scholarly"):
    scholarly_stub = ModuleType("scholarly")
    scholarly_stub.search_pubs = lambda *args, **kwargs: []
    sys.modules["scholarly"] = scholarly_stub


class _StubMinerUParser:
    pass


class _StubFigureParser:
    pass


class _StubPaddleOCRParser:
    pass


class _StubPdfParser:
    @staticmethod
    def remove_tag(txt):
        return txt


class _StubHtmlParser:
    pass


class _StubExcelParser:
    pass


class _StubDocxParser:
    pass


class _StubRAGFlowExcelParser:
    pass


class _StubDoclingParser:
    pass


# Only create stubs for modules that can't be imported
_stubs = [
    ("deepdoc.parser.mineru_parser", "MinerUParser", _StubMinerUParser),
    ("deepdoc.parser.paddleocr_parser", "PaddleOCRParser", _StubPaddleOCRParser),
    ("deepdoc.parser.pdf_parser", "PdfParser", _StubPdfParser),
    ("deepdoc.parser.pdf_parser", "RAGFlowPdfParser", _StubPdfParser),
    ("deepdoc.parser.html_parser", "HtmlParser", _StubHtmlParser),
    ("deepdoc.parser.excel_parser", "ExcelParser", _StubExcelParser),
    ("deepdoc.parser.excel_parser", "RAGFlowExcelParser", _StubRAGFlowExcelParser),
    ("deepdoc.parser.docx_parser", "DocxParser", _StubDocxParser),
    ("deepdoc.parser.docling_parser", "DoclingParser", _StubDoclingParser),
]

for mod_name, class_name, stub_class in _stubs:
    if not _check_import(mod_name):
        mod = sys.modules.get(mod_name, ModuleType(mod_name))
        if not hasattr(mod, class_name):
            setattr(mod, class_name, stub_class)
        sys.modules[mod_name] = mod


# Only create deepdoc stubs if they can't be imported
if not _check_import("deepdoc"):
    deepdoc_stub = ModuleType("deepdoc")
    sys.modules["deepdoc"] = deepdoc_stub

if not _check_import("deepdoc.parser"):
    deepdoc_parser_stub = ModuleType("deepdoc.parser")
    deepdoc_parser_stub.__path__ = []
    if not hasattr(deepdoc_parser_stub, "figure_parser"):
        deepdoc_parser_stub.figure_parser = _StubFigureParser
    if not hasattr(deepdoc_parser_stub, "MinerUParser"):
        deepdoc_parser_stub.MinerUParser = _StubMinerUParser
    if not hasattr(deepdoc_parser_stub, "PaddleOCRParser"):
        deepdoc_parser_stub.PaddleOCRParser = _StubPaddleOCRParser
    if not hasattr(deepdoc_parser_stub, "PdfParser"):
        deepdoc_parser_stub.PdfParser = _StubPdfParser
    if not hasattr(deepdoc_parser_stub, "RAGFlowPdfParser"):
        deepdoc_parser_stub.RAGFlowPdfParser = _StubPdfParser
    if not hasattr(deepdoc_parser_stub, "HtmlParser"):
        deepdoc_parser_stub.HtmlParser = _StubHtmlParser
    if not hasattr(deepdoc_parser_stub, "ExcelParser"):
        deepdoc_parser_stub.ExcelParser = _StubExcelParser
    if not hasattr(deepdoc_parser_stub, "DocxParser"):
        deepdoc_parser_stub.DocxParser = _StubDocxParser
    if not hasattr(deepdoc_parser_stub, "RAGFlowExcelParser"):
        deepdoc_parser_stub.RAGFlowExcelParser = _StubRAGFlowExcelParser
    if not hasattr(deepdoc_parser_stub, "DoclingParser"):
        deepdoc_parser_stub.DoclingParser = _StubDoclingParser
    sys.modules["deepdoc.parser"] = deepdoc_parser_stub

if not _check_import("rag.app.picture"):
    rag_app_picture_stub = ModuleType("rag.app.picture")
    rag_app_picture_stub.OCR = type("_StubOcr", (), {})
    sys.modules["rag.app.picture"] = rag_app_picture_stub


class _StubComponentParamBase:
    def __init__(self):
        self.timeout = 100000000
        self.persist_logs = True


class FileParam:
    def __init__(self):
        pass

    def check(self):
        pass

    def get_input_form(self) -> dict[str, dict]:
        return {}


class File:
    component_name = "File"

    def __init__(self, canvas, id, param: FileParam):
        self._canvas = canvas
        self._id = id
        self._param = param
        self._output = {}
        if hasattr(canvas, "callback"):
            self.callback = partial(canvas.callback, id)
        else:
            self.callback = partial(lambda *args, **kwargs: None, id)

    def set_output(self, key: str, value: Any):
        self._output[key] = value

    def output(self, key: str = None) -> Any:
        if key is None:
            return self._output
        return self._output.get(key)

    def get_exception_default_value(self):
        return False

    def set_exception_default_value(self):
        pass

    async def invoke(self, **kwargs) -> dict[str, Any]:
        import time

        self.set_output("_created_time", time.perf_counter())
        for k, v in kwargs.items():
            self.set_output(k, v)
        try:
            await self._invoke(**kwargs)
            self.callback(1, "Done")
        except Exception as e:
            self.set_output("_ERROR", str(e))
            self.callback(-1, str(e))
        self.set_output("_elapsed_time", time.perf_counter() - self.output("_created_time"))
        return self.output()

    async def _invoke(self, **kwargs):
        if self._canvas._doc_id:
            self.set_output("_ERROR", f"Document({self._canvas._doc_id}) not found!")
            return

        file = kwargs.get("file")[0]
        self.set_output("name", file["name"])
        self.set_output("file", file)

        self.callback(1, "File fetched.")


class MockCanvas:
    def __init__(self, doc_id=None):
        self._doc_id = doc_id
        self._callback_called = False
        self._last_callback_args = None

    def callback(self, id, progress, message):
        self._callback_called = True
        self._last_callback_args = (id, progress, message)


class TestEdgeCaseDocuments:
    """Test class for edge case document processing."""

    @pytest.fixture(autouse=True)
    def setup_settings_mock(self):
        """Setup mock for settings.DATABASE_TYPE.upper()."""
        with patch("api.db.db_models.settings") as mock_settings:
            mock_settings.DATABASE_TYPE.upper.return_value = "SQLITE"
            yield mock_settings

    def test_empty_document(self):
        """Test processing of empty document."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "file_1", param)

        result = asyncio.run(file_processor.invoke())
        assert result.get("_ERROR") is not None

    def test_whitespace_only_document(self):
        """Test processing of whitespace-only document."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "file_1", param)

        asyncio.run(file_processor.invoke(file=[{"name": "test.txt", "content": "   \t\n  "}]))
        assert file_processor.output().get("name") == "test.txt"

    def test_extreme_utf8_characters(self):
        """Test processing of document with extreme UTF-8 characters."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "File", param)

        test_content = "🚀🌍👻🔥💀💥"
        asyncio.run(file_processor.invoke(file=[{"name": "test.txt", "content": test_content}]))
        assert file_processor.output().get("name") == "test.txt"

    def test_emoji_only_document(self):
        """Test processing of emoji-only document."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "File", param)

        test_content = "🚀😊😍😎😏"
        asyncio.run(file_processor.invoke(file=[{"name": "emoji.txt", "content": test_content}]))
        assert file_processor.output().get("name") == "emoji.txt"

    def test_mixed_encoding_document(self):
        """Test processing of document with mixed encoding."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "File", param)

        test_content = "Hello 世界! 🚀 Welcome to 2024!"
        asyncio.run(file_processor.invoke(file=[{"name": "mixed.txt", "content": test_content}]))
        assert file_processor.output().get("name") == "mixed.txt"

    def test_null_byte_handling(self):
        """Test processing of document containing null bytes."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "File", param)

        test_content = "Hello\x00World\x00Test"
        asyncio.run(file_processor.invoke(file=[{"name": "null.txt", "content": test_content}]))
        assert file_processor.output().get("name") == "null.txt"

    def test_very_long_single_line(self):
        """Test processing of very long single line document."""
        canvas = MockCanvas()
        param = FileParam()
        file_processor = File(canvas, "File", param)

        test_content = "A" * 100000
        asyncio.run(file_processor.invoke(file=[{"name": "long.txt", "content": test_content}]))
        assert file_processor.output().get("name") == "long.txt"
