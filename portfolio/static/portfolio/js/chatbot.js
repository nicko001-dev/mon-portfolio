/* Assistant IA — widget de chat.
   Parle à /api/chat/ (Django) ; les clés des fournisseurs IA restent côté serveur.

   Particularités :
   - il sait dans quel écran se trouve le visiteur (accueil / univers 3D / atelier) ;
   - dans l'univers 3D, le bouton passe en mode « alerte » tant qu'il n'a pas été ouvert ;
   - le clavier et la molette du chat ne pilotent JAMAIS le vaisseau de l'univers. */
(() => {
  'use strict';
  const root = document.getElementById('chatbot');
  const cfgEl = document.getElementById('chatbot-config');
  if (!root || !cfgEl) return;

  let cfg;
  try { cfg = JSON.parse(cfgEl.textContent); } catch (_) { return; }

  const $ = (id) => document.getElementById(id);
  const toggle = $('cb-toggle'), panel = $('cb-panel'), closeBtn = $('cb-close');
  const log = $('cb-log'), chips = $('cb-chips'), form = $('cb-form');
  const input = $('cb-input'), send = $('cb-send'), alertEl = $('cb-alert');
  const backdrop = $('cb-backdrop'), head = panel.querySelector('.cb-head');
  const app = document.getElementById('portfolio-app');
  const HISTORY_KEY = 'cb-history-v1', SEEN_KEY = 'cb-seen-v1', MAX_KEPT = 40;
  const mobile = window.matchMedia ? window.matchMedia('(max-width: 600px)') : { matches: false };

  let history = [];       // [{role:'user'|'assistant', text}]
  let busy = false;
  let screen = 'home';
  let togglePosition = null;
  let toggleDrag = null;
  let suppressToggleClick = false;

  try { history = JSON.parse(sessionStorage.getItem(HISTORY_KEY) || '[]'); } catch (_) { history = []; }
  if (!Array.isArray(history)) history = [];
  const save = () => { try { sessionStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-MAX_KEPT))); } catch (_) {} };
  const wasSeen = () => { try { return sessionStorage.getItem(SEEN_KEY) === '1'; } catch (_) { return false; } };
  const markSeen = () => { try { sessionStorage.setItem(SEEN_KEY, '1'); } catch (_) {} };
  const isOpen = () => root.classList.contains('is-open');

  /* ── Rendu « markdown léger » SÛR : on échappe d'abord, puis on balise ── */
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  function inline(t) {
    return t
      .replace(/`([^`\n]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
      .replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s).,;:!?]|$)/g, '$1<em>$2</em>')
      .replace(/\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)/g,
               '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
      .replace(/(^|[\s(>])(https?:\/\/[^\s<)]+[^\s<).,;:!?])/g,
               '<a href="$2" target="_blank" rel="noopener noreferrer">$2</a>');
  }
  function render(md) {
    const blocks = [];
    let text = esc(md).replace(/```[a-z0-9]*\n?([\s\S]*?)```/gi, (_, code) => {
      blocks.push('<pre><code>' + code.replace(/\n$/, '') + '</code></pre>');
      return '\u0000' + (blocks.length - 1) + '\u0000';
    });
    const out = [];
    let list = null;                       // 'ul' | 'ol'
    const closeList = () => { if (list) { out.push('</' + list + '>'); list = null; } };
    text.split('\n').forEach((line) => {
      const ph = line.match(/^\u0000(\d+)\u0000$/);
      const ul = line.match(/^\s*[-*•]\s+(.*)$/);
      const ol = line.match(/^\s*\d+[.)]\s+(.*)$/);
      const hd = line.match(/^#{1,4}\s+(.*)$/);
      if (ph) { closeList(); out.push(blocks[+ph[1]]); }
      else if (ul) { if (list !== 'ul') { closeList(); out.push('<ul>'); list = 'ul'; } out.push('<li>' + inline(ul[1]) + '</li>'); }
      else if (ol) { if (list !== 'ol') { closeList(); out.push('<ol>'); list = 'ol'; } out.push('<li>' + inline(ol[1]) + '</li>'); }
      else if (!line.trim()) { closeList(); }
      else { closeList(); out.push('<p>' + (hd ? '<strong>' + inline(hd[1]) + '</strong>' : inline(line)) + '</p>'); }
    });
    closeList();
    return out.join('');
  }

  /* ── Affichage ── */
  const toBottom = () => { log.scrollTop = log.scrollHeight; };
  function bubble(kind, text) {
    const el = document.createElement('div');
    el.className = 'cb-msg ' + kind;
    if (kind === 'user') { el.textContent = text; } else { el.innerHTML = render(text); }
    log.appendChild(el);
    toBottom();
    return el;
  }
  function typing() {
    const el = document.createElement('div');
    el.className = 'cb-msg bot cb-typing';
    el.setAttribute('aria-label', 'L\u2019assistant écrit…');
    el.innerHTML = '<i></i><i></i><i></i>';
    log.appendChild(el);
    toBottom();
    return el;
  }

  /* Suggestions : au début de la conversation ; et EN PERMANENCE dans l'univers 3D,
     où l'on se perd le plus facilement. */
  function renderChips() {
    chips.innerHTML = '';
    const universe = screen === 'universe';
    const list = universe ? (cfg.universeSuggestions || []) : (history.length ? [] : (cfg.suggestions || []));
    chips.classList.toggle('is-row', universe && history.length > 0);
    list.forEach((q) => {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'cb-chip'; b.textContent = q;
      b.addEventListener('click', () => ask(q));
      chips.appendChild(b);
    });
  }

  function boot() {
    log.innerHTML = '';
    bubble('bot', cfg.welcome);
    history.forEach((m) => bubble(m.role === 'user' ? 'user' : 'bot', m.text));
    renderChips();
  }

  /* ── Écran courant + mode alerte ── */
  function currentScreen() {
    const c = app ? app.className : '';
    return c.indexOf('app-ui-b') > -1 ? 'universe' : c.indexOf('app-ui-c') > -1 ? 'atelier' : 'home';
  }
  function clampTogglePosition(left, top) {
    const rect = toggle.getBoundingClientRect();
    return {
      left: Math.max(8, Math.min(left, document.documentElement.clientWidth - rect.width - 8)),
      top: Math.max(8, Math.min(top, window.innerHeight - rect.height - 8))
    };
  }
  function applyTogglePosition() {
    if (!togglePosition) return;
    togglePosition = clampTogglePosition(togglePosition.left, togglePosition.top);
    toggle.style.left = togglePosition.left + 'px';
    toggle.style.right = 'auto';
    toggle.style.top = togglePosition.top + 'px';
    toggle.style.bottom = 'auto';
    toggle.style.marginTop = '0';
  }
  function syncTogglePosition() {
    const movable = mobile.matches && screen === 'universe' && !isOpen();
    root.classList.toggle('is-movable', movable);
    if (movable) {
      applyTogglePosition();
      return;
    }
    toggleDrag = null;
    root.classList.remove('is-dragging');
    ['left', 'right', 'top', 'bottom', 'margin-top'].forEach((property) => {
      toggle.style.removeProperty(property);
    });
  }
  function updateAlert() {
    const on = screen === 'universe' && !wasSeen() && !isOpen();
    root.classList.toggle('is-alert', on);
    alertEl.hidden = !(on && cfg.alertText);
  }
  function applyScreen() {
    const next = currentScreen();
    if (next === screen && root.dataset.screen === next) {
      syncTogglePosition();
      return;
    }
    screen = next;
    root.dataset.screen = next;
    updateAlert();
    renderChips();
    syncTogglePosition();
  }
  if (app && window.MutationObserver) {
    new MutationObserver(applyScreen).observe(app, { attributes: true, attributeFilter: ['class'] });
  }
  applyScreen();
  window.addEventListener('resize', syncTogglePosition);
  if (mobile.addEventListener) mobile.addEventListener('change', syncTogglePosition);
  else if (mobile.addListener) mobile.addListener(syncTogglePosition);

  /* ── Mobile : la feuille suit la zone réellement visible (clavier ouvert) ── */
  function fit() {
    const vv = window.visualViewport;
    if (!isOpen() || !mobile.matches || !vv) {
      ['top', 'bottom', 'height'].forEach((p) => panel.style.removeProperty(p));
      return;
    }
    const keyboard = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
    panel.style.top = 'auto';
    panel.style.bottom = keyboard + 'px';
    panel.style.height = Math.max(260, vv.height - 52) + 'px';
    toBottom();
  }
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', fit);
    window.visualViewport.addEventListener('scroll', fit);
  }

  /* ── Ouverture / fermeture ── */
  function setOpen(open) {
    if (open) markSeen();
    root.classList.toggle('is-open', open);
    syncTogglePosition();
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', (open ? 'Fermer le chat avec ' : 'Ouvrir le chat avec ') + cfg.name);
    if (open) {
      panel.hidden = false;
      fit(); toBottom();
      setTimeout(() => { if (!mobile.matches) input.focus({ preventScroll: true }); }, 280);
    } else {
      fit();
      setTimeout(() => { if (!isOpen()) panel.hidden = true; }, 260);
      toggle.focus({ preventScroll: true });
    }
    updateAlert();
  }
  toggle.addEventListener('pointerdown', (event) => {
    if (!root.classList.contains('is-movable') || !event.isPrimary) return;
    const rect = toggle.getBoundingClientRect();
    toggleDrag = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      startLeft: rect.left,
      startTop: rect.top,
      moved: false
    };
    toggle.setPointerCapture(event.pointerId);
  });
  toggle.addEventListener('pointermove', (event) => {
    if (!toggleDrag || event.pointerId !== toggleDrag.pointerId) return;
    const dx = event.clientX - toggleDrag.startX;
    const dy = event.clientY - toggleDrag.startY;
    if (!toggleDrag.moved && Math.hypot(dx, dy) < 6) return;
    toggleDrag.moved = true;
    root.classList.add('is-dragging');
    togglePosition = clampTogglePosition(toggleDrag.startLeft + dx, toggleDrag.startTop + dy);
    applyTogglePosition();
    if (event.cancelable) event.preventDefault();
  });
  function finishToggleDrag(event) {
    if (!toggleDrag || event.pointerId !== toggleDrag.pointerId) return;
    const moved = toggleDrag.moved;
    toggleDrag = null;
    root.classList.remove('is-dragging');
    if (moved) {
      suppressToggleClick = true;
      window.setTimeout(() => { suppressToggleClick = false; }, 500);
    }
  }
  toggle.addEventListener('pointerup', finishToggleDrag);
  toggle.addEventListener('pointercancel', finishToggleDrag);
  toggle.addEventListener('click', (event) => {
    if (suppressToggleClick) {
      event.preventDefault();
      event.stopImmediatePropagation();
      suppressToggleClick = false;
      return;
    }
    setOpen(!isOpen());
  });
  closeBtn.addEventListener('click', () => setOpen(false));
  backdrop.addEventListener('click', () => setOpen(false));
  // la page derrière ne doit pas défiler quand on fait glisser l'en-tête ou le fond
  [backdrop, head].forEach((el) => el.addEventListener('touchmove', (e) => { if (e.cancelable) e.preventDefault(); }, { passive: false }));
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && isOpen()) setOpen(false); });

  /* ── Isolation : le chat ne doit pas piloter le vaisseau de l'univers 3D ──
     L'univers écoute le clavier et la molette sur window (Z/Q/S/D, Espace, M, molette…).
     On arrête ces événements à la racine du chat : on peut taper, espaces compris, et faire
     défiler la conversation sans bouger le vaisseau. */
  ['keydown', 'keyup', 'keypress', 'wheel'].forEach((type) => {
    root.addEventListener(type, (e) => {
      if (type === 'keydown' && e.key === 'Escape' && isOpen()) setOpen(false);
      e.stopPropagation();
    }, { passive: type === 'wheel' });
  });

  /* ── Envoi ── */
  const autosize = () => { input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, 120) + 'px'; };
  input.addEventListener('input', autosize);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); form.requestSubmit(); }
  });
  form.addEventListener('submit', (e) => { e.preventDefault(); ask(input.value); });

  async function ask(raw) {
    const text = (raw || '').trim();
    if (!text || busy) return;
    busy = true; send.disabled = true;
    chips.innerHTML = '';
    bubble('user', text);
    input.value = ''; autosize();
    const wait = typing();

    const payload = { message: text, history: history.slice(-(cfg.historyMax || 12)), screen };
    try {
      const res = await fetch(cfg.url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': root.dataset.csrf || '' },
        body: JSON.stringify(payload),
      });
      let data = {};
      try { data = await res.json(); } catch (_) {}
      wait.remove();
      if (res.ok && data.reply) {
        history.push({ role: 'user', text }, { role: 'assistant', text: data.reply });
        save();
        bubble('bot', data.reply);
      } else {
        const err = bubble('err', data.error || 'Une erreur est survenue. Réessayez dans un instant.');
        if (data.debug) {   // renvoyé uniquement aux administrateurs connectés
          const dbg = document.createElement('div');
          dbg.className = 'cb-debug';
          dbg.textContent = 'Détail (visible par les admins) : ' + data.debug;
          err.appendChild(dbg);
          toBottom();
        }
      }
    } catch (_) {
      wait.remove();
      bubble('err', 'Connexion impossible. Vérifiez votre réseau puis réessayez.');
    } finally {
      busy = false; send.disabled = false;
      renderChips();
      if (isOpen() && !mobile.matches) input.focus({ preventScroll: true });
    }
  }

  boot();
  applyScreen();
})();
