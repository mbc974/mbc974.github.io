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
| Les photos d'un soir de match (galerie « Sur le terrain ») | `data/galerie-match.json`, et les originaux sortis de l'appareil | `python .claude/build-galerie-match.py --images <dossier>` puis `bump-assets.py` (§ 30) |
| Le calendrier officiel (nouveau PDF de la ligue) | déposer le PDF dans Téléchargements | `python .claude/set-calendrier-prm.py` |
| Une dérogation (rencontre inversée avant un nouveau PDF) | `data/matchs.json` : la rencontre, et son champ `derogation` | `python .claude/build-og-matchs.py` puis `set-calendrier-prm.py --archive` et `bump-assets.py` (§ 29) |
| La photo du hero | `.claude/sources/hero-…jpg` | `python .claude/build-hero.py` |
| Le sitemap | rien, il se déduit des pages | `python .claude/build-sitemap.py` |
| La feuille de style | `style.css` | `python .claude/build-css.py` |
| Le menu, l'en-tête ou le pied de page | `index.html` (le menu aussi dans `adhesion.html`) | `python .claude/set-entete.py` puis les générateurs (§ 27) |

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
informations pratiques de la fiche. L'orange marque une victoire (le vert a été retiré le 13/09/2026, § 26), le blanc énonce une défaite,
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

**Depuis le 13/09/2026 (§ 26)**, un score saisi à la main dans `data/matchs.json` — résultat
communiqué par le club avant que la Ligue ne réédite son PDF — vaut partout : les deux Match
Center (accueil et `/matchs/`), la ligne du calendrier (`set-calendrier-prm.py --archive` la
régénère), la fiche (score en tête) et l'image de partage (`build-og-matchs.py`). Un score
imprimé par la Ligue reste prioritaire.

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
python .claude/build-effectif.py --essai   # les 10 joueurs sont-ils tous là ?
python .claude/build-galerie-match.py --check # le bloc des soirées photo correspond-il au JSON ?
python .claude/verifier-classes.py     # classes HTML sans aucune règle CSS
python .claude/verifier-liens.py       # liens, ancres, ressources, pages orphelines
python .claude/set-entete.py --check   # en-tête et pied de page à jour sur les 24 pages ?
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

`data/effectif.json` porte les dix joueurs : les neuf de départ, **extraits du
markup, jamais ressaisis**, et David Nugent (#12, intérieur), ajouté le
13/09/2026 — nom et numéro lus sur son affiche, poste (que l'affiche ne
porte pas) indiqué par Alexandre. Deux points à connaître avant d'y toucher :

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
  on les décline à la main, voir « Ajouter un joueur » ci-dessous).

`squad--4` sur la seconde rangée n'est pas décoratif : `.squad` est un
accordéon dont les deux rangées doivent avoir la **même somme de `flex-grow`**
(5,02), sinon la carte ouverte n'a pas la même largeur d'une rangée à l'autre
et `--fy` vise un cadre qui n'existe pas. Le générateur le pose tout seul dès
qu'un groupe compte quatre joueurs. Depuis l'arrivée de David Nugent
(13/09/2026), les deux rangées comptent cinq joueurs : le modificateur ne sort
plus, mais la règle CSS reste pour le jour où un groupe retombe à quatre.

**Ajouter un joueur.** Les affiches arrivent en un seul PNG (souvent sous un
nom GUID dans Téléchargements). Dans l'ordre :

1. Les décliner dans `assets/joueurs/` sous
   `mbc-senior-<prenom>-<nom>-<cran>.{avif,webp}`, aux crans
   360/560/760/<largeur d'origine>, en AVIF q45 speed 4 et WebP q66 method 6
   (les réglages de `build-hero.py` — `build-vignettes.py` laisse le WebP en
   method 4), plus un `-<largeur>.jpg` progressif **q80** de repli : la qualité
   des neuf premières affiches, lue dans leur table de quantification
   (luminance `6,4,4,6,10,16,20,24`), et non estimée au poids.
2. Ajouter l'entrée au JSON **à son rang** : par poste, puis par numéro
   croissant (Derras, passé au 94, garde la place de son ancien 10). Son `--fx`
   vise le visage du joueur au premier plan (carte repliée) ; son `--fy` doit
   convenir aux trois cadres dépliés (0,79 à 0,81) **et** au cadre 3/4 du
   téléphone, le plus exigeant pour les affiches 9/16.
3. Retoucher à la main le compte de l'accueil (« Les dix joueurs… » dans le
   `.sec-head__sub` de `#effectif`, hors du bloc généré ; `/effectif/` calcule
   le sien), puis lancer `build-effectif.py`, `bump-assets.py` et
   `build-sitemap.py`, et les contrôles `--essai` / `--check` de la checklist.

Le JSON-LD `SportsTeam` de `/effectif/` déclare **Frédéric Sornom** comme
entraîneur (`coach`) depuis la décision du bureau du 10/09/2026 (voir la table
des décisions). Avant, il n'en déclarait volontairement aucun : le site ne
disait nulle part qui entraînait les seniors.

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

**Retiré le 13/09/2026** : le ruban est remplacé par le Match Center (§ 26) et
`build-ruban-saison.py` n'existe plus. Sa CSS `.msn` est morte, à purger avec la
preuve d'empreinte des styles calculés.

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
portaient l'ancienne barre (`.site-header`). Les 23 pages enfants gardaient
leur `.seo-top` ; **elles sont alignées depuis le 13/09/2026 (§ 27).**

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

---

## 23. Le hero en couches : la parallaxe (10–11/09/2026)

### La demande

Appliquer au hero l'effet « Parallax Layers » d'Osmo (composant React : GSAP
ScrollTrigger + Lenis). **Transposé, pas installé** — même doctrine qu'aux
§ 18 et § 22.

### Comment ça a été décidé

Trois workflows. Le premier : quatre lecteurs (cascade CSS du premier écran,
JS, contraintes du dépôt, support des navigateurs en 2026), trois conceptions
indépendantes, trois juges, une synthèse. Puis deux revues contradictoires au
banc temps réel : la première a fait corriger la lisière, l'absence de
bandeau, l'état final, les tablettes, le relais du bouton, le clavier et le
filet du bandeau ; la seconde n'a plus rien trouvé de grave, et ses points
mineurs sont intégrés ci-dessous.

### Ce que l'œil lit

Un hero qui ralentit, et le bandeau du match qui le rattrape.

| plan | élément | ordinateur et téléphone | tablette (561–919 px) |
|---|---|---|---|
| fond | `<picture>` de la photo | 12svh (88 % de la vitesse) | 5svh |
| milieu | `.hero__inner` (titre, phrase, boutons) | 17svh (83 %) | 7svh |
| lisière | `#nxBand::before`, dégradé de 3svh | opacité 0 → 1 → 0 | idem |
| devant | `#nxBand`, le bandeau | vitesse de la page | idem |

Entre photo et texte, 5 px pour 100 px défilés : la profondeur « titre entre
deux plans » d'Osmo n'est pas reproduite, et c'est voulu (règle 1). Une
timeline de défilement CSS (`animation-timeline:scroll(root block)`) fait le
travail de ScrollTrigger. Le mouvement passe par `translate`, jamais par
`transform` : `heroZoom` (img) et `heroMonte` (titre, boutons) tiennent
`transform` et `opacity` en `fill both`, et `.hero__photo` a `transform:none`
à (0,3,0) quatre fois.

### Les deux règles qui fixent les amplitudes

1. **Le texte descend au moins autant que la photo.** Sinon le titre remonte
   vers le logo MBC du dos de l'entraîneur, qu'il frôle déjà au repos (6 px à
   1366 × 657, § 21). Ici l'écart logo-titre ne fait que grandir.
2. **Le texte ne descend pas de plus de 19svh.** Tout ce qui descend va vers
   le bandeau, et la première chose qu'il y rencontre est « Je m'inscris » :
   à 1440 × 860, son libellé passe sous le bandeau vers 425 px de défilement
   (sans V177, il passait sous la barre du haut vers 600 px).

Pour retoucher : `photo < texte ≤ 19svh`, dans les `@keyframes v177-*`. Les
couches courent sur `0 → 110svh` : l'étape du pic vaut 100 / 110 = 90.9091 %
(à recalculer si la plage change) et la pente vaut amplitude / 100svh. Le
`+1px` du `bottom` de la lisière suit l'épaisseur du `border-top` de `.nx`.

### Le relais « Je m'inscris »

Le bouton du hero partant plus tôt, il ne fallait pas de trou :
- **dès 561 px de large** (là où la barre du haut porte son propre « Je
  m'inscris ») : sur l'accueil, la barre ne se masque plus en descente qu'une
  fois le hero sorti de l'écran (`seuilMasque()` dans script.js ; c'était
  400 px). Ce seuil vaut pour tout l'accueil, parallaxe active ou non ;
- **tablette (561–919 px)** : en plus, 5 et 7svh. À 17svh, le libellé du hero
  commençait à disparaître entre ~270 et ~370 px, avant l'arrivée de la barre
  flottante à 600 px ; à 7svh, il reste lisible au-delà de 600 px (jusqu'à
  ~740–1070 px) ;
- **téléphone** : rien à régler, le libellé du bouton du hero reste lisible
  plus longtemps qu'avant (~560 px contre ~470 à 390 × 844).

### La lisière

Sans elle, le bord du bandeau tranchait net le bouton orange à mi-course —
une languette sans libellé, des lettres coupées en deux : ça se lisait comme
un bug. C'est le `.parallax__fade` d'Osmo : un dégradé `#030a14` de 3svh (20 à
36 px), peint au-dessus du texte, posé juste au-dessus du filet orange du
bandeau (qui reste visible). Une languette assombrie reste visible un
instant, sans libellé.
- 3svh et pas plus : au repos, le bas du bouton est à 21 px du bandeau à
  1440 × 860 (14 à 1366 × 657, 31 à 820 × 1180). À 5svh, la lisière
  assombrissait le bouton dès le premier cran de molette ; à 3svh, seul un
  portable bas (1366 × 657) voit encore le tiers bas du bouton s'assombrir
  dès le premier cran, le libellé restant net.
- Opacité 0 jusqu'à 6 % de la course, pleine à 14 %, éteinte progressivement
  de 95 à 100 %.
