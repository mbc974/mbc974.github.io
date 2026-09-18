# -*- coding: utf-8 -*-
"""Genere le dossier de partenariat MBC x OLA Energy (10 pages, 16:9).

LE PRINCIPE DE MISE EN PAGE. Les huit pages de contenu partagent exactement le
meme squelette, au pixel :

    56   haut des capitales du surtitre
    96   haut des capitales du titre  (Anton 64 px, UNE ligne, toujours)
   185   haut des capitales du sous-titre
   232   premiere ligne de contenu
   588   derniere ligne de contenu
   648   filet du pied
   664   signature du pied et numero de page

Le dossier d'origine n'avait rien de tel : neuf tailles de titre pour dix pages
(49,5 a 84,75 pt, la taille ayant visiblement ete rabaissee page par page pour
faire tenir le texte), sept ecarts differents entre la mention et le pied, et
jusqu'a six bords gauches sur une meme page. Ici tout decoule de grille.py et
des metriques reelles des polices du site (typo.py), et verifier.py le controle.
"""
import sys
import typo
import grille as G
import css, contenu as C
from bloc import (txt, lignes, filet, filet_v, pave, image, qr, pied,
                  surtitre, titre, cap_apres_titre, Y_FILET, CAP_PIED)

CAP_SURTITRE = 56
CAP_TITRE = 96
CAP_SOUS = cap_apres_titre(1)          # 185
HAUT_CONTENU = 232
BAS_CONTENU = 588                      # 356 px de bande utile, sur chaque page
BANDE = BAS_CONTENU - HAUT_CONTENU

# Le « € » d'Anton culmine a 0,7695 em quand un chiffre culmine a 0,8672 em :
# a taille egale il est visiblement plus petit. 0,8672/0,7695 = 1,127 le remet
# exactement a la hauteur des chiffres, sur la meme ligne de base, sans transform
# — c'est le « € blanc a la taille du chiffre » demande pour les gros montants.
# L'espace fine avant le symbole est un retrait CSS et non un caractere :
# l'espace fine insecable U+202F est absente des sous-ensembles du site.
EURO = '<span style="font-size:1.127em;margin-left:.10em">&euro;</span>'


# Les decrochages INTERIEURS assumes : gouttiere de chiffres, retrait de carte,
# intitule a cote d'un QR, signature a cote du logo. Le garde-fou les importe
# d'ici plutot que d'en garder une copie, qui derivait a chaque reglage.
QR_P2 = 100          # cote des plaques de QR de la page 2
QR_P10 = 96          # idem page 10
GOUT_CHIFFRE_P3 = 146
GOUT_CHIFFRE_P6 = 104
GOUT_CHIFFRE_P9 = 176
RETRAIT_CARTE = 26

def decrochages():
    """Les x, en px, ou du texte commence legitimement hors colonne."""
    import grille as G
    return [
        G.MARGE + 100,                       # « MBC x OLA ENERGY » a cote du logo
        G.x(7) + GOUT_CHIFFRE_P3,            # libelles des chiffres, page 3
        G.x(6) + GOUT_CHIFFRE_P6,            # idem page 6
        G.x(8) + GOUT_CHIFFRE_P9,            # identifiants, page 9
        G.x(7) + QR_P2 + 24,                 # intitules a cote des QR, page 2
        G.x(9) + QR_P10 + 22,                # idem page 10
        G.x(9) + 62,                         # intitules a cote des numeros, page 4
        G.x(1) + RETRAIT_CARTE,              # retrait des trois cartes, page 8
        G.x(5) + RETRAIT_CARTE,
        G.x(9) + RETRAIT_CARTE,
        G.x(9) + G.w(4) - RETRAIT_CARTE
        - (round(G.largeur_texte("surtitre", "RECOMMANDÉ")) + 24) + 12,
    ]


def page(classe, corps):
    return '<section class="p %s">%s</section>' % (classe, corps)


def entete(sur, tit, sous=None, sombre=False, left=G.MARGE, largeur=None,
           couleur_sur=None, lignes_titre=1):
    """Le bloc d'en-tete, identique sur les huit pages de contenu."""
    c_tit = "c-blanc" if sombre else "c-encre"
    c_sous = "c-glacier" if sombre else "c-douce"
    o = [surtitre(sur, cap=CAP_SURTITRE, couleur=couleur_sur or
                  ("c-orange" if sombre else "c-roi"), left=left),
         titre(tit, cap=CAP_TITRE, left=left, couleur=c_tit,
               largeur=largeur or G.CONTENU)]
    if sous:
        o.append(txt("lead", sous, left=left, cap=cap_apres_titre(lignes_titre),
                     couleur=c_sous, largeur=largeur or G.CONTENU))
    return "".join(o)


