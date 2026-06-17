# MBC — La Montagne Basket Club

Site officiel du **MBC La Montagne Basket Club**, club de basket de La Montagne / Saint-Denis, à La Réunion (974).

Site statique (HTML / CSS / JavaScript), **sans build ni dépendance** : il se déploie tel quel.

---

## Mise en ligne sur Netlify

1. Connectez-vous sur [app.netlify.com](https://app.netlify.com).
2. Glissez-déposez **le contenu de ce dossier** (ou le `.zip`) dans la zone de déploiement.
3. C'est en ligne. `index.html` étant à la racine, aucune configuration n'est nécessaire.

Le fichier `netlify.toml` configure automatiquement le cache des images et quelques en-têtes de sécurité.

> Après une mise à jour, faites un rafraîchissement forcé (`Ctrl + F5` / `Cmd + Shift + R`) pour voir la nouvelle version.

---

## Structure du projet

```text
/
├── index.html              Page unique du site
├── style.css               Styles
├── script.js               Interactions (menu, reveal, lightbox, formulaire…)
├── 404.html                Page d'erreur de marque (servie par Netlify)
├── robots.txt              Indexation moteurs de recherche
├── sitemap.xml             Plan du site
├── site.webmanifest        Manifeste PWA
├── netlify.toml            Cache + en-têtes de sécurité
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
    └── documents/          Dossier de partenariat (PDF)
```

---

## Modifier le contenu

Tout le contenu se trouve dans `index.html` :

- **Textes** : modifiez directement le texte entre les balises.
- **Créneaux / calendrier** : section `id="calendrier"`.
- **Sponsors** : ajoutez le logo dans `assets/sponsors/` puis dupliquez une carte dans la section `id="partenaires"`.
- **Maillots / galerie** : remplacez les images dans `assets/maillots/` et `assets/galerie/` (gardez les mêmes noms de fichiers).
- **Coordonnées / email** : recherchez `mbc.re974@gmail.com` dans `index.html`.

---

## Images & performance

La plupart des images utilisent le schéma `<picture>` avec trois formats :

- **AVIF** (servi en priorité, le plus léger) ;
- **WebP** (repli moderne) ;
- **JPG / PNG** (repli universel).

Pour remplacer une image avec ses 3 formats, conservez les mêmes noms de base. Pour les maillots et la galerie, un simple `<img>` JPG est utilisé (fiabilité maximale).

Cibles : chargement différé (`loading="lazy"`), dimensions `width`/`height` définies (zéro décalage de mise en page), images optimisées.

---

## SEO

- Balises Open Graph / Twitter Cards.
- Données structurées **Schema.org** (`SportsClub` + `FAQPage`).
- `sitemap.xml`, `robots.txt`, URL canonique, `lang="fr"`.

> Avant la mise en production sur le domaine définitif, vérifiez que le domaine utilisé dans `sitemap.xml`, `robots.txt` et les balises Open Graph (`https://mbc974.re`) correspond bien à votre domaine final.

---

*Passion · Respect · Solidarité · Engagement*
