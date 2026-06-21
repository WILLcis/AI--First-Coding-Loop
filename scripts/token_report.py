#!/usr/bin/env python3
"""Aggregate token usage from state/token-usage.jsonl."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TOKEN_LOG = ROOT / "state" / "token-usage.jsonl"


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def load_records(days: int) -> list[dict]:
    if not TOKEN_LOG.exists():
        return []
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    records: list[dict] = []
    for line in TOKEN_LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if parse_time(record["ts"]) >= since:
                records.append(record)
        except Exception:
            continue
    return records


def cmd_add(args: argparse.Namespace) -> int:
    TOKEN_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "loop": args.loop,
        "role": args.role,
        "model": args.model,
        "input_tokens": args.input_tokens,
        "output_tokens": args.output_tokens,
        "client": args.client,
    }
    with TOKEN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    records = load_records(args.days)
    by_loop = collections.Counter()
    by_role = collections.Counter()
    by_model = collections.Counter()
    total_in = 0
    total_out = 0

    for record in records:
        input_tokens = int(record.get("input_tokens", 0))
        output_tokens = int(record.get("output_tokens", 0))
        tokens = input_tokens + output_tokens
        total_in += input_tokens
        total_out += output_tokens
        by_loop[record.get("loop", "?")] += tokens
        by_role[record.get("role", "?")] += tokens
        by_model[record.get("model", "?")] += tokens

    payload = {
        "window_days": args.days,
        "records": len(records),
        "input_tokens": total_in,
        "output_tokens": total_out,
        "total_tokens": total_in + total_out,
        "by_loop": dict(by_loop.most_common()),
        "by_role": dict(by_role.most_common()),
        "by_model": dict(by_model.most_common()),
    }

    monthly_budget = int(args.monthly_budget or os.getenv("MONTHLY_TOKEN_BUDGET", "0") or 0)
    if monthly_budget:
        projected = int((total_in + total_out) * (30 / max(args.days, 1)))
        payload["projected_monthly_tokens"] = projected
        payload["monthly_budget"] = monthly_budget
        payload["budget_usage_pct"] = round(projected / monthly_budget * 100, 1)
        if projected / monthly_budget >= 0.8:
            payload["alert"] = "projected usage is at least 80% of monthly budget"

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"# Token Report · last {args.days} day(s)")
    print()
    print(f"- records: {payload['records']}")
    print(f"- input/output: {total_in:,} / {total_out:,}")
    print(f"- total: {total_in + total_out:,}")
    if "monthly_budget" in payload:
        print(f"- projected monthly: {payload['projected_monthly_tokens']:,}")
        print(f"- budget usage: {payload['budget_usage_pct']}%")
        if "alert" in payload:
            print(f"- alert: {payload['alert']}")
    print()
    print("## By Loop")
    for key, value in by_loop.most_common():
        print(f"- {key}: {value:,}")
    print()
    print("## By Role")
    for key, value in by_role.most_common():
        print(f"- {key}: {value:,}")
    print()
    print("## By Model")
    for key, value in by_model.most_common():
        print(f"- {key}: {value:,}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add")
    add.add_argument("--loop", required=True)
    add.add_argument("--role", required=True)
    add.add_argument("--model", required=True)
    add.add_argument("--input-tokens", type=int, default=0)
    add.add_argument("--output-tokens", type=int, default=0)
    add.add_argument("--client", default="unknown")
    add.set_defaults(func=cmd_add)

    report = sub.add_parser("report")
    report.add_argument("--days", type=int, default=1)
    report.add_argument("--monthly-budget", type=int, default=0)
    report.add_argument("--format", choices=["markdown", "json"], default="markdown")
    report.set_defaults(func=cmd_report)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

