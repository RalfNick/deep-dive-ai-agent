// Optional local visual QA for the unpublished Chapter 15 candidate.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

const bookDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)));
const root = path.resolve(bookDir, '..');
const htmlPath = path.join(root, 'chapter15/preview-pages/index.html');
const output = path.join(root, 'chapter15/preview-pages/screenshots');
await fs.mkdir(output, { recursive: true });

const browser = await chromium.launch({ channel: 'msedge', headless: true });
const audits = [];
try {
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const failures = [];
    page.on('pageerror', error => failures.push(`pageerror:${error.message}`));
    page.on('requestfailed', request => failures.push(`request:${request.url()}:${request.failure()?.errorText}`));
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    const audit = await page.evaluate(() => ({
      viewportWidth: innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      figures: document.querySelectorAll('figure').length,
      figureLinks: document.querySelectorAll('figure > a.figure-link').length,
      tables: document.querySelectorAll('.table-wrap').length,
      images: [...document.images].map(img => ({
        loaded: img.complete && img.naturalWidth > 0,
        width: img.clientWidth,
      })),
      brokenFragments: [...document.querySelectorAll('a[href^="#"]')]
        .filter(link => !document.getElementById(decodeURIComponent(link.hash.slice(1)))).length,
      figureScrollable: [...document.querySelectorAll('figure > a.figure-link')]
        .every(node => node.scrollWidth > node.clientWidth),
      tableContained: [...document.querySelectorAll('.table-wrap')]
        .every(node => node.getBoundingClientRect().right <= innerWidth && node.scrollWidth >= node.clientWidth),
      chapter15ImagesOnly: [...document.images]
        .every(img => img.getAttribute('src')?.includes('/book/images/chapter15/')),
    }));
    if (audit.documentWidth > viewport.width || audit.figures !== 7 ||
        audit.figureLinks !== 7 || audit.tables < 4 || audit.images.length !== 7 ||
        audit.images.some(item => !item.loaded || item.width <= 0) ||
        audit.brokenFragments || !audit.tableContained || !audit.chapter15ImagesOnly ||
        failures.length ||
        (viewport.width === 390 && (!audit.figureScrollable ||
          audit.images.some(item => item.width < 700)))) {
      throw new Error(JSON.stringify({ audit, failures }));
    }
    const label = `${viewport.width}x${viewport.height}`;
    await page.screenshot({ path: path.join(output, `chapter15-${label}-full.png`), fullPage: true });
    if (viewport.width === 1440) {
      for (const number of [2, 4, 5]) {
        await page.locator('figure').nth(number - 1).screenshot({
          path: path.join(output, `chapter15-figure-${number}-rc2.png`),
        });
      }
    }
    audits.push(audit);
    await page.close();
  }
} finally {
  await browser.close();
}
console.log(JSON.stringify(audits, null, 2));
