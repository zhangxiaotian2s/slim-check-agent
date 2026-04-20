from dataclasses import dataclass, asdict
from typing import Literal, Optional

Intensity = Literal["low", "moderate", "high"]

@dataclass
class ExerciseItem:
    """Analyzed exercise item."""
    exercise_type: str
    duration_minutes: float
    intensity: Intensity
    calories_burned: float
    notes: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ExerciseItem":
        return cls(**data)
