#!/usr/bin/env python3
"""Client-agnostic goal loop state helper.

This script manages durable loop state, emits compact prompts, and can call an
independent checker model through scripts/model_adapter.py.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

import model_adapter


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
    return role_prompt(state, role="implementer")


def role_prompt(state: dict, *, role: str) -> str:
    task_id = state["task_id"]
    remaining_iterations = state["max_iterations"] - len(state["iterations"])
    remaining_tokens = state["max_tokens"] - state.get("tokens_used", 0)
    if role == "checker":
        return checker_prompt(state)

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
2. Use the slice-policy skill.
3. Read only the smallest useful context.
4. Continue through routine phases without asking for approval.
5. Work in the smallest verifiable result, not the smallest code edit.
6. Stop only for human judgment, unsafe ambiguity, missing authority, irreversible action, failed verification outside approved scope, or budget exhaustion.
7. After the run, update state/tasks/{task_id}.json and record a concise iteration summary.
"""


def checker_prompt(state: dict, evidence: str = "") -> str:
    task_id = state["task_id"]
    iterations = state.get("iterations", [])
    checks = state.get("checks", [])
    recent_iterations = "\n".join(
        f"- {i + 1}. verdict={item.get('verdict', '?')} summary={item.get('summary', '')[:500]}"
        for i, item in enumerate(iterations[-6:])
    ) or "- none"
    recent_checks = "\n".join(
        f"- {item.get('ts', '?')}: {item.get('verdict', '?')} {item.get('reason', '')[:300]}"
        for item in checks[-3:]
    ) or "- none"
    return f"""You are the independent checker agent.

You must not write code. Judge only whether the stop condition is satisfied.

Return your verdict with the first line exactly one of:
done
continue
stuck

Task id:
{task_id}

Task excerpt:
{state.get('task_excerpt', '')[:3000]}

Stop condition:
{state.get('stop_condition', '')}

Current status:
{state.get('status', '')}

Recent implementer iterations:
{recent_iterations}

Recent checker history:
{recent_checks}

Verification evidence:
{evidence or state.get('last_evidence', 'No explicit evidence provided.')}

Judge using these rules:
- done: stop condition is met with concrete evidence.
- continue: next step is safe, in scope, and likely to advance the same slice.
- stuck: human decision, missing authority, unsafe ambiguity, irreversible action, out-of-scope repair, or budget exhaustion is required.

Also flag micro-slicing if the work is only reading files, writing plans, or making tiny unverifiable edits.
"""


def parse_verdict(text: str) -> str:
    first = (text.splitlines()[0] if text else "").strip().lower()
    first = re.sub(r"[^a-z]", "", first)
    if first in {"done", "continue", "stuck"}:
        return first
    lowered = text.lower()
    if "done" in lowered and "continue" not in lowered:
        return "done"
    if "stuck" in lowered or "blocked" in lowered:
        return "stuck"
    return "continue"


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
    print(role_prompt(state, role=args.role))
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
    if args.evidence:
        iteration["evidence"] = args.evidence
        state["last_evidence"] = args.evidence
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


def cmd_prompt(args: argparse.Namespace) -> int:
    state = load_state(args.task_id)
    if not state.get("stop_condition"):
        raise SystemExit(f"no initialized state for {args.task_id}")
    evidence = read_evidence(args)
    if args.role == "checker":
        print(checker_prompt(state, evidence=evidence))
    else:
        print(role_prompt(state, role=args.role))
    return 0


def read_evidence(args: argparse.Namespace) -> str:
    evidence_parts: list[str] = []
    if getattr(args, "evidence", None):
        evidence_parts.append(args.evidence)
    if getattr(args, "evidence_file", None):
        evidence_path = Path(args.evidence_file)
        if evidence_path.exists():
            evidence_parts.append(evidence_path.read_text(encoding="utf-8")[:6000])
        else:
            raise SystemExit(f"evidence file not found: {evidence_path}")
    return "\n\n".join(part for part in evidence_parts if part)


def apply_checker_verdict(state: dict, verdict: str, reason: str, result: model_adapter.ModelResult, evidence: str) -> None:
    check = {
        "ts": now(),
        "verdict": verdict,
        "reason": reason[:2000],
        "provider": result.provider,
        "model": result.model,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "mocked": result.mocked,
    }
    if evidence:
        check["evidence_excerpt"] = evidence[:1000]
        state["last_evidence"] = evidence[:4000]
    state.setdefault("checks", []).append(check)
    state["tokens_used"] = state.get("tokens_used", 0) + result.input_tokens + result.output_tokens

    if verdict == "done":
        state["status"] = "done"
    elif verdict == "stuck":
        state["status"] = "needs_human"
    elif len(state.get("iterations", [])) >= state.get("max_iterations", 0):
        state["status"] = "exhausted_iterations"
    elif state.get("tokens_used", 0) >= state.get("max_tokens", 0):
        state["status"] = "exhausted_tokens"
    else:
        state["status"] = "running"


def cmd_check(args: argparse.Namespace) -> int:
    state = load_state(args.task_id)
    if not state.get("stop_condition"):
        raise SystemExit(f"no initialized state for {args.task_id}")
    evidence = read_evidence(args)
    prompt = checker_prompt(state, evidence=evidence)
    result = model_adapter.summarize(
        prompt,
        role="checker",
        loop=args.task_id,
        provider=args.provider,
        model=args.model,
    )
    verdict = parse_verdict(result.text)
    apply_checker_verdict(state, verdict, result.text, result, evidence)
    save_state(state)
    print(json.dumps({
        "task_id": args.task_id,
        "verdict": verdict,
        "status": state["status"],
        "provider": result.provider,
        "model": result.model,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "mocked": result.mocked,
        "reason": result.text,
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
    resume.add_argument("--role", choices=["implementer", "checker"], default="implementer")
    resume.set_defaults(func=cmd_resume)

    record = sub.add_parser("record")
    record.add_argument("--task-id", required=True)
    record.add_argument("--summary", required=True)
    record.add_argument("--verdict", choices=["continue", "done", "stuck"], required=True)
    record.add_argument("--tokens", type=int, default=0)
    record.add_argument("--evidence")
    record.set_defaults(func=cmd_record)

    prompt = sub.add_parser("prompt")
    prompt.add_argument("--task-id", required=True)
    prompt.add_argument("--role", choices=["implementer", "checker"], default="implementer")
    prompt.add_argument("--evidence")
    prompt.add_argument("--evidence-file")
    prompt.set_defaults(func=cmd_prompt)

    check = sub.add_parser("check")
    check.add_argument("--task-id", required=True)
    check.add_argument("--evidence")
    check.add_argument("--evidence-file")
    check.add_argument("--provider")
    check.add_argument("--model")
    check.set_defaults(func=cmd_check)

    status = sub.add_parser("status")
    status.add_argument("--task-id", required=True)
    status.set_defaults(func=cmd_status)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
