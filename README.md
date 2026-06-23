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
    └── documents/          Dossier de partenariat (PDF)
```

---

## Modifier le contenu

- **Textes** : modifiez directement le texte entre les balises dans `index.html` / `adhesion.html`.
- **Créneaux / calendrier** : section `id="calendrier"` dans `index.html`. ⚠️ Pensez à mettre à jour en cohérence le bloc `openingHoursSpecification` du JSON-LD (dans le `<head>`).
- **Staff** : photos dans `assets/staff/`, noms/rôles affichés via `.team__cap` (et déclarés dans le `member` du JSON-LD).
- **Sponsors** : ajoutez le logo dans `assets/sponsors/` puis dupliquez une carte dans la section `id="partenaires"`.
- **Maillots / galerie** : remplacez les images dans `assets/maillots/` et `assets/galerie/` (gardez les mêmes noms de fichiers).
- **Coordonnées / email** : l'email public est `contact@mbc974.com` (présent dans `index.html`, `adhesion.html`, le footer, les mentions légales et le JSON-LD).

---

## Images & performance

La plupart des images utilisent le schéma `<picture>` avec jusqu'à trois formats : **AVIF** (le plus léger), **WebP** (repli moderne), **JPG / PNG** (repli universel). Pour remplacer une image, conservez les mêmes noms de base.

Bonnes pratiques en place : chargement différé (`loading="lazy"`), dimensions `width`/`height` définies (zéro décalage de mise en page), image LCP préchargée.

---

## SEO & GEO

- Balises Open Graph / Twitter Cards, URL canonique, `lang="fr"`.
- Données structurées **Schema.org** : `SportsClub` (avec `@id`, `geo`, `openingHoursSpecification`, `member`), `VideoObject`, `FAQPage`, `BreadcrumbList`.
- `sitemap.xml`, `robots.txt`.
- Le domaine de référence est **`https://mbc974.com`** (canonical, sitemap, Open Graph, JSON-LD). Les comptes `@mbc974.re` sont les **réseaux sociaux** (à ne pas confondre avec le domaine web).

---

*Passion · Respect · Solidarité · Engagement*
