"""
健康检查路由
提供 liveness 和 readiness 探针
"""
from fastapi import APIRouter
from datetime import datetime
import psutil
import sys

from src.models.api_models import ApiResponse, HealthData, DetailedHealthData

router = APIRouter()


# 服务启动时间
_start_time = datetime.now()


@router.get("/health", summary="健康检查", response_model=ApiResponse[HealthData])
async def health_check():
    """基础健康检查 - 用于 liveness 探针"""
    data = HealthData(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )
    return ApiResponse[HealthData](
        code=0,
        data=data,
        msg="服务运行正常"
    )


@router.get("/health/detailed", summary="详细健康检查", response_model=ApiResponse[DetailedHealthData])
async def detailed_health_check():
    """详细健康检查 - 包含系统资源信息"""
    now = datetime.now()
    uptime = (now - _start_time).total_seconds()

    process = psutil.Process()
    memory_info = process.memory_info()

    data = DetailedHealthData(
        status="healthy",
        timestamp=now.utcnow().isoformat(),
        version="1.0.0",
        uptime_seconds=uptime,
        memory={
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
            "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
            "percent": round(process.memory_percent(), 2)
        },
        cpu={
            "percent": process.cpu_percent(),
            "python_version": sys.version
        }
    )
    return ApiResponse[DetailedHealthData](
        code=0,
        data=data,
        msg="获取系统信息成功"
    )


@router.get("/ready", summary="就绪检查", response_model=ApiResponse[HealthData])
async def readiness_check():
    """就绪检查 - 用于 readiness 探针"""
    data = HealthData(
        status="ready",
        timestamp=datetime.utcnow().isoformat()
    )
    return ApiResponse[HealthData](
        code=0,
        data=data,
        msg="服务就绪"
    )
