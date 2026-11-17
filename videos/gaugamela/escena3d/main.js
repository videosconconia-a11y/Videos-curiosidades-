// Gaugamela, 331 a. C.: personajes 2D (recortes dibujados con código) en un mundo 3D real.
// Reciben la luz principal y proyectan sombras reales; el mundo es geometría 3D con contorno de tinta.
// La cámara nunca corta: viaja de un momento al siguiente por una curva continua.
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
let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;

// ------------------------------------------------------------------ renderer
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xd9a46a, 300, 3200);
const camera = new THREE.PerspectiveCamera(50, W / H, 0.5, 6000);

// ------------------------------------------------------------------ luz (sigue a la historia)
const hemi = new THREE.HemisphereLight(0xffd9a0, 0x6a4a3a, 0.9); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffc27a, 2.6); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.6;
scene.add(sun); scene.add(sun.target);
// cálida y brillante mientras se plantea; azul de noche al llegar la explicación; fuego en el choque; noche al final
const MOODS = {
  warm:  { sun: 0xffc27a, si: 2.7, sky: 0x4a8fd8, hor: 0xffc58a, gnd: 0x7a5236, hs: 0xffd9a0, fog: 0xe0a66c, exp: 1.05, dir: [-0.55, 0.42, 0.72] },
  dusk:  { sun: 0xd0c4ff, si: 2.1, sky: 0x1a2a66, hor: 0x7a7ac0, gnd: 0x3a2c38, hs: 0x6a7ad0, fog: 0x4a5490, exp: 0.98, dir: [0.5, 0.6, 0.62] },
  fire:  { sun: 0xffb070, si: 2.8, sky: 0x2e2448, hor: 0xff8a48, gnd: 0x4a3a40, hs: 0xd8c0b0, fog: 0x9a6a50, exp: 1.08, dir: [-0.6, 0.3, 0.75] },
  night: { sun: 0x8fb0ff, si: 1.4, sky: 0x050a1e, hor: 0x1e2c5a, gnd: 0x0a0c18, hs: 0x4a5fa8, fog: 0x141c3a, exp: 0.95, dir: [0.35, 0.26, -0.9] },
};
const MOOD_KEYS = [
  [0, 'warm'], [at('carros', 1) - 0.4, 'warm'], [at('diagonal', 0.08), 'dusk'], [at('hueco', 1) - 0.3, 'dusk'],
  [at('pasillos', 0.15), 'fire'], [at('huida', 1), 'fire'], [at('final', 0.2), 'night'], [TL.total + 1, 'night'],
];
const tmpC1 = new THREE.Color(), tmpC2 = new THREE.Color();
function mixCol(a, b, u) { return tmpC1.set(a).lerp(tmpC2.set(b), u).clone(); }
function mood(t) {
  let i = 0; while (i < MOOD_KEYS.length - 2 && t > MOOD_KEYS[i + 1][0]) i++;
  const [t0, m0] = MOOD_KEYS[i], [t1, m1] = MOOD_KEYS[i + 1];
  const u = ease(clamp01((t - t0) / (t1 - t0))); const A = MOODS[m0], B = MOODS[m1];
  return {
    sun: mixCol(A.sun, B.sun, u), si: lerp(A.si, B.si, u), sky: mixCol(A.sky, B.sky, u), hor: mixCol(A.hor, B.hor, u),
    gnd: mixCol(A.gnd, B.gnd, u), hs: mixCol(A.hs, B.hs, u), fog: mixCol(A.fog, B.fog, u), exp: lerp(A.exp, B.exp, u),
    dir: new THREE.Vector3(...A.dir).lerp(new THREE.Vector3(...B.dir), u).normalize(),
  };
}

// ------------------------------------------------------------------ cielo
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { top: { value: new THREE.Color() }, hor: { value: new THREE.Color() } },
  vertexShader: 'varying vec3 vp; void main(){ vp = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }',
  fragmentShader: 'uniform vec3 top; uniform vec3 hor; varying vec3 vp; void main(){ float h = clamp(vp.y*2.2,0.,1.); gl_FragColor = vec4(mix(hor, top, pow(h,0.7)),1.); }',
});
const sky = new THREE.Mesh(new THREE.SphereGeometry(5000, 32, 16), skyMat); scene.add(sky);

// ------------------------------------------------------------------ materiales de cómic
const grad3 = new THREE.DataTexture(new Uint8Array([90, 170, 255]), 3, 1, THREE.RedFormat);
grad3.minFilter = grad3.magFilter = THREE.NearestFilter; grad3.needsUpdate = true;
const toon = (color, extra = {}) => new THREE.MeshToonMaterial({ color, gradientMap: grad3, ...extra });
const inkMat = new THREE.MeshBasicMaterial({ color: 0x140f0f, side: THREE.BackSide, fog: true });
function inked(geom, mat, thick = 1.04) {           // contorno de tinta por "casco invertido"
  const g = new THREE.Group();
  const m = new THREE.Mesh(geom, mat); m.castShadow = true; m.receiveShadow = true;
  const o = new THREE.Mesh(geom, inkMat); o.scale.setScalar(thick);
  g.add(m, o); return g;
}

