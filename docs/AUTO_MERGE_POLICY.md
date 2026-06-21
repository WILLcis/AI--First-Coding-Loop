# Auto Merge Policy

CI passing should not be treated as a human approval gate.

When a pull request is in scope for the active task, merge or enable platform auto-merge without asking the human if all merge gates are satisfied.

## Required Merge Gates

All of these must be true:

- Acceptance criteria are met or explicitly revised in task state.
- The independent checker verdict is `done`, or the task state contains equivalent done evidence.
- Required CI/status checks are passing, with no required checks pending, skipped unexpectedly, or cancelled.
- Required reviews and branch protection rules are satisfied.
- There are no unresolved requested changes or actionable review threads.
- The branch is up to date, accepted by the merge queue, or merge policy permits the current state.
- The merge affects only the approved task scope.
- No secrets, local credentials, or private artifacts are included.

## Continue Instead Of Asking

Continue without asking when:

- CI fails for an in-scope reason: fix, verify locally, push, and wait for CI again.
- CI passes but the merge queue is pending: wait/poll if the client can do so within budget.
- Platform auto-merge is available but immediate merge is blocked only by pending required checks: enable auto-merge if policy allows it.
- A routine post-merge step is mechanically implied, such as updating task state, deleting a feature branch, or starting the next planned slice.

## Stop And Ask

Stop and ask when:

- A required human/product decision remains.
- A reviewer requested changes and the intended resolution is not mechanical or in scope.
- Branch protection requires a permission the agent does not have.
- The merge would trigger a production deploy that the project has not explicitly defined as routine, reversible, and covered by gates.
- The merge includes migrations, destructive operations, paid actions, legal/compliance changes, or other irreversible effects.
- CI is green only because checks were skipped, disabled, or are known flaky without an approved waiver.
- The branch contains unrelated or user-owned changes whose ownership is unclear.

## Merge Is Not The Final Stop

After merge:

1. Record the merge result in task state.
2. Record token/iteration usage when available.
3. Continue to the next planned slice if one exists and budgets allow.
4. Only final-handoff when the task stop condition is truly met or a real stop rule applies.
