// Hiroo Onoda: personajes 2D (recortes dibujados con código) en un mundo 3D real, con sombras.
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
  dawn:   { sun: 0xffb080, si: 2.4, sky: 0x3a5aa8, hor: 0xffb090, gnd: 0x3a4a30, hs: 0xffd0b0, fog: 0xc8a890, exp: 1.05, dir: [0.7, 0.3, 0.6] },
  day:    { sun: 0xfff0d0, si: 3.0, sky: 0x2f7ae0, hor: 0xcfe8d8, gnd: 0x3a5a30, hs: 0xdcefd8, fog: 0xb8d8c0, exp: 1.0,  dir: [-0.4, 0.7, 0.6] },
  dusk:   { sun: 0xff9a6a, si: 2.2, sky: 0x2a2a6a, hor: 0xff8a60, gnd: 0x2a3028, hs: 0xd8a0a0, fog: 0x8a6a70, exp: 1.02, dir: [0.7, 0.2, 0.68] },
  night:  { sun: 0x8fb0ff, si: 1.3, sky: 0x050a1e, hor: 0x1e2c5a, gnd: 0x0a0c18, hs: 0x4a5fa8, fog: 0x141c3a, exp: 1.05, dir: [0.35, 0.5, -0.8] },
  rain:   { sun: 0xb8c0c8, si: 1.6, sky: 0x3a4250, hor: 0x7a8490, gnd: 0x2a3028, hs: 0x9aa8b0, fog: 0x6a7480, exp: 1.0,  dir: [-0.3, 0.7, 0.6] },
  golden: { sun: 0xffc070, si: 2.9, sky: 0x3a6ac0, hor: 0xffc08a, gnd: 0x4a5030, hs: 0xffd8b0, fog: 0xd8b890, exp: 1.04, dir: [-0.6, 0.35, 0.7] },
  violet: { sun: 0xff8a70, si: 2.2, sky: 0x2a1a50, hor: 0xff7a5a, gnd: 0x2a2838, hs: 0xb080c0, fog: 0x7a5070, exp: 1.02, dir: [0.7, 0.18, -0.7] },
};
const MK = [['gancho', 0, 'dawn'], ['gancho', 1, 'dawn'], ['orden', 0.4, 'day'], ['panfletos', 1, 'day'], ['truco', 0.4, 'dusk'], ['truco', 1, 'dusk'],
  ['anos', 0.1, 'day'], ['anos', 1, 'dusk'], ['solo', 0.3, 'rain'], ['solo', 1, 'rain'], ['suzuki', 0.3, 'day'], ['exige', 0.5, 'dusk'],
  ['rendicion', 0.3, 'golden'], ['rendicion', 1, 'golden'], ['final', 0.4, 'golden']];
const MOOD_KEYS = MK.map(([n, u, m]) => [at(n, u), m]); MOOD_KEYS.push([TL.total + 1, 'golden']);
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

// ------------------------------------------------------------------ la selva de Lubang: siempre el mismo claro
const C = V(0, 0, 0);
function noise2(x, z) { return Math.sin(x * 0.013 + Math.sin(z * 0.011) * 2) * 0.5 + Math.sin(z * 0.017 + x * 0.004) * 0.35 + Math.sin((x + z) * 0.041) * 0.15; }
function groundY(x, z) {
  const d = Math.hypot(x, z); let h = (6 * noise2(x * 1.4, z * 1.4) + 18 * (noise2(x * 0.5, z * 0.4) + 0.7)) * clamp01((d - 14) / 40);
  if (z > 160) h = lerp(h, -8, clamp01((z - 160) / 40));           // la costa y el mar al sur
  return h;
}
const GROUND = 2400, GSEG = 260;
const gGeo = new THREE.PlaneGeometry(GROUND, GROUND, GSEG, GSEG); gGeo.rotateX(-Math.PI / 2);
const gPos = gGeo.attributes.position, gCol = new Float32Array(gPos.count * 3);
for (let i = 0; i < gPos.count; i++) { const x = gPos.getX(i), z = gPos.getZ(i); const y = groundY(x, z); gPos.setY(i, y);
  const n = noise2(x * 3.1, z * 2.7) * 0.5 + 0.5; let c = [0.32 + 0.08 * n, 0.5 + 0.1 * n, 0.22 + 0.05 * n];
  if (Math.hypot(x, z) < 12) c = [0.52, 0.44, 0.3];                  // tierra pisada del claro
  if (y < -1 && z > 140) c = [0.86, 0.8, 0.6];
  gCol.set(c, i * 3); }
