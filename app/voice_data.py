from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .tts import resolve_model_paths


@dataclass(frozen=True)
class NumericChoices:
    """Represents validated choices for a numeric inference parameter."""

    values: dict[str, float]
    default_label: str


@dataclass(frozen=True)
class VoiceMetadata:
    """Metadata describing which options are available for a Piper voice."""

    name: str
    speaker_choices: dict[str, int]
    default_speaker: str | None
    numeric_parameters: dict[str, NumericChoices]


def discover_voice_names(voice_dir: Path) -> list[str]:
    """Return the list of available voice names (without extensions)."""

    voices = sorted({voice.stem for voice in voice_dir.rglob("*.onnx")})
    return voices


def load_voice_metadata(voice_name: str, voice_dir: Path) -> VoiceMetadata:
    _, config_path = resolve_model_paths(voice_name, voice_dir)
    with config_path.open("r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)

    return parse_voice_config(voice_name, config_data)


def parse_voice_config(voice_name: str, config: dict[str, Any]) -> VoiceMetadata:
    speaker_choices, default_speaker = _extract_speaker_choices(config)
    numeric_parameters: dict[str, NumericChoices] = {}

    for parameter_name in ("length_scale", "noise_scale", "noise_w"):
        numeric_choice = _extract_numeric_choices(config, parameter_name)
        if numeric_choice is not None:
            numeric_parameters[parameter_name] = numeric_choice

    return VoiceMetadata(
        name=voice_name,
        speaker_choices=speaker_choices,
        default_speaker=default_speaker,
        numeric_parameters=numeric_parameters,
    )


def _extract_speaker_choices(config: dict[str, Any]) -> tuple[dict[str, int], str | None]:
    if isinstance(config.get("speaker_id_map"), dict) and config["speaker_id_map"]:
        items = sorted(
            ((str(name), int(idx)) for name, idx in config["speaker_id_map"].items()),
            key=lambda item: item[1],
        )
        speaker_choices = {label: value for label, value in items}
        default_label = next(iter(speaker_choices))
        return speaker_choices, default_label

    num_speakers = config.get("num_speakers")
    if isinstance(num_speakers, int) and num_speakers > 1:
        speaker_choices = {f"Speaker {idx}": idx for idx in range(num_speakers)}
        default_label = "Speaker 0"
        return speaker_choices, default_label

    return {}, None


def _extract_numeric_choices(config: dict[str, Any], parameter_name: str) -> NumericChoices | None:
    inference = config.get("inference")
    if not isinstance(inference, dict):
        return None

    default_value = inference.get(parameter_name)
    if not isinstance(default_value, (int, float)):
        return None

    values = _generate_numeric_variations(float(default_value))
    labels = [
        _format_float(value)
        for value in sorted({round(option, 5) for option in values})
    ]

    value_map = {label: float(label) for label in labels}
    default_label = _format_float(float(default_value))

    if default_label not in value_map:
        value_map[default_label] = float(default_value)
        labels.append(default_label)

    # Preserve order by recreating mapping with labels sequence
    ordered_value_map = {label: value_map[label] for label in labels}

    return NumericChoices(values=ordered_value_map, default_label=default_label)


def _generate_numeric_variations(default: float) -> list[float]:
    factors = [0.75, 0.9, 1.0, 1.1, 1.25]
    return [max(0.0, round(default * factor, 5)) for factor in factors]


def _format_float(value: float) -> str:
    formatted = f"{value:.3f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted or "0"
