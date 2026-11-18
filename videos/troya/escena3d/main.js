// Troya: personajes 2D (recortes dibujados con código) en un mundo 3D real, con sombras.
// Misma técnica que Gaugamela: cámara continua sin cortes, luz que sigue a la historia, contorno de tinta.
import * as THREE from './node_modules/three/build/three.module.js';
import * as SP from './sprites.js';

const W = 1080, H = 1920;
const TL = await (await fetch('timeline.json')).json();
const SC = Object.fromEntries(TL.scenes.map(s => [s.name, s]));
const at = (name, u) => SC[name].a + u * (SC[name].b - SC[name].a);
const prog = (t, name) => Math.min(1, Math.max(0, (t - SC[name].a) / (SC[name].b - SC[name].a)));
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const ease = u => u * u * (3 - 2 * u);
const easeIn = u => u * u;
const clamp01 = u => Math.min(1, Math.max(0, u));
const lerp = (a, b, u) => a + (b - a) * u;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;

// ------------------------------------------------------------------ renderer
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xd9a46a, 300, 3200);
const camera = new THREE.PerspectiveCamera(50, W / H, 0.5, 7000);

// ------------------------------------------------------------------ luz que sigue a la historia
const hemi = new THREE.HemisphereLight(0xffd9a0, 0x6a4a3a, 0.9); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffc27a, 2.6); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.6;
scene.add(sun, sun.target);
const MOODS = {
  golden:  { sun: 0xffb060, si: 2.8, sky: 0x3a5aa8, hor: 0xff9a5a, gnd: 0x6a4436, hs: 0xffc890, fog: 0xd98a5c, exp: 1.05, dir: [0.6, 0.28, 0.75] },
  day:     { sun: 0xffe0b0, si: 3.0, sky: 0x3f86d8, hor: 0xbfdcf0, gnd: 0x7a5a40, hs: 0xd8e4ff, fog: 0xc8d4e0, exp: 1.0,  dir: [-0.5, 0.6, 0.62] },
  morning: { sun: 0xffe8d0, si: 2.4, sky: 0x6a9ad8, hor: 0xf0d8c8, gnd: 0x6a5a50, hs: 0xd8e0f0, fog: 0xe0d8d8, exp: 1.05, dir: [0.7, 0.3, 0.6] },
  omen:    { sun: 0xd8c8b0, si: 1.8, sky: 0x4a5068, hor: 0x9a9098, gnd: 0x4a3c38, hs: 0xa8a8b8, fog: 0x8a8890, exp: 1.0,  dir: [0.4, 0.5, 0.75] },
  dusk:    { sun: 0xd0c4ff, si: 2.1, sky: 0x1a2a66, hor: 0x7a7ac0, gnd: 0x3a2c38, hs: 0x6a7ad0, fog: 0x4a5490, exp: 0.98, dir: [0.5, 0.6, 0.62] },
  night:   { sun: 0x8fb0ff, si: 1.3, sky: 0x050a1e, hor: 0x1e2c5a, gnd: 0x0a0c18, hs: 0x4a5fa8, fog: 0x141c3a, exp: 1.0,  dir: [0.35, 0.5, -0.8] },
  fire:    { sun: 0xffb070, si: 2.6, sky: 0x2e1a38, hor: 0xff7a38, gnd: 0x4a3030, hs: 0xd8a080, fog: 0x8a4a3a, exp: 1.05, dir: [-0.5, 0.35, 0.78] },
  today:   { sun: 0xfff2e0, si: 3.0, sky: 0x2f7ae0, hor: 0xd8eaf8, gnd: 0x5a6a40, hs: 0xe0ecff, fog: 0xd0dcea, exp: 1.0,  dir: [-0.4, 0.7, 0.6] },
  violet:  { sun: 0xff9ab0, si: 2.0, sky: 0x1e1a50, hor: 0xc86a8a, gnd: 0x3a2838, hs: 0x9a80c8, fog: 0x6a4a78, exp: 1.0,  dir: [0.6, 0.18, 0.78] },
};
const MOOD_KEYS = [
  [0, 'golden'], [at('gancho', 1) - 0.3, 'golden'], [at('asedio', 0.35), 'day'], [at('murallas', 1) - 0.2, 'day'],
  [at('retirada', 0.25), 'morning'], [at('caballo', 1), 'morning'], [at('aviso', 0.3), 'omen'], [at('aviso', 1) - 0.2, 'omen'],
  [at('brecha', 0.15), 'dusk'], [at('brecha', 1) - 0.3, 'dusk'], [at('noche', 0.2), 'night'], [at('noche', 1) - 0.4, 'night'],
  [at('incendio', 0.25), 'fire'], [at('incendio', 1) - 0.2, 'fire'], [at('ruinas', 0.12), 'today'], [at('ruinas', 1) - 0.3, 'today'],
  [at('final', 0.2), 'violet'], [TL.total + 1, 'violet'],
];
const tc1 = new THREE.Color(), tc2 = new THREE.Color();
const mixCol = (a, b, u) => tc1.set(a).lerp(tc2.set(b), u).clone();
function mood(t) {
  let i = 0; while (i < MOOD_KEYS.length - 2 && t > MOOD_KEYS[i + 1][0]) i++;
  const [t0, m0] = MOOD_KEYS[i], [t1, m1] = MOOD_KEYS[i + 1];
  const u = ease(clamp01((t - t0) / (t1 - t0))); const A = MOODS[m0], B = MOODS[m1];
  return { sun: mixCol(A.sun, B.sun, u), si: lerp(A.si, B.si, u), sky: mixCol(A.sky, B.sky, u), hor: mixCol(A.hor, B.hor, u),
    gnd: mixCol(A.gnd, B.gnd, u), hs: mixCol(A.hs, B.hs, u), fog: mixCol(A.fog, B.fog, u), exp: lerp(A.exp, B.exp, u),
    dir: V(...A.dir).lerp(V(...B.dir), u).normalize() };
}

