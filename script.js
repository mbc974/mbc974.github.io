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
    /* data-count-delay : laisse la colonne finir son entree avant de compter.
       Sans ce decalage le chiffre a deja atteint sa valeur quand l'oeil arrive
       dessus, et l'animation ne sert a rien. */
    const retard = parseInt(el.getAttribute('data-count-delay'), 10) || 0;
    const dur = 1500;
    el.textContent = '0';
    window.setTimeout(function () {
      const start = performance.now();
      function tick(now) {
        const p = Math.min((now - start) / dur, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(target * eased);
        if (p < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    }, retard);
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
            /* La mesure d'audience ecoute cet evenement, et lui seul : compter
               l'evenement « submit » revenait a compter les tentatives, y
               compris celles refusees par la validation du navigateur. */
            form.dispatchEvent(new CustomEvent('mbc:contact-ok'));
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
  /* .pack et .visi ne vivent que sur la page sponsors, qui ne charge pas ce
     fichier : ils ne coutent rien ici et documentent l'intention. En
     revanche .hero-offer, .tarifs, .cal-venue, .solidaire et .social-card
     ont ete retires du site — les citer laissait croire a des composants
     qui n'existent plus. */
  var SEL = '.essentiel-card,.cat,.visi,' +
            '.contact-form,.contact-info,.pack,.p-pillar,' +
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
   Mesure d'audience
   ============================================================
   Les evenements GA4 vivent dans consent.js, charge sur TOUTES les pages
   (celui-ci ne l'est que sur la home et adhesion.html). Un seul ecouteur
   delegue y suffit, et il ne lit que des URL de destination.
   Le formulaire de contact fait exception : lui seul sait s'il a REUSSI,
   il emet donc « mbc:contact-ok » et consent.js n'a rien a deviner. */

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
   L'heure de La Réunion, pour tout le monde
   ------------------------------------------------------------
   Trois modules de ce fichier décidaient qu'une rencontre était
   passée avec un `new Date('2026-09-11T20:30:00')` — une chaîne
   SANS fuseau, que le navigateur lit donc dans le fuseau du
   VISITEUR. Depuis Paris la rencontre restait « à venir » deux
   heures après le coup de sifflet final ; depuis Tokyo elle
   basculait au passé cinq heures trop tôt. Le gymnase, lui, est
   à La Montagne : l'instant doit être le même partout.

   Les blocs générés publient désormais l'instant complet, suffixé
   +04:00 (data-debut / data-fin sur les lignes du calendrier,
   data-fin sur le bandeau du prochain match). MBC.instant() le
   lit tel quel ; il sait aussi retomber sur une date seule, pour
   un HTML qui n'aurait pas encore été régénéré.

   +04:00 est écrit en dur, et c'est volontaire : La Réunion n'a
   pas d'heure d'été. Cette valeur ne bouge jamais.
   ============================================================ */
window.MBC = window.MBC || {};
MBC.FUSEAU = '+04:00';

MBC.instant = function (iso, heureDefaut) {
  if (!iso) return null;
  var s = String(iso);
  if (!/[+-]\d{2}:\d{2}$|Z$/.test(s)) {
    s = (s.length > 10 ? s : s + 'T' + (heureDefaut || '00:00') + ':00') + MBC.FUSEAU;
  }
  var d = new Date(s);
  return isNaN(d) ? null : d;
};

/* « 20h30 » tel qu'il est écrit dans la ligne -> « 20:30 ».
   Sert de repli quand data-debut manque : l'heure lue dans la page
   vaut toujours mieux qu'une heure inventée dans le script — c'est
   exactement l'erreur que faisait le bandeau du Match Center, qui
   annonçait « 20h30 » en dur pendant que la ligne juste en dessous
   affichait l'horaire réel lu dans le PDF de la ligue. */
MBC.heureDe = function (racine) {
  var e = racine && racine.querySelector('.mx-h');
  var t = e ? e.textContent.trim() : '';
  return /^\d{1,2}\s*h\s*\d{0,2}$/.test(t)
    ? t.replace(/\s/g, '').replace('h', ':').replace(/:$/, ':00').replace(/^(\d):/, '0$1:')
    : null;
};

/* « vendredi 18 septembre 2026 », toujours lu à l'heure de La Réunion.
   Sans timeZone, un visiteur à Tokyo verrait « samedi 19 » pour un match
   du vendredi soir : le jour affiché aurait changé avec le fuseau. */
MBC.dateLongue = function (d, avecAnnee) {
  var o = { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'Indian/Reunion' };
  if (avecAnnee) o.year = 'numeric';
  var t;
  try { t = d.toLocaleDateString('fr-FR', o); }
  catch (e) {
    try { t = d.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' }); }
    catch (e2) { return ''; }
  }
  return t.charAt(0).toUpperCase() + t.slice(1);
};

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
  /* Le coup d'envoi et le coup de sifflet final, en instants ABSOLUS.
     On les emprunte à la ligne correspondante du calendrier, plus bas dans
     la page : c'est le générateur qui les y publie, fuseau compris. Écrire
     « 20h30 » ici serait faux dès la première dérogation d'horaire — et
     l'article 4 du règlement en autorise jusqu'à 5 jours avant la
     rencontre. Le repli ne devine donc pas non plus : il relit l'heure
     affichée dans la ligne. */
  var ligne = document.getElementById('match-' + d);
  var coup = MBC.instant(ligne && ligne.getAttribute('data-debut')) ||
             MBC.instant(d, MBC.heureDe(ligne) || '20:30');
  var fin = MBC.instant(ligne && ligne.getAttribute('data-fin')) ||
            MBC.instant(d, '23:59');
  if (!coup || !fin) return;

  var now = new Date();
  if (fin < now) {
    // La rencontre est passee. Le bloc s'efface plutot que d'annoncer
    // un match qui a eu lieu. Le jour ou le club voudra afficher un
    // resultat, il suffira de passer data-state a "result" et de mettre
    // le score dans .nx__body : la structure ne bouge pas.
    if (bloc.getAttribute('data-state') !== 'result') bloc.hidden = true;
    return;
  }

  // Compte a rebours jours / heures / minutes.
  //
  // Trois garde-fous, parce qu'un compteur faux est pire que pas de compteur :
  //  - au-dela de 60 jours il ne s'affiche pas (personne ne compte 8 mois) ;
  //  - des que l'ecart devient negatif il se retire et l'intervalle s'arrete ;
  //  - il se rafraichit a la minute, pas a la seconde : aucun cout perceptible,
  //    et rien qui clignote dans le coin de l'oeil.
  var cd = document.getElementById('nxCountdown');
  if (!cd || isNaN(coup)) return;

  var MIN = 6e4, H = 36e5, J = 864e5;
  var timer = null;

  function unite(valeur, libelle) {
    return '<span class="sb__cd-u"><span class="sb__cd-n">' +
      (valeur < 10 ? '0' : '') + valeur +
      '</span><span class="sb__cd-s">' + libelle + '</span></span>';
  }

  function rendre() {
    var reste = coup - new Date();

    if (reste <= 0) {
      // Le coup d'envoi est passe : soit c'est ce soir (le bloc entier
      // reste, il s'effacera demain), soit il n'y a plus rien a compter.
      cd.className = 'sb__cd sb__cd--soir';
      cd.textContent = new Date() <= fin ? "C'est ce soir" : '';
      cd.hidden = new Date() > fin;
      if (timer) { clearInterval(timer); timer = null; }
      return;
    }
    if (reste > 60 * J) {
      /* Plus rien a afficher : on arrete aussi le minuteur, qui sinon
         tournait chaque minute jusqu'a la fermeture de l'onglet. */
      cd.hidden = true;
      if (timer) { clearInterval(timer); timer = null; }
      return;
    }

    var j = Math.floor(reste / J);
    var h = Math.floor((reste % J) / H);
    var m = Math.floor((reste % H) / MIN);
    var sep = '<span class="sb__cd-sep" aria-hidden="true">\u00b7</span>';

    cd.className = 'sb__cd';
    cd.innerHTML =
      '<span class="sb__cd-lab">Prochain match dans</span>' +
      '<span class="sb__cd-val">' +
        unite(j, j > 1 ? 'jours' : 'jour') + sep +
        unite(h, 'h') + sep +
        unite(m, 'min') +
      '</span>';
    cd.hidden = false;
  }

  rendre();
  timer = setInterval(rendre, MIN);
  /* Meme regle que le rotateur du hero : rien ne tourne dans le vide
     quand l'onglet est en arriere-plan. */
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      if (timer) { clearInterval(timer); timer = null; }
    } else if (!timer && !cd.hidden) {
      rendre();
      timer = setInterval(rendre, MIN);
    }
  });
})();

