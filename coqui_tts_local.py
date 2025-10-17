"""Script para conversão de texto em fala usando Coqui TTS."""

# Instalação das dependências (executar no terminal):
# pip install torch coqui-tts gradio

from __future__ import annotations

import argparse
import inspect
import logging
import wave
from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import numpy as np

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


@lru_cache(maxsize=None)
def _caracteristicas_modelo(tts_type: type) -> tuple[bool, dict[str, inspect.Parameter]]:
    """Retorna as características da função ``tts`` do modelo informado."""
    try:
        assinatura = inspect.signature(tts_type.tts)  # type: ignore[attr-defined]
    except (TypeError, ValueError):  # pragma: no cover - fallback para objetos não inspecionáveis
        return True, {}

    aceita_kwargs = any(
        parametro.kind == inspect.Parameter.VAR_KEYWORD for parametro in assinatura.parameters.values()
    )
    parametros = {nome: parametro for nome, parametro in assinatura.parameters.items() if nome != "self"}
    return aceita_kwargs, parametros


def ler_texto(arquivo: Path) -> str:
    """Lê o texto de entrada em UTF-8."""
    LOGGER.debug("Lendo arquivo de texto em %s", arquivo)
    return arquivo.read_text(encoding="utf-8")


def _obter_sample_rate(tts: TTS) -> int:
    """Retorna a taxa de amostragem configurada no sintetizador."""
    sintetizador = getattr(tts, "synthesizer", None)
    if sintetizador is not None:
        sample_rate = getattr(sintetizador, "output_sample_rate", None)
        if sample_rate:
            return int(sample_rate)
    return 22050  # valor padrão de fallback


def _salvar_audio_com_progresso(audio: np.ndarray, sample_rate: int, caminho_saida: Path) -> None:
    """Salva o áudio em WAV exibindo o progresso da gravação."""
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    dados = np.asarray(audio, dtype=np.float32)
    if dados.ndim == 1:
        dados = dados[:, np.newaxis]
    elif dados.ndim == 2 and dados.shape[0] < dados.shape[1]:
        # Normaliza para o formato (amostras, canais)
        dados = dados.T

    total_amostras = dados.shape[0]
    if total_amostras == 0:
        raise ValueError("O modelo não retornou amostras de áudio.")

    # Normaliza e converte para PCM16.
    max_abs = np.max(np.abs(dados))
    if max_abs > 1:
        dados = dados / max_abs
    dados_pcm16 = np.clip(dados, -1.0, 1.0)
    dados_pcm16 = (dados_pcm16 * np.iinfo(np.int16).max).astype(np.int16)

    chunk = max(1, total_amostras // 40)  # atualiza a cada ~2.5%
    ultimo_percentual = -1

    LOGGER.info("Progresso da gravação: 0%%")
    with wave.open(str(caminho_saida), "wb") as wav_file:
        wav_file.setnchannels(dados_pcm16.shape[1])
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        for inicio in range(0, total_amostras, chunk):
            fim = min(inicio + chunk, total_amostras)
            wav_file.writeframes(dados_pcm16[inicio:fim].tobytes())

            percentual = int((fim / total_amostras) * 100)
            if percentual >= ultimo_percentual + 5 or percentual == 100:
                LOGGER.info("Progresso da gravação: %s%%", percentual)
                ultimo_percentual = percentual


def sintetizar(
    tts: TTS,
    texto: str,
    caminho_saida: Path,
    velocidade: float = 1.0,
    idioma: Optional[str] = None,
    falante: Optional[str] = None,
    indice_falante: Optional[int] = None,
) -> Path:
    """Gera o áudio a partir do texto fornecido."""
    if not texto.strip():
        raise ValueError("O texto de entrada está vazio.")

    LOGGER.info("Gerando áudio...")
    kwargs: dict[str, object] = {"text": texto}

    aceita_kwargs, parametros = _caracteristicas_modelo(type(tts))
    parametros_suportados = set(parametros)
    parametros_obrigatorios = {
        nome
        for nome, parametro in parametros.items()
        if parametro.default is inspect._empty
        and parametro.kind
        in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }
    parametros_ignorados: set[str] = set()

    def adicionar_parametro(nome: str, valor: Optional[object]) -> None:
        if valor is None:
            return
        if aceita_kwargs or nome in parametros_suportados:
            kwargs[nome] = valor
        else:
            if nome not in parametros_ignorados:
                LOGGER.warning("O parâmetro '%s' não é suportado por este modelo e será ignorado.", nome)
                parametros_ignorados.add(nome)

    # Ajustes de voz opcionais.
    if velocidade != 1.0:
        adicionar_parametro("speed", velocidade)

    # Modelos multilíngues aceitam a seleção de idioma e falante.
    if idioma:
        adicionar_parametro("language", idioma)
    if falante:
        adicionar_parametro("speaker", falante)
    if indice_falante is not None:
        adicionar_parametro("speaker_idx", indice_falante)

    LOGGER.info("Sintetizando áudio (pode levar alguns instantes)...")
    audio = tts.tts(**kwargs)
    sample_rate = _obter_sample_rate(tts)
    LOGGER.info("Síntese concluída. Gravando arquivo em disco...")
    _salvar_audio_com_progresso(audio, sample_rate, caminho_saida)
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
    **kwargs: object,
) -> Path:
    """Executa o fluxo automático: ler arquivo e gerar o WAV."""
    if kwargs:
        nomes_desconhecidos = ", ".join(sorted(kwargs))
        LOGGER.warning(
            "Parâmetros não reconhecidos ignorados em executar_modo_automatico: %s",
            nomes_desconhecidos,
        )

    texto = ler_texto(arquivo_entrada)
    return sintetizar(
        tts,
        texto,
        arquivo_saida,
        velocidade=velocidade,
        idioma=idioma,
        falante=falante,
        indice_falante=indice_falante,
    )


def executar_modo_interativo(
    tts: TTS,
    velocidade_padrao: float,
    idioma_padrao: Optional[str],
    falante_padrao: Optional[str],
) -> None:
    """Inicializa uma interface simples com Gradio para testes rápidos."""
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover - reporta falha de importação
        raise SystemExit(
            "Gradio não está instalado. Execute `pip install gradio`."
        ) from exc

    def gerar_audio(texto: str, velocidade: float, idioma: str, falante: str):
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
        botao = gr.Button("Gerar áudio")
        saida_audio = gr.Audio(label="Resultado", type="filepath")

        botao.click(
            gerar_audio,
            inputs=[entrada_texto, velocidade_slider, idioma_input, falante_input],
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
    )


if __name__ == "__main__":
    main()
