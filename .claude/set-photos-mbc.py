# -*- coding: utf-8 -*-
"""Integre les deux photos MBC : « L'essentiel » et la transmission.

À FAIRE AVANT DE LANCER — deposer les deux cliches dans Telechargements,
avec exactement ces noms (jpg, jpeg, png ou webp) :

    essentiel-duo.jpg      les deux joueurs de dos, maillots CLAIN 2 et
                           ALEX 1, ballon sous le bras, sur le plateau.
    transmission.jpg       l'encadrant accroupi (maillot LUIZI 24) aupres
                           d'un jeune joueur qui tient un ballon.

Puis, depuis la racine du depot :
    python .claude/set-photos-mbc.py
    python .claude/set-photos-mbc.py --essai   (n'ecrit rien, controle seul)

Le cadrage de la premiere est le point delicat. La consigne est de couper
au bassin pour que le jean du joueur de gauche ne devienne pas un sujet :
on garde donc une bande partant du haut du cliche et s'arretant avant les
jambes — voir HAUT et BAS ci-dessous, exprimes en fraction de la hauteur.
"""
import io
import os
import sys

from PIL import Image

SRC = 'C:/Users/ALEX/Downloads/'
DEST = 'assets/images/'
EXTS = ('.jpg', '.jpeg', '.png', '.webp')

# fractions de la hauteur d'origine conservees pour le duo :
# du haut du cliche jusqu'au bassin, jambes exclues.
HAUT, BAS = 0.04, 0.62
# la transmission garde sa verticalite, on retire seulement un peu de ciel
T_HAUT, T_BAS = 0.10, 1.00

LARGEURS = (1400, 1000, 640)


def trouver(base):
    # on accepte le nom avec ou sans tiret : essentiel-duo / essentielduo
    for nom in (base, base.replace('-', '')):
        for e in EXTS:
            p = SRC + nom + e
            if os.path.exists(p):
                return p
    return None


def sortir(im, nom, essai):
    """Ecrit les trois largeurs en webp, plus un jpg de repli."""
    tailles = []
    # la plus grande largeur retenue ne depasse jamais la source : sans ce
    # garde-fou, une source de 1200 px ne produisait aucun fichier principal.
    dispo = sorted({min(l, im.width) for l in LARGEURS}, reverse=True)
    for larg in dispo:
        r = im.resize((larg, round(im.height * larg / im.width)), Image.LANCZOS)
        suff = '' if larg == dispo[0] else '-%d' % larg
        chemin = '%s%s%s.webp' % (DEST, nom, suff)
        if not essai:
            r.save(chemin, 'WEBP', quality=82, method=6)
        tailles.append((chemin, r.width, r.height))
    jpg = '%s%s.jpg' % (DEST, nom)
    if not essai:
        im.save(jpg, 'JPEG', quality=84, optimize=True, progressive=True)
    return tailles


def preparer(chemin, haut, bas):
    im = Image.open(chemin)
    im = im.convert('RGB')
    y0, y1 = int(im.height * haut), int(im.height * bas)
    im = im.crop((0, y0, im.width, y1))
    return im


def main():
    essai = '--essai' in sys.argv
    if not os.path.exists('index.html'):
        print('!! lancer depuis la racine du depot')
        return 1
    if not essai:
        os.makedirs(DEST, exist_ok=True)

    jobs = [('essentiel-duo', 'mbc-duo-terrain', HAUT, BAS),
            ('transmission', 'mbc-transmission', T_HAUT, T_BAS)]
    manquants = []
    for base, nom, h, b in jobs:
        p = trouver(base)
        if not p:
            manquants.append(base)
            continue
        im = preparer(p, h, b)
        src = Image.open(p)
        print('  %-16s %dx%d  ->  cadre %dx%d (%.2f)'
              % (base, src.width, src.height, im.width, im.height,
                 im.width / float(im.height)))
        for chemin, w, hh in sortir(im, nom, essai):
            taille = (os.path.getsize(chemin) / 1024.) if os.path.exists(chemin) else 0
            print('      %-44s %4dx%-4d %5.0f Ko' % (chemin, w, hh, taille))

    if manquants:
        print('\n!! absents de %s : %s' % (SRC, ', '.join(manquants)))
        print('   les photos actuelles sont conservees.')
        return 1
    if essai:
        print('\n  essai : aucun fichier ecrit')
    return 0


if __name__ == '__main__':
    sys.exit(main())
