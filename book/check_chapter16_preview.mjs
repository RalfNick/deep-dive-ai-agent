// Local QA only: existing Edge and book Playwright, no server/public mutation.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath,pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const html=path.join(root,'chapter16/preview-pages/index.html');
const output=path.join(root,'chapter16/preview-pages/screenshots');
await fs.mkdir(output,{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const audits=[];
try {
  for (const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
    const page=await browser.newPage({viewport});
    const failures=[];
    page.on('pageerror',e=>failures.push(`pageerror:${e.message}`));
    page.on('requestfailed',r=>failures.push(`request:${r.url()}`));
    page.on('console',msg=>{if(msg.type()==='error') failures.push(`console:${msg.text()}`)});
    await page.goto(pathToFileURL(html).href,{waitUntil:'load'});
    await page.evaluate(()=>document.fonts.ready);
    const audit=await page.evaluate(()=>({
      viewportWidth:innerWidth,documentWidth:document.documentElement.scrollWidth,
      figures:document.querySelectorAll('figure').length,figureLinks:document.querySelectorAll('figure > a.figure-link').length,
      tables:document.querySelectorAll('.table-wrap').length,
      images:[...document.images].map(i=>({loaded:i.complete&&i.naturalWidth>0,width:i.clientWidth})),
      brokenFragments:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(decodeURIComponent(a.hash.slice(1)))).length,
      figureScrollable:[...document.querySelectorAll('.figure-link')].every(n=>n.scrollWidth>n.clientWidth),
      tableContained:[...document.querySelectorAll('.table-wrap')].every(n=>n.getBoundingClientRect().right<=innerWidth&&n.scrollWidth>=n.clientWidth),
      localImagesOnly:[...document.images].every(i=>i.getAttribute('src').includes('/book/images/chapter16/')),
      remoteRuntime:document.querySelectorAll('script[src^="http"],link[href^="http"]').length
    }));
    if(audit.documentWidth>viewport.width||audit.figures!==7||audit.figureLinks!==7||audit.tables!==5||audit.images.length!==7||
       audit.images.some(i=>!i.loaded||i.width<=0)||audit.brokenFragments||!audit.tableContained||!audit.localImagesOnly||audit.remoteRuntime||failures.length||
       (viewport.width===390&&(!audit.figureScrollable||audit.images.some(i=>i.width<700)))) throw new Error(JSON.stringify({audit,failures}));
    await page.screenshot({path:path.join(output,`chapter16-${viewport.width}x${viewport.height}-full.png`),fullPage:true});
    await page.screenshot({path:path.join(output,`chapter16-${viewport.width}x${viewport.height}-top.png`)});
    if(viewport.width===1440) for(const number of [2,5,6,7]) await page.locator('figure').filter({has:page.locator(`img[alt^="图 16-${number} "]`)}).screenshot({path:path.join(output,`chapter16-figure-${number}.png`)});
    audits.push(audit);
    await page.close();
  }
} finally {await browser.close();}
console.log(JSON.stringify(audits,null,2));
