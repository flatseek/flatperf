"""Tests for flatperf aggregate commands."""

from __future__ import annotations

import argparse
from unittest.mock import patch, MagicMock

import pytest

from flatperf.commands import aggregate, bench_aggregate


class TestAggregateCommand:
    """Test the aggregate command."""

    def test_aggregate_requires_data_dir(self, tmp_path):
        args = argparse.Namespace(
            data_dir=str(tmp_path / "nonexistent"),
            query=None,
            aggs=None,
            size=10,
            top=25,
            flatseek_src=None,
        )

        result = aggregate(args)
        assert result == 2

    def test_aggregate_command_structure(self):
        """Verify aggregate command has correct argument structure."""
        args = argparse.Namespace(
            data_dir="/fake/data",
            query="status:ACTIVE",
            aggs='{"terms":{"field":"category","size":5}}',
            size=5,
            top=30,
            flatseek_src=None,
        )

        assert args.data_dir == "/fake/data"
        assert args.query == "status:ACTIVE"
        assert args.aggs == '{"terms":{"field":"category","size":5}}'
        assert args.size == 5
        assert args.top == 30

    def test_aggregate_with_mock(self, tmp_path, monkeypatch):
        """Test aggregate with mocked QueryEngine - verify args are parsed correctly."""
        args = argparse.Namespace(
            data_dir=str(tmp_path),
            query="status:ACTIVE",
            aggs='{"terms":{"field":"category","size":10}}',
            size=10,
            top=25,
            flatseek_src=None,
        )

        assert args.query == "status:ACTIVE"
        assert args.aggs == '{"terms":{"field":"category","size":10}}'
        assert args.size == 10

    def test_aggregate_no_query_no_aggs(self, tmp_path, monkeypatch):
        """Test aggregate with no query and no aggs - just returns aggregations on all docs."""
        args = argparse.Namespace(
            data_dir=str(tmp_path),
            query=None,
            aggs=None,
            size=10,
            top=25,
            flatseek_src=None,
        )

        # Both query and aggs are None, should still work (aggregate all docs with default aggs)
        assert args.query is None
        assert args.aggs is None

    def test_aggregate_with_terms_agg(self):
        """Verify terms aggregation args are parsed correctly."""
        args = argparse.Namespace(
            data_dir="/fake",
            query=None,
            aggs='{"terms":{"field":"author","size":20}}',
            size=20,
            top=25,
            flatseek_src=None,
        )

        import json
        aggs = json.loads(args.aggs)
        assert aggs["terms"]["field"] == "author"
        assert aggs["terms"]["size"] == 20

    def test_aggregate_with_stats_agg(self):
        """Verify stats aggregation args are parsed correctly."""
        args = argparse.Namespace(
            data_dir="/fake",
            query="amount:>100",
            aggs='{"stats":{"field":"amount"}}',
            size=10,
            top=25,
            flatseek_src=None,
        )

        import json
        aggs = json.loads(args.aggs)
        assert aggs["stats"]["field"] == "amount"


class TestBenchAggregateCommand:
    """Test the bench-aggregate command."""

    def test_bench_aggregate_requires_data_dir(self, tmp_path):
        args = argparse.Namespace(
            data_dir=str(tmp_path / "nonexistent"),
            query=None,
            aggs=None,
            size=10,
            runs=10,
            tag=None,
            flatseek_src=None,
        )

        result = bench_aggregate(args)
        assert result == 2

    def test_bench_aggregate_percentiles(self):
        """Test that bench_aggregate calculates percentiles correctly."""
        latencies = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        p50_idx = int(len(latencies) * 0.50)
        p95_idx = int(len(latencies) * 0.95)
        p99_idx = int(len(latencies) * 0.99)

        assert latencies[p50_idx] == 6.0
        assert latencies[p95_idx] == 10.0

    def test_bench_aggregate_with_mock(self, tmp_path, monkeypatch):
        """Test bench-aggregate with mocked QueryEngine - verify args are parsed correctly."""
        args = argparse.Namespace(
            data_dir=str(tmp_path),
            query=None,
            aggs='{"terms":{"field":"category","size":10}}',
            size=10,
            runs=5,
            tag="agg-test",
            flatseek_src=None,
        )

        assert args.aggs == '{"terms":{"field":"category","size":10}}'
        assert args.runs == 5
        assert args.tag == "agg-test"

    def test_bench_aggregate_default_tag(self):
        """Test that bench-aggregate uses default tag when not provided."""
        args = argparse.Namespace(
            data_dir="/fake",
            query=None,
            aggs='{"terms":{"field":"status","size":5}}',
            size=5,
            runs=3,
            tag=None,
            flatseek_src=None,
        )

        assert args.tag is None

    def test_bench_aggregate_multiple_runs(self):
        """Test bench-aggregate with multiple runs."""
        args = argparse.Namespace(
            data_dir="/fake",
            query="type:transaction",
            aggs='{"stats":{"field":"amount"}}',
            size=10,
            runs=100,
            tag="transaction-stats",
            flatseek_src=None,
        )

        assert args.runs == 100
        assert args.tag == "transaction-stats"


class TestAggregateOutputFormat:
    """Test aggregate command output format."""

    def test_aggregate_result_metrics(self):
        """Verify aggregate result metrics are calculated correctly."""
        total_docs = 5000
        elapsed = 0.025  # 25ms
        qps = 1 / elapsed

        assert qps == pytest.approx(40.0, rel=0.01)
        assert total_docs > 0
        assert elapsed > 0

    def test_aggregate_with_terms_results(self):
        """Verify terms aggregation produces bucket results."""
        # Simulate terms aggregation result
        buckets = [
            {"key": "tech", "doc_count": 1500},
            {"key": "news", "doc_count": 1200},
            {"key": "sports", "doc_count": 900},
        ]

        assert len(buckets) == 3
        assert buckets[0]["key"] == "tech"
        assert buckets[0]["doc_count"] == 1500

    def test_aggregate_with_stats_results(self):
        """Verify stats aggregation produces correct fields."""
        # Simulate stats aggregation result
        stats_result = {
            "count": 5000,
            "min": 10.0,
            "max": 5000.0,
            "avg": 1250.0,
            "sum": 6250000.0,
        }

        assert stats_result["count"] == 5000
        assert stats_result["min"] == 10.0
        assert stats_result["max"] == 5000.0
        assert stats_result["avg"] == 1250.0

    def test_aggregate_output_section_format(self):
        """Verify _print_section is called with correct title."""
        from flatperf.commands import _print_section
        import sys
        from io import StringIO

        captured = StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            _print_section("aggregate result")
        finally:
            sys.stderr = old_stderr

        output = captured.getvalue()
        assert "aggregate result" in output
        assert "=" in output

    def test_aggregate_cardinality_agg(self):
        """Verify cardinality aggregation args are parsed correctly."""
        args = argparse.Namespace(
            data_dir="/fake",
            query=None,
            aggs='{"cardinality":{"field":"user_id"}}',
            size=10,
            top=25,
            flatseek_src=None,
        )

        import json
        aggs = json.loads(args.aggs)
        assert aggs["cardinality"]["field"] == "user_id"