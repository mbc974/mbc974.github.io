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

  /* ---- Hero : subtle 3D basketball layer (static-site canvas, no build step) ---- */
  const heroBasketLayer = document.querySelector('.hero__basket3d');
  const heroBasketCanvas = document.querySelector('.hero__basket3d-canvas');
  if (heroBasketLayer && heroBasketCanvas && heroBasketLayer.dataset.heroBasket3d !== 'off') {
    const ctx = heroBasketCanvas.getContext('2d', { alpha: true });
    const desktop3d = window.matchMedia('(min-width: 981px)');
    let basketRaf = null;
    let basketVisible = true;
    let basketW = 0;
    let basketH = 0;
    let basketDpr = 1;

    function resizeHeroBasket() {
      const rect = heroBasketCanvas.getBoundingClientRect();
      basketW = Math.max(1, rect.width);
      basketH = Math.max(1, rect.height);
      basketDpr = Math.min(2, window.devicePixelRatio || 1);
      heroBasketCanvas.width = Math.round(basketW * basketDpr);
      heroBasketCanvas.height = Math.round(basketH * basketDpr);
      ctx.setTransform(basketDpr, 0, 0, basketDpr, 0, 0);
    }

    function spherePoint(cx, cy, r, lon, lat, rot) {
      const x3 = Math.cos(lat) * Math.sin(lon + rot);
      const y3 = Math.sin(lat);
      const z3 = Math.cos(lat) * Math.cos(lon + rot);
      const depth = 1 / (1 - z3 * 0.16);
      return {
        x: cx + x3 * r * depth,
        y: cy - y3 * r * depth,
        z: z3
      };
    }

    function drawProjectedPath(cx, cy, r, points, color, width, glow) {
      ctx.save();
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      if (glow) {
        ctx.shadowColor = glow;
        ctx.shadowBlur = width * 2.2;
      }
      ctx.beginPath();
      let drawing = false;
      points.forEach(function (p) {
        if (p.z < -0.18) {
          drawing = false;
          return;
        }
        if (!drawing) {
          ctx.moveTo(p.x, p.y);
          drawing = true;
        } else {
          ctx.lineTo(p.x, p.y);
        }
      });
      ctx.stroke();
      ctx.restore();
    }

    function buildLatitude(cx, cy, r, lat, rot) {
      const pts = [];
      for (let i = -88; i <= 88; i += 2) {
        pts.push(spherePoint(cx, cy, r, i / 88 * Math.PI, lat, rot));
      }
      return pts;
    }

    function buildMeridian(cx, cy, r, lon, rot) {
      const pts = [];
      for (let i = -74; i <= 74; i += 2) {
        const lat = i / 74 * 1.22;
        pts.push(spherePoint(cx, cy, r, lon + Math.sin(lat * 1.8) * 0.22, lat, rot));
      }
      return pts;
    }

    function drawHeroBasket(now) {
      if (!ctx || !desktop3d.matches) return;
      const t = reduceMotion ? 0 : now;
      const rot = t * 0.00016;
      const bob = reduceMotion ? 0 : Math.sin(t * 0.00045) * 5;
      const cx = basketW * 0.5;
      const cy = basketH * 0.5 + bob;
      const r = Math.min(basketW, basketH) * 0.34;

      ctx.clearRect(0, 0, basketW, basketH);

      const glow = ctx.createRadialGradient(cx - r * 0.12, cy - r * 0.1, r * 0.08, cx, cy, r * 1.34);
      glow.addColorStop(0, 'rgba(255,255,255,.18)');
      glow.addColorStop(0.34, 'rgba(232,130,42,.18)');
      glow.addColorStop(0.62, 'rgba(27,81,158,.18)');
      glow.addColorStop(1, 'rgba(7,13,24,0)');
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(cx, cy, r * 1.34, 0, Math.PI * 2);
      ctx.fill();

      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.clip();

      const base = ctx.createRadialGradient(cx - r * 0.35, cy - r * 0.42, r * 0.04, cx + r * 0.18, cy + r * 0.2, r * 1.18);
      base.addColorStop(0, '#ffb15b');
      base.addColorStop(0.2, '#f1842d');
      base.addColorStop(0.58, '#c95816');
      base.addColorStop(0.82, '#692915');
      base.addColorStop(1, '#141017');
      ctx.fillStyle = base;
      ctx.fillRect(cx - r, cy - r, r * 2, r * 2);

      ctx.globalCompositeOperation = 'screen';
      let light = ctx.createRadialGradient(cx - r * 0.42, cy - r * 0.44, 0, cx - r * 0.24, cy - r * 0.32, r * 0.9);
      light.addColorStop(0, 'rgba(255,255,255,.42)');
      light.addColorStop(0.35, 'rgba(255,177,91,.22)');
      light.addColorStop(1, 'rgba(255,177,91,0)');
      ctx.fillStyle = light;
      ctx.fillRect(cx - r, cy - r, r * 2, r * 2);

      light = ctx.createRadialGradient(cx + r * 0.45, cy + r * 0.2, 0, cx + r * 0.48, cy + r * 0.18, r * 0.8);
      light.addColorStop(0, 'rgba(27,81,158,.34)');
      light.addColorStop(1, 'rgba(27,81,158,0)');
      ctx.fillStyle = light;
      ctx.fillRect(cx - r, cy - r, r * 2, r * 2);
      ctx.globalCompositeOperation = 'source-over';

      for (let i = 0; i < 85; i += 1) {
        const lon = ((i * 2.399) % (Math.PI * 2)) - Math.PI;
        const lat = Math.asin(Math.sin(i * 1.618) * 0.86);
        const p = spherePoint(cx, cy, r * 0.96, lon, lat, rot * 0.8);
        if (p.z > -0.08) {
          ctx.fillStyle = i % 7 === 0 ? 'rgba(255,226,185,.16)' : 'rgba(64,28,18,.18)';
          ctx.beginPath();
          ctx.arc(p.x, p.y, Math.max(0.7, r * 0.0055), 0, Math.PI * 2);
          ctx.fill();
        }
      }

      const seamColor = 'rgba(40,22,18,.78)';
      const seamGlow = 'rgba(255,148,58,.35)';
      [-0.42, 0.42].forEach(function (lat) {
        drawProjectedPath(cx, cy, r, buildLatitude(cx, cy, r, lat, rot), seamColor, r * 0.036, seamGlow);
      });
      [-1.55, 0, 1.55, 3.1].forEach(function (lon) {
        drawProjectedPath(cx, cy, r, buildMeridian(cx, cy, r, lon, rot), seamColor, r * 0.034, seamGlow);
      });

      const rim = ctx.createRadialGradient(cx, cy, r * 0.68, cx, cy, r);
      rim.addColorStop(0, 'rgba(0,0,0,0)');
      rim.addColorStop(0.78, 'rgba(0,0,0,.08)');
      rim.addColorStop(1, 'rgba(3,7,15,.66)');
      ctx.fillStyle = rim;
      ctx.fillRect(cx - r, cy - r, r * 2, r * 2);
      ctx.restore();

      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.strokeStyle = 'rgba(232,130,42,.28)';
      ctx.lineWidth = Math.max(1, r * 0.014);
      ctx.beginPath();
      ctx.arc(cx, cy, r * 1.01, -0.9, 2.5);
      ctx.stroke();
      ctx.strokeStyle = 'rgba(27,81,158,.22)';
      ctx.beginPath();
      ctx.arc(cx, cy, r * 1.04, 2.2, 5.2);
      ctx.stroke();
      ctx.restore();
    }

    function stopHeroBasket() {
      if (basketRaf) {
        window.cancelAnimationFrame(basketRaf);
        basketRaf = null;
      }
    }

    function loopHeroBasket(now) {
      drawHeroBasket(now);
      if (!reduceMotion && desktop3d.matches && basketVisible && !document.hidden) {
        basketRaf = window.requestAnimationFrame(loopHeroBasket);
      } else {
        basketRaf = null;
      }
    }

    function startHeroBasket() {
      stopHeroBasket();
      if (!desktop3d.matches) {
        ctx.clearRect(0, 0, basketW, basketH);
        return;
      }
      resizeHeroBasket();
      if (reduceMotion) {
        drawHeroBasket(0);
      } else if (basketVisible && !document.hidden) {
        basketRaf = window.requestAnimationFrame(loopHeroBasket);
      }
    }

    resizeHeroBasket();
    if ('IntersectionObserver' in window) {
      const basketObserver = new IntersectionObserver(function (entries) {
        basketVisible = entries[0].isIntersecting;
        if (basketVisible) startHeroBasket(); else stopHeroBasket();
      }, { threshold: 0.08 });
      basketObserver.observe(heroBasketLayer);
    } else {
      startHeroBasket();
    }
    window.addEventListener('resize', startHeroBasket, { passive: true });
    if (desktop3d.addEventListener) desktop3d.addEventListener('change', startHeroBasket);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stopHeroBasket(); else startHeroBasket();
    });
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
      if (parent && (parent.classList.contains('cat-grid') || parent.classList.contains('why-grid') ||
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
  const lightboxClose = document.getElementById('lightboxClose');
  const lightboxImg = document.getElementById('lightboxImg');
  const lightboxViewport = lightbox ? lightbox.querySelector('.lightbox__viewport') : null;
  const zoomIn = document.getElementById('lightboxZoomIn');
  const zoomOut = document.getElementById('lightboxZoomOut');
  const zoomReset = document.getElementById('lightboxZoomReset');
  const zoomLabel = document.getElementById('lightboxZoomLabel');
  if (lightboxTriggers.length && lightbox && lightboxClose && lightboxImg && lightboxViewport) {
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

  /* ---- Cartes "spotlight" : halo qui suit le curseur (why-spon + formules) ---- */
  if (finePointer && !reduceMotion) {
    document.querySelectorAll('.why-spon__item,.pack').forEach(function (card) {
      card.addEventListener('pointermove', function (e) {
        const r = card.getBoundingClientRect();
        card.style.setProperty('--mx', ((e.clientX - r.left) / r.width * 100).toFixed(1) + '%');
        card.style.setProperty('--my', ((e.clientY - r.top) / r.height * 100).toFixed(1) + '%');
      });
    });
  }
})();
