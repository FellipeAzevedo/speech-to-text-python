"""Command-line interface for the Coqui XTTS application."""
from __future__ import annotations

import argparse
import logging
import sys
import traceback
from pathlib import Path

from . import config, main
from .logging_utils import setup_logging
from .text_utils import read_text_file

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Síntese de voz utilizando Coqui XTTS v2",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--text-file", required=True, help="Caminho para o arquivo .txt")
    parser.add_argument("--lang", default=config.DEFAULT_LANGUAGE, help="Idioma alvo")
    parser.add_argument(
        "--output",
        default=config.OUTPUT_DIR / config.DEFAULT_OUTPUT_FILENAME,
        help="Arquivo WAV de saída",
    )
    parser.add_argument("--speaker-wav", help="Arquivo WAV para clonagem de voz", default=None)
    parser.add_argument("--speaker", help="Nome/ID do locutor", default=None)
    parser.add_argument(
        "--sr", dest="sample_rate", type=int, help="Sample rate desejado", default=None
    )
    parser.add_argument(
        "--split-sentences",
        action="store_true",
        help="Habilita divisão automática de sentenças",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Exibe tracebacks completos em caso de erro",
    )
    return parser


def main_cli(argv: list[str] | None = None) -> int:
    """Entrypoint for the CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    setup_logging(debug=args.debug)

    text_path = Path(args.text_file).expanduser().resolve()
    try:
        raw_text = read_text_file(text_path)
    except Exception as exc:
        logger.error("Não foi possível ler o arquivo de texto: %s", exc)
        if args.debug:
            traceback.print_exc()
        return 1

    try:
        output_path = main.synthesize_to_wav(
            text=raw_text,
            lang=args.lang,
            output_path=args.output,
            speaker_wav=args.speaker_wav,
            speaker=args.speaker,
            sample_rate=args.sample_rate,
            split_sentences=args.split_sentences,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Erro durante a síntese: %s", exc)
        if args.debug:
            traceback.print_exc()
        return 2

    logger.info("Áudio gerado com sucesso: %s", output_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main_cli())

