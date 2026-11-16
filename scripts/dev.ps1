# Sobe o ambiente de desenvolvimento local.
#   powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
& ".\.venv\Scripts\python.exe" -m pip install --quiet -U --pre "yt-dlp[default]"

Write-Host "`nServidor em http://127.0.0.1:8000`n" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