- Elle ne passe devant le texte que parce que le hero isole sa pile
  (`isolation:isolate`, reposé dans V177 même si d'anciennes couches le
  disent déjà).

### L'état final est le repos

Safari 26.0 à 26.4 peut mal restaurer une timeline au retour arrière (état
arbitraire, dont l'état final ; corrigé en 26.5 : webkit.org/blog/17938).
Chaque animation revient donc à son point de départ en fin de course : les
deux couches courent sur `0 → 110svh` (pente inchangée jusqu'à 100svh, retour
à 0 ensuite, hero déjà hors écran) et la lisière s'éteint à 100 %. Pire cas :
un hero au repos.

### Sans bandeau, pas de parallaxe

En fin de phase et hors saison, script.js masque le bandeau (`hidden`) ou
build-matchs.py n'écrit rien entre les marqueurs. Plus de plan de devant ni de
lisière : le texte serait tranché net au bord du hero. Un `:has()` remet alors
les deux couches au repos.

### Deux pièges

- **Une view-timeline sur le hero se décroche quand le menu s'ouvre.**
  `syncBodyLock` (script.js) pose `overflow:hidden` sur `<body>` ; `<html>`
  étant en `overflow-x:clip`, le body devient un conteneur de défilement et la
  timeline s'y rattache. `scroll(root)` suit la fenêtre.
- **`overflow:hidden` laissait le hero défiler de l'intérieur** : un
  `scrollIntoView` (recherche dans la page, ancre) sur le lien d'essai le
  décalait de 37 à 55 px à 1440 × 860 selon la position, jusqu'au retour en
  haut. `overflow:clip` coupe au même bord sans rien de défilable.

### Où l'effet ne s'applique pas

Mouvement réduit ; navigateurs sans `animation-timeline` (Firefox stable en
septembre 2026 — activation annoncée par Mozilla pour fin 2026, à repasser au
banc ce jour-là — et Safari avant 26) ; fenêtres de 520 px de haut ou moins ;
sans bandeau ; impression ; et tant qu'un élément du hero a le focus clavier
(couches au repos, lisière éteinte : WCAG 2.4.11).

Support : Chrome/Edge 115+, Samsung Internet 23+, Safari 26+ (sur le fil du
compositeur à partir de 26.4 : webkit.org/blog/17862).

### Ce qui a été écarté

Lenis (réécrit le défilement, bloque les ancres, ne fait rien au doigt) ; GSAP
(~70 Ko de JS pour ce que le navigateur fait seul) ; un pilote JS (une image
de retard sur le défilement) ; l'opacité sur le titre et les boutons ; un zoom
(flou au-delà de ce que décrit `sizes`) ; des calques d'image supplémentaires
(une seule vraie photo, doctrine V108) ; un fondu permanent au bord du
bandeau (il assombrissait le bouton au repos).

### Vérifier : `.claude/banc-parallaxe.mjs`

Le seul banc qui voit l'effet : les captures à temps virtuel
(`--virtual-time-budget`) ne ré-échantillonnent pas une timeline de
défilement et ne montrent que le repos, sans erreur. Mode d'emploi en tête du
fichier ; il faut le serveur local « mbc-static » (port 8000) :

    node .claude/banc-parallaxe.mjs apres 1440x860,390x844 0,0.25,0.5,0.75 --shots
    node .claude/banc-parallaxe.mjs avant 1440x860,390x844 0 --shots --off
    node .claude/banc-parallaxe.mjs sansbande 1440x860 0,0.5 --sans-bandeau

`--off` coupe la couche CSS, pas le seuil de script.js. Les seuils de relais
cités plus haut sont « la première position, au pas de 5 % de la hauteur du
hero, où… » ; « visible » est géométrique (le champ `libelleSousLisierePx`
dit ce que la lisière assombrit).

Mesuré le 11/09 : au repos, même géométrie qu'avant aux 8 formats du banc
(1440 × 860, 2560 × 1300, 1366 × 657, 820 × 1180, 768 × 1024, 912 × 1368,
390 × 844, 375 × 667) ; pixels identiques à 1/255 près, hors décompte du
bandeau, sauf à 1440 × 860 et 2560 × 1300 où la photo, devenue un calque
composite, est rééchantillonnée (22 et 28/255 au plus sur des contours,
reproductible, invisible). En défilant : pentes exactes (0,12 et 0,17 ; 0,05
et 0,07 sur tablette), aucun défilement interne, aucun débordement
horizontal, filet du bandeau intact.

### Limites acceptées

- Une languette assombrie du bouton reste visible un instant au bord du
  bandeau.
- Sur ordinateur, le bouton du hero part plus tôt qu'avant (425 px contre 600
  à 1440 × 860) ; la barre du haut assure le relais.
- Deux calques composites de plus tant que le hero est dans la page : non
  mesuré sur un vrai Android d'entrée de gamme.

## 24. L'essentiel en trois cartes (11/09/2026)

### La demande

Faire de la bande « 95 € · Dès 3 ans · 2 terrains » une vraie section de
cartes, avec les effets d'un composant « Pricing » (React : framer-motion,
NumberFlow, canvas-confetti, shadcn). **Transposé, pas installé** — même
doctrine qu'aux § 18, 22 et 23.

### Ce que l'œil lit

Un titre visible, « Le MBC en trois chiffres », puis trois cartes. Au centre,
le tarif : bordure orange, pastille « Tarif unique », surélevée de 20 px, un
halo chaud derrière. De part et d'autre, deux volets réduits à 0,94 qui se
tournent vers elle (9° sous perspective, pivot sur le bord intérieur, glissés
de 30 px sous la carte du centre). À l'arrivée à l'écran, les trois cartes
montent de 50 px et prennent la pose ; le 95 roule depuis 00.

| effet du composant | ici |
|---|---|
| framer-motion `whileInView` + ressort | transition CSS ease-out de 1,3 s lancée par un IntersectionObserver (le ressort k = 100, c = 30 est suramorti : aucun rebond) |
| `rotate-y-[10deg]` | vrai `rotateY(±9deg)` sous `perspective` (dans la démo, le transform de framer-motion l'écrasait) |
| NumberFlow | colonnes de chiffres 0-9 qui défilent ; « 3 × » et « ,67 » s'ouvrent en largeur |
| Switch de shadcn | `<button role="switch" aria-checked>` |
| canvas-confetti | même physique, rejouée en Web Animations : 50 disques aux couleurs du club, sous la barre du haut |
| bouton « outline » à anneau | calque orange en opacité + anneau `box-shadow` décalé |

### Le contenu

Rien d'inventé : chaque ligne existait déjà sur le site.
- Tarif : la FAQ de l'accueil (95 €, adhésion + licence FFBB + assurance,
  aucun autre règlement, dirigeant / bénévole gratuit). Les montants et les
  phrases de l'interrupteur sont ceux du module #pay d'adhesion.html
  (3 × 31,67 €) ; le `<noscript>` donne les trois échéances (31,67 / 31,67 /
  31,66). **Si le bureau change le tarif : la FAQ, #pay et ces cartes.**
- Âges : le sélecteur d'âge (Baby Basket nés de 2020 à 2023, École de
  Basket, U13, U15, U18, Seniors ou Loisirs dès 16 ans, débutants bienvenus).
- Terrains : la section calendrier (gymnase chemin des Bauhinias, plateau
  couvert de Ruisseau Blanc, entraînements lundi, mercredi et samedi, matchs
  à domicile vendredi soir et dimanche matin, « les créneaux peuvent
  évoluer »).

Les trois destinations d'origine restent (adhesion.html#tarif, #categories,
#calendrier), ainsi que l'ancre #essentiel visée par la flèche du hero.

### Les règles de construction

- **L'état posé est l'état par défaut de la CSS.** script.js ne pose
  `.kc--pre` (50 px plus bas, à plat) que s'il a un IntersectionObserver pour
  le lever. Sans JS, sans observateur ou en mouvement réduit, la section est
  complète et posée ; seul l'interrupteur reste caché (`hidden`).
- **Le survol se lit sur le `<li>`, jamais sur la carte pivotée** : en se
  redressant, son bord extérieur glisserait sous le curseur et le survol
  clignoterait. Au survol comme au focus clavier, un volet se redresse ; la
  carte du tarif monte de 6 px.
- **Une perspective par `<li>`**, point de fuite ramené vers le centre de la
  rangée (165 % / −65 %) : les deux volets partagent à peu près le même, sans
  `preserve-3d`.
- L'ordre du DOM est l'ordre visuel (âge, tarif, lieux) : la tabulation ne
  saute pas.
- Sous 900 px : cartes empilées (33rem au plus), sans 3D, une simple montée
  carte par carte.

### Un piège

`.section p{color:var(--txt-soft)}` (0,1,1) bat toute règle à une seule
classe posée sur un `<p>` : les chiffres sont d'abord sortis gris-bleu, et le
texte de la pastille gris sur orange. D'où `.kc__card .kc__val` et
`.kc__card .kc__badge`.

### Vérifier : `.claude/banc-essentiel.mjs`

Chrome piloté en CDP (serveur local « mbc-static », port 8000 ; captures
dans `%TEMP%\mbc-banc-essentiel`). Il ralentit la ligne de temps
(`Animation.setPlaybackRate`) pour saisir l'entrée et les confettis à des
instants connus, survole un volet et le bouton du tarif, bascule à la souris
puis revient avec la touche Espace, et mesure les transforms, les chiffres
affichés, `aria-checked`, la phrase annoncée et le débordement horizontal.

    node .claude/banc-essentiel.mjs v2 1440x1150,768x1500,390x2400
    node .claude/banc-essentiel.mjs v2 1440x1150 --extras

`--extras` ajoute, en 1440, le mouvement réduit et le rendu sans JavaScript.

Mesuré le 11/09 à 1440 × 1150, 2560 × 1300, 1024 × 1100, 768 × 1500 et
390 × 2400 : aucun débordement horizontal ; pose finale exacte (0,94, ±30 px,
±9° ; carte du centre à −20 px) ; bascule « 3 fois » : 3 × 31,67,
`aria-checked="true"`, phrase annoncée, 50 confettis ; retour « 1 fois » à la
touche Espace ; mouvement réduit : ni état d'avant ni confettis ; sans JS :
section posée, interrupteur caché, échéances en clair.

