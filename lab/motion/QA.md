# QA — MBC Motion Lab

Contrôles du 10 septembre 2026. Prototype de revue, pas validation de mise en production.

## Méthode et portée

Inspection réelle dans Chrome distant : site public pour l'audit, puis source originale et variantes sur un même serveur local. Le banc `qa.html` affiche le site dans un iframe dont la largeur CSS est contrôlée ; le cadre est réduit visuellement lorsqu'il dépasse l'écran disponible. Cela teste les media queries et le reflow, pas le matériel, le DPR ou le tactile d'un téléphone.

Largeurs inspectées : 390, 430, 768, 1024, 1440 et 1920 px. Accueils A/B/C inspectés ; catégories, fiche de match et galerie examinées dans le navigateur ; terrain et retour au scoreboard examinés sur C. Cette couverture n'est pas une matrice exhaustive de chaque section de chaque variante à chaque largeur.

## Résultats fonctionnels

| Contrôle | Résultat / portée |
|---|---|
| Hero et CTA | Lisibles sans attendre une animation ; photos originales chargées |
| Largeurs demandées | Aucun overflow horizontal détecté dans les relevés ; composition observée dans le navigateur |
| Sélecteur d'âge | End→Adulte et Home→Baby au clavier ; clic Adulte validé ; contenu et sélection accessibles conservés |
| Navigation match | Accueil A→fiche réelle Sainte-Suzanne, puis retour navigateur ; liens calendrier/itinéraire présents |
| Mode calme | Activation puis navigation A→C : préférence conservée, bouton pressé ; accès direct au prochain match validé |
| Galerie | Home/End changent les photographies visibles, focus visible ; glissement souris exercé et rendu contrôlé |
| Menu mobile | Ouverture à 390 px, focus placé dans la navigation, fermeture via Échap |
| Ressources | Pas d'image cassée ni de requête tierce dans les relevés initiaux du lab |
| Sources | Pages dérivées des HTML réels ; données, médias, inscription et production conservés |
| Contrôles statiques | Syntaxe JS ; CSS minifié et versions d'assets de production à jour ; destinations locales et IDs contrôlés |

## Défauts corrigés pendant l'exploration

- Superposition du traitement photographique mobile hérité : simplification des pseudo-éléments dans le lab.
- Trajectoire sur les visages dans A : supprimée de cette direction.
- Texte secondaire trop clair dans les sections blanches de A : contraste renforcé.
- Signature trop proche du sous-titre sur grand écran : suppression de la hauteur de ligne héritée du H1 ; résultat revu à 1920 px.
- Chemins de préchargement de polices des fiches : normalisation des segments relatifs lors de la génération.
- Perspective mobile C : amplitude réduite à 20°→12°, séquence dans le flux.

## Mesures exploratoires avant/après

Source : `qa-results.json`. LCP en millisecondes, déplacements de layout sans unité. Navigations locales isolées, sans bridage réseau/CPU, après chargement initial et environ 1,2 s de stabilisation. Ce ne sont ni des percentiles terrain, ni des scores Lighthouse, ni des mesures de réseau réunionnais. Les premiers relevés cumulaient les déplacements sans interaction ; l'instrument a ensuite été corrigé pour conserver la plus grande fenêtre de session CLS. Ces petits échantillons ne permettent pas de conclure à un gain de vitesse.

| Vue | Largeur | LCP local | Déplacements de layout | Requêtes ressources |
|---|---:|---:|---:|---:|
| Original | 390 | 292 | 0 | 13 |
| A | 390 | 188 | 0,0042 | 14 |
| B | 390 | 160 | 0,0042 | 14 |
| C | 390 | 268 | 0,0043 | 14 |
| Original | 1440 | 300 | 0,0048 | 13 |
| A | 1440 | 352 | 0,0148 | 14 |
| B | 1440 | 180 | 0,0134 | 14 |
| C | 1440 | 232 | 0,0131 | 14 |

Les autres relevés couvrent 430/768/1024/1920 px. Entre zéro et deux tâches longues ont été observées au chargement selon la passe. Les mesures de ressources excluent le document HTML et incluent le petit instrument QA. Le lab retire le chargeur de consentement/Analytics uniquement de ses copies ; il ajoute deux ressources motion, soit +1 requête nette dans ces passes. Les corrections CSS finales changent légèrement les octets par rapport aux premières passes.

**INP non mesuré.** `interactionMax` est un diagnostic Event Timing, pas un INP ; les relevés initiaux sont null. Une vraie comparaison INP exige des interactions représentatives et une collecte correctement instrumentée. [Définition INP, web.dev](https://web.dev/articles/inp).

| Ressource | Octets source | Octets gzip local |
|---|---:|---:|
| CSS existant minifié | 308 346 | 54 433 |
| JS existant | 72 189 | 22 722 |
| CSS motion ajouté | 23 756 | 5 997 |
| JS motion ajouté | 7 918 | 3 043 |
| HTML original | 188 702 | 42 927 |
| HTML A | 160 695 | 31 504 |
| HTML B | 160 627 | 31 498 |
| HTML C | 163 262 | 32 401 |

Poids mesurés avant la normalisation des préchargements de fiches et le remplacement du formulaire actif par un lien de contact. Les accueils finaux sont donc légèrement plus légers ; les ressources motion restent identiques. Compression gzip locale, pas garantie de transfert du serveur de production. WebGL ajouté : **0 octet**. Images ajoutées : **0**. Fonts ajoutées : **0**. Les photos et polices existantes restent partagées ; leur transfert dépend de la largeur et du défilement. Le poids HTML moindre vient principalement du retrait des commentaires et schémas du lab, pas d'une optimisation transposable automatiquement en production.

## Limites et validation avant intégration

Non disponibles ici : Safari/iOS réel, Android tactile, lecteur d'écran avec synthèse vocale, émulation du réglage système reduced-motion, profil matériel lent et réseau mobile. Le bouton calme a été testé ; les media queries reduced-motion et le listener système ont été inspectés dans le code. Cela ne remplace pas un essai du réglage OS.

À exécuter avant fusion d'une intégration : Safari/iPhone et Chrome/Android, portrait/paysage, zoom 200 % et 400 %, VoiceOver/NVDA, contraste complet des composants hérités, scroll lent/rapide prolongé, retour depuis plusieurs rencontres, interruptions rapides des onglets, drag tactile et annulation du geste. Vérifier aussi les transitions interdocuments là où elles sont prises en charge. La navigation HTML fonctionne sans dépendre de leur disponibilité.

Court Vision doit être simplifié ou retiré si les essais matériels montrent du jank. La pile CSS de production reste importante : pour une intégration définitive, remplacer les règles devenues inutiles, plutôt que publier les surcharges expérimentales telles quelles.

Le formulaire actif a été retiré des copies expérimentales au contrôle de publication : la clé du service n’est pas nécessaire au lab. Un lien conduit au contact original. Le formulaire de production est inchangé.
