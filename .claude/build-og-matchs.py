# -*- coding: utf-8 -*-
"""Dessine l'image de partage (og:image) de chaque rencontre.

    python .claude/build-og-matchs.py
    python .claude/build-og-matchs.py --essai   affiche le bilan, n'ecrit rien

POURQUOI CE SCRIPT EXISTE
-------------------------
Six fiches de match sur sept partageaient la MEME image : social-preview.png,
la banniere generique du site. Coller le lien d'une rencontre dans une
conversation WhatsApp — c'est le geste principal du club le vendredi soir —
affichait donc un visuel qui ne disait ni contre qui, ni quand, ni ou. Seule
la premiere journee avait son affiche, faite a la main.

Ici, chaque rencontre a la sienne, dessinee a partir de data/matchs.json. Rien
n'est saisi : l'adversaire, la date, l'heure, le lieu et l'entree libre en
sortent, et le score s'y ajoute des qu'il est publie.

DEUX ETATS, PARCE QU'UNE AFFICHE A DEUX VIES
--------------------------------------------
  a venir : MBC  vs  SAINTE-SUZANNE / VEN. 11 SEPT. 20H30 / GYMNASE / ENTREE LIBRE
  jouee   : le score prend la place de l'heure, et le bandeau dit TERMINE.

Le meme lien, partage avant et apres, ne raconte donc pas la meme chose — et
c'est bien ce qu'on attend de lui.

FORMAT
------
1200 x 630, le format que Facebook, WhatsApp, Messenger, X et Discord
recadrent le moins. Les textes tiennent dans une marge de securite de 60 px :
certains clients rognent les bords.
"""
import io
import json
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("!! Pillow est requis : python -m pip install pillow")

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
SORTIE = os.path.join(RACINE, "assets", "og")

L, H = 1200, 630
MARGE = 72

# La charte, reprise telle quelle de .claude/affiche-calendrier.py : deux
# generateurs qui dessinent pour le meme club ne doivent pas avoir deux bleus.
NUIT = (9, 16, 32)
NUIT_2 = (13, 21, 38)
BLEU = (27, 81, 158)
ORANGE = (232, 130, 42)
ORANGE_S = (215, 105, 26)
BLANC = (255, 255, 255)
GLACIER = (150, 173, 197)
ENCRE = (6, 12, 26)
VERT = (143, 224, 166)

ANTON = os.path.join(ICI, "fonts", "Anton-Regular.ttf")
BARLOW_C = os.path.join(ICI, "fonts", "BarlowCondensed-SemiBold.ttf")

JOURS = [u"lundi", u"mardi", u"mercredi", u"jeudi", u"vendredi", u"samedi", u"dimanche"]
MOIS = [u"janv.", u"févr.", u"mars", u"avril", u"mai", u"juin",
        u"juil.", u"août", u"sept.", u"oct.", u"nov.", u"déc."]


def police(chemin, taille):
    return ImageFont.truetype(chemin, taille)


def larg(d, txt, f, espace=0):
    if espace:
        return int(sum(d.textlength(c, font=f) for c in txt) + espace * max(0, len(txt) - 1))
    b = d.textbbox((0, 0), txt, font=f)
    return b[2] - b[0]


def texte(d, xy, txt, f, fill, espace=0, centre=None):
    """Ecrit un texte. PIL ne sait pas interlettrer : on le fait a la main,
    caractere par caractere — c'est ce qui donne aux capitales le meme
    espacement que sur le site."""
    x, y = xy
    if centre is not None:
        x = centre - larg(d, txt, f, espace) // 2
    if not espace:
        d.text((x, y), txt, font=f, fill=fill)
        return larg(d, txt, f)
    for c in txt:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + espace
    return larg(d, txt, f, espace)


