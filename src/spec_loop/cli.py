"""Command-line entry point for spec-loop."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .artifact import write_spec
from .config import load_settings
from .llm import LiteLLMClient
from .loop import SpecLoop


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spec-loop",
        description="Turn a short statement of intent into a reviewable spec.",
    )
    parser.add_argument(
        "--version", action="version", version=f"spec-loop {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Draft, critique, and revise a spec.")
    run.add_argument("intent", nargs="?", help="The statement of intent.")
    run.add_argument("--out", default="specs", help="Output directory (default: specs).")
    run.add_argument("--model", default=None, help="Model id override.")
    run.add_argument(
        "--authoring-effort",
        default=None,
        help="Reasoning effort for draft/revise (default: max).",
    )
    run.add_argument(
        "--loop-effort",
        default=None,
        help="Reasoning effort for critique (default: medium).",
    )
    run.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum revise cycles (default: 3).",
    )
    run.add_argument(
        "--intent-file",
        default=None,
        help="Read the intent from a file instead of the positional argument.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "run":
        return 1

    if args.max_iterations < 1:
        parser.error("--max-iterations must be at least 1")
    if args.intent and args.intent_file:
        parser.error("INTENT and --intent-file are mutually exclusive")
    if args.intent_file:
        intent = Path(args.intent_file).read_text(encoding="utf-8").strip()
    elif args.intent:
        intent = args.intent
    else:
        parser.error("provide INTENT or --intent-file")

    settings = load_settings(
        model=args.model,
        max_iterations=args.max_iterations,
        out_dir=Path(args.out),
        authoring_effort=args.authoring_effort,
        loop_effort=args.loop_effort,
    )

    if not settings.api_key:
        print(
            "error: OPENROUTER_API_KEY is not set; export it to call OpenRouter.",
            file=sys.stderr,
        )
        return 2

    client = LiteLLMClient(
        model=settings.model,
        api_key=settings.api_key,
        session_id=settings.session_id,
    )
    loop = SpecLoop(
        client=client,
        model=settings.model,
        max_iterations=settings.max_iterations,
        authoring_effort=settings.authoring_effort,
        loop_effort=settings.loop_effort,
    )
    result = loop.run(intent)
    path = write_spec(result, settings.out_dir)

    status = "clean" if result.clean else "gaps remain"
    print(path)
    print(
        f"{status}; {result.iterations} revision(s); model {result.model}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
