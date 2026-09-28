"""Session 管理模块。

- Session: 单个对话会话，包含 thread_id、graph、state 等
- SessionManager: 管理多个 session，支持创建、查询、删除

子图逐步确认：send() 跑到下一个子图确认点会返回确认话术，
此时调用 Session.confirm(decision) 回复后继续。
"""

from typing import Any, Optional
from uuid import uuid4

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from ..app import _initial_state, _invoke, create_graph


class Session:
    """单个对话会话，支持逐步确认子图产出。"""

    def __init__(self, agent_name: str, session_id: Optional[str] = None,
                 project_dir: Optional[str] = None):
        self.session_id = session_id or str(uuid4())
        self.agent_name = agent_name
        self.project_dir = project_dir
        self.thread_id = f"{agent_name}-{self.session_id}"
        self.checkpointer = MemorySaver()
        self.graph = create_graph(agent_name, checkpointer=self.checkpointer)
        self.compiled = self.graph.get_graph()
        self.config = {"configurable": {"thread_id": self.thread_id}}
        self.pending = False
        self.last_result: dict[str, Any] = {}

    # ------------------------------------------------------------------
    def _run(self, payload) -> dict[str, Any]:
        out = _invoke(self.compiled, payload, self.config)
        self.pending = out["status"] == "confirm"
        self.last_result = out
        return out

    @staticmethod
    def _reply_text(out: dict[str, Any]) -> str:
        if out["status"] != "confirm":
            return out["reply"]
        q = out["question"] or {}
        return (f"【第 {q.get('step', '?')} 步｜{q.get('intent', '?')}】已完成，请确认\n"
                f"任务：{q.get('task', '')}\n"
                f"产出：{q.get('result', '')}\n"
                f"剩余步骤：{'、'.join(q.get('remaining') or []) or '无'}\n"
                f"可回复：{' / '.join(q.get('options') or {})}")

    # ------------------------------------------------------------------
    def send(self, message: str) -> str:
        """发送消息。跑到子图确认点会返回确认话术，待确认时调用 confirm()。"""
        if self.pending:
            return self.confirm(message)
        out = self._run(_initial_state(self.agent_name, message, self.project_dir))
        return self._reply_text(out)

    def confirm(self, decision: str = "通过") -> str:
        """回复一次子图确认并继续跑；当前没有待确认时原样返回上次结果。"""
        if not self.pending:
            return self._reply_text(self.last_result or {"status": "done", "reply": "（无输出）"})
        return self._reply_text(self._run(Command(resume=decision)))

    def auto_confirm(self, decision: str = "通过", limit: int = 20) -> str:
        """一口气通过所有剩余确认，返回最终回复。"""
        out = self.last_result
        n = 0
        while self.pending and n < limit:
            n += 1
            out = self._run(Command(resume=decision))
        return self._reply_text(out or {"status": "done", "reply": "（无输出）"})

    def reset(self):
        """重置会话。"""
        self.checkpointer = MemorySaver()
        self.graph = create_graph(self.agent_name, checkpointer=self.checkpointer)
        self.compiled = self.graph.get_graph()
        self.pending = False
        self.last_result = {}

class SessionManager:
    """管理多个 session。"""
    
    def __init__(self):
        self.sessions: dict[str, Session] = {}
    
    def create_session(self, agent_name: str, project_dir: Optional[str] = None) -> Session:
        """创建新 session。"""
        session = Session(agent_name, project_dir=project_dir)
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取 session。"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """删除 session。"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> list[dict]:
        """列出所有 session。"""
        return [
            {
                "session_id": s.session_id,
                "agent_name": s.agent_name,
                "project_dir": s.project_dir,
            }
            for s in self.sessions.values()
        ]


# 全局 session 管理器
_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """获取全局 session 管理器。"""
    return _manager
