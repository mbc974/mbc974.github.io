# -*- coding: utf-8 -*-
"""Les visuels propres au dossier V3.

La V3 change de sujet photographique. Le v2 illustrait des LIEUX — un gymnase
vide en pleine page 5, un plateau desert — alors qu'il vendait une communaute.
Ici les trois photos ajoutees montrent des PERSONNES : des enfants et leurs
parents (page 4), le reportage tele (page 3), le dos du maillot (page 6).

Les autres visuels sont ceux du dossier generique, deja prepares par assets.py
et assets_general.py : couverture.jpg, maillot-dos.jpg, mbc-logo.png, les QR.
"""
import os
from PIL import Image

SITE = r"C:\Users\ALEX\Documents\GitHub\mbc974-site-officiel"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "img")
os.makedirs(OUT, exist_ok=True)


def recadre(src, dst, w, h, fx=0.5, fy=0.5, q=88):
    """Recadre en remplissant w x h, ancre sur (fx, fy). Jamais d'agrandissement
    silencieux : l'echelle est affichee, et au-dessus de 1,00x c'est un defaut."""
    im = Image.open(src).convert("RGB")
    sw, sh = im.size
    cible = w / h
    if sw / sh > cible:
        nw, nh = int(round(sh * cible)), sh
        x, y = int(round((sw - nw) * fx)), 0
    else:
        nw, nh = sw, int(round(sw / cible))
        x, y = 0, int(round((sh - nh) * fy))
    im = im.crop((x, y, x + nw, y + nh))
    if nw != w:
        im = im.resize((w, h), Image.LANCZOS)
    im.save(os.path.join(OUT, dst), "JPEG", quality=q, optimize=True,
            progressive=True, subsampling=1)
    alerte = "  <-- AGRANDI" if nw < w else ""
    print(f"  {dst:26s} {w}x{h}  (source {sw}x{sh}, echelle {nw/w:.2f}x){alerte}")


print("Photos de la V3 :")

# Page 4, pleine page : des enfants ET leurs parents dans le meme cadre. C'est
# la photo qui dit « communaute intergenerationnelle » sans l'ecrire.
recadre(os.path.join(SITE, "assets/galerie/ecole-basket-enfant-mbc-saint-denis.jpg"),
        "communaute.jpg", 1400, 788, fx=0.5, fy=0.46)

# Page 3, bandeau : le sujet de Reunion La 1ere.
recadre(os.path.join(SITE, "assets/galerie/mbc-reportage-reunion-la-1ere.jpg"),
        "reportage.jpg", 1000, 281, fx=0.5, fy=0.42)

# Page 6 : le dos du maillot, en paysage cette fois (la V3 le pose dans une
# colonne large et non plus en portrait a cote d'un second cliche).
recadre(os.path.join(os.path.expanduser("~"), "Downloads", "DSC05076.jpg"),
        "maillot-dos-large.jpg", 852, 470, fx=0.52, fy=0.33)

# LES LOGOS DES PARTENAIRES ne sont pas repris, et ce n'est pas un oubli. Six
# logos lisibles demandent environ 760 x 44 px : la page 3 ne les a pas sans
# ramener ses QR sous le seuil de scan (96 px de plaque, cf. LISEZMOI). A
# 118 x 40 px, l'essai rendait deux des six marques illisibles — or une preuve
# illisible ne prouve rien. Le fait est donc ecrit en toutes lettres :
# « Cinq entreprises et associations, aux cotes d'InPlay. » Si le bureau veut
# la bande de logos, il faut lui donner sa propre demi-page.
print("\nLogos des partenaires : volontairement absents (voir le commentaire).")
