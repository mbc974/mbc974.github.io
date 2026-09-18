# -*- coding: utf-8 -*-
"""Le dossier partenaire GENERIQUE du MBC (10 pages, 16:9).

Meme grille, memes polices, memes garde-fous que le dossier OLA — voir
LISEZMOI.md. Ce qui change, c'est le destinataire : ici le dossier s'adresse a
tout partenaire possible, du commercant du quartier au groupe regional, et il
reprend la grille publique de quatre formules du site.

Les maquettes du dossier OLA portent la marque OLA a chaque plan : la page qui
faisait voir la visibilite est remplacee par deux pages plus utiles a tous —
le maillot (et la place qui reste dans le dos) et les six supports.
"""
import sys
import typo
import grille as G
import css
import contenu_general as C
import bloc
from bloc import (txt, lignes, filet, filet_v, pave, image, qr, pied,
                  surtitre, titre, cap_apres_titre, Y_FILET, CAP_PIED)

# Ce dossier ne s'adresse a personne en particulier : la signature du pied ne
# nomme donc que le club.
bloc.SIGNATURE = "MBC LA MONTAGNE BASKET CLUB  ·  SAISON 2026/2027"
SIGNATURE = bloc.SIGNATURE

CAP_SURTITRE = 56
CAP_TITRE = 96
HAUT_CONTENU = 232
BAS_CONTENU = 588
BANDE = BAS_CONTENU - HAUT_CONTENU

EURO = '<span style="font-size:1.127em;margin-left:.10em">&euro;</span>'

# Les decrochages interieurs assumes, exportes pour le garde-fou.
QR_P2 = 100
QR_P10 = 96
GOUT_CHIFFRE = 146
RETRAIT_CARTE = 20          # cartes de 3 colonnes : retrait plus serre
PASTILLE = "POPULAIRE"


def decrochages():
    return [
        G.MARGE + 100,
        G.x(7) + GOUT_CHIFFRE,
        G.x(7) + QR_P2 + 24,
        G.x(9) + QR_P10 + 22,
        G.x(8) + 176,
        G.x(1) + 62, G.x(5) + 62, G.x(9) + 62,          # supports, page 6
        G.x(7) + 120,                                   # chiffres, page 4
        G.x(1) + RETRAIT_CARTE, G.x(4) + RETRAIT_CARTE,
        G.x(7) + RETRAIT_CARTE, G.x(10) + RETRAIT_CARTE,
        G.x(4) + G.w(3) - RETRAIT_CARTE
        - (round(G.largeur_texte("surtitre", PASTILLE)) + 24) + 12,
    ]


def page(classe, corps):
    return '<section class="p %s">%s</section>' % (classe, corps)


