# -*- coding: utf-8 -*-
u"""Publie la photo du maillot porte, celle qui montre de VRAIS logos partenaires.

    python .claude/set-maillot-partenaires.py            ecrit les derives
    python .claude/set-maillot-partenaires.py --essai    montre le bilan, n'ecrit rien

A FAIRE AVANT DE LANCER — deposer le cliche dans Telechargements sous son nom
d'appareil : DSC04996.jpg (Sony ILCE-7M4, 4341 x 5633, pris le 11/09/2026 a
20 h 54, premiere journee de championnat au gymnase de La Montagne).

POURQUOI CE SCRIPT EXISTE
-------------------------
La page partenaires montrait un RENDU 3D du maillot (assets/maillots/
maillot-domicile.*), floque d'un « 23 » qui n'existe pas et vierge de tout
logo. Elle promettait donc a une entreprise un emplacement qu'elle ne lui
montrait pas. MAINTENANCE § 17.4 avait deja releve ces maquettes comme le
dernier reste de synthese du site, « a verifier un jour » : c'est ce jour.

La photo retenue montre le maillot 2026/2027 porte en match, avec trois
marques deja floquees — l'ecusson du club, Oxysom sur la poitrine, Les
Agitateurs du Midi en bas de maillot — plus le logo de l'equipementier. Pour
un prospect, c'est une preuve a la place d'une promesse : il voit
l'emplacement, sa taille et son voisinage.

LE RECADRAGE, ET SA RAISON
--------------------------
Le cliche d'origine est un plein pied. A 420 px de large — la largeur reelle
de la figure dans la colonne de texte — le mot « OXYSOM » y mesurerait 33 px :
illisible, donc sans valeur de preuve. Le buste le porte a 74 px.

Le cadrage part donc juste au-dessus de la tete et s'arrete sous la ceinture
du short : on garde le visage (c'est un joueur, pas un mannequin) et LA TOTALITE
du devant du maillot, jusqu'au bas ou signe le second partenaire. On entame les
deux bords pour ecarter le coequipier flou de gauche et le banc de droite.

⚠️ QUELQUES SILHOUETTES ASSISES RESTENT au second plan, aux deux bords : les
sortir demanderait de resserrer au point d'amputer le joueur. C'est licite — la
page confidentialite prevoit la diffusion des photos d'activite et le retrait
sur simple demande, et l'accueil publie deja la photo d'equipe entiere — mais
il ne faut pas ecrire le contraire ici : c'est l'ecart entre le commentaire et
l'image qui serait le defaut, pas les silhouettes.

Aucune retouche, aucun flou : ce que la photo montre, elle le montrait deja.

UNE QUATRIEME MARQUE, ILLISIBLE. Sur l'ourlet du maillot, a demi cachee par la
ceinture du short, on devine une marque (« …OOD / FRIENDS ») qui ne figure pas
parmi les partenaires publies sur l'accueil. C'est pourquoi la legende de la
page dit « deux DES emplacements » et jamais « deux partenaires y sont
floques » : on montre ce qu'on peut nommer, on ne compte pas ce qu'on ne lit
pas. Le logo CPA Paysage, lui, est sur l'ourlet du SHORT (y ~ 0,73 de
l'original) : il est hors cadre, donc il n'est ni nomme ni decrit.

CE QU'IL NE FAUT PAS FAIRE
--------------------------
Ecraser un fichier deja publie en gardant son nom. Le service worker sert les
images en stale-while-revalidate en les supposant versionnees par leur nom
(sw.js) : un visiteur deja venu reverrait l'ancienne. Nouvelle photo = nouveau
nom de fichier.
"""
import os
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    raise SystemExit("!! Pillow est requis : python -m pip install pillow")

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.expanduser("~"), "Downloads")
DEST = os.path.join(RACINE, "assets", "maillots")

SOURCE = "DSC04996.jpg"
NOM = "maillot-mbc-2026-2027-partenaires"

# Fractions conservees du cliche d'origine : (gauche, haut, droite, bas).
# haut  : juste au-dessus des cheveux ;
# bas   : sous la ceinture du short, le maillot entier est dedans ;
# bords : on coupe le coequipier flou a gauche et le banc a droite.
GAUCHE, HAUT, DROITE, BAS = 0.255, 0.145, 0.705, 0.585

# Memes crans et memes qualites que la galerie de match
# (.claude/build-galerie-match.py, CRANS_PORTRAIT et QUALITE) : la figure fait
# 420 px dans la colonne de texte sur ordinateur et au plus 335 px sur
# telephone, soit 670 px en DPR 2 — 760 les couvre, 1200 sert les ecrans
# denses et le zoom navigateur.
CRANS = (360, 560, 760, 1200)
QUALITE = {"avif": {"quality": 45}, "webp": {"quality": 66, "method": 6}}
QUALITE_JPEG = 80


def main():
    essai = "--essai" in sys.argv[1:]
    chemin = os.path.join(SRC, SOURCE)
    if not os.path.exists(chemin):
        raise SystemExit(u"!! introuvable : %s" % chemin)

    with Image.open(chemin) as im0:
        prise = im0.getexif().get_ifd(0x8769).get(36867)   # DateTimeOriginal
        im = ImageOps.exif_transpose(im0).convert("RGB")
    # Sans ce vidage, l'EXIF complet de l'original (GPS compris) partirait dans
    # chaque derive : convert() et resize() recopient info.
    im.info.clear()

    # Une photo sortie d'un appareil porte une date de prise de vue. Son absence
    # signalerait une image generee ou retouchee par une IA — MAINTENANCE § 17.4.
    if not prise:
        raise SystemExit(u"!! %s : aucune date de prise de vue" % SOURCE)
    print(u"   prise de vue : %s" % prise)

    x0, x1 = int(im.width * GAUCHE), int(im.width * DROITE)
    y0, y1 = int(im.height * HAUT), int(im.height * BAS)
    im = im.crop((x0, y0, x1, y1))
    print(u"   cadre retenu : %d x %d" % im.size)

    base = os.path.join(DEST, NOM)
    faits = []
    for w in [c for c in CRANS if c <= im.width]:
        reduite = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        for ext in ("avif", "webp"):
            cible = "%s-%d.%s" % (base, w, ext)
            faits.append(cible)
            if not essai:
                reduite.save(cible, ext.upper(), **QUALITE[ext])
    w = max(c for c in CRANS if c <= im.width)
    jpg = base + ".jpg"
    faits.append(jpg)
    if not essai:
        im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(
            jpg, "JPEG", quality=QUALITE_JPEG, optimize=True, progressive=True)

    for f in faits:
        poids = (u"%6.1f Ko" % (os.path.getsize(f) / 1024.0)) if os.path.exists(f) else u"     — "
        print(u"   %s  %s" % (poids, os.path.relpath(f, RACINE).replace("\\", "/")))
    print(u"%s%d fichiers" % (u"[essai] " if essai else u"", len(faits)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
