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

/* ───────────────────────── Titres atelier : révélation lettre par lettre ───────────────────────── */
let letterIndex = 0;
$$('[data-split]').forEach(el => {
  const text = (el.textContent || '').replace(/\s+/g, ' ').trim();
  el.textContent = '';
  const words = text.split(' ');
  words.forEach((word, wi) => {
    const wrap = document.createElement('span');
    wrap.className = 'w';
    for (const ch of word) {
      const s = document.createElement('span');
      s.className = 'c';
      s.textContent = ch;
      s.style.setProperty('--d', (0.03 * letterIndex).toFixed(3) + 's');
      letterIndex++;
      wrap.appendChild(s);
    }
    el.appendChild(wrap);
    if (wi < words.length - 1) el.appendChild(document.createTextNode(' '));
  });
});

/* ───────────────────────── Reveal générique au scroll ───────────────────────── */
const revealEls = $$('[data-reveal],[data-split]');
if (revealEls.length) {
  const io = new IntersectionObserver(entries => {
    entries.forEach(en => { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
  }, { threshold: .15 });
  revealEls.forEach(el => io.observe(el));
}

/* ───────────────────────── Compteurs animés (section cœur 3D) ───────────────────────── */
const counters = $$('[data-count]');
if (counters.length) {
  const run = node => {
    const target = parseInt(node.getAttribute('data-count'), 10) || 0;
    if (reduce) { node.textContent = String(target); return; }
    const start = performance.now(), dur = 1400;
    const step = now => {
      const t = Math.min(1, (now - start) / dur);
      const e = 1 - Math.pow(1 - t, 3);
      node.textContent = String(Math.round(target * e));
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  const cio = new IntersectionObserver(entries => {
    entries.forEach(en => { if (en.isIntersecting) { run(en.target); cio.unobserve(en.target); } });
  }, { threshold: .6 });
  counters.forEach(el => cio.observe(el));
}

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
  const rafLoop = now => {
    sf.draw(now);
    requestAnimationFrame(rafLoop);
  };
  requestAnimationFrame(rafLoop);
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

/* ───────────────────────── Vidéo d'introduction ───────────────────────── */
const heroVideo = $('#heroVideo');
if (heroVideo) {
  heroVideo.loop = false;
  heroVideo.currentTime = 0;
  const play = heroVideo.play();
  if (play && play.catch) play.catch(() => {});
}

/* ───────────────────────── Gestion des ancres pour l'app 3-écrans ───────────────────────── */
$$('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const targetId = a.getAttribute('href');
    if (!targetId || targetId === '#') return;
    const app = $('#portfolio-app');
    if (!app) return;

    if (targetId === '#home') {
      e.preventDefault();
      app.className = 'app-ui-a';
      document.documentElement.classList.add('no-scroll');
      document.body.classList.add('no-scroll');
      window.scrollTo(0, 0);
      if (heroVideo) {
        heroVideo.currentTime = 0;
        const p = heroVideo.play();
        if (p && p.catch) p.catch(() => {});
      }
    } else {
      // Pour les sections de l'Atelier
      const targetEl = $(targetId);
      if (targetEl) {
        e.preventDefault();
        app.className = 'app-ui-c';
        document.documentElement.classList.remove('no-scroll');
        document.body.classList.remove('no-scroll');
        setTimeout(() => {
          targetEl.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth' });
        }, 50);
      }
    }
  });
});

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
