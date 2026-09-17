"""LLM 工厂：统一的 ChatOpenAI 实例构建入口。

供 tools_factory（skill 工具内部调用）与 app 层（装配 agent 图）共用。
配置优先读环境变量: LLM_API_KEY / LLM_BASE_URL / LLM_MODEL / LLM_TEMPERATURE。
"""

import os
from typing import Optional

from langchain_openai import ChatOpenAI


def get_llm(temperature: Optional[float] = None) -> ChatOpenAI:
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise RuntimeError("请设置环境变量 LLM_API_KEY")
    default_temp = float(os.environ.get("LLM_TEMPERATURE", "0.85"))
    return ChatOpenAI(
        model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1"),
        api_key=api_key,
        temperature=default_temp if temperature is None else temperature,
    )