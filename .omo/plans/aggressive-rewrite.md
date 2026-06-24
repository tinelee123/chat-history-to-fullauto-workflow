# Aggressive Rewrite Plan: chat-history-to-fullauto-workflow

## 1. Mission Statement

Transform a 230-line single-file CLI script into a production-grade workflow engine that turns chat history into executable self-reviewing agent pipelines. Support 4 controller patterns (prompt-loop, automation, hybrid-handoff, generator), optional LLM closed-loop via OpenAI/Anthropic SDKs, enriched state machine with branching/parallel/conditional/rollback, full test coverage, CI, packaging, and example workflows.

## 2. Architecture Diagram (Post-Rewrite)

```
src/chwflow/
├── __init__.py          # version, public API re-exports
├── __main__.py          # python -m chwflow entry
├── cli.py               # typer CLI: chw {init,next,record,sample,status,watch,run}
├── models.py            # Pydantic v2: Workflow, Step, State, HistoryEntry, ReviewStatus
├── state.py             # StateMachine: load/save/advance/rollback/branch/parallel
├── engine.py            # WorkflowEngine: execute deterministic steps (automation runner)
├── prompts.py           # PromptRenderer: render_next_prompt, self-review gate
├── controllers/
│   ├── __init__.py
│   ├── prompt_loop.py   # PromptLoopController (existing pattern, rewritten with engine)
│   ├── automation.py    # AutomationController: run local scripts/API calls with retry
│   ├── hybrid.py        # HybridController: alternating script+human/agent review
│   └── generator.py     # GeneratorController: create parameterized scripts from templates
├── adapters/
│   ├── __init__.py
│   ├── base.py          # AbstractLLMAdapter: call(prompt) -> str
│   ├── openai_adapter.py   # OpenAIAdapter: openai>=1.0
│   └── anthropic_adapter.py # AnthropicAdapter: anthropic>=0.30
├── render.py            # Rich rendering: tables, spinners, progress bars, color
└── templates/           # Generator templates (Jinja2)
examples/                # Pre-built workflow JSONs
tests/                   # pytest test suite
```

## 3. File-by-File Change Ledger

| # | Path | Action | Purpose | LOC |
|---|------|--------|---------|-----|
| 1 | `LICENSE` | CREATE | MIT License | 21 |
| 2 | `pyproject.toml` | CREATE | uv build config, deps, scripts, extras | 80 |
| 3 | `src/chwflow/__init__.py` | CREATE | Version `0.2.0`, public API | 15 |
| 4 | `src/chwflow/__main__.py` | CREATE | `python -m chwflow` | 5 |
| 5 | `src/chwflow/models.py` | CREATE | Pydantic v2 Workflow, Step, State, HistoryEntry | 180 |
| 6 | `src/chwflow/state.py` | CREATE | StateMachine: load/save/advance/branch/parallel/rollback | 200 |
| 7 | `src/chwflow/engine.py` | CREATE | WorkflowEngine: deterministic step execution | 120 |
| 8 | `src/chwflow/prompts.py` | CREATE | PromptRenderer with self-review gate, port from prompt_loop_runner.py | 130 |
| 9 | `src/chwflow/cli.py` | CREATE | Typer CLI: init/next/record/sample/status/watch/run | 200 |
| 10 | `src/chwflow/render.py` | CREATE | Rich: tables, progress, status, color output | 80 |
| 11 | `src/chwflow/controllers/__init__.py` | CREATE | Re-exports | 8 |
| 12 | `src/chwflow/controllers/prompt_loop.py` | CREATE | PromptLoopController | 100 |
| 13 | `src/chwflow/controllers/automation.py` | CREATE | AutomationController | 150 |
| 14 | `src/chwflow/controllers/hybrid.py` | CREATE | HybridController | 120 |
| 15 | `src/chwflow/controllers/generator.py` | CREATE | GeneratorController | 100 |
| 16 | `src/chwflow/adapters/__init__.py` | CREATE | Re-exports | 6 |
| 17 | `src/chwflow/adapters/base.py` | CREATE | AbstractLLMAdapter protocol | 30 |
| 18 | `src/chwflow/adapters/openai_adapter.py` | CREATE | OpenAIAdapter | 60 |
| 19 | `src/chwflow/adapters/anthropic_adapter.py` | CREATE | AnthropicAdapter | 60 |
| 20 | `src/chwflow/templates/` | CREATE | Jinja2 generator templates dir | 50 |
| 21 | `README.md` | REWRITE | Full project docs, usage, examples | 200 |
| 22 | `SKILL.md` | MODIFY | Update to reference new package, preserve Codex skill contract | 80 |
| 23 | `scripts/prompt_loop_runner.py` | DELETE | Replaced by `src/chwflow/cli.py` | 0 |
| 24 | `references/script_patterns.md` | MODIFY | Update to reflect new architecture | 60 |
| 25 | `agents/openai.yaml` | MODIFY | Update display_name, description | 5 |
| 26 | `tests/test_models.py` | CREATE | Pydantic model validation tests | 100 |
| 27 | `tests/test_state.py` | CREATE | StateMachine unit tests | 150 |
| 28 | `tests/test_prompts.py` | CREATE | Prompt rendering tests | 100 |
| 29 | `tests/test_engine.py` | CREATE | Engine tests | 80 |
| 30 | `tests/test_cli.py` | CREATE | CLI integration tests | 120 |
| 31 | `tests/test_controllers.py` | CREATE | Controller integration tests | 100 |
| 32 | `tests/test_adapters.py` | CREATE | Adapter mock tests | 80 |
| 33 | `examples/code-review-workflow.json` | EXISTS | Already created | - |
| 34 | `examples/data-migration-workflow.json` | EXISTS | Already created | - |
| 35 | `.github/workflows/ci.yml` | EXISTS | Already created, refine paths | - |
| 36 | `CONTRIBUTING.md` | CREATE | Contributing guide | 40 |
| 37 | `CHANGELOG.md` | CREATE | v0.2.0 changelog | 30 |

