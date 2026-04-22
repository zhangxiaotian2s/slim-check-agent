"""
请求管理器
支持并行请求控制、请求追踪、取消请求、状态查询
"""
import asyncio
from uuid import UUID
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock


class RequestStatus(str, Enum):
    """请求状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class RequestState:
    """请求状态数据"""
    request_id: UUID
    status: RequestStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    result: Optional[dict] = None
    error: Optional[str] = None
    current_stage: Optional[str] = None

    @property
    def duration_ms(self) -> Optional[int]:
        """请求耗时（毫秒）"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        if self.started_at:
            return int((datetime.utcnow() - self.started_at).total_seconds() * 1000)
        return None


class RequestManager:
    """
    请求管理器 - 单例模式

    功能：
    - 并发请求控制（信号量）
    - 请求状态追踪
    - 取消请求
    - 已完成请求清理
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        """初始化（仅调用一次）"""
        from config import get_settings

        settings = get_settings()

        self._requests: Dict[UUID, RequestState] = {}
        self._max_concurrent = settings.MAX_CONCURRENT_REQUESTS
        self._request_timeout = settings.REQUEST_TIMEOUT_SECONDS
        self._completed_ttl = timedelta(hours=settings.COMPLETED_REQUEST_TTL_HOURS)
        self._semaphore = asyncio.Semaphore(self._max_concurrent)

    async def acquire_slot(self) -> bool:
        """获取并发槽位（带超时）"""
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=30.0  # 最多等待30秒
            )
            return True
        except asyncio.TimeoutError:
            return False

    def release_slot(self):
        """释放槽位"""
        try:
            self._semaphore.release()
        except ValueError:
            # 避免重复释放
            pass

    async def register_request(self, request_id: UUID) -> RequestState:
        """
        注册新请求

        Returns:
            RequestState: 请求状态对象
        Raises:
            asyncio.TimeoutError: 等待超时
        """
        # 先注册（防止重复）
        if request_id in self._requests:
            return self._requests[request_id]

        # 获取并发槽位
        success = await self.acquire_slot()
        if not success:
            raise asyncio.TimeoutError("Too many concurrent requests")

        state = RequestState(
            request_id=request_id,
            status=RequestStatus.PENDING
        )
        self._requests[request_id] = state
        return state

    def start_request(self, request_id: UUID):
        """标记请求开始"""
        if request_id in self._requests:
            state = self._requests[request_id]
            state.status = RequestStatus.RUNNING
            state.started_at = datetime.utcnow()

    def update_stage(self, request_id: UUID, stage: str):
        """更新请求当前阶段"""
        if request_id in self._requests:
            self._requests[request_id].current_stage = stage

    def complete_request(self, request_id: UUID, result: Optional[dict] = None):
        """标记请求完成，释放槽位"""
        if request_id in self._requests:
            state = self._requests[request_id]
            state.status = RequestStatus.COMPLETED
            state.completed_at = datetime.utcnow()
            state.result = result
            self.release_slot()

    def fail_request(self, request_id: UUID, error: str):
        """标记请求失败，释放槽位"""
        if request_id in self._requests:
            state = self._requests[request_id]
            state.status = RequestStatus.FAILED
            state.completed_at = datetime.utcnow()
            state.error = error
            self.release_slot()

    def cancel_request(self, request_id: UUID) -> bool:
        """
        取消请求

        Returns:
            bool: 是否成功取消
        """
        if request_id not in self._requests:
            return False

        state = self._requests[request_id]
        if state.status in [RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.CANCELLED]:
            return False

        state.cancel_event.set()
        state.status = RequestStatus.CANCELLED
        state.completed_at = datetime.utcnow()
        self.release_slot()
        return True

    def is_cancelled(self, request_id: UUID) -> bool:
        """检查请求是否被取消"""
        state = self._requests.get(request_id)
        return state is not None and state.cancel_event.is_set()

    def get_request_state(self, request_id: UUID) -> Optional[RequestState]:
        """获取请求状态"""
        return self._requests.get(request_id)

    def list_requests(self, status: Optional[RequestStatus] = None) -> List[RequestState]:
        """列出请求（可按状态过滤）"""
        states = list(self._requests.values())
        if status:
            states = [s for s in states if s.status == status]
        return states

    def cleanup_completed(self, max_age: Optional[timedelta] = None) -> int:
        """
        清理已完成的请求

        Args:
            max_age: 最大保留时间，默认使用配置值

        Returns:
            int: 清理的请求数量
        """
        if max_age is None:
            max_age = self._completed_ttl

        now = datetime.utcnow()
        to_remove = []

        for req_id, state in self._requests.items():
            if state.status in [RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.CANCELLED]:
                if state.completed_at and (now - state.completed_at) > max_age:
                    to_remove.append(req_id)

        for req_id in to_remove:
            del self._requests[req_id]

        return len(to_remove)

    def get_stats(self) -> dict:
        """获取统计信息"""
        counts = {status: 0 for status in RequestStatus}
        for state in self._requests.values():
            counts[state.status] += 1

        return {
            "total": len(self._requests),
            **counts,
            "available_slots": self._semaphore._value,
            "max_concurrent": self._max_concurrent
        }


# 全局单例实例
request_manager = RequestManager()
