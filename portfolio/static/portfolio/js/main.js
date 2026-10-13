(() => {
'use strict';
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const smooth = x => x * x * (3 - 2 * x);
const lerp = (a, b, t) => a + (b - a) * t;
const reduce = matchMedia('(prefers-reduced-motion:reduce)').matches;

/* ───────────────────────── En-tête ───────────────────────── */
const hdr = $('#site-header');
function onScroll() { hdr.classList.toggle('scrolled', scrollY > 40); }
addEventListener('scroll', onScroll, { passive: true });
onScroll();

const railFill = $('#progress-rail i');
function updateRail() {
  const doc = document.documentElement;
  const p = clamp(scrollY / Math.max(1, doc.scrollHeight - innerHeight));
  railFill.style.setProperty('--p', p.toFixed(4));
}

/* ───────────────────────── Menu mobile ───────────────────────── */
const drawer = $('#drawer');
function openDrawer() { drawer.classList.add('open'); document.body.classList.add('lb-open'); }
function closeDrawer() { drawer.classList.remove('open'); document.body.classList.remove('lb-open'); }
$('#hambbtn')?.addEventListener('click', openDrawer);
$('#drawerclose')?.addEventListener('click', closeDrawer);
$('#drawerbg')?.addEventListener('click', closeDrawer);
$$('.drawer-panel a').forEach(a => a.addEventListener('click', closeDrawer));

/* ───────────────────────── Reveal générique (compétences, formation…) ───────────────────────── */
const revealEls = $$('[data-reveal]');
if (revealEls.length) {
  const io = new IntersectionObserver(entries => {
    entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
  }, { threshold: .15 });
  revealEls.forEach(el => io.observe(el));
}

/* ───────────────────────── Système de particules (silhouettes) ───────────────────────── */
const PALETTE = ['#f4f4f7', '#eab54d', '#8b5cf6', '#2dd4bf', '#f472b6'];

function makeShape(kind, n, W, H) {
  const cx = W * (kind === 'brain2' ? 0.30 : 0.62), cy = H * 0.48;
  const R = Math.min(W, H) * 0.30;
  const pts = [];
  const rnd = () => Math.random() * 2 - 1;

  if (kind === 'scatter' || kind === 'burst') {
    const tight = kind === 'burst';
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2;
      const r = (tight ? Math.pow(Math.random(), 0.6) * R * 1.3 : Math.random() * Math.max(W, H) * 0.62);
      pts.push([W / 2 + Math.cos(a) * r, H / 2 + Math.sin(a) * r * (tight ? 1 : 0.7)]);
    }
    return pts;
  }

  if (kind === 'brain' || kind === 'brain2') {
    const bx = kind === 'brain2' ? W * 0.30 : W * 0.66;
    // Deux hémisphères nettement séparés en haut (scissure interhémisphérique)
    // et reliés plus bas, + un petit tronc cérébral. Chaque hémisphère est fait
    // de plusieurs petits cercles décalés pour un contour irrégulier (circonvolutions).
    const hemi = side => ([
      [bx + side * .64 * R, cy - .16 * R, .36 * R],
      [bx + side * .40 * R, cy - .36 * R, .32 * R],
      [bx + side * .16 * R, cy - .40 * R, .26 * R],
      [bx + side * .80 * R, cy + .10 * R, .30 * R],
      [bx + side * .54 * R, cy + .30 * R, .34 * R],
      [bx + side * .22 * R, cy + .10 * R, .30 * R],
      [bx + side * .30 * R, cy + .40 * R, .24 * R],
    ]);
    const circles = [...hemi(-1), ...hemi(1),
      [bx, cy + .56 * R, .15 * R], [bx, cy + .70 * R, .10 * R], // tronc cérébral
    ];
    let guard = 0;
    while (pts.length < n && guard < n * 80) {
      guard++;
      const x = bx + rnd() * R * 1.25, y = cy + rnd() * R * 1.1;
      for (const [ccx, ccy, cr] of circles) {
        if ((x - ccx) ** 2 + (y - ccy) ** 2 <= cr * cr) { pts.push([x, y]); break; }
      }
    }
    return pts;
  }

  if (kind === 'lightbulb') {
    const bcx = W * 0.32, bcy = H * 0.38, br = R * 0.50;
    const ty = bcy + br * 0.92, by = ty + br * 1.15;
    const topHW = br * 0.32, botHW = br * 0.15;
    // Allocation explicite : le culot doit rester visible même s'il occupe peu de surface.
    const nBase = Math.round(n * 0.26), nBulb = n - nBase;
    for (let i = 0; i < nBulb; i++) {
      const a = Math.random() * Math.PI * 2, r = Math.sqrt(Math.random()) * br;
      pts.push([bcx + Math.cos(a) * r, bcy + Math.sin(a) * r * 0.96]);
    }
    for (let i = 0; i < nBase; i++) {
      // 4 bandes nettes (comme un filetage de culot) plutôt qu'un remplissage uniforme
      const band = Math.floor(Math.random() * 4);
      const f = clamp((band + Math.random() * 0.55) / 4);
      const y = lerp(ty, by, f);
      const tw = lerp(topHW, botHW, f) + 1.5;
      pts.push([bcx + (Math.random() * 2 - 1) * tw, y]);
    }
    return pts;
  }

  if (kind === 'globe') {
    const gr = R * 0.80;
    const nGrid = Math.round(n * 0.55);
    // Méridiens (ellipses verticales) pour suggérer la courbure du globe
    const meridians = [1, 0.62, 0.22];
    // Parallèles (ellipses horizontales) à différentes latitudes
    const parallels = [0, 0.5, -0.5];
    for (let i = 0; i < nGrid; i++) {
      const a = Math.random() * Math.PI * 2;
      if (i % 2 === 0) {
        const rx = gr * meridians[i % meridians.length];
        pts.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * gr]);
      } else {
        const lat = parallels[i % parallels.length];
        const ry = gr * 0.30, cyl = cy + lat * gr * 0.62;
        const rx = gr * Math.cos(lat * 1.1);
        pts.push([cx + Math.cos(a) * rx, cyl + Math.sin(a) * ry]);
      }
    }
    for (let i = nGrid; i < n; i++) {
      const a = Math.random() * Math.PI * 2, r = Math.sqrt(Math.random()) * gr;
      pts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
    }
    return pts;
  }
  return pts;
}

