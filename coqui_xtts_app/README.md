# Coqui XTTS v2 - Aplicação de Síntese de Voz

Projeto em Python para geração de áudio WAV utilizando o modelo
`tts_models/multilingual/multi-dataset/xtts_v2` da Coqui TTS. Inclui uma
interface web em Gradio e uma CLI para uso automatizado.

## Requisitos

- Python 3.10 ou superior
- Dependências listadas em `requirements.txt`

## Instalação

```bash
cd coqui_xtts_app
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\\Scripts\\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

O modelo XTTS v2 será baixado automaticamente na primeira execução e
armazenado no cache local da biblioteca.

## Uso

### Interface web (Gradio)

```bash
python -m app.ui
```

1. Envie um arquivo `.txt` **ou** escreva um texto curto diretamente na
   interface.
2. Ajuste os parâmetros desejados (idioma, voz, sample rate,
   divisão de sentenças, nome do arquivo de saída).
3. Clique em **Gerar Áudio**. O arquivo final será salvo na pasta
   `outputs/` e poderá ser ouvido/baixado diretamente na página.

### Linha de comando (CLI)

```bash
python -m app.cli --text-file entrada.txt --lang pt --output saida.wav
```

Opções adicionais:

- `--speaker-wav sample.wav`: arquivo WAV curto para clonagem de voz.
- `--speaker nome`: seleciona um locutor disponível pelo modelo.
- `--sr 24000`: define o sample rate (24000 Hz suportado pelo XTTS v2).
- `--split-sentences`: habilita divisão automática de sentenças.
- `--debug`: exibe tracebacks completos em caso de erro.

### Limitações e dicas

- Caso o texto ultrapasse **8000 caracteres**, divida-o em partes menores.
- O campo de sample rate aceita apenas valores suportados pelo modelo
  (24000 Hz). Outros valores serão rejeitados com uma mensagem amigável.
- Quando um arquivo de referência (`speaker_wav`) não for informado, o
  sistema utiliza o locutor padrão configurado (`random`).

## Testes

Testes unitários cobrem a função de saneamento de texto:

```bash
pytest
```

## Estrutura do projeto

```
coqui_xtts_app/
  app/
    __init__.py
    main.py
    ui.py
    cli.py
    text_utils.py
    config.py
    logging_utils.py
  tests/
    test_text_utils.py
  requirements.txt
  README.md
```

## Solução de problemas

- **Erro ao carregar o modelo**: garanta que todas as dependências foram
  instaladas. Reinstale com `pip install -r requirements.txt`.
- **Texto vazio após saneamento**: verifique se o arquivo contém apenas
  caracteres suportados (o saneamento remove emojis, controle, tags HTML
  e símbolos não textuais).
- **Erro de sample rate**: utilize 24000 Hz, compatível com o XTTS v2.
- **Execução em CPU**: o modelo funciona em CPU, porém a síntese pode
  levar alguns minutos dependendo do tamanho do texto.