def ajuste(chemin, txt, maxi, depart, mini=28, espace=0):
    """La plus grande taille a laquelle `txt` tient dans `maxi` pixels.

    « Picks La Possession 3 » fait plus du double de « MTG » : sans cela, le
    nom du club deborderait du cadre ou sortirait minuscule selon la journee.
    """
    img = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(img)
    t = depart
    while t > mini and larg(d, txt, police(chemin, t), espace) > maxi:
        t -= 2
    return police(chemin, t)


def fond():
    """Un degrade nuit, plus clair vers le haut a droite : la meme lumiere que
    le hero du site, qui vient du meme cote."""
    im = Image.new("RGB", (L, H), NUIT)
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / float(H)
        d.line([(0, y), (L, y)],
               fill=(int(NUIT_2[0] + (NUIT[0] - NUIT_2[0]) * k),
                     int(NUIT_2[1] + (NUIT[1] - NUIT_2[1]) * k),
                     int(NUIT_2[2] + (NUIT[2] - NUIT_2[2]) * k)))
    # halo bleu en haut a droite
    halo = Image.new("RGB", (L, H), NUIT)
    hd = ImageDraw.Draw(halo)
    hd.ellipse([L - 620, -360, L + 190, 300], fill=BLEU)
    from PIL import ImageFilter
    halo = halo.filter(ImageFilter.GaussianBlur(150))
    im = Image.blend(im, halo, 0.30)
    # liseré orange en pied : la signature du club, deja sur l'affiche calendrier
    ImageDraw.Draw(im).rectangle([0, H - 10, L, H], fill=ORANGE)
    return im


def ecusson(d, im, cx, cy, r, chemin, sigle):
    """L'ecusson du club, ou son sigle dans une pastille si l'image manque —
    exactement le repli que le site applique en HTML avec onerror."""
    p = os.path.join(RACINE, chemin) if chemin else None
    if p and os.path.exists(p):
        try:
            logo = Image.open(p).convert("RGBA")
            logo.thumbnail((r * 2, r * 2), Image.LANCZOS)
            im.paste(logo, (cx - logo.width // 2, cy - logo.height // 2), logo)
            return
        except Exception:
            pass
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 18),
              outline=GLACIER, width=3)
    f = ajuste(BARLOW_C, sigle, r * 2 - 16, 46, 18, 1)
    texte(d, (0, cy - 22), sigle, f, BLANC, 1, centre=cx)


def logo_club(nom):
    for ext in (".webp", ".png"):
        p = "assets/logos/clubs/%s%s" % (nom, ext)
        if os.path.exists(os.path.join(RACINE, p)):
            return p
    return None


