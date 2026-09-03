# syntax=docker/dockerfile:1
#
# Containerizza SOLO anf-api. L'agent privilegiato e il web server restano
# servizi nativi sull'host: vedere docs/DOCKER.md e docs/PIANO.md (Nodo 1)
# per il perche'.

# --- Build: compila le dipendenze una volta sola -------------------------
# build-essential/libffi-dev servono solo se PyPI non ha ancora una ruota
# precompilata per argon2-cffi su questa versione di Python: restano fuori
# dall'immagine finale.
FROM python:3.14-slim AS build

RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir --root-user-action=ignore --prefix=/install .

# --- Immagine finale: solo il runtime -------------------------------------
FROM python:3.14-slim

LABEL org.opencontainers.image.title="Advanced NAS Folder - API" \
      org.opencontainers.image.source="https://github.com/wifi75/advanced-nas-folder" \
      org.opencontainers.image.licenses="MIT"

# Utente non privilegiato, stessa regola del servizio systemd nativo: questa
# applicazione non deve mai poter toccare il sistema. UID/GID reali li sceglie
# docker-compose (ANF_UID/ANF_GID) per combaciare col proprietario dei volumi
# montati dall'host: qui basta che l'utente esista.
RUN groupadd --system anf \
    && useradd --system --no-create-home --gid anf --shell /usr/sbin/nologin anf

WORKDIR /app
COPY --from=build /install /usr/local
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown -R anf:anf /app

USER anf
EXPOSE 8100

# Verifica anche il database: un container "up" con l'agent o il DB
# irraggiungibili non e' uno stato sano da tenere in piedi.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "\
import os, sys, urllib.request; \
u = f'http://127.0.0.1:{os.environ.get(\"ANF_PORT\", \"8100\")}/api/v1/health/ready'; \
sys.exit(0 if urllib.request.urlopen(u, timeout=3).status == 200 else 1)"

ENTRYPOINT ["/entrypoint.sh"]
