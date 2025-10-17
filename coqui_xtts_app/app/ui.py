"""Gradio interface for the Coqui XTTS application."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

import gradio as gr

from . import config, main
from .logging_utils import setup_logging
from .text_utils import read_text_file, sanitize_text

logger = logging.getLogger(__name__)


def _load_languages() -> list[str]:
    try:
        return main.get_available_languages()
    except Exception as exc:  # pragma: no cover - runtime dependent
        logger.error("Não foi possível obter idiomas do modelo: %s", exc)
        return config.SAFE_LANGUAGES_FALLBACK


def _load_speakers() -> list[str]:
    try:
        speakers = main.get_available_speakers()
        return speakers or config.SAFE_SPEAKERS_FALLBACK
    except Exception as exc:  # pragma: no cover - runtime dependent
        logger.error("Não foi possível obter locutores: %s", exc)
        return config.SAFE_SPEAKERS_FALLBACK


def _extract_text(text_file: Optional[gr.File], direct_text: str) -> str:
    if text_file:
        path = Path(text_file.name)
        return read_text_file(path)
    if direct_text:
        return direct_text
    raise ValueError("Envie um arquivo .txt ou informe um texto no campo correspondente.")


def generate_audio(
    text_file: Optional[gr.File],
    direct_text: str,
    language: str,
    speaker: Optional[str],
    speaker_wav: Optional[gr.File],
    sample_rate: Union[str, int],
    split_sentences: bool,
    output_filename: str,
) -> tuple[Optional[str], Optional[str], str]:
    """Callback executed when the user clicks the generate button."""

    progress = gr.Progress(track_tqdm=True)
    progress(0.1, "Preparando dados...")

    try:
        raw_text = _extract_text(text_file, direct_text)
        sanitized = sanitize_text(raw_text)
        if not sanitized:
            raise ValueError("O texto ficou vazio após o saneamento.")

        if not output_filename.lower().endswith(".wav"):
            output_filename = f"{output_filename}.wav"

        output_path = config.OUTPUT_DIR / output_filename

        speaker_wav_path: Optional[str] = None
        if speaker_wav:
            speaker_wav_path = speaker_wav.name

        sr_value = int(sample_rate) if sample_rate else config.DEFAULT_SAMPLE_RATE

        progress(0.5, "Gerando áudio...")
        audio_path = main.synthesize_to_wav(
            text=sanitized,
            lang=language,
            output_path=output_path,
            speaker_wav=speaker_wav_path,
            speaker=speaker,
            sample_rate=sr_value,
            split_sentences=split_sentences,
        )
        progress(1.0, "Concluído!")
        message = f"Áudio gerado com sucesso: {audio_path}"
        return audio_path, audio_path, message
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Falha na geração do áudio: %s", exc)
        return None, None, f"Erro: {exc}"


def build_interface() -> gr.Blocks:
    setup_logging()
    languages = _load_languages()
    speakers = _load_speakers()

    with gr.Blocks(title="Coqui XTTS v2 - Sintetizador de Voz") as demo:
        gr.Markdown(
            """# Coqui XTTS v2
Forneça um arquivo `.txt` ou escreva um texto curto para gerar áudio utilizando o modelo XTTS v2."""
        )

        with gr.Row():
            text_file_input = gr.File(label="Arquivo .txt", file_types=[".txt"], interactive=True)
            direct_text_input = gr.Textbox(
                label="Texto opcional",
                lines=5,
                placeholder="Cole aqui um texto curto se não enviar arquivo.",
            )

        with gr.Row():
            language_dropdown = gr.Dropdown(
                choices=languages,
                value=config.DEFAULT_LANGUAGE,
                label="Idioma",
                allow_custom_value=False,
            )
            speaker_dropdown = gr.Dropdown(
                choices=speakers,
                value=speakers[0] if speakers else config.DEFAULT_SPEAKER,
                label="Voz padrão",
                allow_custom_value=False,
            )
            sample_rate_dropdown = gr.Dropdown(
                choices=[str(sr) for sr in sorted(config.SUPPORTED_SAMPLE_RATES)],
                value=str(config.DEFAULT_SAMPLE_RATE),
                label="Sample rate",
                allow_custom_value=False,
            )

        with gr.Row():
            speaker_wav_input = gr.File(label="Amostra de voz (opcional)", file_types=[".wav"])
            split_sentences_checkbox = gr.Checkbox(
                label="Dividir sentenças automaticamente",
                value=False,
            )
            output_filename_input = gr.Textbox(
                label="Nome do arquivo de saída",
                value=config.DEFAULT_OUTPUT_FILENAME,
            )

        generate_button = gr.Button("Gerar Áudio")
        audio_output = gr.Audio(label="Pré-escuta", autoplay=False)
        file_output = gr.File(label="Download do áudio")
        status_output = gr.Textbox(label="Status", interactive=False)

        generate_button.click(
            fn=generate_audio,
            inputs=[
                text_file_input,
                direct_text_input,
                language_dropdown,
                speaker_dropdown,
                speaker_wav_input,
                sample_rate_dropdown,
                split_sentences_checkbox,
                output_filename_input,
            ],
            outputs=[audio_output, file_output, status_output],
        )

    demo.queue()
    return demo


def main() -> None:
    demo = build_interface()
    demo.launch()


if __name__ == "__main__":  # pragma: no cover
    main()

