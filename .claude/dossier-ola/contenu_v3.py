# -*- coding: utf-8 -*-
"""Le texte du dossier partenaire V3 — la version COMMERCIALE.

Le dossier v2 expliquait « qui nous sommes » et « ce que nous avons ». Il le
faisait bien : chaque chiffre y etait source et qualifie. Mais un dirigeant qui
le refermait savait tout du club et rien de ce qu'il achetait. La V3 garde la
rigueur et change l'ordre des questions :

    p2  ce que le club pese          (avant : p3)
    p3  pourquoi le croire           (avant : p2, retourne a l'endroit)
    p4  QUI votre marque touche      (page NEUVE)
    p5  CE QUE votre argent fait     (page NEUVE)
    p6  CE QUE vous recevez          (avant : p4 + p6 fondues)
    p7  combien                      (avant : p8, contreparties precisees)
    p8  on se parle                  (avant : p7 + p9 + p10 fondues)

RIEN N'EST INVENTE. Chaque ligne ci-dessous sort du depot ou des pages publiees
de mbc974.com, et la source est notee en commentaire. Trois retraits par rapport
a la v2, tous deliberes :

  - « 4 supports de diffusion actifs » : FAUX. La page publique en liste SIX,
    et la page 6 de la v2 s'intitulait elle-meme « SIX SUPPORTS ». Le chiffre
    disparait. (Deja corrige sur le site le 18/09, cf. memoire V192.)
  - « maillot domicile et exterieur » : le 11/09 etait un match A DOMICILE et
    l'equipe portait le BLANC, alors que le rendu etiquete « domicile » du site
    est bleu nuit. Tant que le bureau n'a pas tranche, on ecrit « le maillot »,
    jamais « le maillot domicile ». (Regle etablie le 18/09.)
  - « Trois preuves a un clic. Aucune n'a besoin de nous. » : defensif. On ne
    plaide pas sa bonne foi, on la montre.
"""

# ---------------------------------------------------------------------------
# LES LIENS — un seul endroit, pour que le PDF soit cliquable
# ---------------------------------------------------------------------------
# Le dossier est lu a l'ecran autant qu'imprime. Les QR servent le papier ;
# ces URL servent l'ecran, posees sous le texte deja present — on ne rajoute
# pas une ligne « cliquez ici », on rend cliquable ce qui est deja ecrit.
LIENS = dict(
    site="https://mbc974.com/",
    partenaires="https://mbc974.com/sponsor-club-basket-reunion/",
    reportage="https://mbc974.com/actualites/reportage-reunion-la-1ere-mbc-la-montagne/",
    ffbb="https://competitions.ffbb.com/ligues/reu/comites/0974/clubs/reu0974104",
    # Le QR reste sur l'URL NUE et le LIEN porte le message pre-rempli. Mesure :
    # avec ?text=, le code passe de 33 a 61 modules, soit 0,312 mm par module a
    # l'impression A4 paysage — sous le seuil de scan fiable de 0,40 mm. Un clic
    # n'a pas cette contrainte. Le papier scanne, l'ecran clique.
    whatsapp="https://wa.me/262692556458?text=Bonjour%2C%20je%20souhaiterais"
             "%20%C3%A9changer%20au%20sujet%20d%27un%20partenariat%20avec%20le%20MBC.",
    creneaux="https://mbc974.com/creneaux/",
    soutenir="https://mbc974.com/soutenir-le-club/",
    mail="mailto:contact@mbc974.com",
    # +262 est l'indicatif de La Reunion ; c'est deja celui du lien WhatsApp.
    tel="tel:+262692556458",
)

# ---------------------------------------------------------------------------
# PAGE 1 — COUVERTURE
# ---------------------------------------------------------------------------
P1_TITRE = "DEVENEZ<br>PARTENAIRE"
# « le basket a La Montagne » laissait entendre que le basket y commencait avec
# le club. C'est le MBC qui est dans sa saison fondatrice, pas le sport.
P1_LEAD = "Rejoignez la saison fondatrice du MBC à La Montagne."
P1_PIED = "DOSSIER PARTENAIRE  ·  SAISON 2026/2027"

# ---------------------------------------------------------------------------
# PAGE 2 — LE MBC EN 30 SECONDES
# ---------------------------------------------------------------------------
P2_SUR = "LE MBC EN 30 SECONDES"
P2_TITRE = "NÉ EN 2026. DÉJÀ LÀ."
P2_LEAD = ("En quelques mois, le MBC est devenu un nouveau point de rencontre "
           "du basket à La Montagne.")

