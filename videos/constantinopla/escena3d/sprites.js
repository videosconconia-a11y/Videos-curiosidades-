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

// ================================================================== Troya
// ------------------------------------------------------------------ caballo de madera sobre plataforma con ruedas
export function woodenHorse(open = false) {
  const [c, g] = canvas(768, 768);
  const WOOD = '#a8743a', DARK = '#7a4f22', LIGHT = '#c99556';
  // plataforma y ruedas
  rrect(g, 150, 640, 470, 46, 8, DARK);
  for (const x of [200, 330, 450, 570]) { ell(g, x, 700, 40, 40, '#6b4220', 0, 8); ell(g, x, 700, 10, 10, '#c0c0c8', 0, 4); }
  // patas
  for (const [x, a] of [[240, 6], [300, -4], [470, 5], [530, -6]]) {
    g.save(); g.translate(x, 470); g.rotate(a * Math.PI / 180); rrect(g, -24, 0, 48, 180, 10, WOOD); g.restore();
  }
  // cuerpo de tablones
  const body = gg => gg.roundRect(170, 320, 440, 190, 70);
  shape(g, WOOD, body);
  g.save(); g.beginPath(); body(g); g.clip();
  g.strokeStyle = DARK; g.lineWidth = 5;
  for (let y = 340; y < 510; y += 26) { g.beginPath(); g.moveTo(160, y); g.lineTo(620, y + 4); g.stroke(); }
  for (let k = 0; k < 18; k++) { g.fillStyle = '#5a3818'; g.beginPath(); g.arc(190 + k * 24, 330 + (k % 7) * 26, 3, 0, 7); g.fill(); }
  g.fillStyle = 'rgba(40,20,0,0.25)'; g.fillRect(160, 450, 470, 80);
  g.restore(); g.strokeStyle = INK; g.lineWidth = LW; g.beginPath(); body(g); g.stroke();
  // trampilla en el vientre
  if (open) {
    rrect(g, 340, 480, 110, 40, 6, '#140d08');
    poly(g, [[340, 520], [450, 520], [470, 600], [360, 600]], LIGHT, 5);           // portezuela abatida
    g.strokeStyle = '#d8c090'; g.lineWidth = 5; g.beginPath(); g.moveTo(395, 500); g.lineTo(400, 640); g.stroke();   // cuerda
  } else {
    g.strokeStyle = DARK; g.lineWidth = 4; g.strokeRect(345, 470, 100, 34);
  }
  // cuello y cabeza
  shape(g, WOOD, gg => { gg.moveTo(230, 360); gg.lineTo(150, 150); gg.lineTo(220, 120); gg.lineTo(300, 340); });
  shape(g, WOOD, gg => { gg.moveTo(150, 160); gg.lineTo(40, 210); gg.quadraticCurveTo(20, 240, 50, 256); gg.lineTo(150, 236); gg.lineTo(222, 128); });
  poly(g, [[170, 130], [184, 74], [204, 126]], WOOD, 6);                            // oreja
  for (let k = 0; k < 7; k++) poly(g, [[214 + k * 12, 120 + k * 32], [250 + k * 12, 110 + k * 32], [232 + k * 12, 146 + k * 32]], DARK, 4);   // crin
  ell(g, 104, 196, 12, 12, '#1a0f08', 0, 4); ell(g, 100, 192, 4, 4, '#fff', 0, 1);
  shape(g, DARK, gg => { gg.moveTo(610, 360); gg.quadraticCurveTo(690, 380, 680, 520); gg.quadraticCurveTo(650, 430, 604, 400); }, 6);   // cola
  return c;
}

