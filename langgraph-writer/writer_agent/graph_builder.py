"""区间式工作流图构建器。

核心能力:
- build_agent(start, end): 只装配 [start, end] 区间内的阶段节点,
  使执行严格从 start 开始、于 end 结束 (支持单节点区间)。
- interactive=True: 在每个阶段之间设置 interrupt_after 断点,
  供人工在节点间注入/修正数据后再继续 (对应 LangGraph-Chatchat
  的 article_generation 用例的 break point 模式)。
- checkpointer: 支持 MemorySaver / SqliteSaver, 可中断恢复。

仿照 LangGraph-Chatchat graphs_factory 的思路: 状态用
TypedDict + add_messages, 节点返回更新字典, 图编译时挂 checkpointer。
"""

import os
from typing import Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .nodes import get_llm  # noqa: F401  (注册副作用: 导入 nodes 触发 @register_stage)
from .registry import all_stages
from .state import WriterState, interval_stages


def build_agent(
    start: str = "research",
    end: str = "finalize",
    interactive: bool = False,
    checkpointer: Optional[object] = None,
    interrupt_every_stage: bool = True,
):
    """构建只包含 [start, end] 区间阶段的 LangGraph。

    参数:
        start: 起始阶段 (research/outline/draft/review/revise/finalize 或中文名)
        end:   结束阶段 (同上)
        interactive: 是否在每个阶段边界设置断点, 供人工注入数据
        checkpointer: 检查点保存器; 默认 MemorySaver (内存级, 进程内可恢复)
        interrupt_every_stage: interactive 时对每个阶段输出后都中断
    """
    stages = interval_stages(start, end)  # 校验顺序 + 展开区间
    if not stages:
        raise ValueError("区间为空, 请检查 start/end")

    if checkpointer is None:
        checkpointer = MemorySaver()

    builder = StateGraph(WriterState)

    registry = all_stages()
    for name in stages:
        builder.add_node(name, registry[name])

    # 线性串联区间内各阶段
    for prev, nxt in zip(stages, stages[1:]):
        builder.add_edge(prev, nxt)
    builder.add_edge(stages[-1], END)

    builder.set_entry_point(stages[0])

    interrupt_after = None
    if interactive and interrupt_every_stage:
        # 在阶段完成后暂停, 用户可以 update_state 注入数据后再 resume
        interrupt_after = list(stages[:-1]) if len(stages) > 1 else None

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_after=interrupt_after,
        debug=bool(os.environ.get("WRITER_DEBUG", "")),
    )


def run_interval(
    initial_state: dict,
    start: str = "research",
    end: str = "finalize",
    config: Optional[dict] = None,
    interactive: bool = False,
    on_interrupt=None,
):
    """便捷入口: 构建区间图并执行, 返回最终 state。

    on_interrupt: 若提供, 每次中断时调用 on_interrupt(graph, state_snapshot, config)
                  并返回注入 dict; 用于 CLI 交互/自动续跑。
    """
    graph = build_agent(start=start, end=end, interactive=interactive)
    cfg = config or {"configurable": {"thread_id": "writer-default"}}
    state = dict(initial_state)

    while True:
        snapshot = graph.invoke(state, cfg)
        interrupts = snapshot.get("__interrupt__") if isinstance(snapshot, dict) else None
        if not interrupts:
            return snapshot
        if on_interrupt is None:
            return snapshot  # 停在断点, 交给调用方处理
        updates = on_interrupt(graph, snapshot, cfg)
        if updates:
            graph.update_state(cfg, updates)
        state = None  # 已提交状态, 继续走 None


class WriterGraph:
    """面向对象封装 (仿 chatchat Graph 基类的调用方式)。"""

    name = "writer"
    label = "agent"
    title = "小说创作区间式 Agent"

    def __init__(self, start="research", end="finalize", interactive=False,
                 checkpointer=None):
        self.start = start
        self.end = end
        self.interactive = interactive
        self._checkpointer = checkpointer
        self._graph = build_agent(start, end, interactive, checkpointer)

    def get_graph(self):
        return self._graph

    def invoke(self, initial_state: dict, config: Optional[dict] = None):
        cfg = config or {"configurable": {"thread_id": "writer-graph"}}
        return self._graph.invoke(initial_state, cfg)

    def update_state(self, config: dict, updates: dict):
        self._graph.update_state(config, updates)

    def __repr__(self):
        return f"<WriterGraph {self.start}→{self.end} interactive={self.interactive}>"