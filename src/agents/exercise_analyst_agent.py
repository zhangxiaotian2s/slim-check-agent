import json
from typing import List
from src.graph.state import CalorieState
from src.models import ExerciseItem
from src.agents.base_agent import BaseAgent
from src.prompts import (
    EXERCISE_ANALYST_SYSTEM_PROMPT,
    EXERCISE_ANALYST_USER_PROMPT,
    EXERCISE_ANALYST_WITH_USER_PROMPT,
)

class ExerciseAnalystAgent(BaseAgent):
    """Exercise Analyst Agent - calculates calories burned based on exercise description."""

    def run(self, state: CalorieState) -> dict:
        self.logger.info("Running ExerciseAnalystAgent")

        text_input = state.get("text_input")
        user_profile = state.get("user_profile")

        if not text_input:
            self.logger.error("No text description provided")
            return {"error_message": "没有提供运动描述"}

        # Build prompt based on whether we have user info
        if user_profile:
            prompt = EXERCISE_ANALYST_WITH_USER_PROMPT.format(
                text=text_input.strip(),
                gender=user_profile.gender,
                age=user_profile.age,
                height_cm=user_profile.height_cm,
                weight_kg=user_profile.weight_kg,
                bmi=user_profile.bmi,
                daily_calorie_needs=user_profile.daily_calorie_needs,
            )
        else:
            prompt = EXERCISE_ANALYST_USER_PROMPT.format(text=text_input.strip())

        messages = [
            {"role": "system", "content": EXERCISE_ANALYST_SYSTEM_PROMPT},
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
            exercises_data = result.get("exercises", [])
            total = result.get("total", {})

            analyzed_exercise: List[ExerciseItem] = []
            for ex in exercises_data:
                item = ExerciseItem(
                    exercise_type=ex.get("exercise_type", "未知运动"),
                    duration_minutes=float(ex.get("duration_minutes", 0)),
                    intensity=ex.get("intensity", "moderate"),
                    calories_burned=float(ex.get("calories_burned", 0)),
                    notes=ex.get("notes"),
                )
                analyzed_exercise.append(item)

            self.logger.info(
                f"Exercise analysis complete: {len(analyzed_exercise)} exercises, "
                f"total {total.get('calories_burned', 0)} calories burned"
            )

            return {"analyzed_exercise": analyzed_exercise}

        except Exception as e:
            self.logger.error(f"Failed to parse exercise analysis: {e}, response={response}")
            return {"error_message": f"运动分析失败: {str(e)}"}
