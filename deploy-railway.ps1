# Agora Railway Deployment Script
# Run this script in PowerShell (interactive terminal)

Write-Host "=== AGORA RAILWAY DEPLOYMENT ===" -ForegroundColor Cyan
Write-Host ""

# Check Railway login
Write-Host "1. Sprawdzam status Railway..." -ForegroundColor Yellow
railway whoami
railway status

Write-Host ""
Write-Host "2. Dodawanie MongoDB..." -ForegroundColor Yellow
Write-Host "   Wybierz: Database -> mongo" -ForegroundColor Gray
railway add -d mongo

Write-Host ""
Write-Host "3. Dodawanie Redis..." -ForegroundColor Yellow
Write-Host "   Wybierz: Database -> redis" -ForegroundColor Gray
railway add -d redis

Write-Host ""
Write-Host "4. Tworzenie serwisu Backend..." -ForegroundColor Yellow
Write-Host "   Wybierz: Empty Service, nazwa: backend" -ForegroundColor Gray
railway add -s backend

Write-Host ""
Write-Host "5. Tworzenie serwisu Frontend..." -ForegroundColor Yellow
Write-Host "   Wybierz: Empty Service, nazwa: frontend" -ForegroundColor Gray
railway add -s frontend

Write-Host ""
Write-Host "=== SERWISY UTWORZONE ===" -ForegroundColor Green
Write-Host ""
Write-Host "Teraz uruchom ponownie Claude Code i powiedz:" -ForegroundColor Cyan
Write-Host "'kontynuuj deployment na railway'" -ForegroundColor White
Write-Host ""
