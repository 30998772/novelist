#!/bin/bash
# Writer 一键启动脚本
# 用法: bash start.sh

set -e

WRITER_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$WRITER_ROOT/langgraph-writer/.venv"

echo "=== Writer Agent 启动中 ==="

# 激活虚拟环境
source "$VENV/bin/activate"

# 1. 启动 LangGraph Server (端口 2024)
echo "[1/3] 启动 LangGraph Server..."
cd "$WRITER_ROOT/langgraph-writer"
langgraph dev --port 2024 &
LANGGRAPH_PID=$!
sleep 3

# 2. 启动 FastAPI 后端 (端口 8000, --reload 热更新)
echo "[2/3] 启动 FastAPI 后端..."
cd "$WRITER_ROOT/writer-backend"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
sleep 2

# 3. 启动前端 (端口 3000)
echo "[3/3] 启动前端..."
cd "$WRITER_ROOT/writer-frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== 启动完成 ==="
echo "  前端:    http://localhost:3000"
echo "  后端:    http://localhost:8000/docs"
echo "  LangGraph: http://localhost:2024"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $LANGGRAPH_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