/* ============================================================
   Le bandeau « prochain match » sous le hero : il se périme,
   et il se ré-arme
   ------------------------------------------------------------
   Ce bandeau est écrit par .claude/build-matchs.py. Il était le
   SEUL des trois blocs « prochain match » de la page à n'avoir
   aucune date de péremption — le scoreboard plus bas en portait
   une depuis toujours. Or c'est lui qu'on voit en premier, juste
   sous le hero : le 12 septembre au matin, il aurait encore
   annoncé « Prochain match · J1 · vendredi 11 septembre », et ce
   jusqu'à la prochaine publication du site.

   Il ne se contente pas de disparaître : disparaître laisserait
   la home sans aucune annonce de rencontre. Il se reconstruit à
   partir de la ligne suivante du calendrier, plus bas dans la
   même page.

   RIEN N'EST INVENTÉ ICI. L'écusson est cloné de cette ligne, le
   nom court, l'heure, le lieu, le lien et « entrée libre » en
   sont lus — ce sont les attributs que le générateur y publie
   exprès. Si une seule de ces pièces manque, on se rabat sur
   l'effacement : un bandeau muet vaut mieux qu'un bandeau faux.
   ============================================================ */
(function () {
  var band = document.getElementById('nxBand');
  if (!band) return;

  var fin = MBC.instant(band.getAttribute('data-fin'));
  if (!fin) return;                    // pas d'instant publié : on ne touche à rien
  if (fin >= new Date()) return;       // la rencontre annoncée n'est pas encore finie

  if (!rearmer()) band.hidden = true;

  /* Le libellé d'un camp, débarrassé de son écusson. */
  function libelle(span) {
    var c = span.cloneNode(true), cr = c.querySelector('.nx__crest');
    if (cr && cr.parentNode) cr.parentNode.removeChild(cr);
    return c.textContent.trim();
  }

  function estMbc(n) {
    var i = n && n.querySelector('img');
    return !!(i && /mbc-logo/.test(i.getAttribute('src') || ''));
  }

  function rearmer() {
    var maintenant = new Date();
    var rows = document.querySelectorAll('.mx-list .mx-row[data-date]');
    var row = null;
    for (var i = 0; i < rows.length; i++) {
      var f = MBC.instant(rows[i].getAttribute('data-fin')) ||
              MBC.instant(rows[i].getAttribute('data-date'), '23:59');
      if (f && f >= maintenant) { row = rows[i]; break; }
    }
    if (!row) return false;            // la phase est terminée : plus rien à annoncer

    var debut = MBC.instant(row.getAttribute('data-debut')) ||
                MBC.instant(row.getAttribute('data-date'), MBC.heureDe(row));
    var journee = row.querySelector('.mx-j');
    var crests = row.querySelectorAll('.mx-duel .mx-crest');
    var heure = row.querySelector('.mx-h');
    var lieu = row.querySelector('.mx-lieu');
    var fiche = row.querySelector('.mx-fiche');
    var court = row.getAttribute('data-court');
    var dom = row.classList.contains('mx-row--dom');

    var spanClub = band.querySelector('.nx__club');
    var spanOpp = band.querySelector('.nx__opp');
    var eyebrow = band.querySelector('.nx__eyebrow');
    var temps = band.querySelector('.nx__meta time');
    var ou = band.querySelector('.nx__ou');
    var cta = band.querySelector('.nx__a .btn');

    if (!debut || !journee || crests.length < 2 || !heure || !lieu || !fiche ||
        !court || !spanClub || !spanOpp || !eyebrow || !temps || !ou || !cta) return false;

    // Le nom du club tel que CETTE page l'écrit, relevé avant de rien changer.
    var nomMbc = estMbc(spanClub) ? libelle(spanClub)
               : (estMbc(spanOpp) ? libelle(spanOpp) : 'MBC');

    /* Les deux écussons de la ligne sont déjà dans l'ordre d'affichage :
       le club qui reçoit est nommé en premier. On peut donc les recopier
       tels quels, sans avoir à décider qui va à gauche. */
    function poser(span, crest, nom) {
      var cible = span.querySelector('.nx__crest');
      var img = crest.querySelector('img');
      if (cible) {
        while (cible.firstChild) cible.removeChild(cible.firstChild);
        if (img) {
          var c = img.cloneNode(true);
          c.setAttribute('sizes', '40px');   // le crest du bandeau, pas celui de la ligne
          cible.appendChild(c);
        }
      }
      // le libellé est le dernier nœud texte du camp
      var n = span.lastChild;
      while (n && n.nodeType !== 3) n = n.previousSibling;
      if (n) n.nodeValue = nom;
      else span.appendChild(document.createTextNode(nom));
    }

    poser(spanClub, crests[0], dom ? nomMbc : court);
    poser(spanOpp, crests[1], dom ? court : nomMbc);

    var nEye = eyebrow.lastChild;
    while (nEye && nEye.nodeType !== 3) nEye = nEye.previousSibling;
    if (nEye) nEye.nodeValue = journee.textContent.trim();

    temps.setAttribute('datetime', row.getAttribute('data-debut') || '');
    var sep = temps.querySelector('i');
    while (temps.firstChild) temps.removeChild(temps.firstChild);
    temps.appendChild(document.createTextNode(MBC.dateLongue(debut, true) + ' '));
    if (sep) temps.appendChild(sep);
    temps.appendChild(document.createTextNode(' ' + heure.textContent.trim()));

    ou.textContent = lieu.textContent.trim();
    cta.setAttribute('href', fiche.getAttribute('href'));

    var libre = band.querySelector('.nx__libre');
    if (libre) libre.hidden = !row.getAttribute('data-libre');
    // L'itinéraire ne vaut que pour une rencontre dont on connaît la salle.
    var itin = band.querySelector('.nx__second');
    if (itin) itin.hidden = !dom;

    band.hidden = false;
    return true;
  }
})();

