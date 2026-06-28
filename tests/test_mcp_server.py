"""Tests for the MCP server module."""

import json

from textzip.mcp_server import (
    create_textzip_tools,
    handle_analyze,
    handle_compress,
    handle_mcp_tool_call,
)


class TestCreateTextZipTools:
    """Tests for tool creation."""

    def test_returns_list(self):
        tools = create_textzip_tools()
        assert isinstance(tools, list)

    def test_has_two_tools(self):
        tools = create_textzip_tools()
        assert len(tools) == 2

    def test_compress_tool_exists(self):
        tools = create_textzip_tools()
        names = [t["name"] for t in tools]
        assert "textzip_compress" in names

    def test_analyze_tool_exists(self):
        tools = create_textzip_tools()
        names = [t["name"] for t in tools]
        assert "textzip_analyze" in names

    def test_tool_has_description(self):
        tools = create_textzip_tools()
        for tool in tools:
            assert "description" in tool
            assert len(tool["description"]) > 0

    def test_tool_has_input_schema(self):
        tools = create_textzip_tools()
        for tool in tools:
            assert "inputSchema" in tool
            assert "properties" in tool["inputSchema"]


class TestHandleCompress:
    """Tests for compress handler."""

    def test_basic_compress(self):
        text = "Hello    world    this    is    a    test"
        result = handle_compress(text, "whitespace")
        assert "compressed_text" in result
        assert "savings_pct" in result
        assert "original_tokens" in result
        assert "compressed_tokens" in result

    def test_combined_strategy(self):
        text = "Hello    world    hello    world\n\n\n\nHello    world"
        result = handle_compress(text, "combined")
        assert result["savings_pct"] > 0

    def test_default_strategy(self):
        text = "Hello world"
        result = handle_compress(text)
        assert "combined" in result["strategy"]

    def test_empty_text(self):
        result = handle_compress("")
        assert result["original_tokens"] == 0

    def test_code_strategy(self):
        text = "# Comment\ndef foo():\n    return 1"
        result = handle_compress(text, "code")
        assert "# Comment" not in result["compressed_text"]


class TestHandleAnalyze:
    """Tests for analyze handler."""

    def test_basic_analyze(self):
        text = "Hello world this is a test"
        result = handle_analyze(text)
        assert "original_tokens" in result
        assert "strategies" in result

    def test_has_all_strategies(self):
        text = "Hello world"
        result = handle_analyze(text)
        for name in ["whitespace", "deduplicate", "code", "key_info", "combined"]:
            assert name in result["strategies"]

    def test_strategy_has_metrics(self):
        text = "Hello world"
        result = handle_analyze(text)
        for _name, data in result["strategies"].items():
            assert "tokens" in data
            assert "savings_pct" in data


class TestHandleMcpToolCall:
    """Tests for MCP tool call handler."""

    def test_compress_call(self):
        result = handle_mcp_tool_call(
            "textzip_compress",
            {"text": "Hello    world", "strategy": "whitespace"},
        )
        data = json.loads(result)
        assert "compressed_text" in data

    def test_analyze_call(self):
        result = handle_mcp_tool_call(
            "textzip_analyze",
            {"text": "Hello world"},
        )
        data = json.loads(result)
        assert "original_tokens" in data

    def test_unknown_tool(self):
        result = handle_mcp_tool_call(
            "unknown_tool",
            {},
        )
        data = json.loads(result)
        assert "error" in data