// ------------------------------------------------------------------ Laocoonte: sacerdote con lanza alzada
export function priest(frame = 0) {
  const [c, g] = canvas(256, 512);
  poly(g, [[86, 220], [170, 220], [196, 496], [60, 496]], '#f4f0e6');
  shadeClip(g, gg => { gg.moveTo(86, 220); gg.lineTo(170, 220); gg.lineTo(196, 496); gg.lineTo(60, 496); }, 'rgba(60,60,120,0.2)', gg => gg.fillRect(130, 210, 80, 300));
  rrect(g, 60, 300, 140, 16, 6, '#b8862e', 5);                                  // fajín dorado
  g.save(); g.translate(150, 236); g.rotate(-1.2 - frame * 0.25);                 // brazo alzado con lanza
  rrect(g, -12, -8, 24, 90, 10, '#d99a68'); rrect(g, -4, -150, 8, 240, 3, '#7a4f25', 4);
  poly(g, [[0, -170], [10, -146], [-10, -146]], '#d0d0d0', 4); g.restore();
  rrect(g, 70, 236, 24, 80, 10, '#d99a68');
  ell(g, 128, 186, 30, 34, '#d99a68');
  shape(g, '#e8e8e8', gg => { gg.moveTo(98, 196); gg.quadraticCurveTo(128, 270, 158, 196); gg.lineTo(150, 206); gg.quadraticCurveTo(128, 226, 106, 206); });   // barba canosa
  shape(g, '#5a8a3a', gg => { gg.moveTo(96, 170); gg.quadraticCurveTo(128, 140, 160, 170); gg.lineTo(156, 160); gg.quadraticCurveTo(128, 132, 100, 160); }, 4);   // laurel
  ell(g, 116, 184, 4, 5, INK, 0, 1);
  shape(g, INK, gg => { gg.moveTo(108, 210); gg.quadraticCurveTo(118, 218, 128, 212); }, 3);                       // boca gritando
  return c;
}

// ------------------------------------------------------------------ Sinón: prisionero griego con las manos atadas
export function captive() {
  const [c, g] = canvas(256, 512);
  rrect(g, 98, 400, 22, 92, 8, '#e0a878'); rrect(g, 136, 400, 22, 92, 8, '#c98d5d');
  poly(g, [[84, 240], [172, 240], [180, 410], [76, 410]], '#9a8a70');
  for (const [x, y] of [[90, 380], [150, 300], [120, 350]]) poly(g, [[x, y], [x + 18, y + 8], [x + 4, y + 20]], '#6a5a44', 3);   // harapos
  rrect(g, 100, 300, 56, 30, 8, '#e0a878');                                       // brazos atados delante
  g.strokeStyle = '#c8a860'; g.lineWidth = 6; for (let k = 0; k < 3; k++) { g.beginPath(); g.moveTo(104 + k * 18, 298); g.lineTo(112 + k * 18, 332); g.stroke(); }
  ell(g, 128, 200, 30, 34, '#e0a878');
  shape(g, '#3a2414', gg => { gg.moveTo(96, 196); gg.quadraticCurveTo(100, 156, 128, 158); gg.quadraticCurveTo(160, 156, 162, 196); gg.lineTo(150, 180); gg.lineTo(106, 180); });
  ell(g, 116, 198, 4, 5, INK, 0, 1);
  shape(g, INK, gg => { gg.moveTo(110, 220); gg.quadraticCurveTo(122, 214, 132, 222); }, 3);                      // sonrisa torcida
  return c;
}

// ------------------------------------------------------------------ vela de barco (franjas)
export function sail() {
  const [c, g] = canvas(256, 256);
  g.fillStyle = '#f2e8d0'; g.fillRect(8, 8, 240, 240);
  g.fillStyle = '#b02a2a'; for (let x = 8; x < 248; x += 60) g.fillRect(x, 8, 26, 240);
  g.strokeStyle = INK; g.lineWidth = 10; g.strokeRect(8, 8, 240, 240);
  return c;
}

