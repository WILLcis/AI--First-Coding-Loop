# skills/

Skills are loaded only when needed.

Do not load every skill into every task. That burns context and weakens active instructions.

Recommended pattern:

1. Read the task.
2. Pick the smallest relevant skill set.
3. Read only those skill files.
4. Record which skill was used in task state.

## Included Skills

- `context-economy/SKILL.md`: token budget, discovery cache, file-reading limits, and context hygiene.
- `slice-policy/SKILL.md`: defines a slice as the smallest verifiable result and prevents token-wasting micro-slices.

The top-level `context-economy.md` and `slice-policy.md` files are compatibility pointers for older prompts. New clients should load the `SKILL.md` files.
