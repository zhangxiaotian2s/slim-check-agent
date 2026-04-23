"""
MySQL 数据库模型和存储实现
"""
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config import get_settings
from src.models.user_profile import UserProfile
from src.utils.logger import logger

settings = get_settings()

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class UserProfileModel(Base):
    """用户健康档案数据库模型"""
    __tablename__ = 'tb_user_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    person_id = Column(String(32), unique=True, nullable=False, comment='用户唯一标识')
    name = Column(String(100), comment='用户姓名')
    gender = Column(Enum('male', 'female'), nullable=False, comment='性别')
    age = Column(Integer, nullable=False, comment='年龄')
    height_cm = Column(Float, nullable=False, comment='身高（厘米）')
    weight_kg = Column(Float, nullable=False, comment='体重（公斤）')
    activity_level = Column(
        Enum('sedentary', 'light', 'moderate', 'active', 'very_active'),
        nullable=False,
        default='moderate',
        comment='活动水平'
    )
    bmi = Column(Float, nullable=False, comment='身体质量指数')
    bmr = Column(Float, nullable=False, comment='基础代谢率')
    daily_calorie_needs = Column(Float, nullable=False, comment='每日所需热量')
    health_assessment = Column(String(200), nullable=False, comment='健康评估')
    created_at = Column(DateTime, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, nullable=False, comment='更新时间')


@contextmanager
def get_db_session():
    """获取数据库会话的上下文管理器"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


class MySQLUserStorage:
    """MySQL 数据库用户存储实现"""

    def __init__(self):
        self.engine = engine

    def _model_to_profile(self, model: UserProfileModel) -> UserProfile:
        """将数据库模型转换为 UserProfile 对象"""
        return UserProfile(
            person_id=model.person_id,
            name=model.name,
            gender=model.gender,
            age=model.age,
            height_cm=model.height_cm,
            weight_kg=model.weight_kg,
            activity_level=model.activity_level,
            bmi=model.bmi,
            bmr=model.bmr,
            daily_calorie_needs=model.daily_calorie_needs,
            health_assessment=model.health_assessment,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _profile_to_model(self, profile: UserProfile) -> UserProfileModel:
        """将 UserProfile 对象转换为数据库模型"""
        return UserProfileModel(
            person_id=profile.person_id,
            name=profile.name,
            gender=profile.gender,
            age=profile.age,
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg,
            activity_level=profile.activity_level,
            bmi=profile.bmi,
            bmr=profile.bmr,
            daily_calorie_needs=profile.daily_calorie_needs,
            health_assessment=profile.health_assessment,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

    def save(self, profile: UserProfile) -> None:
        """保存或更新用户档案"""
        with get_db_session() as session:
            existing = session.query(UserProfileModel).filter_by(person_id=profile.person_id).first()

            if existing:
                # 更新现有记录
                existing.name = profile.name
                existing.gender = profile.gender
                existing.age = profile.age
                existing.height_cm = profile.height_cm
                existing.weight_kg = profile.weight_kg
                existing.activity_level = profile.activity_level
                existing.bmi = profile.bmi
                existing.bmr = profile.bmr
                existing.daily_calorie_needs = profile.daily_calorie_needs
                existing.health_assessment = profile.health_assessment
                existing.updated_at = datetime.now()
                logger.info(f"Updated user profile: {profile.person_id}")
            else:
                # 创建新记录
                model = self._profile_to_model(profile)
                session.add(model)
                logger.info(f"Saved new user profile: {profile.person_id}")

    def load(self, person_id: str) -> Optional[UserProfile]:
        """加载用户档案"""
        with get_db_session() as session:
            model = session.query(UserProfileModel).filter_by(person_id=person_id).first()
            if model:
                # 需要将实例分离出session，避免detached错误
                session.expunge(model)
                return self._model_to_profile(model)
            logger.warning(f"User profile not found: {person_id}")
            return None

    def delete(self, person_id: str) -> bool:
        """删除用户档案"""
        with get_db_session() as session:
            deleted_count = session.query(UserProfileModel).filter_by(person_id=person_id).delete()
            if deleted_count > 0:
                logger.info(f"Deleted user profile: {person_id}")
                return True
            logger.warning(f"User profile not found for deletion: {person_id}")
            return False

    def list_all(self) -> List[UserProfile]:
        """列出所有用户档案"""
        with get_db_session() as session:
            models = session.query(UserProfileModel).order_by(UserProfileModel.created_at.desc()).all()
            # 将所有实例分离出session
            for model in models:
                session.expunge(model)
            return [self._model_to_profile(model) for model in models]

    def count(self) -> int:
        """统计用户数量"""
        with get_db_session() as session:
            return session.query(UserProfileModel).count()

    def exists(self, person_id: str) -> bool:
        """检查用户是否存在"""
        with get_db_session() as session:
            return session.query(UserProfileModel).filter_by(person_id=person_id).first() is not None


def init_database():
    """初始化数据库（创建表）"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def test_database_connection() -> bool:
    """测试数据库连接"""
    try:
        with get_db_session() as session:
            # 执行简单查询测试连接
            session.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
