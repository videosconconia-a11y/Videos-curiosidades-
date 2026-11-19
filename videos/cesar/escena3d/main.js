// Julio César y los piratas: personajes 2D (recortes dibujados con código) en un mundo 3D real, con sombras.
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
  night:  { sun: 0x8fb0ff, si: 1.3, sky: 0x050a1e, hor: 0x1e2c5a, gnd: 0x0a0c18, hs: 0x4a5fa8, fog: 0x141c3a, exp: 1.05, dir: [0.35, 0.5, -0.8] },
  day:    { sun: 0xfff0d8, si: 3.0, sky: 0x1f6ae0, hor: 0xbfe0f4, gnd: 0x7a6a50, hs: 0xdce8ff, fog: 0xc8e0f0, exp: 1.0,  dir: [-0.45, 0.65, 0.6] },
  golden: { sun: 0xffc070, si: 2.9, sky: 0x3a6ac0, hor: 0xffc08a, gnd: 0x6a5040, hs: 0xffd8b0, fog: 0xe0b890, exp: 1.04, dir: [-0.6, 0.35, 0.7] },
  violet: { sun: 0xff8a70, si: 2.2, sky: 0x2a1a50, hor: 0xff7a5a, gnd: 0x3a2838, hs: 0xb080c0, fog: 0x8a5070, exp: 1.02, dir: [0.7, 0.16, -0.7] },
};
const MK = [['gancho', 0, 'night'], ['gancho', 1, 'night'], ['ataque', 0.25, 'day'], ['rescate', 1, 'day'], ['isla', 0.05, 'day'], ['isla', 1, 'golden'],
  ['jefe', 1, 'golden'], ['poemas', 0.25, 'night'], ['risas', 1, 'night'], ['vuelta', 0.25, 'day'], ['captura', 1, 'day'], ['final', 0.3, 'violet']];
const MOOD_KEYS = MK.map(([n, u, m]) => [at(n, u), m]); MOOD_KEYS.push([TL.total + 1, 'violet']);
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

