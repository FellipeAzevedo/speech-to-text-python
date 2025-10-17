"""Unit tests for text utilities."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from coqui_xtts_app.app.text_utils import sanitize_text


def test_sanitize_preserves_accents():
    text = "Olá, coração!"
    assert sanitize_text(text) == text


def test_sanitize_removes_emojis_and_symbols():
    text = "Olá 😀 — bem-vindo!"
    assert sanitize_text(text) == "Olá — bem-vindo!"


def test_sanitize_removes_html_tags():
    text = "<p>Texto</p> com <strong>marcação</strong>"
    assert sanitize_text(text) == "Texto com marcação"


def test_sanitize_normalizes_whitespace_and_ellipsis():
    text = "Olá   mundo.... ...."  # multiple spaces and long ellipsis
    assert sanitize_text(text) == "Olá mundo... ..."

