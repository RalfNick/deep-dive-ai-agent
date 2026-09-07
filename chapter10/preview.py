"""Optional local HTML preview; does not change the public site's allowlist."""
from pathlib import Path
import re
from urllib.parse import urlsplit


def build_preview(root: Path) -> Path:
    import markdown  # Optional: install chapter10/requirements-preview.txt.
    source = (root / "book" / "chapter10.md").read_text(encoding="utf-8")
    body = markdown.markdown(source, extensions=["extra", "toc"])

    def relative(match):
        prefix, target, suffix = match.groups()
        if not target or target.startswith("#") or urlsplit(target).scheme:
            return match.group(0)
        return f'{prefix}../../book/{target}{suffix}'

    body = re.sub(r'((?:src|href)=")([^"]+)(")', relative, body)
    body = re.sub(r'<p>(<img[^>]+alt="([^"]+)"[^>]*>)</p>',
                  r'<figure>\1<figcaption>\2</figcaption></figure>', body)
    body = re.sub(r'(<table>.*?</table>)', r'<div class="table-wrap">\1</div>', body, flags=re.S)
    html = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>第 10 章 · 大规模工具集与异步任务 · 本地候选预览</title>
<style>
*{box-sizing:border-box}html{background:#f5f1e9;color:#172c49}
body{max-width:860px;margin:0 auto;background:#fffdfa;padding:48px 52px;font:17px/1.95 "Microsoft YaHei",sans-serif}
h1{font-size:30px;line-height:1.45}h2{font-size:24px;margin-top:2.6em;border-top:1px solid #ded8cc;padding-top:1em;line-height:1.5}
h3{font-size:20px;margin-top:2em}p{margin:1.1em 0}a{color:#155ca6;overflow-wrap:anywhere}
blockquote{margin:1.5em 0;padding:1px 22px;border-left:4px solid #5782a6;background:#eff4f6}
pre{overflow:auto;padding:20px;background:#f0f3f5;font:14px/1.7 Consolas,monospace;border-radius:10px}
code{font-family:Consolas,monospace;overflow-wrap:anywhere}pre code{overflow-wrap:normal}
figure{margin:38px 0}img{width:100%;height:auto;display:block;border-radius:10px}figcaption{font-size:14px;color:#576676;line-height:1.7;margin-top:12px}
.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.7}th,td{border:1px solid #d9dedf;padding:10px;text-align:left;min-width:110px}th{background:#e9eff2}
li{margin:.65em 0}.footnote{font-size:14px;border-top:1px solid #ddd;margin-top:40px}
@media(max-width:600px){body{padding:24px 18px;font-size:16px}h1{font-size:26px}h2{font-size:22px}h3{font-size:19px}}
</style><main>''' + body + "</main></html>\n"
    output = root / "chapter10" / "preview-pages" / "index.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8", newline="\n")
    return output


if __name__ == "__main__":
    print(build_preview(Path(__file__).resolve().parents[1]))
