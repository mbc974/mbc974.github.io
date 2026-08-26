# -*- coding: utf-8 -*-
"""Integre les deux photos MBC : « L'essentiel » et la transmission.

À FAIRE AVANT DE LANCER — deposer le ou les cliches dans Telechargements,
avec exactement ces noms (jpg, jpeg, png ou webp) :

    essentiel-duo.jpg      les deux joueurs de dos, maillots GLAIN 2 et
                           ALEX 1, ballon sous le bras, face au tableau
                           « NOTRE PLAN DE MATCH ».
    transmission.jpg       l'encadrant accroupi (maillot LUIZI 24) aupres
                           d'un jeune joueur qui tient un ballon.

Puis, depuis la racine du depot :
    python .claude/set-photos-mbc.py            les deux photos
    python .claude/set-photos-mbc.py duo        seulement « L'essentiel »
    python .claude/set-photos-mbc.py --essai    n'ecrit rien, controle seul

Deux recadrages, deux raisons.

En hauteur, on coupe au bassin pour que le jean du joueur de gauche ne
devienne pas un sujet : on garde une bande partant du haut du cliche et
s'arretant avant les jambes — voir HAUT et BAS, en fraction de la hauteur.

En largeur, on entame le bord gauche : s'y trouvent la banderole, du
mobilier de bord de terrain et une silhouette de dos. Les couper est un
cadrage, pas une retouche — l'image ne dit rien qu'elle ne montre.

Il n'y a volontairement AUCUN flou d'arriere-plan. L'ancien cliche en
demandait un, car des spectateurs y etaient reconnaissables. Sur celui-ci
le fond est le sujet : le tableau tactique, ses quatre consignes jusqu'au
« ANSANM NOU LE PLI FOR » et l'ecusson du club. Le flouter reviendrait a
effacer ce qui justifie la photo. Le fondu vers le texte est fait en CSS
(masque degrade de .ess__photo), pas dans le fichier.
"""
import io
import os
import sys

from PIL import Image

SRC = 'C:/Users/ALEX/Downloads/'
DEST = 'assets/images/'
EXTS = ('.jpg', '.jpeg', '.png', '.webp')

# fractions conservees pour le duo : (gauche, haut, bas).
# gauche ecarte la banderole et le bord de terrain ; haut/bas cadrent du
# haut du cliche jusqu'au bassin, jambes exclues.
D_GAUCHE, D_HAUT, D_BAS = 0.092, 0.03, 0.53
# la transmission garde sa verticalite, on retire seulement un peu de ciel
T_GAUCHE, T_HAUT, T_BAS = 0.0, 0.10, 1.00

LARGEURS = (1400, 1000, 640)


def trouver(base):
    # on accepte le nom avec ou sans tiret : essentiel-duo / essentielduo
    for nom in (base, base.replace('-', '')):
        for e in EXTS:
            p = SRC + nom + e
            if os.path.exists(p):
                return p
    return None


def sortir(im, nom, essai, qualite):
    """Ecrit les largeurs utiles en webp, plus un jpg de repli."""
    tailles = []
    # la plus grande largeur retenue ne depasse jamais la source : sans ce
    # garde-fou, une source de 1200 px ne produisait aucun fichier principal.
    # Corollaire : une source etroite donne moins de crans que LARGEURS n'en
    # annonce, d'ou le srcset recopie en fin de course.
    dispo = sorted({min(l, im.width) for l in LARGEURS}, reverse=True)
    for larg in dispo:
        r = im.resize((larg, round(im.height * larg / im.width)), Image.LANCZOS)
        suff = '' if larg == dispo[0] else '-%d' % larg
        chemin = '%s%s%s.webp' % (DEST, nom, suff)
        if not essai:
            r.save(chemin, 'WEBP', quality=qualite, method=6)
        tailles.append((chemin, r.width, r.height))
    jpg = '%s%s.jpg' % (DEST, nom)
    if not essai:
        im.save(jpg, 'JPEG', quality=qualite + 2, optimize=True, progressive=True)
    return tailles


def preparer(chemin, gauche, haut, bas):
    im = Image.open(chemin).convert('RGB')
    x0 = int(im.width * gauche)
    y0, y1 = int(im.height * haut), int(im.height * bas)
    return im.crop((x0, y0, im.width, y1))


# Le nom de sortie porte la version : le service worker sert les images en
# stale-while-revalidate en supposant qu'elles sont « versionnees par leur
# nom » (sw.js). Remplacer le contenu d'un fichier sans le renommer ferait
# donc voir l'ancienne photo a tout visiteur deja venu. Nouvelle photo =
# nouveau nom, et l'ancien fichier est supprime du depot.
#
# La qualite webp est reglee par photo, pas en global. Sur le duo, un
# balayage 70/74/78/82 montre un ecart moyen de 0,4/255 sur le tableau
# tactique -- invisible a l'oeil, meme agrandi 3x -- pour 26 Ko de moins.
# Le fond y est net et feuillu, donc couteux : 74 rend le fichier au poids
# de l'ancienne version floutee. La transmission garde 82, faute d'avoir
# ete mesuree.
JOBS = [
    ('duo',          'essentiel-duo', 'mbc-duo-plan-de-match', D_GAUCHE, D_HAUT, D_BAS, 74),
    ('transmission', 'transmission',  'mbc-transmission',  T_GAUCHE, T_HAUT, T_BAS, 82),
]


def main():
    args = sys.argv[1:]
    essai = '--essai' in args
    choix = [a for a in args if not a.startswith('--')]
    if not os.path.exists('index.html'):
        print('!! lancer depuis la racine du depot')
        return 1
    if not essai:
        os.makedirs(DEST, exist_ok=True)

    jobs = [j for j in JOBS if not choix or j[0] in choix]
    inconnus = [c for c in choix if c not in [j[0] for j in JOBS]]
    if inconnus:
        print('!! job inconnu : %s (connus : %s)'
              % (', '.join(inconnus), ', '.join(j[0] for j in JOBS)))
        return 1

    manquants = []
    for _, base, nom, g, h, b, q in jobs:
        p = trouver(base)
        if not p:
            manquants.append(base)
            continue
        im = preparer(p, g, h, b)
        src = Image.open(p)
        print('  %-16s %dx%d  ->  cadre %dx%d (%.2f)'
              % (base, src.width, src.height, im.width, im.height,
                 im.width / float(im.height)))
        crans = sortir(im, nom, essai, q)
        for chemin, w, hh in crans:
            taille = (os.path.getsize(chemin) / 1024.) if os.path.exists(chemin) else 0
            print('      %-44s %4dx%-4d %5.0f Ko' % (chemin, w, hh, taille))
        # le srcset a recopier tel quel dans le HTML : c'est le seul point
        # ou fichiers et balisage peuvent diverger sans que rien ne casse
        # bruyamment (un cran absent = une 404 silencieuse).
        srcset = ', '.join('%s %dw' % (c, w) for c, w, _ in sorted(crans, key=lambda t: t[1]))
        print('      srcset -> %s' % srcset)
        print('      width="%d" height="%d"' % (crans[0][1], crans[0][2]))

    if manquants:
        print('\n!! absents de %s : %s' % (SRC, ', '.join(manquants)))
        print('   les photos actuelles sont conservees.')
        return 1
    if essai:
        print('\n  essai : aucun fichier ecrit')
    return 0


if __name__ == '__main__':
    sys.exit(main())
