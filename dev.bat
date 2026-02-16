@echo off
setlocal
set "ROOT=%~dp0"

echo ================================================
echo   ModelTrain Platform - Dev Launcher
echo ================================================
echo.

:: [1/3] Dify (via dify/docker docker-compose)
echo [1/3] Starting Dify...
docker version >nul 2>&1
if errorlevel 1 (
    echo       [SKIP] Docker not available, Dify will not start.
    goto start_backend
)
set "DIFY_DIR=%ROOT%dify\docker"
set "DIFY_PROXY_CONF=%DIFY_DIR%\nginx\proxy.conf.template"
if exist "%DIFY_PROXY_CONF%" (
    findstr /c:"proxy_hide_header X-Frame-Options;" "%DIFY_PROXY_CONF%" >nul 2>nul
    if errorlevel 1 (
        echo       Patching Dify nginx proxy to allow iframe...
        powershell -NoProfile -Command "\$f='%DIFY_PROXY_CONF%';\$c=Get-Content \$f -Raw;if(-not \$c.Contains('proxy_hide_header X-Frame-Options;')){\$c=\$c -replace 'proxy_buffering off;','proxy_buffering off;`r`nproxy_hide_header X-Frame-Options;';Set-Content -Path \$f -Value \$c -Encoding UTF8;}"
    )
)
if not exist "%DIFY_DIR%\.env" if exist "%DIFY_DIR%\.env.example" (
    copy "%DIFY_DIR%\.env.example" "%DIFY_DIR%\.env" >nul 2>nul
    echo       Created .env from .env.example
)
docker ps --filter "name=docker-nginx-1" --format "{{.Names}}" 2>nul | findstr /i "nginx" >nul 2>nul
if errorlevel 1 (
    echo       Starting Dify containers...
    cd /d "%DIFY_DIR%"
    docker compose up -d
    cd /d "%ROOT%"
    echo       Dify started.
) else (
    echo       Dify already running.
)
echo.

:: [2/4] SwanLab demo data
set "SL_DIR=%ROOT%backend\swanlab_data"
if not exist "%SL_DIR%\" mkdir "%SL_DIR%" >nul 2>nul
dir /b "%SL_DIR%" 2>nul | findstr "." >nul 2>nul
if errorlevel 1 (
    echo [2/4] Generating SwanLab demo data...
    python "%ROOT%backend\seed_swanlab_demo.py" "%SL_DIR%"
    echo.
) else (
    echo [2/4] SwanLab data exists, skip seeding.
    echo.
)

:: [3/4] Backend (local)
:start_backend
echo [3/4] Starting Backend (FastAPI :8000)...
start "modeltrain-backend" /d "%ROOT%backend" cmd /k "pip install -r requirements.txt -q 2>nul && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo       Backend started in new window.
echo.

:: [4/4] Frontend (local)
echo [4/4] Starting Frontend (Vue3 :5173)...
start "modeltrain-frontend" /d "%ROOT%frontend" cmd /k "npm install --silent 2>nul && npm run dev"
echo       Frontend started in new window.
echo.

echo ================================================
echo   All services launched!
echo.
echo   Frontend:       http://localhost:5173
echo   Backend API:    http://localhost:8000
echo   API Docs:       http://localhost:8000/docs
echo   Dify Console:   http://localhost
echo   LLaMA-Factory:  http://localhost:7860  (auto via backend)
echo   SwanLab:        http://localhost:5092  (auto via backend)
echo ================================================
echo.
echo   Press Q to stop all services and exit.
echo.

:wait
choice /c QR /t 3600 /d R /n >nul
if errorlevel 1 goto cleanup
goto wait

:cleanup
echo.
echo   Stopping services...
taskkill /fi "WINDOWTITLE eq modeltrain-backend*" /f >nul 2>nul
taskkill /fi "WINDOWTITLE eq modeltrain-frontend*" /f >nul 2>nul
docker version >nul 2>&1 && (
    echo   Stopping Dify containers...
    cd /d "%ROOT%dify\docker"
    docker compose down >nul 2>nul
)
echo   All services stopped.
timeout /t 2 >nul
endlocal
