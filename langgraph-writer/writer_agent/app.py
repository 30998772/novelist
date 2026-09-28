"""应用层：把 tools_registry 与 graphs_registry 装配成可调用的 agent。

- build_tools(name): 按图的 tool_names 过滤工具清单（"*" = 全部）。
- create_graph(name, ...): 实例化图类（LLM 默认走 get_llm()）。
- start_agent(name, ...): 执行一轮，遇到子图确认时返回确认请求。
- resume_agent(name, thread_id, decision): 回复确认，继续跑。
- run_agent(name, ...): 单轮跑到底（自动通过所有确认），返回最终 AI 回复。
"""

import os
from typing import Any, Optional
from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from . import tools_factory  # noqa: F401  注册全部工具
from . import graphs_factory  # noqa: F401  注册全部图
from .graphs_factory import get_graph_class
from .llm import get_llm
from .tools_factory import list_tools

DEFAULT_HISTORY_LEN = 8

# checkpointer 必须跨调用存活，interrupt 暂停后还要能恢复
_CHECKPOINTERS: dict[str, MemorySaver] = {}


def _checkpointer_for(thread_id: str) -> MemorySaver:
    """按 thread_id 取/建 checkpointer，保证 interrupt 后能恢复。"""
    if thread_id not in _CHECKPOINTERS:
        _CHECKPOINTERS[thread_id] = MemorySaver()
    return _CHECKPOINTERS[thread_id]


def _msg_text(msg: BaseMessage) -> str:
    text = getattr(msg, "content", "")
    if isinstance(text, list):
        text = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in text
        )
    return str(text).strip()


def build_tools(name: str) -> list[BaseTool]:
    """按 graph.tool_names 过滤工具清单。"""
    cls = get_graph_class(name)
    tool_names = getattr(cls, "tool_names", None)
    tools = list_tools()
    if tool_names and tool_names != ["*"]:
        matched = {t for t in tool_names}
        tools = [t for t in tools if t.name in matched]
    return tools


def create_graph(name, llm=None, history_len: int = DEFAULT_HISTORY_LEN,
                 checkpointer=None, **kwargs):
    """实例化图类。LLM 缺省用环境变量配置; checkpoint 缺省 MemorySaver。"""
    cls = get_graph_class(name)
    if llm is None:
        llm = get_llm()
    if checkpointer is None:
        checkpointer = MemorySaver()
    tools = build_tools(name)
    return cls(llm=llm, tools=tools, history_len=history_len,
               checkpoint=checkpointer, **kwargs)


def _initial_state(name: str, message: str, project_dir: Optional[str]) -> dict:
    return {
        "messages": [HumanMessage(content=message)],
        "history": [],
        "agent": name,
        "project_dir": project_dir,
        "plan": [],
        "intent_list": [],
        "current_intent": "",
        "intent_index": 0,
        "intent_results": {},
        "clarification_attempts": 0,
        "user_continues": True,
        "pending_confirm": {},
        "step_feedback": {},
        "step_attempts": {},
        "retry_current": False,
    }


def _invoke(compiled, payload, config) -> dict:
    """执行图并把 interrupt 结果规整成统一结构。"""
    result = compiled.invoke(payload, config)
    interrupts = result.get("__interrupt__") or []
    reply = ""
    msgs = result.get("messages") or []
    if msgs:
        reply = _msg_text(msgs[-1])
    if interrupts:
        return {
            "status": "confirm",
            "question": interrupts[0].value,
            "reply": "",
            "thread_id": config["configurable"]["thread_id"],
        }
    return {
        "status": "done",
        "question": None,
        "reply": reply or "（无输出）",
        "thread_id": config["configurable"]["thread_id"],
    }


def start_agent(name: str, message: str, project_dir: Optional[str] = None,
                llm=None, history_len: int = DEFAULT_HISTORY_LEN,
                thread_id: Optional[str] = None, **kwargs) -> dict[str, Any]:
    """执行一轮；每个子图跑完会返回一次确认请求。

    返回 {"status": "confirm", "question": {...}} 时，调用方需确认后调用
    resume_agent(thread_id, decision) 继续。
    """
    thread_id = thread_id or f"{name}-{os.getpid()}-{uuid4().hex[:8]}"
    graph_obj = create_graph(name, llm=llm, history_len=history_len,
                             checkpointer=_checkpointer_for(thread_id), **kwargs)
    compiled = graph_obj.get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    return _invoke(compiled, _initial_state(name, message, project_dir), config)


def resume_agent(name: str, thread_id: str, decision: Any = "通过",
                 **kwargs) -> dict[str, Any]:
    """回复一次子图确认并继续执行。"""
    graph_obj = create_graph(name, checkpointer=_checkpointer_for(thread_id), **kwargs)
    compiled = graph_obj.get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    return _invoke(compiled, Command(resume=decision), config)


def run_agent(name: str, message: str, project_dir: Optional[str] = None,
              llm=None, history_len: int = DEFAULT_HISTORY_LEN,
              max_auto_confirm: int = 20, **kwargs) -> str:
    """单轮执行到底（自动通过所有子图确认），返回最终 AI 文本回复。

    需要人工逐步确认的场景请改用 start_agent / resume_agent。
    """
    thread_id = f"{name}-{os.getpid()}-run-{uuid4().hex[:8]}"
    graph_obj = create_graph(name, llm=llm, history_len=history_len,
                             checkpointer=_checkpointer_for(thread_id), **kwargs)
    compiled = graph_obj.get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    out = _invoke(compiled, _initial_state(name, message, project_dir), config)
    auto = 0
    while out["status"] == "confirm" and auto < max_auto_confirm:
        auto += 1
        out = resume_agent(name, thread_id, "通过", **kwargs)
    if out["status"] == "confirm":
        out["reply"] = f"（自动确认次数用尽，仍在等待确认：{out['question']}）"
    return out["reply"]

