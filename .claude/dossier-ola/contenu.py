# -*- coding: utf-8 -*-
"""Le texte du dossier. Chaque chiffre affiche est adosse a une source du depot.

Les affirmations que rien ne prouvait dans le dossier d'origine ont ete retirees
ou requalifiees :
  - la video « 48 SEC. » : aucune trace dans le depot -> remplacee par le sujet
    « Grand Sport » de Reunion la 1ere, lui date (13/09/2026) et chronometre (3 min 14) ;
  - « 40+ JEUNES A L'ENTRAINEMENT » : rien ne les denombre -> remplace par les
    8 categories et les 10 h d'entrainement hebdomadaires, qui sont dans creneaux.json ;
  - « DOFE STUDIO » : zero occurrence dans le depot -> la page 6 s'appuie desormais
    sur ce que le club produit lui-meme, ce qui est a la fois vrai et plus fort ;
  - la grille 500/1500/3000 EUR contredisait la grille PUBLIQUE du club
    (Rookie 200, MVP 500, All-Star 1000, Hall of Fame 2000 et +) : on reprend les
    noms et les montants publics, le haut de gamme restant a 3 000 EUR au titre
    du « 2 000 EUR et plus » du Hall of Fame.
"""

DATE = "18 septembre 2026"
PIED_MENTION_P1 = "PROPOSITION DE PARTENARIAT  ·  SAISON 2026/2027"

# --- Les chiffres, avec leur source ---------------------------------------
CHIFFRES = [
    ("100", "adhésions et préinscriptions",
     "effectifs communiqués par le club au 18/09/2026"),
    ("73–52", "premier match officiel, gagné à domicile",
     "data/matchs.json, J1 du 11/09/2026"),
    ("8", "catégories, du Baby Basket de 3 ans aux adultes",
     "data/creneaux.json, 8 formules"),
    ("9", "réceptions au gymnase en phase 1, entrée libre",
     "5 seniors + 4 U13, data/matchs.json + matchs-u13.json"),
    ("10", "heures d'entraînement encadré par semaine",
     "data/creneaux.json, 9 créneaux sur 2 équipements"),
    ("95 €", "la saison, licence FFBB et assurance comprises",
     "data/creneaux.json, tarif unique"),
]

PALIERS = [
    dict(nom="MVP", tempo="Premier quart-temps", prix="500", duree="3 mois",
         recommande=False,
         lignes=["Logo, nom et lien sur le mur des partenaires",
                 "Logo sur les affiches de 4 réceptions",
                 "3 publications et 3 stories, @mbc974.re",
                 "1 album photo de match livré, fichiers inclus",
                 "Bilan à 30 jours : les liens publiés"]),
    dict(nom="ALL-STAR", tempo="Saison complète", prix="1 000", duree="Saison 2026/2027",
         recommande=False,
         lignes=["Tout le palier MVP, sur la saison entière",
                 "Logo sur les 9 réceptions et leurs pages",
                 "6 publications et 6 stories",
                 "Maillot et bâche du gymnase*",
                 "Bilan à mi-parcours et bilan final"]),
    dict(nom="HALL OF FAME", tempo="Partenaire titre", prix="3 000", duree="Saison 2026/2027",
         recommande=True,
         lignes=["Tout le palier All-Star",
                 "Exclusivité du secteur de l'énergie",
                 "Partenaire titre du plateau Mini-Basket",
                 "10 licences solidaires offertes à 95 €",
                 "Un rendez-vous club avec vos équipes"]),
]

ETAPES = [
    ("01", "JOURS 1–7", ["Choix des supports",
                           "Validation des visuels",
                           "Convention signée"]),
    ("02", "JOURS 8–21", ["Logo en ligne sur mbc974.com",
                            "Première publication",
                            "Logo sur l'affiche du match suivant"]),
    ("03", "JOURS 22–30", ["Retour en images",
                             "Liens de chaque publication",
                             "Bilan remis, captures comprises"]),
]
