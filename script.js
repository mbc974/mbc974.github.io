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
    var wasOpen = navOpen;
    navOpen = Boolean(open);
    nav.classList.toggle('open', navOpen);
    if (backdrop) backdrop.classList.toggle('show', navOpen);
    burger.setAttribute('aria-expanded', String(navOpen));
    burger.setAttribute('aria-label', navOpen ? 'Fermer le menu' : 'Ouvrir le menu');
    syncBodyLock();
    /* Accessibilité clavier : focus sur le premier lien à l'ouverture,
       retour du focus au burger à la fermeture (si le focus était dans le menu). */
    if (navOpen) {
      var first = nav.querySelector('a');
      if (first) first.focus();
    } else if (wasOpen && document.activeElement && nav.contains(document.activeElement)) {
      burger.focus();
    }
  }
  if (burger && nav) {
    burger.addEventListener('click', function () { setNav(!nav.classList.contains('open')); });
    nav.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { setNav(false); }); });
    if (backdrop) backdrop.addEventListener('click', function () { setNav(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && navOpen) setNav(false); });
    /* Piège de focus léger : Tab reste dans le menu mobile ouvert (burger + liens) */
    document.addEventListener('keydown', function (e) {
      if (!navOpen || e.key !== 'Tab') return;
      var items = [burger].concat(Array.prototype.slice.call(nav.querySelectorAll('a')));
      var first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
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
  const footerEl = document.querySelector('.site-footer, .seo-foot');
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

  /* ---- Hero : effets permanents suspendus hors champ ----
     Le hero n'a pas la classe .section : il echappe au
     content-visibility:auto pose sur les sections, et ses boucles
     continuent de tourner pendant les ~4000 px ou on ne le regarde
     pas. La plus couteuse anime background-position sous un flou de
     44 px — une peinture, que rien ne peut promouvoir en calque.
     Un seul observateur, seuil 0, et surtout PAS d'unobserve : il
     doit continuer a basculer dans les deux sens. Deux callbacks par
     traversee, rien de plus. Sous reduceMotion on ne l'installe meme
     pas, chaque effet du hero ayant deja son propre garde-fou. */
  if (hero && !reduceMotion && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      hero.classList.toggle('is-idle', !entries[0].isIntersecting);
    }, { threshold: 0 }).observe(hero);
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
      if (parent && parent.classList.contains('cat-grid')) {
        const idx = Array.prototype.indexOf.call(parent.children, el);
        el.style.transitionDelay = Math.min(idx, 6) * 90 + 'ms';
      }
      io.observe(el);
    });
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
    const nomEl = form.nom, emailEl = form.email;
    function setFieldError(el, on) {
      if (!el) return;
      if (on) { el.setAttribute('aria-invalid', 'true'); el.setAttribute('aria-describedby', 'formFeedback'); }
      else { el.removeAttribute('aria-invalid'); el.removeAttribute('aria-describedby'); }
    }
    /* l'erreur se lève dès que l'utilisateur corrige le champ */
    [nomEl, emailEl].forEach(function (el) {
      if (el) el.addEventListener('input', function () { setFieldError(el, false); });
    });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const nom = form.nom.value.trim();
      const email = form.email.value.trim();
      const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
      setFieldError(nomEl, !nom);
      setFieldError(emailEl, !emailOk);
      if (!nom || !emailOk) {
        feedback.textContent = !nom
          ? 'Merci d’indiquer votre nom et prénom.'
          : 'Merci d’indiquer un email valide (ex. prenom@email.com).';
        feedback.className = 'form-feedback err';
        feedback.setAttribute('role', 'alert');
        feedback.setAttribute('aria-live', 'assertive');
        const firstInvalid = !nom ? nomEl : emailEl;
        if (firstInvalid && firstInvalid.focus) firstInvalid.focus();
        return;
      }
      feedback.setAttribute('role', 'status');
      feedback.setAttribute('aria-live', 'polite');
      const subject = encodeURIComponent('Contact MBC — ' + nom);
      const body = encodeURIComponent([
        'Nom : ' + nom, 'Email : ' + email,
        'Téléphone : ' + ((form.tel && form.tel.value.trim()) || '—'),
        'Catégorie : ' + ((form.cat && form.cat.value) || '—'), '', (form.msg && form.msg.value.trim()) || ''
      ].join('\n'));
      const waHref = 'https://wa.me/262692556458?text=' + body;
      const altLinks = '<a href="' + waHref + '" target="_blank" rel="noopener">WhatsApp</a> ou par email : ' +
        '<a href="mailto:contact@mbc974.com">contact@mbc974.com</a>';

      /* Envoi réel si un endpoint (Formspree / Web3Forms) est renseigné dans data-endpoint sur le <form>.
         Tant que data-endpoint est vide, on reste sur le repli mailto ci-dessous. */
      const endpoint = (form.getAttribute('data-endpoint') || '').trim();
      if (endpoint && window.fetch) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.disabled = true;
        feedback.textContent = 'Envoi en cours…';
        feedback.className = 'form-feedback';
        fetch(endpoint, { method: 'POST', body: new FormData(form), headers: { 'Accept': 'application/json' } })
          .then(function (res) {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            feedback.textContent = 'Merci ! Votre demande a bien été envoyée — le club vous répond sous 48 h.';
            feedback.className = 'form-feedback ok';
            form.reset();
          })
          .catch(function () {
            feedback.innerHTML = 'L\u2019envoi a échoué. Contactez-nous directement sur ' + altLinks + '.';
            feedback.className = 'form-feedback err';
          })
          .then(function () { if (submitBtn) submitBtn.disabled = false; });
        return;
      }

      /* Repli mailto — message honnête : l'ouverture d'une messagerie n'est pas garantie,
         on affiche donc systématiquement les alternatives directes (WhatsApp / email). */
      feedback.innerHTML = 'Votre messagerie va s\u2019ouvrir pour finaliser l\u2019envoi. ' +
        'Si elle ne s\u2019ouvre pas, contactez-nous directement sur ' + altLinks + '.';
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

  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  /* ---- Marquee : pause au tap (WCAG 2.2.2 — le hook .is-paused vit dans style.css) ---- */
  Array.prototype.forEach.call(document.querySelectorAll('.marquee'), function (m) {
    m.addEventListener('click', function () { m.classList.toggle('is-paused'); });
  });

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
   Roster "L'équipe MBC" — rail horizontal du staff
   ------------------------------------------------------------
   Le défilement lui-même est NATIF (overflow-x + CSS scroll-snap) : il
   fonctionne au doigt, au trackpad, à la molette shift et au clavier même
   si ce script ne s'exécute pas. On n'ajoute ici que ce que le CSS ne sait
   pas faire : le drag à la souris, les deux flèches précédent / suivant et
   la barre de progression. Aucun autoplay — l'utilisateur pilote.
   ============================================================ */
