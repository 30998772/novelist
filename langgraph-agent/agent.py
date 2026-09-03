"""
LangGraph Novelist Agent - 小说创作状态图 Agent
通过 MCP 协议与 opencode 集成，使用 OpenAI 兼容 API。

环境变量:
  LLM_API_KEY     - API Key (必填)
  LLM_BASE_URL    - API 端点 (默认: https://api.openai.com/v1)
  LLM_MODEL       - 模型名 (默认: gpt-4o-mini)
"""

import os
import json
import asyncio
from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI


# ============ LLM 初始化 ============

def get_llm():
    """从环境变量读取配置，创建 LLM 实例"""
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("请设置环境变量 LLM_API_KEY")

    return ChatOpenAI(
        model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
        api_key=api_key,
        temperature=0.85,
    )


# ============ 状态定义 ============

class NovelState(TypedDict):
    """Agent 状态在各节点间传递"""
    messages: Annotated[list[BaseMessage], add_messages]
    task: str                          # 当前任务类型
    outline: dict                      # 大纲数据
    characters: list                   # 人物档案
    current_chapter: dict              # 当前章节信息
    draft: str                         # 草稿内容
    review_notes: list                 # 审稿意见
    final_content: str                 # 最终输出
    iteration: int                     # 当前迭代次数
    max_iterations: int                # 最大迭代次数


# ============ 节点函数 ============

def research_node(state: NovelState) -> dict:
    """研究节点：收集素材、回顾设定"""
    llm = get_llm()
    chapter = state.get("current_chapter", {})
    characters = state.get("characters", [])

    prompt = f"""你是一位小说创作助手。正在准备撰写章节。

章节信息: {json.dumps(chapter, ensure_ascii=False)}
相关人物: {json.dumps(characters, ensure_ascii=False)}

请梳理写作要点，包括：
1. 本章核心冲突/事件
2. 需要呼应的前文伏笔
3. 人物在本章应有的状态
4. 节奏和情绪走向"""

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "messages": [AIMessage(content=f"研究完成: {response.content[:200]}...")],
    }


def draft_node(state: NovelState) -> dict:
    """写作节点：生成章节内容"""
    llm = get_llm()
    chapter = state.get("current_chapter", {})
    characters = state.get("characters", [])
    iteration = state.get("iteration", 0)
    review_notes = state.get("review_notes", [])

    chapter_number = chapter.get("number", 0)
    chapter_title = chapter.get("title", "未命名")
    outline_card = chapter.get("outline", "")

    if iteration > 0 and review_notes:
        # 修改模式
        prompt = f"""你是小说创作助手。请根据以下审稿意见修改章节。

原章节内容:
{state.get("draft", "")}

审稿意见:
{chr(10).join(f"- {note}" for note in review_notes)}

请输出修改后的完整章节内容。"""
    else:
        # 初稿模式
        prompt = f"""你是小说创作助手。请撰写以下章节。

章节编号: 第{chapter_number}章
章节标题: {chapter_title}
大纲卡片: {outline_card}
相关人物: {json.dumps(characters, ensure_ascii=False)}

要求:
- 每章严格 3200-3800 中文字符
- 流畅的现代白话文，避免翻译腔和 AI 腔
- 对话符合人物身份
- 展示而非说教 (show, don't tell)
- 章节末尾留下推进力

请直接输出章节正文，不要加标题。"""

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "draft": response.content,
        "iteration": iteration + 1,
        "messages": [AIMessage(content=f"第{iteration + 1}版草稿完成，约 {len(response.content)} 字符")],
    }


def review_node(state: NovelState) -> dict:
    """审稿节点：检查质量"""
    llm = get_llm()
    draft = state.get("draft", "")
    chapter = state.get("current_chapter", {})
    characters = state.get("characters", [])

    prompt = f"""你是严格的审稿编辑。请检查以下章节，输出 JSON 格式的审稿意见。

章节: 第{chapter.get("number", "?")}章 - {chapter.get("title", "?")}
正文（前500字）: {draft[:500]}...
正文字数: {len(draft)}
相关人物: {json.dumps(characters, ensure_ascii=False)}

检查维度:
1. 字数是否在 3200-3800 字范围内
2. 是否符合人物设定
3. 是否有 AI 写作痕迹（套话、空洞修辞）
4. 节奏是否合适
5. 章节末尾是否有推进力

请输出 JSON 数组，每项是一条修改意见。如果没有问题返回空数组。
格式: ["意见1", "意见2", ...]"""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        notes = json.loads(response.content.strip())
        if not isinstance(notes, list):
            notes = []
    except (json.JSONDecodeError, ValueError):
        notes = []

    return {
        "review_notes": notes,
        "messages": [AIMessage(content=f"审稿完成，发现 {len(notes)} 个问题")],
    }


