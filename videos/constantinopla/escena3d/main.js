// Constantinopla 1453: personajes 2D (recortes dibujados con código) en un mundo 3D real, con sombras.
// Misma técnica que Gaugamela: cámara continua sin cortes, luz que sigue a la historia, contorno de tinta.
import * as THREE from './node_modules/three/build/three.module.js';
import * as SP from './sprites.js';

const W = 1920, H = 1080;                          // vídeo largo en horizontal (16:9)
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
  dusk:    { sun: 0xffa060, si: 2.6, sky: 0x2a2a6a, hor: 0xff8a50, gnd: 0x4a3036, hs: 0xd8a890, fog: 0xb07a6a, exp: 1.02, dir: [0.7, 0.22, 0.68] },
  golden:  { sun: 0xffc070, si: 2.9, sky: 0x3a6ac0, hor: 0xffc08a, gnd: 0x6a5040, hs: 0xffd8b0, fog: 0xe0b890, exp: 1.04, dir: [-0.6, 0.35, 0.7] },
  day:     { sun: 0xfff0d8, si: 3.0, sky: 0x2f7ae0, hor: 0xcfe2f4, gnd: 0x7a6a50, hs: 0xdce8ff, fog: 0xc8d8e8, exp: 1.0,  dir: [-0.45, 0.65, 0.6] },
  grey:    { sun: 0xd8d8e0, si: 2.0, sky: 0x5a6478, hor: 0xa8acb8, gnd: 0x4a4a4a, hs: 0xb8bcc8, fog: 0x9aa0aa, exp: 1.0,  dir: [-0.3, 0.7, 0.6] },
  night:   { sun: 0x8fb0ff, si: 1.3, sky: 0x050a1e, hor: 0x1e2c5a, gnd: 0x0a0c18, hs: 0x4a5fa8, fog: 0x141c3a, exp: 1.05, dir: [0.35, 0.5, -0.8] },
  fire:    { sun: 0xffb070, si: 2.6, sky: 0x2e1a38, hor: 0xff7a38, gnd: 0x4a3030, hs: 0xd8a080, fog: 0x8a4a3a, exp: 1.05, dir: [0.6, 0.3, 0.74] },
  violet:  { sun: 0xff9ab0, si: 2.1, sky: 0x1e1a50, hor: 0xd8708a, gnd: 0x3a2838, hs: 0x9a80c8, fog: 0x7a5080, exp: 1.02, dir: [-0.7, 0.2, 0.68] },
};
const MK = [['gancho', 0, 'fire'], ['gancho2', 0.3, 'golden'], ['murallas', 0.3, 'day'], ['imperio', 0.3, 'grey'], ['sultan', 0.3, 'golden'],
  ['fortaleza', 0.3, 'day'], ['canon', 1, 'day'], ['asedio', 0.2, 'golden'], ['bombardeo', 0.4, 'fire'], ['reparar', 0.3, 'night'],
  ['cadena', 0.3, 'day'], ['genoveses', 1, 'day'], ['truco', 0.2, 'night'], ['cuerno', 0.3, 'golden'], ['minas', 0.4, 'dusk'],
  ['presagios', 0.15, 'night'], ['presagios', 0.97, 'night'], ['asalto', 0.3, 'fire'], ['emperador', 1, 'fire'], ['caida', 0.35, 'golden'], ['despues', 0.4, 'dusk'], ['final', 0.3, 'violet']];
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

