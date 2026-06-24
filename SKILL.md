---
name: conversation-workflow-generator
description: Generate executable workflow scripts from visible conversation context, provided chat transcripts, or user-summarized history. Use when the user wants to derive, design, improve, or save a workflow from conversation history, recurring task patterns, prior corrections, preferences, unfinished plans, or "how we usually do this"; especially use when the user wants a self-reviewing prompt loop, agent workflow controller, executable automation script, CLI workflow runner, or script-based process that avoids long Markdown prompts.
---

# Conversation Workflow Generator

## Core Rule

Output executable scripts only. Do not output Markdown workflow documents, SOPs, cards, playbooks, BPMN text, or Codex skill drafts as the generated artifact.

The required deliverable is one or more runnable script files plus optional machine-readable config/state files such as JSON. The script may emit compact plain-text prompts for another agent, but the workflow itself must live in code/config rather than a long Markdown document.

Use only:

- The current visible thread.
- User-provided transcripts, summaries, files, or links.
- The `chw` CLI tool (`chw sample`, `chw init`, `chw next`, `chw record`) or the Python API (`from chwflow import ...`).

If the relevant history is not visible or retrievable, generate a script with explicit configurable assumptions instead of pretending to know hidden history.

## Script-First Workflow

1. Define the target outcome.
   - Identify the user's goal, desired final artifact, and success condition.
   - Choose a controller pattern: **prompt-loop**, **automation**, **hybrid**, or **generator**.
   - If another AI agent will execute the workflow over multiple turns, prefer the prompt-loop pattern.

2. Extract workflow evidence.
   - Capture repeated steps, prior corrections, preferences, constraints, tools, files, naming conventions, validation habits, and final-answer expectations.
   - Convert stable workflow knowledge into config values, acceptance criteria, or script constants.
   - Keep large history out of generated prompts; summarize it into state/config.

3. Choose the script pattern.
   - **Prompt-loop controller**: Stores workflow state, emits the next compact prompt, records the previous agent output, and requires review before advancing.
   - **Automation runner**: Runs deterministic local/API/CI steps with args, logs, retries, and exit codes.
   - **Hybrid handoff runner**: Produces prompts or tasks for humans/agents while tracking state and completion.
   - **Generator script**: Creates another script/config when the workflow itself must be parameterized.

4. Implement the script.
   - Use the `chw` CLI: `chw sample --out workflow.json`, `chw init --workflow workflow.json --state state.json`, `chw next`, `chw record`.
   - Or use the Python API: `from chwflow.controllers import PromptLoopController`.
   - Store mutable workflow progress in JSON state files via the StateMachine.
   - Every generated next-step prompt must include a self-review gate comparing previous output against acceptance criteria.

5. Add self-review when driving agents.
   - The prompt-loop controller enforces review gates automatically.
   - Statuses: `ok`, `needs_revision`, `blocked`.
   - The CLI supports auto-watching with `chw watch`.

6. Verify.
   - Use `chw run --dry-run` for automation workflows.
   - Run a sample `chw init → chw next → chw record → chw next` flow for prompt-loop scripts.

## Evidence Model

Track these fields and encode them into script/config:

| Field | Script Representation |
| --- | --- |
| Trigger | CLI command, config name, scheduler/webhook metadata |
| Goal | `"goal"` field in workflow JSON |
| Inputs | CLI args, env vars, config fields, files |
| Preferences | `"constraints"` field in workflow JSON |
| Steps | `"steps"` array in workflow JSON |
| Branches | `"depends_on"` per step, branch API in StateMachine |
| Actors | Agent/human/system labels in step metadata |
| Verification | `"acceptance"` per step |
| Done Signal | Exit code, final state, generated artifact |

## References

Read `references/script_patterns.md` when generating a script artifact or choosing between script patterns.

Use the `chw` CLI (`chw --help`) for discovery of available commands and options.
