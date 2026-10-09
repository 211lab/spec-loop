"""Command-line entry point for spec-loop."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .artifact import write_document, write_spec
from .config import load_settings
from .llm import LiteLLMClient
from .loop import SpecLoop
from .prompts import document_prompt

_EXAMPLES = (
    "Examples:\n"
    '  uv run spec-loop run "add dark mode to the settings page" --out specs\n'
    "  uv run spec-loop generate readme "
    "--source specs/add-dark-mode-to-the-settings-page.md --out README.md\n"
    "  uv run spec-loop generate plan "
    "--source specs/add-dark-mode-to-the-settings-page.md "
    "--out IMPLEMENTATION_PLAN.md\n"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spec-loop",
        description=(
            "Turn a short statement of intent into a reviewable spec, README, "
            "or implementation plan."
        ),
        epilog=_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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

    generate = subparsers.add_parser(
        "generate",
        help="Author a README or implementation plan from source files.",
        description=(
            "Author a README or implementation plan from one or more source "
            "files with a single authoring call. Sources are read as UTF-8 and "
            "labeled by path; the repository is not inspected automatically."
        ),
        epilog=_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    documents = generate.add_subparsers(dest="document", required=True)
    for kind, help_text in (
        ("readme", "Generate a project README from source files."),
        ("plan", "Generate an ordered implementation plan from source files."),
    ):
        document = documents.add_parser(kind, help=help_text)
        document.add_argument(
            "--source",
            action="append",
            required=True,
            metavar="PATH",
            help="UTF-8 source file; repeat for additional context.",
        )
        document.add_argument(
            "--out",
            required=True,
            metavar="PATH",
            help="Exact output file path (overwritten if it exists).",
        )
        document.add_argument("--model", default=None, help="Model id override.")
        document.add_argument(
            "--authoring-effort",
            default=None,
            help="Authoring reasoning effort override (default: max).",
        )
    return parser


def _read_sources(paths: Sequence[str]) -> list[tuple[str, str]] | None:
    sources: list[tuple[str, str]] = []
    for raw in paths:
        path = Path(raw)
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: cannot read source {path}: {exc}", file=sys.stderr)
            return None
        sources.append((str(path), content))
    return sources


def _run(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
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


def _generate(args: argparse.Namespace) -> int:
    sources = _read_sources(args.source)
    if sources is None:
        return 1

    settings = load_settings(
        model=args.model,
        out_dir=Path(args.out).parent,
        authoring_effort=args.authoring_effort,
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
    system, user = document_prompt(args.document, sources)
    content = client.complete(
        system=system, user=user, reasoning_effort=settings.authoring_effort
    )
    path = write_document(content, Path(args.out))

    print(path)
    print(
        f"{args.document} generated from {len(sources)} source(s); "
        f"model {settings.model}"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return _run(args, parser)
    if args.command == "generate":
        return _generate(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
