from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


TEXT_SUFFIXES = {
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".jsonl",
    ".md",
    ".mjs",
    ".py",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_NAMES = {".gitattributes", ".gitignore", "LICENSE"}
SKIP_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "_web",
    "dist",
    "live-reports",
    "node_modules",
    "site",
    "venv",
}
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\((?P<target>[^)]+)\)")
HTML_LINK_RE = re.compile(
    r"\b(?:href|src)\s*=\s*[\"'](?P<target>[^\"']+)[\"']", re.IGNORECASE
)
FENCE_RE = re.compile(r"^\s{0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b", re.IGNORECASE),
    re.compile(
        r"\b[A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|SECRET)\s*=\s*[\"']?"
        r"(?P<value>[A-Za-z0-9._~+/=-]{16,})"
    ),
)
AUTHOR_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+", re.IGNORECASE),  # safety-fixture: allow
    re.compile(r"(?:^|[^A-Za-z0-9_])[DE]:[\\/]+", re.IGNORECASE),  # safety-fixture: allow
    re.compile(r"file://", re.IGNORECASE),  # safety-fixture: allow
    re.compile(r"\.worktrees(?:[\\/]|\b)", re.IGNORECASE),  # safety-fixture: allow
)


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    line: int
    message: str


def _relative_display(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def iter_publishable_files(root: Path):
    root = root.resolve()
    if root.is_file():
        yield root
        return
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        lowered = {part.casefold() for part in relative.parts[:-1]}
        if lowered & {name.casefold() for name in SKIP_DIRECTORIES}:
            continue
        if relative.parts[:3] == ("tests", "fixtures", "safety"):
            continue
        if path.suffix.casefold() in TEXT_SUFFIXES or path.name in TEXT_NAMES:
            yield path


def _scannable_text_lines(text: str):
    fence_character: str | None = None
    fence_length = 0
    ignore_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        match = FENCE_RE.match(line)
        if match:
            marker = match.group("fence")
            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
                ignore_fence = "invalid-example" in match.group("info").casefold()
                if not ignore_fence:
                    yield number, line
                continue
            if marker[0] == fence_character and len(marker) >= fence_length:
                if not ignore_fence:
                    yield number, line
                fence_character = None
                fence_length = 0
                ignore_fence = False
                continue
        if ignore_fence or "safety-fixture: allow" in line:
            continue
        yield number, line


def _scannable_lines(path: Path):
    yield from _scannable_text_lines(
        path.read_text(encoding="utf-8", errors="replace")
    )


def _local_target(target: str) -> str | None:
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    elif " " in target:
        target = target.split(None, 1)[0]
    if not target or target.startswith("#"):
        return None
    parsed = urlsplit(target)
    if parsed.scheme or target.startswith("//"):
        return None
    path = unquote(parsed.path)
    return path or None


def check_local_links(root: Path) -> tuple[Finding, ...]:
    root = root.resolve()
    findings: list[Finding] = []
    for path in iter_publishable_files(root):
        if path.suffix.casefold() not in {".html", ".md"}:
            continue
        for line_number, line in _scannable_lines(path):
            matches = (*MARKDOWN_LINK_RE.finditer(line), *HTML_LINK_RE.finditer(line))
            for match in matches:
                target = _local_target(match.group("target"))
                if target is None:
                    continue
                pure_windows = PureWindowsPath(target)
                if pure_windows.is_absolute():
                    continue
                relative = PurePosixPath(target.replace("\\", "/"))
                candidate = (
                    root.joinpath(*relative.parts)
                    if relative.is_absolute()
                    else path.parent.joinpath(*relative.parts)
                ).resolve()
                if not candidate.exists():
                    findings.append(
                        Finding(
                            "missing_local_link",
                            _relative_display(path, root),
                            line_number,
                            f"local target does not exist: {target}",
                        )
                    )
    return tuple(sorted(findings, key=lambda item: (item.path, item.line, item.code)))


def _is_placeholder(value: str) -> bool:
    upper = value.upper()
    return any(
        marker in upper
        for marker in ("YOUR_", "EXAMPLE", "PLACEHOLDER", "REDACTED", "NOT_A_REAL")
    )


def _secret_findings_from_text(
    text: str, path: str, *, code: str = "possible_secret"
) -> tuple[Finding, ...]:
    return _secret_findings_from_lines(
        _scannable_text_lines(text), path, code=code
    )


def _secret_findings_from_lines(
    lines, path: str, *, code: str = "possible_secret"
) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    seen_lines: set[int] = set()
    for line_number, line in lines:
        if "safety-fixture: allow" in line:
            continue
        for pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            value = match.groupdict().get("value") or match.group(0)
            if _is_placeholder(value) or line_number in seen_lines:
                continue
            findings.append(
                Finding(code, path, line_number, "possible credential detected; value redacted")
            )
            seen_lines.add(line_number)
    return tuple(findings)


def check_secrets(root: Path) -> tuple[Finding, ...]:
    root = root.resolve()
    findings: list[Finding] = []
    for path in iter_publishable_files(root):
        findings.extend(
            _secret_findings_from_lines(
                _scannable_lines(path), _relative_display(path, root)
            )
        )
    return tuple(sorted(findings, key=lambda item: (item.path, item.line, item.code)))


def _author_path_findings_from_text(
    text: str, path: str, *, code: str = "author_machine_path"
) -> tuple[Finding, ...]:
    return _author_path_findings_from_lines(
        _scannable_text_lines(text), path, code=code
    )


def _author_path_findings_from_lines(
    lines, path: str, *, code: str = "author_machine_path"
) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    for line_number, line in lines:
        if "safety-fixture: allow" in line:
            continue
        if any(pattern.search(line) for pattern in AUTHOR_PATH_PATTERNS):
            findings.append(
                Finding(code, path, line_number, "author-machine path or local URI detected")
            )
    return tuple(findings)


def check_author_paths(root: Path) -> tuple[Finding, ...]:
    root = root.resolve()
    findings: list[Finding] = []
    for path in iter_publishable_files(root):
        findings.extend(
            _author_path_findings_from_lines(
                _scannable_lines(path), _relative_display(path, root)
            )
        )
    return tuple(sorted(findings, key=lambda item: (item.path, item.line, item.code)))


def check_chapter_mapping(root: Path) -> tuple[Finding, ...]:
    root = root.resolve()
    findings: list[Finding] = []
    readme = root / "README.md"
    readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    for number in range(1, 7):
        required = (
            root / "book" / f"chapter{number}.md",
            root / f"chapter{number}" / "README.md",
            root / f"chapter{number}" / "reference-answers.md",
        )
        for path in required:
            if not path.is_file():
                findings.append(
                    Finding(
                        "missing_chapter_mapping",
                        path.relative_to(root).as_posix(),
                        0,
                        f"required Chapter {number} file is missing",
                    )
                )
        for target in (f"book/chapter{number}.md", f"chapter{number}/README.md"):
            count = readme_text.count(f"({target})")
            if count == 0:
                findings.append(
                    Finding(
                        "missing_chapter_mapping",
                        "README.md",
                        0,
                        f"root navigation omits {target}",
                    )
                )
            elif count > 1:
                findings.append(
                    Finding(
                        "duplicate_chapter_mapping",
                        "README.md",
                        0,
                        f"root navigation repeats {target}",
                    )
                )
    return tuple(sorted(findings, key=lambda item: (item.path, item.line, item.code)))


def _history_blob_entries(root: Path):
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-list", "--objects", "--all"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    seen: set[str] = set()
    for line in completed.stdout.splitlines():
        object_id, _, object_path = line.partition(" ")
        if object_id in seen:
            continue
        seen.add(object_id)
        kind = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-t", object_id],
            check=True,
            capture_output=True,
            text=True,
            encoding="ascii",
        ).stdout.strip()
        if kind != "blob":
            continue
        normalized = object_path.replace("\\", "/")
        if normalized.startswith("tests/fixtures/safety/"):
            continue
        payload = subprocess.run(
            ["git", "-C", str(root), "cat-file", "blob", object_id],
            check=True,
            capture_output=True,
        ).stdout
        if b"\0" in payload:
            continue
        yield object_id, normalized or "<unknown>", payload.decode("utf-8", errors="replace")


def check_git_history(root: Path) -> tuple[Finding, ...]:
    root = root.resolve()
    findings: list[Finding] = []
    for object_id, object_path, text in _history_blob_entries(root):
        display = f"git:{object_id[:12]}:{object_path}"
        findings.extend(_secret_findings_from_text(text, display, code="history_secret"))
        findings.extend(
            _author_path_findings_from_text(text, display, code="history_author_path")
        )
    return tuple(sorted(findings, key=lambda item: (item.path, item.line, item.code)))


def run_checks(root: Path) -> tuple[Finding, ...]:
    root = root.resolve()
    findings = (
        *check_local_links(root),
        *check_secrets(root),
        *check_author_paths(root),
        *check_chapter_mapping(root),
    )
    return tuple(sorted(findings, key=lambda item: (item.path, item.line, item.code)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repository publication safety")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--git-history", action="store_true")
    args = parser.parse_args(argv)
    findings = list(run_checks(args.root))
    if args.git_history:
        findings.extend(check_git_history(args.root))
    findings.sort(key=lambda item: (item.path, item.line, item.code))
    for item in findings:
        print(f"{item.path}:{item.line}: {item.code}: {item.message}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
