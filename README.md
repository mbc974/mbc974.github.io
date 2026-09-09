# MBC — La Montagne Basket Club

Site officiel du **MBC La Montagne Basket Club**, club de basket de La Montagne / Saint-Denis, à La Réunion (974).

Site **statique** (HTML / CSS / JavaScript), **sans build ni dépendance** : les fichiers sont servis tels quels.

---

## Hébergement & mise en ligne

Le site est publié avec **GitHub Pages**, depuis la branche `main`, **à la racine du dépôt** (`/`).
Le domaine `mbc974.com` est configuré via le fichier `CNAME`.

**Pour mettre à jour le site :** committez et poussez sur `main`. GitHub Pages republie automatiquement la racine.

```bash
git add -A
git commit -m "Mise à jour du contenu"
git push
```

> Après une mise à jour, faites un rafraîchissement forcé (`Ctrl + F5` / `Cmd + Shift + R`) pour voir la nouvelle version.

> ⚠️ GitHub Pages n'applique **pas** d'en-têtes HTTP personnalisés (cache, sécurité). Le versionnage du CSS/JS se fait via le paramètre `?v=…` dans `index.html` / `adhesion.html` (à incrémenter quand on modifie `style.css` ou `script.js`).

---

## Structure du projet

```text
/
├── index.html              Page d'accueil
├── adhesion.html           Page adhésion 2026/2027
├── 404.html                Page d'erreur de marque
├── style.css               Styles
├── script.js               Interactions (menu, reveal, lightbox, formulaire…)
├── robots.txt              Indexation moteurs de recherche
├── sitemap.xml             Plan du site
├── site.webmanifest        Manifeste PWA
├── CNAME                   Domaine personnalisé (mbc974.com)
├── .nojekyll               Désactive le traitement Jekyll de GitHub Pages
├── README.md               Ce fichier
├── data/                   Sources JSON des pages générées (matchs, actualités, créneaux)
├── creneaux/               GÉNÉRÉ — planning hebdomadaire de toutes les catégories
├── matchs/                 GÉNÉRÉ — /matchs/ + une page par rencontre
├── actualites/             GÉNÉRÉ — /actualites/ + une page par article
└── assets/
    ├── logos/              Logo du club
    ├── icons/              Favicon
    ├── sponsors/           Logos des partenaires
    ├── staff/              Photos de l'encadrement
    ├── maillots/           Maillots domicile / extérieur
    ├── galerie/            Photos de matchs / équipe
    ├── flyers/             Affiches (recrutement, bénévoles, service civique)
    ├── images/             Visuels divers (créneaux, partenariat, partage social)
    ├── videos/             Vidéo d'adhésion + posters
    ├── fonts/              Polices auto-hébergées (14 woff2) — plus rien chez Google
    └── documents/          PDF (partenariat, calendrier officiel) + .ics des matchs
```

Les dossiers marqués **GÉNÉRÉ** ne se modifient pas à la main : on édite le JSON
correspondant dans `data/`, puis on relance le script indiqué dans
[MAINTENANCE.md](MAINTENANCE.md#1-bis-les-pages-générées--on-modifie-le-json-jamais-le-html).

---

## Modifier le contenu

- **Textes** : modifiez directement le texte entre les balises dans `index.html` / `adhesion.html`.
- **Créneaux / catégories** : `data/creneaux.json`, puis `python .claude/build-creneaux.py`. Un seul fichier alimente le planning de l'accueil, la page `/creneaux/`, les huit cartes catégories, les six panneaux du sélecteur d'âge **et** le bloc `openingHoursSpecification` du JSON-LD. Il n'y a plus rien à mettre à jour « en cohérence » : c'est le script qui s'en charge.
- **Matchs** : `data/matchs.json`, puis `python .claude/build-matchs.py`. ⚠️ Le `slug` d'une rencontre **est** son URL publique : le changer casse un lien déjà partagé.
- **Actualités** : `data/actualites.json`, puis `python .claude/build-actus.py`. Chaque article doit avoir sa source citée dans le bloc `_sources` du fichier — on ne publie rien qu'on ne puisse pas montrer.
- **Staff** : photos dans `assets/staff/`, noms/rôles affichés via `.team__cap` (et déclarés dans le `member` du JSON-LD).
- **Sponsors** : ajoutez le logo dans `assets/sponsors/` puis dupliquez une carte dans la section `id="partenaires"`.
- **Maillots / galerie** : remplacez les images dans `assets/maillots/` et `assets/galerie/` (gardez les mêmes noms de fichiers).
- **Coordonnées / email** : l'email public est `contact@mbc974.com` (présent dans `index.html`, `adhesion.html`, le footer, les mentions légales et le JSON-LD).

---

## Images & performance

La plupart des images utilisent le schéma `<picture>` avec jusqu'à trois formats : **AVIF** (le plus léger), **WebP** (repli moderne), **JPG / PNG** (repli universel). Pour remplacer une image, conservez les mêmes noms de base.

Bonnes pratiques en place : chargement différé (`loading="lazy"`), dimensions `width`/`height` définies (zéro décalage de mise en page), image LCP préchargée.

Les **portraits du staff** et les **photos de catégories** sont déclinés en plusieurs largeurs par
`python .claude/build-vignettes.py`, qui recâble aussi le `srcset`/`sizes` de `index.html`. Avant lui,
un téléphone téléchargeait 760 px de large pour 274 affichés : les six portraits pesaient 593 Ko.
On remplace le `.jpg`, on relance le script — on ne retouche jamais un cran à la main.

Les variantes du hero **ne se retouchent pas une par une** : `python .claude/build-hero.py` les
régénère toutes (panoramique + recadrage mobile, AVIF et WebP) à partir de l'original conservé
dans `.claude/sources/`. Réencoder à partir d'un fichier déjà compressé dégrade l'image à chaque
passage — c'est pour l'éviter que l'original est versionné.

---

## SEO & GEO

- Balises Open Graph / Twitter Cards, URL canonique, `lang="fr"`.
- Données structurées **Schema.org** : `SportsClub` (avec `@id`, `geo`, `openingHoursSpecification`, `member`), `VideoObject`, `FAQPage`, `BreadcrumbList`, `ItemList`, `NewsArticle`.
- **`SportsEvent` : un par rencontre, sur SA page** (`/matchs/<slug>/`), et nulle part ailleurs. La page d'accueil ne déclare qu'une `ItemList` qui pointe vers elles. Deux nœuds `Event` pour un même match sur deux URL différentes, c'est de la duplication : Google choisit alors lui-même la page à montrer.
- Aucun `SportsEvent` n'est écrit quand le lieu est inconnu — un `Event` sans `location` est une **erreur** Search Console, pas un avertissement. Les trois matchs en déplacement n'en ont donc pas.
- `sitemap.xml`, `robots.txt`.
- Le domaine de référence est **`https://mbc974.com`** (canonical, sitemap, Open Graph, JSON-LD). Les comptes `@mbc974.re` sont les **réseaux sociaux** (à ne pas confondre avec le domaine web).

---

*Passion · Respect · Solidarité · Engagement*
