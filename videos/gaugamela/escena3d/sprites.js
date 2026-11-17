// Personajes 2D dibujados con código (Canvas 2D): colores planos, sombreado de cómic y contorno de tinta.
// Todos miran hacia la IZQUIERDA (o de frente); la escena los voltea según la dirección de movimiento.

const INK = '#141010';
const LW = 7;

function canvas(w, h) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); g.lineJoin = 'round'; g.lineCap = 'round';
  g.strokeStyle = INK; g.lineWidth = LW;
  return [c, g];
}
function shape(g, fill, path, lw = LW) {
  g.beginPath(); path(g); g.closePath();
  g.fillStyle = fill; g.fill(); g.lineWidth = lw; g.stroke();
}
function ell(g, x, y, rx, ry, fill, rot = 0, lw = LW) {
  shape(g, fill, gg => gg.ellipse(x, y, rx, ry, rot, 0, Math.PI * 2), lw);
}
function poly(g, pts, fill, lw = LW) {
  shape(g, fill, gg => { gg.moveTo(pts[0][0], pts[0][1]); for (const p of pts.slice(1)) gg.lineTo(p[0], p[1]); }, lw);
}
function rrect(g, x, y, w, h, r, fill, lw = LW) {
  shape(g, fill, gg => gg.roundRect(x, y, w, h, r), lw);
}
// sombra de cómic: mancha más oscura recortada dentro de la última forma
function shadeClip(g, pathFn, color, drawFn) {
  g.save(); g.beginPath(); pathFn(g); g.clip(); g.fillStyle = color; drawFn(g); g.restore();
}

// ------------------------------------------------------------------ soldado macedonio (falange)
export function phalangite() {
  const [c, g] = canvas(256, 512);
  // sarisa (lanza larga)
  rrect(g, 166, 4, 10, 470, 4, '#8a5a2b', 5);
  poly(g, [[171, 0], [180, 26], [162, 26]], '#d9d9d9', 4);
  // piernas
  rrect(g, 96, 392, 22, 98, 8, '#e0a878'); rrect(g, 136, 392, 22, 98, 8, '#c98d5d');
  rrect(g, 90, 474, 32, 22, 8, '#5a3420'); rrect(g, 132, 474, 32, 22, 8, '#5a3420');
  // túnica
  poly(g, [[84, 300], [172, 300], [182, 410], [74, 410]], '#c8202a');
  // coraza de lino
  rrect(g, 86, 222, 86, 104, 14, '#f2ead2');
  shadeClip(g, gg => gg.rect(86, 222, 86, 104), 'rgba(120,90,40,0.25)', gg => gg.fillRect(140, 222, 40, 104));
  // brazo con lanza
  rrect(g, 150, 236, 24, 80, 10, '#d99a68');
  // cabeza + casco tracio
  ell(g, 128, 190, 30, 34, '#e0a878');
  shape(g, '#c99a3a', gg => { gg.moveTo(92, 196); gg.quadraticCurveTo(96, 140, 128, 136); gg.quadraticCurveTo(164, 140, 166, 196); gg.lineTo(150, 196); gg.lineTo(148, 176); gg.lineTo(108, 176); gg.lineTo(106, 214); gg.lineTo(92, 214); });
  shape(g, '#e23a2a', gg => { gg.moveTo(108, 140); gg.quadraticCurveTo(128, 92, 168, 112); gg.quadraticCurveTo(150, 120, 146, 140); });
  ell(g, 118, 186, 4, 5, INK, 0, 1);
  // escudo redondo de bronce con la estrella
  ell(g, 104, 318, 74, 74, '#d4a13c');
  ell(g, 104, 318, 58, 58, '#b9822a', 0, 4);
  g.save(); g.translate(104, 318); g.strokeStyle = '#f7d77a'; g.lineWidth = 5;
  for (let k = 0; k < 8; k++) { g.rotate(Math.PI / 4); g.beginPath(); g.moveTo(10, 0); g.lineTo(46, 0); g.stroke(); }
  g.restore(); ell(g, 104, 318, 10, 10, '#f7d77a', 0, 4);
  shadeClip(g, gg => gg.arc(104, 318, 74, 0, 7), 'rgba(60,30,0,0.28)', gg => gg.fillRect(110, 240, 80, 160));
  return c;
}

