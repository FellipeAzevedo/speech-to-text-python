# Guia de Configuração do Piper TTS em Docker

Este documento descreve como preparar uma nova máquina Windows para executar o pipeline de texto para fala utilizando os modelos da biblioteca [rhasspy/piper](https://huggingface.co/rhasspy) já disponíveis em `A:\\python-projects\\piper\\voices`.

## 1. Pré-requisitos

1. **Instale o Docker Desktop** (https://www.docker.com/products/docker-desktop/) e certifique-se de que o recurso de `WSL 2` está habilitado.
2. **Habilite o compartilhamento do drive A:**
   - Abra o Docker Desktop.
   - Vá para *Settings → Resources → File Sharing*.
   - Adicione `A:` à lista de diretórios compartilhados.
3. **Clonar este repositório** em um diretório acessível (por exemplo `C:\\Users\\<USUARIO>\\Projects\\speech-to-text-python`).
4. **(Opcional) Instale o `docker-compose` standalone** se utilizar versões antigas do Docker Desktop. As versões recentes já incluem o `docker compose` integrado.

## 2. Estrutura esperada

```
A:\python-projects\piper\voices\
    ├── <voz>\
    │   ├── <voz>.onnx
    │   └── <voz>.onnx.json
speech-to-text-python\
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    └── app\
        └── tts.py
```

## 3. Construir a imagem Docker

No diretório raiz do projeto (`speech-to-text-python`), execute:

```powershell
docker compose build
```

A imagem resultante instalará o `piper-tts` e dependências de áudio necessárias.

## 4. Executar uma síntese de voz

Utilize `docker compose run` para executar o utilitário `app.tts`. Monte o diretório com os modelos e defina o texto desejado. Exemplo:

```powershell
$voiceName = "pt_BR-faber-medium"
$voiceDir = "A:/python-projects/piper/voices"
$texto = "Olá, este é um teste de texto para fala executado localmente."

docker compose run --rm ^
  -e PIPER_VOICE_DIR="/voices" ^
  -v "$voiceDir:/voices:ro" ^
  -v "${PWD}/output:/app/output" ^
  piper-tts ^
  --voice $voiceName ^
  --text "$texto" ^
  --output /app/output/fala.wav
```

Explicação dos parâmetros principais:

- `-v "$voiceDir:/voices:ro"`: monta o diretório de vozes do Windows dentro do contêiner em `/voices`.
- `-v "${PWD}/output:/app/output"`: monta uma pasta local para salvar o resultado.
- `--voice`: nome do arquivo `.onnx` sem extensão.
- `--text`: texto a ser convertido.
- `--output`: caminho do arquivo WAV a ser gerado dentro do contêiner (espelhado pelo volume `output`).

## 5. Utilizando arquivo de texto

Você pode sintetizar a partir de um arquivo `.txt` UTF-8:

```powershell
docker compose run --rm ^
  -e PIPER_VOICE_DIR="/voices" ^
  -v "A:/python-projects/piper/voices:/voices:ro" ^
  -v "${PWD}/input:/app/input" ^
  -v "${PWD}/output:/app/output" ^
  piper-tts ^
  --voice pt_BR-faber-medium ^
  --text-file /app/input/exemplo.txt ^
  --output /app/output/fala.wav
```

## 6. Ajustes adicionais

- Use `--speaker` para selecionar um índice específico em vozes multi-speaker.
- Parâmetros como `--length-scale`, `--noise-scale` e `--noise-w` podem ser utilizados para controlar velocidade e variação da voz.
- Se desejar reutilizar o contêiner sem reconstruir, remova a flag `--rm`.

## 7. Limpeza

Para remover contêineres parados criados pelo `docker compose run`, utilize:

```powershell
docker container prune
```

## 8. Solução de problemas

- **`Voice '...' not found`**: verifique se o nome passado em `--voice` coincide exatamente com o arquivo `.onnx` (sem a extensão) existente em `A:\\python-projects\\piper\\voices`.
- **`Configuration file ... not found`**: o script exige o arquivo `.onnx.json` correspondente no mesmo diretório do modelo.
- **Erros de permissão**: confirme que o drive A está compartilhado com o Docker Desktop e que você executa o PowerShell como usuário com permissões suficientes.

Após a geração, os arquivos WAV estarão disponíveis em `speech-to-text-python\output` no Windows.
