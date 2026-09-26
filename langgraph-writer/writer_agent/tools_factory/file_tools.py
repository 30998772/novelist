"""基础文件工具（无 LLM，供 agent 图读取/写入小说项目文件）。"""

import fnmatch
import os
from pathlib import Path

from .registry import regist_tool

# 项目根目录（novelist/）
_NOVELS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "novelist"


def _resolve(path: str, project_dir: str = "") -> Path:
    """解析路径：如果 project_dir 非空，基于 project_dir 解析；否则基于 _NOVELS_DIR。"""
    p = Path(path).expanduser()
    if p.is_absolute():
        return p
    base = _NOVELS_DIR / project_dir if project_dir else _NOVELS_DIR
    return base / p


@regist_tool(
    title="读取文件",
    description="读取小说项目中的文本文件。可指定起始行和行数来只读部分文件。路径相对于项目目录（书名/）。",
)
def read_file(path: str, project_dir: str = "", offset: int = 0, limit: int = 0) -> str:
    """Read a text file, optionally with line range."""
    p = _resolve(path, project_dir)
    if not p.exists():
        return f"（文件不存在: {p}）"
    try:
        content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        if offset > 0 or limit > 0:
            end = offset + limit if limit > 0 else len(lines)
            selected = lines[offset:end]
            total = len(lines)
            return f"（第{offset+1}-{min(end, total)}行/共{total}行）\n" + "\n".join(selected)
        return content
    except Exception as exc:
        return f"（读取失败: {exc}）"


@regist_tool(
    title="写入文件",
    description="把内容写入小说项目文件（覆盖）。路径相对于项目目录（书名/）。自动创建父目录。",
)
def write_file(path: str, content: str, project_dir: str = "") -> str:
    """Write content to a file (overwrites)."""
    import asyncio
    p = _resolve(path, project_dir)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        # 如果在异步上下文中，用线程池写入
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                loop.run_in_executor(pool, lambda: p.write_text(content, encoding="utf-8"))
        except RuntimeError:
            # 同步上下文，直接写
            p.write_text(content, encoding="utf-8")
        return f"（已写入: {p}）"
    except Exception as exc:
        return f"（写入失败: {exc}）"


@regist_tool(
    title="搜索文件内容",
    description="在项目目录下按关键词/正则搜索。",
)
def search_files(pattern: str, directory: str = "", project_dir: str = "") -> str:
    """Search text files under directory for pattern."""
    root = _resolve(directory, project_dir)
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
            except Exception:
                continue
    return "\n".join(hits) if hits else "（无匹配）"


@regist_tool(
    title="列出文件",
    description="列出项目目录结构。可指定最大深度。",
)
def list_files(directory: str = "", pattern: str = "*", project_dir: str = "", max_depth: int = 3) -> str:
    """List files under directory matching glob pattern."""
    root = _resolve(directory, project_dir)
    if not root.exists():
        return f"（目录不存在: {root}）"
    lines = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", ".venv", "__pycache__", ".idea"}]
        depth = dirpath[len(str(root)):].count(os.sep)
        if depth >= max_depth:
            dirnames.clear()
            continue
        rel_head = os.path.relpath(dirpath, root).replace("\\", "/")
        prefix = "  " * depth
        lines.append(f"{prefix}{rel_head}/" if rel_head != "." else f"{prefix}.")
        for fn in sorted(filenames):
            if fnmatch.fnmatch(fn, pattern):
                lines.append(f"{prefix}  {fn}")
    return "\n".join(lines) if lines else "（空目录）"


@regist_tool(
    title="创建项目目录",
    description="为新书创建标准目录结构。传入书名，自动创建：设定/、章节大纲/、正文/、系列规划/ 等文件夹及基础文件。",
)
def create_project(book_title: str, genre: str = "", summary: str = "") -> str:
    """Create project directory structure for a new book. Creates folders and base files."""
    base = _NOVELS_DIR / book_title
    try:
        # 创建目录
        for d in ["设定", "设定/世界观设定", "设定/角色设定", "章节大纲", "正文", "系列规划"]:
            (base / d).mkdir(parents=True, exist_ok=True)

        # 写入 README.md
        readme = f"""# 《{book_title}》

## 项目简介
- **题材**：{genre or '待定'}
- **核心冲突**：{summary or '待定'}

## 目录结构
```
{book_title}/
├── SKILL.md           # 本书专属规范
├── README.md          # 项目说明
├── 设定/
│   ├── 世界观设定/
│   └── 角色设定/
├── 章节大纲/
│   ├── 总纲.md        # 全书总览
│   └── 逐章卡片.md    # 逐章大纲
├── 正文/              # 章节正文
└── 系列规划/          # 分卷结构
```
"""
        (base / "README.md").write_text(readme, encoding="utf-8")

        # 写入空 SKILL.md
        (base / "SKILL.md").write_text(f"# 《{book_title}》创作规范\n\n## 类型定位\n{genre or '待定'}\n", encoding="utf-8")

        # 写入空总纲
        (base / "章节大纲" / "总纲.md").write_text(f"# 《{book_title}》总纲\n\n## 故事梗概\n\n## 人物表\n\n## 伏笔登记\n", encoding="utf-8")

        return f"（已创建项目目录: {base}）"
    except Exception as exc:
        return f"（创建失败: {exc}）"
