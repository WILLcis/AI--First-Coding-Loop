# Run Task Prompt

Read the repository agent instruction file and follow it.

Task:

`state/tasks/<task-id>.md`

Loop state:

`state/tasks/<task-id>.json`

Rules:

1. Use `skills/context-economy/SKILL.md`.
2. Use `skills/slice-policy/SKILL.md`.
3. Continue working unless a real stop condition is met.
4. Read only the smallest useful context.
5. Use cached discovery if present.
6. Update task state after each meaningful slice, not after every tiny step.
7. Do not treat progress updates as approval gates.
8. Stop only for human judgment, missing authority, unsafe ambiguity, irreversible action, failed checker verdict, or budget exhaustion.

Optional automation:

- Use `scripts/client_runner.py run --task-id <task-id> --role implementer` to render or execute the implementer prompt.
- Use `scripts/goal_loop.py check --task-id <task-id> --evidence "<verification evidence>"` for independent checker judgment.
- Do not treat a successful client command as completion; completion still requires checker verdict and verification evidence.

Final handoff:

- status
- changed files
- verification
- token/iteration usage if known
- risks and next step
