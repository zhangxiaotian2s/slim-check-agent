import json
from typing import Optional, List
from src.graph.state import CalorieState
from src.models import UserProfile
from src.agents.base_agent import BaseAgent
from src.storage import get_user_storage
from src.prompts import (
    HEALTH_MANAGER_SYSTEM_PROMPT,
    HEALTH_MANAGER_EXTRACT_PROMPT,
)

class HealthManagerAgent(BaseAgent):
    """Health Manager Agent - collects and manages user health information."""

    def check_info(self, state: CalorieState) -> dict:
        """Check if user registration info is complete, extract from text."""
        self.logger.info("Checking user health information")

        text_input = state.get("text_input")
        if not text_input:
            self.logger.error("No text provided for user registration")
            return {
                "requires_user_input": True,
                "missing_fields": ["性别", "年龄", "身高", "体重"],
            }

        messages = [
            {"role": "system", "content": HEALTH_MANAGER_SYSTEM_PROMPT},
            {"role": "user", "content": HEALTH_MANAGER_EXTRACT_PROMPT.format(text=text_input)},
        ]

        response = self.llm.chat(messages, temperature=0.1)

        try:
            # Clean up markdown code blocks
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            result = json.loads(cleaned)
            extracted = result.get("extracted", {})
            missing_fields = result.get("missing_fields", [])
            is_complete = result.get("is_complete", False)

            # Map missing field names to Chinese for user
            field_mapping = {
                "gender": "性别",
                "age": "年龄",
                "height_cm": "身高(厘米)",
                "weight_kg": "体重(公斤)",
            }
            missing_chinese = [field_mapping.get(f, f) for f in missing_fields]

            extracted_gender = extracted.get("gender")
            extracted_age = extracted.get("age")
            extracted_height = extracted.get("height_cm")
            extracted_weight = extracted.get("weight_kg")
            extracted_name = extracted.get("name")

            # Build temporary user profile with what we have
            # If complete, we'll calculate metrics in save_profile
            profile: Optional[UserProfile] = None

            if is_complete:
                # Gender needs to be normalized
                if extracted_gender in ["男", "male", "m", "男性"]:
                    extracted_gender = "male"
                elif extracted_gender in ["女", "female", "f", "女性"]:
                    extracted_gender = "female"

                try:
                    profile = UserProfile.create(
                        gender=extracted_gender,
                        age=int(extracted_age),
                        height_cm=float(extracted_height),
                        weight_kg=float(extracted_weight),
                        name=extracted_name if extracted_name else None,
                    )
                    self.logger.info(f"User info complete, created profile: {profile.person_id}")
                    return {
                        "user_profile": profile,
                        "requires_user_input": False,
                        "missing_fields": [],
                    }
                except Exception as e:
                    self.logger.error(f"Failed to create user profile: {e}")
                    return {
                        "requires_user_input": True,
                        "missing_fields": ["无法解析信息，请重新提供性别、年龄、身高、体重"],
                    }
            else:
                self.logger.info(f"User info incomplete, missing: {missing_chinese}")
                return {
                    "requires_user_input": True,
                    "missing_fields": missing_chinese,
                }

        except Exception as e:
            self.logger.error(f"Failed to parse user info extraction: {e}, response={response}")
            return {
                "requires_user_input": True,
                "missing_fields": ["无法解析信息，请提供性别、年龄、身高、体重"],
            }

    def save_profile(self, state: CalorieState) -> dict:
        """Save the complete user profile to storage."""
        profile = state.get("user_profile")
        if not profile:
            self.logger.error("No user profile to save")
            return {"error_message": "没有用户信息可保存"}

        storage = get_user_storage()
        storage.save(profile)
        self.logger.info(f"User profile saved: {profile.person_id}")

        return {"user_profile": profile}