### Ce qui reste

- L'ancienne CSS `.keyfig*` / `.keyfig-sec` (une trentaine de couches) ne
  sert plus : à purger, avec une empreinte des styles calculés avant/après.
- Firefox et Safari n'ont pas été passés au banc (Chrome seulement).

## 25. La grille bento de la page adhésion (11/09/2026)

### La demande

Remplacer la grille « essentiel » d'adhesion.html (95 €, 8 formules, 2 lieux,
Sous 48 h, séance d'essai) par le composant « BentoGrid » de Magic UI (React,
Tailwind, shadcn, Radix). **Transposé, pas installé** — même doctrine qu'aux
§ 18, 22, 23 et 24.

### Comment ça a été décidé

Un workflow de conception (quatre lecteurs, trois conceptions, trois juges,
une synthèse), une revue contradictoire (cinq relecteurs, un vérificateur
adverse chacun, un critique), puis une vérification finale sur le code
corrigé. La revue a été coupée par un disque C: plein (voir « Ce qui
reste ») : les bancs de captures consomment vite de l'espace.

### Ce que l'œil lit

- **1024 px et plus** : trois colonnes. Le tarif tient la colonne de GAUCHE
  sur les trois rangées (la démo met la carte haute au centre : ici l'ordre
  du DOM reste l'ordre visuel et la tabulation ne saute pas) ; formules sur
  deux rangées puis lieux ; délai puis essai sur deux rangées. Rangées
  `minmax(15rem,auto)` (22rem dans la démo) : grille de 752 px.
- Chaque carte : un fond décoratif (photos du club déjà dans le dépôt, ou le
  terrain au trait en SVG pour le tarif), une icône, un nom, une description,
  un pied avec son ou ses liens, un voile.
- **Au survol** (souris, 1024 px et plus, sans mouvement réduit, à l'écran
  seulement) : le texte monte de 2.5rem, le pied glisse dessous, l'icône
  passe à .75, le voile teinte la carte. Le tarif garde son texte en haut.
- **Partout ailleurs** (doigt, clavier via `:focus-within`, mouvement
  réduit, impression) : les liens sont simplement visibles.
- **640 à 1023 px** : deux colonnes, le tarif sur deux rangées, les bandes
  photo limitées aux 55 % du haut de la carte.
- **Sous 640 px** : une colonne compacte, icône à gauche, lien en rangée de
  44 px ; les photos ne sont pas téléchargées. Idem au téléphone tenu en
  paysage (`(hover:none) and (max-height:540px) and (max-width:1023px)`).

### Le contenu

Les textes des cinq cartes sont ceux de l'ancienne grille. Chaque carte gagne
un lien vers une destination qui existait déjà : #tarif (« Ce que couvrent
les 95 € »), #formules (« Quelle formule choisir ? »), les deux liens Google
Maps de l'accueil et de /creneaux/, #parcours (« Voir les 5 étapes
détaillées », comme dans la FAQ) et WhatsApp pour la séance d'essai (même
texte prérempli qu'index.html). « Sous 48 h » est repris de la grille
d'origine ; le même délai figure en #parcours (étape 2), dans la ligne de
réassurance de la page et sur cinq autres pages (enfant, école de basket,
club, bénévoles, sponsors) : s'il change, huit endroits sont à modifier.

### Les photos de fond

| carte | fichiers |
|---|---|
| formules | `assets/galerie/initiation-basket-enfants-600.avif` / `.webp` |
| lieux | `assets/images/gymnase-la-montagne-clair-400/640.webp`, `assets/images/ruisseau-blanc-terrain-400/640.webp` |
| délai | `assets/galerie/benevole-mbc-accueil-la-montagne-400/600.avif` / `.webp` |
| essai | `assets/galerie/mbc-cercle-ecole-de-basket-saint-denis-420/660.avif` / `.webp` |

Décoratives (`alt=""`, `aria-hidden`), en `loading=lazy`. Renommer un de ces
fichiers impose de mettre à jour adhesion.html (verifier-liens.py lit les
`src`/`srcset`). Les `sizes` des lieux (202 et 228 px) suivent la hauteur de
la bande duo (9,5rem) : à recalculer si elle change.

### Ce que la revue a fait corriger

| constat | correctif |
|---|---|
| A4 paysage : les liens des cartes ne s'imprimaient pas (Chrome évalue hover et pointer sur l'appareil, même à l'impression) | `@media screen and (...)` sur la montée |
| Impression : photos imprimées sous le texte, cartes coupées par le saut de page | `@media print` : fonds retirés, rangées auto, cartes insécables |
| Au bureau, le « 95 € » sortait du premier écran ; grandes cartes vides de 250 à 440 px | rangées de 15rem, bandes de 17rem, tarif en haut de sa carte et terrain ancré en pied |
| Tablette en portrait : la photo des formules devenait l'élément LCP (+1 s) | bandes photo limitées aux 55 % du haut |
| Zoom texte 200 % : mots et liens rognés par le cadre de la carte | `overflow-wrap` sur les descriptions et les liens ; les liens des lieux gardent le droit de passer sur deux rangées (un `nowrap`, d'abord essayé, rognait « Ruisseau Blanc » à 200 %) |
| Téléphone en paysage : 244 Ko de photos | photos masquées |
| Tablette 7 pouces en paysage (3 colonnes, 540 px de haut au plus) : cartes vides sans photos | règle du téléphone en paysage bornée à 1023 px |
| Premier écran à 1366 × 768 : grille pas encore révélée | l'IIFE V180 révèle la liste dès son premier pixel à l'écran |

Acceptés : au téléphone la grille passe de 606 à 912 px (le prix des liens
toujours visibles au doigt) ; au bureau les photos retardent d'environ
165 ms les polices non préchargées (LCP toujours bon) ; la photo des
formules n'existe qu'en 600 px de large. Reporté à une tâche séparée : la
barre flottante #floatCta peut masquer le focus clavier sous 640 px (défaut
de tout le site). Réfuté : les noms accessibles des liens Maps.

### Vérifier : `.claude/banc-bento.mjs`

Chrome piloté en CDP (serveur local « mbc-static », port 8000 ; captures
dans `%TEMP%\mbc-banc-bento`) : mise en page, survol de chaque carte, vraie
touche Tab, tactile (`Emulation.setTouchEmulationEnabled`), mouvement
réduit, sans JavaScript.

    node .claude/banc-bento.mjs v3 1440x1300,1024x1250,768x1500,390x1900 --tactile --extras --sel='{"grille":".adh-bento","carte":".adh-bento__card","cta":".adh-bento__cta","corps":".adh-bento__body"}'

Trois pièges de mesure : l'opacité du pied est sur `.adh-bento__foot`, pas
sur le lien (le banc calcule l'opacité effective) ; `captureBeyondViewport`
fait tomber la media query du survol le temps de la capture (le banc capture
la fenêtre entière) ; `html{scroll-behavior:smooth}` impose
`behavior:'instant'`.

Mesuré le 11/09 : grille de 752 px à 1440 et 1024, 848 en tablette, 912 à
390 ; aucun texte rogné ni débordement horizontal ; au repos en mode survol
les cinq pieds à opacité 0, révélés au survol et au focus clavier ; au
doigt, en mouvement réduit et sans JS, liens visibles. « 95 € » sans
défiler : visible à 1440 × 900, 1536 × 864 et 1024 × 768 (à 1366 × 768 et
1280 × 800 il reste sous le pli, comme avec l'ancienne grille, qui commence
elle-même à 690-722 px). Impression A4 : les six liens présents dans le PDF,
aucune photo de la grille, aucune carte coupée.

### Ce qui reste

- L'ancienne CSS `.essentiel-grid` / `.essentiel-card` (une cinquantaine de
  règles, beaucoup en `!important`) ne sert plus : à purger avec le motif
  `\.essentiel-(grid|card)` SEULEMENT (`.essentiel-cta` sert encore, ici et
  sur l'accueil), preuve d'empreinte des styles calculés à l'appui.
- Firefox et Safari n'ont pas été passés au banc.
- Limites acceptées du lien révélé au survol (1024 px et plus, pointeur
  fin) : sur un portable tactile ou un iPad avec trackpad, un premier tap
  révèle le lien, un second l'active ; un lecteur d'écran en mode lecture
  (curseur virtuel) peut lire un lien encore à opacité 0 à l'écran si le
  focus système ne le suit pas. Au clavier (Tab), le lien est révélé.
- Coût mesuré des photos en 4G lente : +144 à +160 ms sur le LCP (du
  texte) et un CLS de 0,005 : accepté.
- Disque : le 11/09, C: s'est rempli (0 Go libre), surtout à cause du cache
  de shaders NVIDIA (`%LOCALAPPDATA%\NVIDIA\DXCache`, 39 Go) ; les bancs de
  la revue avaient laissé 2,5 Go de captures dans `%TEMP%`. Vérifier
  l'espace libre avant une revue à plusieurs agents.

---

## 26. Le Match Center de la saison (13/09/2026)

Branche `feature/season-match-center`.

### La demande

Transformer le calendrier des seniors en un vrai Match Center. On doit y lire
immédiatement le dernier résultat, le prochain match et le lieu, puis les
rencontres suivantes, la différence entre championnat et Coupe, et ce qui est
confirmé face à ce qui dépend encore d'un classement ou d'une qualification.
Le prochain match doit changer SEUL, sans retoucher le HTML. Mobile d'abord.
Sources de vérité : les PDF de la Ligue. Aucune affiche, aucune date, aucun
camp ne doit être inventé.

### Ce que disent les documents, et ce qu'ils ne disent pas

| source | ce qu'on en tire |
|---|---|
| `CALENDRIER SENIOR PRM NORD.pdf` (25/08/2026, archivé) | les 7 journées de la phase 1, le vendredi à 20h30 ; le camp est donné par l'ORDRE des équipes (art. 10) ; aucun score imprimé |
| calendrier général sportif 2026-2027, **V2** (lignes « PRM D1 » et « PRM D2 ») | 14 dates de 2e phase (1A → 7A, 1R → 7R), **identiques dans les deux divisions** ; phase finale sur la seule ligne D1 (½ A 02/04, ½ R 09/04, finale A 16/04, finale R 23/04/2027) ; TRCF les 26/09, 17/10, 14/11, 29/11 et 12/12 |
| règlement particulier PRM (art. 3 et 4) | D1 = les 4 premiers de chaque poule, D2 = les 5e à 8e ; aller-retour ; horaire officiel vendredi 20h30 |

Trois conséquences, visibles sur le site :

- **La division du MBC en 2e phase n'est pas connue** : le site écrit « Division
  1 ou 2 selon le classement », jamais « D1 ». Les dates, elles, sont sûres,
  puisqu'elles sont les mêmes dans les deux lignes.
- **Les tours de Coupe** : le 29/11 est surligné en jaune (légende « Finales
  régionales »), le 12/12 en vert (« Finales zone »). D'où les libellés
  « Finale régionale » et « Finale de zone », à corriger dans `data/matchs.json`
  si la Ligue les précise. La case TRCF du 04/09, antérieure à la J1, n'est
  pas reprise : rien ne dit si le MBC l'a disputée.
- **La J1 (73-52)** vient du club (13/09), pas du PDF, qui n'a pas encore été
  réédité. Voir `_sources` en tête de `data/matchs.json`.

La lecture du calendrier général a été contre-vérifiée par trois agents
indépendants : deux lecteurs à l'aveugle (rendus PyMuPDF, colonnes recoupées au
pixel) et un contradicteur. Résultat : 31/31 cases identiques sur la ligne D1,
27/27 sur la ligne D2, couleurs comprises. Le contradicteur a confirmé 30
affirmations sur 31 ; la seule réserve est que le PDF ne développe jamais le
sigle « TRCF ».

