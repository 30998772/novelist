# Spec Delta

## Purpose

定义自研 workflow_engine 的工作流调度行为：在 linear / dag / parallel 三种模式下如何决定节点执行顺序、并发与合并，以及 `auto`、`ready` 两个 CLI 子命令的外部契约。

## ADDED Requirements

### Requirement: 就绪波次计算
引擎 SHALL 依据节点 `depends_on` 计算「就绪节点」集合：仅当某节点的全部前置依赖均已 `completed` 时，该节点才算就绪；`linear` 模式下就绪集合仍按拓扑顺序返回。

#### Scenario: 依赖未完成时不就绪
- **WHEN** 节点 B 依赖节点 A，且 A 仍为 `pending`
- **THEN** B 不出现在就绪集合中

#### Scenario: 依赖完成后就绪
- **WHEN** 节点 A 变为 `completed`，且 B、C 都只依赖 A
- **THEN** 就绪集合同时包含 B 和 C

### Requirement: 并行波次执行与 join
当 `schedule.mode` 为 `dag` 或 `parallel` 时，引擎 SHALL 并发执行同一就绪波次内的全部节点，并在该波次全部结束后 join，将各节点输出统一合并回 state 后再计算下一波次。

#### Scenario: 同波次节点并发
- **WHEN** 就绪波次包含 4 个互不依赖的节点，且每个节点执行耗时约 1 秒
- **THEN** 该波次的 wall time 约为 1 秒而非 4 秒

#### Scenario: 波次末统一合并
- **WHEN** 同一波次的节点全部成功返回
- **THEN** 所有输出在一次 join 中写入 state，且记入同一条波次完成日志

### Requirement: 线性模式兼容
当 `schedule.mode` 为 `linear`（默认或缺省）时，引擎 SHALL 每轮只执行一个就绪节点，保持既有串行语义。

#### Scenario: 线性模式串行执行
- **WHEN** 工作流声明 `mode=linear`，且存在 6 个顺序节点
- **THEN** 节点按拓扑顺序逐个执行，互不并发

### Requirement: 并发度控制
引擎 SHALL 支持通过 `schedule.max_concurrency` 限制并行波次的最大并发度；`auto` 命令的 `--workers N` SHALL 覆盖该配置；取值 0 表示并发度等于当前波次大小。

#### Scenario: 命令行覆盖并发度
- **WHEN** 波次包含 4 个就绪节点，且以 `auto --workers 2` 调用
- **THEN** 同一时刻最多有 2 个节点在执行

### Requirement: 自动调度命令契约
`auto` 命令 SHALL 作为引擎接管的端到端调度入口，输出以每行一个 JSON 事件表示调度进度，事件动作至少包含 `wave`、`joined`，并在会话结束时输出 `done` 或 `failed`。

#### Scenario: 完成事件
- **WHEN** 所有节点成功完成
- **THEN** `auto` 输出 `{"action":"done", ...}` 且会话状态置为 `completed`

#### Scenario: 失败事件
- **WHEN** 某一节点执行失败且不存在可回退的重试目标
- **THEN** `auto` 输出 `{"action":"failed", ...}` 且会话状态置为 `failed`

### Requirement: 就绪波次查询命令
`ready` 命令 SHALL 以只读方式输出当前全部就绪节点、所属模式与是否为并行模式，且不得修改 state 文件。

#### Scenario: 只读查询
- **WHEN** 对一个 `mode=dag` 的会话执行 `ready`
- **THEN** 返回包含 `ready` 数组与 `parallel: true` 的 JSON，且 state 文件内容不变
