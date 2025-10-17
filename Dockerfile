# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libsndfile1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app

ENTRYPOINT ["python", "-m", "app.tts"]
