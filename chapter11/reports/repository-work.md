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
    "details": [],
    "exit_code": 0,
    "stdout": "",
    "stderr": "",
    "scope": "tests"
  },
  "initial_acceptance": {
    "checks": {
      "nested_path": false,
      "nested_valid": false,
      "root_valid": true,
      "missing_still_fails": true
    },
    "ok": false,
    "exit_code": 0,
    "stdout": "",
    "stderr": ""
  },
  "red": {
    "count": 4,
    "failures": 1,
    "errors": 0,
    "ok": false,
    "details": [
      {
        "test": "test_links.LinkTests.test_nested_document",
        "kind": "failure",
        "message": "AssertionError: Lists differ: [] != ['../faq.md']\n\nSecond list contains 1 additional elements.\nFirst extra element 0:\n'../faq.md'\n\n- []\n+ ['../faq.md']"
      }
    ],
    "exit_code": 1,
    "stdout": "",
    "stderr": "",
    "scope": "tests"
  },
  "final": {
    "tests": {
      "count": 4,
      "failures": 0,
      "errors": 0,
      "ok": true,
      "details": [],
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "scope": "tests"
    },
    "acceptance": {
      "checks": {
        "nested_path": true,
        "nested_valid": true,
        "root_valid": true,
        "missing_still_fails": true
      },
      "ok": true,
      "exit_code": 0,
      "stdout": "",
      "stderr": ""
    },
    "tests_unchanged": true,
    "snapshot_stable": true,
    "snapshot_recorded": true,
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
    "details": [],
    "exit_code": 0,
    "stdout": "",
    "stderr": "",
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
      "details": [],
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "scope": "tests"
    },
    "acceptance": {
      "checks": {
        "nested_path": false,
        "nested_valid": false,
        "root_valid": true,
        "missing_still_fails": true
      },
      "ok": false,
      "exit_code": 0,
      "stdout": "",
      "stderr": ""
    },
    "tests_unchanged": true,
    "snapshot_stable": true,
    "snapshot_recorded": true,
    "accepted": false
  },
  "zero_tests": {
    "tests": {
      "count": 0,
      "failures": 0,
      "errors": 0,
      "ok": true,
      "details": [],
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "scope": "empty_tests"
    },
    "acceptance": {
      "checks": {
        "nested_path": false,
        "nested_valid": false,
        "root_valid": true,
        "missing_still_fails": true
      },
      "ok": false,
      "exit_code": 0,
      "stdout": "",
      "stderr": ""
    },
    "tests_unchanged": true,
    "snapshot_stable": true,
    "snapshot_recorded": true,
    "accepted": false
  },
  "tampered_tests": {
    "tests": {
      "count": 0,
      "failures": 0,
      "errors": 0,
      "ok": true,
      "details": [],
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "scope": "tests"
    },
    "acceptance": {
      "checks": {
        "nested_path": false,
        "nested_valid": false,
        "root_valid": true,
        "missing_still_fails": true
      },
      "ok": false,
      "exit_code": 0,
      "stdout": "",
      "stderr": ""
    },
    "tests_unchanged": false,
    "snapshot_stable": true,
    "snapshot_recorded": true,
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
      "details": [],
      "exit_code": 0,
      "stdout": "",
      "stderr": "",
      "scope": "tests"
    },
    "acceptance": {
      "checks": {
        "nested_path": false,
        "nested_valid": false,
        "root_valid": true,
        "missing_still_fails": true
      },
      "ok": false,
      "exit_code": 0,
      "stdout": "",
      "stderr": ""
    },
    "tests_unchanged": true,
    "snapshot_stable": true,
    "snapshot_recorded": true,
    "accepted": false
  }
}
```
