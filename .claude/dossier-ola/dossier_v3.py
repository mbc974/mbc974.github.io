# -*- coding: utf-8 -*-
"""Le dossier partenaire V3 du MBC — 8 pages, 16:9, orientation COMMERCIALE.

Meme grille, memes polices, memes garde-fous que les deux dossiers precedents
(voir LISEZMOI.md). Ce qui change, c'est l'ORDRE DES QUESTIONS. Le v2 repondait
a « qui sommes-nous » ; la V3 repond, dans cet ordre, aux cinq questions qu'un
dirigeant se pose vraiment :

    p2  combien pesez-vous ?          -> LE MBC EN 30 SECONDES
    p3  pourquoi vous croire ?        -> DES PREUVES, PAS DES PROMESSES
    p4  qui vais-je toucher ?         -> QUI VOTRE MARQUE VA TOUCHER   (NEUVE)
    p5  a quoi sert mon argent ?      -> CE QUE VOTRE SOUTIEN PERMET   (NEUVE)
    p6  qu'est-ce que je recois ?     -> VOTRE MARQUE, AVEC LE MBC
    p7  combien ca coute ?            -> QUATRE FORMULES, DES 200 EUR
    p8  comment on commence ?         -> FAISONS EQUIPE

Deux pages du v2 disparaissent en tant que telles, sans rien perdre :
  - « Comment on devient partenaire » (p7) : trois etapes qui tenaient une page
    entiere et que la page de cloture repetait deja. Elles sont desormais une
    colonne de la page 8.
  - « Un club declare » (p9) : la page administrative. Un service achats a
    besoin du RNA et du SIREN, pas d'une page pour eux. Ils tiennent dans un
    encart de la page 8.

Et deux pages du v2 fusionnent : « Il reste de la place dans le dos » (p4) et
« Six supports » (p6) formaient deux fois la meme promesse. La page 6 porte
maintenant les supports A GAUCHE et l'emplacement rare A DROITE, avec la photo.

Le squelette reste identique au pixel sur les SIX pages de contenu (2 a 7).
"""
import sys
import typo
import grille as G
import css
import contenu_v3 as C
import bloc
from bloc import (txt, lignes, filet, filet_v, pave, image, qr, pied,
                  surtitre, titre, cap_apres_titre, Y_FILET, CAP_PIED)

bloc.SIGNATURE = "MBC LA MONTAGNE BASKET CLUB  ·  SAISON 2026/2027"
SIGNATURE = bloc.SIGNATURE

# Espace insecable avant ; : ! ? et dans les guillemets. Sans elle, la mention
# de la page 8 renvoyait son point-virgule en debut de ligne suivante.
bloc.TYPO_FR = True

CAP_SURTITRE = 56
CAP_TITRE = 96
HAUT_CONTENU = 232
BAS_CONTENU = 588
BANDE = BAS_CONTENU - HAUT_CONTENU          # 356 px, sur chaque page

# Le « € » d'Anton culmine a 0,7695 em quand un chiffre culmine a 0,8672 em :
# 0,8672/0,7695 = 1,127 le remet exactement a la hauteur des chiffres.
EURO = '<span style="font-size:1.127em;margin-left:.10em">&euro;</span>'

# --- Les decrochages interieurs assumes, exportes pour le garde-fou --------
GOUT_P2 = 150            # libelle a cote du chiffre, page 2
QR_P3 = 88               # cote des plaques de QR, page 3
QR_P8 = 96
RETRAIT_CARTE = 20       # cartes de 3 colonnes, page 7
RETRAIT_PANNEAU = 20     # encart du maillot, page 6
GOUT_P5 = 56             # libelle a cote du numero de famille, page 5
GOUT_P8 = 52             # libelle a cote du numero d'etape, page 8
GOUT_ENG = 172           # description a cote de son intitule, engagements
PASTILLE = "POPULAIRE"


# --- Les liens du PDF ------------------------------------------------------
# Le dossier est lu a l'ecran autant qu'imprime. Chrome headless emet une
# annotation de lien par <a href> : on rend donc cliquable le texte DEJA
# ecrit — une adresse, un intitule de preuve — au lieu d'ajouter des
# « cliquez ici ». Les QR, eux, restent pour le papier, et leur plaque recoit
# en plus une zone cliquable transparente.
def lien(cle, contenu):
    """Enveloppe un contenu deja HTML dans un lien vers C.LIENS[cle]."""
    return '<a href="%s">%s</a>' % (C.LIENS[cle], contenu)


