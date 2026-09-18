"""应用层：把 tools_registry 与 graphs_registry 装配成可调用的 agent。

- build_tools(name): 按图的 tool_names 过滤工具清单（"*" = 全部）。
- create_graph(name, ...): 实例化图类（LLM 默认走 get_llm()）。
- run_agent(name, message, ...): 单轮执行, 返回最终 AI 回复。
"""

import os
from typing import Optional

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver

from . import tools_factory  # noqa: F401  注册全部工具
from . import graphs_factory  # noqa: F401  注册全部图
from .graphs_factory import get_graph_class
from .llm import get_llm
from .tools_factory import list_tools

DEFAULT_HISTORY_LEN = 8


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


def run_agent(name: str, message: str, project_dir: Optional[str] = None,
              llm=None, history_len: int = DEFAULT_HISTORY_LEN, **kwargs) -> str:
    """对指定 agent 图执行一次对话, 返回最终 AI 文本回复。"""
    graph_obj = create_graph(name, llm=llm, history_len=history_len, **kwargs)
    compiled = graph_obj.get_graph()
    initial = {
        "messages": [HumanMessage(content=message)],
        "history": [],
        "agent": name,
        "project_dir": project_dir,
        "intent_list": [],
        "current_intent": "",
        "intent_results": {},
        "clarification_attempts": 0,
        "user_continues": True,
    }
    config = {"configurable": {"thread_id": f"{name}-{os.getpid()}-run"}}
    result = compiled.invoke(initial, config)
    msgs = result.get("messages") or []
    if not msgs:
        return "（无输出）"
    last: BaseMessage = msgs[-1]
    text = getattr(last, "content", "")
    if isinstance(text, list):
        text = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in text
        )
    return str(text).strip() or "（无输出）"
