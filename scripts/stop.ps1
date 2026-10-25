$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (Test-Path .pids.json) {
    $record = Get-Content .pids.json | ConvertFrom-Json
    foreach ($idValue in @($record.backend, $record.frontend)) {
        # Stop only tracked process trees, never every Python/Node process on the machine.
        if (Get-Process -Id $idValue -ErrorAction SilentlyContinue) { taskkill /PID $idValue /T /F }
    }
    Remove-Item .pids.json
    Write-Host "Stopped tracked development processes."
} else { Write-Host "No tracked development processes." }
