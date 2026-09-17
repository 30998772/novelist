"""区间式工作流图构建器。

核心能力:
- build_agent(start, end): 只装配 [start, end] 区间内的阶段节点,
  使执行严格从 start 开始、于 end 结束 (支持单节点区间)。
- 确定性 code 校验节点: draft 之后自动插入 check_word_count / check_blacklist
  (纯 Python，不经 LLM)。校验失败通过条件路由回跳 draft 重写。
- review→revise→review 条件回跳: review 有意见 → 回 revise；意见为空 → 进 finalize。
  受 max_iterations 约束，循环耗尽后强制放行 finalize。
- interactive=True: 在每个阶段之间设置 interrupt_after 断点,
  供人工在节点间注入/修正数据后再继续 (对应 LangGraph-Chatchat
  的 article_generation 用例的 break point 模式)。
- checkpointer: 支持 MemorySaver / SqliteSaver, 可中断恢复。
"""

import os
from typing import Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .nodes import get_llm  # noqa: F401  (注册副作用: 导入 nodes 触发 @register_stage)
from .registry import all_stages
from .state import WriterState, interval_stages

# 校验节点在节点间的固定顺序
_CODE_CHECKS = ["check_word_count", "check_blacklist"]

# LangGraph 要求节点名不能与 state 键重名。WriterState 里的 outline/draft 等
# 与阶段名冲突, 故统一经 _node_id 加后缀规避 (路由返回值仍用逻辑阶段名)。
_STATE_KEYS = set(WriterState.__annotations__)


def _node_id(name: str) -> str:
    return f"{name}_stage" if name in _STATE_KEYS else name


def _route_check_word_count(state: dict) -> str:
    """字数校验失败 → 回 draft 重写；通过 → 下一校验。

    达到 max_iterations 仍不合格时放行到下一校验（避免死循环，
    交由 review 把关）。
    """
    if state.get("check_error") and int(state.get("iteration", 0)) < int(state.get("max_iterations", 3)):
        return "draft"
    return "check_blacklist"


def _route_check_blacklist(state: dict) -> str:
    """禁用词命中 → 回 draft 重写；干净 → 进 review。

    达到 max_iterations 仍命中时放行进 review（避免死循环）。
    """
    if state.get("blacklist_hits") and int(state.get("iteration", 0)) < int(state.get("max_iterations", 3)):
        return "draft"
    return "review"


def _route_review(state: dict) -> str:
    """review 后路由：有意见且未超限 → revise；否则 → finalize/END。"""
    notes = state.get("review_notes") or []
    iteration = int(state.get("iteration", 0))
    max_iterations = int(state.get("max_iterations", 3))
    if notes and iteration < max_iterations:
        return "revise"
    return "finalize"


