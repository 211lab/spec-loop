"""Configuration loading for spec-loop."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

DEFAULT_MODEL = "openrouter/anthropic/claude-sonnet-4.5"


@dataclass(frozen=True)
class Settings:
    model: str
    api_key: str | None
    max_iterations: int
    out_dir: Path


def load_settings(
    model: str | None = None,
    max_iterations: int = 3,
    out_dir: Path = Path("specs"),
    env: Mapping[str, str] | None = None,
) -> Settings:
    if env is None:
        env = os.environ
    resolved_model = model or env.get("SPEC_LOOP_MODEL") or DEFAULT_MODEL
    api_key = env.get("OPENROUTER_API_KEY") or None
    return Settings(
        model=resolved_model,
        api_key=api_key,
        max_iterations=max_iterations,
        out_dir=Path(out_dir),
    )