def zone(cle, left, top, largeur, hauteur):
    """Zone cliquable transparente, posee sur une plaque de QR."""
    return ('<a class="zn" href="%s" style="left:%.2fpx;top:%.2fpx;'
            'width:%.2fpx;height:%.2fpx"></a>'
            % (C.LIENS[cle], left, top, largeur, hauteur))


# Les URL citees dans les mentions, rendues cliquables sans changer un mot du
# texte imprime : le lecteur voit « mbc974.com/creneaux/ », il peut cliquer.
_URL_VISIBLE = dict(creneaux=("creneaux", "mbc974.com/creneaux/"),
                    soutenir=("soutenir", "mbc974.com/soutenir-le-club/"),
                    sponsor=("partenaires", "mbc974.com/sponsor-club-basket-reunion/"))


def mention(modele):
    """Remplace les {creneaux} / {soutenir} / {sponsor} d'une mention par des
    liens. Le resultat part en HTML brut : on verifie donc qu'il n'y a rien a
    echapper, sinon un « & » du texte casserait silencieusement la page."""
    for ch in "<>&":
        assert ch not in modele, "caractere a echapper dans une mention : " + ch
    return modele.format(**{k: lien(c, t) for k, (c, t) in _URL_VISIBLE.items()})


def decrochages():
    """Les x, en px, ou du texte commence legitimement hors colonne."""
    return [
        G.MARGE + 100,                                   # nom a cote du logo
        G.x(7) + GOUT_P2,                                # chiffres, page 2
        G.x(1) + GOUT_P2,                                # chiffres, page 2
        G.x(1) + 336,                                    # etiquette TV, page 3
        G.x(9) + QR_P3 + 20,                             # preuves, page 3
        G.x(1) + GOUT_P5, G.x(4) + GOUT_P5,              # familles, page 5
        G.x(7) + GOUT_P5, G.x(10) + GOUT_P5,
        G.x(8) + RETRAIT_PANNEAU,                        # encart maillot, page 6
        G.x(1) + RETRAIT_CARTE, G.x(4) + RETRAIT_CARTE,  # cartes, page 7
        G.x(7) + RETRAIT_CARTE, G.x(10) + RETRAIT_CARTE,
        G.x(4) + G.w(3) - RETRAIT_CARTE
        - (round(G.largeur_texte("surtitre", PASTILLE)) + 24) + 12,
        G.x(6) + GOUT_P8,                                # etapes, page 8
        G.x(6) + QR_P8 + 20, G.x(9) + QR_P8 + 20,        # QR, page 8
        G.x(6) + GOUT_ENG,                               # engagements, page 8
    ]


# --- Un garde-fou local : aucune ligne ne doit passer a la ligne toute seule
_TROP_LARGE = []


def tient(style, texte, largeur, ou=""):
    """Prévient si une ligne censee tenir sur UNE ligne va se replier.

    Une ligne qui se replie decale tout ce qui la suit — or ici rien ne suit :
    chaque ligne a sa position absolue. Le repli passe donc INAPERCU dans le
    code et se voit seulement a l'oeil, sur le PDF. On le mesure.
    """
    w = G.largeur_texte(style, texte)
    if w > largeur:
        _TROP_LARGE.append((ou, style, round(w), largeur, texte[:46]))
    return texte


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
        # Un sous-titre qui se replie descend sa seconde ligne a 221 px, la ou
        # les cartes de la page 7 commencent a 226 — et comme elles sont
        # peintes APRES, elles la recouvrent : l'information disparait sans
        # que rien ne deborde ni ne chevauche visiblement. C'est arrive a
        # « ... y compris en materiel ou en services », dont la fin etait
        # cachee derriere la carte ROOKIE. On mesure donc chaque chapo.
        tient("lead", sous, largeur or G.CONTENU, "chapo de page")
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
    o.append(titre(C.P1_TITRE, cap=396 - pas, left=G.MARGE,
                   couleur="c-blanc", largeur=880, style="d1"))
    o.append(txt("lead", C.P1_LEAD, left=G.MARGE, cap=544, couleur="c-glacier",
                 largeur=720))

    o.append(filet(G.MARGE, 600, 320, "r-orange", 2))
    o.append(txt("pied", C.P1_PIED, left=G.MARGE, cap=632, couleur="c-glacier"))
    o.append(txt("pied", lien("site", "mbc974.com"), right=G.MARGE, cap=632,
                 couleur="c-glacier", align="right", brut=True))
    return page("f-nuit", "".join(o))


