param([switch]$Stop)
$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $repoPath
try {
    if ($Stop) {
        docker compose --profile share stop tunnel
        if ($LASTEXITCODE -ne 0) { throw 'Could not stop the sharing tunnel.' }
        return
    }
    try {
        $health = Invoke-RestMethod 'http://localhost:8080/api/health' -TimeoutSec 5
    } catch {
        throw 'Start the app first: docker compose up --build -d. Wait until the API is healthy, then run this script again.'
    }
    docker compose --profile share up -d --no-deps tunnel
    if ($LASTEXITCODE -ne 0) { throw 'Could not start the sharing tunnel.' }
    $tunnelId = docker compose ps -q tunnel
    if (-not $tunnelId) { throw 'The sharing container is not running.' }
    $startedAt = docker inspect --format '{{.State.StartedAt}}' $tunnelId
    if ($LASTEXITCODE -ne 0) { throw 'Could not read the sharing container start time.' }
    $liveUrl = $null
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        # A restarted container keeps old logs; only use the current session's URL.
        $tunnelLog = (docker compose logs --no-color --since $startedAt tunnel 2>&1 | Out-String)
        $matchesFound = [regex]::Matches($tunnelLog, 'https://[-a-z0-9]+\.trycloudflare\.com')
        if ($matchesFound.Count -gt 0) { $liveUrl = $matchesFound[$matchesFound.Count - 1].Value; break }
        Start-Sleep -Seconds 1
    }
    if (-not $liveUrl) { throw 'No public URL yet. Inspect: docker compose logs tunnel' }
    $linkRecord = @{
        url = $liveUrl
        checked_at = [DateTime]::UtcNow.ToString('o')
        note = 'Temporary live demo. Requires the host computer and Docker tunnel to remain running.'
    } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $repoPath 'share/live.json'), $linkRecord + "`n", [Text.UTF8Encoding]::new($false))
    Write-Host "Live search: $liveUrl"
    Write-Host 'Keep this computer awake and Docker running. Restarting the tunnel can change the URL.'
    Write-Host 'If the URL changed, share it directly or commit/push share/live.json to main to update the showcase button.'
    Write-Host 'Stop sharing: .\scripts\share.ps1 -Stop'
} finally { Pop-Location }
