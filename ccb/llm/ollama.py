import httpx
from .base import BaseLLMProvider
from ..config import config
from typing import Optional

class OllamaProvider(BaseLLMProvider):
    def summarize(self, context: str, symbol_code: str) -> Optional[str]:
        prompt = f"Summarize this code from {context}. Intent only, 1-2 sentences. No preambles.\n\nCode:\n{symbol_code}"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{config.llm.base_url}/api/generate",
                    json={
                        "model": config.llm.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                return response.json().get("response", "").strip()
        except:
            return None