class ParticleField {
  constructor(canvas, { count = 560, sequence = ['scatter'] } = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.count = reduce ? Math.round(count * .4) : count;
    this.sequence = sequence;
    this.shapes = [];
    this.cur = new Float32Array(this.count * 2);
    this.vel = new Float32Array(this.count * 2);
    this.colors = Array.from({ length: this.count }, () => PALETTE[(Math.random() * PALETTE.length) | 0]);
    this.sizes = Array.from({ length: this.count }, () => 2 + Math.random() * Math.random() * 8);
    this.rots = Array.from({ length: this.count }, () => Math.random() * Math.PI * 2);
    this.spins = Array.from({ length: this.count }, () => (Math.random() - .5) * .01);
    this.jphase = Array.from({ length: this.count }, () => Math.random() * Math.PI * 2);
    this.t = 0; // position dans la séquence de formes (flottant)
    this.roamBlend = 0; // 0 = reste groupé dans la forme ; 1 = vagabonde librement
    this.roamX = new Float32Array(this.count);
    this.roamY = new Float32Array(this.count);
    this.roamNext = new Float32Array(this.count);
    this.mx = -9999; this.my = -9999;
    // Écoute globale (et non sur le canvas) : la grille vagabonde derrière des
    // sections qui captureraient sinon le survol avant qu'il n'atteigne le canvas.
    if (!reduce && matchMedia('(pointer:fine)').matches) {
      addEventListener('mousemove', e => { this.mx = e.clientX; this.my = e.clientY; }, { passive: true });
      addEventListener('mouseleave', () => { this.mx = -9999; this.my = -9999; }, { passive: true });
    }
    this.resize();
    addEventListener('resize', () => this.resize(), { passive: true });
  }
  resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    this.canvas.width = w * dpr; this.canvas.height = h * dpr;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.W = w; this.H = h;
    this.shapes = this.sequence.map(k => makeShape(k, this.count, w, h));
    // première pose : place directement sur la première forme
    const s0 = this.shapes[0];
    for (let i = 0; i < this.count; i++) {
      const p = s0[i % s0.length] || [w / 2, h / 2];
      this.cur[i * 2] = p[0]; this.cur[i * 2 + 1] = p[1];
      if (!this.roamX[i] && !this.roamY[i]) {
        this.roamX[i] = Math.random() * w; this.roamY[i] = Math.random() * h;
      }
    }
  }
  setProgress(t) { this.t = clamp(t, 0, this.shapes.length - 1); }
  setRoamBlend(b) { this.roamBlend = clamp(b, 0, 1); }
  updateRoam(now, i) {
    if (now < this.roamNext[i]) return;
    // Nouvelle destination lointaine, à un rythme propre à chaque particule :
    // ça les empêche de se déplacer toutes ensemble, donc elles se dispersent
    // naturellement sur tout l'espace plutôt que de rester groupées.
    const margin = 40;
    this.roamX[i] = margin + Math.random() * (this.W - margin * 2);
    this.roamY[i] = margin + Math.random() * (this.H - margin * 2);
    this.roamNext[i] = now + 3200 + Math.random() * 5200;
  }
  target(i) {
    const n = this.shapes.length;
    const a = Math.floor(this.t), b = Math.min(n - 1, a + 1);
    const f = smooth(this.t - a);
    const pa = this.shapes[a][i % this.shapes[a].length] || [this.W / 2, this.H / 2];
    const pb = this.shapes[b][i % this.shapes[b].length] || pa;
    const sx = lerp(pa[0], pb[0], f), sy = lerp(pa[1], pb[1], f);
    if (this.roamBlend <= 0.0015) return [sx, sy];
    return [lerp(sx, this.roamX[i], this.roamBlend), lerp(sy, this.roamY[i], this.roamBlend)];
  }
  draw(now) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.W, this.H);
    ctx.lineWidth = 1;
    if (this.roamBlend > 0.0015) {
      for (let i = 0; i < this.count; i++) this.updateRoam(now, i);
    }
    for (let i = 0; i < this.count; i++) {
      const ix = i * 2, iy = i * 2 + 1;
      const [tx, ty] = this.target(i);
      const jig = reduce ? 0 : Math.sin(now * .0011 + this.jphase[i]) * 3;
      // Vagabondage plus lent et plus doux que la mise en forme du cerveau/ampoule/globe
      const k = reduce ? 1 : lerp(0.06, 0.015, this.roamBlend);
      this.cur[ix] += (tx - this.cur[ix]) * k;
      this.cur[iy] += (ty + jig - this.cur[iy]) * k;
      this.rots[i] += this.spins[i];

      const s = this.sizes[i];
      const featured = s > 7;
      let x = this.cur[ix], y = this.cur[iy], r = this.rots[i];

      // Répulsion douce autour du curseur : les particules s'écartent et brillent davantage
      let boost = 0;
      const dxm = x - this.mx, dym = y - this.my, dm = Math.hypot(dxm, dym);
      const RAD = 110;
      if (dm < RAD) {
        const f = (1 - dm / RAD);
        const push = f * f * 34;
        const inv = dm > 0.001 ? 1 / dm : 0;
        x += dxm * inv * push; y += dym * inv * push;
        boost = f;
      }

      ctx.save();
      ctx.translate(x, y); ctx.rotate(r);
      ctx.strokeStyle = this.colors[i];
      ctx.globalAlpha = Math.min(1, (featured ? .85 : .5) + boost * .4);
      if (featured || boost > 0) { ctx.shadowColor = this.colors[i]; ctx.shadowBlur = 10 + boost * 14; }
      const sc = 1 + boost * .5;
      ctx.beginPath();
      ctx.moveTo(0, -s * sc); ctx.lineTo(s * .87 * sc, s * .6 * sc); ctx.lineTo(-s * .87 * sc, s * .6 * sc); ctx.closePath();
      ctx.stroke();
      ctx.restore();
    }
  }
}

