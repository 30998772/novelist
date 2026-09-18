"""LangGraph Studio (`langgraph dev`) 的图装配入口。

langgraph.json 中的 graphs 指向本模块:
    "graphs": {"novelist": "./writer_agent/studio.py:novelist_graph"}

注意:
- 工厂函数必须无参可调用, 返回 CompiledStateGraph;
- 这里刻意不传 checkpointer (checkpoint=None), dev server 会注入自己的
  持久化层, 供 Studio 的 thread / time-travel 调试使用;
- .env 由 langgraph.json 的 "env": ".env" 自动加载 (LLM_API_KEY 等)。
"""

from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from .app import build_tools
from .graphs_factory import get_graph_class
from .llm import get_llm


def novelist_llm() -> ChatOpenAI:
    return get_llm()


def novelist_tools() -> list[BaseTool]:
    return build_tools("novelist")


def novelist_graph():
    """构建「小说家」主图 (不带外部 checkpointer, 交给 dev server)。"""
    cls = get_graph_class("novelist")
    graph_obj = cls(
        llm=novelist_llm(),
        tools=novelist_tools(),
        history_len=8,
        checkpoint=None,
    )
    return graph_obj.get_graph()