// ------------------------------------------------------------------ el Egeo y la isla de Farmacusa
const WATER_Y = -1.2, ISLE = V(0, 0, -200), ISLE_R = 150;
function noise2(x, z) { return Math.sin(x * 0.013 + Math.sin(z * 0.011) * 2) * 0.5 + Math.sin(z * 0.017 + x * 0.004) * 0.35 + Math.sin((x + z) * 0.041) * 0.15; }
function groundY(x, z) {
  const d = Math.hypot(x - ISLE.x, (z - ISLE.z) * 1.15) + noise2(x * 2, z * 2) * 10;
  const k = clamp01(1 - d / ISLE_R);
  let h = -6 + 9 * ease(clamp01(k * 4)) + 40 * Math.pow(k, 1.7) + 3 * noise2(x * 1.7, z * 1.3) * k;
  for (const [ix, iz, r, hh] of [[-700, -900, 160, 70], [800, -1200, 220, 90], [-1200, -400, 140, 50]]) { const q = clamp01(1 - Math.hypot(x - ix, z - iz) / r); h = Math.max(h, -6 + hh * Math.pow(q, 1.3) + 6 * ease(clamp01(q * 4))); }
  return h;
}
const GROUND = 4200, GSEG = 300;
const gGeo = new THREE.PlaneGeometry(GROUND, GROUND, GSEG, GSEG); gGeo.rotateX(-Math.PI / 2); gGeo.translate(0, 0, -400);
const gPos = gGeo.attributes.position, gCol = new Float32Array(gPos.count * 3);
for (let i = 0; i < gPos.count; i++) {
  const x = gPos.getX(i), z = gPos.getZ(i); const y = groundY(x, z); gPos.setY(i, y);
  const n = noise2(x * 3.1, z * 2.7) * 0.5 + 0.5;
  let c = y < 2.5 ? [0.94, 0.86, 0.66] : [0.62 + 0.1 * n, 0.6 + 0.08 * n, 0.42 + 0.05 * n];          // arena / monte bajo
  if (y > 14) c = c.map((v, k) => lerp(v, [0.72, 0.7, 0.66][k], clamp01((y - 14) / 16)));            // roca
  gCol.set(c, i * 3);
}
gGeo.setAttribute('color', new THREE.BufferAttribute(gCol, 3)); gGeo.computeVertexNormals();
const detail = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  g.fillStyle = '#d8d0c4'; g.fillRect(0, 0, 256, 256);
  for (let k = 0; k < 2200; k++) { const v = 150 + rnd() * 105 | 0; g.fillStyle = `rgb(${v},${v - 8},${v - 20})`; g.fillRect(rnd() * 256, rnd() * 256, 1 + rnd() * 3, 1 + rnd() * 3); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(GROUND / 9, GROUND / 9); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
})();
const ground = new THREE.Mesh(gGeo, new THREE.MeshLambertMaterial({ vertexColors: true, map: detail })); ground.receiveShadow = true; scene.add(ground);
const seaGeo = new THREE.PlaneGeometry(GROUND * 1.5, GROUND * 1.5, 140, 140); seaGeo.rotateX(-Math.PI / 2); seaGeo.translate(0, WATER_Y, -400);
const seaBase = seaGeo.attributes.position.array.slice();
const sea = new THREE.Mesh(seaGeo, toon(0x1a8ac8, { flatShading: true })); sea.receiveShadow = true; scene.add(sea);
function waveSea(t) { const a = seaGeo.attributes.position; for (let i = 0; i < a.count; i++) { const x = seaBase[i * 3], z = seaBase[i * 3 + 2]; a.setY(i, WATER_Y + Math.sin(x * 0.02 + t * 1.3) * 0.5 + Math.sin(z * 0.03 - t) * 0.5); } a.needsUpdate = true; seaGeo.computeVertexNormals(); }
// rocas y cipreses
const rockGeo = new THREE.DodecahedronGeometry(1, 0);
for (let k = 0; k < 70; k++) { const a = rnd() * 6.28, r = 20 + rnd() * 110; const x = ISLE.x + Math.cos(a) * r, z = ISLE.z + Math.sin(a) * r * 0.85; if (Math.hypot(x - 10, z + 108) < 30) continue; const s = 1 + rnd() * 3; const m = inked(rockGeo, toon(0xb0a490, { flatShading: true }), 1.08); m.scale.set(s * (1 + rnd()), s * 0.8, s); m.position.set(x, groundY(x, z) + s * 0.3, z); m.rotation.set(rnd(), rnd() * 6, rnd()); scene.add(m); }
for (let k = 0; k < 45; k++) { const a = rnd() * 6.28, r = 40 + rnd() * 90; const x = ISLE.x + Math.cos(a) * r, z = ISLE.z + Math.sin(a) * r * 0.85; if (groundY(x, z) < 4 || Math.hypot(x - 10, z + 108) < 34) continue; const h = 9 + rnd() * 7; const m = inked(new THREE.ConeGeometry(1.8, h, 7).translate(0, h / 2, 0), toon(0x2a5a2a, { flatShading: true }), 1.06); m.position.set(x, groundY(x, z) - 0.5, z); scene.add(m); }
// campamento pirata con hoguera
const CAMP = V(10, 0, -108), FIRE = V(6, 0, -112);
const tentCols = [0xb0402a, 0xd8c8a0, 0x6a4a8a, 0xc8a040];
for (let k = 0; k < 9; k++) { const a = 0.3 + k * 0.33, r = 18 + (k % 3) * 4; const x = CAMP.x + Math.cos(a) * r - 4, z = CAMP.z - Math.sin(a) * r * 0.7 - 6; const t = inked(new THREE.ConeGeometry(3.4, 4.4, 5).translate(0, 2.2, 0), toon(tentCols[k % 4], { flatShading: true }), 1.06); t.position.set(x, groundY(x, z) - 0.2, z); t.rotation.y = rnd(); scene.add(t); }
for (let k = 0; k < 5; k++) { const l = inked(new THREE.CylinderGeometry(0.25, 0.25, 2.4, 6).rotateZ(Math.PI / 2), toon(0x5a3418), 1.15); l.position.set(FIRE.x, groundY(FIRE.x, FIRE.z) + 0.25, FIRE.z); l.rotation.y = k * 1.25; scene.add(l); }
const fireTex = tex(SP.flame()), dotTex = tex(SP.softDot()), smokeTex = tex(SP.smokePuff(5));
const flames = new THREE.InstancedMesh(new THREE.PlaneGeometry(1.6, 3.2), new THREE.MeshBasicMaterial({ map: fireTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }), 6);
flames.frustumCulled = false; scene.add(flames);
const fireLight = new THREE.PointLight(0xff8a40, 0, 60, 1.3); fireLight.position.set(FIRE.x, groundY(FIRE.x, FIRE.z) + 3, FIRE.z); scene.add(fireLight);
// pilas de lingotes de plata (los talentos): primero 20, luego 50
const SILVER = V(-12, 0, -96);
const ingots = new THREE.InstancedMesh(new THREE.BoxGeometry(1.2, 0.5, 0.7), toon(0xd8dce8), 50 * 3); ingots.castShadow = true; ingots.frustumCulled = false; scene.add(ingots);
const cloth = new THREE.Mesh(new THREE.PlaneGeometry(14, 9).rotateX(-Math.PI / 2), toon(0x8a1a2a)); cloth.position.set(SILVER.x, groundY(SILVER.x, SILVER.z) + 0.15, SILVER.z); cloth.receiveShadow = true; scene.add(cloth);
function setIngots(n) {
  const m = new THREE.Matrix4(); let k = 0;
  for (let i = 0; i < 50; i++) for (let j = 0; j < 3; j++, k++) {
    const x = SILVER.x - 5.6 + (i % 10) * 1.25, z = SILVER.z - 3.2 + Math.floor(i / 10) * 1.6, y = groundY(SILVER.x, SILVER.z) + 0.45 + j * 0.5;
    m.compose(V(x, i < n ? y : -100, z), new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), (j % 2) * 0.2), V(1, 1, 1)); ingots.setMatrixAt(k, m);
  }
  ingots.instanceMatrix.needsUpdate = true;
}
// cruces en lo alto de la colina (solo siluetas, al atardecer)
const crosses = new THREE.Group();
for (let k = 0; k < 7; k++) { const x = ISLE.x - 30 + k * 10, z = ISLE.z + 20 + (k % 2) * 6; const g = new THREE.Group(); g.add(inked(new THREE.BoxGeometry(0.5, 7, 0.5).translate(0, 3.5, 0), toon(0x3a2414), 1.1)); g.add(inked(new THREE.BoxGeometry(3.6, 0.5, 0.5).translate(0, 5.6, 0), toon(0x3a2414), 1.1)); g.position.set(x, groundY(x, z) - 0.3, z); crosses.add(g); }
crosses.visible = false; scene.add(crosses);
// barcos
function hullGeo() {
  const s = new THREE.Shape();
  s.moveTo(-11, 1.6); s.quadraticCurveTo(-13, 5, -12, 7.5); s.lineTo(-10.5, 6.5); s.quadraticCurveTo(-9, 3, -7, 2.6);
  s.lineTo(8, 2.6); s.quadraticCurveTo(11, 3, 13, 6); s.lineTo(14, 5.5); s.quadraticCurveTo(12.5, 1.5, 9, 0); s.lineTo(-8, 0); s.quadraticCurveTo(-10, 0.3, -11, 1.6);
  const g = new THREE.ExtrudeGeometry(s, { depth: 4, bevelEnabled: false }); g.translate(0, 0, -2); g.rotateY(Math.PI / 2); return g;
}
const HULL = hullGeo();
function sailCanvas(kind) {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  if (kind === 'pirata') { g.fillStyle = '#3a1a22'; g.fillRect(8, 8, 240, 240); g.fillStyle = '#8a1a2a'; for (let x = 8; x < 248; x += 48) g.fillRect(x, 8, 20, 240); }
  else if (kind === 'roma') { g.fillStyle = '#c8202a'; g.fillRect(8, 8, 240, 240); g.fillStyle = '#f0c040'; g.beginPath(); g.arc(128, 128, 46, 0, 7); g.fill(); }
  else { g.fillStyle = '#f2ead2'; g.fillRect(8, 8, 240, 240); g.fillStyle = '#b02a2a'; for (let x = 8; x < 248; x += 60) g.fillRect(x, 8, 26, 240); }
  g.strokeStyle = '#141010'; g.lineWidth = 10; g.strokeRect(8, 8, 240, 240);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function ship(kind, hullColor = 0x3a2a22, scale = 1, sailOn = true) {
  const g = new THREE.Group(); g.add(inked(HULL, toon(hullColor), 1.03));
  if (sailOn) {
    g.add(inked(new THREE.CylinderGeometry(0.18, 0.22, 12, 6).translate(0, 8, 0), toon(0x6b4220), 1.2));
    const sl = new THREE.Mesh(new THREE.PlaneGeometry(9, 7), new THREE.MeshLambertMaterial({ map: sailCanvas(kind), side: THREE.DoubleSide })); sl.position.set(0, 9.5, 0.3); sl.castShadow = true; g.add(sl);
  }
  g.scale.setScalar(scale); scene.add(g); return g;
}
const romanShip = ship('mercante', 0x6a4a2a, 1.2);
const PIRATES_S = [0, 1, 2].map(k => ship('pirata', 0x1e1a1a, 1.0));
const FLEET = [0, 1, 2, 3, 4].map(k => ship('roma', 0x5a3a22, 1.15));
const rowboat = ship('', 0x6a4a2a, 0.35, false);

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
const caesarH = new Hero([SP.caesar(0), SP.caesar(1), SP.caesar(2)], 1.4, 2.8);
caesarH.mesh.material.emissive.set(0x8a7a66);                                 // que se le vea bien también de noche
const friends = [SP.tourist('#f2ead2', '#2a5ab8'), SP.tourist('#d8c8a8', '#6a4a2a'), SP.tourist('#e8dcc8', '#4a6a2a')].map(c => new Hero([c], 1.2, 2.4));
const PCOL = [['#2a6a8a', '#c8202a'], ['#8a3a1a', '#2a2a2a'], ['#4a7a3a', '#e8c050'], ['#6a2a6a', '#d8d0c0']];
const PIR = []; for (let k = 0; k < 48 && PIR.length < 34; k++) { const a = (k / 48) * Math.PI * 2, r = 7 + (k % 3) * 3.2; if (Math.sin(a) > 0.2) continue; PIR.push([FIRE.x + Math.cos(a) * r, FIRE.z + Math.sin(a) * r * 0.8, rnd()]); }   // el lado de la cámara queda libre
const pirGroups = PCOL.map(() => []); PIR.forEach((p, i) => pirGroups[i % 4].push(p));
const pirates = PCOL.map(([a, b], k) => { const c = new Crowd([SP.pirate(a, b, 0), SP.pirate(a, b, 1)], 1.2, 2.4, pirGroups[k].length, () => new THREE.Color().setScalar(0.85 + rnd() * 0.15)); c.list = pirGroups[k]; return c; });
const LEG = []; for (let k = 0; k < 24; k++) { const a = (k / 24) * Math.PI * 2; LEG.push([FIRE.x + Math.cos(a) * 19, FIRE.z + Math.sin(a) * 15]); }
const legion = new Crowd([SP.legionary()], 1.2, 2.4, LEG.length, () => new THREE.Color().setScalar(0.9 + rnd() * 0.1));
const cloudTex = tex(SP.cloud(9)), clouds = [];
for (let k = 0; k < 14; k++) { const c = new THREE.Mesh(new THREE.PlaneGeometry(600, 300), new THREE.MeshBasicMaterial({ map: cloudTex, transparent: true, alphaTest: 0.1, fog: false, depthWrite: false })); const a = rnd() * 6.28, r = 3000 + rnd() * 800; c.position.set(Math.cos(a) * r, 650 + rnd() * 700, -400 + Math.sin(a) * r); c.lookAt(0, 300, -400); clouds.push(c); scene.add(c); }
const P = (n, u) => at(n, u);
const rockC = inked(new THREE.DodecahedronGeometry(1, 0), toon(0xb0a490, { flatShading: true }), 1.08); rockC.scale.set(1.6, 1.2, 1.4); scene.add(rockC);
const C_POS = V(10, 0, -107);                      // César junto a la hoguera, del lado de la cámara
function romanShipPos(t) { const u = ease(clamp01((t - SC.ataque.a) / (SC.ataque.b - SC.ataque.a))); return t < SC.ataque.a ? V(-200, 0, 40) : V(-200, 0, 40).lerp(V(-30, 0, -50), u); }
function pirShipPos(k, t) {
  const home = V(40 + k * 22, 0, -62 + k * 4);
  if (t < SC.ataque.a || t > SC.ataque.b + 2) return home;
  const u = ease(clamp01((t - SC.ataque.a) / (SC.ataque.b - SC.ataque.a)));
  const tgt = romanShipPos(t).add(V(10 - k * 10, 0, 14 - k * 6));
  return home.clone().lerp(tgt, u);
}
function fleetPos(k, t) {
  const a = SC.vuelta.a, b = SC.captura.b;
  const u = ease(clamp01((t - a) / (SC.vuelta.b - a)));
  const p = V(-60 + k * 26, 0, 380 + k * 20).lerp(V(-40 + k * 20, 0, -55 + k * 3), u);
  if (t > SC.final.a) { const v = ease(clamp01((t - SC.final.a) / (SC.final.b - SC.final.a))); return V(-40 + k * 20, 0, -55 + k * 3).lerp(V(-60 + k * 26, 0, 220 + k * 20), v); }
  return p;
}
// ------------------------------------------------------------------ cámara
function camKeys() {
  const K = []; const k = (n, u, pos, tgt, fov = 44) => K.push({ t: P(n, u), pos, tgt, fov });
  const cy = groundY(C_POS.x, C_POS.z), fy = groundY(FIRE.x, FIRE.z);
  k('gancho', 0, V(C_POS.x + 1.5, cy + 2.3, C_POS.z + 7), V(C_POS.x, cy + 2.1, C_POS.z), 40);
  k('gancho', 0.55, V(C_POS.x + 4, cy + 3, C_POS.z + 12), V(C_POS.x - 3, cy + 2, C_POS.z - 2), 42);
  k('gancho', 1, V(FIRE.x + 18, fy + 9, FIRE.z + 24), V(FIRE.x, fy + 2, FIRE.z), 44);
  { const r0 = romanShipPos(P('ataque', 0.3)), r1 = romanShipPos(P('ataque', 0.9)); k('ataque', 0.3, r0.clone().add(V(-25, 18, 40)), r0.clone().add(V(10, 4, -10)), 46); k('ataque', 0.9, r1.clone().add(V(-30, 22, 45)), r1.clone().add(V(10, 4, -5)), 48); }
  k('rescate', 0.3, V(SILVER.x + 8, cy + 6, SILVER.z + 18), V(SILVER.x + 3, cy + 1, SILVER.z - 2), 44);
  k('rescate', 0.8, V(SILVER.x + 2, groundY(SILVER.x, SILVER.z) + 14, SILVER.z + 19), V(SILVER.x, groundY(SILVER.x, SILVER.z), SILVER.z), 44);
  k('isla', 0.3, V(-40, 46, -170), V(10, 0, -60), 46);
  k('isla', 1, V(40, 50, -190), V(0, 0, -70), 46);
  k('jefe', 0.4, V(C_POS.x + 2, cy + 0.8, C_POS.z + 9), V(C_POS.x, cy + 3, C_POS.z), 42);
  k('jefe', 1, V(C_POS.x - 3, cy + 1.2, C_POS.z + 10), V(C_POS.x, cy + 3, C_POS.z), 42);
  k('poemas', 0.5, V(C_POS.x + 5, cy + 3.5, C_POS.z + 10), V(C_POS.x - 2, cy + 1.6, C_POS.z - 2), 44);
  k('amenaza', 0.5, V(C_POS.x + 1, cy + 2.2, C_POS.z + 7.5), V(C_POS.x, cy + 2.1, C_POS.z), 40);
  k('risas', 0.5, V(FIRE.x + 5, fy + 3.6, FIRE.z + 14), V(FIRE.x - 2, fy + 1.8, FIRE.z - 9), 40);
  { const f = fleetPos(0, P('vuelta', 0.5)); k('vuelta', 0.5, f.clone().add(V(12, 7, -42)), f.clone().add(V(0, 4, 0)), 40); }
  { const f = fleetPos(0, P('vuelta', 1)); k('vuelta', 1, f.clone().add(V(-18, 14, 30)), V(FIRE.x, fy + 2, FIRE.z), 46); }
  k('captura', 0.6, V(FIRE.x + 22, fy + 10, FIRE.z + 26), V(FIRE.x, fy + 2, FIRE.z), 44);
  k('final', 0.45, V(-60, 14, 60), V(ISLE.x - 10, 30, ISLE.z + 20), 40);
  K.push({ t: TL.total, pos: V(-80, 18, 120), tgt: V(ISLE.x - 10, 30, ISLE.z + 20), fov: 38 });
  return K;
}
let KEYS = null;
rockC.position.set(C_POS.x, groundY(C_POS.x, C_POS.z) + 0.2, C_POS.z);
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
  const minY = Math.max(groundY(p.x, p.z), WATER_Y) + 1.4; if (p.y < minY) p.y = minY;
  camera.position.copy(p); camera.lookAt(g); camera.fov = fv; camera.updateProjectionMatrix(); camera.updateMatrixWorld();
  return g;
}
const dummy = new THREE.Matrix4();
function placeShip(g, p, dir, t, ph) { g.position.set(p.x, WATER_Y - 0.3 + Math.sin(t * 1.4 + ph) * 0.3, p.z); if (dir.lengthSq() > 1e-4) g.rotation.set(0, Math.atan2(dir.x, dir.z), Math.sin(t * 1.3 + ph) * 0.03); }
window.renderAt = function (t) {
  if (!KEYS) KEYS = camKeys();
  const tgt = cameraAt(t);
  let M = mood(t);
  // 38 días: ciclo rápido de días y noches durante "isla"
  const iu = clamp01((t - SC.isla.a) / (SC.isla.b - SC.isla.a));
  if (iu > 0 && iu < 1) { const dn = 0.5 + 0.5 * Math.cos(iu * Math.PI * 2 * 5); const N = MOODS.night, D = M;
    M = { ...D, sun: D.sun.clone().lerp(new THREE.Color(N.sun), 1 - dn), si: lerp(N.si, D.si, dn), sky: D.sky.clone().lerp(new THREE.Color(N.sky), 1 - dn), hor: D.hor.clone().lerp(new THREE.Color(N.hor), 1 - dn),
      hs: D.hs.clone().lerp(new THREE.Color(N.hs), 1 - dn), fog: D.fog.clone().lerp(new THREE.Color(N.fog), 1 - dn), dir: V(Math.cos(iu * 31.4), 0.5, Math.sin(iu * 31.4)).normalize() }; }
  sun.color.copy(M.sun); sun.intensity = M.si; hemi.color.copy(M.hs); hemi.groundColor.copy(M.gnd);
  scene.fog.color.copy(M.fog); skyMat.uniforms.top.value.copy(M.sky); skyMat.uniforms.hor.value.copy(M.hor);
  const nightAmt = clamp01((0.6 - M.si / 3) * 3); skyMat.uniforms.stars.value = 0.9 * nightAmt;
  renderer.toneMappingExposure = M.exp; sky.position.copy(camera.position);
  for (const c of clouds) c.material.color.copy(M.hor).lerp(new THREE.Color(1, 1, 1), 0.45);
  const dist = camera.position.distanceTo(tgt), sz = clamp(dist * 0.9, 30, 500);
  sun.position.copy(tgt).addScaledVector(M.dir, 700); sun.target.position.copy(tgt);
  Object.assign(sun.shadow.camera, { left: -sz, right: sz, top: sz, bottom: -sz, near: 1, far: 1800 }); sun.shadow.camera.updateProjectionMatrix();
  waveSea(t);
  // hoguera
  const fireOn = nightAmt > 0.2 || t < SC.ataque.a || (t > SC.poemas.a - 0.5 && t < SC.vuelta.a);
  for (let i = 0; i < 6; i++) { const f = fireOn ? 0.8 + 0.3 * Math.sin(t * 17 + i * 2) : 0; dummy.compose(V(FIRE.x + (i - 2.5) * 0.4, groundY(FIRE.x, FIRE.z) + 1.3, FIRE.z + (i % 2) * 0.3), camera.quaternion, V(f, f, 1)); flames.setMatrixAt(i, dummy); }
  flames.instanceMatrix.needsUpdate = true; fireLight.intensity = fireOn ? 260 * (0.85 + 0.15 * Math.sin(t * 13)) : 0;
  // talentos: 20 y luego 50
  const ru = clamp01((t - SC.rescate.a) / (SC.rescate.b - SC.rescate.a));
  setIngots(t < SC.rescate.a ? 0 : (t > SC.vuelta.a && t < SC.captura.a) ? 0 : ru < 0.45 ? Math.round(20 * clamp01(ru / 0.2)) : 20 + Math.round(30 * clamp01((ru - 0.55) / 0.25)));
  // César
  let frame = 0, cp = C_POS.clone();
  if (t < SC.ataque.a || (t > SC.amenaza.a && t < SC.risas.b) || (t > SC.rescate.a && t < SC.isla.a)) frame = 2;
  if (t > SC.poemas.a && t < SC.amenaza.a) frame = 1;
  let onShip = null;
  if (t > SC.ataque.a && t < SC.rescate.a) onShip = romanShip;
  if (t > SC.vuelta.a && t < SC.captura.a + 0.5) onShip = FLEET[0];
  if (t > SC.final.a) onShip = FLEET[0];
  if (t > SC.jefe.a && t < SC.jefe.b) cp = C_POS.clone().add(V(0, 1.5, 0));          // de pie sobre una roca
  rockC.visible = t > SC.jefe.a - 0.3 && t < SC.jefe.b + 0.3;
  caesarH.setTex(frame);
  if (onShip) { caesarH.mesh.position.set(onShip.position.x, onShip.position.y + 2.6, onShip.position.z); caesarH.mesh.rotation.y = Math.atan2(camera.position.x - onShip.position.x, camera.position.z - onShip.position.z); }
  else caesarH.place(cp, t, frame === 2 ? 0.08 : 0.02);
  friends.forEach((h, i) => h.place(t > SC.isla.a && t < SC.vuelta.a ? V(C_POS.x + 4 + i * 1.6, 0, C_POS.z + 2 - i) : V(0, -200, 0), t, 0.02));
  // piratas: alrededor de la hoguera; ríen en "amenaza" y "risas"; capturados al final
  const laugh = (t > SC.amenaza.a && t < SC.risas.b) || (t > SC.rescate.a && t < SC.rescate.b && false);
  const caught = clamp01((t - SC.captura.a) / 2);
  for (const cr of pirates) {
    cr.list.forEach(([x, z, r], i) => {
      const xx = lerp(x, FIRE.x + (x - FIRE.x) * 0.45, caught), zz = lerp(z, FIRE.z + (z - FIRE.z) * 0.45, caught);
      const hide = (t > SC.ataque.a + 0.3 && t < SC.rescate.a) || t > SC.final.a + 0.5;
      cr.pos.set([xx, groundY(xx, zz) + (hide ? -80 : 0), zz], i * 3);
    });
    cr.setFrame(laugh ? Math.floor(t * 4 + 1) : 0); cr.update(laugh ? 0.3 : 0.04, laugh ? 10 : 2, t);
  }
  const lOn = t > SC.captura.a - 0.5 && t < SC.final.a;
  LEG.forEach(([x, z], i) => { const xx = lerp(x, FIRE.x + (x - FIRE.x) * 0.75, caught), zz = lerp(z, FIRE.z + (z - FIRE.z) * 0.75, caught); legion.pos.set([xx, groundY(xx, zz) + (lOn ? 0 : -80), zz], i * 3); });
  legion.update(0.05, 3, t);
  // barcos
  { const p = romanShipPos(t), p2 = romanShipPos(t + 0.2); placeShip(romanShip, p, p2.sub(p).lengthSq() > 1e-4 ? p2 : V(1, 0, 0), t, 0); romanShip.visible = t < SC.isla.a + 1; }
  PIRATES_S.forEach((s, k) => { const p = pirShipPos(k, t), p2 = pirShipPos(k, t + 0.2); placeShip(s, p, p2.clone().sub(p).lengthSq() > 1e-4 ? p2.sub(p) : V(1, 0, 0.3), t, k + 1); });
  FLEET.forEach((s, k) => { const p = fleetPos(k, t), p2 = fleetPos(k, t + 0.2); placeShip(s, p, p2.clone().sub(p).lengthSq() > 1e-4 ? p2.sub(p) : V(0, 0, -1), t, k + 3); s.visible = t > SC.vuelta.a - 1; });
  { const u = clamp01((t - SC.isla.a) / 4); rowboat.position.set(C_POS.x - 20 - u * 60, WATER_Y - 0.2, -60 + u * 120); rowboat.rotation.y = 0.5; rowboat.visible = t > SC.isla.a && t < SC.isla.a + 5; }
  crosses.visible = t > SC.final.a;

  renderer.render(scene, camera);
  return true;
};
window.grab = (q = 0.93) => renderer.domElement.toDataURL('image/jpeg', q);
window.READY = true;