# Le chiffre phare. Source : bureau, au 18/09/2026 — qualifie dans la mention.
P2_PHARE = ("PRÈS DE", "100", "Adhésions et préinscriptions",
            "au 18 septembre 2026")

# Les six autres. Chacun est verifiable dans le depot :
#   8    -> data/creneaux.json, 8 formules d'adhesion
#   3 ANS-> data/creneaux.json, Baby Basket « 3 — 6 ans »
#   2    -> data/creneaux.json, gymnase + Ruisseau Blanc
#   5/7  -> data/creneaux.json : lundi, mercredi, vendredi, samedi, dimanche
#   10 H -> somme des 7 creneaux d'entrainement : 1,5+1,5+1,5+1,5+1,5+1+1,5
#   95 € -> data/creneaux.json, tarif unique
P2_CHIFFRES = [
    ("8", "catégories", "du Baby Basket aux adultes"),
    ("DÈS 3 ANS", "et jusqu’aux adultes", "compétition et loisirs"),
    ("2", "terrains à La Montagne", "un gymnase, un plateau couvert"),
    ("5/7", "jours de présence", "dans le quartier, chaque semaine"),
    ("10 H", "d’entraînement encadré", "chaque semaine, deux équipements"),
    ("95 €", "la saison", "licence FFBB et assurance comprises"),
]

# Le premier match officiel. Source : data/matchs.json, J1 du 11/09/2026.
# Le club a depuis joue une 2e journee, perdue 57-68 le 18/09 a l'exterieur :
# la formule « premier match officiel » reste donc exacte, et le dossier
# n'avance aucun bilan de saison.
P2_MATCH = ("73–52", "Premier match officiel, gagné à domicile.")

P2_MENTION = (
    "Effectifs communiqués par le club au 18/09/2026, adhésions et "
    "préinscriptions confondues : ce ne sont pas des licences FFBB qualifiées. "
    "Catégories, créneaux, jours et tarif : {creneaux}. Score du "
    "11/09/2026 communiqué par le club, le relevé de la Ligue n’est pas "
    "encore publié.")

# ---------------------------------------------------------------------------
# PAGE 3 — DES PREUVES, PAS DES PROMESSES
# ---------------------------------------------------------------------------
P3_SUR = "QUELQUES MOIS, DÉJÀ DU TERRAIN"
P3_TITRE = "DES PREUVES, PAS DES PROMESSES"
P3_LEAD = "Tout ce que vous lisez ici s’ouvre en un clic."

# Le reportage. Source : actualites/reportage-reunion-la-1ere-mbc-la-montagne/.
P3_TV_ETIQ = "RÉUNION LA 1ÈRE · 13 SEPTEMBRE 2026"
P3_TV_CHIFFRE = "3 MIN 14"
P3_TV_TEXTE = ("Quelques mois après sa création, le club a fait l’objet d’un "
               "sujet dans « Grand Sport », le magazine sportif de Réunion "
               "La 1ère.")

# Le premier QR vise la PAGE DU CLUB qui raconte le reportage, et non le reel
# Facebook : plus durable, et le visiteur reste sur mbc974.com.
# Chaque preuve porte sa cible : le QR la sert au papier, le meme lien rend
# la plaque ET l'intitule cliquables a l'ecran.
P3_PREUVES = [
    ("qr-reportage.svg", "reportage", "LE SUJET, EN LIGNE",
     "Sur mbc974.com,<br>avec le reportage."),
    ("qr-site.svg", "site", "MBC974.COM · @MBC974.RE",
     "27 pages publiées, plus Facebook,<br>Instagram et TikTok."),
    ("qr-ffbb.svg", "ffbb", "FICHE FFBB PUBLIQUE",
     "Affiliation REU0974104,<br>vérifiable chez la fédération."),
]

