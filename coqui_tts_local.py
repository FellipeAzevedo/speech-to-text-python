"""Script para conversão de texto em fala usando Coqui TTS."""

# Instalação das dependências (executar no terminal):
# pip install torch coqui-tts gradio

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

try:
    from TTS.api import TTS  # type: ignore
except ImportError as exc:  # pragma: no cover - falha de importação reportada ao usuário
    raise SystemExit(
        "A biblioteca Coqui TTS não está instalada. Execute `pip install torch coqui-tts gradio`."
    ) from exc

# Observação: A Coqui TTS suporta mais de 1100 idiomas/modelos pré-treinados, incluindo
# síntese multilíngue/multi-locutor. Consulte https://pypi.org/project/TTS/.
# Pausas não utilizam SSML; use pontuação/reticências ("...") para pausas maiores.

LOGGER = logging.getLogger(__name__)


def carregar_modelo(model_name: str) -> TTS:
    """Carrega um modelo pré-treinado do Coqui TTS."""
    LOGGER.info("Carregando modelo '%s'...", model_name)
    return TTS(model_name)


def ler_texto(arquivo: Path) -> str:
    """Lê o texto de entrada em UTF-8."""
    LOGGER.debug("Lendo arquivo de texto em %s", arquivo)
    return arquivo.read_text(encoding="utf-8")


def sintetizar(
    tts: TTS,
    texto: str,
    caminho_saida: Path,
    velocidade: float = 1.0,
    idioma: Optional[str] = None,
    falante: Optional[str] = None,
    indice_falante: Optional[int] = None,
    temperatura: Optional[float] = None,
) -> Path:
    """Gera o áudio a partir do texto fornecido."""
    if not texto.strip():
        raise ValueError("O texto de entrada está vazio.")

    LOGGER.info("Gerando áudio...")
    kwargs = {
        "text": texto,
        "file_path": str(caminho_saida),
        "speed": velocidade,
    }

    # Modelos multilíngues aceitam a seleção de idioma e falante.
    if idioma:
        kwargs["language"] = idioma
    if falante:
        kwargs["speaker"] = falante
    if indice_falante is not None:
        kwargs["speaker_idx"] = indice_falante
    if temperatura is not None:
        # A temperatura controla a aleatoriedade/entonação (default 0.65). Modelos como FastPitch já
        # embutem contornos de frequência, tornando a voz mais expressiva.
        kwargs["temperature"] = temperatura

    tts.tts_to_file(**kwargs)
    LOGGER.info("Arquivo %s criado com sucesso.", caminho_saida)
    return caminho_saida


def executar_modo_automatico(
    tts: TTS,
    arquivo_entrada: Path,
    arquivo_saida: Path,
    velocidade: float,
    idioma: Optional[str],
    falante: Optional[str],
    indice_falante: Optional[int],
    temperatura: Optional[float],
) -> Path:
    """Executa o fluxo automático: ler arquivo e gerar o WAV."""
    texto = ler_texto(arquivo_entrada)
    return sintetizar(
        tts,
        texto,
        arquivo_saida,
        velocidade=velocidade,
        idioma=idioma,
        falante=falante,
        indice_falante=indice_falante,
        temperatura=temperatura,
    )