gGeo.setAttribute('color', new THREE.BufferAttribute(gCol, 3)); gGeo.computeVertexNormals();
const detail = (() => { const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d'); g.fillStyle = '#d8d0c4'; g.fillRect(0, 0, 256, 256);
  for (let k = 0; k < 2200; k++) { const v = 150 + rnd() * 105 | 0; g.fillStyle = `rgb(${v - 20},${v},${v - 30})`; g.fillRect(rnd() * 256, rnd() * 256, 1 + rnd() * 3, 1 + rnd() * 3); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(GROUND / 9, GROUND / 9); t.colorSpace = THREE.SRGBColorSpace; return t; })();
const ground = new THREE.Mesh(gGeo, new THREE.MeshLambertMaterial({ vertexColors: true, map: detail })); ground.receiveShadow = true; scene.add(ground);
const sea = new THREE.Mesh(new THREE.PlaneGeometry(4000, 2000).rotateX(-Math.PI / 2).translate(0, -3, 1200), toon(0x1a8ac8)); scene.add(sea);
// árboles de copa ancha (3D con tinta) y arbustos
for (let k = 0; k < 260; k++) { const a = rnd() * 6.28, r = 14 + rnd() * 200; const x = Math.cos(a) * r, z = -Math.abs(Math.sin(a) * r * 0.9) - 8; if (groundY(x, z) < 0) continue;
  const h = 7 + rnd() * 9, g = new THREE.Group();
  g.add(inked(new THREE.CylinderGeometry(0.35, 0.55, h, 7).translate(0, h / 2, 0), toon(0x5a3a22), 1.12));
  for (let j = 0; j < 3; j++) { const s = 2.6 + rnd() * 2.4; const m = inked(new THREE.IcosahedronGeometry(s, 0).translate((rnd() - 0.5) * 3, h + (rnd() - 0.3) * 2, (rnd() - 0.5) * 3), toon([0x2a6a2a, 0x3a7a30, 0x1e5a2a][j], { flatShading: true }), 1.05); g.add(m); }
  g.position.set(x, groundY(x, z) - 0.3, z); scene.add(g); }
for (let k = 0; k < 120; k++) { const a = rnd() * 6.28, r = 9 + rnd() * 80; const x = Math.cos(a) * r, z = Math.sin(a) * r; if (groundY(x, z) < 0 || (z > -5 && Math.abs(x) < 40 && z < 70)) continue;
  const s = 0.8 + rnd() * 1.6; const b = inked(new THREE.DodecahedronGeometry(s, 0), toon([0x3a8a3a, 0x2a7030, 0x4a9a3a][k % 3], { flatShading: true }), 1.08); b.position.set(x, groundY(x, z) + s * 0.4, z); scene.add(b); }
// refugio de bambú
const hut = new THREE.Group();
for (const [x, z] of [[-2, -1.5], [2, -1.5], [-2, 1.5], [2, 1.5]]) hut.add(inked(new THREE.CylinderGeometry(0.12, 0.12, 2.6, 6).translate(x, 1.3, z), toon(0xa88a4a), 1.2));
const roof = inked(new THREE.BoxGeometry(5.2, 0.3, 4.4).translate(0, 2.7, 0), toon(0x8a6a2a), 1.05); roof.rotation.z = 0.12; hut.add(roof);
hut.position.set(-7, groundY(-7, -6), -6); hut.rotation.y = 0.4; scene.add(hut);
// panfletos: caen y quedan en el suelo
const LEAF_N = 140, leafTex = (() => { const c = document.createElement('canvas'); c.width = 64; c.height = 90; const g = c.getContext('2d'); g.fillStyle = '#f4f0e0'; g.fillRect(0, 0, 64, 90); g.fillStyle = 'rgba(40,40,40,0.7)'; for (let k = 0; k < 7; k++) g.fillRect(8, 10 + k * 11, 48 - (k % 3) * 8, 4); g.strokeStyle = '#141010'; g.lineWidth = 4; g.strokeRect(2, 2, 60, 86); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; })();
const leaflets = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.6, 0.85), new THREE.MeshLambertMaterial({ map: leafTex, side: THREE.DoubleSide }), LEAF_N); leaflets.frustumCulled = false; scene.add(leaflets);
const LEAF = []; for (let k = 0; k < LEAF_N; k++) LEAF.push([(rnd() - 0.5) * 40, (rnd() - 0.5) * 36, rnd(), rnd() * 6.28]);
// avión a reacción con estela y la Luna
const jet = new THREE.Group(); jet.add(inked(new THREE.ConeGeometry(0.9, 9, 8).rotateZ(-Math.PI / 2), toon(0xd8dce4), 1.1)); jet.add(inked(new THREE.BoxGeometry(2, 0.2, 9), toon(0xd8dce4), 1.1)); scene.add(jet);
const trail = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.8, 1, 8).rotateZ(Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.8, fog: false })); scene.add(trail);
const dotTex = tex(SP.softDot()), fireTex = tex(SP.flame());
const moon = new THREE.Mesh(new THREE.CircleGeometry(60, 40), new THREE.MeshBasicMaterial({ color: 0xf4f0e0, fog: false, toneMapped: false })); scene.add(moon);
const moonGlow = new THREE.Mesh(new THREE.CircleGeometry(150, 40), new THREE.MeshBasicMaterial({ map: dotTex, color: 0xf4f0e0, transparent: true, opacity: 0.35, fog: false, depthWrite: false, blending: THREE.AdditiveBlending })); scene.add(moonGlow);
const rainN = 1400, rainGeo = new THREE.BufferGeometry(), rainPos = new Float32Array(rainN * 3), rainSeed = new Float32Array(rainN * 3);
for (let i = 0; i < rainN; i++) rainSeed.set([rnd(), rnd(), rnd()], i * 3);
rainGeo.setAttribute('position', new THREE.BufferAttribute(rainPos, 3));
const rain = new THREE.Points(rainGeo, new THREE.PointsMaterial({ color: 0xbfd8ff, size: 0.22, transparent: true, opacity: 0, depthWrite: false })); rain.frustumCulled = false; scene.add(rain);
const sword = inked(new THREE.BoxGeometry(0.08, 0.12, 1.4), toon(0xd8dce4), 1.2); scene.add(sword);

