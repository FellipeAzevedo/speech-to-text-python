"""Utilities for preparing text for synthesis."""
from __future__ import annotations

import html
import logging
import re
import unicodedata
from pathlib import Path
from typing import Optional

from . import config

logger = logging.getLogger(__name__)

_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_MULTI_DOTS_PATTERN = re.compile(r"\.{4,}")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def read_text_file(path: Path) -> str:
    """Read a UTF-8 encoded text file.

    Args:
        path: Path to the text file.

    Returns:
        File content as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        UnicodeDecodeError: If the file is not UTF-8 decodable.
        OSError: For other IO issues.
    """

    with path.open("r", encoding="utf-8") as file:
        return file.read()


def sanitize_text(text: str) -> str:
    """Clean input text while preserving intelligibility.

    The cleaning routine removes emojis, control characters, HTML tags and
    unsupported punctuation while keeping diacritics, letters and safe
    punctuation intact.

    Args:
        text: Raw input text.

    Returns:
        Sanitized text suitable for synthesis.
    """

    if not text:
        return ""

    # Decode HTML entities if present.
    decoded_text = html.unescape(text)
    without_tags = _HTML_TAG_PATTERN.sub(" ", decoded_text)
    normalized = unicodedata.normalize("NFC", without_tags)

    safe_chars: list[str] = []
    for char in normalized:
        category = unicodedata.category(char)
        if category.startswith("C"):
            # Control characters are removed entirely.
            continue
        if category.startswith(("L", "N")):
            safe_chars.append(char)
            continue
        if char in config.ALLOWED_PUNCTUATION:
            safe_chars.append(char)
            continue
        if category.startswith("P") and char in {"…"}:
            safe_chars.append("...")
            continue
        if category.startswith("Z"):
            safe_chars.append(" ")
            continue
        # Ignore any other symbols such as emojis.

    cleaned = "".join(safe_chars)
    cleaned = _MULTI_DOTS_PATTERN.sub("...", cleaned)
    cleaned = cleaned.replace("…", "...")
    cleaned = _WHITESPACE_PATTERN.sub(" ", cleaned).strip()
    return cleaned


def ensure_text_within_limit(text: str, limit: Optional[int] = None) -> None:
    """Validate that text length does not exceed the configured limit.

    Args:
        text: Text to validate.
        limit: Maximum allowed length. Defaults to ``config.MAX_TEXT_LENGTH``.

    Raises:
        ValueError: If the text length is greater than the limit.
    """

    max_length = limit or config.MAX_TEXT_LENGTH
    if len(text) > max_length:
        logger.error(
            "Input text length %s exceeds limit of %s characters.", len(text), max_length
        )
        raise ValueError(
            "O texto é muito grande para uma única síntese. "
            "Considere dividir o conteúdo em partes menores."
        )

