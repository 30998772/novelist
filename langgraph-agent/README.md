# LangGraph Novelist Agent

基于 LangGraph 的小说创作外部 Agent 服务，通过 MCP 协议与 opencode 集成。

## 架构

```
opencode (novelist agent)
    │
    │ MCP 工具调用
    ▼
┌─────────────────────────┐
│  LangGraph MCP Server   │
│                         │
│  ┌───────┐   ┌───────┐ │
│  │ router│──▶│research│ │
│  └───────┘   └───┬───┘ │
│       │          │     │
│       ▼          ▼     │
│  ┌───────┐   ┌───────┐ │
│  │ draft │──▶│ review │ │
│  └───┬───┘   └───┬───┘ │
│      │           │     │
│      ▼           ▼     │
│  ┌───────────────────┐ │
│  │     finalize      │ │
│  └───────────────────┘ │
└─────────────────────────┘
```

## 状态流转

```
router → research → draft → review → finalize
              ↑___________↓ (迭代修改)
```

## 安装

```bash
pip install -r requirements.txt
```

## 配置到 opencode

在项目 `.opencode/opencode.json` 或全局 `~/.config/opencode/opencode.json` 中添加：

```json
{
  "mcp": {
    "novelist-agent": {
      "type": "local",
      "command": ["python", "/mnt/d/devProject/writer/langgraph-agent/agent.py"],
      "enabled": true
    }
  }
}
```

重启 opencode 后生效。

## 暴露的 MCP 工具

| 工具 | 说明 |
|------|------|
| `write_chapter` | 根据大纲卡片撰写章节 |
| `review_chapter` | 审稿检查（人设/伏笔/文风/AI痕迹） |
| `revise_chapter` | 根据审稿意见修改章节 |

## 后续扩展

- 接入真实 LLM（`langchain_openai` / `langchain_anthropic`）
- 添加持久化状态（`langgraph.checkpoint.sqlite`）
- 增加更多节点：伏笔追踪、世界观一致性检查
- 添加中断/人类审批节点（`interrupt_before`）
