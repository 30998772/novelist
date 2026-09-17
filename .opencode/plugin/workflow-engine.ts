/**
 * Workflow Engine Plugin — 工作流调度引擎插件
 *
 * 为 opencode 提供工作流管理能力：
 * - config hook: 验证工作流文件完整性
 * - tool definitions: workflow_validate / workflow_plan / workflow_status
 * - tool.execute.before: 工作流命令拦截与上下文注入
 */

import type { Plugin } from "@opencode-ai/plugin"
import { readFileSync, existsSync, readdirSync } from "node:fs"
import { join, resolve } from "node:path"

interface WorkflowNode {
  id: string
  ref: string
  inputs: string[]
  outputs: string[]
  depends_on: string[]
}

interface WorkflowDef {
  name: string
  nodes: WorkflowNode[]
  schedule: {
    mode: string
    max_iterations: number
    revise_loop?: {
      enabled: boolean
      trigger_node: string
      loop_back_to: string
      max_loops: number
      exit_condition: string
    }
  }
}

interface NodeDef {
  id: string
  name: string
  agent: string
  prompt_template: string
  inputs: Record<string, { type: string; required: boolean }>
  outputs: Record<string, { type: string }>
}

function getWorkflowDir(projectDir: string): string {
  return join(projectDir, ".opencode", "workflow")
}

function loadJson(filePath: string): any {
  if (!existsSync(filePath)) return null
  return JSON.parse(readFileSync(filePath, "utf-8"))
}

function listWorkflows(projectDir: string): string[] {
  const dir = getWorkflowDir(projectDir)
  if (!existsSync(dir)) return []
  return readdirSync(dir)
    .filter((f) => f.endsWith(".json") && !f.startsWith("_"))
    .map((f) => f.replace(".json", ""))
}

function loadWorkflowDef(projectDir: string, name: string): WorkflowDef | null {
  const dir = getWorkflowDir(projectDir)
  const filePath = join(dir, `${name}.json`)
  return loadJson(filePath)
}

function loadNodeDef(projectDir: string, ref: string): NodeDef | null {
  const dir = getWorkflowDir(projectDir)
  const filePath = join(dir, ref)
  return loadJson(filePath)
}

function validateWorkflow(projectDir: string, name: string): string[] {
  const errors: string[] = []
  const wf = loadWorkflowDef(projectDir, name)
  if (!wf) {
    errors.push(`Workflow "${name}" not found`)
    return errors
  }

  const nodeIds = new Set(wf.nodes.map((n) => n.id))

  for (const node of wf.nodes) {
    const nodeDef = loadNodeDef(projectDir, node.ref)
    if (!nodeDef) {
      errors.push(`Node "${node.id}": ref "${node.ref}" not found`)
    }

    for (const dep of node.depends_on) {
      if (!nodeIds.has(dep)) {
        errors.push(`Node "${node.id}": depends_on unknown "${dep}"`)
      }
    }
  }

  // Check for cycles (simple DFS)
  const visited = new Set<string>()
  const stack = new Set<string>()
  function dfs(id: string): boolean {
    if (stack.has(id)) return true
    if (visited.has(id)) return false
    visited.add(id)
    stack.add(id)
    const node = wf.nodes.find((n) => n.id === id)
    if (node) {
      for (const dep of node.depends_on) {
        if (dfs(dep)) return true
      }
    }
    stack.delete(id)
    return false
  }

  for (const node of wf.nodes) {
    if (dfs(node.id)) {
      errors.push(`Circular dependency detected involving "${node.id}"`)
      break
    }
  }

  return errors
}

function buildExecutionOrder(wf: WorkflowDef): string[] {
  const inDegree: Record<string, number> = {}
  const adj: Record<string, string[]> = {}

  for (const node of wf.nodes) {
    inDegree[node.id] = 0
    adj[node.id] = []
  }

  for (const node of wf.nodes) {
    for (const dep of node.depends_on) {
      adj[dep]?.push(node.id)
      inDegree[node.id]++
    }
  }

  const queue = Object.keys(inDegree).filter((k) => inDegree[k] === 0)
  const order: string[] = []

  while (queue.length > 0) {
    const current = queue.shift()!
    order.push(current)
    for (const neighbor of adj[current]) {
      inDegree[neighbor]--
      if (inDegree[neighbor] === 0) {
        queue.push(neighbor)
      }
    }
  }

  return order
}

