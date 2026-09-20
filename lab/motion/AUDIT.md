# MBC Motion Lab — audit du point de départ

10 septembre 2026 · dépôt `mbc974/mbc974.github.io` · base `01851f0e1c15d9e5849adcbc55e5520d5c3ef9b7`.

## Décision artistique

Conserver la photographie et l'identité typographique. Changer le rythme, la hiérarchie et la continuité, en commençant par le triptyque hero / match / chiffres. Le site n'est pas dépourvu de mouvement : il a besoin d'une direction commune à ses mouvements.

## Architecture observée

- Site HTML/CSS/JS statique, sans framework ni build obligatoire ; GitHub Pages sur `main`, racine du dépôt, domaine déclaré dans `CNAME`.
- `index.html` : accueil, navigation mobile, hero photographique, signature SVG, bandeau du prochain match, chiffres, sélecteur d'âge, catégories repliées, planning, matchs, joueurs, galerie, parents, quartier, soutien, contact et footer.
- `style.css` : source de 597 939 octets / 10 277 lignes. 334 occurrences de `@media`, 68 de `prefers-reduced-motion`. Les nombreuses couches historiques incluent des sélecteurs dormants : leur présence ne prouve pas leur activité à l'écran.
- `style.min.css` : feuille réellement servie, 308 346 octets ; générée par `.claude/build-css.py`. Hachages de cache tenus par `.claude/bump-assets.py` et `sw.js`.
- `script.js` : 72 189 octets ; menu avec gestion de focus, reveals, compteurs, lightbox, formulaire, rail staff, halos au pointeur, service worker, parallaxe quartier, onglets d'âge, façade Maps, dates Réunion, prochain match, planning, signature manuscrite et zoom galerie.
- `data/matchs.json`, `creneaux.json`, `actualites.json`, `effectif.json` sont les sources éditoriales ; générateurs Python dans `.claude/`. Les pages générées ne doivent pas être corrigées manuellement.
- 28 pages HTML hors print et outillage. Les pages secondaires ont un header `seo-top`, différent du header de l'accueil. Les styles sont partagés ; certaines interactions sont inline.
- Assets réels : portraits joueurs, photographies galerie et gymnases, logos clubs/sponsors, affiches, polices locales, documents et vidéo. Aucun nouvel asset photographique nécessaire pour cette exploration.
- Consentement : chargeur Google conditionné à l'accord, logique centralisée dans `consent.js`. Le formulaire comporte une voie POST configurable et un repli email. Aucun formulaire réel soumis pendant l'audit.

## Lecture visuelle par zone

| Zone | Ce qui fonctionne | Limite observée / risque | Direction utile |
|---|---|---|---|
| Hero | Photo collective authentique, titre immédiatement situé, inscription et essai | La signature cyclique attire parfois davantage que le titre ; plusieurs couches de contraste | Photo intacte, signature stabilisée, un seul mouvement d'arrivée |
| Header / navigation | Marque forte, CTA distinct, menu mobile | Deux langages de header selon les pages ; il faut vérifier toute transition de page | Conserver la navigation, animer seulement le repère actif |
| Typographie | Anton reconnaissable et sportive, Barlow lisible | Beaucoup de titres centrés, double ligne blanc/orange, même puissance partout ; interlignes serrés | Varier les alignements et l'échelle, conserver les familles |
| Rythme | Sections clairement séparées | Grandes plages sombres ; répétition titre centré / sous-texte / cartes | Une alternance de masses et des respirations proportionnelles au contenu |
| 95 € / 3 ans / 2 terrains | Trois arguments utiles et liens corrects | Sous-titres et liens très petits ; bloc visuellement secondaire après un match plus contrasté | Bande de marque bleu royal, nombres stables, trois destinations évidentes |
| Match Center | Adversaires, date, heure, itinéraire, lien fiche et chrono existants | Bandeau compact ; petits chiffres ; peu de distinction entre information et événement | Scoreboard typographique, compte à rebours à chiffres fixes, sans inventer de score |
| Sélecteur d'âge | Six onglets, clavier, vraie règle d'année de naissance | Remplacement brutal de panneau ; peu de continuité visuelle | Animation du contenu entrant et ligne de sélection ; pas de morphing du texte lisible |
| Catégories | Contenu utile repliable, CTA et années présents | Huit cartes similaires une fois ouvertes | Garder le dévoilement volontaire, reveals courts par groupe |
| Planning | Deux lieux photographiés, horaires textuels, semaine compréhensible | Beaucoup de hauteur avant les horaires sur tablette ; rythme répétitif | Timeline à repères fixes, révélation des rangées sans retarder l'accès |
| Matchs | Saison complète, distinctions domicile / extérieur, fiches dédiées | Sept cartes étroites, lecture très petite sur desktop | Cartes éditoriales plus larges et rail natif, transition vers une fiche du lab |
| Seniors | Vrais portraits/affiches, noms et postes en DOM | Accordéon changeant les largeurs ; affiches partiellement recadrées | Largeurs stables, déplacement photographique minimal, focus équivalent au hover |
| Galerie | Vraies scènes, mosaïque expressive | Séquence sticky de 240vh desktop / 185vh mobile déjà présente ; certaines légendes disparaissent pendant le zoom | Rail avec snap, légendes visibles, navigation native ; éviter deux immersions longues |
| Parents / bénévoles | Confiance, rôles et actions explicites | Même recette de cartes que plusieurs autres sections | Priorité au texte et au focus, mouvement discret seulement |
| Nout kartié | Photographie locale et récit incarné | Mot de fond/parallaxe faible, séparation graphique classique | Motif abstrait relief→terrain, clairement distinct d'une carte géographique |
| Partenaires | Logos existants et liens nommés | Halos et effets de cartes concurrencent le contenu | Logos immobiles, soulignement au focus/survol |
| Footer | Réseau de liens complet, coordonnées, confidentialité | Densité et petite typographie secondaire | Garder les accès et renforcer le focus ; aucune animation narrative ici |