// ------------------------------------------------------------------ geografía: la península, el Cuerno de Oro, el Bósforo y el Mármara
const WATER_Y = -1.2, WALL_X = -250, Z_HORN = -420, Z_HORN2 = -540, Z_MARM = 80, X_BOS = 270, X_ASIA = 440;
function noise2(x, z) { return Math.sin(x * 0.013 + Math.sin(z * 0.011) * 2) * 0.5 + Math.sin(z * 0.017 + x * 0.004) * 0.35 + Math.sin((x + z) * 0.041) * 0.15; }
function shoreDist(x, z) {            // > 0 tierra (distancia a la orilla), < 0 agua
  const land = [];
  if (z < Z_MARM && z > Z_HORN && x < X_BOS) land.push(Math.min(Z_MARM - z, x > -700 ? z - Z_HORN : 1e4, X_BOS - x));
  if (z <= Z_HORN && z >= Z_HORN2 && x <= -700) land.push(Math.min(-700 - x, z < Z_MARM ? 1e4 : 0));
  if (z < Z_HORN2 && x < X_BOS) land.push(Math.min(Z_HORN2 - z, X_BOS - x));
  if (x > X_ASIA && z < 900) land.push(Math.min(x - X_ASIA, 900 - z));
  if (land.length) return Math.max(...land);
  const w = [];
  if (z >= Z_MARM) w.push(z - Z_MARM);
  if (x >= X_BOS && x <= X_ASIA) w.push(Math.min(x - X_BOS, X_ASIA - x));
  if (z <= Z_HORN && z >= Z_HORN2 && x > -700) w.push(Math.min(Z_HORN - z, z - Z_HORN2));
  return -(w.length ? Math.min(...w) : 30);
}
function groundY(x, z) {
  const d = shoreDist(x, z);
  let h = 6 + 4 * noise2(x * 0.6, z * 0.6);
  h += 18 * Math.exp(-((x - 120) ** 2 + (z + 180) ** 2) / 2.6e4);                // colinas de la ciudad
  h += 46 * Math.exp(-((x - 60) ** 2 + (z + 690) ** 2) / 1.6e4);                 // colina de Gálata
  if (x > X_ASIA) h += 30 * clamp01((x - X_ASIA) / 300) * (1 + noise2(z, x));
  const wallBand = clamp01(1 - Math.abs(x - WALL_X + 20) / 90); h = lerp(h, 7, wallBand * 0.85);   // llano junto a la muralla
  if (Math.abs(x - (WALL_X - 40)) < 8 && z > Z_HORN + 10 && z < Z_MARM - 8) h -= 3.5 * (1 - Math.abs(x - (WALL_X - 40)) / 8);   // foso
  return lerp(-7, h, ease(clamp01((d + 12) / 34)));
}
const GROUND = 5200, GSEG = 420;
const gGeo = new THREE.PlaneGeometry(GROUND, GROUND, GSEG, GSEG); gGeo.rotateX(-Math.PI / 2); gGeo.translate(-100, 0, -300);
const gPos = gGeo.attributes.position, gCol = new Float32Array(gPos.count * 3);
for (let i = 0; i < gPos.count; i++) {
  const x = gPos.getX(i), z = gPos.getZ(i); const y = groundY(x, z); gPos.setY(i, y);
  const n = noise2(x * 3.1, z * 2.7) * 0.5 + 0.5, d = shoreDist(x, z);
  let c = [0.5 + 0.08 * n, 0.6 + 0.08 * n, 0.32 + 0.05 * n];                              // campo verde-ocre
  if (z > Z_HORN && z < Z_MARM && x > WALL_X && x < X_BOS) c = [0.74 + 0.06 * n, 0.66 + 0.05 * n, 0.52 + 0.04 * n];   // suelo urbano
  if (x < WALL_X - 60 && x > -760) c = c.map((v, k) => lerp(v, [0.66, 0.58, 0.42][k], 0.6));                       // campamento pisado
  if (d < 6) c = [0.86, 0.78, 0.58];                                                        // playa
  gCol.set(c, i * 3);
}
gGeo.setAttribute('color', new THREE.BufferAttribute(gCol, 3)); gGeo.computeVertexNormals();
const detail = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  g.fillStyle = '#d8d0c4'; g.fillRect(0, 0, 256, 256);
  for (let k = 0; k < 2200; k++) { const v = 150 + rnd() * 105 | 0; g.fillStyle = `rgb(${v},${v - 8},${v - 20})`; g.fillRect(rnd() * 256, rnd() * 256, 1 + rnd() * 3, 1 + rnd() * 3); }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(GROUND / 9, GROUND / 9);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
})();
const ground = new THREE.Mesh(gGeo, new THREE.MeshLambertMaterial({ vertexColors: true, map: detail })); ground.receiveShadow = true; scene.add(ground);
const seaGeo = new THREE.PlaneGeometry(GROUND, GROUND, 140, 140); seaGeo.rotateX(-Math.PI / 2); seaGeo.translate(-100, WATER_Y, -300);
const seaBase = seaGeo.attributes.position.array.slice();
const sea = new THREE.Mesh(seaGeo, toon(0x2a7ab8, { flatShading: true })); sea.receiveShadow = true; scene.add(sea);
function waveSea(t) { const a = seaGeo.attributes.position; for (let i = 0; i < a.count; i++) { const x = seaBase[i * 3], z = seaBase[i * 3 + 2]; a.setY(i, WATER_Y + Math.sin(x * 0.02 + t * 1.3) * 0.45 + Math.sin(z * 0.03 - t) * 0.45); } a.needsUpdate = true; seaGeo.computeVertexNormals(); }
for (let k = 0; k < 30; k++) {                          // montañas lejanas
  const a = (k / 30) * Math.PI * 2 + rnd() * 0.15, r = 2900 + rnd() * 600;
  const h = 160 + rnd() * 260, w = 420 + rnd() * 500, seg = 6 + (rnd() * 3 | 0), rot = rnd() * 6;
  const geo = new THREE.ConeGeometry(w, h, seg, 1); geo.translate(0, h / 2, 0);
  const m = inked(geo, toon(0x7c7aa8, { flatShading: true }), 1.01);
  m.scale.set(1 + rnd() * 0.6, 1, 0.7 + rnd() * 0.4); m.position.set(-100 + Math.cos(a) * r, -30, -300 + Math.sin(a) * r); m.rotation.y = rot; scene.add(m);
}
const STONE = toon(0xd8c39a), STONE2 = toon(0xc4ab80), ROOF = toon(0xb85a3a), PLASTER = toon(0xf0e4cc), BRONZE = toon(0xb8862e), WOOD = toon(0x7a4a22);
const wallTopAt = z => groundY(WALL_X, z) + 13;
// ---- murallas de Teodosio: muralla interior por tramos (con la puerta de San Romano), torres, muralla exterior y foso
const Z_GATE = -150, Z_KERK = -385, WALL_Z0 = Z_HORN + 8, WALL_Z1 = Z_MARM - 8, SEG = 30;
const innerSegs = [];
for (let z = WALL_Z0; z < WALL_Z1 - 1; z += SEG) {
  const zc = z + SEG / 2, gy = groundY(WALL_X, zc), grp = new THREE.Group(); grp.position.set(WALL_X, gy - 1, zc);
  if (Math.abs(zc - Z_GATE) < SEG / 2) {
    for (const s of [-1, 1]) { const p = inked(new THREE.BoxGeometry(5.5, 14, SEG * 0.36).translate(0, 7, 0), STONE, 1.03); p.position.z = s * SEG * 0.32; grp.add(p); }
    const lint = inked(new THREE.BoxGeometry(5.5, 4, SEG).translate(0, 12, 0), STONE, 1.03); grp.add(lint);
    const doors = []; for (const s of [-1, 1]) { const d = inked(new THREE.BoxGeometry(1, 10, SEG * 0.14).translate(0, 5, s * SEG * 0.07), toon(0x5a3418), 1.04); d.position.set(-2.8, 0, s * SEG * 0.07); grp.add(d); doors.push(d); }
    grp.userData.doors = doors; grp.userData.gate = true;
  } else {
    const w = inked(new THREE.BoxGeometry(5.5, 14, SEG + 0.4).translate(0, 7, 0), (Math.round(zc / SEG) % 2) ? STONE : STONE2, 1.02); grp.add(w);
    for (let m = -2; m <= 2; m++) { const b = inked(new THREE.BoxGeometry(5.9, 2, 2.4).translate(0, 15, m * SEG / 5), STONE, 1.06); grp.add(b); }
  }
  scene.add(grp); innerSegs.push({ grp, zc });
  const tw = inked(new THREE.BoxGeometry(12, 22, 12).translate(0, 11, 0), STONE2, 1.03); tw.position.set(WALL_X - 1, gy - 1, z); scene.add(tw);
  const tw2 = inked(new THREE.BoxGeometry(7, 11, 7).translate(0, 5.5, 0), STONE, 1.04); tw2.position.set(WALL_X - 20, groundY(WALL_X - 20, zc) - 1, zc); scene.add(tw2);
  innerSegs[innerSegs.length - 1].tower = tw;
}
const outer = inked(new THREE.BoxGeometry(3, 8, WALL_Z1 - WALL_Z0).translate(0, 4, 0), STONE2, 1.02); outer.position.set(WALL_X - 20, groundY(WALL_X - 20, -150) - 1, (WALL_Z0 + WALL_Z1) / 2); scene.add(outer);
// Kerkoporta: portillo en la muralla interior, cerca del extremo norte
const kerk = inked(new THREE.BoxGeometry(0.6, 3.6, 2.4).translate(0, 1.8, -1.2), toon(0x4a2a12), 1.05); kerk.position.set(WALL_X - 2.9, groundY(WALL_X, Z_KERK) - 1, Z_KERK + 1.2); scene.add(kerk);
// estacada de reparación (barriles, tierra y troncos) sobre el tramo dañado
const stockade = new THREE.Group();
for (let k = 0; k < 26; k++) { const z = Z_GATE - 34 + k * 2.6; const b = inked(new THREE.CylinderGeometry(0.9, 0.9, 1.8, 10).translate(0, 0.9, 0), WOOD, 1.06); b.position.set(WALL_X + (k % 2) * 1.6, groundY(WALL_X, z) + 4 + (k % 3) * 1.7, z); stockade.add(b); }
for (let k = 0; k < 14; k++) { const z = Z_GATE - 34 + k * 5; const s = inked(new THREE.CylinderGeometry(0.25, 0.3, 9, 6).translate(0, 4.5, 0), toon(0x5a3418), 1.15); s.position.set(WALL_X + 2.6, groundY(WALL_X, z) + 3, z); s.rotation.z = 0.15; stockade.add(s); }
stockade.visible = false; scene.add(stockade);
// murallas del mar
for (const [x, z, w, d] of [[(WALL_X + X_BOS) / 2, Z_HORN + 6, X_BOS - WALL_X, 3], [(WALL_X + X_BOS) / 2, Z_MARM - 6, X_BOS - WALL_X, 3], [X_BOS - 6, (Z_HORN + Z_MARM) / 2, 3, Z_MARM - Z_HORN]]) {
  const sw = inked(new THREE.BoxGeometry(w, 8, d).translate(0, 4, 0), STONE2, 1.005); sw.position.set(x, 4, z); scene.add(sw);
}
// ---- la ciudad: casas instanciadas (con su contorno de tinta) y Santa Sofía
const HS = V(170, 0, -170);
const houseGeo = new THREE.BoxGeometry(1, 1, 1).translate(0, 0.5, 0);
const HOUSES = []; for (let k = 0; k < 420 && HOUSES.length < 300; k++) {
  const x = WALL_X + 20 + rnd() * (X_BOS - WALL_X - 34), z = Z_HORN + 18 + rnd() * (Z_MARM - Z_HORN - 34);
  if (Math.hypot(x - HS.x, z - HS.z) < 85 || (z < Z_HORN + 45 && x > -130) || Math.hypot(x + 215, z - Z_GATE) < 40 || Math.hypot(x + 236, z + 97) < 24) continue;   // Santa Sofía y plazas junto a la puerta y a la muralla
  HOUSES.push([x, z, 6 + rnd() * 9, 6 + rnd() * 9, 4 + rnd() * 6, rnd() * 3]);
}
const houseMesh = new THREE.InstancedMesh(houseGeo, PLASTER, HOUSES.length), houseInk = new THREE.InstancedMesh(houseGeo, inkMat, HOUSES.length);
const roofMesh = new THREE.InstancedMesh(houseGeo, ROOF, HOUSES.length);
houseMesh.castShadow = houseMesh.receiveShadow = roofMesh.castShadow = true;
HOUSES.forEach(([x, z, w, d, h, r], i) => {
  const y = groundY(x, z) - 0.5, q = new THREE.Quaternion().setFromAxisAngle(V(0, 1, 0), r);
  houseMesh.setMatrixAt(i, new THREE.Matrix4().compose(V(x, y, z), q, V(w, h, d)));
  houseInk.setMatrixAt(i, new THREE.Matrix4().compose(V(x, y - 0.1, z), q, V(w * 1.06, h * 1.05, d * 1.06)));
  roofMesh.setMatrixAt(i, new THREE.Matrix4().compose(V(x, y + h, z), q, V(w + 1, 0.8, d + 1)));
});
scene.add(houseMesh, houseInk, roofMesh);
const sophia = new THREE.Group(); const hsY = groundY(HS.x, HS.z) - 0.5;
sophia.add(inked(new THREE.BoxGeometry(70, 24, 76).translate(0, 12, 0), toon(0xe0b890), 1.01));
sophia.add(inked(new THREE.SphereGeometry(18, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2).translate(0, 26, 0), toon(0x9ab0c0), 1.02));
sophia.add(inked(new THREE.CylinderGeometry(19, 19, 4, 24).translate(0, 25, 0), toon(0xe0b890), 1.02));
for (const s of [-1, 1]) sophia.add(inked(new THREE.SphereGeometry(13, 18, 10, 0, Math.PI * 2, 0, Math.PI / 2).translate(0, 22, s * 22), toon(0x9ab0c0), 1.02));
const minarets = new THREE.Group();
for (const [x, z] of [[-40, -42], [40, -42], [-40, 42], [40, 42]]) {
  const m = inked(new THREE.CylinderGeometry(1.6, 2, 46, 10).translate(0, 23, 0), toon(0xf0e8dc), 1.06); m.position.set(x, 0, z); minarets.add(m);
  const c = inked(new THREE.ConeGeometry(2.2, 8, 10).translate(0, 50, 0), toon(0x6a7a8a), 1.06); c.position.set(x, 0, z); minarets.add(c);
}
minarets.visible = false; sophia.add(minarets);
const crossTop = inked(new THREE.BoxGeometry(0.6, 5, 0.6).translate(0, 46.5, 0), toon(0xf0c040), 1.1); sophia.add(crossTop);
sophia.position.set(HS.x, hsY, HS.z); scene.add(sophia);
// ---- campamento otomano: tiendas y la gran tienda roja y dorada del sultán
const TENTS = []; for (let k = 0; k < 170; k++) TENTS.push([-760 + rnd() * 400, -390 + rnd() * 450]);
const tentMesh = new THREE.InstancedMesh(new THREE.ConeGeometry(3.4, 4.6, 6).translate(0, 2.3, 0), toon(0xf0e4cc, { flatShading: true }), TENTS.length);
tentMesh.castShadow = true;
TENTS.forEach(([x, z], i) => tentMesh.setMatrixAt(i, new THREE.Matrix4().compose(V(x, groundY(x, z) - 0.2, z), new THREE.Quaternion(), V(1, 1, 1).multiplyScalar(0.8 + rnd() * 0.6))));
scene.add(tentMesh);
const SULTAN_TENT = V(-420, 0, -150);
const stent = new THREE.Group();
stent.add(inked(new THREE.CylinderGeometry(9, 9, 6, 16).translate(0, 3, 0), toon(0xc8202a), 1.03));
stent.add(inked(new THREE.ConeGeometry(11, 8, 16).translate(0, 10, 0), toon(0xe8c050), 1.03));
stent.position.set(SULTAN_TENT.x, groundY(SULTAN_TENT.x, SULTAN_TENT.z) - 0.3, SULTAN_TENT.z); scene.add(stent);
// ---- el gran cañón de Orbán (8 m) sobre su cureña, y su bala
const cannon = new THREE.Group();
const barrel = inked(new THREE.CylinderGeometry(1.0, 1.35, 8, 20).rotateZ(-Math.PI / 2), BRONZE, 1.04); barrel.position.y = 2.2; cannon.add(barrel);
for (const x of [-3, 0, 3]) { const r = inked(new THREE.TorusGeometry(1.25 + x * 0.03, 0.18, 8, 20).rotateY(Math.PI / 2), toon(0x8a5a1a), 1.02); r.position.set(x, 2.2, 0); cannon.add(r); }
cannon.add(inked(new THREE.BoxGeometry(9, 1.2, 3).translate(0, 0.6, 0), WOOD, 1.04));
const CART = new THREE.Group(); for (const [x, z] of [[-3, 1.8], [3, 1.8], [-3, -1.8], [3, -1.8]]) { const w = inked(new THREE.CylinderGeometry(1, 1, 0.5, 14).rotateX(Math.PI / 2), WOOD, 1.06); w.position.set(x, 1, z); CART.add(w); }
cannon.add(CART); scene.add(cannon);
const ball = inked(new THREE.SphereGeometry(0.6, 12, 8), toon(0x8a8a8a), 1.08); ball.visible = false; scene.add(ball);
const SMALL_GUNS = []; for (let k = 0; k < 8; k++) { const z = -360 + k * 50; if (Math.abs(z - Z_GATE) < 30) continue; const g = inked(new THREE.CylinderGeometry(0.5, 0.7, 4, 12).rotateZ(-Math.PI / 2).translate(0, 1.3, 0), BRONZE, 1.06); g.position.set(-330, groundY(-330, z), z); scene.add(g); SMALL_GUNS.push(g); }
// ---- Rumeli Hisarı ("Bogazkesen"), en la orilla europea del Bósforo
const FORT = V(225, 0, -1060);
for (const [dx, dz, r, h] of [[0, 0, 13, 32], [-30, 40, 10, 26], [-35, -45, 11, 28]]) { const t = inked(new THREE.CylinderGeometry(r, r * 1.08, h, 16).translate(0, h / 2, 0), STONE2, 1.03); t.position.set(FORT.x + dx, groundY(FORT.x + dx, FORT.z + dz) - 1, FORT.z + dz); scene.add(t); }
for (const [x1, z1, x2, z2] of [[0, 0, -30, 40], [0, 0, -35, -45], [-30, 40, -35, -45]]) { const L = Math.hypot(x2 - x1, z2 - z1); const w = inked(new THREE.BoxGeometry(3, 12, L).translate(0, 6, 0), STONE, 1.02); w.position.set(FORT.x + (x1 + x2) / 2, groundY(FORT.x, FORT.z) - 1, FORT.z + (z1 + z2) / 2); w.rotation.y = Math.atan2(x2 - x1, z2 - z1); scene.add(w); }
// ---- la cadena del Cuerno de Oro: troncos flotantes con cadena
const CHAIN_X = 40, chain = new THREE.Group();
for (let z = Z_HORN2 + 4; z < Z_HORN - 4; z += 4.2) { const l = inked(new THREE.CylinderGeometry(0.45, 0.45, 3.8, 8).rotateX(Math.PI / 2), WOOD, 1.1); l.position.set(CHAIN_X, WATER_Y + 0.3, z); chain.add(l); }
chain.add(new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, Z_HORN - Z_HORN2, 6).rotateX(Math.PI / 2).translate(CHAIN_X, WATER_Y + 0.75, (Z_HORN + Z_HORN2) / 2), toon(0x2a2a2e)));
scene.add(chain);
// ---- camino de troncos engrasados sobre la colina de Gálata
const PATH = [V(300, 0, -760), V(200, 0, -735), V(90, 0, -700), V(0, 0, -660), V(-90, 0, -600), V(-160, 0, -548)];
const pathCurve = new THREE.CatmullRomCurve3(PATH.map(p => V(p.x, groundY(p.x, p.z) + 0.2, p.z)));
for (let k = 0; k <= 160; k++) { const u = k / 160, p = pathCurve.getPointAt(u), tg = pathCurve.getTangentAt(u); const l = inked(new THREE.CylinderGeometry(0.3, 0.3, 7, 6).rotateZ(Math.PI / 2), WOOD, 1.12); l.position.copy(p); l.rotation.y = Math.atan2(tg.x, tg.z); scene.add(l); }
// ---- barcos: flota otomana, cuatro barcos cristianos, el barco veneciano y el de los sabios
function hullGeo() {
  const s = new THREE.Shape();
  s.moveTo(-11, 1.6); s.quadraticCurveTo(-13, 5, -12, 7.5); s.lineTo(-10.5, 6.5); s.quadraticCurveTo(-9, 3, -7, 2.6);
  s.lineTo(8, 2.6); s.quadraticCurveTo(11, 3, 13, 6); s.lineTo(14, 5.5); s.quadraticCurveTo(12.5, 1.5, 9, 0); s.lineTo(-8, 0); s.quadraticCurveTo(-10, 0.3, -11, 1.6);
  const g = new THREE.ExtrudeGeometry(s, { depth: 4, bevelEnabled: false }); g.translate(0, 0, -2); g.rotateY(Math.PI / 2); return g;
}
const HULL = hullGeo();
function sailCanvas(kind) {
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  g.fillStyle = kind === 'oto' ? '#c8202a' : '#f2ead2'; g.fillRect(8, 8, 240, 240);
  if (kind === 'oto') { g.fillStyle = '#f4f0e6'; g.beginPath(); g.arc(120, 128, 50, 0, 7); g.fill(); g.fillStyle = '#c8202a'; g.beginPath(); g.arc(138, 128, 42, 0, 7); g.fill(); }
  else { g.fillStyle = '#d8202a'; g.fillRect(104, 8, 48, 240); g.fillRect(8, 104, 240, 48); }
  g.strokeStyle = '#141010'; g.lineWidth = 10; g.strokeRect(8, 8, 240, 240);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const SAIL_OTO = sailCanvas('oto'), SAIL_CRI = sailCanvas('cri');
function ship(sail, hullColor = 0x3a2a22, scale = 1) {
  const g = new THREE.Group(); g.add(inked(HULL, toon(hullColor), 1.03));
  g.add(inked(new THREE.CylinderGeometry(0.18, 0.22, 12, 6).translate(0, 8, 0), WOOD, 1.2));
  const sl = new THREE.Mesh(new THREE.PlaneGeometry(9, 7), new THREE.MeshLambertMaterial({ map: sail, side: THREE.DoubleSide })); sl.position.set(0, 9.5, 0.3); sl.castShadow = true; g.add(sl);
  g.scale.setScalar(scale); scene.add(g); return g;
}
const FLEET = []; for (let k = 0; k < 40; k++) FLEET.push({ g: ship(SAIL_OTO), x0: 300 + (k % 4) * 30 + rnd() * 8, z0: -320 - Math.floor(k / 4) * 70 - rnd() * 20, ph: rnd() * 6 });
const OVER = []; for (let k = 0; k < 30; k++) OVER.push({ g: ship(SAIL_OTO), d: k / 30, ph: rnd() * 6 });
const CHRIST = [0, 1, 2, 3].map(k => ({ g: ship(SAIL_CRI, 0x6a4a2a, 1.3), k }));
const VENICE = ship(SAIL_CRI, 0x5a3a22, 1.1);
const SCHOLAR_SHIP = ship(SAIL_CRI, 0x4a3a2a, 1.2);

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

// ---- personajes y multitudes
const emperorH = new Hero([SP.emperor()], 1.4, 2.8);
const mehmed = new Hero([0, 1].map(f => SP.rider({ frame: f, coat: '#f2eee6', mane: '#c8c0b0', cloak: '#c8202a', helmet: '#f6f2e8', star: false, gold: true })), 4.4, 4.4);
const orban = new Hero([SP.engineer()], 1.35, 2.7);
const giust = new Hero([SP.genoese()], 1.45, 2.9);
const scholars = [0, 1, 2].map(() => new Hero([SP.scholar()], 1.2, 2.4));
const OXEN = []; for (let k = 0; k < 24; k++) OXEN.push([Math.floor(k / 2), k % 2]);
const oxenA = new Crowd([SP.ox(0), SP.ox(1)], 3.2, 2.0, 12), oxenB = new Crowd([SP.ox(1), SP.ox(0)], 3.2, 2.0, 12);
// ejército otomano en bloques frente a la muralla
const ARMY = []; for (let x = -480; x <= -320; x += 2.4) for (let z = -390; z <= 50; z += 2.6) { if (Math.abs(z - Z_GATE) < 16 && x > -365) continue; if (Math.hypot(x - SULTAN_TENT.x, z - SULTAN_TENT.z) < 22) continue; ARMY.push([x + (rnd() - 0.5), z + (rnd() - 0.5), rnd()]); }
const jan = [SP.janissary(0), SP.janissary(1)];
const armyGroups = [[], [], []]; ARMY.forEach((p, i) => armyGroups[i % 3].push(p));
const armies = [
  new Crowd(jan, 1.2, 2.4, armyGroups[0].length, () => new THREE.Color().setScalar(0.85 + rnd() * 0.15)),
  new Crowd([SP.persian('#c8202a', '#f2c230')], 1.15, 2.3, armyGroups[1].length, () => new THREE.Color().setScalar(0.8 + rnd() * 0.2)),
  new Crowd([SP.persian('#3a8a3a', '#f2e6c0')], 1.15, 2.3, armyGroups[2].length, () => new THREE.Color().setScalar(0.8 + rnd() * 0.2)),
]; armies.forEach((c, k) => { c.list = armyGroups[k]; });
// defensores en lo alto de las murallas
const DEF = []; for (let k = 0; k < 360; k++) DEF.push([rnd() < 0.7 ? 0 : 1, WALL_Z0 + 4 + rnd() * (WALL_Z1 - WALL_Z0 - 8)]);
const defA = new Crowd([SP.byzantine('#8a1d4a')], 1.15, 2.3, 240, () => new THREE.Color().setScalar(0.85 + rnd() * 0.15));
const defB = new Crowd([SP.genoese()], 1.15, 2.3, 120, () => new THREE.Color().setScalar(0.85 + rnd() * 0.15));
// banderas
function flagMesh(kind, w = 4, h = 2.5) {
  const geo = new THREE.PlaneGeometry(w, h, 10, 3); geo.translate(w / 2, 0, 0);
  const m = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ map: tex(SP.flagTex(kind)), side: THREE.DoubleSide })); m.castShadow = true;
  const pole = inked(new THREE.CylinderGeometry(0.08, 0.08, 6, 6).translate(0, -h / 2 - 1, 0), WOOD, 1.3); m.add(pole);
  scene.add(m); return { m, base: geo.attributes.position.array.slice(), w };
}
const kerkFlag = flagMesh('otomana', 4, 2.6), tentFlag = flagMesh('otomana', 5, 3), cityFlag = flagMesh('bizantina', 5, 3), fortFlag = flagMesh('otomana', 5, 3);
function waveFlag(f, t) { const a = f.m.geometry.attributes.position; for (let i = 0; i < a.count; i++) { const x = f.base[i * 3]; a.setZ(i, Math.sin(x * 1.6 - t * 6) * 0.22 * x); } a.needsUpdate = true; }
// efectos: fogonazo, humo, polvo del impacto, antorchas, lluvia, luna del eclipse
const fireTex = tex(SP.flame()), smokeTex = tex(SP.smokePuff(5)), dotTex = tex(SP.softDot());
const flash = new THREE.Mesh(new THREE.PlaneGeometry(9, 9), new THREE.MeshBasicMaterial({ map: dotTex, color: 0xffd080, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false })); scene.add(flash);
const PUFF_N = 60, puffs = new THREE.InstancedMesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshLambertMaterial({ map: smokeTex, transparent: true, depthWrite: false, opacity: 0.55, color: 0xb8b0a8 }), PUFF_N);
puffs.frustumCulled = false; scene.add(puffs);
const TORCH = []; for (let k = 0; k < 40; k++) TORCH.push(WALL_Z0 + 6 + k * (WALL_Z1 - WALL_Z0 - 12) / 39);
const torches = new THREE.InstancedMesh(new THREE.PlaneGeometry(1.4, 2.6), new THREE.MeshBasicMaterial({ map: fireTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }), TORCH.length + 40);
torches.frustumCulled = false; scene.add(torches);
const FIRES = []; for (let k = 0; k < 60; k++) FIRES.push([WALL_X - 30 + rnd() * 70, Z_GATE - 80 + rnd() * 160, rnd()]);
const fires = new THREE.InstancedMesh(new THREE.PlaneGeometry(5, 9), new THREE.MeshBasicMaterial({ map: fireTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }), FIRES.length);
fires.frustumCulled = false; scene.add(fires);
const rainN = 1500, rainGeo = new THREE.BufferGeometry(), rainPos = new Float32Array(rainN * 3), rainSeed = new Float32Array(rainN * 3);
for (let i = 0; i < rainN; i++) rainSeed.set([rnd(), rnd(), rnd()], i * 3);
rainGeo.setAttribute('position', new THREE.BufferAttribute(rainPos, 3));
const rain = new THREE.Points(rainGeo, new THREE.PointsMaterial({ color: 0xbfd8ff, size: 0.25, transparent: true, opacity: 0, depthWrite: false })); rain.frustumCulled = false; scene.add(rain);
const embN = 300, embGeo = new THREE.BufferGeometry(), embPos = new Float32Array(embN * 3), embSeed = new Float32Array(embN * 3);
for (let i = 0; i < embN; i++) embSeed.set([rnd(), rnd(), rnd()], i * 3);
embGeo.setAttribute('position', new THREE.BufferAttribute(embPos, 3));
const embers = new THREE.Points(embGeo, new THREE.PointsMaterial({ map: dotTex, size: 0.7, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, color: 0xffa040, fog: false })); embers.frustumCulled = false; scene.add(embers);
const moon = new THREE.Mesh(new THREE.CircleGeometry(70, 48), new THREE.MeshBasicMaterial({ color: 0xf4f0e0, fog: false, toneMapped: false })); scene.add(moon);
const moonGlow = new THREE.Mesh(new THREE.CircleGeometry(160, 48), new THREE.MeshBasicMaterial({ map: dotTex, color: 0xf4f0e0, transparent: true, opacity: 0.35, fog: false, depthWrite: false, blending: THREE.AdditiveBlending })); scene.add(moonGlow);
const cloudTex = tex(SP.cloud(9)), clouds = [];
for (let k = 0; k < 16; k++) { const c = new THREE.Mesh(new THREE.PlaneGeometry(600, 300), new THREE.MeshBasicMaterial({ map: cloudTex, transparent: true, alphaTest: 0.1, fog: false, depthWrite: false })); const a = rnd() * 6.28, r = 3300 + rnd() * 800; c.position.set(-100 + Math.cos(a) * r, 650 + rnd() * 700, -300 + Math.sin(a) * r); c.lookAt(-100, 300, -300); clouds.push(c); scene.add(c); }