# Les partenaires deja engages. Source : page publique — « Cinq entreprises et
# associations soutiennent deja le club, aux cotes de notre equipementier ».
# REGLE : on ne rattache JAMAIS un nom a un montant ni a une formule.
# Les trois acheteurs ont pose la meme question : « qui a deja signe ? ».
# Cinq partenaires anonymes sur une page intitulee « DES PREUVES » produisaient
# l'effet inverse de celui recherche. Les cinq sont publies sur
# mbc974.com/sponsor-club-basket-reunion/ ; on les nomme, et on dit enfin ce
# qu'est InPlay, cite deux fois dans la V3 sans jamais etre presente.
# REGLE MAINTENUE : aucun nom n'est mis en regard d'un montant ni d'une
# formule, et cette page n'en porte aucun.
P3_DEJA = ("ILS SOUTIENNENT DÉJÀ LE CLUB",
           ["Oxysom · Les Agitateurs du Midi · CPA Paysage",
            "Resto Chen · Saint-François d’Assise · InPlay"])

# « Le club ne dispose d'aucun chiffre d'audience » contredisait la page 6, qui
# en avance un (Search Console). La phrase est bornee au REPORTAGE, ou elle est
# exacte. Et la reserve sur la couverture media, qui vivait page 8, remonte ici :
# c'est la page qui parle de presse.
P3_MENTION = (
    "Sujet « Grand Sport » diffusé le 13/09/2026 par Réunion la 1ère. Le club "
    "ne dispose d’aucun chiffre de vues ni d’abonnés sur ce sujet, et n’en "
    "avance aucun ; la couverture média dépend des rédactions et ne fait pas "
    "partie des contreparties. Cinq entreprises et associations soutiennent le "
    "club, aux côtés d’InPlay, son équipementier ; aucune n’est ici rattachée "
    "à une formule ni à un montant.")

# ---------------------------------------------------------------------------
# PAGE 4 — QUI VOTRE ENTREPRISE VA TOUCHER
# ---------------------------------------------------------------------------
P4_SUR = "LA COMMUNAUTÉ DU MBC"
P4_TITRE = "QUI VOTRE MARQUE VA TOUCHER"
P4_LEAD = ("Un partenariat MBC, c’est une présence au cœur d’une communauté "
           "locale et intergénérationnelle.")

# Chaque ligne decoule de data/creneaux.json et des pages publiees.
P4_PUBLICS = [
    ("ENFANTS ET ADOLESCENTS",
     ["Baby Basket dès 3 ans, École de", "Basket, U13, U15 et U18."]),
    # Le niveau de jeu n'apparaissait nulle part : « championnat FFBB » couvre
     # du departemental comme du regional, et un lecteur retient la version la
     # plus flatteuse. Source : data/matchs.json, « Pré-Régionale Masculine,
     # Poule A · zone Nord ».
     ("ADULTES",
     ["Seniors en Pré-Régionale, zone Nord,", "et basket loisirs dès 16 ans."]),
    ("PARENTS, FAMILLES, BÉNÉVOLES",
     ["Les plus jeunes viennent", "accompagnés : vous parlez aussi", "à leurs parents."]),
    ("LE QUARTIER",
     ["Deux équipements municipaux,", "cinq jours sur sept, réceptions", "en entrée libre."]),
]

# Source : data/matchs.json + data/matchs-u13.json (5 receptions seniors +
# 4 receptions U13 en phase 1 ; 7 matchs + 23 echeances = 30 dates).
# Ces deux libelles sont poses sur UNE ligne ferree a droite : le detail
# (phase 1, 5 seniors + 4 U13, 7 journees + 23 echeances) vit dans la mention.
# « 30 echeances sportives PROGRAMMEES » a ete ecarte : sur les 23 echeances,
# 5 sont des tours de Coupe de France « selon qualification » et 4 des dates de
# finale « selon classement ». Neuf d'entre elles n'auront donc lieu que sous
# condition — « programmees » serait plus fort que la donnee. « Dates au
# calendrier sportif » est exact pour les trente ; la mention detaille.
P4_CHIFFRES = [
    ("9", "réceptions en entrée libre"),
    ("30", "dates au calendrier sportif, dont 21 acquises"),
]
# La version precedente opposait l'audience aux voisins — vrai, mais trop
# absolu : le club a AUSSI une audience en ligne, et la page 6 la chiffre.
# « pas SEULEMENT une audience » en deux phrases faisait 1 251 px pour une
# ligne de 1 152 : le « qu’une » dit la meme chose en 1 010 et garde le sujet.
P4_CHUTE = ("Votre marque ne touche pas qu’une audience : "
            "des voisins, des familles, des pratiquants.")

