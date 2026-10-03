import asyncio
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from appendix_a.preparation import (
    build_request, classify_error, inspect_environment, parse_task,
    run_groups, save_reports, simulate_observation,
)


class PreparationTests(unittest.TestCase):
    def test_json_string_becomes_validated_object(self):
        self.assertEqual(parse_task('{"goal":"检查链接","max_steps":3}'),
                         {"goal": "检查链接", "max_steps": 3})

    def test_invalid_inputs_are_rejected_before_action(self):
        for value in ('[]', '{"goal":"","max_steps":3}',
                      '{"goal":"x","max_steps":true}',
                      '{"goal":"x","max_steps":0}',
                      '{"goal":"x","max_steps":"3"}', '{oops',
                      '{"goal":"x","max_steps":3,"secret":"x"}'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_task(value)

    def test_responses_uses_input_not_messages(self):
        result = build_request("openai", "responses", "reader-model", "你好")
        self.assertEqual(result["endpoint"], "https://api.openai.com/v1/responses")
        self.assertEqual(result["body"], {"model": "reader-model", "input": "你好"})
        self.assertNotIn("headers", result)

    def test_deepseek_chat_and_responses_have_distinct_contracts(self):
        chat = build_request("deepseek", "chat", "reader-model", "你好")
        self.assertEqual(chat["endpoint"], "https://api.deepseek.com/chat/completions")
        self.assertEqual(chat["body"]["messages"], [{"role":"user","content":"你好"}])
        responses = build_request("deepseek", "responses", "reader-model", "你好")
        self.assertEqual(responses["endpoint"], "https://api.deepseek.com/responses")
        self.assertEqual(responses["body"]["input"], "你好")

    def test_anthropic_native_messages_needs_output_limit(self):
        result = build_request("anthropic", "messages", "reader-model", "你好")
        self.assertEqual(result["endpoint"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(result["body"]["max_tokens"], 128)
        self.assertEqual(result["key_variable"], "ANTHROPIC_API_KEY")

    def test_missing_or_mismatched_configuration_does_not_build_request(self):
        for args in (("other","chat","m","x"), ("openai","messages","m","x"),
                     ("openai","responses"," ","x"), ("deepseek","chat","m","")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                build_request(*args)

    def test_key_environment_and_network_are_never_used_in_offline_groups(self):
        with patch("os.environ", {}), patch("os.getenv", side_effect=AssertionError("key read")), \
             patch.object(socket, "create_connection", side_effect=AssertionError("network")):
            reports = run_groups()
        self.assertEqual(set(reports), {"environment", "python", "api"})
        self.assertTrue(all(value["network_access"] is False for value in reports.values()))

    def test_environment_check_distinguishes_wrong_root(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.assertFalse(inspect_environment(root)["repository_root_ok"])
            (root / "chapter3").mkdir()
            (root / "chapter3/agent_loop.py").write_text("", encoding="utf-8")
            (root / "book").mkdir()
            (root / "book/OUTLINE.md").write_text("", encoding="utf-8")
            self.assertTrue(inspect_environment(root)["repository_root_ok"])

    def test_local_inspection_does_not_report_provider_success(self):
        result = inspect_environment(Path(__file__).resolve().parents[2])
        self.assertEqual(result["provider_status"], "not_run")
        self.assertFalse(result["network_access"])

    def test_async_observation_is_returned_only_after_await(self):
        result = asyncio.run(simulate_observation("read_file"))
        self.assertEqual(result, {"tool": "read_file", "ok": True, "source": "fixture"})

    def test_429_account_failure_is_not_transient_rate_limit(self):
        for code in ("insufficient_quota", "credit_balance_exhausted",
                     "organization_spend_limit_exceeded", "project_spend_limit_exceeded",
                     "organization_usage_limit_exceeded"):
            self.assertEqual(classify_error(429, code=code)["action"], "check_account")
        self.assertEqual(classify_error(429, code="rate_limit_exceeded")["action"], "bounded_retry")
        self.assertEqual(classify_error(429)["action"], "inspect_error_code")

    def test_timeout_has_unknown_provider_receipt(self):
        result = classify_error(None, kind="timeout")
        self.assertEqual(result["provider_received"], "unknown")
        self.assertEqual(result["action"], "inspect_before_retry")

    def test_permanent_errors_do_not_trigger_automatic_retry(self):
        for status, action in ((400,"fix_request"), (401,"check_credentials"),
                               (403,"check_permissions"), (402,"check_account")):
            self.assertEqual(classify_error(status)["action"], action)
        self.assertEqual(classify_error(503)["action"], "bounded_retry")
        self.assertEqual(classify_error(599)["action"], "inspect_error")

    def test_reports_are_reproducible_and_existing_directory_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            first = save_reports(root / "first", run_groups())
            second = save_reports(root / "second", run_groups())
            self.assertEqual([p.read_bytes() for p in first], [p.read_bytes() for p in second])
            with self.assertRaises(FileExistsError):
                save_reports(root / "first", run_groups())
            manifest = json.loads((root / "first/manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["files"]), 3)


if __name__ == "__main__":
    unittest.main()