# ===========================================================================
# 1 - COUVERTURE
# ===========================================================================
def p1(variante="a"):
    o = []
    o.append(image("couverture.jpg", 0, 0, G.W, G.H, pos="46% 52%",
                   alt="L'ecole de basket du MBC en regroupement au gymnase de La Montagne."))
    # Voile : opaque en bas a gauche, transparent en haut a droite. La photo
    # continue SOUS le texte au lieu d'etre coupee par une arete verticale,
    # comme l'etait la couverture d'origine (panneau bleu | photo, sans liaison,
    # avec un titre qui finissait a 16 pt du raccord pour 45 de marge a gauche).
    o.append(pave(0, 0, G.W, G.H, "none", extra=(
        "background:linear-gradient(104deg,"
        "rgba(13,21,38,.95) 0%,rgba(13,21,38,.90) 30%,"
        "rgba(13,21,38,.60) 54%,rgba(13,21,38,.20) 76%,rgba(13,21,38,.08) 100%)")))
    o.append(pave(0, G.H - 320, G.W, 320, "none", extra=(
        "background:linear-gradient(0deg,rgba(13,21,38,.90) 0%,rgba(13,21,38,0) 100%)")))

    o.append(image("mbc-logo.png", G.MARGE, 48, 78, 80, extra="object-fit:contain"))
    o.append(txt("fort-l", "MBC <span style=\"color:var(--orange)\">&times;</span> OLA ENERGY",
                 left=G.MARGE + 100, cap=75, couleur="c-blanc", brut=True))

    T = {
        "a": ("PRENEZ PLACE<br>MAINTENANT", "La saison fondatrice se joue ici."),
        "b": ("L&rsquo;&Eacute;NERGIE<br>D&rsquo;UNE SAISON",
              "La saison fondatrice du club se joue maintenant."),
        "c": ("LA PROCHAINE<br>IMAGE EST<br>LA V&Ocirc;TRE",
              "La saison fondatrice se joue ici."),
    }[variante]
    nl = T[0].count("<br>") + 1
    # Le titre est pose par le BAS : sa derniere ligne reste au meme endroit
    # quel que soit le nombre de lignes de la variante.
    pas = G.STYLES["d1"][1] * G.STYLES["d1"][2]
    o.append(titre(T[0], cap=396 - (nl - 1) * pas, left=G.MARGE,
                   couleur="c-blanc", largeur=880, style="d1"))
    o.append(txt("lead", T[1], left=G.MARGE, cap=544, couleur="c-glacier", largeur=620))

    o.append(filet(G.MARGE, 600, 320, "r-orange", 2))
    o.append(txt("pied", C.PIED_MENTION_P1, left=G.MARGE, cap=632, couleur="c-glacier"))
    o.append(txt("pied", "mbc974.com", right=G.MARGE, cap=632, couleur="c-glacier",
                 align="right"))
    return page("f-nuit", "".join(o))