// ------------------------------------------------------------------ cielo
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { top: { value: new THREE.Color() }, hor: { value: new THREE.Color() }, stars: { value: 0 } },
  vertexShader: 'varying vec3 vp; void main(){ vp = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
  fragmentShader: `uniform vec3 top; uniform vec3 hor; uniform float stars; varying vec3 vp;
    float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
    void main(){ float h = clamp(vp.y*2.2,0.,1.); vec3 c = mix(hor, top, pow(h,0.7));
      vec2 q = floor(vp.xz/(vp.y+0.3)*260.); float s = step(0.997, h21(q)) * smoothstep(0.05,0.4,vp.y);
      gl_FragColor = vec4(c + s*stars, 1.); }`,
});
const sky = new THREE.Mesh(new THREE.SphereGeometry(6000, 32, 16), skyMat); scene.add(sky);

// ------------------------------------------------------------------ materiales de cómic
const grad3 = new THREE.DataTexture(new Uint8Array([90, 170, 255]), 3, 1, THREE.RedFormat);
grad3.minFilter = grad3.magFilter = THREE.NearestFilter; grad3.needsUpdate = true;
const toon = (color, extra = {}) => new THREE.MeshToonMaterial({ color, gradientMap: grad3, ...extra });
const inkMat = new THREE.MeshBasicMaterial({ color: 0x140f0f, side: THREE.BackSide });
function inked(geom, mat, thick = 1.04) {
  const g = new THREE.Group();
  const m = new THREE.Mesh(geom, mat); m.castShadow = true; m.receiveShadow = true;
  const o = new THREE.Mesh(geom, inkMat); o.scale.setScalar(thick);
  g.add(m, o); g.userData.mat = mat; return g;
}
function tex(canvas) { const t = new THREE.CanvasTexture(canvas); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }

// ------------------------------------------------------------------ terreno: colina de Troya, llanura, playa y mar
const TROY = V(0, 0, -380), HILL_R = 175, HILL_H = 24, SEA_Y = -1.6;
function noise2(x, z) { return Math.sin(x * 0.013 + Math.sin(z * 0.011) * 2) * 0.5 + Math.sin(z * 0.017 + x * 0.004) * 0.35 + Math.sin((x + z) * 0.041) * 0.15; }
function groundY(x, z) {
  const d = Math.hypot(x - TROY.x, z - TROY.z);
  const hillS = HILL_H * (d < 120 ? 1 : ease(clamp01(1 - (d - 120) / (HILL_R - 120))));
  let y = hillS + noise2(x, z) * 1.6 * (d < 125 ? 0.2 : 1);
  y -= Math.max(0, z - 30) * 0.045;                           // la playa baja hacia el mar
  const far = Math.hypot(x, z + 200);
  y += Math.max(0, far - 900) * 0.07 * (1 + noise2(z, x)) * (z < 60 ? 1 : 0);
  return y;
}
const GROUND = 4400, GSEG = 360;
const gGeo = new THREE.PlaneGeometry(GROUND, GROUND, GSEG, GSEG); gGeo.rotateX(-Math.PI / 2);
const gPos = gGeo.attributes.position, gCol = new Float32Array(gPos.count * 3);
const groundTint = { grass: 0 };
for (let i = 0; i < gPos.count; i++) {
  const x = gPos.getX(i), z = gPos.getZ(i) - 200; gPos.setZ(i, z);
  const y = groundY(x, z); gPos.setY(i, y);
  const n = noise2(x * 3.1, z * 2.7) * 0.5 + 0.5;
  let c = [0.74 + 0.1 * n, 0.6 + 0.08 * n, 0.4 + 0.05 * n];               // tierra de la llanura
  if (z > 20) c = c.map((v, k) => lerp(v, [0.95, 0.84, 0.6][k], clamp01((z - 20) / 30)));   // arena
  const d = Math.hypot(x - TROY.x, z - TROY.z);
  if (d < 125) c = c.map((v, k) => lerp(v, [0.7, 0.62, 0.5][k], 0.6));    // suelo pisado de la ciudad
  if (Math.abs(x - 0.25 * (z + 260)) < 7 && z > -270 && z < 40) c = c.map(v => v * 0.86);   // camino a la puerta
  gCol.set(c, i * 3);
}
gGeo.setAttribute('color', new THREE.BufferAttribute(gCol, 3)); gGeo.computeVertexNormals();
const detail = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  g.fillStyle = '#d8d0c4'; g.fillRect(0, 0, 256, 256);
  for (let k = 0; k < 2200; k++) { const v = 150 + rnd() * 105 | 0; g.fillStyle = `rgb(${v},${v - 8},${v - 20})`; g.fillRect(rnd() * 256, rnd() * 256, 1 + rnd() * 3, 1 + rnd() * 3); }
  for (let k = 0; k < 30; k++) { g.strokeStyle = 'rgba(70,40,20,0.3)'; g.lineWidth = 1.5; g.beginPath(); let x = rnd() * 256, y = rnd() * 256; g.moveTo(x, y); for (let j = 0; j < 4; j++) { x += rnd() * 30 - 15; y += rnd() * 30 - 15; g.lineTo(x, y); } g.stroke(); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(GROUND / 9, GROUND / 9);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
})();
const groundMat = new THREE.MeshLambertMaterial({ vertexColors: true, map: detail });
const ground = new THREE.Mesh(gGeo, groundMat); ground.receiveShadow = true; scene.add(ground);
// mar con olas de cómic
const seaGeo = new THREE.PlaneGeometry(9000, 6000, 160, 100); seaGeo.rotateX(-Math.PI / 2); seaGeo.translate(0, SEA_Y, 3000 + 60);
const seaBase = seaGeo.attributes.position.array.slice();
const sea = new THREE.Mesh(seaGeo, toon(0x2a7ab8, { flatShading: true })); sea.receiveShadow = true; scene.add(sea);
function waveSea(t) {
  const a = seaGeo.attributes.position;
  for (let i = 0; i < a.count; i++) { const x = seaBase[i * 3], z = seaBase[i * 3 + 2]; a.setY(i, SEA_Y + Math.sin(x * 0.02 + t * 1.3) * 0.5 + Math.sin(z * 0.03 - t * 1.1) * 0.5); }
  a.needsUpdate = true; seaGeo.computeVertexNormals();
}
// espuma en la orilla
const foam = new THREE.Mesh(new THREE.PlaneGeometry(9000, 6), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 }));
foam.rotation.x = -Math.PI / 2; scene.add(foam);
const shoreZ = 30 + (-SEA_Y) / 0.045;
// isla de Ténedos (donde se esconden las naves)
const ISLE = V(700, 0, 1300);
const isle = inked(new THREE.ConeGeometry(320, 160, 9, 1).translate(0, 60, 0), toon(0x8a9a5a, { flatShading: true }), 1.01);
isle.position.copy(ISLE); isle.scale.set(1.3, 1, 0.8); scene.add(isle);
// montañas lejanas (tierra adentro)
for (let k = 0; k < 26; k++) {
  const a = Math.PI + (k / 25 - 0.5) * 2.6 + Math.PI / 2 * 0, r = 2300 + rnd() * 600;
  const h = 160 + rnd() * 260, w = 420 + rnd() * 500, seg = 6 + (rnd() * 3 | 0), rot = rnd() * 6;
  const geo = new THREE.ConeGeometry(w, h, seg, 1); geo.translate(0, h / 2, 0);
  const m = inked(geo, toon(0x7c7aa8, { flatShading: true }), 1.01);
  m.scale.set(1 + rnd() * 0.6, 1, 0.7 + rnd() * 0.4);
  m.position.set(Math.sin(a) * r, -30, -Math.abs(Math.cos(a)) * r - 300); m.rotation.y = rot; scene.add(m);
}

