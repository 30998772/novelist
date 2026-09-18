"""Session 管理模块。

- Session: 单个对话会话，包含 thread_id、graph、state 等
- SessionManager: 管理多个 session，支持创建、查询、删除
"""

import os
from typing import Optional
from uuid import uuid4

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from ..app import create_graph, run_agent


class Session:
    """单个对话会话。"""
    
    def __init__(self, agent_name: str, session_id: Optional[str] = None,
                 project_dir: Optional[str] = None):
        self.session_id = session_id or str(uuid4())
        self.agent_name = agent_name
        self.project_dir = project_dir
        self.thread_id = f"{agent_name}-{self.session_id}"
        self.checkpointer = MemorySaver()
        self.graph = create_graph(agent_name, checkpointer=self.checkpointer)
        self.compiled = self.graph.get_graph()
        
        # 初始状态
        self.initial_state = {
            "messages": [],
            "history": [],
            "agent": agent_name,
            "project_dir": project_dir,
            "intent_list": [],
            "current_intent": "",
            "intent_results": {},
            "clarification_attempts": 0,
            "user_continues": True,
        }
    
    def send(self, message: str) -> str:
        """发送消息，返回 AI 回复。"""
        config = {"configurable": {"thread_id": self.thread_id}}
        
        # 添加用户消息
        if self.initial_state["messages"]:
            self.initial_state["messages"].append(HumanMessage(content=message))
        else:
            self.initial_state["messages"] = [HumanMessage(content=message)]
        
        # 执行图
        result = self.compiled.invoke(self.initial_state, config)
        
        # 更新状态
        self.initial_state.update(result)
        
        # 获取最后一条 AI 消息
        msgs = result.get("messages") or []
        if not msgs:
            return "（无输出）"
        
        last = msgs[-1]
        text = getattr(last, "content", "")
        if isinstance(text, list):
            text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in text
            )
        return str(text).strip() or "（无输出）"
    
    def reset(self):
        """重置会话。"""
        self.checkpointer = MemorySaver()
        self.graph = create_graph(self.agent_name, checkpointer=self.checkpointer)
        self.compiled = self.graph.get_graph()
        self.initial_state = {
            "messages": [],
            "history": [],
            "agent": self.agent_name,
            "project_dir": self.project_dir,
            "intent_list": [],
            "current_intent": "",
            "intent_results": {},
            "clarification_attempts": 0,
            "user_continues": True,
        }


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
