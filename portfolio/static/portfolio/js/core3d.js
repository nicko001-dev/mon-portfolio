/* ============================================================
   Expérience lilo — cœur 3D en fond continu.

   Une seule scène WebGL (icosphère déformée par un bruit simplex,
   cage filaire, éclats en orbite, champ de particules, anneaux,
   ondes de choc au clic) portée sur Three.js r128 global. Le canvas
   est fixe : il prend le relais après les particules et court
   jusqu'à la fin du site. À chaque section de l'atelier, le cœur
   change de position, d'échelle, de structure et de couleur.

   Le rendu ne tourne que lorsque l'atelier est à l'écran ; sans
   WebGL, la page reste parfaitement lisible (le canvas est masqué).
   ============================================================ */
(() => {
  'use strict';

  const canvas = document.getElementById('core-canvas');
  const lilo = document.getElementById('lilo');
  if (!canvas || !lilo) return;

  if (!window.THREE) { return; }

  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const timeScale = reduce ? 0.22 : 1;
  const isSmall = innerWidth < 760;

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' });
  } catch (err) {
    return;
  }
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.75));
  renderer.setSize(innerWidth, innerHeight, false);
  renderer.setClearColor(0x05050b, 1);

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x05050b, 0.05);

  const camera = new THREE.PerspectiveCamera(45, innerWidth / innerHeight, 0.1, 120);
  camera.position.set(0, 0, 6.4);

  /* ---------- environnement réfléchissant (canvas -> PMREM) ---------- */
  const envCanvas = document.createElement('canvas');
  envCanvas.width = 128; envCanvas.height = 64;
  const ectx = envCanvas.getContext('2d');
  const bgGrad = ectx.createLinearGradient(0, 0, 0, 64);
  bgGrad.addColorStop(0, '#1b1147');
  bgGrad.addColorStop(0.5, '#0a0a12');
  bgGrad.addColorStop(1, '#2b0f24');
  ectx.fillStyle = bgGrad; ectx.fillRect(0, 0, 128, 64);
  function glow(x, y, r, color) {
    const rg = ectx.createRadialGradient(x, y, 0, x, y, r);
    rg.addColorStop(0, color);
    rg.addColorStop(1, 'rgba(0,0,0,0)');
    ectx.fillStyle = rg;
    ectx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  glow(28, 18, 26, 'rgba(110,231,255,.95)');
  glow(100, 40, 30, 'rgba(255,110,214,.85)');
  glow(64, 6, 22, 'rgba(255,255,255,.5)');
  const envTex = new THREE.CanvasTexture(envCanvas);
  envTex.mapping = THREE.EquirectangularReflectionMapping;
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromEquirectangular(envTex).texture;
  envTex.dispose(); pmrem.dispose();

  /* ---------- lumières ---------- */
  scene.add(new THREE.AmbientLight(0xffffff, 0.4));
  const keyLight = new THREE.DirectionalLight(0xffffff, 1.5);
  keyLight.position.set(3, 4, 5);
  scene.add(keyLight);
  const pointA = new THREE.PointLight(0x8b5cf6, 55, 20, 2);
  pointA.position.set(4, 2, 3);
  scene.add(pointA);
  const pointB = new THREE.PointLight(0x2dd4bf, 45, 20, 2);
  pointB.position.set(-4, -2.5, 2);
  scene.add(pointB);

  /* ---------- bruit simplex (GLSL) ---------- */
  const NOISE_GLSL = `
  vec3 mod289(vec3 x){ return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 mod289(vec4 x){ return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 permute(vec4 x){ return mod289(((x*34.0)+1.0)*x); }
  vec4 taylorInvSqrt(vec4 r){ return 1.79284291400159 - 0.85373472095314 * r; }
  float snoise(vec3 v){
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i  = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    i = mod289(i);
    vec4 p = permute( permute( permute(
               i.z + vec4(0.0, i1.z, i2.z, 1.0))
             + i.y + vec4(0.0, i1.y, i2.y, 1.0))
             + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
  }
  `;

  const coreVertex = `
  uniform float uTime;
  uniform float uAmp;
  uniform float uPulse;
  uniform float uInflate;
  varying vec3 vNormal;
  varying vec3 vView;
  varying float vDisp;
  ${NOISE_GLSL}
  float getDisp(vec3 p){
    float t = uTime * 0.35;
    float n1 = snoise(p * 1.3 + vec3(0.0, t, t * 0.6));
    float n2 = snoise(p * 3.1 - vec3(t * 0.9, 0.0, t * 0.4));
    float d = n1 * 0.62 + n2 * 0.22;
    d += uPulse * 0.5 * snoise(p * 2.2 + t * 2.0);
    return d * uAmp;
  }
  void main(){
    vec3 nrm = normalize(normal);
    vec3 up = abs(nrm.y) < 0.99 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
    vec3 tang = normalize(cross(nrm, up));
    vec3 bitan = normalize(cross(nrm, tang));
    float e = 0.07;
    float d0 = getDisp(position);
    float d1 = getDisp(position + tang * e);
    float d2 = getDisp(position + bitan * e);
    vec3 p0 = position + nrm * d0;
    vec3 p1 = position + tang * e + nrm * d1;
    vec3 p2 = position + bitan * e + nrm * d2;
    vec3 dispN = normalize(cross(p1 - p0, p2 - p0));
    vec3 displaced = p0 + nrm * uInflate;
    vDisp = d0;
    vNormal = normalMatrix * dispN;
    vec4 mv = modelViewMatrix * vec4(displaced, 1.0);
    vView = mv.xyz;
    gl_Position = projectionMatrix * mv;
  }
  `;

  const coreFragment = `
  uniform vec3 uColA;
  uniform vec3 uColB;
  uniform float uAmp;
  uniform float uFacet;
  uniform float uTime;
  uniform vec2 uMouse;
  varying vec3 vNormal;
  varying vec3 vView;
  varying float vDisp;
  void main(){
    vec3 N = normalize(vNormal);
    vec3 V = normalize(-vView);
    vec3 flatN = normalize(cross(dFdx(vView), dFdy(vView)));
    flatN *= sign(dot(flatN, N) + 0.0001);
    N = normalize(mix(N, flatN, clamp(uFacet, 0.0, 1.0)));
    float fres = pow(1.0 - clamp(abs(dot(N, V)), 0.0, 1.0), 2.3);
    float grad = smoothstep(-0.55, 0.6, vDisp / max(uAmp, 0.001));
    vec3 base = mix(uColA, uColB, grad);
    vec3 L1 = normalize(vec3(0.6 + uMouse.x * 0.35, 0.8 - uMouse.y * 0.3, 0.55));
    vec3 L2 = normalize(vec3(-0.7, -0.35, 0.4));
    float diff = max(dot(N, L1), 0.0) * 0.75 + max(dot(N, L2), 0.0) * 0.3;
    vec3 col = base * (0.16 + diff * 0.9);
    col += uColB * fres * 1.3;
    col += uColA * pow(max(dot(reflect(-L1, N), V), 0.0), 42.0) * 0.55;
    col *= 1.0 - 0.06 * (0.5 + 0.5 * sin(vView.y * 40.0 - uTime * 3.0));
    gl_FragColor = vec4(col, 1.0);
  }
  `;

  const cageFragment = `
  uniform vec3 uCol;
  varying vec3 vNormal;
  varying vec3 vView;
  varying float vDisp;
  void main(){
    float fres = pow(1.0 - clamp(abs(dot(normalize(vNormal), normalize(-vView))), 0.0, 1.0), 1.6);
    gl_FragColor = vec4(uCol, 0.08 + fres * 0.4);
  }
  `;

  /* ---------- hiérarchies ---------- */
  const group = new THREE.Group();  /* position / échelle / inclinaison souris */
  const spin = new THREE.Group();   /* rotation continue */
  group.add(spin);
  scene.add(group);

  /* ---------- cœur : icosphère déformée ---------- */
  const coreUniforms = {
    uTime:    { value: 0 },
    uAmp:     { value: 0.38 },
    uPulse:   { value: 0 },
    uInflate: { value: 0 },
    uFacet:   { value: 0 },
    uColA:    { value: new THREE.Color('#7c3aed') },
    uColB:    { value: new THREE.Color('#8b5cf6') },
    uMouse:   { value: new THREE.Vector2(0, 0) }
  };
  const coreMat = new THREE.ShaderMaterial({
    uniforms: coreUniforms,
    vertexShader: coreVertex,
    fragmentShader: coreFragment,
    extensions: { derivatives: true }
  });
  const core = new THREE.Mesh(new THREE.IcosahedronGeometry(1.15, isSmall ? 24 : 40), coreMat);
  spin.add(core);

  /* ---------- cage filaire ---------- */
  const cageUniforms = {
    uTime:    coreUniforms.uTime,
    uAmp:     coreUniforms.uAmp,
    uPulse:   coreUniforms.uPulse,
    uInflate: { value: 0.04 },
    uCol:     { value: new THREE.Color('#9fe9ff') }
  };
  const cageMat = new THREE.ShaderMaterial({
    uniforms: cageUniforms,
    vertexShader: coreVertex,
    fragmentShader: cageFragment,
    wireframe: true,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending
  });
  const cage = new THREE.Mesh(new THREE.IcosahedronGeometry(1.15, isSmall ? 10 : 16), cageMat);
  spin.add(cage);

  /* ---------- éclats en orbite ---------- */
  const shardMat = new THREE.MeshStandardMaterial({
    color: 0xa8b0cc, metalness: 0.95, roughness: 0.22,
    emissive: 0x0a0c18, transparent: true, opacity: 1
  });
  const shards = [];
  const shardCount = isSmall ? 9 : 16;
  for (let i = 0; i < shardCount; i++) {
    const size = 0.07 + Math.random() * 0.1;
    let geo;
    if (i % 3 === 0) geo = new THREE.BoxGeometry(size * 1.5, size * 1.5, size * 1.5);
    else if (i % 3 === 1) geo = new THREE.OctahedronGeometry(size, 0);
    else geo = new THREE.TetrahedronGeometry(size * 1.2, 0);
    const mesh = new THREE.Mesh(geo, shardMat.clone());
    mesh.userData = {
      radius: 1.85 + Math.random() * 1.05,
      angle: Math.random() * Math.PI * 2,
      speed: 0.1 + Math.random() * 0.22,
      tilt: (Math.random() - 0.5) * 1.3,
      bx: Math.random(), by: Math.random(), bz: Math.random(),
      base: 0.75 + Math.random() * 0.5
    };
    spin.add(mesh);
    shards.push(mesh);
  }

  /* ---------- champ de particules ---------- */
  const pCount = isSmall ? 600 : 1200;
  const pPos = new Float32Array(pCount * 3);
  const pSize = new Float32Array(pCount);
  const pPhase = new Float32Array(pCount);
  for (let i = 0; i < pCount; i++) {
    const r = 3.1 + Math.pow(Math.random(), 0.6) * 7.2;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    pPos[i * 3]     = r * Math.sin(phi) * Math.cos(theta);
    pPos[i * 3 + 1] = r * Math.cos(phi) * 0.72;
    pPos[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
    pSize[i] = 6 + Math.random() * 16;
    pPhase[i] = Math.random() * Math.PI * 2;
  }
  const pGeo = new THREE.BufferGeometry();
  pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
  pGeo.setAttribute('aSize', new THREE.BufferAttribute(pSize, 1));
  pGeo.setAttribute('aPhase', new THREE.BufferAttribute(pPhase, 1));
  const pUniforms = {
    uTime: { value: 0 },
    uPixelRatio: { value: Math.min(devicePixelRatio || 1, 1.75) },
    uColor: { value: new THREE.Color('#9ae6ff') }
  };
  const pointsMat = new THREE.ShaderMaterial({
    uniforms: pUniforms,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    vertexShader: `
      attribute float aSize;
      attribute float aPhase;
      uniform float uTime;
      uniform float uPixelRatio;
      varying float vAlpha;
      void main(){
        vec3 p = position;
        p.y += sin(uTime * 0.32 + aPhase) * 0.45;
        p.x += cos(uTime * 0.24 + aPhase * 1.7) * 0.35;
        p.z += sin(uTime * 0.19 + aPhase * 0.8) * 0.35;
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        gl_PointSize = aSize * uPixelRatio * (1.0 / max(0.001, -mv.z));
        gl_Position = projectionMatrix * mv;
        vAlpha = smoothstep(-17.0, -2.0, mv.z);
      }
    `,
    fragmentShader: `
      uniform vec3 uColor;
      varying float vAlpha;
      void main(){
        float d = length(gl_PointCoord - 0.5);
        float a = smoothstep(0.5, 0.02, d);
        gl_FragColor = vec4(uColor, a * vAlpha * 0.9);
      }
    `
  });
  const points = new THREE.Points(pGeo, pointsMat);
  scene.add(points);

  /* ---------- anneaux ---------- */
  const ringGroup = new THREE.Group();
  spin.add(ringGroup);
  const rings = [];
  for (let i = 0; i < 3; i++) {
    const mat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(i % 2 ? '#2dd4bf' : '#8b5cf6'),
      transparent: true, opacity: 0, depthWrite: false,
      blending: THREE.AdditiveBlending
    });
    const mesh = new THREE.Mesh(new THREE.TorusGeometry(1.72 + i * 0.36, 0.006, 6, 200), mat);
    mesh.rotation.set(Math.PI / 2 + (Math.random() - 0.5) * 0.8, (Math.random() - 0.5) * 0.9, i * 0.6);
    mesh.userData.spin = 0.09 + i * 0.07;
    ringGroup.add(mesh);
    rings.push(mesh);
  }

  /* ---------- ondes de choc au clic ---------- */
  const waves = [];
  const waveGeo = new THREE.RingGeometry(0.86, 1.0, 96);
  function spawnWave() {
    const mat = new THREE.MeshBasicMaterial({
      color: coreUniforms.uColB.value.clone(),
      transparent: true, opacity: 0.9, side: THREE.DoubleSide,
      depthWrite: false, blending: THREE.AdditiveBlending
    });
    const mesh = new THREE.Mesh(waveGeo, mat);
    mesh.position.copy(group.position);
    mesh.scale.setScalar(Math.max(0.6, group.scale.x) * 0.5);
    mesh.userData.life = 0;
    scene.add(mesh);
    waves.push(mesh);
  }

  /* ---------- états traversés section par section ---------- */
  const STATES = [
    { x: 0.55, y:  0.00, z:  0.00, scale: 0.98, amp: 0.38, facet: 0.00, ring: 0.20, shard: 0.80, rot:  0.10, colA: '#7c3aed', colB: '#8b5cf6' }, /* manifeste */
    { x: 1.50, y:  0.14, z: -0.40, scale: 0.86, amp: 0.52, facet: 0.22, ring: 0.60, shard: 0.40, rot: -0.15, colA: '#2dd4bf', colB: '#5ec8ff' }, /* métier */
    { x: 2.25, y: -0.10, z:  0.20, scale: 1.02, amp: 0.28, facet: 0.80, ring: 0.30, shard: 0.90, rot:  0.20, colA: '#8b5cf6', colB: '#2dd4bf' }, /* compétences */
    { x: 1.35, y:  0.18, z: -0.50, scale: 0.80, amp: 0.60, facet: 0.14, ring: 0.80, shard: 0.34, rot: -0.10, colA: '#f472b6', colB: '#8b5cf6' }, /* formation */
    { x: 2.45, y:  0.00, z:  0.10, scale: 1.06, amp: 0.36, facet: 0.52, ring: 0.25, shard: 0.95, rot:  0.18, colA: '#eab54d', colB: '#f472b6' }, /* projets */
    { x: 1.60, y: -0.14, z: -0.30, scale: 0.88, amp: 0.46, facet: 0.30, ring: 0.70, shard: 0.50, rot: -0.18, colA: '#2dd4bf', colB: '#eab54d' }, /* certifications */
    { x: 1.00, y:  0.42, z:  0.30, scale: 0.70, amp: 0.22, facet: 0.60, ring: 0.90, shard: 0.30, rot:  0.26, colA: '#8b5cf6', colB: '#2dd4bf' }  /* contact */
  ];
  STATES.forEach(s => { s.cA = new THREE.Color(s.colA); s.cB = new THREE.Color(s.colB); });

  const cur = {
    x: STATES[0].x, y: STATES[0].y, z: STATES[0].z, scale: STATES[0].scale,
    amp: STATES[0].amp, facet: STATES[0].facet, ring: STATES[0].ring,
    shard: STATES[0].shard, rot: STATES[0].rot
  };
  const tmpA = new THREE.Color(), tmpB = new THREE.Color();
  let pulse = 0;

  /* ---------- mapping scroll -> position continue entre sections ----------
     On lit les positions en direct (relatives au viewport) : aucun cache qui
     pourrait devenir obsolète après le chargement d'une police ou un resize. */
  const sections = [...lilo.querySelectorAll('section.lilo-section')];
  function scrollIndex() {
    const n = sections.length;
    if (n < 2) return 0;
    const y = innerHeight * 0.42;
    let prev = sections[0].getBoundingClientRect().top;
    if (y <= prev) return 0;
    for (let i = 0; i < n - 1; i++) {
      const next = sections[i + 1].getBoundingClientRect().top;
      if (y < next) {
        const span = Math.max(1, next - prev);
        return i + (y - prev) / span;
      }
      prev = next;
    }
    return n - 1;
  }

  /* ---------- mise en page réactive ---------- */
  let xScale = 1, sizeK = 1;
  function layout() {
    const aspect = innerWidth / innerHeight;
    xScale = Math.min(1, Math.max(0.12, (aspect - 0.85) / 0.65));
    sizeK = Math.min(1, Math.max(0.62, aspect / 1.3));
  }

  /* ---------- entrées ---------- */
  const mouseTarget = new THREE.Vector2(0, 0);
  const mouse = new THREE.Vector2(0, 0);
  function onPointerMove(e) {
    mouseTarget.set((e.clientX / innerWidth) * 2 - 1, (e.clientY / innerHeight) * 2 - 1);
  }
  addEventListener('pointermove', onPointerMove, { passive: true });
  addEventListener('touchmove', e => { if (e.touches && e.touches[0]) onPointerMove(e.touches[0]); }, { passive: true });

  addEventListener('pointerdown', e => {
    const t = e.target;
    if (t && t.closest && t.closest('a,button,input,textarea,select')) return;
    if (!document.body.classList.contains('lilo-active')) return;
    pulse = 1;
    spawnWave();
  });

  /* ---------- activation : le canvas n'apparaît que dans l'atelier ---------- */
  function updateActive() {
    const r = lilo.getBoundingClientRect();
    // Le cœur n'apparaît que lorsque l'atelier atteint le haut de l'écran,
    // donc après la section des particules (pas avant).
    const active = r.top < innerHeight * 0.2 && r.bottom > innerHeight * 0.1;
    document.body.classList.toggle('lilo-active', active);
  }
  addEventListener('scroll', updateActive, { passive: true });

  /* ---------- boucle ---------- */
  const clock3d = new THREE.Clock();
  let elapsed = 0, running = false, rafId = 0;

  function frame() {
    if (!running) return;
    rafId = requestAnimationFrame(frame);

    const dt = Math.min(clock3d.getDelta(), 0.05);
    elapsed += dt * timeScale;

    const kM = 1 - Math.exp(-dt * 6);
    mouse.x += (mouseTarget.x - mouse.x) * kM;
    mouse.y += (mouseTarget.y - mouse.y) * kM;

    const f = scrollIndex();
    const i0 = Math.min(STATES.length - 1, Math.max(0, Math.floor(f)));
    const i1 = Math.min(STATES.length - 1, i0 + 1);
    const raw = Math.min(1, Math.max(0, f - i0));
    const te = raw * raw * (3 - 2 * raw);
    const s0 = STATES[i0], s1 = STATES[i1];

    const kS = 1 - Math.exp(-dt * 3.6);
    const kC = 1 - Math.exp(-dt * 2.2);
    const lerpTo = key => { cur[key] += (s0[key] + (s1[key] - s0[key]) * te - cur[key]) * kS; };
    lerpTo('x'); lerpTo('y'); lerpTo('z'); lerpTo('scale');
    lerpTo('amp'); lerpTo('facet'); lerpTo('ring'); lerpTo('shard'); lerpTo('rot');

    tmpA.copy(s0.cA).lerp(s1.cA, te);
    tmpB.copy(s0.cB).lerp(s1.cB, te);
    coreUniforms.uColA.value.lerp(tmpA, kC);
    coreUniforms.uColB.value.lerp(tmpB, kC);

    pulse *= Math.exp(-dt * 2.3);

    coreUniforms.uTime.value = elapsed;
    coreUniforms.uAmp.value = cur.amp;
    coreUniforms.uFacet.value = cur.facet;
    coreUniforms.uPulse.value = pulse;
    coreUniforms.uMouse.value.set(mouse.x, mouse.y);
    cageUniforms.uCol.value.copy(coreUniforms.uColB.value);
    pUniforms.uTime.value = elapsed;
    pUniforms.uColor.value.lerp(coreUniforms.uColB.value, 0.12);

    group.position.set(cur.x * xScale, cur.y, cur.z);
    group.scale.setScalar(cur.scale * sizeK);
    group.rotation.x = -mouse.y * 0.26;
    group.rotation.y = mouse.x * 0.36;
    spin.rotation.y += dt * cur.rot;
    spin.rotation.x += dt * cur.rot * 0.35;

    for (let i = 0; i < shards.length; i++) {
      const m = shards[i], u = m.userData;
      const vis = cur.shard > 0.03;
      m.visible = vis;
      if (!vis) continue;
      u.angle += dt * u.speed;
      m.position.set(
        Math.cos(u.angle) * u.radius,
        Math.sin(u.angle * 1.4) * 0.45 + u.tilt,
        Math.sin(u.angle) * u.radius
      );
      m.rotation.x += dt * u.bx * 0.8;
      m.rotation.y += dt * u.by * 0.8;
      m.rotation.z += dt * u.bz * 0.8;
      m.scale.setScalar(cur.shard * u.base);
    }

    for (let i = 0; i < rings.length; i++) {
      rings[i].material.opacity = cur.ring * 0.6;
      rings[i].rotation.z += dt * rings[i].userData.spin;
    }

    points.rotation.y = elapsed * 0.03;
    points.rotation.x = Math.sin(elapsed * 0.07) * 0.06;

    for (let i = waves.length - 1; i >= 0; i--) {
      const w = waves[i];
      w.userData.life += dt / 0.9;
      const life = w.userData.life;
      w.scale.setScalar((0.6 + life * 3.4) * Math.max(0.6, cur.scale * sizeK));
      w.material.opacity = Math.max(0, 0.9 * (1 - life));
      w.quaternion.copy(camera.quaternion);
      if (life >= 1) {
        scene.remove(w);
        w.material.dispose();
        waves.splice(i, 1);
      }
    }

    const kCam = 1 - Math.exp(-dt * 2.6);
    camera.position.x += (mouse.x * 0.9 - camera.position.x) * kCam;
    camera.position.y += (-mouse.y * 0.62 + Math.sin(elapsed * 0.3) * 0.05 - camera.position.y) * kCam;
    camera.lookAt(group.position.x * 0.34, group.position.y * 0.34, group.position.z * 0.34);

    renderer.render(scene, camera);
  }

  function start() {
    if (running) return;
    running = true;
    clock3d.start();
    rafId = requestAnimationFrame(frame);
  }
  function stop() {
    running = false;
    if (rafId) cancelAnimationFrame(rafId);
    rafId = 0;
  }

  function resize() {
    const w = innerWidth, h = innerHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    const dpr = Math.min(devicePixelRatio || 1, 1.75);
    renderer.setPixelRatio(dpr);
    renderer.setSize(w, h, false);
    pUniforms.uPixelRatio.value = dpr;
    layout();
  }
  addEventListener('resize', resize, { passive: true });
  addEventListener('orientationchange', resize, { passive: true });

  layout();
  resize();
  updateActive();
  if (reduce) renderer.render(scene, camera);

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => { if (en.isIntersecting) start(); else stop(); });
    }, { rootMargin: '15% 0px 15% 0px', threshold: 0 });
    io.observe(lilo);
  } else {
    start();
  }
})();