def carte(m, d_):
    im = fond()
    d = ImageDraw.Draw(im, "RGBA")
    club = d_["club"]
    dom = m["domicile"]
    joue = bool(m.get("score"))

    # --- bandeau du haut : competition + journee, ou TERMINE -----------------
    f_kick = police(BARLOW_C, 30)
    if joue:
        texte(d, (MARGE, 54), u"TERMINÉ", f_kick, ORANGE, 6)
        x = MARGE + larg(d, u"TERMINÉ", f_kick, 6) + 22
    else:
        x = MARGE
    texte(d, (x, 54), u"%s · J%d" % (d_["competition"]["nom"].upper(), m["journee"]),
          f_kick, GLACIER, 5)

    # --- le duel -------------------------------------------------------------
    gauche = club["court"] if dom else m["adversaireCourt"]
    droite = m["adversaireCourt"] if dom else club["court"]
    # UNE SEULE taille pour les deux camps : la plus petite des deux.
    # Ajuster chaque cote separement donnait un « MBC » deux fois plus haut que
    # « SAINTE-SUZANNE » — sur une affiche de duel, cela se lit comme un
    # rapport de force, pas comme une contrainte typographique.
    lg_max = 400
    f_g = ajuste(ANTON, gauche.upper(), lg_max, 92, 40, 2)
    f_d = ajuste(ANTON, droite.upper(), lg_max, 92, 40, 2)
    f_duel = f_g if f_g.size <= f_d.size else f_d
    # la ligne de base descend quand les noms sont petits, pour rester centree
    yb = 250 + (92 - f_duel.size) // 3
    texte(d, (0, yb), gauche.upper(), f_duel, BLANC, 2, centre=300)
    texte(d, (0, yb), droite.upper(), f_duel, BLANC, 2, centre=900)

    f_vs = police(ANTON, 46)
    texte(d, (0, yb + 14), u"VS", f_vs, ORANGE, 3, centre=600)

    # les ecussons, au-dessus de chaque nom
    lg_adv = logo_club(m.get("logo") or "")
    ecusson(d, im, 300, 150, 58, "assets/logos/mbc-logo.png" if dom else lg_adv,
            club["sigle"] if dom else m["sigle"])
    ecusson(d, im, 900, 150, 58, lg_adv if dom else "assets/logos/mbc-logo.png",
            m["sigle"] if dom else club["sigle"])

    # --- le score, quand il existe : il prend la place de l'heure ------------
    y = 392
    if joue:
        s = m["score"]
        pour = s["mbc"] if dom else s["adverse"]
        contre = s["adverse"] if dom else s["mbc"]
        f_sc = police(ANTON, 78)
        coul = VERT if s["mbc"] > s["adverse"] else BLANC
        texte(d, (0, y), u"%d – %d" % (pour, contre), f_sc, coul, 4, centre=600)
        y += 108
    else:
        dt = m["_dt"]
        quand = u"%s %d %s · %s" % (JOURS[dt.weekday()].upper(), dt.day,
                                    MOIS[dt.month - 1].upper(), m["heure"].replace(":", "H"))
        f_q = ajuste(BARLOW_C, quand, L - 2 * MARGE, 44, 26, 4)
        texte(d, (0, y), quand, f_q, BLANC, 4, centre=600)
        y += 66

    # --- lieu ----------------------------------------------------------------
    lieu = (m["_lieu"]["nom"] if m.get("_lieu") else u"Chez l'adversaire").upper()
    f_l = ajuste(BARLOW_C, lieu, L - 2 * MARGE, 32, 20, 3)
    texte(d, (0, y), lieu, f_l, GLACIER, 3, centre=600)
    y += 54

    # --- entree libre : une pastille, seulement si la DONNEE le dit ----------
    if m.get("entreeLibre") and not joue:
        f_e = police(BARLOW_C, 26)
        t = u"ENTRÉE LIBRE"
        w = larg(d, t, f_e, 4) + 44
        d.rounded_rectangle([600 - w // 2, y, 600 + w // 2, y + 46], 23,
                            fill=ORANGE_S)
        texte(d, (0, y + 8), t, f_e, ENCRE, 4, centre=600)
    return im


def main():
    essai = "--essai" in sys.argv
    sys.path.insert(0, ICI)
    import importlib.util
    sp = importlib.util.spec_from_file_location("bm", os.path.join(ICI, "build-matchs.py"))
    bm = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(bm)
    d = bm.charger()

    if not essai and not os.path.isdir(SORTIE):
        os.makedirs(SORTIE)
    for m in d["matchs"]:
        nom = "og-%s.jpg" % m["slug"]
        chemin = os.path.join(SORTIE, nom)
        if essai:
            print(u"  %s  (%s)" % (nom, u"jouee" if m.get("score") else u"a venir"))
            continue
        im = carte(m, d)
        # JPEG et non PNG : WhatsApp recompresse de toute facon, et un PNG de
        # 1200x630 pese six fois plus pour un rendu identique apres son passage.
        im.save(chemin, "JPEG", quality=88, optimize=True, progressive=True)
        print(u"  %-56s %5.0f Ko" % ("assets/og/" + nom, os.path.getsize(chemin) / 1024.0))
    if essai:
        print(u"  (essai : rien n'a ete ecrit)")
        return 0
    print(u"\n  ne pas oublier : python .claude/build-matchs.py puis bump-assets.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
