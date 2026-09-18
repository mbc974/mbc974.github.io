# -*- coding: utf-8 -*-
"""Prepare les visuels du dossier : recadrages haute definition + QR vectoriels.

Deux visuels du dossier d'origine etaient sous-definis : la photo de couverture
(712x668 pour 720x675 pt, soit ~71 dpi) et celle du territoire (576x600 AGRANDIE
pour remplir 648x675 pt). Les originaux existent dans le depot, jusqu'a 2800 px :
on repart d'eux.
"""
import os, shutil
from PIL import Image
import segno

SITE = r"C:\Users\ALEX\Documents\GitHub\mbc974-site-officiel"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "img")
# Le PDF d'origine, dont on reprend les cinq visuels composes.
ORIGINE = os.path.join(os.path.expanduser("~"), "Downloads", "Dossier-OLA-MBC.pdf")
os.makedirs(OUT, exist_ok=True)

def crop_cover(src, dst, w, h, focus_x=0.5, focus_y=0.5, quality=88):
    """Recadre en remplissant le cadre w x h, ancre sur (focus_x, focus_y)."""
    im = Image.open(src).convert("RGB")
    sw, sh = im.size
    target = w / h
    if sw / sh > target:                       # source trop large : on rogne en largeur
        nw = int(round(sh * target)); nh = sh
        x = int(round((sw - nw) * focus_x)); y = 0
    else:                                      # source trop haute : on rogne en hauteur
        nw = sw; nh = int(round(sw / target))
        x = 0; y = int(round((sh - nh) * focus_y))
    im = im.crop((x, y, x + nw, y + nh))
    if nw != w:
        im = im.resize((w, h), Image.LANCZOS)
    im.save(os.path.join(OUT, dst), "JPEG", quality=quality, optimize=True,
            progressive=True, subsampling=1)
    print(f"  {dst:26s} {w}x{h}  (source {sw}x{sh}, recadre {nw}x{nh}, "
          f"echelle {nw/w:.2f}x)")

def qr(data, dst, dark="#0D1526"):
    """QR en SVG : net a toute taille, contrairement aux PNG 396 px d'origine."""
    q = segno.make(data, error="q")
    path = os.path.join(OUT, dst)
    q.save(path, scale=10, border=2, dark=dark, light=None, svgclass=None,
           lineclass=None, omitsize=True)
    print(f"  {dst:26s} {q.symbol_size(scale=1, border=2)[0]} modules  <- {data}")

print("Photos :")
# Couverture : le regroupement de l'ecole de basket. Original 2800x1119.
crop_cover(os.path.join(SITE, "assets/images/mbc-hero-regroupement-2800.webp"),
           "couverture.jpg", 2560, 1440, focus_x=0.42, focus_y=0.55)
# Territoire : le plateau couvert de Ruisseau Blanc, vue mer. Original 1300x866.
crop_cover(os.path.join(SITE, "assets/images/ruisseau-blanc-vue-mer.jpg"),
           "territoire.jpg", 1300, 866, focus_x=0.5, focus_y=0.5)
# Le gymnase, pour la page territoire (deuxieme lieu). Original 1445x1088.
crop_cover(os.path.join(SITE, "assets/images/gymnase-la-montagne-clair.jpg"),
           "gymnase.jpg", 1120, 840, focus_x=0.5, focus_y=0.5)
# Inauguration du plateau avec les elus : la preuve institutionnelle.
crop_cover(os.path.join(SITE, "assets/galerie/inauguration-plateau-officiels.jpg"),
           "inauguration.jpg", 760, 1009, focus_x=0.5, focus_y=0.5)
# L'ecole de basket, pour la page des contenus.
crop_cover(os.path.join(SITE, "assets/galerie/ecole-basket-enfant-mbc-saint-denis.jpg"),
           "ecole.jpg", 1400, 821, focus_x=0.5, focus_y=0.5)

print("\nRepris du dossier d'origine (aucune source de meilleure qualite) :")
# Ces cinq visuels sont des COMPOSITIONS (maquettes OLA, captures d'ecran,
# affiche de joueur) dont le depot ne contient pas d'original : on les extrait
# du PDF d'origine. S'il n'est pas la, on garde ce qui est deja dans img/, pour
# que le generateur reste utilisable sans lui.
REPRIS = [(18, "simulations.jpg"),     # les maquettes OLA composees
          (6, "site.jpg"),             # capture de mbc974.com
          (8, "reel.jpg"),             # capture du reel Facebook
          (22, "affiche-joueur.jpg"),  # affiche de joueur
          (26, "officiels.jpg")]       # les officiels a l'inauguration

if os.path.exists(ORIGINE):
    import fitz
    _doc = fitz.open(ORIGINE)
    for xref, dst in REPRIS:
        try:
            _img = _doc.extract_image(xref)
        except Exception as e:
            print(f"  {dst:26s} NON EXTRAIT ({e})")
            continue
        with open(os.path.join(OUT, dst), "wb") as f:
            f.write(_img["image"])
        print(f"  {dst:26s} {_img['width']}x{_img['height']}  (xref {xref})")
else:
    for _, dst in REPRIS:
        etat = "deja present" if os.path.exists(os.path.join(OUT, dst)) else "MANQUANT"
        print(f"  {dst:26s} {etat}  (PDF d'origine introuvable)")

# Le logo : l'original transparent du depot, pas la version aplatie sur fond bleu.
shutil.copy(os.path.join(SITE, "assets/logos/mbc-logo.png"),
            os.path.join(OUT, "mbc-logo.png"))
print(f"  {'mbc-logo.png':26s} 288x296 (transparent)")

print("\nQR codes (vectoriels) :")
qr("https://mbc974.com/", "qr-site.svg")
qr("https://www.instagram.com/mbc974.re/", "qr-instagram.svg")
qr("https://mbc974.com/actualites/reportage-reunion-la-1ere-mbc-la-montagne/",
   "qr-reportage.svg")
qr("https://competitions.ffbb.com/ligues/reu/comites/0974/clubs/reu0974104", "qr-ffbb.svg")
qr("https://wa.me/262692556458", "qr-whatsapp.svg")
qr("https://mbc974.com/sponsor-club-basket-reunion/", "qr-sponsor.svg")
