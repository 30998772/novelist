"""BaseRagGraph Prompt 配置。

集中管理 RAG 图的检索、评估、生成、改写 prompt，graph.py 按需导入。
"""

RAG_CHATBOT_PROMPT = (
    "你是小说创作助手的检索决策器，判断是否需要调用本地知识库检索工具来回答问题。\n"
    "\n"
    "检索工具参数如下：\n"
    "knowledge_base：{knowledge_base}\n"
    "top_k：{top_k}\n"
    "score_threshold：{score_threshold}\n"
    "\n"
    "对话历史与用户问题如下：\n"
    "{history}"
)

RAG_GRADE_PROMPT = (
    "你是评估「召回文档」与「用户问题」相关性的评审员。\n"
    "召回文档：\n"
    "{docs}\n"
    "\n"
    "历史与用户问题：\n"
    "{history}\n"
    "\n"
    "若文档包含与问题相关的关键词或语义，判为相关。输出 yes 或 no。\n"
    "输出必须是含 binary_score 属性的对象，例如：{{\"binary_score\": \"yes\"}}。"
)

RAG_GENERATE_PROMPT = (
    "【指令】\n"
    "根据已知信息，简洁专业地回答问题。若无法从已知信息得到答案，请回答\n"
    "「根据已知信息无法回答该问题」，不允许编造，答案使用中文。\n"
    "\n"
    "【已知信息】\n"
    "{docs}\n"
    "\n"
    "【历史消息及用户问题】\n"
    "{history}"
)

RAG_REWRITE_PROMPT = (
    "结合以下对话历史，推断用户问题的语义意图，改写出一个更好的检索问题。\n"
    "\n"
    "历史：\n"
    "{history}\n"
    "\n"
    "原始问题：\n"
    "{question}\n"
    "\n"
    "改写后的问题："
)