// ------------------------------------------------------------------ la ciudad: murallas, torres, puerta Escea, casas, palacio
const STONE = toon(0xd8c39a), STONE2 = toon(0xc4ab80), ROOF = toon(0xb85a3a), PLASTER = toon(0xf0e4cc);
const WALL_R = 112, WALL_H = 15, WALL_T = 6, NSEG = 28;
const wallTop = TROY.y + HILL_H;
const wallSegs = [];
const GATE_SEG = 0;                                  // mirando al mar (+z)
const BREACH_SEG = 1;                                // el tramo que derriban para meter el caballo
function segAngle(k) { return Math.PI / 2 - (k / NSEG) * Math.PI * 2 + Math.PI / NSEG * 0; }
for (let k = 0; k < NSEG; k++) {
  const a0 = segAngle(k) - Math.PI / NSEG, a1 = segAngle(k) + Math.PI / NSEG, am = segAngle(k);
  const len = 2 * WALL_R * Math.sin(Math.PI / NSEG) + 0.6;
  const cx = TROY.x + Math.cos(am) * WALL_R, cz = TROY.z + Math.sin(am) * WALL_R;
  const grp = new THREE.Group(); grp.position.set(cx, wallTop - 1, cz); grp.rotation.y = -am + Math.PI / 2;
  if (k === GATE_SEG) {
    for (const s of [-1, 1]) { const p = inked(new THREE.BoxGeometry(len * 0.32, WALL_H, WALL_T), STONE, 1.03); p.position.set(s * len * 0.34, WALL_H / 2, 0); grp.add(p); }
    const lint = inked(new THREE.BoxGeometry(len, 4, WALL_T), STONE, 1.03); lint.position.y = WALL_H - 2; grp.add(lint);
    const doors = []; for (const s of [-1, 1]) { const d = inked(new THREE.BoxGeometry(len * 0.18, WALL_H - 4, 1), toon(0x5a3418), 1.04); d.position.set(s * len * 0.09, (WALL_H - 4) / 2, 0); grp.add(d); doors.push(d); }
    grp.userData.doors = doors;
  } else {
    const w = inked(new THREE.BoxGeometry(len, WALL_H, WALL_T), k % 2 ? STONE : STONE2, 1.02); w.position.y = WALL_H / 2; grp.add(w);
    for (let m = -2; m <= 2; m++) { const b = inked(new THREE.BoxGeometry(2.2, 2, WALL_T + 0.4), STONE, 1.06); b.position.set(m * len / 5, WALL_H + 1, 0); grp.add(b); }   // almenas
  }
  scene.add(grp); wallSegs.push(grp);
  if (k % 2 === 0) {                                   // torres
    const ta = am - Math.PI / NSEG;
    const tw = inked(new THREE.BoxGeometry(11, WALL_H + 9, 11), STONE2, 1.03);
    tw.position.set(TROY.x + Math.cos(ta) * WALL_R, wallTop - 1 + (WALL_H + 9) / 2, TROY.z + Math.sin(ta) * WALL_R); tw.rotation.y = -ta;
    scene.add(tw); wallSegs[k].userData.tower = tw;
  }
}
// talud de la muralla (Troya VI tenía muros en pendiente)
const glacis = new THREE.Mesh(new THREE.CylinderGeometry(WALL_R + 3, WALL_R + 10, 8, NSEG, 1, true), STONE2);
glacis.position.set(TROY.x, wallTop - 4, TROY.z); glacis.receiveShadow = true; scene.add(glacis);
// casas y palacio
const houses = [];
for (let k = 0; k < 120; k++) {
  const a = rnd() * Math.PI * 2, r = 18 + rnd() * 85;
  const x = TROY.x + Math.cos(a) * r, z = TROY.z + Math.sin(a) * r;
  if (Math.hypot(x - 0, z - (-330)) < 26) continue;   // plaza donde acaba el caballo
  const w = 6 + rnd() * 8, d = 6 + rnd() * 8, h = 4 + rnd() * 5;
  const hs = inked(new THREE.BoxGeometry(w, h, d), PLASTER, 1.04); hs.position.set(x, wallTop + h / 2 - 0.5, z); hs.rotation.y = rnd() * 3;
  const rf = inked(new THREE.BoxGeometry(w + 1, 0.8, d + 1), ROOF, 1.05); rf.position.set(0, h / 2 + 0.4, 0); hs.add(rf);
  scene.add(hs); houses.push(hs);
}
const palace = inked(new THREE.BoxGeometry(34, 12, 24), PLASTER, 1.02); palace.position.set(TROY.x - 10, wallTop + 6, TROY.z - 30); scene.add(palace);
const palRoof = inked(new THREE.BoxGeometry(37, 1.5, 27), ROOF, 1.04); palRoof.position.set(0, 6.8, 0); palace.add(palRoof);
for (let k = 0; k < 6; k++) { const col = inked(new THREE.CylinderGeometry(0.8, 0.9, 10, 8), toon(0xc84a3a), 1.08); col.position.set(-14 + k * 5.6, -1, 13); palace.add(col); }
const cityParts = [...houses, palace];

