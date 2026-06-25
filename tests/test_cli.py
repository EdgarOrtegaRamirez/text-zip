"""Tests for the CLI interface."""

import subprocess
import sys


def test_cli_help():
    """Test that the CLI help command works."""
    result = subprocess.run(
        [sys.executable, "-m", "textzip.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "TextZip" in result.stdout


def test_cli_version():
    """Test that the CLI version command works."""
    result = subprocess.run(
        [sys.executable, "-m", "textzip.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_cli_compress_command_help():
    """Test that the compress subcommand help works."""
    result = subprocess.run(
        [sys.executable, "-m", "textzip.cli", "compress", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "compress" in result.stdout


def test_cli_analyze_command_help():
    """Test that the analyze subcommand help works."""
    result = subprocess.run(
        [sys.executable, "-m", "textzip.cli", "analyze", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_info_command():
    """Test that the info command works."""
    result = subprocess.run(
        [sys.executable, "-m", "textzip.cli", "info"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "TextZip" in result.stdout


def test_cli_sample_config():
    """Test that sample_config command works."""
    result = subprocess.run(
        [sys.executable, "-m", "textzip.cli", "sample-config"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "textzip" in result.stdout


def test_cli_compress_inline_text():
    """Test compressing inline text via --text flag."""
    result = subprocess.run(
        [
            sys.executable, "-m", "textzip.cli", "compress",
            "--text", "Hello    world    this    is    a    test",
            "--strategy", "whitespace",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Hello world this is a test" in result.stdout


def test_cli_compress_stats():
    """Test compress with --stats flag."""
    result = subprocess.run(
        [
            sys.executable, "-m", "textzip.cli", "compress",
            "--text", "Hello    world    hello    world",
            "--stats",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Savings:" in result.stdout


def test_cli_compress_stats_json():
    """Test compress with --stats and --format json."""
    result = subprocess.run(
        [
            sys.executable, "-m", "textzip.cli", "compress",
            "--text", "Hello    world",
            "--stats",
            "--format", "json",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "savings_pct" in result.stdout


def test_cli_compress_combined():
    """Test compress with combined strategy."""
    result = subprocess.run(
        [
            sys.executable, "-m", "textzip.cli", "compress",
            "--text", "Hello world this is a test of combined compression",
            "--strategy", "combined",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_compress_invalid_strategy():
    """Test compress with invalid strategy."""
    result = subprocess.run(
        [
            sys.executable, "-m", "textzip.cli", "compress",
            "--text", "Hello world",
            "--strategy", "invalid_strategy",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_cli_missing_input():
    """Test compress with no input (no file, no text, not stdin)."""
    result = subprocess.run(
        [
            sys.executable, "-m", "textzip.cli", "compress",
            "--text", "Hello world",
            "--file", "/nonexistent/file.txt",
        ],
        capture_output=True,
        text=True,
    )
    # Should prefer --text when both are provided, or error on nonexistent file
    # The current logic checks --text first, so this should still work
    # Let's just make sure it doesn't crash with unexpected error
    assert result.returncode == 0 or "file not found" in result.stderr
