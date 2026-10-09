"""Rendering and writing of specification artifacts."""

from __future__ import annotations

import re
from pathlib import Path

from .loop import SpecResult


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    slug = slug[:60].strip("-")
    return slug or "spec"


def render_spec(result: SpecResult) -> str:
    status = "clean" if result.clean else "gaps remain"
    header = (
        f"# Spec: {result.intent}\n\n"
        f"- Intent: {result.intent}\n"
        f"- Model: {result.model}\n"
        f"- Iterations: {result.iterations}\n"
        f"- Status: {status}\n\n"
        "---\n\n"
    )
    return header + result.body


def write_spec(result: SpecResult, out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slugify(result.intent)}.md"
    path.write_text(render_spec(result), encoding="utf-8")
    return path