// ------------------------------------------------------------------ campamento griego: tiendas y naves negras
const tents = [];
for (let k = 0; k < 46; k++) {
  const x = -260 + rnd() * 520, z = -20 + rnd() * 45;
  const t = inked(new THREE.ConeGeometry(3.4, 4.2, 4).translate(0, 2.1, 0), toon(k % 3 ? 0xe8dcc0 : 0xc8a070, { flatShading: true }), 1.06);
  t.position.set(x, groundY(x, z), z); t.rotation.y = rnd(); scene.add(t); tents.push(t);
}
function hullGeo() {
  const s = new THREE.Shape();
  s.moveTo(-11, 1.6); s.quadraticCurveTo(-13, 5, -12, 7.5); s.lineTo(-10.5, 6.5); s.quadraticCurveTo(-9, 3, -7, 2.6);
  s.lineTo(8, 2.6); s.quadraticCurveTo(11, 3, 13, 6); s.lineTo(14, 5.5); s.quadraticCurveTo(12.5, 1.5, 9, 0); s.lineTo(-8, 0); s.quadraticCurveTo(-10, 0.3, -11, 1.6);
  const g = new THREE.ExtrudeGeometry(s, { depth: 4, bevelEnabled: false }); g.translate(0, 0, -2); g.rotateY(Math.PI / 2); return g;
}
const sailTex = tex(SP.sail());
const SHIPS = [];
for (let k = 0; k < 26; k++) {
  const x = -300 + k * 24 + (rnd() - 0.5) * 6, z = shoreZ - 4 + (k % 3) * 5;
  if (Math.abs(x - 30) < 34) continue;                // la playa del caballo queda libre
  const g = new THREE.Group();
  const hull = inked(hullGeo(), toon(0x2a2422), 1.03); g.add(hull);
  const eye = new THREE.Mesh(new THREE.CircleGeometry(0.55, 12), new THREE.MeshBasicMaterial({ color: 0xffffff })); eye.position.set(2.05, 4.2, 10.4); eye.rotation.y = Math.PI / 2; g.add(eye);
  const eye2 = eye.clone(); eye2.position.x = -2.05; eye2.rotation.y = -Math.PI / 2; g.add(eye2);
  const mast = inked(new THREE.CylinderGeometry(0.18, 0.22, 12, 6).translate(0, 8, 0), toon(0x6b4220), 1.2); g.add(mast);
  const sl = new THREE.Mesh(new THREE.PlaneGeometry(9, 7), new THREE.MeshLambertMaterial({ map: sailTex, side: THREE.DoubleSide }));
  sl.position.set(0, 9.5, 0.3); sl.castShadow = true; sl.visible = false; g.add(sl); g.userData.sail = sl;
  g.position.set(x, 0, z); scene.add(g);
  SHIPS.push({ g, x0: x, z0: z, ph: rnd() * 6, lane: rnd() });
}
function shipPose(s, t) {
  // varadas → zarpan hacia la isla y se esconden detrás → vuelven
  const out = ease(prog(t, 'retirada'));
  const back = ease(clamp01((t - SC.incendio.a + 0.5) / (SC.incendio.b - SC.incendio.a + 1)));
  const hide = ISLE.clone().add(V(-120 + s.lane * 240, 0, 260 + s.lane * 120));
  const sea0 = V(s.x0, 0, s.z0 + 30);
  let p;
  if (t < SC.incendio.a - 0.5) p = V(s.x0, 0, s.z0).lerp(sea0, clamp01(out * 4)).lerp(hide, clamp01(out * 1.25 - 0.15));
  else p = hide.clone().lerp(V(s.x0 * 0.8, 0, shoreZ + 25 + s.lane * 30), back);
  const floating = p.z > shoreZ + 2;
  p.y = floating ? SEA_Y - 0.3 + Math.sin(t * 1.5 + s.ph) * 0.3 : groundY(p.x, p.z) - 0.3;
  return p;
}

