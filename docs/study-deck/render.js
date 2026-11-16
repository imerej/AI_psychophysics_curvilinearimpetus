// Renders deck.html to PDF.  Usage: node render.js [out.pdf]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const out = process.argv[2] || path.join(__dirname, 'study-plan-deck.pdf');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto('file://' + path.join(__dirname, 'deck.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: out, width: '1280px', height: '720px', printBackground: true, preferCSSPageSize: true });
  await browser.close();
  console.log('wrote', out);
})();
