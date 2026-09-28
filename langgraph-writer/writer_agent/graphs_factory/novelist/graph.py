"""通用「LLM + 工具」聊天图（对齐 LangGraph-Chatchat base_agent.BaseAgentGraph）。

图结构：history_manager → intent_recognition(生成有序 plan)
        → subgraph_generic(自环按 plan 顺序逐步调用子图)
        → confirm_step(汇报本步产出并等用户确认)
        → collect_results → summarize_results

逐步确认（human-in-the-loop）：每个子图跑完后 confirm_step 会通过 LangGraph
interrupt 暂停，把本步的 intent / task / 产出 / 剩余步骤汇报给用户。用户回复支持
「通过」（采纳并继续）/「重做」（丢弃并重跑，重做次数上限 MAX_STEP_RETRY）/
「跳过」（丢弃并进入下一步）/ 任意文字（当作修改意见重跑本步）。
只有被确认采纳的结果才会进入 intent_results 并参与最终汇总。

计划（plan）：intent_recognition 一次 LLM 调用输出按执行顺序排列的步骤列表，
每步 = {"intent": 子图名, "task": 本步任务}；subgraph_generic 每轮消费一步，
直接把 task 注入子图输入并调用该步对应的子图。

LLM 调用预算：
- 主图自身只有 2 处 LLM 调用 —— intent_recognition（1 次）+ summarize_results（仅多子图时 1 次）；
- 每个子图类型每轮最多运行 1 次（_normalize_plan 去重 + 队列每轮只消费一步）；
- 单个 plan 步骤产出时 summarize_results 直接透传，不消耗 LLM 调用。

拓扑全部由类上的配置声明：NODES / EDGES / CONDITIONAL_EDGES / SUBGRAPHS。
加节点、加边、加子图只改配置，不用动 get_graph。
"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import tools_condition
from langgraph.types import interrupt

from ...logging import get_logger
from ...state import WriterState
from .._shared.chat_node import build_tool_loop
from .._shared.registry import Graph, register_graph
from .configs import (
    NODES as CFG_NODES,
    ENTRY as CFG_ENTRY,
    EDGES as CFG_EDGES,
    ROUTES as CFG_ROUTES,
    CONDITIONAL_EDGES as CFG_CONDITIONAL_EDGES,
    STATE as CFG_STATE,
    SUBGRAPHS as CFG_SUBGRAPHS,
    MAX_CLARIFICATION_ATTEMPTS,
    MAX_STEP_RETRY,
    APPROVE_WORDS,
    RETRY_WORDS,
    SKIP_WORDS,
    FALLBACK_INTENTS,
    NovelistState,
)
from .prompts import (
    PLAN_PROMPT_TEMPLATE,
    PlanOutput,
    NOVELIST_SYSTEM_PROMPT,
)

logger = get_logger("novelist")


class BaseAgentGraph(Graph):
    # ════════════════════════════════════════════════════════════════
    # 图配置（从 configs.py 导入）
    # ════════════════════════════════════════════════════════════════
    NODES = CFG_NODES
    ENTRY = CFG_ENTRY
    EDGES = CFG_EDGES
    ROUTES = CFG_ROUTES
    CONDITIONAL_EDGES = CFG_CONDITIONAL_EDGES
    STATE = CFG_STATE

    # ════════════════════════════════════════════════════════════════
    # 子类覆写
    # ════════════════════════════════════════════════════════════════
    name = ""
    label = "agent"
    title = ""
    system_prompt = ""
    tool_names: list[str] = ["*"]

    # 子图：意图 -> {"node_name", "tools", "description", "build_func"(可选)}
    SUBGRAPHS: dict[str, dict] = {}

    # ════════════════════════════════════════════════════════════════
    # __init__
    # ════════════════════════════════════════════════════════════════
    def __init__(self,
                 llm: ChatOpenAI,
                 tools: list[BaseTool],
                 history_len: int,
                 checkpoint: BaseCheckpointSaver,
                 system_prompt: str | None = None):
        super().__init__(llm, tools, history_len, checkpoint)

        cfg = self.SUBGRAPHS or {}
        known = set(cfg.keys()) | FALLBACK_INTENTS

        # 计划生成：JSON Schema 强制输出有序 plan
        self.plan_prompt = ChatPromptTemplate.from_messages([
            ("system", PLAN_PROMPT_TEMPLATE),
            ("placeholder", "{" + self.STATE["history"] + "}"),
        ])
        self.llm_with_plan = self.plan_prompt | self.llm.with_structured_output(
            PlanOutput,
            method="json_schema",
        )

        # 汇总回复：只在多个子图产出时调用，不绑定工具
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt or self.system_prompt),
            ("placeholder", "{" + self.STATE["history"] + "}"),
        ])
        self.llm_with_summary = prompt | self.llm

        self._valid_intents: set[str] = known
        self._subgraphs: dict[str, CompiledStateGraph] = {}
        for intent, sub in cfg.items():
            builder = sub.get("build_func")
            if builder is not None:
                self._subgraphs[intent] = builder(self.llm, self.tools, self.checkpoint)
            else:
                self._subgraphs[intent] = build_tool_loop(
                    name=sub["node_name"],
                    tool_names=sub["tools"],
                    llm=self.llm,
                    tools=self.tools,
                    state_cls=WriterState,
                    checkpoint=self.checkpoint,
                )

        logger.info(
            "BaseAgentGraph initialized: name=%s, valid_intents=%s, subgraphs=%s",
            self.name, self._valid_intents, list(cfg.keys()),
        )

    # ------------------------------------------------------------------
    # 节点函数表（逻辑名 -> 可调用）
    # ------------------------------------------------------------------
    def _node_funcs(self) -> dict:
        return {
            "history": self.history_manager,
            "intent": self.intent_recognition,
            "clarify": self.ask_clarification,
            "generic": self.execute_subgraph,
            "confirm": self.confirm_step,
            "collect": self.collect_results,
            "summarize": self.summarize_results,
        }

    # ------------------------------------------------------------------
    # 历史管理
    # ------------------------------------------------------------------
    def history_manager(self, state: WriterState) -> WriterState:
        from langchain_core.messages import filter_messages

        try:
            filtered = []
            for message in filter_messages(state[self.STATE["messages"]], exclude_types=[ToolMessage]):
                if isinstance(message, AIMessage) and message.tool_calls:
                    continue
                filtered.append(message)
            state[self.STATE["history"]] = filtered[-self.history_len:]
            logger.debug("history_manager: filtered %d messages, kept %d",
                         len(state[self.STATE["messages"]]), len(state[self.STATE["history"]]))
            return state
        except Exception as e:
            logger.error("history_manager failed: %s", e)
            raise Exception(f"Filtering messages error: {e}")

    # ------------------------------------------------------------------
    # 计划生成（JSON Schema）：输出按执行顺序排列的 plan
    # ------------------------------------------------------------------
    def intent_recognition(self, state: WriterState) -> WriterState:
        try:
            history = state.get(self.STATE["history"]) or []
            last_human = ""
            for msg in reversed(history):
                if isinstance(msg, HumanMessage):
                    last_human = msg.content if isinstance(msg.content, str) else str(msg.content)
                    break
            logger.info("intent_recognition: user input = %s", repr(last_human[:200]))

            result = self.llm_with_plan.invoke(state)
            raw_plan = self._extract_plan(result)
            plan = self._normalize_plan(raw_plan)

            logger.info("intent_recognition: raw plan = %s", raw_plan)
            logger.info("intent_recognition: normalized plan = %s",
                        [(s["intent"], s["task"]) for s in plan])

            state[self.STATE["plan"]] = plan
            state[self.STATE["intents"]] = [s["intent"] for s in plan]
            state[self.STATE["current"]] = plan[0]["intent"] if plan else ""
            state[self.STATE["index"]] = 0
            state[self.STATE["results"]] = {}
            # 逐步确认相关状态每轮重置
            state[self.STATE["pending_confirm"]] = {}
            state[self.STATE["feedback"]] = {}
            state[self.STATE["attempts"]] = {}
            state[self.STATE["retry_current"]] = False
            if plan:
                state[self.STATE["clarify_count"]] = 0
            else:
                state[self.STATE["clarify_count"]] = state.get(self.STATE["clarify_count"], 0) + 1
                logger.warning("intent_recognition: empty plan, clarify_count = %d",
                               state[self.STATE["clarify_count"]])
            return state
        except Exception as e:
            logger.error("intent_recognition failed: %s", e)
            raise Exception(f"Intent recognition error: {e}")

    # ------------------------------------------------------------------
    # 追问 / 结束
    # ------------------------------------------------------------------
    def ask_clarification(self, state: WriterState) -> WriterState:
        options = "\n".join(f"- {k}：{v['description']}" for k, v in (self.SUBGRAPHS or {}).items())
        msg = AIMessage(content=f"我不太确定你想做什么，请告诉我更具体的需求，比如：\n{options}\n- 其他")
        state[self.STATE["messages"]] = [msg]
        state[self.STATE["history"]].append(msg)
        logger.info("ask_clarification: asking user for clarification")
        return state

    def end_conversation(self, state: WriterState) -> WriterState:
        msg = AIMessage(content="抱歉，我无法识别你的意图。请尝试更具体的描述，或者输入 /exit 退出。")
        state[self.STATE["messages"]] = [msg]
        state[self.STATE["history"]].append(msg)
        logger.info("end_conversation: unable to identify intent, ending")
        return state

    # ------------------------------------------------------------------
    # plan 解析 / 归一化
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_plan(result) -> list:
        """从结构化输出里取出原始 plan，兼容 Pydantic / dict / list 三种形态。"""
        if hasattr(result, "plan"):
            raw = result.plan
        elif isinstance(result, dict):
            raw = result.get("plan")
        elif isinstance(result, list):
            raw = result
        else:
            raw = None
        return list(raw) if raw else []

    def _normalize_plan(self, raw_plan: list) -> list[dict]:
        """归一化成 [{"intent": 子图名, "task": 本步任务}]。

        - 丢弃无法识别的 intent；
        - 每种子图最多保留一步（按首次出现），保证每个子图每轮最多运行一次；
        - 保持 LLM 给出的执行顺序。
        """
        plan: list[dict] = []
        seen: set[str] = set()
        dropped: list[str] = []

        for item in raw_plan:
            if isinstance(item, str):                       # 容错：只给了子图名
                intent, task = item.strip(), ""
            elif isinstance(item, dict):
                intent = str(item.get("intent") or "").strip()
                task = str(item.get("task") or "").strip()
            else:                                          # PlanStep 等对象
                intent = str(getattr(item, "intent", "") or "").strip()
                task = str(getattr(item, "task", "") or "").strip()

            if intent not in self._valid_intents:
                dropped.append(intent or "<空>")
                continue
            if intent in seen:
                dropped.append(f"{intent}(重复)")
                continue

            seen.add(intent)
            plan.append({"intent": intent, "task": task})

        if dropped:
            logger.info("_normalize_plan: dropped %s", dropped)
        return plan

    # ------------------------------------------------------------------
    # 子图分派
    # ------------------------------------------------------------------
    # 计划队列：subgraph_generic 自我循环消费 plan，消费完转入 collect
    # ------------------------------------------------------------------
    def route_after_intent(self, state: WriterState) -> str:
        if not state.get(self.STATE["plan"]):
            logger.info("route_after_intent: empty plan -> clarify")
            return self.ROUTES["clarify"]
        logger.info("route_after_intent: plan has %d step(s) -> run subgraphs",
                    len(state[self.STATE["plan"]]))
        return self.ROUTES["generic"]

    def execute_subgraph(self, state: WriterState) -> WriterState:
        """按 plan 顺序执行下一步：取出队首步骤，直接调用它对应的子图。

        每轮只消费一步；plan 消费完毕后本节点不再执行子图，
        由 route_after_subgraph 转入 collect_results。
        """
        plan = state.get(self.STATE["plan"]) or []
        idx = state.get(self.STATE["index"], 0)
        if idx >= len(plan):
            state[self.STATE["current"]] = ""
            return state

        step = plan[idx]
        intent = step["intent"]
        step_task = step.get("task", "")
        state[self.STATE["current"]] = intent
        state[self.STATE["index"]] = idx + 1
        sub = (self.SUBGRAPHS or {}).get(intent)

        if not sub or intent not in self._subgraphs:
            results = dict(state.get(self.STATE["results"]) or {})
            results[intent] = f"「{intent}」子图尚未实装"
            state[self.STATE["results"]] = results
            logger.warning("execute_subgraph: no subgraph for step %d/%d intent=%s",
                           idx + 1, len(plan), intent)
            return state

        # 把本步任务注入为子图输入的最后一条消息，让子图明确本轮要做什么
        content = f"【plan 第 {idx + 1}/{len(plan)} 步｜{intent}】{step_task}"
        feedback = (state.get(self.STATE["feedback"]) or {}).get(intent, "")
        if feedback:
            content += f"\n【用户对上一版结果的修改意见】{feedback}"
        step_msg = HumanMessage(content=content)
        sub_input = dict(state)
        sub_input[self.STATE["messages"]] = (state.get(self.STATE["messages"]) or []) + [step_msg]
        sub_input[self.STATE["history"]] = (state.get(self.STATE["history"]) or []) + [step_msg]
        sub_input[self.STATE["task"]] = step_task or state.get(self.STATE["task"], "")

        # 运行子图
        subgraph = self._subgraphs[intent]
        sub_state = subgraph.invoke(sub_input)

        # 从子图输出中提取最后一条 AI 消息作为结果
        sub_messages = sub_state.get("messages") or []
        result_text = ""
        for msg in reversed(sub_messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                result_text = msg.content if isinstance(msg.content, str) else str(msg.content)
                break

        if not result_text:
            result_text = f"「{intent}」子图未产出有效结果"

        results = dict(state.get(self.STATE["results"]) or {})
        results[intent] = result_text
        state[self.STATE["results"]] = results

        # 把子图产生的消息合并回主图
        state[self.STATE["messages"]] = sub_messages
        state[self.STATE["history"]] = sub_state.get("history") or state.get(self.STATE["history"]) or []

        logger.info("execute_subgraph: step %d/%d intent=%s task=%r result_len=%d",
                    idx + 1, len(plan), intent, step_task, len(result_text))
        return state

    # ------------------------------------------------------------------
    # 子图逐步确认（human-in-the-loop）
    # ------------------------------------------------------------------
    def confirm_step(self, state: WriterState) -> WriterState:
        """子图跑完后向用户汇报本步产出，并通过 interrupt 暂停等用户确认。

        用户回复归一化后有三种去向：
        - 采纳：保留结果，进入下一步（无下一步则收尾）；
        - 重做：丢弃结果并回退一步重跑（同一步最多 MAX_STEP_RETRY 次）；
        - 跳过：丢弃结果，直接进入下一步。

        任何非关键词的回复都当作「修改意见」，按意见重跑本步。
        """
        # 没有 checkpointer 时 interrupt 无法工作，退化为自动采纳
        if self.checkpoint is None:
            logger.warning("confirm_step: no checkpointer, auto-approve step=%s",
                           state.get(self.STATE["current"]))
            state[self.STATE["retry_current"]] = False
            state[self.STATE["pending_confirm"]] = {}
            return state

        plan = state.get(self.STATE["plan"]) or []
        results = state.get(self.STATE["results"]) or {}
        idx = state.get(self.STATE["index"], 0)
        intent = state.get(self.STATE["current"], "")
        step_task = plan[idx - 1].get("task", "") if 0 < idx <= len(plan) else ""
        attempts = int((state.get(self.STATE["attempts"]) or {}).get(intent, 0))

        payload = {
            "type": "subgraph_confirm",
            "step": f"{idx}/{len(plan)}" if plan else "1/1",
            "intent": intent,
            "task": step_task,
            "result": results.get(intent, ""),
            "remaining": [s["intent"] for s in plan[idx:]],
            "retry_used": attempts,
            "retry_left": max(0, MAX_STEP_RETRY - attempts),
            "options": {
                "通过": "采纳本步结果，进入下一步",
                "重做": "丢弃本步结果并重跑（剩余次数见 retry_left）",
                "跳过": "丢弃本步结果，直接进入下一步",
                "任意文字": "作为修改意见，按意见重跑本步",
            },
        }
        state[self.STATE["pending_confirm"]] = payload
        logger.info("confirm_step: 等待确认 step=%s intent=%s retry_used=%d",
                    payload["step"], intent, attempts)

        decision = interrupt(payload)
        action, feedback = self._parse_decision(decision, attempts)

        if action == "approve":
            feedback_map = dict(state.get(self.STATE["feedback"]) or {})
            feedback_map.pop(intent, None)
            state[self.STATE["feedback"]] = feedback_map
            state[self.STATE["retry_current"]] = False
            logger.info("confirm_step: step=%s intent=%s 已采纳", payload["step"], intent)
            return state

        # 采纳之外的动作都要丢弃本步结果
        results.pop(intent, None)
        state[self.STATE["results"]] = results

        if action == "retry":
            attempts += 1
            attempts_map = dict(state.get(self.STATE["attempts"]) or {})
            attempts_map[intent] = attempts
            state[self.STATE["attempts"]] = attempts_map
            feedback_map = dict(state.get(self.STATE["feedback"]) or {})
            feedback_map[intent] = feedback
            state[self.STATE["feedback"]] = feedback_map
            state[self.STATE["index"]] = idx - 1          # 回退一步，下轮重跑本步
            state[self.STATE["retry_current"]] = True
            logger.info("confirm_step: step=%s intent=%s 要求重做(%d/%d) feedback=%r",
                        payload["step"], intent, attempts, MAX_STEP_RETRY, feedback)
            return state

        # skip
        state[self.STATE["retry_current"]] = False
        logger.info("confirm_step: step=%s intent=%s 已跳过", payload["step"], intent)
        return state

    @staticmethod
    def _parse_decision(decision, attempts: int) -> tuple[str, str]:
        """把用户回复解析成 (action, feedback)。

        action ∈ {"approve", "retry", "skip"}；feedback 为修改意见原文（可为空）。
        重做次数用尽时，任何否定回复都降级为 skip，防止无限重跑。
        """
        text = (str(decision).strip() if decision is not None else "")
        key = text.lower()

        if key in APPROVE_WORDS:
            return "approve", ""
        if key in SKIP_WORDS:
            return "skip", ""
        if key in RETRY_WORDS:
            if attempts >= MAX_STEP_RETRY:
                logger.warning("_parse_decision: retry exhausted for step, fallback to skip")
                return "skip", ""
            return "retry", ""
        # 其余一律当作修改意见
        if attempts >= MAX_STEP_RETRY:
            logger.warning("_parse_decision: retry exhausted for step, fallback to skip")
            return "skip", text
        return "retry", text

    def route_after_confirm(self, state: WriterState) -> str:
        """确认之后：需重做 → 重跑本步；否则有下一步就继续，没有就收尾。"""
        plan = state.get(self.STATE["plan"]) or []
        idx = state.get(self.STATE["index"], 0)

        if state.get(self.STATE["retry_current"]):
            return self.ROUTES["generic"]
        if idx < len(plan):
            logger.info("route_after_confirm: %d step(s) left -> next: %s",
                        len(plan) - idx, plan[idx]["intent"])
            return self.ROUTES["generic"]
        logger.info("route_after_confirm: all steps confirmed -> collect")
        return self.ROUTES["collect"]

    def collect_results(self, state: WriterState) -> WriterState:
        results = state.get(self.STATE["results"], {})
        result_text = "\n".join(f"【{k}】{v}" for k, v in results.items()) if results else "（本轮无子任务产出）"
        state[self.STATE["task"]] = result_text
        state[self.STATE["history"]] = (state.get(self.STATE["history"]) or []) + [
            HumanMessage(content=f"以下是子图/工具产出，请据此并结合用户问题作答：\n{result_text}")
        ]
        logger.info("collect_results: collected %d results", len(results))
        return state

    def summarize_results(self, state: WriterState) -> WriterState:
        """汇总子图产出。

        - 0 个产出：直接回一句提示，不调 LLM；
        - 1 个产出：直接透传该子图结果，不调 LLM；
        - ≥2 个产出：调一次 LLM，按 prompt 备注逐个输出各子图的汇总结果。
        """
        results = state.get(self.STATE["results"]) or {}

        if not results:
            logger.info("summarize_results: no results, skip llm")
            msg = AIMessage(content="（本轮无子任务产出）")
        elif len(results) == 1:
            intent, only = next(iter(results.items()))
            logger.info("summarize_results: single subgraph=%s, passthrough, skip llm", intent)
            msg = AIMessage(content=only)
        else:
            logger.info("summarize_results: %d subgraphs, summarize via llm", len(results))
            try:
                out = self.llm_with_summary.invoke({
                    self.STATE["history"]: state.get(self.STATE["history"]) or []
                })
                msg = out if isinstance(out, BaseMessage) else AIMessage(content=str(out))
            except Exception as e:
                logger.error("summarize_results failed, fallback to raw digest: %s", e)
                digest = "\n".join(f"【{k}】{v}" for k, v in results.items())
                msg = AIMessage(content=digest)

        state[self.STATE["messages"]] = [msg]
        state[self.STATE["history"]] = (state.get(self.STATE["history"]) or []) + [msg]
        return state

    # ------------------------------------------------------------------
    # 工具辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _last_human_text(state: WriterState) -> str:
        for m in reversed(state.get(BaseAgentGraph.STATE["messages"]) or []):
            if isinstance(m, HumanMessage):
                return m.content if isinstance(m.content, str) else str(m.content)
        return ""

    def _get_tool(self, name: str) -> BaseTool:
        for t in self.tools:
            if t.name == name:
                return t
        from ...tools_factory import get_tool
        return get_tool(name)

    # ------------------------------------------------------------------
    # 主图装配（读配置）
    # ------------------------------------------------------------------
    def get_graph(self) -> CompiledStateGraph:
        if not isinstance(self.llm, ChatOpenAI):
            raise TypeError("llm must be an instance of ChatOpenAI")
        if not all(isinstance(t, BaseTool) for t in self.tools):
            raise TypeError("All items in tools must be instances of BaseTool")

        builder = StateGraph(WriterState)
        funcs = self._node_funcs()
        for key, node in self.NODES.items():
            builder.add_node(node, funcs[key])

        builder.set_entry_point(self.NODES[self.ENTRY])
        for src, dst in self.EDGES:
            builder.add_edge(self.NODES[src], END if dst is END else self.NODES[dst])

        for src, spec in self.CONDITIONAL_EDGES.items():
            router = spec["router"]
            fn = tools_condition if router is None else getattr(self, router)
            mapping = spec["map"]
            if mapping is None:
                builder.add_conditional_edges(self.NODES[src], fn)
            else:
                builder.add_conditional_edges(
                    self.NODES[src], fn, {k: self.NODES[v] for k, v in mapping.items()}
                )

        # 子图统一经由 subgraph_generic 串行执行（子图在 execute_subgraph 内部 invoke），
        # 自我循环消费计划队列；每步跑完先进 confirm_step 等用户确认。
        builder.add_conditional_edges(
            self.NODES["confirm"],
            self.route_after_confirm,
            {self.ROUTES["generic"]: self.NODES["generic"],
             self.ROUTES["collect"]: self.NODES["collect"]},
        )

        if self.checkpoint is not None:
            return builder.compile(checkpointer=self.checkpoint)
        return builder.compile()

    @staticmethod
    def handle_event(node: str, event: WriterState) -> BaseMessage:
        return event[BaseAgentGraph.STATE["messages"]][-1]


ToolCallingAgentGraph = BaseAgentGraph


@register_graph
class NovelistGraph(BaseAgentGraph):
    SUBGRAPHS = CFG_SUBGRAPHS

    name = "novelist"
    label = "agent"
    title = "小说家"
    tool_names = ["*"]
    system_prompt = NOVELIST_SYSTEM_PROMPT
