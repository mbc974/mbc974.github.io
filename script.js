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
