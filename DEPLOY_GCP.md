# Deploy do TitasBot no Google Cloud

Este deploy publica o TitasBot como um unico servico Cloud Run no projeto `siadon`, sem reutilizar VM, IP fixo, Cloud SQL ou outros recursos antigos do SIAD.

## Arquitetura

- Cloud Run em `us-central1`, com `min-instances=0` e `max-instances=1`.
- Frontend React gerado por Vite e servido pelo mesmo backend Python.
- API publica no mesmo dominio: `POST /chat` e `GET /health`.
- Banco vetorial Chroma gerado durante o build da imagem a partir dos PDFs em `back/base`.
- Segredo `OPENAI_API_KEY` no Secret Manager.
- Modelo de producao: `gpt-5-nano`.

## Deploy

No PowerShell, defina a chave somente na sessao atual:

```powershell
$env:OPENAI_API_KEY = "sk-..."
.\deploy\deploy_cloud_run.ps1
```

O script cria ou atualiza:

- Artifact Registry `titasbot`;
- Secret Manager `titasbot-openai-api-key`;
- Cloud Run `titasbot`.

Depois do deploy:

```powershell
$url = gcloud run services describe titasbot --project siadon --region us-central1 --format="value(status.url)"
Invoke-RestMethod "$url/health"
Invoke-RestMethod "$url/chat" -Method Post -ContentType "application/json" -Body '{"question":"qual foi o primeiro nome da equipe?"}'
```

## Limpeza do SIAD antigo

O script abaixo remove os recursos legados conhecidos: VM, IP fixo, regras de firewall especificas e Cloud SQL antigo.

```powershell
.\deploy\remove_siad_legacy.ps1
```

Nao ha backup neste fluxo porque o deploy antigo foi descartado por decisao do projeto.

## Atualizacao e rollback

Para atualizar, rode novamente:

```powershell
$env:OPENAI_API_KEY = "sk-..."
.\deploy\deploy_cloud_run.ps1
```

Para rollback, liste revisoes e direcione trafego para uma revisao anterior:

```powershell
gcloud run revisions list --service titasbot --project siadon --region us-central1
gcloud run services update-traffic titasbot --project siadon --region us-central1 --to-revisions REVISAO=100
```

## Controle de custo

Rode periodicamente:

```powershell
.\deploy\cleanup_artifacts.ps1
```

Isso ajuda a manter o Artifact Registry abaixo do limite gratuito. O Cloud Run pode ficar sem custo dentro do free tier, mas trafego alto, logs excessivos ou imagens grandes podem gerar cobranca. As chamadas da OpenAI sao cobradas fora do Google Cloud.
