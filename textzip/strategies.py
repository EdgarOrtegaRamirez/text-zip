"""Core compression strategies for TextZip."""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CompressionResult:
    """Result of a compression operation."""
    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    strategy: str
    savings_pct: float = 0.0

    def __post_init__(self) -> None:
        if self.original_tokens > 0:
            self.savings_pct = round(
                (1 - self.compressed_tokens / self.original_tokens) * 100, 2
            )
        else:
            self.savings_pct = 0.0


class CompressionStrategy(ABC):
    """Base class for all compression strategies."""

    @abstractmethod
    def compress(self, text: str) -> CompressionResult:
        """Compress the given text and return the result."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this strategy."""
        ...


class Tokenizer:
    """Simple token counter based on whitespace + punctuation splitting."""

    @staticmethod
    def count_tokens(text: str) -> int:
        """Estimate token count using a simple whitespace-based heuristic."""
        if not text or not text.strip():
            return 0
        # Rough approximation: ~4 chars per token for English
        return max(1, len(text) // 4)


class WhitespaceNormalizer(CompressionStrategy):
    """Normalize whitespace: collapse multiple spaces/newlines into single."""

    @property
    def name(self) -> str:
        return "whitespace"

    def compress(self, text: str) -> CompressionResult:
        original_tokens = Tokenizer.count_tokens(text)
        # Collapse multiple whitespace chars into single space
        compressed = re.sub(r"[ \t]+", " ", text)
        # Collapse multiple newlines into double newline (paragraph break)
        compressed = re.sub(r"\n{3,}", "\n\n", compressed)
        # Strip leading/trailing whitespace
        compressed = compressed.strip()
        compressed_tokens = Tokenizer.count_tokens(compressed)
        logger.debug(
            "Whitespace: %d -> %d tokens (%.1f%% savings)",
            original_tokens,
            compressed_tokens,
            (1 - compressed_tokens / original_tokens) * 100 if original_tokens else 0,
        )
        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy=self.name,
        )


class Deduplicator(CompressionStrategy):
    """Remove duplicate lines while preserving order."""

    @property
    def name(self) -> str:
        return "deduplicate"

    def compress(self, text: str) -> CompressionResult:
        original_tokens = Tokenizer.count_tokens(text)
        lines = text.split("\n")
        seen: set[str] = set()
        unique_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped and stripped not in seen:
                seen.add(stripped)
                unique_lines.append(line)
        compressed = "\n".join(unique_lines)
        compressed_tokens = Tokenizer.count_tokens(compressed)
        logger.debug(
            "Dedup: %d -> %d tokens (%.1f%% savings)",
            original_tokens,
            compressed_tokens,
            (1 - compressed_tokens / original_tokens) * 100 if original_tokens else 0,
        )
        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy=self.name,
        )


class CodeFormatter(CompressionStrategy):
    """Compress code by removing comments, blank lines, and extra whitespace."""

    @property
    def name(self) -> str:
        return "code"

    def compress(self, text: str) -> CompressionResult:
        original_tokens = Tokenizer.count_tokens(text)
        lines = text.split("\n")
        compressed_lines: list[str] = []
        in_block_comment = False

        for line in lines:
            stripped = line.strip()

            # Handle block comments (/* ... */)
            if in_block_comment:
                if "*/" in stripped:
                    in_block_comment = False
                continue

            if stripped.startswith("/*"):
                if "*/" not in stripped[2:]:
                    in_block_comment = True
                continue

            # Skip single-line comments
            if stripped.startswith(("//", "#", ";", "--", "*")):
                continue

            # Skip blank lines
            if not stripped:
                continue

            compressed_lines.append(line)

        compressed = "\n".join(compressed_lines)
        compressed_tokens = Tokenizer.count_tokens(compressed)
        logger.debug(
            "Code: %d -> %d tokens (%.1f%% savings)",
            original_tokens,
            compressed_tokens,
            (1 - compressed_tokens / original_tokens) * 100 if original_tokens else 0,
        )
        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy=self.name,
        )


class KeyExtractor(CompressionStrategy):
    """Extract key information: headers, first sentences, key-value pairs."""

    @property
    def name(self) -> str:
        return "key_info"

    def compress(self, text: str) -> CompressionResult:
        original_tokens = Tokenizer.count_tokens(text)
        lines = text.split("\n")
        extracted: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Headers and titles
            if re.match(r"^(#{1,6}\s|.+\s*:\s*.+|- \[x\]|\* \[x\])", stripped):
                extracted.append(stripped)
                continue

            # First sentence of paragraphs
            if (not extracted or extracted[-1] != "___NEW_PARA___") and len(stripped) > 20:  # Only meaningful sentences
                extracted.append(stripped)
                extracted.append("___NEW_PARA___")
                continue

            # Key-value pairs
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*[:=]", stripped):
                extracted.append(stripped)

        # Remove the marker
        extracted = [e for e in extracted if e != "___NEW_PARA___"]
        compressed = "\n".join(extracted)
        compressed_tokens = Tokenizer.count_tokens(compressed)
        logger.debug(
            "KeyInfo: %d -> %d tokens (%.1f%% savings)",
            original_tokens,
            compressed_tokens,
            (1 - compressed_tokens / original_tokens) * 100 if original_tokens else 0,
        )
        return CompressionResult(
            original_text=text,
            compressed_text=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy=self.name,
        )


class CombinedCompressor:
    """Apply multiple compression strategies in sequence for maximum savings."""

    def __init__(
        self,
        strategies: list[CompressionStrategy] | None = None,
    ) -> None:
        if strategies is None:
            # Default pipeline: whitespace -> dedup -> key extraction
            self.strategies = [
                WhitespaceNormalizer(),
                Deduplicator(),
                KeyExtractor(),
            ]
        else:
            self.strategies = strategies

    def compress(self, text: str) -> CompressionResult:
        """Apply all strategies in sequence."""
        result = CompressionResult(
            original_text=text,
            compressed_text=text,
            original_tokens=Tokenizer.count_tokens(text),
            compressed_tokens=Tokenizer.count_tokens(text),
            strategy="combined",
        )

        for strategy in self.strategies:
            result = CompressionResult(
                original_text=result.original_text,
                compressed_text=strategy.compress(result.compressed_text).compressed_text,
                original_tokens=result.original_tokens,
                compressed_tokens=Tokenizer.count_tokens(
                    strategy.compress(result.compressed_text).compressed_text
                ),
                strategy=f"{result.strategy}+{strategy.name}",
            )

        return result
