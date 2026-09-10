# writer-agent-fx - 区间式小说创作 LangGraph Agent

基于 LangGraph 的小说创作 Agent。与 `../langgraph-agent` 不同, 本 Agent 支持
**从任意阶段开始、任意阶段结束**的区间执行, 管路按需裁剪, 仿照
LangGraph-Chatchat 的 graph 注册/断点/checkpoint 模式实现。

原 `langgraph-agent` 保持不变, 本目录为新增。

## 工作流阶段

| 阶段标识 | 中文 | 输入(前置) | 产物 |
|---------|------|-----------|------|
| `research` | 调研 | task / input_data | research_notes |
| `outline`  | 大纲 | research_notes | outline |
| `draft`    | 写稿 | outline | draft |
| `review`   | 审稿 | draft | review_notes |
| `revise`   | 修改 | draft + review_notes | draft(更新) |
| `finalize` | 定稿 | draft | final_content |

## 区间执行

任意 `[start, end]` 区间都可作为独立的一次运行:

- 整段: `research → outline → draft → review → revise → finalize`
- 只写稿+审稿: `draft → review` (从写稿开始, 审稿后结束)
- 只定稿: `finalize → finalize`
- 跳过头尾: `review → revise`

> 从中间阶段开始时, 必须预置该阶段所需输入字段 (见上表"输入")。
> 例如 `--start review` 需要提供 `draft`; `--start revise` 需要
> 提供 `draft` 与 `review_notes`。

## 安装

```bash
# Windows 推荐用你自己的 Python 环境 (与 LangGraph-Chatchat 同栈)
cd D:\devProject\writer\langgraph-writer
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 配置密钥 (复制 .env.example 为 .env 并填写)
copy .env.example .env
```

## 独立命令行

```bash
# 全流程
python run_agent.py cli --start research --end finalize --task "写第7章: 主角伪装成NPC混入敌方公会"

# 只写稿+审稿 (从写稿开始, 大纲可由 @文件 传入)
python run_agent.py cli --start draft --end review --outline @outline_07.txt --task "本章以对白为主"

# 只修改+定稿 (预置草稿与意见)
python run_agent.py cli --start revise --end finalize --draft @chap7_draft.md --notes "AI痕迹重,节奏拖沓,结尾钩子弱"

# 交互模式: 阶段之间暂停, 可人工注入/修正后继续
python run_agent.py cli --start draft --end review --interactive --task "..."

# 列出阶段
python run_agent.py cli --list-stages
```

## 库方式调用

```python
from writer_agent import build_agent, run_interval
from langgraph.checkpoint.memory import MemorySaver

# 只跑写稿→审稿
graph = build_agent(start="draft", end="review", checkpointer=MemorySaver())
result = graph.invoke({
    "task": "写第8章: 陆寻拿到织律者徽记后的第一次实战",
    "outline": "开场战 → 首胜 → 发现徽记异常 → 悬念收尾",
    "iteration": 0,
    "max_iterations": 3,
    "messages": [],
})
print(result["draft"])
print(result["review_notes"])
```

## MCP 集成 (opencode)

把本目录的 `opencode.json` 合并进项目 `.opencode/opencode.json`:

```json
{
  "mcp": {
    "writer-interval-agent": {
      "type": "local",
      "command": ["python", "D:/devProject/writer/langgraph-writer/run_agent.py", "mcp"],
      "enabled": true,
      ...
    }
  }
}
```

暴露工具: `run_workflow` — 参数 `start` / `end` 选定区间, 其余字段按需预置。

## 架构

```
writer_agent/
├── state.py          # WriterState + 阶段顺序/区间校验
├── registry.py       # @register_stage 注册中心 (仿 chatchat graphs_registry)
├── nodes.py          # 6 个阶段节点实现
├── graph_builder.py  # 区间动态建图 + interrupt 断点 + run_interval
├── cli.py            # 独立命令行入口
└── mcp_server.py     # MCP server 封装
run_agent.py          # 统一入口 (cli | mcp)
```

状态统一用 `TypedDict + add_messages` (与 chatchat 相同的消息队列语义);
`WriterGraph`/`build_agent` 提供面向对象与函数式两种调用方式;
区间图只编译 `[start, end]` 范围内的节点, 执行严格从 start 入、于 end 出。

## 依赖

`langgraph`, `langchain-core`, `langchain-openai`, `mcp`, `python-dotenv`