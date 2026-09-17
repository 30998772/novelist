---
name: workflow-writer
description: 创建或修改 opencode 工作流。当用户要新增工作流、修改工作流节点顺序、调整输入输出、编写节点 JSON 时使用。Use when creating/editing workflow definitions, node JSONs, or adding new pipeline steps.
---

# 工作流编写指南

本 skill 说明如何在 `.opencode/workflow/` 下创建完整的工作流，包含流程定义、节点注册、输出文件配置。

## 目录结构

```
.opencode/workflow/
├── workflow.schema.json          # workflow 定义的 JSON Schema
├── node.schema.json              # node 定义的 JSON Schema
├── chapter-pipeline.json         # 示例：章节创作全流程
├── workflow_engine.py            # 调度引擎（读 JSON → 解析 → 执行）
├── nodes/                        # 各节点定义
│   ├── research.json
│   ├── outline.json
│   ├── draft.json
│   ├── review.json
│   ├── revise.json
│   └── finalize.json
└── output/                       # workflow 产出的文件（若 project_dir 未指定）
```

## 创建新工作流的步骤

### 第1步：写 workflow JSON

文件名即工作流 ID（小写英文+连字符），放在 `.opencode/workflow/` 根目录。

必填字段：

```json
{
  "name": "my-workflow",
  "description": "一句话说明",
  "version": "1.0.0",
  "input": { ... },
  "output": { ... },
  "output_config": { ... },
  "nodes": [ ... ],
  "schedule": { ... }
}
```

**input 定义**：列出用户需要提供的参数，每个参数声明 type / required / default / description。

**output_config**：控制节点输出如何落盘。
- `base_dir`：根目录，支持 `{project_dir}` 模板
- `fallback_dir`：未指定 project_dir 时的兜底目录
- `file_map`：key 为节点 id，value 定义 output_keys + file 路径

**nodes 数组**：每个元素引用一个 node JSON，声明 id / ref / inputs / outputs / depends_on。

**schedule**：调度策略。
- `mode`：linear（默认） / dag / parallel
  - `linear`：单节点顺序执行，兼容旧行为
  - `dag` / `parallel`：按「就绪波次」并发调度——同一波次内所有前置依赖已完成的节点并发执行，全部完成后 join，再计算下一波次。适合互不依赖的分支并行（如多个方向的素材检索/多个模块同时生成）
- `max_concurrency`：并行最大并发度（0 = 等于当前波次大小），可被 `auto --workers N` 覆盖
- `revise_loop`：启用则形成 trigger_node → loop_back_to 循环
- `max_iterations`：全局迭代上限

### 第2步：写 node JSON

每个节点单独一个文件，放在 `.opencode/workflow/nodes/` 下，文件名随意但建议用节点 id。

**必填字段**：

| 字段 | 说明 |
|------|------|
| `id` | 节点 ID，须与 workflow 中一致 |
| `name` | 中文展示名 |
| `agent` | 调用哪个 agent（novelist / chapter-finalizer / ...） |
| `inputs` | 对象，每个 key 为输入字段名，声明 type / required |
| `outputs` | 对象，每个 key 为输出字段名，声明 type |
| `prompt_template` | 发给 agent 的提示词，`{var}` 会被 state 值替换 |

**output_file**（可选）：控制该节点输出落盘。

```json
"output_file": {
  "file": "正文/{volume}/第{chapter_num}章-{chapter_title}.md",
  "output_keys": ["final_content"],
  "append": false,
  "overwrite": false,
  "format": "plain"
}
```

`file` 为 null 表示不落盘。支持的模板变量来自 state.data。

### 第3步：注册到 opencode

在 `opencode.json` 中不需要额外注册——引擎自动扫描 `.opencode/workflow/*.json`。

但建议在 `.opencode/command/` 下创建一个触发命令，方便一键运行。

## 设计规则

### 依赖方向

节点依赖必须是 DAG（有向无环图），`depends_on` 不能形成环。拓扑排序决定执行顺序。

### 输入输出对接

节点 A 输出 `x`，节点 B 要读 `x`，则 B 的 `inputs` 必须包含 `x`，且 A 的 `outputs` 必须包含 `x`，并且 A 必须在 B 的 `depends_on` 路径上。

### 循环（revise_loop）

只支持单触发节点 → 单回跳节点的简单循环。触发条件由 exit_condition 描述（通常是"某字段为空"）。最大循环次数由 `max_loops` 限定。

### 输出文件路径

路径模板变量来自 `state.data`，引擎在 `complete` 命令时自动替换并写入文件。

常用变量：
- `{project_dir}` — 小说项目目录
- `{chapter_num}` — 章节编号
- `{chapter_title}` — 章节标题
- `{volume}` — 所属卷
- `{node_id}` — 当前节点 id

## Session 与断点续跑

引擎为每次执行分配唯一 `session_id`，每个节点独立跟踪状态：

```
pending → running → completed / failed
```

**每次操作都立即写盘**（checkpoint），agent 中断不会丢失已完成进度。

### State 文件结构

```json
{
  "session": {
    "id": "20260916-223522-3223a7",
    "workflow": "chapter-pipeline",
    "status": "running",
    "created_at": "...",
    "updated_at": "..."
  },
  "pipeline": {
    "interval": ["research", "outline", ...],
    "iteration": 0,
    "max_iterations": 3
  },
  "node_tasks": {
    "research": { "status": "completed", "agent": "novelist", "output_file": null },
    "outline":  { "status": "running",   "agent": "novelist", "output_file": "章节大纲/逐章卡片.md" },
    "draft":    { "status": "pending",   "agent": null, "output_file": null }
  },
  "data": { "task": "...", "research_notes": "..." },
  "log": [ { "time": "...", "node": "research", "status": "completed" } ]
}
```

### 恢复流程

```bash
# 查看下一个待执行节点
python3 .opencode/workflow/workflow_engine.py next <wf.json> --state <state.json>

# 自动恢复（从上次中断处继续）
python3 .opencode/workflow/workflow_engine.py resume <wf.json> --state <state.json>
```

State 文件固定在：`.opencode/workflow/output/{workflow名}-state.json`

### Engine 命令速查

| 命令 | 用途 |
|------|------|
| `init` | 新建 session，初始化 state |
| `plan` | 打印执行计划（只读） |
| `run` | 标记节点 running（触发输入校验） |
| `complete` | 标记完成，写 output 文件，返回下一步动作 |
| `fail` | 标记失败，记录 error |
| `resume` | 从上次中断处恢复 |
| `next` | 查询下一个 pending 节点（只读） |
| `ready` | 查询当前全部就绪节点（DAG 波次，只读） |
| `auto` | 引擎全自动调度（`mode=dag/parallel` 时并发执行就绪波次 + join） |
| `status` | 打印当前 session 摘要 |
| `sessions` | 列出目录下所有 session |
| `validate` | 校验 workflow 结构 |

> `auto` 是引擎亲自接管的调度入口：代码决定波次、并发、join、重试与 revise_loop，
> LLM 只在 agent 节点被调用，退化为内容生成器。`mode=linear` 时退化为单节点顺序执行。

## 参考文件

- Schema：`workflow.schema.json`、`node.schema.json`
- 示例 workflow：`chapter-pipeline.json`
- 示例节点：`nodes/*.json`
- 引擎源码：`workflow_engine.py`
