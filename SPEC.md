# spec-loop: Specification

Version: 0.3, October 8, 2026. Status: implementation baseline. Scope: a
spec-generation loop plus direct README and implementation-plan authoring via
OpenRouter. Version 0.3 adds documented UV commands and single-call generation
for supporting project documents.

## 1. Goal

`spec-loop` is a command-line tool that turns a short statement of intent into a
durable, reviewable specification artifact. It runs a bounded LLM loop: draft a
spec, critique it against a fixed rubric, revise it, and repeat until the
critique reports no blocking gaps or a maximum iteration count is reached. The
result is written to a Markdown file that a human can review and that later
stages (plan, tasks, implement, verify) can consume.

The tool is the first slice of a larger spec-driven development loop. This
version implements the spec stage only, but the loop shape and the artifact
contract are designed so later stages attach without rework.

## 2. User-visible behavior

The user runs:

```sh
spec-loop run "add dark mode to the settings page" --out specs
```

The tool:

1. Reads the intent from the positional argument (or `--intent-file PATH`).
2. Calls the **authoring model** (Luna max) through OpenRouter (via LiteLLM) to
   draft a spec.
3. Calls the **loop model** (Luna medium) to critique the draft against the
   rubric in section 4.
4. If the critique lists blocking gaps, calls the authoring model to revise the
   draft, then critiques again with the loop model. Repeats up to
   `--max-iterations` times (default 3).
5. Writes the final spec to `<out>/<slug>.md`, where `<slug>` is a lowercase,
   hyphenated form of the intent.
6. Prints the artifact path and a one-line summary to stdout.

Exit codes: `0` success; `2` configuration error (for example a missing API
key); `1` any other failure.

### Supporting document generation

Use the `generate` subcommand to author a README or implementation plan from
one or more input files. Each source file is read as UTF-8 and labeled by its
path in the prompt. The generated Markdown is written to the exact `--out` file
path, replacing that path if it already exists.

```sh
# Generate a spec through the existing critique/revise loop.
uv run spec-loop run "add dark mode to the settings page" --out specs

# Generate a README from the approved spec.
uv run spec-loop generate readme --source specs/add-dark-mode-to-the-settings-page.md --out README.md

# Generate an ordered implementation plan from the spec.
uv run spec-loop generate plan --source specs/add-dark-mode-to-the-settings-page.md --out IMPLEMENTATION_PLAN.md
```

README and plan generation each make one authoring call at `max` effort. Both
generation commands accept `--model` and `--authoring-effort` overrides, matching
the environment configuration supported by `run`. The `run` command remains the
quality-gated spec loop: it drafts and revises at `max` effort and critiques at
`medium` effort. The generation commands do not
inspect the repository automatically; pass relevant source files with repeated
`--source` options. This avoids claiming project facts that were not provided.

### Model tiers

Two tiers share one floating model alias and differ only by reasoning effort:

| Tier | Used for | Model | Reasoning effort |
| --- | --- | --- | --- |
| Authoring | Spec, README, and implementation-plan authoring (draft and revise) | `openrouter/~openai/gpt-luna-latest` | `max` |
| Loop | Iterative loop runs (critique) | `openrouter/~openai/gpt-luna-latest` | `medium` |

The effort is sent to OpenRouter as `reasoning.effort` via LiteLLM's
`extra_body`, so the literal `max` value is used (LiteLLM's `reasoning_effort`
parameter would rewrite `max` to `xhigh`). Both tiers are overridable:
`--model`/`SPEC_LOOP_MODEL` set the model id, and
`--authoring-effort`/`SPEC_LOOP_AUTHORING_EFFORT` and
`--loop-effort`/`SPEC_LOOP_LOOP_EFFORT` set the efforts.

### Session id

Every LLM call carries a `session_id` derived from the directory that invokes
the tool: the SHA-256 hex digest of the absolute current working directory. This
gives OpenRouter a stable sticky-routing and cache-grouping key per calling
directory, so repeated runs from the same directory reuse the same provider and
cache. The value is sent in the request body via `extra_body`.

## 3. Non-goals

- No task execution, code implementation, or verification stages. The plan command only writes an implementation plan; it does not execute tasks.
- No GitHub, Gitea, or CI integration inside the tool.
- No web UI, database, server, or streaming output.
- No multi-provider abstraction beyond LiteLLM's OpenRouter routing.
- No prompt-caching tuning, retries, or cost accounting in this version.
- No editing of an existing spec; each run produces a new artifact.
- No automatic repository scanning for README/plan generation; sources must be passed explicitly.

## 4. Spec rubric

The critique stage judges a draft against these criteria and reports each as a
blocking gap or not:

1. A one-sentence goal is present.
2. User-visible behavior is described concretely.
3. Non-goals are listed.
4. Acceptance criteria are written as Given/When/Then.
5. Assumptions are marked inline with `ASSUMPTION:`.
6. Open questions are listed.

A critique is "clean" when it reports no blocking gaps. The loop stops early on
a clean critique.

