"""CLI interface for TextZip."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from textzip import __version__
from textzip.strategies import (
    CodeFormatter,
    CombinedCompressor,
    CompressionResult,
    Deduplicator,
    KeyExtractor,
    Tokenizer,
    WhitespaceNormalizer,
)

logger = logging.getLogger("textzip")


def _load_text(source: str | None, input_text: str | None) -> str:
    """Load text from file path, stdin, or inline argument."""
    if input_text:
        return input_text
    if source:
        path = Path(source)
        if not path.exists():
            click.echo(f"Error: file not found: {source}", err=True)
            sys.exit(1)
        return path.read_text(encoding="utf-8")
    # Read from stdin
    if not sys.stdin.isatty():
        return sys.stdin.read()
    click.echo("Error: provide text via --text, --file, or pipe via stdin", err=True)
    sys.exit(1)


def _get_strategy(strategy_name: str) -> CombinedCompressor:
    """Get a compressor instance based on strategy name."""
    strategy_map = {
        "whitespace": CombinedCompressor([WhitespaceNormalizer()]),
        "deduplicate": CombinedCompressor([Deduplicator()]),
        "code": CombinedCompressor([CodeFormatter()]),
        "key_info": CombinedCompressor([KeyExtractor()]),
        "combined": CombinedCompressor(),
    }
    if strategy_name not in strategy_map:
        click.echo(
            f"Error: unknown strategy '{strategy_name}'. "
            f"Available: {', '.join(strategy_map.keys())}",
            err=True,
        )
        sys.exit(1)
    return strategy_map[strategy_name]


@click.group()
@click.version_option(version=__version__, prog_name="textzip")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def main(verbose: bool) -> None:
    """TextZip - Token compression CLI and library for AI agents.

    Compress text to reduce token usage when sending to LLMs.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)


@main.command()
@click.option("--text", "-t", "input_text", help="Inline text to compress")
@click.option("--file", "-f", "source", help="File path to compress")
@click.option(
    "--strategy",
    "-s",
    default="combined",
    type=click.Choice(["combined", "whitespace", "deduplicate", "code", "key_info"]),
    help="Compression strategy to use",
)
@click.option(
    "--format",
    "-o",
    "output_format",
    default="text",
    type=click.Choice(["text", "json"]),
    help="Output format",
)
@click.option(
    "--stats",
    is_flag=True,
    help="Show compression statistics instead of compressed text",
)
def compress(
    input_text: str | None,
    source: str | None,
    strategy: str,
    output_format: str,
    stats: bool,
) -> None:
    """Compress text using the specified strategy."""
    text = _load_text(source, input_text)
    compressor = _get_strategy(strategy)
    result = compressor.compress(text)

    if stats:
        if output_format == "json":
            click.echo(json.dumps({
                "original_tokens": result.original_tokens,
                "compressed_tokens": result.compressed_tokens,
                "savings_pct": result.savings_pct,
                "strategy": result.strategy,
            }, indent=2))
        else:
            click.echo(f"Strategy: {result.strategy}")
            click.echo(f"Original tokens: {result.original_tokens}")
            click.echo(f"Compressed tokens: {result.compressed_tokens}")
            click.echo(f"Savings: {result.savings_pct}%")
    else:
        click.echo(result.compressed_text)


@main.command()
@click.option(
    "--text", "-t", "input_text", help="Inline text to analyze"
)
@click.option("--file", "-f", "source", help="File path to analyze")
def analyze(input_text: str | None, source: str | None) -> None:
    """Analyze text and show compression potential for each strategy."""
    text = _load_text(source, input_text)
    original_tokens = Tokenizer.count_tokens(text)

    strategies = {
        "whitespace": WhitespaceNormalizer(),
        "deduplicate": Deduplicator(),
        "code": CodeFormatter(),
        "key_info": KeyExtractor(),
    }

    click.echo(f"Original text: {original_tokens} tokens")
    click.echo("-" * 50)

    for name, strategy in strategies.items():
        result = strategy.compress(text)
        click.echo(f"  {name:15s}: {result.compressed_tokens:5d} tokens "
                   f"({result.savings_pct:5.1f}% savings)")

    # Combined
    combined = CombinedCompressor()
    combined_result = combined.compress(text)
    click.echo("-" * 50)
    click.echo(f"  {'combined':15s}: {combined_result.compressed_tokens:5d} tokens "
               f"({combined_result.savings_pct:5.1f}% savings)")


@main.command()
def sample_config() -> None:
    """Print a sample textzip config file."""
    click.echo("""# TextZip configuration
# Save as .textzip.yaml in your project root

# Default compression strategy
default_strategy: combined

# Strategies to apply (in order)
# Options: whitespace, deduplicate, code, key_info
pipeline:
  - whitespace
  - deduplicate
  - key_info

# Output format
output_format: text

# Always show stats alongside output
show_stats: false
""")


@main.command()
def info() -> None:
    """Show TextZip version and available strategies."""
    click.echo(f"TextZip v{__version__}")
    click.echo("Available strategies:")
    click.echo("  combined   - Full pipeline: whitespace + dedup + key extraction")
    click.echo("  whitespace - Normalize whitespace and newlines")
    click.echo("  deduplicate - Remove duplicate lines")
    click.echo("  code       - Strip comments and blank lines from code")
    click.echo("  key_info   - Extract headers, key-value pairs, first sentences")


if __name__ == "__main__":
    main()
