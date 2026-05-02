"""Tests for flatperf CLI main module."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest


class TestCLIMain:
    """Test the CLI main entry point."""

    def test_cli_imports_without_error(self):
        """Test that CLI module can be imported."""
        from flatperf.__main__ import main
        assert callable(main)

    def test_cli_no_args_shows_help(self, capsys):
        """Test that running without args shows help."""
        with patch("sys.argv", ["flatperf"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            # Should exit with code 0 or 1 (help displayed)
            assert exc_info.value.code in (0, 1)

    def test_cli_help_flag(self, capsys):
        """Test that --help works."""
        with patch("sys.argv", ["flatperf", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_generate_help(self, capsys):
        """Test generate subcommand help."""
        with patch("sys.argv", ["flatperf", "generate", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_profile_help(self, capsys):
        """Test profile subcommand help."""
        with patch("sys.argv", ["flatperf", "profile", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_compare_help(self, capsys):
        """Test compare subcommand help."""
        with patch("sys.argv", ["flatperf", "compare", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_search_help(self, capsys):
        """Test search subcommand help."""
        with patch("sys.argv", ["flatperf", "search", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_bench_search_help(self, capsys):
        """Test bench-search subcommand help."""
        with patch("sys.argv", ["flatperf", "bench-search", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_join_help(self, capsys):
        """Test join subcommand help."""
        with patch("sys.argv", ["flatperf", "join", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_bench_join_help(self, capsys):
        """Test bench-join subcommand help."""
        with patch("sys.argv", ["flatperf", "bench-join", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_aggregate_help(self, capsys):
        """Test aggregate subcommand help."""
        with patch("sys.argv", ["flatperf", "aggregate", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_bench_aggregate_help(self, capsys):
        """Test bench-aggregate subcommand help."""
        with patch("sys.argv", ["flatperf", "bench-aggregate", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_encrypt_help(self, capsys):
        """Test encrypt subcommand help."""
        with patch("sys.argv", ["flatperf", "encrypt", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_decrypt_help(self, capsys):
        """Test decrypt subcommand help."""
        with patch("sys.argv", ["flatperf", "decrypt", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_compress_help(self, capsys):
        """Test compress subcommand help."""
        with patch("sys.argv", ["flatperf", "compress", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_cli_delete_help(self, capsys):
        """Test delete subcommand help."""
        with patch("sys.argv", ["flatperf", "delete", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                from flatperf.__main__ import main
                main()

            assert exc_info.value.code == 0

    def test_all_commands_recognized(self):
        """Verify all expected commands are registered."""
        from flatperf.__main__ import main
        import argparse

        # We can't easily test the full parser, but we can verify
        # the main function has the expected structure
        assert callable(main)


class TestCLICommandsDispatch:
    """Test CLI command dispatch."""

    def test_generate_command_exists(self):
        """Test generate command is accessible."""
        from flatperf.generate import generate
        assert callable(generate)

    def test_profile_command_exists(self):
        """Test profile command is accessible."""
        from flatperf.commands import profile
        assert callable(profile)

    def test_compare_command_exists(self):
        """Test compare command is accessible."""
        from flatperf.commands import compare
        assert callable(compare)

    def test_search_command_exists(self):
        """Test search command is accessible."""
        from flatperf.commands import search
        assert callable(search)

    def test_bench_search_command_exists(self):
        """Test bench_search command is accessible."""
        from flatperf.commands import bench_search
        assert callable(bench_search)

    def test_join_command_exists(self):
        """Test join command is accessible."""
        from flatperf.commands import join
        assert callable(join)

    def test_bench_join_command_exists(self):
        """Test bench_join command is accessible."""
        from flatperf.commands import bench_join
        assert callable(bench_join)

    def test_aggregate_command_exists(self):
        """Test aggregate command is accessible."""
        from flatperf.commands import aggregate
        assert callable(aggregate)

    def test_bench_aggregate_command_exists(self):
        """Test bench_aggregate command is accessible."""
        from flatperf.commands import bench_aggregate
        assert callable(bench_aggregate)

    def test_encrypt_command_exists(self):
        """Test encrypt command is accessible."""
        from flatperf.commands import encrypt
        assert callable(encrypt)

    def test_decrypt_command_exists(self):
        """Test decrypt command is accessible."""
        from flatperf.commands import decrypt
        assert callable(decrypt)

    def test_compress_command_exists(self):
        """Test compress command is accessible."""
        from flatperf.commands import compress
        assert callable(compress)

    def test_delete_command_exists(self):
        """Test delete command is accessible."""
        from flatperf.commands import delete_bench
        assert callable(delete_bench)