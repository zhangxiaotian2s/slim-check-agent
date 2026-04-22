"""
SSE 流式输出工具
"""
import json
from uuid import UUID
from datetime import datetime
from typing import Any, Dict, Optional
from sse_starlette import ServerSentEvent


def create_sse_event(
    event: str,
    data: Dict[str, Any],
    request_id: Optional[UUID] = None,
    id: Optional[str] = None
) -> ServerSentEvent:
    """
    创建 SSE 事件

    Args:
        event: 事件类型 (status/partial_result/error/complete)
        data: 事件数据
        request_id: 请求 ID
        id: 事件 ID（可选，默认使用时间戳）

    Returns:
        ServerSentEvent: SSE 事件对象
    """
    # 确保包含 timestamp
    if "timestamp" not in data:
        data["timestamp"] = datetime.utcnow().isoformat()

    # 确保包含 request_id
    if request_id and "request_id" not in data:
        data["request_id"] = str(request_id)

    if id is None:
        id = str(int(datetime.utcnow().timestamp() * 1000))

    # ServerSentEvent 需要 JSON 字符串，不是 Python 字典
    return ServerSentEvent(
        event=event,
        data=json.dumps(data, ensure_ascii=False),
        id=id
    )


def create_status_event(
    request_id: UUID,
    stage: str,
    message: str,
    progress: int
) -> ServerSentEvent:
    """创建状态更新事件"""
    return create_sse_event(
        event="status",
        data={
            "stage": stage,
            "message": message,
            "progress": progress
        },
        request_id=request_id
    )


def create_thinking_event(
    request_id: UUID,
    stage: str,
    content: str,
    chunk_index: Optional[int] = None,
    total_chunks: Optional[int] = None,
    token_usage: Optional[Dict[str, Any]] = None
) -> ServerSentEvent:
    """创建大模型思考过程事件"""
    data = {
        "stage": stage,
        "content": content
    }
    if chunk_index is not None:
        data["chunk_index"] = chunk_index
    if total_chunks is not None:
        data["total_chunks"] = total_chunks
    if token_usage is not None:
        data["token_usage"] = token_usage
    return create_sse_event(
        event="thinking",
        data=data,
        request_id=request_id
    )


def create_partial_result_event(
    request_id: UUID,
    result_type: str,
    result_data: Dict[str, Any]
) -> ServerSentEvent:
    """创建部分结果事件"""
    return create_sse_event(
        event="partial_result",
        data={
            "type": result_type,
            "data": result_data
        },
        request_id=request_id
    )


def create_error_event(
    request_id: UUID,
    message: str,
    code: str = "INTERNAL_ERROR",
    details: Optional[Dict[str, Any]] = None
) -> ServerSentEvent:
    """创建错误事件"""
    data = {"message": message, "code": code}
    if details:
        data["details"] = details
    return create_sse_event(
        event="error",
        data=data,
        request_id=request_id
    )


def create_complete_event(
    request_id: UUID,
    success: bool,
    duration_ms: Optional[int] = None,
    final_result: Optional[Dict[str, Any]] = None
) -> ServerSentEvent:
    """创建完成事件"""
    data = {"success": success}
    if duration_ms is not None:
        data["duration_ms"] = duration_ms
    if final_result is not None:
        data["final_result"] = final_result
    return create_sse_event(
        event="complete",
        data=data,
        request_id=request_id
    )


def create_cancelled_event(
    request_id: UUID,
    message: str = "请求已被用户取消"
) -> ServerSentEvent:
    """创建取消事件"""
    return create_sse_event(
        event="cancelled",
        data={"message": message},
        request_id=request_id
    )


# ==================== 阶段映射 ====================

# 节点名称 -> 显示消息、进度（0-100）
STAGE_MAPPING = {
    "route_input": ("识别输入类型...", 5),
    "classify_text": ("分析文本内容...", 10),
    "check_user_info": ("检查用户信息...", 15),
    "analyze_diet": ("分析饮食卡路里...", 30),
    "analyze_exercise": ("分析运动消耗...", 50),
    "health_review": ("生成健康综合点评...", 80),
    "generate_result": ("生成最终报告...", 95),
    "save_user_profile": ("保存用户档案...", 90),
}


def get_stage_info(node_name: str):
    """
    获取阶段显示信息

    Returns:
        tuple: (message, progress)
    """
    return STAGE_MAPPING.get(node_name, ("处理中...", 50))


def calculate_overall_progress(current_stage: str, has_diet: bool, has_exercise: bool) -> int:
    """
    根据当前阶段计算总体进度

    Args:
        current_stage: 当前节点名称
        has_diet: 是否包含饮食分析
        has_exercise: 是否包含运动分析

    Returns:
        int: 0-100 的进度值
    """
    _, base_progress = get_stage_info(current_stage)

    # 根据是否有饮食/运动调整权重
    if has_diet and has_exercise:
        # 双分析任务权重
        weight_map = {
            "route_input": 0.05,
            "classify_text": 0.10,
            "analyze_diet": 0.35,
            "analyze_exercise": 0.60,
            "health_review": 0.85,
            "generate_result": 0.95,
        }
        return int(weight_map.get(current_stage, base_progress / 100) * 100)

    return base_progress