### La source unique

`data/matchs.json`, deux listes :

- `matchs` : les rencontres confirmées, chacune avec sa fiche. Champs nouveaux :
  `competition` (`prm` / `trcf`), `phase` (`brassage` / `phase2` / `finale`),
  `journee` + `manche`, ou bien `tour` ;
- `echeances` : les dates fixées par la Ligue sans affiche connue, avec leur
  `etat` (`a-determiner`, `selon-classement`, `selon-qualification`).

**Quand une affiche de 2e phase ou de Coupe est connue**, on l'ajoute à
`matchs` avec son slug. L'échéance du même jour, de la même journée ou du même
tour disparaît d'elle-même (`remplacee()` dans `build-match-center.py`) : il
n'y a rien à retirer, et une dérogation qui déplace la date ne crée pas de
doublon.

### Ce qui est généré, et par quoi

- `.claude/build-match-center.py` (appelé par `build-matchs.py`) écrit le bloc
  `MATCH-CENTER` de l'accueil (dernier résultat, prochain match, « À suivre »,
  lien vers la saison) et le `<main>` de `/matchs/` (les deux cartes, les
  filtres, la saison mois par mois, le format, la poule, les sources).
- `build-matchs.py` enveloppe `/matchs/` du gabarit du site, qui charge
  désormais `script.js` comme `/creneaux/`. Une fiche de match jouée affiche
  le score en tête, n'offre plus ni itinéraire ni agenda, et se partage avec la
  carte portant le score. L'étiquette de journée est commune à tout le site
  (`_etiquette`) : une rencontre de Coupe, qui n'a pas de numéro de journée, ne
  casse plus le bandeau, la fiche, le `.ics` ni l'image de partage.
- `set-calendrier-prm.py` ne compare au PDF que la phase 1 (`dans_le_pdf()`).
  La ligne du calendrier reprend le score du JSON quand la Ligue n'en a pas
  imprimé.
- `build-ruban-saison.py` est **retiré**, remplacé par le Match Center. Il
  aurait planté au premier score saisi (`ech()` appliqué au dictionnaire du
  score), et l'erreur était avalée par un `except` : la home serait restée
  figée sans que personne ne le voie. L'appel est désormais sans `except`.

### Le temps

Le HTML est juste à la date de publication, et complet sans JavaScript. Les
cartes des semaines qui suivent sont écrites d'avance dans des `<template>` :
4 rencontres sur `/matchs/`, 3 sur l'accueil (≈ 3 Ko gzippés). `script.js`
(bloc V181) choisit, à l'heure de La Réunion, celle qui vaut, sans fabriquer
de texte. Les libellés « En cours » et « Score à venir » sont écrits par le
générateur (`data-live`, `data-apres`). Une fenêtre de Coupe « selon
qualification » ne passe jamais devant une rencontre confirmée.
Dégradation voulue : sans republication pendant plus de trois ou quatre
semaines, la carte « prochain match » disparaît plutôt qu'annoncer une date
passée. Le bandeau sous le hero et la saison continuent de se recaler.

`MBC_MAINTENANT=AAAA-MM-JJTHH:MM` simule une autre date côté générateur (le
bandeau et le Match Center lisent la même horloge).

### Publier un résultat

```bash
python .claude/build-og-matchs.py
python .claude/set-calendrier-prm.py --archive
python .claude/bump-assets.py
python .claude/build-sitemap.py
```

La carte de partage d'abord : une fiche NOUVELLE (affiche de 2e phase ou de
Coupe) ne pointe sur sa carte que si le fichier existe au moment où elle est
écrite ; dans l'autre ordre, il fallait deux passages.

Au préalable, dans `data/matchs.json` : `"score": {"mbc": 73, "adverse": 52}`
(toujours du point de vue du MBC) et `"statut": "joue"`. Avec un nouveau PDF de
la Ligue, lancer `set-calendrier-prm.py` sans `--archive`.

### Vérifier : `.claude/banc-match-center.mjs`

```bash
node .claude/banc-match-center.mjs --base=http://localhost:8010
```

Il prend 375, 390, 430, 768 et 1440 de large en viewport émulé exact (pas
`--window-size`, clampé à 500 px). Il teste les filtres à la souris et à la
touche Espace, la page sans JavaScript et en mouvement réduit. Il simule quatre
instants en remplaçant `Date` avant les scripts de la page : J2 en cours, le
lendemain de J2, le jour de Coupe du 26/09, la veille de J5. Enfin, il ouvre
les pages `_banc-mc-*.html` que l'on génère à une autre date (git-ignorées).
Captures et rapport dans `%TEMP%\mbc-banc-match-center`.

Mesuré le 13/09 : aucun débordement horizontal à aucun format, 0 erreur
console. Filtres : Coupe 5, Domicile 4, Extérieur 3, Coupe + Domicile 0 avec
le message vide. Sans JavaScript : 30 dates visibles, barre de filtres masquée.
Le lendemain de J2, la carte principale passe seule à J3 et J2 dit « Résultat à
venir ». Le 7/11, la carte principale devient « Prochaine échéance · 2e phase ·
J1 aller ».

### Pièges rencontrés

- `content-visibility:auto` : la première version du banc, qui sautait sur
  `#matchs` en un seul calcul, photographiait les créneaux. Il faut répéter
  `scrollIntoView`.
- Des `id` dans les `<template>` se retrouvaient plusieurs fois dans le fichier
  (`verifier-jsonld.py` les compte). Les cartes n'en portent plus : leur titre
  suffit.
- `.section p` (0,1,1) repeint et regrossit tout paragraphe sous 760 px :
  chaque `<p>` du Match Center est donc visé par deux classes.
- Le compte à rebours est construit nœud par nœud : les espaces doivent être de
  vrais nœuds texte, sans quoi un lecteur d'écran lit « dans05jours07h ».

### La revue contradictoire (13/09)

Cinq relecteurs (faits sportifs, chaîne Python, logique du temps en JS,
accessibilité et design, SEO et intégration), chacun doublé d'un vérificateur
chargé de réfuter : 36 constats confirmés, 1 réfuté. Ce qui a été corrigé :

- **deux plantages** dès qu'une rencontre de Coupe, sans numéro de journée,
  entre dans `matchs` : le sujet du courriel bénévole et le résumé final
  écrivaient encore `J%d` ;
- **`reporte` et `annule` hors jeu** : une rencontre reportée était annoncée
  comme prochain match, puis « terminée » ; le repli pouvait promouvoir une
  rencontre annulée ;
- **l'orientation du score** : la ligne du calendrier et la fiche d'un match à
  l'extérieur écrivaient « victoire du MBC 60–70 ». Règle : les chiffres
  suivent l'ordre du duel affiché (le recevant d'abord) ; une phrase « du MBC »
  est suivie des chiffres du MBC ; le lecteur d'écran entend une phrase
  complète ;
- **les fenêtres de Coupe** couvertes par un tour joué la veille ou le
  lendemain restaient affichées : tolérance de ±3 jours ;
- **la page laissée ouverte** : le Match Center passait à la J3 au coup de
  sifflet final pendant que le bandeau sous le hero et les lignes du
  calendrier restaient sur la J2. Le bloc V181 émet `mbc:minute`, que ces
  blocs écoutent désormais ; la minute est calée sur la minute pleine ;
- **le focus clavier** tombait sur `<body>` quand une carte était remplacée ;
  **un second clic de filtre rapide** était avalé par la transition de vue
  (retirée : un fondu CSS des mois, qui ne capte aucun clic) ;
- **accessibilité** : colonne « Lieu » écrasée à 200 % de texte, boutons de
  filtre portés à 44 px, état pressé lisible en couleurs forcées, jour de la
  semaine masqué par le quantième en couleurs forcées, accueil imprimé sans
  Match Center (`.reveal` restait à opacité 0 à l'impression) ;
- **les ancres de l'accueil** (`/#matchs`, `/#match-…`, `/#calendrier`)
  atterrissaient 1 000 à 2 500 px trop haut à cause de `content-visibility` —
  défaut antérieur, que le nouveau lien « Revenir à l'accueil » rendait
  visible : la cible est recalée sur quatre images, pour toute ancre ;
- **les libellés** : « 2e phase · J1 aller » au lieu de « J1 aller », plus de
  « Zone Nord » sur une fiche de 2e phase, noms d'adversaires repris du JSON
  dans les lignes du calendrier, « poule de brassage » définie dans le format,
  textes de l'accueil qui parlaient encore de « 7 rencontres de la saison ».

### Ce qui reste

- **Rencontre reportée et bandeau** : le réarmement du bandeau (JS) lit les
  lignes du calendrier, qui ne portent pas le statut ; une rencontre reportée
  y reste annoncée jusqu'à la republication (le HTML publié, lui, l'écarte).