/* ============================================================
   Ancre dans un volet replie
   ------------------------------------------------------------
   La refonte replie ce qui n'a pas a s'imposer : les huit
   categories, les sept rencontres, la FAQ. Or ces blocs portent
   des ancres citees ailleurs — /#match-2026-10-02 est l'URL
   canonique d'une rencontre dans le JSON-LD, /#faq est en pied
   de page. Sans ceci, le lien menerait a un bloc ferme.
   On ouvre donc chaque volet ancetre de la cible, puis on
   recale le defilement (le contenu vient de changer de hauteur).
   ============================================================ */
(function () {
  function ouvrir(hash) {
    if (!hash || hash.length < 2) return;
    var cible;
    try { cible = document.getElementById(decodeURIComponent(hash.slice(1))); }
    catch (e) { return; }
    if (!cible) return;

    var n = cible, ouvert = false;
    while (n && n !== document.body) {
      if (n.tagName === 'DETAILS' && !n.open) { n.open = true; ouvert = true; }
      n = n.parentNode;
    }
    if (!ouvert) return;
    // Le volet vient de s'ouvrir : la position calculee avant ne vaut plus.
    requestAnimationFrame(function () {
      cible.scrollIntoView({ block: 'start', behavior: 'auto' });
    });
  }

  ouvrir(location.hash);
  window.addEventListener('hashchange', function () { ouvrir(location.hash); });
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

  var maintenant = new Date();
  var next = null;

  rows.forEach(function (row) {
    /* L'instant publié par le générateur (fuseau +04:00 compris). Le repli
       relit la ligne elle-même plutôt que de supposer 20h30 : c'est l'heure
       imprimée dans le PDF de la ligue qui fait foi, pas une habitude. */
    var debut = MBC.instant(row.getAttribute('data-debut')) ||
                MBC.instant(row.getAttribute('data-date'), MBC.heureDe(row) || '20:30');
    var fin = MBC.instant(row.getAttribute('data-fin')) ||
              MBC.instant(row.getAttribute('data-date'), '23:59');
    if (!debut || !fin) return;
    /* Au coup de sifflet FINAL, pas à minuit : c'est la règle que suit déjà
       le générateur (voir MAINTENANCE.md § 1 ter). Un supporter qui ouvre le
       site à 20h45 un vendredi voit la rencontre en cours comme « à venir ». */
    if (fin < maintenant) {
      row.classList.add('is-past');
    } else if (!next) {
      next = { row: row, date: debut };
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
  var lieu = next.row.querySelector('.mx-lieu');
  /* L'heure vient de la LIGNE, pas d'une constante. « 20h30 » était écrit en
     dur ici alors que la ligne juste en dessous affiche l'horaire réel lu
     dans le PDF de la ligue : à la première dérogation, la bannière et la
     ligne se seraient contredites dans le même bloc. */
  var heure = next.row.querySelector('.mx-h');
  var fmt = MBC.dateLongue(next.date) || next.row.getAttribute('data-date');

  /* Construit par nœuds et non par innerHTML : le nom de l'adversaire faisait
     un aller-retour textContent -> innerHTML, ce qui réinterprétait comme du
     balisage tout caractère « & » ou « < » d'un nom de club. */
  bandeau.textContent = 'Prochaine rencontre — ';
  var b = document.createElement('b');
  b.textContent = fmt;
  bandeau.appendChild(b);
  bandeau.appendChild(document.createTextNode(
    (heure ? ', ' + heure.textContent.trim() : '') +
    ', ' + (dom ? 'au ' + (lieu ? lieu.textContent.trim() : 'Gymnase de La Montagne')
                : 'en déplacement') +
    (opp ? ', face à ' + opp.textContent.trim() : '') + '.'));
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

  /* --- Les deux cartes de lieu suivent le filtre -------------------------
     Choisir « U13 » ne dit pas seulement QUAND on joue, mais OU. On compte
     donc les creneaux restes visibles par lieu et on le montre sur les
     cartes juste au-dessus : celle qui accueille la categorie s'elargit,
     l'autre s'attenue. Les lieux sont apparies par data-lieu, jamais par le
     lien Maps ni par le libelle — l'un comme l'autre peuvent changer sans
     que le lieu change. Ce fut d'ailleurs le cas : les deux blocs portaient
     deux URL courtes differentes pour Ruisseau Blanc, jusqu'a ce que
     data/creneaux.json n'en garde qu'une.
     Tout ce bloc est optionnel : s'il n'y a pas de cartes, le filtre
     fonctionne comme avant. */
  var cartes = document.querySelectorAll('.cal-lieu[data-lieu]');
  var rangee = document.querySelector('.cal-lieux');

  function refletLieux(cat, libelle) {
    if (!cartes.length || !rangee) return;

    // combien de creneaux visibles par lieu, apres filtrage
    var parLieu = {};
    Array.prototype.forEach.call(creneaux, function (c) {
      if (c.hidden) return;
      var l = c.getAttribute('data-lieu');
      if (l) parLieu[l] = (parLieu[l] || 0) + 1;
    });

    var actifs = 0, indexActif = -1;
    Array.prototype.forEach.call(cartes, function (carte, i) {
      var n = parLieu[carte.getAttribute('data-lieu')] || 0;
      var cnt = carte.querySelector('.cal-lieu__cnt');
      var concerne = n > 0;

      if (cat !== 'tous' && concerne) { actifs++; indexActif = i; }

      carte.classList.toggle('is-actif', cat !== 'tous' && concerne);
      carte.classList.toggle('is-attenue', cat !== 'tous' && !concerne);

      if (cnt) {
        if (cat === 'tous' || !concerne) {
          cnt.hidden = true;
          cnt.textContent = '';
        } else {
          cnt.hidden = false;
          cnt.textContent = n + (n > 1 ? ' créneaux ' : ' créneau ') + libelle;
        }
      }
    });

    // La rangee ne s'elargit que si UN SEUL lieu est concerne : quand la
    // categorie s'entraine aux deux, les mettre a egalite est plus juste.
    rangee.classList.remove('is-lieu-1', 'is-lieu-2');
    if (cat !== 'tous' && actifs === 1 && indexActif >= 0) {
      rangee.classList.add(indexActif === 0 ? 'is-lieu-1' : 'is-lieu-2');
    }
  }

  function appliquer(cat, libelle) {
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
    refletLieux(cat, libelle);
  }

  Array.prototype.forEach.call(boutons, function (b) {
    b.addEventListener('click', function () {
      Array.prototype.forEach.call(boutons, function (x) {
        x.classList.remove('is-on');
        x.setAttribute('aria-pressed', 'false');
      });
      b.classList.add('is-on');
      b.setAttribute('aria-pressed', 'true');
      appliquer(b.getAttribute('data-cat'), (b.textContent || '').trim());
    });
  });
})();


/* ============================================================
   HERO — la signature manuscrite s'ecrit, puis cede la place
   ============================================================
   Les trois phrases sont dans le HTML, en contours SVG (voir la couche V138
   de style.css). Tout le trace est en CSS : ici on ne fait que deplacer deux
   classes, .is-on et .is-out. Retirer .is-on puis le rendre a un autre SVG
   suffit a relancer ses animations depuis zero — la phrase suivante est donc
   bel et bien REECRITE, jamais simplement rallumee.

   Sous prefers-reduced-motion on n'installe rien : la premiere phrase reste
   affichee, deja encree par le CSS. Idem si ce script ne s'execute pas — le
   .is-on pose en dur dans le HTML prend alors le relais.

   Le minuteur s'arrete franchement quand l'onglet passe en arriere-plan ou
   quand le hero sort de l'ecran : on ne reecrit pour personne. */
(function () {
  var scene = document.querySelector('[data-hw]');
  if (!scene) return;
  var phrases = scene.querySelectorAll('.hw__f');
  if (phrases.length < 2) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var TRACE = 1650, LECTURE = 3100, FONDU = 550;   /* cf. --hw-trace en CSS */
  var i = 0, minuteur = null, ongletVisible = true, heroAEcran = true;

  function attendre(ms, quoi) { minuteur = window.setTimeout(quoi, ms); }
  function arreter() { if (minuteur) { window.clearTimeout(minuteur); minuteur = null; } }

  function sortir() {
    minuteur = null;
    phrases[i].classList.add('is-out');
    attendre(FONDU, entrer);
  }
  function entrer() {
    minuteur = null;
    phrases[i].classList.remove('is-on', 'is-out');
    i = (i + 1) % phrases.length;
    phrases[i].classList.add('is-on');
    attendre(TRACE + LECTURE, sortir);
  }
  function demarrer() {
    if (minuteur) return;
    /* Si l'arret est tombe pendant le fondu, la phrase courante est restee
       transparente : on enchaine tout de suite plutot que d'afficher un vide
       pendant le temps de lecture. */
    if (phrases[i].classList.contains('is-out')) { entrer(); return; }
    attendre(LECTURE, sortir);
  }
  function arbitrer() { if (ongletVisible && heroAEcran) demarrer(); else arreter(); }

  attendre(TRACE + LECTURE, sortir);

  document.addEventListener('visibilitychange', function () {
    ongletVisible = !document.hidden;
    arbitrer();
  });

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entrees) {
      heroAEcran = entrees[0].isIntersecting;
      arbitrer();
    }).observe(scene);
  }
})();


