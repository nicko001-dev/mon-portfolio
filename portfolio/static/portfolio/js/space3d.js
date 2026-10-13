/* ============================================================
   Acte II — Espace 3D interactif (Three.js)
   Un nœud de tore en fil de fer et un nuage d'étoiles réagissent à
   la souris et au défilement. Le rendu s'active uniquement quand la
   section est à l'écran, et reste inerte sans Three.js.
   ============================================================ */
(() => {
  'use strict';

  const root = document.getElementById('space-runway');
  if (!root || !window.THREE) return;

  const canvas = document.getElementById('three-canvas');
  const copy = root.querySelector('.space-copy');
  if (!canvas) return;

  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  let renderer, scene, camera, clock, particles, torus;
  let mouseX = 0, mouseY = 0, targetX = 0, targetY = 0;
  let progress = 0, running = false, rafId = 0;

  function build() {
    const w = canvas.clientWidth || innerWidth;
    const h = canvas.clientHeight || innerHeight;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x050505);
    scene.fog = new THREE.FogExp2(0x050505, 0.045);

    camera = new THREE.PerspectiveCamera(75, w / h, 0.1, 1000);
    camera.position.set(0, 0, 5.2);

    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    renderer.setSize(w, h, false);

    scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const violet = new THREE.PointLight(0x8b5cf6, 2.6, 60);
    violet.position.set(5, 5, 5);
    scene.add(violet);
    const teal = new THREE.PointLight(0x2dd4bf, 2.0, 60);
    teal.position.set(-5, -5, 5);
    scene.add(teal);

    // Nuage d'étoiles ambiant
    const g = new THREE.BufferGeometry();
    const verts = new Float32Array(5000 * 3);
    for (let i = 0; i < 5000; i++) {
      verts[i * 3] = (Math.random() - 0.5) * 24;
      verts[i * 3 + 1] = (Math.random() - 0.5) * 24;
      verts[i * 3 + 2] = (Math.random() - 0.5) * 24;
    }
    g.setAttribute('position', new THREE.BufferAttribute(verts, 3));
    const pm = new THREE.PointsMaterial({
      size: 0.022,
      color: 0xffffff,
      transparent: true,
      opacity: 0.55,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    particles = new THREE.Points(g, pm);
    scene.add(particles);

    // Objet central
    const tg = new THREE.TorusKnotGeometry(1, 0.3, 220, 36);
    const tm = new THREE.MeshPhysicalMaterial({
      color: 0x1b1b22,
      metalness: 0.9,
      roughness: 0.15,
      wireframe: true,
      emissive: 0x8b5cf6,
      emissiveIntensity: 0.35,
    });
    torus = new THREE.Mesh(tg, tm);
    scene.add(torus);

    clock = new THREE.Clock();
    addEventListener('resize', resize, { passive: true });
    if (!reduce && matchMedia('(pointer:fine)').matches) {
      addEventListener('mousemove', onMove, { passive: true });
    }

    if (reduce) paint();
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

  function frame() {
    if (!running) return;
    rafId = requestAnimationFrame(frame);

    const t = clock.getElapsedTime();
    targetX += (mouseX - targetX) * 0.05;
    targetY += (mouseY - targetY) * 0.05;

    if (torus) {
      torus.rotation.x = t * 0.3 + progress * Math.PI * 0.9;
      torus.rotation.y = t * 0.4 + progress * Math.PI * 1.4;
      torus.rotation.z += targetX * 0.5;
      torus.scale.setScalar(1 + Math.sin(t) * 0.06 + progress * 0.28);
      torus.material.emissiveIntensity = 0.3 + progress * 1.5;
    }
    if (particles) {
      particles.rotation.y = t * 0.05 + progress * 0.7;
      particles.rotation.x = targetY * 0.2;
    }

    camera.position.x += (targetX * 2 - camera.position.x) * 0.05;
    camera.position.y += (-targetY * 2 - camera.position.y) * 0.05;
    camera.position.z = 5.2 - progress * 2.4;
    camera.lookAt(scene.position);

    renderer.render(scene, camera);
  }

  function paint() {
    if (renderer) renderer.render(scene, camera);
  }

  function start() {
    if (reduce || running || !renderer) return;
    running = true;
    clock.start();
    rafId = requestAnimationFrame(frame);
  }
  function stop() {
    running = false;
    if (rafId) cancelAnimationFrame(rafId);
    rafId = 0;
  }

  function onScroll() {
    const total = root.offsetHeight - innerHeight;
    const top = root.getBoundingClientRect().top + scrollY;
    progress = total > 0 ? Math.min(1, Math.max(0, (scrollY - top) / total)) : 0;
    if (copy) {
      const fadeIn = progress / 0.16;
      const fadeOut = 1 - Math.max(0, (progress - 0.8) / 0.2);
      const o = Math.min(1, Math.max(0, Math.min(fadeIn, fadeOut)));
      copy.style.opacity = o.toFixed(3);
      copy.classList.toggle('on', o > 0.55);
    }
  }

  build();

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => (en.isIntersecting ? (onScroll(), start()) : stop()));
    }, { rootMargin: '20% 0px 20% 0px', threshold: 0 });
    io.observe(root);
  } else {
    start();
  }

  addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();
