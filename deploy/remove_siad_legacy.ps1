param(
    [string]$ProjectId = "siadon"
)

$ErrorActionPreference = "Stop"

Write-Host "Removendo recursos legados do SIAD em $ProjectId..."

$vm = gcloud compute instances describe siadon-api-vm --project $ProjectId --zone us-central1-a --format="value(name)" 2>$null
if ($vm) {
    gcloud compute instances delete siadon-api-vm --project $ProjectId --zone us-central1-a --quiet
}

$ip = gcloud compute addresses describe siadon-api-ip --project $ProjectId --region us-central1 --format="value(name)" 2>$null
if ($ip) {
    gcloud compute addresses delete siadon-api-ip --project $ProjectId --region us-central1 --quiet
}

foreach ($rule in @("allow-iap-ssh-siadon", "allow-siadon-3000", "allow-siadon-8080")) {
    $exists = gcloud compute firewall-rules describe $rule --project $ProjectId --format="value(name)" 2>$null
    if ($exists) {
        gcloud compute firewall-rules delete $rule --project $ProjectId --quiet
    }
}

$sql = gcloud sql instances describe free-trial-first-project --project $ProjectId --format="value(name)" 2>$null
if ($sql) {
    gcloud sql instances delete free-trial-first-project --project $ProjectId --quiet
}

Write-Host "Limpeza legada concluida."
