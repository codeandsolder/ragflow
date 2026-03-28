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

import pytest


def _check_import(module_name: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True
    except (ImportError, SyntaxError):
        return False


def _patch_sqlglot_compatibility():
    """Patch sqlglot to support older code importing Expression from it."""
    try:
        import sqlglot
        from sqlglot import exp

        if not hasattr(sqlglot, "Expression"):
            sqlglot.Expression = exp.Expression
    except Exception:
        pass


_patch_sqlglot_compatibility()

skipif_no_s3 = pytest.mark.skipif(not _check_import("s3fs"), reason="s3fs not installed")

skipif_no_oss = pytest.mark.skipif(not _check_import("oss2"), reason="oss2 not installed")

skipif_no_azure = pytest.mark.skipif(not _check_import("azure.storage.blob"), reason="azure.storage.blob not installed")

skipif_no_gcs = pytest.mark.skipif(not _check_import("gcloud.storage"), reason="gcloud.storage not installed")

skipif_no_minio = pytest.mark.skipif(not _check_import("minio"), reason="minio not installed")

skipif_no_redis = pytest.mark.skipif(not _check_import("redis"), reason="redis not installed")
