# Active Session Adoption Prompt

Use this when an AI coding session is already working and you want to attach it to this harness without restarting.

Paste the prompt below into the active session.

```text
From now on, attach the current work to the repository AI-first harness. You should do the adoption work yourself; do not ask me to create files manually.

Goal:
Turn the current session's task into durable repository state, then continue from the current progress.

Steps:

1. Read the repository agent instruction file:
   - Prefer AGENTS.md if present.
   - Otherwise look for *agent*.md, *instruction*.md, CLAUDE.md, or README.md sections relevant to agent work.

2. Confirm or create the state structure:
   - state/tasks/
   - state/_local/
   - skills/
   - prompts/

   If this repository uses .agent-loop/ instead of state/, use:
   - .agent-loop/tasks/
   - .agent-loop/runs/
   - .agent-loop/skills/
   - .agent-loop/prompts/

3. If a context economy skill is missing, create it. It must say:
   - Load only the smallest context needed for the current phase.
   - Prefer discovery cache over rediscovery.
   - Do not repeatedly read full README files, full instructions, full logs, or full histories.
   - Progress updates are not approval gates.
   - Continue by default. Stop only for human judgment, missing authority, unsafe ambiguity, irreversible action, budget exhaustion, or out-of-scope repair.

   Also ensure a slice policy exists. It must say:
   - A slice is the smallest verifiable result, not the smallest code edit.
   - Do not create separate slices for read-only discovery, planning, one-line edits, or phase transitions.
   - A good slice includes behavior, implementation, verification evidence, and compact records.
   - Fold tiny mechanical steps into the current slice.

4. Generate a task id:
   - Format: YYYYMMDD-short-topic.
   - If the session already has a branch, issue, ticket, or task id, reuse it.

5. Create the task file:
   - state/tasks/<task-id>.md
   - or .agent-loop/tasks/<task-id>.md if this repo uses .agent-loop/

   Include:
   - Goal
   - Context: what this active session already did and what remains
   - Acceptance Criteria
   - Stop Condition
   - Scope: allowed and not allowed
   - Verification commands
   - Budgets:
     - Max iterations: 6
     - Max token budget: 120000
     - Max initial discovery files: 12
   - Open Questions
   - Run Log: "Adopted from active session"

6. Create a compact discovery cache:
   - state/tasks/<task-id>.discovery.md
   - or .agent-loop/runs/<task-id>/discovery.md

   Do not rescan the whole repository. Summarize known facts from the current chat, current diff, key files, risks, and verification commands.

7. Create or update the current plan:
   - state/tasks/<task-id>.plan.md
   - or .agent-loop/runs/<task-id>/plan.md

8. Continue from the current progress. Do not redo completed work.

Execution rules:

- Do not stop between PLAN / BUILD / VERIFY / RECORD just to ask for approval.
- Do not create micro-slices. Work in the smallest verifiable result.
- Stop only for human judgment, missing authority, unsafe ambiguity, irreversible action, out-of-scope change, or budget exhaustion.
- A progress update is not an approval gate.
- After meaningful progress, update task state and run records.

Start adoption now, then continue until the acceptance criteria are met or the task is genuinely blocked.
```