(function () {
  'use strict';
  var vp   = document.getElementById('rosterViewport');
  var bar  = document.getElementById('rosterBar');
  var prev = document.getElementById('rosterPrev');
  var next = document.getElementById('rosterNext');
  if (!vp || !bar || !prev || !next) return;

  var track = vp.querySelector('.roster__track');
  var items = track ? Array.prototype.slice.call(track.children) : [];
  if (items.length < 2) return;

  // flèches + barre restent invisibles tant que ce module n'a pas démarré
  var section = vp.closest ? vp.closest('.staff') : null;
  if (section) section.classList.add('roster-ready');

  var reduce = window.matchMedia('(prefers-reduced-motion:reduce)').matches;
  var behavior = reduce ? 'auto' : 'smooth';

  function maxScroll() { return vp.scrollWidth - vp.clientWidth; }

  // Position de défilement qui amène chaque carte au bord du rail. Mesurée au
  // pixel réel (les largeurs sont fractionnaires : calc() sur une fraction de
  // carte), sinon un multiple de « largeur + gouttière » dérive de 1 à 2 px.
  function offsets() {
    var pad = parseFloat(getComputedStyle(vp).paddingLeft) || 0;
    var origin = vp.getBoundingClientRect().left + pad;
    var sl = vp.scrollLeft;
    var max = maxScroll();
    return items.map(function (el) {
      return Math.max(0, Math.min(max, sl + (el.getBoundingClientRect().left - origin)));
    });
  }
  function nearestIndex(list) {
    var sl = vp.scrollLeft, best = 0, bd = Infinity;
    for (var i = 0; i < list.length; i++) {
      var d = Math.abs(list[i] - sl);
      if (d < bd) { bd = d; best = i; }
    }
    return best;
  }
  function goToIndex(i) {
    var list = offsets();
    i = Math.max(0, Math.min(list.length - 1, i));
    vp.scrollTo({ left: list[i], behavior: behavior });
  }

  /* ---- barre de progression + état désactivé des flèches ---- */
  var raf = null, railW = 0, thumbW = 0;

  function setDisabled(btn, state) {
    if (btn.disabled === state) return;
    // ne pas laisser le focus clavier tomber dans le vide en fin de rail
    if (state && document.activeElement === btn) {
      (btn === prev ? next : prev).focus();
    }
    btn.disabled = state;
  }

  function paint() {
    var max = maxScroll();
    // Sur grand écran les six cartes tiennent sur la ligne : il n'y a plus rien
    // à faire défiler, donc plus de raison d'afficher flèches ni barre.
    var scrollable = max > 2;
    if (section) section.classList.toggle('roster-static', !scrollable);
    var p = scrollable ? Math.min(1, Math.max(0, vp.scrollLeft / max)) : 0;
    bar.style.transform = 'translateX(' + ((railW - thumbW) * p).toFixed(1) + 'px)';
    setDisabled(prev, !scrollable || p <= 0.002);
    setDisabled(next, !scrollable || p >= 0.998);
  }

  function measure() {
    railW = bar.parentNode.clientWidth;
    // longueur du curseur = part du rail visible, avec un minimum lisible
    var ratio = vp.scrollWidth > 0 ? vp.clientWidth / vp.scrollWidth : 1;
    thumbW = Math.round(railW * Math.max(0.16, Math.min(1, ratio)));
    bar.style.width = thumbW + 'px';
    paint();
  }

  vp.addEventListener('scroll', function () {
    if (raf) return;
    raf = window.requestAnimationFrame(function () { raf = null; paint(); });
  }, { passive: true });

  /* ---- flèches + clavier ---- */
  function go(dir) { goToIndex(nearestIndex(offsets()) + dir); }
  prev.addEventListener('click', function () { go(-1); });
  next.addEventListener('click', function () { go(1); });

  vp.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
    else if (e.key === 'Home') { e.preventDefault(); vp.scrollTo({ left: 0, behavior: behavior }); }
    else if (e.key === 'End') { e.preventDefault(); vp.scrollTo({ left: maxScroll(), behavior: behavior }); }
  });

  /* ---- drag à la souris (le tactile garde le scroll natif, plus fluide) ---- */
  var dragging = false, moved = false, startX = 0, startLeft = 0, pid = null;

  vp.addEventListener('pointerdown', function (e) {
    if (e.pointerType === 'touch' || e.button !== 0) return;
    if (maxScroll() < 1) return;
    dragging = true; moved = false;
    startX = e.clientX; startLeft = vp.scrollLeft; pid = e.pointerId;
    vp.classList.add('is-dragging');
  });

  vp.addEventListener('pointermove', function (e) {
    if (!dragging) return;
    var dx = e.clientX - startX;
    if (!moved) {
      if (Math.abs(dx) < 3) return;   // simple clic : on ne détourne rien
      moved = true;
      try { vp.setPointerCapture(pid); } catch (err) {}
    }
    e.preventDefault();
    vp.scrollLeft = startLeft - dx;
  });

  function endDrag() {
    if (!dragging) return;
    dragging = false;
    vp.classList.remove('is-dragging');
    if (pid !== null) { try { vp.releasePointerCapture(pid); } catch (err) {} pid = null; }
    if (!moved) return;
    // le snap CSS vient d'être réactivé : on cale nous-mêmes sur la carte la
    // plus proche pour que l'arrêt soit net plutôt que subi.
    goToIndex(nearestIndex(offsets()));
  }
  vp.addEventListener('pointerup', endDrag);
  vp.addEventListener('pointercancel', endDrag);
  vp.addEventListener('lostpointercapture', endDrag);
  // pas de fantôme de drag natif sur les portraits
  vp.addEventListener('dragstart', function (e) { e.preventDefault(); });

  /* ---- mesures ---- */
  if ('ResizeObserver' in window) {
    new ResizeObserver(function () { measure(); }).observe(vp);
  } else {
    window.addEventListener('resize', measure);
  }
  window.addEventListener('load', measure);
  measure();
})();

