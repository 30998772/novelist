"""Writer Backend - FastAPI 服务。

通过 LangGraph HTTP API (port 2024) 与 agent 通信。
"""

import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ── 路径配置 ──────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).parent.resolve()
WRITER_ROOT = BACKEND_DIR.parent
NOVELS_DIR = WRITER_ROOT / "novelist"

# LangGraph Server 地址
LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://localhost:2024")

app = FastAPI(title="Writer Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════════
# 对话 API（通过 LangGraph HTTP API）
# ════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    session_id: str


_sessions: dict[str, list[dict]] = {}
_thread_map: dict[str, str] = {}  # session_id -> thread_id (UUID)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id
    history = _sessions.get(session_id, [])
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": req.message})

    # 获取或创建 thread UUID
    if session_id not in _thread_map:
        _thread_map[session_id] = str(uuid.uuid4())
    thread_id = _thread_map[session_id]

    async with httpx.AsyncClient(timeout=120) as client:
        # 创建 thread
        await client.post(f"{LANGGRAPH_URL}/threads", json={"thread_id": thread_id})

        # 创建 run
        resp = await client.post(
            f"{LANGGRAPH_URL}/threads/{thread_id}/runs",
            json={
                "assistant_id": "novelist",
                "input": {"messages": messages},
            },
        )
        run = resp.json()
        run_id = run.get("run_id")
        if not run_id:
            raise HTTPException(500, f"创建 run 失败: {run}")

        # 轮询等待完成
        for _ in range(120):
            await asyncio.sleep(1)
            status_resp = await client.get(f"{LANGGRAPH_URL}/threads/{thread_id}/runs/{run_id}")
            status = status_resp.json()
            if status.get("status") == "success":
                break
            elif status.get("status") == "error":
                raise HTTPException(500, f"Agent error: {status}")

        # 获取最终状态
        state_resp = await client.get(f"{LANGGRAPH_URL}/threads/{thread_id}/state")
        state = state_resp.json()

    # 提取最后一条 AI 消息
    reply = ""
    for msg in reversed(state.get("values", {}).get("messages", [])):
        if msg.get("type") == "ai" and msg.get("content"):
            reply = msg["content"]
            break

    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply})
    _sessions[session_id] = history

    return ChatResponse(reply=reply, session_id=session_id)


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    session_id = req.session_id
    history = _sessions.get(session_id, [])
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": req.message})

    if session_id not in _thread_map:
        _thread_map[session_id] = str(uuid.uuid4())
    thread_id = _thread_map[session_id]

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(300, connect=10)) as client:
                # 创建 thread
                await client.post(f"{LANGGRAPH_URL}/threads", json={"thread_id": thread_id})

                # 创建 run，使用 stream_mode=["messages"] 获取 SSE 流
                full_reply = []
                async with client.stream(
                    "POST",
                    f"{LANGGRAPH_URL}/threads/{thread_id}/runs",
                    json={
                        "assistant_id": "novelist",
                        "input": {"messages": messages},
                        "stream_mode": ["messages"],
                    },
                ) as resp:
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        try:
                            data = json.loads(line[6:])
                        except json.JSONDecodeError:
                            continue

                        # messages stream 事件
                        event = data.get("event")
                        if event == "on_chat_model_stream":
                            content = data.get("data", {}).get("chunk", {}).get("content", "")
                            if content:
                                full_reply.append(content)
                                yield f"data: {json.dumps({'chunk': content, 'node': 'llm'})}\n\n"
                        elif event == "on_tool_start":
                            tool_name = data.get("name", "")
                            yield f"data: {json.dumps({'status': f'调用工具: {tool_name}'})}\n\n"
                        elif event == "on_tool_end":
                            yield f"data: {json.dumps({'status': '工具执行完毕'})}\n\n"
                        elif event == "error":
                            yield f"data: {json.dumps({'error': str(data)})}\n\n"

                # 存储历史
                final = "".join(full_reply)
                history.append({"role": "user", "content": req.message})
                history.append({"role": "assistant", "content": final})
                _sessions[session_id] = history

            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/sessions")
async def list_sessions():
    return {"sessions": list(_sessions.keys())}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    history = _sessions.get(session_id, [])
    return {"session_id": session_id, "history": history}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"ok": True}


# ════════════════════════════════════════════════════════════════
# 文件管理 API
# ════════════════════════════════════════════════════════════════

@app.get("/api/files")
async def list_files(directory: str = ""):
    root = NOVELS_DIR / directory if directory else NOVELS_DIR
    if not root.exists():
        return {"root": directory or ".", "items": []}

    def _scan(path: Path, rel: str = "") -> list[dict]:
        items = []
        for p in sorted(path.iterdir()):
            if p.name.startswith(".") or p.name == "__pycache__":
                continue
            rel_path = f"{rel}/{p.name}" if rel else p.name
            if p.is_dir():
                items.append({
                    "name": p.name,
                    "path": rel_path,
                    "type": "directory",
                    "children": _scan(p, rel_path),
                })
            else:
                items.append({
                    "name": p.name,
                    "path": rel_path,
                    "type": "file",
                    "size": p.stat().st_size,
                })
        return items

    return {"root": directory or ".", "items": _scan(root)}


@app.get("/api/files/read")
async def read_file(path: str):
    target = NOVELS_DIR / path
    if not target.exists():
        raise HTTPException(404, f"文件不存在: {path}")
    try:
        content = target.read_text(encoding="utf-8")
        return {"path": path, "content": content}
    except Exception as e:
        raise HTTPException(500, f"读取失败: {e}")


@app.get("/api/health")
async def health():
    return {"status": "ok", "novels_dir": str(NOVELS_DIR), "langgraph_url": LANGGRAPH_URL}
