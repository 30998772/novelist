# Design

## Context

`workflow_engine.py` 既有 `get_stage_order()`（Kahn 拓扑排序 + 环检测）与 `find_next()`（返回首个就绪节点）。`cmd_auto` 以单节点轮询方式推进：每轮取一个节点、调用 agent、写盘、再判定 revise_loop。节点执行与 state 合并耦合在同一个循环里，无法安全并发。参见 `proposal.md` 的 Why。

## Goals / Non-Goals

**Goals:**
- 在不动 `next` / `run` / `resume` 等既有命令行为的前提下，让 `auto` 支持波次并发
- 并发执行期间避免多线程写 state 的竞争
- 保留失败重试与 revise_loop 回退语义

**Non-Goals:**
- 不引入外部 DAG 库（保持纯标准库）
- 不改变子进程 / agent 调用协议
- 不实现跨进程分布式调度

## Decisions

- **就绪波次而非逐节点**：抽出 `get_ready_nodes()` 返回整波就绪节点，`find_next()` 退化为 `get_ready_nodes()[0]`，兼顾兼容与复用。
- **节点执行无副作用**：`_run_node_once(node_def, state)` 只读取 state，返回 `(outputs, error)`，绝不写 state。并发调用安全。
- **主线程统一 join**：波次内节点在 `ThreadPoolExecutor` 中并发执行，结果经 `as_completed` 收集后，由主线程串行执行写盘与 `state["data"].update()`，消除写竞争。输入快照用 `_deep_copy` 隔离。
- **模式退化**：`linear` 时 `wave = ready[:1]`，代码路径完全一致，避免双份逻辑。
- **并发度**：`schedule.max_concurrency` 作默认值，`auto --workers` 覆盖，`len(wave)` 兜底。
- **失败语义**：code 节点按 `on_fail` 回退并 `_reset_for_loop` 重置目标节点；agent 节点无回退目标则整会话失败。

**备选方案**：进程池（multiprocessing）——因 state 与内置函数闭包难以序列化而放弃；asyncio——需将 `_call_agent` 改为异步且侵入既有同步代码，收益不抵成本。

## Risks / Trade-offs

- [agent 调用可能非线程安全（共享子进程/环境）] → 波次默认并发度可控，并提供 `--workers 1` 退化开关
- [同一波次内两个节点写同一输出键] → join 按波次顺序串行合并，后写覆盖，行为确定
- [异常在子线程被吞] → `_run_node_once` 捕获全部异常并转为 `(None, error)` 返回

## Migration Plan

1. 引擎与 schema 更新（本变更）
2. 既有 `chapter-pipeline.json` 保持 `mode=linear`，无需迁移，行为不变
3. 需要提速的工作流显式改为 `mode=dag/parallel` 并配置 `max_concurrency`
4. 回滚：将相关工作流改回 `mode=linear` 即恢复旧行为
