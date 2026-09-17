"""基础文件工具（无 LLM，供 agent 图读取/写入小说项目文件）。

与原 opencode agent 依赖编辑器文件能力对应：agent 需自行读取
`SKILL.md / 设定/ / 章节大纲/ / 正文/` 等文件后再调用 skill 工具。
"""

import fnmatch
import os
from pathlib import Path

from .registry import regist_tool


def _resolve(path: str) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return p


@regist_tool(
    title="读取文件",
    description="读取小说项目中的任意文本文件（SKILL.md、设定、大纲、正文、修改记录等）并返回内容。",
)
def read_file(path: str) -> str:
    """Read a text file from the novel project."""
    p = _resolve(path)
    if not p.exists():
        return f"（文件不存在: {p}）"
    try:
        return p.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        return f"（读取失败: {exc}）"


@regist_tool(
    title="写入文件",
    description="把内容写入小说项目文件（覆盖）。用于保存章节正文、大纲、设定、修改记录、推荐平台档案等。路径相对项目目录或写绝对路径。",
)
def write_file(path: str, content: str) -> str:
    """Write content to a file (overwrites)."""
    p = _resolve(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"（已写入: {p}）"
    except Exception as exc:  # noqa: BLE001
        return f"（写入失败: {exc}）"


@regist_tool(
    title="搜索文件内容",
    description="在指定目录下的文本文件中按关键词/正则搜索（如查人名、地名、伏笔关键词是否出现）。",
)
def search_files(pattern: str, directory: str = "") -> str:
    """Search text files under directory for pattern, return file:line matches."""
    root = _resolve(directory) if directory else Path.cwd()
    import re

    try:
        regex = re.compile(pattern)
    except re.error as exc:
        return f"（正则错误: {exc}）"
    hits: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", ".venv", "__pycache__", ".idea"}]
        for fn in sorted(filenames):
            if not fn.endswith((".md", ".txt", ".json")):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                for i, line in enumerate(Path(fp).read_text(encoding="utf-8").splitlines(), 1):
                    if regex.search(line):
                        hits.append(f"{fp}:{i}: {line.strip()[:200]}")
            except Exception:  # noqa: BLE001
                continue
    return "\n".join(hits) if hits else "（无匹配）"


@regist_tool(
    title="列出文件",
    description="列出目录结构（含文件与子目录名），用于确认小说项目/分部/章节布局。",
)
def list_files(directory: str = "", pattern: str = "*") -> str:
    """List files under directory matching glob pattern."""
    root = _resolve(directory) if directory else Path.cwd()
    if not root.exists():
        return f"（目录不存在: {root}）"
    lines = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", ".venv", "__pycache__", ".idea"}]
        depth = dirpath[len(str(root)):].count(os.sep)
        if depth > 4:
            continue
        rel_head = os.path.relpath(dirpath, root).replace("\\", "/")
        prefix = "  " * depth
        lines.append(f"{prefix}{rel_head}/" if rel_head != "." else f"{prefix}.")
        for fn in sorted(filenames):
            if fnmatch.fnmatch(fn, pattern):
                lines.append(f"{prefix}  {fn}")
    return "\n".join(lines) if lines else "（空目录）"