# ===========================================================================
# 2 - LE MBC EN 30 SECONDES
# ===========================================================================
def p2():
    o = [entete(C.P2_SUR, C.P2_TITRE, C.P2_LEAD, sombre=True,
                couleur_sur="c-blanc")]

    # Le chiffre phare occupe cinq colonnes : c'est le seul de la page qui a le
    # droit d'etre enorme, sinon aucun ne l'est. Sous lui, le premier match —
    # un chiffre du club, pas une preuve a scanner : sa place est ici.
    HX = G.x(1)
    sur, val, lib, src = C.P2_PHARE
    o.append(txt("surtitre", sur, left=HX, cap=256, couleur="c-orange"))
    o.append(txt("stat-xl", val, left=HX, cap=296, couleur="c-blanc"))
    o.append(filet(HX, 440, G.w(4), "r-roi", 2))
    o.append(txt("fort", lib, left=HX, cap=468, couleur="c-blanc", largeur=G.w(5)))
    o.append(txt("petit", src, left=HX, cap=498, couleur="c-glacier", largeur=G.w(5)))
    o.append(filet(HX, 528, G.w(5), "r-roi"))
    mv, ml = C.P2_MATCH
    o.append(txt("stat-m", mv, left=HX, cap=544, couleur="c-orange"))
    o.append(txt("petit", tient("petit", ml, G.w(5) - GOUT_P2, "p2 match"),
                 left=HX + GOUT_P2, cap=556, couleur="c-blanc",
                 largeur=G.w(5) - GOUT_P2))

    # Les six autres, en deux colonnes de trois. Le libelle est POSE SOUS le
    # chiffre : a 46 px, un libelle a cote tiendrait sur deux lignes dans une
    # colonne de 270 px et mordrait la ligne suivante.
    for i, (val, lib, sous) in enumerate(C.P2_CHIFFRES):
        CX, CW = G.x(7 if i < 3 else 10), G.w(3)
        yy = HAUT_CONTENU + 10 + (i % 3) * 116
        o.append(filet(CX, yy - 22, CW, "r-roi"))
        o.append(txt("stat-m", val, left=CX, cap=yy, couleur="c-orange"))
        o.append(txt("fort", tient("fort", lib, CW, "p2 libelle"), left=CX,
                     cap=yy + 54, couleur="c-blanc", largeur=CW))
        o.append(txt("petit", tient("petit", sous, CW, "p2 sous"), left=CX,
                     cap=yy + 80, couleur="c-glacier", largeur=CW))
    for col in (7, 10):
        o.append(filet(G.x(col), HAUT_CONTENU + 10 + 3 * 116 - 22, G.w(3), "r-roi"))

    o.append(pied("02", sombre=True, mention=mention(C.P2_MENTION),
                  brut_mention=True))
    return page("f-roi", "".join(o))


