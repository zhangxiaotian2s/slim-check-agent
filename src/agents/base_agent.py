from abc import ABC
from src.utils.llm_client import LLMClient, get_llm_client
from src.utils.logger import logger

class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self):
        self.llm: LLMClient = get_llm_client()
        self.logger = logger