// ------------------------------------------------------------------ suelo
const GROUND = 3200, GSEG = 320;
const gGeo = new THREE.PlaneGeometry(GROUND, GROUND, GSEG, GSEG); gGeo.rotateX(-Math.PI / 2);
const gPos = gGeo.attributes.position, gCol = new Float32Array(gPos.count * 3);
const LEVEL = { x0: -200, x1: 175, z0: -240, z1: -25 };              // terreno allanado por Darío
function inLevel(x, z, m = 0) { return x > LEVEL.x0 - m && x < LEVEL.x1 + m && z > LEVEL.z0 - m && z < LEVEL.z1 + m; }
function noise2(x, z) { return Math.sin(x * 0.013 + Math.sin(z * 0.011) * 2) * 0.5 + Math.sin(z * 0.017 + x * 0.004) * 0.35 + Math.sin((x + z) * 0.041) * 0.15; }
const burns = []; for (let k = 0; k < 40; k++) burns.push([-260 + rnd() * 560, -330 + rnd() * 380, 6 + rnd() * 16]);
function levelAmt(x, z) {           // 1 dentro del terreno allanado, transición suave de 25 m
  const dx = Math.max(LEVEL.x0 - x, 0, x - LEVEL.x1), dz = Math.max(LEVEL.z0 - z, 0, z - LEVEL.z1);
  return Math.max(0, 1 - Math.hypot(dx, dz) / 25);
}
function groundY(x, z) {
  const d = Math.hypot(x, z + 200);
  const y = noise2(x, z) * 2.2 + Math.max(0, d - 700) * 0.08 * (1 + noise2(z, x));
  return y * (1 - 0.85 * levelAmt(x, z));
}
for (let i = 0; i < gPos.count; i++) {
  const x = gPos.getX(i), z = gPos.getZ(i) - 200;
  gPos.setZ(i, z);
  const lv = levelAmt(x, z);
  gPos.setY(i, groundY(x, z));
  const n = noise2(x * 3.1, z * 2.7) * 0.5 + 0.5;
  let c = [0.78 + 0.1 * n, 0.58 + 0.08 * n, 0.36 + 0.05 * n];              // tierra seca, ocre saturado
  if (lv > 0) c = c.map((v, k) => lerp(v, [0.9, 0.74, 0.5][k], lv * 0.75));   // allanado: más claro y liso
  for (const [bx, bz, br] of burns) {                                     // tierra quemada
    const q = Math.hypot(x - bx, z - bz) / br; if (q < 1) c = c.map(v => v * (0.35 + 0.65 * q));
  }
  gCol.set(c, i * 3);
}
gGeo.setAttribute('color', new THREE.BufferAttribute(gCol, 3)); gGeo.computeVertexNormals();
const detail = (() => {           // textura de detalle repetida (grano de tierra, piedrecitas)
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  g.fillStyle = '#d8d0c4'; g.fillRect(0, 0, 256, 256);
  for (let k = 0; k < 2200; k++) { const v = 150 + rnd() * 105 | 0; g.fillStyle = `rgb(${v},${v - 8},${v - 20})`; g.fillRect(rnd() * 256, rnd() * 256, 1 + rnd() * 3, 1 + rnd() * 3); }
  for (let k = 0; k < 40; k++) { g.strokeStyle = 'rgba(70,40,20,0.35)'; g.lineWidth = 1.5; g.beginPath(); let x = rnd() * 256, y = rnd() * 256; g.moveTo(x, y); for (let j = 0; j < 4; j++) { x += rnd() * 30 - 15; y += rnd() * 30 - 15; g.lineTo(x, y); } g.stroke(); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(GROUND / 9, GROUND / 9);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
})();
const ground = new THREE.Mesh(gGeo, new THREE.MeshLambertMaterial({ vertexColors: true, map: detail }));
ground.receiveShadow = true; scene.add(ground);

// ------------------------------------------------------------------ montañas con nieve, rocas, matorrales (3D con tinta)
for (let k = 0; k < 34; k++) {
  const a = (k / 34) * Math.PI * 2 + rnd() * 0.15, r = 2100 + rnd() * 700;
  const h = 150 + rnd() * 260, w = 420 + rnd() * 520, seg = 6 + (rnd() * 3 | 0), rot = rnd() * 6;
  const geo = new THREE.ConeGeometry(w, h, seg, 1); geo.translate(0, h / 2, 0);
  const m = inked(geo, toon(0x7c7aa8, { flatShading: true }), 1.01);
  m.scale.set(1 + rnd() * 0.6, 1, 0.7 + rnd() * 0.4);
  m.position.set(Math.cos(a) * r, -30, Math.sin(a) * r - 200); m.rotation.y = rot; scene.add(m);
  const cg = new THREE.ConeGeometry(w * 0.32, h * 0.32, seg, 1); cg.translate(0, h - h * 0.16 + 0.5, 0);
  const cap = new THREE.Mesh(cg, toon(0xf4f6ff, { flatShading: true }));
  cap.scale.copy(m.scale).multiplyScalar(1.01); cap.position.copy(m.position); cap.rotation.y = rot; scene.add(cap);
}
const rockGeo = new THREE.DodecahedronGeometry(1, 0);
for (let k = 0; k < 160; k++) {
  const x = -700 + rnd() * 1400, z = -700 + rnd() * 900;
  if (inLevel(x, z, 15) || (z < -250 && z > -400 && Math.abs(x) < 440) || (z > -20 && z < 40 && x > -290 && x < 330)) continue;
  const s = 0.6 + rnd() * 2.6;
  const r = inked(rockGeo, toon(0x9a7a5a, { flatShading: true }), 1.08);
  r.scale.set(s * (1 + rnd()), s * 0.7, s); r.position.set(x, groundY(x, z) + s * 0.3, z); r.rotation.set(rnd(), rnd() * 6, rnd()); scene.add(r);
}

// ------------------------------------------------------------------ sprites 2D en el mundo 3D
function tex(canvas) { const t = new THREE.CanvasTexture(canvas); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t; }
function spriteMat(t) {
  // recorte 2D iluminado por la luz del mundo; la normal no se invierte por la cara trasera
  const m = new THREE.MeshLambertMaterial({ map: t, alphaTest: 0.5, side: THREE.DoubleSide, emissive: 0x3a3026, emissiveMap: t });
  m.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;', 'float faceDirection = 1.0;'); };
  return m;
}
function depthMat(t) { return new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: t, alphaTest: 0.5, side: THREE.DoubleSide }); }
function spriteGeo(w, h) {
  const g = new THREE.PlaneGeometry(w, h); g.translate(0, h / 2, 0);
  const n = g.attributes.normal; for (let i = 0; i < n.count; i++) n.setXYZ(i, 0, 0.75, 0.66);   // mirando arriba y a cámara
  return g;
}

