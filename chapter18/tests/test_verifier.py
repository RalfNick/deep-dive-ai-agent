from chapter18.fixtures import create_workspace
from chapter18.tests.helpers import fixture_repo


def test_actual_baseline_three_of_four_then_real_fix_four_of_four(tmp_path):
    from chapter18.verifier import verify_workspace
    root = fixture_repo(tmp_path)
    workspace = create_workspace(root, root / "chapter18/.runs/verify/workspace")
    fixture = root / "chapter18/fixtures/link-checker"
    before = verify_workspace(workspace, fixture_root=fixture)
    assert not before.passed and before.tests_passed == 3 and before.tests_total == 4
    assert not before.behavior_passed
    path = workspace / "src/linkcheck.py"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("    return path\n", "    return posixpath.normpath(posixpath.join(posixpath.dirname(document), path))\n"), encoding="utf-8")
    after = verify_workspace(workspace, fixture_root=fixture)
    assert after.passed and after.tests_passed == after.tests_total == 4 and after.behavior_passed


def test_protected_test_copy_tamper_does_not_change_frozen_acceptance(tmp_path):
    from chapter18.verifier import verify_workspace
    root = fixture_repo(tmp_path)
    workspace = create_workspace(root, root / "chapter18/.runs/tamper/workspace")
    (workspace / "tests/test_existing.py").write_text("# no tests here", encoding="utf-8")
    result = verify_workspace(workspace, fixture_root=root / "chapter18/fixtures/link-checker")
    assert not result.passed and result.reason_code == "protected_tests_changed"
