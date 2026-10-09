"""The bounded draft/critique/revise loop."""

from __future__ import annotations

from dataclasses import dataclass

from .llm import LLMClient
from .prompts import (
    critique_is_clean,
    critique_prompt,
    draft_prompt,
    revise_prompt,
)


@dataclass(frozen=True)
class SpecResult:
    intent: str
    body: str
    iterations: int
    clean: bool
    model: str
    authoring_effort: str
    loop_effort: str
    session_id: str


class SpecLoop:
    def __init__(
        self,
        client: LLMClient,
        model: str,
        max_iterations: int = 3,
        authoring_effort: str = "max",
        loop_effort: str = "medium",
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        self.client = client
        self.model = model
        self.max_iterations = max_iterations
        self.authoring_effort = authoring_effort
        self.loop_effort = loop_effort

    def run(self, intent: str) -> SpecResult:
        system, user = draft_prompt(intent)
        body = self.client.complete(
            system=system, user=user, reasoning_effort=self.authoring_effort
        )

        iterations = 0
        clean = False
        for _ in range(self.max_iterations):
            system, user = critique_prompt(intent, body)
            critique = self.client.complete(
                system=system, user=user, reasoning_effort=self.loop_effort
            )
            if critique_is_clean(critique):
                clean = True
                break
            system, user = revise_prompt(intent, body, critique)
            body = self.client.complete(
                system=system, user=user, reasoning_effort=self.authoring_effort
            )
            iterations += 1

        return SpecResult(
            intent=intent,
            body=body,
            iterations=iterations,
            clean=clean,
            model=self.model,
            authoring_effort=self.authoring_effort,
            loop_effort=self.loop_effort,
            session_id=getattr(self.client, "session_id", ""),
        )
