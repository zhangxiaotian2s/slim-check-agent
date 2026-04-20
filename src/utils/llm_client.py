from typing import List, Optional, Union
from openai import OpenAI
from config import config
from src.utils.logger import logger

class LLMClient:
    """Wrapper for OpenAI-compatible LLM client (works with Volcano Engine Doubao)."""

    def __init__(self):
        self.client = OpenAI(
            base_url=config.openai_base_url,
            api_key=config.openai_api_key,
        )
        self.model = config.openai_model
        logger.info(f"LLM client initialized with model: {self.model}")

    def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send chat completion request and return response content."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            preview = content[:100] if content else ""
            logger.debug(f"LLM response received: {preview}...")
            return content.strip() if content else ""
        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}")
            raise

    def vision_chat(
        self,
        prompt: str,
        image_base64: str,
        temperature: float = 0.7,
    ) -> str:
        """Chat with vision model."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            content = response.choices[0].message.content
            preview = content[:100] if content else ""
            logger.debug(f"Vision LLM response received: {preview}...")
            return content.strip() if content else ""
        except Exception as e:
            logger.error(f"Vision LLM request failed: {str(e)}")
            raise

# Global singleton instance
_llm_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