- **Coupe saisie sans `tour`** : l'étiquette retombe sur « Coupe de France »
  (« Trophée Coupe de France · Coupe de France ») : toujours saisir le tour.
- **Petite finale PRM** : le règlement la prévoit, mais le calendrier général ne
  lui donne aucune date.
- **Salles des matchs à l'extérieur** : la Ligue ne les publie pas. Le site
  écrit « Chez l'adversaire », sans `SportsEvent` (règle du § SEO : pas
  d'événement sans lieu).
- **Affiches de 2e phase** : `set-calendrier-prm.py` ne lit que la poule de la
  phase 1. Quand la Ligue publiera la 2e phase, il faudra l'étendre, ou saisir
  les affiches dans `data/matchs.json`, slugs compris.
- La CSS `.msn` (ruban V162) est morte : à purger avec la preuve d'empreinte
  (§ « Prouver une non-régression »).
- Firefox et Safari n'ont pas été passés au banc.

---

## 27. Un seul en-tête et un seul pied de page pour tout le site (13–14/09/2026)

Branche `feature/season-match-center`, commit séparé du Match Center.

### La demande

« Attention, sur cette page le header n'est pas le même que sur l'index
principal » : Alexandre sur `/matchs/`. La décision laissée ouverte au § 22 est
prise pour **les 23 pages enfants**. Elles prennent la barre de l'accueil : la
marque « MBC 974 », « Je m'inscris » et le bouton Menu plein écran.

### Comment

- **Une seule source** : `adhesion.html`, entre `<!-- EN-TETE:DEBUT -->` et
  `<!-- EN-TETE:FIN -->`. C'était la seule page hors accueil qui portait déjà
  la barre V176. `entete_enfant()` (dans `build-matchs.py`) en tire le bloc
  des pages enfants, avec deux retouches : elle retire les deux `aria-current`
  propres à la page d'adhésion et ajoute le modificateur `site-header--enfant`.
- **Les 17 pages générées** reçoivent ce bloc par `gabarit()` (build-matchs,
  build-actus, build-creneaux, build-effectif). **Les 6 pages écrites à la
  main** le reçoivent par `.claude/set-entete.py`. Les deux passent par la même
  fonction : une page ne peut pas recevoir deux formes d'en-tête.
- **`script.js` sur toutes les pages** : le menu en dépend. `gabarit()` ou
  `set-entete.py` pose une seule balise, et les ajouts propres à `/creneaux/`
  et à `/matchs/` sont retirés. Deux `script.js` sur une page brancheraient
  chaque module deux fois.
- **Une barre collante, pas fixe**, sur les pages enfants. Sur l'accueil, elle
  glisse sur la photo du hero ; une page enfant n'a pas de hero, et une barre
  fixe y aurait masqué le fil d'Ariane. Collante, elle occupe sa place comme
  l'ancienne `.seo-top` : les quatre règles d'espacement `.seo-top ~ main`
  passent telles quelles sur `.site-header--enfant ~ main` (style.css, V182).

### Pour changer le menu ou le pied de page

- **Le menu** : modifier `index.html` ET `adhesion.html`, qui sont tous deux
  écrits à la main.
- **Le pied de page** : modifier `index.html` seul, entre
  `<!-- PIED:DEBUT -->` et `<!-- PIED:FIN -->` (V184, plus bas).

Puis relancer :

```bash
python .claude/set-entete.py
python .claude/build-creneaux.py
python .claude/build-effectif.py
python .claude/set-calendrier-prm.py --archive
python .claude/build-actus.py
python .claude/bump-assets.py
```

`set-entete.py` signale une dérive entre les deux menus. `set-entete.py --check`
sort en 1 si une page enfant n'est pas à jour.

### Vérifié le 13/09

Banc CDP sur les 25 pages, à 390 et à 1440 px de large :

- **La barre** : collante sur les 23 pages enfants, fixe sur l'accueil et
  `adhesion.html`, haute de 72 px. Elle ne recouvre jamais le premier contenu
  (le fil d'Ariane de `/matchs/` commence à 120 px).
- **Le chargement** : plus aucune `.seo-top`, une seule balise `script.js` par
  page, 0 débordement horizontal, 0 erreur console.
- **Le menu**, testé sur `/matchs/` à 390 px et sur `/club/` à 1440 px : il
  s'ouvre au vrai clic, avec le focus sur « Le club » ; Échap le ferme et rend
  le focus au bouton. La barre se masque en descendant et revient en remontant.
- **Idempotence** : après les générateurs, `set-entete.py --check` ne trouve plus
  aucune page à mettre à jour.
- **Le Match Center** est inchangé : filtres, cartes et quatre instants simulés.

### Le pied de page (V184, 14/09/2026)

Branche `feature/pied-de-page`, empilée sur la précédente.

Le pied de page avait le même écart que l'en-tête. L'accueil portait le grand
pied `.site-footer` : le club, les liens utiles, le contact, l'affiliation FFBB,
« Le basket près de chez vous ». Les 23 pages enfants gardaient `.seo-foot`,
une ligne de liens. Il est aligné de la même façon.

- **Une seule source** : `index.html`, entre `<!-- PIED:DEBUT -->` et
  `<!-- PIED:FIN -->`. `pied_enfant()` (dans `build-matchs.py`) en tire le bloc
  des pages enfants, avec deux retouches :
  - les mentions légales détaillées (`details#legal`) restent sur l'accueil
    seul. Recopiées, elles auraient fait 24 ancres `#legal` et 23 copies du
    même texte ; les liens « Mentions légales » visent `/#legal`, comme avant ;
  - les liens relatifs de l'accueil (`#matchs`, `benevoles/`, `adhesion.html`)
    deviennent absolus.
- **Les mêmes chemins que l'en-tête** : `gabarit()` pour les pages générées,
  `set-entete.py` pour les pages écrites à la main. Ce script pose désormais
  les deux blocs, et `--check` contrôle les deux.
- **La barre CTA mobile** : chaque page enfant avait un module en ligne qui
  attendait `.seo-foot` pour s'effacer. Ce module est retiré. `script.js`,
  chargé partout depuis V182, fait exactement la même chose (`floatCta`, qui
  cherche `.site-footer, .seo-foot`).
- **`adhesion.html` aussi**, à la demande d'Alexandre, le même jour. Son pied
  à part (« Documents & garanties », liens « Agir ») est remplacé par le bloc
  commun. `set-entete.py` s'en charge et ne touche qu'au pied : l'en-tête
  d'`adhesion.html` reste la source de celui des pages enfants, et reste fixe.
  Le RNA et le SIREN ne sont plus affichés sur cette page ; ils restent dans
  les mentions légales de l'accueil (`/#legal`).
- **Aucun octet de CSS ni de JS** : les `?v=` ne bougent pas.

Vérifié le 14/09 (banc CDP, 25 pages à 375, 390, 430 et 1440 px) :

- **Structure** : un seul `<footer>` par page, plus aucune `.seo-foot`, et
  `#legal` sur l'accueil seulement. Le bloc `PIED` est identique, octet pour
  octet, sur les 24 pages qui le reçoivent (23 enfants et `adhesion.html`).
- **`adhesion.html`** : la barre du haut reste fixe, et la barre CTA mobile
  s'efface sur le nouveau pied comme ailleurs.
- **Contenu** : aucun lien relatif dans un pied enfant, et le même texte que
  l'accueil, mentions détaillées exceptées.
- **Affichage** : le pied est pleine largeur et ne chevauche jamais `<main>`,
  sans débordement ni erreur console.
- **Liens** : les 20 liens internes du pied répondent en 200, et leurs 7
  ancres existent.
- **Barre CTA** : elle paraît au milieu de `/matchs/`,
  `/ecole-de-basket-saint-denis/` et `/creneaux/`, et s'efface sur le pied.
- **Garde-fous** : `verifier-liens` et `verifier-jsonld` sont à 0 ;
  `verifier-classes` ne relève que les 4 anomalies antérieures, et
  `set-entete.py --check` est à 0 après les générateurs.

**Piège vécu** : une copie de travail extraite par `git worktree` sur ce poste
sort en CRLF (`core.autocrlf=true`), alors que le dépôt est en LF.
`bump-assets.py` hache les octets : il a changé les trois `?v=` et le nom du
cache du service worker sans aucune modification réelle. Pour corriger :
supprimer les fichiers hachés, les ré-extraire avec
`git -c core.autocrlf=false checkout -- style.css style.min.css script.js consent.js`,
puis relancer `bump-assets.py`. Un simple `checkout` ne suffit pas : git juge
ces fichiers inchangés. Vérifier avec `git ls-files --eol` (`w/lf`).

**Relecture contradictoire du 14/09** : 5 angles (chaîne, liens et SEO,
accessibilité, CSS, comportement), puis un contradicteur par constat, en
lecture seule. Sur 12 constats, 7 ont été réfutés : le lien « Matchs » vers
`/#matchs`, « L'équipe », l'impression du grand pied, l'arrêt de
`--check`. Les 5 autres sont corrigés :

- **Saut de titres** : sur `/effectif/` et `/actualites/`, on passait du `h1`
  aux `h3` du pied. Le pied porte désormais un titre `h2` invisible
  (`.sr-only`, « Le club : liens et contact »). Aucun CSS n'a changé.
- **La signature** « Made with ❤ by Alex » est en anglais : `lang="en"`. Le
  cœur, qui portait `aria-hidden`, a désormais un nom lu (`role="img"`,
  `aria-label="love"`) ; avant, on entendait « Made with by Alex ».
- **`pied_enfant()` durci** :
  - le test du protocole ne dépend plus de la casse ;
  - `xlink:href` et `data-href` ne sont plus touchés ;
  - un `href` entre apostrophes ou sans guillemets arrête le script ;
  - le commentaire qui précède `#legal` peut changer de texte.
  Onze cas ont été testés en mémoire, et le bloc produit ne change pas.
- **La documentation** : `set-entete.py --check` entre dans les tests
  avant publication (§ 7) et dans le tableau du § 1 bis. Le décompte de
  la CSS morte est corrigé.

La preuve que ces retouches ne changent rien à l'écran : une empreinte du
pied de page, soit la boîte de chaque élément et 14 styles calculés, sur 7
pages à 390 et 1440 px. Elle a été relevée avant, puis une seconde fois à
code identique (0 écart), puis après : **0 écart sur 1 218 éléments**. Le plan
des titres des 25 pages ne montre plus aucun saut dû au pied. Le seul saut
restant, `h2` vers `h4` sur `/creneaux/`, est antérieur.

### La purge des anciens styles (V185, 14/09/2026)

Demande d'Alexandre : « purge les anciens styles d'en-tête et de pied de
page ». Même branche, commit séparé.

- **Ce qui est parti** (`.claude/purger-entete-pied.py`) :
  - l'ancienne barre des pages enfants : `.seo-top`, `.seo-top__brand`,
    `.seo-top__nav` et `html:has(.seo-top)` ;
  - l'ancien pied des pages enfants : `.seo-foot`, `.seo-foot__links` ;
  - l'ancien pied d'`adhesion.html` : `.footer__tag`, `.footer__actions`,
    `.footer__trust*`, `.footer__mini-logo`, `.footer__brand .small` et
    `.footer__brand p.small` ;
  - le bloc « petit logo MBC dans la barre basse ».

  Au total :
  - 57 règles retirées : 51, plus les 6 du bloc « petit logo » ;
  - 1 règle allégée : `.footer__actions a,.footer__social a` garde
    `.footer__social a` ;
  - 6 blocs `@media` vidés, retirés avec elles. Les 6 `@media` qui étaient
    déjà vides avant la purge sont restés.

  `style.css` perd 124 lignes, `style.min.css` 5,7 Ko ; seul son `?v=`
  change.
- **Le bloc « petit logo » visait deux classes vivantes**, `.footer__bottom`
  et `.footer__legal`, mais il était inerte. Plus bas, `.footer__bottom`
  repasse en `display:flex`, et ni `grid-template-columns` ni `justify-self`
  n'agissent dans un conteneur flex.
- **Les commentaires orphelins** : douze commentaires ne décrivaient plus que
  des règles purgées. Ils ont été retirés ou réécrits au passé. Le script
  refuse d'écrire si le CSS lui-même change : le CSS sans commentaires doit
  être identique avant et après.
- **`set-entete.py` garde ses motifs de migration**, l'ancienne barre `.seo-top`
  et l'ancien pied `.seo-foot`. Ils servent encore pour la branche du
  reportage (`93babdb`), antérieure au pied commun. Mais `verifier-classes.py`
  lit les chaînes `class="..."` des scripts comme des classes à couvrir, et il
  les aurait signalées sans CSS. Ils s'écrivent donc `class="%s"`, que le
  garde-fou traite comme une famille qu'il ne réclame pas.
- **Hors périmètre, laissés** :
  - `.msn`, l'ancienne liste de `/matchs/` ;
  - la classe `.small` générique ;
  - le sélecteur `.site-footer, .seo-foot` de `floatCta` dans `script.js` ;
  - les règles de grille inertes de `.footer__bottom` (vers la ligne 1182),
    qui visent des classes vivantes ;
  - les 21 pages du laboratoire `astra-motion-lab`, une branche non déployée,
    qui gardent l'ancien en-tête.

Vérifié le 14/09 :

- **Contre-examen avant d'écrire** : 3 angles (usage à l'exécution, logique
  des sélecteurs et cascade, complétude), puis un contradicteur par constat,
  en lecture seule. Aucune règle de la liste n'a été trouvée vivante. Le
  contre-examen a fait ajouter les trois `.footer__brand p.small` que le
  premier motif manquait, et annoncer d'avance les écarts du bloc « petit
  logo ».