# Les deux chiffres de la ligne ne portent pas sur le meme perimetre : le 9
# compte les U13, le 30 non. La mention doit donc permettre de REFAIRE les deux.
# Deux « neuf » a deux lignes d'ecart — « 9 receptions » et « neuf restent
# conditionnelles » — faisaient comprendre que les receptions etaient
# conditionnelles, donc les affiches achetees aussi. Le chiffre visible est
# desormais celui qui est acquis, et la mention ne repete plus « neuf ».
P4_MENTION = (
    "Catégories et créneaux : {creneaux}. Réceptions : 5 seniors et 4 U13 en "
    "phase 1, toutes acquises. Calendrier seniors au 19/09/2026 : 21 dates "
    "acquises (7 journées de phase 1, 14 de phase 2) et, sous condition, "
    "4 finales selon classement et 5 tours de Coupe selon qualification, "
    "jusqu’au 23 avril 2027. Le club ne compte pas son public.")

# ---------------------------------------------------------------------------
# PAGE 5 — CE QUE VOTRE SOUTIEN PERMET
# ---------------------------------------------------------------------------
P5_SUR = "À QUOI SERT VOTRE SOUTIEN"
P5_TITRE = "CE QUE VOTRE SOUTIEN PERMET"
# « le samedi matin » reduisait le club a son creneau Baby Basket : il tourne
# cinq jours sur sept, et jusqu'au 23 avril.
P5_LEAD = ("Votre logo, c’est la contrepartie visible. Votre soutien, lui, "
           "fait tourner le club toute la saison.")

# Les quatre familles. Vocabulaire repris de mbc974.com/soutenir-le-club/ et
# de mbc974.com/benevoles/ : « materiel », « licences solidaires »,
# « encadrement », « deplacements des equipes », « on vous forme, notamment a
# la table de marque », « actions jeunesse ».
P5_FAMILLES = [
    # « Jeux de maillots FLOQUES » employait le mot que les pages 6 et 7
     # reservent au logo du PARTENAIRE : un lecteur presse comprenait que son
     # don payait son propre flocage. Et la table de marque n'est pas un poste
     # d'equipement dans le depot : c'est une mission de benevole.
     ("01", "ÉQUIPER",
     ["Ballons de match et d’entraînement",
      "Jeux de maillots aux couleurs du club",
      "Matériel de séance : plots, chasubles"]),
    # « encadrants » laissait entendre une formation diplomante de coachs, que
     # le depot n'atteste nulle part ; « officiels » (arbitres, chronometreurs)
     # non plus. Ce que le club dit former, ce sont ses BENEVOLES, notamment a
     # la table de marque — c'est ce qui reste.
     ("02", "FORMER",
     ["Formation des bénévoles du club",
      "Encadrement des jeunes catégories",
      "Formation à la table de marque"]),
    # Le site dit que les enfants PARTICIPENT a des plateaux « avec d'autres
     # clubs de l'ile » — il ne dit pas que le MBC les organise, ni qu'ils sont
     # « du quartier ».
     ("03", "ACCUEILLIR",
     ["Réceptions au gymnase, entrée libre",
      "Plateaux avec les clubs de l’île",
      "Déplacements des équipes"]),
    # La page des dons enumere limitativement ce que le soutien finance :
     # materiel, licences solidaires, encadrement, deplacements. La
     # communication n'y figure pas — « affiches, site et contenus » sortait
     # donc de la liste. Reste ce que le club publie bien comme une facon de
     # l'aider : faire connaitre le club.
     ("04", "DÉVELOPPER",
     ["Licences solidaires pour les familles",
      "Actions jeunesse à La Montagne",
      "Faire connaître le club dans le quartier"]),
]

# Les reperes PUBLIES par le club. Source : mbc974.com/soutenir-le-club/.
# Le bandeau posait une EQUIVALENCE — 20 EUR = un ballon — que la mention
# reprenait en bas de page (« n'est pas affecté à une dépense précise »). Les
# deux acheteurs a 500 et 1 000 EUR ont releve la contradiction : « si je dis
# que j'ai paye cinq licences, le club me dement en corps 8 ». Les memes
# chiffres, presentes comme des ORDRES DE GRANDEUR DES DEPENSES, ne promettent
# plus de flechage — et la mention redevient une precision.
P5_REPERES_TITRE = "CE QUE COÛTE UNE SAISON, EN REPÈRES"
P5_REPERES = [
    ("20 €", "un ballon de match pour une équipe"),
    ("95 €", "une licence offerte — le tarif de la saison"),
    ("300 €", "le déplacement d’une équipe à un tournoi"),
]
P5_OBJECTIF = ("OBJECTIF DE LA SAISON FONDATRICE",
               "10 licences solidaires, pour des familles qui en ont besoin.")

