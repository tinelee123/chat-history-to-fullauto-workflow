# Script Patterns

Use these patterns to generate executable workflow artifacts. Do not generate Markdown workflow documents as final artifacts.

## Prompt-Loop Controller

Use when another AI agent should receive one compact prompt at a time.

Required files:

- `workflow_runner.py`: executable controller script, or reuse `scripts/prompt_loop_runner.py`.
- `workflow.json`: stable goal, constraints, steps, and acceptance criteria.
- `state.json`: mutable runtime state created by the script.

Required commands:

```text
python workflow_runner.py init --workflow workflow.json --state state.json
python workflow_runner.py next --workflow workflow.json --state state.json --out next_prompt.txt
python workflow_runner.py record --state state.json --status ok --output agent_output.txt
```

Prompt contract:

- Review previous output against previous acceptance criteria.
- If previous output fails, revise before advancing.
- Execute only the current step.
- Return status: `ok`, `needs_revision`, or `blocked`.

## Automation Runner

Use when the workflow is deterministic local/API/CI automation.

Script requirements:

- CLI args with `--help`.
- Dry run when actions are destructive or external.
- Structured logs or clear progress output.
- Exit code `0` on success and non-zero on failure.
- Idempotency check when duplicate work is possible.
- Configurable paths, credentials via env vars, and no hardcoded secrets.

## Hybrid Handoff Runner

Use when the workflow alternates between script actions and human/agent review.

Script requirements:

- Track each task state in JSON.
- Emit the next human/agent instruction as plain text.
- Record output/review files.
- Require acceptance criteria before advancing.
- Support `blocked` with a named missing input.

## Generated Script Quality

Every generated script should include:

- Runtime and file path.
- Clear CLI usage.
- Input validation.
- State/config format.
- Review or verification step.
- Minimal reproducible sample command.
- Syntax check or smoke test when possible.
