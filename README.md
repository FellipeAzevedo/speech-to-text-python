# speech-to-text-python

Ambiente Dockerizado para síntese de fala local utilizando os modelos [Piper](https://huggingface.co/rhasspy/).

## Componentes principais

- `Dockerfile`: constrói a imagem Python com `piper-tts` e dependências de áudio.
- `docker-compose.yml`: simplifica a execução do contêiner, montando diretórios de saída e definindo variáveis de ambiente padrão.
- `app/tts.py`: wrapper em Python que resolve automaticamente o caminho do modelo e delega a síntese para o CLI `piper`.
- `SETUP_GUIDE.md`: guia passo a passo para configurar uma nova máquina Windows com os modelos já baixados.

Consulte o [SETUP_GUIDE.md](SETUP_GUIDE.md) para instruções detalhadas de uso.
