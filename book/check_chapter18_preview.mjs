// Local visual QA, using the already installed browser; never publishes.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const html = path.join(root, 'chapter18/preview-pages/index.html');
const captures = path.join(root, 'chapter18/preview-pages/screenshots');
await fs.mkdir(captures, { recursive: true });
const browser = await chromium.launch({ channel: 'msedge', headless: true });
const results = [];
try {
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const errors = [];
    const remoteRequests = [];
    page.on('pageerror', error => errors.push(`page: ${error.message}`));
    page.on('requestfailed', request => errors.push(`request: ${request.url()}`));
    page.on('request', request => { if (/^https?:/.test(request.url())) remoteRequests.push(request.url()); });
    await page.goto(pathToFileURL(html).href, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    const audit = await page.evaluate(() => ({
      viewportWidth: innerWidth, documentWidth: document.documentElement.scrollWidth,
      figures: document.querySelectorAll('figure').length,
      tables: document.querySelectorAll('.table-wrap').length,
      images: [...document.images].map(image => ({
        loaded: image.complete && image.naturalWidth > 0,
        local: image.getAttribute('src').includes('/book/images/chapter18/'),
      })),
      brokenFragments: [...document.querySelectorAll('a[href^="#"]')]
        .filter(link => !document.getElementById(decodeURIComponent(link.hash.slice(1)))).length,
      tableContained: [...document.querySelectorAll('.table-wrap')]
        .every(table => table.getBoundingClientRect().right <= innerWidth && table.scrollWidth >= table.clientWidth),
      figureScrollable: [...document.querySelectorAll('.figure-link')].every(link => link.scrollWidth > link.clientWidth),
      headingLines: (() => {
        const text = document.querySelector('h1').firstChild;
        const lines = {};
        for (let i = 0; i < text.length; i++) {
          if (!text.textContent[i].trim()) continue;
          const range = document.createRange();
          range.setStart(text, i); range.setEnd(text, i + 1);
          const y = Math.round(range.getBoundingClientRect().top);
          lines[y] = (lines[y] ?? 0) + 1;
        }
        return Object.values(lines);
      })(),
    }));
    if (audit.documentWidth > viewport.width || audit.figures !== 7 || audit.tables !== 5 ||
        audit.images.length !== 7 || audit.images.some(image => !image.loaded || !image.local) ||
        audit.brokenFragments || Math.min(...audit.headingLines) < 3 || !audit.tableContained || errors.length || remoteRequests.length ||
        (viewport.width === 390 && !audit.figureScrollable)) {
      throw new Error(JSON.stringify({ viewport, audit, errors, remoteRequests }));
    }
    await page.screenshot({ path: path.join(captures, `chapter18-rc1-${viewport.width}x${viewport.height}-top.png`) });
    // Capture the complete overview and delegation figure as additional reading evidence.
    for (const index of [2, 6]) {
      await page.locator('figure').nth(index).screenshot({
        path: path.join(captures, `chapter18-rc1-${viewport.width}-figure-${index + 1}.png`),
      });
    }
    results.push({ ...audit, pageErrors: errors.length, remoteRequests: remoteRequests.length });
    await page.close();
  }
} finally { await browser.close(); }
console.log(JSON.stringify(results, null, 2));