/* ============================================================
   Spotlight glow MBC autour des cartes (adaptation native de
   spotlight-card) : le liseré suit le curseur dans la carte survolée.
   ============================================================ */
(function () {
  'use strict';
  if (window.matchMedia('(hover:none)').matches) return;
  // Tous les éléments rectangulaires qui reçoivent le liseré lumineux.
  var SEL = '.essentiel-card,.hero-offer,.cine-card,.cat,.tarifs,.cal-venue,' +
            '.solidaire,.visi,.contact-form,.contact-info,' +
            '.pack,.p-pillar,.social-card,' +
            '.team__photo,.sponsor-card,.btn--ghost';
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
   Carte cinématique "La licence MBC" : la vidéo apparaît en fondu
   (transition CSS .cine-video) à l'entrée dans le viewport, + reflet/
   parallaxe à la souris (sans GSAP). L'ancienne jauge « 0→100 % »
   était factice (aucun chargement réel, vidéo en preload="none") :
   supprimée au profit d'une révélation honnête.
   ============================================================ */
(function () {
  'use strict';
  var card = document.getElementById('cineCard');
  if (!card) return;
  var phone = document.getElementById('cinePhone');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var started = false;

  function runLoad() {
    if (started) return; started = true;
    card.classList.add('is-loaded'); /* fondu .6s géré par le CSS (.cine-card.is-loaded .cine-video) */
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
   Vidéo adhésion (mobile) : à la lecture, le téléphone « s'approche »
   en zoom fluide (FLIP) jusqu'au plein écran, puis la vidéo joue en
   grand dans un overlay. On re-parente le téléphone sur <body> pour
   échapper au perspective/overflow de la carte. Fermeture : bouton ×,
   tap sur le fond, Échap, ou fin de la vidéo. Desktop : lecture en
   ligne inchangée. prefers-reduced-motion : ouverture instantanée.
   ============================================================ */
(function () {
  'use strict';
  var card = document.getElementById('cineCard');
  if (!card) return;
  var phone = document.getElementById('cinePhone');
  var video = card.querySelector('.adhesion-video__player');
  if (!phone || !video) return;

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function isMobile() { return window.matchMedia('(max-width: 760px)').matches; }

  /* overlay plein écran, créé une seule fois */
  var overlay = document.createElement('div');
  overlay.className = 'cine-fs';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-label', 'Vidéo d’adhésion MBC en plein écran');
  var closeBtn = document.createElement('button');
  closeBtn.type = 'button';
  closeBtn.className = 'cine-fs__close';
  closeBtn.setAttribute('aria-label', 'Fermer la vidéo');
  closeBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" stroke-linecap="round"/></svg>';
  overlay.appendChild(closeBtn);
  document.body.appendChild(overlay);

  var isOpen = false, animating = false;
  var placeholder = null, homeParent = null, lastFocus = null, flatTimer = null;

  function flip(first, last, dur, ease, onEnd) {
    var dx = first.left - last.left, dy = first.top - last.top;
    var sx = first.width / last.width, sy = first.height / last.height;
    phone.style.willChange = 'transform';
    phone.style.backfaceVisibility = 'hidden';
    phone.style.transformOrigin = 'top left';
    phone.style.transition = 'none';
    phone.style.transform = 'translate(' + dx + 'px,' + dy + 'px) scale(' + sx + ',' + sy + ')';
    phone.getBoundingClientRect(); /* reflow */
    var called = false;
    var done = function (e) {
      if (e && (e.target !== phone || e.propertyName !== 'transform')) return;
      if (called) return; called = true;
      phone.removeEventListener('transitionend', done);
      onEnd();
    };
    window.requestAnimationFrame(function () {
      phone.style.transition = 'transform ' + dur + 'ms ' + ease;
      phone.style.transform = 'translate(0,0) scale(1)';
    });
    phone.addEventListener('transitionend', done);
    window.setTimeout(done, dur + 150);
  }

  function clearPhone() {
    phone.style.transition = ''; phone.style.transform = ''; phone.style.transformOrigin = '';
    phone.style.willChange = ''; phone.style.backfaceVisibility = '';
  }

  function open() {
    if (isOpen || animating || !isMobile()) return;
    isOpen = true; animating = true;
    lastFocus = document.activeElement;
    card.classList.add('is-loaded'); /* garantit la vidéo visible */

    var first = phone.getBoundingClientRect();
    placeholder = document.createElement('div');
    placeholder.className = 'cine-phone-ph';
    placeholder.style.width = first.width + 'px';
    placeholder.style.height = first.height + 'px';
    homeParent = phone.parentNode;
    homeParent.insertBefore(placeholder, phone);

    overlay.classList.add('is-open');               /* display:flex (opacité 0) */
    overlay.insertBefore(phone, closeBtn.nextSibling);
    document.body.classList.add('cine-fs-lock');
    phone.classList.add('is-fs');
    clearPhone();
    overlay.getBoundingClientRect();                /* reflow : taille finale */

    var p = video.play(); if (p && p.catch) p.catch(function () {});
    try { closeBtn.focus({ preventScroll: true }); } catch (e) { closeBtn.focus(); }

    if (reduce) { overlay.classList.add('is-visible'); phone.classList.add('is-flat'); animating = false; return; }
    var last = phone.getBoundingClientRect();
    /* is-flat lance le « dépliage » de l'écran jusqu'aux bords, en parallèle du FLIP :
       le téléphone reste visible pendant le transit puis s'efface en plein écran. */
    window.requestAnimationFrame(function () { overlay.classList.add('is-visible'); });
    /* dépliage DIFFÉRÉ (~44% du zoom) : on voit d'abord le téléphone grandir/s'approcher,
       puis l'écran s'ouvre jusqu'aux bords pour finir en plein écran exactement quand le zoom se pose. */
    flatTimer = window.setTimeout(function () { flatTimer = null; phone.classList.add('is-flat'); }, 480);
    flip(first, last, 1080, 'cubic-bezier(.33,0,.2,1)', function () {
      animating = false; clearPhone();
    });
  }

  function restore() {
    if (flatTimer) { window.clearTimeout(flatTimer); flatTimer = null; }
    if (placeholder && homeParent) { homeParent.insertBefore(phone, placeholder); placeholder.remove(); }
    placeholder = null; homeParent = null;
    phone.classList.remove('is-fs', 'is-flat');
    clearPhone();
    overlay.classList.remove('is-open', 'is-visible');
    document.body.classList.remove('cine-fs-lock');
    animating = false; isOpen = false;
    if (lastFocus && lastFocus.focus) { try { lastFocus.focus({ preventScroll: true }); } catch (e) {} }
  }

  function close() {
    if (!isOpen || animating) return;
    animating = true;
    if (flatTimer) { window.clearTimeout(flatTimer); flatTimer = null; }
    try { video.pause(); } catch (e) {}
    overlay.classList.remove('is-visible');         /* le fond se referme */
    phone.classList.remove('is-flat');              /* l'écran se ré-encadre en téléphone pendant le retour */
    if (reduce || !placeholder) { restore(); return; }
    /* le téléphone est en grand (transform identité) -> on l'anime vers sa place d'origine */
    var target = placeholder.getBoundingClientRect();
    var cur = phone.getBoundingClientRect();
    var dx = target.left - cur.left, dy = target.top - cur.top;
    var sx = target.width / cur.width, sy = target.height / cur.height;
    phone.style.willChange = 'transform';
    phone.style.backfaceVisibility = 'hidden';
    phone.style.transformOrigin = 'top left';
    phone.style.transition = 'transform 720ms cubic-bezier(.4,0,.2,1)';
    var called = false;
    var done = function (e) {
      if (e && (e.target !== phone || e.propertyName !== 'transform')) return;
      if (called) return; called = true;
      phone.removeEventListener('transitionend', done);
      restore();
    };
    phone.addEventListener('transitionend', done);
    window.setTimeout(done, 900);
    window.requestAnimationFrame(function () {
      phone.style.transform = 'translate(' + dx + 'px,' + dy + 'px) scale(' + sx + ',' + sy + ')';
    });
  }

  /* la lecture démarre (tap sur le bouton natif = geste utilisateur) -> ouverture */
  video.addEventListener('play', function () { if (isMobile() && !isOpen) open(); });
  video.addEventListener('ended', function () { if (isOpen) close(); });
  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
  document.addEventListener('keydown', function (e) {
    if (!isOpen) return;
    if (e.key === 'Escape') { close(); return; }
    /* Piège Tab : même pattern que la lightbox — le focus reste dans l'overlay. */
    if (e.key === 'Tab') {
      var focusables = Array.prototype.slice.call(
        overlay.querySelectorAll('button,video,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])'));
      if (!focusables.length) return;
      var first = focusables[0], last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
})();



/* ============================================================
   Mesure d'audience (préparée, inactive tant que l'analytics
   n'est pas activé dans le <head> — voir commentaire ANALYTICS
   de index.html). Aucun cookie, aucun envoi si Plausible absent.
   ============================================================ */
(function () {
  'use strict';
  function track(name) {
    if (typeof window.plausible === 'function') window.plausible(name);
  }
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    var h = a.href || '';
    if (h.indexOf('yapla.com') !== -1) {
      track(h.indexOf('authentication') !== -1 ? 'Connexion espace membre'
          : h.indexOf('campaign') !== -1 ? 'Don Yapla'
          : 'Inscription Yapla');
    }
    // WhatsApp : on distingue la demande d'essai du simple contact, ce sont
    // deux intentions tres differentes cote conversion.
    else if (h.indexOf('wa.me') !== -1) {
      track(/essai/i.test(decodeURIComponent(h)) ? 'WhatsApp essai' : 'WhatsApp');
    }
    else if (h.indexOf('DOSSIER-PARTENARIAT') !== -1) track('Dossier sponsor');
    else if (h.indexOf('tel:') === 0) track('Appel telephone');
    else if (h.indexOf('mailto:') === 0) track('E-mail');
    else if (/maps\.(app\.)?goo|google\.[a-z.]+\/maps/.test(h)) track('Itineraire Maps');
    else if (/\.ics(\?|$)/.test(h)) track('Ajout agenda');
    else if (/\/adhesion\.html/.test(h)) track('Je m inscris');
  }, true);

  // Chargement de la carte : mesure si la facade sert vraiment.
  var mf = document.getElementById('mapFacade');
  if (mf) mf.addEventListener('click', function () { track('Carte chargee'); }, { once: true });

  // Selecteur d'age : quelle tranche interesse les visiteurs ?
  var ageBox = document.getElementById('age-selector');
  if (ageBox) ageBox.addEventListener('click', function (e) {
    var t = e.target && e.target.closest ? e.target.closest('.age__tab') : null;
    if (t) track('Selecteur age');
  });
  var form = document.getElementById('contactForm');
  if (form) form.addEventListener('submit', function () { track('Formulaire contact'); });
})();

/* ============================================================
   PWA — enregistrement du service worker (/sw.js).
   Rend le site installable sur l'écran d'accueil + consultable
   hors-ligne. Silencieux : aucune erreur visible si indisponible.
   ============================================================ */
(function () {
  'use strict';
  if (!('serviceWorker' in navigator)) return;
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('/sw.js').catch(function () {});
  });
})();

/* ============================================================
   Micro-parallaxe du mot de fond « KARTIÉ » (section quartier).
   Relative à la traversée de la SECTION, pas au scrollY global :
   l'amplitude reste bornée à ±12 px quelle que soit la hauteur
   de la page. Désactivée au clavier/réduction de mouvement et
   sous 900 px de large.
   ============================================================ */
(function () {
  var word = document.querySelector('.lp-word');
  if (!word) return;
  var section = word.closest('.local-proof');
  if (!section) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!window.matchMedia('(min-width: 900px)').matches) return;

  var AMPLITUDE = 12;   /* soit 24 px sur toute la traversee */
  var ticking = false;
  var visible = false;

  function update() {
    var r = section.getBoundingClientRect();
    var span = r.height + window.innerHeight;
    if (span > 0) {
      /* -1 quand la section arrive par le bas, +1 quand elle sort par le haut */
      var p = 1 - ((r.bottom) / span) * 2;
      if (p < -1) p = -1; else if (p > 1) p = 1;
      word.style.setProperty('--lp-shift', (p * AMPLITUDE).toFixed(1) + 'px');
    }
    ticking = false;
  }
  function onScroll() {
    if (!visible || ticking) return;
    ticking = true;
    window.requestAnimationFrame(update);
  }
  /* on ne calcule que si la section est a l'ecran */
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      visible = entries[0].isIntersecting;
      if (visible) update();
    }, { rootMargin: '120px' }).observe(section);
  } else {
    visible = true;
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  update();
})();

/* ============================================================
   Selecteur d'age
   ------------------------------------------------------------
   Les six panneaux sont dans le HTML : sans JS, le premier est
   ouvert et les autres restent lisibles. Le script ne fait que
   basculer l'affichage, avec la navigation clavier attendue
   d'un groupe d'onglets (fleches, Home, Fin).
   ============================================================ */
(function () {
  var box = document.getElementById('age-selector');
  if (!box) return;
  var tabs = [].slice.call(box.querySelectorAll('.age__tab'));
  var panels = [].slice.call(box.querySelectorAll('.age__panel'));
  if (!tabs.length || tabs.length !== panels.length) return;

  tabs.forEach(function (t, i) { t.setAttribute('tabindex', i === 0 ? '0' : '-1'); });

  function show(i, focus) {
    tabs.forEach(function (t, k) {
      var on = k === i;
      t.classList.toggle('is-on', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.setAttribute('tabindex', on ? '0' : '-1');
      panels[k].hidden = !on;
      panels[k].classList.toggle('is-on', on);
    });
    if (focus) tabs[i].focus();
  }

  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { show(i); });
    t.addEventListener('keydown', function (e) {
      var k = e.key, n = null;
      if (k === 'ArrowRight' || k === 'ArrowDown') n = (i + 1) % tabs.length;
      else if (k === 'ArrowLeft' || k === 'ArrowUp') n = (i - 1 + tabs.length) % tabs.length;
      else if (k === 'Home') n = 0;
      else if (k === 'End') n = tabs.length - 1;
      if (n === null) return;
      e.preventDefault();
      show(n, true);
    });
  });
})();

