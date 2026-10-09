import hashlib
import os

from spec_loop.config import (
    AUTHORING_EFFORT,
    DEFAULT_MODEL,
    LOOP_EFFORT,
    load_settings,
)


def test_session_id_is_sha256_of_absolute_cwd():
    cwd = "/tmp/spec-loop-config-test"
    settings = load_settings(env={}, cwd=cwd)
    expected = hashlib.sha256(os.path.abspath(cwd).encode("utf-8")).hexdigest()
    assert settings.session_id == expected


def test_session_id_stable_per_directory_and_differs_across_directories():
    first = load_settings(env={}, cwd="/tmp/spec-loop-a")
    second = load_settings(env={}, cwd="/tmp/spec-loop-a")
    other = load_settings(env={}, cwd="/tmp/spec-loop-b")
    assert first.session_id == second.session_id
    assert first.session_id != other.session_id


def test_effort_defaults():
    settings = load_settings(env={}, cwd="/tmp/spec-loop-config-test")
    assert settings.authoring_effort == AUTHORING_EFFORT == "max"
    assert settings.loop_effort == LOOP_EFFORT == "medium"
    assert settings.model == DEFAULT_MODEL


def test_env_overrides():
    settings = load_settings(
        env={
            "SPEC_LOOP_MODEL": "openrouter/other/model",
            "SPEC_LOOP_AUTHORING_EFFORT": "high",
            "SPEC_LOOP_LOOP_EFFORT": "low",
            "SPEC_LOOP_SESSION_ID": "explicit-session",
        },
        cwd="/tmp/spec-loop-config-test",
    )
    assert settings.model == "openrouter/other/model"
    assert settings.authoring_effort == "high"
    assert settings.loop_effort == "low"
    assert settings.session_id == "explicit-session"


def test_explicit_args_beat_env():
    settings = load_settings(
        model="openrouter/explicit",
        authoring_effort="xhigh",
        loop_effort="none",
        session_id="arg-session",
        env={
            "SPEC_LOOP_MODEL": "openrouter/env",
            "SPEC_LOOP_AUTHORING_EFFORT": "high",
            "SPEC_LOOP_LOOP_EFFORT": "low",
            "SPEC_LOOP_SESSION_ID": "env-session",
        },
        cwd="/tmp/spec-loop-config-test",
    )
    assert settings.model == "openrouter/explicit"
    assert settings.authoring_effort == "xhigh"
    assert settings.loop_effort == "none"
    assert settings.session_id == "arg-session"
