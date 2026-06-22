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
      feedback.textContent = 'Votre logiciel de messagerie va s\u2019ouvrir pour finaliser l\u2019envoi…';
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
  var gal = document.getElementById('categories');
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
   Vidéo adhésion (mobile) : tap -> PLEIN ÉCRAN NATIF (100% écran,
   UI du navigateur masquée) + lecture. À la fin, on quitte le plein
   écran. Sur iOS le lecteur natif anime déjà le zoom vers/depuis le
   plein écran ; sur Android la vidéo remplit tout l'écran.
   ============================================================ */
(function () {
  'use strict';
  var card = document.getElementById('cineCard');
  if (!card) return;
  var video = card.querySelector('.adhesion-video__player');
  if (!video) return;

  function isMobile() { return window.matchMedia('(max-width: 760px)').matches; }
  function inFullscreen() {
    return !!(document.fullscreenElement || document.webkitFullscreenElement || video.webkitDisplayingFullscreen);
  }
  function enterFullscreen() {
    if (inFullscreen()) return;
    var fn = video.requestFullscreen || video.webkitRequestFullscreen || video.webkitEnterFullscreen;
    if (fn) { try { fn.call(video); } catch (e) {} }
  }
  function exitFullscreen() {
    if (document.exitFullscreen && document.fullscreenElement) { try { document.exitFullscreen(); } catch (e) {} }
    else if (document.webkitExitFullscreen && document.webkitFullscreenElement) { try { document.webkitExitFullscreen(); } catch (e) {} }
    else if (video.webkitExitFullscreen && video.webkitDisplayingFullscreen) { try { video.webkitExitFullscreen(); } catch (e) {} }
  }

  /* tap direct sur la vidéo (geste utilisateur) -> plein écran natif + lecture */
  video.addEventListener('click', function () {
    if (!isMobile() || inFullscreen()) return;
    var p = video.play();
    if (p && p.catch) p.catch(function () {});
    enterFullscreen();
  });
  /* secours : si la lecture démarre via le bouton natif, on bascule en plein écran */
  video.addEventListener('play', function () {
    if (isMobile() && !inFullscreen()) enterFullscreen();
  });
  /* fin de la vidéo -> on quitte le plein écran (retour à la page) */
  video.addEventListener('ended', exitFullscreen);
})();

/* ============================================================
   Flow field — fond animé section Parents (adaptation NATIVE du
   composant React canvas, sans React). Particules bleu MBC suivant
   un champ de flux, traînées, répulsion au survol. Tourne uniquement
   quand la section est visible ; allégé sur mobile ; coupé en
   prefers-reduced-motion (le fond normal de la section reste).
   ============================================================ */
(function () {
  'use strict';
  var canvas = document.querySelector('[data-flow-field]');
  if (!canvas) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { canvas.remove(); return; }
  var container = canvas.parentElement;
  var ctx = canvas.getContext('2d');
  if (!container || !ctx) return;

  var COLOR = '#4f86e8';                 // particules bleu MBC
  var TRAIL = 'rgba(7,13,24,0.10)';      // fondu vers le bleu nuit (traînées)
  var BASE = '#0a1426';                  // fond initial
  var SPEED = 0.8;
  var COUNT = window.matchMedia('(max-width: 760px)').matches ? 280 : 560;
  var dpr = Math.min(window.devicePixelRatio || 1, 2);

  var width = 0, height = 0, particles = [], raf = null, running = false, inited = false;
  var mouse = { x: -1000, y: -1000 };

  function reset(p) {
    p.x = Math.random() * width; p.y = Math.random() * height;
    p.vx = 0; p.vy = 0; p.age = 0; p.life = Math.random() * 200 + 100;
  }
  function update(p) {
    var angle = (Math.cos(p.x * 0.005) + Math.sin(p.y * 0.005)) * Math.PI;
    p.vx += Math.cos(angle) * 0.2 * SPEED;
    p.vy += Math.sin(angle) * 0.2 * SPEED;
    var dx = mouse.x - p.x, dy = mouse.y - p.y, dist = Math.sqrt(dx * dx + dy * dy), R = 150;
    if (dist < R) { var f = (R - dist) / R; p.vx -= dx * f * 0.05; p.vy -= dy * f * 0.05; }
    p.x += p.vx; p.y += p.vy; p.vx *= 0.95; p.vy *= 0.95;
    p.age++; if (p.age > p.life) reset(p);
    if (p.x < 0) p.x = width; if (p.x > width) p.x = 0;
    if (p.y < 0) p.y = height; if (p.y > height) p.y = 0;
  }
  function size() {
    var rect = container.getBoundingClientRect();
    width = rect.width; height = rect.height;
    canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
    canvas.style.width = width + 'px'; canvas.style.height = height + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = BASE; ctx.fillRect(0, 0, width, height);
  }
  function init() {
    size();
    particles = [];
    for (var i = 0; i < COUNT; i++) { var p = {}; reset(p); particles.push(p); }
  }
  function frame() {
    ctx.globalAlpha = 1;
    ctx.fillStyle = TRAIL;
    ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = COLOR;
    for (var i = 0; i < particles.length; i++) {
      var p = particles[i];
      update(p);
      ctx.globalAlpha = 1 - Math.abs((p.age / p.life) - 0.5) * 2;
      ctx.fillRect(p.x, p.y, 1.6, 1.6);
    }
    raf = window.requestAnimationFrame(frame);
  }
  function start() { if (!running) { running = true; raf = window.requestAnimationFrame(frame); } }
  function stop() { if (running) { running = false; window.cancelAnimationFrame(raf); } }

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) { if (!inited) { init(); inited = true; } start(); }
      else { stop(); }
    }, { threshold: 0 }).observe(container);
  } else { init(); inited = true; start(); }

  window.addEventListener('resize', function () { if (inited) init(); });
  container.addEventListener('mousemove', function (e) {
    var rect = canvas.getBoundingClientRect();
    mouse.x = e.clientX - rect.left; mouse.y = e.clientY - rect.top;
  });
  container.addEventListener('mouseleave', function () { mouse.x = -1000; mouse.y = -1000; });
})();

