"""独立调用 CLI: 以区间方式驱动 Writer Agent。

示例:
    # 全流程
    python cli.py --start research --end finalize --task "写第7章"

    # 只写稿+审稿 (从写稿开始)
    python cli.py --start draft --end review --outline "..." --task "..."

    # 从任意阶段开始, 必须预置该阶段所需字段:
    python cli.py --start revise --end finalize --draft "草稿内容" --notes "意见1,意见2"

    # 交互模式: 阶段之间暂停, 可修改与续跑
    python cli.py --start draft --end review --interactive --task "..."
"""

import argparse
import os
import sys

from langgraph.checkpoint.memory import MemorySaver

from .graph_builder import build_agent
from .state import STAGE_LABELS, STAGE_ORDER, validate_interval


def _load_env():
    """尽力加载 .env (无 python-dotenv 时静默跳过)。"""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def _read_file_or_value(text: str) -> str:
    """若参数以 @ 开头, 视为文件路径读取; 否则返回原值。"""
    if text.startswith("@"):
        path = text[1:]
        if not os.path.exists(path):
            raise FileNotFoundError(f"文件不存在: {path}")
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    return text


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="writer-agent",
        description="区间式小说创作 Agent (LangGraph)",
    )
    parser.add_argument("--agent", help="选择 agent 图: novelist / content_reviser / ai_trace_checker / craft_reviewer / style_curator / chapter_finalizer / writer_workflow / base_rag / plan_execute_agent / reflexion; 提供时用 --message 发指令")
    parser.add_argument("--message", help="发给 agent 的中文指令 (--agent 模式)")
    parser.add_argument("--project", help="小说项目目录 (供 agent 的文件工具使用, 默认当前目录)")
    parser.add_argument("--start", default="research", help="起始阶段")
    parser.add_argument("--end", default="finalize", help="结束阶段")
    parser.add_argument("--task", help="任务描述")
    parser.add_argument("--outline", help="大纲 (支持 @文件路径)")
    parser.add_argument("--draft", help="草稿 (支持 @文件路径)")
    parser.add_argument("--research", help="调研纪要 (支持 @文件路径)")
    parser.add_argument("--notes", help="审稿意见, 逗号分隔")
    parser.add_argument("--input-json", help="整个 input_data 的 JSON 文件/字符串")
    parser.add_argument("--word-count", type=int, default=3200, help="目标字数")
    parser.add_argument("--interactive", action="store_true", help="阶段间暂停供人工介入")
    parser.add_argument("--silent", action="store_true", help="只输出结果, 不打印日志")
    parser.add_argument("--list-stages", action="store_true", help="列出阶段并退出")
    parser.add_argument("--list-agents", action="store_true", help="列出所有 agent 图并退出")
    parser.add_argument("--output", help="将最终输出写入该文件")
    parser.add_argument("--model", help="覆盖 LLM_MODEL 环境变量")
    parser.add_argument("--base-url", help="覆盖 LLM_BASE_URL")
    parser.add_argument("--api-key", help="覆盖 LLM_API_KEY")
    parser.add_argument(
        "text", nargs="*",
        help="裸中文指令（等价于 --message；未指定 --agent 时默认 novelist）",
    )
    return parser.parse_args(argv)


def resolve_agent_message(args) -> None:
    """便捷入口：把裸中文指令收进 --message，并在未指定时默认 novelist。

    让 `run_agent.py cli 帮我写第7章` 等价于
    `run_agent.py cli --agent novelist --message "帮我写第7章"`。
    """
    free_text = " ".join(args.text).strip() if getattr(args, "text", None) else ""
    if not args.message and free_text:
        args.message = free_text
    if args.message and not args.agent:
        args.agent = "novelist"


