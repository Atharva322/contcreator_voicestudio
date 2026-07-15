$ErrorActionPreference = "Stop"

Write-Host "Starting Creator Voice Studio locally..." -ForegroundColor Cyan
Write-Host "API: http://localhost:8000" -ForegroundColor DarkCyan
Write-Host "Web: http://localhost:3000" -ForegroundColor DarkCyan

$root = Split-Path -Parent $PSScriptRoot

$api = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root'; npm run dev:api"
) -PassThru

Start-Sleep -Seconds 2

$web = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root'; npm run dev:web"
) -PassThru

Write-Host "Started API process $($api.Id) and web process $($web.Id)." -ForegroundColor Green
Write-Host "Keep both terminal windows open while using the demo." -ForegroundColor Yellow
