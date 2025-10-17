# speech-to-text-python

Ambiente Dockerizado para síntese de fala local utilizando os modelos [Piper](https://huggingface.co/rhasspy/).

## Componentes principais

- `Dockerfile`: constrói a imagem Python com `piper-tts` e dependências de áudio.
- `docker-compose.yml`: simplifica a execução do contêiner, montando diretórios de saída e definindo variáveis de ambiente padrão, além de expor uma interface web opcional.
- `app/tts.py`: wrapper em Python que resolve automaticamente o caminho do modelo e delega a síntese para o CLI `piper`.
- `app/interface.py`: interface via Gradio para uso interativo com seleção de vozes e parâmetros validados automaticamente.
- `tests/`: suíte de testes que valida a detecção dinâmica de opções dos modelos Piper.
- `SETUP_GUIDE.md`: guia passo a passo para configurar uma nova máquina Windows com os modelos já baixados.

Consulte o [SETUP_GUIDE.md](SETUP_GUIDE.md) para instruções detalhadas de uso.
