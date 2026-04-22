#!/usr/bin/env python3
"""
SlimCheck API Server - 卡路里管理多智能体系统服务端
支持流式 SSE 返回、并行请求、UUID 追踪
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rich.console import Console

from config import get_settings
from src.utils.logger import get_server_logger

console = Console()
logger = get_server_logger()

# 全局初始化标志
_is_initialized = False


async def _init_directories():
    """初始化数据目录"""
    import os
    settings = get_settings()

    for dir_path in [settings.DATA_DIR, settings.USERS_DIR, settings.LOGS_DIR]:
        os.makedirs(dir_path, exist_ok=True)


async def _init_services():
    """初始化服务"""
    from src.utils.request_manager import request_manager

    # 启动定期清理任务
    async def cleanup_loop():
        while True:
            request_manager.cleanup_completed()
            await asyncio.sleep(300)  # 每5分钟清理一次

    asyncio.create_task(cleanup_loop())
    logger.info("Request manager initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global _is_initialized

    if not _is_initialized:
        settings = get_settings()
        logger.info("=" * 60)
        logger.info("SlimCheck API Server starting...")
        logger.info(f"Model: {settings.OPENAI_MODEL}")
        logger.info(f"Max concurrent requests: {settings.MAX_CONCURRENT_REQUESTS}")
        logger.info("=" * 60)

        # 初始化目录
        await _init_directories()

        # 初始化服务
        await _init_services()

        _is_initialized = True
        logger.info("Server started successfully!")

    yield

    # 关闭时清理
    logger.info("Server shutting down...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    settings = get_settings()

    app = FastAPI(
        title="SlimCheck API",
        description="基于 LangGraph 的卡路里管理多智能体系统 - API 服务",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS_LIST,
        allow_credentials=True,
        allow_methods=settings.CORS_METHODS_LIST,
        allow_headers=settings.CORS_HEADERS_LIST,
        expose_headers=["X-Request-ID", "X-Response-Time"]
    )

    # 注册路由
    from src.api.router_health import router as health_router
    from src.api.router_analyze import router as analyze_router
    from src.api.router_users import router as users_router
    from src.api.router_requests import router as requests_router

    app.include_router(health_router, prefix="/api/v1", tags=["健康检查"])
    app.include_router(analyze_router, prefix="/api/v1", tags=["分析接口"])
    app.include_router(users_router, prefix="/api/v1", tags=["用户管理"])
    app.include_router(requests_router, prefix="/api/v1", tags=["请求管理"])

    # 根路径
    @app.get("/", summary="根路径", tags=["系统"])
    async def root():
        return {
            "service": "SlimCheck API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs"
        }

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    console.print("[bold green]🚀 Starting SlimCheck API Server...[/]")
    console.print(f"📄 API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    console.print("=" * 60)

    uvicorn.run(
        "src.server:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG,
        workers=1 if settings.DEBUG else 2
    )
