from pathlib import Path

import pytest

import spec_loop.cli as cli


class FakeClient:
    def __init__(self, model, api_key=None):
        self.model = model
        self.api_key = api_key
        self.responses = ["DRAFT BODY", "no gaps\nVERDICT: CLEAN"]

    def complete(self, *, system, user):
        return self.responses.pop(0)


def test_ac1_end_to_end_artifact(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setattr(cli, "LiteLLMClient", FakeClient)

    code = cli.main(["run", "add dark mode", "--out", str(tmp_path)])

    assert code == 0
    artifact = tmp_path / "add-dark-mode.md"
    assert artifact.exists()
    text = artifact.read_text(encoding="utf-8")
    assert "add dark mode" in text
    assert "DRAFT BODY" in text


def test_ac5_missing_key_fails_clearly(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    code = cli.main(["run", "add dark mode", "--out", str(tmp_path)])

    assert code == 2
    err = capsys.readouterr().err
    assert "OPENROUTER_API_KEY" in err
    assert list(tmp_path.iterdir()) == []


def test_max_iterations_zero_rejected(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

    with pytest.raises(SystemExit):
        cli.main(
            ["run", "add dark mode", "--out", str(tmp_path), "--max-iterations", "0"]
        )
