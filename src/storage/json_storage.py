import json
import os
from typing import Optional
from src.models import UserProfile
from src.utils.logger import logger

# Get absolute path relative to this file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../../data/users"))

class JSONUserStorage:
    """JSON file storage for user profiles."""

    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _get_user_path(self, person_id: str) -> str:
        return os.path.join(self.data_dir, f"{person_id}.json")

    def save(self, user_profile: UserProfile) -> None:
        """Save user profile to JSON file."""
        file_path = self._get_user_path(user_profile.person_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(user_profile.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"User profile saved: {user_profile.person_id} -> {file_path}")

    def load(self, person_id: str) -> Optional[UserProfile]:
        """Load user profile from JSON file."""
        file_path = self._get_user_path(person_id)
        if not os.path.exists(file_path):
            logger.warning(f"User profile not found: {person_id}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            profile = UserProfile.from_dict(data)
            logger.debug(f"User profile loaded: {person_id}")
            return profile
        except Exception as e:
            logger.error(f"Failed to load user profile {person_id}: {str(e)}")
            return None

    def delete(self, person_id: str) -> bool:
        """Delete a user profile."""
        file_path = self._get_user_path(person_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"User profile deleted: {person_id}")
            return True
        return False

    def list_users(self) -> list[str]:
        """List all saved user IDs."""
        if not os.path.exists(self.data_dir):
            return []
        users = []
        for f in os.listdir(self.data_dir):
            if f.endswith(".json") and not f.startswith("."):
                users.append(f[:-5])  # Remove .json extension
        return users

    def load_all(self) -> list[UserProfile]:
        """Load all user profiles."""
        profiles = []
        for person_id in self.list_users():
            profile = self.load(person_id)
            if profile:
                profiles.append(profile)
        # Sort by created_at descending (newest first)
        profiles.sort(key=lambda p: p.created_at if hasattr(p, 'created_at') and p.created_at else "", reverse=True)
        return profiles

# Global singleton instance
_storage: Optional[JSONUserStorage] = None

def get_user_storage() -> JSONUserStorage:
    """Get singleton storage instance."""
    global _storage
    if _storage is None:
        _storage = JSONUserStorage()
    return _storage