// ------------------------------------------------------------------ la historia en el tiempo
const P = (n, u) => at(n, u);
function cannonPos(t) {                     // llega arrastrado por bueyes durante "canon"; antes está fuera de escena
  const u = ease(clamp01((t - P('canon', 0.05)) / (P('canon', 0.8) - P('canon', 0.05))));
  if (t < P('canon', 0.05)) return t < SC.orban.a ? V(-345, 0, Z_GATE) : V(-900, 0, Z_GATE + 10);   // en el gancho ya está (adelanto)
  return V(-900, 0, Z_GATE + 10).lerp(V(-345, 0, Z_GATE), u);
}
const SHOTS = []; { const add = (n, u) => SHOTS.push(P(n, u)); add('gancho', 0.55); add('canon', 0.92); add('asedio', 0.15); for (let k = 0; k < 4; k++) add('bombardeo', 0.1 + k * 0.25); add('asalto', 0.1); }
function lastShot(t) { let s = -99; for (const x of SHOTS) if (x <= t) s = x; return s; }
function wallDamage(t) { return ease(clamp01((t - P('bombardeo', 0.05)) / (SC.bombardeo.b - SC.bombardeo.a))) * (t < SC.caida.b ? 1 : 1); }
function christShip(k, t) {
  const u = ease(clamp01((t - SC.genoveses.a + 2) / (SC.genoveses.b - SC.genoveses.a + 2)));
  const a = V(430 - k * 12, 0, 300 + k * 18), b = V(330 - k * 10, 0, -430 + k * 6), c = V(150 - k * 12, 0, -470 - k * 10);
  const p = u < 0.75 ? a.lerp(b, u / 0.75) : b.lerp(c, (u - 0.75) / 0.25);
  if (t < SC.genoveses.a - 2) return V(900, -100, 900);
  return p;
}
function overPos(s, t) {                   // barcos arrastrados por tierra: en el Bósforo → colina → Cuerno de Oro
  const u = clamp01((t - SC.truco.a - 1) / (SC.truco.b - SC.truco.a - 1)) * 1.6 - s.d * 0.6;
  if (u <= 0) return { p: V(310 + (s.d * 30 % 30), WATER_Y - 0.3, -780 - s.d * 300), land: false, dir: V(0, 0, 1) };
  if (u >= 1) { const q = V(-150 - s.d * 260, WATER_Y - 0.3, -470 - (s.d * 7 % 1) * 60); return { p: q, land: false, dir: V(-1, 0, 0) }; }
  const p = pathCurve.getPointAt(u), tg = pathCurve.getTangentAt(u); return { p: p.clone().add(V(0, 1.4, 0)), land: true, dir: tg };
}