def entete(sur, tit, sous=None, sombre=False, left=G.MARGE, largeur=None,
           couleur_sur=None, lignes_titre=1):
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
def p1():
    o = []
    o.append(image("couverture.jpg", 0, 0, G.W, G.H, pos="46% 52%",
                   alt="L'ecole de basket du MBC en regroupement au gymnase de La Montagne."))
    o.append(pave(0, 0, G.W, G.H, "none", extra=(
        "background:linear-gradient(104deg,"
        "rgba(13,21,38,.95) 0%,rgba(13,21,38,.90) 30%,"
        "rgba(13,21,38,.60) 54%,rgba(13,21,38,.20) 76%,rgba(13,21,38,.08) 100%)")))
    o.append(pave(0, G.H - 320, G.W, 320, "none", extra=(
        "background:linear-gradient(0deg,rgba(13,21,38,.90) 0%,rgba(13,21,38,0) 100%)")))

    o.append(image("mbc-logo.png", G.MARGE, 48, 78, 80, extra="object-fit:contain"))
    o.append(txt("fort-l", "LA MONTAGNE BASKET CLUB", left=G.MARGE + 100, cap=75,
                 couleur="c-blanc"))

    pas = G.STYLES["d1"][1] * G.STYLES["d1"][2]
    o.append(titre("DEVENEZ<br>PARTENAIRE", cap=396 - pas, left=G.MARGE,
                   couleur="c-blanc", largeur=880, style="d1"))
    o.append(txt("lead", "Ensemble, faisons grandir le basket à La Montagne.",
                 left=G.MARGE, cap=544, couleur="c-glacier", largeur=680))

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
    IM_H = round(IM_W * 712 / 1265)
    o.append(txt("etiquette", "mbc974.com · 27 pages publiées", left=IM_X,
                 cap=HAUT_CONTENU, couleur="c-encre"))
    o.append(pave(IM_X, HAUT_CONTENU + 30, IM_W, IM_H, "var(--papier-2)"))
    o.append(image("site.jpg", IM_X, HAUT_CONTENU + 30, IM_W, IM_H, pos="50% 0%",
                   alt="La page d'accueil de mbc974.com."))

    CX, CW, QT = G.x(7), G.w(6), QR_P2
    PREUVES = [
        ("qr-reportage.svg", "RÉUNION LA 1ÈRE",
         "Sujet &laquo;&nbsp;Grand Sport&nbsp;&raquo; du 13/09/2026,<br>3 min 14 sur le club."),
        ("qr-instagram.svg", "@MBC974.RE",
         "Facebook, Instagram et TikTok,<br>liés depuis les 27 pages du site."),
        ("qr-ffbb.svg", "FICHE FFBB PUBLIQUE",
         "Affiliation REU0974104,<br>vérifiable chez la fédération."),
    ]
    for i, (q, lab, sub) in enumerate(PREUVES):
        yy = HAUT_CONTENU + i * 124
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
# 3 - LES CHIFFRES
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

    LX = G.x(7)
    for i, (val, lib, _s) in enumerate(C.CHIFFRES[1:]):
        yy = HAUT_CONTENU + 16 + i * 66
        o.append(filet(LX, yy - 20, G.w(6), "r-roi"))
        o.append(txt("stat-m", val, left=LX, cap=yy, couleur="c-orange"))
        o.append(txt("corps-s", lib, left=LX + GOUT_CHIFFRE, cap=yy + 11,
                     couleur="c-blanc", largeur=G.w(6) - GOUT_CHIFFRE))
    o.append(filet(LX, HAUT_CONTENU + 16 + 5 * 66 - 20, G.w(6), "r-roi"))

    o.append(pied("03", sombre=True, mention=(
        "Effectifs communiqués par le club au 18/09/2026, adhésions et préinscriptions "
        "confondues : ce ne sont pas des licences FFBB qualifiées. Score du 11/09/2026 "
        "communiqué par le club, le relevé de la Ligue n’est pas encore publié.")))
    return page("f-roi", "".join(o))