// Un grupo de sprites instanciados (miles de soldados): cada uno de pie en su sitio y mirando a cámara.
class Crowd {
  constructor(canvases, w, h, n, tintFn) {
    this.n = n; this.base = new Float32Array(n * 3); this.pos = new Float32Array(n * 3);
    this.phase = new Float32Array(n); this.flip = new Float32Array(n).fill(1); this.scl = new Float32Array(n).fill(1);
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
// sprite individual (Alejandro, Darío)
class Hero {
  constructor(canvases, w, h) {
    this.tx = canvases.map(tex);
    this.mesh = new THREE.Mesh(spriteGeo(w, h), spriteMat(this.tx[0]));
    this.mesh.customDepthMaterial = depthMat(this.tx[0]);
    this.mesh.castShadow = true; this.mesh.receiveShadow = true; scene.add(this.mesh); this.flip = 1;
  }
  place(p, t, bob = 0, frameRate = 0) {
    if (frameRate) { const k = Math.floor(t * frameRate) % this.tx.length; this.mesh.material.map = this.mesh.material.emissiveMap = this.tx[k]; this.mesh.customDepthMaterial.map = this.tx[k]; }
    this.mesh.position.set(p.x, groundY(p.x, p.z) + (bob ? Math.abs(Math.sin(t * 9)) * bob : 0), p.z);
    this.mesh.rotation.y = Math.atan2(camera.position.x - p.x, camera.position.z - p.z);
    this.mesh.scale.x = this.flip;
  }
}
// voltear un sprite que mira a la izquierda según su dirección de avance vista desde la cámara
const camRight = new THREE.Vector3();
function flipFor(vx, vz) { camRight.setFromMatrixColumn(camera.matrixWorld, 0); return (vx * camRight.x + vz * camRight.z) > 0 ? -1 : 1; }

// ---- ejército macedonio (~47.000 → representado con 6.500 figuras)
const PH = [];  // [x, z]
for (let x = -175; x <= 90; x += 1.7) for (let r = 0; r < 16; r++) PH.push([x + (r % 2) * 0.85, 4 + r * 1.7]);
for (let x = -300; x < -185; x += 2.4) for (let r = 0; r < 10; r++) PH.push([x, 6 + r * 2.4]);       // ala izquierda (Parmenión)
const phal = new Crowd([SP.phalangite()], 1.15, 2.3, PH.length, () => new THREE.Color().setScalar(0.82 + rnd() * 0.18));
const COMP = [];  // caballería de los Compañeros (ala derecha, con Alejandro)
for (let x = 100; x < 165; x += 3.2) for (let r = 0; r < 7; r++) COMP.push([x + (r % 2) * 1.6, 2 + r * 3.4]);
const compFrames = [0, 1].map(f => SP.rider({ frame: f, coat: '#7a4a2a', cloak: '#b0242c', helmet: '#c99a3a' }));
const compA = new Crowd(compFrames, 3.6, 3.6, Math.ceil(COMP.length / 2), () => new THREE.Color().setHSL(0.06, 0.25 + rnd() * 0.3, 0.6 + rnd() * 0.35));
const compB = new Crowd([compFrames[1], compFrames[0]], 3.6, 3.6, Math.floor(COMP.length / 2), () => new THREE.Color().setHSL(0.06, 0.25 + rnd() * 0.3, 0.6 + rnd() * 0.35));

// ---- ejército persa (el doble; se extiende mucho más a los lados)
const PE = [];
for (let x = -430; x <= 430; x += 2.3) for (let r = 0; r < 52; r++) {
  const z = -262 - r * 2.3 - Math.abs(x) * 0.05 + (rnd() - 0.5) * 1.2, xx = x + (rnd() - 0.5) * 1.4;
  if (Math.hypot(xx, z + 292) < 22) continue;          // hueco alrededor del carro de Darío
  PE.push([xx, z]);
}
const peTypes = [SP.persian('#2f5fb3', '#f2c230'), SP.persian('#e0a020', '#2f5fb3'), SP.persian('#b02a2a', '#f2e6c0')];
const peGroups = [[], [], []]; PE.forEach((p, i) => peGroups[(i * 7 + (i >> 3)) % 3].push(p));
const pers = peGroups.map((g, k) => { const c = new Crowd([peTypes[k]], 1.15, 2.3, g.length, () => new THREE.Color().setScalar(0.8 + rnd() * 0.2)); c.list = g; return c; });

// ---- carros con cuchillas (200 → 48 en pantalla), en carriles frente a la falange
const LANES = [-150, -122, -94, -66, -38, -10, 18, 46];
const CH = []; LANES.forEach((x, i) => { for (let k = 0; k < 6; k++) CH.push([x + (rnd() - 0.5) * 2, -232 - k * 0.0 - (k % 2) * 5, k * 5.5 + rnd() * 3, i]); });
const chFrames = [SP.chariot(0), SP.chariot(1)];
const chariots = new Crowd(chFrames, 6.4, 4.0, CH.length);
const wheels = new THREE.InstancedMesh(new THREE.PlaneGeometry(1.7, 1.7), spriteMat(tex(SP.wheel())), CH.length);
wheels.customDepthMaterial = depthMat(wheels.material.map); wheels.castShadow = true; wheels.frustumCulled = false; scene.add(wheels);
// ---- elefantes (15)
const EL = []; for (let k = 0; k < 15; k++) EL.push([-60 + k * 8.5 + (rnd() - 0.5) * 3, -252 - (k % 2) * 4]);
const eleph = new Crowd([SP.elephant()], 6.0, 4.9, EL.length);
// ---- héroes
const alex = new Hero([0, 1].map(f => SP.rider({ frame: f, coat: '#18161a', mane: '#050505', cloak: '#d8202a', helmet: '#f0c43a', plume: '#ffffff', star: true, gold: true })), 5.0, 5.0);
const dar = new Hero([SP.darius(0), SP.darius(1)], 7.0, 5.7);
// ---- conspiradores del final (sus propios hombres)
const CONS = new Crowd([SP.persian('#1c1c2a', '#3a3a50')], 1.25, 2.5, 6, () => new THREE.Color(0.45, 0.45, 0.55));

// ---- estandartes con tela que ondea (3D, tinta)
const flags = [];
function standard(x, z, color, big = 1) {
  const pole = inked(new THREE.CylinderGeometry(0.08 * big, 0.08 * big, 7 * big, 6), toon(0x6b4220), 1.3);
  pole.position.set(x, groundY(x, z) + 3.5 * big, z); scene.add(pole);
  const geo = new THREE.PlaneGeometry(2.6 * big, 1.6 * big, 12, 4); geo.translate(1.3 * big, 0, 0);
  const cloth = new THREE.Mesh(geo, toon(color, { side: THREE.DoubleSide }));
  cloth.position.set(x, groundY(x, z) + 6.1 * big, z); cloth.castShadow = true; scene.add(cloth);
  flags.push({ cloth, base: geo.attributes.position.array.slice(), ph: rnd() * 6 });
}
for (let x = -160; x <= 80; x += 40) standard(x, 1, 0xc8202a);
for (let x = -400; x <= 400; x += 55) standard(x, -258 - Math.abs(x) * 0.05, 0xe8b830);
standard(-6, -298, 0xe8c050, 1.6);
function waveFlags(t) {
  for (const f of flags) {
    const a = f.cloth.geometry.attributes.position; const b = f.base;
    for (let i = 0; i < a.count; i++) { const x = b[i * 3]; a.setZ(i, Math.sin(x * 2.2 - t * 6 + f.ph) * 0.25 * x); }
    a.needsUpdate = true; f.cloth.geometry.computeVertexNormals();
  }
}

// ---- flechas clavadas ardiendo + humo + polvo + brasas
const fireTex = tex(SP.flame()), smokeTex = tex(SP.smokePuff(5)), dotTex = tex(SP.softDot());
const ARR = []; for (let k = 0; k < 140; k++) { const x = -280 + rnd() * 520, z = -230 + rnd() * 260; ARR.push([x, z, rnd() * 6]); }
const arrowGeo = new THREE.CylinderGeometry(0.03, 0.03, 1.2, 4); arrowGeo.translate(0, 0.6, 0);
const arrows = new THREE.InstancedMesh(arrowGeo, toon(0x3a2416), ARR.length); arrows.castShadow = true;
const flames = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.7, 1.3), new THREE.MeshBasicMaterial({ map: fireTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }), ARR.length);
flames.frustumCulled = arrows.frustumCulled = false; scene.add(arrows, flames);
ARR.forEach(([x, z, r], i) => { const m = new THREE.Matrix4().compose(new THREE.Vector3(x, groundY(x, z) - 0.1, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(0.5 * Math.sin(r), r, 0.4 * Math.cos(r))), new THREE.Vector3(1, 1, 1)); arrows.setMatrixAt(i, m); });
const SMK = []; for (let k = 0; k < 90; k++) SMK.push([-320 + rnd() * 640, -380 + rnd() * 420, rnd() * 20, 8 + rnd() * 18]);
const smoke = new THREE.InstancedMesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshLambertMaterial({ map: smokeTex, transparent: true, depthWrite: false, opacity: 0.32, color: 0x8a7a70 }), SMK.length);
smoke.frustumCulled = false; scene.add(smoke);
const dustN = 2500, dustGeo = new THREE.BufferGeometry(), dustPos = new Float32Array(dustN * 3), dustSeed = new Float32Array(dustN * 4);
for (let i = 0; i < dustN; i++) dustSeed.set([rnd(), rnd(), rnd(), rnd()], i * 4);
dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
const dust = new THREE.Points(dustGeo, new THREE.PointsMaterial({ map: dotTex, size: 2.2, transparent: true, depthWrite: false, opacity: 0.55, color: 0xd9b48a }));
dust.frustumCulled = false; scene.add(dust);
const embN = 260, embGeo = new THREE.BufferGeometry(), embPos = new Float32Array(embN * 3), embSeed = new Float32Array(embN * 3);
for (let i = 0; i < embN; i++) embSeed.set([rnd(), rnd(), rnd()], i * 3);
embGeo.setAttribute('position', new THREE.BufferAttribute(embPos, 3));
const embers = new THREE.Points(embGeo, new THREE.PointsMaterial({ map: dotTex, size: 0.5, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, color: 0xffa040, fog: false }));
embers.frustumCulled = false; scene.add(embers);
// nubes pintadas
const cloudTex = tex(SP.cloud(9)), clouds = [];
for (let k = 0; k < 14; k++) {
  const c = new THREE.Mesh(new THREE.PlaneGeometry(600, 300), new THREE.MeshBasicMaterial({ map: cloudTex, transparent: true, alphaTest: 0.1, fog: false, depthWrite: false }));
  const a = rnd() * 6.28, r = 2600 + rnd() * 800; c.position.set(Math.cos(a) * r, 600 + rnd() * 700, Math.sin(a) * r - 200); c.lookAt(0, 300, -200);
  clouds.push(c); scene.add(c);
}

