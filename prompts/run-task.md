# Run Task Prompt

Read the repository agent instruction file and follow it.

Task:

`state/tasks/<task-id>.md`

Loop state:

`state/tasks/<task-id>.json`

Rules:

1. Use `skills/context-economy.md`.
2. Continue working unless a real stop condition is met.
3. Read only the smallest useful context.
4. Use cached discovery if present.
5. Update task state after each meaningful step.
6. Do not treat progress updates as approval gates.
7. Stop only for human judgment, missing authority, unsafe ambiguity, irreversible action, failed checker verdict, or budget exhaustion.

Final handoff:

- status
- changed files
- verification
- token/iteration usage if known
- risks and next step