// ------------------------------------------------------------------ sprites 2D en el mundo 3D (mismo sistema que Gaugamela)
function spriteMat(t) {
  const m = new THREE.MeshLambertMaterial({ map: t, alphaTest: 0.5, side: THREE.DoubleSide, emissive: 0x3a3026, emissiveMap: t });
  m.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;', 'float faceDirection = 1.0;'); };
  return m;
}
function depthMat(t) { return new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: t, alphaTest: 0.5, side: THREE.DoubleSide }); }
function spriteGeo(w, h) {
  const g = new THREE.PlaneGeometry(w, h); g.translate(0, h / 2, 0);
  const n = g.attributes.normal; for (let i = 0; i < n.count; i++) n.setXYZ(i, 0, 0.75, 0.66);
  return g;
}
class Crowd {
  constructor(canvases, w, h, n, tintFn) {
    this.n = n; this.pos = new Float32Array(n * 3); this.phase = new Float32Array(n);
    this.flip = new Float32Array(n).fill(1); this.scl = new Float32Array(n).fill(1);
    this.tx = canvases.map(tex); this.frame = 0;
    this.mesh = new THREE.InstancedMesh(spriteGeo(w, h), spriteMat(this.tx[0]), n);
    this.mesh.customDepthMaterial = depthMat(this.tx[0]);
    this.mesh.castShadow = true; this.mesh.receiveShadow = true; this.mesh.frustumCulled = false;
    for (let i = 0; i < n; i++) { this.phase[i] = rnd() * 6.28; this.mesh.setColorAt(i, tintFn ? tintFn(i) : new THREE.Color(1, 1, 1)); }
    scene.add(this.mesh);
  }
  setFrame(f) { const k = f % this.tx.length; if (k !== this.frame) { this.frame = k; this.mesh.material.map = this.mesh.material.emissiveMap = this.tx[k]; this.mesh.customDepthMaterial.map = this.tx[k]; } }
  update(bob = 0, bobSpeed = 8, t = 0) {
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3(), eul = new THREE.Euler();
    for (let i = 0; i < this.n; i++) {
      const x = this.pos[i * 3], z = this.pos[i * 3 + 2];
      const dx = camera.position.x - x, dz = camera.position.z - z;
      const yaw = Math.atan2(dx, dz), pitch = Math.atan2(camera.position.y - this.pos[i * 3 + 1], Math.hypot(dx, dz));
      q.setFromEuler(eul.set(-Math.max(0, pitch - 0.25) * 0.8, yaw, 0, 'YXZ'));
      const b = bob ? Math.abs(Math.sin(t * bobSpeed + this.phase[i])) * bob : 0;
      p.set(x, this.pos[i * 3 + 1] + b, z); s.set(this.flip[i] * this.scl[i], this.scl[i], 1);
      m.compose(p, q, s); this.mesh.setMatrixAt(i, m);
    }
    this.mesh.instanceMatrix.needsUpdate = true;
  }
}
class Hero {
  constructor(canvases, w, h) {
    this.tx = canvases.map(tex);
    this.mesh = new THREE.Mesh(spriteGeo(w, h), spriteMat(this.tx[0]));
    this.mesh.customDepthMaterial = depthMat(this.tx[0]);
    this.mesh.castShadow = true; this.mesh.receiveShadow = true; scene.add(this.mesh); this.flip = 1;
  }
  setTex(k) { this.mesh.material.map = this.mesh.material.emissiveMap = this.tx[k]; this.mesh.customDepthMaterial.map = this.tx[k]; }
  place(p, t, bob = 0) {
    this.mesh.position.set(p.x, (p.y ?? 0) + groundY(p.x, p.z) + (bob ? Math.abs(Math.sin(t * 6)) * bob : 0), p.z);
    this.mesh.rotation.y = Math.atan2(camera.position.x - p.x, camera.position.z - p.z);
    this.mesh.scale.x = this.flip;
  }
}
const camRight = new THREE.Vector3();
function flipFor(vx, vz) { camRight.setFromMatrixColumn(camera.matrixWorld, 0); return (vx * camRight.x + vz * camRight.z) > 0 ? -1 : 1; }

// ---- griegos (hoplitas) ante las murallas
const GR = [];
for (let x = -170; x <= 170; x += 2.0) for (let r = 0; r < 12; r++) GR.push([x + (r % 2), -150 + r * 2.2 + Math.abs(x) * 0.12]);
const greeks = new Crowd([SP.phalangite()], 1.15, 2.3, GR.length, () => new THREE.Color().setScalar(0.8 + rnd() * 0.2));
// ---- troyanos: arqueros en la muralla y multitud
const trojanTex = [SP.persian('#6a2a8a', '#f2c230'), SP.persian('#2a7a8a', '#f2e6c0'), SP.persian('#c86a20', '#3a2a6a')];
const WALLMEN = []; for (let k = 0; k < 260; k++) { const a = rnd() * Math.PI * 2; WALLMEN.push([TROY.x + Math.cos(a) * (WALL_R - 1.5), TROY.z + Math.sin(a) * (WALL_R - 1.5)]); }
const wallmen = new Crowd([trojanTex[0]], 1.15, 2.3, WALLMEN.length, () => new THREE.Color().setScalar(0.8 + rnd() * 0.2));
const MOB = []; for (let k = 0; k < 900; k++) { const a = rnd() * Math.PI * 2, r = 9 + Math.sqrt(rnd()) * 34; MOB.push([Math.cos(a) * r, Math.sin(a) * r * 0.8, rnd()]); }
const mobs = trojanTex.map((tx, k) => { const list = MOB.filter((_, i) => i % 3 === k); const c = new Crowd([tx], 1.15, 2.3, list.length, () => new THREE.Color().setScalar(0.8 + rnd() * 0.2)); c.list = list; return c; });
// ---- el caballo, Sinón, Laocoonte y los griegos escondidos
const horse = new Hero([SP.woodenHorse(false), SP.woodenHorse(true)], 13, 13);
const sinon = new Hero([SP.captive()], 1.2, 2.4);
const lao = new Hero([SP.priest(0), SP.priest(1)], 1.3, 2.6);
const HID = 18;
const hidden = new Crowd([SP.phalangite()], 1.15, 2.3, HID, () => new THREE.Color(0.95, 0.95, 0.95));

// ---- fuego, humo, antorchas, brasas
const fireTex = tex(SP.flame()), smokeTex = tex(SP.smokePuff(5)), dotTex = tex(SP.softDot());
const FIRES = []; for (const h of cityParts) for (let k = 0; k < (h === palace ? 10 : 2); k++) FIRES.push([h.position.x + (rnd() - 0.5) * 8, h.position.y + 2 + rnd() * 4, h.position.z + (rnd() - 0.5) * 8, rnd()]);
const flames = new THREE.InstancedMesh(new THREE.PlaneGeometry(6, 11), new THREE.MeshBasicMaterial({ map: fireTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }), FIRES.length);
flames.frustumCulled = false; scene.add(flames);
const SMK = []; for (let k = 0; k < 110; k++) { const a = rnd() * 6.28, r = rnd() * 100; SMK.push([TROY.x + Math.cos(a) * r, TROY.z + Math.sin(a) * r, rnd() * 20, 16 + rnd() * 26]); }
const smoke = new THREE.InstancedMesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshLambertMaterial({ map: smokeTex, transparent: true, depthWrite: false, opacity: 0.4, color: 0x5a4a44 }), SMK.length);
smoke.frustumCulled = false; scene.add(smoke);
const TORCH = []; for (let k = 0; k < 40; k++) { const a = rnd() * 6.28; TORCH.push([TROY.x + Math.cos(a) * (WALL_R - 1), TROY.z + Math.sin(a) * (WALL_R - 1)]); }
const torches = new THREE.InstancedMesh(new THREE.PlaneGeometry(1.2, 2.2), new THREE.MeshBasicMaterial({ map: fireTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }), TORCH.length);
torches.frustumCulled = false; scene.add(torches);
const glowLight = new THREE.PointLight(0xff8030, 0, 260, 1.2); glowLight.position.set(TROY.x, wallTop + 30, TROY.z); scene.add(glowLight);
const embN = 300, embGeo = new THREE.BufferGeometry(), embPos = new Float32Array(embN * 3), embSeed = new Float32Array(embN * 3);
for (let i = 0; i < embN; i++) embSeed.set([rnd(), rnd(), rnd()], i * 3);
embGeo.setAttribute('position', new THREE.BufferAttribute(embPos, 3));
const embers = new THREE.Points(embGeo, new THREE.PointsMaterial({ map: dotTex, size: 0.7, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, color: 0xffa040, fog: false }));
embers.frustumCulled = false; scene.add(embers);
// nubes pintadas
const cloudTex = tex(SP.cloud(9)), clouds = [];
for (let k = 0; k < 16; k++) {
  const c = new THREE.Mesh(new THREE.PlaneGeometry(600, 300), new THREE.MeshBasicMaterial({ map: cloudTex, transparent: true, alphaTest: 0.1, fog: false, depthWrite: false }));
  const a = rnd() * 6.28, r = 3000 + rnd() * 900; c.position.set(Math.cos(a) * r, 650 + rnd() * 700, Math.sin(a) * r - 200); c.lookAt(0, 300, -200);
  clouds.push(c); scene.add(c);
}

