/* ============================================================
   MBC La Montagne Basket Club — V5 interactions
   ============================================================ */
(function () {
  'use strict';
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let navOpen = false;
  let lightboxOpen = false;

  function syncBodyLock() {
    document.body.style.overflow = (navOpen || lightboxOpen) ? 'hidden' : '';
  }

  /* ---- Mobile nav ---- */
  const burger = document.getElementById('burger');
  const nav = document.getElementById('nav');
  const backdrop = document.getElementById('navBackdrop');
  function setNav(open) {
    if (!burger || !nav) return;
    navOpen = Boolean(open);
    nav.classList.toggle('open', navOpen);
    if (backdrop) backdrop.classList.toggle('show', navOpen);
    burger.setAttribute('aria-expanded', String(navOpen));
    burger.setAttribute('aria-label', navOpen ? 'Fermer le menu' : 'Ouvrir le menu');
    syncBodyLock();
  }
  if (burger && nav) {
    burger.addEventListener('click', function () { setNav(!nav.classList.contains('open')); });
    nav.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { setNav(false); }); });
    if (backdrop) backdrop.addEventListener('click', function () { setNav(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && navOpen) setNav(false); });
    window.addEventListener('resize', function () { if (window.innerWidth > 1180) setNav(false); });
  }

  /* ---- Header + scroll bar + floating CTA ---- */
  const header = document.querySelector('.site-header');
  const scrollBar = document.getElementById('scrollBar');
  const floatCta = document.getElementById('floatCta');
  let lastY = window.scrollY;
  let scrollTicking = false;
  let footerVisible = false;

  /* Masque le bouton flottant dès que le footer est visible, afin de
     ne jamais recouvrir le crédit / la signature en bas de page. */
  const footerEl = document.querySelector('.site-footer');
  if (footerEl && floatCta && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      footerVisible = entries[0].isIntersecting;
      if (footerVisible) floatCta.classList.remove('show');
    }, { rootMargin: '0px 0px -40px 0px' }).observe(footerEl);
  }
  function updateScroll() {
    const y = window.scrollY;
    if (header) header.classList.toggle('scrolled', y > 30);
    if (header && !(nav && nav.classList.contains('open'))) {
      if (y > lastY && y > 400) header.classList.add('hide'); else header.classList.remove('hide');
    }
    lastY = y;
    if (scrollBar) {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      scrollBar.style.width = (h > 0 ? (y / h) * 100 : 0) + '%';
    }
    if (floatCta) floatCta.classList.toggle('show', y > 600 && !footerVisible);
    scrollTicking = false;
  }
  function onScroll() {
    if (!scrollTicking) {
      window.requestAnimationFrame(updateScroll);
      scrollTicking = true;
    }
  }
  updateScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* ---- Hero intro ---- */
  const hero = document.getElementById('hero');
  if (hero) requestAnimationFrame(function () { setTimeout(function () { hero.classList.add('in'); }, 80); });

  /* ---- Hero : slogans animés (rotator "Animated Hero" sans React) ----
     Alterne des slogans FR / créole. Fallback : sans JS, seul le 1er slogan
     s'affiche (cf. CSS). Respecte prefers-reduced-motion (pas de rotation). */
  const rotatorStage = document.querySelector('.hero__rotator-stage');
  if (rotatorStage) {
    const words = Array.prototype.slice.call(rotatorStage.querySelectorAll('.hero__rotator-word'));
    if (words.length) {
      rotatorStage.classList.add('is-ready');
      let idx = 0;
      words[0].classList.add('is-active');
      if (!reduceMotion && words.length > 1) {
        let timer = null;
        function advance() {
          const cur = words[idx];
          idx = (idx + 1) % words.length;
          const next = words[idx];
          cur.classList.remove('is-active');
          cur.classList.add('is-leaving');
          next.classList.add('is-active');
          /* une fois sorti par le haut, on le replace en bas SANS animation
             (évite que l'ancien slogan ne traverse la scène en repartant). */
          window.setTimeout(function () {
            cur.classList.add('no-anim');
            cur.classList.remove('is-leaving');
            void cur.offsetWidth; /* reflow : applique le saut instantané */
            cur.classList.remove('no-anim');
          }, 720);
        }
        function start() { if (!timer) timer = window.setInterval(advance, 3200); }
        function stop() { if (timer) { window.clearInterval(timer); timer = null; } }
        start();
        /* on met en pause quand l'onglet n'est pas visible. */
        document.addEventListener('visibilitychange', function () {
          if (document.hidden) stop(); else start();
        });
      }
    }
  }

  /* ---- Scroll reveal ---- */
  const reveals = document.querySelectorAll('.reveal');
  if (reduceMotion || !('IntersectionObserver' in window)) {
    reveals.forEach(function (el) { el.classList.add('in'); });
  } else {
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { entry.target.classList.add('in'); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    reveals.forEach(function (el) {
      const parent = el.parentElement;
      if (parent && (parent.classList.contains('cat-grid') ||
                     parent.classList.contains('staff-grid') || parent.classList.contains('engage-grid') ||
                     parent.classList.contains('fondatrice__pillars'))) {
        const idx = Array.prototype.indexOf.call(parent.children, el);
        el.style.transitionDelay = Math.min(idx, 6) * 90 + 'ms';
      }
      io.observe(el);
    });
  }

  /* ---- Cascade text (lien animé : chaque lettre révèle une copie au survol) ---- */
  Array.prototype.forEach.call(document.querySelectorAll('[data-cascade]'), function (el) {
    const text = (el.getAttribute('data-cascade-text') || el.textContent || '').trim();
    if (!text) return;
    el.setAttribute('aria-label', text);
    let chars;
    if (typeof Intl !== 'undefined' && Intl.Segmenter) {
      chars = Array.from(new Intl.Segmenter('fr', { granularity: 'grapheme' }).segment(text), function (s) { return s.segment; });
    } else {
      chars = Array.prototype.slice.call(text);
    }
    const inner = document.createElement('span');
    inner.className = 'cascade-link__inner';
    inner.setAttribute('aria-hidden', 'true');
    chars.forEach(function (ch, i) {
      const c = document.createElement('span');
      c.className = 'cascade-link__c';
      c.style.setProperty('--i', String(i));
      c.textContent = (ch === ' ') ? ' ' : ch;
      inner.appendChild(c);
    });
    el.textContent = '';
    el.appendChild(inner);
  });

  /* ---- Parallax ---- */
  const layers = Array.prototype.slice.call(document.querySelectorAll('[data-parallax]'));
  /* Parallax désactivé sur mobile (perf + évite tout effet de profondeur lourd au scroll tactile) */
  const allowParallax = window.matchMedia('(min-width: 760px)').matches;
  if (layers.length && !reduceMotion && allowParallax) {
    let ticking = false;
    function applyParallax() {
      const y = window.scrollY;
      layers.forEach(function (el) {
        const speed = parseFloat(el.getAttribute('data-parallax')) || 0;
        el.style.transform = 'translate3d(0,' + (y * speed).toFixed(1) + 'px,0)';
      });
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { window.requestAnimationFrame(applyParallax); ticking = true; }
    }, { passive: true });
    applyParallax();
  }

  /* ---- Counters (numeric only) ---- */
  const counters = document.querySelectorAll('[data-count]');
  function animateCount(el) {
    const target = parseInt(el.getAttribute('data-count'), 10);
    if (reduceMotion) { el.textContent = target; return; }
    const dur = 1300, start = performance.now();
    function tick(now) {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  if ('IntersectionObserver' in window && counters.length) {
    const cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { animateCount(e.target); cio.unobserve(e.target); } });
    }, { threshold: 0.6 });
    counters.forEach(function (c) { cio.observe(c); });
  } else { counters.forEach(animateCount); }

  /* ---- Poster / one-page lightbox ---- */
  const lightboxTriggers = document.querySelectorAll('[data-lightbox-src]');
  const lightbox = document.getElementById('lightbox');
  const lightboxImg = document.getElementById('lightboxImg');
  const lightboxViewport = lightbox ? lightbox.querySelector('.lightbox__viewport') : null;
  if (lightboxTriggers.length && lightbox && lightboxImg && lightboxViewport) {
    /* Contrôles (fermer + zoom) générés en JS → absents du HTML statique parsé.
       Lightbox fermée : tout reste sous inert + aria-hidden sur #lightbox. */
    const lightboxClose = document.createElement('button');
    lightboxClose.type = 'button';
    lightboxClose.className = 'lightbox__close';
    lightboxClose.setAttribute('aria-label', 'Fermer');
    lightboxClose.innerHTML = '&times;';
    lightbox.insertBefore(lightboxClose, lightbox.firstChild);

    const toolbar = document.createElement('div');
    toolbar.className = 'lightbox__toolbar';
    toolbar.setAttribute('aria-label', 'Contrôles de zoom');
    const zoomOut = document.createElement('button');
    zoomOut.type = 'button'; zoomOut.setAttribute('aria-label', 'Réduire le zoom'); zoomOut.textContent = '−';
    const zoomLabel = document.createElement('span'); zoomLabel.textContent = '100%';
    const zoomIn = document.createElement('button');
    zoomIn.type = 'button'; zoomIn.setAttribute('aria-label', 'Augmenter le zoom'); zoomIn.textContent = '+';
    const zoomReset = document.createElement('button');
    zoomReset.type = 'button'; zoomReset.setAttribute('aria-label', 'Réinitialiser le zoom'); zoomReset.textContent = 'Reset';
    toolbar.append(zoomOut, zoomLabel, zoomIn, zoomReset);
    const lightboxStage = lightbox.querySelector('.lightbox__stage');
    if (lightboxStage) lightboxStage.insertBefore(toolbar, lightboxStage.firstChild);

    let zoom = 1;
    let lastFocused = null;
    const minZoom = 0.75;
    const maxZoom = 2.5;

    function applyZoom() {
      lightboxImg.style.transform = 'scale(' + zoom + ')';
      lightboxImg.style.transformOrigin = 'center top';
      if (zoomLabel) zoomLabel.textContent = Math.round(zoom * 100) + '%';
      lightbox.classList.toggle('is-zoomed', zoom > 1.01);
    }

    function setZoom(nextZoom) {
      zoom = Math.max(minZoom, Math.min(maxZoom, nextZoom));
      applyZoom();
    }

    function openLb(src, alt, fallback) {
      zoom = 1;
      lastFocused = document.activeElement;
      lightboxImg.onerror = fallback ? function () {
        lightboxImg.onerror = null;
        lightboxImg.src = fallback;
      } : null;
      lightboxImg.src = src;
      lightboxImg.alt = alt || 'Document MBC agrandi';
      lightboxViewport.scrollTop = 0;
      lightboxViewport.scrollLeft = 0;
      applyZoom();
      lightbox.classList.add('show');
      lightbox.setAttribute('aria-hidden', 'false');
      lightbox.removeAttribute('inert');
      lightboxOpen = true;
      syncBodyLock();
      lightboxClose.focus({ preventScroll: true });
    }

    function closeLb() {
      lightbox.classList.remove('show', 'is-zoomed');
      lightbox.setAttribute('aria-hidden', 'true');
      lightbox.setAttribute('inert', '');
      lightboxOpen = false;
      syncBodyLock();
      zoom = 1;
      applyZoom();
      if (lastFocused && typeof lastFocused.focus === 'function') lastFocused.focus({ preventScroll: true });
    }

    lightboxTriggers.forEach(function (trigger) {
      trigger.addEventListener('click', function () {
        openLb(trigger.getAttribute('data-lightbox-src'), trigger.getAttribute('data-lightbox-alt'), trigger.getAttribute('data-lightbox-fallback'));
      });
      trigger.addEventListener('keydown', function (e) {
        if (trigger.tagName === 'BUTTON') return;
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openLb(trigger.getAttribute('data-lightbox-src'), trigger.getAttribute('data-lightbox-alt'), trigger.getAttribute('data-lightbox-fallback'));
        }
      });
    });

    if (zoomIn) zoomIn.addEventListener('click', function () { setZoom(zoom + 0.25); });
    if (zoomOut) zoomOut.addEventListener('click', function () { setZoom(zoom - 0.25); });
    if (zoomReset) zoomReset.addEventListener('click', function () {
      setZoom(1);
      lightboxViewport.scrollTop = 0;
      lightboxViewport.scrollLeft = 0;
    });
    lightboxClose.addEventListener('click', closeLb);
    lightbox.addEventListener('click', function (e) { if (e.target === lightbox) closeLb(); });
    document.addEventListener('keydown', function (e) {
      if (!lightbox.classList.contains('show')) return;
      if (e.key === 'Escape') closeLb();
      if (e.key === 'Tab') {
        const focusables = Array.prototype.slice.call(lightbox.querySelectorAll('button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])'));
        if (!focusables.length) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
      if ((e.key === '+' || e.key === '=') && (e.ctrlKey || e.metaKey || e.altKey)) {
        e.preventDefault();
        setZoom(zoom + 0.25);
      }
      if (e.key === '-' && (e.ctrlKey || e.metaKey || e.altKey)) {
        e.preventDefault();
        setZoom(zoom - 0.25);
      }
      if (e.key === '0' && (e.ctrlKey || e.metaKey || e.altKey)) {
        e.preventDefault();
        setZoom(1);
      }
    });
  }

  /* ---- Contact form (mailto) ---- */
  const form = document.getElementById('contactForm');
  const feedback = document.getElementById('formFeedback');
  if (form && feedback) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const nom = form.nom.value.trim();
      const email = form.email.value.trim();
      const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
      if (!nom || !emailOk) {
        feedback.textContent = 'Merci de renseigner votre nom et un email valide.';
        feedback.className = 'form-feedback err';
        return;
      }
      const subject = encodeURIComponent('Contact MBC — ' + nom);
      const body = encodeURIComponent([
        'Nom : ' + nom, 'Email : ' + email,
        'Téléphone : ' + (form.tel.value.trim() || '—'),
        'Catégorie : ' + (form.cat.value || '—'), '', form.msg.value.trim()
      ].join('\n'));
      feedback.textContent = 'Votre messagerie va s\u2019ouvrir pour finaliser l\u2019envoi…';
      feedback.className = 'form-feedback ok';
      window.location.href = 'mailto:contact@mbc974.com?subject=' + subject + '&body=' + body;
    });
  }

  /* ---- Footer year ---- */
  const legal = document.querySelector('.footer__legal');
  if (legal) {
    const y = new Date().getFullYear();
    if (y > 2026) legal.textContent = legal.textContent.replace('© 2026', '© 2026–' + y);
  }

  /* ---- 3D tilt on jersey cards (mouse-reactive) ---- */
  const tiltCards = document.querySelectorAll('.kit-card');
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  if (tiltCards.length && finePointer && !reduceMotion) {
    const MAX = 12; // deg
    tiltCards.forEach(function (card) {
      card.classList.add('tilt3d');
      // shine overlay
      const shine = document.createElement('span');
      shine.className = 'tilt3d__shine';
      card.appendChild(shine);
      let raf = null;

      card.addEventListener('pointermove', function (e) {
        const r = card.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width;   // 0..1
        const py = (e.clientY - r.top) / r.height;   // 0..1
        const rx = (0.5 - py) * (MAX * 2);
        const ry = (px - 0.5) * (MAX * 2);
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(function () {
          card.style.transform =
            'perspective(1000px) rotateX(' + rx.toFixed(2) + 'deg) rotateY(' + ry.toFixed(2) + 'deg) scale(1.02)';
          shine.style.setProperty('--mx', (px * 100).toFixed(1) + '%');
          shine.style.setProperty('--my', (py * 100).toFixed(1) + '%');
        });
      });
      card.addEventListener('pointerenter', function () { card.classList.add('is-tilting'); });
      card.addEventListener('pointerleave', function () {
        card.classList.remove('is-tilting');
        if (raf) cancelAnimationFrame(raf);
        card.style.transform = '';
      });
    });
  }

  /* ---- Hero crest : parallaxe doux à la souris (desktop uniquement) ---- */
  const crest = document.querySelector('.hero__crest--giant');
  if (crest && hero && finePointer && !reduceMotion) {
    let craf = null;
    hero.addEventListener('pointerenter', function () { crest.style.animation = 'none'; });
    hero.addEventListener('pointermove', function (e) {
      const r = hero.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width - 0.5;
      const py = (e.clientY - r.top) / r.height - 0.5;
      if (craf) cancelAnimationFrame(craf);
      craf = requestAnimationFrame(function () {
        crest.style.transform = 'translate3d(' + (px * 24).toFixed(1) + 'px,' + (py * 16).toFixed(1) + 'px,0) rotate(' + (px * 2.5).toFixed(2) + 'deg)';
      });
    });
    hero.addEventListener('pointerleave', function () {
      if (craf) cancelAnimationFrame(craf);
      crest.style.transform = '';
      crest.style.animation = '';
    });
  }

  /* ---- CTA majeurs : halo lumineux qui suit le curseur (desktop uniquement) ---- */
  if (finePointer && !reduceMotion) {
    document.querySelectorAll('.btn--primary,.btn--roi').forEach(function (btn) {
      btn.addEventListener('pointermove', function (e) {
        const r = btn.getBoundingClientRect();
        btn.style.setProperty('--bx', ((e.clientX - r.left) / r.width * 100).toFixed(1) + '%');
        btn.style.setProperty('--by', ((e.clientY - r.top) / r.height * 100).toFixed(1) + '%');
      });
    });
  }

  /* ---- Cartes "spotlight" : halo qui suit le curseur (formules partenaires) ---- */
  if (finePointer && !reduceMotion) {
    document.querySelectorAll('.pack').forEach(function (card) {
      card.addEventListener('pointermove', function (e) {
        const r = card.getBoundingClientRect();
        card.style.setProperty('--mx', ((e.clientX - r.left) / r.width * 100).toFixed(1) + '%');
        card.style.setProperty('--my', ((e.clientY - r.top) / r.height * 100).toFixed(1) + '%');
      });
    });
  }

})();

