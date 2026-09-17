"""应用层：把 tools_registry 与 graphs_registry 装配成可调用的 agent。

- build_tools(name): 按图的 tool_names 过滤工具清单（"*" = 全部）。
- create_graph(name, ...): 实例化图类（LLM 默认走 get_llm()）。
- run_agent(name, message, ...): 一次性执行, 返回最终 AI 回复。
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
    """对指定 agent 图执行一次对话, 返回最终 AI 文本回复。

    writer_workflow 图则把 message 当作创作任务, 从 start 到 end 跑流水线。
    """
    cls = get_graph_class(name)
    # start/end 只对区间流水线有意义: 其余图不接收这两个参数, 统一在此剥离,
    # 否则 cli / mcp 传入的 start/end 会落到图构造函数上而报 TypeError。
    start = kwargs.pop("start", "research")
    end = kwargs.pop("end", "finalize")

    if cls.name == "writer_workflow":
        from .graph_builder import run_interval

        result = run_interval(
            {"task": message, "input_data": kwargs.pop("input_data", {}),
             "iteration": 0, "max_iterations": 3, "messages": [],
             "project_dir": project_dir},
            start=start,
            end=end,
        )
        for key in ("final_content", "draft", "outline", "research_notes"):
            if result.get(key):
                return result[key]
        return "（流水线无输出）"

    graph_obj = create_graph(name, llm=llm, history_len=history_len, **kwargs)
    compiled = graph_obj.get_graph()
    initial = {
        "messages": [HumanMessage(content=message)],
        "history": [],
        "agent": name,
        "project_dir": project_dir,
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