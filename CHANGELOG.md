# Changelog

## [0.2.0] — 2026-06-24

### Added
- **Package**: `chwflow` as installable Python package (PyPI-ready via uv/hatchling)
- **CLI**: `chw` command with Typer + Rich (color, tables, progress)
- **Commands**: `init`, `next`, `record`, `sample`, `status`, `run`, `watch`, `version`
- **4 controller patterns**: PromptLoopController, AutomationController, HybridController, GeneratorController
- **LLM adapters**: OpenAIAdapter, AnthropicAdapter (optional `chwflow[llm]` extra)
- **StateMachine**: branching, parallel steps, rollback, conditional advancement
- **Pydantic v2 models**: Workflow, Step, State, HistoryEntry with full validation
- **WorkflowEngine**: deterministic shell/Python/file-check step execution
- **83 tests**: models, state, prompts, engine, CLI, controllers, adapters
- **CI**: GitHub Actions (ruff + basedpyright + pytest on 3.10/3.11/3.12)
- **Examples**: code-review-workflow.json, data-migration-workflow.json
- **License**: MIT

### Changed
- Complete project restructure from single-file script to `src/` layout
- CLI rewritten from argparse to Typer with Rich output
- State format now includes version field for forward-compat

### Removed
- `scripts/prompt_loop_runner.py` (replaced by `src/chwflow/cli.py`)

### Breaking
- Old CLI entry point `python scripts/prompt_loop_runner.py` no longer exists
- Use `chw` command instead, or `python -m chwflow`

## [0.1.0] — Initial release

- `scripts/prompt_loop_runner.py`: prompt-loop controller
- `SKILL.md`: Codex skill instructions
- `references/script_patterns.md`: pattern documentation
