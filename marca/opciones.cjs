// Dibuja tres opciones de avatar (opcion1..3.png) con los mismos sprites de los vídeos
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
(async () => {
  const sprites = fs.readFileSync(path.join(__dirname, '..', 'videos', 'troya', 'escena3d', 'sprites.js'), 'utf8').replace(/^export /gm, '');
  const html = fs.readFileSync(path.join(__dirname, 'dibujar.html'), 'utf8');
  const helmetSrc = html.slice(html.indexOf('function helmet'), html.indexOf('function bg('));
  const b = await chromium.launch(); const p = await b.newPage();
  const page = fs.readFileSync(path.join(__dirname, 'opciones.html'), 'utf8')
    .replace('<script>', '<script>' + sprites + '\n' + helmetSrc.replace('function helmet(g, s){', "function helmet(g, s, gold){") + '\n');
  await p.setContent(page); await p.waitForFunction(() => window.DONE);
  for (const k of [1, 2, 3]) {
    const url = await p.evaluate(id => document.getElementById(id).toDataURL('image/png'), 'o' + k);
    fs.writeFileSync(path.join(__dirname, `opcion${k}.png`), Buffer.from(url.split(',')[1], 'base64'));
  }
  await b.close();
})();