def executar_modo_interativo(
    tts: TTS,
    velocidade_padrao: float,
    idioma_padrao: Optional[str],
    falante_padrao: Optional[str],
    temperatura_padrao: Optional[float],
) -> None:
    """Inicializa uma interface simples com Gradio para testes rápidos."""
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover - reporta falha de importação
        raise SystemExit(
            "Gradio não está instalado. Execute `pip install gradio`."
        ) from exc

    def gerar_audio(texto: str, velocidade: float, idioma: str, falante: str, temperatura: float):
        if not texto.strip():
            return None
        with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            caminho = Path(tmp.name)
        sintetizar(
            tts,
            texto,
            caminho,
            velocidade=velocidade,
            idioma=idioma or None,
            falante=falante or None,
            temperatura=temperatura,
        )
        return str(caminho)

    descricao = (
        "Teste frases rapidamente. Modelos multilíngues permitem selecionar idioma (ex.: 'pt', 'en').\n"
        "Modelos multi-locutor aceitam nomes como 'Ana Florence' ou índices numéricos."
    )

    with gr.Blocks() as demo:
        gr.Markdown("## Coqui TTS - Teste Interativo")
        gr.Markdown(descricao)
        entrada_texto = gr.Textbox(label="Texto", lines=4)
        velocidade_slider = gr.Slider(
            label="Velocidade",
            minimum=0.6,
            maximum=1.4,
            step=0.05,
            value=velocidade_padrao,
        )
        idioma_input = gr.Textbox(label="Idioma (opcional)", value=idioma_padrao or "")
        falante_input = gr.Textbox(label="Falante (opcional)", value=falante_padrao or "")
        temperatura_slider = gr.Slider(
            label="Temperatura (0.2 a 1.0)", minimum=0.2, maximum=1.0, step=0.05, value=temperatura_padrao or 0.65
        )
        botao = gr.Button("Gerar áudio")
        saida_audio = gr.Audio(label="Resultado", type="filepath")

        botao.click(
            gerar_audio,
            inputs=[entrada_texto, velocidade_slider, idioma_input, falante_input, temperatura_slider],
            outputs=saida_audio,
        )

    demo.queue()  # reutiliza o modelo carregado para múltiplas requisições
    demo.launch()


def configurar_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Conversão de texto para fala com Coqui TTS.")
    parser.add_argument(
        "--modelo",
        default="tts_models/pt/cv/vits",
        help=(
            "Modelo pré-treinado (ex.: 'tts_models/en/ljspeech/fast_pitch', 'tts_models/pt/cv/vits', "
            "'tts_models/multilingual/multi-dataset/xtts_v2')."
        ),
    )
    parser.add_argument(
        "--entrada",
        type=Path,
        default=Path("entrada.txt"),
        help="Arquivo de texto UTF-8 a ser narrado.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("saida.wav"),
        help="Arquivo WAV de saída.",
    )
    parser.add_argument(
        "--velocidade",
        type=float,
        default=1.0,
        help="Velocidade da fala (ex.: 0.8 para mais lento, 1.2 para mais rápido).",
    )
    parser.add_argument(
        "--idioma",
        type=str,
        default=None,
        help="Código de idioma (ex.: 'pt', 'en') para modelos multilíngues.",
    )
    parser.add_argument(
        "--falante",
        type=str,
        default=None,
        help="Nome do falante (modelos multi-locutor, ex.: 'Ana Florence').",
    )
    parser.add_argument(
        "--falante-idx",
        type=int,
        default=None,
        help="Índice numérico do falante (para modelos multi-locutor).",
    )
    parser.add_argument(
        "--temperatura",
        type=float,
        default=0.65,
        help="Temperatura para variação de entonação (default 0.65).",
    )
    parser.add_argument(
        "--interativo",
        action="store_true",
        help="Inicia a interface interativa com Gradio.",
    )
    parser.add_argument(
        "--log",
        default="INFO",
        help="Nível de log (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def main() -> None:
    args = configurar_argumentos()
    logging.basicConfig(level=getattr(logging, args.log.upper(), logging.INFO))

    tts = carregar_modelo(args.modelo)

    if args.interativo:
        executar_modo_interativo(
            tts,
            velocidade_padrao=args.velocidade,
            idioma_padrao=args.idioma,
            falante_padrao=args.falante,
            temperatura_padrao=args.temperatura,
        )
        return

    executar_modo_automatico(
        tts,
        arquivo_entrada=args.entrada,
        arquivo_saida=args.saida,
        velocidade=args.velocidade,
        idioma=args.idioma,
        falante=args.falante,
        indice_falante=args.falante_idx,
        temperatura=args.temperatura,
    )


if __name__ == "__main__":
    main()
