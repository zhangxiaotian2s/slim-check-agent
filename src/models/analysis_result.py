from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Literal, Optional, List
from .user_profile import UserProfile
from .food_item import FoodItem
from .exercise_item import ExerciseItem

RequestType = Literal["diet_analysis", "exercise_analysis", "user_registration"]

@dataclass
class AnalysisResult:
    """Final analysis result."""
    request_type: RequestType
    timestamp: datetime
    person_id: Optional[str]
    user_profile: Optional[UserProfile]

    # Diet analysis
    total_calories_intake: Optional[float] = None
    total_protein: Optional[float] = None
    total_carbs: Optional[float] = None
    total_fat: Optional[float] = None
    food_items: Optional[List[FoodItem]] = None

    # Exercise analysis
    total_calories_burned: Optional[float] = None
    exercise_items: Optional[List[ExerciseItem]] = None

    # Recommendations
    recommendations: List[str] = None
    summary: str = ""

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []

    def to_dict(self):
        result = asdict(self)
        # Convert datetime to ISO string
        result["timestamp"] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "AnalysisResult":
        from .user_profile import UserProfile

        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if data.get("user_profile"):
            data["user_profile"] = UserProfile.from_dict(data["user_profile"])
        if data.get("food_items"):
            data["food_items"] = [FoodItem.from_dict(item) for item in data["food_items"]]
        if data.get("exercise_items"):
            data["exercise_items"] = [ExerciseItem.from_dict(item) for item in data["exercise_items"]]
        return cls(**data)
