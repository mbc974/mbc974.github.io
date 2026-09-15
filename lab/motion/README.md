# MBC Motion Lab

Expérimentation sur `astra-motion-lab`, issue du dépôt réel `mbc974/mbc974.github.io`, base `01851f0e1c15d9e5849adcbc55e5520d5c3ef9b7`. Aucun fichier de production modifié, aucune fusion sur main.

## Ouvrir les concepts

Après récupération de la branche, lancer depuis la racine :

```sh
npm run dev
```

Aucune installation npm nécessaire ; Node suffit. Ouvrir `http://localhost:4173/lab/motion/`. Le serveur est un outil local, pas une nouvelle infrastructure de production. Le lab n'est pas déployé sur mbc974.com.

- `/lab/motion/editorial/` : A, composition éditoriale blanche, photographie et hiérarchie.
- `/lab/motion/sport/` : B, affiche sportive et scoreboard.
- `/lab/motion/court/` : C, terrain SVG, trajectoire et ballon liés au scroll, relief abstrait.

Les liens « Voir le match » conduisent à sept vraies fiches par concept. Les inscriptions, actualités, effectifs détaillés et autres destinations conservent les ressources et parcours du site existant. Le contact du lab est un lien vers le formulaire original ; aucune clé du service de formulaire n’est recopiée dans les expériences.

## Documents

[Audit](AUDIT.md) · [Motion Design System](DESIGN-SYSTEM.md) · [QA et performance](QA.md) · [Inventaire exact](FILES.txt)

| Direction | Avantage | Limite | Complexité |
|---|---|---|---|
| A | Lisibilité, respiration, photographie au premier plan | Moins événementielle ; vigilance sur les fonds clairs hérités | Faible à moyenne |
| B | Identité de compétition, prochain match immédiat | Risque de répétition des grands chiffres | Moyenne |
| C | Signature basket reconnaissable, continuité terrain→match | Orchestration et vérifications Safari/mobile supplémentaires | Moyenne à élevée |

**Recommandation : A comme structure, B pour les rencontres, une seule séquence C comme signature.** Les trois variantes sont des explorations comparables ; les additionner intégralement alourdirait le récit.

## Sources et fichiers concernés

Tous les ajouts sont listés dans `FILES.txt`. Aucun média copié ou modifié.

| Fichier / groupe | Rôle |
|---|---|
| `lab/motion/index.html` | Hub, comparaison et accès aux démonstrations |
| `lab/motion/motion.css` | Compositions et mouvements limités au lab |
| `lab/motion/motion.js` | Préférence calme, terrain, catégories, galerie, transitions |
| `lab/motion/build.py` | Dérivation reproductible depuis les vrais HTML et matchs |
| `lab/motion/{editorial,sport,court}/index.html` | Trois accueils générés |
| `lab/motion/{editorial,sport,court}/matchs/*/index.html` | 21 fiches générées depuis les sept rencontres réelles |
| `lab/motion/source-manifest.json` | Empreinte SHA256 de l'accueil source |
| `lab/motion/qa.html`, `measure.js`, `qa-results.json` | Banc de contrôle local et relevés |
| `lab/motion/*.md`, `FILES.txt` | Audit, système, limites, intégration |
| `package.json`, `.claude/motion-preview.mjs` | Serveur local optionnel sans dépendance |

Pour régénérer : exécuter d'abord les générateurs éditoriaux habituels si les données ont changé, puis `python lab/motion/build.py`. Ne pas éditer manuellement les 24 pages générées. Le CSS et le JS de production restent partagés en lecture : une mise à jour de ceux-ci peut affecter les expériences et exige une nouvelle QA.

## Intégration progressive proposée — après validation

1. Intégrer la bande 95 € / dès 3 ans / 2 terrains et la hiérarchie du prochain match : `index.html`, `style.css`, puis génération `style.min.css` et versions d'assets.
2. Intégrer les interactions retenues dans `script.js` et leurs styles : sélecteur, calendrier, portraits, galerie. Supprimer les anciens comportements superposés au lieu d'empiler des couches.
3. Adapter les générateurs de fiches de match avant de régénérer `matchs/*/index.html`, pour pérenniser la transition carte→fiche.
4. Intégrer Court Vision uniquement après essais Safari/iOS, tactile, zoom et réseau mobile. Faire une mesure terrain avant/après, notamment INP ; conserver un interrupteur simple permettant de retirer cette séquence.

Les futurs changements de production ne sont pas inclus dans cette branche. Le consentement existant doit être conservé lors de l'intégration : le lab retire seulement son propre chargeur Analytics pour éviter les visites de test. Les pages expérimentales sont `noindex,nofollow`, absentes du sitemap et des liens de production.

## Impact et rollback

Aucun framework, GSAP ou WebGL. Aucun nouvel asset photo/font. Environ 6 Ko CSS et 3 Ko JS supplémentaires après gzip, partagés entre variantes. Les pages HTML générées réutilisent les sources et suppriment les commentaires/JSON-LD du lab ; leur poids ne prédit pas celui d'une future intégration.

Rollback : abandonner la branche suffit. Si le lab était ultérieurement intégré pour revue, supprimer uniquement les fichiers de `FILES.txt` (ou annuler les commits du lab), sans toucher aux données ni aux assets. Ne pas fusionner cette exploration telle quelle dans l'accueil.
