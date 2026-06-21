#!/usr/bin/env python3
"""Provider-neutral model adapter for checker/reviewer style calls.

Supported providers:
- mock / dry-run: deterministic local response, no network
- openai: OpenAI Chat Completions API
- anthropic: Anthropic Messages API
- openai-compatible: any Chat Completions compatible endpoint via LLM_BASE_URL

This adapter is intentionally small and dependency-free.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
TOKEN_LOG = ROOT / "state" / "token-usage.jsonl"


@dataclass
class ModelResult:
    text: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    mocked: bool = False


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def env_name_for_role(role: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", role).strip("_").upper()
    return f"LLM_MODEL_{normalized}"


def resolve_provider(provider: str | None = None) -> str:
    return (provider or os.getenv("LLM_PROVIDER") or "mock").strip().lower()


def resolve_model(role: str, model: str | None = None) -> str:
    return (
        model
        or os.getenv(env_name_for_role(role))
        or os.getenv("LLM_MODEL")
        or "mock-model"
    )


def record_token_usage(
    *,
    loop: str,
    role: str,
    model: str,
    provider: str,
    input_tokens: int,
    output_tokens: int,
    mocked: bool = False,
) -> None:
    TOKEN_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": now(),
        "loop": loop,
        "role": role,
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "mocked": mocked,
    }
    with TOKEN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def rough_tokens(text: str) -> int:
    # Cheap approximation for providers that do not return usage.
    return max(1, len(text) // 4)


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"model provider HTTP {exc.code}: {body}") from exc


def mock_response(prompt: str, role: str) -> str:
    lower = prompt.lower()
    if role == "checker":
        if "verification evidence" in lower and (
            "passed" in lower
            or "success" in lower
            or "all checks passed" in lower
        ):
            return "done\nMock checker found passing verification evidence."
        if "blocked" in lower or "missing credential" in lower or "permission denied" in lower:
            return "stuck\nMock checker found a blocker phrase."
        return "continue\nMock checker needs concrete verification evidence before done."
    return "continue\nMock model is configured; no external provider was called."


def call_openai(prompt: str, role: str, model: str, provider: str) -> ModelResult:
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("missing LLM_API_KEY or OPENAI_API_KEY")
    base = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": f"You are the {role} agent."},
            {"role": "user", "content": prompt},
        ],
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0")),
        "max_tokens": int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1200")),
    }
    data = post_json(
        f"{base}/chat/completions",
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        payload,
    )
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return ModelResult(
        text=text,
        provider=provider,
        model=model,
        input_tokens=int(usage.get("prompt_tokens", rough_tokens(prompt))),
        output_tokens=int(usage.get("completion_tokens", rough_tokens(text))),
    )


def call_anthropic(prompt: str, role: str, model: str, provider: str) -> ModelResult:
    api_key = os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("missing LLM_API_KEY or ANTHROPIC_API_KEY")
    payload = {
        "model": model,
        "max_tokens": int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "1200")),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0")),
        "system": f"You are the {role} agent.",
        "messages": [{"role": "user", "content": prompt}],
    }
    data = post_json(
        "https://api.anthropic.com/v1/messages",
        {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": os.getenv("ANTHROPIC_VERSION", "2023-06-01"),
        },
        payload,
    )
    parts = data.get("content", [])
    text = "".join(part.get("text", "") for part in parts if part.get("type") == "text")
    usage = data.get("usage", {})
    return ModelResult(
        text=text,
        provider=provider,
        model=model,
        input_tokens=int(usage.get("input_tokens", rough_tokens(prompt))),
        output_tokens=int(usage.get("output_tokens", rough_tokens(text))),
    )


def summarize(
    prompt: str,
    *,
    role: str,
    loop: str = "goal_loop",
    provider: str | None = None,
    model: str | None = None,
    record_usage: bool = True,
) -> ModelResult:
    used_provider = resolve_provider(provider)
    used_model = resolve_model(role, model)

    if used_provider in {"mock", "dry-run", "dryrun", "none"}:
        result = ModelResult(
            text=mock_response(prompt, role),
            provider=used_provider,
            model=used_model,
            input_tokens=rough_tokens(prompt),
            output_tokens=rough_tokens(mock_response(prompt, role)),
            mocked=True,
        )
    elif used_provider in {"openai", "openai-compatible"}:
        result = call_openai(prompt, role, used_model, used_provider)
    elif used_provider == "anthropic":
        result = call_anthropic(prompt, role, used_model, used_provider)
    else:
        raise RuntimeError(f"unsupported LLM_PROVIDER: {used_provider}")

    if record_usage:
        record_token_usage(
            loop=loop,
            role=role,
            provider=result.provider,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            mocked=result.mocked,
        )
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", default="checker")
    parser.add_argument("--loop", default="manual")
    parser.add_argument("--prompt-file")
    parser.add_argument("--prompt")
    args = parser.parse_args()

    prompt = args.prompt or ""
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    if not prompt:
        raise SystemExit("provide --prompt or --prompt-file")

    result = summarize(prompt, role=args.role, loop=args.loop)
    print(result.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

