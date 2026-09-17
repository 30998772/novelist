"""图注册中心（对齐 LangGraph-Chatchat graphs_factory/graphs_registry.py）。

每个图转换成一个 Graph 类：
- 类属性 `name` / `label`（"agent" 或 "rag"） / `title` 作为注册键;
- `get_graph()` 返回编译好的 StateGraph;
- `handle_event()` 定义图输出的消息处理。

@register_graph 装饰器负责把图类登记到 `rag_registry` / `agent_registry` 与 `graph_registry`。
"""

from abc import abstractmethod
from typing import Annotated, Optional, Type, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ToolMessage,
    filter_messages,
)
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

from ..state import WriterState

__all__ = [
    "Graph",
    "State",
    "register_graph",
    "get_graph_class",
    "all_graph_names",
    "list_graph_titles_by_label",
    "get_graph_class_by_label_and_title",
    "rag_registry",
    "agent_registry",
    "graph_registry",
]


class State(TypedDict):
    """基础 State 供各类 graph 继承：

    1. messages 为所有 graph 的核心信息队列（add_messages 自动合并）;
    2. history 为单次启动时 history_len 裁剪后的历史上下文（可丢弃）。
    实际业务字段见 writer_agent/state.WriterState。
    """
    messages: Annotated[list[BaseMessage], add_messages]
    history: Optional[list[BaseMessage]]


# 全局字典: graph name -> {class, title}
rag_registry: dict[str, dict] = {}
agent_registry: dict[str, dict] = {}
graph_registry: dict[str, dict] = {}


def register_graph(cls):
    """将图类注册到注册表中。类必须定义 name / label / title 属性。"""
    label = cls.label
    name = cls.name
    title = cls.title

    if label == "rag":
        rag_registry[name] = {"class": cls, "title": title}
    elif label == "agent":
        agent_registry[name] = {"class": cls, "title": title}
    else:
        raise ValueError(f"Unknown label '{label}' for class '{cls.__name__}'.")

    graph_registry[name] = {"class": cls, "title": title}
    return cls


class Graph:
    def __init__(self,
                 llm: ChatOpenAI,
                 tools: list[BaseTool],
                 history_len: int,
                 checkpoint: BaseCheckpointSaver,
                 *args,
                 **kwargs):
        self.llm = llm
        self.tools = tools
        self.history_len = history_len
        self.checkpoint = checkpoint

    @abstractmethod
    def get_graph(self) -> CompiledStateGraph:
        """定义 graph 流程，子类必须实现。"""
        pass

    @abstractmethod
    def handle_event(self, *args, **kwargs):
        """定义 graph 消息返回处理逻辑，子类必须实现。"""
        pass

    def history_manager(self, state: Type[State]) -> Type[State]:
        """给 LLM 传历史时过滤 Tool 与 function-call 消息，只保留最近 history_len 条。"""
        try:
            filtered_messages = []
            for message in filter_messages(state["messages"], exclude_types=[ToolMessage]):
                if isinstance(message, AIMessage) and message.tool_calls:
                    continue
                filtered_messages.append(message)
            state["history"] = filtered_messages[-self.history_len:]
            return state
        except Exception as e:  # noqa: BLE001
            raise Exception(f"Filtering messages error: {e}")

    @staticmethod
    def break_point(state: Type[State]) -> Type[State]:
        """在 graph 中增加断点，暂停 graph。"""
        print("---BREAK POINT---")
        return state

    @staticmethod
    def human_feedback(state: Type[State]) -> Type[State]:
        """获取用户反馈后的处理入口。"""
        print("---HUMAN FEEDBACK---")
        return state

    @staticmethod
    def init_docs(state: Type[State]) -> Type[State]:
        """知识检索后把检索结果提取为 docs，并手动追加入 history。"""
        state["docs"] = state["messages"][-1].content
        if isinstance(state["messages"][-1], ToolMessage):
            state["history"].append(state["messages"][-1])
        return state


def list_graph_titles_by_label(label: str) -> list[str]:
    if label == "rag":
        return [info["title"] for info in rag_registry.values()]
    elif label == "agent":
        return [info["title"] for info in agent_registry.values()]
    raise ValueError(f"Unknown label '{label}'.")


def get_graph_class_by_label_and_title(label: str, title: str) -> Type[Graph]:
    if label == "rag":
        for info in rag_registry.values():
            if info["title"] == title:
                return info["class"]
    elif label == "agent":
        for info in agent_registry.values():
            if info["title"] == title:
                return info["class"]
    raise ValueError(f"No graph found with title '{title}' for label '{label}'.")


def get_graph_class(name: str) -> Type[Graph]:
    if name not in graph_registry:
        raise ValueError(
            f"Graph '{name}' is not registered. Available: {', '.join(graph_registry)}"
        )
    return graph_registry[name]["class"]


def all_graph_names() -> list[str]:
    return list(graph_registry.keys())