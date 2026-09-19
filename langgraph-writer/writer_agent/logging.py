"""全局日志配置。

所有模块统一使用 get_logger(name) 获取 logger，日志写入 logs/writer_agent.log。
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "writer_agent.log")

# 确保 logs 目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 日志格式
FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 全局是否已初始化
_initialized = False


def _setup_root():
    """配置 root logger，只执行一次。"""
    global _initialized
    if _initialized:
        return
    _initialized = True

    root = logging.getLogger("writer_agent")
    root.setLevel(logging.DEBUG)

    # 文件 handler：详细日志，轮转 5MB × 3
    fh = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(fh)

    # 控制台 handler：INFO 及以上
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(ch)


def get_logger(name: str) -> logging.Logger:
    """获取 logger，自动初始化日志系统。"""
    _setup_root()
    return logging.getLogger(f"writer_agent.{name}")
