"""MCP server for TextZip - integrate compression with AI agents."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("textzip.mcp")


def create_textzip_tools() -> list[dict[str, Any]]:
    """Create MCP tool definitions for TextZip."""
    return [
        {
            "name": "textzip_compress",
            "description": (
                "Compress text using TextZip to reduce token usage. "
                "Returns the compressed text and statistics."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to compress",
                    },
                    "strategy": {
                        "type": "string",
                        "enum": [
                            "combined",
                            "whitespace",
                            "deduplicate",
                            "code",
                            "key_info",
                        ],
                        "default": "combined",
                        "description": "Compression strategy to use",
                    },
                },
                "required": ["text"],
            },
        },
        {
            "name": "textzip_analyze",
            "description": (
                "Analyze text to show compression potential across all strategies. "
                "Returns token counts and savings for each strategy."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to analyze",
                    },
                },
                "required": ["text"],
            },
        },
    ]


def handle_compress(text: str, strategy: str = "combined") -> dict[str, Any]:
    """Handle the compress tool call."""
    from textzip.strategies import CombinedCompressor

    compressor = _get_strategy(strategy)
    result = compressor.compress(text)

    return {
        "compressed_text": result.compressed_text,
        "original_tokens": result.original_tokens,
        "compressed_tokens": result.compressed_tokens,
        "savings_pct": result.savings_pct,
        "strategy": result.strategy,
    }


def handle_analyze(text: str) -> dict[str, Any]:
    """Handle the analyze tool call."""
    from textzip.strategies import (
        CombinedCompressor,
        WhitespaceNormalizer,
        Deduplicator,
        CodeFormatter,
        KeyExtractor,
        Tokenizer,
    )

    original_tokens = Tokenizer.count_tokens(text)
    strategies = {
        "whitespace": WhitespaceNormalizer(),
        "deduplicate": Deduplicator(),
        "code": CodeFormatter(),
        "key_info": KeyExtractor(),
    }

    results = {}
    for name, strategy in strategies.items():
        r = strategy.compress(text)
        results[name] = {
            "tokens": r.compressed_tokens,
            "savings_pct": r.savings_pct,
        }

    combined = CombinedCompressor()
    combined_result = combined.compress(text)
    results["combined"] = {
        "tokens": combined_result.compressed_tokens,
        "savings_pct": combined_result.savings_pct,
    }

    return {
        "original_tokens": original_tokens,
        "strategies": results,
    }


def _get_strategy(strategy_name: str) -> CombinedCompressor:
    """Get a compressor instance based on strategy name."""
    from textzip.strategies import (
        CombinedCompressor,
        WhitespaceNormalizer,
        Deduplicator,
        CodeFormatter,
        KeyExtractor,
    )

    strategy_map = {
        "whitespace": CombinedCompressor([WhitespaceNormalizer()]),
        "deduplicate": CombinedCompressor([Deduplicator()]),
        "code": CombinedCompressor([CodeFormatter()]),
        "key_info": CombinedCompressor([KeyExtractor()]),
        "combined": CombinedCompressor(),
    }
    return strategy_map.get(strategy_name, CombinedCompressor())


def handle_mcp_tool_call(tool_name: str, arguments: dict[str, Any]) -> str:
    """Handle an MCP tool call and return JSON result."""
    try:
        if tool_name == "textzip_compress":
            text = arguments.get("text", "")
            strategy = arguments.get("strategy", "combined")
            result = handle_compress(text, strategy)
        elif tool_name == "textzip_analyze":
            text = arguments.get("text", "")
            result = handle_analyze(text)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        return json.dumps(result)
    except Exception as e:
        logger.exception("Error handling tool call %s", tool_name)
        return json.dumps({"error": str(e)})
