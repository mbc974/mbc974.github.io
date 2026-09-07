/* ============================================================
   MBC — consentement statistiques + evenements GA4
   ============================================================
   CONSENT MODE BASIQUE. C'est le point essentiel de ce fichier : tant que
   le visiteur n'a pas accepte, RIEN de Google n'est charge. Pas de
   gtag.js, pas de requete vers googletagmanager.com, pas de ping anonyme,
   pas de dataLayer. Un refus n'est donc pas « une mesure sans cookie » :
   c'est l'absence totale de Google sur la page.

   Le chargement lui-meme vit dans le <head> de chaque page, sous la forme
   de mbcChargerGA(). Ce fichier ne fait que decider QUAND l'appeler :

     - accord deja memorise  -> le <head> l'a deja appele, des la premiere
                                ligne de la page ;
     - clic sur « Accepter » -> on l'appelle ici ;
     - refus, ou pas encore de choix -> on ne l'appelle jamais.

   Le MBC n'utilise pas Google Ads : ad_storage, ad_user_data et
   ad_personalization restent refuses en toutes circonstances, y compris
   apres acceptation. Seul analytics_storage passe a « granted ».

   MEMOIRE DU CHOIX : localStorage, cle « mbc-consent ». La valeur ecrite
   est « accepted » ou « refused » ; « granted » est encore reconnu, c'est
   la valeur qu'ecrivait la version precedente — un visiteur qui avait
   deja accepte n'a pas a repondre une seconde fois. Tout est enveloppe
   dans des try/catch : en navigation privee, ou si le stockage est
   bloque, le bandeau reapparait, ce qui est le comportement correct —
   sans memoire, pas de consentement presume. */
