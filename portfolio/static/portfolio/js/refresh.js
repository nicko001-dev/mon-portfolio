/* « Tirer pour actualiser » sur l'écran d'accueil (mobile).

   Pourquoi : sur l'accueil, le défilement est désactivé (classe .no-scroll → overflow:hidden),
   et les navigateurs mobiles n'offrent alors plus leur geste natif de rafraîchissement.
   Ce script le recrée à l'identique : tirer vers le bas depuis le haut de l'écran, relâcher
   au-delà du seuil → la page se recharge.

   Limité à l'ACCUEIL : dans l'univers 3D, glisser le doigt sert à regarder autour de soi
   et ne doit jamais recharger la page. */
(() => {
  'use strict';
  const app = document.getElementById('portfolio-app');
  if (!app) return;
  const touch = ('ontouchstart' in window) || (navigator.maxTouchPoints || 0) > 0;
  if (!touch) return;

  const THRESHOLD = 70;    // distance (px, après amortissement) qui déclenche l'actualisation
  const MAX = 120;
  const DAMPING = 0.5;     // le doigt parcourt 2× la distance affichée

  const ind = document.createElement('div');
  ind.className = 'ptr';
  ind.setAttribute('aria-hidden', 'true');
  ind.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" ' +
                  'stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M6 13l6 6 6-6"/></svg>';
  document.body.appendChild(ind);

  let x0 = null, y0 = null, pulling = false, dist = 0, loading = false;

  const isHome = () => app.classList.contains('app-ui-a');
  // On ne démarre pas le geste sur le chat, le menu ouvert ou un champ de saisie.
  const blocked = (t) => !!(t.closest && t.closest('#chatbot, #drawer, input, textarea, select')) ||
                         document.body.classList.contains('lb-open');

  function paint(d) {
    ind.style.opacity = String(Math.min(1, d / 40));
    ind.style.transform = 'translateY(' + (d - 70) + 'px)';
    ind.classList.toggle('is-ready', d >= THRESHOLD);
  }
  function reset(animated) {
    ind.classList.toggle('is-anim', !!animated);
    ind.classList.remove('is-ready');
    ind.style.opacity = '0';
    ind.style.transform = 'translateY(-70px)';
    x0 = y0 = null; pulling = false; dist = 0;
  }

  addEventListener('touchstart', (e) => {
    if (loading || !isHome() || e.touches.length !== 1 || blocked(e.target)) { x0 = y0 = null; return; }
    x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; pulling = false; dist = 0;
    ind.classList.remove('is-anim');
  }, { passive: true });

  addEventListener('touchmove', (e) => {
    if (y0 === null || loading) return;
    if (!isHome()) { reset(false); return; }
    const dy = e.touches[0].clientY - y0, dx = e.touches[0].clientX - x0;
    if (!pulling) {
      if (dy < 10 || Math.abs(dx) > dy) { if (dy < -4) y0 = null; return; }   // vers le haut ou horizontal : on ignore
      pulling = true;
    }
    dist = Math.min(MAX, Math.max(0, dy * DAMPING));
    paint(dist);
    if (e.cancelable) e.preventDefault();      // évite un double effet avec le geste natif
  }, { passive: false });

  function end() {
    if (!pulling) { x0 = y0 = null; return; }
    if (dist >= THRESHOLD && !loading) {
      loading = true;
      ind.classList.add('is-anim', 'is-loading', 'is-ready');
      ind.style.opacity = '1';
      ind.style.transform = 'translateY(' + (THRESHOLD - 70 + 24) + 'px)';
      setTimeout(() => {
        // Point d'accroche : un script peut annuler le rechargement (preventDefault).
        if (window.dispatchEvent(new CustomEvent('portfolio:refresh', { cancelable: true }))) {
          window.location.reload();
        } else { loading = false; ind.classList.remove('is-loading'); reset(true); }
      }, 350);
    } else {
      reset(true);
    }
  }
  addEventListener('touchend', end, { passive: true });
  addEventListener('touchcancel', () => { if (!loading) reset(true); }, { passive: true });
})();
