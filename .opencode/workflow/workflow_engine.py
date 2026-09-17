#!/usr/bin/env python3
"""Workflow Scheduling Engine v3 — 纯数据路由引擎

职责：
  - 解析 workflow DAG，决定执行顺序
  - 校验节点输入输出的类型和完整性
  - 管理 session / checkpoint / resume
  - 将节点输出写入文件
  - 不做 prompt 渲染，不做任何业务决策

用法:
    python3 workflow_engine.py init      <wf.json> --state <s.json> --input <i.json>
    python3 workflow_engine.py plan      <wf.json> [--start S] [--end E]
    python3 workflow_engine.py run       <wf.json> --state <s.json> --node <id>
    python3 workflow_engine.py complete  <wf.json> --state <s.json> --node <id> --outputs '<json>'
    python3 workflow_engine.py fail      <wf.json> --state <s.json> --node <id> --error 'msg'
    python3 workflow_engine.py resume    <wf.json> --state <s.json>
    python3 workflow_engine.py next      <wf.json> --state <s.json>
    python3 workflow_engine.py status    <state.json>
    python3 workflow_engine.py validate  <wf.json>
"""

import json
import sys
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

WORKFLOW_DIR = Path(__file__).parent


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Loading ──────────────────────────────────────────────────────────────

