# Chat History to Full-Auto Workflow

A Codex skill for turning visible chat history or user-provided conversation transcripts into executable, self-reviewing workflow scripts.

Instead of producing long Markdown SOPs or playbooks, this skill generates script-based workflow controllers. The default pattern is a prompt loop: the script stores workflow state, emits the next compact prompt for an AI agent, records the previous output, and requires the next prompt to review that previous output before advancing.

## What It Generates

- Runnable workflow scripts such as Python, PowerShell, Bash, or JavaScript.
- JSON workflow definitions for goals, constraints, steps, and acceptance criteria.
- JSON state files for multi-turn execution.
- Compact plain-text prompts for the next agent step.

It does not generate Markdown workflow documents as the final artifact.

## Included Files

- `SKILL.md` - the Codex skill instructions.
- `scripts/prompt_loop_runner.py` - a reusable prompt-loop controller.
- `references/script_patterns.md` - script-only workflow generation patterns.
- `agents/openai.yaml` - UI metadata for the skill.

## Prompt Loop Example

Create a sample workflow:

```bash
python scripts/prompt_loop_runner.py sample --out workflow.json
```

Initialize state:

```bash
python scripts/prompt_loop_runner.py init --workflow workflow.json --state state.json
```

Generate the next prompt:

```bash
python scripts/prompt_loop_runner.py next --workflow workflow.json --state state.json --out next_prompt.txt
```

After the agent responds, record the result:

```bash
python scripts/prompt_loop_runner.py record --state state.json --status ok --output agent_output.txt
```

The next generated prompt will include a self-review gate for the previous output before continuing.

## Core Idea

Conversation history is useful, but sending a long workflow document to an agent every turn wastes context. This skill compresses the stable workflow into code and structured state, then sends only the current step, the previous result, acceptance criteria, and the next action.
