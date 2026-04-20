from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class FoodItem:
    """Identified food item from image or text."""
    food_name: str
    estimated_grams: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: Optional[float] = None
    confidence: float = 1.0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FoodItem":
        return cls(**data)
