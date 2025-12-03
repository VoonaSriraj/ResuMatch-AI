@echo off
echo Starting JobAlign Backend...
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
