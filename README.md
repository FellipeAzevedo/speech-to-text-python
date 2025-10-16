# speech-to-text-python

Script em Python que demonstra como converter texto em fala localmente usando a biblioteca [Coqui TTS](https://coqui.ai/tts) e, opcionalmente, uma interface interativa com [Gradio](https://gradio.app/).

## Instalação

> Os comandos abaixo devem ser executados em um ambiente com Python 3.8+.

```bash
pip install torch coqui-tts gradio
```

## Uso rápido

1. Ajuste o texto no arquivo `entrada.txt` (codificação UTF-8).
2. Execute o script principal para gerar `saida.wav` com o modelo configurado:

```bash
python coqui_tts_local.py --modelo tts_models/pt/cv/vits --entrada entrada.txt --saida saida.wav
```

### Parâmetros importantes

- `--modelo`: nome do modelo pré-treinado da Coqui (ex.: `tts_models/en/ljspeech/fast_pitch`, `tts_models/pt/cv/vits`, `tts_models/multilingual/multi-dataset/xtts_v2`).
- `--velocidade`: ajusta a velocidade de fala (1.0 = normal). Valores como 0.8 ou 1.2 deixam a voz mais lenta ou mais rápida.
- `--idioma`: define o idioma para modelos multilíngues (ex.: `pt`, `en`).
- `--falante`/`--falante-idx`: escolhe a voz nos modelos multi-locutor (ex.: `Ana Florence`).
- `--temperatura`: controla a variação de entonação (0.65 é o padrão).
- `--interativo`: abre uma interface web com Gradio para testes rápidos reutilizando o mesmo modelo carregado.

> A documentação oficial informa que o pacote é testado no Ubuntu, mas funciona também no macOS e Windows.

## Interface interativa com Gradio

Para abrir o modo interativo, execute:

```bash
python coqui_tts_local.py --interativo
```

Será exibida uma página com campo de texto, controles de velocidade/temperatura e seleção opcional de idioma/falante. A saída de áudio é reproduzida diretamente no navegador.

## Dicas de narração

- A Coqui TTS não suporta SSML; utilize pontuação ou reticências (`...`) para inserir pausas mais longas.
- Modelos como FastPitch fornecem contornos de frequência que resultam em vozes mais expressivas. Combine com ajustes de `--temperatura` para controlar a aleatoriedade.
- Consulte a [lista de modelos](https://coqui-tts.readthedocs.io/en/latest/models.html) para explorar vozes em mais de 1100 idiomas.
