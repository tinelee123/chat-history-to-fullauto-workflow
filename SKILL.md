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
- Available local/app tools that are explicitly present in the session.

If the relevant history is not visible or retrievable, generate a script with explicit configurable assumptions instead of pretending to know hidden history.

## Script-First Workflow

1. Define the target outcome.
   - Identify the user's goal, desired final artifact, and success condition.
   - Identify whether the script should drive an AI agent, automate local work, call APIs, or coordinate mixed manual/automated steps.
   - If another AI agent will execute the workflow over multiple turns, generate a prompt-loop controller script.

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
   - Prefer Python for portability unless the user asks for Bash, PowerShell, JavaScript, or another runtime.
   - Include CLI help, arguments, input validation, error messages, and non-zero exits on failure.
   - Store mutable workflow progress in JSON or another structured state file.
   - Put stable workflow definition in JSON/config rather than repeating it in every prompt.
   - Emit plain text prompts or task instructions, not Markdown workflow documents.

5. Add self-review when driving agents.
   - Every generated next-step prompt must include a review gate for the previous step.
   - The review gate must compare the previous output against the previous step's acceptance criteria.
   - If the previous output is not acceptable, the prompt must instruct the agent to revise before advancing.
   - The script should support `ok`, `needs_revision`, and `blocked` statuses.

6. Verify.
   - Run syntax checks for generated scripts when possible.
   - Run a sample `init -> next -> record -> next` flow for prompt-loop scripts.
   - Confirm the second prompt includes previous output, acceptance criteria, and review instructions.

## Evidence Model

Track these fields and encode them into script/config:

| Field | Script Representation |
| --- | --- |
| Trigger | CLI command, config name, scheduler/webhook metadata, or script purpose |
| Goal | Config `goal` field or script constant |
| Inputs | CLI args, env vars, config fields, files, or stdin |
| Preferences | Config values, prompt constraints, default options |
| Constraints | Validation rules, prompt constraints, guardrails |
| Steps | Config `steps` array or functions |
| Branches | Conditional logic or status transitions |
| Actors | Agent/human/system labels in config |
| Verification | Acceptance criteria, tests, check functions |
| Done Signal | Exit code, final state, generated artifact, or summary output |

## Output Rules

- Generate script files, not Markdown process files.
- Use `.py`, `.js`, `.sh`, `.ps1`, or another executable extension.
- Use `.json` for workflow definitions, state, examples, or fixtures.
- If explaining usage, put brief comments, `--help`, or a short final summary outside the artifact.
- Do not generate `.md` workflow artifacts.
- Do not generate Codex `SKILL.md` files unless the user explicitly changes this requirement.
- Do not call an output a script unless it contains executable code or points to a concrete executable file.

## Prompt-Loop Requirements

When generating a script for multi-turn agent workflows:

- Provide commands to initialize state, emit the next prompt, and record results.
- Keep prompts compact by including only the current step, previous output summary, previous acceptance criteria, review instruction, and next action.
- Do not paste the full workflow into every prompt.
- Persist state outside the prompt.
- Allow retry without advancing when status is `needs_revision`.
- Mark the workflow blocked when required input is missing.
- End with a final summary prompt when all steps are complete.

Use `scripts/prompt_loop_runner.py` as the default skeleton unless the user needs another language/runtime.

## References

Read `references/script_patterns.md` when generating a script artifact or choosing between script patterns.
