"""Three offline exercise groups. Request sketches are never sent."""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys


def parse_task(text: str) -> dict[str, object]:
    """Decode JSON, then validate the small teaching task contract."""
    try:
        task = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("invalid_json") from error
    if not isinstance(task, dict) or set(task) != {"goal", "max_steps"}:
        raise ValueError("invalid_fields")
    if not isinstance(task["goal"], str) or not task["goal"].strip():
        raise ValueError("invalid_goal")
    if type(task["max_steps"]) is not int or not 1 <= task["max_steps"] <= 10:
        raise ValueError("invalid_budget")
    return task


async def simulate_observation(tool: str) -> dict[str, object]:
    await asyncio.sleep(0)
    return {"tool": tool, "ok": True, "source": "fixture"}


def inspect_environment(root: Path) -> dict[str, object]:
    """Local observations only; no package installation or credential lookup."""
    root = Path(root)
    return {
        "python": ".".join(map(str, sys.version_info[:3])),
        "supported_python": (3, 11) <= sys.version_info[:2] < (3, 14),
        "in_virtual_environment": sys.prefix != sys.base_prefix,
        "repository_root_ok": all((root / p).is_file()
                                  for p in ("book/OUTLINE.md", "chapter3/agent_loop.py")),
        "network_access": False, "provider_status": "not_run",
    }


def build_request(provider: str, protocol: str, model: str, prompt: str) -> dict[str, object]:
    """A safe request sketch, not an HTTP client or capability detector."""
    routes = {
        ("openai", "responses"): ("https://api.openai.com/v1/responses", "OPENAI_API_KEY"),
        ("deepseek", "chat"): ("https://api.deepseek.com/chat/completions", "DEEPSEEK_API_KEY"),
        ("deepseek", "responses"): ("https://api.deepseek.com/responses", "DEEPSEEK_API_KEY"),
        ("anthropic", "messages"): ("https://api.anthropic.com/v1/messages", "ANTHROPIC_API_KEY"),
    }
    if (provider, protocol) not in routes:
        raise ValueError("unsupported_teaching_route")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("missing_model")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("missing_prompt")
    endpoint, key_variable = routes[provider, protocol]
    body: dict[str, object] = {"model": model}
    if protocol == "responses":
        body["input"] = prompt
    else:
        body["messages"] = [{"role": "user", "content": prompt}]
    if protocol == "messages":
        body["max_tokens"] = 128
    return {"provider": provider, "protocol": protocol, "endpoint": endpoint,
            "key_variable": key_variable, "body": body, "network_access": False,
            "provider_status": "not_run"}


def classify_error(status: int | None, *, code: str = "", kind: str = "") -> dict[str, object]:
    """Conservative teaching diagnosis, never executes retries."""
    if status is None:
        action = {"import": "check_interpreter", "json": "fix_json",
                  "timeout": "inspect_before_retry", "connection": "check_network"}.get(kind, "inspect_error")
        receipt = "not_sent" if kind in {"import", "json"} else "unknown"
    else:
        receipt = "http_response_received"
        action = {400: "fix_request", 401: "check_credentials", 402: "check_account",
                  403: "check_permissions", 404: "check_endpoint_or_model",
                  422: "fix_request", 500: "bounded_retry", 503: "bounded_retry"}.get(status, "inspect_error")
        if status == 429:
            account_codes = {"insufficient_quota", "credit_balance_exhausted",
                             "organization_spend_limit_exceeded", "project_spend_limit_exceeded",
                             "organization_usage_limit_exceeded"}
            action = ("check_account" if code in account_codes else
                      "bounded_retry" if code == "rate_limit_exceeded" else "inspect_error_code")
    return {"status": status, "code": code, "kind": kind,
            "provider_received": receipt, "action": action}


def run_groups() -> dict[str, dict[str, object]]:
    """Stable fixtures, deliberately separate from actual host inspection."""
    environment = {
        "scenario": "pip and runner select different interpreters",
        "installer": "env-A", "runner": "env-B", "same_interpreter": False,
        "diagnosis": "check_interpreter", "provider_status": "not_run",
    }
    valid = parse_task('{"goal":"检查链接","max_steps":3}')
    failures = []
    for text in ('{"goal":"检查链接","max_steps":true}', '{"goal":"检查链接","max_steps":"3"}', "[]"):
        try:
            parse_task(text)
        except ValueError as error:
            failures.append(str(error))
    language = {"task": valid, "decoded_type": "dict", "rejected": failures,
                "awaited": asyncio.run(simulate_observation("read_file"))}
    api = {
        "requests": [build_request(*args) for args in (
            ("openai", "responses", "reader-model", "你好"),
            ("deepseek", "chat", "reader-model", "你好"),
            ("deepseek", "responses", "reader-model", "你好"),
            ("anthropic", "messages", "reader-model", "你好"))],
        "errors": [classify_error(401), classify_error(429, code="rate_limit_exceeded"),
                   classify_error(429, code="credit_balance_exhausted"),
                   classify_error(None, kind="timeout")],
    }
    return {name: {"schema_version": "appendix-a/1", "group": name,
                   "evidence": "offline_fixture", "network_access": False, **data}
            for name, data in (("environment", environment), ("python", language), ("api", api))}


def save_reports(output: Path, reports: dict[str, dict[str, object]]) -> tuple[Path, ...]:
    """Exclusive directory creation protects all existing reports."""
    output = Path(output)
    payloads = {name + ".json": (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
                               + "\n").encode("utf-8") for name, value in reports.items()}
    # Names are owned by our group selector, not arbitrary caller paths.
    if any(Path(name).name != name or "/" in name or "\\" in name for name in payloads):
        raise ValueError("invalid_report_name")
    output.mkdir(parents=True, exist_ok=False)
    paths = []
    for name, content in sorted(payloads.items()):
        path = output / name
        path.write_bytes(content)
        paths.append(path)
    manifest = {"schema_version": "appendix-a/1", "network_access": False,
                "files": {name: hashlib.sha256(content).hexdigest()
                          for name, content in sorted(payloads.items())}}
    path = output / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")
    return (*paths, path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("all", "environment", "python", "api"), default="all")
    parser.add_argument("--inspect", action="store_true", help="Inspect the current directory without saving host data")
    parser.add_argument("--output", type=Path, help="New report directory under appendix_a/.runs or appendix_a/reports")
    args = parser.parse_args()
    if args.inspect:
        if args.output:
            parser.error("--inspect observations are stdout-only")
        print(json.dumps(inspect_environment(Path.cwd()), ensure_ascii=False, indent=2))
        return
    reports = run_groups()
    if args.group != "all":
        reports = {args.group: reports[args.group]}
    if args.output:
        root = Path(__file__).resolve().parents[1]
        target = args.output.resolve()
        allowed = tuple((root / p).resolve() for p in ("appendix_a/.runs", "appendix_a/reports"))
        if not any(target.is_relative_to(parent) and target != parent for parent in allowed):
            parser.error("output must be a new child directory of appendix_a/.runs or appendix_a/reports")
        for path in save_reports(target, reports):
            print(path.relative_to(root).as_posix())
    else:
        print(json.dumps(reports, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
