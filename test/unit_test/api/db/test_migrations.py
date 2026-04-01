"""
Tests for database migration functions.
"""

import pytest
from unittest.mock import MagicMock, patch
from peewee import SqliteDatabase, Model, CharField, BooleanField
from playhouse.migrate import SqliteMigrator

from api.db.db_models import (
    alter_db_add_column,
    alter_db_rename_column,
    migrate_add_unique_email,
    update_tenant_llm_to_id_primary_key,
)


class TestMigrations:
    """Test cases for database migration functions."""

    @pytest.fixture
    def in_memory_db(self):
        """Create an in-memory SQLite database for testing."""
        db = SqliteDatabase(":memory:")
        yield db
        db.close()

    @pytest.fixture
    def test_model(self, in_memory_db):
        """Create a test model bound to the in-memory database."""

        class TestUser(Model):
            id = CharField(max_length=32, primary_key=True)
            email = CharField(max_length=255, null=False)
            nickname = CharField(max_length=100, null=False)
            is_superuser = BooleanField(default=False)
            create_time = MagicMock()

            class Meta:
                database = in_memory_db
                db_table = "test_user"

        in_memory_db.create_tables([TestUser])
        return TestUser

    def test_migrate_from_clean_database(self, in_memory_db, test_model):
        """Test that migrations work on a clean database."""
        migrator = SqliteMigrator(in_memory_db)

        from peewee import TextField

        alter_db_add_column(migrator, test_model._meta.db_table, "new_field", TextField(null=True))

        columns = in_memory_db.get_columns(test_model._meta.db_table)
        column_names = [col.name for col in columns]
        assert "new_field" in column_names

    def test_migrate_add_unique_email(self, in_memory_db, test_model):
        """Test migrate_add_unique_email handles duplicates."""
        migrator = SqliteMigrator(in_memory_db)

        test_model.create(id="user1", email="test@example.com", nickname="User 1")
        test_model.create(id="user2", email="test@example.com", nickname="User 2")

        with patch("api.db.db_models.User", test_model):
            with patch("api.db.db_models.DB", in_memory_db):
                with patch("api.db.db_models.settings") as mock_settings:
                    mock_settings.DATABASE_TYPE.upper.return_value = "SQLITE"

                    result = migrate_add_unique_email(migrator)
                    assert result is None

                    emails = [u.email for u in test_model.select()]
                    assert len(set(emails)) == 2

    def test_migrate_idempotency(self, in_memory_db, test_model):
        """Test that migrations are idempotent (can be run multiple times)."""
        migrator = SqliteMigrator(in_memory_db)

        from peewee import TextField

        alter_db_add_column(migrator, test_model._meta.db_table, "idempotent_field", TextField(null=True))
        alter_db_add_column(migrator, test_model._meta.db_table, "idempotent_field", TextField(null=True))

        columns = in_memory_db.get_columns(test_model._meta.db_table)
        column_names = [col.name for col in columns]
        assert "idempotent_field" in column_names

    def test_migration_preserves_data(self, in_memory_db, test_model):
        """Test that migrations preserve existing data."""
        migrator = SqliteMigrator(in_memory_db)

        test_model.create(id="preserve_test", email="preserve@example.com", nickname="Preserve User", is_superuser=True)

        from peewee import TextField

        alter_db_add_column(migrator, test_model._meta.db_table, "preserved_field", TextField(null=True, default="default_value"))

        user = test_model.get(test_model.id == "preserve_test")
        assert user.email == "preserve@example.com"
        assert user.nickname == "Preserve User"
        assert user.is_superuser is True

    def test_alter_db_column_type(self, in_memory_db, test_model):
        """Test column type alteration."""
        migrator = SqliteMigrator(in_memory_db)

        from peewee import IntegerField

        alter_db_add_column(migrator, test_model._meta.db_table, "score", IntegerField(default=0))

        columns = in_memory_db.get_columns(test_model._meta.db_table)
        column_names = [col.name for col in columns]
        assert "score" in column_names

    def test_alter_db_rename_column(self, in_memory_db, test_model):
        """Test column renaming."""
        migrator = SqliteMigrator(in_memory_db)

        from peewee import CharField

        alter_db_add_column(migrator, test_model._meta.db_table, "old_name", CharField(max_length=100, null=True))
        alter_db_rename_column(migrator, test_model._meta.db_table, "old_name", "new_name")

    def test_migrate_add_unique_email_no_duplicates(self, in_memory_db, test_model):
        """Test migrate_add_unique_email when no duplicates exist."""
        migrator = SqliteMigrator(in_memory_db)

        test_model.create(id="unique1", email="unique1@example.com", nickname="Unique 1")
        test_model.create(id="unique2", email="unique2@example.com", nickname="Unique 2")

        with patch("api.db.db_models.User", test_model):
            with patch("api.db.db_models.DB", in_memory_db):
                with patch("api.db.db_models.settings") as mock_settings:
                    mock_settings.DATABASE_TYPE.upper.return_value = "SQLITE"

                    result = migrate_add_unique_email(migrator)
                    assert result is None

                    users = list(test_model.select())
                    emails = [u.email for u in users]
                    assert len(emails) == len(set(emails))

    def test_migrate_add_unique_email_keeps_superuser(self, in_memory_db, test_model):
        """Test that migrate_add_unique_email keeps superuser when deduplicating."""
        migrator = SqliteMigrator(in_memory_db)

        test_model.create(id="super1", email="shared@example.com", nickname="Superuser", is_superuser=True)
        test_model.create(id="regular1", email="shared@example.com", nickname="Regular", is_superuser=False)

        with patch("api.db.db_models.User", test_model):
            with patch("api.db.db_models.DB", in_memory_db):
                with patch("api.db.db_models.settings") as mock_settings:
                    mock_settings.DATABASE_TYPE.upper.return_value = "SQLITE"

                    migrate_add_unique_email(migrator)

                    superuser = test_model.get(test_model.id == "super1")
                    assert superuser.email == "shared@example.com"

                    regular = test_model.get(test_model.id == "regular1")
                    assert "_DUPLICATE_" in regular.email

    def test_update_tenant_llm_to_id_primary_key_mysql(self, in_memory_db):
        """Test update_tenant_llm_to_id_primary_key for MySQL."""

        class MockCursor:
            def __init__(self, rowcount=0):
                self.rowcount = rowcount

        with patch("api.db.db_models.DB") as mock_db:
            mock_db.execute_sql = MagicMock(
                side_effect=[
                    MockCursor(0),
                    MockCursor(1),
                    MockCursor(1),
                    MockCursor(1),
                    MockCursor(1),
                    MockCursor(1),
                    MockCursor(1),
                ]
            )
            mock_db.atomic = MagicMock()

            with patch("api.db.db_models.settings") as mock_settings:
                mock_settings.DATABASE_TYPE.upper.return_value = "MYSQL"

                update_tenant_llm_to_id_primary_key()

                assert mock_db.execute_sql.call_count >= 7

    def test_update_tenant_llm_to_id_primary_key_postgres(self, in_memory_db):
        """Test update_tenant_llm_to_id_primary_key for PostgreSQL."""

        class MockCursor:
            def __init__(self, rowcount=0):
                self.rowcount = rowcount

        with patch("api.db.db_models.DB") as mock_db:
            mock_db.execute_sql = MagicMock(
                side_effect=[
                    MockCursor(0),
                    MockCursor(1),
                    MockCursor(1),
                    MockCursor(1),
                    MockCursor(1),
                    MockCursor(1),
                ]
            )
            mock_db.atomic = MagicMock()

            with patch("api.db.db_models.settings") as mock_settings:
                mock_settings.DATABASE_TYPE.upper.return_value = "POSTGRES"

                update_tenant_llm_to_id_primary_key()

                assert mock_db.execute_sql.call_count >= 6

    def test_update_tenant_llm_to_id_primary_key_already_exists(self, in_memory_db):
        """Test update_tenant_llm_to_id_primary_key when ID column already exists."""

        class MockCursor:
            def __init__(self, rowcount=1):
                self.rowcount = rowcount

        with patch("api.db.db_models.DB") as mock_db:
            mock_db.execute_sql = MagicMock(return_value=MockCursor(1))
            mock_db.atomic = MagicMock()

            with patch("api.db.db_models.settings") as mock_settings:
                mock_settings.DATABASE_TYPE.upper.return_value = "MYSQL"

                update_tenant_llm_to_id_primary_key()

                mock_db.execute_sql.assert_called_once()


