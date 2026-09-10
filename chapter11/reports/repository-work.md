# 第 11 章实验记录

实际执行文件修改、Git 和测试子进程；决策序列固定，未调用模型。

## repair

```json
{
  "initial_tests": {
    "count": 3,
    "failures": 0,
    "errors": 0,
    "ok": true,
    "exit_code": 0,
    "scope": "tests"
  },
  "initial_acceptance": {
    "checks": {
      "nested_path": false,
      "nested_valid": false,
      "root_valid": true,
      "missing_still_fails": true
    },
    "ok": false
  },
  "red": {
    "count": 4,
    "failures": 1,
    "errors": 0,
    "ok": false,
    "exit_code": 1,
    "scope": "tests"
  },
  "final": {
    "tests": {
      "count": 4,
      "failures": 0,
      "errors": 0,
      "ok": true,
      "exit_code": 0,
      "scope": "tests"
    },
    "acceptance": {
      "checks": {
        "nested_path": true,
        "nested_valid": true,
        "root_valid": true,
        "missing_still_fails": true
      },
      "ok": true
    },
    "tests_unchanged": true,
    "snapshot_stable": true,
    "snapshot": "50f021c4182b794367298071213894a9fd7d7b9195e213d60d025f43e89ff146",
    "accepted": true
  },
  "diff": "diff --git a/linkcheck.py b/linkcheck.py\nindex 6d253cd..9719c7f 100644\n--- a/linkcheck.py\n+++ b/linkcheck.py\n@@ -5,7 +5,7 @@ LINK = re.compile(r\"(?<!!)\\[[^\\]\\n]+\\]\\(([^()\\s]+)\\)\")\n \n \n def resolve_link(root: Path, document: Path, target: str) -> Path:\n-    base = root\n+    base = document.parent\n     return (base / target).resolve()\n \n \ndiff --git a/tests/test_links.py b/tests/test_links.py\nindex c066e7f..db43ef9 100644\n--- a/tests/test_links.py\n+++ b/tests/test_links.py\n@@ -14,3 +14,6 @@ class LinkTests(unittest.TestCase):\n \n     def test_external_link_is_skipped(self):\n         self.assertEqual([], broken_links(ROOT, ROOT / \"external-example.md\"))\n+\n+    def test_nested_document(self):\n+        self.assertEqual([], broken_links(ROOT, ROOT / \"docs/guide/start.md\"))\n"
}
```

## instructions

```json
{
  "before": {
    "agents_exists": false,
    "claude_exists": false,
    "agents_bytes": 0,
    "product_adherence": "not_measured"
  },
  "after": {
    "agents_exists": true,
    "claude_exists": true,
    "agents_bytes": 455,
    "product_adherence": "not_measured"
  },
  "command_observation": {
    "count": 3,
    "failures": 0,
    "errors": 0,
    "ok": true,
    "exit_code": 0,
    "scope": "tests"
  },
  "interpretation": "file inventory and real command execution; not product instruction adherence"
}
```

## conflict

```json
{
  "error": "stale_source",
  "workspace_preserved": true,
  "dirty_files": [
    "linkcheck.py",
    "notes.txt"
  ]
}
```

## verification

```json
{
  "insufficient_coverage": {
    "tests": {
      "count": 3,
      "failures": 0,
      "errors": 0,
      "ok": true,
      "exit_code": 0,
      "scope": "tests"
    },
    "acceptance": {
      "checks": {
        "nested_path": false,
        "nested_valid": false,
        "root_valid": true,
        "missing_still_fails": true
      },
      "ok": false
    },
    "tests_unchanged": true,
    "snapshot_stable": true,
    "snapshot": "b79989c0e6a24ee25eb95f8b7b522b2411c11fd09f9f93729e157daecf9c0dbb",
    "accepted": false
  },
  "zero_tests": {
    "tests": {
      "count": 0,
      "failures": 0,
      "errors": 0,
      "ok": true,
      "exit_code": 0,
      "scope": "empty_tests"
    },
    "acceptance": {
      "checks": {
        "nested_path": false,
        "nested_valid": false,
        "root_valid": true,
        "missing_still_fails": true
      },
      "ok": false
    },
    "tests_unchanged": true,
    "snapshot_stable": true,
    "snapshot": "b79989c0e6a24ee25eb95f8b7b522b2411c11fd09f9f93729e157daecf9c0dbb",
    "accepted": false
  },
  "tampered_tests": {
    "tests": {
      "count": 0,
      "failures": 0,
      "errors": 0,
      "ok": true,
      "exit_code": 0,
      "scope": "tests"
    },
    "acceptance": {
      "checks": {
        "nested_path": false,
        "nested_valid": false,
        "root_valid": true,
        "missing_still_fails": true
      },
      "ok": false
    },
    "tests_unchanged": false,
    "snapshot_stable": true,
    "snapshot": "595c8f9547eff757ca5b2a0224805159d099527f6dff8ff9de598ae0a16538e0",
    "accepted": false
  }
}
```

## resume

```json
{
  "before_change_current": true,
  "old_evidence_current": false,
  "revalidation": {
    "tests": {
      "count": 3,
      "failures": 0,
      "errors": 0,
      "ok": true,
      "exit_code": 0,
      "scope": "tests"
    },
    "acceptance": {
      "checks": {
        "nested_path": false,
        "nested_valid": false,
        "root_valid": true,
        "missing_still_fails": true
      },
      "ok": false
    },
    "tests_unchanged": true,
    "snapshot_stable": true,
    "snapshot": "b79989c0e6a24ee25eb95f8b7b522b2411c11fd09f9f93729e157daecf9c0dbb",
    "accepted": false
  }
}
```