// ================================================================== Constantinopla 1453
export function janissary(frame = 0) {
  const [c, g] = canvas(256, 512);
  const legs = frame ? [[-14, 14], [14, -14]] : [[-6, 6], [6, -6]];
  for (const [dx, a] of legs) { g.save(); g.translate(128 + dx, 392); g.rotate(a * Math.PI / 180); rrect(g, -12, 0, 24, 96, 9, '#b8862e'); rrect(g, -15, 82, 30, 18, 6, '#3a2214', 5); g.restore(); }
  poly(g, [[84, 230], [172, 230], [190, 420], [66, 420]], '#2a4a9a');                      // kaftán azul
  shadeClip(g, gg => { gg.moveTo(84, 230); gg.lineTo(172, 230); gg.lineTo(190, 420); gg.lineTo(66, 420); }, 'rgba(0,0,30,0.25)', gg => gg.fillRect(132, 220, 70, 210));
  rrect(g, 76, 300, 104, 14, 6, '#d8202a', 4);                                               // fajín rojo
  g.save(); g.translate(176, 250); g.rotate(-0.35); rrect(g, -10, 0, 20, 80, 9, '#c88c5c'); rrect(g, -4, -150, 8, 230, 3, '#7a4f25', 4); poly(g, [[0, -175], [12, -150], [-12, -150]], '#d0d0d0', 4); g.restore();
  rrect(g, 62, 250, 22, 80, 9, '#c88c5c');
  ell(g, 128, 196, 28, 32, '#c88c5c');
  shape(g, '#1a1410', gg => { gg.moveTo(104, 212); gg.quadraticCurveTo(128, 236, 152, 212); gg.lineTo(146, 220); gg.quadraticCurveTo(128, 230, 110, 220); }, 3);   // bigote
  shape(g, '#f6f2e8', gg => { gg.moveTo(98, 176); gg.lineTo(102, 60); gg.quadraticCurveTo(128, 40, 150, 60); gg.lineTo(158, 176); });   // börk blanco alto
  shape(g, '#f6f2e8', gg => { gg.moveTo(150, 70); gg.quadraticCurveTo(200, 110, 190, 200); gg.quadraticCurveTo(176, 140, 146, 110); });  // caída del börk
  rrect(g, 94, 166, 68, 16, 6, '#e8c050', 4);
  ell(g, 116, 196, 4, 5, INK, 0, 1);
  return c;
}
export function byzantine(cloak = '#8a1d4a') {
  const [c, g] = canvas(256, 512);
  rrect(g, 100, 400, 22, 92, 8, '#6a5a4a'); rrect(g, 136, 400, 22, 92, 8, '#5a4a3a');
  shape(g, cloak, gg => { gg.moveTo(84, 230); gg.quadraticCurveTo(40, 340, 60, 430); gg.lineTo(196, 430); gg.quadraticCurveTo(214, 340, 172, 230); });   // capa
  rrect(g, 86, 226, 84, 140, 16, '#9aa0aa');                                                 // lorica de láminas
  g.save(); g.beginPath(); g.roundRect(86, 226, 84, 140, 16); g.clip(); g.strokeStyle = 'rgba(40,40,50,0.55)'; g.lineWidth = 3;
  for (let y = 236; y < 366; y += 12) for (let x = 86 + (y / 12 % 2) * 6; x < 172; x += 12) { g.beginPath(); g.arc(x, y, 6, 0, Math.PI); g.stroke(); } g.restore();
  rrect(g, 166, 50, 9, 420, 4, '#7a4f25', 5); poly(g, [[170, 30], [182, 58], [158, 58]], '#d0d0d0', 4);
  ell(g, 128, 190, 28, 32, '#d99a68');
  shape(g, '#a8acb4', gg => { gg.moveTo(96, 196); gg.quadraticCurveTo(96, 140, 128, 138); gg.quadraticCurveTo(160, 140, 160, 196); gg.lineTo(150, 176); gg.lineTo(106, 176); });   // casco
  poly(g, [[124, 140], [132, 140], [130, 120]], '#d8202a', 3);
  ell(g, 116, 192, 4, 5, INK, 0, 1);
  ell(g, 96, 330, 58, 58, '#d8202a');                                                         // escudo redondo
  g.strokeStyle = '#f0c040'; g.lineWidth = 9; g.beginPath(); g.moveTo(96, 290); g.lineTo(96, 370); g.moveTo(58, 330); g.lineTo(134, 330); g.stroke();
  g.strokeStyle = INK; g.lineWidth = LW; g.beginPath(); g.arc(96, 330, 58, 0, 7); g.stroke();
  return c;
}
export function genoese() {
  const [c, g] = canvas(256, 512);
  rrect(g, 100, 400, 22, 92, 8, '#3a3a4a'); rrect(g, 136, 400, 22, 92, 8, '#2a2a3a');
  rrect(g, 84, 228, 90, 190, 14, '#f4f0e6');                                                 // sobreveste blanca
  g.fillStyle = '#d8202a'; g.fillRect(118, 236, 22, 172); g.fillRect(90, 300, 78, 22);      // cruz roja de Génova
  g.strokeStyle = INK; g.lineWidth = LW; g.beginPath(); g.roundRect(84, 228, 90, 190, 14); g.stroke();
  ell(g, 128, 192, 28, 32, '#e0a878');
  shape(g, '#8a8e98', gg => { gg.moveTo(92, 186); gg.quadraticCurveTo(100, 140, 128, 140); gg.quadraticCurveTo(156, 140, 164, 186); gg.lineTo(176, 190); gg.lineTo(80, 190); });   // capelina
  ell(g, 118, 196, 4, 5, INK, 0, 1);
  rrect(g, 40, 262, 140, 12, 5, '#6b4220', 4);                                                // ballesta
  g.strokeStyle = '#3a2a1a'; g.lineWidth = 6; g.beginPath(); g.arc(46, 268, 34, -1.2, 1.2); g.stroke();
  rrect(g, 150, 250, 24, 30, 8, '#e0a878', 4);
  return c;
}
export function emperor() {
  const [c, g] = canvas(256, 512);
  poly(g, [[86, 220], [170, 220], [196, 496], [60, 496]], '#6a1f7a');
  shadeClip(g, gg => { gg.moveTo(86, 220); gg.lineTo(170, 220); gg.lineTo(196, 496); gg.lineTo(60, 496); }, 'rgba(0,0,0,0.25)', gg => gg.fillRect(130, 210, 80, 300));
  rrect(g, 108, 220, 40, 270, 6, '#e8c050', 4);                                                // loros dorado
  for (let y = 240; y < 480; y += 30) ell(g, 128, y, 8, 8, '#b02a2a', 0, 3);
  rrect(g, 64, 236, 22, 90, 10, '#d99a68'); rrect(g, 172, 236, 22, 90, 10, '#d99a68');
  ell(g, 128, 180, 30, 34, '#d99a68');
  shape(g, '#3a2414', gg => { gg.moveTo(98, 190); gg.quadraticCurveTo(128, 260, 158, 190); gg.lineTo(150, 200); gg.quadraticCurveTo(128, 222, 106, 200); });
  shape(g, '#e8c050', gg => { gg.moveTo(94, 160); gg.lineTo(96, 116); gg.quadraticCurveTo(128, 96, 160, 116); gg.lineTo(162, 160); });   // corona
  for (let x = 104; x < 160; x += 14) ell(g, x, 136, 5, 5, x % 28 ? '#2a6ab8' : '#b02a2a', 0, 2);
  g.strokeStyle = '#f4f0e0'; g.lineWidth = 4; for (const x of [98, 158]) { g.beginPath(); g.moveTo(x, 160); g.lineTo(x, 200); g.stroke(); ell(g, x, 204, 4, 4, '#f4f0e0', 0, 2); }   // pendilia
  ell(g, 116, 180, 4, 5, INK, 0, 1);
  return c;
}
export function engineer() {
  const [c, g] = canvas(256, 512);
  rrect(g, 100, 400, 24, 92, 8, '#5a4030'); rrect(g, 136, 400, 24, 92, 8, '#4a3020');
  rrect(g, 80, 226, 96, 186, 16, '#8a6a4a');
  rrect(g, 96, 260, 64, 160, 10, '#3a2a1a');                                                    // mandil de cuero
  rrect(g, 60, 240, 24, 90, 10, '#d99a68'); rrect(g, 172, 240, 24, 90, 10, '#d99a68');
  rrect(g, 176, 310, 46, 16, 4, '#5a5a62', 4); rrect(g, 210, 296, 20, 44, 4, '#5a5a62', 4);    // martillo
  ell(g, 128, 186, 30, 34, '#d99a68');
  shape(g, '#c8661a', gg => { gg.moveTo(96, 190); gg.quadraticCurveTo(128, 290, 160, 190); gg.lineTo(152, 202); gg.quadraticCurveTo(128, 226, 104, 202); });   // barba pelirroja
  shape(g, '#3a2a20', gg => { gg.moveTo(94, 176); gg.quadraticCurveTo(100, 140, 128, 140); gg.quadraticCurveTo(160, 140, 164, 176); });
  ell(g, 116, 184, 4, 5, INK, 0, 1);
  return c;
}
export function scholar() {
  const [c, g] = canvas(256, 512);
  poly(g, [[88, 220], [168, 220], [190, 496], [66, 496]], '#2a4a7a');
  rrect(g, 70, 280, 116, 70, 8, '#8a3a1a');                                                      // pila de libros
  for (let k = 0; k < 3; k++) { g.strokeStyle = '#f4e8c8'; g.lineWidth = 5; g.beginPath(); g.moveTo(76, 296 + k * 20); g.lineTo(180, 296 + k * 20); g.stroke(); }
  g.strokeStyle = INK; g.lineWidth = LW; g.strokeRect(70, 280, 116, 70);
  ell(g, 128, 180, 30, 34, '#d99a68');
  shape(g, '#d8d8d8', gg => { gg.moveTo(98, 190); gg.quadraticCurveTo(128, 280, 158, 190); gg.lineTo(150, 200); gg.quadraticCurveTo(128, 222, 106, 200); });
  shape(g, '#3a3a4a', gg => { gg.moveTo(94, 170); gg.quadraticCurveTo(128, 110, 162, 170); });
  ell(g, 116, 180, 4, 5, INK, 0, 1);
  return c;
}
export function ox(frame = 0) {
  const [c, g] = canvas(512, 320);
  const legs = frame ? [[150, 8], [190, -8], [330, 6], [370, -6]] : [[150, -6], [190, 6], [330, -8], [370, 8]];
  for (const [x, a] of legs) { g.save(); g.translate(x, 200); g.rotate(a * Math.PI / 180); rrect(g, -14, 0, 28, 100, 9, '#6a4a2a'); g.restore(); }
  ell(g, 270, 170, 150, 70, '#8a6238');
  shadeClip(g, gg => gg.ellipse(270, 170, 150, 70, 0, 0, 7), 'rgba(0,0,0,0.2)', gg => gg.fillRect(110, 200, 330, 60));
  ell(g, 110, 150, 52, 44, '#8a6238');
  shape(g, '#f4f0e0', gg => { gg.moveTo(98, 112); gg.quadraticCurveTo(70, 70, 40, 84); gg.quadraticCurveTo(66, 92, 86, 124); }, 5);   // cuerno
  rrect(g, 100, 100, 160, 20, 8, '#6b4220', 4);                                                    // yugo
  ell(g, 86, 150, 5, 6, INK, 0, 1);
  return c;
}
export function flagTex(kind = 'otomana') {
  const [c, g] = canvas(256, 160);
  if (kind === 'otomana') {
    g.fillStyle = '#c8202a'; g.fillRect(0, 0, 256, 160);
    g.fillStyle = '#f4f0e6'; g.beginPath(); g.arc(110, 80, 46, 0, 7); g.fill(); g.fillStyle = '#c8202a'; g.beginPath(); g.arc(126, 80, 38, 0, 7); g.fill();
  } else {
    g.fillStyle = '#e8c050'; g.fillRect(0, 0, 256, 160);
    g.fillStyle = '#8a1d4a'; g.fillRect(112, 0, 32, 160); g.fillRect(0, 64, 256, 32);
  }
  return c;
}
