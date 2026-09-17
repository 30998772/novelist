# writer-agent-fx - 小说创作 LangGraph Agent

基于 LangGraph 的小说创作 Agent（架构对齐
[LangGraph-Chatchat](https://github.com/chatchat-space/LangGraph-Chatchat)）。
本项目把 writer 项目里原有的 opencode agent / skill 全部迁移进 LangGraph 框架，并按
LangGraph-Chatchat 的 graphs_factory 结构补齐框架层与 Agentic RAG：

- **原 6 个 agent → 图（graphs_factory）**：novelist、content-reviser、ai-trace-checker、
  craft-reviewer、style-curator、chapter-finalizer，各自注册为 Graph 类。
- **框架层图**：`base_agent`（LLM+工具聊天图基类）、`base_rag`（Agentic RAG：
  检索→评分→生成/改写）、`plan_execute_agent`（计划执行）、`reflexion`（自我反思）。
- **原 25 个 skill → 工具（tools_factory）**：每个 skill 导出一个 tool，被图内的 LLM
  以 function-call 方式调用，工具内部按技能规则调用 LLM 输出结果；另有 2 个 RAG 检索
  工具（`search_knowledge` / `search_manuscript`）与 4 个文件工具。
- 每个图是可独立运行的「LLM + 工具集」聊天工作流；`novelist` 绑定全部工具做全能调度，
  专项 agent 只绑定自己辖区的工具（逻辑/技法/AI痕迹/文风）。

## 工作流阶段（writer_workflow 图）

保留原区间式流水线，作为注册图之一直接可用:

| 阶段标识 | 中文 | 输入(前置) | 产物 |
|---------|------|-----------|------|
| `research` | 调研 | task / input_data | research_notes |
| `outline`  | 大纲 | research_notes | outline |
| `draft`    | 写稿 | outline | draft |
| `check_word_count` | 字数校验（code 节点） | draft | cjk_count（失败自动回跳 draft） |
| `check_blacklist` | 禁用词扫描（code 节点） | draft | blacklist_hits（命中自动回跳 draft） |
| `review`   | 审稿 | draft | review_notes |
| `revise`   | 修改 | draft + review_notes | draft(更新) |
| `finalize` | 定稿 | draft | final_content |

支持任意 `[start, end]` 区间执行（含断点交互与 checkpoint 恢复）。

### 确定性校验与条件回跳（harness 部分）

`draft` 后有 2 个 **code 节点（纯 Python，不经 LLM）** 做硬校验——

```
draft → check_word_count →(不达标 且 未超限)→ draft(携带失败原因重写)
         │ 达标
         ▼
     check_blacklist →(命中禁用词 且 未超限)→ draft(携带失败原因重写)
         │ 干净
         ▼
        review ──(有意见 且 未超限)──→ revise ─→ check_word_count →… → review(复检)
           └─(无意见 / 循环耗尽)─→ finalize → END
```

- 校验失败时 `state.check_error` 会写明原因，回跳 `draft` 时注入重写提示词（只修问题、保留骨架）
- 回跳次数以 `max_iterations` 封顶，耗尽后即使不合格也强制放行进 `review`，避免死循环
- 禁用词默认清单 `nodes.py#DEFAULT_BLACKLIST`（微微/轻轻/缓缓/某种…），可用 `input_data.blacklist_words` 覆盖
- 字数目标来自 `input_data.target_word_count`，允许区间 `[0.9×, 1.1×]`，可用 `min_word_count`/`max_word_count` 显式指定

## 已注册图（label: agent / rag）

| 图名 | label | 中文标题 | 角色 |
|------|-------|----------|------|
| `base_rag` | rag | 基础RAG | Agentic RAG：chatbot 决定是否检索 → retrieve → grade → generate/rewrite |
| `plan_execute_agent` | agent | 计划执行机器人 | planner → executor(react) → replan 循环，直到给出 Response |
| `reflexion` | agent | 自我反思机器人 | draft → 检索 → revise 循环，带 missing/superfluous 批判与引用 |
| `novelist` | agent | 小说创作主力 | 全能调度，绑定全部 skill 工具 + 文件工具 |
| `content_reviser` | 内容修订 | 逻辑/连贯/人设/伏笔/时间线；continuity_check 等 |
| `ai_trace_checker` | AI 痕迹审核 | 降AI/高频词/标点/重复；ai_trace_check |
| `craft_reviewer` | 技法审稿 | 节奏/钩子/对话/描写/情感/打斗 |
| `style_curator` | 文风定制守护 | writing_style / scene_description |
| `chapter_finalizer` | 一站式终审 | 八步流水线，绑全部工具 |
| `writer_workflow` | 区间式创作流水线 | research→…→finalize；含 code 校验节点与 review↔revise 条件回跳 |

## 已注册工具（25 个 skill + 2 个 RAG 检索 + 4 文件工具）

RAG 检索: `search_knowledge`(写作知识库) `search_manuscript`(各书设定/正文，跨章查伏笔)

构思规划: `story_brainstorm` `story_outline`(含大纲评分) `character_design` `worldbuilding`
`story_core_master`(含丰满度/AI协作)

写作技法: `writing_style` `narrative_viewpoint` `dialogue_craft` `scene_description`
`pacing_control` `hook_opening` `dragon_ride_007` `urobuchi_gen`
`anime_lightnovel_styles`

场景类型: `emotion_scene` `action_scene` `suspense_twist`

质检修订: `chapter_drafting` `revision` `continuity_check` `ai_trace_check` `revision_log`

运营辅助: `title_blurb` `recommend_platform` `add_setting`

文件工具: `read_file` `write_file` `search_files` `list_files`

## 安装

需要 **Python 3.12**（与 LangGraph-Chatchat 旧栈一致；langchain 0.3 / langgraph 0.2
在 3.13+ 上会因 pydantic 无法解析旧类型注解而导入失败）。

```bash
# Windows: 用 Python 3.12 建环境 (与 LangGraph-Chatchat 同栈)
cd D:\devProject\writer\langgraph-writer
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# WSL/Linux (无 py3.12 时可用 uv 装):
#   curl -LsSf https://astral.sh/uv/install.sh | sh
#   uv python install 3.12
#   uv venv --python 3.12 .venv
#   uv pip install --python .venv/bin/python -r requirements.txt

# 配置密钥 (复制 .env.example 为 .env 并填写)
copy .env.example .env
```

## 独立命令行

```bash
# 走 novelist 全能 agent: "写下一章"、"终审 ch012"、"这本书投哪好"
python run_agent.py cli --agent novelist --message "写第7章: 主角伪装成NPC混入敌方公会" --project "D:\devProject\writer\BUG 玩家：我能卡出游戏规则"

# 专项 agent
python run_agent.py cli --agent content_reviser --message "查一下ch012的逻辑和伏笔" --project ...
python run_agent.py cli --agent ai_trace_checker  --message "降一下ch013的AI痕迹" --project ...
python run_agent.py cli --agent chapter_finalizer --message "终审这一章" --project ...

# 区间流水线 (旧 CLI 不变)
python run_agent.py cli --start research --end finalize --task "写第7章: ..."
python run_agent.py cli --start draft --end review --outline @outline_07.txt --task "本章以对白为主"
python run_agent.py cli --list-stages
```

## 库方式调用

```python
from writer_agent import create_graph, run_agent, build_tools, get_graph_class
from langgraph.checkpoint.memory import MemorySaver

# 1) 装配 novelist 图 (绑定全部 skill 工具)
graph_obj = create_graph("novelist", checkpointer=MemorySaver())
compiled = graph_obj.get_graph()
result = compiled.invoke({
    "messages": [("user", "帮我设计一个能卡系统BUG的主角设定")],
    "history": [],
    "project_dir": "D:/devProject/writer/BUG 玩家：我能卡出游戏规则",
})
print(result["messages"][-1].content)

# 2) 一键执行
print(run_agent("novelist", "写下一章", project_dir="..."))
print(run_agent("ai_trace_checker", "降一下AI痕迹", project_dir="..."))

# 3) 区间流水线
from writer_agent.graph_builder import build_agent
graph = build_agent(start="draft", end="review", checkpointer=MemorySaver())
```

## MCP 集成 (opencode)

把本目录的 `opencode.json` 合并进项目 `.opencode/opencode.json`（或直接引用）。启动后
暴露两个工具:

- `run_agent` — 参数 `agent`(10 个图之一) / `message` / `project_dir` / `start` / `end`。
- `run_workflow` — 参数 `start` / `end` 选定区间, 其余字段按需预置。

## 架构

```
writer_agent/
├── state.py              # WriterState: 消息队列(消息/历史) + 阶段字段 + agent 路由
├── llm.py                # get_llm() 统一入口
├── registry.py           # @register_stage 阶段节点注册 (区间流水线用)
├── nodes.py              # 6 个流水线阶段节点
├── graph_builder.py      # 区间动态建图 + interrupt 断点 + run_interval
├── app.py                # build_tools / create_graph / run_agent 装配入口
├── graphs_factory/
│   ├── graphs_registry.py    # @register_graph + Graph 基类 (rag/agent 双注册表)
│   ├── base_agent.py         # LLM+工具 聊天图基类 (仿 chatchat base_agent)
│   ├── base_rag.py           # Agentic RAG 图 (仿 chatchat base_rag, label=rag)
│   ├── plan_and_execute.py   # 计划执行图 (仿 chatchat plan_and_execute)
│   ├── reflexion.py          # 自我反思图 (仿 chatchat reflexion)
│   ├── novelist.py ...       # 6 个 agent 图 + writer_workflow 图
├── tools_factory/
│   ├── tools_registry.py     # @regist_tool 工具注册中心 (仿 chatchat)
│   ├── _runner.py / _files.py # skill 规则加载 + LLM 执行器
│   ├── file_tools.py         # read_file / write_file / search_files / list_files
│   └── *.py                  # 27 个 skill 工具
├── cli.py                 # 命令行 (--agent / 区间流水线)
└── mcp_server.py          # MCP server (run_agent / run_workflow)
run_agent.py               # 统一入口 (cli | mcp)
```

状态语义与 chatchat 对齐：`TypedDict + add_messages`；图只把关键信息写入
`messages` 队列，`history` 做 history_len 裁剪；图的注册/断点/checkpoint 模式
均仿照 LangGraph-Chatchat 的 graphs_factory 实现。

## 依赖

`langgraph`(0.2.x), `langchain`(0.3.x), `langchain-core`(0.3.x), `langchain-openai`(0.3.x),
`mcp`, `python-dotenv`；已在 `requirements.txt` 用上界锁死，避免被拉到 1.x 破坏旧 API。