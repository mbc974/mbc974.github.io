# -*- coding: utf-8 -*-
"""Produit les crans responsives des portraits du staff et des photos categories.

    python .claude/build-vignettes.py
    python .claude/build-vignettes.py --essai   montre le bilan, n'ecrit rien

POURQUOI CE SCRIPT EXISTE
-------------------------
Ces deux familles d'images etaient servies en UNE seule definition, la meme du
telephone au 4K, sans srcset ni sizes. Mesure dans le navigateur :

    portraits du staff   fichier 760x1140   affiche 184x277 (desktop, DPR 1)
                                            affiche 274x413 (375 px, DPR 2)
    photos categories    fichier 820x1230   affiche 548x196 (desktop, DPR 1)
                                            affiche 336x132 (375 px, DPR 2)

Un visiteur sur telephone telechargeait donc 760 px de large pour 548 utiles,
et un visiteur desktop 820 px pour 548 — dans les deux cas en portrait 2:3
alors que la carte categorie n'en montre qu'une bande. Les six portraits
pesaient 593 Ko d'AVIF, les six vignettes 495 Ko de WebP.

CE QU'IL NE FAIT PAS
--------------------
Il ne RECADRE rien. Le cadrage est un choix editorial (on voit le visage, on
voit le ballon) et il est fait par la CSS via object-fit/object-position, qui
peut differer d'un point de rupture a l'autre. Ce script se contente de fournir
la meme image a plusieurs tailles ; le navigateur choisit.

LA SOURCE
---------
Le .jpg de chaque image, qui est le fichier le moins compresse dont dispose le
depot. Reencoder depuis le .webp ou le .avif ajouterait une generation de
pertes a chaque passage — c'est le raisonnement deja pose dans build-hero.py.
"""
import io
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from PIL import Image
except ImportError:
    raise SystemExit("!! Pillow est requis : python -m pip install pillow")

# Memes reglages que build-hero.py : au-dela, on paye des octets que l'oeil ne
# voit pas ; en deca, les aplats du maillot se marbrent.
Q_AVIF, Q_WEBP = 45, 66

FAMILLES = [
    # dossier, prefixe, crans, pourquoi ces crans
    ("assets/staff", "staff-", [280, 380, 560],
     "184 px en desktop (368 en DPR 2), 274 px sous 680 px (548 en DPR 2)"),
    ("assets/categories", "cat-", [400, 560, 700],
     "548 px en desktop, 336 px sous 680 px (672 en DPR 2)"),
]


def sources(dossier, prefixe):
    d = os.path.join(RACINE, dossier)
    if not os.path.isdir(d):
        return []
    out = []
    for f in sorted(os.listdir(d)):
        base, ext = os.path.splitext(f)
        if ext.lower() != ".jpg" or not base.startswith(prefixe):
            continue
        # on ignore les crans deja produits (suffixe -<nombre>)
        if base.rsplit("-", 1)[-1].isdigit():
            continue
        out.append((base, os.path.join(d, f)))
    return out