P5_MENTION = (
    "Repères publiés par le club sur {soutenir} à titre "
    "d’exemples de financement, et objectif que le club s’est fixé pour sa "
    "première saison — ce n’est pas un résultat acquis. Un partenariat est un "
    "achat de visibilité avec contreparties et facture : il entre au budget "
    "général du club et n’est pas affecté à une dépense précise.")

# ---------------------------------------------------------------------------
# PAGE 6 — VOTRE MARQUE AVEC LE MBC
# ---------------------------------------------------------------------------
P6_SUR = "OÙ VOUS APPARAISSEZ, ET CE QUE ÇA FAIT"
P6_TITRE = "VOTRE MARQUE, AVEC LE MBC"
# « Vous heritez de la chaine » : image juste, formulation artificielle.
# Les deux idees fusionnees tenaient 1 192 px pour une ligne de 1 152, et la
# 2e ligne repartait de travers. Le deux-points dit le lien de cause en 997.
# « ecosysteme » a ete ecarte : c'est du jargon, et le dossier s'en passe.
P6_LEAD = ("Le club crée et diffuse ses propres contenus : un partenariat, "
           "plusieurs points de contact.")

# LE DEFAUT LE PLUS LOURD DE LA V3 ETAIT ICI. La page decrivait toute la
# chaine — site, reseaux, affiches, flyers, evenements, maillots, gymnase —
# sans dire A PARTIR DE QUELLE FORMULE chacun demarre. Un commercant qui
# signait a 200 EUR apres avoir lu cette page pouvait de bonne foi croire
# qu'il aurait les affiches, les flyers et les evenements : la page 7 les
# reserve a 500, et le maillot a 1 000. La page publique du site souffre du
# meme defaut (« Tous les autres supports demarrent des la signature »).
# Chaque ligne porte donc desormais son PALIER, repris de la grille.
# Les quatre lignes couvrent les sept supports du site : site et reseaux ;
# affiches et flyers ; evenements ; maillots et gymnase.
P6_EFFETS = [
    ("EN LIGNE", "Site mbc974.com et réseaux du club",
     "Une présence continue toute la saison.", "dès ROOKIE · 200 €"),
    ("AFFICHES ET FLYERS", "Rencontres, créneaux, inscriptions",
     "Votre marque sur nos imprimés.", "dès MVP · 500 €"),
    ("AU CONTACT DU PUBLIC", "Invitations et temps forts du club",
     "Présent, et pas seulement visible.", "dès MVP · 500 €"),
    # « Flocage, bache OU panneau » : la grille de la page 7 vend les deux
     # comme deux items distincts a All-Star. Le « ou » laissait croire a un
     # choix — un ecart qui se regle mal en avril.
     ("SUR LE MAILLOT ET AU GYMNASE", "Flocage et bâche ou panneau*",
     "Une visibilité portée par les joueurs.", "dès ALL-STAR · 1 000 €"),
]

# L'emplacement rare. Source : la page publique (« Deux des emplacements
# partenaires y sont deja occupes ») + les photos du 18/09/2026.
P6_RARETE = ["1 EMPLACEMENT.", "1 PARTENAIRE.", "1 SAISON."]
# L'asterisque manquait a la promesse la PLUS forte de la page — un panneau
# pleine hauteur, une photo, trois lignes en capitales — alors que toutes les
# autres mentions de flocage le portaient. Un acheteur aurait pu soutenir que
# l'encart etait un engagement ferme.
P6_RARETE_ETIQ = "DOS DU MAILLOT SENIORS 2026/2027*"
# « Disponible. » etait defini et jamais imprime : le seul mot qui dit que
# l'emplacement est a prendre ne figurait pas dans le PDF.
P6_RARETE_ETAT = "Disponible."
# « trois marques » face a « cinq partenaires » page 3 : la phrase qui
# reconciliait les deux comptes avait disparu de la V3.
P6_RARETE_TEXTE = "La face en porte trois, équipementier compris."
# Le flocage appartient a All-Star ; le DOS, lui, reste a negocier — aucun
# tarif specifique n'a ete valide par le bureau.
P6_RARETE_OFFRE = "Le flocage entre dans All-Star. Pour le dos, parlons-en."