**Total new LOC**: ~2300 (16 new source files, avg ~130 LOC each, largest file 200 LOC).

## 4. Concrete Decisions (Zero Ambiguity)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Package name** | `chwflow` | Short, unique on PyPI, pronounceable |
| **CLI entry** | `chw` | 3 letters, fast to type, mnemonic "Chat History Workflow" |
| **Python min** | 3.10 | `from __future__ import annotations` already used; wide compatibility |
| **Type system** | Pydantic v2 | User confirmed; `model_validate`, discriminated unions for status |
| **CLI lib** | Typer | Rich integration, auto-help, shell completion, modern |
| **Color/TUI** | Rich | Typer's default renderer, tables, progress, spinners |
| **Test** | pytest + pytest-mock + syrupy (snapshot) | Standard, fast |
| **Lint/format** | ruff (format + check) + basedpyright | Global project rules |
| **Build backend** | uv + hatchling | Fastest, modern, lockfile support |
| **License** | MIT | Most permissive, standard for Python tools |
| **LLM SDKs** | `openai>=1.0`, `anthropic>=0.30` | Latest stable APIs; installed via `chwflow[llm]` extra |
| **State schema** | Version field in JSON; `StateMachine.migrate()` handles v1→v2 | Forward compat |
| **Backward compat** | Break old CLI (`prompt_loop_runner.py`); old `workflow.json` schema preserved via migration | Aggressive rewrite allows breaking |
| **Entry point** | `chw = "chwflow.cli:app"` | Single command, subcommands for all operations |

## 5. Wave-Based Execution Graph

### Wave 1 — Scaffold & Foundation (PARALLEL)
Tasks with NO inter-dependencies. All 4 file creates parallel.
- Task 1.1: `pyproject.toml` CREATE — verify `uv sync` exits 0
- Task 1.2: `LICENSE` + `src/chwflow/__init__.py` + `src/chwflow/__main__.py` CREATE — verify `python -m chwflow --version`
- Task 1.3: `src/chwflow/models.py` CREATE — verify `python -c "from chwflow.models import Workflow"`
- Task 1.4: `src/chwflow/render.py` CREATE — verify `python -c "from chwflow.render import console"`

### Wave 2 — Engine & State & CLI (PARALLEL, depends on Wave 1)
- Task 2.1: `src/chwflow/state.py` CREATE — verify unit test
- Task 2.2: `src/chwflow/engine.py` + `src/chwflow/prompts.py` CREATE — verify engine runs sample workflow
- Task 2.3: `src/chwflow/cli.py` CREATE — verify `chw --help`, `chw sample`, `chw init/next/record/status`

### Wave 3 — Controllers & Adapters (PARALLEL)
- Task 3.1: `controllers/prompt_loop.py` CREATE + `adapters/base.py` + `adapters/openai_adapter.py` + `adapters/anthropic_adapter.py` CREATE
- Task 3.2: `controllers/automation.py` CREATE
- Task 3.3: `controllers/hybrid.py` CREATE
- Task 3.4: `controllers/generator.py` + `templates/` CREATE

### Wave 4 — Tests & Docs (PARALLEL)
- Task 4.1: All 7 test files CREATE — verify `pytest` green
- Task 4.2: `README.md` REWRITE + `SKILL.md` MODIFY + `references/script_patterns.md` MODIFY
- Task 4.3: `CONTRIBUTING.md` + `CHANGELOG.md` CREATE

