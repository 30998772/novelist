---
description: 运行工作流。按 JSON 定义的节点顺序执行完整流水线，支持断点续跑。Use `$ARGUMENTS` as workflow name (e.g. `chapter-pipeline`).
agent: workflow-executor
---

你是工作流调度引擎的执行者。用户要运行的工作流: **$ARGUMENTS**

## 核心规则

1. **每次 `run`/`complete` 都会实时写盘**，中途断掉不会丢失已完成进度
2. **用 `resume` 恢复**，引擎自动找到下一个未完成节点继续
3. **不要跳步、不要合并步骤**，严格按引擎输出执行

---

## 第0步：检查是否有未完成的 session

先检查是否有上次中断的 session 可以恢复：

```bash
python3 .opencode/workflow/workflow_engine.py next \
  .opencode/workflow/$ARGUMENTS.json \
  --state .opencode/workflow/output/$ARGUMENTS-state.json
```

如果输出中 `session_status` 为 `"running"` 且 `next` 不为 null，**直接跳到第3步恢复执行**。

如果文件不存在或 session 已 `completed`，从第1步开始新流程。

---

## 第1步：验证工作流

```bash
python3 .opencode/workflow/workflow_engine.py validate .opencode/workflow/$ARGUMENTS.json
```

失败则停止并报告。成功则继续。

---

## 第2步：初始化新 session

创建输入文件 `.opencode/workflow/output/$ARGUMENTS-input.json`：

```json
{
  "task": "用户任务描述",
  "project_dir": "小说项目目录（如 裂缝余痕/）",
  "chapter_num": "031",
  "chapter_title": "章节标题",
  "volume": "第一部",
  "target_word_count": 3500
}
```

根据用户实际提供的参数填写，缺失的字段省略（引擎会用默认值）。

执行初始化：

```bash
mkdir -p .opencode/workflow/output
python3 .opencode/workflow/workflow_engine.py init \
  .opencode/workflow/$ARGUMENTS.json \
  --state .opencode/workflow/output/$ARGUMENTS-state.json \
  --input .opencode/workflow/output/$ARGUMENTS-input.json
```

记下输出中的 `session_id`。

---

## 第3步：逐节点执行（核心循环）

使用引擎的 `next` 命令获取下一个节点：

```bash
python3 .opencode/workflow/workflow_engine.py next \
  .opencode/workflow/$ARGUMENTS.json \
  --state .opencode/workflow/output/$ARGUMENTS-state.json
```

输出中 `next` 字段即为要执行的节点 ID。若为 null 说明全部完成，跳到第4步。

### 3a. 启动节点（标记 running）

```bash
python3 .opencode/workflow/workflow_engine.py run \
  .opencode/workflow/$ARGUMENTS.json \
  --state .opencode/workflow/output/$ARGUMENTS-state.json \
  --node <NEXT_NODE_ID>
```

输出包含：
- `inputs` — 引擎从 state 中取出的该节点输入数据（引擎只做数据路由，不做 prompt 渲染）
- `agent` — 应使用哪个 agent 执行
- `outputs` — 该节点必须返回的字段名
- `output_file` — 输出文件路径（可选，用于汇报）
- `session_id` — 会话 ID

**如果输出中 `skip: true`**，说明该节点已完成，直接回到第3步取下一个。

### 3b. 派发子 agent 执行

**关键：prompt 由 agent 自行处理，引擎只交接数据。** 把 `inputs` 原样交给对应 agent，让它自己决定怎么写。

```bash
# 动笔前先读取历史错误禁令（mistake memory）
python3 .opencode/workflow/workflow_engine.py mistakes inject
```

用 `task` 工具派发，agent 选择：

| agent | 用途 |
|-------|------|
| `novelist` | 调研 / 大纲 / 写稿 / 修改 / 定稿 |
| `chapter-finalizer` | 审稿 |

task 的 prompt 这样组织：
1. 注入 `mistakes inject` 输出的禁令块
2. 给出该节点的 `inputs` 数据
3. 明确要求返回什么：引擎 `outputs` 里声明的字段
4. 其余写作规则让 agent 自己按规范执行（novelist/chapter-finalizer 的 agent 系统提示词已包含）

将子 agent 返回的内容组装为该节点的 outputs。

### 3c. 标记完成（立即写盘）

将子 agent 输出组装为 JSON，然后调用 complete：

```bash
python3 .opencode/workflow/workflow_engine.py complete \
  .opencode/workflow/$ARGUMENTS.json \
  --state .opencode/workflow/output/$ARGUMENTS-state.json \
  --node <NODE_ID> \
  --outputs '<JSON>'
```

**各节点输出格式：**

| 节点 | outputs JSON |
|------|-------------|
| research | `{"research_notes": "纪要内容"}` |
| outline | `{"outline": "大纲内容"}` |
| draft | `{"draft_content": "正文草稿"}` |
| review | `{"review_notes": ["意见1", "意见2"]}` |
| revise | `{"draft_content": "修改后的正文"}` |
| finalize | `{"final_content": "最终正文"}` |

**complete 的输出：**
- `{"action":"continue","next":"xxx"}` → 回到第3步执行下一个节点
- `{"action":"loop","target":"revise"}` → 回到第3步，用 target 节点 ID 执行
- `{"action":"done"}` → 全部完成

### 3d. 标记失败（如果子 agent 报错）

```bash
python3 .opencode/workflow/workflow_engine.py fail \
  .opencode/workflow/$ARGUMENTS.json \
  --state .opencode/workflow/output/$ARGUMENTS-state.json \
  --node <NODE_ID> \
  --error '错误描述'
```

下次 `resume` 时会跳过已失败节点。

---

## 第4步：汇报结果

```bash
python3 .opencode/workflow/workflow_engine.py status \
  .opencode/workflow/output/$ARGUMENTS-state.json
```

向用户汇报：
1. session_id 和总进度（各节点 completed/failed 状态）
2. 每个节点的输出文件路径（如果有）
3. 最终定稿内容（从 `data.final_content` 读取）
4. 如有遗留 C 级意见，列出供用户决策

---

## 中断恢复流程

如果执行过程中你被中断（agent 断连、用户暂停等），恢复时：

1. **不需要重新 init**，状态已保存在 `output/$ARGUMENTS-state.json`
2. 直接从第0步开始，引擎会检测到未完成的 session
3. 用 `resume` 或 `next` 获取下一个节点，从第3步继续

```bash
# 恢复示例
python3 .opencode/workflow/workflow_engine.py resume \
  .opencode/workflow/chapter-pipeline.json \
  --state .opencode/workflow/output/chapter-pipeline-state.json
```

---

## 区间执行

用户可指定只执行部分阶段：

```
/run-workflow chapter-pipeline --start draft --end revise
```

引擎会自动缩小区间，只标记区间内的节点为 pending。

---

## 注意事项

- 每个子 agent 执行时，确保它遵循对应 agent 的写作规范和字数要求
- 审稿节点输出必须是严格的 JSON 数组格式
- 修改节点必须保留原有剧情骨架，只针对审稿意见做具体修改
- 最终定稿输出纯正文，不要标题和注释
- **state 文件路径固定**：`.opencode/workflow/output/{workflow名}-state.json`
