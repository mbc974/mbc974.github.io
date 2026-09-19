# -*- coding: utf-8 -*-
"""Primitives de mise en page. Tout se pose sur la grille, rien a l'oeil."""
import html as _h
import grille as G

def esc(t):
    return _h.escape(t, quote=False)


# --- Ponctuation francaise -------------------------------------------------
# En francais, le point-virgule, le deux-points, le point d'exclamation, le
# point d'interrogation et les guillemets prennent une espace AVANT. Avec une
# espace ordinaire, la ligne peut casser juste avant le signe : la page 8 de
# la V3.1 affichait « ... fait l'objet d'une facture » puis, ligne suivante,
# « ; si votre soutien... ». L'espace fine insecable U+202F serait la bonne,
# mais elle est ABSENTE des sous-ensembles du site (Chrome y substituerait
# Times New Roman en silence) ; U+00A0, elle, est couverte par les huit
# fichiers de police. Verifie.
#
# L'option est DESACTIVEE par defaut : les dossiers OLA et generique ont ete
# rendus et relus sans elle, et la changer decalerait leurs coupures de ligne
# sans qu'on l'ait demande. `dossier_v3` l'active pour lui seul.
TYPO_FR = False
INSECABLE = "\u00A0"


def _typo_fr(html):
    """Espace insecable avant ; : ! ? et dans les guillemets, HORS balises."""
    import re
    morceaux = re.split(r"(<[^>]+>)", html)
    for i in range(0, len(morceaux), 2):        # 0, 2, 4... = le texte
        t = morceaux[i]
        t = re.sub(r" ([;:!?\u00BB])", INSECABLE + r"\1", t)
        t = re.sub(r"(\u00AB) ", r"\1" + INSECABLE, t)
        morceaux[i] = t
    return "".join(morceaux)

def _cls(*c):
    return " ".join(x for x in c if x)

def txt(style, contenu, left=None, top=None, cap=None, largeur=None,
        couleur=None, extra="", align=None, right=None, bottom=None,
        optique=True, brut=False):
    """Un bloc de texte pose par le HAUT DE SES CAPITALES (cap=) ou par sa boite (top=).

    `optique` annule le side bearing du premier glyphe : l'encre commence alors
    exactement sur la marge demandee, quelle que soit la police et la lettre.
    C'est la correction du defaut le plus visible du dossier d'origine, ou six
    bords gauches differents coexistaient sur une meme page.
    """
    st = []
    if left is not None:
        st.append(f"left:{left:.2f}px")
    if right is not None:
        st.append(f"right:{right:.2f}px")
    if largeur is not None:
        st.append(f"width:{largeur:.2f}px")
    if cap is not None:
        st.append(f"top:{cap - G.decalage_cap(style):.3f}px")
    elif top is not None:
        st.append(f"top:{top:.2f}px")
    if bottom is not None:
        st.append(f"bottom:{bottom:.2f}px")
    if align:
        st.append(f"text-align:{align}")
    if optique:
        # margin-left et NON text-indent : text-indent ne decale que la PREMIERE
        # ligne, si bien qu'un bloc de deux lignes voyait sa seconde ligne
        # repartir du side bearing (mesure : +2,44 px sur un titre Anton 64,
        # +1,22 px sur une mention Barlow 13). Le margin decale la boite
        # entiere, donc toutes ses lignes. La largeur est recompensee pour que
        # le bord droit du bloc ne bouge pas.
        import typo
        police = G.STYLES[style][0]
        taille = G.STYLES[style][1]
        plat = _plat(contenu)
        if align == "right":
            d = typo.rsb(police, plat) * taille
            if abs(d) > 1e-4:
                st.append(f"margin-right:{-d:.3f}px")
        else:
            d = typo.lsb(police, plat) * taille
            if abs(d) > 1e-4:
                st.append(f"margin-left:{-d:.3f}px")
                if largeur is not None:
                    st = [x for x in st if not x.startswith("width:")]
                    st.append(f"width:{largeur + d:.2f}px")
    if extra:
        st.append(extra.rstrip(";"))
    corps = contenu if brut else esc(contenu)
    if TYPO_FR:
        corps = _typo_fr(corps)
    return (f'<div class="{_cls("b", "t-" + style, couleur)}" '
            f'style="{";".join(st)}">{corps}</div>')

def _plat(contenu):
    """Texte sans balises, pour mesurer le side bearing du 1er glyphe reel."""
    import re
    return re.sub(r"<[^>]+>", "", contenu).lstrip()

def lignes(style, items, left, cap, pas, couleur=None, largeur=None, extra=""):
    """Plusieurs lignes independantes, chacune posee sur la grille.

    On ne compte pas sur l'interligne pour l'espacement : chaque ligne a sa
    position, donc un retour a la ligne dans l'une ne decale pas les autres.
    """
    out = []
    for i, it in enumerate(items):
        out.append(txt(style, it, left=left, cap=cap + i * pas,
                       couleur=couleur, largeur=largeur, extra=extra))
    return "".join(out)

def filet(left, top, largeur, classe="r-clair", epaisseur=1):
    return (f'<div class="r {classe}" style="left:{left:.2f}px;top:{top:.2f}px;'
            f'width:{largeur:.2f}px;height:{epaisseur}px"></div>')

