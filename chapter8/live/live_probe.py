from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
from urllib import error, request

if __package__ in (None, ""):
    repository_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repository_root))

from chapter8.experiments.run_all import _case_map, _retriever
from chapter8.knowledge_runtime.evidence import build_evidence_packet


PROVIDERS = {
    "deepseek": {
        "environment": "DEEPSEEK_API_KEY",
        "endpoint": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat",
    }
}


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    )


def _evidence_prompt() -> tuple[str, list[str]]:
    case = _case_map()["governance-compound-upgrade"]
    hits = _retriever().retrieve(case.query)
    packet = build_evidence_packet(case.query, hits, case.required_fact_ids)
    evidence = [
        f"[{citation.citation_id}] {hit.chunk.context_prefix}\n{hit.chunk.content}"
        for citation, hit in zip(packet.citations, packet.evidence)
    ]
    prompt = (
        "只依据下面证据回答问题。每个事实都用 [C1] 形式引用；证据不足就明确拒答。\n\n"
        f"问题：{case.query.text}\n\n证据：\n" + "\n\n".join(evidence)
    )
    return prompt, [citation.citation_id for citation in packet.citations]


def run_deepseek(api_key: str, timeout_seconds: float) -> dict[str, object]:
    config = PROVIDERS["deepseek"]
    prompt, citation_ids = _evidence_prompt()
    body = json.dumps(
        {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    http_request = request.Request(
        str(config["endpoint"]),
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with request.urlopen(http_request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        return {
            "status": "provider_error",
            "http_status": exc.code,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "provider": "deepseek",
            "model": config["model"],
            "usage": None,
            "answer": None,
            "quality": None,
        }
    except (error.URLError, TimeoutError) as exc:
        return {
            "status": "transport_error",
            "error_type": type(exc).__name__,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "provider": "deepseek",
            "model": config["model"],
            "usage": None,
            "answer": None,
            "quality": None,
        }
    answer = payload["choices"][0]["message"]["content"]
    return {
        "status": "ok",
        "provider": "deepseek",
        "model": payload.get("model", config["model"]),
        "latency_ms": round((time.perf_counter() - started) * 1000, 3),
        "usage": payload.get("usage"),
        "answer": answer,
        "expected_citation_ids": citation_ids,
        "quality": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an optional, non-canonical Chapter 8 live probe.")
    parser.add_argument("--provider", choices=tuple(PROVIDERS), default="deepseek")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    parser.add_argument("--output", type=Path, default=Path("chapter8/live-output/live-probe.json"))
    args = parser.parse_args()

    config = PROVIDERS[args.provider]
    environment_name = str(config["environment"])
    credential = os.environ.get(environment_name)
    if not args.execute:
        payload = {
            "status": "dry_run",
            "provider": args.provider,
            "model": config["model"],
            "required_environment": environment_name,
            "credential_present": bool(credential),
            "usage": None,
            "latency_ms": None,
            "quality": None,
        }
        _write(args.output, payload)
        return 0
    if not credential:
        _write(
            args.output,
            {
                "status": "config_error",
                "provider": args.provider,
                "model": config["model"],
                "required_environment": environment_name,
                "usage": None,
                "latency_ms": None,
                "quality": None,
            },
        )
        return 2
    _write(args.output, run_deepseek(credential, args.timeout_seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