// ------------------------------------------------------------------ la historia
const BEACH = V(30, 0, 52);                                  // donde aparece el caballo
const BREACH = (() => { const a = segAngle(BREACH_SEG); return V(TROY.x + Math.cos(a) * WALL_R, 0, TROY.z + Math.sin(a) * WALL_R); })();
const PLAZA = V(0, 0, -330);
function horsePos(t) {
  if (t < SC.brecha.a + 0.4) return BEACH.clone();
  const u = ease(clamp01((t - SC.brecha.a - 0.4) / (SC.brecha.b - SC.brecha.a - 0.4)));
  const outside = BREACH.clone().add(V(0, 0, 0)).add(BREACH.clone().sub(TROY).setY(0).normalize().multiplyScalar(30));
  if (u < 0.72) return BEACH.clone().lerp(outside, u / 0.72);
  return outside.lerp(PLAZA, (u - 0.72) / 0.28);
}
function breachDrop(t) { return ease(clamp01((t - SC.brecha.a - 0.3) / 2.2)); }   // el tramo derribado se hunde

// ------------------------------------------------------------------ cámara (Catmull-Rom con tangentes limitadas)
function camKeys() {
  const K = []; const k = (t, pos, tgt, fov = 50) => K.push({ t, pos, tgt, fov });
  const HP = t => horsePos(t), top = wallTop;
  let t;
  t = 0;                        k(t, V(36, 2.8, 100), V(2, 26, -300), 30);
  t = at('gancho', 0.6);         k(t, V(38, 4.5, 110), V(0, 26, -310), 31);
  t = at('gancho', 1);           k(t, V(70, 26, 122), V(0, 22, -360), 34);
  t = at('asedio', 0.55);        k(t, V(110, 40, -40), V(0, 14, -200), 44);
  t = at('asedio', 1);           k(t, V(30, 7, -120), V(-10, 18, -268), 44);
  t = at('murallas', 0.5);       k(t, V(18, top + 2, -238), V(4, top + 11, -268), 52);
  t = at('murallas', 1);         k(t, V(-22, top + 3, -234), V(-14, top + 13, -266), 54);
  t = at('retirada', 0.25);      k(t, V(-2, top + 20, -262), V(20, -40, 120), 46);
  t = at('retirada', 0.75);      k(t, V(10, top + 19, -256), V(120, -30, 420), 42);
  t = at('retirada', 1);         k(t, V(50, 30, 120), V(30, 6, 50), 48);
  t = at('caballo', 0.45);       k(t, V(56, 4, 86), V(30, 7, 50), 46);
  t = at('caballo', 1);          k(t, V(24, 2.6, 64), V(36, 1.8, 58), 40);
  t = at('aviso', 0.5);          k(t, V(19, 2.2, 73), V(25, 3.2, 60), 40);
  t = at('aviso', 1);            k(t, V(10, 6, 80), V(28, 6, 50), 46);
  t = at('brecha', 0.3);         k(t, V(90, 45, -110), V(BREACH.x, top + 4, BREACH.z), 50);
  t = at('brecha', 0.75);        k(t, V(70, 40, -170), V(BREACH.x, top + 2, BREACH.z), 46);
  t = at('brecha', 1);           k(t, V(36, top + 18, -290), V(PLAZA.x, top + 5, PLAZA.z), 48);
  t = at('noche', 0.5);          k(t, V(9, top + 9, -316), V(PLAZA.x, top + 4, PLAZA.z), 50);
  t = at('noche', 1);            k(t, V(-22, top + 22, -322), V(0, top + 6, -264), 50);
  t = at('incendio', 0.12);      k(t, V(10, top + 48, -290), V(0, top + 6, -380), 50);
  t = at('incendio', 0.5);       k(t, V(120, 60, -110), V(0, top + 10, -370), 48);
  t = at('incendio', 1);         k(t, V(150, 80, -60), V(0, top, -380), 50);
  t = at('ruinas', 0.5);         k(t, V(70, top + 40, -250), V(0, top, -380), 48);
  t = at('ruinas', 1);           k(t, V(-20, top + 30, -230), V(0, top, -380), 48);
  t = at('final', 0.4);          k(t, V(58, 5, 106), V(30, 7, 50), 40);
  t = TL.total;                  k(t, V(48, 4.5, 90), V(30, 7, 50), 36);
  return K;
}
let KEYS = null;
function hermite(K, t, f) {
  let i = 0; while (i < K.length - 2 && t > K[i + 1].t) i++;
  const k0 = K[Math.max(0, i - 1)], k1 = K[i], k2 = K[i + 1], k3 = K[Math.min(K.length - 1, i + 2)];
  const dt = k2.t - k1.t, u = clamp01((t - k1.t) / dt);
  const m1 = f(k2).clone().sub(f(k0)).multiplyScalar(dt / Math.max(1e-3, k2.t - k0.t));
  const m2 = f(k3).clone().sub(f(k1)).multiplyScalar(dt / Math.max(1e-3, k3.t - k1.t));
  const seg = f(k2).distanceTo(f(k1)); if (m1.length() > seg) m1.setLength(seg); if (m2.length() > seg) m2.setLength(seg);
  const u2 = u * u, u3 = u2 * u;
  return f(k1).clone().multiplyScalar(2 * u3 - 3 * u2 + 1).add(m1.multiplyScalar(u3 - 2 * u2 + u))
    .add(f(k2).clone().multiplyScalar(-2 * u3 + 3 * u2)).add(m2.multiplyScalar(u3 - u2));
}
function cameraAt(t) {
  const p = hermite(KEYS, t, k => k.pos), g = hermite(KEYS, t, k => k.tgt), fv = hermite(KEYS, t, k => V(k.fov, 0, 0)).x;
  // brecha: cámara que sigue al caballo mientras lo arrastran hasta la muralla abierta
  const f0 = SC.brecha.a + 0.5, f1 = SC.brecha.b - 0.3;
  const w = ease(clamp01((t - f0) / 1.0)) * ease(clamp01((f1 - t) / 1.0));
  if (w > 0) {
    const HP = horsePos(t), u = prog(t, 'brecha');
    const dir = BREACH.clone().sub(HP).setY(0); const L = dir.length(); dir.normalize();
    const side = V(-dir.z, 0, dir.x);
    const fp = HP.clone().addScaledVector(dir, -24).addScaledVector(side, 7); fp.y = groundY(fp.x, fp.z) + 11;
    const look = HP.clone().addScaledVector(dir, Math.min(L, 60)); look.y = groundY(look.x, look.z) + 6;
    p.lerp(fp, w); g.lerp(look, w);
  }
  p.x += Math.sin(t * 1.3) * 0.12; p.y += Math.sin(t * 1.7 + 1) * 0.08;
  const minY = Math.max(groundY(p.x, p.z), SEA_Y) + 1.4; if (p.y < minY) p.y = minY;
  camera.position.copy(p); camera.lookAt(g); camera.fov = fv; camera.updateProjectionMatrix(); camera.updateMatrixWorld();
  return g;
}

