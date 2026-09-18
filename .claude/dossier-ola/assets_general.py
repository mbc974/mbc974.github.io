# -*- coding: utf-8 -*-
"""Visuels propres au dossier partenaire GENERIQUE.

Les maquettes du dossier OLA portent la marque OLA a chaque plan : elles ne
peuvent pas servir ici. La page 4 s'appuie a la place sur les photos de maillot
du 18/09/2026, qui montrent l'argument noir sur blanc : la face porte deja trois
marques, le dos n'en porte AUCUNE.
"""
import os
from PIL import Image
import segno

SITE = r"C:\Users\ALEX\Documents\GitHub\mbc974-site-officiel"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "img")
TELECH = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(OUT, exist_ok=True)


def recadre(src, dst, w, h, fx=0.5, fy=0.5, q=88):
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
    print(f"  {dst:28s} {w}x{h}  (source {sw}x{sh}, echelle {nw/w:.2f}x)")


print("Maillots (photos du 18/09/2026) :")
# Le dos du 12 : c'est LA photo de la page 4. Cadre portrait serre sur le dossard.
recadre(os.path.join(TELECH, "DSC05076.jpg"), "maillot-dos.jpg",
        1120, 1400, fx=0.52, fy=0.36)
# La face du 34 : montre les trois marques deja presentes.
recadre(os.path.join(TELECH, "DSC04996.jpg"), "maillot-face.jpg",
        760, 950, fx=0.52, fy=0.30)
# Le dos du 9, en reserve (deuxieme angle).
recadre(os.path.join(TELECH, "DSC04885.jpg"), "maillot-dos-2.jpg",
        760, 950, fx=0.50, fy=0.36)

print("\nSupports produits par le club :")
recadre(os.path.join(SITE, "assets/affiches/mbc-premier-match-sainte-suzanne-2026.jpg"),
        "affiche-match.jpg", 700, 875)
recadre(os.path.join(SITE, "assets/affiches/calendrier-phase1-2026-2027-07b7787b.png"),
        "affiche-calendrier.jpg", 700, 875)

print("\nQR propres au dossier generique :")
segno.make("https://mbc974.com/sponsor-club-basket-reunion/", error="q").save(
    os.path.join(OUT, "qr-partenaires.svg"), scale=10, border=2,
    dark="#0D1526", light=None, omitsize=True)
print("  qr-partenaires.svg          -> mbc974.com/sponsor-club-basket-reunion/")