# ===========================================================================
# 2 - CE QUI EST DEJA EN LIGNE
# ===========================================================================
def p2():
    o = [entete("CE QUI EST DÉJÀ EN LIGNE", "OUVREZ LE SITE",
                "Trois preuves à un clic. Aucune n’a besoin de nous.")]

    IM_X, IM_W = G.x(1), G.w(6)
    IM_H = round(IM_W * 712 / 1265)                 # 317 : la capture entiere
    IM_Y = HAUT_CONTENU + 30
    o.append(txt("etiquette", "mbc974.com · 27 pages publiées", left=IM_X,
                 cap=HAUT_CONTENU, couleur="c-encre"))
    o.append(pave(IM_X, IM_Y, IM_W, IM_H, "var(--papier-2)"))
    o.append(image("site.jpg", IM_X, IM_Y, IM_W, IM_H, pos="50% 0%",
                   alt="La page d'accueil de mbc974.com."))

    # Trois preuves au meme gabarit : plaque de QR identique, intitule et
    # sous-ligne aux memes retraits, un filet entre chacune. D'origine les deux
    # QR d'une meme colonne etaient a 7,5 pt l'un de l'autre en horizontal, de
    # trois tailles differentes (87 / 87 / 78,75 pt), et l'un n'avait pas de
    # legende du tout.
    CX, CW, QT = G.x(7), G.w(6), QR_P2
    PREUVES = [
        ("qr-reportage.svg", "RÉUNION LA 1ÈRE",
         "Sujet &laquo;&nbsp;Grand Sport&nbsp;&raquo; du 13/09/2026,<br>3 min 14 sur le club."),
        ("qr-instagram.svg", "@MBC974.RE",
         "Facebook, Instagram et TikTok,<br>liés depuis les 27 pages du site."),
        ("qr-ffbb.svg", "FICHE FFBB PUBLIQUE",
         "Affiliation REU0974104,<br>vérifiable chez la fédération."),
    ]
    PAS = 124
    for i, (q, lab, sub) in enumerate(PREUVES):
        yy = HAUT_CONTENU + i * PAS
        if i:
            o.append(filet(CX, yy - 24, CW, "r-clair"))
        o.append(pave(CX, yy, QT, QT, "var(--blanc)"))
        o.append(qr(q, CX + 7, yy + 7, QT - 14))
        o.append(txt("etiquette-s", lab, left=CX + QT + 24, cap=yy + 14, couleur="c-encre"))
        o.append(txt("petit", sub, left=CX + QT + 24, cap=yy + 42, couleur="c-douce",
                     largeur=CW - QT - 24, brut=True))

    o.append(pied("02", sombre=False, mention=(
        "Le reportage est un sujet publié le 13/09/2026 sur la page Facebook de Réunion la "
        "1ère. Le club ne dispose d’aucun chiffre d’audience, de vues ni d’abonnés : "
        "il n’en avance aucun.")))
    return page("f-papier", "".join(o))


# ===========================================================================
# 3 - LES CHIFFRES DE LA SAISON FONDATRICE
# ===========================================================================
def p3():
    o = [entete("SAISON FONDATRICE 2026/2027", "LES CHIFFRES, SANS ARRONDI",
                "Un club de six mois, deux équipes en championnat, un tarif unique.",
                sombre=True, couleur_sur="c-blanc")]

    HX = G.x(1)
    o.append(txt("surtitre", "PRÈS DE", left=HX, cap=HAUT_CONTENU + 28,
                 couleur="c-orange"))
    o.append(txt("stat-xl", "100", left=HX, cap=HAUT_CONTENU + 68, couleur="c-blanc"))
    o.append(filet(HX, HAUT_CONTENU + 224, G.w(4), "r-roi", 2))
    o.append(txt("fort", "Adhésions et préinscriptions", left=HX,
                 cap=HAUT_CONTENU + 252, couleur="c-blanc", largeur=G.w(5)))
    o.append(txt("petit", "au 18 septembre 2026", left=HX, cap=HAUT_CONTENU + 282,
                 couleur="c-glacier", largeur=G.w(5)))

    # Les nombres occupent une gouttiere de largeur FIXE : tous les libelles
    # commencent donc exactement au meme x. D'origine les libelles d'une meme
    # rangee etaient a 50,25 / 643,5 / 843 pt, sur deux grilles incompatibles
    # (deux colonnes en haut, trois en bas), et de deux corps differents.
    LX, NUM_W = G.x(7), GOUT_CHIFFRE_P3
    PAS = 66
    for i, (val, lib, _s) in enumerate(C.CHIFFRES[1:]):
        yy = HAUT_CONTENU + 16 + i * PAS
        o.append(filet(LX, yy - 20, G.w(6), "r-roi"))
        v = val.replace(" €", EURO).replace(" €", EURO).replace("€", EURO)
        o.append(txt("stat-m", v, left=LX, cap=yy, couleur="c-orange", brut=True))
        o.append(txt("corps-s", lib, left=LX + NUM_W, cap=yy + 11, couleur="c-blanc",
                     largeur=G.w(6) - NUM_W))
    o.append(filet(LX, HAUT_CONTENU + 16 + 5 * PAS - 20, G.w(6), "r-roi"))

    o.append(pied("03", sombre=True, mention=(
        "Effectifs communiqués par le club au 18/09/2026, adhésions et préinscriptions "
        "confondues : ce ne sont pas des licences FFBB qualifiées. Score du 11/09/2026 "
        "communiqué par le club, le relevé de la Ligue n’est pas encore publié.")))
    return page("f-roi", "".join(o))