def load_workflow(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Workflow not found: {path}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def load_node(ref: str) -> dict:
    if os.path.isabs(ref):
        p = Path(ref)
    else:
        p = WORKFLOW_DIR / ref
    if not p.exists():
        raise FileNotFoundError(f"Node not found: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def get_nodes(wf: dict) -> dict:
    """返回 {node_id: node_def}。兼容两种结构：
    - 2.0: nodes 是 dict {id: def}（内联）
    - 1.x: nodes 是 list（每个含 id/ref，指向外部文件）
    """
    nodes = wf.get("nodes", {})
    if isinstance(nodes, dict):
        return {k: dict(v, id=k) for k, v in nodes.items()}
    result = {}
    for n in nodes:
        nd = load_node(n["ref"]) if isinstance(n.get("ref"), str) else dict(n)
        nd = dict(nd, id=n["id"])
        result[n["id"]] = nd
    return result


def _save(state: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ─── DAG 排序 ─────────────────────────────────────────────────────────────

def get_stage_order(wf: dict) -> list[str]:
    nodes = get_nodes(wf)
    ids = list(nodes.keys())
    indeg = {i: 0 for i in ids}
    adj = {i: [] for i in ids}
    for i, n in nodes.items():
        for d in n.get("depends_on", []):
            adj[d].append(i)
            indeg[i] += 1
    q = [i for i in ids if indeg[i] == 0]
    order = []
    while q:
        c = q.pop(0)
        order.append(c)
        for nb in adj[c]:
            indeg[nb] -= 1
            if indeg[nb] == 0:
                q.append(nb)
    if len(order) != len(ids):
        raise ValueError("Circular dependency detected")
    return order


def get_interval(order: list[str], start: str, end: str) -> list[str]:
    if start not in order or end not in order:
        raise ValueError(f"Unknown stage: {start} or {end}")
    si, ei = order.index(start), order.index(end)
    if si > ei:
        raise ValueError(f"start '{start}' is after end '{end}'")
    return order[si: ei + 1]


# ─── Execution Plan ───────────────────────────────────────────────────────

def build_plan(wf: dict, start=None, end=None) -> list[dict]:
    order = get_stage_order(wf)
    s = start or wf.get("input", {}).get("start_stage", {}).get("default", order[0])
    e = end or wf.get("input", {}).get("end_stage", {}).get("default", order[-1])
    interval = get_interval(order, s, e)
    nodes = get_nodes(wf)
    plan = []
    for sid in interval:
        nd = nodes[sid]
        plan.append({
            "step": len(plan) + 1,
            "id": sid,
            "name": nd.get("name", sid),
            "agent": nd.get("agent"),
            "type": nd.get("type", "agent"),
            "inputs": list(nd.get("inputs", {}).keys()),
            "outputs": list(nd.get("outputs", {}).keys()),
            "depends_on": nd.get("depends_on", []),
        })
    return plan


# ─── I/O 校验 ─────────────────────────────────────────────────────────────

_TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "number": lambda v: isinstance(v, (int, float)),
    "boolean": lambda v: isinstance(v, bool),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
}


def validate_inputs(node_def: dict, data: dict) -> list[str]:
    """校验 state.data 是否满足节点输入要求。返回缺失/类型错误列表。"""
    errors = []
    for name, spec in node_def.get("inputs", {}).items():
        if spec.get("required", True) and name not in data:
            errors.append(f"missing required input: {name}")
            continue
        if name in data:
            expected = spec.get("type")
            checker = _TYPE_CHECKS.get(expected)
            if checker and not checker(data[name]):
                errors.append(f"input '{name}' expected {expected}, got {type(data[name]).__name__}")
    return errors


def validate_outputs(node_def: dict, outputs: dict) -> list[str]:
    """校验节点输出是否符合 outputs 定义。"""
    errors = []
    for name, spec in node_def.get("outputs", {}).items():
        if name not in outputs:
            errors.append(f"missing expected output: {name}")
            continue
        expected = spec.get("type")
        checker = _TYPE_CHECKS.get(expected)
        if checker and not checker(outputs[name]):
            errors.append(f"output '{name}' expected {expected}, got {type(outputs[name]).__name__}")
    return errors


# ─── State Management ─────────────────────────────────────────────────────

def init_state(wf: dict, user_input: dict, start=None, end=None) -> dict:
    order = get_stage_order(wf)
    s = start or wf.get("input", {}).get("start_stage", {}).get("default", order[0])
    e = end or wf.get("input", {}).get("end_stage", {}).get("default", order[-1])
    interval = get_interval(order, s, e)
    session_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]

    node_tasks = {}
    for nid in interval:
        node_tasks[nid] = {
            "status": "pending",
            "agent": None,
            "output_file": None,
            "started_at": None,
            "completed_at": None,
            "error": None,
        }

    state = {
        "session": {
            "id": session_id,
            "workflow": wf.get("name", "unnamed"),
            "status": "running",
            "created_at": _now(),
            "updated_at": _now(),
        },
        "pipeline": {
            "start_stage": s,
            "end_stage": e,
            "interval": interval,
            "iteration": 0,
            "max_iterations": wf.get("schedule", {}).get("max_iterations", 3),
        },
        "node_tasks": node_tasks,
        "current_node": None,
        "data": {},
        "log": [],
    }
    state["data"].update(user_input)
    return state


def get_ready_nodes(wf: dict, state: dict) -> list[str]:
    """DAG 就绪波次：返回所有 pending 且前置依赖已全部完成的节点 id。

    保持 pipeline.interval 的拓扑顺序，因此同一波次内多个节点互不依赖，
    可以并发执行；全部完成后（join）再计算下一波次。
    """
    nodes = get_nodes(wf)
    ready = []
    for nid in state["pipeline"]["interval"]:
        task = state["node_tasks"].get(nid)
        if not task or task["status"] != "pending":
            continue
        nd = nodes.get(nid)
        if not nd:
            continue
        deps = nd.get("depends_on", [])
        if all(state["node_tasks"].get(d, {}).get("status") == "completed" for d in deps if d in state["node_tasks"]):
            ready.append(nid)
    return ready


def find_next(wf: dict, state: dict) -> str | None:
    """区间内下一个可执行节点（就绪波次的第一个，兼容旧的单步调度）。"""
    ready = get_ready_nodes(wf, state)
    return ready[0] if ready else None


def resolve_output_file(state: dict, node_def: dict) -> str | None:
    out = node_def.get("output_file")
    if not out or not out.get("file"):
        return None
    result = out["file"]
    for k, v in state.get("data", {}).items():
        if isinstance(v, (str, int, float)):
            result = result.replace("{" + k + "}", str(v))
    result = result.replace("{node_id}", node_def.get("id", ""))
    return result


def write_output_file(state: dict, node_def: dict, outputs: dict) -> str | None:
    out = node_def.get("output_file")
    if not out or not out.get("file"):
        return None
    rel = resolve_output_file(state, node_def)
    if not rel:
        return None

    base = state.get("data", {}).get("project_dir")
    abs_path = Path(base) / rel if base else (WORKFLOW_DIR / "output" / rel)
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    keys = out.get("output_keys", [])
    parts = []
    for key in keys:
        val = outputs.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            fmt = out.get("format", "plain")
            if fmt == "json":
                parts.append(json.dumps(val, ensure_ascii=False, indent=2))
            elif fmt == "markdown_table":
                for i, item in enumerate(val):
                    parts.append(f"| {i+1} | {item} |")
            else:
                parts.extend(f"- {item}" for item in val)
        else:
            parts.append(str(val))

    content = "\n\n".join(parts)
    if out.get("append") and abs_path.exists():
        with open(abs_path, "a", encoding="utf-8") as f:
            f.write("\n\n" + content)
    else:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
    return str(abs_path)


# ─── Revise Loop ──────────────────────────────────────────────────────────

def check_revise_loop(state: dict, wf: dict, just_done: str) -> str | None:
    cfg = wf.get("schedule", {}).get("revise_loop", {})
    if not cfg.get("enabled"):
        return None
    trigger = cfg.get("trigger_node", "review")
    back = cfg.get("loop_back_to", "revise")
    mx = cfg.get("max_loops", 2)

    if just_done == back:
        c = sum(1 for e in state["log"] if e.get("node") == back and e.get("status") == "completed")
        if c >= mx:
            state["log"].append({"time": _now(), "node": back, "status": "loop_exhausted"})
            return None
        return trigger

    if just_done == trigger:
        notes = state.get("data", {}).get("review_notes", [])
        if notes:
            c = sum(1 for e in state["log"] if e.get("node") == back and e.get("status") == "completed")
            if c < mx:
                return back
        return None

    return None


# ─── CLI ──────────────────────────────────────────────────────────────────

def _arg(args, key):
    for i, a in enumerate(args):
        if a == key and i + 1 < len(args):
            return args[i + 1]
    return None


def cmd_init(args):
    wf = load_workflow(args[0])
    sp = _arg(args, "--state")
    ip = _arg(args, "--input")
    if not sp:
        print("Error: --state required", file=sys.stderr); sys.exit(1)
    inp = json.load(open(ip, encoding="utf-8")) if ip else {}
    state = init_state(wf, inp)
    _save(state, sp)
    print(json.dumps({
        "session_id": state["session"]["id"],
        "interval": state["pipeline"]["interval"],
        "node_tasks": {k: v["status"] for k, v in state["node_tasks"].items()},
    }, ensure_ascii=False, indent=2))


def cmd_plan(args):
    wf = load_workflow(args[0])
    plan = build_plan(wf, _arg(args, "--start"), _arg(args, "--end"))
    print(json.dumps(plan, ensure_ascii=False, indent=2))


def cmd_run(args):
    wf = load_workflow(args[0])
    sp, nid = _arg(args, "--state"), _arg(args, "--node")
    if not sp or not nid:
        print("Error: --state --node required", file=sys.stderr); sys.exit(1)

    nodes = get_nodes(wf)
    if nid not in nodes:
        print(json.dumps({"error": f"unknown node: {nid}"})); sys.exit(1)

    with open(sp, encoding="utf-8") as f:
        state = json.load(f)

    task = state["node_tasks"].get(nid, {})
    if task.get("status") == "completed":
        print(json.dumps({"skip": True, "node_id": nid}))
        return

    # 校验依赖是否已完成
    for dep in nodes[nid].get("depends_on", []):
        if state["node_tasks"].get(dep, {}).get("status") != "completed":
            print(json.dumps({"error": f"dependency not satisfied: '{dep}' must complete before '{nid}'", "node_id": nid}))
            sys.exit(1)

    node_def = nodes[nid]
    errs = validate_inputs(node_def, state["data"])
    if errs:
        print(json.dumps({"error": errs, "node_id": nid})); sys.exit(1)

    # mark running
    task["status"] = "running"
    task["agent"] = node_def.get("agent")
    task["started_at"] = _now()
    state["current_node"] = nid
    state["session"]["updated_at"] = _now()
    state["log"].append({"time": _now(), "node": nid, "status": "running"})
    _save(state, sp)

    # 只返回输入数据，不渲染 prompt
    input_data = {k: state["data"][k] for k in node_def.get("inputs", {}) if k in state["data"]}
    print(json.dumps({
        "node_id": nid,
        "name": node_def.get("name", nid),
        "agent": node_def.get("agent"),
        "inputs": input_data,
        "outputs": list(node_def.get("outputs", {}).keys()),
        "output_file": resolve_output_file(state, node_def),
        "session_id": state["session"]["id"],
        "state_file": sp,
    }, ensure_ascii=False, indent=2))


def cmd_complete(args):
    wf = load_workflow(args[0])
    sp = _arg(args, "--state")
    nid = _arg(args, "--node")
    os_str = _arg(args, "--outputs")
    if not sp or not nid:
        print("Error: --state --node required", file=sys.stderr); sys.exit(1)

    with open(sp, encoding="utf-8") as f:
        state = json.load(f)

    outputs = json.loads(os_str) if os_str else {}

    nodes = get_nodes(wf)
    if nid not in nodes:
        print(json.dumps({"error": f"unknown node: {nid}"})); sys.exit(1)

    # 校验依赖是否已完成
    ref = nodes[nid]
    for dep in ref.get("depends_on", []):
        if state["node_tasks"].get(dep, {}).get("status") != "completed":
            print(json.dumps({"error": f"dependency not satisfied: '{dep}' must complete before '{nid}'", "node_id": nid}))
            sys.exit(1)

    node_def = ref

    # 校验输入
    in_errs = validate_inputs(node_def, state["data"])
    if in_errs:
        print(json.dumps({"error": in_errs, "node_id": nid}))
        sys.exit(1)

    # 校验输出
    out_errs = validate_outputs(node_def, outputs)
    if out_errs:
        print(json.dumps({"error": out_errs}))
        sys.exit(1)

    # 写文件
    out_file = write_output_file(state, node_def, outputs)

    # mark completed
    task = state["node_tasks"].get(nid, {})
    task["status"] = "completed"
    task["completed_at"] = _now()
    task["output_file"] = out_file
    state["data"].update(outputs)
    state["current_node"] = None
    state["pipeline"]["iteration"] += 1
    state["session"]["updated_at"] = _now()
    state["log"].append({"time": _now(), "node": nid, "status": "completed", "outputs": list(outputs.keys()), "output_file": out_file})
    _save(state, sp)

    # revise loop
    lt = check_revise_loop(state, wf, nid)
    if lt:
        state["current_node"] = lt
        state["log"].append({"time": _now(), "node": nid, "status": f"loop_to_{lt}"})
        _save(state, sp)
        print(json.dumps({"action": "loop", "target": lt, "session_id": state["session"]["id"]}))
    else:
        nxt = find_next(wf, state)
        if nxt:
            print(json.dumps({"action": "continue", "next": nxt, "session_id": state["session"]["id"]}))
        else:
            state["session"]["status"] = "completed"
            _save(state, sp)
            print(json.dumps({"action": "done", "session_id": state["session"]["id"]}))


def cmd_fail(args):
    sp = _arg(args, "--state")
    nid = _arg(args, "--node")
    err = _arg(args, "--error")
    with open(sp, encoding="utf-8") as f:
        state = json.load(f)
    task = state["node_tasks"].get(nid, {})
    task["status"] = "failed"
    task["error"] = err
    task["completed_at"] = _now()
    state["current_node"] = None
    state["session"]["status"] = "failed"
    state["session"]["updated_at"] = _now()
    state["log"].append({"time": _now(), "node": nid, "status": "failed", "error": err})
    _save(state, sp)
    print(json.dumps({"action": "failed", "node": nid}))


def cmd_resume(args):
    wf = load_workflow(args[0])
    sp = _arg(args, "--state")
    with open(sp, encoding="utf-8") as f:
        state = json.load(f)
    state["session"]["status"] = "running"
    state["session"]["updated_at"] = _now()
    nxt = find_next(wf, state)
    if nxt:
        state["log"].append({"time": _now(), "node": "__resume__", "status": "resumed", "detail": f"→ {nxt}"})
        _save(state, sp)
        print(json.dumps({"action": "resume", "next": nxt,
                           "completed": [k for k, v in state["node_tasks"].items() if v["status"] == "completed"],
                           "session_id": state["session"]["id"]}, ensure_ascii=False, indent=2))
    else:
        state["session"]["status"] = "completed"
        _save(state, sp)
        print(json.dumps({"action": "already_done", "session_id": state["session"]["id"]}))


def cmd_next(args):
    wf = load_workflow(args[0])
    sp = _arg(args, "--state")
    with open(sp, encoding="utf-8") as f:
        state = json.load(f)
    nxt = find_next(wf, state)
    print(json.dumps({
        "session_id": state["session"]["id"],
        "status": state["session"]["status"],
        "current_node": state["current_node"],
        "node_tasks": {k: v["status"] for k, v in state["node_tasks"].items()},
        "next": nxt,
    }, ensure_ascii=False, indent=2))


def cmd_status(args):
    with open(args[0], encoding="utf-8") as f:
        state = json.load(f)
    out = {
        "session_id": state["session"]["id"],
        "workflow": state["session"]["workflow"],
        "status": state["session"]["status"],
        "iteration": state["pipeline"]["iteration"],
        "current_node": state["current_node"],
        "node_tasks": {k: {"status": v["status"], "agent": v.get("agent"), "output_file": v.get("output_file"), "error": v.get("error")} for k, v in state["node_tasks"].items()},
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_validate(args):
    wf = load_workflow(args[0])
    errs = []
    nodes = get_nodes(wf)
    for nid, n in nodes.items():
        for d in n.get("depends_on", []):
            if d not in nodes:
                errs.append(f"'{nid}': unknown dep '{d}'")
        ntype = n.get("type", "agent")
        if ntype not in ("agent", "code"):
            errs.append(f"'{nid}': unknown type '{ntype}'")
        if ntype == "code" and not n.get("handler"):
            errs.append(f"'{nid}': code 节点缺少 handler")
        if ntype == "code" and _builtin(n.get("handler")) is None:
            errs.append(f"'{nid}': 未知 handler '{n.get('handler')}'")
    try:
        get_stage_order(wf)
    except ValueError as e:
        errs.append(str(e))
    if errs:
        print("FAILED:"); [print(f"  - {e}") for e in errs]; sys.exit(1)
    print(f"OK: {len(nodes)} nodes")


# ─── Auto Harness ─────────────────────────────────────────────────────────
# auto 命令：唯一调度者。所有流程决策（next/回退/校验/循环/重试）都在这里用代码完成，
# LLM 退化为内容生成器，仅在 agent 节点被 `opencode run` 子进程调用。

import subprocess
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _builtin(name: str):
    return _BUILTINS.get(name)


def _exec_code_node(node_def: dict, state: dict) -> dict:
    """执行 code 节点。返回 outputs dict。handler 不存在则抛错。"""
    handler = node_def.get("handler")
    if not handler:
        raise ValueError(f"code node '{node_def.get('id')}' missing 'handler'")
    fn = _builtin(handler)
    if fn is None:
        raise ValueError(f"code node '{node_def.get('id')}': unknown handler '{handler}'")

    params = {}
    for k, v in (node_def.get("params") or {}).items():
        if isinstance(v, str) and v.startswith("@"):
            params[k] = state["data"].get(v[1:])
        else:
            params[k] = v
    result = fn(**params)
    if isinstance(result, dict):
        return result
    keys = list(node_def.get("outputs", {}).keys())
    if len(keys) == 1:
        return {keys[0]: result}
    raise ValueError(f"code node '{node_def.get('id')}' handler returned non-dict but has {len(keys)} outputs")


def _check_node(node_def: dict, outputs: dict) -> list[str]:
    """对 code 节点输出做确定性断言。返回违反列表，空 = 通过。"""
    faults = []
    for c in node_def.get("checks", []):
        field = c.get("field")
        if field not in outputs:
            faults.append(f"check '{field}': handler 未输出该字段")
            continue
        val = outputs[field]
        if "min" in c and not (val >= c["min"]):
            faults.append(f"{field}={val} 不满足 min={c['min']}")
        if "max" in c and not (val <= c["max"]):
            faults.append(f"{field}={val} 不满足 max={c['max']}")
        if c.get("empty") is True and not isinstance(val, list):
            faults.append(f"{field} 应为数组")
        elif c.get("empty") is True and len(val) > 0:
            faults.append(f"{field} 应为空，实际命中: {val}")
        if "min_length" in c and len(str(val)) < c["min_length"]:
            faults.append(f"{field} 长度 {len(str(val))} 小于 {c['min_length']}")
        if c.get("truthy") is True and not val:
            faults.append(f"{field} 应为真值")
        if c.get("falsy") is True and val:
            faults.append(f"{field} 应为假值，实际: {val}")
    return faults


def _build_agent_prompt(node_def: dict, state: dict, inject_block: str) -> str:
    """构造一次 LLM 调用的最小 prompt。不包含任何调度知识。"""
    inputs = {k: state["data"][k] for k in node_def.get("inputs", {}) if k in state["data"]}
    outs = node_def.get("outputs", {})
    lines = [
        f"你是该工作流的节点执行者。本节点：{node_def.get('name', node_def.get('id'))}",
        f"输入数据：{json.dumps(inputs, ensure_ascii=False)}",
    ]
    if inject_block:
        lines.append(inject_block)
    lines.append(f"必须输出字段（JSON 键）：{json.dumps(list(outs.keys()), ensure_ascii=False)}")
    if len(outs) == 1 and list(outs.values())[0].get("type") == "string":
        lines.append("若只有一个 string 输出字段，直接输出该字段的纯文本内容，不要包 JSON。")
    else:
        lines.append("直接输出一个 JSON 对象，键严格对应该字段列表，不要多余文字。")
    return "\n".join(lines)


def _call_agent(agent: str, prompt: str) -> str:
    """通过 opencode run 子进程发起一次 LLM 调用，返回合并后的文本结果。"""
    cmd = ["opencode", "run", prompt, "--agent", agent, "--format", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=str(WORKFLOW_DIR.parent.parent))
    except Exception as e:
        raise RuntimeError(f"opencode run 失败: {e}")
    if proc.returncode != 0:
        raise RuntimeError(f"opencode run 退出码 {proc.returncode}: {proc.stderr[:400]}")
    # NDJSON 事件流，聚合 type=text 的 part.text
    texts = []
    for line in proc.stdout.splitlines():
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if ev.get("type") == "text":
            t = ev.get("part", {}).get("text")
            if t:
                texts.append(t)
    out = "\n".join(texts).strip()
    if not out:
        raise RuntimeError("opencode run 未返回文本")
    return out


def _parse_agent_output(text: str, outputs_spec: dict) -> dict:
    """把 LLM 文本解析为 outputs dict。单 string 输出按纯文本；否则尝试 JSON。"""
    if len(outputs_spec) == 1 and list(outputs_spec.values())[0].get("type") == "string":
        return {list(outputs_spec.keys())[0]: text}
    try:
        return json.loads(text)
    except Exception:
        raise RuntimeError(f"LLM 输出不是合法 JSON: {text[:200]}")


def _code_target(node_def: dict) -> str:
    """失败时回退目标。优先 node 配置回退链。"""
    of = node_def.get("on_fail")
    if not of:
        return None
    dep = node_def.get("depends_on") or []
    return of.get("loop_back_to") or (dep[0] if dep else None)


def _run_node_once(node_def: dict, state: dict) -> tuple[dict | None, str | None]:
    """执行单个节点，返回 (outputs, error)。

    纯函数式：不修改传入的 state，便于多节点在同一波次内并发调用；
    输出由主线程在 join 后统一合并回 state。
    """
    node_type = node_def.get("type", "agent")
    try:
        if node_type == "code":
            outputs = _exec_code_node(node_def, state)
            faults = _check_node(node_def, outputs)
            if faults:
                return None, "; ".join(faults)
            return outputs, None

        if node_type == "agent":
            inject_block = ""
            m = _load_mistakes()
            rules = [r for r in m.get("rules", []) if int(r.get("times_seen", 0)) >= 2]
            if rules:
                inject_block = "## 历史错误禁令（禁止再犯）\n" + "\n".join(
                    f"- {r['rule']}（曾犯{r['times_seen']}次）" for r in rules
                )
            prompt = _build_agent_prompt(node_def, state, inject_block)
            text = _call_agent(node_def.get("agent"), prompt)
            outputs = _parse_agent_output(text, node_def.get("outputs", {}))
            errs = validate_outputs(node_def, outputs)
            if errs:
                return None, "; ".join(errs)
            return outputs, None

        return None, f"unknown node type: {node_type}"
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def _reset_for_loop(state: dict, nid: str):
    """把某节点重置为 pending，供 revise_loop 回跳重跑。"""
    task = state["node_tasks"].get(nid)
    if not task:
        return
    task["status"] = "pending"
    task["started_at"] = None
    task["completed_at"] = None
    task["error"] = None


def _deep_copy(obj: dict) -> dict:
    return json.loads(json.dumps(obj, ensure_ascii=False))


def cmd_auto(args):
    """python3 workflow_engine.py auto <wf.json> --state <s.json>
       [--input <i.json>] [--start S] [--end E] [--workers N]

    并行 DAG 调度入口（引擎是唯一调度者，LLM 仅作为节点内容生成器）：
      1. 每一轮计算「就绪波次」= 所有前置依赖已完成的 pending 节点；
      2. mode=linear 时每轮只取第一个节点（串行，兼容旧行为）；
         mode=dag / parallel 时并发执行整波节点，全部完成后 join；
      3. join 后由主线程统一合并输出、写盘、判定失败重试与 revise_loop。
    """
    wf = load_workflow(args[0])
    sp = _arg(args, "--state")
    ip = _arg(args, "--input")
    start = _arg(args, "--start")
    end = _arg(args, "--end")
    workers_arg = _arg(args, "--workers")
    if not sp:
        print("Error: --state required", file=sys.stderr); sys.exit(1)

    mode = str(wf.get("schedule", {}).get("mode", "linear")).lower()
    parallel = mode in ("dag", "parallel")

    if os.path.exists(sp):
        with open(sp, encoding="utf-8") as f:
            state = json.load(f)
        if state["session"]["status"] == "completed":
            print(json.dumps({"action": "already_done", "session_id": state["session"]["id"]},
                             ensure_ascii=False, indent=2))
            return
    else:
        inp = json.load(open(ip, encoding="utf-8")) if ip else {}
        state = init_state(wf, inp, start, end)
        _save(state, sp)

    nodes = get_nodes(wf)
    retries = {}

    while True:
        ready = get_ready_nodes(wf, state)
        if not ready:
            pending = [n for n, t in state["node_tasks"].items() if t["status"] == "pending"]
            if pending:
                state["session"]["status"] = "failed"
                _save(state, sp)
                print(json.dumps({"action": "blocked", "pending": pending,
                                  "reason": "存在无法就绪的节点（依赖失败或依赖未完成）"},
                                 ensure_ascii=False, indent=2))
                return
            state["session"]["status"] = "completed"
            _save(state, sp)
            print(json.dumps({"action": "done", "session_id": state["session"]["id"],
                              "data": state["data"]}, ensure_ascii=False, indent=2))
            return

        wave = ready if parallel else ready[:1]
        snapshot = _deep_copy(state)  # 供并发节点只读，隔离写竞争

        for nid in wave:
            node_def = nodes[nid]
            task = state["node_tasks"][nid]
            task["status"] = "running"
            task["agent"] = node_def.get("agent")
            task["started_at"] = _now()
            state["log"].append({"time": _now(), "node": nid, "status": "running",
                                 "type": node_def.get("type", "agent")})
        state["current_node"] = wave if parallel else wave[0]
        _save(state, sp)
        print(json.dumps({"action": "wave", "mode": mode, "nodes": wave, "size": len(wave)},
                         ensure_ascii=False), flush=True)

        # ── 并发执行本波次全部节点 ──
        results: dict[str, tuple[dict | None, str | None]] = {}
        if len(wave) == 1:
            results[wave[0]] = _run_node_once(nodes[wave[0]], snapshot)
        else:
            schema_workers = int(wf.get("schedule", {}).get("max_concurrency") or 0)
            max_workers = int(workers_arg) if workers_arg else (schema_workers or len(wave))
            max_workers = max(1, min(max_workers, len(wave)))
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {pool.submit(_run_node_once, nodes[nid], snapshot): nid for nid in wave}
                for fut in as_completed(futures):
                    nid = futures[fut]
                    try:
                        results[nid] = fut.result()
                    except Exception as e:  # noqa: BLE001
                        results[nid] = (None, str(e))

        # ── join：主线程统一合并，避免并发写 state ──
        failed = []
        for nid in wave:
            outputs, err = results[nid]
            node_def = nodes[nid]
            task = state["node_tasks"][nid]
            if err is None:
                out_file = write_output_file(state, node_def, outputs)
                task["status"] = "completed"
                task["completed_at"] = _now()
                task["output_file"] = out_file
                state["data"].update(outputs)
                state["pipeline"]["iteration"] += 1
                state["log"].append({"time": _now(), "node": nid, "status": "completed",
                                     "type": node_def.get("type", "agent"), "output_file": out_file})
            else:
                task["status"] = "failed"
                task["error"] = err
                state["log"].append({"time": _now(), "node": nid, "status": "failed", "error": err})
                failed.append(nid)

        state["current_node"] = None
        _save(state, sp)
        print(json.dumps({"action": "joined", "nodes": wave, "failed": failed},
                         ensure_ascii=False), flush=True)

        # ── 失败处理：code 节点按 on_fail 回退重试 ──
        if failed:
            retry_targets = []
            for nid in failed:
                node_def = nodes[nid]
                target = _code_target(node_def)
                if target and retries.get(nid, 0) < int(node_def.get("on_fail", {}).get("max_retries", 2)):
                    retries[nid] = retries.get(nid, 0) + 1
                    state["data"][f"__retry_{nid}"] = results[nid][1]
                    state["log"].append({"time": _now(), "node": nid,
                                         "status": f"retry_to_{target}", "error": results[nid][1]})
                    _reset_for_loop(state, target)
                    retry_targets.append(target)
            if retry_targets:
                state["current_node"] = retry_targets
                _save(state, sp)
                print(json.dumps({"action": "retry", "loop_back_to": retry_targets},
                                 ensure_ascii=False))
                continue
            state["session"]["status"] = "failed"
            _save(state, sp)
            print(json.dumps({"action": "failed", "nodes": failed,
                              "errors": {n: results[n][1] for n in failed}},
                             ensure_ascii=False, indent=2))
            return

        # ── revise loop（纯代码决策，命中则重置回跳节点重跑）──
        lt = None
        for nid in wave:
            lt = check_revise_loop(state, wf, nid)
            if lt:
                break
        if lt:
            _reset_for_loop(state, lt)
            state["current_node"] = lt
            state["log"].append({"time": _now(), "node": wave[-1], "status": f"loop_to_{lt}"})
            _save(state, sp)
            print(json.dumps({"action": "loop", "target": lt}, ensure_ascii=False))


# 内置 code 节点函数库 —— 引擎不同进程共享的实现
_BUILTINS = {
    "count_cjk": lambda text: len(_CJK_RE.findall(text or "")),
    "check_blacklist": lambda text, words: [w for w in (words or []) if w and w in (text or "")],
    "read_text": lambda path: open(path, encoding="utf-8").read(),
    "length": lambda value: len(value) if value is not None else 0,
    "truthy": lambda value: bool(value),
}


# ─── Mistake Memory ───────────────────────────────────────────────────────

_MISTAKES_FILE = WORKFLOW_DIR / "mistakes.json"
_CATEGORIES = {"ai_pattern", "structure", "character", "logic", "pacing"}


def _load_mistakes() -> dict:
    if not _MISTAKES_FILE.exists():
        return {"version": "1.0", "project": "", "rules": []}
    with open(_MISTAKES_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_mistakes(m: dict):
    with open(_MISTAKES_FILE, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)


def _next_id(m: dict) -> str:
    mx = 0
    for r in m.get("rules", []):
        try:
            mx = max(mx, int(str(r.get("id", "M0")).lstrip("M")))
        except ValueError:
            pass
    return f"M{mx + 1:03d}"


def cmd_mistakes(args):
    sub = args[0] if args else "list"

    if sub == "list":
        m = _load_mistakes()
        print(json.dumps(m, ensure_ascii=False, indent=2))
        return

    if sub == "add":
        # add "<rule>" --category <cat> --chapter <ch>
        rule = None
        category = "ai_pattern"
        chapter = None
        for i, a in enumerate(args):
            if a == "--category" and i + 1 < len(args): category = args[i + 1]
            if a == "--chapter" and i + 1 < len(args): chapter = args[i + 1]
        rule = _arg(args, "add") and args[1] if len(args) > 1 and not args[1].startswith("--") else None
        if not rule:
            # try after "add" token before any --flag
            rule = next((a for a in args[1:] if not a.startswith("--")), None)
        if not rule:
            print("Error: usage: mistakes add '<rule>' [--category X] [--chapter Y]", file=sys.stderr); sys.exit(1)
        if category not in _CATEGORIES and category != "other":
            print(f"Warning: unknown category '{category}', using 'other'", file=sys.stderr)
            category = "other"

        m = _load_mistakes()

        # 若已有相同规则 → bump
        for r in m.get("rules", []):
            if r.get("rule") == rule:
                r["times_seen"] = int(r.get("times_seen", 0)) + 1
                if chapter: r["last_seen_chapter"] = chapter
                r["last_seen_at"] = _now()
                _save_mistakes(m)
                print(json.dumps({"action": "bumped", "id": r["id"], "times_seen": r["times_seen"]}))
                return

        entry = {
            "id": _next_id(m),
            "category": category,
            "rule": rule,
            "times_seen": 1,
            "last_seen_chapter": chapter,
            "last_seen_at": _now(),
        }
        m.setdefault("rules", []).append(entry)
        _save_mistakes(m)
        print(json.dumps({"action": "added", "id": entry["id"], "rule": rule}))
        return

    if sub == "inject":
        """输出一个可直接拼进 agent prompt 的禁令块（top N 高频错误）。"""
        m = _load_mistakes()
        rules = sorted(m.get("rules", []), key=lambda r: int(r.get("times_seen", 0)), reverse=True)
        lines = []
        for r in rules:
            ts = r.get("times_seen", 0)
            if int(ts) >= 2:
                lines.append(f"- {r['rule']}（曾犯{ts}次）")
        if not lines:
            lines = ["（当前无）"]
        output = {"inject_block": "## 历史错误禁令（禁止再犯）\n" + "\n".join(lines)}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print("Error: unknown subcommand. Use: list | add | inject", file=sys.stderr); sys.exit(1)


def cmd_ready(args):
    """python3 workflow_engine.py ready <wf.json> --state <s.json>

    只读：打印当前所有「就绪节点」（DAG 就绪波次），供调用方并发派发。
    mode=dag/parallel 时可一次拿到多个可并行执行的节点。
    """
    wf = load_workflow(args[0])
    sp = _arg(args, "--state")
    if not sp:
        print("Error: --state required", file=sys.stderr); sys.exit(1)
    with open(sp, encoding="utf-8") as f:
        state = json.load(f)
    mode = str(wf.get("schedule", {}).get("mode", "linear")).lower()
    ready = get_ready_nodes(wf, state)
    print(json.dumps({
        "session_id": state["session"]["id"],
        "status": state["session"]["status"],
        "mode": mode,
        "parallel": mode in ("dag", "parallel"),
        "ready": ready,
        "size": len(ready),
    }, ensure_ascii=False, indent=2))


COMMANDS = {
    "init": cmd_init, "plan": cmd_plan, "run": cmd_run,
    "complete": cmd_complete, "fail": cmd_fail, "resume": cmd_resume,
    "next": cmd_next, "status": cmd_status, "validate": cmd_validate,
    "mistakes": cmd_mistakes, "auto": cmd_auto, "ready": cmd_ready,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: {sys.argv[0]} <{'|'.join(COMMANDS.keys())}> [args...]")
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
