# Example Smoke Task

Status: planned
Owner: AI agent
Created: 2026-06-21

## Goal

Verify that the universal AI-first harness can initialize a resumable task loop.

## Context

This is a non-code smoke task for validating the harness itself.

## Acceptance Criteria

- [ ] `scripts/goal_loop.py start` creates `state/tasks/example-smoke.json`.
- [ ] The emitted prompt includes remaining iteration and token budget.
- [ ] `scripts/token_report.py report` runs without error.

## Stop Condition

The task is done when the loop state exists and token reporting runs successfully.

## Scope

Allowed:

- Universal harness state files

Not allowed:

- Repository business code
- Remote services

## Verification

- [ ] `python3 scripts/goal_loop.py status --task-id example-smoke`
- [ ] `python3 scripts/token_report.py report --days 1`

## Budgets

- Max iterations: 3
- Max tokens: 10000
- Max initial discovery files: 3

## Open Questions

None.

## Run Log

- 2026-06-21: Created smoke task.

