"""
API 请求/响应数据模型
"""
from uuid import UUID
from typing import Optional, Literal, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, field_validator, model_validator, Field


T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应模型"""
    code: int = Field(..., description="响应码: 0=成功, -1=失败")
    data: Optional[T] = Field(None, description="响应数据")
    msg: str = Field(..., description="响应消息")


# ==================== 枚举定义 ====================

class InputType(str):
    TEXT_ONLY = "text_only"
    IMAGE = "image"
    IMAGE_WITH_TEXT = "image_with_text"


class ContentTypeHint(str):
    DIET = "diet"
    EXERCISE = "exercise"
    BOTH = "both"


class SSEEventType(str):
    STATUS = "status"
    PARTIAL_RESULT = "partial_result"
    ERROR = "error"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    LOG = "log"


# ==================== 请求模型 ====================

class AnalyzeRequest(BaseModel):
    """分析请求"""
    input_type: Literal["text_only", "image", "image_with_text"]
    text: Optional[str] = None
    image_base64: Optional[str] = None
    person_id: Optional[str] = None
    content_type_hint: Optional[Literal["diet", "exercise", "both"]] = None
    request_id: Optional[UUID] = None

    @model_validator(mode="after")
    def validate_input(self):
        """验证输入有效性"""
        if self.input_type in ["image", "image_with_text"]:
            if not self.image_base64:
                raise ValueError("image_base64 is required for image input")

        if self.input_type == "image_with_text" and not self.text:
            raise ValueError("text is required for image_with_text input")

        if self.input_type == "text_only" and not self.text:
            raise ValueError("text is required for text_only input")

        return self

    @field_validator('image_base64')
    @classmethod
    def validate_image_base64(cls, v):
        """验证 base64 图片格式"""
        if v is None:
            return v

        # 常见图片格式的 base64 前缀
        valid_prefixes = (
            'data:image/',
            '/9j/',  # JPEG
            'iVB',  # PNG
            'R0lG',  # GIF
            'UklGR',  # WEBP
        )

        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError("Invalid base64 image format")

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "input_type": "text_only",
                "text": "早餐吃了一个包子，喝了一杯豆浆",
                "person_id": "0a5f4a0c",
                "content_type_hint": "diet"
            }]
        }
    }


class RegisterUserRequest(BaseModel):
    """注册用户请求"""
    gender: Literal["male", "female"] = Field(..., description="性别")
    age: int = Field(..., ge=1, le=150, description="年龄")
    height_cm: float = Field(..., gt=0, le=300, description="身高(厘米)")
    weight_kg: float = Field(..., gt=0, le=500, description="体重(公斤)")
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"] = Field(
        default="moderate",
        description="活动水平"
    )
    name: Optional[str] = Field(None, max_length=100, description="姓名(可选)")


# ==================== SSE 事件数据 ====================

class StatusEventData(BaseModel):
    """状态更新事件数据"""
    request_id: str
    stage: str
    message: str
    progress: int = Field(..., ge=0, le=100)
    timestamp: str


class PartialResultEventData(BaseModel):
    """部分结果事件数据"""
    request_id: str
    type: Literal["food_items", "exercise_items", "health_review", "user_profile"]
    data: Dict[str, Any]
    timestamp: str


class ErrorEventData(BaseModel):
    """错误事件数据"""
    request_id: str
    message: str
    code: str = "INTERNAL_ERROR"
    details: Optional[Dict[str, Any]] = None
    timestamp: str


class CompleteEventData(BaseModel):
    """完成事件数据"""
    request_id: str
    success: bool
    duration_ms: Optional[int] = None
    final_result: Optional[Dict[str, Any]] = None
    timestamp: str


class CancelledEventData(BaseModel):
    """取消事件数据"""
    request_id: str
    message: str = "请求已被取消"
    timestamp: str


# ==================== 响应模型 ====================

class HealthData(BaseModel):
    """健康检查数据"""
    status: str
    timestamp: str
    version: str = "1.0.0"


class DetailedHealthData(BaseModel):
    """详细健康检查数据"""
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    memory: dict
    cpu: dict


class UserProfileResponse(BaseModel):
    """用户档案响应"""
    person_id: str
    name: Optional[str] = None
    gender: str
    age: int
    height_cm: float
    weight_kg: float
    activity_level: str
    bmi: float
    bmr: float
    daily_calorie_needs: float
    health_assessment: str
    created_at: str


class UserListData(BaseModel):
    """用户列表数据"""
    total: int
    users: List[UserProfileResponse]


class DeleteUserData(BaseModel):
    """删除用户数据"""
    person_id: str


class RequestStatusResponse(BaseModel):
    """请求状态响应"""
    request_id: str
    status: str
    current_stage: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


class RequestListResponse(BaseModel):
    """请求列表响应"""
    total: int
    requests: List[RequestStatusResponse]
    stats: Dict[str, Any]


class CancelResponse(BaseModel):
    """取消请求响应"""
    success: bool
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    """错误响应"""
    code: str = "INTERNAL_ERROR"
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
