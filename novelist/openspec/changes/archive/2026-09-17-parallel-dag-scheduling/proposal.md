# Proposal

## Why

自研 `workflow_engine` 目前只能按线性顺序逐节点执行。`schedule.mode` 虽声明支持 `dag` / `parallel`，但引擎没有实现对应调度：所有节点都被串行执行，互不依赖的节点（如多方向素材检索、多模块并行生成）白白浪费 wall time。

## What Changes

- 新增「就绪波次」（ready wave）计算：每轮返回所有前置依赖已完成的 pending 节点
- `mode=dag` / `mode=parallel` 时并发执行同一波次内节点，波次末 join 后统一合并输出到 state
- 新增 `auto` 子命令（引擎接管的端到端调度入口）与 `ready` 子命令（只读查询当前就绪波次）
- 新增 `schedule.max_concurrency` 配置项，可被 `auto --workers N` 覆盖
- **BREAKING**：`auto` 由「单节点轮询」改为「波次并发」，事件输出新增 `wave` / `joined` 动作

## Capabilities

### New Capabilities

- `workflow-scheduling`: 工作流调度引擎的 linear / dag / parallel 调度行为，以及 `auto`、`ready` CLI 契约

### Modified Capabilities

（无）

## Impact

- 代码：`workflow_engine.py`（新增 `get_ready_nodes`、`_run_node_once`、`cmd_auto`、`cmd_ready`）
- 配置：`workflow.schema.json` 的 `schedule` 增加 `max_concurrency`
- 兼容性：`mode=linear` 保持串行语义，`next` / `run` / `resume` / `complete` / `fail` 行为不变