def filet_v(left, top, hauteur, classe="r-clair", epaisseur=1):
    return (f'<div class="r {classe}" style="left:{left:.2f}px;top:{top:.2f}px;'
            f'width:{epaisseur}px;height:{hauteur:.2f}px"></div>')

def pave(left, top, largeur, hauteur, fond, extra=""):
    return (f'<div class="b" style="left:{left:.2f}px;top:{top:.2f}px;'
            f'width:{largeur:.2f}px;height:{hauteur:.2f}px;background:{fond};'
            f'{extra}"></div>')

def image(src, left, top, largeur, hauteur, pos="50% 50%", extra="", alt=""):
    return (f'<img class="im" src="img/{src}" alt="{esc(alt)}" '
            f'style="left:{left:.2f}px;top:{top:.2f}px;width:{largeur:.2f}px;'
            f'height:{hauteur:.2f}px;object-position:{pos};{extra}">')

def qr(src, left, top, taille, fond="#FFFFFF", marge=0):
    """Un QR vectoriel. Sa plaque blanche est dimensionnee ici, pas dans le SVG."""
    out = ""
    if marge:
        out += pave(left - marge, top - marge, taille + 2 * marge,
                    taille + 2 * marge, fond)
    out += (f'<img class="qr" src="img/{src}" alt="" '
            f'style="left:{left:.2f}px;top:{top:.2f}px;'
            f'width:{taille:.2f}px;height:{taille:.2f}px">')
    return out

# --- Le pied de page, strictement identique d'une page a l'autre ------------
# Dans le dossier d'origine l'ecart entre la mention et le pied valait 22,4 /
# 23,3 / 25,6 / 27,1 / 28,6 / 30,8 / 31,6 pt selon la page : sept valeurs pour
# une meme respiration.
#
# Et surtout : la mention y etait posee par le HAUT. Des qu'elle passait a deux
# lignes, sa seconde ligne tombait sur le pied. Ici elle est ancree par le BAS
# (propriete CSS `bottom`), donc elle POUSSE VERS LE HAUT : une, deux ou trois
# lignes degagent toujours le filet de la meme facon.
Y_FILET = G.H - 72              # 648 : le filet du pied
CAP_PIED = G.H - 56             # 664 : haut des capitales de la signature
BAS_MENTION = G.H - Y_FILET + 14        # ancrage bas de la mention
BAS_CONTENU = Y_FILET - 76      # 572 : rien d'autre ne descend plus bas

SIGNATURE = "MBC × OLA ENERGY  ·  SAISON 2026/2027"


def pied(numero, sombre, mention=None, largeur_mention=None, left_mention=None,
         brut_mention=False):
    """`brut_mention` laisse passer le HTML de la mention — utile depuis la V3,
    dont les mentions citent des URL que l'on veut CLIQUABLES. Sans lui, un
    <a href> s'affiche en toutes lettres au bas de la page."""
    coul = "c-glacier" if sombre else "c-douce"
    out = filet(G.MARGE, Y_FILET, G.CONTENU, "r-sombre" if sombre else "r-clair")
    if mention:
        out += txt("mention", mention, left=left_mention or G.MARGE,
                   bottom=BAS_MENTION, largeur=largeur_mention or G.CONTENU,
                   couleur=coul, brut=brut_mention)
    out += txt("pied", SIGNATURE, left=G.MARGE,
               cap=CAP_PIED, couleur=coul)
    if numero:
        out += txt("pagenum", numero, right=G.MARGE, cap=CAP_PIED,
                   couleur="c-glacier" if sombre else "c-encre",
                   align="right")
    return out


def cap_apres_titre(nb_lignes, ecart=34, style="d2", cap_titre=96):
    """Haut des capitales du sous-titre, mesure depuis l'ENCRE du titre.

    Le sous-titre etait cale a une position fixe : sous un titre de deux lignes
    il ne restait que 9 px, sous un titre d'une ligne 80. Ici l'ecart est
    constant parce qu'il part du bas des capitales du titre.
    """
    police, taille, lh, _ = G.STYLES[style]
    import typo
    bas_encre = cap_titre + (nb_lignes - 1) * taille * lh + typo.metrics(police)["cap"] * taille
    return round(bas_encre + ecart)

def surtitre(texte, cap=G.HAUT, couleur=None, left=G.MARGE):
    return txt("surtitre", texte, left=left, cap=cap, couleur=couleur)

def titre(texte_html, cap=None, left=G.MARGE, couleur=None, largeur=None,
          style="d2"):
    """Le titre de page, UNE LIGNE PAR BLOC POSITIONNE.

    Chaque ligne recoit la compensation de son propre premier glyphe : un bloc
    unique ne pourrait en compenser qu'un seul, alors que le V de « VINGT » et
    le U de « UNE DECISION » n'ont pas le meme side bearing dans Anton.
    """
    if cap is None:
        cap = G.HAUT + 32
    police, taille, lh, _ = G.STYLES[style]
    out = []
    for i, ligne in enumerate(texte_html.split("<br>")):
        out.append(txt(style, ligne, left=left, cap=cap + i * taille * lh,
                       couleur=couleur, largeur=largeur or G.CONTENU, brut=True))
    return "".join(out)
