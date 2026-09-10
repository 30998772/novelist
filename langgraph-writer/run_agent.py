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

    args, rest = parser.parse_known_args(argv)

    if args.command == "mcp":
        from writer_agent.mcp_server import main as mcp_main

        asyncio_run(mcp_main())
        return 0

    if args.command == "cli":
        from writer_agent.cli import main as cli_main

        return cli_main(rest)

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