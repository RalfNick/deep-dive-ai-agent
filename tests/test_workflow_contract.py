from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "ci.yml"
PAGES = ROOT / ".github" / "workflows" / "pages.yml"


class WorkflowContractTests(unittest.TestCase):
    def workflow_text(self, path: Path) -> str:
        self.assertTrue(path.is_file(), f"missing workflow: {path.relative_to(ROOT)}")
        return path.read_text(encoding="utf-8")

    def test_ci_pins_runtime_and_action_majors(self) -> None:
        text = self.workflow_text(CI)
        for fragment in (
            "actions/checkout@v4",
            "actions/setup-python@v5",
            "actions/setup-node@v4",
            "python-version: '3.11'",
            "node-version: '22'",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)
        self.assertNotIn("${{ secrets.", text)
        self.assertNotIn("pages: write", text)

    def test_ci_runs_repository_chapter_report_render_and_site_gates(self) -> None:
        text = self.workflow_text(CI)
        required = (
            "python scripts/check_repository.py --root . --git-history",
            "python -m unittest discover -s tests -v",
            "python -m unittest discover -s chapter1/tests -v",
            "python chapter2/sft_mask_demo.py",
            "python chapter2/real_sft_evidence.py",
            "python chapter2/preference_demo.py",
            "python chapter2/sampling_demo.py",
            "python chapter2/reasoning_budget_demo.py",
            "python chapter2/structured_output_demo.py",
            "python chapter2/model_selection_demo.py",
            "python -m unittest discover -s chapter3/tests -v",
            "python -m unittest discover -s chapter4/tests -v",
            "python -m unittest discover -s chapter5/tests -v",
            "python -m unittest discover -s chapter6/tests -v",
            "python chapter1/generate_report.py",
            "python chapter3/run_all_experiments.py",
            "python -m chapter4.experiments.boundary_matrix_demo",
            "python -m chapter5.experiments.run_all --output chapter5/reports/context-experiments.json",
            "python -m chapter6.experiments.run_all --output chapter6/reports",
            "npm test --prefix book",
            "python scripts/build_site.py --root . --output _web",
            "python -m mkdocs build --strict",
        )
        for fragment in required:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_pages_deploys_only_a_successful_main_ci_commit(self) -> None:
        text = self.workflow_text(PAGES)
        for fragment in (
            "workflow_run:",
            "workflows: [CI]",
            "github.event.workflow_run.conclusion == 'success'",
            "github.event.workflow_run.head_branch == 'main'",
            "ref: ${{ github.event.workflow_run.head_sha }}",
            "actions/configure-pages@v5",
            "actions/upload-pages-artifact@v3",
            "actions/deploy-pages@v4",
            "pages: write",
            "id-token: write",
            "environment:",
            "name: github-pages",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)
        self.assertNotIn("${{ secrets.", text)


if __name__ == "__main__":
    unittest.main()
