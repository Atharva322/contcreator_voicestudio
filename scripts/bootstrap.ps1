$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

$PythonBin = Join-Path $RootDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonBin)) {
    $PythonBin = Join-Path $RootDir ".venv\bin\python"
}

& $PythonBin -m pip install --upgrade pip
& $PythonBin -m pip install -r apps/api/requirements.txt

npm ci --prefix apps/web

if (-not (Test-Path "apps/api/.env")) {
    Copy-Item "apps/api/.env.example" "apps/api/.env"
}

if (-not (Test-Path "apps/web/.env.local")) {
    Copy-Item "apps/web/.env.example" "apps/web/.env.local"
}

Write-Host ""
Write-Host "Bootstrap complete."
Write-Host ""
Write-Host "Next:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  npm run dev:api"
Write-Host "  npm run dev:web"
Write-Host ""
Write-Host "Validate:"
Write-Host "  npm run verify"
