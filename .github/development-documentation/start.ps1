# Kassensoftware Startup Script für Windows
Write-Host "=================================================="
Write-Host "    Kassensoftware - Docker Startup" -ForegroundColor Cyan
Write-Host "=================================================="
Write-Host ""

# Start containers
Write-Host "Container werden gestartet..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "SUCCESS: Container erfolgreich gestartet!" -ForegroundColor Green
Write-Host ""
Write-Host "=================================================="
Write-Host "ZUGRIFF:" -ForegroundColor Green
Write-Host "=================================================="
Write-Host ""
Write-Host "Frontend:     http://localhost:8000" -ForegroundColor Yellow
Write-Host "API Health:   http://localhost:8000/api/health" -ForegroundColor Yellow
Write-Host "Login:        admin / admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "=================================================="
Write-Host "BEFEHLE:" -ForegroundColor Green
Write-Host "=================================================="
Write-Host ""
Write-Host "Logs verfolgen:    docker logs -f kassensoftware-app" -ForegroundColor Gray
Write-Host "Container stop:    docker-compose down" -ForegroundColor Gray
Write-Host ""
Write-Host "=================================================="
