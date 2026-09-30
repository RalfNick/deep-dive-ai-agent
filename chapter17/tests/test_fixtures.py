import pytest

from chapter17.fixtures import load_fixture


@pytest.mark.parametrize("name", ["../AGENTS.md", "C:/Windows/win.ini", "/etc/passwd", "sub/x.svg", "..\\secret"])
def test_fixture_rejects_parent_or_absolute_name(name):
    with pytest.raises(ValueError):
        load_fixture(name)


def test_fixture_missing_is_explicit():
    with pytest.raises(FileNotFoundError):
        load_fixture("missing.json")
