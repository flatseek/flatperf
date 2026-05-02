"""Pytest configuration and fixtures for flatperf tests."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


# Resolve flatseek source path - use local source if available
FLATSEEK_SRC = os.environ.get("FLATSEEK_SRC") or str(
    Path(__file__).parent.parent.parent / "flatseek" / "src"
)


@pytest.fixture(scope="session")
def flatseek_src():
    """Path to flatseek source directory."""
    if not os.path.isdir(FLATSEEK_SRC):
        pytest.skip(f"flatseek source not found at {FLATSEEK_SRC}")
    return FLATSEEK_SRC


@pytest.fixture(scope="session")
def python_with_flatseek(flatseek_src):
    """Python executable with flatseek in path."""
    # Insert flatseek src at the start of sys.path
    old_path = sys.path.copy()
    if flatseek_src not in sys.path:
        sys.path.insert(0, flatseek_src)
    yield sys.executable
    sys.path = old_path


@pytest.fixture
def temp_csv(tmp_path):
    """Create a temporary CSV file for testing."""
    csv_path = tmp_path / "test.csv"
    csv_content = """id,title,content,author,category,published_at,views,status
1,Test Article One,This is the content of article one with some text.,john,tech,2024-01-15,1000,published
2,Second Article,Content for the second article here.,jane,news,2024-01-16,2500,published
3,Third Piece,Another article content with different text.,bob,sports,2024-01-17,500,archived
4,Fourth Article,Yet more content for testing purposes.,alice,tech,2024-01-18,3000,published
5,Fifth Article,Sample content number five here.,charlie,opinion,2024-01-19,750,draft
"""
    csv_path.write_text(csv_content)
    return str(csv_path)


@pytest.fixture
def temp_index_dir(tmp_path):
    """Create a temporary index directory."""
    index_dir = tmp_path / "index_data"
    index_dir.mkdir()
    return str(index_dir)


@pytest.fixture
def generated_csv(tmp_path):
    """Generate a CSV using flatperf generate command."""
    output_path = tmp_path / "generated.csv"
    from flatperf.generate import SCHEMAS, _random_text, _random_date

    import csv

    schema = SCHEMAS["article"]
    fields = schema["fields"]
    rows = 100

    rows_data = []
    for i in range(rows):
        row = {
            "id": i + 1,
            "title": _random_text(4, 8),
            "content": _random_text(10, 30),
            "author": _random_text(1, 2).replace(" ", "_").lower(),
            "category": ["tech", "news", "opinion", "sports", "entertainment"][i % 5],
            "published_at": _random_date(),
            "views": (i + 1) * 100,
            "status": ["published", "draft", "archived"][i % 3],
        }
        rows_data.append(row)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows_data)

    return str(output_path)


@pytest.fixture
def built_index(temp_csv, temp_index_dir, python_with_flatseek, flatseek_src):
    """Build an index from the temp CSV using flatseek."""
    sys.path.insert(0, flatseek_src)

    try:
        from flatseek.cli import cmd_build
        import argparse

        ns = argparse.Namespace(
            csv_dir=temp_csv,
            output=temp_index_dir,
            map=None,
            dataset=None,
            sep=",",
            columns=None,
            workers=1,
            plan=None,
            worker_id=None,
            estimate=False,
            dedup=False,
            dedup_fields=None,
            daemon=False,
        )

        cmd_build(ns)

        # Verify index was built
        index_dir = os.path.join(temp_index_dir, "index")
        if not os.path.isdir(index_dir):
            pytest.skip("Index not built - flatseek build failed")

        yield temp_index_dir
    finally:
        sys.path.remove(flatseek_src)
        if flatseek_src in sys.path:
            sys.path.remove(flatseek_src)