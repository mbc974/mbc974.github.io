# -*- coding: utf-8 -*-
"""Le texte du dossier partenaire GENERIQUE, pour tous les types de partenaire.

Il reprend au centime la grille publique de mbc974.com/sponsor-club-basket-reunion/
— quatre formules de 200 a 2 000 EUR et plus, chacune incluant la precedente —
pour qu'un dirigeant qui ouvre le site retrouve exactement ce dossier.

Ce qui vient du one-pager mais qui N'EST PAS repris, et pourquoi :
  - « +60 licencies » : c'etait un OBJECTIF dans le PDF de juin, devenu un chiffre
    acquis sur le visuel, ce qui a valu le retrait de l'image du site le
    09/09/2026. Le chiffre du jour est « pres de 100 adhesions et
    preinscriptions », communique par le bureau, et le dossier le dit.
  - « U11 (9-10 ans) » : le site ne connait pas cette categorie, il dit « Ecole
    de Basket, 7-10 ans ». On reprend les 8 formules de data/creneaux.json, qui
    sont celles du tunnel de paiement.
  - « Baby Basket (4-6 ans) » : le site dit 3-6 ans.
  - « Club 100 % benevole » : vrai, mais on prefere le dire autrement, l'expression
    pouvant se lire comme « personne n'est paye pour encadrer ».
"""

PIED_MENTION_P1 = "DOSSIER PARTENAIRE  ·  SAISON 2026/2027"

# --- Les chiffres, avec leur source ---------------------------------------
CHIFFRES = [
    ("100", "adhesions et preinscriptions",
     "effectifs communiques par le club au 18/09/2026"),
    ("73–52", "premier match officiel, gagne à domicile",
     "data/matchs.json, J1 du 11/09/2026"),
    ("8", "catégories, du Baby Basket de 3 ans aux adultes",
     "data/creneaux.json, 8 formules"),
    ("9", "réceptions au gymnase en phase 1, entrée libre",
     "5 seniors + 4 U13"),
    ("10", "heures d’entraînement encadré par semaine",
     "data/creneaux.json, 9 créneaux sur 2 équipements"),
    ("95", "euros la saison, licence FFBB et assurance comprises",
     "data/creneaux.json, tarif unique"),
]

# --- Les quatre formules publiques ----------------------------------------
# Source : mbc974.com/sponsor-club-basket-reunion/ — reprises au centime.
FORMULES = [
    dict(nom="ROOKIE", prix="200", tempo="Un premier soutien local",
         populaire=False,
         lignes=["Mention sur nos réseaux sociaux",
                 "Votre logo sur le site",
                 "Remerciements en fin de saison"]),
    dict(nom="MVP", prix="500", tempo="Le meilleur rapport visibilité / budget",
         populaire=True,
         lignes=["Logo sur les affiches et les flyers",
                 "Une publication dédiée",
                 "Invitations aux événements",
                 "Inclut Rookie"]),
    dict(nom="ALL-STAR", prix="1 000", tempo="Présence forte, jusque sur le terrain",
         populaire=False,
         lignes=["Bâche ou panneau au gymnase*",
                 "Logo floqué sur les maillots*",
                 "Mise en avant toute la saison",
                 "Inclut MVP"]),
    dict(nom="HALL OF FAME", prix="2 000", suffixe="+",
         tempo="Partenaire majeur, exclusivité secteur", populaire=False,
         lignes=["Partenaire titre d’un événement",
                 "Prise de parole lors des remises",
                 "Visibilité premium",
                 "Exclusivité dans votre secteur",
                 "Inclut All-Star"]),
]

# --- Comment on devient partenaire ----------------------------------------
# Source : les trois etapes de la page publique.
ETAPES = [
    ("01", "VOUS NOUS ÉCRIVEZ",
     ["Formulaire, WhatsApp ou téléphone",
      "Réponse en général sous 48 h",
      "Sans engagement"]),
    ("02", "ON BÂTIT LA FORMULE",
     ["Soutien financier, matériel ou en services",
      "Une formule de la grille, ou sur mesure",
      "Selon vos moyens et vos objectifs"]),
    ("03", "VOTRE VISIBILITÉ DÉMARRE",
     ["Mise en ligne et première publication",
      "Valorisée toute la saison",
      "Bilan avec les liens publiés"]),
]

# --- Les six supports de visibilite ---------------------------------------
# Source : « Vos supports de visibilite » de la page publique.
SUPPORTS = [
    ("LE SITE", "27 pages publiées, votre logo et votre lien"),
    ("LES RÉSEAUX", "Facebook, Instagram, TikTok"),
    ("LES AFFICHES", "Une affiche produite à chaque réception"),
    ("LES FLYERS", "Créneaux, inscriptions, événements"),
    ("LES ÉVÉNEMENTS", "Plateaux, tournois, temps forts"),
    ("LES MAILLOTS", "Domicile et extérieur, sous réserve*"),
]

# --- L'audience mesuree ---------------------------------------------------
# Source : Google Search Console, releve fin aout 2026 sur 3 mois glissants,
# tel que la page publique le formule — « apparitions, pas des personnes ».
AUDIENCE = [
    ("~1 130", "apparitions dans Google en 3 mois"),
    ("5", "position moyenne dans Google"),
    ("4", "supports de diffusion actifs"),
]
