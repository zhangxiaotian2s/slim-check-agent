import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    openai_base_url: str
    openai_api_key: str
    openai_model: str

def load_config() -> Config:
    """Load configuration from .env file."""
    load_dotenv()

    return Config(
        openai_base_url=os.getenv("OPENAI_BASE_URL", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", ""),
    )

config = load_config()