# ===========================================================================
# 4 - SIMULATIONS DE VISIBILITE
# ===========================================================================
def p4():
    o = [entete("SIMULATIONS DE VISIBILITÉ", "OÙ VOTRE LOGO SERAIT VU",
                "Quatre supports que le club produit lui-même, montrés en situation.")]

    # Le visuel occupe TOUTE la bande de contenu : c'est la page qui doit faire
    # voir la marque. D'origine il flottait avec 21 pt d'air au-dessus et 8,7
    # au-dessous, et sa legende etait centree sur un axe qui n'existait pas
    # (39 pt hors du centre de l'image, a cote d'un intitule cale a la marge).
    IM_X, IM_W, IM_H = G.x(1), G.w(7), BANDE
    o.append(pave(IM_X, HAUT_CONTENU, IM_W, IM_H, "var(--papier-2)"))
    o.append(image("simulations.jpg", IM_X, HAUT_CONTENU, IM_W, IM_H, pos="50% 46%",
                   alt="Simulations : bache de terrain, kakemono, affiche de match, site et story."))

    CX, CW = G.x(9), G.w(4)
    SUP = [("La bâche de terrain", "et le kakémono du gymnase*"),
           ("L’affiche de match", "produite à chaque réception"),
           ("La page du match", "et son image de partage"),
           ("Le mur des partenaires", "logo, nom et lien sortant")]
    PAS = 88
    for i, (t, s) in enumerate(SUP):
        yy = HAUT_CONTENU + 8 + i * PAS
        o.append(txt("stat-m", "0%d" % (i + 1), left=CX, cap=yy,
                     extra="color:var(--papier-3)"))
        o.append(txt("etiquette-s", t, left=CX + 62, cap=yy + 2, couleur="c-encre"))
        o.append(txt("petit", s, left=CX + 62, cap=yy + 28, couleur="c-douce",
                     largeur=CW - 62))

    o.append(pied("04", sombre=False, mention=(
        "* Visuels de travail. Formats et implantations à convenir entre OLA, le club et la "
        "Ville de Saint-Denis : le gymnase et le plateau sont des équipements municipaux, "
        "la bâche et le floquage restent soumis à autorisation. Un emplacement du maillot "
        "est déjà occupé par l’équipementier du club.")))
    return page("f-papier", "".join(o))


# ===========================================================================
# 5 - LE TERRITOIRE
# ===========================================================================
def p5():
    o = []
    o.append(image("territoire.jpg", 0, 0, G.W, G.H, pos="44% 50%",
                   alt="Le plateau couvert de Ruisseau Blanc, a La Montagne, ouvert sur la mer."))
    PAN_X = G.x(7) - G.GOUT
    o.append(pave(PAN_X - 130, 0, 130, G.H, "none", extra=(
        "background:linear-gradient(90deg,rgba(13,21,38,0),rgba(13,21,38,.97))")))
    o.append(pave(PAN_X, 0, G.W - PAN_X, G.H, "rgba(13,21,38,.97)"))

    TX, TW = G.x(7), G.w(6)
    o.append(entete("LA MONTAGNE · SAINT-DENIS", "UN QUARTIER,<br>DEUX TERRAINS",
                    "Des enfants dès 3 ans, des familles, des adultes. "
                    "Le même quartier, cinq jours sur sept.",
                    sombre=True, left=TX, largeur=TW, lignes_titre=2))

    LIEUX = [("GYMNASE DE LA MONTAGNE", "Chemin des Bauhinias · salle couverte",
              "7 des 9 créneaux hebdomadaires"),
             ("PLATEAU DE RUISSEAU BLANC", "Plateau couvert, en plein air",
              "Inauguré en août 2026 avec la Ville")]
    y = 352
    for i, (nom, l1, l2) in enumerate(LIEUX):
        yy = y + i * 104
        o.append(filet(TX, yy - 28, TW, "r-sombre"))
        o.append(txt("etiquette-s", nom, left=TX, cap=yy, couleur="c-orange"))
        o.append(txt("corps-s", l1, left=TX, cap=yy + 30, couleur="c-blanc", largeur=TW))
        o.append(txt("petit", l2, left=TX, cap=yy + 56, couleur="c-glacier", largeur=TW))
    o.append(filet(TX, y + 2 * 104 - 28, TW, "r-sombre"))
    o.append(txt("fort", "Toutes nos réceptions sont en entrée libre.",
                 left=TX, cap=y + 2 * 104 + 2, couleur="c-blanc", largeur=TW))

    # La mention reste DANS le panneau sombre : posee a la marge de gauche comme
    # sur les autres pages, elle tombait sur la photo en plein soleil.
    # Le pied ENTIER vit dans le panneau : pose a la marge de gauche comme sur
    # les autres pages, le filet et la signature couraient sur la photo en plein
    # soleil, ou ils etaient illisibles.
    o.append(filet(TX, Y_FILET, TW, "r-sombre"))
    o.append(txt("mention", "Deux équipements municipaux que le club fait vivre. "
                 "Ansanm nou lé pli for.", left=TX, bottom=G.H - Y_FILET + 14,
                 largeur=TW, couleur="c-glacier"))
    o.append(txt("pied", "MBC × OLA ENERGY  ·  SAISON 2026/2027", left=TX,
                 cap=CAP_PIED, couleur="c-glacier"))
    o.append(txt("pagenum", "05", right=G.MARGE, cap=CAP_PIED, couleur="c-glacier",
                 align="right"))
    return page("f-nuit", "".join(o))


