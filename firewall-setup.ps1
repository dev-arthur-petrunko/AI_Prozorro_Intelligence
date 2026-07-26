# ============================================
# AI Prozorro Intelligence - Відкриття портів
# ============================================
# ЗАПУСТІТЬ ЦЕЙ ФАЙЛ ВІД ІМЕНІ АДМІНІСТРАТОРА:
# 1. Натисніть Win + X -> "Термінал (Адміністратор)"
# 2. Виконайте: powershell -ExecutionPolicy Bypass -File "f:\ПРОЕКТ AI\AI Prozorro Intelligence\firewall-setup.ps1"
#
# Після цього додаток буде доступний з телефона:
#   http://192.168.0.80:3000/uk/dashboard
# (телефон має бути в тій самій Wi-Fi мережі, що й комп'ютер)

Write-Host "Створення правил фаєрвола для AI Prozorro Intelligence..." -ForegroundColor Cyan

# Видалити старі правила, якщо існують
Remove-NetFirewallRule -DisplayName "AI Prozorro Frontend 3000" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "AI Prozorro Backend 8000" -ErrorAction SilentlyContinue

# Frontend (Next.js) - порт 3000
New-NetFirewallRule -DisplayName "AI Prozorro Frontend 3000" `
    -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow -Profile Any | Out-Null
Write-Host "OK Порт 3000 (Frontend) відкрито" -ForegroundColor Green

# Backend (FastAPI) - порт 8000
New-NetFirewallRule -DisplayName "AI Prozorro Backend 8000" `
    -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Any | Out-Null
Write-Host "OK Порт 8000 (Backend) відкрито" -ForegroundColor Green

Write-Host ""
Write-Host "Готово! Відкрийте на телефоні: http://192.168.0.80:3000/uk/dashboard" -ForegroundColor Yellow
Write-Host "(телефон має бути пiдключений до тiєї ж Wi-Fi мережi)" -ForegroundColor Yellow
