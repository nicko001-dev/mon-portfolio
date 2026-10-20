/* ============================================================
   Acte II — Espace 3D « Applications intelligentes »
   Inspiré du fichier HTML d'origine (dossier lilo) :
     - nœud de tore en fil de fer + pulsation d'échelle
     - poussière de 5000 étoiles
     - caméra qui suit la souris (lerp) + lookAt
     - libellé de chargement puis sa disparition         (loader)
   Et, piloté par le DÉFILEMENT (comme demandé) :
     - un ZOOM sur le tore (caméra de z 5 vers z 2, comme le CTA du mockup)
     - un virage PROGRESSIF de couleur jusqu'au violet du site
       (turquoise -> violet), avant que le texte n'apparaisse
     - le tout réversible quand on remonte
   Le texte de la section apparaît ensuite, lui aussi au fil du scroll.
   Palette : violet #8b5cf6 et turquoise #2dd4bf.
   ============================================================ */
(() => {
  'use strict';

  const root = document.getElementById('space-runway');
  if (!root) return;
  const canvas = document.getElementById('three-canvas');
  const copy = root.querySelector('.space-copy');
  const loader = root.querySelector('.space-loader');
  // Le contenu révélé en cascade : titre, puis paragraphe, puis bouton.
  const copyKids = copy ? [...copy.querySelectorAll('h2, p, .btn')] : [];
  if (!canvas || !window.THREE) {
    if (copy) copy.style.opacity = '1';
    if (loader) loader.classList.add('is-done');
    return;
  }

  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const clamp01 = x => Math.min(1, Math.max(0, x));
  const smooth01 = x => { const t = clamp01(x); return t * t * (3 - 2 * t); };
  const lerp = (a, b, t) => a + (b - a) * t;

  const VIOLET = new THREE.Color(0x8b5cf6);
  const TEAL = new THREE.Color(0x2dd4bf);
  const BG = 0x050505;

  // Fenêtres du scénario (en progression de section). La section est épinglée
  // jusqu'à ~0.545 : le texte doit donc être entièrement là avant, avec un
  // temps de repos confortable.
  //  0.02 -> 0.50 : zoom + virage de couleur (commence AVANT le texte)
  //  0.16 -> 0.38 : apparition du texte (titre, puis texte, puis bouton)
  //  0.80 -> 1.00 : la section s'efface
  const ZOOM_A = 0.02, ZOOM_B = 0.50;
  const TEXT_A = 0.16, TEXT_B = 0.30, TEXT_STAGGER = 0.04;
  const FADE_A = 0.80, FADE_B = 1.00;

  let scene, camera, renderer, particles, torus, clock;
  let mouseX = 0, mouseY = 0, targetX = 0, targetY = 0;
  let progress = 0, running = false, rafId = 0, firstFrame = true, lastNow = 0;

  function build() {
    const w = canvas.clientWidth || innerWidth;
    const h = canvas.clientHeight || innerHeight;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(BG);
    scene.fog = new THREE.FogExp2(BG, 0.05);

    camera = new THREE.PerspectiveCamera(75, w / h, 0.1, 1000);
    camera.position.z = 5;

    try {
      renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    } catch (err) {
      console.error('[space3d] WebGL indisponible :', err);
      if (loader) loader.classList.add('is-done');
      if (copy) copy.style.opacity = '1';
      return;
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    renderer.setSize(w, h, false);

    // Lumières : violet + turquoise (au lieu du vert + bleu d'origine)
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const pointLight = new THREE.PointLight(VIOLET, 2.2, 50);
    pointLight.position.set(5, 5, 5);
    scene.add(pointLight);
    const secondLight = new THREE.PointLight(TEAL, 1.6, 50);
    secondLight.position.set(-5, -5, 5);
    scene.add(secondLight);

    buildParticles();
    buildCentralObject();

    clock = new THREE.Clock();
    addEventListener('resize', resize, { passive: true });
    if (!reduce && matchMedia('(pointer:fine)').matches) {
      addEventListener('mousemove', onMove, { passive: true });
    }

    if (reduce) paint();
  }

  function buildParticles() {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    for (let i = 0; i < 5000; i++) {
      vertices.push((Math.random() - 0.5) * 20, (Math.random() - 0.5) * 20, (Math.random() - 0.5) * 20);
    }
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    particles = new THREE.Points(geometry, new THREE.PointsMaterial({
      size: 0.02,
      color: 0xffffff,
      transparent: true,
      opacity: 0.5,
      blending: THREE.AdditiveBlending,
    }));
    scene.add(particles);
  }

  function buildCentralObject() {
    // Même matière que le mockup (fil de fer métallique sombre), avec une
    // émission que l'on fera virer du turquoise au violet au fil du scroll.
    const geometry = new THREE.TorusKnotGeometry(1, 0.3, 200, 32);
    const material = new THREE.MeshPhysicalMaterial({
      color: 0x222222,
      metalness: 0.6,
      roughness: 0.2,
      wireframe: true,
      emissive: TEAL.clone(),
      emissiveIntensity: 0.6,
    });
    torus = new THREE.Mesh(geometry, material);
    scene.add(torus);
  }

  function resize() {
    if (!renderer) return;
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
    if (reduce) paint();
  }

  function onMove(e) {
    mouseX = (e.clientX - innerWidth / 2) * 0.001;
    mouseY = (e.clientY - innerHeight / 2) * 0.001;
  }

  function frame(now) {
    if (!running) return;
    rafId = requestAnimationFrame(frame);

    const dt = lastNow ? Math.min(0.05, (now - lastNow) / 1000) : 0.016;
    lastNow = now;
    const t = clock.getElapsedTime();

    // Lerp souris (comme l'original)
    targetX += (mouseX - targetX) * 0.05;
    targetY += (mouseY - targetY) * 0.05;

    // Torus : rotation continue + pulsation d'échelle
    if (torus) {
      torus.rotation.x = t * 0.3;
      torus.rotation.y = t * 0.4;
      torus.rotation.z += targetX * 0.5;
      const scale = 1 + Math.sin(t) * 0.1;
      torus.scale.set(scale, scale, scale);
    }
    // Particules
    if (particles) {
      particles.rotation.y = t * 0.05;
      particles.rotation.x = targetY * 0.2;
    }

    // ZOOM piloté par le scroll : caméra de z 5 -> z 2 (le tore grossit).
    const zoomK = smooth01((progress - ZOOM_A) / (ZOOM_B - ZOOM_A));
    const camZ = lerp(5, 2, zoomK);
    camera.position.x += (targetX * 2 - camera.position.x) * 0.05;
    camera.position.y += (-targetY * 2 - camera.position.y) * 0.05;
    camera.position.z += (camZ - camera.position.z) * 0.12;
    camera.lookAt(scene.position);

    // Couleur progressive : turquoise -> violet du site.
    if (torus) {
      torus.material.emissive.copy(TEAL).lerp(VIOLET, zoomK);
      torus.material.emissiveIntensity = lerp(0.6, 1.15, zoomK);
    }

    renderer.render(scene, camera);
    if (firstFrame) { firstFrame = false; if (loader) loader.classList.add('is-done'); }
  }

  function paint() {
    if (renderer) renderer.render(scene, camera);
    if (firstFrame) { firstFrame = false; if (loader) loader.classList.add('is-done'); }
  }

  function start() {
    if (reduce || running || !renderer) return;
    running = true;
    lastNow = 0;
    clock.start();
    rafId = requestAnimationFrame(frame);
  }
  function stop() {
    running = false;
    if (rafId) cancelAnimationFrame(rafId);
    rafId = 0;
  }

  function onScroll() {
    const top = root.getBoundingClientRect().top + scrollY;
    const span = Math.max(1, root.offsetHeight);
    progress = clamp01((scrollY - top) / span);

    // La section s'efface en toute fin (le tore disparaît avant les particules).
    canvas.style.opacity = (1 - smooth01((progress - FADE_A) / (FADE_B - FADE_A))).toFixed(3);

    // Le texte apparaît APRÈS le début du zoom, bien avant la fin de la
    // section, en cascade : titre, puis paragraphe, puis bouton. Tout est
    // calculé depuis le scroll, donc réversible en remontant.
    if (copy) {
      copy.style.opacity = '1';
      const span = Math.max(1e-3, TEXT_B - TEXT_A);
      for (let i = 0; i < copyKids.length; i++) {
        const el = copyKids[i];
        const k = reduce ? 1 : smooth01((progress - (TEXT_A + i * TEXT_STAGGER)) / span);
        el.style.opacity = k.toFixed(3);
        el.style.transform = 'translateY(' + ((1 - k) * 26).toFixed(1) + 'px)';
        el.style.pointerEvents = k > 0.5 ? 'auto' : 'none';
      }
    }
  }

  build();

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (en.isIntersecting) { onScroll(); start(); } else stop();
      });
    }, { rootMargin: '20% 0px 20% 0px', threshold: 0 });
    io.observe(root);
  } else {
    start();
  }

  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Sécurité : le libellé de chargement ne reste jamais bloqué.
  setTimeout(() => { if (loader) loader.classList.add('is-done'); }, 6000);
})();
