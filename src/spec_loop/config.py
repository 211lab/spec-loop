"""Configuration loading for spec-loop."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

DEFAULT_MODEL = "openrouter/~openai/gpt-luna-latest"
AUTHORING_EFFORT = "max"
LOOP_EFFORT = "medium"


@dataclass(frozen=True)
class Settings:
    model: str
    api_key: str | None
    max_iterations: int
    out_dir: Path
    authoring_effort: str
    loop_effort: str
    session_id: str


def load_settings(
    model: str | None = None,
    max_iterations: int = 3,
    out_dir: Path = Path("specs"),
    authoring_effort: str | None = None,
    loop_effort: str | None = None,
    session_id: str | None = None,
    env: Mapping[str, str] | None = None,
    cwd: str | None = None,
) -> Settings:
    if env is None:
        env = os.environ
    resolved_model = model or env.get("SPEC_LOOP_MODEL") or DEFAULT_MODEL
    resolved_authoring_effort = (
        authoring_effort
        or env.get("SPEC_LOOP_AUTHORING_EFFORT")
        or AUTHORING_EFFORT
    )
    resolved_loop_effort = (
        loop_effort or env.get("SPEC_LOOP_LOOP_EFFORT") or LOOP_EFFORT
    )
    resolved_session_id = (
        session_id
        or env.get("SPEC_LOOP_SESSION_ID")
        or hashlib.sha256(
            os.path.abspath(cwd or os.getcwd()).encode("utf-8")
        ).hexdigest()
    )
    api_key = env.get("OPENROUTER_API_KEY") or None
    return Settings(
        model=resolved_model,
        api_key=api_key,
        max_iterations=max_iterations,
        out_dir=Path(out_dir),
        authoring_effort=resolved_authoring_effort,
        loop_effort=resolved_loop_effort,
        session_id=resolved_session_id,
    )