# ===========================================================================
# 6 - CE QUE VOUS RECEVEZ
# ===========================================================================
def p6():
    o = []
    # L'affiche joueur devient une colonne a fond perdu : c'est une affiche
    # GRAVEE (nom et numero dans l'image), on ne lui ajoute donc aucune legende.
    # D'origine elle commencait a 63,85 pt pour une marge de 48, et s'arretait
    # a 4,6 pt de la mention.
    AF_W = G.MARGE + G.w(4)
    o.append(image("affiche-joueur.jpg", 0, 0, AF_W, G.H, pos="52% 22%",
                   alt="Affiche de joueur produite par le club."))

    TX, TW = G.x(6), G.w(7)
    # Le titre ne tient pas sur une ligne dans une colonne de 662 px (il en
    # demande 802) : on POSE la coupe au lieu de la laisser au renvoi, et on
    # declare deux lignes pour que le sous-titre descende d'autant.
    o.append(entete("CE QUE VOUS RECEVEZ", "DES IMAGES,<br>PAS DES PROMESSES",
                    "Le club photographie, écrit et publie lui-même.",
                    left=TX, largeur=TW, lignes_titre=2))

    ITEMS = [("24", "photos du club publiées, en trois formats",
              "Le club n’achète aucune image."),
             ("10", "affiches de joueurs, prêtes pour un co-branding",
              "Plus une affiche à chaque réception."),
             ("7", "pages de match, chacune avec son image de partage",
              "Et son fichier d’agenda téléchargeable."),
             ("48", "heures pour mettre un logo ou une actualité en ligne",
              "Le site est généré depuis ses données.")]
    PAS, NUM_W = 74, GOUT_CHIFFRE_P6
    for i, (n, t, s) in enumerate(ITEMS):
        yy = HAUT_CONTENU + 84 + i * PAS
        o.append(filet(TX, yy - 24, TW, "r-clair"))
        o.append(txt("stat-m", n, left=TX, cap=yy + 2, couleur="c-roi"))
        o.append(txt("corps-s", t, left=TX + NUM_W, cap=yy, couleur="c-encre",
                     largeur=TW - NUM_W))
        o.append(txt("petit", s, left=TX + NUM_W, cap=yy + 26, couleur="c-douce",
                     largeur=TW - NUM_W))
    o.append(filet(TX, HAUT_CONTENU + 84 + 4 * PAS - 24, TW, "r-clair"))

    # Pied cantonne a la colonne de texte : le filet et la signature ne doivent
    # pas courir sur l'affiche a fond perdu.
    o.append(filet(TX, Y_FILET, TW, "r-clair"))
    o.append(txt("mention", "Photothèque publiée du club : 24 visuels, 182 fichiers. "
                 "Les droits d’usage sont définis support par support dans la convention.",
                 left=TX, bottom=G.H - Y_FILET + 14, largeur=TW, couleur="c-douce"))
    o.append(txt("pied", "MBC × OLA ENERGY  ·  SAISON 2026/2027", left=TX,
                 cap=CAP_PIED, couleur="c-douce"))
    o.append(txt("pagenum", "06", right=G.MARGE, cap=CAP_PIED, couleur="c-encre",
                 align="right"))
    return page("f-papier", "".join(o))


