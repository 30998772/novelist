"""MCP Server 封装: 将区间式 Writer Agent 暴露给 opencode 调用。

用法:
    python -m writer_agent.mcp_server
或通过 opencode.json 注册为 local MCP server。
"""

import asyncio
import json
import os
import sys

from . import __version__
from .graph_builder import run_interval
from .state import STAGE_LABELS, STAGE_ORDER, validate_interval


def _build_initial(args: dict) -> dict:
    """把工具参数组装成初始 WriterState。"""
    validate_interval(args.get("start", "research"), args.get("end", "finalize"))

    input_data = dict(args.get("input_data") or {})
    if not input_data.get("target_word_count"):
        input_data["target_word_count"] = args.get("target_word_count", 3200)
        if args.get("review_dimensions"):
            input_data["review_dimensions"] = args["review_dimensions"]

    state = {
        "task": args.get("task") or "创作章节正文",
        "input_data": input_data,
        "iteration": 0,
        "max_iterations": args.get("max_iterations", 3),
        "messages": [],
    }
    if args.get("research_notes"):
        state["research_notes"] = args["research_notes"]
    if args.get("outline"):
        state["outline"] = args["outline"]
    if args.get("draft"):
        state["draft"] = args["draft"]
    if args.get("review_notes"):
        notes = args["review_notes"]
        state["review_notes"] = notes if isinstance(notes, list) else [notes]
    return state


def _pick_output(result: dict) -> str:
    for key in ("final_content", "draft", "outline", "research_notes"):
        value = result.get(key)
        if value:
            return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if result.get("review_notes"):
        return "审稿意见:\n" + "\n".join(f"- {n}" for n in result["review_notes"])
    return "(无输出)"


STAGE_CHOICES = ", ".join(STAGE_ORDER)

SCHEMAS = {
    "run_workflow": {
        "type": "object",
        "properties": {
            "start": {"type": "string", "description": f"起始阶段。可选: {STAGE_CHOICES}", "enum": STAGE_ORDER},
            "end": {"type": "string", "description": f"结束阶段。可选: {STAGE_CHOICES}", "enum": STAGE_ORDER},
            "task": {"type": "string", "description": "任务描述"},
            "research_notes": {"type": "string", "description": "调研纪要(从调研阶段开始时预置)"},
            "outline": {"type": "string", "description": "大纲(从大纲及以后阶段开始时预置)"},
            "draft": {"type": "string", "description": "草稿(从写稿及以后阶段开始时预置)"},
            "review_notes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "审稿意见(从修改阶段开始时预置)",
            },
            "target_word_count": {"type": "integer", "description": "目标字数", "default": 3200},
            "review_dimensions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "审稿维度(自定义时使用)",
            },
            "input_data": {"type": "object", "description": "附加结构化素材"},
            "max_iterations": {"type": "integer", "description": "最大迭代次数", "default": 3},
        },
        "required": [],
    },
}


def create_app():
    """创建 MCP Server 应用。"""
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool

    app = Server("writer-interval-agent")

    @app.list_tools()
    async def list_tools():
        return [
            Tool(
                name="run_workflow",
                description=(
                    f"区间式小说创作工作流: 从 start 阶段开始、end 阶段结束执行。"
                    f"阶段: {'→'.join(f'{s}({STAGE_LABELS[s]})' for s in STAGE_ORDER)}。"
                    f"可从任意阶段开始(需在参数中预置该阶段所需字段), "
                    f"在任意阶段结束。返回区间终点的产物。"
                ),
                inputSchema=SCHEMAS["run_workflow"],
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            if name == "run_workflow":
                if not os.environ.get("LLM_API_KEY"):
                    return [TextContent(type="text", text="错误: 未设置环境变量 LLM_API_KEY")]
                result = await asyncio.to_thread(
                    run_interval,
                    _build_initial(arguments),
                    start=arguments.get("start", "research"),
                    end=arguments.get("end", "finalize"),
                    interactive=False,
                )
                return [TextContent(type="text", text=_pick_output(result))]

            return [TextContent(type="text", text=f"未知工具: {name}")]

        except Exception as exc:  # noqa: BLE001
            return [TextContent(type="text", text=f"错误: {exc}")]

    return app


async def main():
    app = create_app()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())


def _self_echo(extra: str = "") -> str:
    """辅助: 打印版本信息 (供 --version 等场景, 不影响 MCP stdio 协议)."""
    return f"writer-interval-agent {__version__} {extra}"


if "--version" in sys.argv:
    print(_self_echo())
    sys.exit(0)