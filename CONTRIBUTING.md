# Contributing to chwflow

## Setup

```bash
git clone https://github.com/tinelee123/chat-history-to-fullauto-workflow.git
cd chat-history-to-fullauto-workflow
pip install -e ".[dev]"
```

## Development commands

```bash
pytest -v                  # Run all tests
ruff check src/ tests/     # Lint
ruff format src/ tests/    # Format
basedpyright src/          # Type check
```

## Code conventions

- Python 3.10+ with `from __future__ import annotations`
- Pydantic v2 for data models
- Strict typing — no `Any`, no `# type: ignore`
- 250 LOC ceiling per file
- Parse, don't validate
- No swallowed exceptions

## Testing

- Tests are in `tests/` using pytest
- Every behavior change requires a failing test first (RED-GREEN)
- Run `pytest -v` before committing

## Pull requests

1. Create a feature branch
2. Add tests for new behavior
3. Ensure all tests pass: `pytest -v`
4. Ensure lint passes: `ruff check .`
5. Open a PR against `main`
