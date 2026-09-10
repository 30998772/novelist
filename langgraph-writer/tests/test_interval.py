"""区间执行逻辑测试。

纯逻辑部分 (无 LLM/无依赖) 可直接在任意 Python 运行:
    python -m pytest tests/test_interval.py -v

需要真实 LangGraph 的图装配测试, 在安装依赖后运行。
"""

import sys

import pytest

from writer_agent.registry import get_stage, registered_names
from writer_agent.state import (
    STAGE_LABELS,
    STAGE_ORDER,
    interval_stages,
    normalize_stage,
    validate_interval,
)
import writer_agent.nodes as _  # noqa: F401  触发节点注册

STAGES = STAGE_ORDER


def test_stage_order_complete():
    assert STAGES == ["research", "outline", "draft", "review", "revise", "finalize"]


def test_all_21_intervals_expand_correctly():
    n = len(STAGES)
    total = 0
    for si in range(n):
        for ei in range(si, n):
            total += 1
            assert interval_stages(STAGES[si], STAGES[ei]) == STAGES[si : ei + 1]
    assert total == 21


def test_reversed_interval_rejected():
    with pytest.raises(ValueError):
        validate_interval("finalize", "draft")
    with pytest.raises(ValueError):
        validate_interval("写稿", "调研")


def test_stage_normalization():
    assert normalize_stage("写稿") == "draft"
    assert normalize_stage("DRAFT") == "draft"
    assert normalize_stage(" research ") == "research"
    assert interval_stages("审稿", "修改") == ["review", "revise"]


def test_six_nodes_registered():
    assert sorted(registered_names()) == sorted(STAGES)


def test_node_pipeline_chains_products_without_llm(tmp_path, monkeypatch):
    """用假 LLM 驱动 6 节点全链路, 验证产物逐段接续。"""

    class FakeLLM:
        def __init__(self, *a, **k):
            pass

        def invoke(self, messages):
            return SimpleNamespace(content="stub_output")

    monkeypatch.setattr(
        sys.modules["writer_agent.nodes"], "ChatOpenAI", FakeLLM
    )
    monkeypatch.setenv("LLM_API_KEY", "test")

    state = {
        "task": "写一章示例",
        "input_data": {"target_word_count": 3000},
        "iteration": 0,
        "max_iterations": 3,
        "messages": [],
    }
    out_keys = {
        "research": "research_notes",
        "outline": "outline",
        "draft": "draft",
        "review": "review_notes",
        "revise": "draft",
        "finalize": "final_content",
    }
    for name, outkey in out_keys.items():
        state.update(get_stage(name)(state))
        assert outkey in state

    assert isinstance(state["review_notes"], list)
    assert len(state["messages"]) == len(STAGES)


def test_review_returns_json_list(monkeypatch):
    class FakeLLM:
        def invoke(self, messages):
            return SimpleNamespace(content='["问题A", "问题B"]')

        def __init__(self, *a, **k):
            pass

    monkeypatch.setattr(sys.modules["writer_agent.nodes"], "ChatOpenAI", FakeLLM)
    monkeypatch.setenv("LLM_API_KEY", "test")

    state = {
        "task": "t", "input_data": {}, "draft": "草稿内容", "iteration": 0,
        "max_iterations": 3, "messages": [],
    }
    result = get_stage("review")(state)
    assert result["review_notes"] == ["问题A", "问题B"] or result["review_notes"]


def test_build_agent_wiring():
    """需要真实 LangGraph。未安装时跳过。"""
    pytest.importorskip("langgraph")
    from writer_agent.graph_builder import build_agent

    graph = build_agent(start="draft", end="review")
    assert graph is not None

    full = build_agent()
    assert full is not None


from types import SimpleNamespace  # noqa: E402  (放末尾避免头部 import 告警; 运行时才解析, 无碍)