/* ============================================================
   Orbite radiale "L'essentiel en un coup d'œil"
   (adaptation native de radial-orbital-timeline — pas de React)
   ============================================================ */
(function () {
  'use strict';
  var orb = document.getElementById('essOrbital');
  if (!orb) return;
  var stage = orb.querySelector('.orbital__stage');
  var detail = orb.querySelector('.orbital__detail');
  var items = Array.prototype.slice.call(orb.querySelectorAll('.orbital__item'));
  var N = items.length;
  if (!stage || !detail || !N) return;

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var mqMobile = window.matchMedia('(max-width: 760px)');
  var mobile = mqMobile.matches;
  var R = 180, rot = 0, active = null, raf = null;

  function computeR() {
    mobile = mqMobile.matches;
    var w = stage.clientWidth || 520;
    R = Math.min(190, Math.max(120, w * 0.36));
  }
  function place() {
    if (mobile) {
      items.forEach(function (it) { it.style.transform = ''; it.style.opacity = ''; it.style.zIndex = ''; });
      return;
    }
    items.forEach(function (it, i) {
      var ang = ((i / N) * 360 + rot) % 360;
      var rad = ang * Math.PI / 180;
      var x = R * Math.cos(rad), y = R * Math.sin(rad);
      it.style.transform = 'translate(-50%,-50%) translate(' + x.toFixed(1) + 'px,' + y.toFixed(1) + 'px)';
      if (!active) {
        it.style.zIndex = String(Math.round(100 + 50 * Math.cos(rad)));
        it.style.opacity = Math.max(0.5, Math.min(1, 0.5 + 0.5 * ((1 + Math.sin(rad)) / 2))).toFixed(3);
      }
    });
  }
  function frame() {
    if (!active && !reduce && !mobile) { rot = (rot + 0.22) % 360; place(); }
    raf = window.requestAnimationFrame(frame);
  }
  function open(it) {
    active = it;
    items.forEach(function (o) {
      var on = o === it;
      o.classList.toggle('is-active', on);
      o.classList.toggle('is-dim', !on);
      var btn = o.querySelector('.orbital__node');
      if (btn) btn.setAttribute('aria-expanded', on ? 'true' : 'false');
      o.style.zIndex = on ? '300' : '70';
      o.style.opacity = on ? '1' : '0.4';
    });
    var cat = it.getAttribute('data-cat') || '';
    var label = it.querySelector('.orbital__label').textContent;
    var sub = it.querySelector('.orbital__sub');
    detail.innerHTML =
      '<button type="button" class="orbital__d-close" aria-label="Fermer le détail">×</button>' +
      '<span class="orbital__d-cat">' + cat + '</span>' +
      '<strong class="orbital__d-title">' + label + '</strong>' +
      '<div class="orbital__d-text">' + (sub ? sub.innerHTML : '') + '</div>';
    orb.classList.add('is-open');
  }
  function close() {
    if (!active) return;
    active = null;
    items.forEach(function (o) {
      o.classList.remove('is-active', 'is-dim');
      var btn = o.querySelector('.orbital__node');
      if (btn) btn.setAttribute('aria-expanded', 'false');
      o.style.opacity = '';
    });
    detail.innerHTML = '';
    orb.classList.remove('is-open');
    place();
  }

  items.forEach(function (it) {
    var btn = it.querySelector('.orbital__node');
    if (!btn) return;
    btn.addEventListener('click', function (e) {
      if (mobile) return;
      e.stopPropagation();
      if (active === it) close(); else open(it);
    });
  });
  detail.addEventListener('click', function (e) { if (e.target.closest('.orbital__d-close')) close(); });
  stage.addEventListener('click', function (e) { if (active && e.target === stage) close(); });
  document.addEventListener('keydown', function (e) { if ((e.key === 'Escape' || e.key === 'Esc') && active) close(); });

  computeR();
  place();
  if (!reduce && !mobile) raf = window.requestAnimationFrame(frame);

  var rt;
  window.addEventListener('resize', function () {
    clearTimeout(rt);
    rt = setTimeout(function () {
      computeR();
      if (mobile && active) close();
      place();
      if (mobile && raf) { window.cancelAnimationFrame(raf); raf = null; }
      else if (!mobile && !reduce && !raf) { raf = window.requestAnimationFrame(frame); }
    }, 160);
  });
})();