// ------------------------------------------------------------------ soldado persa (3 colores de túnica)
export function persian(tunic = '#2f5fb3', trim = '#f2c230') {
  const [c, g] = canvas(256, 512);
  rrect(g, 60, 70, 9, 400, 4, '#7a4f25', 5);                       // lanza
  poly(g, [[64, 50], [74, 78], [56, 78]], '#d0d0d0', 4);
  rrect(g, 98, 400, 24, 92, 8, '#6b4b8a'); rrect(g, 136, 400, 24, 92, 8, '#5a3d78');   // pantalones
  rrect(g, 92, 478, 32, 20, 8, '#3a2214'); rrect(g, 132, 478, 32, 20, 8, '#3a2214');
  poly(g, [[86, 236], [170, 236], [190, 420], [66, 420]], tunic);     // túnica larga
  for (let y = 300; y < 420; y += 34) { g.fillStyle = trim; g.fillRect(74 + (420 - y) * 0.0, y, 108, 8); }
  g.strokeStyle = INK; g.lineWidth = LW; g.beginPath(); g.moveTo(86, 236); g.lineTo(66, 420); g.lineTo(190, 420); g.lineTo(170, 236); g.stroke();
  shadeClip(g, gg => { gg.moveTo(86, 236); gg.lineTo(170, 236); gg.lineTo(190, 420); gg.lineTo(66, 420); }, 'rgba(0,0,30,0.25)', gg => gg.fillRect(132, 230, 70, 200));
  rrect(g, 58, 250, 26, 76, 10, '#c88c5c');                        // brazo
  ell(g, 128, 196, 30, 34, '#c88c5c');                              // cabeza
  shape(g, '#2a1a12', gg => { gg.moveTo(100, 206); gg.quadraticCurveTo(128, 262, 156, 206); gg.lineTo(150, 214); gg.quadraticCurveTo(128, 236, 106, 214); });   // barba
  shape(g, '#f3e6c4', gg => { gg.moveTo(96, 190); gg.quadraticCurveTo(100, 130, 132, 124); gg.quadraticCurveTo(150, 128, 162, 150); gg.lineTo(164, 200); gg.lineTo(156, 214); gg.lineTo(158, 176); gg.lineTo(100, 176); gg.lineTo(100, 214); gg.lineTo(92, 206); });  // gorro
  ell(g, 118, 192, 4, 5, INK, 0, 1);
  // escudo de mimbre
  rrect(g, 128, 270, 84, 140, 16, '#b88a4a');
  g.strokeStyle = 'rgba(80,50,20,0.7)'; g.lineWidth = 4;
  for (let y = 286; y < 404; y += 14) { g.beginPath(); g.moveTo(134, y); g.lineTo(206, y); g.stroke(); }
  g.strokeStyle = INK; g.lineWidth = LW; g.beginPath(); g.roundRect(128, 270, 84, 140, 16); g.stroke();
  return c;
}

