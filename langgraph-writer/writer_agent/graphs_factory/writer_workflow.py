"""graph —— 区间式创作流水线 agent（保留原有 research→outline→draft→review→revise→finalize 图）。

由 writer_agent/graphs_factory 之外的旧 registry/nodes 构建, 封装为注册图类,
与 6 个 agent 图统一入口。
"""

from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver

from ..state import WriterState
from .graphs_registry import Graph, register_graph


@register_graph
class WriterWorkflowGraph(Graph):
    name = "writer_workflow"
    label = "agent"
    title = "区间式创作流水线"

    def __init__(self,
                 llm: ChatOpenAI,
                 tools: list[BaseTool],
                 history_len: int,
                 checkpoint: BaseCheckpointSaver,
                 start: str = "research",
                 end: str = "finalize",
                 interactive: bool = False):
        super().__init__(llm, tools, history_len, checkpoint)
        self.start = start
        self.end = end
        self.interactive = interactive

    def get_graph(self):  # noqa: D102
        from ..graph_builder import build_agent

        return build_agent(
            start=self.start,
            end=self.end,
            interactive=self.interactive,
            checkpointer=self.checkpoint,
        )

    @staticmethod
    def handle_event(node: str, event: WriterState) -> BaseMessage:
        return event["messages"][-1]