# Tasks

## 1. 就绪波次计算

- [x] 1.1 新增 `get_ready_nodes(wf, state)`，返回全部依赖已完成的 pending 节点（linear 下保持拓扑序）；用 `python3 -c` 构造菱形依赖验证返回值
- [x] 1.2 将 `find_next()` 重构为 `get_ready_nodes()[0]`，运行 `next` 子命令确认行为不变

## 2. 无副作用节点执行

- [x] 2.1 抽出 `_run_node_once(node_def, state) -> (outputs, error)`，捕获全部异常；对 agent 与 code 两类节点分别验证返回结构
- [x] 2.2 新增 `_reset_for_loop(state, nid)` 供 revise_loop 与失败回退重置节点状态为 pending

## 3. 并行波次调度

- [x] 3.1 重写 `cmd_auto`：按波次取就绪节点，`mode=dag/parallel` 时用 `ThreadPoolExecutor` 并发、`as_completed` join
- [x] 3.2 join 逻辑由主线程串行合并输出与写盘，验证同一波次输出无丢失
- [x] 3.3 `mode=linear` 退化为 `wave = ready[:1]`，验证 6 节点工作流耗时约等于串行
- [x] 3.4 失败处理：code 节点按 `on_fail` 回退重试并重置目标节点，无可回退目标则整会话 `failed`

## 4. 配置与 CLI

- [x] 4.1 `workflow.schema.json` 的 `schedule` 增加 `max_concurrency`（整数，默认 0）
- [x] 4.2 `auto` 读取 `max_concurrency` 并支持 `--workers N` 覆盖，验证并发度受限
- [x] 4.3 新增只读 `ready` 子命令，输出就绪波次与模式；验证执行后 state 文件不变

## 5. 验证

- [x] 5.1 菱形工作流（A → B,C,D,E → F）在 `mode=dag` 下 wall time 约 3s（对比串行约 6s），输出全部合并
- [x] 5.2 `python3 -m py_compile workflow_engine.py` 通过
- [x] 5.3 对既有 `chapter-pipeline.json` 运行 `validate`，8 节点仍 OK（linear 兼容）
- [x] 5.4 更新 `skills/workflow-writer/SKILL.md`，补充 dag/parallel 波次语义、`max_concurrency` 与 `auto`/`ready` 命令

## 6. 归档

- [x] 6.1 运行 `openspec validate` 与 `openspec archive`，确认变更归档后主 spec 生成于 `openspec/specs/workflow-scheduling/`
