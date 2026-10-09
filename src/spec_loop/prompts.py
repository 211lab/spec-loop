"""Prompt construction for the draft, critique, and revise stages."""

from __future__ import annotations

import re
from typing import Sequence

DRAFT_SYSTEM = (
    "You are a specification writer. Turn the user's intent into a concise, "
    "reviewable specification in Markdown. Include: a one-sentence goal; "
    "concrete user-visible behavior; non-goals; acceptance criteria written as "
    "Given/When/Then; assumptions marked inline with `ASSUMPTION:`; and open "
    "questions. Do not invent unrelated scope."
)

CRITIQUE_SYSTEM = (
    "You are a specification reviewer. Judge the draft against this rubric and "
    "report each criterion as a blocking gap or not:\n"
    "1. A one-sentence goal is present.\n"
    "2. User-visible behavior is described concretely.\n"
    "3. Non-goals are listed.\n"
    "4. Acceptance criteria are written as Given/When/Then.\n"
    "5. Assumptions are marked inline with `ASSUMPTION:`.\n"
    "6. Open questions are listed.\n"
    "List any blocking gaps, then end your reply with exactly one verdict line: "
    "`VERDICT: CLEAN` when there are no blocking gaps, or `VERDICT: GAPS` when "
    "there are."
)

REVISE_SYSTEM = (
    "You are a specification writer. Revise the draft to resolve every blocking "
    "gap raised in the critique. Keep what is already good, address each gap, "
    "and return the full revised specification in Markdown."
)

README_SYSTEM = (
    "You are a technical writer. Write a usable project README in Markdown "
    "based only on the provided source documents. Include an overview, install "
    "and usage commands, and any other sections the sources support. Use only "
    "facts, names, and commands found in the sources; do not invent repository "
    "facts or commands. Omit details the sources do not provide."
)

PLAN_SYSTEM = (
    "You are an implementation planner. Write an ordered implementation plan in "
    "Markdown based only on the provided source documents. Break the work into "
    "small, verifiable tasks in dependency order. For each task, state the "
    "touched areas, how to verify it, its dependencies, and rollback. Use only "
    "facts from the sources; do not invent repository facts."
)

_DOCUMENT_SYSTEMS = {"readme": README_SYSTEM, "plan": PLAN_SYSTEM}


def document_prompt(
    kind: str, sources: Sequence[tuple[str, str]]
) -> tuple[str, str]:
    try:
        system = _DOCUMENT_SYSTEMS[kind]
    except KeyError:
        raise ValueError(f"unknown document kind: {kind!r}") from None
    labeled = "\n\n".join(
        f"Source: {path}\n\n{content}" for path, content in sources
    )
    return system, f"Source documents:\n\n{labeled}"


def draft_prompt(intent: str) -> tuple[str, str]:
    return DRAFT_SYSTEM, f"Intent:\n{intent}"


def critique_prompt(intent: str, draft: str) -> tuple[str, str]:
    return CRITIQUE_SYSTEM, f"Intent:\n{intent}\n\nDraft:\n{draft}"


def revise_prompt(intent: str, draft: str, critique: str) -> tuple[str, str]:
    return (
        REVISE_SYSTEM,
        f"Intent:\n{intent}\n\nDraft:\n{draft}\n\nCritique:\n{critique}",
    )


_CLEAN_VERDICT = re.compile(r"(?m)^\s*VERDICT:\s*CLEAN\s*$")


def critique_is_clean(critique: str) -> bool:
    """True only when the critique carries a clean verdict line.

    The verdict must be its own line so prose that merely mentions the token
    (for example "this is not VERDICT: CLEAN") is not misread as clean.
    """
    return _CLEAN_VERDICT.search(critique) is not None