// ------------------------------------------------------------------ caballo (+ jinete opcional), mirando a la izquierda
function horse(g, ox, oy, s, coat, mane, frame, star = false) {
  g.save(); g.translate(ox, oy); g.scale(s, s);
  const legA = frame ? [[-80, 18], [-50, -14], [70, 22], [100, -10]] : [[-74, -6], [-44, 18], [64, -8], [96, 20]];
  for (const [x, a] of legA) {          // patas (dos tonos)
    g.save(); g.translate(x, 40); g.rotate(a * Math.PI / 180);
    rrect(g, -10, 0, 20, 92, 8, coat); rrect(g, -12, 80, 24, 16, 5, '#2a2a2a', 5);
    g.restore();
  }
  ell(g, 10, 20, 120, 56, coat);                                       // cuerpo
  shadeClip(g, gg => gg.ellipse(10, 20, 120, 56, 0, 0, 7), 'rgba(0,0,0,0.22)', gg => gg.fillRect(-120, 44, 260, 60));
  shape(g, coat, gg => { gg.moveTo(-70, 0); gg.lineTo(-120, -86); gg.lineTo(-96, -104); gg.lineTo(-40, -20); });   // cuello
  shape(g, coat, gg => { gg.moveTo(-122, -92); gg.lineTo(-176, -58); gg.quadraticCurveTo(-186, -40, -166, -36); gg.lineTo(-110, -60); gg.lineTo(-96, -100); });  // cabeza
  poly(g, [[-112, -100], [-104, -126], [-96, -98]], coat, 5);          // oreja
  shape(g, mane, gg => { gg.moveTo(-100, -104); gg.quadraticCurveTo(-60, -70, -40, -16); gg.lineTo(-56, -10); gg.quadraticCurveTo(-82, -56, -112, -92); }, 5);
  shape(g, mane, gg => { gg.moveTo(124, 0); gg.quadraticCurveTo(170, 20, 160, 80); gg.quadraticCurveTo(150, 40, 118, 24); }, 5);    // cola
  ell(g, -140, -70, 5, 5, INK, 0, 1);
  if (star) ell(g, -134, -84, 7, 5, '#ffffff', 0, 3);
  g.restore();
}

export function rider(opts = {}) {
  const { coat = '#7a4a2a', mane = '#2a1a10', cloak = '#7b2d8b', helmet = '#c99a3a', plume = null,
          frame = 0, star = false, gold = false } = opts;
  const [c, g] = canvas(512, 512);
  horse(g, 270, 300, 1.0, coat, mane, frame, star);
  // jinete
  shape(g, cloak, gg => { gg.moveTo(270, 150); gg.quadraticCurveTo(372, 170 + frame * 10, 420, 120 + frame * 14); gg.quadraticCurveTo(380, 230, 300, 250); gg.lineTo(260, 230); });   // capa al viento
  rrect(g, 236, 250, 34, 74, 12, '#e0a878');                              // pierna
  rrect(g, 236, 150, 64, 110, 18, gold ? '#e8c050' : '#f2ead2');         // coraza
  shadeClip(g, gg => gg.rect(236, 150, 64, 110), 'rgba(90,60,0,0.25)', gg => gg.fillRect(274, 150, 40, 120));
  rrect(g, 200, 170, 54, 22, 10, '#e0a878');                              // brazo adelantado
  rrect(g, 120, 172, 120, 9, 4, '#8a5a2b', 4);                            // lanza (xyston)
  poly(g, [[110, 176], [134, 168], [134, 186]], '#d9d9d9', 4);
  ell(g, 262, 120, 28, 32, '#e0a878');                                    // cabeza
  shape(g, helmet, gg => { gg.moveTo(232, 124); gg.quadraticCurveTo(232, 78, 266, 76); gg.quadraticCurveTo(300, 80, 296, 124); gg.lineTo(284, 120); gg.lineTo(282, 104); gg.lineTo(244, 104); gg.lineTo(244, 134); });
  if (plume) shape(g, plume, gg => { gg.moveTo(248, 82); gg.quadraticCurveTo(270, 30, 330, 44 + frame * 6); gg.quadraticCurveTo(296, 56, 290, 84); });
  ell(g, 250, 118, 4, 5, INK, 0, 1);
  return c;
}

