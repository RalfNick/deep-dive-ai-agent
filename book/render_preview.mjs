import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

import { assertMathAudit, offlineMathJaxOptions } from "./render_checks.mjs";

const require = createRequire(import.meta.url);
const { marked } = require("marked");
const { chromium } = require("playwright");
const mathJaxUrl = pathToFileURL(require.resolve("mathjax/tex-svg.js")).href;

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(.:)/, "$1")), "..");
const chapterName = process.argv[2] ?? "chapter1";
if (!/^chapter\d+$/.test(chapterName)) {
  throw new Error(`Invalid chapter name: ${chapterName}`);
}
const previewConfig = {
  chapter1: {
    chapterLabel: "第 1 章",
    shortTitle: "大模型入门",
    subtitle: "从 Token、Embedding 与 Transformer，一直走到可执行、可验证的 Coding Agent",
    formula: "Model + Context + Tools + Harness → Agent",
    characters: "2 万+",
    figures: "6 张",
    experiments: "5 个",
    exercises: "14 道",
  },
  chapter2: {
    chapterLabel: "第 2 章",
    shortTitle: "训练、对齐与推理",
    subtitle: "从预训练、SFT 与偏好优化，走到推理预算、结构化输出与模型选择",
    formula: "Pretraining → SFT → Preference / RL → Inference",
    characters: "3.4 万",
    figures: "7 张",
    experiments: "7 个",
    exercises: "17 道",
  },
  chapter3: {
    chapterLabel: "第 3 章",
    shortTitle: "从生成到闭环执行",
    subtitle: "手写最小 Agent Loop，讲清工具协议、状态、停止、错误、验证与现代 Agent SDK",
    formula: "Observe → Decide → Act → Verify → Repeat",
    characters: "1.07 万 / 2.28 万",
    figures: "7 张",
    experiments: "5+1 个",
    exercises: "18 道",
  },
  chapter4: {
    chapterLabel: "第 4 章",
    shortTitle: "Harness Engineering",
    subtitle: "同一决策策略，为什么换一个外围系统就像换了一个 Agent",
    formula: "Context + Policy + Executor + State + Verifier + Recorder",
    characters: "2.7 万+",
    figures: "8 张",
    experiments: "5 组",
    exercises: "15+3 道",
  },
};
const config = previewConfig[chapterName];
if (!config) throw new Error(`Missing preview config for ${chapterName}`);
const chapterPath = path.join(repoRoot, "book", `${chapterName}.md`);
const outputDir = path.join(repoRoot, "output", "pdf");
const htmlPath = path.join(outputDir, `${chapterName}-preview.html`);
const pdfPath = path.join(outputDir, `${chapterName}-preview.pdf`);
const edgePath = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";

await fs.mkdir(outputDir, { recursive: true });

let source = await fs.readFile(chapterPath, "utf8");

const footnotes = new Map();
source = source.replace(/^\[\^([^\]]+)\]:\s*(.+)$/gm, (_, id, content) => {
  footnotes.set(id, content.trim());
  return "";
});

const referencedFootnotes = [];
source = source.replace(/\[\^([^\]]+)\]/g, (_, id) => {
  if (!referencedFootnotes.includes(id)) referencedFootnotes.push(id);
  const number = referencedFootnotes.indexOf(id) + 1;
  return `<sup class="footnote-ref"><a href="#footnote-${id}" id="footnote-ref-${id}">${number}</a></sup>`;
});

const blockMath = [];
source = source.replace(/\\\[([\s\S]*?)\\\]/g, (_, formula) => {
  const index = blockMath.push(formula.trim()) - 1;
  return `\n<math-block data-index="${index}"></math-block>\n`;
});

const inlineMath = [];
source = source.replace(/\\\((.+?)\\\)/g, (_, formula) => {
  const index = inlineMath.push(formula.trim()) - 1;
  return `<math-inline data-index="${index}"></math-inline>`;
});
const expectedMathCount = blockMath.length + inlineMath.length;

marked.setOptions({ gfm: true, breaks: false });
let articleHtml = marked.parse(source);

articleHtml = articleHtml.replace(/<math-block data-index="(\d+)"><\/math-block>/g, (_, rawIndex) => {
  return `<div class="display-math">\\[${blockMath[Number(rawIndex)]}\\]</div>`;
});
articleHtml = articleHtml.replace(/<math-inline data-index="(\d+)"><\/math-inline>/g, (_, rawIndex) => {
  return `<span class="inline-math">\\(${inlineMath[Number(rawIndex)]}\\)</span>`;
});

