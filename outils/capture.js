// Usage : node outils/capture.js page.html dossier_sortie -> un PNG 1080x1350 par <section class="s" id=...>
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [, , page, out] = process.argv;
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 1400 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(page));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(800);
  for (const el of await p.$$('section.s')) {
    const id = await el.getAttribute('id');
    await el.screenshot({ path: path.join(out, id + '.png') });
    console.log(id);
  }
  await b.close();
})();
