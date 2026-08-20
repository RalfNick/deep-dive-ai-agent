import json
import hashlib
import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from chapter5.probes import CredentialMissing, HttpStatusError
from chapter6.context_continuity.live_probe import DeepSeekCompactionProbe
from chapter6.experiments.live_probe import _normalized_resolved, run_cli


VALID_KEYS = [
    "repair-price",
    "decimal-result",
    "legacy-compatibility",
    "regression-coverage",
    "public-signature",
    "user-clarification",
    "compatible-patch-plan",
    "preserve-decimal-path",
    "rounding-only-rejected",
    "legacy-config-open",
    "legacy-test-failing",
    "next-intent",
]


class FakeTransport:
    def __init__(self, response=None, error=None) -> None:
        self.response = response
        self.error = error
        self.calls = []

    def post_json(self, url, *, headers, payload, timeout):
        self.calls.append((url, headers, payload, timeout))
        if self.error is not None:
            raise self.error
        return self.response


def provider_response(content, *, model="deepseek-chat"):
    return {
        "model": model,
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4},
    }


class DeepSeekCompactionProbeTest(unittest.TestCase):
    def test_protected_path_key_is_case_insensitive_on_posix_too(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            upper = Path(directory) / "REPORTS" / "RESULT.JSON"
            lower = Path(directory) / "reports" / "result.json"
            with patch(
                "chapter6.experiments.live_probe.os.path.normcase",
                side_effect=lambda value: value,
            ):
                self.assertEqual(
                    _normalized_resolved(upper),
                    _normalized_resolved(lower),
                )

    def test_live_cli_rejects_canonical_report_paths_and_aliases_before_provider(self) -> None:
        canonical_paths = (
            Path("chapter6/reports/context-continuity.json"),
            Path("chapter6/reports/context-continuity.md"),
            Path("chapter6/reports/context-continuity-trace.jsonl"),
        )
        before = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in canonical_paths
        }
        aliases = (
            canonical_paths[0],
            canonical_paths[1].resolve(),
            Path("chapter6/reports/live/../context-continuity-trace.jsonl"),
            Path("CHAPTER6/REPORTS/CONTEXT-CONTINUITY.JSON"),
            Path("chapter6/REPORTS/context-continuity.MD"),
            Path("chapter6/reports/other/../context-continuity-trace.JSONL"),
        )
        factory_calls = 0

        def forbidden_factory(**_):
            nonlocal factory_calls
            factory_calls += 1
            raise AssertionError("provider factory must not be called")

        errors = io.StringIO()
        with redirect_stderr(errors):
            for alias in aliases:
                with self.subTest(alias=str(alias)):
                    exit_code = run_cli(
                        ["--repeats", "1", "--output", str(alias)],
                        environ={"DEEPSEEK_API_KEY": "fixture-key"},
                        probe_factory=forbidden_factory,
                    )
                    self.assertEqual(exit_code, 2)

        self.assertEqual(factory_calls, 0)
        self.assertIn("canonical offline report", errors.getvalue())
        self.assertNotIn(str(canonical_paths[0].resolve()), errors.getvalue())
        self.assertEqual(
            {
                path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in canonical_paths
            },
            before,
        )

    def test_valid_json_returns_only_redacted_request_evidence(self) -> None:
        secret = "test-key-never-persist"
        transport = FakeTransport(provider_response(json.dumps({"retained_keys": VALID_KEYS})))
        run = DeepSeekCompactionProbe(api_key=secret, transport=transport).run()

        self.assertEqual(run.status, "ok")
        self.assertEqual(run.retained_keys, tuple(sorted(VALID_KEYS)))
        self.assertIsNone(run.infrastructure_failure)
        self.assertEqual(len(run.request_digest), 64)
        evidence = repr(run)
        self.assertNotIn(secret, evidence)
        self.assertNotIn("Authorization", evidence)
        payload_text = json.dumps(transport.calls[0][2], ensure_ascii=False)
        self.assertNotIn(secret, payload_text)

    def test_from_environment_reads_only_named_credential(self) -> None:
        with self.assertRaises(CredentialMissing):
            DeepSeekCompactionProbe.from_environment(environ={"OTHER_API_KEY": "wrong"})

    def test_http_statuses_are_provider_evidence_not_behavior_results(self) -> None:
        cases = ((401, "authentication"), (403, "authentication"), (429, "rate_limit"))
        for status_code, expected in cases:
            with self.subTest(status_code=status_code):
                run = DeepSeekCompactionProbe(
                    api_key="fixture-key",
                    transport=FakeTransport(error=HttpStatusError(status_code, "private body")),
                ).run()
                self.assertEqual(run.status, "infrastructure_failure")
                self.assertEqual(run.infrastructure_failure, expected)
                self.assertNotIn("private body", repr(run))

    def test_timeout_is_classified_separately(self) -> None:
        run = DeepSeekCompactionProbe(
            api_key="fixture-key",
            transport=FakeTransport(error=TimeoutError("slow")),
        ).run()

        self.assertEqual(run.infrastructure_failure, "timeout")
        self.assertEqual(run.retained_keys, ())

    def test_malformed_json_is_invalid_response(self) -> None:
        run = DeepSeekCompactionProbe(
            api_key="fixture-key",
            transport=FakeTransport(provider_response("not json")),
        ).run()

        self.assertEqual(run.status, "infrastructure_failure")
        self.assertEqual(run.infrastructure_failure, "invalid_response")

    def test_valid_shape_with_missing_keys_is_behavior_evidence(self) -> None:
        run = DeepSeekCompactionProbe(
            api_key="fixture-key",
            transport=FakeTransport(
                provider_response(json.dumps({"retained_keys": ["repair-price"]}))
            ),
        ).run()

        self.assertEqual(run.status, "ok")
        self.assertEqual(run.retained_keys, ("repair-price",))
        self.assertIn("public-signature", run.missing_keys)
        self.assertIsNone(run.infrastructure_failure)

    def test_live_cli_requires_credential_and_does_not_create_offline_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "live.json"
            exit_code = run_cli(
                ["--repeats", "1", "--output", str(output)],
                environ={},
            )

            self.assertEqual(exit_code, 2)
            self.assertFalse(output.exists())

    def test_live_cli_keeps_provider_failures_in_live_only_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "live.json"
            exit_code = run_cli(
                ["--repeats", "2", "--output", str(output)],
                environ={"DEEPSEEK_API_KEY": "fixture-key"},
                probe_factory=lambda **_: DeepSeekCompactionProbe(
                    api_key="fixture-key",
                    transport=FakeTransport(error=HttpStatusError(429, "private")),
                ),
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["valid_attempts"], 0)
            self.assertEqual(payload["provider_failures"], 2)
            self.assertEqual(len(payload["runs"]), 2)
            self.assertNotIn("fixture-key", output.read_text(encoding="utf-8"))

    def test_live_cli_allows_nested_live_report_path(self) -> None:
        transport = FakeTransport(provider_response(json.dumps({"retained_keys": VALID_KEYS})))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "chapter6" / "reports" / "live" / "deepseek.json"
            exit_code = run_cli(
                ["--repeats", "1", "--output", str(output)],
                environ={"DEEPSEEK_API_KEY": "fixture-key"},
                probe_factory=lambda **_: DeepSeekCompactionProbe(
                    api_key="fixture-key",
                    transport=transport,
                ),
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())
            self.assertEqual(len(transport.calls), 1)


if __name__ == "__main__":
    unittest.main()