// ------------------------------------------------------------------ cámara
function camKeys() {
  const K = []; const k = (n, u, pos, tgt, fov = 42) => K.push({ t: P(n, u), pos, tgt, fov });
  const top = wallTopAt(-97);
  k('gancho', 0, V(-366, 5.2, -144), V(-250, 15, -151), 40);
  k('gancho', 0.6, V(-364, 6.2, -143), V(-252, 15, -150), 42);
  k('gancho', 1, V(-380, 40, -40), V(-250, 10, -150), 44);
  k('gancho2', 0.5, V(-760, 240, 330), V(0, 0, -200), 42);
  k('gancho2', 1, V(-420, 180, 470), V(60, 0, -200), 42);
  k('ciudad', 0.3, V(330, 130, 220), V(170, 20, -170), 42);
  k('ciudad', 0.7, V(70, 60, -40), V(170, 30, -170), 42);
  k('ciudad', 1, V(-130, 60, 10), V(-250, 10, -150), 44);
  k('murallas', 0.35, V(-330, 12, -40), V(-250, 14, -150), 44);
  k('murallas', 1, V(-320, 22, -300), V(-250, 16, -210), 44);
  k('imperio', 0.25, V(-249.5, top + 2.4, -91), V(-254, top + 1.6, -97.5), 38);
  k('imperio', 0.55, V(-238, top + 7, -92), V(-262, top, -100), 40);
  k('imperio', 0.85, V(-200, 650, 650), V(-60, 0, -200), 44);
  k('sultan', 0.35, V(-384, 9, -132), V(-405, 4, -148), 40);
  k('sultan', 1, V(-376, 15, -176), V(-405, 4, -150), 42);
  k('fortaleza', 0.35, V(340, 45, -960), V(220, 15, -1050), 44);
  k('fortaleza', 1, V(400, 26, -990), V(350, 0, -1060), 44);
  k('orban', 0.2, V(-222, 4.5, -137), V(-233, 2.6, -146), 38);
  k('orban', 0.55, V(-290, 14, -110), V(-300, 4, -150), 42);
  k('orban', 0.85, V(-388, 8, -128), V(-408, 4, -150), 40);
  { const c3 = cannonPos(P('canon', 0.3)), c7 = cannonPos(P('canon', 0.7)); k('canon', 0.3, c3.clone().add(V(30, 7, 22)), c3.clone().add(V(10, 3, 0)), 42); k('canon', 0.7, c7.clone().add(V(-14, 5, 16)), c7.clone().add(V(4, 2.5, 0)), 40); }
  k('canon', 1, V(-336, 7, -130), V(-252, 14, -150), 42);
  k('asedio', 0.35, V(-580, 80, -320), V(-360, 0, -150), 44);
  k('asedio', 0.7, V(-215, 32, -60), V(-320, 4, -150), 44);
  k('asedio', 1, V(-238, top + 3, -168), V(-249, top + 1.5, -158), 40);
  k('bombardeo', 0.6, V(-305, 11, -112), V(-250, 12, -150), 44);
  k('reparar', 0.6, V(-220, 32, -172), V(-252, 14, -150), 44);
  k('cadena', 0.4, V(120, 26, -470), V(40, 0, -480), 44);
  k('cadena', 1, V(-10, 30, -500), V(40, 0, -480), 44);
  k('genoveses', 0.45, V(380, 24, -500), V(340, 3, -560), 44);
  k('genoveses', 1, V(300, 7, -592), V(282, 3, -612), 40);
  k('truco', 0.3, V(260, 70, -630), V(110, 30, -700), 44);
  k('truco', 0.7, V(70, 52, -620), V(10, 40, -680), 42);
  k('truco', 1, V(-50, 42, -600), V(-150, 5, -545), 44);
  k('cuerno', 0.4, V(-100, 20, -404), V(-260, 2, -500), 44);
  k('cuerno', 1, V(-20, 24, -400), V(-220, 2, -505), 44);
  k('minas', 0.6, V(-302, 10, -60), V(-280, 2, -100), 44);
  k('presagios', 0.3, V(-180, 40, 120), V(400, 260, 900), 44);
  k('presagios', 0.48, V(-234, top + 7, -96), V(-254, top + 1.6, -97.5), 40);
  k('presagios', 0.6, V(-249.5, top + 2.4, -91), V(-254, top + 1.6, -97.5), 38);
  k('presagios', 1, V(110, 32, -100), V(170, 25, -170), 44);
  k('asalto', 0.4, V(-335, 26, -40), V(-262, 5, -150), 44);
  k('asalto', 1, V(-300, 12, -192), V(-255, 8, -150), 44);
  k('giustiniani', 0.6, V(-224, 3.6, -160), V(-233, 2.6, -151), 40);
  k('kerkoporta', 0.4, V(-292, 12, -358), V(-252, 5, Z_KERK), 42);
  k('kerkoporta', 1, V(-282, 26, -350), V(-251, wallTopAt(Z_KERK - 15) + 6, Z_KERK - 15), 42);
  k('emperador', 0.6, V(-232, 4, -142), V(-243, 2.6, -150), 40);
  k('caida', 0.45, V(4, 9, -124), V(38, 4, -150), 42);
  k('caida', 1, V(50, 72, -40), V(170, 40, -170), 44);
  k('despues', 0.4, V(-300, 16, 232), V(-350, 3, 200), 42);
  k('despues', 1, V(-880, 30, 255), V(-1300, 5, 220), 42);
  k('final', 0.4, V(-620, 270, 460), V(0, 0, -200), 42);
  K.push({ t: TL.total, pos: V(-920, 390, 620), tgt: V(0, 0, -200), fov: 42 });
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
  // convoy del cañón: cámara que sigue al cañón y a los bueyes
  const f0 = P('canon', 0.08), f1 = P('canon', 0.86), w = ease(clamp01((t - f0) / 1.2)) * ease(clamp01((f1 - t) / 1.2));
  if (w > 0) { const cp = cannonPos(t); const gy = groundY(cp.x, cp.z); p.lerp(V(cp.x + 1, gy + 5.5, cp.z + 21), w); g.lerp(V(cp.x + 9, gy + 2.2, cp.z), w); }
  p.x += Math.sin(t * 1.3) * 0.12; p.y += Math.sin(t * 1.7 + 1) * 0.08;
  const minY = Math.max(groundY(p.x, p.z), WATER_Y) + 1.4; if (p.y < minY) p.y = minY;
  camera.position.copy(p); camera.lookAt(g); camera.fov = fv; camera.updateProjectionMatrix(); camera.updateMatrixWorld();
  return g;
}
const dummy = new THREE.Matrix4();
function placeShip(g, p, dir, t, ph, onLand = false) {
  g.position.copy(p); g.rotation.set(onLand ? -Math.asin(clamp(dir.y, -0.5, 0.5)) * 0 : 0, Math.atan2(dir.x, dir.z), onLand ? 0 : Math.sin(t * 1.3 + ph) * 0.03);
}
window.renderAt = function (t) {
  if (!KEYS) KEYS = camKeys();
  const tgt = cameraAt(t);
  const M = mood(t);
  sun.color.copy(M.sun); sun.intensity = M.si; hemi.color.copy(M.hs); hemi.groundColor.copy(M.gnd);
  scene.fog.color.copy(M.fog); skyMat.uniforms.top.value.copy(M.sky); skyMat.uniforms.hor.value.copy(M.hor);
  const night = Math.max(clamp01(1 - Math.abs(t - P('presagios', 0.5)) / 18), clamp01(1 - Math.abs(t - P('truco', 0.55)) / 11), clamp01(1 - Math.abs(t - P('reparar', 0.5)) / 6));
  skyMat.uniforms.stars.value = 0.9 * night;
  renderer.toneMappingExposure = M.exp; sky.position.copy(camera.position);
  for (const c of clouds) c.material.color.copy(M.hor).lerp(new THREE.Color(1, 1, 1), 0.45);
  const dist = camera.position.distanceTo(tgt), sz = clamp(dist * 0.9, 40, 700);
  sun.position.copy(tgt).addScaledVector(M.dir, 900); sun.target.position.copy(tgt);
  Object.assign(sun.shadow.camera, { left: -sz, right: sz, top: sz, bottom: -sz, near: 1, far: 2400 }); sun.shadow.camera.updateProjectionMatrix();
  waveSea(t);

  // luna (y eclipse el 22 de mayo)
  moon.position.copy(camera.position).add(V(1400, 900, 2200)); moon.lookAt(camera.position); moonGlow.position.copy(moon.position).add(V(0, 0, 1)); moonGlow.lookAt(camera.position);
  const ecl = clamp01((t - P('presagios', 0.25)) / 3) * (1 - clamp01((t - P('presagios', 0.7)) / 3));
  moon.material.color.set(0xf4f0e0).lerp(new THREE.Color(0x9a3a1a), ecl);
  moon.visible = moonGlow.visible = night > 0.05; moonGlow.material.opacity = 0.35 * night * (1 - 0.6 * ecl);

  // murallas: daños del bombardeo, estacada nocturna, puertas, Kerkoporta
  const dmg = wallDamage(t);
  for (const s of innerSegs) {
    const near = clamp01(1 - Math.abs(s.zc - Z_GATE) / 50);
    s.grp.scale.y = 1 - 0.55 * dmg * near * (s.grp.userData.gate ? 0.6 : 1);
    if (s.tower) s.tower.scale.y = 1 - 0.4 * dmg * clamp01(1 - Math.abs(s.tower.position.z - Z_GATE) / 45);
    if (s.grp.userData.doors) { const open = ease(clamp01((t - P('caida', 0.15)) / 1.5)); s.grp.userData.doors.forEach((d, i) => { d.rotation.y = (i ? -1 : 1) * open * 1.4; }); }
  }
  stockade.visible = t > P('reparar', 0.2) && t < SC.caida.b;
  kerk.rotation.y = -1.3 * ease(clamp01((t - P('kerkoporta', 0.2)) / 1.2)) * (t > P('kerkoporta', 0.1) ? 1 : 0);
  // Santa Sofía: la cruz se cambia por minaretes tras la conquista
  const mosque = t > P('caida', 0.55); minarets.visible = mosque; crossTop.visible = !mosque;

  // banderas
  { const tw = innerSegs.reduce((a, s) => Math.abs(s.zc - Z_KERK) < Math.abs(a.zc - Z_KERK) ? s : a).tower;
    const raised = t > P('kerkoporta', 0.5) && t < SC.despues.a;
    kerkFlag.m.position.set(tw.position.x, tw.position.y + 22 * tw.scale.y + 3.5 + (raised ? 0 : -400), tw.position.z); kerkFlag.m.rotation.y = 0.4; waveFlag(kerkFlag, t); }
  tentFlag.m.position.set(SULTAN_TENT.x, groundY(SULTAN_TENT.x, SULTAN_TENT.z) + 17, SULTAN_TENT.z); waveFlag(tentFlag, t);
  cityFlag.m.position.set(HS.x, hsY + 56 + (mosque ? -400 : 0), HS.z); waveFlag(cityFlag, t);
  fortFlag.m.position.set(FORT.x, groundY(FORT.x, FORT.z) + 36, FORT.z); waveFlag(fortFlag, t);

  // cañón: llegada con bueyes, disparos (fogonazo, bala, humo, polvo en la muralla)
  const cp = cannonPos(t); cannon.position.set(cp.x, groundY(cp.x, cp.z), cp.z);
  cannon.visible = t < SC.gancho2.b || t > P('canon', 0.02);
  const oxOn = t > P('canon', 0.02) && t < P('canon', 0.85);
  let oi = 0;
  for (const cr of [oxenA, oxenB]) {
    for (let i = 0; i < cr.n; i++, oi++) { const [row, side] = OXEN[oi]; const x = cp.x + 9 + row * 4.2, z = cp.z + (side ? 1.6 : -1.6); cr.pos.set([x, groundY(x, z) + (oxOn ? 0 : -60), z], i * 3); cr.flip[i] = flipFor(1, 0); }
    cr.setFrame(Math.floor(t * 3)); cr.update(0.05, 6, t);
  }
  const ls = lastShot(t), since = t - ls, muzzle = V(cp.x + 4.5, groundY(cp.x, cp.z) + 2.2, cp.z);
  flash.visible = since < 0.25; flash.position.copy(muzzle).add(V(2, 0, 0)); flash.lookAt(camera.position); flash.scale.setScalar(1 + since * 6);
  barrel.position.x = -Math.max(0, 0.6 - since * 2) * (since < 0.3 ? 1 : 0);
  const hit = V(WALL_X - 3, wallTopAt(Z_GATE) - 6, Z_GATE + 6);
  ball.visible = since < 0.9; if (ball.visible) { const u = clamp01(since / 0.9); ball.position.copy(muzzle).lerp(hit, u); ball.position.y += Math.sin(u * Math.PI) * 6; }
  for (let i = 0; i < PUFF_N; i++) {
    const near = i < PUFF_N / 2; const age = since - (near ? 0 : 0.9) - (i % 30) * 0.015;
    const base = near ? muzzle : hit; const r = (i * 37 % 100) / 100;
    const vis = age > 0 && age < 4 && ls > 0 ? 1 : 0;
    const sc = (2 + age * 4) * vis;
    dummy.compose(base.clone().add(V((near ? 3 : -1) * age * (1 + r), age * (1.5 + r * 2), (r - 0.5) * age * 3)), camera.quaternion, V(sc, sc, 1)); puffs.setMatrixAt(i, dummy);
  }
  puffs.instanceMatrix.needsUpdate = true; puffs.material.opacity = 0.55;
  SMALL_GUNS.forEach((g, k) => { g.position.x = -330 - Math.max(0, 0.4 - ((t * 0.7 + k * 0.37) % 2.5)) * 1.5; });

  // ejército otomano: espera y, en el asalto, corre hacia la muralla
  const charge = clamp01((t - P('asalto', 0.15)) / 9);
  const armyOn = t > SC.asedio.a - 3 && t < SC.caida.a + 1 || t < SC.gancho2.b;
  for (const cr of armies) {
    cr.list.forEach(([x, z, r], i) => {
      let xx = x;
      if (charge > 0 && r < 0.45) xx = lerp(x, WALL_X - 24 - r * 10, ease(clamp01(charge * 1.4 - r)));
      cr.pos.set([xx, groundY(xx, z) + (armyOn ? 0 : -80), z], i * 3);
    });
    cr.setFrame(Math.floor(t * 6)); cr.update(charge > 0 ? 0.3 : 0.05, charge > 0 ? 9 : 2, t);
  }
  // defensores en las murallas
  let di = 0;
  for (const cr of [defA, defB]) {
    for (let i = 0; i < cr.n; i++, di++) {
      const [outerW, z] = DEF[di % DEF.length]; const x = outerW ? WALL_X - 20 : WALL_X - 1;
      const y = outerW ? groundY(x, z) + 7 : wallTopAt(z);
      const gone = t > P('caida', 0.1) && t < SC.final.a;
      cr.pos.set([x + (rnd() * 0) , y + (gone ? -80 : 0), z], i * 3);
    }
    cr.update(0.05, 2, t);
  }
  // personajes
  const top = wallTopAt(-97);
  const empOn = (t > SC.imperio.a && t < SC.sultan.a) || (t > SC.presagios.a && t < SC.asalto.a) || (t > SC.emperador.a - 1 && t < SC.caida.a);
  emperorH.place(empOn ? (t > SC.emperador.a - 1 ? V(-243, 0, -150) : V(-248, top - groundY(-248, -97), -97)) : V(0, -200, 0), t, t > SC.emperador.a - 1 ? 0.12 : 0.02);
  const mOn = (t > SC.sultan.a - 1 && t < SC.fortaleza.a) || (t > P('orban', 0.6) && t < SC.canon.a) || (t > SC.genoveses.a && t < SC.cuerno.a) || (t > SC.caida.a && t < SC.despues.a);
  let mp = V(-405, 0, -148);
  if (t > SC.genoveses.a && t < SC.truco.a) { const u = ease(clamp01((t - P('genoveses', 0.5)) / 3)); mp = V(262 + u * 20, 0, -612); }
  else if (t > SC.truco.a && t < SC.cuerno.a) mp = V(150, 0, -735);
  else if (t > SC.caida.a) { const u = ease(clamp01((t - SC.caida.a) / (SC.caida.b - SC.caida.a))); mp = V(-20, 0, -150).lerp(V(98, 0, -150), u); }
  const mv = (t > SC.caida.a) || (t > P('genoveses', 0.5) && t < SC.truco.a);
  mehmed.flip = flipFor(1, 0); mehmed.setTex(mv ? Math.floor(t * 8) % 2 : 0);
  mehmed.place(mOn ? mp : V(0, -200, 0), t, mv ? 0.2 : 0.03);
  if (mOn && mp.x > X_BOS - 8 && t < SC.truco.a) mehmed.mesh.position.y = WATER_Y - 0.8;
  const ou = clamp01((t - P('orban', 0.3)) / (P('orban', 0.8) - P('orban', 0.3)));
  orban.flip = flipFor(-1, 0); orban.place(t > SC.orban.a - 1 && t < SC.canon.a ? V(-232, 0, -146).lerp(V(-404, 0, -144), ease(ou)) : V(0, -200, 0), t, ou > 0 && ou < 1 ? 0.12 : 0.02);
  const gOn = (t > P('asedio', 0.7) && t < SC.bombardeo.a) || (t > SC.asalto.a && t < SC.kerkoporta.a);
  const gu = ease(clamp01((t - P('giustiniani', 0.4)) / 3));
  giust.place(gOn ? (t > SC.asalto.a ? V(-246, 0, -152).lerp(V(-215, 0, -150), gu) : V(-249, wallTopAt(-158) - groundY(-249, -158), -158)) : V(0, -200, 0), t, 0.03);
  giust.mesh.rotation.z = t > P('giustiniani', 0.3) ? -0.35 : 0;
  // barcos
  for (const s of FLEET) { const atk = clamp01((t - SC.genoveses.a) / 4) * (1 - clamp01((t - SC.genoveses.b) / 4)); const p = V(s.x0 - atk * 25, WATER_Y - 0.3 + Math.sin(t * 1.5 + s.ph) * 0.3, s.z0); placeShip(s.g, p, V(0, 0, -1), t, s.ph); s.g.visible = t < SC.truco.a + 2 || t > SC.final.a; }
  for (const s of OVER) { const o = overPos(s, t); placeShip(s.g, o.p, o.dir, t, s.ph, o.land); s.g.visible = t > SC.truco.a - 2 && t < SC.minas.b; }
  for (const s of CHRIST) { const p = christShip(s.k, t), p2 = christShip(s.k, t + 0.2); p.y = WATER_Y - 0.3 + Math.sin(t * 1.4 + s.k) * 0.3; placeShip(s.g, p, p2.sub(p), t, s.k); s.g.visible = p.z < 800; }
  { const u = clamp01((t - SC.fortaleza.a) / (SC.fortaleza.b - SC.fortaleza.a)); const p = V(350, WATER_Y - 0.3, -1300 + u * 300); const sink = clamp01((u - 0.55) * 3);
    VENICE.position.copy(p); VENICE.position.y -= sink * 7; VENICE.rotation.set(0, 0, sink * 0.7); VENICE.visible = t > SC.fortaleza.a - 1 && t < SC.orban.a; }
  { const u = clamp01((t - SC.despues.a) / (SC.despues.b - SC.despues.a)); const p = V(-300 - u * 700, WATER_Y - 0.3, 200 + u * 20);
    SCHOLAR_SHIP.position.copy(p); SCHOLAR_SHIP.rotation.set(0, -Math.PI / 2, Math.sin(t * 1.3) * 0.03); SCHOLAR_SHIP.visible = t > SC.despues.a - 1 && t < SC.final.a;
    scholars.forEach((h, i) => { h.place(SCHOLAR_SHIP.visible ? V(p.x - 3 + i * 3, 0, p.z) : V(0, -200, 0), t, 0.02); if (SCHOLAR_SHIP.visible) h.mesh.position.y = WATER_Y + 2.4; }); }
  // fuego, antorchas, lluvia, brasas
  const torchOn = night > 0.2 || (t > SC.asalto.a && t < SC.caida.a);
  TORCH.forEach((z, i) => { const f = torchOn ? (0.85 + 0.25 * Math.sin(t * 21 + i)) : 0; dummy.compose(V(WALL_X - 1, wallTopAt(z) + 1.5, z), camera.quaternion, V(f, f, 1)); torches.setMatrixAt(i, dummy); });
  for (let i = 0; i < 40; i++) { const tr = t > SC.truco.a && t < SC.truco.b; const p = pathCurve.getPointAt(i / 40); const f = tr ? (0.85 + 0.25 * Math.sin(t * 19 + i)) : 0; dummy.compose(p.clone().add(V(4, 1.5, 0)), camera.quaternion, V(f, f, 1)); torches.setMatrixAt(TORCH.length + i, dummy); }
  torches.instanceMatrix.needsUpdate = true;
  const burn = clamp01((t - SC.asalto.a) / 3) * (1 - clamp01((t - SC.caida.a - 4) / 3)) + clamp01(1 - Math.abs(t - 4) / 5) * 0.8;
  FIRES.forEach(([x, z, r], i) => { const f = burn > r * 0.8 ? (0.8 + 0.3 * Math.sin(t * 19 + r * 9)) * clamp01((burn - r * 0.8) * 3) : 0; dummy.compose(V(x, groundY(x, z) + 3.5, z), camera.quaternion, V(f, f, 1)); fires.setMatrixAt(i, dummy); });
  fires.instanceMatrix.needsUpdate = true;
  const storm = clamp01((t - P('presagios', 0.8)) / 1.5) * (1 - clamp01((t - SC.asalto.a) / 1.5));
  rain.material.opacity = 0.6 * storm;
  for (let i = 0; i < rainN; i++) { const [a, b, c] = [rainSeed[i * 3], rainSeed[i * 3 + 1], rainSeed[i * 3 + 2]]; const life = (t * 1.6 + a) % 1; rainPos.set([camera.position.x + (b - 0.5) * 80, camera.position.y + 30 - life * 50, camera.position.z + (c - 0.5) * 80], i * 3); }
  rainGeo.attributes.position.needsUpdate = true;
  for (let i = 0; i < embN; i++) { const [a, b, c] = [embSeed[i * 3], embSeed[i * 3 + 1], embSeed[i * 3 + 2]]; const life = (t * (0.15 + 0.2 * c) + a) % 1; embPos.set([WALL_X - 20 + (a - 0.5) * 120, 6 + life * 40, Z_GATE + (b - 0.5) * 160], i * 3); }
  embGeo.attributes.position.needsUpdate = true; embers.material.opacity = burn;

  renderer.render(scene, camera);
  return true;
};
window.grab = (q = 0.93) => renderer.domElement.toDataURL('image/jpeg', q);
window.READY = true;