# ===========================================================================
# 7 - L'ACTIVATION EN 30 JOURS
# ===========================================================================
def p7():
    o = [entete("PROPOSITION D’ACTIVATION", "VISIBLE EN TRENTE JOURS",
                "Les dates ne sont pas à inventer : elles sont déjà au calendrier.",
                sombre=True)]

    # Le numero est EMPILE au-dessus de son intitule. D'origine l'intitule etait
    # pose a distance fixe du bord de colonne, si bien que l'ecart au chiffre
    # valait 45, 36 puis 34 pt selon la largeur du numero : trois ecarts pour
    # un seul et meme motif.
    Y_NUM = HAUT_CONTENU + 48
    Y_FIL = Y_NUM + 112
    Y_LAB = Y_FIL + 28
    Y_LIS = Y_LAB + 44
    for i, (num, lab, items) in enumerate(C.ETAPES):
        CX, CW = G.x(1 + i * 4), G.w(4)
        o.append(txt("num", num, left=CX, cap=Y_NUM, couleur="c-orange"))
        o.append(filet(CX, Y_FIL, CW, "r-sombre"))
        o.append(txt("etiquette", lab, left=CX, cap=Y_LAB, couleur="c-blanc"))
        o.append(lignes("corps-s", items, left=CX, cap=Y_LIS, pas=32,
                        couleur="c-glacier", largeur=CW))
        if i < 2:
            haut = Y_NUM - 16
            bas = Y_LIS + 2 * 32 + 22
            o.append(filet_v(CX + CW + G.GOUT / 2 - 0.5, haut, bas - haut, "r-sombre"))

    o.append(pied("07", sombre=True, mention=(
        "Calendrier à compter de la signature. Dates sportives sous réserve du calendrier "
        "officiel : une rencontre peut être déplacée, le calendrier à jour vit sur "
        "mbc974.com/matchs/.")))
    return page("f-nuit", "".join(o))


# ===========================================================================
# 8 - LES TROIS PALIERS
# ===========================================================================
def p8():
    o = [entete("TROIS FAÇONS DE PRENDRE PLACE", "LA MÊME GRILLE QU’EN LIGNE",
                "Les formules du club sont publiques. Voici les trois qui visent OLA.")]

    # Trois cartes de gabarit STRICTEMENT identique : meme largeur, meme hauteur,
    # meme retrait sur les quatre cotes. La hauteur DECOULE du contenu (retrait
    # bas = retrait haut) et la carte est calee par le BAS sur la bande utile,
    # pour ne jamais empieter sur la mention.
    #
    # D'origine, deux colonnes etaient nues et la troisieme une carte au retrait
    # dissymetrique (24 pt a gauche, 60 a droite) qui laissait 98 pt de bleu vide
    # sous son dernier mot, a 4,7 pt de la mention.
    PAD = RETRAIT_CARTE
    D_NOM = PAD                       # decalages RELATIFS au haut de la carte
    D_TEMPO = D_NOM + 26
    D_PRIX = D_TEMPO + 34
    D_DUREE = D_PRIX + 76
    D_FIL = D_DUREE + 28
    D_LIS = D_FIL + 24
    PAS_LIS = 25
    NB_LIS = max(len(p["lignes"]) for p in C.PALIERS)
    bas_encre = D_LIS + (NB_LIS - 1) * PAS_LIS +         typo.metrics("barlow")["cap"] * G.STYLES["petit"][1]
    CARD_H = round(bas_encre + PAD)
    CARD_Y = BAS_CONTENU - CARD_H
    assert CARD_Y > CAP_SOUS + 30, CARD_Y

    for i, p in enumerate(C.PALIERS):
        CX, CW = G.x(1 + i * 4), G.w(4)
        reco = p["recommande"]
        o.append(pave(CX, CARD_Y, CW, CARD_H,
                      "var(--roi)" if reco else "var(--papier-2)"))
        ix, iw = CX + PAD, CW - 2 * PAD
        c_nom = "c-blanc" if reco else "c-roi"
        c_txt = "c-blanc" if reco else "c-encre"
        c_dim = "c-glacier" if reco else "c-douce"
        o.append(txt("etiquette-s", p["nom"], left=ix, cap=CARD_Y + D_NOM,
                     couleur=c_nom))
        if reco:
            # La recommandation est une pastille DANS la carte, pas un bandeau
            # au-dessus : les trois cartes gardent ainsi exactement la meme
            # hauteur et le meme haut. Sa largeur est MESUREE sur le texte, pas
            # devinee : 118 px devines pour 114,3 px d'encre laissaient le E
            # accentue deborder du fond orange.
            P_INT = 12
            p_larg = round(G.largeur_texte("surtitre", "RECOMMANDÉ")) + 2 * P_INT
            p_x = CX + CW - PAD - p_larg
            o.append(pave(p_x, CARD_Y + D_NOM - 7, p_larg, 27, "var(--orange)"))
            o.append(txt("surtitre", "RECOMMANDÉ", left=p_x + P_INT,
                         cap=CARD_Y + D_NOM, couleur="c-blanc"))
        o.append(txt("petit", p["tempo"], left=ix, cap=CARD_Y + D_TEMPO,
                     couleur=c_dim, largeur=iw))
        o.append(txt("prix", p["prix"] + EURO, left=ix, cap=CARD_Y + D_PRIX,
                     couleur=c_txt, brut=True))
        o.append(txt("petit", p["duree"], left=ix, cap=CARD_Y + D_DUREE,
                     couleur=c_dim, largeur=iw))
        o.append(filet(ix, CARD_Y + D_FIL, iw, "r-roi" if reco else "r-clair"))
        o.append(lignes("petit", p["lignes"], left=ix, cap=CARD_Y + D_LIS,
                        pas=PAS_LIS, couleur=c_txt, largeur=iw))

    o.append(pied("08", sombre=False, mention=(
        "Grille publique du club sur mbc974.com : Rookie 200 €, MVP 500 €, "
        "All-Star 1 000 €, Hall of Fame 2 000 € et plus — chaque formule inclut "
        "la précédente. Fidélité : −10 % sur deux saisons, −20 % sur trois. "
        "* Maillot et bâche sous réserve d’autorisation. Soutien en nature possible "
        "(carburant, mobilité des équipes), valorisé au même niveau.")))
    return page("f-papier", "".join(o))


