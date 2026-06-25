# AGENTS.md - Notes for AI Agents

## Project: TextZip

A lightweight token compression CLI and library for AI agents.

## What it does

Compresses text to reduce token usage when sending to LLMs. Uses rule-based strategies (no LLM dependency required):
- Whitespace normalization
- Line deduplication
- Code comment/blank-line stripping
- Key information extraction

## Quick reference

```bash
# Compress text
textzip compress --text "your text here"
textzip compress --file document.txt --strategy combined

# Show stats
textzip compress --text "your text here" --stats

# Analyze compression potential
textzip analyze --text "your text here"

# List strategies
textzip info
```

## Python API

```python
from textzip.strategies import CombinedCompressor, Tokenizer

compressor = CombinedCompressor()
result = compressor.compress(text)
# result.compressed_text, result.savings_pct, result.original_tokens, result.compressed_tokens
```

## Project structure

- `textzip/strategies.py` - Core compression strategies (WhitespaceNormalizer, Deduplicator, CodeFormatter, KeyExtractor, CombinedCompressor)
- `textzip/cli.py` - Click CLI interface
- `textzip/mcp_server.py` - MCP tool definitions and handlers
- `tests/` - Test suite (pytest)

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Dependencies

- `click>=8.1.7,<9.0.0` - CLI framework
- `toml>=0.10.2,<1.0.0` - Config parsing
- Optional: `mcp>=1.0.0,<2.0.0` - MCP server support

## Security notes

- No network calls or external API dependencies
- No hardcoded secrets
- File paths are validated before reading
- All input is handled safely