/* ============================================================
   GALERIE — zoom parallaxe vers « Votre enfant »
   ------------------------------------------------------------
   Le seul role de ce bloc : traduire l'avancee du defilement a
   travers la scene collee en une variable CSS --p, de 0 a 1.
   Toute la mise en scene est dans style.css (bloc « GALERIE —
   zoom parallaxe ») ; ici, aucune geometrie.

   Il pose aussi .is-on. Sans lui — pas de JS, ou visiteur qui a
   demande a reduire les animations — la galerie reste la mosaique
   d'origine, legendes comprises. L'effet est un surcroit, jamais
   un prerequis pour voir les photos.

   VOLONTAIREMENT SANS IntersectionObserver. Une premiere version
   s'en servait pour ne calculer que section visible ; mais si
   l'observateur ne repond pas, --p ne bouge plus et les six
   photos restent empilees au centre d'une zone collee de 240vh :
   la panne ne ressemble pas a « pas d'animation », elle ressemble
   a une page cassee. Le rectangle qu'on lit de toute facon dit
   deja si l'on est hors ecran — ce test-la ne peut pas tomber en
   panne. Une lecture par image (requestAnimationFrame) suffit.
   ============================================================ */
(function () {
  const zone = document.getElementById('galerieZoom');
  if (!zone) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  zone.classList.add('is-on');

  let demande = false;
  let vivante = false;

  function calculer() {
    demande = false;
    const r = zone.getBoundingClientRect();
    const h = window.innerHeight;

    /* hors champ : on ne touche a rien, et on rend la main au navigateur
       (le will-change des six calques coute de la memoire graphique). */
    if (r.bottom < 0 || r.top > h) {
      if (vivante) { vivante = false; zone.classList.remove('is-live'); }
      return;
    }
    if (!vivante) { vivante = true; zone.classList.add('is-live'); }

    /* course utile = ce qui depasse la fenetre : la scene reste collee
       pendant exactement cette distance. */
    const course = r.height - h;
    if (course <= 0) { zone.style.setProperty('--p', '0'); return; }
    let p = -r.top / course;
    if (p < 0) p = 0; else if (p > 1) p = 1;
    zone.style.setProperty('--p', p.toFixed(4));
  }

  function auDefilement() {
    if (!demande) { demande = true; requestAnimationFrame(calculer); }
  }

  window.addEventListener('scroll', auDefilement, { passive: true });
  window.addEventListener('resize', auDefilement);
  calculer();
})();
