/* ============================================================
   MBC La Montagne Basket Club — Service Worker (PWA)
   Rend le site installable (écran d'accueil) et consultable
   hors-ligne. 100 % statique, aucune dépendance.
   ⚠️  Bump le nom du cache (mbc-vN) à chaque déploiement
       important pour purger l'ancien contenu.
   ============================================================ */
const CACHE = 'mbc-1f7b081a-987ed51a';
const OFFLINE_URL = '/offline.html';
const PRECACHE = [
  '/',
  '/index.html',
  '/adhesion.html',
  '/offline.html',
  '/site.webmanifest',
  '/style.css?v=1f7b081a',
  '/script.js?v=987ed51a',
  '/assets/logos/mbc-logo.webp',
  '/assets/icons/favicon.png',
  // Les deux polices du premier ecran (le titre en Anton, les intertitres en
  // Barlow Condensed 700). Elles sont prechargees dans le <head> et pesent
  // 41 Ko a elles deux : les mettre au cache evite qu'une visite hors ligne
  // retombe sur Impact / Arial Narrow. Les autres graisses sont mises en
  // cache par le gestionnaire de fetch quand la page les demande.
  '/assets/fonts/anton-400-latin.woff2',
  '/assets/fonts/barlow-condensed-700-latin.woff2'
  // Pas d'image de hero ici : depuis que le <picture> sert deux cadrages
  // differents (mobile 912 px / desktop 1983 px), precharger une variante
  // fixe ferait telecharger a un telephone 103 Ko qu'il n'affichera jamais.
  // Le gestionnaire de fetch met de toute facon en cache celle que l'appareil
  // a reellement demandee, des la premiere visite.
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      // Ajout tolérant : une ressource manquante ne fait pas échouer toute l'installation.
      return Promise.all(PRECACHE.map(function (u) { return c.add(u).catch(function () {}); }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) { if (k !== CACHE) return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  // Cross-origin (Yapla, Google Maps après clic, réseaux sociaux…) : on laisse
  // le réseau gérer. Les polices, elles, sont désormais servies par cette origine
  // et passent donc par le cache ci-dessous comme n'importe quel asset.
  if (url.origin !== self.location.origin) return;

  // Pages (navigations) : réseau d'abord → cache en repli → page hors-ligne en dernier recours.
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); });
        return res;
      }).catch(function () {
        return caches.match(req).then(function (r) { return r || caches.match(OFFLINE_URL); });
      })
    );
    return;
  }

  // Feuille de style et script : RÉSEAU D'ABORD.
  // En stale-while-revalidate, un visiteur recevait le HTML du jour avec la CSS
  // de la veille — donc une mise en page cassée jusqu'au rechargement suivant.
  // Ces deux fichiers sont petits : on préfère quelques millisecondes de réseau
  // à un rendu faux. Le cache reste le filet en cas de coupure.
  if (/\.(css|js)(\?|$)/.test(url.pathname + url.search)) {
    e.respondWith(
      fetch(req).then(function (res) {
        if (res && res.status === 200 && res.type === 'basic') {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      }).catch(function () { return caches.match(req); })
    );
    return;
  }

  // Images, polices, médias : stale-while-revalidate.
  // Ce sont des fichiers lourds et versionnés par leur nom : servir la copie
  // locale immédiatement est ici le bon compromis.
  e.respondWith(
    caches.match(req).then(function (cached) {
      var network = fetch(req).then(function (res) {
        if (res && res.status === 200 && res.type === 'basic') {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      }).catch(function () { return cached; });
      return cached || network;
    })
  );
});
