"""
分析接口 - 流式 SSE 返回
支持饮食分析、运动分析、图片分析
"""
import asyncio
import base64
import io
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status, UploadFile, File, Form, Query
from typing import Literal as TypingLiteral
from sse_starlette.sse import EventSourceResponse

from src.models.api_models import AnalyzeRequest
from src.graph.state import CalorieState
from src.graph.calorie_graph import create_calorie_graph
from src.utils.request_manager import request_manager, RequestStatus
from src.utils.logger import get_request_logger
from src.utils.sse_utils import (
    create_status_event,
    create_thinking_event,
    create_partial_result_event,
    create_error_event,
    create_complete_event,
    create_cancelled_event,
    get_stage_info,
)

router = APIRouter()

# 创建 LangGraph 应用实例
calorie_app = create_calorie_graph()


def _decode_base64_image(base64_str: str) -> bytes:
    """解码 base64 图片"""
    # 移除 data:image/xxx;base64, 前缀
    if base64_str.startswith('data:image'):
        base64_str = base64_str.split(',', 1)[1]
    # 解码
    return base64.b64decode(base64_str)


def _build_graph_state(request: AnalyzeRequest, request_id: UUID) -> CalorieState:
    """构建 LangGraph 初始状态"""
    state: CalorieState = {
        "input_type": request.input_type,
        "image_data": None,
        "image_base64": None,
        "text_input": request.text or "",
        "person_id": request.person_id,
        "user_profile": None,
        "content_type": None,
        "analyzed_foods": None,
        "analyzed_exercise": None,
        "_has_diet": False,
        "_has_exercise": False,
        "_is_user_registration": False,
        "analysis_result": None,
        "requires_user_input": False,
        "missing_fields": None,
        "error_message": None,
    }

    # 处理图片
    if request.input_type in ["image", "image_with_text"] and request.image_base64:
        state["image_data"] = _decode_base64_image(request.image_base64)
        state["image_base64"] = request.image_base64

    # 设置 content_type 提示
    if request.content_type_hint:
        state["content_type"] = request.content_type_hint

    return state


def _get_thinking_content(node_name: str, node_output: dict, state: CalorieState) -> Optional[str]:
    """生成每个阶段的思考内容，模拟大模型深度思考过程"""

    if node_name == "route_input":
        return "正在解析用户输入，判断内容类型...\n识别到文本输入，准备进行自然语言分析。"

    if node_name == "classify_text":
        content = state.get("text_input", "")
        has_food = any(word in content for word in ["吃", "餐", "饭", "面", "包子", "豆浆", "沙拉", "肉", "菜"])
        has_exercise = any(word in content for word in ["跑", "运动", "走", "健身", "骑", "游泳", "锻炼"])
        return f"正在分类输入内容...\n检测到饮食关键词: {has_food}\n检测到运动关键词: {has_exercise}\n将分配至对应分析模块。"

    if node_name == "check_user_info":
        person_id = state.get("person_id", "")
        return f"正在获取用户档案...\n用户ID: {person_id[:12]}...\n检索用户基础代谢率和活动水平数据，为后续卡路里计算做准备。"

    if node_name == "analyze_diet" and node_output and "analyzed_foods" in node_output:
        foods = node_output["analyzed_foods"]
        total_cal = sum(f.calories for f in foods)
        food_names = ", ".join(f.food_name for f in foods[:3])
        return (
            f"识别到 {len(foods)} 种食物: {food_names}\n"
            f"饮食总热量: {total_cal} kcal\n"
            f"正在计算蛋白质、碳水化合物、脂肪宏量营养素..."
        )

    if node_name == "analyze_exercise" and node_output and "analyzed_exercise" in node_output:
        exercises = node_output["analyzed_exercise"]
        total_burned = sum(e.calories_burned for e in exercises)
        exercise_names = ", ".join(e.exercise_type for e in exercises[:3])
        return (
            f"识别到 {len(exercises)} 项运动: {exercise_names}\n"
            f"运动总消耗: {total_burned} kcal\n"
            f"根据运动强度和持续时间调整卡路里消耗计算。"
        )

    if node_name == "health_review" and node_output and "health_review" in node_output:
        review = node_output["health_review"]
        if review:
            review_count = len(review.get("review_points", []))
            return (
                f"正在综合评估健康状况...\n"
                f"生成了 {review_count} 条个性化建议\n"
                f"正在生成总体评估结论..."
            )
        return "正在综合评估健康状况..."

    if node_name == "generate_result":
        return "正在生成最终分析报告...\n整合所有模块数据，格式化输出结果。"

    return None


def _extract_result_data(node_name: str, node_output: dict) -> Optional[dict]:
    """从节点输出中提取结果数据（用于 partial_result 事件）"""
    if not node_output:
        return None

    # 饮食分析结果
    if node_name == "analyze_diet" and "analyzed_foods" in node_output:
        foods = node_output["analyzed_foods"]
        return {
            "foods": [
                {
                    "name": f.food_name,
                    "calories": f.calories,
                    "protein_g": f.protein_g,
                    "carbs_g": f.carbs_g,
                    "fat_g": f.fat_g,
                    "estimated_grams": f.estimated_grams
                }
                for f in foods
            ],
            "total_calories": sum(f.calories for f in foods)
        }

    # 运动分析结果
    if node_name == "analyze_exercise" and "analyzed_exercise" in node_output:
        exercises = node_output["analyzed_exercise"]
        return {
            "exercises": [
                {
                    "type": e.exercise_type,
                    "duration_minutes": e.duration_minutes,
                    "intensity": e.intensity,
                    "calories_burned": e.calories_burned
                }
                for e in exercises
            ],
            "total_calories_burned": sum(e.calories_burned for e in exercises)
        }

    # 健康点评结果
    if node_name == "health_review" and "health_review" in node_output:
        return node_output["health_review"]

    return None


