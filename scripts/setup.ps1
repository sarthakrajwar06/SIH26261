$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
py -3.11 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 is required" }
& .\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Backend dependency installation failed" }
npm --prefix frontend ci
if ($LASTEXITCODE -ne 0) { throw "Frontend dependency installation failed" }
if (!(Test-Path .env)) { Copy-Item .env.example .env }
Write-Host "Edit .env, apply Supabase migration and seed.sql, then provision Auth profiles. See README.md."
Write-Host "For scanned files install Tesseract separately and add tesseract.exe to PATH."