# ===========================================================================
# 9 - LE CADRE
# ===========================================================================
def p9():
    o = [entete("LE CADRE DU PARTENARIAT", "UN CLUB DÉCLARÉ",
                "Tout ce qu’un service achats demande, en une page.", sombre=True)]

    IM_X, IM_W, IM_H = G.x(1), G.w(6), BANDE - 48
    o.append(image("officiels.jpg", IM_X, HAUT_CONTENU, IM_W, IM_H, pos="50% 36%",
                   alt="Le MBC avec les elus de la Ville de Saint-Denis."))
    o.append(txt("petit", "Inauguration du plateau de Ruisseau Blanc avec la Ville, "
                 "août 2026.", left=IM_X, cap=HAUT_CONTENU + IM_H + 24,
                 couleur="c-glacier", largeur=IM_W))

    TX, TW = G.x(8), G.w(5)
    IDENT = [("AFFILIATION FFBB", "REU0974104"),
             ("N° RNA", "W9R1011179"),
             ("SIREN", "104 461 124")]
    for i, (k, v) in enumerate(IDENT):
        yy = HAUT_CONTENU + 8 + i * 58
        o.append(filet(TX, yy - 20, TW, "r-sombre"))
        o.append(txt("petit", k, left=TX, cap=yy + 4, couleur="c-glacier"))
        o.append(txt("stat-s", v, left=TX + GOUT_CHIFFRE_P9, cap=yy + 3, couleur="c-blanc"))
    y2 = HAUT_CONTENU + 8 + 3 * 58
    o.append(filet(TX, y2 - 20, TW, "r-sombre"))
    # Trois lignes POSEES, pas un renvoi automatique : une ligne de renvoi ne
    # peut pas recevoir la compensation de son propre premier glyphe.
    o.append(lignes("corps-s", ["Association loi 1901, créée en 2026.",
                                "Siège social : 23 Chemin des Alizés,",
                                "La Montagne, 97417 Saint-Denis."],
                    left=TX, cap=y2 + 6, pas=25, couleur="c-blanc", largeur=TW))

    Y_CONV = y2 + 86
    o.append(txt("etiquette-s", "UNE CONVENTION SIMPLE", left=TX, cap=Y_CONV,
                 couleur="c-orange"))
    o.append(lignes("petit", ["Supports, durée et livrables définis.",
                              "Visuels validés avant diffusion.",
                              "Droits des photos adaptés à leur usage."],
                    left=TX, cap=Y_CONV + 26, pas=22, couleur="c-blanc", largeur=TW))

    # 96 px et non 76 : l'URL de la fiche FFBB demande 45 modules, et a 76 px
    # un module ne mesurait que 0,30 mm a l'impression A4 — sous le seuil de
    # scan. A 96 px il en fait 0,40.
    QT = QR_P10
    QX9, QY9 = G.W - G.MARGE - QT, BAS_CONTENU - QT
    o.append(pave(QX9, QY9, QT, QT, "var(--blanc)"))
    o.append(qr("qr-ffbb.svg", QX9 + 6, QY9 + 6, QT - 12))

    o.append(pied("09", sombre=True, mention=(
        "Le club ne publie pas de SIRET et ne délivre aucun avis fiscal : le traitement du "
        "versement se décide avec votre conseil comptable. La couverture média dépend des "
        "rédactions et ne fait pas partie des contreparties.")))
    return page("f-nuit", "".join(o))


