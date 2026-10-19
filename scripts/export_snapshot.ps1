param([string]$Container = 'roamwise-api-1')
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path 'data/processed' | Out-Null
docker cp "${Container}:/data/processed/." 'data/processed'
if ($LASTEXITCODE -ne 0) { throw 'Could not copy the processed snapshot.' }
Write-Host 'Snapshot copied. The cloud image build checks its hashes before indexing.'
