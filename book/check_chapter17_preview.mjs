// Local Chapter 17 visual QA; screenshots remain in the ignored preview folder.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = path.join(root, 'chapter17/preview-pages/index.html');
const captures = path.join(root, 'chapter17/preview-pages/screenshots');
await fs.mkdir(captures, { recursive: true });
const browser = await chromium.launch({ channel: 'msedge', headless: true });
const results = [];
try {
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const errors = [];
    page.on('pageerror', error => errors.push(`page: ${error.message}`));
    page.on('requestfailed', request => errors.push(`request: ${request.url()}`));
    await page.goto(pathToFileURL(html).href, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    const audit = await page.evaluate(() => ({
      viewportWidth: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      figures: document.querySelectorAll('figure').length,
      tables: document.querySelectorAll('.table-wrap').length,
      images: [...document.images].map(image => ({
        loaded: image.complete && image.naturalWidth > 0,
        local: image.getAttribute('src').includes('/book/images/chapter17/'),
      })),
      brokenFragments: [...document.querySelectorAll('a[href^="#"]')]
        .filter(link => !document.getElementById(decodeURIComponent(link.hash.slice(1)))).length,
      tableContained: [...document.querySelectorAll('.table-wrap')]
        .every(table => table.getBoundingClientRect().right <= innerWidth &&
                        table.scrollWidth >= table.clientWidth),
      figureScrollable: [...document.querySelectorAll('.figure-link')]
        .every(link => link.scrollWidth > link.clientWidth),
      remoteRuntime: document.querySelectorAll('script[src^="http"],link[href^="http"]').length,
    }));
    if (audit.documentWidth > viewport.width || audit.figures !== 7 ||
        audit.tables !== 5 || audit.images.length !== 7 ||
        audit.images.some(image => !image.loaded || !image.local) ||
        audit.brokenFragments || !audit.tableContained || audit.remoteRuntime ||
        errors.length || (viewport.width === 390 && !audit.figureScrollable)) {
      throw new Error(JSON.stringify({ viewport, audit, errors }));
    }
    await page.screenshot({
      path: path.join(captures, `chapter17-rc2-${viewport.width}x${viewport.height}-top.png`),
    });
    results.push(audit);
    await page.close();
  }
} finally {
  await browser.close();
}
console.log(JSON.stringify(results, null, 2));
