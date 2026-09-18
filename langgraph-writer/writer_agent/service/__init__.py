"""Service 层 - session 管理。

- Session: 单个对话会话，包含 thread_id、graph 等
- SessionManager: 管理多个 session
"""

from .session import Session, SessionManager, get_session_manager

__all__ = ["Session", "SessionManager", "get_session_manager"]