# ===========================================================================
# 4 - LE MAILLOT, ET LA PLACE QUI RESTE
# ===========================================================================
def p4():
    o = [entete("LE MAILLOT 2026/2027", "IL RESTE DE LA PLACE DANS LE DOS",
                "Le devant porte déjà trois marques. Le dos, lui, n’en porte aucune.")]

    # Deux photos de MEME gabarit, cote a cote : la preuve se lit sans legende.
    # Hauteur 320 px et non toute la bande, pour que les legendes tiennent
    # AU-DESSUS de la zone de la mention.
    PH_H = 320
    PH = [("maillot-dos.jpg", 1, "52% 30%", "Le dos : aucun partenaire.",
           "Le dos du maillot domicile du MBC : nom du club, numero et devise, "
           "aucun logo de partenaire."),
          ("maillot-face.jpg", 4, "52% 18%", "La face : trois marques.",
           "La face du maillot : logo du club, Oxysom et Les Agitateurs du Midi.")]
    for src, col, pos, leg, alt in PH:
        PX, PW = G.x(col), G.w(3)
        o.append(pave(PX, HAUT_CONTENU, PW, PH_H, "var(--papier-2)"))
        o.append(image(src, PX, HAUT_CONTENU, PW, PH_H, pos=pos, alt=alt))
        o.append(txt("petit", leg, left=PX, cap=HAUT_CONTENU + PH_H + 22,
                     couleur="c-douce", largeur=PW))

    # Ce que cette place represente, en chiffres verifiables.
    TX, TW = G.x(7), G.w(6)
    ITEMS = [("10", "joueurs seniors, maillot domicile et extérieur"),
             ("9", "réceptions au gymnase en phase 1, entrée libre"),
             ("30", "dates au calendrier, jusqu’au 23 avril 2027")]
    for i, (n, t) in enumerate(ITEMS):
        yy = HAUT_CONTENU + 10 + i * 78
        o.append(filet(TX, yy - 22, TW, "r-clair"))
        o.append(txt("stat-m", n, left=TX, cap=yy, couleur="c-roi"))
        o.append(txt("corps-s", t, left=TX + 120, cap=yy + 4, couleur="c-encre",
                     largeur=TW - 120))
    o.append(filet(TX, HAUT_CONTENU + 10 + 3 * 78 - 22, TW, "r-clair"))
    o.append(txt("fort", "Le floquage du dos entre dans la formule All-Star.",
                 left=TX, cap=HAUT_CONTENU + 10 + 3 * 78 + 4, couleur="c-encre",
                 largeur=TW))
    o.append(txt("petit", "Une seule marque y sera floquée : la place est unique.",
                 left=TX, cap=HAUT_CONTENU + 10 + 3 * 78 + 36, couleur="c-douce",
                 largeur=TW))

    o.append(pied("04", sombre=False, mention=(
        "* Le floquage d’un maillot se décide avec le club et son équipementier, et "
        "reste soumis aux règles de la compétition. Un emplacement de la face est déjà "
        "occupé par InPlay, équipementier du club. Photographies du 18 septembre 2026.")))
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

    o.append(filet(TX, Y_FILET, TW, "r-sombre"))
    o.append(txt("mention", "Deux équipements municipaux que le club fait vivre. "
                 "Ansanm nou lé pli for.", left=TX, bottom=G.H - Y_FILET + 14,
                 largeur=TW, couleur="c-glacier"))
    o.append(txt("pied", SIGNATURE, left=TX,
                 cap=CAP_PIED, couleur="c-glacier"))
    o.append(txt("pagenum", "05", right=G.MARGE, cap=CAP_PIED, couleur="c-glacier",
                 align="right"))
    return page("f-nuit", "".join(o))


# ===========================================================================
# 6 - LES SIX SUPPORTS + L'AUDIENCE MESUREE
# ===========================================================================
def p6():
    o = [entete("OÙ VOTRE MARQUE APPARAÎT", "SIX SUPPORTS, UNE SAISON",
                "Le club produit et publie lui-même. Vous héritez de la chaîne.",
                sombre=True)]

    # Six supports en deux rangees de trois.
    for i, (nom, det) in enumerate(C.SUPPORTS):
        col = 1 + (i % 3) * 4
        rang = i // 3
        CX, CW = G.x(col), G.w(4)
        yy = HAUT_CONTENU + 10 + rang * 112
        o.append(filet(CX, yy - 24, CW, "r-sombre"))
        o.append(txt("stat-m", "0%d" % (i + 1), left=CX, cap=yy,
                     extra="color:rgba(191,210,228,.28)"))
        o.append(txt("etiquette-s", nom, left=CX + 62, cap=yy + 2, couleur="c-orange"))
        o.append(txt("petit", det, left=CX + 62, cap=yy + 28, couleur="c-glacier",
                     largeur=CW - 62))

    # L'audience, telle que le club la publie : des apparitions, pas des personnes.
    Y_AUD = HAUT_CONTENU + 10 + 2 * 112 + 14
    o.append(filet(G.x(1), Y_AUD - 26, G.CONTENU, "r-sombre"))
    o.append(txt("surtitre", "L’AUDIENCE, TELLE QU’ELLE EST", left=G.x(1),
                 cap=Y_AUD, couleur="c-blanc"))
    # Le libelle est EMPILE sous le chiffre : une gouttiere de largeur fixe
    # laissait un trou apres un chiffre d'un seul caractere (« 5 », « 4 »),
    # et ces trois chiffres sont chacun dans leur colonne — rien a aligner
    # horizontalement entre eux.
    for i, (val, lib) in enumerate(C.AUDIENCE):
        CX = G.x(1 + i * 4)
        o.append(txt("stat-m", val, left=CX, cap=Y_AUD + 30, couleur="c-orange"))
        o.append(txt("petit", lib, left=CX, cap=Y_AUD + 84, couleur="c-glacier",
                     largeur=G.w(4)))

    o.append(pied("06", sombre=True, mention=(
        "Source : Google Search Console, relevé fin août 2026 sur les trois derniers mois "
        "glissants. Ce sont des APPARITIONS du site dans les résultats, pas un nombre de "
        "personnes. * Maillots et bâche sous réserve d’autorisation.")))
    return page("f-nuit", "".join(o))


