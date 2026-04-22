"""
请求管理接口
支持查询请求状态、取消请求、列出所有请求
"""
from uuid import UUID
from typing import Optional, Dict, Any

from fastapi import APIRouter

from src.utils.request_manager import request_manager, RequestStatus
from src.models.api_models import (
    RequestStatusResponse,
    RequestListResponse,
    CancelResponse,
    ApiResponse,
)

router = APIRouter()


def _state_to_response(state) -> RequestStatusResponse:
    """将请求状态转换为响应格式"""
    return RequestStatusResponse(
        request_id=str(state.request_id),
        status=state.status,
        current_stage=state.current_stage,
        created_at=state.created_at.isoformat(),
        started_at=state.started_at.isoformat() if state.started_at else None,
        completed_at=state.completed_at.isoformat() if state.completed_at else None,
        duration_ms=state.duration_ms,
        error=state.error,
    )


@router.get("/requests/{request_id}/status", summary="查询请求状态", response_model=ApiResponse[RequestStatusResponse])
async def get_request_status(request_id: UUID):
    """
    查询指定请求的状态

    - **request_id**: 请求 ID
    """
    state = request_manager.get_request_state(request_id)

    if not state:
        return ApiResponse[RequestStatusResponse](
            code=-1,
            data=None,
            msg="请求不存在"
        )

    return ApiResponse[RequestStatusResponse](
        code=0,
        data=_state_to_response(state),
        msg="查询成功"
    )


@router.post("/requests/{request_id}/cancel", summary="取消请求", response_model=ApiResponse[CancelResponse])
async def cancel_request(request_id: UUID):
    """
    取消正在进行的请求

    - **request_id**: 要取消的请求 ID
    """
    success = request_manager.cancel_request(request_id)

    if not success:
        state = request_manager.get_request_state(request_id)
        if not state:
            return ApiResponse[CancelResponse](
                code=-1,
                data=None,
                msg="请求不存在"
            )
        return ApiResponse[CancelResponse](
            code=-1,
            data=None,
            msg=f"请求无法取消，当前状态: {state.status}"
        )

    data = CancelResponse(
        success=True,
        message="请求已取消",
        request_id=str(request_id)
    )
    return ApiResponse[CancelResponse](
        code=0,
        data=data,
        msg="取消成功"
    )


@router.get("/requests", summary="列出所有请求", response_model=ApiResponse[RequestListResponse])
async def list_requests(status_filter: Optional[RequestStatus] = None):
    """
    列出所有请求，可按状态过滤

    - **status_filter**: 可选，按状态过滤: pending/running/completed/cancelled/failed
    """
    states = request_manager.list_requests(status_filter)

    response_states = [_state_to_response(state) for state in states]

    data = RequestListResponse(
        total=len(response_states),
        requests=response_states,
        stats=request_manager.get_stats()
    )

    return ApiResponse[RequestListResponse](
        code=0,
        data=data,
        msg="获取请求列表成功"
    )


@router.get("/requests/stats", summary="请求统计", response_model=ApiResponse[Dict[str, Any]])
async def get_request_stats():
    """
    获取请求统计信息
    """
    stats = request_manager.get_stats()
    return ApiResponse[Dict[str, Any]](
        code=0,
        data=stats,
        msg="获取统计信息成功"
    )
