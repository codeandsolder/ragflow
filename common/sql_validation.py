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
import re
import sqlglot
from sqlglot.errors import ParseError


ALLOWED_SQL_KEYWORDS = frozenset(
    {
        "SELECT",
        "WITH",
        "FROM",
        "WHERE",
        "GROUP BY",
        "HAVING",
        "ORDER BY",
        "LIMIT",
        "OFFSET",
        "AS",
        "JOIN",
        "LEFT JOIN",
        "RIGHT JOIN",
        "INNER JOIN",
        "OUTER JOIN",
        "CROSS JOIN",
        "ON",
        "AND",
        "OR",
        "NOT",
        "IN",
        "BETWEEN",
        "LIKE",
        "IS NULL",
        "IS NOT NULL",
        "EXISTS",
        "CASE",
        "WHEN",
        "THEN",
        "ELSE",
        "END",
        "DISTINCT",
        "ALL",
        "UNION",
        "INTERSECT",
        "EXCEPT",
    }
)


DANGEROUS_PATTERNS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bTRUNCATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bxp_",
    r"\bsp_\w+",
    r"\bINTO\s+OUTFILE\b",
    r"\bINTO\s+DUMPFILE\b",
    r"\bLOAD_FILE\b",
    r"\bBENCHMARK\b",
    r"\bSLEEP\b",
    r"\bWAITFOR\b",
    r"\bSHUTDOWN\b",
    r"\bGRANT\b",
    r"\bTRIGGER\b",
    r"\bINFORMATION_SCHEMA\b",
]


class SQLValidationError(Exception):
    pass


def validate_sql_syntax(sql: str) -> sqlglot.expressions.Expression:
    try:
        parsed = sqlglot.parse(sql, read="mysql")
        if not parsed:
            raise SQLValidationError("Failed to parse SQL")
        return parsed[0]
    except ParseError as e:
        raise SQLValidationError(f"SQL syntax error: {e}")


def check_statement_type(parsed: sqlglot.expressions.Expression) -> None:
    if not isinstance(parsed, (sqlglot.expressions.Select, sqlglot.expressions.Union)):
        raise SQLValidationError(f"Only SELECT statements are allowed. Got: {type(parsed).__name__}")


def check_for_dangerous_patterns(sql: str) -> None:
    sql_upper = sql.upper()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, sql_upper, re.IGNORECASE):
            raise SQLValidationError(f"SQL contains forbidden operation pattern: {pattern}")


def validate_table_and_column_names(parsed: sqlglot.expressions.Expression, allowed_tables: set[str], allowed_columns: set[str]) -> None:
    tables = extract_table_names(parsed)
    for table in tables:
        if table.lower() not in allowed_tables:
            raise SQLValidationError(f"Table '{table}' is not in the allowed list: {allowed_tables}")

    columns = extract_column_names(parsed)
    for column in columns:
        if column.lower() not in allowed_columns:
            raise SQLValidationError(f"Column '{column}' is not in the allowed list: {allowed_columns}")


def extract_table_names(parsed: sqlglot.expressions.Expression) -> set[str]:
    tables = set()
    for node in parsed.walk():
        if isinstance(node, sqlglot.expressions.Table):
            table_name = node.name
            if table_name:
                tables.add(table_name)
    return tables


def extract_column_names(parsed: sqlglot.expressions.Expression) -> set[str]:
    columns = set()
    for node in parsed.walk():
        if isinstance(node, sqlglot.expressions.Column):
            col_name = node.name
            if col_name:
                columns.add(col_name)
        elif isinstance(node, sqlglot.expressions.Alias):
            alias = node.alias
            if alias:
                columns.add(alias)
    return columns


def validate_text_to_sql(
    sql: str,
    allowed_tables: set[str],
    allowed_columns: set[str],
    max_statements: int = 1,
) -> sqlglot.expressions.Expression:
    sql_clean = sql.strip()
    if not sql_clean:
        raise SQLValidationError("SQL cannot be empty")

    if sql_clean.upper().startswith("/*") or sql_clean.startswith("--"):
        raise SQLValidationError("SQL comments are not allowed")

    statements = [s.strip() for s in sql_clean.split(";") if s.strip()]
    if len(statements) > max_statements:
        raise SQLValidationError(f"Multiple SQL statements are not allowed. Max: {max_statements}")

    check_for_dangerous_patterns(sql_clean)

    parsed = validate_sql_syntax(sql_clean)

    check_statement_type(parsed)

    if allowed_tables or allowed_columns:
        validate_table_and_column_names(parsed, allowed_tables, allowed_columns)

    return parsed
