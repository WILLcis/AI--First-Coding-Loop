# Client Runner

`scripts/client_runner.py` connects the harness loop to an external AI coding client.

It is intentionally conservative:

- Default is dry-run.
- It writes the prompt to `state/_local/prompts/`.
- It does not run any external command unless `--execute` is passed or `CLIENT_RUNNER_AUTO=1`.
- Client stdout/stderr are stored under `state/_local/client-runs/`.
- `state/_local/` is ignored by git.

## Dry Run

Generate the implementer prompt without running a client:

```bash
python3 scripts/client_runner.py run \
  --task-id <task-id> \
  --role implementer
```

Generate a checker prompt:

```bash
python3 scripts/client_runner.py run \
  --task-id <task-id> \
  --role checker \
  --evidence "verification passed"
```

## Execute A Client

Use a command template with `{prompt_file}`:

```bash
python3 scripts/client_runner.py run \
  --task-id <task-id> \
  --role implementer \
  --command 'your-agent-cli --prompt-file {prompt_file}' \
  --execute
```

If your client reads prompt from stdin, omit `{prompt_file}`:

```bash
python3 scripts/client_runner.py run \
  --task-id <task-id> \
  --role implementer \
  --command 'your-agent-cli run' \
  --execute
```

## Environment Mode

```bash
export CLIENT_RUNNER_COMMAND='your-agent-cli --prompt-file {prompt_file}'
export CLIENT_RUNNER_AUTO=1

python3 scripts/client_runner.py run --task-id <task-id> --role implementer
```

## Examples

These are examples only. Exact CLI flags vary by client/version.

```bash
# Generic prompt-file style
python3 scripts/client_runner.py run \
  --task-id <task-id> \
  --command 'agent-cli --prompt-file {prompt_file}' \
  --execute

# Generic stdin style
python3 scripts/client_runner.py run \
  --task-id <task-id> \
  --command 'agent-cli run' \
  --execute
```

## Safety

Avoid `--shell` unless your command truly needs shell features. Without `--shell`, the command is split with `shlex` and executed directly.

The runner does not interpret success as task completion. After a client run, use:

```bash
python3 scripts/goal_loop.py record ...
python3 scripts/goal_loop.py check ...
```
