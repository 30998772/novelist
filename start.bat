@echo off
REM Writer 一键启动脚本 (Windows)
REM 用法: 双击 start.bat

set WRITER_ROOT=%~dp0

echo === Writer Agent 启动中 ===

REM 激活虚拟环境
call "%WRITER_ROOT%langgraph-writer\.venv\Scripts\activate.bat"

REM 1. 启动 LangGraph Server
echo [1/3] 启动 LangGraph Server...
cd /d "%WRITER_ROOT%langgraph-writer"
start "LangGraph" cmd /k "langgraph dev --port 2024"
timeout /t 4 /nobreak >nul

REM 2. 启动 FastAPI 后端
echo [2/3] 启动 FastAPI 后端...
cd /d "%WRITER_ROOT%writer-backend"
start "Writer Backend" cmd /k "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul

REM 3. 启动前端
echo [3/3] 启动前端...
cd /d "%WRITER_ROOT%writer-frontend"
start "Writer Frontend" cmd /k "npm run dev"

echo.
echo === 启动完成 ===
echo   前端:      http://localhost:3000
echo   后端:      http://localhost:8000/docs
echo   LangGraph: http://localhost:2024
echo.
pause