articleHtml = articleHtml.replace(
  /<p><img src="([^"]+)" alt="([^"]*)"><\/p>/g,
  (_, src, alt) => `<figure><img src="${src}" alt="${alt}"><figcaption>${alt}</figcaption></figure>`,
);

const footnoteHtml = referencedFootnotes.length
  ? `<section class="footnotes"><h2>注释</h2><ol>${referencedFootnotes
      .map((id) => {
        const note = footnotes.get(id) ?? `缺少脚注定义：${id}`;
        return `<li id="footnote-${id}">${marked.parseInline(note)} <a class="footnote-back" href="#footnote-ref-${id}">↩</a></li>`;
      })
      .join("")}</ol></section>`
  : "";

const bookBaseUrl = pathToFileURL(path.join(repoRoot, "book") + path.sep).href;
const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <base href="${bookBaseUrl}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>《深入浅出 AI Agent》${config.chapterLabel}预览</title>
  <script>
    window.MathJax = {
      tex: { inlineMath: [["\\\\(", "\\\\)"]], displayMath: [["\\\\[", "\\\\]"]] },
      svg: { fontCache: "global" },
      options: ${JSON.stringify(offlineMathJaxOptions)}
    };
  </script>
  <script defer src="${mathJaxUrl}"></script>
  <style>
    :root {
      --ink: #172033;
      --muted: #5d6b82;
      --line: #dce3ed;
      --blue: #3157d5;
      --blue-soft: #eef3ff;
      --cyan: #0a91aa;
      --orange: #df6b20;
      --paper: #ffffff;
      --code: #f5f7fb;
    }
    * { box-sizing: border-box; }
    html { background: #e9edf3; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: "Microsoft YaHei", "DengXian", "Noto Sans CJK SC", sans-serif;
      font-size: 15.2px;
      line-height: 1.78;
      letter-spacing: 0.01em;
      text-rendering: optimizeLegibility;
    }
    .cover {
      min-height: 248mm;
      padding: 38mm 20mm 24mm;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      color: #fff;
      background:
        radial-gradient(circle at 82% 18%, rgba(58, 218, 225, .38), transparent 28%),
        radial-gradient(circle at 10% 90%, rgba(109, 91, 255, .46), transparent 35%),
        linear-gradient(145deg, #101b3f 0%, #17336d 55%, #0c6c85 100%);
      break-after: page;
    }
    .cover-kicker { font-size: 16px; letter-spacing: .2em; opacity: .78; }
    .cover h1 {
      margin: 16mm 0 5mm;
      color: #fff;
      border: 0;
      font-size: 42px;
      line-height: 1.25;
      letter-spacing: .04em;
    }
    .cover-subtitle { max-width: 135mm; font-size: 22px; line-height: 1.6; color: #dce9ff; }
    .cover-formula {
      display: inline-block;
      margin-top: 18mm;
      padding: 5mm 8mm;
      border: 1px solid rgba(255,255,255,.36);
      border-radius: 4mm;
      background: rgba(255,255,255,.10);
      font-size: 18px;
      font-weight: 700;
    }
    .cover-meta {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 4mm;
    }
    .cover-meta div {
      min-height: 24mm;
      padding: 4mm;
      border-radius: 3mm;
      background: rgba(255,255,255,.09);
      border: 1px solid rgba(255,255,255,.17);
    }
    .cover-meta strong { display: block; font-size: 22px; color: #fff; }
    .cover-meta span { font-size: 12px; color: #c8d7f3; }
    main { width: 100%; }
    article { width: 100%; }
    article > h1:first-child {
      margin: 0 0 12mm;
      padding: 17mm 0 7mm;
      border-bottom: 2px solid var(--blue);
      color: #172b5b;
      font-size: 31px;
      line-height: 1.35;
    }
    h2, h3 { break-after: avoid; page-break-after: avoid; }
    h2 {
      margin: 11mm 0 4mm;
      padding: 2.2mm 0 2.2mm 4mm;
      border-left: 4px solid var(--blue);
      border-bottom: 1px solid var(--line);
      color: #183771;
      font-size: 22px;
      line-height: 1.4;
    }
    h3 {
      margin: 7mm 0 2.5mm;
      color: #20345d;
      font-size: 17.5px;
      line-height: 1.5;
    }
    p { margin: 0 0 3.6mm; orphans: 3; widows: 3; }
    strong { color: #172b5b; }
    a { color: #2255bd; text-decoration: none; }
    ul, ol { margin: 1.5mm 0 4mm; padding-left: 7mm; }
    li { margin-bottom: 1.4mm; }
    article > ol > li { break-inside: avoid; page-break-inside: avoid; }
    blockquote {
      margin: 5mm 0;
      padding: 4mm 5mm;
      border: 1px solid #cbd7f8;
      border-left: 4px solid var(--blue);
      border-radius: 2mm;
      background: var(--blue-soft);
      color: #273a62;
      break-inside: avoid;
    }
    blockquote p:last-child { margin-bottom: 0; }
    code {
      padding: .2em .38em;
      border-radius: 4px;
      background: #edf1f7;
      color: #b33f26;
      font-family: Consolas, "Cascadia Mono", monospace;
      font-size: .9em;
    }
    pre {
      margin: 4mm 0 5mm;
      padding: 4mm 5mm;
      overflow: hidden;
      border: 1px solid #d8e0eb;
      border-radius: 2mm;
      background: var(--code);
      color: #1b2940;
      font-size: 11.4px;
      line-height: 1.55;
      white-space: pre-wrap;
      word-break: break-word;
      break-inside: avoid;
    }
    pre code { padding: 0; background: transparent; color: inherit; font-size: inherit; }
    table {
      width: 100%;
      margin: 4mm 0 6mm;
      border-collapse: collapse;
      font-size: 12.2px;
      line-height: 1.55;
      break-inside: auto;
    }
    thead { display: table-header-group; }
    tr { break-inside: avoid; page-break-inside: avoid; }
    th, td { padding: 2.2mm 2.4mm; border: 1px solid #d8e0ea; vertical-align: top; }
    th { color: #183771; background: #edf3ff; font-weight: 700; }
    tbody tr:nth-child(even) { background: #fafbfe; }
    figure { margin: 7mm auto 8mm; text-align: center; break-inside: avoid; }
    figure img { display: block; width: 100%; max-height: 176mm; object-fit: contain; margin: 0 auto; }
    figcaption { margin-top: 2.5mm; color: var(--muted); font-size: 11.5px; }
    .display-math { margin: 4mm 0 5mm; text-align: center; overflow: hidden; break-inside: avoid; }
    .inline-math { white-space: nowrap; }
    mjx-container { max-width: 100%; }
    .footnote-ref { font-size: .72em; line-height: 0; vertical-align: super; }
    .footnotes { margin-top: 12mm; padding-top: 3mm; border-top: 1px solid var(--line); font-size: 10.4px; line-height: 1.48; color: #4d5c73; }
    .footnotes h2 { margin-top: 0; }
    .footnotes ol { columns: 2 70mm; column-gap: 8mm; }
    .footnotes li { margin-bottom: 1.4mm; break-inside: avoid; }
    .footnote-back { margin-left: 1mm; }
    @media screen {
      body { max-width: 210mm; margin: 12mm auto; box-shadow: 0 8px 38px rgba(21,32,57,.16); }
      main { padding: 0 18mm 20mm; }
      .cover { margin: 0 -18mm; }
    }
    @media print {
      html, body { background: #fff; }
      main { padding: 0; }
      .cover { min-height: 244mm; }
    }
  </style>
</head>
<body>
  <main>
    <section class="cover">
      <div>
        <div class="cover-kicker">深入浅出 AI AGENT · 章节预览</div>
        <h1>${config.chapterLabel}<br>${config.shortTitle}</h1>
        <div class="cover-subtitle">${config.subtitle}</div>
        <div class="cover-formula">${config.formula}</div>
      </div>
      <div class="cover-meta">
        <div><strong>${config.characters}</strong><span>内容规模</span></div>
        <div><strong>${config.figures}</strong><span>原创技术图</span></div>
        <div><strong>${config.experiments}</strong><span>可运行实验</span></div>
        <div><strong>${config.exercises}</strong><span>分级练习</span></div>
      </div>
    </section>
    <article>${articleHtml}${footnoteHtml}</article>
  </main>
</body>
</html>`;

await fs.writeFile(htmlPath, html, "utf8");

const browser = await chromium.launch({ executablePath: edgePath, headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 1 });
  const pageErrors = [];
  const failedRequests = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") pageErrors.push(message.text());
  });
  page.on("requestfailed", (request) => {
    failedRequests.push(`${request.url()} (${request.failure()?.errorText ?? "unknown error"})`);
  });

  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load", timeout: 60000 });
  await page.waitForFunction(() => document.fonts.status === "loaded", null, { timeout: 30000 });
  await page.waitForFunction(() => Boolean(window.MathJax?.startup?.promise), null, { timeout: 30000 });
  await page.evaluate(async () => window.MathJax.startup.promise);

  const mathAudit = await page.evaluate(() => ({
    rendered: document.querySelectorAll(
      ".display-math > mjx-container, .inline-math > mjx-container",
    ).length,
    rawWrappers: [...document.querySelectorAll(".display-math, .inline-math")].filter((element) =>
      /\\\(|\\\[/.test(element.textContent ?? ""),
    ).length,
  }));
  assertMathAudit({
    expected: expectedMathCount,
    rendered: mathAudit.rendered,
    rawWrappers: mathAudit.rawWrappers,
    pageErrors,
    failedRequests,
  });

  await page.pdf({
    path: pdfPath,
    format: "A4",
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: `<div style="width:100%;padding:0 18mm;font-family:'Microsoft YaHei',sans-serif;font-size:8px;color:#718096;display:flex;justify-content:space-between"><span>深入浅出 AI Agent</span><span>${config.chapterLabel} · ${config.shortTitle}</span></div>`,
    footerTemplate: `<div style="width:100%;padding:0 18mm;font-family:'Microsoft YaHei',sans-serif;font-size:8px;color:#718096;text-align:center"><span class="pageNumber"></span> / <span class="totalPages"></span></div>`,
    margin: { top: "17mm", right: "18mm", bottom: "18mm", left: "18mm" },
    preferCSSPageSize: false,
  });
} finally {
  await browser.close();
}

console.log(`HTML: ${htmlPath}`);
console.log(`PDF: ${pdfPath}`);