class TestMigrateDb:
    """Test cases for the complete migrate_db() function."""

    def test_migrate_db_executes_all_migrations(self):
        """Test that migrate_db() executes all migration operations."""
        from unittest.mock import patch, MagicMock, call

        with patch("api.db.db_models.DatabaseMigrator") as mock_migrator_class:
            mock_migrator = MagicMock()
            mock_migrator_class.value = MagicMock(return_value=mock_migrator)

            with patch("api.db.db_models.alter_db_add_column") as mock_add_column:
                with patch("api.db.db_models.alter_db_column_type") as mock_column_type:
                    with patch("api.db.db_models.alter_db_rename_column") as mock_rename:
                        with patch("api.db.db_models.update_tenant_llm_to_id_primary_key") as mock_update_tenant:
                            with patch("api.db.db_models.migrate_add_unique_email") as mock_unique_email:
                                with patch("api.db.db_models.DB"):
                                    from api.db.db_models import migrate_db

                                    migrate_db()

                                    assert mock_add_column.call_count >= 30, "Should call alter_db_add_column at least 30 times"
                                    assert mock_column_type.call_count >= 5, "Should call alter_db_column_type at least 5 times"
                                    assert mock_rename.call_count >= 2, "Should call alter_db_rename_column at least 2 times"
                                    assert mock_update_tenant.called, "Should call update_tenant_llm_to_id_primary_key"
                                    assert mock_unique_email.called, "Should call migrate_add_unique_email"

    def test_migrate_db_adds_required_columns(self):
        """Test that migrate_db() adds all required columns."""
        from unittest.mock import patch, MagicMock

        added_columns = []

        def capture_add_column(migrator, table, col_name, *args, **kwargs):
            added_columns.append((table, col_name))

        with patch("api.db.db_models.DatabaseMigrator") as mock_migrator_class:
            mock_migrator = MagicMock()
            mock_migrator_class.value = MagicMock(return_value=mock_migrator)

            with patch("api.db.db_models.alter_db_add_column", side_effect=capture_add_column):
                with patch("api.db.db_models.alter_db_column_type"):
                    with patch("api.db.db_models.alter_db_rename_column"):
                        with patch("api.db.db_models.update_tenant_llm_to_id_primary_key"):
                            with patch("api.db.db_models.migrate_add_unique_email"):
                                with patch("api.db.db_models.DB"):
                                    from api.db.db_models import migrate_db

                                    migrate_db()

                                    tables_with_cols = {t for t, c in added_columns}
                                    assert "file" in tables_with_cols, "Should add columns to 'file' table"
                                    assert "tenant" in tables_with_cols, "Should add columns to 'tenant' table"
                                    assert "dialog" in tables_with_cols, "Should add columns to 'dialog' table"

    def test_migrate_db_handles_rename_migrations(self):
        """Test that migrate_db() handles column renames correctly."""
        from unittest.mock import patch, MagicMock

        renames = []

        def capture_rename(migrator, table, old_name, new_name):
            renames.append((table, old_name, new_name))

        with patch("api.db.db_models.DatabaseMigrator") as mock_migrator_class:
            mock_migrator = MagicMock()
            mock_migrator_class.value = MagicMock(return_value=mock_migrator)

            with patch("api.db.db_models.alter_db_add_column"):
                with patch("api.db.db_models.alter_db_column_type"):
                    with patch("api.db.db_models.alter_db_rename_column", side_effect=capture_rename):
                        with patch("api.db.db_models.update_tenant_llm_to_id_primary_key"):
                            with patch("api.db.db_models.migrate_add_unique_email"):
                                with patch("api.db.db_models.DB"):
                                    from api.db.db_models import migrate_db

                                    migrate_db()

                                    rename_pairs = {(t, o, n) for t, o, n in renames}
                                    assert ("task", "process_duation", "process_duration") in rename_pairs, "Should rename process_duation to process_duration in task table"
                                    assert ("document", "process_duation", "process_duration") in rename_pairs, "Should rename process_duation to process_duration in document table"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
