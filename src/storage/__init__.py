"""
存储工厂模块
根据配置选择存储方式：JSON 或 MySQL
"""
from typing import Union, Optional
from config import get_settings
from src.utils.logger import logger
from .json_storage import JSONUserStorage
from .database import MySQLUserStorage

settings = get_settings()

# 全局单例
_storage_instance: Optional[Union[JSONUserStorage, MySQLUserStorage]] = None


def get_user_storage() -> Union[JSONUserStorage, MySQLUserStorage]:
    """
    获取用户存储实例（单例）

    根据 STORAGE_TYPE 配置返回对应的存储实现
    - mysql: MySQL 数据库存储
    - json: JSON 文件存储
    """
    global _storage_instance

    if _storage_instance is None:
        storage_type = settings.STORAGE_TYPE.lower()

        if storage_type == "mysql":
            logger.info("Using MySQL storage for user profiles")
            _storage_instance = MySQLUserStorage()
        elif storage_type == "json":
            logger.info("Using JSON storage for user profiles")
            _storage_instance = JSONUserStorage()
        else:
            logger.warning(f"Unknown storage type '{storage_type}', falling back to JSON storage")
            _storage_instance = JSONUserStorage()

    return _storage_instance


def reset_storage_instance() -> None:
    """
    重置存储单例（用于测试或配置变更）
    """
    global _storage_instance
    _storage_instance = None
    logger.info("Storage instance reset")


__all__ = [
    'get_user_storage',
    'reset_storage_instance',
    'JSONUserStorage',
    'MySQLUserStorage'
]