# La version precedente promettait que CINQ supports demarraient des la
# signature — or une affiche depend d'une reception a venir et un flyer d'une
# campagne. Seul le numerique demarre vraiment tout de suite.
P6_DEMARRE = ("La visibilité en ligne démarre dès validation ; les autres "
              "supports suivent le calendrier du club.")

P6_MENTION = (
    "* Flocage, bâche et panneau dépendent du planning de l’équipementier, des "
    "emplacements disponibles et, pour le gymnase, de l’autorisation de la "
    "Ville — le club vous le dit dès le premier échange. Photographie du "
    "18/09/2026. Le site a enregistré ~1 130 apparitions dans Google sur trois "
    "mois glissants, en position moyenne 5 (Search Console, fin août 2026) : "
    "des apparitions du site, pas des personnes.")

# ---------------------------------------------------------------------------
# PAGE 7 — LES FORMULES
# ---------------------------------------------------------------------------
P7_SUR = "LA GRILLE PUBLIQUE DU CLUB"
P7_TITRE = "QUATRE FORMULES, DÈS 200 €"
# « Tout est adaptable » ouvrait aussi bien les contreparties que le PRIX,
# juste au-dessus d'une grille que la mention dit reprise « au centime ».
P7_LEAD = ("Chaque formule inclut la précédente. Contreparties adaptables, "
           "en euros, en matériel ou en services.")

# Les quatre formules de mbc974.com/sponsor-club-basket-reunion/, reprises au
# centime. Les LIVRABLES sont ceux du site ; la ligne en gris qui les suit dit
# ce qu'ils valent concretement, sans rien promettre de neuf.
P7_FORMULES = [
    dict(nom="ROOKIE", prix="200", populaire=False,
         tempo="Votre logo en ligne, dès la signature.",
         lignes=[("Votre logo sur le site", "présent sur mbc974.com"),
                 ("Mention sur nos réseaux", "Facebook, Instagram, TikTok"),
                 ("Remerciements en fin de saison", "publication du club")]),
    dict(nom="MVP", prix="500", populaire=True,
         tempo="Pour une présence régulière sur nos principaux supports.",
         # « une affiche PAR reception » devenait un engagement chiffrable
         # des que la page 4 annonce 9 receptions — dont 4 U13, dont rien ne
         # dit qu'elles ont une affiche.
         lignes=[("Logo sur les affiches", "à chaque réception"),
                 ("Logo sur les flyers", "créneaux, inscriptions, événements"),
                 ("Une publication dédiée", "sur les réseaux du club"),
                 ("Invitations aux événements", "vous êtes sur place"),
                 ("Inclut Rookie", "")]),
    dict(nom="ALL-STAR", prix="1 000", populaire=False,
         tempo="Jusque sur le maillot et au gymnase.",
         # La page 6 montre le DOS en pleine page et dit qu'il se negocie a
         # part ; la page 7 disait « les maillots » sans preciser lequel. Un
         # service com lit « le dos ».
         lignes=[("Logo floqué sur les maillots*", "emplacement défini avec le club"),
                 ("Bâche ou panneau au gymnase*", "vu à chaque réception"),
                 ("Mise en avant toute la saison", "jusqu’au 23 avril 2027"),
                 ("Inclut MVP", "")]),
    dict(nom="HALL OF FAME", prix="2 000", suffixe="+", populaire=False,
         tempo="Votre secteur d’activité, à vous seul.",
         # « un seul partenaire par metier » ouvrait un debat sur ce qu'est un
         # metier ; « votre marque en tete des supports » etait pire, une
         # promesse que rien ne fondait. Les deux renvoient desormais a la
         # convention, seul document ou ces perimetres se definissent.
         lignes=[("Exclusivité dans votre secteur", "périmètre défini dans la convention"),
                 ("Partenaire titre d’un événement", "événement défini à la signature"),
                 ("Prise de parole lors des remises", "devant les familles"),
                 ("Visibilité premium", "définie avec vous dans la convention"),
                 ("Inclut All-Star", "")]),
]

# P7_FIDELITE et P7_SURMESURE ont ete retires : ils etaient definis et jamais
# imprimes. La fidelite vit desormais dans la mention de la page 7, le sur
# mesure dans son chapo et a l'etape 02 de la page 8.

