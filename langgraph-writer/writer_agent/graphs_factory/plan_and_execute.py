"""计划执行图（对齐 LangGraph-Chatchat graphs_factory/plan_and_execute.PlanExecuteGraph）。

流程（取自 LangGraph plan-and-execute 教程）：
    history_manager → planner(结构化 Plan) → agent(react 执行一步)
      → replan(结构化 Act: Response / Plan) → agent … → END

与 Chatchat 的差异：执行节点改用内联提示词，不再 `hub.pull("wfh/react-agent-executor")`，
避免运行期依赖 LangChain Hub 网络拉取。
"""

from typing import Any, List, Literal, Optional, Union

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from ..state import WriterState
from .graphs_registry import Graph, register_graph


class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )


class Response(BaseModel):
    """Response to user."""

    response: str


class Act(BaseModel):
    """Action to perform."""

    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. "
                    "If you need to further use tools to get the answer, use Plan."
    )


class PlanStepExecuteResult(BaseModel):
    step: str
    result: str


class PlanExecute(WriterState, total=False):
    """plan_and_execute 的核心 state：plan / past_steps / response。"""

    plan: Optional[Plan]
    past_steps: Optional[List[PlanStepExecuteResult]]
    response: Optional[Response]


@register_graph
class PlanExecuteGraph(Graph):
    name = "plan_execute_agent"
    label = "agent"
    title = "计划执行机器人[Beta]"

    def __init__(self,
                 llm: ChatOpenAI,
                 tools: list[BaseTool],
                 history_len: int,
                 checkpoint: BaseCheckpointSaver,
                 **kwargs):
        super().__init__(llm, tools, history_len, checkpoint)

    def plan_step(self, state: PlanExecute) -> PlanExecute:
        planner_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """针对给定目标，制定一个简单的分步计划。计划应由若干可独立执行的任务组成，
执行完即可得到正确结果，不要添加多余步骤。最后一步的结果应当就是最终答案。
确保每一步都包含所需信息，不要遗漏步骤。""",
                ),
                ("placeholder", "{history}"),
            ]
        )
        planner = planner_prompt | self.llm.with_structured_output(Plan)

        plan_steps = planner.invoke(state)
        state["plan"] = Plan(steps=plan_steps.steps)
        return state

    def execute_step(self, state: PlanExecute) -> PlanExecute:
        executor_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """你是一个善于调用工具逐步完成计划的执行器。给定完整计划与当前要执行的
这一步，调用合适的工具完成它，并汇报这一步的执行结果。""",
                ),
            ]
        )
        agent_executor = create_react_agent(
            self.llm, self.tools, prompt=executor_prompt
        )

        plan = state["plan"]
        plan_str = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(plan.steps))

        task = plan.steps[0]
        task_formatted = f"""以下是完整计划：
    {plan_str}\n\n你现在负责执行第 {1} 步：{task}。"""

        agent_response = agent_executor.invoke(
            {"messages": [("user", task_formatted)]}
        )

        plan_step_execute_result = PlanStepExecuteResult(
            step=task, result=agent_response["messages"][-1].content
        )

        if "past_steps" not in state or state["past_steps"] is None:
            state["past_steps"] = []
        state["past_steps"].append(plan_step_execute_result)
        return state

    def replan_step(self, state: PlanExecute) -> PlanExecute:
        replanner_prompt = ChatPromptTemplate.from_template(
            """针对给定目标，制定一个简单的分步计划。计划应由若干可独立执行的任务组成，
执行完即可得到正确结果，不要添加多余步骤。最后一步的结果应当就是最终答案。
确保每一步都包含所需信息，不要遗漏步骤。

你的原始目标是：
{history}

你原来的计划是：
{plan}

你目前已经完成以下步骤：
{past_steps}

据此更新你的计划。如果无需更多步骤、可以直接回复用户，就给出回复；否则补充计划。
只添加仍然需要完成的步骤，不要把已完成的步骤再次列入计划。"""
        )
        replanner = replanner_prompt | self.llm.with_structured_output(Act)

        output = replanner.invoke(state)

        if not hasattr(output, "action"):
            raise ValueError(
                "输出中缺少 'action' 属性, 说明 replan_step 执行异常, 请重试或改用更强的 LLM。"
            )

        if isinstance(output.action, Response):
            state["response"] = Response(response=output.action.response)
            state["messages"] = [AIMessage(content=output.action.response)]
        elif isinstance(output.action, Plan):
            state["plan"] = Plan(steps=output.action.steps)
        else:
            raise ValueError("replan_step 输出中出现未预期的 action 类型")

        return state

    @staticmethod
    def should_end(state: PlanExecute) -> Literal["executor", "__end__"]:
        if state.get("response"):
            return "__end__"
        return "executor"

    def get_graph(self) -> CompiledGraph:
        if not isinstance(self.llm, ChatOpenAI):
            raise TypeError("llm must be an instance of ChatOpenAI")
        if not all(isinstance(tool, BaseTool) for tool in self.tools):
            raise TypeError("All items in tools must be instances of BaseTool")

        graph_builder = StateGraph(PlanExecute)

        graph_builder.add_node("history_manager", self.history_manager)
        graph_builder.add_node("planner", self.plan_step)
        graph_builder.add_node("executor", self.execute_step)
        graph_builder.add_node("replan", self.replan_step)

        graph_builder.add_edge(START, "history_manager")
        graph_builder.add_edge("history_manager", "planner")
        graph_builder.add_edge("planner", "executor")
        graph_builder.add_edge("executor", "replan")
        graph_builder.add_conditional_edges("replan", self.should_end)

        return graph_builder.compile(checkpointer=self.checkpoint)

    @staticmethod
    def handle_planner(event_data: PlanExecute) -> Plan:
        return event_data["plan"]

    @staticmethod
    def handle_agent(event_data: PlanExecute) -> List[PlanStepExecuteResult]:
        return event_data["past_steps"]

    @staticmethod
    def handle_replan(event_data: PlanExecute) -> Union[Plan, Response]:
        if event_data.get("response"):
            return event_data["response"]
        return event_data["plan"]

    def handle_event(self, node: str, event: PlanExecute) -> Any:
        handler_map = {
            "planner": self.handle_planner,
            "executor": self.handle_agent,
            "replan": self.handle_replan,
        }
        handler = handler_map.get(node)
        if handler:
            return handler(event)
        raise ValueError(f"Unsupported plan_and_execute node type: {node}")
