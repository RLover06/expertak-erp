$ErrorActionPreference = "Stop"

# Run FastAPI in a stable mode (no auto-reload).
$backendDir = $PSScriptRoot
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir "$backendDir"