# ===========================================================================
# 3 - DES PREUVES, PAS DES PROMESSES
# ===========================================================================
def p3():
    """V3.2 : la page passe a TROIS colonnes de quatre.

    Elle n'en portait que deux, et sa seule image etait le bandeau du
    reportage — un dos de tee-shirt en letterbox, la plus faible des preuves
    a l'oeil. La colonne de gauche accueille desormais la photo des elus sous
    le plateau : un ecran tricolore, des costumes, les joueurs du club. C'est
    l'ancrage local prouve en une image, la ou trois lignes n'y suffisaient
    pas. Le reportage garde son chiffre, sa phrase, sa photo et son QR : rien
    n'a ete retire, la page a ete redistribuee.
    """
    o = [entete(C.P3_SUR, C.P3_TITRE, C.P3_LEAD)]

    # --- Colonne A : la preuve d'ancrage, en photo -------------------------
    AX, AW = G.x(1), G.w(4)
    o.append(pave(AX, HAUT_CONTENU, AW, 310, "var(--papier-2)"))
    o.append(image("officiels-ville.jpg", AX, HAUT_CONTENU, AW, 310, pos="50% 44%",
                   alt="Elus de la Ville de Saint-Denis et joueurs du MBC reunis "
                       "sous le plateau sportif couvert, le jour de son inauguration."))
    o.append(txt("mention", C.P3_PHOTO_LEGENDE, left=AX, cap=558,
                 couleur="c-douce", largeur=AW))

    # --- Colonne B : le reportage ------------------------------------------
    BX, BW = G.x(5), G.w(4)
    o.append(txt("stat-l", tient("stat-l", C.P3_TV_CHIFFRE, BW, "p3 chiffre TV"),
                 left=BX, cap=HAUT_CONTENU, couleur="c-roi"))
    o.append(txt("etiquette-s", lien("reportage", tient("etiquette-s", C.P3_TV_ETIQ, BW, "p3 etiquette")),
                 left=BX, cap=316, couleur="c-encre", brut=True))
    o.append(txt("corps-s", C.P3_TV_TEXTE, left=BX, cap=344, couleur="c-encre",
                 largeur=BW))
    IM_H = 130
    o.append(pave(BX, 446, BW, IM_H, "var(--papier-2)"))
    o.append(image("reportage.jpg", BX, 446, BW, IM_H, pos="50% 40%",
                   alt="Le sujet de Reunion La 1ere consacre au MBC, septembre 2026."))
    o.append(zone("reportage", BX, 446, BW, IM_H))

    # --- Colonne C : les trois preuves a scanner ---------------------------
    # Les plaques font 88 px : en dessous, le plus dense des trois codes passe
    # sous 0,40 mm par module a l'impression A4 et cesse de se scanner.
    CX, CW, QT = G.x(9), G.w(4), QR_P3
    for i, (q, cle, lab, dessous) in enumerate(C.P3_PREUVES):
        yy = HAUT_CONTENU + i * 104
        if i:
            o.append(filet(CX, yy - 20, CW, "r-clair"))
        o.append(pave(CX, yy, QT, QT, "var(--blanc)"))
        o.append(qr(q, CX + 7, yy + 7, QT - 14))
        o.append(zone(cle, CX, yy, QT, QT))
        o.append(txt("etiquette-s", lien(cle, lab), left=CX + QT + 20, cap=yy + 14,
                     couleur="c-encre", brut=True))
        o.append(txt("petit", dessous, left=CX + QT + 20, cap=yy + 40,
                     couleur="c-douce", largeur=CW - QT - 20, brut=True))
    o.append(filet(CX, HAUT_CONTENU + 3 * 104 - 20, CW, "r-clair"))
    o.append(txt("etiquette-s", C.P3_DEJA[0], left=CX, cap=534, couleur="c-roi"))
    for l in C.P3_DEJA[1]:
        tient("mention", l, CW, "p3 partenaire")
    o.append(lignes("mention", C.P3_DEJA[1], left=CX, cap=556, pas=18,
                    couleur="c-douce", largeur=CW))

    o.append(pied("03", sombre=False, mention=mention(C.P3_MENTION),
                  brut_mention=True))
    return page("f-papier", "".join(o))


# ===========================================================================
# 4 - QUI VOTRE MARQUE VA TOUCHER
# ===========================================================================
def p4():
    """La page que le v2 n'avait pas : non pas OU le logo apparait, mais DEVANT
    QUI. La photo montre des enfants ET leurs parents dans le meme cadre — le
    v2 illustrait cette idee par un gymnase vide."""
    o = []
    o.append(image("communaute.jpg", 0, 0, G.W, G.H, pos="50% 50%",
                   alt="L'ecole de basket du MBC au plateau de Ruisseau Blanc, "
                       "enfants assis en cercle et parents autour du terrain."))
    # Deux voiles, un par bord : l'en-tete et les publics reposent chacun sur
    # une zone opaque, et le CENTRE de l'image — les enfants — reste intact.
    o.append(pave(0, 0, G.W, 330, "none", extra=(
        "background:linear-gradient(180deg,rgba(13,21,38,.96) 0%,"
        "rgba(13,21,38,.92) 40%,rgba(13,21,38,.55) 74%,rgba(13,21,38,0) 100%)")))
    o.append(pave(0, G.H - 390, G.W, 390, "none", extra=(
        "background:linear-gradient(0deg,rgba(13,21,38,.97) 0%,"
        "rgba(13,21,38,.95) 52%,rgba(13,21,38,.72) 76%,rgba(13,21,38,0) 100%)")))

    o.append(entete(C.P4_SUR, C.P4_TITRE, C.P4_LEAD, sombre=True))

    o.append(filet(G.x(1), 396, G.CONTENU, "r-sombre"))
    for i, (nom, det) in enumerate(C.P4_PUBLICS):
        CX, CW = G.x(1 + i * 3), G.w(3)
        o.append(txt("etiquette-s", nom, left=CX, cap=416, couleur="c-orange"))
        for j, l in enumerate(det):
            tient("petit", l, CW, "p4 public")
        o.append(lignes("petit", det, left=CX, cap=442, pas=22,
                        couleur="c-glacier", largeur=CW))

    o.append(filet(G.x(1), 500, G.CONTENU, "r-sombre"))
    o.append(txt("fort-l", tient("fort-l", C.P4_CHUTE, G.CONTENU, "p4 chute"),
                 left=G.x(1), cap=520, couleur="c-blanc", largeur=G.CONTENU))
    # DEUX lignes ferrees a droite, et non une : « 9 receptions » et « jusqu'a
    # 9 dates » cote a cote remettraient la collision de deux « neuf ».
    for i, ligne_c in enumerate(C.P4_CHIFFRES):
        o.append(txt("petit", tient("petit", ligne_c, G.w(8), "p4 chiffres"),
                     right=G.MARGE, cap=552 + i * 22, couleur="c-glacier",
                     largeur=G.w(8), align="right"))

    o.append(pied("04", sombre=True, mention=mention(C.P4_MENTION),
                  brut_mention=True))
    return page("f-nuit", "".join(o))


