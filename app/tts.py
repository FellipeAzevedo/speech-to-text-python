import argparse
import os
import subprocess
from pathlib import Path


def resolve_model_paths(voice_name: str, voice_dir: Path) -> tuple[Path, Path]:
    candidates = list(voice_dir.rglob(f"{voice_name}.onnx"))
    if not candidates:
        raise FileNotFoundError(
            f"Voice '{voice_name}' not found in '{voice_dir}'. "
            "Ensure the .onnx model is available."
        )
    model_path = candidates[0]
    config_path = Path(f"{model_path}.json")
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file '{config_path.name}' not found for voice '{voice_name}'."
        )
    return model_path, config_path


def build_command(
    *,
    text: str | None,
    text_file: Path | None,
    model_path: Path,
    config_path: Path,
    output_file: Path,
    speaker: int | None,
    length_scale: float | None,
    noise_scale: float | None,
    noise_w: float | None,
) -> list[str]:
    command: list[str] = [
        "piper",
        "--model",
        str(model_path),
        "--config",
        str(config_path),
        "--output_file",
        str(output_file),
    ]

    if text is not None:
        command.extend(["--text", text])
    elif text_file is not None:
        command.extend(["--input_file", str(text_file)])

    if speaker is not None:
        command.extend(["--speaker", str(speaker)])
    if length_scale is not None:
        command.extend(["--length_scale", str(length_scale)])
    if noise_scale is not None:
        command.extend(["--noise_scale", str(noise_scale)])
    if noise_w is not None:
        command.extend(["--noise_w", str(noise_w)])

    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Utility wrapper around the Piper CLI for running text-to-speech inside Docker."
        )
    )
    parser.add_argument(
        "--voice",
        required=True,
        help="Voice model name without extension (e.g., en_US-amy-medium).",
    )
    parser.add_argument(
        "--voice-dir",
        default=os.environ.get("PIPER_VOICE_DIR", "/voices"),
        type=Path,
        help="Directory containing Piper voice models (defaults to the PIPER_VOICE_DIR env var).",
    )
    text_group = parser.add_mutually_exclusive_group(required=True)
    text_group.add_argument("--text", help="Text to synthesize.")
    text_group.add_argument(
        "--text-file",
        type=Path,
        help="Path to a UTF-8 text file to synthesize.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output") / "tts.wav",
        help="Path for the generated WAV file (default: output/tts.wav).",
    )
    parser.add_argument(
        "--speaker",
        type=int,
        help="Optional speaker index for multi-speaker voices.",
    )
    parser.add_argument(
        "--length-scale",
        type=float,
        help="Speech length scaling factor.",
    )
    parser.add_argument(
        "--noise-scale",
        type=float,
        help="Noise scale factor controlling speech variability.",
    )
    parser.add_argument(
        "--noise-w",
        type=float,
        help="Phoneme noise value controlling prosody randomness.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    voice_dir: Path = args.voice_dir
    if not voice_dir.exists():
        raise SystemExit(f"Voice directory '{voice_dir}' does not exist.")

    model_path, config_path = resolve_model_paths(args.voice, voice_dir)

    output_file: Path = args.output
    output_file.parent.mkdir(parents=True, exist_ok=True)

    command = build_command(
        text=args.text,
        text_file=args.text_file,
        model_path=model_path,
        config_path=config_path,
        output_file=output_file,
        speaker=args.speaker,
        length_scale=args.length_scale,
        noise_scale=args.noise_scale,
        noise_w=args.noise_w,
    )

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc


if __name__ == "__main__":
    main()
