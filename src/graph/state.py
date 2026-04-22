from typing import TypedDict, Optional, List, Literal
from src.models import UserProfile, FoodItem, ExerciseItem, AnalysisResult

InputType = Literal["image", "image_with_text", "text_only"]
ContentType = Literal["diet", "exercise", "user_registration"]

class CalorieState(TypedDict):
    """State for the calorie analysis workflow."""

    # Input information
    input_type: InputType
    image_data: Optional[bytes]
    image_base64: Optional[str]
    text_input: Optional[str]
    person_id: Optional[str]

    # Intermediate state
    user_profile: Optional[UserProfile]
    content_type: Optional[ContentType]
    analyzed_foods: Optional[List[FoodItem]]
    analyzed_exercise: Optional[List[ExerciseItem]]
    health_review: Optional[dict]  # Health review from HealthReviewAgent

    # Classification flags
    _has_diet: bool
    _has_exercise: bool
    _is_user_registration: bool

    # Output
    analysis_result: Optional[AnalysisResult]
    requires_user_input: bool
    missing_fields: Optional[List[str]]
    error_message: Optional[str]