const plugin: Plugin = async ({ project, directory }) => {
  const projectDir = project?.path ?? directory ?? process.cwd()

  return {
    config: (cfg) => {
      // Validate all workflows on startup
      const wfDir = getWorkflowDir(projectDir)
      if (!existsSync(wfDir)) return cfg

      const workflows = listWorkflows(projectDir)
      for (const name of workflows) {
        const errors = validateWorkflow(projectDir, name)
        if (errors.length > 0) {
          console.warn(
            `[workflow-engine] Warning: workflow "${name}" has ${errors.length} issue(s):`,
            errors
          )
        }
      }

      return cfg
    },

    "tool.execute.before": async (input, output) => {
      const toolName = input?.tool?.name
      if (!toolName) return

      // Intercept bash commands that run the workflow engine
      if (toolName === "bash") {
        const cmd = (input?.args?.command as string) || ""
        if (cmd.includes("workflow_engine.py")) {
          // Let it through — the engine is invoked via bash
          return
        }
      }

      // Intercept task tool to inject workflow context
      if (toolName === "task") {
        const prompt = (input?.args?.prompt as string) || ""
        if (prompt.includes("workflow") || prompt.includes("工作流")) {
          // Could inject workflow state context here if needed
          return
        }
      }
    },

    tool: {
      workflow_validate: {
        description:
          "验证工作流定义文件的结构完整性，检查节点引用、依赖关系和循环",
        parameters: {
          type: "object",
          properties: {
            name: {
              type: "string",
              description: "工作流名称（不含 .json 后缀）",
            },
          },
          required: ["name"],
        },
        execute: async (args: { name: string }) => {
          const errors = validateWorkflow(projectDir, args.name)
          if (errors.length === 0) {
            const wf = loadWorkflowDef(projectDir, args.name)
            const order = buildExecutionOrder(wf!)
            return {
              valid: true,
              workflow: args.name,
              node_count: wf!.nodes.length,
              execution_order: order,
            }
          }
          return { valid: false, workflow: args.name, errors }
        },
      },

      workflow_list: {
        description: "列出所有可用的工作流定义",
        parameters: { type: "object", properties: {} },
        execute: async () => {
          const names = listWorkflows(projectDir)
          const result = names.map((name) => {
            const wf = loadWorkflowDef(projectDir, name)
            return {
              name,
              description: wf?.description || "",
              node_count: wf?.nodes?.length || 0,
            }
          })
          return { workflows: result }
        },
      },

      workflow_plan: {
        description:
          "生成工作流执行计划，返回有序节点列表及每个节点的输入输出",
        parameters: {
          type: "object",
          properties: {
            name: {
              type: "string",
              description: "工作流名称",
            },
            start: {
              type: "string",
              description: "起始阶段（可选，默认从头开始）",
            },
            end: {
              type: "string",
              description: "结束阶段（可选，默认到末尾）",
            },
          },
          required: ["name"],
        },
        execute: async (args: {
          name: string
          start?: string
          end?: string
        }) => {
          const wf = loadWorkflowDef(projectDir, args.name)
          if (!wf) return { error: `Workflow "${args.name}" not found` }

          const fullOrder = buildExecutionOrder(wf)
          let startIdx = 0
          let endIdx = fullOrder.length - 1

          if (args.start) {
            startIdx = fullOrder.indexOf(args.start)
            if (startIdx === -1)
              return { error: `Unknown start stage: ${args.start}` }
          }
          if (args.end) {
            endIdx = fullOrder.indexOf(args.end)
            if (endIdx === -1)
              return { error: `Unknown end stage: ${args.end}` }
          }

          const interval = fullOrder.slice(startIdx, endIdx + 1)
          const nodesById = Object.fromEntries(
            wf.nodes.map((n) => [n.id, n])
          )

          const plan = interval.map((id, i) => {
            const node = nodesById[id]
            const nodeDef = loadNodeDef(projectDir, node.ref)
            return {
              step: i + 1,
              id,
              name: nodeDef?.name || id,
              agent: nodeDef?.agent || "novelist",
              inputs: node.inputs,
              outputs: node.outputs,
              depends_on: node.depends_on,
            }
          })

          return {
            workflow: args.name,
            interval: `${interval[0]} → ${interval[interval.length - 1]}`,
            steps: plan,
          }
        },
      },

      workflow_status: {
        description: "查看工作流执行状态（读取 state JSON 文件）",
        parameters: {
          type: "object",
          properties: {
            state_file: {
              type: "string",
              description: "状态文件路径",
            },
          },
          required: ["state_file"],
        },
        execute: async (args: { state_file: string }) => {
          const state = loadJson(args.state_file)
          if (!state) return { error: "State file not found" }
          return {
            workflow: state.workflow,
            status: state.status,
            current_node: state.current_node,
            completed: state.completed_nodes,
            iteration: state.iteration,
            data_keys: Object.keys(state.data || {}),
          }
        },
      },
    },
  }
}

export default plugin
