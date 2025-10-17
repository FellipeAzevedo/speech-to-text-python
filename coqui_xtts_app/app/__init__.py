"""Coqui XTTS application package."""

from .main import synthesize_to_wav, get_available_languages, get_available_speakers

__all__ = [
    "synthesize_to_wav",
    "get_available_languages",
    "get_available_speakers",
]