/* ============================================================
   Carte : injection a la demande
   ------------------------------------------------------------
   L'iframe Google Maps n'est creee qu'au clic sur la facade.
   Avant : ~700 Ko de scripts tiers et des cookies Google poses
   a chaque visite pour une carte que peu de gens manipulent.
   ============================================================ */
(function () {
  var f = document.getElementById('mapFacade');
  if (!f) return;
  f.addEventListener('click', function () {
    var url = f.getAttribute('data-embed');
    if (!url) return;
    var wrap = f.parentNode;
    var fr = document.createElement('iframe');
    fr.title = 'Carte — Gymnase de La Montagne, Saint-Denis, La Réunion';
    fr.src = url;
    fr.loading = 'lazy';
    fr.referrerPolicy = 'no-referrer-when-downgrade';
    fr.setAttribute('allowfullscreen', '');
    fr.setAttribute('sandbox',
      'allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-forms');
    wrap.classList.add('is-loaded');
    f.replaceWith(fr);
    try { fr.focus(); } catch (e) {}
  }, { once: true });
})();

/* ============================================================
   Affiche « prochain rendez-vous » : elle s'efface d'elle-meme
   ------------------------------------------------------------
   Le bloc annonce UNE rencontre precise. Passee cette date il
   deviendrait faux, et personne ne pense a retirer un bloc dans
   une page de 1500 lignes. Il porte donc sa propre date de
   peremption dans data-match-date : le lendemain, il disparait
   et le calendrier juste en dessous prend le relais.
   ============================================================ */
