# AGENTS.md

## Commits

- Use [Conventional Commits](https://www.conventionalcommits.org/) (for example
  `feat:`, `fix:`, `test:`, `docs:`, `chore:`).
- One change set per commit.
- Push to `origin` after committing.

## Secrets

- Never commit secrets. The API key comes from `OPENROUTER_API_KEY` in the
  environment; `.env` is gitignored.

## Tests

- Keep tests offline. All LLM calls go through the single injectable seam in
  `src/spec_loop/llm.py`; tests must not make network calls.
- The live smoke test is env-gated and must stay skipped by default.