/* ============================================================
   Éventail staff "L'équipe MBC" — survol : mise en avant + écartement
   (adaptation native de card-fan-carousel — pas de GSAP)
   ============================================================ */
(function () {
  'use strict';
  var fan = document.getElementById('staffFan');
  if (!fan) return;
  var cards = Array.prototype.slice.call(fan.querySelectorAll('.fan-card'));
  if (cards.length !== 6) return; // l'éventail est calibré pour 6 cartes

  var XM = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5];
  var YF = [1, 0.38, 0.05, 0.05, 0.38, 1];
  var ROT = [-22, -13, -4, 4, 13, 22];
  var SC = [0.84, 0.93, 0.99, 0.99, 0.93, 0.84];
  var Z = [5, 7, 9, 9, 7, 5];
  var mqMobile = window.matchMedia('(max-width: 760px)');

  function num(name, fallback) {
    var n = parseFloat(getComputedStyle(fan).getPropertyValue(name));
    return isNaN(n) ? fallback : n;
  }
  function setT(c, x, y, rot, sc, z) {
    c.style.transform = 'translate(-50%,-50%) translateX(' + x.toFixed(1) + 'px) translateY(' + y.toFixed(1) + 'px) rotate(' + rot.toFixed(2) + 'deg) scale(' + sc.toFixed(3) + ')';
    c.style.zIndex = String(z);
  }
  function spread(hi) {
    var u = num('--u', 72), lf = num('--lift', 24);
    for (var j = 0; j < 6; j++) {
      var bx = XM[j] * u, by = YF[j] * lf;
      if (j === hi) {
        setT(cards[j], bx, by - 40, ROT[j] * 0.5, SC[j] * 1.09, 30);
      } else {
        var dir = j < hi ? -1 : 1, dist = Math.abs(j - hi);
        var push = Math.max(0, 30 - 9 * (dist - 1));
        setT(cards[j], bx + dir * push, by, ROT[j], SC[j], Z[j]);
      }
    }
  }
  function reset() {
    cards.forEach(function (c) { c.style.transform = ''; c.style.zIndex = ''; });
  }
  cards.forEach(function (c, i) {
    c.addEventListener('mouseenter', function () { if (!mqMobile.matches) spread(i); });
  });
  fan.addEventListener('mouseleave', function () { if (!mqMobile.matches) reset(); });
})();

