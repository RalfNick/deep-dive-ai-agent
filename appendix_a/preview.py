"""Standalone local reading preview, without changing published navigation."""
from html import escape
from pathlib import Path
import re
from urllib.parse import urlsplit


def build_preview(root: Path, *, output: Path | None = None) -> Path:
    root = Path(root).resolve()
    directory = (root / "appendix_a/preview-pages").resolve()
    # Reject both traversal and a preview directory redirected outside the repo.
    if not directory.is_relative_to(root):
        raise ValueError("preview directory escapes repository")
    destination = (output or directory / "index.html").resolve()
    if destination.parent != directory or destination.suffix != ".html":
        raise ValueError("preview output must be directly inside appendix_a/preview-pages")
    import markdown
    body = markdown.markdown((root / "book/appendix-a.md").read_text(encoding="utf-8"),
                             extensions=["extra", "toc", "footnotes"])

    def relative(match):
        prefix, target, suffix = match.groups()
        if not target or target.startswith("#") or urlsplit(target).scheme:
            return match.group(0)
        return prefix + "../../book/" + target + suffix

    body = re.sub(r'((?:src|href)=")([^"]+)(")', relative, body)

    def figure(match):
        image, alt, target = match.groups()
        return ('<figure><a class="figure-link" href="' + escape(target, quote=True)
                + '" target="_blank" rel="noopener">' + image + '</a><figcaption>'
                + '<span class="mobile-hint">图内可横向滑动，点击打开原图。 </span>'
                + escape(alt) + '</figcaption></figure>')

    body = re.sub(r'<p>(<img[^>]+alt="([^"]+)"[^>]+src="([^"]+)"[^>]*>)</p>', figure, body)
    body = re.sub(r'(<table>.*?</table>)', r'<div class="table-wrap" role="region" aria-label="可滚动表格">\1</div>', body, flags=re.S)
    page = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>附录 A · 本地候选预览</title><style>
*{box-sizing:border-box}html{background:#eee8dd;color:#17365d;scroll-behavior:smooth}
body{max-width:960px;margin:0 auto;padding:50px 56px;background:#fffdf8;font:17px/1.95 "Microsoft YaHei","PingFang SC",sans-serif;overflow-wrap:anywhere}
main{max-width:100%}h1{font-size:32px;line-height:1.45;margin:0 0 1.5em}h2{font-size:25px;line-height:1.5;margin-top:2.6em;border-top:1px solid #ddd4c5;padding-top:1em;color:#18577d}
h3{font-size:20px;line-height:1.6;margin-top:2em;color:#305b65}p{margin:1em 0}a{color:#155ca6}
blockquote{margin:1.4em 0;padding:5px 22px;border-left:4px solid #527da2;background:#edf4f5}
pre{max-width:100%;overflow:auto;padding:20px;background:#eef2f4;font:14px/1.7 Consolas,monospace;border-radius:10px}
code{font-family:Consolas,monospace;overflow-wrap:anywhere}pre code{overflow-wrap:normal}
figure{max-width:100%;margin:38px 0;padding:10px;background:#f8f4eb;border:1px solid #ded5c4;border-radius:14px}
.figure-link{display:block;overflow:auto}img{display:block;width:100%;height:auto;max-width:100%}
figcaption{font-size:14px;color:#566878;line-height:1.7;margin:12px 6px 0}.mobile-hint{display:none;font-weight:700}
.table-wrap{overflow:auto;max-width:100%;margin:1.4em 0}table{border-collapse:collapse;width:100%;min-width:680px;font-size:14px}
th,td{border:1px solid #d5dcdd;padding:10px;text-align:left;min-width:110px}th{background:#e8eff1}li{margin:.6em 0}
@media(max-width:600px){body{padding:24px 17px;font-size:16px;line-height:1.9}h1{font-size:27px}h2{font-size:22px}h3{font-size:19px}
blockquote{padding:3px 15px}figure{padding:5px 5px 10px;overflow:hidden}.figure-link img{width:760px;max-width:none}
.mobile-hint{display:inline}pre{padding:15px;font-size:13px}}
</style></head><body><main>''' + body + '</main></body></html>\n'
    directory.mkdir(parents=True, exist_ok=True)
    destination.write_text(page, encoding="utf-8", newline="\n")
    return destination


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(build_preview(root).relative_to(root).as_posix())
