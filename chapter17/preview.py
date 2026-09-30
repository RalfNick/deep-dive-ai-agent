"""Local-only Chapter 17 reading preview. Never updates public site files."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re
from urllib.parse import urlsplit

from .output import _is_reparse


def build_preview(root: Path, *, output: Path | None = None) -> Path:
    import markdown

    root = Path(root).absolute()
    allowed = root / "chapter17" / "preview-pages"
    destination = (Path(output).absolute() if output is not None
                   else allowed / "index.html")
    if (destination.suffix != ".html" or not destination.is_relative_to(allowed)
            or ".." in destination.parts):
        raise ValueError("preview output must stay under chapter17/preview-pages")
    for candidate in (destination, *destination.parents):
        if _is_reparse(candidate):
            raise ValueError("linked preview path denied")
        if candidate == root:
            break
    source = (root / "book" / "chapter17.md").read_text(encoding="utf-8")
    body = markdown.markdown(source, extensions=["extra", "toc", "footnotes"])

    def relative(match: re.Match[str]) -> str:
        prefix, target, suffix = match.groups()
        if not target or target.startswith("#") or urlsplit(target).scheme:
            return match.group(0)
        return f"{prefix}../../book/{target}{suffix}"

    body = re.sub(r'((?:src|href)=")([^"]+)(")', relative, body)

    def figure(match: re.Match[str]) -> str:
        image, alt, target = match.groups()
        return ('<figure><a class="figure-link" href="' + escape(target, quote=True)
                + '" target="_blank" rel="noopener" aria-label="打开原图">'
                + image + '</a><figcaption><span class="mobile-hint">移动端可在图内左右滑动。 </span>'
                + escape(alt) + '</figcaption></figure>')

    body = re.sub(r'<p>(<img[^>]+alt="([^"]+)"[^>]+src="([^"]+)"[^>]*>)</p>', figure, body)
    body = re.sub(r'(<table>.*?</table>)',
                  r'<div class="table-wrap" role="region" aria-label="可横向滚动的表格">\1</div>',
                  body, flags=re.S)
    page = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>第17章 多模态与实时 Agent · 本地候选预览</title><style>
*{box-sizing:border-box}html{background:#ede8df;color:#17365d;scroll-behavior:smooth}
body{max-width:960px;margin:0 auto;background:#fffdf8;padding:52px 58px;font:17px/1.96 "Microsoft YaHei","PingFang SC",sans-serif;overflow-wrap:anywhere}
main{max-width:100%}h1{font-size:33px;line-height:1.4;margin:.2em 0 1.3em;color:#112e53}
h2{font-size:25px;margin-top:2.7em;border-top:1px solid #dcd4c6;padding-top:1em;line-height:1.5;color:#164d75}
h3{font-size:20px;margin-top:2em;line-height:1.55;color:#305a65}p{margin:1em 0}a{color:#155ca6}
blockquote{margin:1.4em 0;padding:5px 22px;border-left:4px solid #527da2;background:#edf4f5}
pre{max-width:100%;overflow:auto;padding:20px;background:#eef2f4;font:14px/1.7 Consolas,monospace;border-radius:10px}
code{font-family:Consolas,monospace;overflow-wrap:anywhere}pre code{overflow-wrap:normal}
figure{max-width:100%;margin:40px 0;padding:10px 10px 14px;background:#f8f4eb;border:1px solid #ded5c4;border-radius:14px}
.figure-link{display:block;overflow-x:auto;border-radius:12px;outline-offset:4px}img{width:100%;max-width:100%;height:auto;display:block;border-radius:9px}
figcaption{font-size:14px;color:#566878;line-height:1.7;margin:12px 6px 0}.mobile-hint{display:none;font-weight:700;color:#a44d14}
.table-wrap{overflow:auto;max-width:100%;margin:1.4em 0}table{border-collapse:collapse;width:100%;min-width:680px;font-size:14px;line-height:1.7}
th,td{border:1px solid #d5dcdd;padding:10px;text-align:left;min-width:110px}th{background:#e8eff1}li{margin:.62em 0}
@media(max-width:600px){body{padding:24px 17px;font-size:16px;line-height:1.9}h1{font-size:27px}h2{font-size:22px}h3{font-size:19px}
blockquote{padding:3px 15px}figure{margin:30px -3px;padding:5px 5px 10px;overflow:hidden}.figure-link img{width:760px;max-width:none}
figcaption{font-size:13px}.mobile-hint{display:inline}pre{padding:15px;font-size:13px}}
</style></head><body><main>''' + body + '</main></body></html>\n'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page, encoding="utf-8", newline="\n")
    return destination


if __name__ == "__main__":
    print(build_preview(Path(__file__).resolve().parents[1]))