/* ============================================================
   Pile animée "La licence MBC" — bouton Suivant fait défiler la pile
   (adaptation native de animate-card-animation — pas de framer-motion)
   ============================================================ */
(function () {
  'use strict';
  var stack = document.getElementById('licStack');
  if (!stack) return;
  var deck = stack.querySelector('.licstack__deck');
  var cards = Array.prototype.slice.call(deck.querySelectorAll('.licstack__card'));
  var btn = document.getElementById('licStackBtn');
  if (cards.length < 2 || !btn) return;

  var PCLS = ['is-p0', 'is-p1', 'is-p2'];
  var ord = cards.map(function (_, i) { return i; }); // ord[0]=avant … ord[n-1]=arrière
  var animating = false;

  function clsFor(slot) { return PCLS[Math.min(slot, PCLS.length - 1)]; }
  function setSlot(card, slot) {
    card.classList.remove('is-exit', 'is-p0', 'is-p1', 'is-p2');
    card.classList.add(clsFor(slot));
  }
  function paint() { ord.forEach(function (idx, slot) { setSlot(cards[idx], slot); }); }
  function next() {
    if (animating) return;
    animating = true;
    var exitIdx = ord[0];
    var exitCard = cards[exitIdx];
    exitCard.classList.remove('is-p0', 'is-p1', 'is-p2');
    exitCard.classList.add('is-exit');
    ord = ord.slice(1).concat(exitIdx);
    ord.forEach(function (idx, slot) {
      if (idx === exitIdx) return; // la carte sortante est replacée après l'animation
      setSlot(cards[idx], slot);
    });
    window.setTimeout(function () {
      exitCard.style.transition = 'none';
      setSlot(exitCard, ord.length - 1); // placée à l'arrière, sans glissement
      void exitCard.offsetHeight;
      exitCard.style.transition = '';
      animating = false;
    }, 600);
  }
  btn.addEventListener('click', next);
  paint();
})();