- **Empreinte de tout le site** (`.claude/empreinte-site.mjs`) : les 27 pages
  à 390, 768 et 1440 px, soit 81 vues et 30 948 éléments. Pour chacun, et
  pour ses `::before`/`::after`, la boîte et 55 styles calculés, avec l'heure
  figée, le hasard graine et les animations coupées. La passe témoin, à code
  identique, donne 2 écarts de bruit : les marges automatiques d'un `.wrap` de
  `/effectif/`, dont la boîte ne bouge pas. Ils sont écartés.
- **Après la purge : 125 écarts, tous annoncés avant la mesure, et 0
  régression** (`.claude/comparer-empreintes.py`). Ce sont les deux valeurs du
  bloc « petit logo », sur les 25 pages qui portent le pied :
  `grid-template-columns` de `.footer__bottom` à 768 et 1440 px (50 écarts),
  et `justify-self` de `.footer__legal` aux trois largeurs (75 écarts). Un
  écart n'était admis que s'il était seul sur sa ligne : aucune boîte et
  aucune autre propriété n'a bougé.
- **Banc de l'en-tête et du pied** (25 pages à 375, 390, 430 et 1440 px) :
  0 problème.
- **Garde-fous** : `build-css --check` et `bump-assets --check` sont à 0,
  `verifier-liens` et `verifier-jsonld` aussi. `verifier-classes` ne relève
  plus que ses 4 anomalies antérieures.

Pour une prochaine purge, remplacer les écarts `ATTENDUS` de
`comparer-empreintes.py` par ceux qu'on annonce, AVANT de mesurer.

### Intégration et mise en ligne (14/09/2026)

« Intègre la branche au-dessus du reportage […] et mets-le en ligne sur
main » : Alexandre, le même jour.

- **Rebase** des trois commits V184, V184 bis et V185, de `cd91a15` sur le
  commit du reportage (`93babdb`, § 28), dans une copie de travail extraite en
  LF. Les conflits étaient attendus et mécaniques :
  - `MAINTENANCE.md`, trois fois : la fin du § 27 touchait le début du § 28.
    On a gardé le § 27 de la branche, puis le § 28 intact ;
  - `sitemap.xml` : on a gardé la version du reportage, qui porte sa nouvelle
    URL ;
  - les `?v=` de 25 pages et le nom de cache de `sw.js` étaient la seule
    différence entre les deux côtés, vérifiée bloc par bloc. On a gardé la
    version du reportage, puis relancé `bump-assets.py` ;
  - `style.css` et `style.min.css` ont fusionné seuls. La purge est
    complète, le bloc V183 intact, et `build-css.py --check` passe.
- **La chaîne relancée** après le rebase : la page du reportage, antérieure au
  pied commun, le reçoit à son tour. Elle n'a plus de `.seo-foot` ni de
  module en ligne, et les 25 pages portent le même bloc `PIED`.
- **Les trois constats confirmés de la relecture du reportage** étaient
  restés sans suite quand sa session a atteint sa limite. Ils sont appliqués
  (§ 28, « Suites de la relecture »).
- **Relecture contradictoire avant mise en ligne** : 3 angles, puis un
  contradicteur par constat. Les angles : la fidélité de l'intégration, les
  parties du reportage que sa relecture n'avait pas couvertes, et la
  préparation à la production. Rien de bloquant : l'intégration n'a rien
  perdu, d'un côté comme de l'autre. Deux constats mineurs, confirmés, sont
  laissés pour après la mise en ligne (voir « Ce qui reste »).
- **Vérifié avant le push** :
  - tous les contrôles du § 7 ;
  - `set-entete.py --check` à 0 sur 25 pages ;
  - `verifier-classes` réduit à ses 4 anomalies antérieures ;
  - le banc de l'en-tête et du pied, sur 26 pages à 375, 390, 430 et
    1440 px : 0 problème.

### Ce qui reste

- **Le contraste du libellé « Réunion la 1ère • Grand Sport »**, posé sur la
  photo de la façade vidéo (`.vid-facade__src`, 10,6 px). Il passe sous 4,5:1
  sur environ 20 % de son fond, là où il croise le toit clair. La relecture a
  mesuré un correctif : un second dégradé en haut du voile,
  `linear-gradient(to bottom,rgba(6,11,20,.72) 0,rgba(6,11,20,0) 24%)`, posé
  devant celui de `.vid-facade__veil`. Il donne au moins 6,1:1 à 768 et
  1440 px.
- **Le `<title>` de l'article du reportage** fait 57 caractères, au-delà de la
  règle des 52 (voir build-matchs.py). Prévoir un champ `titreSeo` dans
  `data/actualites.json`, lu par `build-actus.py`.
- Facultatif :
  - donner l'heure à l'`uploadDate` du `VideoObject`
    (2026-09-13T19:50:29+04:00) ;
  - un `.gitattributes`, pour garder les `.ics` en CRLF dans le dépôt.

## 28. Le reportage de Réunion la 1ère : une vidéo tierce en façade (14/09/2026)

Branche `feature/season-match-center`, commit séparé.

### Le fait

Le 13 septembre 2026, Réunion la 1ère a publié sur sa page Facebook
(`facebook.com/reunionla1ere`) un sujet de son émission « Grand Sport » :
« La Montagne a désormais son club de basket, le Montagne Basket Club.
Découverte. » — 3 min 14, tourné sous le plateau couvert de Ruisseau Blanc avec
les jeunes du club à l'entraînement. Alexandre a demandé qu'il entre sur le
site « de la manière la plus pertinente possible ».

### Où il vit

| Endroit | Quoi | Fichier |
|---|---|---|
| `/actualites/reportage-reunion-la-1ere-mbc-la-montagne/` | l'article, la vidéo en tête (façade), le `VideoObject` | `data/actualites.json` → `build-actus.py` |
| `/actualites/` | la carte « Médias », en une | idem (généré) |
| accueil, section `#inauguration` | la carte `.lp-media` « Vu dans Grand Sport », qui **mène** à l'article | `index.html` |
| `/club-basket-la-montagne/` | une phrase dans « Un club de quartier » | écrit à la main |
| `/confidentialite/` | le lecteur Facebook dans la liste des services tiers, et la phrase sur les cookies | écrit à la main |

Pourquoi `#inauguration` et pas une section neuve : c'est la section « preuve
locale » du site (`.local-proof`) — le quartier, la mairie, le plateau. Un
reportage de la télévision régionale est la preuve locale la plus forte que
le site ait à montrer. Et la section garde la hauteur que V152b lui a rendue :
une carte compacte qui mène à l'article, pas un second lecteur.

### Pourquoi une façade, et pas l'iframe de Facebook

