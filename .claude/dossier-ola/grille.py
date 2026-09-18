# -*- coding: utf-8 -*-
"""La grille et l'echelle de texte du dossier. Un seul point de verite.

Le dossier d'origine n'avait ni l'une ni l'autre : neuf tailles de titre pour dix
pages (49,5 / 50,25 / 53,25 / 55,5 / 58,5 / 59,25 / 62,25 / 76,5 / 84,75 pt), la
taille ayant visiblement ete reduite page par page pour faire tenir le texte. Ici
les titres ont UNE taille, et c'est le texte qui s'y plie.
"""
import typo

# --- La page ---------------------------------------------------------------
# 1280 x 720 px = 13,333 x 7,5 in = 960 x 540 pt : le 16:9 standard des decks.
W, H = 1280, 720
MARGE = 64            # gauche et droite
HAUT = 56             # premiere ligne de la grille
BAS = 56              # ligne du pied

CONTENU = W - 2 * MARGE          # 1152
COLS, GOUT = 12, 24
COL = (CONTENU - (COLS - 1) * GOUT) / COLS   # 74.0 px pile
RYTHME = 8            # toute position verticale est un multiple de 8

def x(col):
    """Bord gauche de la colonne col (1-indexee)."""
    return MARGE + (col - 1) * (COL + GOUT)

def w(n):
    """Largeur de n colonnes accolees, gouttieres comprises."""
    return n * COL + (n - 1) * GOUT

assert abs(COL - 74.0) < 1e-9, COL
assert abs(x(1) + w(12) - (W - MARGE)) < 1e-9
assert abs(x(7) - (MARGE + 6 * (COL + GOUT))) < 1e-9

# --- L'echelle de texte ----------------------------------------------------
# Interligne des capitales Anton : une capitale accentuee monte a 1,1006 em
# au-dessus de la ligne de base (mesure, cf. typo.py). Un interligne inferieur
# fait mordre l'accent d'une ligne sur celle du dessus — c'est ce que .9 faisait
# dans l'essai. 1,12 garantit la garde en toutes lettres.
LH_TITRE = 1.12
LH_CORPS = 1.45
LH_SERRE = 1.30

STYLES = {
    #  nom            police       taille  interligne  interlettre
    "d1":          ("anton",        104,   LH_TITRE,   "0.005em"),   # couverture / cloture
    "d2":          ("anton",         64,   LH_TITRE,   "0.008em"),   # titre de page, UNIQUE
    "d3":          ("anton",         30,   1.20,       "0.014em"),   # tete de section
    "stat-xl":     ("anton",        132,   1.00,       "-0.004em"),  # le chiffre phare
    "stat-l":      ("anton",         76,   1.00,       "0.000em"),   # chiffres secondaires
    "stat-m":      ("anton",         46,   1.00,       "0.004em"),
    "stat-s":      ("anton",         38,   1.00,       "0.006em"),
    "prix":        ("anton",         66,   1.00,       "0.000em"),
    "prix-s":      ("anton",         46,   1.00,       "0.000em"),
    "num":         ("anton",         84,   1.00,       "0.000em"),   # 01 / 02 / 03
    "lead":        ("barlow",        26,   1.38,       "0.000em"),
    "corps":       ("barlow",        20,   LH_CORPS,   "0.002em"),
    "corps-s":     ("barlow",        18,   LH_CORPS,   "0.002em"),
    "petit":       ("barlow",        16,   LH_SERRE,   "0.004em"),
    "mention":     ("barlow",        13,   1.35,       "0.006em"),
    "pied":        ("barlow",        13,   1.20,       "0.060em"),
    "surtitre":    ("barlow600",     15,   1.20,       "0.150em"),   # oeil-de-boeuf
    "etiquette":   ("barlow600",     17,   1.25,       "0.040em"),
    "etiquette-s": ("barlow600",     15,   1.25,       "0.040em"),
    "fort":        ("barlow600",     20,   LH_CORPS,   "0.002em"),
    "fort-l":      ("barlow600",     26,   1.30,       "0.002em"),
    "pagenum":     ("barlow600",     15,   1.20,       "0.040em"),
}

def style(nom):
    police, taille, lh, ls = STYLES[nom]
    return dict(police=police, taille=taille, lh=lh, ls=ls)

def decalage_cap(nom):
    """Distance, en px, entre le bord haut de la boite et le HAUT DES CAPITALES.

    C'est la mesure qui permet de poser un titre sur la grille par son encre et
    non par sa boite : deux titres de tailles differentes, ou l'un accentue et
    l'autre pas, s'alignent alors exactement.
    """
    s = STYLES[nom]
    police, taille, lh = s[0], s[1], s[2]
    m = typo.metrics(police)
    demi_interligne = (lh - (m["asc"] - m["desc"])) / 2
    return taille * (demi_interligne + m["asc"] - m["cap"])

def decalage_base(nom):
    """Distance, en px, entre le bord haut de la boite et la 1re ligne de base."""
    s = STYLES[nom]
    police, taille, lh = s[0], s[1], s[2]
    m = typo.metrics(police)
    return taille * ((lh - (m["asc"] - m["desc"])) / 2 + m["asc"])

def largeur_texte(nom, texte):
    """Largeur d'encre d'une chaine dans un style donne, en px.

    Sert a dimensionner ce qui doit envelopper du texte (pastille, bouton) :
    une largeur devinee laisse deborder le dernier glyphe, ce qui est arrive a
    la pastille RECOMMANDE de la page 8 (118 px devines pour 131 mesures).
    """
    police, taille, _, ls = STYLES[nom]
    inter = float(ls.replace("em", "")) * taille
    total = 0.0
    prem = der = None
    for i, ch in enumerate(texte):
        b = typo.glyph_box(police, ch)
        if b is None:
            continue
        total += b[4] * taille + inter
        if (b[2] - b[0]) > 0:
            if prem is None:
                prem = b[0] * taille
            der = b[4] * taille - b[2] * taille
    if prem is None:
        return 0.0
    # On retire l'interlettrage en trop apres le dernier glyphe, et les deux
    # side bearings : ce qui reste est l'encre.
    return total - inter - prem - der


def indent(nom, texte):
    """text-indent qui pose l'encre du 1er glyphe pile sur la marge."""
    return typo.indent_css(STYLES[nom][0], texte)

if __name__ == "__main__":
    print(f"page {W}x{H}  contenu {CONTENU}  colonne {COL}  gouttiere {GOUT}")
    for i in (1, 4, 7, 10, 13):
        if i <= 12:
            print(f"  col {i:2d} -> x={x(i):7.1f}   w(4 cols)={w(4):.1f}")
    print()
    print(f"{'style':12s} {'police':10s} {'px':>4s} {'lh':>5s}  {'cap_top':>8s} {'baseline':>8s}")
    for n in STYLES:
        s = STYLES[n]
        print(f"{n:12s} {s[0]:10s} {s[1]:4d} {s[2]:5.2f}  "
              f"{decalage_cap(n):8.2f} {decalage_base(n):8.2f}")
