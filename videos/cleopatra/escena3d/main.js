// Cleopatra y el camino del tiempo: personajes 2D (recortes dibujados con código) en un mundo 3D real, con sombras.
// Misma técnica que Gaugamela y Troya: cámara continua sin cortes, luz que sigue a la historia, contorno de tinta.
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
  golden:  { sun: 0xffb060, si: 2.8, sky: 0x3a5aa8, hor: 0xff9a5a, gnd: 0x6a4436, hs: 0xffc890, fog: 0xe0a070, exp: 1.05, dir: [-0.6, 0.3, 0.7] },
  day:     { sun: 0xfff0d0, si: 3.1, sky: 0x2f7ae0, hor: 0xf0dcb8, gnd: 0x8a6a48, hs: 0xdce8ff, fog: 0xead8b8, exp: 1.0,  dir: [-0.5, 0.65, 0.58] },
  dusk:    { sun: 0xd0c4ff, si: 2.1, sky: 0x1a2a66, hor: 0x8a7ac0, gnd: 0x3a2c38, hs: 0x7a8ad8, fog: 0x5a5a98, exp: 1.0,  dir: [0.5, 0.6, 0.62] },
  arctic:  { sun: 0xe8f0ff, si: 2.6, sky: 0x5a8ad0, hor: 0xe0ecf8, gnd: 0x8a98a8, hs: 0xe8f0ff, fog: 0xdce6f2, exp: 1.05, dir: [0.4, 0.4, 0.82] },
  violet:  { sun: 0xff9ab0, si: 2.1, sky: 0x1e1a50, hor: 0xd8708a, gnd: 0x3a2838, hs: 0x9a80c8, fog: 0x7a5080, exp: 1.02, dir: [-0.7, 0.2, 0.68] },
};
const MOOD_KEYS = [
  [0, 'golden'], [at('gancho', 1) - 0.2, 'golden'], [at('piramide', 0.3), 'day'], [at('viaje2', 1), 'day'],
  [at('mapa', 0.2), 'dusk'], [at('mapa', 1) - 0.3, 'dusk'], [at('tut', 0.3), 'day'], [at('turistas', 1), 'day'],
  [at('alejandro', 0.3), 'golden'], [at('plutarco', 1) - 0.3, 'golden'], [at('mamuts', 0.15), 'arctic'], [at('mamuts', 1) - 0.3, 'arctic'],
  [at('final', 0.25), 'violet'], [TL.total + 1, 'violet'],
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

// ------------------------------------------------------------------ el camino del tiempo: 1 año = 20 cm
const YEAR = y => (y + 2560) * 0.2;                      // la Gran Pirámide en x = 0
const X_TUT = YEAR(-1330), X_ALEX = YEAR(-332), X_CLEO = YEAR(-50), X_PHONE = YEAR(2007);
const NILE_Z0 = -175, NILE_Z1 = -140, ISLE = V(70, 0, 175);
function noise2(x, z) { return Math.sin(x * 0.013 + Math.sin(z * 0.011) * 2) * 0.5 + Math.sin(z * 0.017 + x * 0.004) * 0.35 + Math.sin((x + z) * 0.041) * 0.15; }
function groundY(x, z) {
  let y = (noise2(x * 0.7, z * 0.9) * 3.5 + Math.sin(x * 0.02) * Math.cos(z * 0.025) * 2.5) * clamp01((Math.abs(z) - 18) / 40);   // dunas lejos del camino
  const nz = clamp01(1 - Math.abs(z - (NILE_Z0 + NILE_Z1) / 2) / 30); y -= nz * 4;                                             // cauce del Nilo
  const di = Math.hypot(x - ISLE.x, z - ISLE.z); if (di < 75) y = lerp(y, -3, clamp01((75 - di) / 12));                         // laguna de la isla
  const far = Math.hypot(x - 450, z); y += Math.max(0, far - 1100) * 0.08 * (1 + noise2(z, x));
  return y;
}
const GROUND = 5200, GSEG = 360;
const gGeo = new THREE.PlaneGeometry(GROUND, GROUND, GSEG, GSEG); gGeo.rotateX(-Math.PI / 2); gGeo.translate(450, 0, 0);
const gPos = gGeo.attributes.position, gCol = new Float32Array(gPos.count * 3);
for (let i = 0; i < gPos.count; i++) {
  const x = gPos.getX(i), z = gPos.getZ(i); gPos.setY(i, groundY(x, z));
  const n = noise2(x * 3.1, z * 2.7) * 0.5 + 0.5;
  let c = [0.93 + 0.05 * n, 0.76 + 0.06 * n, 0.5 + 0.05 * n];                              // arena dorada
  const green = clamp01(1 - (Math.abs(z - (NILE_Z0 + NILE_Z1) / 2) - 14) / 26);            // vega verde del Nilo
  c = c.map((v, k) => lerp(v, [0.42, 0.62, 0.3][k], green * 0.85));
  gCol.set(c, i * 3);
}
gGeo.setAttribute('color', new THREE.BufferAttribute(gCol, 3)); gGeo.computeVertexNormals();
const detail = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  g.fillStyle = '#e0d4c0'; g.fillRect(0, 0, 256, 256);
  for (let k = 0; k < 2200; k++) { const v = 170 + rnd() * 85 | 0; g.fillStyle = `rgb(${v},${v - 8},${v - 24})`; g.fillRect(rnd() * 256, rnd() * 256, 1 + rnd() * 2, 1 + rnd() * 2); }
  for (let k = 0; k < 14; k++) { g.strokeStyle = 'rgba(150,100,50,0.18)'; g.lineWidth = 2; g.beginPath(); const y = rnd() * 256; g.moveTo(0, y); g.bezierCurveTo(80, y - 10, 170, y + 10, 256, y); g.stroke(); }   // ondas de arena
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(GROUND / 9, GROUND / 9);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
})();
const ground = new THREE.Mesh(gGeo, new THREE.MeshLambertMaterial({ vertexColors: true, map: detail })); ground.receiveShadow = true; scene.add(ground);
// el Nilo
const nile = new THREE.Mesh(new THREE.PlaneGeometry(GROUND, NILE_Z1 - NILE_Z0 + 10, 200, 4).rotateX(-Math.PI / 2).translate(450, -2.2, (NILE_Z0 + NILE_Z1) / 2), toon(0x2a8ac8));
nile.receiveShadow = true; scene.add(nile);
// la laguna helada con la isla de los mamuts
const lagoon = new THREE.Mesh(new THREE.CircleGeometry(72, 48).rotateX(-Math.PI / 2), toon(0x5aa8d8)); lagoon.position.set(ISLE.x, -1.6, ISLE.z); scene.add(lagoon);
const isle = inked(new THREE.CylinderGeometry(34, 44, 5, 12).translate(0, 1, 0), toon(0xf4f8ff, { flatShading: true }), 1.03); isle.position.set(ISLE.x, -2, ISLE.z); scene.add(isle);
for (let k = 0; k < 4; k++) { const f = inked(new THREE.ConeGeometry(10 + k * 3, 14 + k * 4, 6).translate(0, 7, 0), toon(0xe8f0ff, { flatShading: true }), 1.04); f.position.set(ISLE.x - 20 + k * 13, 2, ISLE.z - 25 + (k % 2) * 8); scene.add(f); }
// montañas lejanas
for (let k = 0; k < 30; k++) {
  const a = (k / 30) * Math.PI * 2 + rnd() * 0.15, r = 2600 + rnd() * 700;
  const h = 140 + rnd() * 240, w = 420 + rnd() * 500, seg = 6 + (rnd() * 3 | 0), rot = rnd() * 6;
  const geo = new THREE.ConeGeometry(w, h, seg, 1); geo.translate(0, h / 2, 0);
  const m = inked(geo, toon(0xb08a78, { flatShading: true }), 1.01);
  m.scale.set(1 + rnd() * 0.6, 1, 0.7 + rnd() * 0.4); m.position.set(450 + Math.cos(a) * r, -30, Math.sin(a) * r); m.rotation.y = rot; scene.add(m);
}
// ---- el camino del tiempo: losas, un mojón cada 100 años y un obelisco cada 500
const STONE = toon(0xe8d2a0), STONE2 = toon(0xd4b880), GOLD = toon(0xf0c040), DARK = toon(0x1c1c22);
const road = inked(new THREE.BoxGeometry(1060, 0.6, 10).translate(450, 0, 0), STONE2, 1.002); road.position.y = 0.05; scene.add(road);
for (let x = -40; x <= 1000; x += 20) for (const z of [-6.5, 6.5]) {
  const big = Math.round(x / 20) % 5 === 0;
  const m = big ? inked(new THREE.ConeGeometry(1.1, 9, 4).translate(0, 4.5, 0), STONE, 1.08) : inked(new THREE.BoxGeometry(0.9, 1.4, 0.9).translate(0, 0.7, 0), STONE, 1.08);
  if (big) { const cap = new THREE.Mesh(new THREE.ConeGeometry(0.5, 1.2, 4).translate(0, 9.1, 0), GOLD); m.add(cap); }
  m.position.set(x, 0, z); m.rotation.y = Math.PI / 4; scene.add(m);
}
// ---- Guiza: tres pirámides (la grande con piramidión de oro)
function pyramid(base, h, x, z, gold = false) {
  const g = new THREE.Group();
  const p = inked(new THREE.ConeGeometry(base / Math.SQRT2, h, 4, 1).rotateY(Math.PI / 4).translate(0, h / 2, 0), toon(0xe8cf9a, { flatShading: true }), 1.01);
  g.add(p);
  if (gold) { const c = inked(new THREE.ConeGeometry(base / Math.SQRT2 * 0.06, h * 0.06, 4).rotateY(Math.PI / 4).translate(0, h * 0.97, 0), GOLD, 1.06); g.add(c); }
  g.position.set(x, groundY(x, z) - 0.5, z); scene.add(g); return g;
}
const greatP = pyramid(84, 54, 0, -80, true); pyramid(74, 48, -80, -120); pyramid(40, 26, -140, -150);
// ---- santuario de Tutankamón, terraza del palacio de Cleopatra
function colonnade(x, z, n, w, h, color) {
  const g = new THREE.Group();
  for (let k = 0; k < n; k++) { const c = inked(new THREE.CylinderGeometry(0.7, 0.8, h, 10).translate(0, h / 2, 0), toon(color), 1.07); c.position.set(-w / 2 + (k * w) / (n - 1), 0, 0); g.add(c); }
  const roof = inked(new THREE.BoxGeometry(w + 3, 1.4, 5).translate(0, h + 0.7, 0), STONE, 1.03); g.add(roof);
  g.position.set(x, 0, z); scene.add(g); return g;
}
colonnade(X_TUT, -12, 5, 16, 9, 0xd85a3a);
const palace = colonnade(X_CLEO + 2, -14, 6, 22, 11, 0x3a8ac8);
const terrace = inked(new THREE.BoxGeometry(30, 1, 14), STONE, 1.02); terrace.position.set(X_CLEO + 2, 0.5, -12); scene.add(terrace);
// ---- el iPhone gigante clavado en la arena
const phoneScreen = (() => {
  const c = document.createElement('canvas'); c.width = 512; c.height = 1024; const g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 512, 1024); gr.addColorStop(0, '#ff7a3a'); gr.addColorStop(0.5, '#c83a8a'); gr.addColorStop(1, '#3a3ad8');
  g.fillStyle = gr; g.fillRect(0, 0, 512, 1024);
  for (let r = 0; r < 5; r++) for (let k = 0; k < 4; k++) { g.fillStyle = `hsl(${(r * 4 + k) * 37 % 360},70%,${55 + (k % 2) * 10}%)`; g.beginPath(); g.roundRect(48 + k * 110, 220 + r * 120, 84, 84, 20); g.fill(); }
  g.fillStyle = '#111'; g.beginPath(); g.roundRect(196, 28, 120, 30, 15); g.fill();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
})();
const phone = new THREE.Group();
const body = inked(new THREE.BoxGeometry(14, 28, 1.6), DARK, 1.03); phone.add(body);
const screenM = new THREE.Mesh(new THREE.PlaneGeometry(12.6, 26.4), new THREE.MeshBasicMaterial({ map: phoneScreen, toneMapped: false })); screenM.position.z = 0.82; phone.add(screenM);
phone.position.set(X_PHONE, 15.5, 0); phone.rotation.set(-0.08, -Math.PI / 2 + 0.2, 0.05); scene.add(phone);
const phoneLight = new THREE.PointLight(0xff8ad0, 600, 120, 1.4); phoneLight.position.set(X_PHONE - 12, 16, 0); scene.add(phoneLight);

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