Le lecteur intégré de Facebook (`plugins/video.php`) pèse plus d'un mégaoctet
de scripts et dépose ses cookies dès le chargement de la page, avant tout
geste du visiteur. La page de confidentialité promet l'inverse (« aucun pixel
ni script de ces plateformes »). On applique donc à la vidéo ce qui est fait
pour la carte Google Maps de l'accueil : une image fixe hébergée ici
(`assets/galerie/mbc-reportage-reunion-la-1ere-*`), un bouton « Regarder le
reportage », et `script.js` (module « Vidéo tierce : injection à la demande »)
n'injecte l'iframe qu'au clic. La largeur du lecteur est mesurée au clic et
passée en `&width=` : c'est ce paramètre, pas la taille de l'iframe, qui fait
cadrer la vidéo chez Facebook. `autoplay=true` est demandé ; Facebook garde
néanmoins son propre bouton de lecture — deux clics, c'est le prix du choix.

Sans JavaScript, la façade reste une image et le lien « Voir sur Facebook »
sous la vidéo mène au reel. L'iframe reprend le `sandbox` de la carte, sans
`allow-forms` (le lecteur n'a pas de formulaire à soumettre), et avec
`allow-presentation` en plus. Le conteneur (`.vid-facade__wrap`) tient sa hauteur
du seul `aspect-ratio:16/9` : rien ne saute quand l'iframe remplace le bouton.

### Le bloc « video » de `data/actualites.json`

Les champs sont décrits en tête de `.claude/build-actus.py`. Trois règles :

- **`affiche`** : les crans doivent exister dans `assets/`, le générateur ne
  fabrique rien. Ici la seule image que Facebook fournit est son `og:image`,
  1000 × 563 : d'où un cran maximal de 1000. Un écran Retina de 860 px de
  large la verra un peu douce — c'est la source, pas un réglage.
- **`datePublication`** : la date de mise en ligne **chez la source**, relevée
  et jamais supposée. Sans elle, `build-actus.py` n'écrit pas de `VideoObject`
  (`uploadDate` est obligatoire pour Google) et le dit à la console. Ici : le
  champ `creation_time` de la page du reel, 1789314629, soit le 13/09/2026 à
  19 h 50, heure de La Réunion.
- Si le bloc est **le premier du corps**, sa façade prend la place de l'image
  de tête. L'`image` de l'article garde ses autres rôles : carte de la liste,
  `og:image`, `NewsArticle.image`.

### Données structurées

`NewsArticle.video` porte le `VideoObject` imbriqué : `name`, `description`,
`thumbnailUrl` (notre vignette), `uploadDate`, `duration` (`PT3M14S`),
`embedUrl`, `url`, et un `publisher` Organization « Réunion la 1ère ». Le
publisher est bien la chaîne, pas le club : l'article est à nous, la vidéo non.

### Pour ajouter une autre vidéo

1. La vignette : `assets/galerie/<base>-<cran>.webp` pour chaque cran, plus
   `<base>.jpg` en repli (Pillow, WEBP qualité 45 comme `build-vignettes.py`).
   Pas de script dédié : trois lignes de Python suffisent, et une vidéo de
   temps en temps ne justifie pas un générateur de plus.
2. Le bloc dans `data/actualites.json`, sa source dans `_sources`, puis la
   chaîne : `build-actus.py` → `build-css.py` (si la feuille a changé) →
   `build-sitemap.py` → `bump-assets.py`, et les contrôles du § 7.
3. Si la source n'est pas Facebook : `embed` change, le module de `script.js`
   non (il ne connaît que `data-embed`). Adapter la note « Lecteur Facebook »
   dans `video_html()` — écrite en dur, volontairement, tant qu'il n'y a
   qu'une source — et la page de confidentialité.

### Vérifié le 14/09

- Chaîne complète relancée : 27 pages re-versionnées, sitemap à 26 URL,
  `set-entete.py --check` sans écart.
- `verifier-jsonld.py` : 29 pages, 0 erreur, 0 avertissement.
  `verifier-classes.py` : les trois `.sponsor-pack--*` connus, rien d'autre.
  `verifier-liens.py` : `_banc.html` seul orphelin (page de banc, hors git).
  `build-css.py --check` et `bump-assets.py --check` en 0.
- Chrome, 1538 px de large : l'article (façade, puis lecteur Facebook au vrai
  clic, dans le cadre 16/9), la liste des actualités (la carte « Médias » en
  une), la carte de l'accueil dans `#inauguration` (vue dans une iframe de
  1240 px : `_banc-video-desktop.html`, hors git).
- À 390 px, dans des iframes (`_banc-video.html`, hors git) : la façade tient
  (kicker, bouton, libellé, note), la carte « Médias » passe en une colonne,
  la page club et la liste sont intactes.

### Suites de la relecture (appliquées à l'intégration, 14/09)

La relecture contradictoire de ce commit s'était arrêtée à la limite de
session. Trois constats étaient confirmés, mais pas appliqués. Ils le sont
au moment de l'intégration sur `main` (§ 27, « Intégration et mise en
ligne ») :

- `/confidentialite/` : la « Dernière mise à jour » passe au 14 septembre
  2026, pour l'ajout du lecteur vidéo de Facebook. La page promet en effet
  que toute modification substantielle y sera visible ;
- les mentions légales de l'accueil (`#legal`) disent que les images tirées
  du reportage restent la propriété de Réunion la 1ère (France Télévisions).
  La légende de la vidéo porte aussi « Image d'aperçu : Réunion la 1ère. » ;
- le paragraphe sur le `sandbox` de l'iframe vidéo, plus haut, décrit
  désormais l'attribut tel qu'il est.

Les angles « accessibilité », « JavaScript » et « CSS » de cette relecture
n'avaient pas tourné. Ils ont été repris avant la mise en ligne, sans
constat bloquant. Deux points restent à traiter, le contraste du libellé de
la façade et la longueur du titre (§ 27).

### Ce qui reste

- La vignette est celle de Facebook (1000 px). Si la chaîne publie le sujet
  sur `la1ere.franceinfo.fr`, une image plus large et un lien vers son article
  seraient à ajouter (`sourceUrl` pointe pour l'instant sur la page Réunion du
  site de la chaîne).
- Si la chaîne retire le reel, la façade reste (image et lien) mais le
  lecteur affichera « Vidéo non disponible ». À vérifier de temps en temps,
  comme n'importe quel lien externe.

## 29. Une dérogation : le J5 contre Sainte-Rose se joue à domicile (14/09/2026)

« Le match du 23 octobre vs Ste Rose se jouera à domicile » : Alexandre, le
14/09. Le PDF de la Ligue (édition du 25/08) nomme Sainte-Rose en premier, et
la place donc là-bas. L'article 4 du règlement autorise ces inversions jusqu'à
cinq jours avant la rencontre.

**Le problème** : le site tient le camp de deux sources.
- `data/matchs.json` produit les fiches, `/matchs/` et le Match Center.
- Le PDF produit le tableau du calendrier de l'accueil, le décompte « dont N à
  domicile » et l'affiche.

`set-calendrier-prm.py` refusait de publier dès que les deux divergeaient :
toute la chaîne s'arrêtait.

**Le mécanisme** :
- dans `data/matchs.json`, la rencontre est modifiée comme n'importe quel match
  à domicile (`domicile`, `lieu`, `entreeLibre`, `benevoles`, `intro`). Elle
  reçoit en plus un champ `derogation` :
  `{ "domicile": true, "le": "…", "source": "…" }` ;
- `appliquer_derogations()`, dans `set-calendrier-prm.py`, reporte ce champ sur
  la liste lue dans le PDF : le tableau, le décompte, les postes bénévoles et
  l'affiche suivent. Une dérogation sans `source`, sans date `le` au format
  AAAA-MM-JJ, ou qui contredit sa rencontre, est refusée ;
- le jour où un PDF réédité intègre l'inversion, le script le signale, et le
  champ peut alors être retiré ;
- un PDF plus récent que la dérogation, qui la contredit encore, est signalé
  par un « !! » : la Ligue ne l'a peut-être pas enregistrée, ou elle a été
  annulée ;
- pour l'annuler : retirer `derogation`, remettre la rencontre comme avant, et
  relancer la même chaîne ;
- `--archive` redessine l'affiche d'elle-même dès qu'un camp change par
  rapport au tableau déjà en ligne, que la dérogation soit ajoutée ou annulée.
  `--affiche` force ce dessin ;
- la chaîne complète : `build-og-matchs.py` (l'image de partage dépend du
  camp), puis `set-calendrier-prm.py --archive`, `bump-assets.py` et
  `build-sitemap.py` ;
- seul le camp est pris en charge. Une dérogation d'horaire demanderait la même
  chose pour `heure`.

**Ce qui a changé pour le J5** :
- **La fiche** : « MBC vs Sainte-Rose », l'entrée libre, les trois postes
  bénévoles et un fichier `.ics` (seuls les matchs à domicile en ont).
- **L'image de partage et l'affiche du calendrier** ; l'affiche annonce
  « 5 matchs à domicile ».
- **Le tableau et le Match Center de l'accueil, et `/matchs/`**.
- **La fiche du J6** : « cinquième — et dernière — rencontre à domicile ».
- **L'article « Le calendrier de la phase 1 »** : cinq matchs à domicile,
  deux déplacements, et une phrase sur l'inversion (`dateModifiee` au 14/09).
- **`.claude/benevoles-matchs.json`** : la date est ajoutée, avec ses postes à
  pourvoir.

Vérifié le 14/09 :
- tous les contrôles du § 7 ;
- la présence correcte du J5 dans chaque page produite, en 13 points : ligne
  de l'accueil, décomptes, fiche, données structurées, `.ics`, `/matchs/`,
  article et fiche du J6 ;
- l'affiche et l'image de partage, contrôlées à l'œil.

**Relecture contradictoire** : 2 angles et 6 agents, en lecture seule. Ils
n'ont rien trouvé sur le site. Cinq retouches du mécanisme en sont sorties :
- l'affiche redessinée dès qu'un camp change ;
- un message exact quand la rencontre et sa dérogation divergent ;
- la date `le` contrôlée et comparée à l'édition du PDF ;
- la recette complète, avec `build-og-matchs.py` ;
- une phrase du README qui comptait « trois » déplacements.

**À savoir** : le script affiche une alerte, « encart « prochain
rendez-vous » : data-match-date introuvable ». Elle est ancienne et sans
effet : l'encart qu'elle vérifiait a disparu avec le Match Center (§ 26).

---

