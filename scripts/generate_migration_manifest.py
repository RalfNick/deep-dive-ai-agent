from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re


@dataclass(frozen=True)
class ManifestRecord:
    target: str
    source: str
    commit: str
    size: int
    sha256: str


LATER_BOOK_RE = re.compile(
    r"^book/(?:chapter[56]\.md|images/fig[56]-|sources/chapter[56]-|"
    r"reviews/chapter[56]-|versions/CHAPTER_VERSIONS\.md)"
)
BINARY_SUFFIXES = {".gif", ".jpeg", ".jpg", ".pdf", ".png", ".webp"}


def canonical_payload(path: Path) -> bytes:
    payload = path.read_bytes()
    if path.suffix.casefold() in BINARY_SUFFIXES or b"\0" in payload:
        return payload
    return payload.replace(b"\r\n", b"\n")


def _source_for(target: str) -> str:
    if LATER_BOOK_RE.match(target) or re.match(r"^chapter[56]/", target):
        return "chapter6-worktree"
    return "current-workspace"


def _iter_migrated_files(root: Path):
    roots = [root / "book"]
    roots.extend(root / f"chapter{number}" for number in range(1, 7))
    roots.append(root / "docs" / "author-sources")
    for content_root in roots:
        if not content_root.is_dir():
            continue
        for path in sorted(content_root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            yield path


def build_records(
    root: Path, current_commit: str, later_commit: str
) -> tuple[ManifestRecord, ...]:
    commits = {
        "current-workspace": current_commit,
        "chapter6-worktree": later_commit,
    }
    records: list[ManifestRecord] = []
    for path in _iter_migrated_files(root):
        payload = canonical_payload(path)
        target = path.relative_to(root).as_posix()
        source = _source_for(target)
        records.append(
            ManifestRecord(
                target=target,
                source=source,
                commit=commits[source],
                size=len(payload),
                sha256=hashlib.sha256(payload).hexdigest(),
            )
        )
    return tuple(sorted(records, key=lambda record: record.target))


def render_manifest(records: tuple[ManifestRecord, ...]) -> str:
    lines = [
        "# 迁移清单",
        "",
        "本清单记录独立书籍仓库中从原工程迁移的文件。`source` 是可移植的来源标签；",
        "`commit` 是迁移时冻结的来源提交；文本按 `.gitattributes` 的 LF 规范化后计算字节数与 SHA-256，二进制保持原字节。",
        "",
        "不导入 PDF、HTML、渲染中间图、缓存、虚拟环境、真实凭据或旧分支中的重复章节。",
        "版本台账由两个来源确定性合并，归入包含第 5–6 章发布记录的 `chapter6-worktree`。",
        "第 6 章来源台账依赖的三篇作者既有工程文章及其直接图片迁入 `docs/author-sources/`；不扩张为旧工程文档镜像。",
        "本仓库不迁移 `chapter6/tests/test_pdf_release.py` 及其 PDF 二进制，并将第 6 章依赖收窄为真实的标准库合同。",
        "",
        "| target | source | commit | bytes | sha256 |",
        "| --- | --- | --- | ---: | --- |",
    ]
    lines.extend(
        f"| `{record.target}` | `{record.source}` | `{record.commit}` | "
        f"{record.size} | `{record.sha256}` |"
        for record in records
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the book migration manifest")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--current-commit", required=True)
    parser.add_argument("--later-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = build_records(args.root, args.current_commit, args.later_commit)
    output = args.output if args.output.is_absolute() else args.root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_manifest(records), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