const fields = [];
function rafLoop(now) {
  fields.forEach(f => f.el.draw(now));
  requestAnimationFrame(rafLoop);
}
requestAnimationFrame(rafLoop);

/* ───────────────────────── Étoiles d'ambiance, en mouvement permanent ───────────────────────── */
class Starfield {
  constructor(canvas, count = 180) {
    this.canvas = canvas; this.ctx = canvas.getContext('2d');
    this.count = reduce ? Math.round(count * .5) : count;
    this.resize();
    addEventListener('resize', () => this.resize(), { passive: true });
  }
  resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    this.W = innerWidth; this.H = innerHeight;
    this.canvas.width = this.W * dpr; this.canvas.height = this.H * dpr;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.stars = Array.from({ length: this.count }, () => ({
      x: Math.random() * this.W, y: Math.random() * this.H,
      r: 0.5 + Math.random() * 1.3,
      vx: (Math.random() - .5) * .07, vy: (Math.random() - .5) * .07,
      ph: Math.random() * Math.PI * 2, fq: .0006 + Math.random() * .0012,
      base: .35 + Math.random() * .5,
    }));
  }
  draw(now) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.W, this.H);
    for (const s of this.stars) {
      if (!reduce) {
        s.x += s.vx; s.y += s.vy;
        if (s.x < -4) s.x = this.W + 4; if (s.x > this.W + 4) s.x = -4;
        if (s.y < -4) s.y = this.H + 4; if (s.y > this.H + 4) s.y = -4;
      }
      const tw = reduce ? s.base : s.base * (0.6 + 0.4 * Math.sin(now * s.fq + s.ph));
      ctx.globalAlpha = tw;
      ctx.fillStyle = '#fff';
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
  }
}
const starsCanvas = $('#stars-canvas');
if (starsCanvas) {
  const sf = new Starfield(starsCanvas);
  fields.push({ el: sf });
}