/* ============================================================
   Team showcase "L'équipe MBC" — survol synchronisé nom <-> photo
   (adaptation native de team-showcase — pas de React)
   ============================================================ */
(function () {
  'use strict';
  var root = document.getElementById('teamShowcase');
  if (!root) return;
  var els = Array.prototype.slice.call(root.querySelectorAll('[data-m]'));
  if (!els.length) return;

  function set(active) {
    els.forEach(function (el) {
      var m = el.getAttribute('data-m');
      el.classList.toggle('is-active', !!active && m === active);
      el.classList.toggle('is-dim', !!active && m !== active);
    });
  }
  els.forEach(function (el) {
    el.addEventListener('mouseenter', function () { set(el.getAttribute('data-m')); });
  });
  root.addEventListener('mouseleave', function () { set(null); });
})();

/* ============================================================
   Spotlight glow MBC autour des cartes (adaptation native de
   spotlight-card) : le liseré suit le curseur dans la carte survolée.
   ============================================================ */
(function () {
  'use strict';
  if (window.matchMedia('(hover:none)').matches) return;
  // Tous les éléments rectangulaires qui reçoivent le liseré lumineux.
  var SEL = '.essentiel-card,.hero-offer,.cine-card,.recr__visual,.cat,.tarifs,.cal-venue,' +
            '.dons__card,.impact li,.dons__fiscal,.solidaire,.partner-intro,.visi,.contact-form,.contact-info,' +
            '.action-card,.engage-card,.pack,.p-pillar,.social-card,.kit-spon,.kit-card,' +
            '.team__photo,.sponsor-card,.partner-slot,.adhesion-video__frame,.btn--ghost';
  var targets = Array.prototype.slice.call(document.querySelectorAll(SEL));
  if (!targets.length) return;
  // glow = élément enfant injecté (pas de pseudo -> aucun conflit, marche partout)
  targets.forEach(function (el) {
    if (el.querySelector(':scope > .spotglow__fx')) return;
    el.classList.add('spotglow');
    var fx = document.createElement('i');
    fx.className = 'spotglow__fx';
    fx.setAttribute('aria-hidden', 'true');
    el.appendChild(fx);
  });

  // Un seul handler délégué (rAF) : éclaire l'élément bordé sous le curseur.
  var raf = null, cx = 0, cy = 0, src = null;
  document.addEventListener('pointermove', function (e) {
    cx = e.clientX; cy = e.clientY; src = e.target;
    if (raf) return;
    raf = window.requestAnimationFrame(function () {
      raf = null;
      var el = (src && src.closest) ? src.closest('.spotglow') : null;
      if (!el) return;
      var r = el.getBoundingClientRect();
      if (!r.width) return;
      el.style.setProperty('--smx', (cx - r.left).toFixed(0) + 'px');
      el.style.setProperty('--smy', (cy - r.top).toFixed(0) + 'px');
      el.style.setProperty('--smxp', Math.max(0, Math.min(1, (cx - r.left) / r.width)).toFixed(3));
    });
  }, { passive: true });
})();