def main():
    essai = "--essai" in sys.argv
    total_avant = total_apres = 0
    ecrits = 0
    for dossier, prefixe, crans, pourquoi in FAMILLES:
        print(u"\n  %s  (crans %s — %s)" % (dossier, ", ".join(map(str, crans)), pourquoi))
        for base, chemin in sources(dossier, prefixe):
            im = Image.open(chemin)
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            # le poids actuellement servi : l'AVIF s'il existe, sinon le WebP
            for ext in (".avif", ".webp"):
                p = os.path.join(RACINE, dossier, base + ext)
                if os.path.exists(p):
                    total_avant += os.path.getsize(p)
                    break
            ligne = []
            for w in crans:
                if w >= im.width:
                    continue        # on n'agrandit jamais
                h = round(im.height * w / im.width)
                petit = im.resize((w, h), Image.LANCZOS)
                for ext, fmt, q in ((".avif", "AVIF", Q_AVIF), (".webp", "WEBP", Q_WEBP)):
                    nom = "%s-%d%s" % (base, w, ext)
                    dest = os.path.join(RACINE, dossier, nom)
                    if not essai:
                        petit.save(dest, fmt, quality=q, **({"speed": 4} if fmt == "AVIF" else {}))
                        ecrits += 1
                    taille = os.path.getsize(dest) if os.path.exists(dest) else 0
                    if ext == ".avif":
                        ligne.append("%d:%.0f Ko" % (w, taille / 1024.0))
                        if w == crans[-1]:
                            total_apres += taille
            print(u"    %-22s %sx%s  ->  %s" % (base, im.width, im.height, "  ".join(ligne)))
    print(u"\n  %d fichier(s) ecrit(s)" % ecrits)
    print(u"  poids du plus grand cran AVIF, cumule : %.0f Ko (contre %.0f Ko servis avant)"
          % (total_apres / 1024.0, total_avant / 1024.0))
    if essai:
        print(u"  (essai : rien n'a ete ecrit)")
        return 0
    n = recabler_markup()
    print(u"  index.html : %d image(s) recablee(s) sur les crans" % n)
    return 0


# --------------------------------------------------------------------------
# Le recablage du markup
# --------------------------------------------------------------------------
# Les `sizes` ne sont pas des approximations : ce sont les largeurs relevees
# dans le navigateur (voir l'en-tete du fichier). Un `sizes` trop large fait
# telecharger un cran de trop, un `sizes` trop etroit fait etirer l'image —
# les deux erreurs coutent, dans des sens opposes.
SIZES_STAFF = "(max-width:680px) 74vw, 184px"
SIZES_CAT = "(max-width:680px) 90vw, (max-width:1240px) 45vw, 548px"


def crans_dispo(dossier, base, ext, crans):
    """Les crans REELLEMENT presents. staff-oswald n'existe qu'en 507 px de
    large : lui promettre un cran 560 ferait une requete 404 silencieuse."""
    out = []
    for w in crans:
        if os.path.exists(os.path.join(RACINE, dossier, "%s-%d%s" % (base, w, ext))):
            out.append("%s/%s-%d%s %dw" % (dossier, base, w, ext, w))
    return ", ".join(out)


def recabler_markup():
    import re
    P = os.path.join(RACINE, "index.html")
    s = io.open(P, encoding="utf-8").read()
    n = 0

    # --- staff : les <source> existent deja, on leur donne des crans ---------
    def rempl_staff(m):
        base, ext = m.group(1), m.group(2)
        srcset = crans_dispo("assets/staff", base, "." + ext, [280, 380, 560])
        if not srcset:
            return m.group(0)
        return ('<source srcset="%s" sizes="%s" type="image/%s">'
                % (srcset, SIZES_STAFF, ext))
    s, k = re.subn(r'<source srcset="assets/staff/(staff-[a-z]+)\.(avif|webp)" type="image/(?:avif|webp)">',
                   rempl_staff, s)
    n += k

    # --- categories : un <img> nu, qu'on enveloppe -------------------------
    def rempl_cat(m):
        img, base = m.group(0), m.group(1)
        a = crans_dispo("assets/categories", base, ".avif", [400, 560, 700])
        w = crans_dispo("assets/categories", base, ".webp", [400, 560, 700])
        if not a or not w:
            return img
        return ('<picture><source srcset="%s" sizes="%s" type="image/avif">'
                '<source srcset="%s" sizes="%s" type="image/webp">%s</picture>'
                % (a, SIZES_CAT, w, SIZES_CAT, img))
    s, k = re.subn(r'<img src="assets/categories/(cat-[a-z0-9]+)\.webp"(?:(?!</picture>).)*?>',
                   rempl_cat, s, flags=re.S)
    n += k

    io.open(P, "w", encoding="utf-8", newline="\n").write(s)
    return n


if __name__ == "__main__":
    sys.exit(main())
