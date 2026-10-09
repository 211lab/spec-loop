"""The single injectable LLM seam."""

from __future__ import annotations

from typing import Protocol

import litellm


class LLMClient(Protocol):
    def complete(self, *, system: str, user: str, reasoning_effort: str) -> str: ...


class LiteLLMClient:
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        session_id: str | None = None,
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.session_id = session_id

    def complete(self, *, system: str, user: str, reasoning_effort: str) -> str:
        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            api_key=self.api_key,
            extra_body={
                "reasoning": {"effort": reasoning_effort},
                "session_id": self.session_id,
            },
        )
        return response.choices[0].message.content