## 30. Les photos d'un soir de match dans « Sur le terrain » (15/09/2026)

« ajoute ces photos dans sur le terrain » : Alexandre, le 15/09, avec onze
photos. Dix sont publiées : les seniors le soir de la J1, le 11/09 (victoire
73-52 contre Sainte-Suzanne, au Gymnase de La Montagne). Leur date de prise de
vue (EXIF) le confirme. L'heure, elle, ne tranche rien : l'appareil l'enregistre
avec un décalage de +05:00, quand La Réunion est à +04:00. Aucun `alt` ne dit
donc « pendant le match ».

**La onzième est écartée.** `DSC048468.png` fait 1024 × 1536, n'a pas d'EXIF,
et aucun original d'appareil ne lui correspond. Sous le numéro de son maillot,
l'inscription est illisible, là où le vrai maillot du n° 12 porte « Ansanm nou
lé pli for » : c'est une image retouchée ou régénérée par une IA, et le § 17.4
les exclut du site. Si l'original existe, il suffit de l'ajouter au JSON.

**Où.** Dans `#galerie`, entre le titre de la section et le zoom parallaxe.
- Pas dans le zoom : ses six tuiles ont chacune une place et une géométrie
  calculées (§ 16).
- Pas dessous : le zoom atterrit plein cadre sur « Le cercle d'avant-séance »,
  qui ouvre sur #parents.

**La chaîne.**
- `data/galerie-match.json` : une entrée par soirée, la plus récente en
  premier. Chacune porte le slug de la rencontre, un titre, et ses photos dans
  l'ordre de la soirée. La date, l'adversaire, le score et le lieu sont lus
  dans `data/matchs.json`.
- `python .claude/build-galerie-match.py --images <dossier des originaux>`
  crée les dérivés manquants dans `assets/galerie/`, puis réécrit le bloc
  entre les marqueurs `galerie:soirees` d'`index.html`. Les dérivés : AVIF 45
  et WebP 66, aux crans 360/560/760/1200 en portrait et 560/760/1200/1800 en
  paysage, plus un JPEG 80 au plus grand cran.
- Sans `--images`, le script ne réécrit que le bloc. `--check` sort en 1 si le
  bloc publié n'est plus celui du JSON.
- Puis `bump-assets.py`.
- `build-matchs.py` (et donc `set-calendrier-prm.py`) réécrit aussi le bloc,
  par `regenerer()` : un score corrigé dans `data/matchs.json` change la
  légende du même coup. Un échec y est annoncé par un « !! », sans bloquer la
  publication d'un résultat.
- `--images` n'exige que les originaux des photos pas encore publiées.

**Les règles.**
- Un nom de fichier publié ne sert qu'une fois : une photo remplacée prend un
  nouveau nom (règle du cache). Un dérivé existant n'est jamais réécrit.
- Les dérivés sont vidés de toutes leurs métadonnées : boîtier, réglages,
  GPS éventuel. Vérifié sur les 90 fichiers.
- Le script signale deux cas : un original sans date de prise de vue (c'était
  le cas du PNG), et une photo prise un autre jour que la rencontre.
- Les `alt` décrivent ce que la photo montre. Un joueur n'est nommé que si son
  maillot l'identifie et que l'effectif concorde : c'est le cas de Kevin Nazir
  (floqué NAZIR, n° 11). Les autres sont désignés par leur numéro. Le flocage
  du n° 1 et celui du n° 34 ne reprennent pas le nom inscrit dans
  `data/effectif.json`, et le n° 12 de l'effectif, David Nugent, a rejoint le
  club le 13/09, deux jours après le match.

**La mise en page** (style.css, bloc « GALERIE — les soirées photo »).
- Dès 880 px, des rangées justifiées : chaque photo prend pour `flex-grow` son
  rapport largeur/hauteur (`--r`), avec une base nulle. Aucune photo n'est
  recadrée. Deux rangées (6 + 4), de 273 et 252 px de haut à 1440 px, de 219
  et 203 px à 1024.
- En dessous, une bande qui défile au doigt (`scroll-snap`). Les photos y
  mesurent min(70vw, 420px) de haut, et un paysage est borné à la largeur de
  l'écran.
- Le générateur écrit les `sizes` d'après cette géométrie (constantes en tête
  du script) : si l'une change, l'autre aussi. Mesuré : le 360 pour un
  portrait de 175 px à DPR 2, le 760 pour un paysage de 338 px.
- Le filet de 1 px est un `::after` posé par-dessus la photo. En bordure, il
  décalait de 1,7 px le bas des paysages par rapport à celui des portraits.

**La visionneuse** (`#lightbox`, script.js). Elle n'avait plus aucun
déclencheur sur le site.
- Un déclencheur qui porte `data-lightbox-group` l'ouvre en mode photo : la
  photo entière, un compteur, deux flèches, les touches ← →, le balayage du
  doigt. À la fermeture, le focus revient sur la photo regardée.
- Sans groupe, le mode affiche ne change pas.
- Premier défaut corrigé au passage : avec `visibility .3s`, la visionneuse
  était encore `hidden` quand le script lui donnait le focus, qui restait
  derrière elle. `.lightbox.show` bascule désormais sans transition.
- Second défaut : pas encore chargée, l'image mesurait 0 × 0. En mode photo,
  sa boîte est désormais calculée d'après `--lb-r`, et l'image se charge sans
  attendre (`loading` passe à `eager` à l'ouverture).

**Au passage, le cadre du zoom** (style.css, bloc « GALERIE — zoom
parallaxe »). En mode zoom, chaque tuile est un calque plein cadre. La règle
V17 `.g-tile{box-shadow:…, var(--bevel) !important}` l'emportait sur le
`box-shadow:none` du zoom : le liseré intérieur des six calques traçait un
filet de 1 px tout autour de la scène, le « cadre de fenêtre » que le § 16
croyait retiré. Il était déjà là sur main, mais il tombait désormais juste sous
les photos. Correctif : `box-shadow:none!important`, comme pour `border`.
Vérifié dans Chrome, à 1440 et à 390 px : le filet a disparu.

**Relecture contradictoire** : 14 agents. Les `alt` ont été confrontés aux
images : 9 sur 10 tenaient. « pendant le match » a été retiré du regroupement,
que l'image ne prouve pas, et « suivent le match » et « garnies » du banc.
Huit défauts de code, tous confirmés par un sceptique, tous corrigés :
- la page défilait derrière la visionneuse ouverte : `body{overflow:hidden}`
  ne tient pas quand `<html>` est en `overflow-x:clip`. Le verrou est posé sur
  la racine (`html.lb-open`), comme celui du menu, barre de défilement
  compensée ;
- pendant le chargement, le navigateur peint encore la photo précédente dans
  la nouvelle boîte, où elle était étirée : `object-fit:contain`, et les deux
  voisines sont préchargées, plus seulement la suivante ;
- `button:focus-visible{border-radius:4px}` (0,1,1) ôtait leurs coins aux
  photos et aux flèches au clavier : l'arrondi est reposé dans leur propre
  `:focus-visible` ;
- à l'ouverture, le lecteur d'écran ne disait ni la photo ni son rang : le
  dialogue porte `aria-describedby` vers le compteur ;
- à l'impression A4 portrait, la bande coupait 7 photos sur 10 : les rangées
  justifiées valent aussi pour `print` ;
- le score de la légende n'était remis à jour par aucune chaîne, et `--images`
  réclamait les originaux de toutes les soirées : voir « La chaîne ».

**Le poids.** 90 fichiers, 5,9 Mo dans le dépôt. Un visiteur ne charge que les
vignettes, en différé, sous la ligne de flottaison : 123 Ko sur ordinateur,
142 Ko sur un téléphone à DPR 2. Une photo ouverte dans la visionneuse pèse
de 59 à 173 Ko.

**Vérifié le 15/09.**
- Tous les contrôles du § 7. `verifier-liens` ne signale que les `_banc*.html`,
  ignorés par git, et `verifier-classes` que les 4 anomalies connues.
- Des mesures dans le panneau à 375, 768, 1024 et 1440 px : rangées alignées
  au dixième de pixel, aucun débordement horizontal. Le zoom garde sa course
  de 240vh.
- La visionneuse : ouverture, flèches, touches, passage de la dernière photo à
  la première, Échap, et retour du focus.
- Dans Chrome piloté en CDP, à 1440 × 900 et 390 × 844 : de vraies touches
  (Entrée, Tab, →, Échap), un vrai balayage du doigt, et une vraie molette,
  visionneuse ouverte, qui ne fait plus bouger la page. Le lecteur d'écran lit
  bien la description. Les coins restent arrondis au focus. En impression A4
  portrait, les dix photos tiennent dans la largeur. Le zoom avance toujours
  (`--p` = 0,50 à mi-course).

**En ligne le 15/09** (`main` = `59c415f`). GitHub Pages servait la nouvelle
version dès le premier contrôle. La production a été vérifiée sous trois angles
indépendants, chaque anomalie étant soumise à un sceptique :
- le banc navigateur, rejoué sur https://mbc974.com : toutes les valeurs du
  banc local, 0 erreur de console ;
- le balayage de régression : les 32 pages en 200, identiques octet pour
  octet au commit, 383 ressources sur 383 en 200 au bon type MIME, les 76
  blocs JSON-LD lisibles, aucun débordement horizontal ;
- le visiteur revenant : aucun mélange d'ancien et de nouveau en ligne. Le CDN
  de GitHub Pages ignore bien le `?v=`, mais chaque déploiement purge son
  bord : l'anomalie a été réfutée.

Deux défauts confirmés, corrigés dans la foulée :
- « Fermer » prenait l'anneau de focus orange de la règle de repli, et les
  flèches le bleu glacier de la convention unique (`--focus-*`). Les deux
  partagent désormais la même règle.
- `sw.js` précachait l'accueil À TRAVERS le cache HTTP du navigateur
  (max-age=600). Un visiteur revenu dans les dix minutes suivant un
  déploiement faisait donc précacher l'ancien accueil, dont la feuille et le
  script partaient avec l'ancien cache : hors ligne, la page sortait sans
  style. Le défaut a été reproduit sur l'origine réelle. Le précache se fait
  désormais en `cache:'reload'`, et le repli du stale-while-revalidate rend
  `Response.error()` au lieu d'`undefined`.
