from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Literal, Optional
import uuid
import json
import os

from src.utils.logger import logger

ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]

@dataclass
class UserProfile:
    person_id: str
    name: Optional[str]
    gender: Literal["male", "female"]
    age: int
    height_cm: float
    weight_kg: float
    activity_level: ActivityLevel
    bmi: float
    bmr: float
    daily_calorie_needs: float
    health_assessment: str
    created_at: datetime
    updated_at: datetime

    def to_dict(self):
        data = asdict(self)
        # Convert datetime to ISO string for JSON serialization
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        # Convert string dates back to datetime
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)

    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> float:
        """Calculate BMI."""
        height_m = height_cm / 100
        return weight_kg / (height_m * height_m)

    @staticmethod
    def calculate_bmr(gender: Literal["male", "female"], weight_kg: float, height_cm: float, age: int) -> float:
        """Calculate BMR using Mifflin-St Jeor equation."""
        if gender == "male":
            return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
        else:
            return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    @staticmethod
    def calculate_daily_calorie_needs(bmr: float, activity_level: ActivityLevel) -> float:
        """Calculate daily calorie needs based on activity level."""
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9,
        }
        return bmr * activity_multipliers[activity_level]

    @classmethod
    def create(
        cls,
        gender: Literal["male", "female"],
        age: int,
        height_cm: float,
        weight_kg: float,
        activity_level: ActivityLevel = "moderate",
        name: Optional[str] = None,
    ) -> "UserProfile":
        """Create a new UserProfile with calculated health metrics."""
        person_id = str(uuid.uuid4())[:8]  # Short UUID for usability
        now = datetime.now()

        bmi = cls.calculate_bmi(weight_kg, height_cm)
        bmr = cls.calculate_bmr(gender, weight_kg, height_cm, age)
        daily_calorie_needs = cls.calculate_daily_calorie_needs(bmr, activity_level)

        # Generate health assessment based on BMI
        if bmi < 18.5:
            health_assessment = "体重偏低，建议适当增加热量摄入"
        elif 18.5 <= bmi < 24:
            health_assessment = "体重在正常范围"
        elif 24 <= bmi < 28:
            health_assessment = "超重，建议控制热量摄入并增加运动"
        else:
            health_assessment = "肥胖，建议在专业指导下进行减重"

        profile = cls(
            person_id=person_id,
            name=name,
            gender=gender,
            age=age,
            height_cm=height_cm,
            weight_kg=weight_kg,
            activity_level=activity_level,
            bmi=round(bmi, 2),
            bmr=round(bmr, 2),
            daily_calorie_needs=round(daily_calorie_needs, 2),
            health_assessment=health_assessment,
            created_at=now,
            updated_at=now,
        )

        logger.info(f"Created new user profile: person_id={person_id}, BMI={bmi:.2f}, BMR={bmr:.2f}")
        return profile
