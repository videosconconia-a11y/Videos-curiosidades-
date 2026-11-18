// Genera avatar.png (1024x1024) y banner_youtube.png (2560x1440) a partir de dibujar.html
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + path.join(__dirname, 'dibujar.html')); await p.waitForFunction(() => window.DONE);
  for (const [id, out] of [['a', 'avatar.png'], ['b', 'banner_youtube.png']]) {
    const url = await p.evaluate(id => document.getElementById(id).toDataURL('image/png'), id);
    fs.writeFileSync(path.join(__dirname, out), Buffer.from(url.split(',')[1], 'base64'));
  }
  await b.close();
})();
