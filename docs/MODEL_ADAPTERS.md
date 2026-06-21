# Model Adapters

The harness is client-agnostic, but `scripts/model_adapter.py` can call a model for checker/reviewer-style work.

It never runs by accident with paid providers. Default provider is `mock`.

## Providers

### Mock

No API key, no network, no cost.

```bash
LLM_PROVIDER=mock python3 scripts/goal_loop.py check \
  --task-id example-smoke \
  --evidence "verification passed"
```

### OpenAI

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=...
export LLM_MODEL_CHECKER=gpt-4o-mini

python3 scripts/goal_loop.py check \
  --task-id <task-id> \
  --evidence-file state/tasks/<task-id>.verification.md
```

### Anthropic

```bash
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=...
export LLM_MODEL_CHECKER=claude-sonnet-4-6

python3 scripts/goal_loop.py check \
  --task-id <task-id> \
  --evidence-file state/tasks/<task-id>.verification.md
```

### OpenAI-Compatible

Use this for gateways and providers with a Chat Completions compatible API.

```bash
export LLM_PROVIDER=openai-compatible
export LLM_BASE_URL=https://example.com/v1
export LLM_API_KEY=...
export LLM_MODEL_CHECKER=<model>
```

## Role Model Environment Variables

Role-specific model variables override `LLM_MODEL`:

```text
LLM_MODEL_EXPLORER
LLM_MODEL_IMPLEMENTER
LLM_MODEL_CHECKER
LLM_MODEL_VERIFIER_QUALITY
LLM_MODEL_VERIFIER_SECURITY
LLM_MODEL_VERIFIER_DEPENDENCY
```

## Token Ledger

Every adapter call appends to:

```text
state/token-usage.jsonl
```

Report usage:

```bash
python3 scripts/token_report.py report --days 1
```

