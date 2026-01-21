from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx


class LLMClient:
    api_key: str | None
    base_url: str
    model: str

    def __init__(self, api_key: str | None = None, model: str = "MiniMax-M2.1"):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.base_url = "https://api.minimax.chat/v1"
        self.model = model

    async def acomplete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        response_format: dict[str, object] | None = None,
    ) -> str:
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY is not set")

        payload: dict[str, object] = {
            "model": model or self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if response_format is not None:
            payload["response_format"] = response_format

        headers: dict[str, str] = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions", json=payload, headers=headers
            )
            _ = response.raise_for_status()
            data: Any = response.json()

        parsed = self._parse_response_data(data)
        return parsed

    def _parse_response_data(self, data: object) -> str:
        if not isinstance(data, dict):
            return str(data)

        choices_value = data.get("choices")
        if isinstance(choices_value, list) and choices_value:
            first = choices_value[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if content is not None:
                        return str(content)
                text = first.get("text")
                if text is not None:
                    return str(text)

        if "text" in data:
            return str(data["text"])

        return str(data)

    def complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        response_format: dict[str, object] | None = None,
    ) -> str:
        return asyncio.run(
            self.acomplete(
                prompt=prompt,
                model=model,
                temperature=temperature,
                response_format=response_format,
            )
        )
