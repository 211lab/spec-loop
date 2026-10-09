from pathlib import Path

import pytest

import spec_loop.cli as cli


class FakeClient:
    def __init__(self, model, api_key=None, session_id=None):
        self.model = model
        self.api_key = api_key
        self.session_id = session_id
        self.responses = ["DRAFT BODY", "no gaps\nVERDICT: CLEAN"]

    def complete(self, *, system, user, reasoning_effort):
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


class RecordingClient:
    instances: list["RecordingClient"] = []

    def __init__(self, model, api_key=None, session_id=None):
        self.model = model
        self.api_key = api_key
        self.session_id = session_id
        self.calls = []
        self.response = "GENERATED MARKDOWN"
        RecordingClient.instances.append(self)

    def complete(self, *, system, user, reasoning_effort):
        self.calls.append((system, user, reasoning_effort))
        return self.response


@pytest.fixture
def recording_client(monkeypatch):
    RecordingClient.instances = []
    monkeypatch.setattr(cli, "LiteLLMClient", RecordingClient)
    return RecordingClient


def test_ac9_readme_generation(tmp_path: Path, monkeypatch, recording_client):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    source = tmp_path / "SPEC.md"
    source.write_text("SOURCE CONTENT", encoding="utf-8")
    out = tmp_path / "nested" / "README.md"

    code = cli.main(
        ["generate", "readme", "--source", str(source), "--out", str(out)]
    )

    assert code == 0
    assert out.read_text(encoding="utf-8") == "GENERATED MARKDOWN"
    assert len(recording_client.instances) == 1
    client = recording_client.instances[0]
    assert len(client.calls) == 1
    system, user, effort = client.calls[0]
    assert effort == "max"
    assert client.model == "openrouter/~openai/gpt-luna-latest"
    assert str(source) in user
    assert "SOURCE CONTENT" in user
    assert "README" in system


def test_ac10_plan_generation(tmp_path: Path, monkeypatch, recording_client):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    source = tmp_path / "SPEC.md"
    source.write_text("SOURCE CONTENT", encoding="utf-8")
    out = tmp_path / "IMPLEMENTATION_PLAN.md"

    code = cli.main(
        ["generate", "plan", "--source", str(source), "--out", str(out)]
    )

    assert code == 0
    assert out.read_text(encoding="utf-8") == "GENERATED MARKDOWN"
    client = recording_client.instances[0]
    assert len(client.calls) == 1
    system, user, effort = client.calls[0]
    assert effort == "max"
    assert str(source) in user
    assert "SOURCE CONTENT" in user
    assert "ordered" in system
    assert "rollback" in system


def test_generation_model_and_effort_can_be_overridden(
    tmp_path: Path, monkeypatch, recording_client
):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    source = tmp_path / "SPEC.md"
    source.write_text("SOURCE CONTENT", encoding="utf-8")
    out = tmp_path / "README.md"

    code = cli.main(
        [
            "generate",
            "readme",
            "--source",
            str(source),
            "--out",
            str(out),
            "--model",
            "openrouter/test-model",
            "--authoring-effort",
            "high",
        ]
    )

    assert code == 0
    client = recording_client.instances[0]
    assert client.model == "openrouter/test-model"
    assert client.calls[0][2] == "high"


def test_repeated_sources_are_labeled(tmp_path: Path, monkeypatch, recording_client):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    first = tmp_path / "a.md"
    second = tmp_path / "b.md"
    first.write_text("ALPHA", encoding="utf-8")
    second.write_text("BETA", encoding="utf-8")
    out = tmp_path / "README.md"

    code = cli.main(
        [
            "generate",
            "readme",
            "--source",
            str(first),
            "--source",
            str(second),
            "--out",
            str(out),
        ]
    )

    assert code == 0
    _, user, _ = recording_client.instances[0].calls[0]
    assert str(first) in user and "ALPHA" in user
    assert str(second) in user and "BETA" in user


def test_ac11_missing_source_fails_before_model_call(
    tmp_path: Path, monkeypatch, recording_client, capsys
):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    out = tmp_path / "README.md"

    code = cli.main(
        [
            "generate",
            "readme",
            "--source",
            str(tmp_path / "missing.md"),
            "--out",
            str(out),
        ]
    )

    assert code != 0
    assert recording_client.instances == []
    assert not out.exists()
    assert "missing.md" in capsys.readouterr().err


def test_generation_missing_key_returns_two(
    tmp_path: Path, monkeypatch, recording_client, capsys
):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    source = tmp_path / "SPEC.md"
    source.write_text("SOURCE CONTENT", encoding="utf-8")
    out = tmp_path / "README.md"

    code = cli.main(
        ["generate", "readme", "--source", str(source), "--out", str(out)]
    )

    assert code == 2
    assert recording_client.instances == []
    assert not out.exists()
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err


def test_ac12_help_lists_workflows(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    top = capsys.readouterr().out
    assert "run" in top
    assert "generate" in top
    assert "readme" in top
    assert "plan" in top
    assert "uv run spec-loop generate readme" in top

    with pytest.raises(SystemExit):
        cli.main(["generate", "--help"])
    generate = capsys.readouterr().out
    assert "readme" in generate
    assert "plan" in generate
    assert "uv run spec-loop generate plan" in generate
