"""
SlimCheck 服务配置管理
使用 Pydantic Settings，支持环境变量覆盖
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


def _parse_comma_separated_list(value: str | List[str]) -> List[str]:
    """解析逗号分隔的字符串为列表"""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        if value == "*":
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    """应用配置"""

    # ========== LLM 配置 ==========
    OPENAI_BASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "doubao-seed-2.0-pro"

    # ========== 服务配置 ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8083
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    # ========== CORS 配置 ==========
    CORS_ORIGINS: str | List[str] = ["*"]
    CORS_METHODS: str | List[str] = ["*"]
    CORS_HEADERS: str | List[str] = ["*"]

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        return _parse_comma_separated_list(self.CORS_ORIGINS)

    @property
    def CORS_METHODS_LIST(self) -> List[str]:
        return _parse_comma_separated_list(self.CORS_METHODS)

    @property
    def CORS_HEADERS_LIST(self) -> List[str]:
        return _parse_comma_separated_list(self.CORS_HEADERS)

    # ========== 认证配置 ==========
    API_KEY_ENABLED: bool = False
    API_KEY: Optional[str] = None

    # ========== 并发控制 ==========
    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_TIMEOUT_SECONDS: int = 120
    COMPLETED_REQUEST_TTL_HOURS: int = 1

    # ========== 限流配置 ==========
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 30

    # ========== 数据存储 ==========
    STORAGE_TYPE: str = "mysql"  # json / mysql
    DATA_DIR: str = "./data"
    USERS_DIR: str = "./data/users"
    LOGS_DIR: str = "./data/logs"

    # ========== MySQL 数据库 ==========
    DB_HOST: str = "172.32.6.110"
    DB_PORT: int = 30308
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "db_slimcheck"
    DB_CHARSET: str = "utf8mb4"

    @property
    def DATABASE_URL(self) -> str:
        """构建数据库连接URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset={self.DB_CHARSET}"

    # ========== 健康检查 ==========
    HEALTH_CHECK_LIVENESS_THRESHOLD: int = 3
    HEALTH_CHECK_READINESS_THRESHOLD: int = 3

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例（带缓存）"""
    return Settings()