# ===========================================================================
# 7 - COMMENT ON DEVIENT PARTENAIRE
# ===========================================================================
def p7():
    o = [entete("EN TROIS ÉTAPES", "COMMENT ON DEVIENT PARTENAIRE",
                "Soutien financier, matériel ou en services : on s’adapte à vos moyens.")]

    Y_NUM = HAUT_CONTENU + 48
    Y_FIL = Y_NUM + 112
    Y_LAB = Y_FIL + 28
    Y_LIS = Y_LAB + 44
    for i, (num, lab, items) in enumerate(C.ETAPES):
        CX, CW = G.x(1 + i * 4), G.w(4)
        o.append(txt("num", num, left=CX, cap=Y_NUM, couleur="c-roi"))
        o.append(filet(CX, Y_FIL, CW, "r-clair"))
        o.append(txt("etiquette", lab, left=CX, cap=Y_LAB, couleur="c-encre"))
        o.append(lignes("corps-s", items, left=CX, cap=Y_LIS, pas=32,
                        couleur="c-douce", largeur=CW))
        if i < 2:
            haut, bas = Y_NUM - 16, Y_LIS + 2 * 32 + 22
            o.append(filet_v(CX + CW + G.GOUT / 2 - 0.5, haut, bas - haut, "r-clair"))

    o.append(pied("07", sombre=False, mention=(
        "Aucun engagement avant accord écrit. Le club répond en général sous 48 h. "
        "Selon la nature du soutien et votre situation, une contribution peut relever du "
        "mécénat : rapprochez-vous de votre conseil comptable pour les conditions "
        "applicables.")))
    return page("f-papier", "".join(o))


