# Script Patterns

Four controller patterns supported by `chwflow`. Use these to decide the right architecture for any workflow.

## Prompt-Loop Controller

Use when another AI agent should receive one compact prompt at a time with self-review gates.

```bash
chw sample --out workflow.json
chw init --workflow workflow.json --state state.json
chw next --workflow workflow.json --state state.json --out next_prompt.txt
# ... agent responds ...
chw record --state state.json --status ok --output agent_result.txt
```

Prompt contract (embedded in every generated prompt):
1. Review previous output against previous acceptance criteria.
2. If previous output fails, revise before advancing.
3. Execute only the current step.
4. Return status: `ok`, `needs_revision`, or `blocked`.

Python API:
```python
from chwflow.controllers import PromptLoopController
ctrl = PromptLoopController.from_files("workflow.json", "state.json")
ctrl.init()
prompt = ctrl.next_prompt()
ctrl.record("ok", output="agent result")
```

## Automation Runner

Use when the workflow is deterministic local/API/CI automation.

```bash
chw run --workflow automation-workflow.json
chw run --workflow automation-workflow.json --dry-run
```

Step actions support:
- `"action": "shell command"` — Execute via subprocess
- `"action": {"shell": "..."}` — Same as above, explicit
- `"action": {"python": "result = 2 + 3"}` — Execute inline Python
- `"action": {"check_file": "path/to/file"}` — Verify file exists

Python API:
```python
from chwflow.controllers import AutomationController
ctrl = AutomationController.from_files("workflow.json")
results = ctrl.execute()
print(ctrl.summary())
```

## Hybrid Handoff Runner

Use when the workflow alternates between script actions and human/agent review checkpoints.

Steps with `"review_required": true` pause execution until approved/rejected.

Python API:
```python
from chwflow.controllers import HybridController
ctrl = HybridController.from_files("workflow.json")
results = ctrl.run_automated()
if ctrl.pending_checkpoint:
    ctrl.approve_checkpoint("LGTM")
```

## Generator Script

Use to programmatically create parameterized workflows and CLI scripts.

Python API:
```python
from chwflow.controllers import GeneratorController
gen = GeneratorController()
gen.generate_json("deploy", "Deploy to production", steps=[...], out_path="deploy.json")
gen.generate_cli_script("deployer", "Production deployment tool", commands=[...], out_path="deployer.py")
```

## State Machine

All patterns share the same `StateMachine` for tracking progress:

- Linear advancement: `advance()`, `record("ok")`
- Retry without advancing: `record("needs_revision")`
- Block on missing input: `record("blocked")`
- Rollback to any step: `rollback(target_step)`
- Parallel branches: `start_branch()`, `advance_branch()`, `all_branches_done()`
