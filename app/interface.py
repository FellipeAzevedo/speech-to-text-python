from __future__ import annotations

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import gradio as gr

from .tts import build_command, resolve_model_paths
from .voice_data import VoiceMetadata, discover_voice_names, load_voice_metadata

VOICE_DIR = Path(os.environ.get("PIPER_VOICE_DIR", "/voices"))
OUTPUT_DIR = Path(os.environ.get("PIPER_OUTPUT_DIR", "/app/output"))

_VOICE_CACHE: dict[str, VoiceMetadata] = {}


def _get_voice_metadata(voice_name: str) -> VoiceMetadata:
    if voice_name not in _VOICE_CACHE:
        _VOICE_CACHE[voice_name] = load_voice_metadata(voice_name, VOICE_DIR)
    return _VOICE_CACHE[voice_name]


def _dropdown_update_from_mapping(mapping: dict[str, Any], default: str | None) -> gr.Dropdown.update:
    if not mapping:
        return gr.Dropdown.update(visible=False, choices=[], value=None)
    return gr.Dropdown.update(
        visible=True,
        choices=list(mapping.keys()),
        value=default if default in mapping else next(iter(mapping)),
    )


def _numeric_dropdown_update(metadata: VoiceMetadata, parameter: str) -> gr.Dropdown.update:
    numeric = metadata.numeric_parameters.get(parameter)
    if numeric is None:
        return gr.Dropdown.update(visible=False, choices=[], value=None)

    return gr.Dropdown.update(
        visible=True,
        choices=list(numeric.values.keys()),
        value=numeric.default_label,
    )


def _resolve_numeric_value(metadata: VoiceMetadata, parameter: str, label: str | None) -> float | None:
    if not label:
        return None
    numeric = metadata.numeric_parameters.get(parameter)
    if numeric is None:
        return None
    return numeric.values.get(label)


def _on_voice_change(voice_name: str) -> tuple[gr.Dropdown.update, gr.Dropdown.update, gr.Dropdown.update, gr.Dropdown.update]:
    metadata = _get_voice_metadata(voice_name)
    return (
        _dropdown_update_from_mapping(metadata.speaker_choices, metadata.default_speaker),
        _numeric_dropdown_update(metadata, "length_scale"),
        _numeric_dropdown_update(metadata, "noise_scale"),
        _numeric_dropdown_update(metadata, "noise_w"),
    )


def synthesize(
    text: str,
    voice_name: str,
    speaker_label: str | None,
    length_scale_label: str | None,
    noise_scale_label: str | None,
    noise_w_label: str | None,
    progress=gr.Progress(track_tqdm=False),
) -> tuple[str, str]:
    if not VOICE_DIR.exists():
        raise gr.Error(
            f"Diretório de vozes '{VOICE_DIR}' não encontrado. Atualize a variável PIPER_VOICE_DIR."
        )

    if not text or not text.strip():
        raise gr.Error("Informe um texto para síntese.")

    metadata = _get_voice_metadata(voice_name)

    speaker = metadata.speaker_choices.get(speaker_label) if speaker_label else None
    length_scale = _resolve_numeric_value(metadata, "length_scale", length_scale_label)
    noise_scale = _resolve_numeric_value(metadata, "noise_scale", noise_scale_label)
    noise_w = _resolve_numeric_value(metadata, "noise_w", noise_w_label)

    model_path, config_path = resolve_model_paths(voice_name, VOICE_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir=OUTPUT_DIR) as tmp_file:
        output_path = Path(tmp_file.name)

    command = build_command(
        text=text.strip(),
        text_file=None,
        model_path=model_path,
        config_path=config_path,
        output_file=output_path,
        speaker=speaker,
        length_scale=length_scale,
        noise_scale=noise_scale,
        noise_w=noise_w,
    )

    log_lines = ["[INFO] Iniciando síntese de áudio..."]
    progress(log_lines[-1])

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    start_time = time.perf_counter()

    try:
        while True:
            return_code = process.poll()
            elapsed = time.perf_counter() - start_time
            log_line = f"[INFO] Tempo decorrido: {elapsed:.1f}s"
            log_lines.append(log_line)
            progress(log_line)
            if return_code is not None:
                stdout_data, _ = process.communicate()
                if stdout_data:
                    for raw_line in stdout_data.splitlines():
                        cleaned = raw_line.strip()
                        if cleaned:
                            log_lines.append(cleaned)
                if return_code != 0:
                    raise gr.Error("Falha durante a síntese. Consulte os logs para detalhes.")
                break
            time.sleep(1.0)
    except Exception:
        process.kill()
        raise

    total_time = time.perf_counter() - start_time
    log_lines.append(
        f"[INFO] Síntese concluída em {total_time:.2f}s. Arquivo salvo em '{output_path.name}'."
    )

    return str(output_path), "\n".join(log_lines)