P7_MENTION = (
    "Grille publique de {sponsor}, reprise au centime ; les précisions en gris "
    "situent les contreparties, elles n’en créent pas. Fidélité : −10 % sur "
    "deux saisons, −20 % et mention « Partenaire fidèle » sur trois. "
    "* Flocage, bâche et panneau sous réserve du planning de l’équipementier, "
    "des emplacements disponibles et de l’autorisation de la Ville.")

# ---------------------------------------------------------------------------
# PAGE 8 — FAISONS ÉQUIPE
# ---------------------------------------------------------------------------
P8_TITRE = "FAISONS<br>ÉQUIPE"
P8_LEAD = "20 minutes suffisent pour construire votre partenariat."

# Le contact nominatif. Le titre de secretaire vient du bureau : il n'est
# ecrit nulle part sur le site, qui ne publie pas la composition du bureau.
# A verifier avant diffusion. Variante sans contact nominatif :
# `python dossier_v3.py --sans-contact`.
P8_CONTACT = ("VOTRE CONTACT PARTENARIAT", "Alexandre Debieuvre · Secrétaire du MBC")
P8_CONTACT_SANS = ("PARLER À QUELQU’UN", "Le club répond en général sous 48 h.")

P8_MAIL = "contact@mbc974.com"
P8_TEL = "0692 55 64 58"

# « En ligne, puis sur le terrain » decrivait le parcours d'un ALL-STAR, pas
# celui d'un ROOKIE : c'etait la derniere chose lue avant d'appeler.
P8_ETAPES = [("01", "On échange", "Sans engagement, 20 minutes."),
             ("02", "On choisit ou on adapte", "Une formule, ou du sur mesure."),
             ("03", "Votre visibilité démarre", "En ligne, puis selon la formule.")]

# La reponse a « comment je sais que le club fera ce qu'il promet ? ».
# Chaque ligne ne promet que ce que le club peut reellement livrer : aucune
# n'annonce de ROI, de ventes, d'impressions ni de frequentation, puisque le
# club ne mesure rien de tout cela — et le dossier le dit page 4.
P8_ENGAGEMENTS = [
    ("CONVENTION ÉCRITE", "Supports, durée et contreparties définis."),
    ("VISUELS VALIDÉS", "Vos éléments de marque validés avant diffusion."),
    # PAS un mot de « retombees » ni de « resultats » : le club ne mesure ni
    # frequentation, ni clics (aucun parametre utm_ dans tout le depot), ni
    # audience reseaux — et les pages 3 et 4 le disent. Ce qui est promis ici
    # est exactement ce qu'il peut sortir : la liste de ce qui a ete diffuse.
    ("BILAN PARTENAIRE", "En fin de saison : supports diffusés, publications et liens."),
]

# « Message pre-rempli » etait FAUX pour le QR : il encode l'URL nue. Le lien
# cliquable, lui, porte bien le message. La legende doit etre vraie des deux
# cotes — elle ne promet donc plus rien que le scan ne tienne pas.
P8_QR = [("qr-whatsapp.svg", "whatsapp", "ÉCRIRE AU CLUB",
          "WhatsApp · réponse<br>en général sous 48 h."),
         ("qr-partenaires.svg", "partenaires", "LA PAGE PARTENAIRES",
          "La grille, en ligne.")]

# L'etat civil tenait un encart ; il descend dans la mention, ou un service
# achats sait le chercher. La phrase sur le mecenat est ramenee au minimum :
# le dossier vend du partenariat avec contreparties et facture, pas du don.
P8_ETAT_CIVIL = ("Association loi 1901 créée en 2026 · affiliation FFBB "
                 "REU0974104 · RNA W9R1011179 · SIREN 104 461 124 · siège : "
                 "23 Chemin des Alizés, La Montagne, 97417 Saint-Denis.")

# Le mecenat suppose l'absence de contrepartie significative ; le dossier vend
# quatre formules de contreparties. Suggerer le mecenat trois pages plus loin
# contredisait la page 5. La mention ne dit donc plus que ce qui est certain :
# il y a une facture. La couverture media est remontee page 3, ou l'on parle
# de presse.
P8_MENTION = (
    P8_ETAT_CIVIL +
    " Le partenariat fait l’objet d’une facture ; si votre soutien prend une"
    " autre forme, parlons-en.")

P8_DEVISE = "La Montagne en lèr !"
