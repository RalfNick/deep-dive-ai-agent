// Same native browser-QA approach as the book's existing chapter previews.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const captures = path.join(root, 'output/playwright/appendix-a-rc1');
await fs.mkdir(captures, { recursive: true });
const browser = await chromium.launch({ channel: 'msedge', headless: true });
const results = [];
try {
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const errors = [];
    const remote = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('requestfailed', request => errors.push(request.url()));
    await page.route(/^https?:/, route => { remote.push(route.request().url()); return route.abort(); });
    await page.goto(pathToFileURL(path.join(root, 'appendix_a/preview-pages/index.html')).href);
    await page.evaluate(() => document.fonts.ready);
    const audit = await page.evaluate(() => ({
      viewportWidth: innerWidth, documentWidth: document.documentElement.scrollWidth,
      figures: document.querySelectorAll('figure').length,
      tables: document.querySelectorAll('.table-wrap').length,
      loadedImages: [...document.images].filter(img => img.complete && img.naturalWidth > 0).length,
      brokenFragments: [...document.querySelectorAll('a[href^="#"]')]
        .filter(a => !document.getElementById(decodeURIComponent(a.hash.slice(1)))).length,
      containedTables: [...document.querySelectorAll('.table-wrap')]
        .every(t => t.getBoundingClientRect().right <= innerWidth),
      mobileFiguresScrollable: [...document.querySelectorAll('.figure-link')]
        .every(a => a.scrollWidth > a.clientWidth),
    }));
    if (audit.documentWidth > viewport.width || audit.figures !== 4 || audit.loadedImages !== 4 ||
        audit.tables !== 4 || audit.brokenFragments || !audit.containedTables || errors.length || remote.length ||
        (viewport.width === 390 && !audit.mobileFiguresScrollable)) {
      throw new Error(JSON.stringify({ audit, errors, remote }));
    }
    await page.screenshot({ path: path.join(captures, 'top-' + viewport.width + '.png') });
    results.push({ ...audit, pageErrors: errors.length, remoteRequests: remote.length });
    await page.close();
  }
  const diagramPage = await browser.newPage({ viewport: { width: 1600, height: 960 } });
  const images = (await fs.readdir(path.join(root, 'book/images/appendix-a'))).filter(n => n.endsWith('.svg')).sort();
  for (const name of images) {
    await diagramPage.goto(pathToFileURL(path.join(root, 'book/images/appendix-a', name)).href);
    await diagramPage.evaluate(() => document.fonts.ready);
    await diagramPage.screenshot({ path: path.join(captures, name.replace('.svg', '.png')) });
  }
  await diagramPage.close();
} finally { await browser.close(); }
console.log(JSON.stringify(results, null, 2));
