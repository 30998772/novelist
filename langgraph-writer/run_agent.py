"""统一入口。

命令行调用 (独立 Agent):
    python run_agent.py cli --start draft --end review --outline @大纲.txt

MCP server 运行 (供 opencode 集成):
    python run_agent.py mcp

库方式调用 (示例):
    from writer_agent import build_agent
    graph = build_agent(start="draft", end="review")
    result = graph.invoke({...})
"""

import argparse
import os
import sys


def _load_env():
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def main(argv=None):
    _load_env()
    parser = argparse.ArgumentParser(prog="run_agent")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("cli", help="以命令行方式运行 (同 writer_agent.cli)")
    sub.add_parser("mcp", help="以 MCP Server 方式运行")

    p_index = sub.add_parser("rag-index", help="重建 RAG 索引 (知识库 / 正文)")
    p_index.add_argument("--scope", default="all", choices=["all", "knowledge", "manuscript"])
    p_index.add_argument("--force", action="store_true", help="强制全量重建")

    p_query = sub.add_parser("rag-query", help="查询 RAG 索引，打印召回片段")
    p_query.add_argument("query", help="查询语句")
    p_query.add_argument("--scope", default="knowledge", choices=["knowledge", "manuscript"])
    p_query.add_argument("-k", type=int, default=5, help="召回条数")

    args, rest = parser.parse_known_args(argv)

    if args.command == "mcp":
        from writer_agent.mcp_server import main as mcp_main

        asyncio_run(mcp_main())
        return 0

    if args.command == "cli":
        from writer_agent.cli import main as cli_main

        return cli_main(rest)

    if args.command == "rag-index":
        from writer_agent.rag import build_all, build_index

        if args.scope == "all":
            build_all(force=args.force)
        else:
            build_index(args.scope, force=args.force)
        return 0

    if args.command == "rag-query":
        from writer_agent.rag import retrieve

        hits = retrieve(args.query, k=args.k, scope=args.scope)
        if not hits:
            print("(无召回结果)")
            return 0
        for h in hits:
            print(f"[{h['score']:.3f}] {h['source']}#{h['start']}-{h['end']} {h['heading']}")
            print(h["text"][:400])
            print("-" * 60)
        return 0

    return 2


def asyncio_run(coro):
    import asyncio

    try:
        asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(coro)


if __name__ == "__main__":
    sys.exit(main())