async def _stream_analysis(
    request: AnalyzeRequest,
    request_id: UUID,
    logger
):
    """
    执行流式分析的核心协程

    Yields:
        ServerSentEvent: SSE 事件
    """
    final_result = None
    start_time = datetime.utcnow()

    try:
        # 构建初始状态
        initial_state = _build_graph_state(request, request_id)

        # 标记请求开始
        request_manager.start_request(request_id)

        # 执行 LangGraph 流
        async for chunk in calorie_app.astream(initial_state):
            # 检查是否被取消
            if request_manager.is_cancelled(request_id):
                logger.info("Request cancelled by user")
                # 发送状态事件
                yield create_status_event(request_id, "cancelled", "用户取消了分析", 100)
                # 发送思考内容
                yield create_thinking_event(
                    request_id,
                    "cancelled",
                    "⚠️ 用户主动取消了分析请求"
                )
                yield create_cancelled_event(request_id)
                return

            for node_name, node_output in chunk.items():
                logger.info(f"Processing node: {node_name}")

                # 更新请求阶段
                request_manager.update_stage(request_id, node_name)

                # 发送状态事件
                message, progress = get_stage_info(node_name)
                yield create_status_event(request_id, node_name, message, progress)

                # 发送思考过程（模拟大模型深度思考）
                thinking_content = _get_thinking_content(node_name, node_output, initial_state)
                if thinking_content:
                    yield create_thinking_event(request_id, node_name, thinking_content)

                # 发送部分结果（如果有）
                result_data = _extract_result_data(node_name, node_output)
                if result_data:
                    # 映射到前端期望的 type 值
                    result_type_map = {
                        "analyze_diet": "food_items",
                        "analyze_exercise": "exercise_items",
                        "health_review": "health_review"
                    }
                    result_type = result_type_map.get(node_name, node_name)
                    yield create_partial_result_event(request_id, result_type, result_data)

        # 计算耗时
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # 发送完成事件
        yield create_complete_event(
            request_id,
            success=True,
            duration_ms=duration_ms,
            final_result=final_result
        )

        # 标记请求完成
        request_manager.complete_request(request_id, {
            "success": True,
            "duration_ms": duration_ms
        })

        logger.info(f"Analysis completed in {duration_ms}ms")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Analysis failed: {error_msg}", exc_info=True)

        # 发送状态事件 - 显示错误状态
        yield create_status_event(request_id, "error", "分析过程中发生错误", 100)

        # 发送思考内容 - 记录错误详情
        yield create_thinking_event(
            request_id,
            "error",
            f"❌ 分析失败: {error_msg}\n请检查输入后重试。"
        )

        # 发送错误事件
        yield create_error_event(request_id, error_msg)

        # 标记请求失败
        request_manager.fail_request(request_id, error_msg)


@router.post("/analyze/stream", summary="流式分析接口")
async def analyze_stream(
    request: AnalyzeRequest,
    x_request_id: Optional[UUID] = Header(None, description="请求追踪ID")
):
    """
    # 流式分析接口

    基于 SSE (Server-Sent Events) 的流式分析接口，实时返回分析状态和中间结果。

    ## 事件类型

    | 事件类型 | 说明 |
    |---------|------|
    | `status` | 阶段更新，包含进度(0-100) |
    | `partial_result` | 中间结果（饮食/运动/健康点评） |
    | `error` | 错误信息 |
    | `complete` | 分析完成 |
    | `cancelled` | 请求被取消 |

    ## 请求头

    - `X-Request-ID`: 前端生成的 UUID，用于追踪请求（可选，服务端自动生成）

    ## 使用示例

    ```javascript
    const eventSource = new EventSource('/api/v1/analyze/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': crypto.randomUUID()
      },
      body: JSON.stringify({
        input_type: 'text_only',
        text: '早餐吃了一个包子，一杯豆浆',
        person_id: '0a5f4a0c'
      })
    });

    eventSource.addEventListener('status', (e) => {
      const data = JSON.parse(e.data);
      console.log(`进度: ${data.progress}% - ${data.message}`);
    });

    eventSource.addEventListener('complete', () => {
      eventSource.close();
    });
    ```
    """
    # 1. 获取或生成 request_id
    request_id = x_request_id or request.request_id or uuid4()
    logger = get_request_logger(request_id)

    logger.info(f"New analysis request: {request.input_type}")

    # 2. 注册请求（获取并发槽位）
    try:
        await request_manager.register_request(request_id)
    except asyncio.TimeoutError:
        logger.warning("Too many concurrent requests, rejected")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="服务器繁忙，请稍后重试"
        )

    # 3. 返回 SSE 响应
    event_generator = _stream_analysis(request, request_id, logger)
    response = EventSourceResponse(event_generator)
    response.headers["X-Request-ID"] = str(request_id)
    return response


@router.post("/analyze/text", summary="文本分析接口（非流式）")
async def analyze_text(request: AnalyzeRequest):
    """纯文本分析接口（非流式，一次性返回结果）"""
    # TODO: 实现非流式版本
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/analyze/image", summary="图片分析接口（非流式）")
async def analyze_image(
    image: UploadFile = File(...),
    text: Optional[str] = Form(None),
    person_id: Optional[str] = Form(None)
):
    """图片分析接口（非流式）"""
    # TODO: 实现非流式版本
    raise HTTPException(status_code=501, detail="Not implemented yet")