const P = (n, u) => at(n, u);
const onodaT = [0, 1, 2].map(r => SP.soldierJP(r));
const onoda = new Hero(onodaT, 1.4, 2.8);
const comrades = [0, 1, 2].map(k => new Hero([SP.soldierJP(1, ['#5a5a3a', '#6a5a3a', '#4a5a3a'][k], false)], 1.35, 2.7));
const suzuki = new Hero([SP.backpacker()], 1.35, 2.7), tani = new Hero([SP.businessman()], 1.35, 2.7);
const PALMS = []; for (let k = 0; k < 320; k++) { const a = rnd() * 6.28, r = 12 + rnd() * 160; const x = Math.cos(a) * r, z = Math.sin(a) * r * 0.9; if (groundY(x, z) < 0 || (z > -6 && Math.abs(x) < 40 && z < 70)) continue; PALMS.push([x, z]); }
const palms = new Crowd([SP.palm()], 4.5, 9, PALMS.length, () => new THREE.Color().setScalar(0.75 + rnd() * 0.25));
PALMS.forEach(([x, z], i) => { palms.pos.set([x, groundY(x, z), z], i * 3); palms.scl[i] = 0.9 + rnd() * 0.7; });
const cloudTex = tex(SP.cloud(9)), clouds = [];
for (let k = 0; k < 14; k++) { const c = new THREE.Mesh(new THREE.PlaneGeometry(600, 300), new THREE.MeshBasicMaterial({ map: cloudTex, transparent: true, alphaTest: 0.1, fog: false, depthWrite: false })); const a = rnd() * 6.28, r = 2600 + rnd() * 600; c.position.set(Math.cos(a) * r, 600 + rnd() * 600, Math.sin(a) * r); c.lookAt(0, 300, 0); clouds.push(c); scene.add(c); }
const ON = V(1.5, 0, 1);                    // Onoda en el claro
// cámara: siempre el mismo claro; se acerca y se aleja según el momento
function camKeys() {
  const K = []; const k = (n, u, pos, tgt, fov = 42) => K.push({ t: P(n, u), pos, tgt, fov });
  const y0 = groundY(ON.x, ON.z);
  k('gancho', 0, V(ON.x + 0.6, y0 + 2.3, ON.z + 6.5), V(ON.x, y0 + 2.2, ON.z), 38);
  k('gancho', 1, V(ON.x + 2, y0 + 2.8, ON.z + 9), V(ON.x, y0 + 2, ON.z), 40);
  k('orden', 1, V(ON.x - 4, y0 + 4, ON.z + 14), V(ON.x, y0 + 2, ON.z), 44);
  k('fin', 0.6, V(ON.x + 18, y0 + 26, ON.z + 34), V(ON.x, y0, ON.z - 6), 46);
  k('panfletos', 0.6, V(ON.x + 3, y0 + 3, ON.z + 10), V(ON.x, y0 + 3.2, ON.z), 44);
  k('truco', 0.6, V(ON.x - 1, y0 + 2.2, ON.z + 6), V(ON.x, y0 + 2.2, ON.z), 38);
  k('anos', 0.2, V(ON.x + 6, y0 + 3, ON.z + 14), V(ON.x, y0 + 7, ON.z - 30), 48);
  k('anos', 0.7, V(ON.x + 4, y0 + 2.8, ON.z + 12), V(ON.x - 8, y0 + 16, ON.z - 80), 50);
  k('anos', 1, V(ON.x + 3, y0 + 3, ON.z + 10), V(ON.x, y0 + 2, ON.z), 44);
  k('solo', 0.6, V(ON.x - 6, y0 + 4.5, ON.z + 12), V(ON.x, y0 + 2, ON.z), 44);
  k('suzuki', 0.5, V(ON.x + 9, y0 + 3.5, ON.z + 12), V(ON.x + 3.5, y0 + 2, ON.z), 42);
  k('exige', 0.6, V(ON.x + 1, y0 + 2.3, ON.z + 7), V(ON.x, y0 + 2.2, ON.z), 38);
  k('rendicion', 0.5, V(ON.x + 4, y0 + 3, ON.z + 11), V(ON.x + 2, y0 + 2, ON.z), 42);
  k('rendicion', 1, V(ON.x + 2.5, y0 + 2.4, ON.z + 7), V(ON.x + 2, y0 + 1.8, ON.z), 40);
  k('final', 0.5, V(ON.x + 5, y0 + 5, ON.z + 15), V(ON.x + 2, y0 + 2, ON.z), 42);
  K.push({ t: TL.total, pos: V(ON.x + 8, y0 + 9, ON.z + 24), tgt: V(ON.x + 2, y0 + 2, ON.z), fov: 44 });
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
const dummy = new THREE.Matrix4();
window.renderAt = function (t) {
  if (!KEYS) KEYS = camKeys();
  const tgt = cameraAt(t);
  let M = mood(t);
  // los años pasan: ciclo rápido de días y noches
  const au = clamp01((t - SC.anos.a) / (SC.anos.b - SC.anos.a));
  let dn = 1;
  if (au > 0 && au < 1) { dn = 0.45 + 0.55 * (0.5 + 0.5 * Math.cos(au * Math.PI * 2 * 4));   /* noches claras: que se vea el paso del tiempo */ const N = MOODS.night, D = M;
    M = { ...D, sun: D.sun.clone().lerp(new THREE.Color(N.sun), 1 - dn), si: lerp(N.si, D.si, dn), sky: D.sky.clone().lerp(new THREE.Color(N.sky), 1 - dn), hor: D.hor.clone().lerp(new THREE.Color(N.hor), 1 - dn),
      hs: D.hs.clone().lerp(new THREE.Color(N.hs), 1 - dn), fog: D.fog.clone().lerp(new THREE.Color(N.fog), 1 - dn), dir: V(Math.cos(au * 25.1), 0.55, Math.sin(au * 25.1)).normalize() }; }
  sun.color.copy(M.sun); sun.intensity = M.si; hemi.color.copy(M.hs); hemi.groundColor.copy(M.gnd);
  scene.fog.color.copy(M.fog); skyMat.uniforms.top.value.copy(M.sky); skyMat.uniforms.hor.value.copy(M.hor);
  const nightAmt = clamp01((0.6 - M.si / 3) * 3); skyMat.uniforms.stars.value = 0.9 * nightAmt;
  renderer.toneMappingExposure = M.exp; sky.position.copy(camera.position);
  for (const c of clouds) c.material.color.copy(M.hor).lerp(new THREE.Color(1, 1, 1), 0.45);
  const dist = camera.position.distanceTo(tgt), sz = clamp(dist * 0.9, 25, 400);
  sun.position.copy(tgt).addScaledVector(M.dir, 600); sun.target.position.copy(tgt);
  Object.assign(sun.shadow.camera, { left: -sz, right: sz, top: sz, bottom: -sz, near: 1, far: 1500 }); sun.shadow.camera.updateProjectionMatrix();
  // Luna (visible de noche; durante "anos", cuando el hombre la pisa)
  moon.position.copy(camera.position).add(V(-600, 700, -1400)); moon.lookAt(camera.position); moonGlow.position.copy(moon.position).add(V(0, 0, 1)); moonGlow.lookAt(camera.position);
  moon.visible = moonGlow.visible = nightAmt > 0.15;
  // avión a reacción cruzando el cielo con su estela
  const ju = clamp01((t - P('anos', 0.15)) / 2.6);
  jet.visible = trail.visible = ju > 0 && ju < 1 && t < SC.anos.b;
  if (jet.visible) { const a = V(-500, 260, -500), b = V(500, 260, -300); const p = a.clone().lerp(b, ju); jet.position.copy(p); jet.lookAt(b); jet.rotateY(-Math.PI / 2);
    const L = a.distanceTo(p); trail.scale.set(L, 1, 1); trail.position.copy(a.clone().lerp(p, 0.5)); trail.rotation.set(0, -Math.atan2(b.z - a.z, b.x - a.x), 0); }
  // Onoda: el uniforme se desgasta con los años
  const rag = t < SC.panfletos.a ? 0 : t < P('anos', 0.5) ? 1 : 2;
  onoda.setTex(rag);
  const hide = (t > P('fin', 0.25) && t < P('fin', 0.95));
  onoda.place(hide ? V(0, -200, 0) : ON, t, 0.02);
  // compañeros: se van quedando por el camino
  const alive = t < P('solo', 0.2) ? 3 : t < P('solo', 0.45) ? 2 : t < P('solo', 0.75) ? 1 : 0;
  comrades.forEach((h, i) => h.place(i < alive && t > SC.orden.a && !hide ? V(ON.x - 3 - i * 2.2, 0, ON.z - 2 + (i % 2) * 2) : V(0, -200, 0), t, 0.02));
  suzuki.place(t > SC.suzuki.a && t < SC.rendicion.a ? V(ON.x + 4.5, 0, ON.z + 0.5) : V(0, -200, 0), t, 0.03);
  tani.place(t > SC.rendicion.a - 0.3 && t < SC.final.b ? V(ON.x + 4, 0, ON.z + 0.4) : V(0, -200, 0), t, 0.02);
  // la espada pasa de Onoda al comandante
  const su = ease(clamp01((t - P('rendicion', 0.6)) / 1.5));
  sword.visible = t > P('rendicion', 0.55) && t < SC.final.b;
  const sy = groundY(ON.x, ON.z) + 1.6; sword.position.copy(V(ON.x + 0.6, sy, ON.z + 0.4).lerp(V(ON.x + 3.4, sy, ON.z + 0.6), su)); sword.rotation.set(0, Math.PI / 2, 0);
  // panfletos: caen desde el cielo y se quedan en el suelo
  const fallStart = P('fin', 0.3);
  LEAF.forEach(([x, z, r, ph], i) => {
    const age = t - fallStart - r * 4; let y, rot;
    if (age < 0 || t > SC.solo.a) { y = -100; rot = 0; }
    else { const fall = Math.max(0, 40 - age * 9); y = groundY(x, z) + 0.05 + fall; rot = fall > 0 ? t * 3 + ph : 0; }
    dummy.compose(V(x + Math.sin(t + ph) * (y > 1 ? 1 : 0), y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(y > 1 ? Math.sin(rot) : -Math.PI / 2, ph, y > 1 ? Math.cos(rot) : 0)), V(1, 1, 1)); leaflets.setMatrixAt(i, dummy);
  });
  leaflets.instanceMatrix.needsUpdate = true;
  palms.update(0, 0, t);
  // lluvia en "solo"
  const wet = clamp01((t - SC.solo.a) / 1) * (1 - clamp01((t - SC.solo.b) / 1));
  rain.material.opacity = 0.6 * wet;
  for (let i = 0; i < rainN; i++) { const [a, b, c] = [rainSeed[i * 3], rainSeed[i * 3 + 1], rainSeed[i * 3 + 2]]; const life = (t * 1.6 + a) % 1; rainPos.set([camera.position.x + (b - 0.5) * 40, camera.position.y + 16 - life * 26, camera.position.z + (c - 0.5) * 40 - 8], i * 3); }
  rainGeo.attributes.position.needsUpdate = true;

  renderer.render(scene, camera);
  return true;
};
window.grab = (q = 0.93) => renderer.domElement.toDataURL('image/jpeg', q);
window.READY = true;