### Wave 5 — CI + QA + Push + PR (SERIAL, requires gh auth)
- Task 5.1: Verify CI passes locally (`ruff` + `basedpyright` + `pytest`)
- Task 5.2: Manual QA — run all `chw` commands end-to-end
- Task 5.3: `git add`, `git commit`, `git push`
- Task 5.4: `gh pr create` to upstream

## 6. TDD Scenarios Contract (12 Minimum)

| # | Scenario | Pytest Assertion |
|---|----------|------------------|
| S1 | Valid workflow JSON → Workflow model validates | `Workflow.model_validate(data)` returns without error |
| S2 | Missing `steps` field → ValidationError | `pytest.raises(ValidationError)` |
| S3 | Empty steps array → ValidationError | `pytest.raises(ValidationError)` |
| S4 | State init from workflow → step 0, status "active" | `state.current_step == 0 and state.status == "active"` |
| S5 | Record "ok" → advances current_step | `after record ok, state.current_step == 1` |
| S6 | Record "needs_revision" → stays on same step | `after record needs_revision, state.current_step unchanged` |
| S7 | Record "blocked" → status becomes "blocked" | `state.status == "blocked"` |
| S8 | Render prompt for step N → contains previous step review gate | `"Review the previous step" in prompt` |
| S9 | Render prompt for step 0 → no review gate, has "No previous step" | `"No previous step" in prompt` |
| S10 | CLI `chw sample --out /tmp/wf.json` → JSON file created | `Path("/tmp/wf.json").exists()` |
| S11 | CLI `chw init --workflow wf.json --state state.json` → state created | `"workflow_name" in json.load(open("state.json"))` |
| S12 | CLI `chw status --state state.json` → colorful table output | subprocess output contains current_step and status |
| S13 | Parallel steps: two branches complete → merge advances | state.current_step advances when all branches done |
| S14 | Rollback to step 2 → state.current_step == 2 | `after rollback(2), state.current_step == 2` |

## 7. Manual QA Scripts

```bash
# QA-1: Full prompt-loop lifecycle
chw sample --out /tmp/wf.json
chw init --workflow /tmp/wf.json --state /tmp/state.json
chw next --workflow /tmp/wf.json --state /tmp/state.json --out /tmp/p1.txt
echo "✅ Scoped requirements" > /tmp/out1.txt
chw record --state /tmp/state.json --status ok --output /tmp/out1.txt
chw next --workflow /tmp/wf.json --state /tmp/state.json --out /tmp/p2.txt
grep -q "Review the previous step" /tmp/p2.txt && echo "✓ Self-review gate present"
chw status --state /tmp/state.json    # verify colorful output

# QA-2: python -m entry
python -m chwflow --version

# QA-3: Type checking
uv run basedpyright src/

# QA-4: Lint
uv run ruff check src/ tests/

# QA-5: Full test suite
uv run pytest -v

# QA-6: Automation runner (dry run)
chw run --workflow /tmp/wf.json --dry-run
```

## 8. PR Details

**PR Title**: `feat: aggressive rewrite — production-grade workflow engine v0.2.0`

**PR Body Template**:
```markdown
## Summary
Aggressive rewrite of `chat-history-to-fullauto-workflow` from a 230-line single-file CLI to a production-grade Python package (v0.2.0).

## What changed
- **Package**: `chwflow` (PyPI-ready via uv/hatchling), CLI entry `chw`
- **Architecture**: 16 source files, Pydantic v2 models, modular `src/chwflow/` layout
- **4 pattern controllers**: prompt-loop ✅, automation ✅, hybrid ✅, generator ✅
- **LLM closed loop**: optional `chwflow[llm]` extra with OpenAI + Anthropic adapters
- **State machine**: branching, parallel steps, conditional, rollback
- **UX**: Rich colored output, `chw status`, `chw watch`, `chw run`
- **Quality**: 100% type coverage, 7 test files, ruff+basedpyright+CI, MIT License
- **Examples**: code-review + data-migration workflow JSONs
- **Breaking**: old `scripts/prompt_loop_runner.py` deleted; old workflow.json schema auto-migrated

## How to test
```bash
uv sync --all-extras
uv run pytest -v
chw sample --out /tmp/wf.json
chw init --workflow /tmp/wf.json --state /tmp/state.json
chw next --workflow /tmp/wf.json --state /tmp/state.json
```

## Checklist
- [x] All tests pass
- [x] ruff clean
- [x] basedpyright clean
- [x] Manual QA completed
```

## 9. Open Risks

- **Upstream may reject aggressive breaking change**: mitigate by offering to maintain backward-compat shim if needed
- **uv not installed by user**: `pyproject.toml` also supports pip install if uv absent
- **LLM extras require API keys**: clearly document `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` env vars; adapters gracefully degrade to "no LLM configured" message
- **macOS-specific CI issues**: GH Actions runs ubuntu-latest by default; test matrix covers this
