# Раздача Flutter Web для Telegram Desktop на ЭТОМ же ПК.
# Перед первым запуском: cd frontend && flutter build web
# Затем: WEB_APP_URL=http://127.0.0.1:8080 в backend/.env

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$web = Join-Path $root "frontend\build\web"
if (-not (Test-Path (Join-Path $web "index.html"))) {
    Write-Host "Нет сборки. Выполните: cd frontend; flutter build web" -ForegroundColor Yellow
    exit 1
}
Set-Location $web
Write-Host "Откройте в Telegram Desktop бота с кнопкой Web App. URL статики: http://127.0.0.1:8080" -ForegroundColor Green
python -m http.server 8080 --bind 127.0.0.1
