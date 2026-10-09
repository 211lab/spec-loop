# spec-loop: Specification

Version: 0.1, October 8, 2026. Status: first-pass baseline. Scope: the minimal
spec stage of a spec-driven development loop, runnable end to end against
OpenRouter.

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
2. Calls the configured model through OpenRouter (via LiteLLM) to draft a spec.
3. Calls the model to critique the draft against the rubric in section 4.
4. If the critique lists blocking gaps, calls the model to revise the draft,
   then critiques again. Repeats up to `--max-iterations` times (default 3).
5. Writes the final spec to `<out>/<slug>.md`, where `<slug>` is a lowercase,
   hyphenated form of the intent.
6. Prints the artifact path and a one-line summary to stdout.

Exit codes: `0` success; `2` configuration error (for example a missing API
key); `1` any other failure.

## 3. Non-goals

- No plan, task, implement, or verify stages. Spec stage only.
- No GitHub, Gitea, or CI integration inside the tool.
- No web UI, database, server, or streaming output.
- No multi-provider abstraction beyond LiteLLM's OpenRouter routing.
- No prompt-caching tuning, retries, or cost accounting in this version.
- No editing of an existing spec; each run produces a new artifact.

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

## 6. Constraints

- Python `>=3.11`, managed by `uv`.
- `litellm` is the only LLM dependency.
- All LLM calls go through one injectable seam so tests run offline.
- Conventional Commits; one change set per commit.
- No secrets in the repository; the API key comes from the environment.

## 7. Assumptions

- `ASSUMPTION:` The default model is `openrouter/anthropic/claude-sonnet-4.5`,
  overridable with `--model` or `SPEC_LOOP_MODEL`. The exact model id may change;
  it is configuration, not behavior.
- `ASSUMPTION:` The API key is read from `OPENROUTER_API_KEY`. LiteLLM reads it
  from the environment for the `openrouter/` provider.
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
