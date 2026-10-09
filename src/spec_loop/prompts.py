"""Prompt construction for the draft, critique, and revise stages."""

from __future__ import annotations

import re

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