# ===========================================================================
# 8 - LES QUATRE FORMULES
# ===========================================================================
def p8():
    o = [entete("LA GRILLE PUBLIQUE DU CLUB", "QUATRE FORMULES, DÈS 200 €",
                "Chaque formule inclut la précédente. Toutes sont adaptables.")]

    PAD = RETRAIT_CARTE
    D_NOM = PAD
    D_TEMPO = D_NOM + 24
    D_PRIX = D_TEMPO + 54
    D_FIL = D_PRIX + 62
    D_LIS = D_FIL + 22
    PAS_LIS = 25
    NB = max(len(f["lignes"]) for f in C.FORMULES)
    bas = D_LIS + (NB - 1) * PAS_LIS + typo.metrics("barlow")["cap"] * G.STYLES["petit"][1]
    CARD_H = round(bas + PAD)
    CARD_Y = BAS_CONTENU - CARD_H

    for i, f in enumerate(C.FORMULES):
        CX, CW = G.x(1 + i * 3), G.w(3)
        pop = f["populaire"]
        o.append(pave(CX, CARD_Y, CW, CARD_H,
                      "var(--roi)" if pop else "var(--papier-2)"))
        ix, iw = CX + PAD, CW - 2 * PAD
        c_nom = "c-blanc" if pop else "c-roi"
        c_txt = "c-blanc" if pop else "c-encre"
        c_dim = "c-glacier" if pop else "c-douce"
        if pop:
            P_INT = 12
            larg = round(G.largeur_texte("surtitre", PASTILLE)) + 2 * P_INT
            px = CX + CW - PAD - larg
            o.append(pave(px, CARD_Y + D_NOM - 7, larg, 27, "var(--orange)"))
            o.append(txt("surtitre", PASTILLE, left=px + P_INT, cap=CARD_Y + D_NOM,
                         couleur="c-blanc"))
        o.append(txt("etiquette-s", f["nom"], left=ix, cap=CARD_Y + D_NOM, couleur=c_nom))
        o.append(txt("petit", f["tempo"], left=ix, cap=CARD_Y + D_TEMPO, couleur=c_dim,
                     largeur=iw))
        # Le « + » du Hall of Fame : retrait CSS et non espace fine, l'espace
        # fine insecable U+2009 manquant au sous-ensemble Barlow du site.
        prix = f["prix"] + EURO + (
            '<span style="font-size:.62em;margin-left:.16em">'
            + f["suffixe"] + '</span>' if f.get("suffixe") else "")
        o.append(txt("prix-s", prix, left=ix, cap=CARD_Y + D_PRIX, couleur=c_txt,
                     brut=True))
        o.append(filet(ix, CARD_Y + D_FIL, iw, "r-roi" if pop else "r-clair"))
        o.append(lignes("petit", f["lignes"], left=ix, cap=CARD_Y + D_LIS,
                        pas=PAS_LIS, couleur=c_txt, largeur=iw))

    o.append(pied("08", sombre=False, mention=(
        "Grille publique sur mbc974.com/sponsor-club-basket-reunion/, reprise ici au centime. "
        "Fidélité : −10 % sur deux saisons, −20 % et mention "
        "« Partenaire fidèle » sur trois. * Bâche au gymnase et floquage maillot "
        "sous réserve d’autorisation. Une formule sur mesure est possible, y compris en "
        "soutien matériel ou en services.")))
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
        o.append(txt("stat-s", v, left=TX + 176, cap=yy + 3, couleur="c-blanc"))
    y2 = HAUT_CONTENU + 8 + 3 * 58
    o.append(filet(TX, y2 - 20, TW, "r-sombre"))
    o.append(lignes("corps-s", ["Association loi 1901, créée en 2026.",
                                "Siège social : 23 Chemin des Alizés,",
                                "La Montagne, 97417 Saint-Denis."],
                    left=TX, cap=y2 + 6, pas=25, couleur="c-blanc", largeur=TW))

    Y_CONV = y2 + 86
    o.append(txt("etiquette-s", "UNE CONVENTION SIMPLE", left=TX, cap=Y_CONV,
                 couleur="c-orange"))
    o.append(lignes("petit", ["Supports, durée et livrables définis.",
                              "Visuels validés avant diffusion.",
                              "Bilan des retombées mesurées."],
                    left=TX, cap=Y_CONV + 26, pas=22, couleur="c-blanc", largeur=TW))

    QT = 96
    QX, QY = G.W - G.MARGE - QT, BAS_CONTENU - QT
    o.append(pave(QX, QY, QT, QT, "var(--blanc)"))
    o.append(qr("qr-ffbb.svg", QX + 6, QY + 6, QT - 12))

    o.append(pied("09", sombre=True, mention=(
        "Le club ne publie pas de SIRET et ne délivre aucun avis fiscal : le traitement du "
        "versement se décide avec votre conseil comptable. La couverture média dépend des "
        "rédactions et ne fait pas partie des contreparties.")))
    return page("f-nuit", "".join(o))