def _handshake_interrupt(graph, snapshot, config):
    """交互断点处理器: 展示当前产物, 让用户编辑后继续。"""
    print("\n=== [断点] 阶段产出预览 ===", file=sys.stderr)

    preview_fields = {
        "research_notes": "调研纪要",
        "outline": "大纲",
        "draft": "草稿",
        "review_notes": "审稿意见",
        "final_content": "定稿",
    }
    for key, label in preview_fields.items():
        value = snapshot.get(key)
        if value:
            text = (
                "\n".join(f"- {n}" for n in value)
                if isinstance(value, list)
                else str(value)
            )
            print(f"--- {label} ---\n{text[:500]}{'…' if len(str(value)) > 500 else ''}\n", file=sys.stderr)

    choice = input("继续输入 'c' / 'q' 退出; 其余输入将作为新的任务描述注入: ").strip()
    if choice.lower() == "q":
        raise SystemExit(f"用户中止。当前停在: {[i.name for i in snapshot.get('__interrupt__', [])]}")
    if choice.lower() == "c":
        return None
    return {"task": choice}


def build_initial_state(args) -> dict:
    """将 CLI 参数组装为初始 WriterState。"""
    if args.outline:
        args.outline = _read_file_or_value(args.outline)
    if args.draft:
        args.draft = _read_file_or_value(args.draft)
    if args.research:
        args.research = _read_file_or_value(args.research)

    validate_interval(args.start, args.end)

    input_data = {"target_word_count": args.word_count}
    if args.input_json:
        import json

        raw = _read_file_or_value(args.input_json)
        try:
            input_data = json.loads(raw)
            if not isinstance(input_data, dict):
                input_data = {"payload": input_data}
        except json.JSONDecodeError:
            input_data = {"raw": raw}

    notes = [
        n.strip() for n in (args.notes or "").split(",") if n.strip()
    ] or None

    state = {
        "task": args.task or "创作章节正文",
        "input_data": input_data,
        "iteration": 0,
        "max_iterations": 3,
        "messages": [],
    }
    if args.research:
        state["research_notes"] = args.research
    if args.outline:
        state["outline"] = args.outline
    if args.draft:
        state["draft"] = args.draft
    if notes:
        state["review_notes"] = notes
    return state


def main(argv=None) -> int:
    args = parse_args(argv)
    _load_env()

    if args.list_stages:
        print("阶段顺序 (索引: 名称: 中文):")
        for idx, name in enumerate(STAGE_ORDER):
            print(f"  {idx}: {name} -> {STAGE_LABELS[name]}")
        return 0

    # 环境变量覆盖
    if args.model:
        os.environ["LLM_MODEL"] = args.model
    if args.base_url:
        os.environ["LLM_BASE_URL"] = args.base_url
    if args.api_key:
        os.environ["LLM_API_KEY"] = args.api_key

    if not os.environ.get("LLM_API_KEY"):
        print("错误: 未设置 LLM_API_KEY (可在 cli.py 同目录 .env 配置)", file=sys.stderr)
        return 2

    resolve_agent_message(args)

    # agent 图模式: 由选定 agent 解析指令并调用 skill 工具
    if args.agent:
        from .app import run_agent

        if not args.message:
            print("错误: --agent 模式需要 --message 指令", file=sys.stderr)
            return 2
        print(f"[writer-agent] 执行 agent: {args.agent}")
        output = run_agent(
            args.agent,
            args.message,
            project_dir=args.project,
            start=args.start,
            end=args.end,
        )
        print("\n========= 输出 =========")
        print(output)
        print("========= 结束 =========")
        if args.output:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(output)
            print(f"\n已写入: {args.output}")
        return 0

    state = build_initial_state(args)
    if not args.silent:
        print(f"[writer-agent] 执行区间: {STAGE_LABELS[args.start]} → {STAGE_LABELS[args.end]}")


    graph = build_agent(
        start=args.start,
        end=args.end,
        interactive=args.interactive,
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "cli-run"}}

    if args.interactive:
        from .graph_builder import run_interval

        result = run_interval(
            state,
            start=args.start,
            end=args.end,
            config=config,
            interactive=True,
            on_interrupt=_handshake_interrupt,
        )
    else:
        result = graph.invoke(state, config)

    output = result.get("final_content") or result.get("draft") or ""
    if not output and result.get("review_notes"):
        output = "审稿意见:\n" + "\n".join(f"- {n}" for n in result["review_notes"])
    if not output and result.get("outline"):
        output = result["outline"]
    if not output and result.get("research_notes"):
        output = result["research_notes"]

    if args.silent:
        print(output)
    else:
        print("\n========= 输出 =========")
        print(output)
        print("========= 结束 =========")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"\n已写入: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())