## 5. Acceptance criteria

**AC1 — End-to-end artifact.** Given a fake LLM that returns a draft and a clean
critique, when `spec-loop run "add dark mode" --out <tmp>` runs, then
`<tmp>/add-dark-mode.md` exists and contains the intent and the draft text.

**AC2 — The loop iterates on critique.** Given a fake LLM whose first critique
lists a gap and whose revision fixes it, when the loop runs, then the model is
called for draft, critique, revise, and a final critique, and the artifact
contains the revised text.

**AC3 — Iterations are bounded.** Given a fake LLM that always reports a gap,
when `--max-iterations 2` is set, then the loop performs exactly two revise
cycles, stops, and still writes the artifact with a note that gaps remain.

**AC4 — OpenRouter wiring.** Given a configured model and API key, when the LLM
client is built, then it is a LiteLLM call with an `openrouter/`-prefixed model
and the key passed through, proven by a unit test that monkeypatches
`litellm.completion` and inspects the captured arguments. No network is used.

**AC5 — Missing key fails clearly.** Given no `OPENROUTER_API_KEY`, when the CLI
runs, then it exits `2`, prints a clear error naming the variable, and writes no
artifact.

**AC6 — Offline tests.** `uv run pytest` passes with no network access.

**AC7 — Tier routing.** Given a fake LLM, when the loop runs, then the draft and
revise calls carry reasoning effort `max` and the critique call carries
reasoning effort `medium`, proven by a unit test that inspects the captured
per-call effort.

**AC8 — Session id.** Given the tool is invoked from a directory, when any LLM
call is made, then it carries a `session_id` equal to the SHA-256 hex digest of
that directory's absolute path, and two invocations from the same directory
produce the same id, proven by a unit test that monkeypatches `litellm.completion`
and inspects the captured `extra_body`.

**AC9 — README generation.** Given one or more source files and an output path,
when `uv run spec-loop generate readme --source SPEC.md --out README.md` runs,
then one LiteLLM call is made at authoring effort `max`, and the output file
contains generated Markdown based on the labeled input contents.

**AC10 — Implementation-plan generation.** Given one or more source files and
an output path, when `uv run spec-loop generate plan --source SPEC.md --out
IMPLEMENTATION_PLAN.md` runs, then one LiteLLM call is made at authoring effort
`max`, and the output file contains an ordered implementation plan based on the
labeled input contents.

**AC11 — Missing source fails before model call.** Given a source path that does
not exist, when either generation command runs, then it reports a clear error,
returns non-zero, makes no LLM call, and writes no output file.

**AC12 — Document commands are discoverable.** Given a user runs
`uv run spec-loop --help` or `uv run spec-loop generate --help`, then help
lists the spec, README, and plan workflows and their UV command examples or
subcommand syntax.

**AC13 — Generation overrides.** Given a user supplies `--model M` and
`--authoring-effort E` to a generation command, when the generation call is made,
then LiteLLM receives model `M` and reasoning effort `E`.

## 6. Constraints

- Python `>=3.11`, managed by `uv`.
- `litellm` is the only LLM dependency.
- All LLM calls go through one injectable seam so tests run offline.
- Conventional Commits; one change set per commit.
- No secrets in the repository; the API key comes from the environment.

## 7. Assumptions

- `ASSUMPTION:` The default model is the floating alias
  `openrouter/~openai/gpt-luna-latest` for both tiers, overridable with
  `--model` or `SPEC_LOOP_MODEL`. The alias tracks the latest GPT Luna model;
  the exact resolved model may change, which is configuration, not behavior.
- `ASSUMPTION:` "Luna max" and "Luna medium" are the `max` and `medium` values
  of the model's `reasoning.effort`, not separate model ids. The model metadata
  lists supported efforts `max, xhigh, high, medium, low, none` with default
  `medium`.
- `ASSUMPTION:` The session id is the SHA-256 hex digest of the absolute current
  working directory, computed when settings load. It is opaque but stable per
  directory.
- `ASSUMPTION:` The API key is read from `OPENROUTER_API_KEY`. LiteLLM reads it
  from the environment for the `openrouter/` provider.
- `ASSUMPTION:` README and implementation-plan generation are single-call
  authoring operations at `max` effort. Only spec `run` uses the medium-effort
  critique loop.
- `ASSUMPTION:` Generated README and plan output replaces the explicitly named
  `--out` file if it already exists.
- `ASSUMPTION:` Sources are UTF-8 text files. Binary inputs are not supported.
- `ASSUMPTION:` Specs are written as Markdown with a short generated header
  (intent, model, iteration count) followed by the model's spec body.
- `ASSUMPTION:` A "blocking gap" is any rubric criterion the critique marks as
  missing. The critique returns a simple machine-readable verdict line so the
  loop can decide without parsing prose.

## 8. Open questions

- Should the loop also emit a machine-readable JSON spec alongside the Markdown?
- Should later stages share one artifact directory convention, or one directory
  per stage?
- Which model best balances spec quality and cost for this workload?