# ===========================================================================
# 10 - PARLONS-EN
# ===========================================================================
def p10():
    o = []
    o.append(image("mbc-logo.png", G.MARGE, 48, 78, 80, extra="object-fit:contain"))
    o.append(txt("fort-l", "LA MONTAGNE BASKET CLUB", left=G.MARGE + 100, cap=75,
                 couleur="c-blanc"))

    o.append(titre("PARLONS-EN,<br>SANS ENGAGEMENT", cap=200, left=G.MARGE,
                   couleur="c-blanc", largeur=G.w(8), style="d1"))
    o.append(txt("lead", "Un vendredi soir au gymnase, à la table de marque. Entrée libre.",
                 left=G.MARGE, cap=444, couleur="c-glacier", largeur=G.w(8)))

    o.append(filet(G.MARGE, 492, G.w(7), "r-orange", 2))
    o.append(txt("fort-l", "contact@mbc974.com", left=G.MARGE, cap=524, couleur="c-blanc"))
    o.append(txt("fort-l", "0692 55 64 58", left=G.MARGE, cap=566, couleur="c-blanc"))
    o.append(txt("petit", "Téléphone et WhatsApp du club · réponse en général sous 48 h.",
                 left=G.MARGE, cap=596, couleur="c-glacier", largeur=G.w(7)))

    QX = G.x(9)
    o.append(filet(QX, 172, G.w(4), "r-roi"))
    o.append(titre("TROIS FORMES DE SOUTIEN", cap=200, left=QX, couleur="c-blanc",
                   largeur=G.w(4), style="etiquette"))
    o.append(txt("petit", "Financier, matériel ou en services. Une formule de la grille, "
                 "ou sur mesure.", left=QX, cap=232, couleur="c-glacier",
                 largeur=G.w(4)))

    QT = QR_P10
    for i, (q, lab, sub) in enumerate([
            ("qr-whatsapp.svg", "WHATSAPP DU CLUB", "Message d’accueil pré-rempli."),
            ("qr-partenaires.svg", "LA PAGE PARTENAIRES", "La grille, en ligne.")]):
        yy = 348 + i * 132
        o.append(filet(QX, yy - 26, G.w(4), "r-roi"))
        o.append(pave(QX, yy, QT, QT, "var(--blanc)"))
        o.append(qr(q, QX + 7, yy + 7, QT - 14))
        o.append(txt("etiquette-s", lab, left=QX + QT + 22, cap=yy + 14, couleur="c-blanc"))
        o.append(txt("petit", sub, left=QX + QT + 22, cap=yy + 42, couleur="c-glacier",
                     largeur=G.w(4) - QT - 22))

    o.append(filet(G.MARGE, Y_FILET, G.CONTENU, "r-roi"))
    o.append(txt("pied", SIGNATURE, left=G.MARGE, cap=CAP_PIED,
                 couleur="c-glacier"))
    o.append(txt("etiquette-s", "La Montagne en lèr !", right=G.MARGE, cap=CAP_PIED - 2,
                 couleur="c-orange", align="right"))
    return page("f-roi", "".join(o))


# ===========================================================================
def construire():
    pages = [p1(), p2(), p3(), p4(), p5(), p6(), p7(), p8(), p9(), p10()]
    return ("<!DOCTYPE html>\n<html lang=\"fr\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<title>MBC La Montagne Basket Club — Dossier partenaire 2026/2027</title>\n"
            "<style>\n" + css.feuille() + "\n</style>\n</head>\n<body>\n"
            + "\n".join(pages) + "\n</body>\n</html>\n")


if __name__ == "__main__":
    html = construire()
    open("dossier-general.html", "w", encoding="utf-8").write(html)
    print("dossier-general.html : %d Ko, %d pages"
          % (len(html) // 1024, html.count("<section")))
