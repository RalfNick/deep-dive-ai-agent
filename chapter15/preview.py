"""Build an optional local Chapter 15 preview without publishing it."""
from __future__ import annotations

from html import escape
from pathlib import Path
import re
from urllib.parse import urlsplit


def build_preview(root: Path, *, output: Path | None = None) -> Path:
    import markdown  # Optional dependency, pinned in requirements-preview.txt.

    root = Path(root).resolve()
    source = (root / "book" / "chapter15.md").read_text(encoding="utf-8")
    body = markdown.markdown(source, extensions=["extra", "toc"])

    def relative(match: re.Match[str]) -> str:
        prefix, target, suffix = match.groups()
        if not target or target.startswith("#") or urlsplit(target).scheme:
            return match.group(0)
        return f'{prefix}../../book/{target}{suffix}'

    body = re.sub(r'((?:src|href)=")([^"]+)(")', relative, body)

    def figure(match: re.Match[str]) -> str:
        image, caption, target = match.groups()
        return (
            '<figure><a class="figure-link" href="'
            + escape(target, quote=True)
            + '" target="_blank" rel="noopener" aria-label="打开原图">'
            + image
            + '</a><figcaption><span class="mobile-figure-hint">'
            + "移动端可在图内左右滑动查看完整内容。 </span>"
            + caption
            + "</figcaption></figure>"
        )

    body = re.sub(
        r'<p>(<img[^>]+alt="([^"]+)"[^>]+src="([^"]+)"[^>]*>)</p>',
        figure,
        body,
    )
    body = re.sub(
        r'(<table>.*?</table>)',
        r'<div class="table-wrap" role="region" aria-label="可横向滚动的表格">\1</div>',
        body,
        flags=re.S,
    )

    html = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>第 15 章 · Agent 的后训练 · 本地候选预览</title>
<style>
*{box-sizing:border-box}html{background:#eee9df;color:#142b4a}
body{max-width:940px;margin:0 auto;background:#fffdf8;padding:52px 58px;font:17px/1.95 "Microsoft YaHei","PingFang SC",sans-serif;overflow-wrap:anywhere}
main{max-width:100%}h1{font-size:32px;line-height:1.4;margin:.2em 0 1.4em;color:#0d2f59}
h2{font-size:25px;margin-top:2.7em;border-top:1px solid #dcd4c6;padding-top:1em;line-height:1.5;color:#164d75}
h3{font-size:20px;margin-top:2.1em;line-height:1.55;color:#305a65}p{margin:1.05em 0}
a{color:#155ca6}.figure-link{display:block;border-radius:12px;outline-offset:4px}
blockquote{margin:1.5em 0;padding:4px 22px;border-left:4px solid #527da2;background:#edf4f5}
pre{max-width:100%;overflow:auto;padding:20px;background:#eef2f4;font:14px/1.7 Consolas,monospace;border-radius:10px}
code{font-family:Consolas,monospace;overflow-wrap:anywhere}pre code{overflow-wrap:normal}
figure{max-width:100%;margin:42px 0;padding:10px 10px 14px;background:#f8f4eb;border:1px solid #ded5c4;border-radius:14px}
img{width:100%;max-width:100%;height:auto;display:block;border-radius:9px}
figcaption{font-size:14px;color:#566878;line-height:1.75;margin:12px 6px 0}.mobile-figure-hint{display:none;font-weight:700;color:#a44d14}
.table-wrap{overflow:auto;max-width:100%;margin:1.4em 0}table{border-collapse:collapse;width:100%;min-width:680px;font-size:14px;line-height:1.7}
th,td{border:1px solid #d5dcdd;padding:10px;text-align:left;min-width:110px}th{background:#e8eff1}
li{margin:.62em 0}
@media(max-width:600px){body{padding:24px 17px;font-size:16px;line-height:1.9}h1{font-size:27px}h2{font-size:22px;margin-top:2.25em}h3{font-size:19px}blockquote{margin:1.25em 0;padding:3px 15px}figure{margin:30px -3px;padding:5px 5px 10px;overflow:hidden}.figure-link{overflow-x:auto}.figure-link img{width:760px;max-width:none}figcaption{font-size:13px}.mobile-figure-hint{display:inline}pre{padding:15px;font-size:13px}}
</style></head><body><main>""" + body + "</main></body></html>\n"

    destination = Path(output) if output is not None else root / "chapter15" / "preview-pages" / "index.html"
    destination = destination.resolve()
    if not destination.is_relative_to(root):
        raise ValueError("output_outside_repository")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8", newline="\n")
    return destination


if __name__ == "__main__":
    print(build_preview(Path(__file__).resolve().parents[1]))
