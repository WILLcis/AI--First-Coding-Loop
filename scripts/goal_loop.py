#!/usr/bin/env python3
"""Client-agnostic goal loop state helper.

This script does not call an LLM. It manages durable loop state and emits a
compact prompt that can be handed to any AI development client.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "state" / "tasks"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def state_path(task_id: str) -> Path:
    return STATE_DIR / f"{task_id}.json"


def load_state(task_id: str) -> dict:
    path = state_path(task_id)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "task_id": task_id,
        "status": "pending",
        "iterations": [],
        "tokens_used": 0,
        "created_at": now(),
    }


def save_state(state: dict) -> None:
    state["updated_at"] = now()
    state_path(state["task_id"]).write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def compact_prompt(state: dict) -> str:
    task_id = state["task_id"]
    remaining_iterations = state["max_iterations"] - len(state["iterations"])
    remaining_tokens = state["max_tokens"] - state.get("tokens_used", 0)
    return f"""Read the repository agent instruction file and follow it.

Run task: {task_id}

Task file:
state/tasks/{task_id}.md

Loop state:
state/tasks/{task_id}.json

Stop condition:
{state["stop_condition"]}

Remaining budget:
- iterations: {remaining_iterations}
- tokens: {remaining_tokens}

Required behavior:
1. Use the context-economy skill.
2. Read only the smallest useful context.
3. Continue through routine phases without asking for approval.
4. Stop only for human judgment, unsafe ambiguity, missing authority, irreversible action, failed verification outside approved scope, or budget exhaustion.
5. After the run, update state/tasks/{task_id}.json and record a concise iteration summary.
"""


def cmd_start(args: argparse.Namespace) -> int:
    task_file = Path(args.task_file)
    if not task_file.exists():
        raise SystemExit(f"task file not found: {task_file}")

    state = load_state(args.task_id)
    if state["iterations"] and not args.force:
        raise SystemExit(
            f"state already exists for {args.task_id}; use resume or --force"
        )

    state.update(
        {
            "status": "running",
            "task_file": str(task_file),
            "task_excerpt": task_file.read_text(encoding="utf-8")[:4000],
            "stop_condition": args.stop,
            "max_iterations": args.max_iterations,
            "max_tokens": args.max_tokens,
            "tokens_used": 0,
            "iterations": [],
        }
    )
    save_state(state)
    print(compact_prompt(state))
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    state = load_state(args.task_id)
    if not state.get("stop_condition"):
        raise SystemExit(f"no initialized state for {args.task_id}")
    print(compact_prompt(state))
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    state = load_state(args.task_id)
    if not state.get("stop_condition"):
        raise SystemExit(f"no initialized state for {args.task_id}")

    iteration = {
        "ts": now(),
        "summary": args.summary,
        "verdict": args.verdict,
        "tokens": args.tokens,
    }
    state.setdefault("iterations", []).append(iteration)
    state["tokens_used"] = state.get("tokens_used", 0) + args.tokens

    if args.verdict == "done":
        state["status"] = "done"
    elif args.verdict == "stuck":
        state["status"] = "needs_human"
    elif len(state["iterations"]) >= state["max_iterations"]:
        state["status"] = "exhausted_iterations"
    elif state["tokens_used"] >= state["max_tokens"]:
        state["status"] = "exhausted_tokens"
    else:
        state["status"] = "running"

    save_state(state)
    print(json.dumps({
        "task_id": args.task_id,
        "status": state["status"],
        "iterations": len(state["iterations"]),
        "tokens_used": state["tokens_used"],
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    state = load_state(args.task_id)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    start = sub.add_parser("start")
    start.add_argument("--task-id", required=True)
    start.add_argument("--task-file", required=True)
    start.add_argument("--stop", required=True)
    start.add_argument("--max-iterations", type=int, default=6)
    start.add_argument("--max-tokens", type=int, default=120000)
    start.add_argument("--force", action="store_true")
    start.set_defaults(func=cmd_start)

    resume = sub.add_parser("resume")
    resume.add_argument("--task-id", required=True)
    resume.set_defaults(func=cmd_resume)

    record = sub.add_parser("record")
    record.add_argument("--task-id", required=True)
    record.add_argument("--summary", required=True)
    record.add_argument("--verdict", choices=["continue", "done", "stuck"], required=True)
    record.add_argument("--tokens", type=int, default=0)
    record.set_defaults(func=cmd_record)

    status = sub.add_parser("status")
    status.add_argument("--task-id", required=True)
    status.set_defaults(func=cmd_status)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

