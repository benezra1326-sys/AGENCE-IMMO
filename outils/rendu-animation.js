// Usage : node outils/rendu-animation.js page.html dossier_images duree_s [fps]
// La page expose window.render(t) et un élément #stage 1080x1920. Une image PNG par frame (TRANSPARENT=1 : fond transparent, pour superposer à une vidéo).
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [, , page, out, dur, fpsArg] = process.argv;
  const fps = Number(fpsArg || 30), n = Math.round(Number(dur) * fps);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(page));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(800);
  const stage = await p.$('#stage');
  for (let i = 0; i < n; i++) {
    await p.evaluate(t => window.render(t), i / fps);
    await stage.screenshot({ path: path.join(out, 'f' + String(i).padStart(5, '0') + '.png'), omitBackground: !!process.env.TRANSPARENT });
  }
  await b.close();
  console.log(n + ' images');
})();
