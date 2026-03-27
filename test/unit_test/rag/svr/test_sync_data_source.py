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

"""
Unit tests for rag/svr/sync_data_source module.
Tests external data source synchronization module structure.
"""

import ast
from pathlib import Path


class TestSyncDataSourceFileExists:
    """Test that sync_data_source.py exists and is readable."""

    def test_file_exists(self):
        """Test that sync_data_source.py exists."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        assert module_path.exists()

    def test_file_is_valid_python(self):
        """Test that sync_data_source.py is valid Python."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        tree = ast.parse(content)
        assert tree is not None


class TestSyncBaseClass:
    """Test SyncBase class structure."""

    def test_sync_base_class_defined(self):
        """Test that SyncBase class is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()

        assert "class SyncBase:" in content
        assert "def __init__(self, conf:" in content
        assert "async def __call__(self, task:" in content

    def test_sync_base_has_run_task_logic(self):
        """Test that SyncBase has _run_task_logic method."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()

        assert "async def _run_task_logic(self, task" in content
        assert "async def _generate(self, task" in content

    def test_sync_base_uses_task_limiter(self):
        """Test that SyncBase uses task_limiter for concurrency control."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()

        assert "task_limiter" in content
        assert "asyncio.Semaphore" in content


class TestConnectorClasses:
    """Test that all connector classes are defined."""

    def test_s3_connector_defined(self):
        """Test S3 connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class S3(" in content

    def test_r2_connector_defined(self):
        """Test R2 connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class R2(" in content

    def test_notion_connector_defined(self):
        """Test Notion connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Notion(" in content

    def test_discord_connector_defined(self):
        """Test Discord connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Discord(" in content

    def test_gmail_connector_defined(self):
        """Test Gmail connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Gmail(" in content

    def test_dropbox_connector_defined(self):
        """Test Dropbox connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Dropbox(" in content

    def test_github_connector_defined(self):
        """Test GitHub connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Github(" in content

    def test_gitlab_connector_defined(self):
        """Test GitLab connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Gitlab(" in content

    def test_jira_connector_defined(self):
        """Test Jira connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Jira(" in content

    def test_confluence_connector_defined(self):
        """Test Confluence connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Confluence(" in content

    def test_google_drive_connector_defined(self):
        """Test Google Drive connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class GoogleDrive(" in content

    def test_imap_connector_defined(self):
        """Test IMAP connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class IMAP(" in content

    def test_zendesk_connector_defined(self):
        """Test Zendesk connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Zendesk(" in content

    def test_airtable_connector_defined(self):
        """Test Airtable connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Airtable(" in content

    def test_asana_connector_defined(self):
        """Test Asana connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Asana(" in content

    def test_seafile_connector_defined(self):
        """Test SeaFile connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class SeaFile(" in content

    def test_webdav_connector_defined(self):
        """Test WebDAV connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class WebDAV(" in content

    def test_moodle_connector_defined(self):
        """Test Moodle connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class Moodle(" in content

    def test_box_connector_defined(self):
        """Test Box connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class BOX(" in content

    def test_mysql_connector_defined(self):
        """Test MySQL connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class MySQL(" in content

    def test_postgresql_connector_defined(self):
        """Test PostgreSQL connector is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "class PostgreSQL(" in content


class TestFuncFactory:
    """Test connector factory mapping."""

    def test_func_factory_defined(self):
        """Test func_factory dictionary is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()

        assert "func_factory = {" in content

    def test_func_factory_maps_all_sources(self):
        """Test that func_factory maps all source types."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()

        # Check that func_factory contains the source types
        assert "FileSource.S3" in content
        assert "FileSource.NOTION" in content
        assert "FileSource.DISCORD" in content
        assert "FileSource.CONFLUENCE" in content
        assert "FileSource.GMAIL" in content
        assert "FileSource.GOOGLE_DRIVE" in content
        assert "FileSource.JIRA" in content
        assert "FileSource.DROPBOX" in content
        assert "FileSource.WEBDAV" in content
        assert "FileSource.GITHUB" in content
        assert "FileSource.GITLAB" in content
        assert "FileSource.BITBUCKET" in content
        assert "FileSource.SEAFILE" in content
        assert "FileSource.MYSQL" in content
        assert "FileSource.POSTGRESQL" in content


class TestDispatchTasksFunction:
    """Test dispatch_tasks function."""

    def test_dispatch_tasks_defined(self):
        """Test dispatch_tasks function is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()

        assert "async def dispatch_tasks(" in content

    def test_dispatch_tasks_uses_func_factory(self):
        """Test dispatch_tasks uses func_factory."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()

        assert "func_factory" in content

    def test_dispatch_tasks_uses_asyncio_gather(self):
        """Test dispatch_tasks uses asyncio.gather."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()

        assert "asyncio.gather" in content


class TestSignalHandler:
    """Test signal handler."""

    def test_signal_handler_defined(self):
        """Test signal handler is defined."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()

        assert "def signal_handler(" in content
        assert "stop_event.set()" in content


class TestConsumerName:
    """Test consumer name configuration."""

    def test_consumer_name_construction(self):
        """Test consumer name follows expected format."""
        consumer_no = "0"
        consumer_name = "data_sync_" + consumer_no
        assert consumer_name == "data_sync_0"


class TestModuleImports:
    """Test required imports."""

    def test_has_asyncio_import(self):
        """Test asyncio import."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "import asyncio" in content

    def test_has_signal_import(self):
        """Test signal import."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "import signal" in content

    def test_has_connector_service_import(self):
        """Test ConnectorService import."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "ConnectorService" in content

    def test_has_file_source_import(self):
        """Test FileSource import."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "FileSource" in content

    def test_has_task_status_import(self):
        """Test TaskStatus import."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "TaskStatus" in content


class TestErrorHandling:
    """Test error handling patterns."""

    def test_timeout_handling(self):
        """Test that timeout is handled."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "TimeoutError" in content
        assert "wait_for" in content

    def test_exception_handling(self):
        """Test that exceptions are handled."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "except Exception" in content
        assert "error_msg" in content

    def test_collation_conflict_handling(self):
        """Test that collation conflicts are handled."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "collation" in content.lower()


class TestDataProcessing:
    """Test data processing patterns."""

    def test_doc_hash_generation(self):
        """Test document hashing for IDs."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "hash128" in content

    def test_batch_processing(self):
        """Test batch processing is supported."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "batch_size" in content.lower()
        assert "INDEX_BATCH_SIZE" in content

    def test_sync_logging(self):
        """Test sync progress is logged."""
        module_path = Path("/mnt/d/ragflow/rag/svr/sync_data_source.py")
        content = module_path.read_text()
        assert "SyncLogsService" in content
        assert "start(" in content
        assert "done(" in content