// ---- personajes
const cleo = new Hero([SP.cleopatra(0), SP.cleopatra(1)], 1.4, 2.8);
const tut = new Hero([SP.tutankhamun()], 1.35, 2.7);
const alex = new Hero([0, 1].map(f => SP.rider({ frame: f, coat: '#18161a', mane: '#050505', cloak: '#d8202a', helmet: '#f0c43a', plume: '#ffffff', star: true, gold: true })), 4.6, 4.6);
const MACS = []; for (let k = 0; k < 40; k++) MACS.push([X_ALEX - 6 - (k % 8) * 2.2, -12 + Math.floor(k / 8) * 2.4 + (rnd() - 0.5)]);
const macs = new Crowd([SP.phalangite()], 1.15, 2.3, MACS.length, () => new THREE.Color().setScalar(0.85 + rnd() * 0.15));
const NW = 10;                                                        // obreros arrastrando un bloque hacia la pirámide
const workersA = new Crowd([SP.worker(0), SP.worker(1)], 1.3, 2.6, NW / 2), workersB = new Crowd([SP.worker(1), SP.worker(0)], 1.3, 2.6, NW / 2);
const block = inked(new THREE.BoxGeometry(2.6, 1.6, 1.8).translate(0, 1.1, 0), STONE, 1.05); scene.add(block);
const sled = inked(new THREE.BoxGeometry(3.2, 0.3, 2.2).translate(0, 0.15, 0), toon(0x7a4a22), 1.05); block.add(sled);
const TOUR = [['#f2ead2', '#2a5ab8'], ['#e8d0a0', '#b02a2a'], ['#f6f0e6', '#7a2a8a'], ['#d8e0f0', '#c8862a'], ['#f2ead2', '#3a8a3a'], ['#efe2c8', '#b02a2a']];
const tourists = TOUR.map(([a, b]) => new Hero([SP.tourist(a, b)], 1.2, 2.4));
const MAM = [0, 1, 2].map(k => new Hero([SP.mammoth(0), SP.mammoth(1)], 7, 5.7));
const PALMS = []; for (let k = 0; k < 140; k++) { const x = -300 + rnd() * 1500, z = (rnd() < 0.5 ? NILE_Z0 - 8 - rnd() * 22 : NILE_Z1 + 6 + rnd() * 18); PALMS.push([x, z]); }
const palms = new Crowd([SP.palm()], 4.5, 9, PALMS.length, () => new THREE.Color().setScalar(0.8 + rnd() * 0.2));
PALMS.forEach(([x, z], i) => { palms.pos.set([x, groundY(x, z), z], i * 3); palms.scl[i] = 0.8 + rnd() * 0.5; });
// nieve sobre la isla
const snowN = 700, snowGeo = new THREE.BufferGeometry(), snowPos = new Float32Array(snowN * 3), snowSeed = new Float32Array(snowN * 3);
for (let i = 0; i < snowN; i++) snowSeed.set([rnd(), rnd(), rnd()], i * 3);
snowGeo.setAttribute('position', new THREE.BufferAttribute(snowPos, 3));
const dotTex = tex(SP.softDot());
const snow = new THREE.Points(snowGeo, new THREE.PointsMaterial({ map: dotTex, size: 0.9, transparent: true, depthWrite: false, color: 0xffffff }));
snow.frustumCulled = false; scene.add(snow);
// arena que vuela con el viento
const sandN = 900, sandGeo = new THREE.BufferGeometry(), sandPos = new Float32Array(sandN * 3), sandSeed = new Float32Array(sandN * 3);
for (let i = 0; i < sandN; i++) sandSeed.set([rnd(), rnd(), rnd()], i * 3);
sandGeo.setAttribute('position', new THREE.BufferAttribute(sandPos, 3));
const sand = new THREE.Points(sandGeo, new THREE.PointsMaterial({ map: dotTex, size: 0.35, transparent: true, depthWrite: false, opacity: 0.6, color: 0xf0d8a8 }));
sand.frustumCulled = false; scene.add(sand);
const cloudTex = tex(SP.cloud(9)), clouds = [];
for (let k = 0; k < 16; k++) {
  const c = new THREE.Mesh(new THREE.PlaneGeometry(600, 300), new THREE.MeshBasicMaterial({ map: cloudTex, transparent: true, alphaTest: 0.1, fog: false, depthWrite: false }));
  const a = rnd() * 6.28, r = 3200 + rnd() * 900; c.position.set(450 + Math.cos(a) * r, 650 + rnd() * 700, Math.sin(a) * r); c.lookAt(450, 300, 0);
  clouds.push(c); scene.add(c);
}

