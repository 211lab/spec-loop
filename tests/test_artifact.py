from pathlib import Path

from spec_loop.artifact import render_spec, slugify, write_document, write_spec
from spec_loop.loop import SpecResult


def test_slugify_spaces():
    assert slugify("Add Dark Mode") == "add-dark-mode"


def test_slugify_punctuation():
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_empty_falls_back():
    assert slugify("") == "spec"
    assert slugify("!!!") == "spec"


def test_slugify_long_is_truncated():
    slug = slugify("word " * 100)
    assert len(slug) <= 60
    assert not slug.startswith("-")
    assert not slug.endswith("-")


def test_render_contains_intent_and_model():
    result = SpecResult(
        intent="add dark mode",
        body="BODY TEXT",
        iterations=1,
        clean=True,
        model="openrouter/anthropic/claude-sonnet-4.5",
        authoring_effort="max",
        loop_effort="medium",
        session_id="sid-123",
    )
    rendered = render_spec(result)
    assert "add dark mode" in rendered
    assert "openrouter/anthropic/claude-sonnet-4.5" in rendered
    assert "BODY TEXT" in rendered
    assert "max" in rendered
    assert "medium" in rendered
    assert "sid-123" in rendered


def test_write_spec_creates_file(tmp_path: Path):
    result = SpecResult(
        intent="add dark mode",
        body="BODY TEXT",
        iterations=0,
        clean=True,
        model="m",
        authoring_effort="max",
        loop_effort="medium",
        session_id="sid-123",
    )
    path = write_spec(result, tmp_path)
    assert path == tmp_path / "add-dark-mode.md"
    assert path.exists()
    assert "BODY TEXT" in path.read_text(encoding="utf-8")


def test_write_document_creates_parents_and_overwrites(tmp_path: Path):
    out = tmp_path / "nested" / "README.md"
    out.parent.mkdir(parents=True)
    out.write_text("OLD", encoding="utf-8")

    path = write_document("NEW CONTENT", out)

    assert path == out
    assert out.read_text(encoding="utf-8") == "NEW CONTENT"


def test_write_document_makes_missing_parents(tmp_path: Path):
    out = tmp_path / "a" / "b" / "PLAN.md"

    path = write_document("PLAN", out)

    assert path == out
    assert out.read_text(encoding="utf-8") == "PLAN"
