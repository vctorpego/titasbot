#!/bin/sh
# Entrypoint do container de producao.
#
# O banco vetorial Chroma e gerado a partir dos PDFs de back/base chamando a API
# de embeddings da OpenAI. Isso custa dinheiro e leva minutos, entao NAO deve
# rodar a cada deploy: o indice fica em um volume (CHROMA_DB_PATH) e so e
# regerado quando a base de conhecimento muda.
#
# A "impressao digital" da base (nome + tamanho de cada arquivo) e gravada junto
# com o indice. Se ela bater, a ingestao e pulada.
set -eu

CHROMA_DB_PATH="${CHROMA_DB_PATH:-/data/chroma}"
BASE_DIR="${BASE_DIR:-/app/back/base}"
STAMP="${CHROMA_DB_PATH}/.base_fingerprint"

mkdir -p "${CHROMA_DB_PATH}"

fingerprint="$(find "${BASE_DIR}" -type f -printf '%f %s\n' 2>/dev/null | sort | md5sum | cut -d' ' -f1)"
current=""
if [ -f "${STAMP}" ]; then
    current="$(cat "${STAMP}")"
fi

if [ "${current}" = "${fingerprint}" ]; then
    echo "[entrypoint] Indice vetorial reaproveitado de ${CHROMA_DB_PATH} (base inalterada)."
else
    if [ -z "${current}" ]; then
        echo "[entrypoint] Nenhum indice vetorial encontrado. Gerando a partir de ${BASE_DIR}..."
    else
        echo "[entrypoint] Base de conhecimento mudou. Regerando o indice vetorial..."
    fi

    if python criar_db.py; then
        printf '%s' "${fingerprint}" > "${STAMP}"
        echo "[entrypoint] Indice vetorial pronto."
    elif [ -n "${current}" ]; then
        # Falhou (sem credito na OpenAI, rede fora, etc), mas existe um indice
        # anterior: e melhor subir com a base antiga do que ficar em loop de
        # restart gastando chamadas de API.
        echo "[entrypoint] ERRO ao regerar o indice. Subindo com o indice anterior." >&2
    else
        echo "[entrypoint] ERRO ao gerar o indice e nao ha indice anterior. Abortando." >&2
        echo "[entrypoint] Confira OPENAI_API_KEY e o saldo da conta OpenAI." >&2
        exit 1
    fi
fi

exec python web_server.py
