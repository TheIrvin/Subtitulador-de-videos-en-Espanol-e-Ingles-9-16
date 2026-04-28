@echo off
title Mini Editor de Subtitulos
cd /d "%~dp0"

start "Backend Subtitulos" cmd /k python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

cd /d "%~dp0frontend"
start "Frontend Subtitulos" cmd /k npm run dev

timeout /t 3 >nul
start http://127.0.0.1:5173