(function () {
  var bloc = document.getElementById('prochain-match');
  if (!bloc) return;
  var d = bloc.getAttribute('data-match-date');
  if (!d) return;
  var coup = new Date(d + 'T20:30:00');
  var fin = new Date(d + 'T23:59:59');
  if (isNaN(fin)) return;

  var now = new Date();
  if (fin < now) {
    // La rencontre est passee. Le bloc s'efface plutot que d'annoncer
    // un match qui a eu lieu. Le jour ou le club voudra afficher un
    // resultat, il suffira de passer data-state a "result" et de mettre
    // le score dans .nx__body : la structure ne bouge pas.
    if (bloc.getAttribute('data-state') !== 'result') bloc.hidden = true;
    return;
  }

  // Compteur J-XX : un simple reperage, pas un chrono anime.
  var cd = document.getElementById('nxCountdown');
  if (!cd || isNaN(coup)) return;
  var jour = 864e5;
  var a = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  var b = new Date(coup.getFullYear(), coup.getMonth(), coup.getDate());
  var n = Math.round((b - a) / jour);
  if (n > 0 && n <= 60) { cd.textContent = 'J–' + n; cd.hidden = false; }
  else if (n === 0) { cd.textContent = "C'est ce soir"; cd.hidden = false; }
})();

