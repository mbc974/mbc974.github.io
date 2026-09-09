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
| Un article d'actualité | `data/actualites.json` | `python .claude/build-actus.py` |
| Un créneau d'entraînement, une catégorie, un tarif | `data/creneaux.json` | `python .claude/build-creneaux.py` |
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
**Caveat 700** (Google Fonts, SIL OFL 1.1), convertis en chemins SVG une fois pour toutes et
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

### L'affiche des créneaux (`index.html`, section `#calendrier`)

`assets/images/creneaux.avif` annonce l'entraînement Seniors/U18 du **lundi à
20h30–22h00** ; `data/creneaux.json`, le planning, les `openingHoursSpecification`
et la page basket adulte disent tous **19h00–20h30**. Elle place aussi le créneau
Seniors du mercredi au Terrain Ruisseau Blanc (il est au Gymnase) et publie une
adresse e-mail — `mbc974.re@gmail.com` — qui n'apparaît nulle part ailleurs.

**Pour la rétablir** : refaire l'affiche depuis `data/creneaux.json`, la déposer
sous un **nouveau nom de fichier** (règle du § 1 : nouvelle image = nouveau nom),
puis décommenter le bouton et corriger ses deux `data-lightbox-*`.

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
- **Deux joueurs portent le numéro 10** (Guillaume Moine et Hakim Derras).
  C'est l'état constaté sur les affiches ; il est repris tel quel. C'est au
  club de trancher, pas au dépôt.

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
