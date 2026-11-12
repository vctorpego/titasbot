# syntax=docker/dockerfile:1.7

FROM node:22-slim AS frontend-builder
WORKDIR /app/front
COPY front/package*.json ./
RUN npm ci
COPY front/ ./
# Vazio = o frontend chama /chat na mesma origem em que foi servido.
ENV VITE_API_URL=""
RUN npm run build

FROM python:3.12-slim AS backend-builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app/back
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY back/requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt
COPY back/ ./

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080 \
    FRONT_DIST_DIR=/app/front/dist \
    BASE_DIR=/app/back/base \
    CHROMA_DB_PATH=/data/chroma \
    CHROMA_COLLECTION=titas_docs \
    OPENAI_CHAT_MODEL=gpt-5-mini \
    OPENAI_EMBEDDING_MODEL=text-embedding-3-small \
    CHAT_TEMPERATURE=0 \
    CHAT_REASONING_EFFORT=low \
    CHAT_FAST_REASONING_EFFORT=minimal
WORKDIR /app/back
RUN useradd --create-home --shell /usr/sbin/nologin appuser
COPY --from=backend-builder /usr/local /usr/local
COPY --from=backend-builder --chown=appuser:appuser /app/back /app/back
COPY --from=frontend-builder --chown=appuser:appuser /app/front/dist /app/front/dist
COPY --chown=appuser:appuser deploy/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh \
    && mkdir -p /data \
    && chown appuser:appuser /data
# /data vira volume: o Docker herda esse dono ao criar o volume pela 1a vez,
# entao o appuser consegue escrever o indice sem rodar como root.
VOLUME ["/data"]
USER appuser
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
