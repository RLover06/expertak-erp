@echo off
REM Run FastAPI in a stable mode (no auto-reload).
set "BACKEND_DIR=%~dp0"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir "%BACKEND_DIR%"
