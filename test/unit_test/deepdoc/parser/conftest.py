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

import os
import tempfile

import pytest


@pytest.fixture
def temp_xlsx(tmp_path):
    """Fixture that writes bytes to a temp xlsx file and returns the path.

    Caller is responsible for cleanup via pytest's tmp_path mechanism,
    or use this fixture's returned path with explicit cleanup.

    Usage:
        path = temp_xlsx(suffix=".xlsx")
        # write bytes to path manually, or use in conjunction with
        # the _create_* helper functions from test files.
    """
    paths = []

    def _create(suffix=".xlsx", content=None):
        fd, path = tempfile.mkstemp(suffix=suffix, dir=tmp_path)
        if content:
            os.write(fd, content)
        os.close(fd)
        paths.append(path)
        return path

    yield _create

    for p in paths:
        if os.path.exists(p):
            os.unlink(p)


@pytest.fixture
def temp_docx(tmp_path):
    """Fixture that creates a temp docx file path and returns it."""
    paths = []

    def _create(suffix=".docx", content=None):
        fd, path = tempfile.mkstemp(suffix=suffix, dir=tmp_path)
        if content:
            os.write(fd, content)
        os.close(fd)
        paths.append(path)
        return path

    yield _create

    for p in paths:
        if os.path.exists(p):
            os.unlink(p)


@pytest.fixture
def temp_pptx(tmp_path):
    """Fixture that creates a temp pptx file path and returns it."""
    paths = []

    def _create(suffix=".pptx", content=None):
        fd, path = tempfile.mkstemp(suffix=suffix, dir=tmp_path)
        if content:
            os.write(fd, content)
        os.close(fd)
        paths.append(path)
        return path

    yield _create

    for p in paths:
        if os.path.exists(p):
            os.unlink(p)
