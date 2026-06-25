"""Tests for compression strategies."""

import pytest
from textzip.strategies import (
    Tokenizer,
    CompressionResult,
    WhitespaceNormalizer,
    Deduplicator,
    CodeFormatter,
    KeyExtractor,
    CombinedCompressor,
)


class TestTokenizer:
    """Tests for the Tokenizer class."""

    def test_count_tokens_basic(self):
        text = "Hello world this is a test"
        tokens = Tokenizer.count_tokens(text)
        assert tokens > 0
        # Rough check: ~4 chars per token
        assert tokens == max(1, len(text) // 4)

    def test_count_tokens_empty(self):
        assert Tokenizer.count_tokens("") == 0
        assert Tokenizer.count_tokens("   ") == 0
        assert Tokenizer.count_tokens("\n\n") == 0

    def test_count_tokens_long_text(self):
        text = "The quick brown fox jumps over the lazy dog. " * 10
        tokens = Tokenizer.count_tokens(text)
        assert tokens > 0
        # ~4 chars per token is the approximation
        assert tokens == max(1, len(text) // 4)


class TestWhitespaceNormalizer:
    """Tests for WhitespaceNormalizer strategy."""

    @pytest.fixture
    def strategy(self):
        return WhitespaceNormalizer()

    def test_collapse_spaces(self, strategy):
        text = "Hello    world    test"
        result = strategy.compress(text)
        assert "Hello world test" == result.compressed_text

    def test_collapse_newlines(self, strategy):
        text = "Line 1\n\n\n\nLine 2"
        result = strategy.compress(text)
        assert "\n\n" in result.compressed_text
        assert "\n\n\n" not in result.compressed_text

    def test_strip_whitespace(self, strategy):
        text = "  hello  "
        result = strategy.compress(text)
        assert result.compressed_text == "hello"

    def test_savings_positive(self, strategy):
        text = "Hello    world    this    has    extra    whitespace"
        result = strategy.compress(text)
        assert result.savings_pct > 0
        assert result.compressed_tokens < result.original_tokens

    def test_empty_text(self, strategy):
        result = strategy.compress("")
        assert result.original_tokens == 0
        assert result.compressed_tokens == 0

    def test_no_change_needed(self, strategy):
        text = "Already clean text"
        result = strategy.compress(text)
        assert result.compressed_text == text

    def test_name(self, strategy):
        assert strategy.name == "whitespace"


class TestDeduplicator:
    """Tests for Deduplicator strategy."""

    @pytest.fixture
    def strategy(self):
        return Deduplicator()

    def test_remove_duplicate_lines(self, strategy):
        text = "Line 1\nLine 2\nLine 1\nLine 3\nLine 2"
        result = strategy.compress(text)
        # Should preserve order, remove duplicates
        lines = result.compressed_text.split("\n")
        assert len(lines) == len(set(lines))
        assert "Line 1" in result.compressed_text
        assert "Line 2" in result.compressed_text
        assert "Line 3" in result.compressed_text

    def test_preserve_order(self, strategy):
        text = "A\nB\nC\nA\nB"
        result = strategy.compress(text)
        lines = result.compressed_text.split("\n")
        assert lines == ["A", "B", "C"]

    def test_skip_empty_lines(self, strategy):
        text = "Line 1\n\nLine 2\n\nLine 1"
        result = strategy.compress(text)
        # Empty lines are skipped (stripped == "")
        assert result.compressed_text == "Line 1\nLine 2"

    def test_savings_positive(self, strategy):
        text = "Same line\nSame line\nSame line\n" * 10
        result = strategy.compress(text)
        assert result.savings_pct > 0

    def test_no_duplicates(self, strategy):
        text = "A\nB\nC\nD\nE"
        result = strategy.compress(text)
        assert result.compressed_text == text

    def test_name(self, strategy):
        assert strategy.name == "deduplicate"


class TestCodeFormatter:
    """Tests for CodeFormatter strategy."""

    @pytest.fixture
    def strategy(self):
        return CodeFormatter()

    def test_remove_python_comments(self, strategy):
        text = """# This is a comment
def hello():
    # Another comment
    print("hello")  # inline comment
"""
        result = strategy.compress(text)
        assert "# This is a comment" not in result.compressed_text
        assert "def hello():" in result.compressed_text
        assert 'print("hello")' in result.compressed_text

    def test_remove_block_comments(self, strategy):
        text = """/* This is a block comment
that spans multiple lines */
function hello() {}
"""
        result = strategy.compress(text)
        assert "block comment" not in result.compressed_text
        assert "function hello()" in result.compressed_text

    def test_remove_blank_lines(self, strategy):
        text = "line1\n\n\n\nline2"
        result = strategy.compress(text)
        assert "\n\n\n" not in result.compressed_text

    def test_preserve_code(self, strategy):
        text = "def foo():\n    return 42\n\nclass Bar:\n    pass"
        result = strategy.compress(text)
        assert "def foo():" in result.compressed_text
        assert "return 42" in result.compressed_text

    def test_savings_positive(self, strategy):
        text = """# Comment
# Another comment

def foo():
    # Inline comment
    x = 1

# More comments
    return x
"""
        result = strategy.compress(text)
        assert result.savings_pct > 0

    def test_name(self, strategy):
        assert strategy.name == "code"


class TestKeyExtractor:
    """Tests for KeyExtractor strategy."""

    @pytest.fixture
    def strategy(self):
        return KeyExtractor()

    def test_extract_headers(self, strategy):
        text = "# Header 1\nSome text\n## Header 2\nMore text"
        result = strategy.compress(text)
        assert "# Header 1" in result.compressed_text
        assert "## Header 2" in result.compressed_text

    def test_extract_key_value_pairs(self, strategy):
        text = "name: John\ndescription: A person\nage: 30"
        result = strategy.compress(text)
        assert "name: John" in result.compressed_text
        assert "description: A person" in result.compressed_text

    def test_extract_first_sentences(self, strategy):
        text = "This is a long paragraph with many words that should be kept because it is meaningful."
        result = strategy.compress(text)
        assert "This is a long paragraph" in result.compressed_text

    def test_savings_positive(self, strategy):
        text = """# Introduction
This is a long paragraph with lots of filler text that doesn't add much value to the document.

# Section 2
More filler text that could be compressed without losing important information.

# Section 3
Even more filler text here.
"""
        result = strategy.compress(text)
        assert result.savings_pct > 0

    def test_name(self, strategy):
        assert strategy.name == "key_info"


class TestCombinedCompressor:
    """Tests for CombinedCompressor."""

    def test_default_pipeline(self):
        compressor = CombinedCompressor()
        assert len(compressor.strategies) == 3

    def test_custom_pipeline(self):
        compressor = CombinedCompressor(
            strategies=[WhitespaceNormalizer(), Deduplicator()]
        )
        assert len(compressor.strategies) == 2

    def test_combined_savings(self):
        compressor = CombinedCompressor()
        text = "Hello    world    hello    world\n\n\n\nHello    world"
        result = compressor.compress(text)
        assert result.savings_pct > 0
        assert result.strategy.startswith("combined")

    def test_combined_with_code(self):
        compressor = CombinedCompressor(
            strategies=[CodeFormatter()]
        )
        text = "# Comment\ndef foo():\n    # Another\n    return 1"
        result = compressor.compress(text)
        assert result.savings_pct > 0

    def test_empty_text(self):
        compressor = CombinedCompressor()
        result = compressor.compress("")
        assert result.original_tokens == 0
        assert result.compressed_tokens == 0

    def test_result_dataclass(self):
        compressor = CombinedCompressor()
        text = "Test text"
        result = compressor.compress(text)
        assert isinstance(result, CompressionResult)
        assert hasattr(result, "original_text")
        assert hasattr(result, "compressed_text")
        assert hasattr(result, "savings_pct")
