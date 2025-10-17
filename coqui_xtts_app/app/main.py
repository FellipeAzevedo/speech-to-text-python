"""Core synthesis routines for the Coqui XTTS application."""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, List, Optional

from . import config
from .text_utils import ensure_text_within_limit, sanitize_text

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover
    from TTS.api import TTS as TTSModel
else:
    TTSModel = Any

_MODEL_LOCK = threading.Lock()
_TTS_INSTANCE: Optional[TTSModel] = None
_LANGUAGES_CACHE: Optional[List[str]] = None
_SPEAKERS_CACHE: Optional[List[str]] = None


def get_tts() -> TTSModel:
    """Load and cache the TTS model instance."""

    global _TTS_INSTANCE
    if _TTS_INSTANCE is None:
        with _MODEL_LOCK:
            if _TTS_INSTANCE is None:
                try:
                    logger.info("Carregando modelo %s...", config.MODEL_NAME)
                    from TTS.api import TTS  # noqa: WPS433

                    _TTS_INSTANCE = TTS(model_name=config.MODEL_NAME, progress_bar=True)
                except Exception as exc:  # pragma: no cover - depends on runtime env
                    logger.error("Falha ao carregar o modelo: %s", exc)
                    raise RuntimeError(
                        "Não foi possível carregar o modelo de voz. "
                        "Verifique a instalação das dependências e tente novamente."
                    ) from exc
    return _TTS_INSTANCE


def _extract_languages(model: TTSModel) -> List[str]:
    languages: Iterable[str]
    if hasattr(model, "languages") and model.languages:
        languages = list(model.languages)
    else:
        languages = config.SAFE_LANGUAGES_FALLBACK
    return sorted(set(lang.lower() for lang in languages))


def _extract_speakers(model: TTSModel) -> List[str]:
    speakers: Iterable[str]
    if hasattr(model, "speakers") and model.speakers:
        speakers = list(model.speakers)
    else:
        speakers = config.SAFE_SPEAKERS_FALLBACK
    return sorted(set(str(speaker) for speaker in speakers))


def get_available_languages() -> List[str]:
    """Return cached list of supported languages."""

    global _LANGUAGES_CACHE
    if _LANGUAGES_CACHE is None:
        model = get_tts()
        _LANGUAGES_CACHE = _extract_languages(model)
    return _LANGUAGES_CACHE


def get_available_speakers() -> List[str]:
    """Return cached list of supported speakers."""

    global _SPEAKERS_CACHE
    if _SPEAKERS_CACHE is None:
        model = get_tts()
        _SPEAKERS_CACHE = _extract_speakers(model)
    return _SPEAKERS_CACHE


def synthesize_to_wav(
    text: str,
    lang: str,
    output_path: str | Path,
    speaker_wav: Optional[str] = None,
    speaker: Optional[str] = None,
    sample_rate: Optional[int] = None,
    split_sentences: bool = False,
) -> str:
    """Synthesize text into a WAV file using XTTS v2.

    Args:
        text: Raw input text.
        lang: Target language identifier.
        output_path: Destination path for the generated WAV file.
        speaker_wav: Optional path to a speaker reference audio file.
        speaker: Optional speaker id/name for multi-speaker models.
        sample_rate: Desired sample rate. Must be supported by the model.
        split_sentences: Whether to split sentences during synthesis.

    Returns:
        Path to the generated WAV file.

    Raises:
        ValueError: If validation fails.
        RuntimeError: If synthesis fails.
    """

    sanitized_text = sanitize_text(text)
    if not sanitized_text:
        raise ValueError("O texto fornecido ficou vazio após o saneamento.")

    ensure_text_within_limit(sanitized_text)

    available_languages = get_available_languages()
    lang_lower = lang.lower()
    if lang_lower not in available_languages:
        raise ValueError(
            "Idioma '%s' não é suportado. Idiomas disponíveis: %s"
            % (lang, ", ".join(available_languages))
        )

    if sample_rate is not None and sample_rate not in config.SUPPORTED_SAMPLE_RATES:
        raise ValueError(
            "Sample rate %s não é suportado pelo modelo. Utilize %s Hz."
            % (sample_rate, config.DEFAULT_SAMPLE_RATE)
        )

    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    model = get_tts()

    speaker_wav_path: Optional[str] = None
    if speaker_wav:
        wav_path = Path(speaker_wav).expanduser().resolve()
        if not wav_path.exists():
            raise ValueError(f"Arquivo de voz de referência não encontrado: {speaker_wav}")
        speaker_wav_path = str(wav_path)

    selected_speaker: Optional[str] = None
    if speaker_wav_path is None:
        available_speakers = get_available_speakers()
        if speaker and speaker in available_speakers:
            selected_speaker = speaker
        elif speaker:
            logger.warning("Speaker '%s' não encontrado. Usando fallback.", speaker)
            selected_speaker = config.DEFAULT_SPEAKER
        else:
            selected_speaker = config.DEFAULT_SPEAKER

    try:
        logger.info("Gerando áudio em %s", output)
        model.tts_to_file(
            text=sanitized_text,
            file_path=str(output),
            language=lang_lower,
            speaker_wav=speaker_wav_path,
            speaker=selected_speaker,
            split_sentences=split_sentences,
        )
    except Exception as exc:  # pragma: no cover - depends on backend
        logger.error("Falha na síntese de áudio: %s", exc)
        raise RuntimeError(
            "Ocorreu um erro durante a síntese de áudio. Consulte os logs para mais detalhes."
        ) from exc

    if not output.exists():
        raise RuntimeError("A síntese foi concluída, mas o arquivo de saída não foi encontrado.")

    return str(output)