# ===========================================================================
# 5 - CE QUE VOTRE SOUTIEN PERMET
# ===========================================================================
def p5():
    """L'autre page neuve. Le v2 disait ce que le partenaire RECOIT ; il ne
    disait nulle part ce que son argent FAIT. Les quatre familles reprennent le
    vocabulaire de mbc974.com/soutenir-le-club/ et de /benevoles/, et les trois
    reperes chiffres sont ceux que le club publie lui-meme."""
    o = [entete(C.P5_SUR, C.P5_TITRE, C.P5_LEAD)]

    for i, (num, nom, items) in enumerate(C.P5_FAMILLES):
        CX, CW = G.x(1 + i * 3), G.w(3)
        o.append(filet(CX, HAUT_CONTENU - 14, CW, "r-clair"))
        o.append(txt("stat-s", num, left=CX, cap=HAUT_CONTENU + 6,
                     extra="color:rgba(13,21,38,.22)"))
        o.append(txt("etiquette", nom, left=CX + GOUT_P5, cap=HAUT_CONTENU + 12,
                     couleur="c-roi"))
        o.append(lignes("petit", items, left=CX, cap=300, pas=30,
                        couleur="c-encre", largeur=CW))

    # La bande des reperes publies, a fond perdu : c'est une CITATION du site,
    # pas une affirmation de plus, et elle doit se lire comme telle.
    Y_R = 392
    o.append(pave(0, Y_R, G.W, BAS_CONTENU - Y_R, "var(--papier-2)"))
    o.append(txt("surtitre", C.P5_REPERES_TITRE, left=G.x(1), cap=Y_R + 24,
                 couleur="c-roi"))
    for i, (val, lib) in enumerate(C.P5_REPERES):
        CX, CW = G.x(1 + i * 3), G.w(3)
        o.append(txt("stat-m", val, left=CX, cap=Y_R + 64, couleur="c-roi"))
        o.append(txt("petit", lib, left=CX, cap=Y_R + 120, couleur="c-encre",
                     largeur=CW))
    OX = G.x(10)
    o.append(filet_v(OX - G.GOUT / 2 - 0.5, Y_R + 24, 140, "r-clair"))
    o.append(txt("etiquette-s", C.P5_OBJECTIF[0], left=OX, cap=Y_R + 64,
                 couleur="c-encre"))
    o.append(txt("petit", C.P5_OBJECTIF[1], left=OX, cap=Y_R + 92, couleur="c-douce",
                 largeur=G.w(3)))

    o.append(pied("05", sombre=False, mention=mention(C.P5_MENTION),
                  brut_mention=True))
    return page("f-papier", "".join(o))


