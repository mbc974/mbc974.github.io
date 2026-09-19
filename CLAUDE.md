# Claude Instructions — MBC974 Website

Tu travailles sur le site officiel du La Montagne Basket Club.

Objectif : améliorer le site sans casser sa structure ni ses chemins de fichiers.

## Commence par lire AGENTS.md
`AGENTS.md` porte les règles du dépôt (structure, assets, pages générées,
publication). Elles ne sont pas recopiées ici. **Lis-le avant de modifier quoi
que ce soit.** `MAINTENANCE.md` est le mode d'emploi de la chaîne de génération
et des garde-fous.

Trois règles ne souffrent aucune exception, rappelées ici parce qu'une erreur
dessus se voit en production :
1. Ne jamais casser les chemins `assets/...`.
2. Ne pas éditer à la main une page marquée « GÉNÉRÉ » : on change `data/*.json`
   puis on relance le générateur.
3. Site statique, sans build ni framework : aucune dépendance lourde.

## Priorités
1. Garder le site simple, rapide et maintenable.
2. Améliorer le rendu visuel premium/sportif.
3. Optimiser le responsive mobile.
4. Renforcer le SEO local : La Montagne, Saint-Denis, La Réunion, basket.

## Avant toute modification
- Lire les fichiers concernés (`index.html`, `style.css`, `script.js`, ou la
  source `data/*.json` s'il s'agit d'une page générée).
- Identifier les chemins d'images utilisés.
- Proposer un plan court avant de modifier.
- Éviter les refontes inutiles si une correction ciblée suffit.

## Après modification
- Résumer les fichiers modifiés.
- Expliquer ce qui a été amélioré.
- Signaler les points à vérifier visuellement.
