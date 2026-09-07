/* ============================================================
   MBC — consentement statistiques + evenements GA4
   ============================================================
   Ce fichier est charge sur TOUTES les pages, en defer. Il fait trois
   choses, et rien d'autre :

     1. affiche le bandeau de choix tant que le visiteur n'a pas tranche ;
     2. transmet ce choix a Google Consent Mode ;
     3. envoie une poignee d'evenements de conversion, sans aucune donnee
        personnelle.

   L'ETAT PAR DEFAUT EST « REFUSE ». Il est pose en clair dans le <head> de
   chaque page, AVANT le chargement de gtag.js — c'est la seule facon d'etre
   sur qu'aucun cookie de mesure n'existe avant le choix. Ce fichier ne fait
   que passer de « refuse » a « accepte » quand le visiteur l'accepte.

   Le MBC n'utilise pas Google Ads : ad_storage, ad_user_data et
   ad_personalization restent refuses en toutes circonstances, y compris
   apres acceptation. Seul analytics_storage bascule.

   MEMOIRE DU CHOIX : localStorage, cle « mbc-consent », valeurs
   « granted » / « denied ». C'est le PREMIER stockage local du site ; tout
   est enveloppe dans des try/catch car un navigateur en navigation privee,
   ou configure pour bloquer le stockage, leve une exception a la lecture
   comme a l'ecriture. Dans ce cas le bandeau reapparait, ce qui est le
   comportement correct : sans memoire, pas de consentement presume. */
(function () {
  'use strict';

  var CLE = 'mbc-consent';

  function lire() {
    try { return localStorage.getItem(CLE); } catch (e) { return null; }
  }
  function ecrire(v) {
    try { localStorage.setItem(CLE, v); } catch (e) { /* stockage refuse : tant pis */ }
  }
  function gtag() {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(arguments);
  }

  /* ---- 1. Le bandeau ------------------------------------------------- */
  /* Il n'est construit que s'il doit etre montre : aucune page n'a de DOM
     inutile une fois le choix fait. Ce n'est volontairement PAS une boite
     modale — elle ne bloque pas la lecture et ne capture pas le focus ;
     elle reste atteignable au clavier comme n'importe quel contenu. */
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
      + 'est utile sur ce site. Rien n’est mesuré sans votre accord, et '
      + 'aucune donnée de formulaire n’est transmise.';

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
      ecrire(accepte ? 'granted' : 'denied');
      gtag('consent', 'update', { analytics_storage: accepte ? 'granted' : 'denied' });
      b.remove();
    }
    oui.addEventListener('click', function () { repondre(true); });
    non.addEventListener('click', function () { repondre(false); });

    document.body.appendChild(b);
    /* Laisse un cadre au navigateur pour peindre avant la transition. */
    requestAnimationFrame(function () { b.classList.add('is-on'); });
  }

  if (!lire()) bandeau();

  /* ---- 2. Les evenements --------------------------------------------- */
  /* Un seul ecouteur delegue, en phase de capture, pour attraper aussi les
     liens dont le clic est intercepte ailleurs. On ne lit QUE l'URL de
     destination : jamais un champ, jamais un texte saisi. Aucun nom, aucun
     e-mail, aucun telephone ne peut transiter par ici.

     gtag() empile dans dataLayer meme si gtag.js n'est pas encore charge :
     les evenements ne sont pas perdus. Et si le consentement est refuse,
     c'est Consent Mode qui les neutralise cote Google — pas ce fichier. */
  function evenement(nom) {
    gtag('event', nom);
  }

  document.addEventListener('click', function (e) {
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
    else if (/^\/matchs\/|\/matchs\//.test(h)) evenement('match_cta_click');
    else if (/facebook\.com|instagram\.com|tiktok\.com|youtube\.com/.test(h)) evenement('social_click');
  }, true);

  /* Le formulaire de contact : seul l'envoi REUSSI compte. script.js emet
     « mbc:contact-ok » depuis la branche de succes de l'envoi Web3Forms.
     Aucun champ n'est lu : on ne transmet que le fait qu'un envoi a abouti. */
  var f = document.getElementById('contactForm');
  if (f) f.addEventListener('mbc:contact-ok', function () { evenement('contact_form_success'); });
})();
