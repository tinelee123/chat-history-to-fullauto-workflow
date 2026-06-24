# chwflow — Chat History to Full-Auto Workflow

Turn chat history into **executable, self-reviewing workflow scripts** that AI agents or humans can follow step by step.

Instead of long Markdown SOPs, `chwflow` compresses a workflow into:
1. A **JSON definition** (goals, steps, acceptance criteria)
2. A **JSON state file** (mutable runtime progress)
3. **Compact prompts** (current step only, with self-review gate)

## Installation

```bash
pip install chwflow
# or with LLM extras
pip install "chwflow[llm]"
```

## Quick Start

### 1. Create a sample workflow

```bash
chw sample --out my-workflow.json
```

### 2. Initialize state

```bash
chw init --workflow my-workflow.json --state state.json
```

### 3. Generate the next prompt for an AI agent

```bash
chw next --workflow my-workflow.json --state state.json --out next_prompt.txt
```

### 4. After the agent responds, record the result

```bash
chw record --state state.json --status ok --output agent_result.txt
```

### 5. Check workflow progress

```bash
chw status --state state.json
```

## Four Controller Patterns

### Prompt Loop (classic)

Multi-turn AI agent workflow with self-review gates. Each prompt includes:
- Current step objective
- Previous step review (output vs. acceptance criteria)
- Instructions to revise before advancing

```bash
chw next --workflow wf.json --state st.json
chw record --state st.json --status ok --output result.txt
```

### Automation Runner

Execute deterministic steps locally: shell commands, Python snippets, file checks.

```bash
chw run --workflow build-workflow.json
chw run --workflow build-workflow.json --dry-run
```

### Hybrid Handoff

Alternate between automated steps and human/agent review checkpoints. Steps marked `"review_required": true` pause for approval.

### Generator

Programmatically build parameterized workflow scripts and JSON configs.

```python
from chwflow.controllers import GeneratorController
gen = GeneratorController()
gen.generate_json("my-wf", "Do X", steps=[...], out_path="wf.json")
gen.generate_cli_script("my-tool", "A custom CLI tool", commands=[...], out_path="my-tool.py")
```

## LLM Closed Loop (optional)

With `chwflow[llm]` installed:

```python
from chwflow.adapters import OpenAIAdapter, AnthropicAdapter

# OpenAI
gpt = OpenAIAdapter(model="gpt-4o")  # Reads OPENAI_API_KEY from env
response = gpt.call("Summarize this pull request.")

# Anthropic
claude = AnthropicAdapter(model="claude-sonnet-4-20250514")
response = claude.call("Review this code for security vulnerabilities.")
```

## Example Workflows

- `examples/code-review-workflow.json` — Multi-step PR review with security/quality/verdict phases
- `examples/data-migration-workflow.json` — Database migration with snapshot, transform, verify

## Development

```bash
git clone https://github.com/tinelee123/chat-history-to-fullauto-workflow.git
cd chat-history-to-fullauto-workflow
pip install -e ".[dev]"
pytest -v
```

## License

MIT — see [LICENSE](LICENSE)