// ------------------------------------------------------------------ cámara
function camKeys() {
  const K = []; const k = (t, pos, tgt, fov = 50) => K.push({ t, pos, tgt, fov });
  const C = X_CLEO; let t;
  t = 0;                         k(t, V(C + 6.5, 2.4, 11), V(C + 9, 2.3, 4), 40);
  t = at('gancho', 0.38);         k(t, V(C + 5.5, 2.7, 12.5), V(C + 9, 2.3, 4), 40);
  t = at('gancho', 0.62);         k(t, V(C + 3, 3.6, 16), V(C + 40, 5, 2), 36);
  t = at('gancho', 1);            k(t, V(C - 14, 12, 22), V(X_PHONE, 15, 0), 30);
  t = at('piramide', 0.35);       k(t, V(62, 3.2, 14), V(8, 16, -70), 48);
  t = at('piramide', 1);          k(t, V(42, 26, 46), V(0, 24, -80), 50);
  t = at('viaje1', 0.2);          k(t, V(60, 13, 18), V(260, 6, 0), 46);
  t = at('viaje1', 1);            k(t, V(C - 30, 8, 18), V(C + 9, 3, 4), 46);
  t = at('viaje2', 0.3);          k(t, V(C + 70, 10, 16), V(X_PHONE, 12, 0), 44);
  t = at('viaje2', 1);            k(t, V(X_PHONE - 42, 9, 28), V(X_PHONE, 15, 0), 46);
  t = at('mapa', 0.3);            k(t, V(1020, 210, 110), V(430, 0, 0), 50);
  t = at('mapa', 1);              k(t, V(990, 250, 50), V(380, 0, -20), 50);
  t = at('tut', 0.4);             k(t, V(X_TUT + 13, 3.6, 15), V(X_TUT, 2.6, 4), 42);
  t = at('tut', 1);               k(t, V(X_TUT - 10, 4.5, 18), V(X_TUT, 3, 2), 44);
  t = at('turistas', 0.25);       k(t, V(48, 4, 10), V(16, 4, -32), 46);
  t = at('turistas', 0.7);        k(t, V(30, 3, 2), V(8, 10, -60), 50);
  t = at('turistas', 1);          k(t, V(10, 14, 26), V(0, 22, -80), 50);
  t = at('alejandro', 0.4);       k(t, V(X_ALEX + 13, 3.8, 14), V(X_ALEX + 3, 3, 0), 44);
  t = at('alejandro', 0.75);      k(t, V(X_ALEX + 22, 3.8, 14), V(X_ALEX + 11, 3, 0), 44);
  t = at('alejandro', 1);         k(t, V(C - 14, 4, 15), V(C + 9, 2.6, 4), 44);
  t = at('plutarco', 0.5);        k(t, V(C + 5.5, 2.3, 10.5), V(C + 9, 2.4, 4), 40);
  t = at('plutarco', 1);          k(t, V(C + 12.5, 2.6, 11), V(C + 9, 2.4, 4), 40);
  t = at('mamuts', 0.4);          k(t, V(ISLE.x + 34, 9, ISLE.z + 52), V(ISLE.x, 3, ISLE.z), 46);
  t = at('mamuts', 1);            k(t, V(ISLE.x - 18, 11, ISLE.z + 58), V(ISLE.x, 3, ISLE.z), 46);
  t = at('final', 0.45);          k(t, V(-45, 55, 70), V(460, 0, 0), 48);
  t = TL.total;                   k(t, V(-70, 85, 55), V(460, 0, 0), 46);
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
  const M = mood(t);
  sun.color.copy(M.sun); sun.intensity = M.si; hemi.color.copy(M.hs); hemi.groundColor.copy(M.gnd);
  scene.fog.color.copy(M.fog); skyMat.uniforms.top.value.copy(M.sky); skyMat.uniforms.hor.value.copy(M.hor);
  skyMat.uniforms.stars.value = 0.6 * clamp01((t - SC.final.a) / 3);
  renderer.toneMappingExposure = M.exp; sky.position.copy(camera.position);
  for (const c of clouds) c.material.color.copy(M.hor).lerp(new THREE.Color(1, 1, 1), 0.45);
  const dist = camera.position.distanceTo(tgt), sz = clamp(dist * 0.9, 40, 600);
  sun.position.copy(tgt).addScaledVector(M.dir, 800); sun.target.position.copy(tgt);
  Object.assign(sun.shadow.camera, { left: -sz, right: sz, top: sz, bottom: -sz, near: 1, far: 2000 }); sun.shadow.camera.updateProjectionMatrix();
  phoneLight.intensity = 600 + 200 * Math.sin(t * 2);
  phone.position.y = 15.5 + Math.sin(t * 1.1) * 0.3;

  // personajes
  cleo.setTex(Math.floor(t * 1.5) % 2); cleo.place(V(X_CLEO + 9, 0, 4), t, 0.02);
  tut.place(V(X_TUT, 0, 2), t, 0.02);
  const charge = ease(clamp01((t - SC.alejandro.a) / (SC.alejandro.b - SC.alejandro.a)));
  const A = V(X_ALEX + charge * 14, 0, 0); const moving = t > SC.alejandro.a && t < SC.alejandro.b;
  alex.flip = flipFor(1, 0); alex.setTex(moving ? Math.floor(t * 8) % 2 : 0); alex.place(A, t, moving ? 0.25 : 0.03);
  MACS.forEach(([x, z], i) => { const xx = x + charge * 14; macs.pos.set([xx, groundY(xx, z), z], i * 3); }); macs.update(0.05, 2, t);
  // obreros: avanzan muy despacio arrastrando el bloque hacia la pirámide
  const pull = (t % 30) * 0.45;
  const B = V(46 - pull * 0.55, 0, -20 - pull * 0.35); block.position.set(B.x, groundY(B.x, B.z), B.z); block.rotation.y = 0.55;
  const dirW = V(-0.84, 0, -0.54);
  let wi = 0;
  for (const cr of [workersA, workersB]) {
    for (let i = 0; i < cr.n; i++, wi++) {
      const row = Math.floor(wi / 2), side = wi % 2 ? 1.2 : -1.2;
      const p = B.clone().addScaledVector(dirW, 4 + row * 2.2).add(V(dirW.z * side, 0, -dirW.x * side));
      cr.pos.set([p.x, groundY(p.x, p.z), p.z], i * 3); cr.flip[i] = flipFor(dirW.x, dirW.z);
    }
    cr.setFrame(Math.floor(t * 4)); cr.update(0.06, 8, t);
  }
  // turistas en la pirámide (solo en su escena)
  const tOn = t > SC.turistas.a - 0.5 && t < SC.alejandro.a + 0.5;
  tourists.forEach((h, i) => { const a = i / tourists.length * 2.2 - 1.1; h.place(tOn ? V(18 + Math.sin(a) * 14, 0, -34 + Math.cos(a) * 6 + (i % 2) * 3) : V(0, -100, 0), t, 0.02); });
  // mamuts
  MAM.forEach((h, i) => {
    const a = t * 0.08 + i * 2.1, p = V(ISLE.x + Math.cos(a) * (14 + i * 4), 3.2, ISLE.z + Math.sin(a) * (10 + i * 3));
    h.flip = flipFor(-Math.sin(a), Math.cos(a)); h.setTex(Math.floor(t * 2 + i) % 2);
    h.mesh.position.set(p.x, p.y, p.z); h.mesh.rotation.y = Math.atan2(camera.position.x - p.x, camera.position.z - p.z); h.mesh.scale.x = h.flip;
  });
  palms.update(0, 0, t);
  for (let i = 0; i < snowN; i++) { const [a, b, c] = [snowSeed[i * 3], snowSeed[i * 3 + 1], snowSeed[i * 3 + 2]]; const life = (t * (0.05 + 0.05 * c) + a) % 1;
    snowPos.set([ISLE.x + (b - 0.5) * 90 + Math.sin(t + a * 9) * 2, 30 - life * 32, ISLE.z + (c - 0.5) * 90], i * 3); }
  snowGeo.attributes.position.needsUpdate = true;
  for (let i = 0; i < sandN; i++) { const [a, b, c] = [sandSeed[i * 3], sandSeed[i * 3 + 1], sandSeed[i * 3 + 2]]; const life = (t * (0.3 + 0.3 * c) + a) % 1;
    sandPos.set([camera.position.x - 40 + life * 80, groundY(camera.position.x, camera.position.z) + 0.3 + b * 3, camera.position.z - 6 - c * 40], i * 3); }
  sandGeo.attributes.position.needsUpdate = true;
  sand.material.opacity = 0.5 * (1 - clamp01((camera.position.y - 20) / 20));

  renderer.render(scene, camera);
  return true;
};
window.grab = (q = 0.93) => renderer.domElement.toDataURL('image/jpeg', q);
window.READY = true;
