param(
    [string]$ProjectId = "siadon",
    [string]$Region = "us-central1",
    [string]$ServiceName = "titasbot",
    [string]$Repository = "titasbot",
    [string]$SecretName = "titasbot-openai-api-key"
)

$ErrorActionPreference = "Stop"

if (-not $env:OPENAI_API_KEY) {
    throw "Defina OPENAI_API_KEY apenas nesta sessao antes do deploy. Ex.: `$env:OPENAI_API_KEY = 'sk-...'"
}

$account = gcloud config get-value account 2>$null
if (-not $account) {
    throw "Nenhuma conta autenticada no gcloud. Rode gcloud auth login."
}

gcloud config set project $ProjectId | Out-Null
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com --project $ProjectId

$repoExists = gcloud artifacts repositories describe $Repository --project $ProjectId --location $Region --format="value(name)" 2>$null
if (-not $repoExists) {
    gcloud artifacts repositories create $Repository --project $ProjectId --location $Region --repository-format docker --description "TitasBot container images"
}

$secretExists = gcloud secrets describe $SecretName --project $ProjectId --format="value(name)" 2>$null
if (-not $secretExists) {
    gcloud secrets create $SecretName --project $ProjectId --replication-policy automatic
}
$env:OPENAI_API_KEY | gcloud secrets versions add $SecretName --project $ProjectId --data-file=-

$projectNumber = gcloud projects describe $ProjectId --format="value(projectNumber)"
$runtimeServiceAccount = "$projectNumber-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding $SecretName `
    --project $ProjectId `
    --member "serviceAccount:$runtimeServiceAccount" `
    --role "roles/secretmanager.secretAccessor" | Out-Null

gcloud auth configure-docker "$Region-docker.pkg.dev" --quiet

$gitSha = git rev-parse --short HEAD
if (git status --porcelain) {
    $gitSha = "$gitSha-dirty-$(Get-Date -Format yyyyMMddHHmmss)"
}
$image = "$Region-docker.pkg.dev/$ProjectId/$Repository/$ServiceName`:$gitSha"

docker buildx build `
    --secret id=openai_api_key,env=OPENAI_API_KEY `
    -t $image `
    .
docker push $image

gcloud run deploy $ServiceName `
    --project $ProjectId `
    --region $Region `
    --platform managed `
    --image $image `
    --allow-unauthenticated `
    --cpu 1 `
    --memory 1Gi `
    --concurrency 10 `
    --timeout 300 `
    --min-instances 0 `
    --max-instances 1 `
    --set-env-vars "OPENAI_CHAT_MODEL=gpt-5-nano,OPENAI_EMBEDDING_MODEL=text-embedding-3-small,CHAT_TEMPERATURE=0,BASE_DIR=/app/back/base,CHROMA_DB_PATH=/app/back/.runtime_chroma_db,CHROMA_COLLECTION=titas_docs" `
    --update-secrets "OPENAI_API_KEY=$SecretName`:latest"

$url = gcloud run services describe $ServiceName --project $ProjectId --region $Region --format="value(status.url)"
Write-Host "Deploy concluido: $url"
Write-Host "Teste rapido: Invoke-RestMethod $url/health"
