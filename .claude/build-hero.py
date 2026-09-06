# -*- coding: utf-8 -*-
"""Regenere TOUTES les variantes de l'image du hero a partir de son original.

    python .claude/build-hero.py            ecrit les fichiers
    python .claude/build-hero.py --essai    affiche le bilan, n'ecrit rien

Pourquoi ce script existe
-------------------------
Les variantes livrees en septembre 2026 avaient ete produites une par une, sans
reglage commun. Resultat : le fichier que TELECHARGE un telephone (le recadrage
mobile 1102) pesait 163 Ko alors qu'un encodage propre du meme original donne
97 Ko **et** reste plus fidele — mesure a l'appui (ecart moyen a l'original :
4,87 avant, 3,68 apres). Autrement dit on payait 66 Ko pour une image moins
bonne. Ce fichier fige les reglages pour que cela ne se reproduise pas.

Deux cadrages, pas un
---------------------
L'original est un panoramique 4080x1630 (2,5:1). Dans un cadre de telephone, un
2,5:1 ne peut pas tenir : ou il devient une bande de 150 px de haut, ou
`object-fit: cover` en coupe les quatre cinquiemes. On sort donc une SECONDE
serie, recadree sur la fenetre x=1387..2489 — le coach et le cercle d'enfants,
c'est-a-dire le sujet. La bascule se fait a 640 px, dans le <picture> ET dans
la feuille de style : les deux valeurs doivent rester egales.

Qualites
--------
AVIF 45 / WebP 66 : au-dessus, on paye des octets que l'oeil ne voit pas ; en
dessous (q=34 par exemple) la moyenne des ecarts reste bonne mais les aplats du
parquet commencent a se marbrer. Le JPEG n'est qu'un repli pour les navigateurs
sans WebP : un seul cran, en 1672.
"""
import io
import os
import sys

from PIL import Image

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(RACINE, '.claude', 'sources',
                        'hero-regroupement-4080x1630.jpg')
SORTIE = os.path.join(RACINE, 'assets', 'images')
BASE = 'mbc-hero-regroupement'

# La fenetre du recadrage mobile dans l'original, en pixels.
FENETRE_MOBILE = (1387, 0, 2489, 1630)

LARGEURS_DESKTOP = (1280, 1672, 2048, 2400, 2800)
LARGEURS_MOBILE = (440, 700, 1102)
REPLI_JPEG = 1672

Q_AVIF = 45
Q_WEBP = 66
Q_JPEG = 82


def hauteur(src, larg):
    """Hauteur qui preserve exactement le rapport de la source."""
    return int(round(larg * src.size[1] / float(src.size[0])))


def ecrire(im, chemin, format, essai, **opts):
    tampon = io.BytesIO()
    im.save(tampon, format, **opts)
    octets = tampon.getvalue()
    avant = os.path.getsize(chemin) if os.path.exists(chemin) else 0
    if not essai:
        with open(chemin, 'wb') as f:
            f.write(octets)
    ecart = (' (%s%.0f %%)' % ('-' if avant > len(octets) else '+',
                               abs(100. * (avant - len(octets)) / avant))) if avant else ' (nouveau)'
    print('   %-46s %7.1f Ko%s' % (os.path.basename(chemin), len(octets) / 1024., ecart))
    return len(octets), avant


def serie(src, largeurs, suffixe, essai):
    total, total_avant = 0, 0
    for larg in largeurs:
        im = src.resize((larg, hauteur(src, larg)), Image.LANCZOS)
        nom = '%s%s%d' % (BASE, suffixe, larg)
        n, a = ecrire(im, os.path.join(SORTIE, nom + '.avif'), 'AVIF', essai,
                      quality=Q_AVIF, speed=4)
        total += n
        total_avant += a
        n, a = ecrire(im, os.path.join(SORTIE, nom + '.webp'), 'WEBP', essai,
                      quality=Q_WEBP, method=6)
        total += n
        total_avant += a
    return total, total_avant


def main():
    essai = '--essai' in sys.argv
    if not os.path.exists(ORIGINAL):
        print('!! original introuvable : %s' % ORIGINAL)
        print('   (c\'est le panoramique 4080x1630 fourni par le club)')
        return 1

    o = Image.open(ORIGINAL).convert('RGB')
    print('original : %s  %.1f Mo' % (o.size, os.path.getsize(ORIGINAL) / 1048576.))
    if o.size != (4080, 1630):
        print('!! l\'original n\'a pas les dimensions attendues (4080x1630) :')
        print('   les largeurs et la fenetre mobile ci-dessus ont ete calculees')
        print('   pour CE fichier. Verifiez avant de continuer.')
        return 1

    print('\npanoramique (>= 641 px)')
    t1, a1 = serie(o, LARGEURS_DESKTOP, '-', essai)

    print('\nrecadrage mobile (<= 640 px), fenetre x=%d..%d' % (FENETRE_MOBILE[0], FENETRE_MOBILE[2]))
    m = o.crop(FENETRE_MOBILE)
    t2, a2 = serie(m, LARGEURS_MOBILE, '-m-', essai)

    print('\nrepli JPEG')
    j = o.resize((REPLI_JPEG, hauteur(o, REPLI_JPEG)), Image.LANCZOS)
    t3, a3 = ecrire(j, os.path.join(SORTIE, BASE + '.jpg'), 'JPEG', essai,
                    quality=Q_JPEG, optimize=True, progressive=True)

    tot, av = t1 + t2 + t3, a1 + a2 + a3
    print('\ntotal : %.0f Ko -> %.0f Ko  (%s%.0f %%)'
          % (av / 1024., tot / 1024., '-' if av > tot else '+',
             abs(100. * (av - tot) / av) if av else 0))
    if essai:
        print('\nessai : aucun fichier ecrit')
    else:
        print('\nne pas oublier : python .claude/bump-assets.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