// ------------------------------------------------------------------ fotograma
const dummy = new THREE.Matrix4();
window.renderAt = function (t) {
  if (!KEYS) KEYS = camKeys();
  const tgt = cameraAt(t);
  const M = mood(t);
  sun.color.copy(M.sun); sun.intensity = M.si; hemi.color.copy(M.hs); hemi.groundColor.copy(M.gnd);
  scene.fog.color.copy(M.fog); skyMat.uniforms.top.value.copy(M.sky); skyMat.uniforms.hor.value.copy(M.hor);
  const nightU = clamp01(1 - Math.abs(t - at('noche', 0.5)) / ((SC.noche.b - SC.noche.a) * 0.75));
  skyMat.uniforms.stars.value = 0.9 * nightU;
  renderer.toneMappingExposure = M.exp; sky.position.copy(camera.position);
  for (const c of clouds) c.material.color.copy(M.hor).lerp(new THREE.Color(1, 1, 1), 0.45);
  const dist = camera.position.distanceTo(tgt), sz = clamp(dist * 0.9, 40, 520);
  sun.position.copy(tgt).addScaledVector(M.dir, 700); sun.target.position.copy(tgt);
  Object.assign(sun.shadow.camera, { left: -sz, right: sz, top: sz, bottom: -sz, near: 1, far: 1800 }); sun.shadow.camera.updateProjectionMatrix();
  waveSea(t); foam.position.set(0, SEA_Y + 0.25 + Math.sin(t * 1.2) * 0.15, shoreZ + Math.sin(t * 0.9) * 1.5);

  // ruinas (hoy): la ciudad desaparece y las murallas quedan bajas
  const ruin = clamp01((t - SC.ruinas.a) / 0.9) * (1 - clamp01((t - SC.final.a - 0.5) / 1.2));
  const cityVis = ruin < 0.5;
  for (const h of cityParts) h.visible = cityVis;
  wallSegs.forEach((s, k) => {
    let sy = lerp(1, 0.28 + 0.12 * Math.sin(k * 2.7), ruin);
    let drop = 0;
    if (k === BREACH_SEG) drop = breachDrop(t) * (WALL_H + 2);
    s.scale.y = sy; s.position.y = wallTop - 1 - drop;
    if (s.userData.tower) { const ts = lerp(1, 0.3, ruin); s.userData.tower.scale.y = ts; s.userData.tower.position.y = wallTop - 1 + (WALL_H + 9) * ts / 2; }
    if (s.userData.doors) { const open = ease(clamp01((t - at('noche', 0.55)) / 1.2)) * (t < SC.ruinas.a ? 1 : 0); s.userData.doors.forEach((d, i) => { d.rotation.y = (i ? -1 : 1) * open * 1.4; }); }
  });
  groundMat.color.copy(new THREE.Color(1, 1, 1).lerp(new THREE.Color(0.75, 0.95, 0.65), ruin));

  // naves
  for (const s of SHIPS) {
    const p = shipPose(s, t), p2 = shipPose(s, t + 0.2), dir = p2.clone().sub(p); dir.y = 0;
    s.g.position.copy(p);
    if (dir.length() > 0.05) s.g.rotation.y = Math.atan2(dir.x, dir.z);
    else s.g.rotation.y = 0;
    s.g.rotation.z = Math.sin(t * 1.3 + s.ph) * 0.03 * (p.z > shoreZ ? 1 : 0);
    s.g.userData.sail.visible = p.z > shoreZ + 3;
    s.g.visible = ruin < 0.5;
  }
  tents.forEach(tn => { tn.visible = t < SC.retirada.a + 1.2; });

  // griegos ante las murallas (se van en la retirada)
  const grVis = t < SC.retirada.a + 0.8 ? 1 : 0;
  GR.forEach(([x, z], i) => { const zz = z + 3 * Math.sin(t * 0.6 + i); greeks.pos.set([x, groundY(x, zz) - (grVis ? 0 : 80), zz], i * 3); });
  greeks.update(0.05, 2, t);
  // arqueros troyanos en la muralla
  const onWall = t < SC.brecha.a && ruin < 0.5;          // vigilan desde la muralla hasta que bajan al caballo
  WALLMEN.forEach(([x, z], i) => { wallmen.pos.set([x, wallTop + WALL_H - 1 + (onWall ? 0 : -80), z], i * 3); });
  wallmen.update(0.03, 2, t);
  // multitud troyana: en la playa alrededor del caballo, tirando de él, celebrando en la plaza
  const HP = horsePos(t);
  const mobOn = t > SC.retirada.b - 0.3 && t < SC.incendio.a;
  for (const cr of mobs) {
    cr.list.forEach(([dx, dz, r], i) => {
      let x = HP.x + dx, z = HP.z + dz;
      if (t > SC.brecha.a && t < SC.noche.a) { x = HP.x + dx * 0.5; z = HP.z - 14 - Math.abs(dz) * 1.4; }   // delante, tirando
      if (t > SC.noche.a) { x = HP.x + dx * 1.2; z = HP.z + dz * 1.1; }
      const asleep = t > at('noche', 0.3) ? -0.9 * ease(clamp01((t - at('noche', 0.3)) / 1.5)) * (r < 0.6 ? 1 : 0) : 0;
      cr.pos.set([x, groundY(x, z) + (mobOn ? asleep : -80), z], i * 3);
    });
    const dancing = t > SC.noche.a && t < at('noche', 0.3);
    cr.update(dancing ? 0.35 : (t > SC.brecha.a && t < SC.noche.a ? 0.15 : 0.05), dancing ? 7 : 3, t);
  }
  // caballo
  horse.setTex(t > at('noche', 0.25) && t < SC.ruinas.a ? 1 : 0);
  const moving = t > SC.brecha.a + 0.4 && t < SC.brecha.b;
  const hv = horsePos(t + 0.1).sub(HP);
  horse.flip = moving && hv.length() > 0.01 ? flipFor(hv.x, hv.z) : 1;
  const ghost = clamp01((t - SC.final.a) / 1.0);
  horse.mesh.visible = ruin < 0.5 || ghost > 0;
  const hp = ghost > 0 ? BEACH.clone() : HP;
  horse.place(hp, t, moving ? 0.12 : 0);
  const op = ghost > 0 ? lerp(1, 0.4, ease(clamp01((t - at('final', 0.45)) / 2))) : 1;
  horse.mesh.material.transparent = op < 1; horse.mesh.material.opacity = op; horse.mesh.material.alphaTest = 0.45 * op;
  horse.mesh.castShadow = op > 0.9;
  // Sinón y Laocoonte
  const sinOn = t > SC.caballo.a + 0.5 && t < SC.brecha.a;
  sinon.place(sinOn ? BEACH.clone().add(V(6, 0, 7)) : V(0, -100, 0), t, 0.02);
  const laoOn = t > SC.aviso.a - 0.3 && t < SC.brecha.a;
  lao.setTex(Math.floor(t * 3) % 2); lao.place(laoOn ? BEACH.clone().add(V(-5, 0, 10)) : V(0, -100, 0), t, 0.04);
  // griegos que bajan del caballo
  const out = clamp01((t - at('noche', 0.3)) / ((SC.noche.b - SC.noche.a) * 0.6));
  for (let i = 0; i < HID; i++) {
    const u = clamp01(out * HID / 4 - i / 4);
    const tgtP = V(HP.x + (i - HID / 2) * 1.6, 0, HP.z + 18 + (i % 3) * 3);
    const p = V(HP.x - 0.5, 0, HP.z + 0.2).lerp(tgtP, ease(u));
    hidden.pos.set([p.x, groundY(p.x, p.z) + (u > 0 && t < SC.incendio.b ? 0 : -80) + (u < 0.15 ? (1 - u / 0.15) * 4 : 0), p.z], i * 3);
  }
  hidden.update(0.2, 8, t);

  // fuego
  const burn = clamp01((t - SC.incendio.a) / 1.5) * (ruin < 0.5 ? 1 : 0);
  FIRES.forEach(([x, y, z, r], i) => {
    const f = burn > r * 0.6 ? (0.8 + 0.3 * Math.sin(t * 19 + r * 9) + 0.15 * Math.sin(t * 37 + r)) * clamp01((burn - r * 0.6) * 3) : 0;
    dummy.compose(V(x, y - 1, z), camera.quaternion, V(f, f, 1)); flames.setMatrixAt(i, dummy);
  });
  flames.instanceMatrix.needsUpdate = true;
  glowLight.intensity = burn * 900 * (0.85 + 0.15 * Math.sin(t * 13));
  SMK.forEach(([x, z, ph, s], i) => {
    const life = ((t * 0.07 + ph / 20) % 1), sc = s * (0.6 + life * 1.4) * burn;
    dummy.compose(V(x + life * 30, wallTop + 6 + life * 70, z), camera.quaternion, V(sc, sc, 1)); smoke.setMatrixAt(i, dummy);
  });
  smoke.instanceMatrix.needsUpdate = true;
  const torchOn = (t > SC.brecha.a + 1 && t < SC.ruinas.a) ? 1 : 0;
  TORCH.forEach(([x, z], i) => { const f = torchOn * (0.85 + 0.25 * Math.sin(t * 21 + i)); dummy.compose(V(x, wallTop + WALL_H + 1.2, z), camera.quaternion, V(f, f, 1)); torches.setMatrixAt(i, dummy); });
  torches.instanceMatrix.needsUpdate = true;
  for (let i = 0; i < embN; i++) {
    const [a, b, c] = [embSeed[i * 3], embSeed[i * 3 + 1], embSeed[i * 3 + 2]];
    const life = (t * (0.12 + 0.2 * c) + a) % 1;
    embPos.set([TROY.x + (a - 0.5) * 220, wallTop + life * 90, TROY.z + (b - 0.5) * 220], i * 3);
  }
  embGeo.attributes.position.needsUpdate = true; embers.material.opacity = burn;

  renderer.render(scene, camera);
  return true;
};
window.grab = (q = 0.93) => renderer.domElement.toDataURL('image/jpeg', q);
window.READY = true;
