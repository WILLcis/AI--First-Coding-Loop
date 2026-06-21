---
name: context-economy
description: Keep AI coding loops token-efficient by using targeted discovery, cached summaries, small relevant file reads, and role-specific context. Use for every non-trivial agent loop, when starting or resuming a task, when token usage is rising too quickly, or when an agent is repeatedly rereading instructions, logs, repository structure, or unrelated files.
---

# Context Economy

Use this skill to keep the agent effective without repeatedly loading large context.

## Rules

1. Read task state first.
2. Read only instruction sections relevant to the current phase.
3. Prefer cached discovery summaries over rescanning the repository.
4. Prefer `rg`, file lists, and targeted line reads over whole-file dumps.
5. Limit initial discovery to project identity, stack, commands, and likely touched files.
6. Do not load more than 5 large files before forming a plan.
7. Do not load more than 2 skills for a single phase unless a blocker requires it.
8. Summarize long outputs into state files; do not paste long logs into future prompts.
9. Use the cheapest capable role/model for exploration and mechanical checks.
10. Stop when token or iteration budget is exhausted.

## Suggested Budgets

| Phase | File Reads | Context Target |
|---|---:|---:|
| Intake | 1-3 files | tiny |
| Discovery | 5-12 targeted files | small |
| Plan | task + discovery summary | small |
| Build | changed files + nearby patterns | medium |
| Verify | command output summaries | small |
| Review | diff + tests + acceptance criteria | medium |

## Red Flags

- Rereading full README/instructions every iteration
- Loading all skills "just in case"
- Copying full test logs into task files
- Re-discovering unchanged repository structure
- Using a strong model for file search or dependency listing
