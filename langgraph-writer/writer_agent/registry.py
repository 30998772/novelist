"""阶段节点注册中心。

参考 LangGraph-Chatchat 的 graphs_factory/graphs_registry.py 的注册模式,
将每个阶段节点通过 @register_stage 装饰器注册到 STAGES registry 中。
"""

from typing import Callable

from .state import WriterState

# stage name -> node function
_STAGES: dict[str, Callable[[WriterState], dict]] = {}


def register_stage(name: str):
    """将节点函数注册到全局 registry。"""

    def decorator(func: Callable[[WriterState], dict]) -> Callable[[WriterState], dict]:
        if name in _STAGES:
            raise KeyError(f"阶段 {name!r} 重复注册")
        _STAGES[name] = func
        func.stage_name = name  # type: ignore[attr-defined]
        return func

    return decorator


def get_stage(name: str) -> Callable[[WriterState], dict]:
    if name not in _STAGES:
        raise KeyError(f"阶段 {name!r} 未注册")
    return _STAGES[name]


def all_stages() -> dict[str, Callable[[WriterState], dict]]:
    return dict(_STAGES)


def registered_names() -> list[str]:
    return list(_STAGES.keys())