/* ============================================================
   Calendrier des matchs : repère la prochaine rencontre et
   atténue celles déjà jouées. Les dates restent en dur dans le
   HTML (site statique, aucune source dynamique) : le script ne
   fait que les situer par rapport à aujourd'hui.
   ============================================================ */
(function () {
  var list = document.querySelector('.mx-list');
  if (!list) return;
  var rows = Array.prototype.slice.call(list.querySelectorAll('.mx-row[data-date]'));
  if (!rows.length) return;

  var today = new Date();
  today.setHours(0, 0, 0, 0);
  var next = null;

  rows.forEach(function (row) {
    var d = new Date(row.getAttribute('data-date') + 'T20:30:00');
    if (isNaN(d)) return;
    var fin = new Date(d.getTime());
    fin.setHours(23, 59, 59, 999);
    if (fin < today) {
      row.classList.add('is-past');
    } else if (!next) {
      next = { row: row, date: d };
    }
  });

  if (!next) return;
  next.row.classList.add('is-next');

  var bandeau = document.getElementById('mxNext');
  if (!bandeau) return;
  // le nom seul : .mx-opp porte aussi le sigle, masque en CSS mais bien
  // present dans le textContent (on lisait « Sainte-SuzanneBC2S »)
  var opp = next.row.querySelector('.mx-opp__n');
  var dom = next.row.classList.contains('mx-row--dom');
  var fmt;
  try {
    fmt = next.date.toLocaleDateString('fr-FR',
      { weekday: 'long', day: 'numeric', month: 'long' });
  } catch (e) {
    fmt = next.row.getAttribute('data-date');
  }
  bandeau.innerHTML = 'Prochaine rencontre — <b>' + fmt + '</b>, 20h30, ' +
    (dom ? 'au Gymnase de La Montagne' : 'en déplacement') +
    (opp ? ', face à ' + opp.textContent.trim() : '') + '.';
  bandeau.hidden = false;
})();

