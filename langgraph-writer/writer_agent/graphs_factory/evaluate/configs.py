"""评估子图配置。"""

from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class EvaluateState(TypedDict, total=False):
    """评估子图状态：六维评分、故事核心诊断、ACGN风格参考。"""

    messages: Annotated[List[BaseMessage], add_messages]
    history: Optional[List[BaseMessage]]
    task: str
    draft: str               # 待评估稿件


NODE_NAME = "evaluate"
TOOL_NAMES = ["story_core_master", "dragon_ride_007", "urobuchi_gen", "anime_lightnovel_styles"]
AFTER_TOOLS_MSG = "评估工具执行完毕，请查看评估结果并继续"
