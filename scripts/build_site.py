from __future__ import annotations

import argparse
import posixpath
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit


REPOSITORY_URL = "https://github.com/RalfNick/deep-dive-ai-agent"
MARKDOWN_LINK_RE = re.compile(r"(?P<prefix>!?\[[^\]]*\]\()(?P<target>[^)]+)(?P<suffix>\))")
IMAGE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
REPORT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".txt"}


def _output_relative(source_relative: Path) -> Path:
    if source_relative == Path("README.md"):
        return Path("index.md")
    if source_relative == Path("book/README.md"):
        return Path("book/index.md")
    if source_relative == Path("book-en/README.md"):
        return Path("book-en/index.md")
    if (
        len(source_relative.parts) == 2
        and re.fullmatch(r"chapter[1-7]", source_relative.parts[0])
        and source_relative.name == "README.md"
    ):
        return Path(source_relative.parts[0]) / "index.md"
    return source_relative


def _allowlisted_sources(root: Path) -> tuple[Path, ...]:
    explicit = (
        "README.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "book/README.md",
        "book/introduction.md",
        "book/OUTLINE.md",
        "book/WRITING_GUIDE.md",
        "book-en/README.md",
        "docs/EXPERIMENT_STATUS.md",
        "docs/TRANSLATION.md",
        "docs/RELEASES.md",
    )
    explicit += tuple(f"book/chapter{number}.md" for number in range(1, 8))
    explicit += tuple(f"chapter{number}/README.md" for number in range(1, 8))
    explicit += tuple(
        f"chapter{number}/reference-answers.md" for number in range(1, 8)
    )
    sources = [root / relative for relative in explicit]

    images = root / "book" / "images"
    if images.is_dir():
        sources.extend(
            path
            for path in sorted(images.rglob("*"))
            if path.is_file() and path.suffix.casefold() in IMAGE_SUFFIXES
        )
    for number in range(1, 8):
        reports = root / f"chapter{number}" / "reports"
        if not reports.is_dir():
            continue
        sources.extend(
            path
            for path in sorted(reports.rglob("*"))
            if path.is_file() and path.suffix.casefold() in REPORT_SUFFIXES
        )
    missing = [path.relative_to(root).as_posix() for path in sources if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing site source: {', '.join(missing)}")
    return tuple(dict.fromkeys(path.resolve() for path in sources))


def _rewrite_links(
    text: str,
    *,
    source: Path,
    destination: Path,
    root: Path,
    source_to_destination: dict[Path, Path],
) -> str:
    def replace(match: re.Match[str]) -> str:
        target = match.group("target").strip()
        wrapped = target.startswith("<") and target.endswith(">")
        raw_target = target[1:-1].strip() if wrapped else target
        if not raw_target or raw_target.startswith("#"):
            return match.group(0)
        parsed = urlsplit(raw_target)
        if parsed.scheme or raw_target.startswith("//"):
            return match.group(0)
        candidate = (source.parent / parsed.path).resolve()
        try:
            relative_source = candidate.relative_to(root)
        except ValueError:
            return match.group(0)
        mapped = source_to_destination.get(candidate)
        if mapped is not None:
            rewritten = posixpath.relpath(
                mapped.as_posix(), start=destination.parent.as_posix()
            )
        elif candidate.exists():
            kind = "tree" if candidate.is_dir() else "blob"
            rewritten = f"{REPOSITORY_URL}/{kind}/main/{relative_source.as_posix()}"
        else:
            return match.group(0)
        if parsed.query:
            rewritten += f"?{parsed.query}"
        if parsed.fragment:
            rewritten += f"#{parsed.fragment}"
        return f"{match.group('prefix')}{rewritten}{match.group('suffix')}"

    return MARKDOWN_LINK_RE.sub(replace, text)


def build_site(root: Path, output: Path) -> tuple[Path, ...]:
    root = root.resolve()
    output = output.resolve() if output.is_absolute() else (root / output).resolve()
    if output == root:
        raise ValueError("output must stay inside repository and differ from root")
    try:
        output.relative_to(root)
    except ValueError as error:
        raise ValueError("output must stay inside repository") from error

    sources = _allowlisted_sources(root)
    mapping = {
        source: (output / _output_relative(source.relative_to(root))).resolve()
        for source in sources
    }
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    written: list[Path] = []
    for source, destination in mapping.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.casefold() == ".md":
            text = source.read_text(encoding="utf-8")
            text = _rewrite_links(
                text,
                source=source,
                destination=destination,
                root=root,
                source_to_destination=mapping,
            )
            destination.write_text(text, encoding="utf-8", newline="\n")
        else:
            shutil.copy2(source, destination)
        written.append(destination)
    return tuple(sorted(written))


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble the allowlisted book site")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("_web"))
    args = parser.parse_args()
    written = build_site(args.root, args.output)
    print(f"site_sources={len(written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