/* ============================================================
   Grille infinie "Sur le terrain" : le calque révélé suit le curseur
   (adaptation native de the-infinite-grid — pas de framer-motion)
   ============================================================ */
(function () {
  'use strict';
  var gal = document.getElementById('recrutement');
  if (!gal || !gal.querySelector('.grid-fx')) return;
  if (window.matchMedia('(hover:none)').matches) return;
  var raf = null, gx = 0, gy = 0;
  gal.addEventListener('pointermove', function (e) {
    var r = gal.getBoundingClientRect();
    gx = e.clientX - r.left; gy = e.clientY - r.top;
    if (raf) return;
    raf = window.requestAnimationFrame(function () {
      raf = null;
      gal.style.setProperty('--grx', gx.toFixed(0) + 'px');
      gal.style.setProperty('--gry', gy.toFixed(0) + 'px');
    });
  }, { passive: true });
})();

/* ============================================================
   Carte cinématique "La licence MBC" : chargement 0->100% qui révèle
   la vidéo officielle + reflet/parallaxe à la souris (sans GSAP).
   ============================================================ */
(function () {
  'use strict';
  var card = document.getElementById('cineCard');
  if (!card) return;
  var pctEl = document.getElementById('cinePct');
  var ringFg = card.querySelector('.cine-ring__fg');
  var phone = document.getElementById('cinePhone');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var DASH = 390, started = false;

  function runLoad() {
    if (started) return; started = true;
    if (reduce) {
      if (pctEl) pctEl.textContent = '100';
      if (ringFg) ringFg.style.strokeDashoffset = '0';
      card.classList.add('is-loaded');
      return;
    }
    var pct = 0;
    var iv = window.setInterval(function () {
      pct = Math.min(100, pct + 2);
      if (pctEl) pctEl.textContent = pct;
      if (ringFg) ringFg.style.strokeDashoffset = (DASH * (1 - pct / 100)).toFixed(1);
      if (pct >= 100) { window.clearInterval(iv); card.classList.add('is-loaded'); }
    }, 44);
  }

  // déclenchement fiable au défilement (l'IO peut être throttlé hors écran)
  function maybeStart() {
    if (started) return;
    var r = card.getBoundingClientRect();
    if (r.top < window.innerHeight * 0.8 && r.bottom > 0) {
      runLoad();
      window.removeEventListener('scroll', maybeStart);
    }
  }
  maybeStart();
  window.addEventListener('scroll', maybeStart, { passive: true });

  /* reflet (sheen) + parallaxe 3D du téléphone à la souris */
  if (!window.matchMedia('(hover:none)').matches) {
    var raf = null, mx = 0, my = 0, gx = 0, gy = 0;
    card.addEventListener('pointermove', function (e) {
      var r = card.getBoundingClientRect();
      mx = e.clientX - r.left; my = e.clientY - r.top;
      gx = mx / r.width - 0.5; gy = my / r.height - 0.5;
      if (raf) return;
      raf = window.requestAnimationFrame(function () {
        raf = null;
        card.style.setProperty('--mouse-x', mx.toFixed(0) + 'px');
        card.style.setProperty('--mouse-y', my.toFixed(0) + 'px');
        if (phone && !reduce) phone.style.transform = 'rotateY(' + (gx * 9).toFixed(2) + 'deg) rotateX(' + (-gy * 9).toFixed(2) + 'deg)';
      });
    }, { passive: true });
    card.addEventListener('pointerleave', function () { if (phone) phone.style.transform = ''; });
  }
})();