# ===========================================================================
# 6 - VOTRE MARQUE, AVEC LE MBC
# ===========================================================================
def p6():
    """La page qui a le plus change entre la V3 et la V3.1.

    Elle decrivait toute la chaine de diffusion sans dire A PARTIR DE QUELLE
    FORMULE chaque support demarre : un commercant qui signait a 200 EUR apres
    l'avoir lue pouvait croire de bonne foi qu'il aurait les affiches, les
    flyers et les evenements — que la page suivante reserve a 500, et le
    maillot a 1 000. Chaque ligne porte donc son palier, en regard de son
    intitule. C'est aussi, accessoirement, le meilleur argument de montee en
    gamme du dossier : l'ecart entre deux formules se lit d'un coup d'oeil.
    """
    o = [entete(C.P6_SUR, C.P6_TITRE, C.P6_LEAD, sombre=True)]

    # --- A gauche : les supports du site, par effet ET par palier ----------
    TX, TW = G.x(1), G.w(7)
    EX, EW = G.x(5), G.w(3)          # la colonne de droite du bloc
    for i, (titre_e, support, effet, palier) in enumerate(C.P6_EFFETS):
        yy = HAUT_CONTENU + 6 + i * 78
        o.append(filet(TX, yy - 22, TW, "r-sombre"))
        o.append(txt("etiquette-s", tient("etiquette-s", titre_e, G.w(4), "p6 titre"),
                     left=TX, cap=yy, couleur="c-orange"))
        o.append(txt("mention", tient("mention", palier, EW, "p6 palier"),
                     left=EX, cap=yy + 2, couleur="c-glacier", largeur=EW))
        corps = support if i else lien("site", support)
        tient("petit", support, G.w(4), "p6 support")
        o.append(txt("petit", corps, left=TX, cap=yy + 26, couleur="c-blanc",
                     largeur=G.w(4), brut=not i))
        o.append(txt("petit", tient("petit", effet, EW, "p6 effet"),
                     left=EX, cap=yy + 26, couleur="c-glacier", largeur=EW))
    o.append(filet(TX, 524, TW, "r-sombre"))
    o.append(txt("fort", C.P6_DEMARRE, left=TX, cap=544, couleur="c-blanc",
                 largeur=TW))

    # --- A droite : l'emplacement rare -------------------------------------
    PX, PW = G.x(8), G.w(5)
    o.append(pave(PX, 212, PW, BAS_CONTENU - 212, "var(--nuit-3)"))
    IX, IW = PX + RETRAIT_PANNEAU, PW - 2 * RETRAIT_PANNEAU
    # V3.2 : la photo perd 20 px de haut pour que l'offre tienne sur DEUX
    # lignes. Elle disait « pour le dos, parlons-en » ; elle dit maintenant ce
    # qu'All-Star donne ET ce qu'il ne donne pas, ce qui prend une ligne de
    # plus et vaut largement les 20 px.
    o.append(image("maillot-dos-large.jpg", IX, 224, IW, 140, pos="50% 42%",
                   alt="Le dos du maillot du MBC : nom du club et numero, aucun "
                       "logo de partenaire."))
    o.append(txt("etiquette-s", C.P6_RARETE_ETIQ, left=IX, cap=384,
                 couleur="c-glacier"))
    for i, ligne in enumerate(C.P6_RARETE):
        o.append(txt("stat-s", tient("stat-s", ligne, IW, "p6 rarete"), left=IX,
                     cap=410 + i * 37, couleur="c-blanc"))
    # Le seul mot qui dit que l'emplacement est A PRENDRE. Il etait ecrit dans
    # le contenu depuis la V3 et n'avait jamais ete imprime.
    o.append(txt("etiquette", tient("etiquette", C.P6_RARETE_ETAT, IW, "p6 etat"),
                 left=IX, cap=528, couleur="c-orange"))
    o.append(txt("mention", C.P6_RARETE_OFFRE, left=IX, cap=552,
                 couleur="c-glacier", largeur=IW))

    o.append(pied("06", sombre=True, mention=C.P6_MENTION))
    return page("f-nuit", "".join(o))


