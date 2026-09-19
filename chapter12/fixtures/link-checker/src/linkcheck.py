"""Small local Markdown-link checker; the nested-path behavior needs repair."""
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


def broken_links(document: Path, root: Path) -> list[str]:
    missing = []
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith('//') or not parsed.path:
            continue
        target = unquote(parsed.path)
        candidate = root / target
        if not candidate.is_file():
            missing.append(target)
    return missing
