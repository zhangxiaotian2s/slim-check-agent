import json
from typing import List
from src.graph.state import CalorieState
from src.agents.base_agent import BaseAgent
from src.prompts import (
    HEALTH_REVIEW_SYSTEM_PROMPT,
    HEALTH_REVIEW_DIET_PROMPT,
    HEALTH_REVIEW_DIET_WITH_USER_PROMPT,
    HEALTH_REVIEW_EXERCISE_PROMPT,
    HEALTH_REVIEW_EXERCISE_WITH_USER_PROMPT,
    HEALTH_REVIEW_BOTH_PROMPT,
    HEALTH_REVIEW_BOTH_WITH_USER_PROMPT,
)


class HealthReviewAgent(BaseAgent):
    """Health Review Agent - provides health review and personalized suggestions
    based on diet and/or exercise analysis results."""

    def run(self, state: CalorieState) -> dict:
        """Generate health review based on analysis results."""
        self.logger.info("Running HealthReviewAgent")

        analyzed_foods = state.get("analyzed_foods") or []
        analyzed_exercises = state.get("analyzed_exercise") or []
        user_profile = state.get("user_profile")

        has_diet = len(analyzed_foods) > 0
        has_exercise = len(analyzed_exercises) > 0

        if not has_diet and not has_exercise:
            self.logger.warning("No diet or exercise data to review")
            return {"health_review": None}

        # Build summary strings for prompt
        foods_summary = ""
        if has_diet:
            foods_summary = "\n".join([
                f"- {f.food_name}: {f.estimated_grams:.0f}g, {f.calories:.0f} 大卡"
                for f in analyzed_foods
            ])

        exercises_summary = ""
        if has_exercise:
            exercises_summary = "\n".join([
                f"- {e.exercise_type}: {e.duration_minutes:.0f}分钟, {e.calories_burned:.0f} 大卡"
                for e in analyzed_exercises
            ])

        # Calculate totals
        total_calories = sum(f.calories for f in analyzed_foods) if has_diet else 0
        total_protein = sum(f.protein_g for f in analyzed_foods) if has_diet else 0
        total_carbs = sum(f.carbs_g for f in analyzed_foods) if has_diet else 0
        total_fat = sum(f.fat_g for f in analyzed_foods) if has_diet else 0
        total_burned = sum(e.calories_burned for e in analyzed_exercises) if has_exercise else 0
        net_calories = total_calories - total_burned

        # Select appropriate prompt
        if has_diet and has_exercise:
            if user_profile:
                prompt = HEALTH_REVIEW_BOTH_WITH_USER_PROMPT.format(
                    foods_summary=foods_summary,
                    exercises_summary=exercises_summary,
                    total_calories=total_calories,
                    total_burned=total_burned,
                    net_calories=net_calories,
                    gender=user_profile.gender,
                    age=user_profile.age,
                    height_cm=user_profile.height_cm,
                    weight_kg=user_profile.weight_kg,
                    bmi=user_profile.bmi,
                    daily_calorie_needs=user_profile.daily_calorie_needs,
                    health_assessment=user_profile.health_assessment,
                )
            else:
                prompt = HEALTH_REVIEW_BOTH_PROMPT.format(
                    foods_summary=foods_summary,
                    exercises_summary=exercises_summary,
                    total_calories=total_calories,
                    total_burned=total_burned,
                    net_calories=net_calories,
                )
        elif has_diet:
            if user_profile:
                prompt = HEALTH_REVIEW_DIET_WITH_USER_PROMPT.format(
                    foods_summary=foods_summary,
                    total_calories=total_calories,
                    total_protein=total_protein,
                    total_carbs=total_carbs,
                    total_fat=total_fat,
                    gender=user_profile.gender,
                    age=user_profile.age,
                    height_cm=user_profile.height_cm,
                    weight_kg=user_profile.weight_kg,
                    bmi=user_profile.bmi,
                    daily_calorie_needs=user_profile.daily_calorie_needs,
                    health_assessment=user_profile.health_assessment,
                )
            else:
                prompt = HEALTH_REVIEW_DIET_PROMPT.format(
                    foods_summary=foods_summary,
                    total_calories=total_calories,
                    total_protein=total_protein,
                    total_carbs=total_carbs,
                    total_fat=total_fat,
                )
        else:  # exercise only
            if user_profile:
                prompt = HEALTH_REVIEW_EXERCISE_WITH_USER_PROMPT.format(
                    exercises_summary=exercises_summary,
                    total_burned=total_burned,
                    gender=user_profile.gender,
                    age=user_profile.age,
                    height_cm=user_profile.height_cm,
                    weight_kg=user_profile.weight_kg,
                    bmi=user_profile.bmi,
                    daily_calorie_needs=user_profile.daily_calorie_needs,
                    health_assessment=user_profile.health_assessment,
                )
            else:
                prompt = HEALTH_REVIEW_EXERCISE_PROMPT.format(
                    exercises_summary=exercises_summary,
                    total_burned=total_burned,
                )

        messages = [
            {"role": "system", "content": HEALTH_REVIEW_SYSTEM_PROMPT},
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
            review_points = result.get("review_points", [])
            overall_assessment = result.get("overall_assessment", "")

            self.logger.info(f"Health review generated: {len(review_points)} points")

            # 计算净卡路里和蛋白质数据（用于前端显示）
            net_calories = total_calories - total_burned
            protein_goal = 0
            if user_profile and user_profile.weight_kg:
                # 减重目标：每公斤体重 1.6-2.2g 蛋白质
                protein_goal = int(user_profile.weight_kg * 1.8)

            return {
                "health_review": {
                    # 匹配前端字段名
                    "net_calories": net_calories,
                    "total_calories_in": total_calories,
                    "total_calories_out": total_burned,
                    "protein_current": total_protein,
                    "protein_goal": protein_goal,
                    "overall_assessment": overall_assessment,
                    "recommendations": review_points,  # review_points -> recommendations
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to parse health review: {e}, response={response}")
            return {"health_review": None}