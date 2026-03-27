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
import pytest
from common.sql_validation import (
    validate_text_to_sql,
    SQLValidationError,
    validate_sql_syntax,
    check_statement_type,
    check_for_dangerous_patterns,
    validate_table_and_column_names,
    extract_table_names,
    extract_column_names,
)


class TestSQLValidation:
    """Tests for SQL injection vulnerability fixes."""

    # === Tests for allowed SQL (should pass) ===

    def test_simple_select(self):
        sql = "SELECT * FROM users WHERE id = 1"
        result = validate_text_to_sql(sql, {"users"}, {"id", "name", "email"})
        assert result is not None

    def test_select_with_columns(self):
        sql = "SELECT id, name, email FROM users"
        result = validate_text_to_sql(sql, {"users"}, {"id", "name", "email"})
        assert result is not None

    def test_select_with_where_clause(self):
        sql = "SELECT * FROM users WHERE name = 'test' AND status = 'active'"
        result = validate_text_to_sql(sql, {"users"}, {"id", "name", "status"})
        assert result is not None

    def test_select_with_join(self):
        sql = "SELECT u.id, o.order_id FROM users u JOIN orders o ON u.id = o.user_id"
        result = validate_text_to_sql(sql, {"users", "orders"}, {"id", "name", "order_id", "user_id"})
        assert result is not None

    def test_select_with_aggregate(self):
        sql = "SELECT COUNT(*) as total, AVG(price) as avg_price FROM products"
        result = validate_text_to_sql(sql, {"products"}, {"id", "price", "total", "avg_price"})
        assert result is not None

    def test_union_select(self):
        sql = "SELECT id FROM users UNION SELECT id FROM admins"
        result = validate_text_to_sql(sql, {"users", "admins"}, {"id"})
        assert result is not None

    def test_subquery(self):
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        result = validate_text_to_sql(sql, {"users", "orders"}, {"id", "user_id"})
        assert result is not None

    def test_case_expression(self):
        sql = "SELECT CASE WHEN status = 'active' THEN 'Active' ELSE 'Inactive' END FROM users"
        result = validate_text_to_sql(sql, {"users"}, {"status"})
        assert result is not None

    # === Tests for SQL injection attempts (should be blocked) ===

    def test_injection_drop_table(self):
        # Multiple statements are blocked first
        sql = "SELECT * FROM users; DROP TABLE users;--"
        with pytest.raises(SQLValidationError):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_injection_delete(self):
        # Multiple statements are blocked first
        sql = "SELECT * FROM users WHERE id = 1; DELETE FROM users WHERE 1=1"
        with pytest.raises(SQLValidationError):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_injection_update(self):
        # Multiple statements are blocked first
        sql = "SELECT * FROM users; UPDATE users SET name='hacked' WHERE 1=1"
        with pytest.raises(SQLValidationError):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_injection_insert(self):
        # Multiple statements are blocked first
        sql = "SELECT * FROM users; INSERT INTO users (name) VALUES ('hacker')"
        with pytest.raises(SQLValidationError):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_injection_alter(self):
        # Multiple statements are blocked first
        sql = "SELECT * FROM users; ALTER TABLE users ADD COLUMN hacked VARCHAR(255)"
        with pytest.raises(SQLValidationError):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_injection_create(self):
        # Multiple statements are blocked first
        sql = "SELECT * FROM users; CREATE TABLE hackers (id INT)"
        with pytest.raises(SQLValidationError):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_injection_truncate(self):
        # Multiple statements are blocked first
        sql = "SELECT * FROM users; TRUNCATE TABLE users"
        with pytest.raises(SQLValidationError):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_injection_exec(self):
        # Multiple statements are blocked first
        sql = "SELECT * FROM users; EXEC sp_executesql 'DROP TABLE users'"
        with pytest.raises(SQLValidationError):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_single_statement_drop_detected(self):
        # Single DROP statement should be detected by pattern check
        sql = "DROP TABLE users"
        with pytest.raises(SQLValidationError, match="forbidden operation"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_single_statement_delete_detected(self):
        # Single DELETE statement should be detected by pattern check
        sql = "DELETE FROM users WHERE id = 1"
        with pytest.raises(SQLValidationError, match="forbidden operation"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_single_statement_update_detected(self):
        # Single UPDATE statement should be detected by pattern check
        sql = "UPDATE users SET name='hacked' WHERE 1=1"
        with pytest.raises(SQLValidationError, match="forbidden operation"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_single_statement_insert_detected(self):
        # Single INSERT statement should be detected by pattern check
        sql = "INSERT INTO users (name) VALUES ('hacker')"
        with pytest.raises(SQLValidationError, match="forbidden operation"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_single_statement_alter_detected(self):
        # Single ALTER statement should be detected by pattern check
        sql = "ALTER TABLE users ADD COLUMN hacked VARCHAR(255)"
        with pytest.raises(SQLValidationError, match="forbidden operation"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_single_statement_create_detected(self):
        # Single CREATE statement should be detected by pattern check
        sql = "CREATE TABLE hackers (id INT)"
        with pytest.raises(SQLValidationError, match="forbidden operation"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_injection_union_injection(self):
        sql = "SELECT id, name FROM users UNION SELECT password, '1' FROM admins"
        with pytest.raises(SQLValidationError, match="not in the allowed list"):
            validate_text_to_sql(sql, {"users", "admins"}, {"id", "name"})

    def test_injection_comment_in_where(self):
        # Comments are blocked
        sql = "SELECT * FROM users WHERE id = 1 OR 1=1--"
        with pytest.raises(SQLValidationError):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_injection_benchmark(self):
        sql = "SELECT * FROM users WHERE id = 1 AND BENCHMARK(1000000, SLEEP(1))"
        with pytest.raises(SQLValidationError, match="forbidden operation"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_injection_into_outfile(self):
        sql = "SELECT * INTO OUTFILE '/tmp/hacked' FROM users"
        with pytest.raises(SQLValidationError, match="forbidden operation"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_sp_prefix_attack(self):
        sql = "SELECT * FROM users; sp_executesql 'DROP TABLE users'"
        with pytest.raises(SQLValidationError):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_sp_prefix_single_statement(self):
        sql = "SELECT sp_executesql('DROP TABLE users') FROM users"
        with pytest.raises(SQLValidationError, match="forbidden operation"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_xp_cmdshell_style(self):
        sql = "SELECT * FROM users; xp_cmdshell 'del C:\\*.*'"
        with pytest.raises(SQLValidationError):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_xp_cmdshell_single_statement(self):
        sql = "SELECT xp_cmdshell('del C:\\*.*') FROM users"
        with pytest.raises(SQLValidationError, match="forbidden operation"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    # === Tests for invalid SQL syntax ===

    def test_invalid_syntax(self):
        sql = "SELEC * FROM users"
        with pytest.raises(SQLValidationError, match="syntax error"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_empty_sql(self):
        sql = ""
        with pytest.raises(SQLValidationError, match="empty"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    # === Tests for multiple statements ===

    def test_multiple_statements_blocked(self):
        sql = "SELECT * FROM users; SELECT * FROM admins"
        with pytest.raises(SQLValidationError, match="Multiple SQL statements"):
            validate_text_to_sql(sql, {"users", "admins"}, {"id", "name"})

    # === Tests for table/column whitelisting ===

    def test_disallowed_table(self):
        sql = "SELECT * FROM secret_table"
        with pytest.raises(SQLValidationError, match="not in the allowed list"):
            validate_text_to_sql(sql, {"users", "orders"}, {"id", "name"})

    def test_disallowed_column(self):
        sql = "SELECT id, password FROM users"
        with pytest.raises(SQLValidationError, match="not in the allowed list"):
            validate_text_to_sql(sql, {"users"}, {"id", "name", "email"})

    def test_aggregation_on_disallowed_column(self):
        sql = "SELECT SUM(salary) FROM employees"
        with pytest.raises(SQLValidationError, match="not in the allowed list"):
            validate_text_to_sql(sql, {"employees"}, {"id", "name"})

    # === Tests for SQL comments ===

    def test_block_comment_blocked(self):
        sql = "/* malicious */ SELECT * FROM users"
        with pytest.raises(SQLValidationError, match="comments are not allowed"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})

    def test_line_comment_blocked(self):
        sql = "-- malicious comment\nSELECT * FROM users"
        with pytest.raises(SQLValidationError, match="comments are not allowed"):
            validate_text_to_sql(sql, {"users"}, {"id", "name"})


class TestSQLParsing:
    """Tests for sqlglot parsing functions."""

    def test_extract_table_names_simple(self):
        parsed = validate_sql_syntax("SELECT * FROM users WHERE id = 1")
        tables = extract_table_names(parsed)
        assert "users" in tables

    def test_extract_table_names_join(self):
        parsed = validate_sql_syntax("SELECT u.id, o.amount FROM users u JOIN orders o ON u.id = o.user_id")
        tables = extract_table_names(parsed)
        assert "users" in tables
        assert "orders" in tables

    def test_extract_column_names(self):
        parsed = validate_sql_syntax("SELECT id, name, email FROM users")
        columns = extract_column_names(parsed)
        assert "id" in columns
        assert "name" in columns
        assert "email" in columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