# ===========================================================================
# 7 - QUATRE FORMULES, DES 200 EUR
# ===========================================================================
def p7():
    """Les memes quatre formules qu'au v2, mais chaque contrepartie porte
    desormais sa ligne de precision. « Visibilite premium » ne veut rien dire
    tant qu'on n'a pas dit OU."""
    o = [entete(C.P7_SUR, C.P7_TITRE, C.P7_LEAD)]

    PAD = RETRAIT_CARTE
    D_NOM = PAD
    D_TEMPO = D_NOM + 26
    D_PRIX = D_TEMPO + 50
    D_FIL = D_PRIX + 54
    D_LIS = D_FIL + 24
    PAS_GLOSE = 18            # ligne principale -> sa precision
    PAS_ENTREE = 22           # precision -> ligne principale suivante
    PAS_SEC = 26              # ligne sans precision -> suivante

    def hauteur(f):
        y = D_LIS
        for j, (main, glose) in enumerate(f["lignes"]):
            if j:
                y += PAS_ENTREE if f["lignes"][j - 1][1] else PAS_SEC
            if glose:
                y += PAS_GLOSE
        cap = typo.metrics("barlow")["cap"]
        dernier = G.STYLES["mention"][1] if f["lignes"][-1][1] else G.STYLES["petit"][1]
        return y + cap * dernier

    CARD_H = round(max(hauteur(f) for f in C.P7_FORMULES) + PAD)
    CARD_Y = BAS_CONTENU - CARD_H

    for i, f in enumerate(C.P7_FORMULES):
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
        o.append(txt("etiquette-s", f["nom"], left=ix, cap=CARD_Y + D_NOM,
                     couleur=c_nom))
        o.append(txt("petit", tient("petit", f["tempo"], iw * 2, "p7 tempo"),
                     left=ix, cap=CARD_Y + D_TEMPO, couleur=c_dim, largeur=iw))
        prix = f["prix"] + EURO + (
            '<span style="font-size:.62em;margin-left:.16em">'
            + f["suffixe"] + '</span>' if f.get("suffixe") else "")
        o.append(txt("prix-s", prix, left=ix, cap=CARD_Y + D_PRIX, couleur=c_txt,
                     brut=True))
        o.append(filet(ix, CARD_Y + D_FIL, iw, "r-roi" if pop else "r-clair"))

        y = D_LIS
        for j, (main, glose) in enumerate(f["lignes"]):
            if j:
                y += PAS_ENTREE if f["lignes"][j - 1][1] else PAS_SEC
            o.append(txt("petit", tient("petit", main, iw, "p7 " + f["nom"]),
                         left=ix, cap=CARD_Y + y, couleur=c_txt, largeur=iw))
            if glose:
                y += PAS_GLOSE
                o.append(txt("mention", tient("mention", glose, iw, "p7 glose"),
                             left=ix, cap=CARD_Y + y, couleur=c_dim, largeur=iw))

    o.append(pied("07", sombre=False, mention=mention(C.P7_MENTION),
                  brut_mention=True))
    return page("f-papier", "".join(o))