def build_interface() -> gr.Blocks:
    voice_choices = discover_voice_names(VOICE_DIR) if VOICE_DIR.exists() else []
    default_voice = voice_choices[0] if voice_choices else None

    metadata: VoiceMetadata | None = None
    initialization_warning: str | None = None

    if default_voice is not None:
        try:
            metadata = _get_voice_metadata(default_voice)
        except FileNotFoundError as error:
            metadata = VoiceMetadata(
                name=default_voice,
                speaker_choices={},
                default_speaker=None,
                numeric_parameters={},
            )
            initialization_warning = str(error)

    if metadata is not None:
        speaker_choices = list(metadata.speaker_choices.keys())
        speaker_value = metadata.default_speaker if speaker_choices else None
        speaker_visible = bool(speaker_choices)
        length_choices = list(
            metadata.numeric_parameters["length_scale"].values.keys()
        ) if "length_scale" in metadata.numeric_parameters else []
        length_value = (
            metadata.numeric_parameters["length_scale"].default_label
            if length_choices
            else None
        )
        length_visible = bool(length_choices)
        noise_choices = list(
            metadata.numeric_parameters["noise_scale"].values.keys()
        ) if "noise_scale" in metadata.numeric_parameters else []
        noise_value = (
            metadata.numeric_parameters["noise_scale"].default_label
            if noise_choices
            else None
        )
        noise_visible = bool(noise_choices)
        noise_w_choices = list(
            metadata.numeric_parameters["noise_w"].values.keys()
        ) if "noise_w" in metadata.numeric_parameters else []
        noise_w_value = (
            metadata.numeric_parameters["noise_w"].default_label
            if noise_w_choices
            else None
        )
        noise_w_visible = bool(noise_w_choices)
    else:
        speaker_choices = []
        speaker_value = None
        speaker_visible = False
        length_choices = []
        length_value = None
        length_visible = False
        noise_choices = []
        noise_value = None
        noise_visible = False
        noise_w_choices = []
        noise_w_value = None
        noise_w_visible = False

    with gr.Blocks(title="Piper TTS Local") as demo:
        gr.Markdown(
            """
            # Piper TTS Local
            Converta texto em fala utilizando modelos Piper locais. As opções são carregadas automaticamente a partir das
            configurações de cada voz.
            """
        )

        with gr.Row():
            voice_dropdown = gr.Dropdown(
                label="Modelo de voz",
                choices=voice_choices,
                value=default_voice,
                interactive=bool(voice_choices),
                allow_custom_value=False,
            )
            speaker_dropdown = gr.Dropdown(
                label="Falante",
                choices=speaker_choices,
                value=speaker_value,
                visible=speaker_visible,
                allow_custom_value=False,
            )

        with gr.Row():
            length_scale_dropdown = gr.Dropdown(
                label="Length scale",
                choices=length_choices,
                value=length_value,
                visible=length_visible,
                allow_custom_value=False,
            )
            noise_scale_dropdown = gr.Dropdown(
                label="Noise scale",
                choices=noise_choices,
                value=noise_value,
                visible=noise_visible,
                allow_custom_value=False,
            )
            noise_w_dropdown = gr.Dropdown(
                label="Noise W",
                choices=noise_w_choices,
                value=noise_w_value,
                visible=noise_w_visible,
                allow_custom_value=False,
            )

        text_input = gr.Textbox(
            label="Texto para sintetizar",
            lines=4,
            placeholder="Digite aqui o texto a ser convertido em fala...",
        )

        generate_button = gr.Button("Gerar áudio", variant="primary")

        audio_output = gr.Audio(label="Resultado", type="filepath")
        log_output = gr.Textbox(label="Logs", lines=12)

        voice_dropdown.change(
            fn=_on_voice_change,
            inputs=voice_dropdown,
            outputs=[
                speaker_dropdown,
                length_scale_dropdown,
                noise_scale_dropdown,
                noise_w_dropdown,
            ],
        )

        generate_button.click(
            fn=synthesize,
            inputs=[
                text_input,
                voice_dropdown,
                speaker_dropdown,
                length_scale_dropdown,
                noise_scale_dropdown,
                noise_w_dropdown,
            ],
            outputs=[audio_output, log_output],
        )

        if not voice_choices:
            gr.Markdown(
                f"⚠️ Nenhum modelo encontrado em `{VOICE_DIR}`. Monte o diretório de vozes antes de iniciar a síntese.",
                elem_id="warning",
            )
        elif initialization_warning:
            gr.Markdown(f"⚠️ {initialization_warning}")

    return demo


def main() -> None:
    demo = build_interface()
    demo.queue()
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "7860")),
        share=False,
    )


if __name__ == "__main__":
    main()
