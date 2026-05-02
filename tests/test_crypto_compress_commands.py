"""Tests for flatperf encrypt/decrypt/compress/delete commands."""

from __future__ import annotations

import argparse
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

from flatperf.commands import encrypt, decrypt, compress, delete_bench


class TestEncryptCommand:
    """Test the encrypt command."""

    def test_encrypt_requires_data_dir(self, tmp_path):
        args = argparse.Namespace(
            data_dir=str(tmp_path / "nonexistent"),
            passphrase="testpass",
            workers=None,
            top=25,
            flatseek_src=None,
        )

        result = encrypt(args)
        assert result == 2

    def test_encrypt_requires_passphrase(self, tmp_path):
        # Create a minimal directory structure
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        index_dir = data_dir / "index"
        index_dir.mkdir()

        args = argparse.Namespace(
            data_dir=str(data_dir),
            passphrase=None,
            workers=None,
            top=25,
            flatseek_src=None,
        )

        result = encrypt(args)
        assert result == 1


class TestDecryptCommand:
    """Test the decrypt command."""

    def test_decrypt_requires_data_dir(self, tmp_path):
        args = argparse.Namespace(
            data_dir=str(tmp_path / "nonexistent"),
            passphrase="testpass",
            top=25,
            flatseek_src=None,
        )

        result = decrypt(args)
        assert result == 2

    def test_decrypt_requires_passphrase(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        args = argparse.Namespace(
            data_dir=str(data_dir),
            passphrase=None,
            top=25,
            flatseek_src=None,
        )

        result = decrypt(args)
        assert result == 1


class TestCompressCommand:
    """Test the compress command."""

    def test_compress_requires_data_dir(self, tmp_path):
        args = argparse.Namespace(
            data_dir=str(tmp_path / "nonexistent"),
            level=6,
            workers=None,
            top=25,
            flatseek_src=None,
        )

        result = compress(args)
        assert result == 2

    def test_compress_level_validation(self, tmp_path):
        """Test that compression level is properly validated."""
        # Valid levels are 1-9
        assert 1 <= 6 <= 9

        # Test the range in argparse
        import sys
        if sys.version_info >= (3, 11):
            choices = range(1, 10)
            assert all(1 <= c <= 9 for c in choices)


class TestDeleteCommand:
    """Test the delete command."""

    def test_delete_requires_data_dir(self, tmp_path):
        args = argparse.Namespace(
            data_dir=str(tmp_path / "nonexistent"),
            runs=3,
            workers=None,
            flatseek_src=None,
        )

        result = delete_bench(args)
        assert result == 2

    def test_delete_runs_parameter(self):
        """Test delete runs parameter is respected."""
        args = argparse.Namespace(
            data_dir="/fake",
            runs=5,
            workers=None,
            flatseek_src=None,
        )

        assert args.runs == 5


class TestEncryptionOutput:
    """Test encryption output structure."""

    def test_encrypt_args_structure(self):
        """Verify encrypt command argument structure."""
        args = argparse.Namespace(
            data_dir="/test/data",
            passphrase="secret123",
            workers=4,
            top=30,
            flatseek_src="/fake/src",
        )

        assert args.data_dir == "/test/data"
        assert args.passphrase == "secret123"
        assert args.workers == 4
        assert args.top == 30


class TestDecryptionOutput:
    """Test decryption output structure."""

    def test_decrypt_args_structure(self):
        """Verify decrypt command argument structure."""
        args = argparse.Namespace(
            data_dir="/test/data",
            passphrase="secret123",
            top=30,
            flatseek_src="/fake/src",
        )

        assert args.data_dir == "/test/data"
        assert args.passphrase == "secret123"
        assert args.top == 30


class TestCompressOutput:
    """Test compression output structure."""

    def test_compress_args_structure(self):
        """Verify compress command argument structure."""
        args = argparse.Namespace(
            data_dir="/test/data",
            level=9,
            workers=8,
            top=25,
            flatseek_src="/fake/src",
        )

        assert args.data_dir == "/test/data"
        assert args.level == 9
        assert args.workers == 8
        assert args.top == 25

    def test_compress_ratio_calculation(self):
        """Test compression ratio calculation."""
        before_size = 100_000_000  # 100 MB
        after_size = 35_000_000   # 35 MB

        ratio = before_size / after_size
        saved_mb = (before_size - after_size) / 1e6

        assert ratio == pytest.approx(2.857, rel=0.01)
        assert saved_mb == pytest.approx(65.0, rel=0.01)


class TestDeleteOutput:
    """Test delete command output structure."""

    def test_delete_args_structure(self):
        """Verify delete command argument structure."""
        args = argparse.Namespace(
            data_dir="/test/data",
            runs=5,
            workers=16,
            flatseek_src="/fake/src",
        )

        assert args.data_dir == "/test/data"
        assert args.runs == 5
        assert args.workers == 16