def build_agent(
    start: str = "research",
    end: str = "finalize",
    interactive: bool = False,
    checkpointer: Optional[object] = None,
    interrupt_every_stage: bool = True,
    with_code_checks: bool = True,
):
    """构建只包含 [start, end] 区间阶段的 LangGraph。

    参数:
        start: 起始阶段 (research/outline/draft/review/revise/finalize 或中文名)
        end:   结束阶段 (同上)
        interactive: 是否在每个阶段边界设置断点, 供人工注入数据
        checkpointer: 检查点保存器; 默认 MemorySaver (内存级, 进程内可恢复)
        interrupt_every_stage: interactive 时对每个阶段输出后都中断
        with_code_checks: 是否启用确定性校验节点与 review 条件回跳 (默认 True)。

    图结构 (with_code_checks=True):

        research → outline → draft → check_word_count → check_blacklist → review
                                          │ (fail→draft)         │ (fail→draft)
                                          ▼                      ▼
                                        draft                  draft
        review ──(有意见且未超限)──→ revise =→ check_word_count →… → review(复检)
            └──(无意见/超限)──→ finalize → END
    """
    stages = interval_stages(start, end)  # 校验顺序 + 展开区间
    if not stages:
        raise ValueError("区间为空, 请检查 start/end")

    if checkpointer is None:
        checkpointer = MemorySaver()

    registry = all_stages()

    # 展开执行序列: draft 后插入校验节点（仅当区间包含完整 draft→review 链路）
    nodes_to_add: list[str] = []
    for s in stages:
        nodes_to_add.append(s)
        if (
            with_code_checks
            and s == "draft"
            and "review" in stages
            and all(c in registry for c in _CODE_CHECKS)
        ):
            nodes_to_add.extend(_CODE_CHECKS)

    seen: list[str] = []
    for name in nodes_to_add:
        if name in registry and name not in seen:
            seen.append(name)

    builder = StateGraph(WriterState)
    for name in seen:
        builder.add_node(_node_id(name), registry[name])
    builder.set_entry_point(_node_id(seen[0]))

    # 哪些节点走条件路由（不作为直线边起点）
    conditional_sources: set[str] = set()
    if with_code_checks and "check_word_count" in seen:
        conditional_sources.add("check_word_count")
    if with_code_checks and "check_blacklist" in seen:
        conditional_sources.add("check_blacklist")
    if with_code_checks and "review" in seen and "revise" in seen:
        conditional_sources.add("review")

    # ── 直线主线（跳过条件路由节点作为起点） ──
    for prev, nxt in zip(seen, seen[1:]):
        if prev in conditional_sources:
            continue
        builder.add_edge(_node_id(prev), _node_id(nxt))
    if seen[-1] not in conditional_sources:
        builder.add_edge(_node_id(seen[-1]), END)

    # ── 校验节点条件路由 ──
    if with_code_checks and "check_word_count" in seen:
        builder.add_conditional_edges(
            _node_id("check_word_count"),
            _route_check_word_count,
            {
                "draft": _node_id("draft"),
                "check_blacklist": _node_id("check_blacklist"),
            },
        )
    if with_code_checks and "check_blacklist" in seen:
        builder.add_conditional_edges(
            _node_id("check_blacklist"),
            _route_check_blacklist,
            {"draft": _node_id("draft"), "review": _node_id("review")},
        )

    # ── review 条件回跳 revise ──
    if with_code_checks and "review" in seen and "revise" in seen:
        builder.add_conditional_edges(
            _node_id("review"),
            _route_review,
            {
                "revise": _node_id("revise"),
                "finalize": _node_id("finalize") if "finalize" in seen else END,
            },
        )
        if "check_word_count" in seen:
            builder.add_edge(_node_id("revise"), _node_id("check_word_count"))
    elif "review" in seen:
        # review 无 revise 在区间内时正常走直线
        builder.add_edge(
            _node_id("review"), _node_id("finalize") if "finalize" in seen else END
        )

    if interactive and interrupt_every_stage:
        # 在阶段完成后暂停, 用户可以 update_state 注入数据后再 resume
        # 校验节点不中断（纯代码无需人工），最后一阶段也不中断
        step_nodes = [n for n in seen if n not in _CODE_CHECKS and n != "finalize"]
        interrupt_after = (
            [_node_id(n) for n in step_nodes[:-1]] if len(step_nodes) > 1 else None
        )
    else:
        interrupt_after = None

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
    with_code_checks: bool = True,
):
    """便捷入口: 构建区间图并执行, 返回最终 state。

    on_interrupt: 若提供, 每次中断时调用 on_interrupt(graph, state_snapshot, config)
                  并返回注入 dict; 用于 CLI 交互/自动续跑。
    with_code_checks: 传给 build_agent 的确定性校验开关。
    """
    graph = build_agent(
        start=start, end=end, interactive=interactive, with_code_checks=with_code_checks
    )
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
                 checkpointer=None, with_code_checks=True):
        self.start = start
        self.end = end
        self.interactive = interactive
        self._checkpointer = checkpointer
        self._graph = build_agent(start, end, interactive, checkpointer,
                                  with_code_checks=with_code_checks)

    def get_graph(self):
        return self._graph

    def invoke(self, initial_state: dict, config: Optional[dict] = None):
        cfg = config or {"configurable": {"thread_id": "writer-graph"}}
        return self._graph.invoke(initial_state, cfg)

    def update_state(self, config: dict, updates: dict):
        self._graph.update_state(config, updates)

    def __repr__(self):
        return f"<WriterGraph {self.start}→{self.end} interactive={self.interactive}>"