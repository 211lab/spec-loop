from types import SimpleNamespace

import litellm

from spec_loop.llm import LiteLLMClient


def test_litellm_client_passes_model_and_key(monkeypatch):
    captured = {}

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(message=SimpleNamespace(content="hello"))
            ]
        )

    monkeypatch.setattr(litellm, "completion", fake_completion)

    client = LiteLLMClient(
        model="openrouter/anthropic/claude-sonnet-4.5", api_key="sk-test"
    )
    out = client.complete(system="sys", user="usr")

    assert out == "hello"
    assert captured["model"].startswith("openrouter/")
    assert captured["api_key"] == "sk-test"
    assert captured["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "usr"},
    ]
