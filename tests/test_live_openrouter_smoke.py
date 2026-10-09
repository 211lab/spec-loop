import os
import unittest

from spec_loop.llm import LiteLLMClient


def _truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() in {"1", "true", "yes", "on"}


@unittest.skipUnless(
    os.environ.get("OPENROUTER_API_KEY")
    and _truthy(os.environ.get("SPEC_LOOP_LIVE_SMOKE")),
    "live smoke disabled (set OPENROUTER_API_KEY and SPEC_LOOP_LIVE_SMOKE=1)",
)
class LiveOpenRouterSmokeTest(unittest.TestCase):
    def test_single_word_pong(self):
        model = os.environ.get(
            "SPEC_LOOP_SMOKE_MODEL", "openrouter/anthropic/claude-haiku-4-5"
        )
        client = LiteLLMClient(
            model=model,
            api_key=os.environ["OPENROUTER_API_KEY"],
            session_id="live-smoke",
        )
        text = client.complete(
            system="You are a terse assistant.",
            user="Reply with the single word: pong",
            reasoning_effort="medium",
        )
        self.assertTrue(text and text.strip())
