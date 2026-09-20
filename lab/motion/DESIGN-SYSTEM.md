# MBC Playbook — Motion Design System

## Thèse

Le mouvement ressemble à une passe : départ clair, trajectoire courte, arrivée nette. Le terrain sert à relier des informations ; la photographie porte l'émotion. Le club doit se reconnaître sans ajouter son écusson à chaque section.

## Fondations

| Rôle | Valeur | Usage |
|---|---|---|
| Bleu royal | `#1B519E` | Bande de marque, surface collective |
| Orange | `#E8822A` | Trajectoire, action, chiffre événementiel |
| Nuit | `#070D18` | Terrain, profondeur, contraste photographique |
| Blanc | `#FFFFFF` | Lecture, respiration éditoriale |
| Glacier | `#BFD2E4` | Texte secondaire sur nuit, focus |
| Display | Anton 400, fichier existant | Titres, numéros, chiffres stables |
| Texte | Barlow, fichier existant | Explication, navigation, légendes |
| Condensé | Barlow Condensed, fichier existant | Repères sportifs courts |

Ne pas dessiner de nouveaux logos. Ne pas recréer les visages. Le motif relief est abstrait : ce n'est pas une carte topographique authentique de La Montagne. Une version géographique exigerait un fond altimétrique sourcé et adapté.

## Grammaire

| Geste | Durée / amplitude | Fonction | État calme |
|---|---|---|---|
| Pass | 180 ms, couleur/soulignement | Confirmation d'une action | Contraste/focus fixes |
| Cut | 240–360 ms, 8–16 px | Changement de catégorie, carte vers fiche | Remplacement immédiat, même espace réservé |
| Arrival | 520–620 ms, 10 px | Entrée d'un chapitre | Contenu visible et composé |
| Playbook Line | 1 150 ms une fois, ou progression liée au scroll | Continuité hero→terrain→match | Trajectoire complète |
| Court Depth | 36°→12°, échelle .91→1 | Passage du collectif au match | Terrain à 12°, ballon à l'arrivée |
| Score Motion | Chiffres tabulaires, entrées courtes | Date/chrono priorisés | Valeurs lisibles, jamais de faux score |
| Portrait | Échelle 1→1.018, 360 ms | Indiquer le portrait visé | Photo fixe, contour de focus |

Courbe commune : `cubic-bezier(.2,.75,.25,1)`. Pas de ressort rebondissant. Pas d'animation infinie ajoutée. Une arrivée se joue une seule fois. Un scroll arrêté ne doit déclencher aucune boucle de rendu Court Vision.

## Trois compositions

**A — Editorial Motion.** Double page texte/photographie sur desktop, blanc et bleu royal, trois promesses au premier plan. Sections en composition titre/texte décentrée. La photographie est dégagée de la trajectoire. Risque : moins d'énergie événementielle ; vérifier les contrastes des composants hérités sur fond clair.

**B — Sport Motion.** Titre d'affiche, séparation orange, Match Center plus grand, chrono structuré et portraits stables. L'énergie vient de la composition et des entrées rapides, pas d'un faux direct. Risque : trop de grands chiffres sur une longue page ; ne pas généraliser le traitement scoreboard à tous les textes.

**C — Court Vision.** Hero photographique, bande de marque, terrain SVG, trajectoire orange et ballon synchronisés au défilement, puis scoreboard en DOM. Le visiteur peut accéder directement au match. Sur mobile, le terrain reste dans le flux et la perspective a une amplitude limitée ; aucune séquence sticky longue. Le récit du quartier reçoit le motif relief→lignes.

## Accessibilité

- Le contenu est visible avant l'amélioration JS. Aucun H1, prix ou bouton ne dépend de la fin d'une animation.
- `prefers-reduced-motion` est écouté au chargement et lorsqu'il change. Le bouton « Version calme » permet aussi de choisir le rendu fixe pour le lab, avec préférence conservée dans la session. Le choix du système est prioritaire.
- Le terrain est décoratif et `aria-hidden` ; le titre, le lien de saut et les informations de match sont du vrai texte. Aucun pseudo-score 0–0 n'est ajouté.
- Les onglets conservent le comportement clavier original : flèches, Home, End, focus et `aria-selected`. La place du panneau le plus haut est réservée après mesure pour limiter les sauts.
- Les galeries utilisent le scroll natif au doigt, le clavier et un drag souris optionnel. Le contenu ne dépend pas du hover.
- Les transitions entre documents restent optionnelles. Les ancres et liens continuent à naviguer normalement si l'API est absente.
- Vérification lecteur d'écran physique non disponible dans cet environnement ; inspection de la structure accessible et des comportements clavier, sans prétendre à une certification.

## Technologies évaluées

| Technologie | Décision | Motif |
|---|---|---|
| HTML/CSS, transforms | Retenue | Site statique, composition, perspective légère |
| SVG | Retenu | Terrain, trajectoire et motif abstrait précis sans bitmap |
| IntersectionObserver | Retenu | Arrivées uniques, pas d'éléments masqués au repos |
| Web Animations API | Retenue | Animations courtes annulables et repli visible |
| requestAnimationFrame | Retenu, uniquement sur événement | Synchroniser trajectoire, ballon et perspective ; sortie immédiate hors champ |
| ResizeObserver | Retenu | Réserver l'espace du sélecteur d'âge selon la largeur réelle |
| View Transitions API | Amélioration progressive | Carte de match→fiche, navigation classique conservée |
| CSS Scroll-Driven Animations | Évaluée, pas requise | Un seul pilote JS coordonne SVG et ballon ; pas de double orchestration ni de polyfill |
| GSAP | Non nécessaire | Pas d'orchestration imposant une dépendance |
| Three.js / WebGL | Non nécessaire | Perspective obtenue en CSS ; coût ajouté 0 octet |

Les capacités navigateur sont détectées ; aucune promesse universelle Safari/iOS. [MDN : animation-timeline](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/animation-timeline) indique une disponibilité limitée. [MDN : View Transitions](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using) décrit les transitions dans et entre documents. La navigation et la lecture restent des fonctions HTML.

## Recommandation d'intégration

Retenir A pour le rythme global, B pour les rencontres, et une seule signature C. D'abord les trois chiffres et le Match Center, ensuite catégories/joueurs/galerie, enfin Court Vision si ses contrôles mobile et Safari sont satisfaisants. Ne pas intégrer le lab entier dans l'accueil.
