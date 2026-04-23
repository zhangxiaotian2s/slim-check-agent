"""
用户管理接口
用户注册、查询、列表
"""
from typing import List
from datetime import datetime

from fastapi import APIRouter

from src.models import UserProfile
from src.models.api_models import (
    RegisterUserRequest,
    UserProfileResponse,
    UserListData,
    DeleteUserData,
    ApiResponse,
)
from src.storage import get_user_storage
from src.utils.logger import logger

router = APIRouter()


def _profile_to_response(profile: UserProfile) -> UserProfileResponse:
    """将 UserProfile 转换为响应格式"""
    return UserProfileResponse(
        person_id=profile.person_id,
        name=profile.name,
        gender=profile.gender,
        age=profile.age,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        activity_level=profile.activity_level,
        bmi=round(profile.bmi, 2),
        bmr=round(profile.bmr, 2),
        daily_calorie_needs=round(profile.daily_calorie_needs, 2),
        health_assessment=profile.health_assessment,
        created_at=profile.created_at.isoformat() if hasattr(profile, 'created_at') and profile.created_at else datetime.now().isoformat(),
    )


@router.post("/users/register", summary="注册用户", response_model=ApiResponse[UserProfileResponse])
async def register_user(request: RegisterUserRequest):
    """
    注册新用户，创建个人健康档案

    ## 请求参数

    - **gender**: 性别: `male` / `female`
    - **age**: 年龄
    - **height_cm**: 身高 (厘米)
    - **weight_kg**: 体重 (公斤)
    - **activity_level**: 活动水平:
        - `sedentary`: 久坐（很少运动）
        - `light`: 轻度运动（每周1-3次）
        - `moderate`: 中度运动（每周3-5次）
        - `active`: 活跃运动（每周6-7次）
        - `very_active`: 非常活跃（每日高强度运动）
    - **name**: 姓名 (可选)

    ## 返回

    创建成功的用户档案，包含：
    - BMI
    - BMR (基础代谢率)
    - 每日所需卡路里
    - 健康评估
    """
    try:
        user_profile = UserProfile.create(
            gender=request.gender,
            age=request.age,
            height_cm=request.height_cm,
            weight_kg=request.weight_kg,
            activity_level=request.activity_level,
            name=request.name
        )

        storage = get_user_storage()
        storage.save(user_profile)

        logger.info(f"User registered: {user_profile.person_id}")

        return ApiResponse[UserProfileResponse](
            code=0,
            data=_profile_to_response(user_profile),
            msg="用户注册成功"
        )

    except Exception as e:
        logger.error(f"Failed to register user: {str(e)}")
        return ApiResponse[UserProfileResponse](
            code=-1,
            data=None,
            msg=f"注册失败: {str(e)}"
        )


@router.get("/users/{person_id}", summary="查询用户档案", response_model=ApiResponse[UserProfileResponse])
async def get_user(person_id: str):
    """
    查询指定用户的健康档案

    - **person_id**: 用户 ID
    """
    storage = get_user_storage()
    profile = storage.load(person_id)

    if not profile:
        return ApiResponse[UserProfileResponse](
            code=-1,
            data=None,
            msg="用户不存在"
        )

    return ApiResponse[UserProfileResponse](
        code=0,
        data=_profile_to_response(profile),
        msg="查询成功"
    )


@router.get("/users", summary="列出所有用户", response_model=ApiResponse[UserListData])
async def list_users():
    """
    列出所有已注册的用户完整信息
    """
    storage = get_user_storage()
    profiles = storage.list_all()

    users_data = [_profile_to_response(p) for p in profiles]
    data = UserListData(
        total=len(users_data),
        users=users_data
    )

    return ApiResponse[UserListData](
        code=0,
        data=data,
        msg="获取用户列表成功"
    )


@router.delete("/users/{person_id}", summary="删除用户", response_model=ApiResponse[DeleteUserData])
async def delete_user(person_id: str):
    """
    删除指定用户

    - **person_id**: 要删除的用户 ID
    """
    storage = get_user_storage()

    profile = storage.load(person_id)
    if not profile:
        return ApiResponse[DeleteUserData](
            code=-1,
            data=None,
            msg="用户不存在"
        )

    storage.delete(person_id)

    logger.info(f"User deleted: {person_id}")

    data = DeleteUserData(person_id=person_id)
    return ApiResponse[DeleteUserData](
        code=0,
        data=data,
        msg="用户已删除"
    )
