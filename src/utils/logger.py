"""
日志工具模块
支持普通日志和带 request_id 的结构化日志
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional
from uuid import UUID
from functools import lru_cache


def setup_logger(name: str = "slimcheck") -> logging.Logger:
    """设置日志器（旧版兼容）"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "../../data/logs"))
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{name}_{today}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 旧版兼容导出
logger = setup_logger()


# ==================== 新版服务端日志 ====================

class RequestBoundLogger:
    """绑定了 request_id 的日志器"""

    def __init__(self, base_logger: logging.Logger, request_id: Optional[UUID] = None):
        self.base_logger = base_logger
        self.request_id = str(request_id) if request_id else None

    def _format_msg(self, msg: str, **kwargs) -> str:
        """格式化日志消息"""
        parts = []
        if self.request_id:
            parts.append(f"[req:{self.request_id[:12]}...]")
        parts.append(msg)
        if kwargs:
            extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
            parts.append(extra)
        return " ".join(parts)

    def info(self, msg: str, **kwargs):
        self.base_logger.info(self._format_msg(msg, **kwargs))

    def warning(self, msg: str, **kwargs):
        self.base_logger.warning(self._format_msg(msg, **kwargs))

    def error(self, msg: str, exc_info: bool = False, **kwargs):
        self.base_logger.error(self._format_msg(msg, **kwargs), exc_info=exc_info)

    def debug(self, msg: str, **kwargs):
        self.base_logger.debug(self._format_msg(msg, **kwargs))


@lru_cache()
def get_server_logger() -> logging.Logger:
    """获取服务端基础日志器"""
    logger = logging.getLogger("slimcheck.server")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_request_logger(request_id: Optional[UUID] = None) -> RequestBoundLogger:
    """获取绑定了 request_id 的日志器"""
    base_logger = get_server_logger()
    return RequestBoundLogger(base_logger, request_id)