/* ============================================================
   Postes bénévoles des matchs à domicile
   ------------------------------------------------------------
   Le compteur du résumé est calculé à partir de la liste, jamais
   saisi à la main : il ne peut donc pas la contredire quand un
   poste est pourvu. Sans JS, le résumé reste « Postes bénévoles »,
   la liste étant de toute façon lisible une fois dépliée.
   ============================================================ */
(function () {
  var blocs = document.querySelectorAll('.mx-roles');
  Array.prototype.forEach.call(blocs, function (d) {
    var etat = d.querySelector('.mx-roles__etat');
    var total = d.querySelectorAll('.mx-poste').length;
    if (!etat || !total) return;
    var libres = d.querySelectorAll('.mx-poste__v--libre').length;
    if (libres === 0) {
      etat.textContent = 'équipe complète';
      etat.className = 'mx-roles__etat is-complet';
    } else {
      etat.textContent = libres + ' poste' + (libres > 1 ? 's' : '') +
        ' à pourvoir';
    }
  });
})();

/* ============================================================
   Planning — filtre par catégorie
   ------------------------------------------------------------
   Masque les créneaux hors sélection, puis les journées qui se
   retrouvent vides, et réaccorde le compteur de chaque journée.
   Pas de rechargement, pas de modification de l'URL : le filtre
   est un confort de lecture, pas un état à partager.
   Sans JS, tout le planning reste affiché — les boutons, eux,
   sont retirés puisqu'ils ne feraient rien.
   ============================================================ */