// ------------------------------------------------------------------ carro con cuchillas (sin rueda: la rueda gira aparte)
export function chariot(frame = 0) {
  const [c, g] = canvas(640, 400);
  horse(g, 190, 250, 0.72, '#8b5a33', '#2b1a10', frame);
  horse(g, 230, 262, 0.72, '#6e4527', '#2b1a10', 1 - frame);
  rrect(g, 250, 230, 200, 10, 4, '#6b4220', 4);                           // lanza de tiro
  poly(g, [[400, 180], [520, 170], [540, 300], [410, 300]], '#a0522d');   // caja
  for (let x = 420; x < 530; x += 22) { g.strokeStyle = 'rgba(60,30,10,0.6)'; g.lineWidth = 4; g.beginPath(); g.moveTo(x, 186); g.lineTo(x + 4, 296); g.stroke(); }
  g.strokeStyle = INK; g.lineWidth = LW; g.beginPath(); g.moveTo(400, 180); g.lineTo(520, 170); g.lineTo(540, 300); g.lineTo(410, 300); g.closePath(); g.stroke();
  // conductor
  rrect(g, 440, 96, 50, 90, 14, '#2f5fb3'); ell(g, 466, 78, 22, 25, '#c88c5c');
  shape(g, '#f3e6c4', gg => { gg.moveTo(444, 74); gg.quadraticCurveTo(450, 40, 470, 40); gg.quadraticCurveTo(492, 44, 490, 80); });
  rrect(g, 380, 120, 70, 12, 6, '#c88c5c', 5);                            // brazos con riendas
  g.lineWidth = 3; g.beginPath(); g.moveTo(384, 126); g.lineTo(130, 170); g.stroke();
  // guadaña del eje
  poly(g, [[470, 318], [620, 304], [628, 318], [480, 332]], '#e8e8f0', 5);
  return c;
}
export function wheel() {
  const [c, g] = canvas(256, 256);
  ell(g, 128, 128, 112, 112, '#6b4220', 0, 9); ell(g, 128, 128, 90, 90, 'rgba(0,0,0,0)', 0, 6);
  g.save(); g.translate(128, 128);
  for (let k = 0; k < 8; k++) { g.rotate(Math.PI / 4); rrect(g, -5, 0, 10, 90, 4, '#8b5a33', 4); }
  g.restore(); ell(g, 128, 128, 20, 20, '#c0c0c8', 0, 5);
  // cuchillas en la llanta
  g.save(); g.translate(128, 128);
  for (let k = 0; k < 4; k++) { g.rotate(Math.PI / 2); poly(g, [[100, -6], [126, -2], [100, 8]], '#e8e8f0', 4); }
  g.restore();
  return c;
}

// ------------------------------------------------------------------ Darío en su carro real
export function darius(frame = 0) {
  const [c, g] = canvas(640, 520);
  horse(g, 170, 370, 0.78, '#f0ead8', '#b8a070', frame);
  horse(g, 214, 382, 0.78, '#e2dccb', '#b8a070', 1 - frame);
  rrect(g, 230, 350, 200, 10, 4, '#6b4220', 4);
  poly(g, [[380, 290], [560, 276], [580, 420], [392, 420]], '#d4a13c');     // caja dorada
  for (let x = 400; x < 570; x += 30) ell(g, x + 12, 350, 9, 9, '#8b1d6b', 0, 3);
  // Darío: túnica púrpura, barba, corona alta
  poly(g, [[430, 150], [520, 150], [536, 300], [420, 300]], '#6a1f7a');
  shadeClip(g, gg => { gg.moveTo(430, 150); gg.lineTo(520, 150); gg.lineTo(536, 300); gg.lineTo(420, 300); }, 'rgba(0,0,0,0.25)', gg => gg.fillRect(482, 140, 70, 170));
  rrect(g, 456, 150, 38, 150, 4, '#f2ead2', 4);
  ell(g, 474, 118, 32, 36, '#c88c5c');
  shape(g, '#1f140e', gg => { gg.moveTo(444, 124); gg.quadraticCurveTo(472, 200, 504, 124); gg.lineTo(496, 134); gg.quadraticCurveTo(474, 152, 452, 134); });
  poly(g, [[442, 100], [446, 30], [504, 30], [508, 100]], '#e8c050');        // kídaris
  for (let x = 452; x < 500; x += 14) ell(g, x + 4, 62, 4, 4, '#b02a2a', 0, 2);
  ell(g, 462, 114, 4, 5, INK, 0, 1);
  rrect(g, 380, 190, 70, 14, 6, '#c88c5c', 5);                                // brazo extendido
  rrect(g, 360, 120, 10, 120, 3, '#d4a13c', 4);                              // cetro
  return c;
}

