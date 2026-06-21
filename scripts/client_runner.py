#!/usr/bin/env python3
"""Run a role prompt through an external AI coding client.

This is the harness boundary between durable loop state and a real client
such as Codex CLI, Claude Code, Cursor CLI-like wrappers, or any custom agent.

Default behavior is dry-run: render the prompt and write it to state/_local.
No external command runs unless --execute is passed or CLIENT_RUNNER_AUTO=1.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import subprocess
from pathlib import Path

import goal_loop


ROOT = Path(__file__).resolve().parent.parent
LOCAL_DIR = ROOT / "state" / "_local"
PROMPT_DIR = LOCAL_DIR / "prompts"
RUN_DIR = LOCAL_DIR / "client-runs"


def now_slug() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_dirs() -> None:
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)


def render_prompt(task_id: str, role: str, evidence: str = "", evidence_file: str | None = None) -> str:
    state = goal_loop.load_state(task_id)
    if not state.get("stop_condition"):
        raise SystemExit(f"no initialized state for {task_id}")

    evidence_parts = []
    if evidence:
        evidence_parts.append(evidence)
    if evidence_file:
        path = Path(evidence_file)
        if not path.exists():
            raise SystemExit(f"evidence file not found: {path}")
        evidence_parts.append(path.read_text(encoding="utf-8")[:6000])
    joined_evidence = "\n\n".join(evidence_parts)

    if role == "checker":
        return goal_loop.checker_prompt(state, evidence=joined_evidence)
    return goal_loop.role_prompt(state, role=role)


def write_prompt(task_id: str, role: str, prompt: str) -> Path:
    ensure_dirs()
    path = PROMPT_DIR / f"{task_id}.{role}.{now_slug()}.md"
    path.write_text(prompt, encoding="utf-8")
    latest = PROMPT_DIR / f"{task_id}.{role}.latest.md"
    latest.write_text(prompt, encoding="utf-8")
    return path


def format_command(command: str, *, prompt_file: Path, task_id: str, role: str) -> str:
    return command.format(
        prompt_file=str(prompt_file),
        task_id=task_id,
        role=role,
    )


def run_command(
    command: str,
    *,
    prompt: str,
    prompt_file: Path,
    task_id: str,
    role: str,
    cwd: Path,
    shell: bool,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    formatted = format_command(command, prompt_file=prompt_file, task_id=task_id, role=role)
    if shell:
        return subprocess.run(
            formatted,
            input=None if "{prompt_file}" in command else prompt,
            text=True,
            capture_output=True,
            cwd=str(cwd),
            shell=True,
            timeout=timeout,
        )
    argv = shlex.split(formatted)
    return subprocess.run(
        argv,
        input=None if "{prompt_file}" in command else prompt,
        text=True,
        capture_output=True,
        cwd=str(cwd),
        timeout=timeout,
    )


def append_client_run(
    *,
    task_id: str,
    role: str,
    command: str,
    prompt_file: Path,
    returncode: int,
    stdout: str,
    stderr: str,
    dry_run: bool,
) -> Path:
    ensure_dirs()
    ts = now_slug()
    base = RUN_DIR / f"{ts}.{task_id}.{role}"
    record_path = Path(f"{base}.json")
    stdout_path = Path(f"{base}.stdout.md")
    stderr_path = Path(f"{base}.stderr.md")
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    record = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "task_id": task_id,
        "role": role,
        "command": command,
        "prompt_file": str(prompt_file),
        "returncode": returncode,
        "stdout_file": str(stdout_path),
        "stderr_file": str(stderr_path),
        "stdout_excerpt": stdout[:2000],
        "stderr_excerpt": stderr[:2000],
        "dry_run": dry_run,
    }
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state = goal_loop.load_state(task_id)
    state.setdefault("client_runs", []).append(record)
    if returncode != 0:
        state["status"] = "client_failed"
    goal_loop.save_state(state)
    return record_path


def cmd_run(args: argparse.Namespace) -> int:
    prompt = render_prompt(args.task_id, args.role, args.evidence, args.evidence_file)
    prompt_file = write_prompt(args.task_id, args.role, prompt)
    command = args.command or os.getenv("CLIENT_RUNNER_COMMAND", "")
    auto = args.execute or os.getenv("CLIENT_RUNNER_AUTO", "").lower() in {"1", "true", "yes"}

    if not command or not auto:
        record_path = append_client_run(
            task_id=args.task_id,
            role=args.role,
            command=command or "(dry-run: no command configured)",
            prompt_file=prompt_file,
            returncode=0,
            stdout=f"Prompt written to {prompt_file}\n\n{prompt}",
            stderr="",
            dry_run=True,
        )
        print(json.dumps({
            "mode": "dry-run",
            "task_id": args.task_id,
            "role": args.role,
            "prompt_file": str(prompt_file),
            "record_file": str(record_path),
            "note": "Pass --execute and --command, or set CLIENT_RUNNER_COMMAND plus CLIENT_RUNNER_AUTO=1, to run a client.",
        }, ensure_ascii=False, indent=2))
        return 0

    cwd = Path(args.cwd or ROOT)
    try:
        result = run_command(
            command,
            prompt=prompt,
            prompt_file=prompt_file,
            task_id=args.task_id,
            role=args.role,
            cwd=cwd,
            shell=args.shell,
            timeout=args.timeout,
        )
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        stdout = exc.stdout or ""
        stderr = f"client command timed out after {args.timeout}s\n{exc.stderr or ''}"
    except OSError as exc:
        returncode = 127
        stdout = ""
        stderr = f"client command failed to start: {exc}"

    record_path = append_client_run(
        task_id=args.task_id,
        role=args.role,
        command=command,
        prompt_file=prompt_file,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        dry_run=False,
    )
    print(json.dumps({
        "mode": "executed",
        "task_id": args.task_id,
        "role": args.role,
        "returncode": returncode,
        "prompt_file": str(prompt_file),
        "record_file": str(record_path),
    }, ensure_ascii=False, indent=2))
    return returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run")
    run.add_argument("--task-id", required=True)
    run.add_argument("--role", choices=["implementer", "checker"], default="implementer")
    run.add_argument("--evidence")
    run.add_argument("--evidence-file")
    run.add_argument("--command", help="Command template. Supports {prompt_file}, {task_id}, {role}.")
    run.add_argument("--execute", action="store_true", help="Actually run the configured command.")
    run.add_argument("--shell", action="store_true", help="Run command through the shell. Off by default.")
    run.add_argument("--cwd", help="Working directory for the client command. Defaults to harness root.")
    run.add_argument("--timeout", type=int, default=int(os.getenv("CLIENT_RUNNER_TIMEOUT", "1800")))
    run.set_defaults(func=cmd_run)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
