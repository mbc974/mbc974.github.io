/* ============================================================
   MBC La Montagne Basket Club — Service Worker (PWA)
   Rend le site installable (écran d'accueil) et consultable
   hors-ligne. 100 % statique, aucune dépendance.
   ⚠️  Bump le nom du cache (mbc-vN) à chaque déploiement
       important pour purger l'ancien contenu.
   ============================================================ */
const CACHE = 'mbc-26450757-b91848b5-e72f7ebb';
const OFFLINE_URL = '/offline.html';
const PRECACHE = [
  '/',
  '/index.html',
  '/adhesion.html',
  '/offline.html',
  '/site.webmanifest',
  '/style.min.css?v=26450757',
  '/script.js?v=b91848b5',
  '/consent.js?v=e72f7ebb',
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
    // La cle de cache ignore la query : sans cela « /?source=pwa » (le
    // start_url du manifeste) et chaque lien partage avec un ?fbclid= ou un
    // ?utm_* creaient une entree distincte. Deux consequences reelles : la
    // PWA installee tombait sur la page hors-ligne a son premier lancement
    // sans reseau, et le cache grossissait sans limite.
    var cle = new Request(url.origin + url.pathname, { headers: req.headers });
    e.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok && !res.redirected) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(cle, copy); });
        }
        return res;
      }).catch(function () {
        return caches.match(cle).then(function (r) { return r || caches.match(OFFLINE_URL); });
      })
    );
    return;
  }

  // TOUT LE RESTE (feuille de style, scripts, images, polices, médias) :
  // stale-while-revalidate. La copie locale part immédiatement, le réseau
  // revalide en tâche de fond.
  //
  // La CSS et le JS avaient ici, jusqu'à présent, un cas particulier
  // « réseau d'abord », posé après un incident réel : un visiteur recevait le
  // HTML du jour avec la CSS de la veille. Il coûtait cher — mesuré à
  // 1,6 Mb/s, la feuille passait de 199 à 2018 ms, soit près de deux secondes
  // de rendu bloqué à chaque page vue, même la centième.
  //
  // Cet incident ne peut plus se reproduire, pour deux raisons indépendantes :
  //   1. le ?v= de style.min.css, script.js et consent.js est un hachage de
  //      leur contenu, tenu par .claude/bump-assets.py. Une feuille modifiée a
  //      donc une URL nouvelle : le cache ne peut pas la connaître, il va au
  //      réseau.
  //   2. le nom de ce cache suit ces mêmes hachages. Un changement de CSS
  //      change CACHE, et le gestionnaire « activate » efface tout l'ancien.
  //
  // PRÉCONDITION : « python .claude/bump-assets.py --check » doit sortir en 0
  // avant toute publication. C'est ce qui rend le raisonnement ci-dessus vrai.
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
