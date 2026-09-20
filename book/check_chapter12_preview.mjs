// Optional visual QA using the book's pinned Playwright dependency.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

const bookDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)));
const root = path.resolve(bookDir, '..');
const htmlPath = path.join(root, 'chapter12/preview-pages/index.html');
const url = pathToFileURL(htmlPath).href;
const output = path.join(root, 'chapter12/preview-pages/screenshots');
await fs.mkdir(output, { recursive: true });

const browser = await chromium.launch({ channel: 'msedge', headless: true });
const audits = [];
try {
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const failures = [];
    page.on('pageerror', error => failures.push(`pageerror:${error.message}`));
    page.on('requestfailed', request => failures.push(`request:${request.url()}:${request.failure()?.errorText}`));
    await page.goto(url, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    const audit = await page.evaluate(() => ({
      title: document.title,
      heading: document.querySelector('h1')?.textContent,
      viewportWidth: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      figures: document.querySelectorAll('figure').length,
      figureLinks: document.querySelectorAll('figure > a.figure-link').length,
      images: [...document.images].map(img => ({
        loaded: img.complete && img.naturalWidth > 0,
        width: img.clientWidth,
        naturalWidth: img.naturalWidth,
      })),
      brokenFragments: [...document.querySelectorAll('a[href^="#"]')]
        .filter(a => !document.getElementById(decodeURIComponent(a.hash.slice(1)))).length,
      tableOverflow: [...document.querySelectorAll('.table-wrap')]
        .every(node => node.scrollWidth >= node.clientWidth),
    }));
    if (audit.documentWidth > viewport.width || audit.figures !== 7 ||
        audit.figureLinks !== 7 || audit.images.length !== 7 ||
        audit.images.some(item => !item.loaded || item.width <= 0) ||
        audit.brokenFragments || !audit.tableOverflow || failures.length) {
      throw new Error(JSON.stringify({ audit, failures }));
    }
    const label = `${viewport.width}x${viewport.height}`;
    await page.screenshot({ path: path.join(output, `chapter12-${label}-full.png`), fullPage: true });
    if (viewport.width === 390) {
      const figures = page.locator('figure');
      for (let index = 0; index < await figures.count(); index += 1) {
        await figures.nth(index).screenshot({ path: path.join(output, `chapter12-mobile-figure-${index + 1}.png`) });
      }
    }
    audits.push(audit);
    await page.close();
  }
} finally {
  await browser.close();
}
console.log(JSON.stringify(audits, null, 2));