## Appareils et limites de preuve

Inspection du site public dans Chrome desktop, puis du checkout original dans un cadre navigateur de dimensions contrôlées. Ce cadre teste réellement les media queries de largeur/hauteur ; ce n'est pas un iPhone physique et il ne simule pas Safari, le DPR ou le pointeur tactile. Les résultats détaillés et dimensions sont consignés dans `QA.md` après les contrôles.

- Mobile : le hero sépare photo et texte, le menu devient compact ; le bandeau de consentement peut recouvrir l'inscription dans la première vue. Les chiffres arrivent tard après le hero et le match. Préserver une voie d'accès directe.
- Tablette : la signature occupe une place importante sur la photo ; le bandeau match passe en pile et s'allonge. Préférer une composition intermédiaire plutôt qu'un desktop réduit.
- Laptop : l'intention de faire tenir hero, match et chiffres en hauteur conduit à réduire fortement certaines informations. La promesse du club mérite une hiérarchie autonome.
- Desktop : photographie convaincante mais longs enchaînements de grandes sections sombres et titres centrés. Les cartes de saison manquent de largeur de lecture.
- Grands écrans : borner la longueur des lignes et la largeur des compositions ; éviter d'agrandir les effets proportionnellement à la fenêtre.

## Mouvement existant à ne pas cumuler

Signature SVG cyclique ; reveal global ; compteur du tarif partant de zéro ; halos au pointeur ; expansion des joueurs ; zoom sticky galerie ; micro-parallaxe du mot KARTIÉ ; battement de créneau en cours. Le laboratoire neutralise les effets concurrents dans ses copies seulement. Les prix restent vrais pendant l'animation : animer leur arrivée, jamais afficher un faux montant intermédiaire.

## Priorités

1. Chiffres de marque et hiérarchie du prochain match.
2. Sélecteur d'âge fluide, stable et utilisable au clavier.
3. Court Vision court et contournable, sans interception du scroll.
4. Joueurs et galerie à tailles stables ; lisibilité avant effets.
5. Intégration ultérieure des transitions dans les générateurs, sans toucher aux fichiers générés à la main.

À exclure : faux live, scores inventés, particules, glow permanent, curseur artificiel, WebGL sans bénéfice, scroll forcé, masquage du H1 ou du CTA jusqu'à la fin d'une animation.

## Baseline de poids

| Fichier | Octets bruts | Gzip local déterministe |
|---|---:|---:|
| index.html | 188 702 | 42 927 |
| style.min.css | 308 346 | 54 433 |
| script.js | 72 189 | 22 722 |
| consent.js | 9 477 | 3 674 |

Gzip local = comparaison de code, pas observation du transfert GitHub Pages. Les LCP/CLS de laboratoire sont des diagnostics locaux ; aucune affirmation sur l'INP terrain ou les Core Web Vitals des visiteurs ne peut en être déduite.
