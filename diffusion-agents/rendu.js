// Rend une window card HTML en PDF A4 (à envoyer) et en PNG (aperçu WhatsApp / back-office).
// Usage : node rendu.js <fiche.html> <sortie.pdf> <sortie.png>
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [html, pdf, png] = process.argv.slice(2);
  if (!html || !pdf || !png) { console.error('usage: node rendu.js fiche.html sortie.pdf sortie.png'); process.exit(2); }
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 2 });
  await page.goto('file://' + path.resolve(html), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: pdf, format: 'A4', printBackground: true, preferCSSPageSize: true });
  await page.screenshot({ path: png, fullPage: false });
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
