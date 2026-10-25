$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
if (Test-Path .pids.json) { throw "A startup record exists. Run scripts/stop.ps1 first." }
if (!(Test-Path .env)) { throw "Run setup.ps1 and configure .env first." }
$backend = Start-Process -FilePath "$root\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend" -WorkingDirectory $root -PassThru
$frontend = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm --prefix frontend run dev" -WorkingDirectory $root -PassThru
@{ backend=$backend.Id; frontend=$frontend.Id } | ConvertTo-Json | Set-Content .pids.json
Write-Host "Frontend http://localhost:5173 | API http://localhost:8000/docs"
