# Maintenance technique — mbc974.com

Complément au [README](README.md), qui couvre déjà la structure, l'hébergement et le SEO.
Ce document rassemble ce qui n'y figure pas : analytics, RGPD, sécurité, accessibilité, tests
et tâches qui ne peuvent pas être faites depuis le dépôt.

---

## 1. Règle absolue après modification de `style.css` ou `script.js`

```bash
python .claude/build-css.py      # seulement si style.css a bougé
python .claude/bump-assets.py
```

`bump-assets.py` recalcule l'empreinte des fichiers servis, met à jour le `?v=…` dans **toutes**
les pages et le nom du cache du service worker. **Sans ce bump, les visiteurs gardent l'ancienne
CSS** : le service worker sert alors une feuille périmée sur un HTML à jour, et la mise en page
casse.

### La feuille éditée n'est pas la feuille servie

On édite **`style.css`** — c'est la source, et c'est elle qui porte les commentaires de version.
Les pages, elles, chargent **`style.min.css`**, que `build-css.py` produit en retirant ces
commentaires. Ils font 230 Ko sur 512, et 88 Ko sur 139 une fois compressés, sur la seule
ressource qui bloque le rendu : les enlever fait gagner **644 ms de premier rendu** à 1,6 Mb/s
(mesuré, quatre passages par variante).

`style.min.css` est **généré** : toute modification faite dedans sera écrasée. `build-css.py` ne
retire que les commentaires et les lignes vides — il ne renomme, ne réordonne et ne raccourcit
rien, et l'équivalence a été vérifiée dans le navigateur (4 300 règles CSSOM, `cssText`
identique pour chacune).

Le piège est d'éditer `style.css` sans régénérer : le hachage de `style.min.css` ne bougerait
pas, les pages garderaient leur `?v=` et le site continuerait de servir l'ancienne feuille, sans
qu'aucun voyant ne passe au rouge. `bump-assets.py` **refuse donc de tourner** dans ce cas et dit
quoi lancer. `python .claude/build-css.py --check` fait le même contrôle seul.

Pour les **images**, la règle est différente : une nouvelle photo = **un nouveau nom de fichier**.
Le service worker met les médias en cache par leur nom ; réutiliser un nom sert l'ancienne image.

---

## 1 bis. Les pages générées — on modifie le JSON, jamais le HTML

Une partie du site est produite par des scripts. Les fichiers concernés portent tous un
commentaire qui le dit ; les modifier à la main, c'est perdre son travail à la régénération
suivante.

| Ce qu'on veut changer | Le fichier à modifier | La commande |
|---|---|---|
| Une rencontre (date, heure, adversaire, bénévoles) | `data/matchs.json` | `python .claude/build-matchs.py` |
|  ↳ *le ruban de saison de l'accueil se régénère avec* | — | *(appelé par `build-matchs.py`, ne pas lancer à la main)* |
| Un article d'actualité | `data/actualites.json` | `python .claude/build-actus.py` |
| Un créneau d'entraînement, une catégorie, un tarif | `data/creneaux.json` | `python .claude/affiche-creneaux.py` **puis** `build-creneaux.py` |
| Une photo de catégorie ou un portrait du staff | remplacer le `.jpg` dans `assets/` | `python .claude/build-vignettes.py` |
| L'image de partage d'une rencontre (og:image) | `data/matchs.json` | `python .claude/build-og-matchs.py` puis `build-matchs.py` |
| Un joueur de l'effectif seniors | `data/effectif.json` | `python .claude/build-effectif.py` |
| Le calendrier officiel (nouveau PDF de la ligue) | déposer le PDF dans Téléchargements | `python .claude/set-calendrier-prm.py` |
| La photo du hero | `.claude/sources/hero-…jpg` | `python .claude/build-hero.py` |
| Le sitemap | rien, il se déduit des pages | `python .claude/build-sitemap.py` |
| La feuille de style | `style.css` | `python .claude/build-css.py` |

**L'ordre compte.** `bump-assets.py` se lance **en dernier** : les générateurs relèvent le
`?v=` sur une page existante, donc bumper avant leur ferait écrire une version périmée.

`set-calendrier-prm.py` refuse d'écrire si le PDF de la ligue et `data/matchs.json` ne disent
pas la même chose — c'est voulu : deux sources qui divergent, c'est un site à moitié faux.
Corriger le JSON, puis relancer.

---

## 1 ter. Le soir d'un match — publier un résultat

**Un seul geste :** dès que la ligue publie le PDF avec les scores, on le dépose dans
Téléchargements et on lance

```bash
python .claude/set-calendrier-prm.py
python .claude/bump-assets.py
```

Le script recopie le score dans `data/matchs.json`, bascule le `statut` de `a-venir` à `joue`,
puis relance `build-matchs.py`. Le résultat apparaît alors aux **trois** endroits d'un coup :
la ligne du Match Center sur l'accueil, la carte de `/matchs/`, et la ligne « Résultat » des
informations pratiques de la fiche. Le vert marque une victoire, le blanc énonce une défaite,
le bleu un match nul — et un lecteur d'écran entend « Victoire du MBC, score » avant les
chiffres.

**Ce qui n'est jamais fait :** deviner. Tant que le PDF imprime `...  ...` à la place du score,
rien n'est écrit nulle part. Et un PDF sans score n'efface pas un score déjà enregistré — celui
de la journée suivante ne republie pas les résultats des précédentes.

**La forme du champ**, si on doit le saisir à la main dans `data/matchs.json` :

```json
"score": { "mbc": 72, "adverse": 65 }
```

toujours du point de vue du MBC, jamais dans l'ordre d'affichage. Le générateur remet les
chiffres dans le bon sens selon que la rencontre est à domicile ou en déplacement. Une autre
forme (une chaîne « 72-65 », par exemple) fait échouer `build-matchs.py` avec un message
explicite plutôt que de produire une page fausse.

**Le passage « à venir » → « déjà joué »** se fait au **coup de sifflet final**, pas au coup
d'envoi : la bascule compare l'heure de fin (début + `duree`, 120 minutes par défaut). Un
supporter qui ouvre le site à 20h45 un vendredi voit toujours la rencontre en cours comme
« prochain match ».

---

## 2. Lancer le site en local

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/static-server.ps1 -Port 8010
```

Puis ouvrir `http://localhost:8010`. Aucun build, aucune dépendance npm : les fichiers sont servis tels quels.

---

## 3. Analytics — catalogue des événements

**Google Analytics 4 est posé sur les 25 pages, en Consent Mode.** Rien de Google n'est chargé
tant que le visiteur n'a pas accepté : `set-analytics.py --etat` le dit page par page.
Plausible avait été préparé puis abandonné au profit de GA4 ; ce paragraphe le décrivait
encore comme « préparé mais désactivé », en contradiction avec le § 5 du même document.

Le code de suivi est **centralisé dans `script.js`** (un seul écouteur délégué sur `document`,
pas de snippets dispersés dans le HTML). Il est inerte tant que `window.plausible` n'existe pas :

```js
function track(name){ if (typeof window.plausible === 'function') window.plausible(name); }
```

| Événement | Déclencheur | Objectif |
|---|---|---|
| `Inscription Yapla` | lien vers `yapla.com` (hors campagne/authentification) | conversion principale |
| `Don Yapla` | lien Yapla contenant `campaign` | don |
| `Connexion espace membre` | lien Yapla contenant `authentication` | usage adhérent |
| `WhatsApp` | tout lien `wa.me` | prise de contact |
| `WhatsApp essai` | lien `wa.me` dont le message contient « essai » | demande d'essai qualifiée |
| `Je m inscris` | tout lien vers `/adhesion.html` | intention d'inscription |
| `Appel telephone` | lien `tel:` | contact direct |
| `E-mail` | lien `mailto:` | contact direct |
| `Itineraire Maps` | lien Google Maps | intention de venir |
| `Ajout agenda` | téléchargement d'un `.ics` | intention de venir à un match |
| `Carte chargee` | clic sur la façade de carte | mesure l'utilité de la carte |
| `Selecteur age` | clic sur un onglet du sélecteur d'âge | quelle tranche intéresse |
| `Dossier sponsor` | téléchargement du PDF partenaire | piste B2B |
| `Formulaire contact` | envoi du formulaire | contact abouti |

**Pour retirer la mesure** : `python .claude/set-analytics.py --off` la retire des 25 pages d'un
geste. ⚠️ Mettre alors `/confidentialite/` à jour en conséquence.

---

## 4. RGPD — ce qui reste à valider par le bureau

La page `/confidentialite/` est en ligne. **Deux points y restent en attente**, signalés dans
la page par un encadré, plutôt que remplis avec des valeurs inventées :

