// Renderiza la escena 3D cuadro a cuadro en Chromium sin ventana y la entrega a ffmpeg.
// Uso: node render.cjs video [salida.mp4] [desde_s] [hasta_s]
//      node render.cjs stills carpeta t1 t2 ...
const http = require('http'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const { chromium } = require('playwright');
const ROOT = __dirname, FPS = 30;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const server = http.createServer((q, r) => {
  const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]));
  if (!f.startsWith(ROOT) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r);
});
(async () => {
  await new Promise(ok => server.listen(0, ok));
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => { if (m.type() === 'error') console.error('[page]', m.text()); });
  page.on('pageerror', e => { console.error('[page error]', e.message); process.exit(1); });
  await page.goto(`http://localhost:${server.address().port}/index.html`);
  await page.waitForFunction(() => window.READY === true, null, { timeout: 120000 });
  const total = JSON.parse(fs.readFileSync(path.join(ROOT, 'timeline.json'))).total;
  const mode = process.argv[2];
  const grab = async t => {
    const url = await page.evaluate(t => { window.renderAt(t); return window.grab(0.94); }, t);
    return Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
  };
  if (mode === 'stills') {
    const dir = process.argv[3]; fs.mkdirSync(dir, { recursive: true });
    for (const s of process.argv.slice(4)) { const t = parseFloat(s); fs.writeFileSync(path.join(dir, `f_${t.toFixed(2)}.jpg`), await grab(t)); console.log('still', t); }
  } else {
    const out = process.argv[3] || path.join(ROOT, '..', 'escena3d.mp4');
    const t0 = parseFloat(process.argv[4] || 0), t1 = parseFloat(process.argv[5] || total);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-r', String(FPS), '-i', '-',
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '15', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const f0 = Math.round(t0 * FPS), f1 = Math.round(t1 * FPS); const start = Date.now();
    for (let f = f0; f < f1; f++) {
      const buf = await grab(f / FPS);
      if (!ff.stdin.write(buf)) await new Promise(ok => ff.stdin.once('drain', ok));
      if ((f - f0) % 60 === 0) console.log(`cuadro ${f}/${f1}  ${((Date.now() - start) / 1000 / Math.max(1, f - f0)).toFixed(2)} s/cuadro`);
    }
    ff.stdin.end(); await new Promise(ok => ff.on('close', ok));
  }
  await browser.close(); server.close();
})();
