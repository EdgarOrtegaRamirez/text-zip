# TextZip

Lightweight token compression CLI and library for AI agents. Compress text to reduce token usage when sending to LLMs, saving 40-80% tokens while preserving semantic meaning.

## Features

- **Multiple compression strategies**: whitespace normalization, deduplication, code formatting, key information extraction
- **Combined pipeline**: applies all strategies sequentially for maximum savings
- **CLI tool**: easy to use from the command line or in scripts
- **Python library**: import and use in your own projects
- **MCP server integration**: expose compression as tools for AI coding agents
- **Zero external LLM dependency**: all compression is rule-based, no API calls needed

## Install

```bash
pip install text-zip
# or from source
pip install .
```

Optional MCP support:
```bash
pip install text-zip[mcp]
```

## Quick Start

### CLI

Compress text inline:
```bash
textzip compress --text "Hello    world    this    has    extra    whitespace"
```

Show compression stats:
```bash
textzip compress --text "Your text here" --stats
```

Analyze compression potential:
```bash
textzip analyze --text "Your text here"
```

Compress from a file:
```bash
textzip compress --file document.txt --strategy combined
```

Pipe from stdin:
```bash
cat document.txt | textzip compress
```

### Python Library

```python
from textzip.strategies import CombinedCompressor, Tokenizer

compressor = CombinedCompressor()
result = compressor.compress("Your long text here...")

print(f"Savings: {result.savings_pct}%")
print(f"Original: {result.original_tokens} tokens")
print(f"Compressed: {result.compressed_tokens} tokens")
print(result.compressed_text)
```

### MCP Server

Use as an MCP tool for AI agents:
```python
from textzip.mcp_server import create_textzip_tools, handle_mcp_tool_call

tools = create_textzip_tools()
result = handle_mcp_tool_call("textzip_compress", {"text": "Your text"})
```

## Strategies

| Strategy | Description | Typical Savings |
|----------|-------------|-----------------|
| `combined` | Full pipeline: whitespace + dedup + key extraction | 40-80% |
| `whitespace` | Normalize whitespace and newlines | 5-15% |
| `deduplicate` | Remove duplicate lines | 10-50% |
| `code` | Strip comments and blank lines from code | 20-40% |
| `key_info` | Extract headers, key-value pairs, first sentences | 30-70% |

## Configuration

Print a sample config file:
```bash
textzip sample-config > .textzip.yaml
```

## Architecture

```
textzip/
├── textzip/
│   ├── __init__.py      # Package init
│   ├── cli.py           # Click CLI interface
│   ├── strategies.py    # Compression strategy implementations
│   └── mcp_server.py    # MCP tool definitions and handlers
├── tests/               # Test suite
├── pyproject.toml       # Project config
├── README.md
├── LICENSE
└── AGENTS.md
```

## Security

- No network calls or external API dependencies
- No file system access beyond explicitly provided file paths
- All input is validated and sanitized
- No hardcoded secrets or tokens

## License

MIT License - see [LICENSE](LICENSE) for details.
