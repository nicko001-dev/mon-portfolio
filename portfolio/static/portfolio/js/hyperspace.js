/* ============================================================
   HYPERSPACE PORTFOLIO — Moteur d'Univers 3D & Navigation 3-Écrans
   Inspiré directement de la base lilo / hyperspace_portfolio.html
   Architecture : UI A (Accueil) -> UI B (Univers 3D) -> UI C (Atelier)
   ============================================================ */
(() => {
  'use strict';

  const $ = id => document.getElementById(id);
  const app = $('portfolio-app');
  const canvas = $('hs-canvas');
  if (!canvas) return;

  const hud = $('hs-hud');
  const flash = $('hs-flash');
  const boot = $('hs-boot');
  const radar = $('hs-radar');
  const joy = $('hs-joy');
  const joyKnob = $('hs-joy-knob');
  const questPill = $('hs-quest-pill');
  const questDist = $('hs-bh-dist');
  const questArrow = $('hs-quest-arrow');
  const targetInfo = $('hs-target-info');
  const speedometer = $('hs-speedometer');
  const planetHudCard = $('planet-hud-card');
  const phBadge = $('ph-badge');
  const phName = $('ph-name');
  const phDesc = $('ph-desc');
  const toastsContainer = $('hs-toasts');

  let DATA = {};
  try { DATA = JSON.parse(($('hs-data') || {}).textContent || '{}'); }
  catch (e) { DATA = {}; }

  const TAU = Math.PI * 2;
  const R = (a, b) => a + Math.random() * (b - a);
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const hasTHREE = typeof THREE !== 'undefined';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Constantes et variables 3D */
  let scene, camera, renderer, clock, stars, dust, dustP, asteroids, astD;
  let bh, bhDisk, bhGlow, bhRing, bhPos = null, bhBeacon = null;
  const bodies = [], anim = [], comets = [], pois = [], projects = [];
  const UP = hasTHREE ? new THREE.Vector3(0, 1, 0) : null;
  const tmpF = hasTHREE ? new THREE.Vector3() : null;
  const tmpR = hasTHREE ? new THREE.Vector3() : null;
  const tmpD = hasTHREE ? new THREE.Vector3() : null;
  const dummy = hasTHREE ? new THREE.Object3D() : null;

  /* État de navigation */
  let activeUI = 'a'; // 'a', 'b', 'c'
  let yaw = 0, pitch = 0, drag = false, lx = 0, ly = 0;
  let warping = false, audio = null;
  let activeCardTimeout = null;
  const keys = Object.create(null);
  const vel = hasTHREE ? new THREE.Vector3() : null;
  const pad = { x: 0, y: 0, on: false, updown: 0, touchId: null };

  /* ───────────────────────── Audio spatial synthétique ───────────────────────── */
  function startAudio() {
    if (audio) return;
    try {
      const A = new (window.AudioContext || window.webkitAudioContext)();
      const mg = A.createGain(), f = A.createBiquadFilter();
      mg.gain.value = 0; mg.connect(A.destination);
      f.type = 'lowpass'; f.frequency.value = 400; f.connect(mg);
      [55, 82.4, 110.3, 164.9].forEach((fr, i) => {
        const o = A.createOscillator(), g = A.createGain();
        o.type = i % 2 ? 'sine' : 'sawtooth';
        o.frequency.value = fr; o.detune.value = R(-8, 8);
        g.gain.value = 0.15; o.connect(g); g.connect(f); o.start();
      });
      const l = A.createOscillator(), lg = A.createGain();
      l.frequency.value = 0.07; lg.gain.value = 250;
      l.connect(lg); lg.connect(f.frequency); l.start();
      mg.gain.linearRampToValueAtTime(0.3, A.currentTime + 3);
      audio = { A, mg, f, on: true };
    } catch (e) { audio = null; }
  }
  function toggleAudio() {
    if (!audio) { startAudio(); return; }
    audio.on = !audio.on;
    audio.mg.gain.setTargetAtTime(audio.on ? 0.3 : 0, audio.A.currentTime, 0.3);
  }

  /* ───────────────────────── Textures procédurales ───────────────────────── */
  function glowTexture() {
    const k = document.createElement('canvas'); k.width = k.height = 128;
    const g = k.getContext('2d'), r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    r.addColorStop(0, 'rgba(255,255,255,1)');
    r.addColorStop(0.3, 'rgba(255,255,255,.35)');
    r.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = r; g.fillRect(0, 0, 128, 128);
    return new THREE.CanvasTexture(k);
  }
  const GT = hasTHREE ? glowTexture() : null;

  function spr(col, size, op, tex) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({
      map: tex || GT, color: col, transparent: true, opacity: op == null ? 1 : op,
      blending: THREE.AdditiveBlending, depthWrite: false, fog: false
    }));
    s.scale.set(size, size, 1);
    return s;
  }

  function cloudTex() {
    const k = document.createElement('canvas'); k.width = k.height = 128;
    const g = k.getContext('2d');
    for (let i = 0; i < 16; i++) {
      const x = R(30, 98), y = R(30, 98), s = R(20, 50);
      const r = g.createRadialGradient(x, y, 0, x, y, s);
      r.addColorStop(0, 'rgba(255,255,255,.35)');
      r.addColorStop(1, 'rgba(255,255,255,0)');
      g.fillStyle = r; g.fillRect(0, 0, 128, 128);
    }
    return new THREE.CanvasTexture(k);
  }

  function ptex(cols, b) {
    const k = document.createElement('canvas'); k.width = 256; k.height = 128;
    const g = k.getContext('2d');
    for (let y = 0; y < 128; y++) {
      g.fillStyle = cols[Math.floor((Math.sin(y * b + Math.sin(y * .3) * 2) * .5 + .5) * cols.length) % cols.length];
      g.fillRect(0, y, 256, 1);
    }
    for (let i = 0; i < 420; i++) {
      g.fillStyle = `rgba(${Math.random() < .5 ? '255,255,255' : '0,0,0'},${R(.03, .13)})`;
      g.beginPath(); g.ellipse(R(0, 256), R(0, 128), R(2, 24), R(1, 6), 0, 0, TAU); g.fill();
    }
    return new THREE.CanvasTexture(k);
  }

  function ringGeo(a, b, seg) {
    const g = new THREE.RingGeometry(a, b, seg, 1), p = g.attributes.position, uv = g.attributes.uv, v = new THREE.Vector3();
    for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i); uv.setXY(i, (v.length() - a) / (b - a), 1); }
    return g;
  }

  function bandTex(stops, streaks) {
    const k = document.createElement('canvas'); k.width = 256; k.height = 4;
    const g = k.getContext('2d'), gr = g.createLinearGradient(0, 0, 256, 0);
    stops.forEach(s => gr.addColorStop(s[0], s[1]));
    g.fillStyle = gr; g.fillRect(0, 0, 256, 4);
    for (let i = 0; i < streaks; i++) {
      g.fillStyle = `rgba(0,0,0,${R(.1, .4)})`;
      g.fillRect(R(0, 256), 0, R(1, 3), 4);
    }
    return new THREE.CanvasTexture(k);
  }

  /* Générateur de label 3D holographique au-dessus de chaque planète */
  function makeHoloLabel(name, subtitle, colorHex) {
    const k = document.createElement('canvas');
    k.width = 512; k.height = 128;
    const g = k.getContext('2d');

    // Fond capsule translucide
    g.fillStyle = 'rgba(4, 12, 26, 0.72)';
    g.strokeStyle = colorHex || '#00f2ff';
    g.lineWidth = 3;
    g.beginPath();
    g.roundRect(10, 10, 492, 108, 24);
    g.fill();
    g.stroke();

    // Ligne 1 : Nom de la planète
    g.font = 'bold 36px "Sora", sans-serif';
    g.fillStyle = '#ffffff';
    g.textAlign = 'center';
    g.fillText(name.toUpperCase(), 256, 56);

    // Ligne 2 : Sous-titre thématique de Nick
    g.font = '600 24px "IBM Plex Mono", monospace';
    g.fillStyle = colorHex || '#00f2ff';
    g.fillText(subtitle.toUpperCase(), 256, 96);

    const tex = new THREE.CanvasTexture(k);
    tex.minFilter = THREE.LinearFilter;
    const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.9, depthWrite: false });
    const s = new THREE.Sprite(mat);
    s.scale.set(180, 45, 1);
    return s;
  }

  function toast(title, sub) {
    if (!toastsContainer) return;
    const el = document.createElement('div');
    el.className = 'hs-toast';
    el.innerHTML = `<b>${title}</b> · ${sub}`;
    toastsContainer.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-10px)';
      setTimeout(() => el.remove(), 400);
    }, 3800);
  }

  function addPoi(name, desc, pos, r, bodyRadius) {
    const p = { name, desc, pos: pos.isVector3 ? pos : new THREE.Vector3(...pos), r, found: false };
    pois.push(p);
    if (bodyRadius) bodies.push({ pos: p.pos, r: bodyRadius });
  }

  /* ───────────────────────── Planètes ───────────────────────── */
  function planet(o) {
    const g = new THREE.Group(); g.position.set(...o.pos);
    const body = new THREE.Mesh(
      new THREE.SphereGeometry(o.r, 48, 32),
      new THREE.MeshStandardMaterial({ map: ptex(o.cols, o.b), roughness: .9, emissive: o.em || 0, emissiveIntensity: .5 })
    );
    g.add(body);
    g.add(new THREE.Mesh(
      new THREE.SphereGeometry(o.r * 1.12, 32, 24),
      new THREE.MeshBasicMaterial({ color: o.atm, transparent: true, opacity: .07, side: THREE.BackSide, blending: THREE.AdditiveBlending, depthWrite: false })
    ));
    if (o.ring) {
      const rm = new THREE.Mesh(
        ringGeo(o.r * 1.4, o.r * 2.4, 96),
        new THREE.MeshBasicMaterial({ map: bandTex([[0, 'rgba(0,0,0,0)'], [.1, '#d9c39a'], [.35, '#8a7658'], [.5, 'rgba(0,0,0,0)'], [.6, '#e8d5ae'], [.9, '#a89070'], [1, 'rgba(0,0,0,0)']], 30), transparent: true, side: THREE.DoubleSide, depthWrite: false, opacity: .9 })
      );
      rm.rotation.x = Math.PI / 2 - .35; rm.rotation.y = .2; g.add(rm);
    }
    (o.moons || []).forEach((m, i) => {
      const mm = new THREE.Mesh(new THREE.SphereGeometry(m.r, 16, 12), new THREE.MeshStandardMaterial({ color: m.c, roughness: 1 }));
      g.add(mm);
      const d = o.r * (2.6 + i * .9), sp = R(.15, .35), ph = R(0, TAU);
      anim.push(t => mm.position.set(Math.cos(t * sp + ph) * d, Math.sin(t * sp + ph) * d * .15, Math.sin(t * sp + ph) * d));
    });

    // Label 3D discret au-dessus de la planète
    const holoLabel = makeHoloLabel(o.name, o.sub || "Information", o.themeCol || "#00f2ff");
    holoLabel.position.set(0, o.r * 1.35 + 25, 0);
    g.add(holoLabel);

    anim.push((t, dt) => body.rotation.y += .03 * dt);
    scene.add(g);
    addPoi(o.name, o.desc, g.position, o.r, o.r * 1.05);

    // Enregistrement pour l'affichage de proximité
    bodies.push({
      pos: g.position,
      r: o.r * 1.05,
      name: o.name,
      sub: o.sub,
      info: o.info,
      type: 'planet'
    });
  }

  /* ───────────────────────── Construction de l'Univers ───────────────────────── */
  function createUniverse() {
    // 1. Étoiles
    const SN = 7000, sg = new THREE.BufferGeometry(), sp = new Float32Array(SN * 3), sc = new Float32Array(SN * 3);
    for (let i = 0; i < SN; i++) {
      sp.set([R(-14000, 14000), R(-14000, 14000), R(-15000, 6000)], i * 3);
      const v = Math.pow(Math.random(), 2.5) * .5 + .08;
      sc.set([v * .8, v * .9, v], i * 3);
    }
    sg.setAttribute('position', new THREE.BufferAttribute(sp, 3));
    sg.setAttribute('color', new THREE.BufferAttribute(sc, 3));
    stars = new THREE.Points(sg, new THREE.PointsMaterial({ size: 1.6, vertexColors: true, fog: false, sizeAttenuation: false }));
    scene.add(stars);

    // 2. Projets du Portfolio
    const rawProjects = DATA.projects && DATA.projects.length ? DATA.projects : [
      { title: "QUANTUM ARCH", kind: "Architecture Système", desc: "Structure monolithique utilisant des shaders temps réel.", stack: "Python · Three.js" },
      { title: "CYBER VEINS", kind: "Flux Réseau & IA", desc: "Réseau de flux de données organiques modélisé en 3D.", stack: "Django · WebSockets" },
      { title: "VOID RUNNER", kind: "Jeu Embarqué", desc: "Expérience de vitesse pure dans un environnement variable.", stack: "Mobile · C++" },
      { title: "ETHER POINT", kind: "Reconnaissance Gestuelle", desc: "IA locale sans connexion externe pour objets connectés.", stack: "PyTorch · OpenCV" }
    ];
    const PROJECT_COLORS = [0x00f2ff, 0xff0077, 0x77ff00, 0xffaa00, 0x8b5cf6, 0x2dd4bf];
    const projectPositions = [
      [0, 50, -2200],
      [800, 260, -4200],
      [-700, -150, -6200],
      [400, 100, -8200],
      [-500, 200, -10000]
    ];

    rawProjects.forEach((d, i) => {
      const pos = projectPositions[i % projectPositions.length];
      const col = PROJECT_COLORS[i % PROJECT_COLORS.length];
      const g = new THREE.Group();
      const m = new THREE.Mesh(
        new THREE.TorusKnotGeometry(130, 34, 140, 20),
        new THREE.MeshPhongMaterial({ color: 0, emissive: col, emissiveIntensity: .55, shininess: 100, wireframe: i % 2 === 0 })
      );
      g.add(m);
      g.add(new THREE.Points(new THREE.SphereGeometry(240, 24, 24), new THREE.PointsMaterial({ color: col, size: 3.5, transparent: true, opacity: .12 })));
      g.add(spr(col, 420, .14));

      // Petit label holographique au-dessus du projet
      const pLabel = makeHoloLabel(d.title, d.kind || "Projet", '#' + col.toString(16).padStart(6, '0'));
      pLabel.position.set(0, 180, 0);
      g.add(pLabel);

      g.position.set(pos[0], pos[1], pos[2]);
      scene.add(g);
      projects.push({
        mesh: g,
        data: {
          title: d.title,
          sub: d.kind || "Projet Réalisé",
          desc: (d.stack ? `Stack : ${d.stack} — ` : '') + (d.desc || "Conçu et développé de bout en bout."),
          color: col
        }
      });
      addPoi(d.title, d.kind || "Projet Portfolio", g.position, 160, 120);
    });

    // 3. Tunnel d'anneaux
    for (let i = 0; i < 20; i++) {
      const r = new THREE.Mesh(new THREE.TorusGeometry(1000, 2.5, 16, 100), new THREE.MeshBasicMaterial({ color: 0x00f2ff, transparent: true, opacity: .1 }));
      r.position.z = -i * 1000; scene.add(r);
      anim.push(t => r.material.opacity = .06 + .04 * Math.sin(t * 2 - i * .5));
    }

    // 4. Nébuleuses
    const cts = [cloudTex(), cloudTex(), cloudTex()], pal = [0x1b4a7a, 0x2a3a7a, 0x0f5a6a];
    for (let i = 0; i < 8; i++) {
      const s = spr(pal[i % 3], R(1600, 3200), R(.05, .11), cts[i % 3]);
      const sx = Math.random() < .5 ? -1 : 1;
      s.position.set(sx * R(700, 4200), R(-1500, 1500), R(1000, -11000));
      s.material.rotation = R(0, TAU); scene.add(s);
    }

    // 5. Soleil Alpha (Présentation Nick Kakaye)
    const sunP = new THREE.Vector3(-4200, 1500, -1500);
    const sun = new THREE.Mesh(new THREE.SphereGeometry(400, 48, 32), new THREE.MeshBasicMaterial({ color: 0xffe2a0, fog: false }));
    sun.position.copy(sunP); scene.add(sun);
    [[0xffcc88, 2000, .35], [0xffffff, 1200, .8]].forEach(a => {
      const s = spr(a[0], a[1], a[2]); s.position.copy(sunP); scene.add(s);
    });
    const sl = new THREE.PointLight(0xfff0d0, 1.8, 8000); sl.position.copy(sunP); scene.add(sl);

    // Label 3D au-dessus du Soleil
    const sunLabel = makeHoloLabel("SOLEIL ALPHA", "NICK KAKAYE · INGÉNIERIE & IA", "#ffd47a");
    sunLabel.position.set(sunP.x, sunP.y + 520, sunP.z);
    scene.add(sunLabel);
    addPoi('SOLEIL ALPHA', 'Étoile naine jaune, foyer central du portfolio.', sunP, 400, 430);
    bodies.push({
      pos: sunP, r: 430, name: "SOLEIL ALPHA", sub: "NICK KAKAYE",
      info: "Étudiant en Système Informatique & Génie Logiciel à l'ESATIC (Abidjan). Concepteur de solutions IA et logicielles.",
      type: 'planet'
    });

    // 6. Planètes représentant chacune une facette clé de Nick Kakaye
    planet({
      name: 'SATURNIA',
      sub: 'FORMATION ESATIC',
      desc: 'Diplôme et parcours universitaire.',
      info: '3e année Licence Système Informatique & Génie Logiciel — ESATIC, Abidjan (2026).',
      r: 240, pos: [1300, 100, -1500],
      cols: ['#c8a165', '#e3c78f', '#a8793f', '#d9b87a'], b: .35, atm: 0xccaa88, ring: 1,
      themeCol: '#ffd47a', moons: [{ r: 28, c: '#bbbbbb' }]
    });

    planet({
      name: 'VERDANIA',
      sub: 'CE QUI M\'ANIME',
      desc: 'Vision et passion technologique.',
      info: 'Second Brain, Jarvis, IA locale et vision par ordinateur : donner de l\'intelligence aux objets du quotidien.',
      r: 200, pos: [-900, -600, -900],
      cols: ['#1c4f8f', '#2b7bc4', '#2f8f4a', '#1c4f8f', '#eeeeee'], b: .9, atm: 0x7799cc,
      themeCol: '#2dd4bf', moons: [{ r: 34, c: '#cccccc' }]
    });

    planet({
      name: 'JOVIS-9',
      sub: 'COMPÉTENCES CLÉS',
      desc: 'Boîte à outils et technologies maîtrisées.',
      info: 'Python (Django, PyTorch), Mobile (Flutter), Systèmes C/C++, Docker, PostgreSQL, WebSockets.',
      r: 420, pos: [-2000, -250, -3600],
      cols: ['#d98b5f', '#f1d3b0', '#9b5a3c', '#e8b98d', '#7a4a3a'], b: .5, atm: 0xaa8866,
      themeCol: '#f59e0b', moons: [{ r: 40, c: '#c9b79c' }, { r: 25, c: '#99aabb' }]
    });

    planet({
      name: 'IGNIS',
      sub: 'CERTIFICATIONS',
      desc: 'Reconnaissances et diplômes certifiés.',
      info: '5 Certifications Cisco obtenues en 2026 (CCNA, CyberOps, Python, Data Science, IoT).',
      r: 190, pos: [1700, 500, -5700],
      cols: ['#1a1210', '#3a2218', '#5a3524', '#241812'], b: 1.7, atm: 0x886655, em: 0x180804,
      themeCol: '#f43f5e'
    });

    planet({
      name: 'CRYOS',
      sub: 'CONTACT & STAGE',
      desc: 'Disponibilité professionnelle.',
      info: 'Disponible pour un stage de fin de cycle. Basé à Abidjan — ouvert au télétravail international.',
      r: 160, pos: [-1500, 350, -6300],
      cols: ['#cfeaff', '#9ccbf0', '#ffffff', '#78a8d8'], b: .8, atm: 0x99bbcc,
      themeCol: '#38bdf8', moons: [{ r: 20, c: '#ffffff' }]
    });

    // 7. ── LE TROU NOIR (SINGULARITÉ & PORTE DE SORTIE VERS UI C) ──
    bhPos = new THREE.Vector3(2300, -100, -8000);
    bh = new THREE.Group();
    bh.position.copy(bhPos);

    // Cœur sombre absolu
    bh.add(new THREE.Mesh(new THREE.SphereGeometry(120, 32, 24), new THREE.MeshBasicMaterial({ color: 0x000000 })));
    // Anneau de photons brillant
    bh.add(new THREE.Mesh(new THREE.TorusGeometry(132, 6, 16, 100), new THREE.MeshBasicMaterial({ color: 0xffe9b0 })));

    // Disque d'accrétion tournant
    bhDisk = new THREE.Mesh(
      ringGeo(160, 680, 128),
      new THREE.MeshBasicMaterial({
        map: bandTex([[0, '#ffffff'], [.22, '#ffd47a'], [.55, 'rgba(255,100,40,.6)'], [1, 'rgba(0,0,0,0)']], 60),
        transparent: true, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending
      })
    );
    bhDisk.rotation.x = Math.PI / 2.15;
    bh.add(bhDisk);

    // Halos de plasma
    bhGlow = spr(0xffaa55, 1400, .22);
    bh.add(bhGlow);

    // Anneaux gravitationnels pulsants
    bhRing = new THREE.Mesh(
      new THREE.TorusGeometry(380, 4, 8, 120),
      new THREE.MeshBasicMaterial({ color: 0xffe9b0, transparent: true, opacity: .45, blending: THREE.AdditiveBlending, depthWrite: false })
    );
    bhRing.rotation.x = Math.PI / 2.3;
    bh.add(bhRing);

    // Faisceau balise vertical
    const beaconGeo = new THREE.CylinderGeometry(8, 45, 12000, 16);
    const beaconMat = new THREE.MeshBasicMaterial({
      color: 0xffe488, transparent: true, opacity: 0.28, blending: THREE.AdditiveBlending, depthWrite: false
    });
    bhBeacon = new THREE.Mesh(beaconGeo, beaconMat);
    bh.add(bhBeacon);

    // Ondes d'énergie
    const waveMat = new THREE.MeshBasicMaterial({ color: 0x00f2ff, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false });
    for (let w = 0; w < 3; w++) {
      const rw = new THREE.Mesh(new THREE.RingGeometry(200, 240, 64), waveMat.clone());
      rw.rotation.x = Math.PI / 2;
      rw.userData.offset = w * 0.33;
      bh.add(rw);
      anim.push((t) => {
        const ph = ((t * 0.4 + rw.userData.offset) % 1);
        rw.scale.setScalar(1 + ph * 6);
        rw.material.opacity = (1 - ph) * 0.4;
      });
    }

    // Label 3D au-dessus du trou noir
    const bhLabel = makeHoloLabel("SINGULARITÉ", "PORTE VERS L'ATELIER", "#ffcc00");
    bhLabel.position.set(0, 360, 0);
    bh.add(bhLabel);

    // Grande flèche holographique 3D pointant vers le centre du trou noir
    const arrowGroup = new THREE.Group();
    const arrowConeGeo = new THREE.ConeGeometry(52, 130, 16);
    arrowConeGeo.rotateX(Math.PI); // Pointe directement vers le bas vers le trou noir
    const arrowMat = new THREE.MeshBasicMaterial({
      color: 0xffd43b, transparent: true, opacity: 0.95, blending: THREE.AdditiveBlending
    });
    const arrowCone = new THREE.Mesh(arrowConeGeo, arrowMat);
    arrowGroup.add(arrowCone);

    const arrowShaftGeo = new THREE.CylinderGeometry(14, 14, 150, 16);
    const arrowShaft = new THREE.Mesh(arrowShaftGeo, arrowMat);
    arrowShaft.position.y = 110;
    arrowGroup.add(arrowShaft);

    // Chevrons lumineux qui glissent le long de la flèche vers le trou noir
    for (let c = 0; c < 3; c++) {
      const ch = new THREE.Mesh(new THREE.TorusGeometry(36 + c * 8, 3.5, 8, 32), new THREE.MeshBasicMaterial({
        color: 0x00f2ff, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending
      }));
      ch.rotation.x = Math.PI / 2;
      ch.userData.offset = c * 0.33;
      arrowGroup.add(ch);
      anim.push((t) => {
        const p = ((t * 0.9 + ch.userData.offset) % 1);
        ch.position.y = 180 - p * 230;
        ch.material.opacity = (1 - p) * 0.9;
      });
    }

    arrowGroup.position.set(0, 520, 0);
    bh.add(arrowGroup);
    anim.push((t) => {
      arrowGroup.position.y = 520 + Math.sin(t * 3.6) * 40;
      arrowCone.rotation.y += 0.03;
    });

    scene.add(bh);
    anim.push((t, dt) => {
      bhDisk.rotation.z += .4 * dt;
      bhRing.rotation.z -= .2 * dt;
      bhBeacon.rotation.y += .15 * dt;
      bhGlow.scale.setScalar(1300 + Math.sin(t * 3) * 150);
    });
    addPoi('SINGULARITÉ', 'Porte d\'accès vers l\'Atelier. Rentre dedans pour franchir le seuil.', bhPos, 200, 0);

    // 8. Galaxie spirale
    const N = 12000, gp = new Float32Array(N * 3), gc = new Float32Array(N * 3), ca = new THREE.Color(0xc8b8a0), cb = new THREE.Color(0x7088b8), cc = new THREE.Color();
    for (let i = 0; i < N; i++) {
      const r = Math.pow(Math.random(), .6) * 2200, ang = (i % 3) / 3 * TAU + r * .0028, s = (1 - r / 2600) * 140 + 10;
      gp.set([Math.cos(ang) * r + (Math.random() - .5) * s * 3, (Math.random() - .5) * s, Math.sin(ang) * r + (Math.random() - .5) * s * 3], i * 3);
      cc.copy(ca).lerp(cb, r / 2200); gc.set([cc.r, cc.g, cc.b], i * 3);
    }
    const gg = new THREE.BufferGeometry();
    gg.setAttribute('position', new THREE.BufferAttribute(gp, 3));
    gg.setAttribute('color', new THREE.BufferAttribute(gc, 3));
    const gal = new THREE.Group(), gpts = new THREE.Points(gg, new THREE.PointsMaterial({ size: 20, vertexColors: true, transparent: true, opacity: .35, blending: THREE.AdditiveBlending, depthWrite: false, fog: false }));
    gal.add(gpts); gal.add(spr(0xffddaa, 700, .3));
    gal.position.set(4500, 2200, -9000); gal.rotation.set(.9, 0, .3);
    scene.add(gal);
    anim.push((t, dt) => gpts.rotation.y += .02 * dt);
    addPoi('GALAXIE SPIRALE', 'Cent millions d\'étoiles en rotation silencieuse.', gal.position, 1800, 0);

    // 9. Station orbitale
    const st = new THREE.Group(), M = new THREE.MeshStandardMaterial({ color: 0x99a4b5, metalness: .8, roughness: .35 }), wheel = new THREE.Group();
    wheel.add(new THREE.Mesh(new THREE.TorusGeometry(110, 9, 12, 48), M));
    const lit = new THREE.Mesh(new THREE.TorusGeometry(110, 2.5, 6, 64), new THREE.MeshBasicMaterial({ color: 0x00f2ff })); lit.position.z = 10; wheel.add(lit);
    for (let i = 0; i < 4; i++) { const sk = new THREE.Mesh(new THREE.BoxGeometry(220, 5, 5), M); sk.rotation.z = i * Math.PI / 4; wheel.add(sk); }
    st.add(wheel);
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(22, 22, 170, 16).rotateX(Math.PI / 2), M); st.add(hub);
    const b1 = spr(0xffffff, 35), b2 = spr(0x00f2ff, 35); b1.position.z = 90; b2.position.z = -90; st.add(b1, b2);
    st.position.set(-1100, 400, -2800); st.rotation.set(.4, .6, 0); scene.add(st);
    anim.push((t, dt) => { wheel.rotation.z += .25 * dt; b1.material.opacity = Math.sin(t * 4) > 0 ? 1 : .1; b2.material.opacity = Math.sin(t * 4 + 2) > 0 ? 1 : .1; });

    const stLabel = makeHoloLabel("ARCHE ORBITALE", "ATELIER & EXPERTISE", "#2dd4bf");
    stLabel.position.set(0, 190, 0);
    st.add(stLabel);
    addPoi('ARCHE ORBITALE', 'Station habitée. Base avancée de recherche.', st.position, 130, 150);

    for (let i = 0; i < 2; i++) {
      const d = new THREE.Group(); d.add(new THREE.Mesh(new THREE.ConeGeometry(6, 28, 6).rotateX(Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xdddddd, metalness: .7, roughness: .3 })));
      const e = spr(0x66ccff, 30); e.position.z = -14; d.add(e); scene.add(d);
      const rad = R(220, 420), sp = R(.2, .5) * (i % 2 ? 1 : -1), ph = R(0, TAU), ti = R(-.6, .6);
      const pos = a => new THREE.Vector3(Math.cos(a) * rad, Math.sin(a * 2) * 50 + Math.sin(a) * rad * ti, Math.sin(a) * rad).add(st.position);
      anim.push(t => { const a = t * sp + ph; d.position.copy(pos(a)); d.lookAt(pos(a + (sp > 0 ? .05 : -.05))); });
    }

    // 10. Champ d'astéroïdes
    const N2 = 180;
    asteroids = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 0), new THREE.MeshStandardMaterial({ color: 0x4a4a4e, roughness: 1, flatShading: true }), N2);
    astD = [];
    for (let i = 0; i < N2; i++) {
      const a = R(0, TAU), r = R(1400, 2200);
      astD.push({ p: [Math.cos(a) * r, R(-140, 140) - 200, Math.sin(a) * r - 4800], s: R(6, 45), k: [R(.5, 1.4), R(.5, 1.4)], r: [R(0, TAU), R(0, TAU), R(0, TAU)], v: R(-.5, .5) });
    }
    scene.add(asteroids);
    addPoi('CEINTURE KUIPER-X', 'Des milliers de roches à frôler en pilotant avec soin.', [0, -200, -3000], 150, 0);

    // 11. Forêt de cristaux
    const cg = new THREE.Group(), cm = new THREE.InstancedMesh(new THREE.OctahedronGeometry(1), new THREE.MeshBasicMaterial({ transparent: true, opacity: .3, blending: THREE.AdditiveBlending, depthWrite: false }), 40), col = new THREE.Color();
    for (let i = 0; i < 40; i++) {
      const s = R(15, 60), v = new THREE.Vector3(R(-1, 1), R(-1, 1), R(-1, 1)).normalize().multiplyScalar(R(0, 450));
      dummy.position.copy(v); dummy.rotation.set(R(0, TAU), R(0, TAU), R(0, TAU)); dummy.scale.set(s * .5, s * 2.2, s * .5);
      dummy.updateMatrix(); cm.setMatrixAt(i, dummy.matrix); cm.setColorAt(i, col.setHSL(.52, .5, R(.35, .55)));
    }
    cg.add(cm); cg.position.set(-1300, -250, -8200); scene.add(cg);
    anim.push((t, dt) => cg.rotation.y += .05 * dt);
    addPoi('CRISTAUX D\'ÉTHER', 'Cristaux vivants qui chantent à basse fréquence.', cg.position, 450, 0);

    // 12. Comètes
    for (let i = 0; i < 2; i++) {
      const c = new THREE.Group(), h = spr(0xddeeff, 60); c.add(h);
      const tl = new THREE.Mesh(new THREE.ConeGeometry(16, 700, 10, 1, true).rotateX(-Math.PI / 2).translate(0, 0, -350), new THREE.MeshBasicMaterial({ color: 0xaaccff, transparent: true, opacity: .12, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
      c.add(tl);
      c.position.set(R(-4000, 4000), R(-1500, 1500), R(500, -10000));
      c.userData.v = new THREE.Vector3(R(-1, 1), R(-.3, .3), R(-1, 1)).normalize().multiplyScalar(R(250, 500));
      scene.add(c); comets.push(c);
    }

    // 13. Poussière locale de vitesse
    dustP = new Float32Array(300 * 3);
    for (let i = 0; i < dustP.length; i++) dustP[i] = R(-700, 700);
    const dg = new THREE.BufferGeometry(); dg.setAttribute('position', new THREE.BufferAttribute(dustP, 3));
    dust = new THREE.Points(dg, new THREE.PointsMaterial({ color: 0xaee8ff, size: 2.5, transparent: true, opacity: .3, fog: false, sizeAttenuation: false }));
    dust.frustumCulled = false; scene.add(dust);
  }

  /* ───────────────────────── Initialisation Three.js ───────────────────────── */
  function init3D() {
    if (!hasTHREE) return;
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000105);
    scene.fog = new THREE.FogExp2(0x000105, 0.00012);

    camera = new THREE.PerspectiveCamera(75, innerWidth / innerHeight, 0.1, 40000);
    camera.rotation.order = 'YXZ';
    camera.position.set(0, 0, 300);

    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(innerWidth, innerHeight);
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));

    clock = new THREE.Clock();
    scene.add(new THREE.AmbientLight(0x334466, 0.9));
    const cl = new THREE.PointLight(0x00f2ff, 1.2, 2000);
    camera.add(cl); scene.add(camera);

    createUniverse();
    bindEvents();
    if (boot) boot.classList.add('is-done');
    animate();
  }

  /* ───────────────────────── Gestion de l'orientation et des entrées ───────────────────────── */
  function bindEvents() {
    // Molette : propulsion
    addEventListener('wheel', e => {
      if (activeUI !== 'b') return;
      camera.getWorldDirection(tmpD);
      vel.addScaledVector(tmpD, e.deltaY * 2.2);
    }, { passive: true });

    // Clavier
    addEventListener('keydown', e => {
      if (activeUI !== 'b') return;
      keys[e.code] = true;
      startAudio();
      if (e.code === 'KeyM') toggleAudio();
      if (e.code === 'Space') e.preventDefault();
    });
    addEventListener('keyup', e => { keys[e.code] = false; });

    // Clic / Touch sur l'écran pour orienter la vue à 360° librement
    canvas.addEventListener('pointerdown', e => {
      if (activeUI !== 'b') return;
      drag = true;
      lx = e.clientX; ly = e.clientY;
      startAudio();
    });
    addEventListener('pointerup', () => { drag = false; });
    addEventListener('pointercancel', () => { drag = false; });
    addEventListener('pointermove', e => {
      if (!drag || activeUI !== 'b') return;
      // Rotation libre horizontale à 360° et verticale souple
      yaw -= (e.clientX - lx) * 0.003;
      pitch = Math.max(-1.5, Math.min(1.5, pitch - (e.clientY - ly) * 0.003));
      lx = e.clientX; ly = e.clientY;
    });

    // Joystick virtuel Mobile (pouce gauche)
    if (joy) {
      const updateJoy = e => {
        const rect = joy.getBoundingClientRect();
        const cx = rect.left + rect.width / 2, cy = rect.top + rect.height / 2;
        const rad = rect.width * 0.42;
        let dx = (e.clientX - cx) / rad, dy = (e.clientY - cy) / rad;
        const len = Math.hypot(dx, dy);
        if (len > 1) { dx /= len; dy /= len; }
        pad.x = dx; pad.y = dy;
        if (joyKnob) joyKnob.style.transform = `translate(${dx * rad}px, ${dy * rad}px)`;
      };
      joy.addEventListener('pointerdown', e => {
        if (activeUI !== 'b') return;
        pad.on = true;
        pad.touchId = e.pointerId;
        startAudio();
        updateJoy(e);
        try { joy.setPointerCapture(e.pointerId); } catch (_) {}
      });
      joy.addEventListener('pointermove', e => {
        if (pad.on && pad.touchId === e.pointerId) updateJoy(e);
      });
      const resetJoy = e => {
        if (pad.touchId === e.pointerId) {
          pad.on = false; pad.x = 0; pad.y = 0; pad.touchId = null;
          if (joyKnob) joyKnob.style.transform = 'none';
        }
      };
      joy.addEventListener('pointerup', resetJoy);
      joy.addEventListener('pointercancel', resetJoy);
    }

    // Boutons d'altitude mobile (pouce droit)
    const setUpDown = (id, dir) => {
      const btn = $(id);
      if (!btn) return;
      btn.addEventListener('pointerdown', e => { e.preventDefault(); pad.updown = dir; btn.classList.add('is-active'); });
      const clear = () => { pad.updown = 0; btn.classList.remove('is-active'); };
      btn.addEventListener('pointerup', clear);
      btn.addEventListener('pointercancel', clear);
    };
    setUpDown('hs-joy-up', 1);
    setUpDown('hs-joy-down', -1);

    // Redimensionnement
    addEventListener('resize', () => {
      if (!camera || !renderer) return;
      camera.aspect = innerWidth / innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(innerWidth, innerHeight);
    });
  }

  /* ───────────────────────── Transmission Planétaire & Projet HUD ───────────────────────── */
  function showPlanetInfo(title, subtitle, desc) {
    if (!planetHudCard) return;
    if (phBadge) phBadge.innerText = 'TRANSMISSION STELLAIRE';
    if (phName) phName.innerText = `${title} · ${subtitle}`;
    if (phDesc) phDesc.innerText = desc;
    planetHudCard.classList.add('active');

    clearTimeout(activeCardTimeout);
    activeCardTimeout = setTimeout(() => {
      if (planetHudCard) planetHudCard.classList.remove('active');
    }, 4500);
  }

  /* ───────────────────────── Radar ───────────────────────── */
  function drawRadar() {
    if (!radar) return;
    const g = radar.getContext('2d'), W = radar.width, cx = W / 2, cy = W / 2, sc = (W * 0.42) / 6500;
    const cy2 = Math.cos(yaw), sy = Math.sin(yaw);
    g.clearRect(0, 0, W, W);

    // Cercles radar
    g.strokeStyle = 'rgba(0, 242, 255, 0.28)';
    g.beginPath();
    g.arc(cx, cy, W * 0.22, 0, TAU);
    g.arc(cx, cy, W * 0.44, 0, TAU);
    g.moveTo(cx, 4); g.lineTo(cx, W - 4);
    g.moveTo(4, cy); g.lineTo(W - 4, cy);
    g.stroke();

    const dot = (p, col, s) => {
      const vx = p.x - camera.position.x, vz = p.z - camera.position.z;
      let rx = (vx * cy2 - vz * sy) * sc, fy = (-vx * sy - vz * cy2) * sc;
      const L = Math.hypot(rx, fy);
      const limit = W * 0.45;
      if (L > limit) { rx *= limit / L; fy *= limit / L; }
      g.fillStyle = col;
      g.beginPath();
      g.arc(cx + rx, cy - fy, s, 0, TAU);
      g.fill();
    };

    // POIs & projets
    pois.forEach(p => dot(p.pos, p.found ? '#00f2ff' : '#ffffff', p.found ? 2.5 : 2));
    projects.forEach(p => dot(p.mesh.position, '#' + p.data.color.toString(16).padStart(6, '0'), 3));

    // Trou noir sur le radar : éclat doré pulsant
    if (bhPos) {
      const vx = bhPos.x - camera.position.x, vz = bhPos.z - camera.position.z;
      let rx = (vx * cy2 - vz * sy) * sc, fy = (-vx * sy - vz * cy2) * sc;
      const L = Math.hypot(rx, fy);
      const limit = W * 0.45;
      if (L > limit) { rx *= limit / L; fy *= limit / L; }
      g.fillStyle = '#ffcc00';
      g.beginPath(); g.arc(cx + rx, cy - fy, 4, 0, TAU); g.fill();
      g.strokeStyle = 'rgba(255, 204, 0, 0.6)';
      g.beginPath(); g.arc(cx + rx, cy - fy, 6 + Math.sin(Date.now() * 0.008) * 2, 0, TAU); g.stroke();
    }

    // Vaisseau
    g.fillStyle = '#fff';
    g.beginPath();
    g.moveTo(cx, cy - 5); g.lineTo(cx - 3, cy + 3); g.lineTo(cx + 3, cy + 3);
    g.fill();
  }

  /* ───────────────────────── Franchir le trou noir (UI B -> UI C) ───────────────────────── */
  function warpToAtelier() {
    if (warping) return;
    warping = true;
    toast('HORIZON FRANCHI', 'Entrée dans l\'Atelier...');
    if (flash) flash.style.opacity = '1';
    setTimeout(() => {
      switchUI('c');
      if (flash) flash.style.opacity = '0';
      warping = false;
    }, 600);
  }

  /* ───────────────────────── Boucle principale 3D ───────────────────────── */
  function animate() {
    requestAnimationFrame(animate);
    if (!renderer || !scene || !camera) return;

    const dt = Math.min(clock.getDelta(), 0.05);
    const t = clock.elapsedTime;

    if (activeUI === 'b') {
      const boost = (keys.ShiftLeft || keys.ShiftRight);
      const acc = (boost ? 4200 : 1800) * dt;

      // Vecteurs directionnels
      camera.getWorldDirection(tmpF);
      tmpR.crossVectors(tmpF, UP).normalize();

      // Déplacements clavier ZQSD / WASD
      if (keys.KeyW || keys.KeyZ) vel.addScaledVector(tmpF, acc);
      if (keys.KeyS) vel.addScaledVector(tmpF, -acc);
      if (keys.KeyD) vel.addScaledVector(tmpR, acc);
      if (keys.KeyA || keys.KeyQ) vel.addScaledVector(tmpR, -acc);
      if (keys.Space) vel.addScaledVector(UP, acc);
      if (keys.KeyC || keys.ControlLeft) vel.addScaledVector(UP, -acc);

      // Déplacements Joystick virtuel (Mobile)
      if (pad.on && (Math.abs(pad.x) > 0.04 || Math.abs(pad.y) > 0.04)) {
        vel.addScaledVector(tmpF, -pad.y * acc * 1.25);
        vel.addScaledVector(tmpR, pad.x * acc * 1.25);
      }
      if (pad.updown) {
        vel.addScaledVector(UP, pad.updown * acc);
      }

      // Orientation flèches
      yaw += ((keys.ArrowLeft ? 1 : 0) - (keys.ArrowRight ? 1 : 0)) * 1.6 * dt;
      pitch = Math.max(-1.5, Math.min(1.5, pitch + ((keys.ArrowUp ? 1 : 0) - (keys.ArrowDown ? 1 : 0)) * 1.6 * dt));

      // Lissage caméra
      const k = 1 - Math.exp(-12 * dt);
      camera.rotation.y += (yaw - camera.rotation.y) * k;
      camera.rotation.x += (pitch - camera.rotation.x) * k;

      // ── Quête & Gravité du Trou Noir ──
      if (bhPos) {
        tmpD.subVectors(bhPos, camera.position);
        const bd = tmpD.length();

        // Distance affichée
        if (questDist) questDist.innerText = `${Math.round(bd)} u`;
        if (questPill) questPill.classList.toggle('is-near', bd < 2500);

        // Flèche de quête 2D pointant vers le trou noir
        if (questArrow) {
          const dx = tmpD.dot(tmpR);
          const dy = tmpD.dot(UP);
          const fwd = tmpD.dot(tmpF);
          let ang = Math.atan2(dx, dy);
          if (fwd < 0) ang += (dx >= 0 ? Math.PI : -Math.PI);
          const deg = (ang * 180 / Math.PI) - 90;
          questArrow.style.transform = `rotate(${deg}deg)`;
        }

        // Attraction gravitationnelle
        if (bd < 2200) {
          vel.addScaledVector(tmpD.normalize(), Math.pow(1 - bd / 2200, 2) * 2800 * dt);
          if (bd < 125) warpToAtelier();
        }
      }

      // Vitesse max et amortissement
      let sp = vel.length(), mx = boost ? 2600 : 1400;
      if (sp > mx) vel.multiplyScalar(mx / sp);
      vel.multiplyScalar(Math.exp(-1.3 * dt));
      sp = vel.length();
      camera.position.addScaledVector(vel, dt);

      // Collisions douces avec les corps célestes et déclenchement de transmission
      for (const b of bodies) {
        tmpD.subVectors(camera.position, b.pos);
        const L = tmpD.length();
        if (L < b.r + 25) {
          camera.position.copy(b.pos).addScaledVector(tmpD.normalize(), b.r + 25);
          vel.multiplyScalar(0.3);
        }
        // Si on est à proximité d'une planète : transmission concise HUD !
        if (b.type === 'planet' && b.info && L < b.r * 2.8 + 180) {
          showPlanetInfo(b.name, b.sub || '', b.info);
        }
      }

      // Effet de vitesse (FOV)
      camera.fov += ((75 + Math.min(35, sp / 2600 * 35 * 1.4)) - camera.fov) * k;
      camera.updateProjectionMatrix();

      // Poussière spatiale
      for (let i = 0; i < dustP.length; i += 3) {
        for (let j = 0; j < 3; j++) {
          const c = camera.position.getComponent(j);
          dustP[i + j] = ((dustP[i + j] - c + 700) % 1400 + 1400) % 1400 - 700 + c;
        }
      }
      dust.geometry.attributes.position.needsUpdate = true;

      // Projets à proximité
      projects.forEach(p => {
        p.mesh.rotation.y += 0.01;
        p.mesh.rotation.x += 0.005;
        if (camera.position.distanceTo(p.mesh.position) < 700) {
          showPlanetInfo(p.data.title, p.data.sub, p.data.desc);
        }
      });

      // Découvertes & Cible
      let near = null, nd = 1e9;
      pois.forEach(p => {
        const d = camera.position.distanceTo(p.pos);
        if (d < nd) { nd = d; near = p; }
        if (!p.found && d < p.r * 3 + 400) {
          p.found = true;
          toast('DÉCOUVERTE', p.name);
        }
      });

      if (targetInfo && near) {
        targetInfo.innerText = `CIBLE : ${near.name} · ${Math.round(nd)} u`;
      }
      if (speedometer) {
        speedometer.innerText = `VITESSE: ${(sp / 100).toFixed(2)}`;
      }

      drawRadar();

      if (audio && audio.on) {
        audio.f.frequency.setTargetAtTime(300 + sp * 1.3, audio.A.currentTime, 0.2);
      }
    }

    // Animations des corps cosmiques
    stars.rotation.z += 0.0004 * dt * 60;
    anim.forEach(f => f(t, dt));
    comets.forEach(c => {
      c.position.addScaledVector(c.userData.v, dt);
      c.lookAt(c.position.clone().add(c.userData.v));
      if (c.position.distanceTo(camera.position) > 9000) {
        c.position.copy(camera.position).add(new THREE.Vector3(R(-6000, 6000), R(-2000, 2000), R(-6000, 6000)));
      }
    });
    if (asteroids) {
      astD.forEach((a, i) => {
        dummy.position.set(...a.p);
        dummy.rotation.set(a.r[0] + t * a.v, a.r[1] + t * a.v * 0.7, a.r[2]);
        dummy.scale.set(a.s * a.k[0], a.s, a.s * a.k[1]);
        dummy.updateMatrix();
        asteroids.setMatrixAt(i, dummy.matrix);
      });
      asteroids.instanceMatrix.needsUpdate = true;
    }

    if (activeUI === 'b') {
      renderer.render(scene, camera);
    }
  }

  /* ───────────────────────── Gestionnaire d'écrans UI A / B / C ───────────────────────── */
  function switchUI(target) {
    if (!app) return;
    activeUI = target;

    // Mise à jour de la classe d'état global
    app.className = `app-ui-${target}`;

    if (target === 'a') {
      document.documentElement.classList.add('no-scroll');
      document.body.classList.add('no-scroll');
      window.scrollTo(0, 0);
      if (audio && audio.on) audio.mg.gain.setTargetAtTime(0, audio.A.currentTime, 0.5);

      // Rejouer la vidéo d'introduction à chaque retour sur UI A (sans boucler)
      const heroVideo = $('heroVideo');
      if (heroVideo) {
        heroVideo.loop = false;
        heroVideo.currentTime = 0;
        const playP = heroVideo.play();
        if (playP && playP.catch) playP.catch(() => {});
      }
    } else if (target === 'b') {
      document.documentElement.classList.add('no-scroll');
      document.body.classList.add('no-scroll');
      window.scrollTo(0, 0);
      if (audio && audio.on) audio.mg.gain.setTargetAtTime(0.3, audio.A.currentTime, 0.5);
      if (camera && renderer) {
        camera.aspect = innerWidth / innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(innerWidth, innerHeight);
      }
    } else if (target === 'c') {
      document.documentElement.classList.remove('no-scroll');
      document.body.classList.remove('no-scroll');
      if (audio && audio.on) audio.mg.gain.setTargetAtTime(0, audio.A.currentTime, 0.5);
      // Remonter en haut de l'Atelier
      const liloEl = $('ui-c');
      if (liloEl) liloEl.scrollIntoView({ behavior: 'smooth' });
    }
  }

  /* ───────────────────────── Câblage des Boutons ───────────────────────── */
  // 1. Bouton "Entrer dans mon univers" (UI A -> UI B)
  const enterBtn = $('btn-enter-universe');
  if (enterBtn) {
    enterBtn.addEventListener('click', () => {
      startAudio();
      if (flash) flash.style.opacity = '1';
      setTimeout(() => {
        switchUI('b');
        if (flash) flash.style.opacity = '0';
        toast('BIENVENUE DANS L\'UNIVERS', 'Quête : Trouve le trou noir pour accéder à l\'Atelier !');
      }, 350);
    });
  }

  // 2. Bouton "Accueil" dans UI B (UI B -> UI A)
  const hsHomeBtn = $('hs-btn-home');
  if (hsHomeBtn) {
    hsHomeBtn.addEventListener('click', () => {
      if (flash) flash.style.opacity = '0.7';
      setTimeout(() => {
        switchUI('a');
        if (flash) flash.style.opacity = '0';
      }, 250);
    });
  }

  // 3. Bouton "Revenir à l'accueil" dans UI C (UI C -> UI A)
  const btnReturnHome = $('btn-return-home');
  if (btnReturnHome) {
    btnReturnHome.addEventListener('click', () => {
      switchUI('a');
    });
  }

  // 4. Bouton "Retourner dans mon univers" dans UI C (UI C -> UI B)
  const btnReturnUniverse = $('btn-return-universe');
  if (btnReturnUniverse) {
    btnReturnUniverse.addEventListener('click', () => {
      startAudio();
      if (flash) flash.style.opacity = '1';
      setTimeout(() => {
        if (camera) camera.position.set(0, 0, 300);
        vel.set(0, 0, 0);
        switchUI('b');
        if (flash) flash.style.opacity = '0';
        toast('RETOUR DANS L\'UNIVERS', 'Cap maintenu vers les étoiles.');
      }, 350);
    });
  }

  // Initialisation
  function init() {
    init3D();
    switchUI('a'); // Démarre en UI A
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