1. **Transferts hors UE** — les garanties (clauses contractuelles types, décision d'adéquation)
   doivent être confirmées service par service auprès de GitHub, Google et Web3Forms.
2. **Activation de Plausible** — si elle a lieu, la section « Cookies » doit être révisée.

Les **durées de conservation** ne sont plus en attente : elles sont publiées sous forme de
**critères**, catégorie par catégorie, ce que l'article 13 du RGPD autorise explicitement quand
une durée fixe ne peut pas être annoncée à l'avance. Si le bureau arrête un jour des durées
chiffrées, elles remplaceront les critères — mais la page n'est plus incomplète en attendant.

Un juriste ou la personne référente RGPD du club doit relire la page avant de la considérer comme définitive.

**Sous-traitants réellement utilisés** (vérifiés dans le code, pas supposés) :
GitHub Pages (hébergement) · Web3Forms (formulaire) · Google Maps (au clic uniquement) ·
Yapla (adhésion/paiement, hors site).
**Google Fonts ne figure plus dans cette liste** : les polices sont servies par le site depuis
le 06/09/2026, plus aucune requête ne part vers Google au chargement d'une page.

---

## 5. Sécurité — limite de plateforme, mesurée

Relevé sur la production le 27/08/2026 :

| En-tête | État |
|---|---|
| `Strict-Transport-Security` | **absent** |
| `Content-Security-Policy` | **absent** |
| `X-Content-Type-Options` | **absent** |
| `Referrer-Policy` | **absent** (en-tête) |
| `Permissions-Policy` | **absent** |
| `X-Frame-Options` | **absent** |

**GitHub Pages ne permet pas de définir d'en-têtes HTTP personnalisés.** Ce n'est pas un oubli de
configuration : la plateforme n'offre aucun mécanisme pour cela.

Ce qui est en place au niveau HTML, et qui fonctionne réellement (recompté le 07/09/2026) :

- `<meta name="referrer" content="strict-origin-when-cross-origin">` sur **les 25 pages** ;
- `rel="noopener"` sur **les 97 liens** `target="_blank"` (protection contre le tabnabbing) —
  aucun n'y échappe ;
- l'iframe Google Maps est créée au clic seulement, avec un attribut `sandbox` restrictif ;
- les polices sont **auto-hébergées** : aucune requête ne part vers Google Fonts.

**Aucune CSP en `<meta>` n'a été ajoutée délibérément**, et le raisonnement a été vérifié plutôt
que supposé. Une CSP posée en meta ne couvre ni `frame-ancestors` ni le mode `report-only` : elle
donnerait une fausse impression de protection. Surtout, la faire passer imposerait
`script-src 'unsafe-inline'` ou une liste de hachages — et **106 images du site portent un attribut
`onerror` de repli** (28 sur l'accueil seul) vers un `.jpg` ou un `.png`. Une CSP qui interdit les
gestionnaires en ligne les rendrait tous inertes, en silence : le jour où un `.webp` ne serait pas
servi, la page afficherait un trou au lieu de son image de secours.

**La seule vraie solution** est de placer un proxy devant le site (Cloudflare en offre gratuite) et
d'y définir les en-têtes. C'est un changement d'infrastructure : il n'a pas été engagé sans validation.
Domaines à autoriser le jour où une CSP sera écrite, relevés dans le code et non devinés :
`www.googletagmanager.com` (mesure d'audience, après consentement), `api.web3forms.com`
(formulaire), `www.google.com` et `maps.google.com` (carte, au clic), `*.yapla.com` (adhésion),
`wa.me` (WhatsApp). **Ni Google Fonts ni Plausible** : les polices sont auto-hébergées et Plausible
a été remplacé par GA4.

**Ce qui ne dépend pas de la plateforme, et reste à faire chez le registrar** : le domaine n'a
ni enregistrement **DMARC** ni enregistrement **CAA**. Le premier laisse un tiers usurper
l'adresse d'expédition `@mbc974.com` sans qu'aucun serveur ne le refuse ; le second laisse
n'importe quelle autorité de certification émettre un certificat pour le domaine. Les deux
s'ajoutent en une ligne dans la zone DNS, et aucun des deux ne peut être posé depuis ce dépôt.

---

## 6. Accessibilité — règles à ne pas casser

- **Contraste** : tout texte doit atteindre 4,5:1 (3:1 au-delà de 24 px, ou 18,7 px en gras).
  Le vert « Adhésion gratuite » a été assombri pour cette raison (3,79 → 5,00:1).
  Le texte sur fond orange est **quasi-noir** (`#190f04`), jamais blanc : c'est ce qui le rend lisible.
- **`inert`** : la lightbox porte `inert` + `aria-hidden` quand elle est fermée, retirés à l'ouverture.
  Ne jamais séparer les deux.
- **Sélecteur d'âge** : les 6 panneaux sont dans le HTML. Le script *retire* `hidden`, il ne l'ajoute pas —
  sans JavaScript, le premier panneau reste ouvert et les liens restent atteignables.
- **`prefers-reduced-motion`** : un bloc dédié désactive reveal, parallaxe et animations continues.
  Toute nouvelle animation doit y être ajoutée.
- **Marquees** : les clones sont `aria-hidden="true"` et `display:none` — jamais focusables.

---

## 7. Tests avant publication

Il n'y a pas de CI. Les contrôles se font en local :

```bash
node --check script.js                 # syntaxe JS
python -c "s=open('style.css',encoding='utf-8').read(); print(s.count('{'), s.count('}'))"
python -c "import xml.dom.minidom; xml.dom.minidom.parse('sitemap.xml')"
python .claude/verifier-jsonld.py      # données structurées, les 25 pages
python .claude/build-creneaux.py --essai # les pages catégories disent-elles encore la vérité ?
python .claude/build-vignettes.py --essai # les crans responsives sont-ils tous là ?
python .claude/build-og-matchs.py --essai  # les 7 affiches de partage existent-elles ?
python .claude/build-effectif.py --essai   # les 9 joueurs sont-ils tous là ?
python .claude/verifier-classes.py     # classes HTML sans aucune règle CSS
python .claude/verifier-liens.py       # liens, ancres, ressources, pages orphelines
python .claude/build-sitemap.py --essai # le sitemap est-il encore à jour ?
python .claude/build-css.py --check    # style.min.css correspond-il à style.css ?
python .claude/bump-assets.py --check  # les ?v= des 25 pages sont-ils à jour ?
```

**Les deux derniers doivent sortir en 0 avant toute publication**, et c'est plus important qu'il
n'y paraît : le service worker sert désormais la CSS et le JS depuis son cache, ce qui n'est sûr
que parce que le `?v=` est un hachage du contenu. Un `?v=` périmé, et un visiteur garderait
indéfiniment l'ancienne feuille. `bump-assets.py` refuse de tourner si `style.min.css` ne
correspond plus à `style.css`, donc la seule façon de se tromper est de ne lancer ni l'un ni
l'autre.

`verifier-jsonld.py` doit sortir **0 erreur, 0 avertissement**. Il contrôle, hors ligne, ce
que Search Console reprocherait ensuite : JSON-LD qui parse, images et fichiers réellement
présents dans le dépôt, ancres `#match-…` qui existent vraiment dans la page, propriétés
recommandées par Google sur chaque `SportsEvent`, ids HTML non dupliqués, entité club unique.
Il ne remplace pas le Rich Results Test, qui seul fait foi.

`verifier-liens.py` doit sortir **0 lien cassé, 0 ancre absente, 0 page orpheline**. La dernière
colonne est la plus utile : une page qu'aucun lien du site n'atteint n'est vue ni par un visiteur
ni par un robot, même si elle figure dans le sitemap.

`verifier-classes.py` lit aussi, depuis le 08/09/2026, les chaînes `class="…"` des **générateurs**
de `.claude/`, et plus seulement le HTML publié. C'est ce qui manquait : un générateur écrit du
markup conditionnel, et `.mx-score` — le score d'une rencontre jouée — n'existe dans aucune page
tant que la ligue n'a rien publié. Il avait donc été compté mort et purgé de la feuille. Un jeton
à suffixe variable (`mx-score--%s`) est traité comme une **famille**, satisfaite dès qu'une règle
commence par ce préfixe.

Les scripts balaient `*.html`, `*/index.html` **et** `*/*/index.html`. Si une rubrique
descend un jour à trois niveaux, étendre les `glob` — sinon les scripts annonceront
« 0 erreur » sur des pages qu'ils n'ont pas ouvertes.

Il reste **trois classes sans règle**, connues et volontairement laissées : `.sponsor-pack--rookie`,
`.sponsor-pack--mvp` et `.sponsor-pack--allstar`, sur la page partenaires. Ce sont des crochets
sémantiques sans style propre — le rendu vient de `.pack--feat`. Les retirer serait une
modification de markup sans bénéfice ; les garder coûte trois lignes de rapport.

Puis, sur le serveur local, vérifier page par page : HTTP 200, un seul `<h1>`, JSON-LD qui parse,
aucun débordement horizontal en 320 / 375 / 768 / 1024 / 1440 / 1920 px, aucune erreur console.

---

## 8. Tâches impossibles depuis le dépôt

| Tâche | Pourquoi externe | Priorité |
|---|---|---|
| Soumettre le sitemap à Search Console | nécessite l'accès au compte | haute |
| Compléter Google Business Profile | plateforme externe | haute |
| Valider la page confidentialité | décision juridique du bureau | haute |
| Harmoniser les fiches FFBB sous « La Montagne Basket Club » | back-office FFBB | moyenne |
| Activer Plausible | création de compte payant | moyenne |
| En-têtes de sécurité via Cloudflare | changement d'infrastructure | moyenne |
| Citations locales / backlinks | relations extérieures | basse |

---
## 9. La signature manuscrite du hero

Les trois phrases écrites à la main sous le titre (« Ansanm nou lé pli for. », « La Montagne
en lèr. », « Nou lé ansanm. ») ne sont **pas du texte** : ce sont les contours des glyphes de
**Caveat 400** — l’instance par défaut de `.claude/fonts/caveat-variable.ttf` (Google Fonts,
SIL OFL 1.1 ; le 700 donnait un feutre, pas une plume, voir V153 et § 19), convertis en chemins
SVG une fois pour toutes et
posés en dur dans `index.html`, dans `<span class="hw" data-hw>`.

C'est ce qui permet d'animer le tracé sans embarquer de police manuscrite ni de bibliothèque :
le hero ne fait **aucune requête** de plus, et un changement de phrase n'en déclenche aucune.
Le style est dans la couche V138 de `style.css`, la rotation en fin de `script.js`.

### Changer les phrases (ou la police)

1. Lancer le serveur local (§ 2), puis ouvrir <http://localhost:8010/.claude/hw-signature.html>.
2. Modifier `PHRASES` (et au besoin `POLICE`) en haut du script de cette page.
3. Recharger. **Vérifier que le bandeau d'état est au vert** : il relit chaque contour tel que
   le navigateur le comprend et signale tout chemin refusé ou déformé. Un séparateur mal placé
   dans un `d` suffit à faire disparaître une lettre — c'est précisément ce que ce contrôle
   attrape.
4. Copier le contenu du champ du bas et remplacer les trois `<svg class="hw__f" …>` d'`index.html`,
   **en gardant** le `<span class="sr-only">` qui les précède : c'est lui que lisent les lecteurs
   d'écran, il doit reprendre la phrase principale.
5. Passer le `?v=` (§ 1) et vérifier le hero à 360 / 390 / 430 px.

Une police manuscrite différente se dépose dans `.claude/fonts/` (source seule, jamais servie).
La choisir **monoline et pas trop grasse** : c'est ce qui rend le tracé crédible, le contour se
lisant alors comme un trait de plume.

### Points à ne pas casser

- **Le `viewBox` est commun aux trois phrases.** C'est lui qui garantit qu'elles se rendent à la
  même taille et qu'aucun changement ne décale le sous-titre, les boutons ou la hauteur du hero.
  Le générateur le calcule sur les trois : ne pas le réécrire à la main.
- **La première phrase porte `is-on` en dur.** Sans elle, un hero muet si le JS ne répond pas.
- **La taille se règle en pourcentage de la largeur** de la colonne (`.hw{width}`), jamais en
  hauteur : seule la largeur peut faire déborder une phrase.
- `prefers-reduced-motion` doit afficher la phrase encrée d'emblée, sans tracé.

---

*Passion · Respect · Solidarité · Engagement*


---

## 10. Ce qui a été retiré du site en attendant une décision

Deux visuels ont été **retirés de l'affichage** le 09/09/2026, parce qu'ils
contredisaient le reste du site. Leur markup est conservé en commentaire à
l'endroit exact où il vivait, avec la preuve du désaccord et la marche à suivre
pour les rétablir.

### L'affiche des créneaux — RÉTABLIE le 10/09/2026

**C'est réglé, et la cause l'est avec.** L'ancienne `assets/images/creneaux.avif`
contredisait le site sur trois points (Seniors/U18 du lundi à 20h30–22h00 au lieu
de 19h00–20h30 ; créneau du mercredi placé à Ruisseau Blanc alors qu'il est au
Gymnase ; une adresse `mbc974.re@gmail.com` qui n'existait nulle part ailleurs).
Elle avait été retirée du site le 08/09/2026.

Le vrai défaut n'était pas l'image : c'était qu'**une affiche dessinée à la main
est une seconde source de vérité**. Elle dérive dès qu'un horaire change, et rien
ne le signale.

`\.claude/affiche-creneaux.py` supprime la cause : l'affiche est **produite à
partir de `data/creneaux.json`**, le fichier qui alimente déjà le planning,
`/creneaux/` et les `openingHoursSpecification`. Elle ne peut plus diverger.

```bash
python .claude/affiche-creneaux.py     # après toute modif de data/creneaux.json
python .claude/build-creneaux.py       # la page reprend le nouveau nom de fichier
```

Le lien est publié sur **`/creneaux/`** — et non sur l'accueil, dont le planning
complet a été replié en `665b34b`. C'est un lien simple, pas une visionneuse :
`/creneaux/` n'a pas de `#lightbox`, et une affiche sert surtout à être partagée
ou imprimée.

Le nom du fichier porte une **empreinte de son contenu**
(`creneaux-2026-2027-<sha>.png`) : le service worker sert les images versionnées
par leur nom, donc une affiche corrigée qui garderait son nom continuerait d'être
servie dans son ancienne version — c'est-à-dire avec les mauvais horaires.
`build-creneaux.py` retrouve ce nom **par glob**, jamais en dur.

La charte (couleurs, polices, fond à deux halos) est **importée** de
`affiche-calendrier.py`. La recopier aurait recréé le même problème à l'échelle
du graphisme : deux affiches du même club qui divergent lentement.

### Le one-page partenaire (`sponsor-club-basket-reunion/`)

`assets/images/one-page-partenaire.jpg` contredit **le PDF qu'il résume**, et que
la page propose au téléchargement juste à côté :

| | Dossier PDF (source) | Image publiée |
|---|---|---|
| Licenciés | « **Objectif** +60 licenciés » | « **+60 LICENCIÉS** et en croissance » |
| Baby Basket | 3-6 ans | 4-6 ans |

Le premier écart transforme un objectif en chiffre acquis, dans un document
commercial remis à une entreprise. C'est exactement ce que la page s'interdit
soixante lignes plus haut à propos des chiffres Search Console.

Le **lien vers le PDF est resté** : c'est la source, et elle est juste. La
récompense de fidélité (−10 % / −20 %), qui n'existait que dans le PDF et dans
cette image, est désormais écrite en toutes lettres sur la page.

### Une divergence à trancher par le bureau

Le dossier PDF annonce une catégorie **« U11 (9-10 ans) »** que le site ne
connaît pas : le site, `data/creneaux.json` et les formules Yapla parlent
d'**« École de Basket (7-10 ans) »**. L'un des deux doit être corrigé. Ce dépôt
ne peut pas en décider : il ne sait pas laquelle des deux structures le club
engage réellement auprès de la FFBB.


---

## 11. L'effectif : ce qu'on ne change pas sans refaire l'affiche

`data/effectif.json` porte les neuf joueurs, **extraits du markup, jamais
ressaisis**. Deux points à connaître avant d'y toucher :

- Les affiches de `assets/joueurs/` portent le nom **et le numéro gravés dans
  l'image**. Modifier un numéro dans le JSON sans refaire l'affiche ferait dire
  deux choses différentes à la même carte.
- **Hakim Derras est passé au n° 94** le 10/09/2026, sur décision du bureau —
  il partageait le 10 avec Guillaume Moine, qui le conserve. ⚠️ **Son affiche
  n'a pas été refaite** : `assets/joueurs/mbc-senior-hakim-derras-*.jpg` porte
  encore « #10 » gravé à trois endroits (maillot, nom, grand chiffre). La
  légende dit donc 94 et l'image dit 10, sur l'accueil comme sur `/effectif/`.
  Le bureau a validé cet écart en connaissance de cause, le temps qu'un
  nouveau visuel existe.

  Le texte alternatif de cette affiche a été **neutralisé** : il ne cite plus
  de numéro. Un `alt` décrit l'image — lui faire dire 94 aurait été faux, lui
  laisser 10 aurait fait entendre à un lecteur d'écran l'inverse de ce que lit
  un voyant. Le nom et le poste suffisent.

  `data/effectif.json` porte une clé `_affiche_a_refaire` sur ce joueur. **La
  retirer le jour où la nouvelle affiche est déposée**, en même temps que les
  crans responsive (`build-vignettes.py` ne traite pas les affiches joueurs :
  elles sont livrées déjà déclinées).

`squad--4` sur la seconde rangée n'est pas décoratif : `.squad` est un
accordéon dont les deux rangées doivent avoir la **même somme de `flex-grow`**
(5,02), sinon la carte ouverte n'a pas la même largeur d'une rangée à l'autre
et `--fy` vise un cadre qui n'existe pas. Le générateur le pose tout seul dès
qu'un groupe compte quatre joueurs.

Le JSON-LD `SportsTeam` de `/effectif/` ne déclare **pas** d'entraîneur : le
site présente Fred comme « Coach principal » et Luigi comme « Coach des
jeunes », mais nulle part qui entraîne l'équipe seniors. À confirmer par le
bureau avant de l'ajouter.

---

## 12. Le design system : couleurs, texte, espacements

Trois chantiers successifs ont donné un nom aux valeurs qui se répétaient dans
`style.css`. Chacun a son **instrument de mesure** (qui n'écrit rien) et son
**migrateur** (qui accepte `--essai`) :

| Sujet | Inventaire | Migration |
|---|---|---|
| Couleurs | `inventaire-couleurs.py` | `migrer-couleurs.py canaux` |
| Typographie | `inventaire-typo.py` | `migrer-typo.py tokens \| <palier>…` |
| Espacements | `inventaire-espacements.py` | `migrer-espacements.py unites \| tokens` |

### La règle qui les gouverne tous

**Le rendu d'abord, le nombre de valeurs ensuite.** Une consolidation ne se
décide pas sur la ressemblance de deux valeurs, mais sur ce qu'elles font. La
phase couleurs l'a appris à ses dépens : 250 occurrences de navies
« indiscernables » au calcul CIE76 se sont révélées être les paliers voulus
d'un dégradé. Elles n'ont pas été fusionnées.

### Ce que chaque phase s'est autorisé

- **Couleurs** — les canaux (`rgb(var(--orange-vif-rgb) / .42)`) : iso-visuel
  au bit près. Aucune teinte fusionnée.
- **Texte** — sept paliers `--text-*`, tirés des masses d'usage mesurées dans
  le navigateur. Une taille ne migre que si son écart au palier reste **sous
  4 %**. La bande display (scores, numéros, hero, mot de fond) est hors échelle.
- **Espacements** — **aucun déplacement, pas même de 0,1 px.** C'est la seule
  des trois phases à s'interdire toute tolérance, et la mesure l'explique :
  aucune grille raisonnable n'absorbe plus de 66 % des espacements sous 4 %
  d'écart, il faut tolérer 20 % pour en absorber 89 %. Or un `gap` se **répète**
  entre N éléments — 3 px d'écart six fois de suite déplacent une carte de
  18 px. On a donc seulement uniformisé l'écriture et nommé les valeurs.

### Les tokens d'espacement

Neuf valeurs dominantes, numérotées en **centièmes de rem** :

```
--sp-50 .5rem   --sp-80  .8rem    --sp-100 1rem
--sp-60 .6rem   --sp-85  .85rem   --sp-110 1.1rem
--sp-70 .7rem   --sp-90  .9rem    --sp-140 1.4rem
```

Pourquoi pas `--sp-16` comme partout ailleurs : le vocabulaire du MBC ne tombe
pas sur des multiples de 4 px. `.7rem` vaut 11,2 px, et `--sp-14` désignerait à
la fois `.85rem` (13,6 px) et `.9rem` (14,4 px). Un nom en pixels serait faux
ou en collision.

Au-dessus d'eux, **`--sp-sec` / `--sp-blk` / `--sp-gap` sont des tokens
d'intention**, pas de valeur : ils portent le rythme vertical des sections et
restent en `clamp()`. Ils ne sont pas renumérotés.

### Ce qui reste volontairement hors système

Le **hero** et la **galerie** sont exclus des trois phases : leur respiration
et leur géométrie leur sont propres. Les valeurs `clamp()`/`calc()` ne sont pas
touchées non plus — c'est le rythme fluide voulu, pas une accumulation.

### Prouver qu'on n'a rien cassé

Le seul contrôle qui vaut est l'**empreinte des styles calculés** avant/après,
sur plusieurs pages et deux largeurs. Deux pièges vécus :

1. `html{scroll-behavior:smooth}` fait que `scrollTo(0,0)` **n'a pas encore eu
   lieu** quand on mesure : les `getBoundingClientRect()` sortent décalés de
   toute la hauteur de défilement. Forcer `scrollBehavior='auto'` et attendre.
2. Un écart n'est une régression qu'après un **témoin à code identique**. En
   rechargeant la *même* feuille, l'animation du hero et l'arrondi
   sous-pixel produisent à eux seuls ~94 écarts de géométrie. La comparaison
   réelle en produisait 2. Sans le témoin, on aurait « trouvé » 93 régressions
   qui n'existent pas.

### Rayons et ombres — le système existait déjà

Contrairement aux trois autres sujets, celui-ci n'a pas eu besoin d'être créé :
`--r-sm/md/lg/pill` et `--e1/e2/e3`, `--glow-o/--glow-b`, `--bevel` étaient là.

**Le piège, et il est sérieux : ces tokens ont DEUX valeurs.** Le bloc V79
les redéfinit sur `main > .section, .site-footer` :

| | hors sections | dans les sections et le pied de page |
|---|---|---|
| `--r-sm` | 14px | **10px** |
| `--r-md` | 18px | **12px** |
| `--r-lg` | 24px | **16px** |
| `--e2` | `0 8px 24px` | `0 4px 12px` |

C'est volontaire — le scope exclut le hero, qui est `main > .hero`. La
conséquence : **remplacer un `14px` littéral par `var(--r-sm)` le fait passer à
10px si la règle est dans une section.** Toute tokenisation de rayon doit donc
être décidée règle par règle, en résolvant le token à l'endroit où il
s'applique. Ce n'est pas iso-visuel par construction, contrairement aux
espacements.

`--r-round:50%` fait exception : il n'est pas redéfini par V79 et vaut 50 %
partout. Il existe séparément de `--r-pill` parce que ce sont deux formes
différentes — `999px` sur un rectangle fait un **stade**, `50%` sur un carré
fait un **cercle**, et sur un rectangle une **ellipse**.

**Les ombres ne sont pas tokenisables.** Mesuré élément par élément : sur 71
éléments ombrés de l'accueil, 8 seulement rendent exactement une valeur de
token. Les 77 compositions sont sur mesure. Les mettre en système reviendrait à
les changer, pas à les centraliser. Et les 8 règles à 3 ou 4 couches
(`.cat:hover`, `.sponsor-pack.pack--feat`, `.essentiel-card`, `.mx-crest--logo`,
`.p-pillar:hover`) sont des **compositions** — élévation + liseré + bevel — à ne
jamais découper en tokens indépendants.

### Une classe absente du markup n'est pas forcément morte

`verifier-classes.py` et les inventaires lisent les `class="…"` du HTML et des
générateurs. Ils ne lisent **pas** le JavaScript. Or `script.js` et
`consent.js` créent des éléments à l'exécution :

```
consent.js:51    b.className = 'ccb'              le bandeau RGPD
script.js:178    toolbar.className = 'lightbox__toolbar'
```

Ces deux-là figuraient dans une liste de « règles mortes ». Les retirer aurait
cassé la visionneuse et le bandeau de consentement. **Avant de supprimer une
règle jugée morte, la confronter à `script.js` et `consent.js`** — et distinguer
une classe *créée* par le JS (vivante) d'une classe seulement *interrogée* par
lui (`querySelectorAll('.btn--roi')` : dormante, pas vivante).

`.btn--roi` (variante bleue) et le bloc `.sb` (« SCOREBOARD ») étaient dans ce
troisième cas. Ils ont été **retirés en entier le 2026-09-10**, sur décision —
et en bloc, jamais propriété par propriété : leur retirer leur seule ombre les
aurait dégradés sans les nettoyer. La ligne `querySelectorAll('.btn--primary,
.btn--roi')` de `script.js` a été nettoyée en même temps.

**Le piège du retrait : un sélecteur mort est rarement seul dans sa règle.**
Onze règles mélangeaient les deux vocabulaires —
`.sb__comp i, .sb__when i, .footer__place i, …` ou
`.h2, .hero__h1, .lp-title, .sb__name, .keyfig__v`. Supprimer la règle entière
aurait emporté le pied de page et les grands titres. `purger-blocs-dormants.py`
retire donc les **sélecteurs** morts de la liste et ne supprime le bloc que si
tous le sont. Contrôle systématique après purge : comparer la liste des
sélecteurs individuels avant/après (45 retirés, **0 vivant perdu**).

### Tokeniser un rayon : 13 règles sur 80, et pourquoi si peu

À cause des deux portées V79, on ne peut pas décider depuis le texte de la
feuille. La méthode qui marche est de demander au **navigateur** ce que le token
vaut là où la règle s'applique :

```js
document.querySelectorAll(rule.selectorText)          // les éléments touchés
getComputedStyle(el).getPropertyValue('--r-md')       // la valeur héritée là
```

Sur 12 pages : 80 règles portent un rayon littéral en px ; **47** ne
correspondent à aucun token là où elles s'appliquent (les tokeniser les
déplacerait) ; **20** ne touchent aucun élément sur les pages testées, donc
invérifiables ; **13** sont unanimes et ont migré. Zéro cas mixte.

Deux pièges rencontrés en écrivant ce contrôle :
- `if (r.cssRules)` est **vrai pour toute règle de style** depuis le support du
  nesting — chaque `CSSStyleRule` expose une `cssRules` vide mais truthy. Un
  `continue` derrière ce test saute silencieusement toutes les règles. Tester
  `r.cssRules && r.cssRules.length`.
- Le CSSOM n'est pas prêt immédiatement après `navigate` : une première lecture
  a rendu 93 règles là où la feuille en compte 2 176. Attendre, et **valider le
  compte** contre un comptage indépendant avant d'exploiter le résultat.

---

## 13. Les points de rupture — inventaire, et pourquoi on n'y touche pas

343 `@media`, 84 conditions, **53 largeurs distinctes**. Le chiffre fait peur ;
la mesure dit autre chose.

**Ce qui n'est pas un breakpoint** et ne le sera jamais : `prefers-reduced-motion`
(65), `hover` (13), `pointer` (7), `orientation` (3), les requêtes de hauteur (7).
Ce sont des capacités et des préférences — ni échelle, ni ordre, rien à
rationaliser.

**Douze largeurs servent à la fois en `min` et en `max`** (360, 560, 640, 680,
700, 720, 760, 820, 900, 980, 1000, 1080). À ces largeurs exactes, les deux jeux
de règles s'appliquent : c'est l'ordre du fichier qui tranche, pas l'intention.
En face, **18 paires sont correctement formées** (`max:N-1` / `min:N`) et il n'y
a **aucun trou**.

**Mais ce chevauchement ne produit aucun défaut.** Vérifié en résolvant chaque
règle en éléments réels : un seul de ces douze points génère des collisions —
900 px, quatre propriétés sur `.hero` et `.hero__scroll`. Puis, en comparant les
propriétés discrètes de 1 719 éléments à 899, 900 et 901 px :

```
bascule entre 899 et 900 :  5 éléments
bascule entre 900 et 901 :  2 éléments
VRAIS HYBRIDES           :  0
```

Aucun élément ne se trouve, à 900 px, dans un état qu'il n'occupe ni à 899 ni à
901. Le découpage est ambigu à l'écriture, jamais à l'affichage.

**Conclusion : pas de rationalisation.** Déplacer une de ces bornes changerait
les règles appliquées à une largeur précise, sans aucun défaut à corriger. C'est
exactement ce que la règle du dépôt interdit : le rendu passe avant la pureté du
CSS. Le vocabulaire de 53 largeurs est documenté ; il n'est pas réduit.

Attention en mesurant : `clientWidth` **exclut** la barre de défilement alors que
les media queries l'**incluent** — à un viewport émulé de 900 px, `clientWidth`
lit 884. Se fier à `matchMedia('(max-width:900px)')`, qui fait autorité.

## 14. Vérifier un changement de CSS : le protocole qui marche

Échanger la seule feuille sur un DOM déjà chargé, plutôt que recharger la page :
même DOM, même état JS, aucun rotateur ni animation pour polluer la comparaison.

```js
link.setAttribute('href', '/_avant.css?t=' + Date.now())   // ← le cache-buster
```

**Quatre pièges, tous rencontrés :**

1. **Le cache.** Sans `?t=`, le navigateur ressert `/_avant.css` d'un essai
   précédent — la comparaison porte alors sur un fichier périmé et affiche des
   écarts qui n'existent plus. Toujours vérifier au passage le nombre d'octets
   réellement chargés.
2. **Le témoin.** Un écart n'est une régression qu'après une comparaison à
   **code identique**. Recharger la *même* feuille produit à lui seul 1 à 94
   écarts de géométrie (animation du hero, arrondi sous-pixel). Sans témoin, on
   « trouve » des régressions imaginaires.
3. **`scroll-behavior:smooth`** fait que `scrollTo(0,0)` n'a pas encore eu lieu
   au moment de la mesure : tous les `getBoundingClientRect()` sortent décalés
   de la hauteur de défilement. Forcer `scrollBehavior='auto'` et attendre.
4. **Les propriétés résolues.** `gridTemplateColumns` rend des largeurs en
   pixels qui varient continûment avec le viewport : les comparer directement
   fait passer 64 éléments pour des « hybrides ». Ne comparer que le **nombre**
   de colonnes.

Contrôle complémentaire après toute purge : comparer la liste des **sélecteurs
individuels** avant/après. Le bon résultat est « N retirés, 0 vivant perdu ».

---

## 15. Release candidate 2026/2027 — l'état figé, et la règle qui suit

**Tag `rc-2026-2027`** (annoté, poussé sur `origin`), posé sur `1e0f98e` le
10/09/2026. Il marque la fin du chantier technique : couleurs, typographie,
espacements, rayons, ombres, points de rupture et purge CSS sont stabilisés et
vérifiés en production sur les 25 URL du sitemap.

### La règle à partir d'ici

> Toute modification doit répondre à un **besoin concret** : une donnée, un
> match, du contenu, un bug réel, une mesure Search Console ou analytics, ou un
> retour d'utilisateur.

Pas de refactor pour faire baisser un compteur CSS. Trois sujets sont
explicitement **clos sans suite**, faute de défaut constaté :

| Sujet | Pourquoi on n'y touche pas |
|---|---|
| Les 53 largeurs de breakpoint | 12 se chevauchent, mais **0 hybride réel** mesuré sur 1 719 éléments à 899/900/901 px. Ambigu à l'écriture, jamais à l'affichage. |
| Les 47 rayons littéraux restants | Le mécanisme V79 à deux portées les rend non tokenisables **sans déplacement**. 20 autres sont invérifiables faute d'élément sur les pages testées. |
| Les 2 ombres quasi-identiques | `.nx__second` α .5 vs `.hero__second` α .55 ; `.lightbox__viewport` α .72 vs `.lightbox img` α .70. Aligner déplacerait vraiment une valeur, pour un écart que personne ne voit. |

Si l'un de ces sujets revient un jour, ce sera parce qu'un défaut aura été
**constaté**, pas parce qu'un compteur est élevé.

### Les cinq décisions — tranchées le 10/09/2026

Le bureau a répondu. Quatre points sont clos, un reste ouvert.

| # | Décision | Réponse du club | État dans le dépôt |
|---|---|---|---|
| 1 | Horaire Seniors du lundi | **19h00-20h30** confirmé. Et le mercredi passe à **20h30-22h00** pour Seniors + U18 au Gymnase | `data/creneaux.json` à jour ; affiche refaite depuis la donnée et republiée sur `/creneaux/` (§ 10) |
| 2 | Adresse e-mail | **`contact@mbc974.com`** | ✅ aucune modification : c'était **déjà** la seule adresse du site (39 occurrences en HTML, 5 en JS). Les deux autres n'existaient que dans ce document |
| 3 | U11 (9-10 ans) ou École de Basket (7-10 ans) | **toujours ouverte** | le site, `data/creneaux.json` et Yapla restent alignés sur École de Basket |
| 4 | Le n° 10 partagé | **Derras passe au 94**, Moine garde le 10 | `data/effectif.json` à jour ; ⚠️ affiche non refaite, voir § 11 |
| 5 | Entraîneur des Seniors | **Frédéric Sornom** — le « Fred » de la carte staff | `coach` renseigné dans le `SportsTeam` de `/effectif/` |

**Le mercredi à 22h00 concerne aussi les U18 (15-17 ans)**, et cet horaire est
public. C'est un choix du club, pris explicitement : la question a été posée
avec ses trois réponses possibles avant d'écrire quoi que ce soit.

**Il reste donc une seule décision ouverte**, la n° 3. La trancher demande de
savoir laquelle des deux structures le club engage réellement auprès de la
FFBB — le dépôt ne peut pas le déduire.

---

## 16. Passe de direction artistique (10/09/2026) — ce qu'il faut savoir

### Le premier écran se calcule par soustraction

`.hero` portait **quatorze** déclarations `min-height` concurrentes, la dernière
gagnant à `clamp(700px,90svh,880px)`. Une fraction de la fenêtre ignore ce qui
vient après : à 892 px de haut, le bas des trois preuves tombait à **1 318 px**.

La hauteur du hero vaut désormais `calc(100svh - 410px)` — la fenêtre **moins**
ce que le bandeau match (191), la gouttière (46) et les preuves (154) occupent.
Le premier écran tient donc à toutes les hauteurs, pas à une seule.

| résolution | dépassement |
|---|---|
| 1366 × 768 | 0 |
| 1440 × 900 | −19 |
| 1717 × 892 | −19 |
| 1920 × 1080 | −6 |

**Si un bloc du premier écran change de hauteur, c'est la constante 410 qu'il
faut reprendre** — elle est commentée dans la couche V153.

### La galerie : le `sizes` doit décrire l'état ZOOMÉ

Chaque tuile affiche une boîte de `--gw` puis subit `scale(--gs)`. Sa largeur
réelle vaut donc `--gw × --gs`, soit **jusqu'à 240 vw**. Les tuiles déclaraient
le `sizes` de la mosaïque (24vw) : le navigateur chargeait un dérivé de 412 px
et l'étirait à 2 146.

Mesuré, à 1717 px et par état d'animation :

```
          avant           après
g-tall    ×5,0  ->  ×1,9  ×0,8   (p=0,25, la tuile couvre encore 12 % de l'écran)
g-shoot   ×5,2  ->  ×2,1  ×0,9
g-banner  ×3,7  ->  ×1,5  ×0,8
g-team    ×0,77 (jamais floue : c'est elle qui finit plein cadre)
```

**Nuance importante** : l'étirement *maximal* n'est pas ce qu'on voit — les
tuiles périphériques sortent du cadre en grandissant. Le flou se jouait entre
p = 0,2 et p = 0,5. Toute correction future se juge là, pas à p = 1.

`.claude/build-galerie.py` regénère les dérivés AVIF manquants et réécrit les
`sizes`. Coût : **+190 Ko** sur la galerie (553 → 744 Ko), en chargement
différé, sous la ligne de flottaison. Le LCP (le hero) n'est pas touché.

Les fichiers de base font 900×978, 900×1000, 1400×745, 760×951 : **on ne peut
pas faire mieux sans originaux plus définis.** Aucun sharpening CSS n'a été
posé pour masquer le résidu.

### Le cadre de la galerie

Pendant le zoom la scène est collée : le haut de la section reste à l'écran, et
avec lui son `::before` d'1 px et son `radial-gradient` orange — lus comme le
cadre d'une fenêtre. Ils sont neutralisés par `:has(.gzoom.is-on)`, avec
`!important` **parce que la règle d'origine l'est aussi**.

Ne pas donner de fond à `.gzoom__stage` : essayé, cela dessine une couture nette
là où la scène commence, c'est-à-dire un second cadre à la place du premier.

### Photographier ce site : Chrome headless, pas le panneau d'aperçu

Le panneau plafonne à 800 px de large et **ne peint pas** cette page en
profondeur. `.claude/` n'embarque pas l'outil, mais la méthode est :

```bash
chrome --headless=new --window-size=1717,892 --screenshot=x.png <url>
```

Et il faut une **copie jetable** de la page (jamais `index.html` retouché) dans
laquelle sont posés : les `.reveal`, les `<details>`, le retrait du bandeau
RGPD, l'état final de la signature manuscrite, la valeur d'arrivée du compteur.

Quatre pièges rencontrés, tous coûteux :
1. **Allonger `--virtual-time-budget` est une fausse bonne idée** : le temps
   accéléré fait tourner le rotateur de signature plusieurs fois (les trois
   phrases se superposaient) et pousse le compteur au-delà de sa cible — il
   affichait « −68 € ». On supprime le temps (aucune animation) au lieu de
   l'allonger.
2. Le compteur : retirer `data-count` donne « NAN € », script.js lisant
   l'attribut. Il faut **remplacer le nœud par un clone** sans attribut.
3. `scroll-behavior:smooth` + temps virtuel = un défilement qui n'arrive jamais.
4. Headless ne défile pas avant de photographier. Le seul mode fiable est
   d'**isoler la section** (masquer tout le reste), pas de scroller.

### Les logos partenaires

Trois des cinq portaient un **fond blanc intégré** — mesure : 87 % (oxysom),
80 % (saint-françois), plus un carré arrondi autour du disque des Agitateurs.
Les coins étant transparents, un contrôle rapide ne le voyait pas : c'est
l'intérieur qu'il faut sonder.

`.claude/detourer-sponsors.py` les détache par **remplissage depuis les bords**,
jamais par un « blanc → transparent » global qui trouerait les blancs
intérieurs du logo. Il refuse d'écrire s'il retire plus de 92 % des pixels
opaques.

**La plaque claire reste** : mesure de la luminance des logos, `agitateurs-midi`
est à 69 % de pixels sombres et `cpa-paysage` à 61 % — sur fond nuit, deux
partenaires payants disparaîtraient. Et on ne repeint pas le logo de quelqu'un
d'autre.

---

## 17. Passe « premium & épuré » (10/09/2026) — six défauts, et l'outil qui mentait

Six points relevés à l'écran par le président. Ce qui suit dit ce qui a changé,
et surtout **ce qu'il ne faut pas défaire**.

### 17.1 Le bandeau « prochain match » : trois zones, un seul axe

La grille nommait **trois** rangées (`"eyebrow actions" "titre actions"
"meta actions"`) pour un bloc qui en contient **quatre** : le compte à rebours
n'avait aucun `grid-area` et se plaçait seul dans une quatrième rangée
implicite, que la colonne d'actions ne couvrait pas.

Mesure à 1717 × 892, avant :

| bloc            | haut | bas | centre |
|-----------------|------|-----|--------|
| colonne gauche  | 499  | 656 | **578** |
| bloc d'actions  | 524  | 578 | **551** |

27 px d'écart : c'est le décentrage visible de « Voir le match » et
« Itinéraire ». Et le compte à rebours, seul sur sa ligne, laissait une ligne
orpheline en bas à gauche pendant qu'un vide de 330 px s'ouvrait au centre.

**V161** passe la grille à **trois colonnes** — identité / compte à rebours /
actions — toutes couvrant les mêmes rangées. Après : les deux centres valent
574. Sous 820 px, tout s'empile dans l'ordre eyebrow / titre / meta / compte à
rebours / actions.

⚠️ Le point médian « · » entre les groupes du décompte a été **retiré du
markup** (`script.js`), pas masqué : « jour », « h » et « min » séparent déjà.
La règle `.nx__cd-sep` est partie avec lui.

### 17.2 La signature manuscrite ne fait plus de pâtés

Voir aussi § 9. Le tracé de plume refermait les contre-formes du **e** et du
**o** en Caveat 400. **V160** anime `stroke-opacity: 1 → 0` après l'encrage :
la plume reste un outil de tracé, l'encre seule subsiste. `prefers-reduced-motion`
pose directement `stroke-opacity:0`.

### 17.3 La catégorie choisie prend la place disponible

**V163** : `.age__cat` devient une grille — libellé au-dessus, **titre à
gauche** (`clamp(2.2rem, 5vw, 3.9rem)`), **années de naissance à droite** en
condensé orange. Le panneau passe à `64rem`. Sous 640 px, les années repassent
sous le titre.

**V167** : les trois faits (Créneau / Lieu / Formule) se présentent pareil à
toutes les largeurs — libellé au-dessus, valeur en dessous. Avant, sous 700 px,
seule la valeur longue passait à la ligne : trois faits, deux présentations
(hauteurs mesurées 62 / 39 / 39).

### 17.4 Plus aucune image de synthèse sur le site

`assets/images/joueuse-action.*` et **tout** `assets/categories/` (48 fichiers)
sont supprimés du dépôt. Trois pages les servaient encore :

| page | remplacée par |
|------|---------------|
| accueil, carte « Basket loisirs » | plus d'image : la carte passe en `.cat--typo` comme les six autres |
| `basket-adulte-loisirs-saint-denis/` | `assets/galerie/equipe-cohesion` |
| `baby-basket-la-reunion/` | `assets/galerie/initiation-basket-enfants` |
| `basket-enfant-saint-denis/` | `assets/galerie/ecole-basket-enfant-mbc-saint-denis` |

La carte « Seniors compétition » gardait `.cat--photo` avec un `<figure>` vide :
elle réservait 132 à 180 px pour une photo absente. Passée en `.cat--typo`.

**Règle** : chaque `alt` réutilisé vient d'une description déjà publiée pour
cette photo ailleurs sur le site. On ne réécrit pas ce qu'une photo montre.

Restent à vérifier un jour : `assets/maillots/maillot-*.jpg` sont des **rendus
produit** (maquettes de maillot), pas des photos — ni des personnes générées.
Laissés en place.

### 17.5 Le ruban de saison — la section « matchs » n'est plus vide

`.claude/build-ruban-saison.py`, entre les marqueurs `SAISON-RUBAN:DEBUT/FIN`
d'`index.html`. Source : `data/matchs.json`, et rien d'autre.

Sept vignettes (journée, écusson, nom court, date, camp), une par rencontre.
Le détail — horaire, lieu, postes bénévoles — reste dans l'accordéon, dont le
libellé devient « Voir le détail de chaque rencontre » : il n'y avait pas de
raison qu'il répète le titre de la section.

Coût : environ 150 px. Tout déplier en coûterait 2 600.

**Les états `is-next` / `is-past` ne sont PAS générés** : le site est statique,
la réponse dépend de l'heure d'ouverture de la page. `script.js` les pose, avec
la fonction `situer()` — **la même** que pour les lignes de l'accordéon, sur les
mêmes attributs `data-debut` / `data-fin`. Ne pas en faire une seconde copie.

Vérifié en reculant J1–J3 d'un an dans une copie jetable : les trois s'éteignent
et J4 prend l'anneau orange.

### 17.6 Les traits qui ne séparaient rien

Recensement fait au navigateur : toute bordure visible de plus de 90 px, plus
tout pseudo-élément servant de filet. Retirés :

1. **Traits verticaux du bandeau de chiffres** (`.keyfig__i + .keyfig__i::before`).
   Les trois blocs portent déjà un filet horizontal de 2 px qui, lui, **sert** :
   il change de couleur au survol et au focus.
2. **Soulignés du sélecteur d'âge** — et ils étaient dissymétriques,
   `:last-child` annulant le troisième.
3. **Bordure des bandes alternées** (`.section.categories/.matchs/.contact`).
   Mesure au pixel à la jonction chiffres-clés / catégories :
   `y=183 rgb(27,36,51)` pleine largeur, `y=184 rgb(38,46,63)` au centre —
   **deux traits à un pixel d'écart**. On garde le filet dégradé (il s'arrête à
   la largeur du contenu et s'efface aux bouts), on retire la bordure.
4. **Pied de page** : `.footer__ident` avait un bord haut tombant exactement sur
   le bord bas de `.footer__top` ; `.footer-legal` redisait 24 px plus bas, sur
   un cinquième de la largeur, la coupe que `.footer__seo` venait de marquer.

**Ce qui reste, et pourquoi** : les cadres de cartes délimitent une surface ; les
bordures de champs de formulaire sont l'affordance ; les filets de section
marquent un chapitre ; les 2 px du bandeau de chiffres portent un état. Un trait
qui informe reste.

### 17.7 L'outil de capture mentait sur la largeur — à lire avant toute mesure

**Chrome headless clampe le viewport à 500 px de large.** Vérifié en écrivant
`innerWidth` dans le DOM et en le relisant par `--dump-dom` :

```
--window-size=390,700   ->  innerWidth réel : 500
--window-size=375,700   ->  innerWidth réel : 500
--window-size=1717,700  ->  innerWidth réel : 1701
```

`--headless=old` fait pareil. La **hauteur**, elle, est respectée.

Conséquence : **toute capture « mobile » de ce dépôt faite par `shot.py` montre
une page mise en page pour 500 px, recadrée à 390** — d'où des textes coupés et
un bouton qui déborde, alors que le vrai navigateur à 390 px ne déborde pas
(`scrollWidth == innerWidth`, mesuré dans le panneau).

La parade est `cadre.py` : un `<iframe>` à la taille voulue. Le viewport d'une
iframe vaut exactement sa taille CSS. On photographie une fenêtre large, on
recadre sur l'iframe. Contrôle : bouton mesuré 39 → 740 en dpr2, soit
19,5 → 370 en CSS — identique au navigateur (20 → 371).

Deux autres pièges du même outillage, corrigés :

- le mode `?only=` remettait `body{padding:0}` : sur mobile c'est la gouttière,
  donc l'isolement **élargissait** le contenu et fabriquait des débordements
  imaginaires. Un instrument qui déplace ce qu'il mesure ne sert à rien ;
- deux tirs de même largeur partageaient le profil Chrome, donc le cache : le
  second rechargeait le `_cadre.html` du premier et photographiait la mauvaise
  section. Le gabarit est désormais horodaté.

Et le classique : le script d'injection vit dans `<head>`, donc au premier appel
synchrone `document.body` est `null`. Une ligne qui le touche sans garde lève une
exception — et décroche du même coup l'enregistrement de tous les handlers qui
suivent.

---

## 18. Le paiement en trois fois — et trois règles qui en sortent

### 18.1 Les quatre faits, décidés par le bureau le 10/09/2026

Le dépôt ne contenait **aucune** mention d'un paiement échelonné, et affirmait
même l'inverse (« Un seul règlement, au club, au moment de l'inscription »).
Ces quatre points ont été tranchés par le président ; ils ne se déduisent de
rien et ne doivent pas être réinventés :

| Question | Réponse |
|---|---|
| Où se choisit le 3× ? | **Dans le tunnel Yapla**, au moment de régler. Pas d'arrangement hors ligne, donc le parcours d'inscription reste le même pour tout le monde. |
| Découpage exact | **31,67 € + 31,67 € + 31,66 €** = 95,00 €. Pas 3 × 31,67 (qui ferait 95,01). |
| Licence FFBB | Elle part **dès la première échéance**. Le joueur est couvert immédiatement. |
| Périmètre | **Toutes les formules joueurs.** |

Ce qui reste inconnu et n'est donc **écrit nulle part** : les dates des 2ᵉ et
3ᵉ échéances. Elles sont nommées par leur rang, jamais datées. Seule la
première est située — « à l'inscription » — parce que c'est vrai par
construction.

### 18.2 Où l'information vit, et où elle est seulement citée

Source canonique : `adhesion.html#paiement`, un `div.adh-block` frère de
`#tarif`. Tout le reste y renvoie plutôt que de recopier des montants — au
prochain changement de tarif, il y a **un** endroit à corriger, pas onze.

Les montants apparaissent à trois endroits, tous sur `adhesion.html` :
le bloc `#paiement`, la FAQ visible, et son jumeau JSON-LD `FAQPage`.
**Les deux versions de la FAQ doivent rester strictement synchrones.**

Deux phrases disaient le contraire et ont été reformulées — les rouvrir sans
y penser recréerait la contradiction :
- `#tarif`, le chapeau : disait « Un seul règlement, au club, au moment de
  l'inscription ». Son propos réel était « pas de second interlocuteur », pas
  « un seul versement ». Reformulé en ce sens.
- `#parcours`, étape 1 : « Vous vous inscrivez et réglez 95 € ». Précise
  désormais « en une fois ou en trois fois sans frais », et dit que la suite
  est identique dans les deux cas.

Sur l'accueil, seul le chiffre-clé le mentionne (« Un seul tarif, ou 3 fois
sans frais ») et renvoie à `#tarif`. Aucun montant d'échéance sur l'accueil.

**Le JSON-LD `makesOffer` de l'accueil n'a PAS été touché** et ne doit pas
l'être : schema.org n'a pas de propriété pour un paiement fractionné, et
`price` doit rester « 95 ». Ne pas confondre avec les `offers` à `price:"0"`
des fiches match, qui sont générés et concernent l'entrée gratuite.

### 18.3 Le composant `.pay` — ce qu'il fait et ce qu'il ne calcule pas

Adaptation en HTML/CSS/JS natif d'un composant React « Pricing » transmis par
le président (bascule mensuel/annuel, prix animé). Le site est statique et le
reste : ce qui a été repris est le **geste**, pas le code — une bascule à deux
positions, et un chiffre qui change sous les yeux.

⚠️ **Les montants ne sont pas calculés par le script.** 95 ÷ 3 = 31,666… : le
découpage réel est une décision du bureau, pas une division. Il est écrit dans
le HTML ; `script.js` ne fait que le montrer. On ne veut pas qu'un arrondi de
JavaScript décide d'un engagement de paiement.

Le compteur `data-count` de l'accueil n'est pas réutilisable ici : il va de 0
vers une cible entière, une seule fois, au défilement. Celui-ci fait des
allers-retours entre deux valeurs décimales, à la demande.

Deux pièges de cascade rencontrés en l'écrivant, tous deux réglés par la
spécificité et jamais par `!important` :
- `.section p` (0,1,1) impose `--txt-soft` : **toute** règle de couleur portant
  sur un `<p>` du bloc doit valoir au moins (0,2,0), d'où le préfixe `.pay`.
  Le prix sortait gris.
- En `--ff-display` (Anton), le signe `×` (U+00D7) **n'existe pas** et tombe
  dans la police de repli : « 3 » sortait grand et « × » minuscule à côté. Le
  multiplicateur est donc en `--ff-cond`.

### 18.4 L'invariant des cartes catégories

`.cat--typo` = **pas d'image**. `.cat--photo` = **une image**. Jamais l'inverse,
jamais les deux.

La passe V154 avait converti les huit cartes en `.cat--typo` parce que six
portaient des images de synthèse — mais la carte « Dirigeant / bénévole » a une
vraie photo. `.cat--typo` recycle `.cat__photo` en bandeau typographique
(`display:flex`, `position:static` sur le numéro) : l'image devenait un
troisième item de flex, et `.cat--wide > .cat__photo{grid-row:1/-1;height:100%}`
étirant la figure sur toute la hauteur, `align-items:center` projetait le « 08 »
et la pastille au milieu vertical de la carte, en plein texte.

### 18.5 Les liens de lieu ont une source unique

`data/creneaux.json`, clé `carte` de chaque lieu. Deux URL, une par lieu :

    gymnase   https://maps.app.goo.gl/KcTePvY47wzi6JMu9
    ruisseau  https://maps.app.goo.gl/2gHjGAH8hY4iMpT36

Ne pas les recopier à la main : `build-creneaux.py` les pose sur le planning de
l'accueil et sur `/creneaux/`. Le `https://maps.google.com/?cid=...` est autre
chose — c'est la **fiche Google Business Profile** du club, qui porte les avis
et sert de `hasMap` au JSON-LD ; ne pas l'uniformiser vers le lien court.

⚠️ Le bloc `<ul class="cal-lieux">` de l'accueil est encore écrit **à la main**
alors que son jumeau de `/creneaux/` est généré depuis `data/creneaux.json`.
Les deux disent la même chose aujourd'hui, rien ne le garantit demain. C'est
exactement le scénario qui avait produit deux URL divergentes pour Ruisseau
Blanc. À entourer d'un marqueur `<!-- creneaux:lieux -->` un jour.

### 18.6 Une modification faite sur github.com ne part PAS en ligne

Le commit `5c0d95a` (« Update style.css ») a corrigé le cadrage du hero entre
641 et 1000 px. Il a été fait **directement dans l'éditeur web de GitHub** —
donc sans lancer `build-css.py`.

Or c'est `style.min.css` qui est servi. Vérifié en production : quatre heures
après le commit, `https://mbc974.com/style.min.css` portait toujours l'ancienne
règle `clamp(600px,82svh,780px)`. **Le correctif était dans le dépôt sans être
sur le site.**

**Règle :** après tout commit qui touche `style.css` sans passer par la chaîne
locale, lancer `python .claude/build-css.py` puis `python .claude/bump-assets.py`
et republier. Le contrôle qui tranche en une seconde :

```bash
curl -s https://mbc974.com/style.min.css | grep -c "<un motif de la nouvelle règle>"
```

Zéro = la modification n'est pas en ligne.

---

## 19. La signature manuscrite : les « pâtés » avaient une autre cause (10/09/2026)

### Le symptôme, signalé deux fois

« On a les espaces vides qui sont remplis » : l'intérieur des **a, e, o, g, p**
de la phrase qui s'écrit sous le titre du hero était plein.

### Le premier diagnostic était faux — et sa vérification aussi

La couche V160 accusait le **trait** de la plume : laissé à la fin de
l'animation, il aurait épaissi chaque glyphe des deux côtés et bouché les
contre-formes. On l'a fait s'effacer après l'encrage. Ça n'a rien changé.

Deux erreurs, à ne pas refaire :

- **L'ordre de grandeur ne collait pas.** `stroke-width` vaut 3 unités du
  viewBox, rendu à l'échelle 0,2 : **0,6 px à l'écran**. Un trait de 0,6 px ne
  bouche rien. Il fallait mesurer avant d'accuser.
- **La vérification était circulaire.** L'outil de capture injectait
  `.hw__p{stroke-opacity:0 !important}` pour figer l'état final : il montrait
  donc le trait effacé *quelle que soit* la CSS livrée.

Le commentaire de V160 dans `style.css` a été corrigé en ce sens.

### La vraie cause

`.claude/hw-signature.html` découpe chaque phrase en contours — « tout ce qui
suit un M jusqu'au M suivant » — et écrivait **un `<path>` par contour**, pour
que la plume les trace un par un. Or l'intérieur d'un « a » est un contour à
part entière. Devenu un `<path>` autonome, il était **rempli pour son propre
compte** : le trou devenait une pastille pleine posée sur la lettre dès que
l'encre arrivait.

Mesuré au navigateur (`getBBox`) : 6 chemins entièrement contenus dans un
autre dans la phrase 1, 7 dans la phrase 2, 4 dans la phrase 3 — les 17
contre-formes du texte.

La preuve qui tranche : rendre la phrase **encre seule, trait coupé**. Les
lettres restaient bouchées : le trait était innocent.

### Le correctif, à deux niveaux

1. **Sur le HTML publié** : `python .claude/fusionner-contreformes.py`.
   Chaque contour entièrement contenu dans un autre **et tournant en sens
   inverse** (aire signée de signe opposé) est rattaché à sa lettre, dans le
   même attribut `d`. La règle `nonzero` en fait alors un trou. Un contour
   contenu qui tournerait dans le *même* sens serait un recouvrement à remplir :
   il est laissé tel quel (aucun des 17 n'était dans ce cas). 67 → 50 chemins.
   Idempotent : relancé, il ne trouve plus rien.
2. **Dans le générateur** : `rattacherContreFormes()` fait la même chose avant
   la sérialisation. Vérifié : sa sortie est **identique octet pour octet** au
   HTML corrigé (50 chemins, 30 366 octets).

Aucune autre valeur ne bouge : géométrie recopiée à l'identique, instants de
tracé (`--d`, `--t`) de la lettre conservés, même viewBox, même nombre de
phrases.

### Régénérer les phrases

Ouvrir `http://127.0.0.1:<port>/.claude/hw-signature.html` servi depuis la
racine du dépôt (la police est lue en `/.claude/fonts/caveat-variable.ttf`),
attendre « OK », copier le contenu du champ de sortie à la place des trois
`<svg class="hw__f">` d'`index.html`. `fusionner-contreformes.py --essai` doit
alors répondre « 0 contre-forme ».

### Vérifier un état final animé

Ni en forçant la propriété qu'on corrige, ni sur une capture : dans un vrai
navigateur, mener les animations à terme puis lire l'état calculé.

```js
document.querySelectorAll('.hw__f.is-on .hw__p')
  .forEach(p => p.getAnimations().forEach(a => a.finish()));
getComputedStyle(document.querySelector('.hw__f.is-on .hw__p')).fillOpacity
```

Les bancs de capture (`cadre.py`, `shot.py`) passent désormais
`--force-prefers-reduced-motion` : c'est la règle `prefers-reduced-motion` **du
site** qui pose l'état final, pas une surcharge de l'outil.

---

## 20. Le premier écran fait une page (10/09/2026)

### La demande

« Sur le hero, je veux simplement la photo, le CTA et la prochaine rencontre »,
et que ce premier écran fasse **une page entière à chaque résolution** —
téléphone, iPad, PC. Le bandeau « 95 € / dès 3 ans / 2 terrains » passe
dessous : il deviendra une section à cartes.

### Avant, mesuré

| | premier écran |
|---|---|
| téléphones 360 → 430 | **débordait** de 170 à 364 px |
| tablettes et ordinateurs | **s'arrêtait trop tôt** : 124 à 517 px de vide, occupés par le haut du bandeau de chiffres |

Cause : la hauteur du hero était une formule — V153,
`clamp(400px, calc(100svh - 410px), 780px) !important` — qui réservait 410 px
« pour la suite » sans connaître ni la taille réelle du bandeau, ni son
existence.

⚠️ **Au passage, V153 rendait inerte la règle tablette du commit `5c0d95a`**
(`clamp(500px,66vw,680px) !important` en 641–1000) : même `!important`, même
spécificité, mais plus bas dans le fichier **et sans media query**, donc
appliquée à toutes les largeurs. Mesuré : 768×1024 → hero 614 px =
1024 − 410. **Toute règle `!important` sans media query posée en fin de
fichier écrase les règles de palier écrites plus haut.**

### La règle qui remplace les formules (V171)

```html
<div class="ecran1">            <!-- ouvert juste avant <section class="hero"> -->
  <section class="hero">…</section>
  <!-- PROCHAIN-MATCH:DEBUT … -->  <section class="nx" id="nxBand">…</section>
  <!-- PROCHAIN-MATCH:FIN -->
</div>                           <!-- fermé juste après le marqueur FIN -->
```

```css
.ecran1{display:flex;flex-direction:column;min-height:100vh;min-height:100svh}
.ecran1 > .hero{flex:1 0 auto;min-height:0 !important}
.ecran1 > .nx{flex:0 0 auto}
```

- Le bandeau prend sa hauteur naturelle, le hero **tout le reste**. S'il n'y a
  plus de match à annoncer (bandeau masqué), le hero remplit l'écran seul.
- `min-height:0 !important` à (0,2,0) **neutralise sans les supprimer** les 21
  `min-height … !important` à (0,1,0) des couches précédentes. En supprimer un
  ressusciterait le précédent de chaque palier.
- `flex-shrink:0` : le hero est en `overflow:hidden`, il ne doit jamais
  descendre sous son contenu, sinon les boutons sont rognés. Jamais de `height`
  ni de `max-height` sur `.hero`.
- `svh` et pas `dvh` : le premier écran tient barres du navigateur déployées ;
  `dvh` ferait sauter la mise en page à chaque repli de la barre d'adresse.
- Le conteneur n'a **pas** la classe `.section` (elle porte
  `content-visibility:auto` et la portée `main > .section` de V79), et il
  enveloppe les marqueurs du générateur sans se trouver entre eux :
  `build-matchs.py` ne réécrit que ce qui est *entre* `DEBUT` et `FIN`.

### Ce qui a quitté le hero

Le sur-titre « La Montagne lé là » et le sous-titre « De 3 ans aux Seniors ·
Loisir & compétition · Saint-Denis ». Il reste : la photo, le titre (H1), la
phrase manuscrite, le bouton d'inscription et le lien d'essai. Les âges et la
mixité iront dans la future section à cartes.

### Téléphone : une seule scène, comme sur ordinateur

Sous 640 px, la photo était une vignette **empilée** au-dessus du texte.
Empilés, photo + titre + signature + bouton + bandeau ne tenaient pas dans
667 px : il fallait une vignette de 100 px ou déborder. La photo passe donc
**derrière** le texte, plein cadre, avec un voile qui monte du bas. Sélecteurs
préfixés `.ecran1 .hero.in .hero__photo` (0,4,0) : `.hero.in .hero__photo`
(0,3,0) est redéclarée six fois plus haut.

### Le bandeau, en plus gros (V172)

Tout est préfixé `#nxBand`, qui passe les trois couches précédentes sans
`!important`. Trois dispositions :

| largeur | disposition |
|---|---|
| ≥ 1001 | trois zones côte à côte (V161), grossies : titre `clamp(1.85rem,3vw,3rem)`, écussons jusqu'à 64 px, bouton 60 px |
| 641–1000 | deux étages : l'affiche en haut, décompte et bouton dessous |
| ≤ 640 | empilé serré ; bouton et « Itinéraire » sur la même ligne |

Plus un cran en dessous pour les ordinateurs à fenêtre basse
(`max-height:820px`).

**Le bandeau suit la boîte du hero, pas `.wrap`** : `max-width:1560px`,
gouttière `clamp(18px,4vw,44px)` (≤ 640 : `clamp(20px,5.4vw,24px)`). Avant,
à 1717 px, le titre du hero partait de 115 px et le bandeau de 289 px — deux
bords gauches décalés de 174 px, et une zone « identité » de 518 px où
« MBC VS SAINTE-SUZANNE » passait sur deux lignes (bandeau à 274 px au lieu
de 165).

### Tablette tenue debout : l'image recadrée

Le hero remplissant l'écran, un iPad debout donne un cadre presque carré : le
panoramique 2,5:1 n'y montrait plus que 34 à 41 % de sa largeur — des enfants
sortaient du cadre, le défaut que corrigeait `5c0d95a`. Le `<picture>` sert
donc aux tablettes en portrait le visuel `-bande` (1400 × 1158, 1,21:1).

Les quatre attributs `media` doivent rester **exactement** ceux-ci — les deux
`<source>` et le preload « portrait » identiques, le preload « paysage » leur
**complément exact**, sinon soit le mauvais fichier est préchargé, soit les
deux sont téléchargés :

```
portrait : (max-width:640px), (orientation:portrait) and (max-width:1100px)
paysage  : (min-width:1101px), (min-width:641px) and (orientation:landscape)
```

`sizes` des sources `-bande` et `imagesizes` du preload portrait : `150vw`
(la photo affichée fait hauteur du hero × 1,21, soit 1,1 à 1,8 fois la largeur
d'écran). `build-hero.py` n'écrit pas ces attributs : ils vivent dans
`index.html`.

### Résultat, mesuré

**PILE aux 16 résolutions du banc**, de 360×740 à 2560×1440, portraits de
tablette compris, et **PILE sur tablette couchée** (1024×600, 1180×820).
Chaque format charge la bonne image (colonne relevée par le banc).

**Limites connues, assumées :**
- **Téléphone couché** (568×320 → 932×430) : le premier écran dépasse de 181 à
  315 px. Le bandeau seul occupe 55 à 72 % d'un écran de 320 à 430 px de haut.
  Rien n'est rogné — le bloc s'allonge.
- `sizes` des sources ordinateur (`(max-width:1550px) 1550px, 100vw`) sous-estime
  désormais la largeur affichée de 10 à 20 % sur grand écran (le hero est plus
  haut, la photo en `cover` plus large). Écart invisible en DPR 1, sans effet en
  DPR 2. Une formule en `max()` serait juste, mais un `sizes` que le navigateur
  refuserait retomberait sur `100vw` : pas touché.
- À la première visite, le bandeau de consentement couvre le bas de l'écran —
  donc le bandeau du match — jusqu'au choix du visiteur. Non modifié.

### Le banc de mesure

`_banc.html` (racine du dépôt, exclue de git par `.git/info/exclude`) charge
l'accueil dans des `<iframe>` à la taille exacte et écrit la géométrie en JSON ;
`banc.py` le lit par `--dump-dom`. C'est la seule mesure fiable sous 500 px de
large en headless (§ 17.7).

⚠️ Sous **Git Bash**, un argument qui ressemble à un chemin absolu est réécrit
avant d'arriver à Python : `/index.html` devient
`C:/Program Files/Git/index.html`, et les iframes chargent une adresse
inexistante — sans erreur, juste « aucun résultat ». Préfixer par
`MSYS_NO_PATHCONV=1`.

---

## 21. Le titre du hero grandit autant que le logo le permet (10/09/2026)

### La demande

« Agrandir nettement la typo *Le basket à La Montagne*, la remonter un peu, et le
bouton *Je m'inscris* aussi — il faut que le logo MBC dans le dos de la personne
tout à gauche soit toujours visible. »

### La contrainte, mesurée

Le logo occupe, dans chaque visuel :

| visuel | largeur | hauteur |
|---|---|---|
| panoramique (`mbc-hero-regroupement-*`) | 25,5 → 36,5 % | 29 → 53 % |
| recadré (`-bande-*`) | 3 → 26 % | 29 → 53 % |

Le titre chevauche le logo **en largeur** sur presque tous les formats (pas à
1366 × 657, où il s'arrête 30 px avant le logo) : la seule
chose qui garde le logo visible, c'est que le **haut du titre reste sous le bas
du logo**. Or le hero change de hauteur avec l'écran — et cette marge aussi :

| fenêtre | marge avant V173 |
|---|---|
| 2560 × 1300 | 264 px |
| 1717 × 892 | 28 px |
| 1366 × 657 (fenêtre de portable) | **−24 px : le titre couvrait déjà le logo** |

⚠️ **Tester des fenêtres réelles, pas des résolutions d'écran.** Une fenêtre de
navigateur fait ~110 px de moins que l'écran (1920 × 1080 → ~1920 × 950,
1366 × 768 → ~1366 × 657). C'est sur ces fenêtres-là que le logo était couvert.

### La formule (V173)

Une taille en `vw` ne peut pas être juste partout : grande là où il y a de la
place, elle couvre le logo là où il n'y en a pas. La taille dépend donc de la
**hauteur**, bornée par la largeur :

```css
--hf: clamp(3.3rem, calc(12.4svh - 33px), min(7.2vw, 9.5rem));   /* >= 1001 px */
--hf: clamp(2.8rem, calc(9svh - 20px), 5.6rem);                  /* 641-1000 px */
```

Dérivation : le bloc titre + phrase + bouton vaut ~2,7 fois la taille du titre
plus une constante ; le bas du logo tombe à 53 % du hero ; le hero vaut 100svh
moins le bandeau. « Haut du titre ≥ bas du logo + marge » donne une droite en
`svh`, calée ensuite au banc sur 21 formats. Le plancher de 3,3rem est le plus
petit titre qui laisse le logo visible sur une fenêtre de portable.

| fenêtre | titre avant → après | marge sous le logo |
|---|---|---|
| 2560 × 1440 | 74 → 146 px | 50 px |
| 2560 × 1300 | 74 → 128 px | 30 px |
| 1920 × 1080 | 74 → 101 px | 12 px |
| 1717 × 892 | 74 → 78 px | 19 px |
| 1366 × 768 | 57 → 62 px | 32 px |
| 1366 × 657 | 57 → 53 px | −24 → +6 px |
| iPad 820 × 1180 | 44 → 86 px | 82 px |
| iPad 768 × 1024 | 42 → 72 px | 59 px |

Ce qui suit le titre :
- la **phrase manuscrite** est dimensionnée sur lui (5,95 fois sa taille, la
  proportion d'avant), plafonnée à **640 px** sur ordinateur et **52vw** sur
  tablette : au-delà, elle finit sur le t-shirt blanc « DEPUIS 1954 » d'un
  enfant — blanc sur blanc, point orange posé sur « DEPUIS » ;
- la **marge sous le bloc** (« remonter un peu ») et la **hauteur du bouton**
  (62 → 74 px) ne grandissent qu'avec la hauteur d'écran : sur un portable,
  elles consommeraient les pixels qui séparent le titre du logo.

`--hf` est posée sur `.hero__h1` et reprise par `.hero__h1-t` et `.hw`. Toute
retouche de taille passe par elle.

### Le cadrage suit le logo

Sur téléphone, le visuel recadré était centré (`50 %`) : le logo, à 3–26 % de
sa largeur, sortait du cadre — **11 à 58 % visible**. Cadré à `8 %` sur
téléphone et `12 %` sur tablette debout : **97 à 100 %**.

**Limite assumée** : sur les petits téléphones (375 × 667, 360 × 740), le hero
ne fait que 415 à 489 px ; titre, phrase et bouton en occupent forcément la
moitié basse, et le logo, dans le cadre, reste en partie sous le titre.

### Le contraste (V174)

En grandissant, le texte sort du maillot noir de l'entraîneur et passe sur le
parquet clair et les t-shirts blancs. Pas de voile : il assombrirait aussi le
logo. Une ombre portée douce, collée aux lettres — `filter:drop-shadow`, et non
`text-shadow`, qui transparaîtrait à travers des lettres remplies par un
dégradé et ne vaut pas pour les contours SVG de la phrase.

### Les outils

- `banc-typo.py` calcule la position **à l'écran** du logo à partir du cadre,
  de la taille réelle de l'image et de son `object-position` calculé, puis la
  marge entre le logo et le titre, format par format.
- `_banc-essai.css` (racine, exclue de git) : une CSS injectée dans les iframes
  du banc avec `--essai`, pour essayer une formule sans reconstruire le site.

---

## 22. Le menu plein écran (10/09/2026)

### La demande

Remplacer la barre de liens par le menu du composant React « Sterling Gate
kinetic navigation » (GSAP). Le site n'a ni React, ni Tailwind, ni étape de
build : le composant est **transposé**, pas installé — même doctrine que pour
le « 3 fois sans frais » (§ 18).

### Ce qui correspond à quoi

| composant React | ici (V176) |
|---|---|
| GSAP (~70 Ko) pour quatre mouvements | des transitions CSS pilotées par **un** attribut, `data-nav` sur `#menu` |
| trois panneaux qui entrent par la droite | `.mn__couche` × 3 — orange ballon, bleu roi, nuit — à 0 / 0,12 / 0,24 s |
| liens qui montent de 140 % en tournant de 10° | `.mn__lien`, à 0,35 s + 0,05 s par rang (`--i`, posé dans le HTML) |
| « Menu » ↔ « Close », croix qui tourne de 315° | « Menu » ↔ « Fermer », sur `.mn-btn[aria-expanded]` |
| formes abstraites au survol | 7 motifs du club : ballon, six âges, terrain, vitesse, crête de La Montagne, ondes, bulles |
| libellés de démo | les 7 entrées de l'ancienne barre : mêmes adresses, même ordre |
| « click me » | « Je m'inscris », **qui reste visible dans la barre** (masqué sous 560 px, où le hero et la barre du bas le portent) |

Pages concernées : `index.html` et `adhesion.html`, les deux seules qui
portaient l'ancienne barre (`.site-header`). Les 23 pages enfants gardent leur
`.seo-top` : les aligner reste une décision à prendre.

Le composant n'avait aucune accessibilité ; elle est dans `script.js` :
`inert` quand c'est fermé, focus sur le premier lien à l'ouverture et retour au
bouton à la fermeture, Échap, voile cliquable, Tab piégé, nom accessible qui
suit l'état. Le focus clavier d'un lien n'est **pas** un outline — le `<li>`
masque ce qui dépasse, c'est la fenêtre de la montée : il allume la bande de
survol et souligne le libellé en orange.

### Deux pièges

1. **`scrollbar-gutter:stable` ne suffit pas.** Il garde bien la place de la
   barre de défilement quand on bloque la page, mais un calque `position:fixed`
   ne peint pas dans cette gouttière : le panneau s'arrêtait à 15 px du bord
   droit, sur une bande du fond de page. `script.js` mesure donc la largeur de
   la barre juste avant de la retirer (`--mn-sbw`) et la rend à la page
   (`padding-right`) et à la barre du haut (`right`).
2. **`.btn--lg` fixe police et marges en `!important`** (l.~1840). Le bouton du
   hero de V173 n'avait grandi qu'en hauteur ; toute retouche de ce bouton
   passe par `!important`.

### Les finitions du premier écran (revue contradictoire de V173/V174)

- Le bas de « LE BASKET À » était grisé : le `text-shadow` hérité de
  `.hero__h1` était peint **par-dessus** les lettres de la ligne du dessus
  (interligne 0,9, les lignes se touchent). Il est retiré ; le
  `filter:drop-shadow` se dessine sous l'élément entier et ne peut recouvrir
  aucune lettre.
- « Je m'inscris » passe de 271 × 60 à **305 × 74 px** à 2560 × 1300 (police
  indexée sur le titre : 20 % de `--hf`). Sur portable, sa largeur ne change
  pas : le titre n'y grandit pas non plus.

### Tester dans le panneau d'aperçu : trois leurres

- Avec une taille **émulée** (`resize_window` à 1440 × 860…), les clics par
  référence sont décalés du rapport d'échelle du panneau (visé 1325 px, reçu
  1413) : le clic tombe à côté du bouton. Tester les clics à la taille native.
- La touche Entrée n'y envoie que `keydown` et `keyup` : un `<button>` ne
  s'active pas. Ce n'est pas le site.
- Panneau masqué (`visibilityState: hidden`) : une transition lancée par script
  reste bloquée à `currentTime` 0 et garde sa valeur de départ. Vérifier l'état
  final avec `getAnimations().forEach(a => a.finish())`, ou par une capture
  headless en `--force-prefers-reduced-motion` d'une copie de la page dont le
  markup porte déjà l'état ouvert (`data-nav="open"`, sans `inert`).
