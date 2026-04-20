import json
from typing import List
from src.graph.state import CalorieState
from src.models import FoodItem, UserProfile
from src.agents.base_agent import BaseAgent
from src.prompts import (
    DIET_ANALYST_SYSTEM_PROMPT,
    DIET_ANALYST_USER_PROMPT,
    DIET_ANALYST_WITH_USER_PROMPT,
)

class DietAnalystAgent(BaseAgent):
    """Diet Analyst Agent - calculates calories and nutrients based on identified foods."""

    def run(self, state: CalorieState) -> dict:
        self.logger.info("Running DietAnalystAgent")

        analyzed_foods = state.get("analyzed_foods") or []
        user_profile = state.get("user_profile")
        text_input = state.get("text_input", "")

        if not analyzed_foods and state["input_type"] == "text_only" and text_input:
            # For pure text diet description, LLM will identify foods directly from text
            foods_json = text_input
        else:
            # Convert existing analyzed foods to JSON for prompt
            foods_data = [
                {
                    "food_name": f.food_name,
                    "estimated_grams": f.estimated_grams,
                    "confidence": f.confidence,
                }
                for f in analyzed_foods
            ]
            # Build prompt based on whether we have user info and whether it's pure text
        if not analyzed_foods and state["input_type"] == "text_only":
            # Pure text input - LLM needs to identify foods from text first
            text = text_input
            if user_profile:
                prompt = DIET_ANALYST_WITH_USER_PROMPT.format(
                    foods_json=text,
                    gender=user_profile.gender,
                    age=user_profile.age,
                    height_cm=user_profile.height_cm,
                    weight_kg=user_profile.weight_kg,
                    bmi=user_profile.bmi,
                    daily_calorie_needs=user_profile.daily_calorie_needs,
                )
            else:
                prompt = DIET_ANALYST_USER_PROMPT.format(foods_json=text)
        else:
            # Already have analyzed foods from image analyst, just calculate nutrition
            foods_data_json = json.dumps({"foods": foods_data}, ensure_ascii=False, indent=2)
            if user_profile:
                prompt = DIET_ANALYST_WITH_USER_PROMPT.format(
                    foods_json=foods_data_json,
                    gender=user_profile.gender,
                    age=user_profile.age,
                    height_cm=user_profile.height_cm,
                    weight_kg=user_profile.weight_kg,
                    bmi=user_profile.bmi,
                    daily_calorie_needs=user_profile.daily_calorie_needs,
                )
            else:
                prompt = DIET_ANALYST_USER_PROMPT.format(foods_json=foods_data_json)

        messages = [
            {"role": "system", "content": DIET_ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        response = self.llm.chat(messages, temperature=0.3)

        try:
            # Clean up markdown code blocks
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            result = json.loads(cleaned)
            foods_data = result.get("foods", [])
            total = result.get("total", {})

            # Update FoodItem objects with nutrition data
            updated_foods: List[FoodItem] = []
            for i, food_data in enumerate(foods_data):
                # If we had existing foods, keep them just update nutrition
                if i < len(analyzed_foods):
                    item = analyzed_foods[i]
                    item.calories = float(food_data.get("calories", 0))
                    item.protein_g = float(food_data.get("protein_g", 0))
                    item.carbs_g = float(food_data.get("carbs_g", 0))
                    item.fat_g = float(food_data.get("fat_g", 0))
                    if "fiber_g" in food_data:
                        item.fiber_g = float(food_data["fiber_g"])
                else:
                    # New item from text analysis
                    item = FoodItem(
                        food_name=food_data.get("food_name", "未知"),
                        estimated_grams=float(food_data.get("estimated_grams", 100)),
                        calories=float(food_data.get("calories", 0)),
                        protein_g=float(food_data.get("protein_g", 0)),
                        carbs_g=float(food_data.get("carbs_g", 0)),
                        fat_g=float(food_data.get("fat_g", 0)),
                        confidence=float(food_data.get("confidence", 1.0)),
                    )
                    if "fiber_g" in food_data:
                        item.fiber_g = float(food_data["fiber_g"])
                updated_foods.append(item)

            self.logger.info(
                f"Diet analysis complete: {len(updated_foods)} foods, "
                f"total {total.get('calories', 0)} calories"
            )

            # For text input, we might need to set analyzed_foods
            return {"analyzed_foods": updated_foods}

        except Exception as e:
            self.logger.error(f"Failed to parse diet analysis: {e}, response={response}")
            return {"error_message": f"饮食分析失败: {str(e)}"}