# ===========================================================================
# 8 - FAISONS EQUIPE
# ===========================================================================
def p8(avec_contact=True):
    """La cloture absorbe trois pages du v2 : le contact, les trois etapes
    (« Comment on devient partenaire », qui tenait une page entiere) et
    l'administratif (« Un club declare », qui en tenait une autre).

    La V3.1 y ajoute la reponse a la seule question qui restait sans reponse :
    « comment je sais que le club fera ce qu'il promet ? ». Pour lui faire de
    la place sans surcharger, deux choses sont parties : le bloc « TROIS
    FORMES DE SOUTIEN », qui redisait la page 7 et l'etape 02, et l'encart
    d'etat civil, descendu dans la mention — un service achats sait l'y
    chercher, un dirigeant n'a pas a le croiser avant le numero de telephone.
    """
    o = []
    o.append(image("mbc-logo.png", G.MARGE, 48, 78, 80, extra="object-fit:contain"))
    o.append(txt("fort-l", "LA MONTAGNE BASKET CLUB", left=G.MARGE + 100, cap=75,
                 couleur="c-blanc"))

    # --- A gauche : l'appel, et a qui on s'adresse -------------------------
    LX, LW = G.MARGE, G.w(5)
    o.append(titre(C.P8_TITRE, cap=148, left=LX, couleur="c-blanc",
                   largeur=LW, style="d1"))
    o.append(txt("lead", C.P8_LEAD, left=LX, cap=384, couleur="c-glacier",
                 largeur=LW))
    o.append(filet(LX, 456, LW, "r-orange", 2))
    etiq, qui = C.P8_CONTACT if avec_contact else C.P8_CONTACT_SANS
    o.append(txt("surtitre", etiq, left=LX, cap=476, couleur="c-orange"))
    o.append(txt("petit", tient("petit", qui, LW, "p8 contact"), left=LX,
                 cap=500, couleur="c-glacier", largeur=LW))
    o.append(txt("fort-l", lien("mail", C.P8_MAIL), left=LX, cap=532,
                 couleur="c-blanc", brut=True))
    o.append(txt("fort-l", lien("tel", C.P8_TEL), left=LX, cap=566,
                 couleur="c-blanc", brut=True))

    # --- A droite : comment on commence, puis ce qui est garanti -----------
    RX, RW = G.x(6), G.w(7)
    o.append(txt("surtitre", "EN TROIS ÉTAPES", left=RX, cap=168, couleur="c-blanc"))
    for i, (num, lab, sous) in enumerate(C.P8_ETAPES):
        yy = 200 + i * 36
        o.append(filet(RX, yy - 14, RW, "r-roi"))
        o.append(txt("etiquette-s", num, left=RX, cap=yy + 3, couleur="c-orange"))
        o.append(txt("fort", lab, left=RX + GOUT_P8, cap=yy, couleur="c-blanc"))
        o.append(txt("petit", sous, right=G.MARGE, cap=yy + 2, couleur="c-glacier",
                     largeur=G.w(4), align="right"))
    o.append(filet(RX, 200 + 3 * 36 - 14, RW, "r-roi"))

    o.append(txt("surtitre", "CE QUE LE CLUB S’ENGAGE À FAIRE", left=RX, cap=318,
                 couleur="c-blanc"))
    for i, (k, v) in enumerate(C.P8_ENGAGEMENTS):
        yy = 350 + i * 36
        o.append(filet(RX, yy - 14, RW, "r-roi"))
        o.append(txt("etiquette-s", k, left=RX, cap=yy + 2, couleur="c-orange"))
        o.append(txt("petit", tient("petit", v, RW - GOUT_ENG, "p8 engagement"),
                     left=RX + GOUT_ENG, cap=yy, couleur="c-blanc",
                     largeur=RW - GOUT_ENG))
    o.append(filet(RX, 350 + 3 * 36 - 14, RW, "r-roi"))

    QT = QR_P8
    for i, (q, cle, lab, sous) in enumerate(C.P8_QR):
        QX = G.x(6 + i * 3)
        fin = (G.x(9) - G.GOUT) if i == 0 else (G.W - G.MARGE)
        LX2 = QX + QT + 20
        o.append(pave(QX, 468, QT, QT, "var(--blanc)"))
        o.append(qr(q, QX + 7, 475, QT - 14))
        o.append(zone(cle, QX, 468, QT, QT))
        o.append(txt("etiquette-s", tient("etiquette-s", lab, fin - LX2, "p8 QR"),
                     left=LX2, cap=482, couleur="c-blanc"))
        o.append(txt("petit", sous, left=LX2, cap=508, couleur="c-glacier",
                     largeur=fin - LX2, brut=True))

    o.append(filet(G.MARGE, Y_FILET, G.CONTENU, "r-roi"))
    o.append(txt("mention", C.P8_MENTION, left=G.MARGE, bottom=G.H - Y_FILET + 14,
                 largeur=G.CONTENU, couleur="c-glacier"))
    o.append(txt("pied", SIGNATURE, left=G.MARGE, cap=CAP_PIED, couleur="c-glacier"))
    o.append(txt("etiquette-s", C.P8_DEVISE, right=G.MARGE, cap=CAP_PIED - 2,
                 couleur="c-orange", align="right"))
    return page("f-roi", "".join(o))


# ===========================================================================
def construire(avec_contact=True):
    pages = [p1(), p2(), p3(), p4(), p5(), p6(), p7(), p8(avec_contact)]
    return ("<!DOCTYPE html>\n<html lang=\"fr\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<title>MBC La Montagne Basket Club — Dossier partenaire 2026/2027</title>\n"
            "<style>\n" + css.feuille() + "\n</style>\n</head>\n<body>\n"
            + "\n".join(pages) + "\n</body>\n</html>\n")


if __name__ == "__main__":
    # `--sans-contact` produit la variante sans contact nominatif : le titre de
    # secretaire vient du bureau et n'est publie nulle part sur le site.
    avec = "--sans-contact" not in sys.argv
    html = construire(avec)
    nom = "dossier-v3.html" if avec else "dossier-v3-sans-contact.html"
    open(nom, "w", encoding="utf-8").write(html)
    print("%s : %d Ko, %d pages%s"
          % (nom, len(html) // 1024, html.count("<section"),
             "" if avec else "  (variante sans contact nominatif)"))
    if _TROP_LARGE:
        print("\nLIGNES QUI VONT SE REPLIER (chacune decale ce qui la suit) :")
        for ou, st, w, lim, t in _TROP_LARGE:
            print("  %-16s %-10s %4d px > %4d : %s" % (ou, st, w, lim, t))
    else:
        print("aucune ligne ne deborde de sa colonne.")
