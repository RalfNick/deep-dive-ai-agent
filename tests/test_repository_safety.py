from pathlib import Path
import subprocess
import tempfile
import unittest


from scripts.check_repository import (
    Finding,
    _known_historical_plan_path,
    check_author_paths,
    check_chapter_mapping,
    check_git_history,
    check_local_links,
    check_secrets,
    run_checks,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "safety"


class RepositorySafetyTests(unittest.TestCase):
    def test_missing_markdown_image_is_reported(self) -> None:
        findings = check_local_links(FIXTURES / "missing-link")

        self.assertEqual(["missing_local_link"], [item.code for item in findings])

    def test_author_machine_paths_and_file_uri_are_reported(self) -> None:
        findings = check_author_paths(FIXTURES / "author-paths")

        self.assertEqual(5, len(findings))
        self.assertEqual({"author_machine_path"}, {item.code for item in findings})

    def test_plausible_secrets_are_detected_without_echoing_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = "sk-" + "0123456789abcdef" * 2
            bearer = "Bearer " + "abcdefghijklmnopqrstuvwxyz012345"
            (root / "secrets.txt").write_text(
                f"DEEPSEEK_API_KEY={secret}\nAuthorization: {bearer}\n",
                encoding="utf-8",
            )

            findings = check_secrets(root)

        self.assertEqual(2, len(findings))
        rendered = "\n".join(item.message for item in findings)
        self.assertNotIn(secret, rendered)
        self.assertNotIn(bearer, rendered)

    def test_placeholders_https_and_explicit_invalid_fence_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = "sk-" + "0123456789abcdef" * 2
            (root / "README.md").write_text(
                "API_KEY=YOUR_API_KEY\n"
                "[official](https://example.com/docs)\n"
                "```text invalid-example\n"
                f"{secret}\n"
                "C:\\Users\\Author\\notes.md\n"  # safety-fixture: allow
                "```\n",
                encoding="utf-8",
            )

            findings = (
                *check_local_links(root),
                *check_secrets(root),
                *check_author_paths(root),
            )

        self.assertEqual((), findings)

    def test_local_worktree_directories_are_not_publishable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / ".worktrees" / "chapter-draft"  # safety-fixture: allow
            nested.mkdir(parents=True)
            secret = "sk-" + "0123456789abcdef" * 2
            (nested / "README.md").write_text(
                f"{secret}\n[missing](./does-not-exist.png)\n",
                encoding="utf-8",
            )

            findings = (
                *check_local_links(root),
                *check_secrets(root),
                *check_author_paths(root),
            )

        self.assertEqual((), findings)

    def test_ignored_execution_workspace_is_not_publishable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scratch = root / ".superpowers" / "sdd" / "task" / "brief.md"
            scratch.parent.mkdir(parents=True)
            local_path = "".join(("D", r":\local\scratch"))
            scratch.write_text(f"workspace = {local_path}\n", encoding="utf-8")

            self.assertEqual((), check_author_paths(root))

    def test_known_historical_plan_path_exception_is_exact(self) -> None:
        blob = "442c08b71c7a347c075e2400e02f40c8d4fab7a6"
        plan = "docs/superpowers/plans/2026-09-27-chapter15-agent-post-training.md"
        finding = Finding("history_author_path", "ignored", 619, "author-machine path")

        self.assertTrue(_known_historical_plan_path(blob, plan, finding))
        self.assertFalse(_known_historical_plan_path("0" * 40, plan, finding))
        self.assertFalse(_known_historical_plan_path(blob, "book/chapter15.md", finding))
        self.assertFalse(_known_historical_plan_path(blob, plan, Finding("history_author_path", "ignored", 620, "author-machine path")))
        self.assertFalse(_known_historical_plan_path(blob, plan, Finding("history_secret", "ignored", 619, "secret")))

    def test_chapter_mapping_rejects_missing_and_duplicate_readme_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "book").mkdir()
            for number in range(1, 8):
                (root / "book" / f"chapter{number}.md").write_text(
                    f"chapter {number}", encoding="utf-8"
                )
                chapter = root / f"chapter{number}"
                chapter.mkdir()
                (chapter / "README.md").write_text("index", encoding="utf-8")
                (chapter / "reference-answers.md").write_text(
                    "answers", encoding="utf-8"
                )
            links = [
                f"[c{number}](book/chapter{number}.md)"
                for number in range(1, 8)
            ]
            links.extend(
                f"[e{number}](chapter{number}/README.md)"
                for number in range(1, 8)
            )
            links.append("[duplicate](chapter1/README.md)")
            (root / "README.md").write_text("\n".join(links), encoding="utf-8")
            (root / "chapter7" / "reference-answers.md").unlink()

            findings = check_chapter_mapping(root)

        self.assertEqual(
            {"duplicate_chapter_mapping", "missing_chapter_mapping"},
            {item.code for item in findings},
        )

    def test_git_history_finds_a_secret_that_was_later_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-b", "main", root], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", root, "config", "user.name", "Safety Test"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", root, "config", "user.email", "safety@example.com"],
                check=True,
            )
            secret = "sk-" + "0123456789abcdef" * 2
            leaked = root / "leaked.txt"
            leaked.write_text(secret, encoding="utf-8")
            subprocess.run(["git", "-C", root, "add", "leaked.txt"], check=True)
            subprocess.run(
                ["git", "-C", root, "commit", "-m", "add fixture"], check=True,
                capture_output=True,
            )
            leaked.unlink()
            subprocess.run(["git", "-C", root, "add", "leaked.txt"], check=True)
            subprocess.run(
                ["git", "-C", root, "commit", "-m", "remove fixture"], check=True,
                capture_output=True,
            )

            findings = check_git_history(root)

        self.assertIn("history_secret", {item.code for item in findings})
        self.assertTrue(all(secret not in item.message for item in findings))

    def test_bare_local_uri_regex_is_not_a_machine_path_but_real_uris_are(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            uri_prefix = "file" + "://"
            (root / "guard.py").write_text(
                'import re\npattern = re.compile(' + repr(r"[A-Za-z]:[\\/]|" + uri_prefix) + ')\n',
                encoding="utf-8",
            )
            self.assertEqual((), check_author_paths(root))
            subprocess.run(["git", "init", "-b", "main", root], check=True, capture_output=True)
            subprocess.run(["git", "-C", root, "-c", "user.name=Safety Test", "-c", "user.email=safety@example.com",
                            "add", "guard.py"], check=True, capture_output=True)
            subprocess.run(["git", "-C", root, "-c", "user.name=Safety Test", "-c", "user.email=safety@example.com",
                            "commit", "-m", "regex fixture"], check=True, capture_output=True)
            self.assertEqual((), check_git_history(root))
            for i, suffix in enumerate(("/tmp/private", "localhost/private", "/" + "D" + ":/private")):
                (root / f"leak{i}.md").write_text(f'[private]({uri_prefix}{suffix})\n', encoding="utf-8")
            self.assertEqual(3, len(check_author_paths(root)))

    def test_real_repository_passes_the_current_tree_gate(self) -> None:
        self.assertEqual((), run_checks(ROOT))

    def test_named_virtualenv_directories_are_not_publishable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dependency = root / ".venv-chapter12" / "Lib" / "site-packages" / "example.py"
            dependency.parent.mkdir(parents=True)
            local_path = "".join(("D", r":\private\dependency"))
            dependency.write_text(f'path = "{local_path}"', encoding="utf-8")
            self.assertEqual((), check_author_paths(root))


if __name__ == "__main__":
    unittest.main()
