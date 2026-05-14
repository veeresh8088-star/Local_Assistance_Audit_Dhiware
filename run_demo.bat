@echo off
title AICyberAuditBox Demo Launcher
echo ==========================================
echo    AICyberAuditBox - Presentation Mode
echo ==========================================

echo.
echo [1/3] Checking Ollama (AI Engine)...
powershell -Command "try { $r = Invoke-WebRequest -Uri http://localhost:11434/api/tags -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if %errorlevel% neq 0 (
    echo [!] WARNING: Ollama is not running on port 11434.
    echo     The AI Assistant will be disabled.
    echo     Please start Ollama if you need AI features.
    echo.
    pause
) else (
    echo [v] OK: Ollama is active.
)

echo.
echo [2/3] Checking Database (ShaktiDB)...
docker ps > nul 2>&1
if %errorlevel% equ 0 (
    echo [v] OK: Docker is running. Starting ShaktiDB container...
    docker-compose up -d
) else (
    echo [i] NOTE: Docker Desktop not detected. 
    echo     The system will automatically use 'shakthidb_local.db' ^(SQLite^).
)

echo.
echo [3/3] Launching Dashboard...
echo Installing/Updating dependencies...
pip install -r requirements.txt --quiet
python -m streamlit run app.py --server.port 8501
