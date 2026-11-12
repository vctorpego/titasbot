param(
    [string]$ProjectId = "siadon",
    [string]$Region = "us-central1",
    [string]$Repository = "titasbot",
    [string]$Package = "titasbot",
    [int]$Keep = 1
)

$ErrorActionPreference = "Stop"

$packageUrl = "$Region-docker.pkg.dev/$ProjectId/$Repository/$Package"
$images = gcloud artifacts docker images list $packageUrl --include-tags --format=json | ConvertFrom-Json
$taggedImages = $images |
    Where-Object { $_.tags -and $_.tags.Count -gt 0 } |
    Sort-Object updateTime -Descending |
    Select-Object -Skip $Keep

foreach ($image in $taggedImages) {
    foreach ($tag in $image.tags) {
        if ($tag) {
            gcloud artifacts docker images delete "$packageUrl`:$tag" --delete-tags --quiet
        }
    }
}
