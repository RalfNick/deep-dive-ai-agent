"""Offline-first Judge calibration plus an explicitly opt-in live boundary."""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import request

LABELS = ("pass", "fail", "unknown")


def parse_live_judge_response(response: object) -> dict[str, object]:
    """Extract and validate the small contract promised by the live Judge prompt."""
    try:
        content = response["choices"][0]["message"]["content"]  # type: ignore[index]
        payload = json.loads(content) if isinstance(content, str) else content
        label = payload["label"]
        evidence = payload["evidence"]
    except (IndexError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid_live_judge_response") from exc
    if (label not in LABELS or not isinstance(evidence, list)
            or not all(isinstance(item, str) for item in evidence)):
        raise ValueError("invalid_live_judge_response")
    return {"label": label, "evidence": evidence}


def calibrate_offline(path: Path | None = None) -> dict[str, object]:
    source = path or Path(__file__).with_name("fixtures") / "judge-calibration.json"
    fixture = json.loads(Path(source).read_text(encoding="utf-8"))
    metadata = fixture["metadata"]
    cases = fixture["cases"]
    confusion = {gold: {predicted: 0 for predicted in LABELS} for gold in LABELS}
    matches = 0
    unknown = 0
    answered_matches = 0
    answered = 0
    for case in cases:
        gold, predicted = case["gold"], case["prediction"]
        confusion[gold][predicted] += 1
        matches += gold == predicted
        unknown += predicted == "unknown"
        if predicted != "unknown":
            answered += 1
            answered_matches += gold == predicted
    unknown_rate = round(unknown / len(cases), 6)
    return {
        "mode": "offline_fixture",
        "case_count": len(cases),
        "agreement": round(matches / len(cases), 6),
        "unknown_rate": unknown_rate,
        "coverage": round(answered / len(cases), 6),
        "answered_accuracy": round(answered_matches / answered, 6) if answered else None,
        "confusion_matrix": confusion,
        "metadata": metadata,
        "limitations": ["fixed fixture, not a live model measurement",
                        "editorial gold is not independently human validated",
                        "agreement does not establish construct validity"],
    }


def run_live_judge(payload: dict[str, object], *, base_url: str, model: str,
                   api_key_env: str = "EVAL_JUDGE_API_KEY") -> dict[str, object]:
    """Call an OpenAI-compatible endpoint only through explicit live invocation."""
    key = os.environ.get(api_key_env)
    if not key:
        raise RuntimeError("judge_api_key_missing")
    body = json.dumps({"model": model, "messages": [
        {"role": "system", "content": "Return JSON with label pass, fail, or unknown and evidence."},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ], "response_format": {"type": "json_object"}}).encode()
    http_request = request.Request(base_url.rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with request.urlopen(http_request, timeout=60) as response:  # noqa: S310 - explicit opt-in URL
        return parse_live_judge_response(json.loads(response.read().decode()))