def finalize_node(state: NovelState) -> dict:
    """定稿节点"""
    draft = state.get("draft", "")
    notes = state.get("review_notes", [])

    if notes:
        final = draft + "\n\n---\n待修改:\n" + "\n".join(f"- {n}" for n in notes)
    else:
        final = draft

    return {
        "final_content": final,
        "messages": [AIMessage(content="定稿完成")],
    }


# ============ 条件边 ============

def should_revise(state: NovelState) -> Literal["draft", "finalize"]:
    """判断是否需要修改：有问题且未达最大迭代次数"""
    notes = state.get("review_notes", [])
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 3)

    if notes and iteration < max_iter:
        return "draft"
    return "finalize"


# ============ 构建图 ============

def build_agent():
    """构建 LangGraph 状态图"""
    builder = StateGraph(NovelState)

    builder.add_node("research", research_node)
    builder.add_node("draft", draft_node)
    builder.add_node("review", review_node)
    builder.add_node("finalize", finalize_node)

    builder.set_entry_point("research")

    builder.add_edge("research", "draft")
    builder.add_edge("draft", "review")
    builder.add_conditional_edges(
        "review",
        should_revise,
        {
            "draft": "draft",
            "finalize": "finalize",
        }
    )
    builder.add_edge("finalize", END)

    return builder.compile()


# ============ MCP Server ============

def create_mcp_server():
    """创建 MCP 服务器"""
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    app = Server("novelist-agent")
    agent = build_agent()

    @app.list_tools()
    async def list_tools():
        return [
            Tool(
                name="write_chapter",
                description="根据大纲和人物设定撰写章节正文，自动审稿和迭代修改",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "chapter_number": {"type": "integer", "description": "章节编号"},
                        "chapter_title": {"type": "string", "description": "章节标题"},
                        "outline_card": {"type": "string", "description": "本章大纲卡片/情节要点"},
                        "characters": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "traits": {"type": "string"},
                                }
                            },
                            "description": "相关人物列表，每项含 name 和 traits"
                        },
                    },
                    "required": ["chapter_number", "chapter_title", "outline_card"],
                },
            ),
            Tool(
                name="review_chapter",
                description="审稿：检查字数、人设一致性、AI痕迹、节奏、钩子",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "chapter_content": {"type": "string", "description": "章节正文"},
                        "characters": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "相关人物列表"
                        },
                    },
                    "required": ["chapter_content"],
                },
            ),
            Tool(
                name="revise_chapter",
                description="根据审稿意见修改章节内容",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "chapter_content": {"type": "string", "description": "原章节内容"},
                        "review_notes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "修改意见列表"
                        },
                    },
                    "required": ["chapter_content", "review_notes"],
                },
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            if name == "write_chapter":
                result = agent.invoke({
                    "task": "chapter",
                    "current_chapter": {
                        "number": arguments["chapter_number"],
                        "title": arguments["chapter_title"],
                        "outline": arguments["outline_card"],
                    },
                    "characters": arguments.get("characters", []),
                    "iteration": 0,
                    "max_iterations": 3,
                    "review_notes": [],
                    "messages": [HumanMessage(content=f"撰写第{arguments['chapter_number']}章")],
                })
                return [TextContent(type="text", text=result.get("final_content", ""))]

            elif name == "review_chapter":
                result = agent.invoke({
                    "task": "review",
                    "draft": arguments["chapter_content"],
                    "characters": arguments.get("characters", []),
                    "current_chapter": {"number": 0, "title": "审稿"},
                    "iteration": 0,
                    "max_iterations": 1,
                    "review_notes": [],
                    "messages": [HumanMessage(content="审稿")],
                })
                notes = result.get("review_notes", [])
                return [TextContent(type="text", text=json.dumps(notes, ensure_ascii=False, indent=2))]

            elif name == "revise_chapter":
                result = agent.invoke({
                    "task": "revise",
                    "draft": arguments["chapter_content"],
                    "review_notes": arguments["review_notes"],
                    "current_chapter": {"number": 0, "title": "修改"},
                    "characters": [],
                    "iteration": 1,
                    "max_iterations": 2,
                    "messages": [HumanMessage(content="修改章节")],
                })
                return [TextContent(type="text", text=result.get("final_content", result.get("draft", "")))]

            return [TextContent(type="text", text=f"未知工具: {name}")]

        except Exception as e:
            return [TextContent(type="text", text=f"错误: {str(e)}")]

    return app


# ============ 入口 ============

async def main():
    app = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
