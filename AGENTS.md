# MBC974 Website — Agent Instructions

Ce repository contient le site officiel de La Montagne Basket Club.
**C'est la référence commune à tous les agents.** `CLAUDE.md` ne redit pas ces
règles, il y renvoie et ajoute sa méthode de travail.

## Structure
- Site statique uniquement : HTML, CSS, JavaScript.
- Pas de framework.
- Pas de build.
- Le fichier principal est `index.html`.
- Les styles sont dans `style.css`.
- Les scripts sont dans `script.js`.
- Tous les médias doivent rester dans `assets/`.

## Règles importantes
- Ne jamais casser les chemins des assets.
- Garder `index.html`, `style.css`, `script.js` et `assets/` à la racine.
- Ne pas déplacer les images sans mettre à jour tous les liens.
- Ne pas renommer les fichiers d'images existants sans raison.
- Préserver un rendu premium, moderne, sportif et local Réunion.
- Optimiser mobile en priorité.
- Vérifier que les liens d'adhésion, de préinscription et de contact restent visibles.
- Ne pas ajouter de dépendances lourdes ou de framework.

## Pages générées : ne pas les éditer à la main
Une partie du site est **produite par des scripts** à partir de `data/*.json` :
créneaux, matchs, actualités, effectif, galerie, sitemap. Le README les marque
« GÉNÉRÉ » dans l'arborescence.

Sur ces pages, on modifie **la source JSON puis on relance le générateur** ;
une retouche directe du HTML est écrasée à la génération suivante.

L'outillage vit dans `.claude/` (`build-*.py`, `set-*.py`, `verifier-*.py`,
`bump-assets.py`). **`MAINTENANCE.md` est le mode d'emploi** : ordre des
scripts, garde-fous, pièges connus. Le consulter avant de toucher à une page
générée ou à la chaîne elle-même.

Après une modification de `style.css` ou `script.js`, le versionnage `?v=…`
doit être repassé (`bump-assets.py`), sinon les visiteurs gardent l'ancien
fichier en cache.

## Publication
Le site est publié via GitHub Pages depuis :
- branche : `main`
- dossier : `/root`

Après chaque modification, vérifier :
- que la page d'accueil charge correctement ;
- que les images s'affichent ;
- que les boutons CTA fonctionnent ;
- que le site reste responsive mobile.
