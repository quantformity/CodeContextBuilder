import httpx
from .base import BaseLLMProvider
from ..config import config
from typing import Optional

class OpenAIProvider(BaseLLMProvider):
    def summarize(self, context: str, symbol_code: str) -> Optional[str]:
        prompt = f"Summarize this code from {context}. Intent only, 1-2 sentences. No preambles.\n\nCode:\n{symbol_code}"
        base_url = config.llm.base_url or "https://api.openai.com/v1"
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{base_url}/chat/completions",
                    json={
                        "model": config.llm.model,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    headers={"Authorization": f"Bearer {config.llm.api_key}"}
                )
                return response.json()["choices"][0]["message"]["content"].strip()
        except:
            return None
