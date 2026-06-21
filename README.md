# Universal AI-First Harness

This is a client-agnostic AI-first development harness.

It combines two layers:

- `AGENT_INSTRUCTIONS.md`: the portable safety and operating contract for any AI development client.
- `state/`, `agents/`, `skills/`, and `scripts/`: the lightweight runtime layer for continuous execution, token control, role separation, and resumable work.

It is intentionally not coupled to Codex, Claude Code, Cursor, GitHub, Linear, Sentry, or any specific model provider.

## Quick Start

Copy this directory into a repository, then:

1. Rename or mirror `AGENT_INSTRUCTIONS.md` into the instruction filename your client supports.
   - Portable default: `AGENTS.md`
   - Claude-style projects may also mirror it to `CLAUDE.md`
   - Other clients can paste or import the same content as their repo rules
2. Keep `state/` in the repository unless your project has a specific privacy reason not to.
3. Create a task file under `state/tasks/<task-id>.md`.
4. Start a loop:

```bash
python3 scripts/goal_loop.py start \
  --task-id <task-id> \
  --task-file state/tasks/<task-id>.md \
  --stop "<verifiable stop condition>" \
  --max-iterations 6 \
  --max-tokens 120000
```

5. Give the emitted compact prompt to your active AI client.
6. Or ask the harness to hand the prompt to a configured client runner:

```bash
python3 scripts/client_runner.py run \
  --task-id <task-id> \
  --role implementer
```

By default this is a dry-run that writes the prompt to `state/_local/prompts/`. See [docs/CLIENT_RUNNER.md](docs/CLIENT_RUNNER.md) to connect a real client command.

7. If you already have an active coding session, use [docs/ACTIVE_SESSION_ADOPTION.md](docs/ACTIVE_SESSION_ADOPTION.md) to attach it without restarting.
8. After each AI/client run, record the iteration:

```bash
python3 scripts/goal_loop.py record \
  --task-id <task-id> \
  --summary "<what changed and how it was verified>" \
  --verdict continue \
  --tokens <observed-token-count-if-known>
```

9. Ask the independent checker to judge whether the stop condition is met:

```bash
python3 scripts/goal_loop.py check \
  --task-id <task-id> \
  --evidence "<verification evidence or failure summary>"
```

By default this uses `LLM_PROVIDER=mock`. See [docs/MODEL_ADAPTERS.md](docs/MODEL_ADAPTERS.md) to connect OpenAI, Anthropic, or an OpenAI-compatible provider.

10. Append explicit token records if your client exposes usage outside the model adapter, then report usage:

```bash
python3 scripts/token_report.py add \
  --loop <task-id> \
  --role implementer \
  --model <model-name> \
  --input-tokens <n> \
  --output-tokens <n> \
  --client <client-name>

python3 scripts/token_report.py report --days 1
```

## Design Rules

- The repository state is the memory. The chat is not the memory.
- Load only the files needed for the current role and phase.
- A slice is the smallest verifiable result, not the smallest code edit.
- Use small/cheap roles for exploration and dependency checks; reserve strong models for implementation, security, architecture, and final review.
- A progress update is not an approval gate.
- Stop only for human judgment, missing authority, unsafe ambiguity, irreversible action, budget exhaustion, or a failed checker verdict.

## Directory Layout

```text
universal-ai-first-harness/
  AGENT_INSTRUCTIONS.md
  agents/
    explorer.toml
    implementer.toml
    checker.toml
    verifier-quality.toml
    verifier-security.toml
    verifier-dependency.toml
  skills/
    README.md
    context-economy/
      SKILL.md
    slice-policy/
      SKILL.md
    context-economy.md
    slice-policy.md
  state/
    README.md
    token-usage.jsonl
    known-flakes.txt
    tasks/
  scripts/
    client_runner.py
    goal_loop.py
    model_adapter.py
    token_report.py
  prompts/
    run-task.md
  templates/
    task.md
```

## What This Adds Over A Plain Instruction File

- Token budgets and reports
- Iteration limits
- Role/model tiers
- Slice policy to prevent token-wasting micro-slices
- Client-agnostic `SKILL.md` directories with legacy markdown pointers
- Model-assisted independent checker
- External client runner for implementer/checker prompts
- Compact run prompts
- External task state
- Discovery caching
- Stop-condition driven work
