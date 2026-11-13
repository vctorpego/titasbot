# Deploy do TitasBot na VPS (Locaweb)

**No ar em <https://titasbot.duckdns.org>** — reserva:
<https://vps73870.publiccloud.com.br> (mesmo servidor).

Substitui o deploy no Cloud Run (`DEPLOY_GCP.md`), que no plano gratuito ficava
lento e instavel.

## Servidor

| | |
|---|---|
| Provedor | Locaweb — VPS 198447 |
| Sistema | Ubuntu 24.04 LTS |
| Recursos | 1 GB RAM, 2 vCPUs, 40 GB disco |
| Acesso | SSH por chave (`~/.ssh/titasbot_vps`), sem senha |
| Diretorio | `/opt/titasbot` |

## Arquitetura

```
push na main
   -> GitHub Actions: testes -> build da imagem -> ghcr.io/vctorpego/titasbot:latest
   -> ssh na VPS: docker compose pull && up -d
                     |
                     +-- caddy  (80/443, HTTPS automatico)
                     +-- app    (Python + frontend buildado, porta interna 8080)
                            +-- volume "chroma": indice vetorial persistente
```

Decisoes que valem registrar:

- **A imagem e construida no GitHub Actions, nao na VPS.** Compilar o frontend
  (`npm`) e as dependencias Python em 1 GB de RAM derrubaria a maquina. A VPS so
  baixa a imagem pronta.
- **O indice vetorial vive em um volume Docker**, nao dentro da imagem. O
  entrypoint grava junto com o indice uma impressao digital dos arquivos de
  `back/base`; se ela nao mudou, a ingestao e pulada. Sem isso, cada deploy
  reprocessaria os PDFs e pagaria embeddings de novo.
- **Swap de 2 GB.** Com 1 GB de RAM, a ingestao ou um pico de acesso poderiam
  ser mortos pelo OOM killer.

## Preparacao inicial (uma vez)

```bash
scp -i ~/.ssh/titasbot_vps deploy/vps/provision.sh root@vps73870.publiccloud.com.br:/root/
ssh -i ~/.ssh/titasbot_vps root@vps73870.publiccloud.com.br 'bash /root/provision.sh'
```

Depois, envie a stack e crie o `.env`:

```bash
scp -i ~/.ssh/titasbot_vps deploy/vps/docker-compose.yml deploy/vps/Caddyfile root@vps73870.publiccloud.com.br:/opt/titasbot/
ssh -i ~/.ssh/titasbot_vps root@vps73870.publiccloud.com.br
# no servidor:
nano /opt/titasbot/.env     # modelo em deploy/vps/.env.example
cd /opt/titasbot && docker compose up -d
```

## Segredos no GitHub

Em **Settings > Secrets and variables > Actions**:

| Secret | Valor |
|---|---|
| `VPS_HOST` | IP da VPS |
| `VPS_USER` | `root` |
| `VPS_SSH_KEY` | conteudo de `~/.ssh/titasbot_vps` (chave privada) |

A publicacao da imagem usa o `GITHUB_TOKEN` automatico — nao precisa de secret.

## Atualizar a producao

Faca merge na `main`. O workflow `.github/workflows/deploy.yml` cuida do resto.
Para reexecutar sem commit novo: aba **Actions > Deploy producao > Run workflow**.

## Rollback

Toda imagem tambem e publicada com a tag do commit:

```bash
ssh -i ~/.ssh/titasbot_vps root@vps73870.publiccloud.com.br
cd /opt/titasbot
sed -i 's|:latest|:SHA_DO_COMMIT_BOM|' .env   # ou edite TITASBOT_IMAGE
docker compose pull && docker compose up -d
```

## Diagnostico

```bash
docker compose -f /opt/titasbot/docker-compose.yml ps
docker compose -f /opt/titasbot/docker-compose.yml logs -f app
curl -s http://127.0.0.1/health
free -h            # RAM e swap
docker stats --no-stream
```

**O bot responde "Nao encontrei informacao suficiente" para tudo:** o indice
vetorial provavelmente nao foi gerado. Veja os logs do `app` no boot e confira
se a `OPENAI_API_KEY` tem credito.

**Forcar a regeracao do indice** (depois de trocar PDFs em `back/base`): o
entrypoint detecta sozinho no proximo deploy. Para forcar na mao:

```bash
docker compose -f /opt/titasbot/docker-compose.yml exec app rm /data/chroma/.base_fingerprint
docker compose -f /opt/titasbot/docker-compose.yml restart app
```

## Dominio e HTTPS

O site atende dois nomes, cada um com certificado Let's Encrypt proprio,
emitido e renovado pelo Caddy:

- **`titasbot.duckdns.org`** — endereco principal. Subdominio gratuito do
  DuckDNS (conta Google do autor), com registro A para 191.252.109.57. O IP
  da VPS e fixo, entao nao ha atualizador dinamico rodando. Para mudar o IP:
  painel do duckdns.org, campo "current ip", "update ip".
- **`vps73870.publiccloud.com.br`** — hostname da Locaweb. Nao pode ser
  renomeado (o dominio e da Locaweb; no painel o campo nao e editavel), mas
  continua valendo como reserva se o DuckDNS cair.

Os dois vem de `SITE_ADDRESS` no `/opt/titasbot/.env`, separados por virgula.
Para trocar ou adicionar um nome (um dominio proprio, um subdominio do Ifes):
aponte o DNS para 191.252.109.57, edite `SITE_ADDRESS` e rode
`docker compose up -d proxy`. `SITE_ADDRESS=:80` volta para HTTP puro no IP.

Depois de criar um nome novo, alguns minutos de "nao encontrado" sao normais:
resolvedores que consultaram o nome antes de ele existir guardam a resposta
negativa por um tempo.

## Tempo de resposta

Medicao de 2026-11-11, pelas mesmas perguntas:

| Pergunta | gpt-5-nano | gpt-5-mini |
|---|---|---|
| Pergunta direta ("primeiro nome da equipe") | 12,2 s | 8,7 s |
| Pergunta aberta / de lista | ~82 s | ~84 s |

O gargalo **nao e o modelo**: trocar nano por mini nao mudou o tempo. Uma
resposta passa por varias chamadas de LLM encadeadas (decisao de contexto,
expansao da consulta, selecao de evidencias, geracao, auditoria, escopo de
equipe e canonicalizacao de listas). Sao os modelos da familia GPT-5, que
gastam tempo raciocinando em cada etapa.

**Otimizado na mesma noite** (commit `5978585`): mediana de ~57 s para
~15–18 s, com a mesma qualidade, via `CHAT_REASONING_EFFORT=low` e
`CHAT_FAST_REASONING_EFFORT=minimal` mais ajustes de prompt e dois bugs de
recuperacao. Analise completa, medicoes e como desfazer em
`estudo_defesa/OTIMIZACAO_TEMPO_RESPOSTA.md`.

Para ver o tempo de cada etapa no log: `CHAT_LOG_TIMINGS=1` no `.env`,
`docker compose up -d` e `docker compose logs -f app`.
