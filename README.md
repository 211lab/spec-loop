# spec-loop

`spec-loop` turns a short statement of intent into a durable, reviewable
specification artifact. It runs a bounded LLM loop: draft a spec, critique it
against a fixed rubric, revise it, and repeat until the critique reports no
blocking gaps or a maximum iteration count is reached. The result is written to
a Markdown file.

It can also author supporting project documents — a README or an ordered
implementation plan — from one or more source files with a single authoring
call.

This is the first slice of a larger spec-driven development loop; only the spec
stage is implemented.

## Install

```sh
uv sync
```

## Usage

```sh
uv run spec-loop run "add dark mode to the settings page" --out specs
uv run spec-loop generate readme --source specs/add-dark-mode-to-the-settings-page.md --out README.md
uv run spec-loop generate plan --source specs/add-dark-mode-to-the-settings-page.md --out IMPLEMENTATION_PLAN.md
```

### Spec loop (`run`)

Options:

- `--out DIR` — output directory (default `specs`).
- `--model M` — model id override.
- `--authoring-effort E` — reasoning effort for draft/revise (default `max`).
- `--loop-effort E` — reasoning effort for critique (default `medium`).
- `--max-iterations N` — maximum revise cycles (default 3).
- `--intent-file PATH` — read the intent from a file instead of the positional
  argument.

The artifact is written to `<out>/<slug>.md` and the path plus a one-line
summary are printed to stdout.

### Document generation (`generate`)

```sh
uv run spec-loop generate readme --source PATH [--source PATH ...] --out README.md
uv run spec-loop generate plan --source PATH [--source PATH ...] --out IMPLEMENTATION_PLAN.md
```

- `readme` writes a usable project README; `plan` writes an ordered
  implementation plan with small, verifiable tasks, touched areas, verification,
  dependencies, and rollback.
- `--source PATH` is required and may be repeated to supply additional project
  context. Each source is read as UTF-8 and labeled by its path in the prompt.
- `--out PATH` is the exact output file path. Parent directories are created and
  an existing file is overwritten.
- `--model M` and `--authoring-effort E` optionally override the default model
  and `max` effort for this generation call.
- Generation makes one authoring call at `max` effort. It does **not** inspect
  the repository automatically, so pass every relevant file with `--source` to
  avoid claims that were not provided.
- A missing or unreadable source fails before any model call or output write.

## Model tiers

Two tiers share one floating model alias and differ only by reasoning effort:

| Tier | Used for | Model | Reasoning effort |
| --- | --- | --- | --- |
| Authoring | Spec draft/revise, README, and plan | `openrouter/~openai/gpt-luna-latest` | `max` |
| Loop | Critique | `openrouter/~openai/gpt-luna-latest` | `medium` |

The effort is sent to OpenRouter as `reasoning.effort` via LiteLLM's
`extra_body`, so the literal `max` value is used (LiteLLM's `reasoning_effort`
parameter would rewrite `max` to `xhigh`).

## Session id

Every LLM call carries a `session_id`: the SHA-256 hex digest of the absolute
current working directory. This gives OpenRouter a stable sticky-routing and
cache-grouping key per calling directory, so repeated runs from the same
directory reuse the same provider and cache. The value is sent in the request
body via `extra_body`.

## Environment variables

- `OPENROUTER_API_KEY` — required; the OpenRouter API key.
- `SPEC_LOOP_MODEL` — optional default model override.
- `SPEC_LOOP_AUTHORING_EFFORT` — optional authoring-tier effort override.
- `SPEC_LOOP_LOOP_EFFORT` — optional loop-tier effort override.
- `SPEC_LOOP_SESSION_ID` — optional session id override (defaults to the
  per-directory SHA-256 digest).

## Tests

```sh
uv run pytest
```

All tests run offline; the live smoke test is skipped unless explicitly enabled.
The suite covers the spec loop, README and plan generation (source labeling,
single `max`-effort call, output writing), missing-source and missing-key
failures, and CLI help discoverability.

## Live smoke test

```sh
OPENROUTER_API_KEY=... SPEC_LOOP_LIVE_SMOKE=1 uv run pytest tests/test_live_openrouter_smoke.py
```

Optionally set `SPEC_LOOP_SMOKE_MODEL` to override the smoke model (default
`openrouter/anthropic/claude-haiku-4-5`).
