#!/usr/bin/env bash
# Preparacao inicial da VPS (Ubuntu 24.04). Roda uma unica vez, como root.
#
#   scp deploy/vps/provision.sh root@IP:/root/
#   ssh root@IP 'bash /root/provision.sh'
#
# O que faz:
#   - atualiza o sistema
#   - cria 2 GB de swap (a VPS tem so 1 GB de RAM)
#   - instala Docker Engine + plugin compose
#   - libera 22/80/443 no firewall
#   - cria /opt/titasbot
set -euo pipefail

log() { printf '\n\033[1;35m==> %s\033[0m\n' "$*"; }

if [ "$(id -u)" -ne 0 ]; then
    echo "Rode como root." >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive

log "Atualizando pacotes"
apt-get update -y
apt-get upgrade -y

log "Instalando utilitarios"
apt-get install -y --no-install-recommends ca-certificates curl gnupg ufw

# ---------------------------------------------------------------- swap
# 1 GB de RAM e pouco: sem swap, o container pode ser morto pelo OOM killer
# durante a ingestao dos PDFs ou em picos de acesso.
if swapon --show | grep -q '/swapfile'; then
    log "Swap ja configurado"
else
    log "Criando swap de 2 GB"
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
    # Pouca pressao de swap: usa RAM enquanto houver, swap so no aperto.
    sysctl -w vm.swappiness=10
    grep -q '^vm.swappiness' /etc/sysctl.conf || echo 'vm.swappiness=10' >> /etc/sysctl.conf
fi

# -------------------------------------------------------------- docker
if command -v docker >/dev/null 2>&1; then
    log "Docker ja instalado"
else
    log "Instalando Docker Engine"
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

systemctl enable --now docker

# ------------------------------------------------------------ firewall
log "Configurando firewall"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# --------------------------------------------------------------- dirs
log "Preparando /opt/titasbot"
mkdir -p /opt/titasbot

log "Pronto"
docker --version
docker compose version
free -h
