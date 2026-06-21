# state/

This directory is the harness memory.

Models forget. Repositories remember.

## Files

| File | Format | Purpose |
|---|---|---|
| `tasks/<task-id>.md` | Markdown | Human-readable task spec |
| `tasks/<task-id>.json` | JSON | Loop state, status, iteration history, budgets |
| `token-usage.jsonl` | JSON Lines | Append-only token usage ledger, written by `token_report.py add` and `model_adapter.py` |
| `known-flakes.txt` | text | Known flaky tests, checks, or error fingerprints |

## Rules

- Prefer append-only records for audit trails.
- Do not store secrets, PII, credentials, private keys, or raw sensitive logs.
- Keep task state compact. Store facts and decisions, not long narrative transcripts.
- Cache discovery summaries and reuse them instead of rereading the whole repository.
- Commit state that is useful for collaboration and continuity; keep local experiments in `state/_local/`.