# ===========================================================================
# 10 - L'APPEL A L'ACTION
# ===========================================================================
def p10():
    o = []
    o.append(image("mbc-logo.png", G.MARGE, 48, 78, 80, extra="object-fit:contain"))
    o.append(txt("fort-l", "MBC <span style=\"color:var(--orange)\">&times;</span> OLA ENERGY",
                 left=G.MARGE + 100, cap=75, couleur="c-blanc", brut=True))

    o.append(titre("VINGT MINUTES,<br>UNE DÉCISION", cap=200, left=G.MARGE,
                   couleur="c-blanc", largeur=G.w(8), style="d1"))
    o.append(txt("lead", "Un vendredi soir au gymnase, à la table de marque. Entrée libre.",
                 left=G.MARGE, cap=444, couleur="c-glacier", largeur=G.w(8)))

    o.append(filet(G.MARGE, 492, G.w(7), "r-orange", 2))
    o.append(txt("fort-l", "contact@mbc974.com", left=G.MARGE, cap=524, couleur="c-blanc"))
    o.append(txt("fort-l", "0692 55 64 58", left=G.MARGE, cap=566, couleur="c-blanc"))
    o.append(txt("petit", "Téléphone et WhatsApp du club · réponse en général sous 48 h.",
                 left=G.MARGE, cap=596, couleur="c-glacier", largeur=G.w(7)))

    # L'argument de cloture, et il est verifiable : aucun des six partenaires
    # affiches sur mbc974.com n'est du secteur de l'energie.
    QX = G.x(9)
    o.append(filet(QX, 172, G.w(4), "r-roi"))
    o.append(titre("LA PLACE DU SECTEUR<br>ÉNERGIE EST ENCORE LIBRE", cap=200,
                   left=QX, couleur="c-blanc", largeur=G.w(4), style="etiquette"))
    o.append(txt("petit", "Aucun des six partenaires déjà affichés sur mbc974.com "
                 "n’en est.", left=QX, cap=258, couleur="c-glacier", largeur=G.w(4)))

    # Deux QR de MEME taille, empiles, chacun avec son intitule a DROITE : meme
    # gabarit que les trois preuves de la page 2. D'origine le seul intitule de
    # la page etait centre sous son QR, a 13,7 pt hors de son axe, quand tout le
    # reste de la page etait ferre a gauche.
    QT = 96
    for i, (q, lab, sub) in enumerate([
            ("qr-whatsapp.svg", "WHATSAPP DU CLUB", "Message d’accueil pré-rempli."),
            ("qr-sponsor.svg", "LA GRILLE EN LIGNE", "À comparer avec ce dossier.")]):
        yy = 348 + i * 132
        o.append(filet(QX, yy - 26, G.w(4), "r-roi"))
        o.append(pave(QX, yy, QT, QT, "var(--blanc)"))
        o.append(qr(q, QX + 7, yy + 7, QT - 14))
        o.append(txt("etiquette-s", lab, left=QX + QT + 22, cap=yy + 14, couleur="c-blanc"))
        o.append(txt("petit", sub, left=QX + QT + 22, cap=yy + 42, couleur="c-glacier",
                     largeur=G.w(4) - QT - 22))

    o.append(filet(G.MARGE, Y_FILET, G.CONTENU, "r-roi"))
    o.append(txt("pied", "MBC × OLA ENERGY  ·  SAISON 2026/2027", left=G.MARGE,
                 cap=CAP_PIED, couleur="c-glacier"))
    o.append(txt("etiquette-s", "La Montagne en lèr !", right=G.MARGE, cap=CAP_PIED - 2,
                 couleur="c-orange", align="right"))
    return page("f-roi", "".join(o))


# ===========================================================================
def construire(variante_couv="a"):
    pages = [p1(variante_couv), p2(), p3(), p4(), p5(), p6(), p7(), p8(), p9(), p10()]
    return ("<!DOCTYPE html>\n<html lang=\"fr\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<title>MBC × OLA Energy — Proposition de partenariat 2026/2027</title>\n"
            "<style>\n" + css.feuille() + "\n</style>\n</head>\n<body>\n"
            + "\n".join(pages) + "\n</body>\n</html>\n")


if __name__ == "__main__":
    var = sys.argv[1] if len(sys.argv) > 1 else "a"
    out = "dossier.html" if var == "a" else "dossier-%s.html" % var
    html = construire(var)
    open(out, "w", encoding="utf-8").write(html)
    print("%s : %d Ko, %d pages" % (out, len(html) // 1024, html.count("<section")))
