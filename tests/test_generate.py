"""Tests for flatperf generate command."""

from __future__ import annotations

import csv
import os

from flatperf.generate import SCHEMAS, generate, _random_text, _random_date


class TestGenerateSchemas:
    """Test that all schemas are properly defined."""

    def test_article_schema_exists(self):
        assert "article" in SCHEMAS
        schema = SCHEMAS["article"]
        assert "fields" in schema
        assert "types" in schema
        assert len(schema["fields"]) == 8

    def test_users_schema_exists(self):
        assert "users" in SCHEMAS
        schema = SCHEMAS["users"]
        assert "fields" in schema
        assert "types" in schema
        assert len(schema["fields"]) == 7

    def test_transactions_schema_exists(self):
        assert "transactions" in SCHEMAS
        schema = SCHEMAS["transactions"]
        assert "fields" in schema
        assert "types" in schema
        assert len(schema["fields"]) == 8


class TestRandomGenerators:
    """Test random data generators."""

    def test_random_text_returns_string(self):
        result = _random_text(3, 5)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_random_text_respects_word_range(self):
        text = _random_text(3, 5)
        words = text.split()
        assert 3 <= len(words) <= 5

    def test_random_date_format(self):
        date = _random_date()
        assert isinstance(date, str)
        # Format: YYYY-MM-DD
        assert len(date) == 10
        assert date[4] == "-"
        assert date[7] == "-"


class TestGenerateFunction:
    """Test the generate function."""

    def test_generate_creates_file(self, tmp_path):
        output = tmp_path / "test_output.csv"

        import argparse

        args = argparse.Namespace(
            schema="article",
            rows=50,
            output=str(output),
        )

        result = generate(args)
        assert result == 0
        assert output.exists()

    def test_generate_article_rows(self, tmp_path):
        output = tmp_path / "article.csv"
        rows = 100

        import argparse

        args = argparse.Namespace(
            schema="article",
            rows=rows,
            output=str(output),
        )

        generate(args)

        # Count rows (excluding header)
        with open(output) as f:
            reader = csv.DictReader(f)
            actual_rows = list(reader)

        assert len(actual_rows) == rows

    def test_generate_users_rows(self, tmp_path):
        output = tmp_path / "users.csv"
        rows = 50

        import argparse

        args = argparse.Namespace(
            schema="users",
            rows=rows,
            output=str(output),
        )

        generate(args)

        with open(output) as f:
            reader = csv.DictReader(f)
            actual_rows = list(reader)

        assert len(actual_rows) == rows

    def test_generate_transactions_rows(self, tmp_path):
        output = tmp_path / "transactions.csv"
        rows = 50

        import argparse

        args = argparse.Namespace(
            schema="transactions",
            rows=rows,
            output=str(output),
        )

        generate(args)

        with open(output) as f:
            reader = csv.DictReader(f)
            actual_rows = list(reader)

        assert len(actual_rows) == rows

    def test_generate_invalid_schema_returns_error(self, tmp_path):
        output = tmp_path / "invalid.csv"

        import argparse

        args = argparse.Namespace(
            schema="invalid_schema",
            rows=10,
            output=str(output),
        )

        result = generate(args)
        assert result == 1

    def test_generate_article_has_required_columns(self, tmp_path):
        output = tmp_path / "article.csv"

        import argparse

        args = argparse.Namespace(
            schema="article",
            rows=10,
            output=str(output),
        )

        generate(args)

        with open(output) as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            expected = SCHEMAS["article"]["fields"]

            for col in expected:
                assert col in headers

    def test_generate_file_size_reasonable(self, tmp_path):
        output = tmp_path / "large.csv"

        import argparse

        args = argparse.Namespace(
            schema="article",
            rows=1000,
            output=str(output),
        )

        generate(args)

        size_kb = os.path.getsize(output) / 1024
        # 1000 rows should be at least 50KB and no more than 5MB
        assert 50 < size_kb < 5000