"""
SlimCheck 配置管理
兼容旧版 CLI 和新版 FastAPI 服务
"""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    """旧版配置类 - 供 CLI 使用"""
    openai_base_url: str
    openai_api_key: str
    openai_model: str


def load_config() -> Config:
    """从 .env 文件加载配置（旧版兼容）"""
    load_dotenv()

    return Config(
        openai_base_url=os.getenv("OPENAI_BASE_URL", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", ""),
    )


# 旧版兼容导出
config = load_config()

# 新版 FastAPI 配置导出
try:
    from .settings import Settings, get_settings
    __all__ = ["Config", "config", "Settings", "get_settings"]
except ImportError:
    # 如果 pydantic-settings 未安装，只导出旧版
    __all__ = ["Config", "config"]
