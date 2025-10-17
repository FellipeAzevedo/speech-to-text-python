"""Application configuration constants."""
from __future__ import annotations

from pathlib import Path
from typing import Final, List, Set

MODEL_NAME: Final[str] = "tts_models/multilingual/multi-dataset/xtts_v2"
DEFAULT_LANGUAGE: Final[str] = "pt"
DEFAULT_SPEAKER: Final[str] = "random"
DEFAULT_SAMPLE_RATE: Final[int] = 24000
SUPPORTED_SAMPLE_RATES: Final[Set[int]] = {24000}
DEFAULT_OUTPUT_FILENAME: Final[str] = "output.wav"
MAX_TEXT_LENGTH: Final[int] = 8000
SAFE_LANGUAGES_FALLBACK: Final[List[str]] = [
    "pt",
    "en",
    "es",
    "fr",
    "de",
    "it",
    "ru",
    "tr",
    "pl",
    "nl",
    "sv",
    "fi",
    "uk",
    "ja",
    "ko",
    "zh-cn",
    "ar",
]
SAFE_SPEAKERS_FALLBACK: Final[List[str]] = ["random"]
ALLOWED_PUNCTUATION: Final[str] = ".,;:!?\'\"()[]-–—%"

APP_DIR: Final[Path] = Path(__file__).resolve().parent
ROOT_DIR: Final[Path] = APP_DIR.parent
OUTPUT_DIR: Final[Path] = ROOT_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