/* ───────────────────────── Hero : timeline pilotée par le scroll ───────────────────────── */
const heroRunway = $('#hero-runway');
if (heroRunway) {
  const canvas = $('#pcanvas');
  const stageEls = $$('.hstage', heroRunway);
  const plines = $$('.pline', heroRunway);
  const shapeSeq = stageEls.map(el => el.dataset.shape === 'brain' ? 'brain' : el.dataset.shape)
    .map((s, i, arr) => s === 'brain' && i > 0 && arr[i - 1] === 'brain' ? 'brain2' : s);
  // Séquence réelle de formes pour le champ de particules (dissolve -> 'scatter')
  const fieldSeq = shapeSeq.map(s => s === 'dissolve' ? 'scatter' : s);
  const field = new ParticleField(canvas, { count: 560, sequence: fieldSeq });
  fields.push({ el: field });

  const N = stageEls.length; // nombre d'étapes (5)
  const HOLD = 0.62, TRANS = 1 - 0.62; // fractions de tenue / transition par segment

  function docTop(el) { return el.getBoundingClientRect().top + scrollY; }
  function heroProgress() {
    const total = heroRunway.offsetHeight - innerHeight;
    return total > 0 ? clamp((scrollY - docTop(heroRunway)) / total) : 0;
  }
  // Au-delà du hero, combien d'écrans a-t-on défilé ? Pilote le vagabondage
  // des particules et la disparition du texte du hero (0 au bas du hero, 1 un
  // peu plus loin). Repasse à 0 si on remonte, donc tout est réversible.
  function pastHero() {
    const heroBottom = docTop(heroRunway) + heroRunway.offsetHeight - innerHeight;
    return clamp((scrollY - heroBottom) / (innerHeight * 1.15));
  }

  const heroCopy = $('.hero-copy', heroRunway);
  let cur = 0, lastStageIdx = -1, lastLine = -1, lastPast = -1;
  function applyHero(p) {
    const seg = p * (N - 1);           // position continue dans [0, N-1]
    field.setProgress(seg);

    const idx = Math.min(N - 1, Math.floor(seg + 1e-6));
    const within = seg - idx;          // 0..1 à l'intérieur du segment [idx, idx+1]
    const holding = within < HOLD || idx === N - 1;
    const activeIdx = holding ? idx : Math.min(N - 1, idx + 1);

    if (activeIdx !== lastStageIdx) {
      lastStageIdx = activeIdx;
      stageEls.forEach((el, i) => el.classList.toggle('on', i === activeIdx));
    }

    // Phrases séquentielles pendant l'état "dissolve". On avance selon la
    // position dans TOUTE la fenêtre de la forme (et non selon `within`, qui
    // repart à 0 au changement de segment) : sinon la dernière phrase est
    // jouée une première fois à la fin du segment précédent, puis rejouée en
    // dernier — d'où le doublon observé.
    const dissolveEl = stageEls[activeIdx];
    if (dissolveEl && dissolveEl.dataset.shape === 'dissolve' && plines.length) {
      const start = activeIdx - (1 - HOLD);
      const end = activeIdx === N - 1 ? N - 1 : activeIdx + HOLD;
      const s = clamp((seg - start) / Math.max(1e-6, end - start));
      const li = Math.min(plines.length - 1, Math.floor(s * plines.length));
      if (li !== lastLine) { lastLine = li; plines.forEach((el, i) => el.classList.toggle('on', i === li)); }
    } else if (lastLine !== -1) {
      lastLine = -1;
      plines.forEach(el => el.classList.remove('on'));
    }

    const cue = $('#hero-cue');
    if (cue) cue.style.setProperty('--cue', p < 0.02 ? 1 : 0);
  }

  let last = performance.now();
  function tick(now) {
    const dt = Math.min(64, now - last); last = now;
    const target = heroProgress();
    const k = reduce ? 1 : 1 - Math.pow(1 - .16, dt / 16.667);
    cur += (target - cur) * k;
    if (Math.abs(target - cur) < .0006) cur = target;
    applyHero(cur);

    const past = pastHero();
    field.setRoamBlend(smooth(past));
    if (Math.abs(past - lastPast) > .004) {
      lastPast = past;
      const fade = 1 - smooth(clamp(past / 0.5)); // s'efface vite, dans le premier 0.5
      if (heroCopy) {
        heroCopy.style.opacity = fade.toFixed(3);
        heroCopy.style.pointerEvents = fade > 0.05 ? '' : 'none';
      }
    }

    updateRail();
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(t => { last = t; tick(t); });
}

/* ───────────────────────── CTA finale : petit champ de particules "burst" ───────────────────────── */
const ctaCanvas = $('#cta-canvas');
if (ctaCanvas) {
  const field = new ParticleField(ctaCanvas, { count: 260, sequence: ['scatter', 'burst'] });
  fields.push({ el: field });
  const io = new IntersectionObserver(entries => {
    entries.forEach(en => field.setProgress(en.isIntersecting ? 1 : 0));
  }, { threshold: .3 });
  io.observe(ctaCanvas.closest('section'));
}

/* ───────────────────────── Projets : cartes qui défilent ───────────────────────── */
const projRunway = $('#proj-runway');
if (projRunway) {
  const cards = $$('.proj-card', projRunway);
  const dots = $$('.proj-dots i', projRunway);
  const numEl = $('#proj-num');
  const N = cards.length;
  let lastIdx = -1;
  function apply() {
    const total = projRunway.offsetHeight - innerHeight;
    const top = projRunway.getBoundingClientRect().top + scrollY;
    const p = total > 0 ? clamp((scrollY - top) / total) : 0;
    const idx = Math.min(N - 1, Math.floor(p * N));
    if (idx !== lastIdx) {
      lastIdx = idx;
      cards.forEach((c, i) => c.classList.toggle('on', i === idx));
      dots.forEach((d, i) => d.classList.toggle('on', i === idx));
      if (numEl) numEl.textContent = `${idx + 1} / ${N}`;
    }
  }
  addEventListener('scroll', apply, { passive: true });
  apply();
}

/* ───────────────────────── Certifications : révélation en cascade ───────────────────────── */
const certItems = $$('.cert-item');
if (certItems.length) {
  const io = new IntersectionObserver(entries => {
    entries.forEach((en, i) => {
      if (en.isIntersecting) {
        const idx = certItems.indexOf(en.target);
        setTimeout(() => en.target.classList.add('in'), reduce ? 0 : idx * 90);
        io.unobserve(en.target);
      }
    });
  }, { threshold: .2 });
  certItems.forEach(el => io.observe(el));
}

/* ───────────────────────── Visionneuse (photo + certificats) ───────────────────────── */
const lb = $('#lb'), lbImg = $('#lbimg'), lbT = $('#lbt'), lbM = $('#lbm');
const certButtons = $$('.cert-btn');
let openIdx = -1, openFrom = null, closing = false, lastFocus = null;

function flip(fromRect, reverse) {
  if (reduce || !fromRect || !fromRect.width) return Promise.resolve();
  const to = lbImg.getBoundingClientRect();
  const dx = fromRect.left - to.left, dy = fromRect.top - to.top;
  const sx = fromRect.width / to.width, sy = fromRect.height / to.height;
  const a = { transformOrigin: '0 0', transform: `translate(${dx}px,${dy}px) scale(${sx},${sy})` };
  const b = { transformOrigin: '0 0', transform: 'none' };
  const anim = lbImg.animate(reverse ? [b, a] : [a, b], { duration: reverse ? 380 : 560, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'both' });
  return anim.finished.catch(() => {});
}
async function reveal(from) {
  lb.hidden = false;
  document.documentElement.classList.add('lb-open'); document.body.classList.add('lb-open');
  try { await lbImg.decode(); } catch (_) {}
  lb.classList.add('show');
  const img = from.querySelector('img');
  flip(img ? img.getBoundingClientRect() : null, false);
  $('#lbx').focus({ preventScroll: true });
}
async function openAt(i, from) {
  if (closing) return;
  openIdx = i; openFrom = from; lastFocus = from;
  lb.classList.remove('single');
  const d = from.dataset;
  lbImg.src = d.full; lbImg.alt = `Certificat : ${d.title}`;
  lbT.textContent = d.title; lbM.textContent = `${d.org} — ${d.date}`;
  await reveal(from);
}
async function openPhoto(from) {
  if (closing) return;
  openIdx = -1; openFrom = from; lastFocus = from;
  lb.classList.add('single');
  const d = from.dataset;
  lbImg.src = d.full; lbImg.alt = d.title || 'Photo';
  lbT.textContent = d.title || ''; lbM.textContent = d.org || '';
  await reveal(from);
}
async function closeLb() {
  if (lb.hidden || closing) return;
  closing = true;
  const img = openFrom && openFrom.querySelector('img');
  const rect = img ? img.getBoundingClientRect() : null;
  lb.classList.remove('show');
  await flip(rect, true);
  lb.hidden = true;
  lbImg.getAnimations().forEach(a => a.cancel());
  document.documentElement.classList.remove('lb-open'); document.body.classList.remove('lb-open');
  closing = false;
  if (lastFocus) lastFocus.focus({ preventScroll: true });
}
function stepCert(d) {
  if (lb.hidden || closing || lb.classList.contains('single') || !certButtons.length) return;
  openIdx = (openIdx + d + certButtons.length) % certButtons.length;
  openFrom = certButtons[openIdx]; lastFocus = openFrom;
  const dd = openFrom.dataset;
  lbImg.animate([{ opacity: 0, transform: `translateX(${d * 24}px)` }, { opacity: 1, transform: 'none' }], { duration: reduce ? 1 : 320, easing: 'cubic-bezier(.16,1,.3,1)' });
  lbImg.src = dd.full; lbImg.alt = `Certificat : ${dd.title}`;
  lbT.textContent = dd.title; lbM.textContent = `${dd.org} — ${dd.date}`;
}
certButtons.forEach((b, i) => b.addEventListener('click', () => openAt(i, b)));
$$('.avatar-trigger').forEach(b => b.addEventListener('click', () => openPhoto(b)));
$('#lbx')?.addEventListener('click', closeLb);
$('#lbbg')?.addEventListener('click', closeLb);
$('#lbp')?.addEventListener('click', () => stepCert(-1));
$('#lbn')?.addEventListener('click', () => stepCert(1));
lb?.addEventListener('click', e => { if (e.target === lb || e.target.classList.contains('lb-fig')) closeLb(); });
addEventListener('keydown', e => {
  if (drawer.classList.contains('open') && e.key === 'Escape') { closeDrawer(); return; }
  if (!lb || lb.hidden) return;
  if (e.key === 'Escape') { e.preventDefault(); closeLb(); }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); stepCert(-1); }
  else if (e.key === 'ArrowRight') { e.preventDefault(); stepCert(1); }
  else if (e.key === 'Tab') {
    const f = lb.classList.contains('single') ? [$('#lbx')] : [$('#lbx'), $('#lbp'), $('#lbn')];
    const i = f.indexOf(document.activeElement); e.preventDefault();
    f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
  }
});
let tx = null;
lb?.addEventListener('touchstart', e => { tx = e.touches[0].clientX; }, { passive: true });
lb?.addEventListener('touchend', e => { if (tx === null) return; const dx = e.changedTouches[0].clientX - tx; tx = null; if (Math.abs(dx) > 55) stepCert(dx < 0 ? 1 : -1); }, { passive: true });

/* ───────────────────────── Copier l'e-mail ───────────────────────── */
const heroVideo = $('#heroVideo');
if (heroVideo) {
  heroVideo.loop = false;
  heroVideo.currentTime = 0;
  const play = heroVideo.play();
  if (play && play.catch) play.catch(() => {});
}

$('#copyBtn')?.addEventListener('click', async () => {
  const addr = $('#copyBtn').dataset.email, lab = $('#copyLbl');
  try { await navigator.clipboard.writeText(addr); }
  catch (_) {
    const t = document.createElement('textarea'); t.value = addr; t.style.position = 'fixed'; t.style.opacity = '0';
    document.body.appendChild(t); t.select(); try { document.execCommand('copy'); } catch (__) {} t.remove();
  }
  lab.textContent = 'Adresse copiée';
  clearTimeout(lab._t); lab._t = setTimeout(() => { lab.textContent = "Copier l'adresse"; }, 2200);
});
})();