(function () {
  'use strict';

  var CLE = 'mbc-consent';
  var accorde = false;

  function lire() {
    try { return localStorage.getItem(CLE); } catch (e) { return null; }
  }
  function ecrire(v) {
    try { localStorage.setItem(CLE, v); } catch (e) { /* stockage bloque */ }
  }

  var memorise = lire();
  accorde = (memorise === 'accepted' || memorise === 'granted');

  /* ---- 1. Le bandeau ------------------------------------------------- */
  /* Construit uniquement s'il doit etre montre. Ce n'est volontairement PAS
     une boite modale : elle ne bloque pas la lecture et ne capture pas le
     focus, et « Refuser » est aussi visible qu'« Accepter ». */
  function bandeau() {
    var b = document.createElement('div');
    b.className = 'ccb';
    b.setAttribute('role', 'dialog');
    b.setAttribute('aria-labelledby', 'ccbT');
    b.setAttribute('aria-describedby', 'ccbD');

    var t = document.createElement('p');
    t.className = 'ccb__t';
    t.id = 'ccbT';
    t.textContent = 'Mesure d’audience';

    var d = document.createElement('p');
    d.className = 'ccb__d';
    d.id = 'ccbD';
    d.textContent = 'Le club aimerait compter les visites pour savoir ce qui '
      + 'est utile sur ce site. Tant que vous n’avez pas accepté, aucun outil '
      + 'de mesure n’est chargé. Aucune donnée de formulaire n’est transmise.';

    var a = document.createElement('div');
    a.className = 'ccb__a';

    var oui = document.createElement('button');
    oui.type = 'button';
    oui.className = 'btn btn--primary ccb__oui';
    oui.textContent = 'Accepter';

    var non = document.createElement('button');
    non.type = 'button';
    non.className = 'ccb__non';
    non.textContent = 'Refuser';

    var lien = document.createElement('a');
    lien.className = 'ccb__lien';
    lien.href = '/confidentialite/';
    lien.textContent = 'En savoir plus';

    a.appendChild(oui);
    a.appendChild(non);
    a.appendChild(lien);
    b.appendChild(t);
    b.appendChild(d);
    b.appendChild(a);

    function repondre(accepte) {
      var avant = lire();
      ecrire(accepte ? 'accepted' : 'refused');
      b.remove();

      if (accepte) {
        accorde = true;
        /* Le chargeur vit dans le <head> : c'est ici, et seulement ici, que
           gtag.js entre dans la page pour la premiere fois. */
        if (typeof window.mbcChargerGA === 'function') window.mbcChargerGA();
        return;
      }

      /* REFUS. Tant que le bandeau ne s'ouvrait qu'en l'absence de choix, cette
         branche n'avait rien a faire : on ne pouvait pas refuser apres avoir
         accepte. Depuis que « Gerer mes cookies » rouvre le choix, c'est
         possible — et il faut alors reellement tout arreter.

         Couper analytics_storage ne suffit pas : en Consent Mode, gtag.js
         reste charge et continue d'emettre des pings sans cookie. Cela
         contredirait la promesse faite au visiteur (« rien de Google »). On
         recharge donc la page : le garde du <head> lit « refused » et
         n'appelle plus le chargeur. Le retrait des cookies est un meilleur
         effort — leur domaine est pose en « auto » par Google. */
      accorde = false;
      if (window.MBC_GA_ON) {
        if (typeof window.gtag === 'function') {
          window.gtag('consent', 'update', { 'analytics_storage': 'denied' });
        }
        var id = String(window.MBC_GA_ID || '').replace(/^G-/, '');
        ['_ga', '_ga_' + id].forEach(function (n) {
          document.cookie = n + '=; Max-Age=0; path=/';
          document.cookie = n + '=; Max-Age=0; path=/; domain=' + location.hostname;
          document.cookie = n + '=; Max-Age=0; path=/; domain=.' + location.hostname;
        });
        if (avant === 'accepted' || avant === 'granted') location.reload();
      }
    }
    oui.addEventListener('click', function () { repondre(true); });
    non.addEventListener('click', function () { repondre(false); });

    /* EN TETE DE PAGE, pas a la fin. Le bandeau est en position:fixed :
       sa place dans le DOM ne change rien a son apparence, mais elle decide
       de son rang dans l'ordre de tabulation. Ajoute en fin de <body>, il
       arrivait au 168e arret sur 171 (mesure sur l'accueil) : il fallait
       traverser toute la page pour repondre a une question posee des la
       premiere seconde.

       On l'insere APRES le lien d'evitement, qui doit rester le tout premier
       arret (WCAG 2.4.1 Contourner des blocs). */
    var evitement = document.querySelector('.skip-link');
    if (evitement && evitement.parentNode === document.body && evitement.nextSibling) {
      document.body.insertBefore(b, evitement.nextSibling);
    } else {
      document.body.insertBefore(b, document.body.firstChild);
    }
    requestAnimationFrame(function () { b.classList.add('is-on'); });
  }

  /* ---- 1 bis. Rouvrir le choix --------------------------------------- */
  /* Le bandeau n'est construit qu'en l'absence de choix memorise : sans ce
     point d'entree, un visiteur qui a repondu ne pourrait plus revenir dessus
     autrement qu'en effacant les donnees du site — ce qui viderait aussi le
     cache hors ligne. Tout element portant data-mbc-cookies le rouvre.

     L'ecouteur est SEPARE de celui des evenements : ce dernier commence par
     « if (!accorde) return », il ne verrait donc jamais le clic d'un visiteur
     ayant refuse — c'est-a-dire precisement celui qui veut changer d'avis. */
  window.mbcRouvrirConsentement = function () {
    if (document.querySelector('.ccb')) return;
    bandeau();
  };
  document.addEventListener('click', function (e) {
    var l = e.target && e.target.closest ? e.target.closest('[data-mbc-cookies]') : null;
    if (!l) return;
    e.preventDefault();
    window.mbcRouvrirConsentement();
  });

  if (!memorise) bandeau();

  /* ---- 2. Les evenements --------------------------------------------- */
  /* Un seul ecouteur delegue, en phase de capture. On ne lit QUE l'URL de
     destination : jamais un champ, jamais un texte saisi. Aucun nom, aucun
     e-mail, aucun telephone ne peut transiter par ici.

     Sans accord, evenement() ne fait RIEN — on n'empile meme pas dans
     dataLayer. Sans cette garde, un clic effectue avant le choix serait
     rejoue au moment ou gtag.js arrive : de la donnee collectee avant le
     consentement, ce qui est precisement ce qu'on veut eviter. */
  function evenement(nom) {
    if (!accorde || typeof window.gtag !== 'function') return;
    window.gtag('event', nom);
  }

  document.addEventListener('click', function (e) {
    if (!accorde) return;
    var a = e.target && e.target.closest ? e.target.closest('a[href],button[data-ga]') : null;
    if (!a) return;

    var forc = a.getAttribute && a.getAttribute('data-ga');
    if (forc) { evenement(forc); return; }

    var h = a.getAttribute('href') || '';
    if (!h) return;

    if (h.indexOf('yapla.com') !== -1) evenement('yapla_click');
    else if (h.indexOf('wa.me') !== -1) evenement('whatsapp_click');
    else if (h.indexOf('adhesion.html') !== -1) evenement('signup_click');
    else if (h.indexOf('mailto:') === 0 || h.indexOf('tel:') === 0) evenement('contact_click');
    else if (/\.ics(\?|$)/.test(h)) evenement('add_to_calendar');
    else if (/\/matchs\//.test(h)) evenement('match_cta_click');
    else if (/facebook\.com|instagram\.com|tiktok\.com|youtube\.com/.test(h)) evenement('social_click');
  }, true);

  /* Le formulaire de contact : seul l'envoi REUSSI compte. script.js emet
     « mbc:contact-ok » depuis la branche de succes de l'envoi Web3Forms.
     Aucun champ n'est lu : on ne transmet que le fait qu'un envoi a abouti. */
  var f = document.getElementById('contactForm');
  if (f) f.addEventListener('mbc:contact-ok', function () { evenement('contact_form_success'); });
})();