// ------------------------------------------------------------------ elefante
export function elephant() {
  const [c, g] = canvas(512, 420);
  for (const x of [150, 210, 330, 380]) rrect(g, x, 250, 52, 150, 16, '#8a8a92');
  ell(g, 280, 210, 170, 110, '#9a9aa4');
  shadeClip(g, gg => gg.ellipse(280, 210, 170, 110, 0, 0, 7), 'rgba(0,0,30,0.2)', gg => gg.fillRect(100, 250, 380, 100));
  ell(g, 120, 170, 80, 74, '#9a9aa4');                                       // cabeza
  shape(g, '#9a9aa4', gg => { gg.moveTo(64, 190); gg.quadraticCurveTo(30, 280, 60, 380); gg.lineTo(88, 380); gg.quadraticCurveTo(70, 290, 104, 214); });   // trompa
  poly(g, [[86, 220], [30, 256], [92, 240]], '#f4f0e0', 5);                  // colmillo
  ell(g, 168, 170, 56, 74, '#8c8c96');                                       // oreja
  ell(g, 100, 150, 6, 7, INK, 0, 1);
  rrect(g, 230, 70, 110, 60, 8, '#b02a2a');                                   // manta
  rrect(g, 250, 20, 30, 60, 10, '#2f5fb3'); ell(g, 265, 14, 16, 18, '#c88c5c');   // jinete
  return c;
}

// ------------------------------------------------------------------ texturas de efectos
export function softDot(rgb = '255,255,255') {
  const [c, g] = canvas(128, 128);
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, `rgba(${rgb},1)`); gr.addColorStop(0.4, `rgba(${rgb},0.5)`); gr.addColorStop(1, `rgba(${rgb},0)`);
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128); return c;
}
export function smokePuff(seed = 1) {
  const [c, g] = canvas(256, 256);
  let s = seed;
  const r = () => (s = (s * 16807) % 2147483647) / 2147483647;
  for (let k = 0; k < 14; k++) {
    const x = 70 + r() * 116, y = 70 + r() * 116, rad = 30 + r() * 50;
    const gr = g.createRadialGradient(x, y, 0, x, y, rad);
    gr.addColorStop(0, 'rgba(255,255,255,0.55)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  }
  return c;
}
export function flame() {
  const [c, g] = canvas(64, 128);
  const gr = g.createRadialGradient(32, 96, 2, 32, 80, 60);
  gr.addColorStop(0, 'rgba(255,250,200,1)'); gr.addColorStop(0.3, 'rgba(255,170,40,0.9)'); gr.addColorStop(1, 'rgba(255,60,0,0)');
  g.fillStyle = gr; g.beginPath(); g.moveTo(32, 4); g.quadraticCurveTo(64, 80, 32, 124); g.quadraticCurveTo(0, 80, 32, 4); g.fill();
  return c;
}
export function cloud(seed = 3) {
  const [c, g] = canvas(512, 256);
  let s = seed; const r = () => (s = (s * 16807) % 2147483647) / 2147483647;
  const blobs = []; for (let k = 0; k < 7; k++) blobs.push([90 + k * 55 + r() * 20, 150 - Math.sin(k / 6 * Math.PI) * 50 - r() * 20, 50 + r() * 40]);
  g.fillStyle = INK; for (const [x, y, rad] of blobs) { g.beginPath(); g.arc(x, y, rad + 6, 0, 7); g.fill(); }   // contorno solo por fuera
  g.fillStyle = '#fff6e8'; for (const [x, y, rad] of blobs) { g.beginPath(); g.arc(x, y, rad, 0, 7); g.fill(); }
  g.save(); g.beginPath(); for (const [x, y, rad] of blobs) { g.moveTo(x + rad, y); g.arc(x, y, rad, 0, 7); } g.clip();
  g.fillStyle = 'rgba(120,140,190,0.35)'; for (const [x, y, rad] of blobs) { g.beginPath(); g.arc(x + rad * 0.2, y + rad * 0.45, rad * 0.8, 0, 7); g.fill(); }
  g.restore();
  return c;
}
