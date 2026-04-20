import json
from typing import List
from src.graph.state import CalorieState
from src.models import FoodItem
from src.agents.base_agent import BaseAgent
from src.prompts import (
    IMAGE_ANALYST_SYSTEM_PROMPT,
    IMAGE_ANALYST_USER_PROMPT,
    IMAGE_ANALYST_WITH_TEXT_PROMPT,
)

class ImageAnalystAgent(BaseAgent):
    """Image Analyst Agent - analyzes food image to identify foods and estimate portion sizes."""

    def run(self, state: CalorieState) -> dict:
        self.logger.info("Running ImageAnalystAgent")

        image_base64 = state.get("image_base64")
        text_input = state.get("text_input")

        if not image_base64:
            self.logger.error("No image data provided")
            return {"error_message": "没有提供图片数据"}

        # Build prompt
        if text_input and text_input.strip():
            prompt = IMAGE_ANALYST_WITH_TEXT_PROMPT.format(text=text_input.strip())
        else:
            prompt = IMAGE_ANALYST_USER_PROMPT

        # Call vision LLM
        response = self.llm.vision_chat(
            prompt=IMAGE_ANALYST_SYSTEM_PROMPT + "\n\n" + prompt,
            image_base64=image_base64,
            temperature=0.3,
        )

        # Parse response
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

            # Convert to FoodItem objects (nutrients will be added by diet analyst)
            analyzed_foods: List[FoodItem] = []
            for food in foods_data:
                item = FoodItem(
                    food_name=food.get("food_name", "未知食物"),
                    estimated_grams=float(food.get("estimated_grams", 100)),
                    calories=0,  # Will be calculated by diet analyst
                    protein_g=0,
                    carbs_g=0,
                    fat_g=0,
                    confidence=float(food.get("confidence", 1.0)),
                )
                analyzed_foods.append(item)

            self.logger.info(f"Identified {len(analyzed_foods)} food items from image")
            return {"analyzed_foods": analyzed_foods}

        except Exception as e:
            self.logger.error(f"Failed to parse image analysis result: {e}, response={response}")
            return {"error_message": f"图片分析失败: {str(e)}"}
