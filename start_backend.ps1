Write-Host "Starting JobAlign Backend..." -ForegroundColor Green
Set-Location backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
