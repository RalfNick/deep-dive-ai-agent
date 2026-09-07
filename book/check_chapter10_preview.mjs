// Optional visual QA using the book's existing Playwright dependency.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const url = pathToFileURL(path.join(root, 'chapter10/preview-pages/index.html')).href;
const output = path.join(root, 'output/playwright');
await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch({ channel: 'msedge', headless: true });
const audits = [];
try {
  for (const width of [1280, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 1000 } });
    const failures = [];
    page.on('pageerror', error => failures.push(error.message));
    page.on('requestfailed', request => failures.push(request.failure()?.errorText));
    await page.goto(url, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    const audit = await page.evaluate(() => ({
      title: document.querySelector('h1').textContent,
      width: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      images: [...document.images].map(img => ({ loaded: img.complete && img.naturalWidth > 0, width: img.clientWidth })),
      figures: document.querySelectorAll('figure').length,
      brokenFragments: [...document.querySelectorAll('a[href^="#"]')].filter(a => !document.getElementById(decodeURIComponent(a.hash.slice(1)))).length,
      footnotes: document.querySelectorAll('.footnote li').length,
    }));
    if (audit.documentWidth > width || audit.images.length !== 6 || audit.images.some(img => !img.loaded) || audit.brokenFragments || failures.length) {
      throw new Error(JSON.stringify({ audit, failures }));
    }
    await page.screenshot({ path: path.join(output, `chapter10-${width}-intro.png`) });
    await page.locator('figure').first().scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(output, `chapter10-${width}-figure.png`) });
    audits.push(audit);
    await page.close();
  }
} finally {
  await browser.close();
}
console.log(JSON.stringify(audits, null, 2));