(function () {
  var pl = document.querySelector('.pl');
  if (!pl) return;
  var zone = pl.querySelector('.pl-filtres');
  var boutons = pl.querySelectorAll('.pl-f');
  var creneaux = pl.querySelectorAll('.pl-slot');
  var jours = pl.querySelectorAll('.pl-jour');
  var aucun = pl.querySelector('.pl-aucun');
  if (!zone || !boutons.length || !creneaux.length) return;

  function appliquer(cat) {
    var visibles = 0;
    Array.prototype.forEach.call(creneaux, function (c) {
      var liste = ' ' + (c.getAttribute('data-cat') || '') + ' ';
      var ok = cat === 'tous' || liste.indexOf(' ' + cat + ' ') !== -1;
      c.hidden = !ok;
      if (ok) visibles++;
    });
    Array.prototype.forEach.call(jours, function (j) {
      var n = j.querySelectorAll('.pl-slot:not([hidden])').length;
      j.hidden = n === 0;
      var cpt = j.querySelector('.pl-jour__n2');
      if (cpt) cpt.textContent = n + (n > 1 ? ' créneaux' : ' créneau');
    });
    if (aucun) aucun.hidden = visibles !== 0;
  }

  Array.prototype.forEach.call(boutons, function (b) {
    b.addEventListener('click', function () {
      Array.prototype.forEach.call(boutons, function (x) {
        x.classList.remove('is-on');
        x.setAttribute('aria-pressed', 'false');
      });
      b.classList.add('is-on');
      b.setAttribute('aria-pressed', 'true');
      appliquer(b.getAttribute('data-cat'));
    });
  });
})();