// ---- flechas de mapa pintadas en el suelo (la maniobra explicada sobre el terreno)
function arrowShape(len, w) {
  const s = new THREE.Shape(); const hw = w / 2, hl = Math.min(len, w * 2.2);
  s.moveTo(0, -hw); s.lineTo(len - hl, -hw); s.lineTo(len - hl, -hw * 2.2); s.lineTo(len, 0); s.lineTo(len - hl, hw * 2.2); s.lineTo(len - hl, hw); s.lineTo(0, hw); s.lineTo(0, -hw);
  return s;
}
function mapArrow(color) {
  const g = new THREE.Group();
  const fill = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.85, depthWrite: false, fog: false, toneMapped: false }));
  const ink = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ color: 0x140f0f, transparent: true, opacity: 0.85, depthWrite: false, fog: false }));
  ink.renderOrder = 1; fill.renderOrder = 2; g.add(ink, fill); g.visible = false; scene.add(g);
  return { g, set(from, to, u, w) {
    const L = Math.hypot(to[0] - from[0], to[1] - from[1]) * u; if (L < 1) { g.visible = false; return; }
    g.visible = true;
    fill.geometry.dispose(); ink.geometry.dispose();
    fill.geometry = new THREE.ShapeGeometry(arrowShape(L, w)); ink.geometry = new THREE.ShapeGeometry(arrowShape(L + 3, w + 3)).translate(-1.5, 0, 0);
    g.position.set(from[0], 1.2, from[1]); g.rotation.set(-Math.PI / 2, 0, Math.atan2(-(to[1] - from[1]), to[0] - from[0]));
  }, fade(o) { fill.material.opacity = 0.85 * o; ink.material.opacity = 0.85 * o; } };
}
const arrowMac = mapArrow(0xff3a2a), arrowPer = mapArrow(0x4a8aff);
const gapGlow = new THREE.Mesh(new THREE.CircleGeometry(1, 48), new THREE.MeshBasicMaterial({ color: 0xffd040, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
gapGlow.rotation.x = -Math.PI / 2; scene.add(gapGlow);

// ------------------------------------------------------------------ la historia: dónde está cada cosa en el instante t
const GAP_X = 40;                                     // el centro del hueco que se abrirá
function macShift(t) {                                // desplazamiento oblicuo a la derecha
  const u = ease(prog(t, 'diagonal')) * 0.75 + ease(prog(t, 'hueco')) * 0.25;
  return { x: 120 * u, z: -30 * u, rot: 0.12 * u };
}
function macPos(x, z, t) {
  const s = macShift(t);
  const zz = z - (x + 175) * Math.sin(s.rot) * 0.6;    // ala derecha más adelantada (orden oblicuo)
  return [x + s.x, zz + s.z];
}
function persStretch(t) { return ease(prog(t, 'hueco')) * 0.85 + ease(prog(t, 'pasillos')) * 0.15; }
function persPos(x, z, t) {
  const g = persStretch(t);
  if (x > GAP_X - 20) return [x + g * (55 + (x - GAP_X) * 0.35), z + g * 8];
  return [x - g * 4, z];
}
function alexPos(t) {
  if (t < SC.cuna.a) {
    const drift = Math.min(t, SC.diagonal.a) * 1.6;   // al principio ya se va apartando (alejándose)
    const [x, z] = macPos(135, -9, t); return new THREE.Vector3(x + drift, 0, z - 2);
  }
  const P0 = alexPos(SC.cuna.a - 1e-3);
  const G = new THREE.Vector3(GAP_X, 0, -262), D = darPos(t).clone().add(new THREE.Vector3(30, 0, 18));
  const u = prog(t, 'cuna');
  if (t < SC.huida.a) {
    if (u < 0.55) return P0.clone().lerp(G, easeIn(u / 0.55) * 0.6 + (u / 0.55) * 0.4);
    return G.clone().lerp(D, ease((u - 0.55) / 0.45));
  }
  const E = darPos(SC.huida.a).clone().add(new THREE.Vector3(30, 0, 18));
  const v = prog(t, 'huida') * 0.35 + prog(t, 'final') * 0.05;
  return E.clone().lerp(new THREE.Vector3(-20, 0, -560), ease(v));
}
function darPos(t) {
  const base = new THREE.Vector3(-4, 0, -292);
  const u = prog(t, 'huida'), v = prog(t, 'final');
  const p = base.clone().add(new THREE.Vector3(-60 * easeIn(u) - 20 * v, 0, -320 * easeIn(u) - 90 * v));
  return p;
}
function chariotPos(i, t) {
  const [x0, z0, delay, lane] = CH[i];
  const u = clamp01((t - SC.pasillos.a - 0.15 * delay / 5.5) / ((SC.pasillos.b - SC.pasillos.a) * 0.95));
  const creep = prog(t, 'carros') * 6 + prog(t, 'diagonal') * 10 + prog(t, 'hueco') * 14;
  const laneX = macPos(LANES[lane], 0, t)[0];
  const x = lerp(x0 + creep * 0.4, laneX + (x0 - LANES[lane]), ease(Math.min(1, u * 2.2)));
  const zEnd = 60 + delay * 2;
  const z = lerp(z0 + creep, zEnd, u < 1 ? (u < 0.85 ? easeIn(u / 0.85) * 0.92 : 0.92 + (u - 0.85) / 0.15 * 0.08) : 1);
  return [x, z, u];
}

// ------------------------------------------------------------------ cámara: claves en el tiempo, curva continua (Catmull-Rom)
const V = (x, y, z) => new THREE.Vector3(x, y, z);
function camKeys() {
  const A = t => alexPos(t), D = t => darPos(t);
  const K = [];
  const k = (t, pos, tgt, fov = 50) => K.push({ t, pos, tgt, fov });
  let t;
  t = 0;                        k(t, A(t).add(V(-0.5, 3.0, 9)), A(t).add(V(-4, 1.0, -260)), 34);
  t = at('gancho', 0.55);        k(t, A(t).add(V(-1.6, 4.0, 13)), A(t).add(V(-8, 0.5, -260)), 38);
  t = at('gancho', 1);           k(t, A(t).add(V(-20, 9, 24)), V(-30, 2, -240), 52);
  t = at('macedonios', 0.35);    k(t, V(-20, 3.2, -22), V(-35, 2.2, 8), 46);
  t = at('macedonios', 1);       k(t, V(-120, 4.5, -26), V(-95, 2, 8), 48);
  t = at('persas', 0.3);         k(t, V(10, 4.5, -277), V(-4, 3.2, -292), 44);
  t = at('persas', 0.6);         k(t, V(10, 30, -205), V(-10, 0, -310), 52);
  t = at('persas', 1);           k(t, V(60, 120, -110), V(0, 0, -360), 56);
  t = at('carros', 0.45);        k(t, V(32, 2.4, -212), V(-10, 2.0, -234), 46);
  t = at('carros', 1);           k(t, V(-55, 3.2, -205), V(-20, 1.0, -235), 48);
  t = at('diagonal', 0.25);      k(t, V(40, 160, 110), V(30, 0, -140), 54);
  t = at('diagonal', 1);         k(t, V(120, 175, 100), V(80, 0, -160), 54);
  t = at('hueco', 1);            k(t, V(140, 130, -40), V(GAP_X + 20, 0, -270), 50);
  t = at('pasillos', 0.25);      k(t, V(-17, 2.4, 34), V(-28, 2.4, -60), 50);
  t = at('pasillos', 0.7);       k(t, V(-15, 2.8, 40), V(-28, 2.0, -20), 52);
  t = at('pasillos', 1);         k(t, V(-38, 6, 70), V(-30, 1.5, 40), 50);
  t = at('cuna', 0.25);          k(t, A(t).add(V(8.6, 6.4, 6.8)), A(t).add(V(-23, 0.0, -19)), 48);
  t = at('cuna', 0.7);           k(t, A(t).add(V(8.0, 6.4, 7.2)), A(t).add(V(-22, 0.0, -20)), 48);
  t = at('cuna', 1);             k(t, A(t).add(V(6.5, 6.6, 8)), D(t).add(V(0, 1.5, 0)), 44);
  t = at('huida', 0.6);          k(t, A(t).add(V(0.8, 7.5, 9.5)), D(t).add(V(0, 1.5, 0)), 38);
  t = at('huida', 1);            k(t, D(t).add(V(22, 8, 30)), D(t).add(V(0, 2.5, 0)), 42);
  t = at('final', 0.5);          k(t, D(t).add(V(13, 3.0, 17)), D(t).add(V(0, 2.8, 0)), 40);
  t = TL.total;                  k(t, D(t).add(V(8, 3.0, 11)), D(t).add(V(0, 3.0, 0)), 38);
  return K;
}
let KEYS = null;
function hermite(K, t, f) {
  let i = 0; while (i < K.length - 2 && t > K[i + 1].t) i++;
  const k0 = K[Math.max(0, i - 1)], k1 = K[i], k2 = K[i + 1], k3 = K[Math.min(K.length - 1, i + 2)];
  const dt = k2.t - k1.t, u = clamp01((t - k1.t) / dt);
  const m1 = f(k2).clone().sub(f(k0)).multiplyScalar(dt / Math.max(1e-3, k2.t - k0.t));
  const m2 = f(k3).clone().sub(f(k1)).multiplyScalar(dt / Math.max(1e-3, k3.t - k1.t));
  const seg = f(k2).distanceTo(f(k1));
  if (m1.length() > seg) m1.setLength(seg); if (m2.length() > seg) m2.setLength(seg);
  const u2 = u * u, u3 = u2 * u;
  return f(k1).clone().multiplyScalar(2 * u3 - 3 * u2 + 1).add(m1.multiplyScalar(u3 - 2 * u2 + u))
    .add(f(k2).clone().multiplyScalar(-2 * u3 + 3 * u2)).add(m2.multiplyScalar(u3 - u2));
}
function cameraAt(t) {
  const p = hermite(KEYS, t, k => k.pos), g = hermite(KEYS, t, k => k.tgt);
  const fv = hermite(KEYS, t, k => V(k.fov, 0, 0)).x;
  // carga y huida: cámara de seguimiento detrás y por encima de Alejandro (la carga es demasiado rápida para claves)
  const f0 = SC.cuna.a + 0.3, f1 = SC.huida.b - 0.2;
  const w = ease(clamp01((t - f0) / 0.9)) * ease(clamp01((f1 - t) / 0.9));
  if (w > 0) {
    const A = alexPos(t), dir = alexPos(t + 0.25).sub(alexPos(t - 0.25)); dir.y = 0;
    if (dir.length() < 0.5) dir.set(-0.3, 0, -1);
    dir.normalize();
    const side = V(-dir.z, 0, dir.x);
    const fp = A.clone().addScaledVector(dir, -10).addScaledVector(side, -3.5); fp.y = groundY(fp.x, fp.z) + 5.2;
    const look = A.clone().addScaledVector(dir, 28); look.y = 1.5;
    const dlook = darPos(t).add(V(0, 2.2, 0));
    look.lerp(dlook, clamp01((t - SC.cuna.a) / (SC.cuna.b - SC.cuna.a) * 1.4 - 0.5));
    p.lerp(fp, w); g.lerp(look, w);
  }
  // micro-movimiento de mano: la cámara nunca está quieta
  p.x += Math.sin(t * 1.3) * 0.12; p.y += Math.sin(t * 1.7 + 1) * 0.08;
  const minY = groundY(p.x, p.z) + 1.4; if (p.y < minY) p.y = minY;
  camera.position.copy(p); camera.lookAt(g); camera.fov = fv; camera.updateProjectionMatrix(); camera.updateMatrixWorld();
  return g;
}

// ------------------------------------------------------------------ fotograma
const dummy = new THREE.Matrix4();
window.renderAt = function (t) {
  if (!KEYS) KEYS = camKeys();
  const tgt = cameraAt(t);
  // luz
  const M = mood(t);
  sun.color.copy(M.sun); sun.intensity = M.si; hemi.color.copy(M.hs); hemi.groundColor.copy(M.gnd);
  scene.fog.color.copy(M.fog); skyMat.uniforms.top.value.copy(M.sky); skyMat.uniforms.hor.value.copy(M.hor);
  renderer.toneMappingExposure = M.exp; sky.position.copy(camera.position);
  for (const c of clouds) c.material.color.copy(M.hor).lerp(new THREE.Color(1, 1, 1), 0.45).multiplyScalar(lerp(1, 0.35, prog(t, 'final')));
  const dist = camera.position.distanceTo(tgt), sz = clamp(dist * 0.9, 40, 520);
  sun.position.copy(tgt).addScaledVector(M.dir, 600); sun.target.position.copy(tgt);
  Object.assign(sun.shadow.camera, { left: -sz, right: sz, top: sz, bottom: -sz, near: 1, far: 1600 }); sun.shadow.camera.updateProjectionMatrix();
  scene.fog.near = lerp(300, 120, prog(t, 'final')); scene.fog.far = lerp(3200, 900, prog(t, 'final'));

  // macedonios (con pasillos que se abren para los carros)
  const lanesOpen = clamp01(prog(t, 'pasillos') * 3) * (1 - clamp01((t - SC.cuna.a) / 3));
  PH.forEach(([x, z], i) => {
    let xx = x;
    if (lanesOpen > 0) for (const L of LANES) { const d = x - L; if (Math.abs(d) < 3.4 && x < 92) xx = L + Math.sign(d || 1) * (3.4 + Math.abs(d) * 0.4) * lanesOpen + d * (1 - lanesOpen); }
    const [px, pz] = macPos(xx, z, t); phal.pos.set([px, groundY(px, pz), pz], i * 3);
  });
  phal.update(0.05, 2, t);
  // compañeros: bloque → cuña detrás de Alejandro
  const A = alexPos(t), wedgeU = ease(clamp01(prog(t, 'cuna') * 3)), charging = t > SC.cuna.a && t < SC.final.a;
  const dirA = alexPos(t + 0.1).sub(A); const moving = dirA.length() > 0.02;
  const ang = moving ? Math.atan2(dirA.x, dirA.z) : Math.PI;
  const fl = moving ? flipFor(dirA.x, dirA.z) : 1;
  let ci = 0;
  for (const cr of [compA, compB]) {
    for (let i = 0; i < cr.n; i++, ci++) {
      const [x, z] = COMP[ci]; let [px, pz] = macPos(x, z, t);
      px += Math.min(t, SC.diagonal.a) * 1.6;
      if (wedgeU > 0) {
        const r = Math.floor(Math.sqrt(ci)), c = ci - r * r - r;            // fila r tiene 2r+1 jinetes
        const lx = c * 3.0, lz = (r + 1) * 3.6;
        const wx = A.x + lx * Math.cos(ang) + lz * Math.sin(ang), wz = A.z - lx * Math.sin(ang) + lz * Math.cos(ang);
        px = lerp(px, wx, wedgeU); pz = lerp(pz, wz, wedgeU);
      }
      cr.pos.set([px, groundY(px, pz), pz], i * 3); cr.flip[i] = charging ? fl : 1;
    }
    cr.setFrame(Math.floor(t * (charging ? 9 : 2)));
    cr.update(charging ? 0.35 : 0.04, charging ? 9 : 2, t);
  }
  // persas
  for (const cr of pers) { cr.list.forEach(([x, z], i) => { const [px, pz] = persPos(x, z, t); cr.pos.set([px, groundY(px, pz), pz], i * 3); }); cr.update(0.06, 2.5, t); }
  // carros + ruedas que giran
  const cFl = flipFor(0, 1);
  CH.forEach((c, i) => {
    const [x, z, u] = chariotPos(i, t); chariots.pos.set([x, groundY(x, z), z], i * 3);
    const spd = (u > 0 && u < 1) ? 1 : 0.05;
    chariots.flip[i] = (u > 0 && u < 1) ? cFl : 1;
    const yaw = Math.atan2(camera.position.x - x, camera.position.z - z);
    const q = new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), yaw);
    const off = V(chariots.flip[i] * 1.55, 0.9, 0.05).applyQuaternion(q);
    const spin = new THREE.Quaternion().setFromAxisAngle(V(0, 0, 1), -t * 14 * spd * chariots.flip[i] + i);
    dummy.compose(V(x, groundY(x, z), z).add(off), q.clone().multiply(spin), V(1, 1, 1)); wheels.setMatrixAt(i, dummy);
  });
  chariots.setFrame(Math.floor(t * 8)); chariots.update(t > SC.pasillos.a ? 0.25 : 0.02, 10, t); wheels.instanceMatrix.needsUpdate = true;
  EL.forEach(([x, z], i) => { const [px, pz] = persPos(x, z, t); eleph.pos.set([px, groundY(px, pz), pz], i * 3); }); eleph.update(0.05, 1.5, t);
  // Alejandro y Darío
  alex.flip = moving ? fl : 1; alex.place(A, t, charging ? 0.35 : 0.05, charging ? 9 : 2);
  const Dp = darPos(t), dv = darPos(t + 0.1).sub(Dp); const fleeing = dv.length() > 0.02;
  dar.flip = fleeing ? flipFor(dv.x, dv.z) : 1; dar.place(Dp, t, fleeing ? 0.25 : 0.03, fleeing ? 8 : 1.5);
  // conspiradores: aparecen alrededor de Darío al final, avanzando con sombras largas
  const cu = prog(t, 'final');
  camRight.setFromMatrixColumn(camera.matrixWorld, 0); camRight.y = 0; camRight.normalize();
  const back = V(-camRight.z, 0, camRight.x);                         // hacia el fondo, lejos de la cámara
  for (let i = 0; i < CONS.n; i++) {
    const side = (i % 2 ? 1 : -1) * (1 + (i >> 1) * 0.55), r = lerp(26, 5.5, ease(clamp01(cu * 1.25)));
    const p = Dp.clone().addScaledVector(camRight, side * r).addScaledVector(back, 2 + (i >> 1) * 2.5);
    CONS.pos.set([p.x, groundY(p.x, p.z) + (cu > 0 ? 0 : -50), p.z], i * 3);
  }
  CONS.update(0.04, 3, t);
  // estandartes, flechas ardiendo, humo, polvo, brasas
  waveFlags(t);
  const war = clamp01((t - SC.carros.a) / 4);
  ARR.forEach(([x, z, r], i) => {
    const vis = war > r / 6 ? 1 : 0; const fl2 = 0.8 + 0.3 * Math.sin(t * 23 + r * 9) + 0.15 * Math.sin(t * 41 + r);
    dummy.compose(V(x, groundY(x, z) + 1.0, z), camera.quaternion, V(fl2 * vis, fl2 * vis, 1)); flames.setMatrixAt(i, dummy);
  });
  flames.instanceMatrix.needsUpdate = true; arrows.visible = war > 0;
  SMK.forEach(([x, z, ph, s], i) => {
    const life = ((t * 0.08 + ph / 20) % 1);
    const sc = s * (0.6 + life) * clamp01((t - SC.pasillos.a) / 2);
    dummy.compose(V(x + life * 12, groundY(x, z) + 2 + life * 30, z), camera.quaternion, V(sc, sc, 1)); smoke.setMatrixAt(i, dummy);
  });
  smoke.instanceMatrix.needsUpdate = true;
  smoke.material.color.copy(M.fog).lerp(new THREE.Color(0x5a4a44), 0.5);
  // polvo alrededor de lo que se mueve (carros y caballería)
  for (let i = 0; i < dustN; i++) {
    const [a, b, c, d] = [dustSeed[i * 4], dustSeed[i * 4 + 1], dustSeed[i * 4 + 2], dustSeed[i * 4 + 3]];
    const src = i % 3 === 0 ? A : (() => { const k = (i * 7) % CH.length; const [x, z] = chariotPos(k, t); return V(x, 0, z); })();
    const life = (t * 0.6 + d) % 1;
    dustPos.set([src.x + (a - 0.5) * 14 + life * 4, groundY(src.x, src.z) + 0.3 + life * 3.5 * b, src.z + (c - 0.5) * 14 + life * 6], i * 3);
  }
  dustGeo.attributes.position.needsUpdate = true;
  dust.material.opacity = 0.15 + 0.5 * clamp01(war) * (t < SC.final.a ? 1 : 0.2);
  for (let i = 0; i < embN; i++) {
    const [a, b, c] = [embSeed[i * 3], embSeed[i * 3 + 1], embSeed[i * 3 + 2]];
    const life = (t * (0.15 + 0.2 * c) + a) % 1;
    embPos.set([camera.position.x + (a - 0.5) * 40 + Math.sin(t + b * 9) * 3, groundY(camera.position.x, camera.position.z) + life * 12, camera.position.z - 5 - b * 40], i * 3);
  }
  embGeo.attributes.position.needsUpdate = true;
  embers.material.opacity = 0.8 * clamp01((t - SC.pasillos.a) / 2) * (t < SC.final.a + 1.5 ? 1 : 0.3);
  // flechas de mapa y el hueco
  const ud = prog(t, 'diagonal'), uh = prog(t, 'hueco');
  const mapFade = clamp01(ud * 5) * (1 - clamp01((t - SC.pasillos.a) / 1.0));
  arrowMac.set([-40, -40], [190, -110], ease(clamp01(ud * 1.4)), 14); arrowMac.fade(mapFade);
  arrowPer.set([150, -330], [330, -330], ease(clamp01(uh * 1.6)), 12); arrowPer.fade(mapFade);
  gapGlow.position.set(GAP_X, 0.8, -300); gapGlow.scale.setScalar(lerp(5, 34, ease(uh)) * (1 + 0.06 * Math.sin(t * 6)));
  gapGlow.material.opacity = 0.55 * ease(clamp01(uh * 2 - 0.4)) * (1 - clamp01((t - SC.cuna.a - 2) / 1.5));

  renderer.render(scene, camera);
  return true;
};
window.grab = (q = 0.93) => renderer.domElement.toDataURL('image/jpeg', q);
window.READY = true;
