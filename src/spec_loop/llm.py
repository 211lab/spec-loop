"""The single injectable LLM seam."""

from __future__ import annotations

from typing import Protocol

import litellm


class LLMClient(Protocol):
    def complete(self, *, system: str, user: str) -> str: ...


class LiteLLMClient:
    def __init__(self, model: str, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key

    def complete(self, *, system: str, user: str) -> str:
        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            api_key=self.api_key,
        )
        return response.choices[0].message.content