/* ============================================================
   Fond animé "L'essentiel" : shader WebGL natif (adaptation du
   composant shader-animation — SANS Three.js, sans build).
   Quad plein écran + fragment shader (traits lumineux radiaux).
   Pause hors-écran / onglet caché ; respecte prefers-reduced-motion.
   ============================================================ */
(function () {
  'use strict';
  var canvas = document.querySelector('.ess-shader');
  if (!canvas) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  // Comme tous les autres effets du site (parallax/tilt/spotglow/grille), on coupe sur
  // tactile/petit écran : un shader plein écran en boucle viderait la batterie mobile.
  if (window.matchMedia && window.matchMedia('(hover:none),(max-width:760px)').matches) return;

  var gl = null;
  try { gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl'); } catch (e) { gl = null; }
  if (!gl) return; // pas de WebGL -> fond nu (dégradation gracieuse)

  var vertSrc =
    'attribute vec2 position;' +
    'void main(){ gl_Position = vec4(position, 0.0, 1.0); }';

  // Maths du shader d'origine conservées, mais sortie RE-TEINTÉE bleu roi -> orange
  // ballon (identité MBC) au lieu des canaux R/V/B arc-en-ciel d'origine.
  var fragSrc = [
    'precision highp float;',
    'uniform vec2 resolution;',
    'uniform float time;',
    'void main(void){',
    '  vec2 uv = (gl_FragCoord.xy * 2.0 - resolution.xy) / min(resolution.x, resolution.y);',
    '  float t = time * 0.05;',
    '  float lineWidth = 0.002;',
    '  vec3 color = vec3(0.0);',
    '  for(int j = 0; j < 3; j++){',
    '    for(int i = 0; i < 5; i++){',
    '      color[j] += lineWidth*float(i*i) / abs(fract(t - 0.01*float(j)+float(i)*0.01)*5.0 - length(uv) + mod(uv.x+uv.y, 0.2));',
    '    }',
    '  }',
    '  float glow = color.r + color.g + color.b;',
    '  vec3 roi = vec3(0.106, 0.318, 0.620);',     // bleu roi MBC ~#1B519E
    '  vec3 orange = vec3(0.851, 0.416, 0.106);',  // orange ballon MBC ~#D96A1B
    '  vec3 tint = mix(roi, orange, clamp(glow * 0.6, 0.0, 1.0));',
    '  gl_FragColor = vec4(tint * glow, 1.0);',
    '}'
  ].join('\n');

  var buf = null, uTime = null, uRes = null, ready = false;

  function compile(type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { gl.deleteShader(s); return null; }
    return s;
  }

  // (Re)crée toutes les ressources GL — appelé au démarrage ET après webglcontextrestored.
  function initGL() {
    ready = false;
    var vs = compile(gl.VERTEX_SHADER, vertSrc);
    var fs = compile(gl.FRAGMENT_SHADER, fragSrc);
    if (!vs || !fs) return false;
    var prog = gl.createProgram();
    gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return false;
    gl.useProgram(prog);
    // Quad plein écran : 2 triangles couvrant le clip-space
    buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(prog, 'position');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    uTime = gl.getUniformLocation(prog, 'time');
    uRes = gl.getUniformLocation(prog, 'resolution');
    ready = true;
    return true;
  }
  if (!initGL()) return;

  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  function resize() {
    var w = Math.max(1, Math.floor(canvas.clientWidth * dpr));
    var h = Math.max(1, Math.floor(canvas.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
      gl.viewport(0, 0, w, h);
    }
    gl.uniform2f(uRes, canvas.width, canvas.height);
  }
  window.addEventListener('resize', resize, { passive: true });

  function onScreen() {
    var r = canvas.getBoundingClientRect();
    return r.bottom > 0 && r.top < (window.innerHeight || document.documentElement.clientHeight);
  }

  // UNE SEULE passe quand la section entre dans le viewport (pas de boucle
  // perpétuelle) : on anime ~6 s puis on FIGE la dernière image en fond statique.
  var DURATION = 6000; // ms
  var time = 1.0, rafId = 0, running = false, played = false, t0 = 0;
  function draw() {
    if (!ready || gl.isContextLost()) return;
    time += 0.05; gl.uniform1f(uTime, time); gl.drawArrays(gl.TRIANGLES, 0, 6);
  }
  function frame(ts) {
    if (!running) return;
    if (!t0) t0 = ts;
    draw();
    if (ts - t0 < DURATION) rafId = window.requestAnimationFrame(frame);
    else { running = false; rafId = 0; } // fin de la passe : image figée
  }
  function playOnce() {
    if (played || !ready) return;
    played = true; running = true; t0 = 0; resize();
    rafId = window.requestAnimationFrame(frame);
  }
  function stop() { running = false; if (rafId) window.cancelAnimationFrame(rafId); rafId = 0; }

  // Perte de contexte (reset GPU/veille) : on stoppe, puis on REJOUE la passe à la restauration.
  canvas.addEventListener('webglcontextlost', function (e) { e.preventDefault(); ready = false; stop(); }, false);
  canvas.addEventListener('webglcontextrestored', function () {
    if (initGL()) { resize(); played = false; if (!document.hidden && onScreen()) playOnce(); }
  }, false);

  // Déclencheur : la passe unique part dès que la section est visible.
  // IntersectionObserver + repli scroll/chargement -> robuste partout, et "played" garantit une seule passe.
  function maybeStart() {
    if (played) { window.removeEventListener('scroll', maybeStart); return; }
    if (onScreen()) playOnce();
  }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      for (var k = 0; k < es.length; k++) {
        if (es[k].isIntersecting) { playOnce(); io.disconnect(); break; }
      }
    }, { threshold: 0.15 });
    io.observe(canvas);
  }
  window.addEventListener('scroll', maybeStart, { passive: true });
  maybeStart();
})();
