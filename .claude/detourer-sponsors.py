# -*- coding: utf-8 -*-
"""Retire le fond blanc INTEGRE de certains logos partenaires.

    python .claude/detourer-sponsors.py --essai
    python .claude/detourer-sponsors.py

LE CONSTAT
----------
Mesure du contenu de chaque fichier, part de pixels opaques quasi blancs :

    oxysom           87 %   <- une plaque blanche, logo au milieu
    saint-francois   80 %   <- idem
    agitateurs-midi         <- un carre blanc arrondi autour du disque
    resto-chen              <- fond rouge : c'est le logo lui-meme
    cpa-paysage       5 %   <- scan de carte de visite, fond propre au visuel

Les coins sont transparents, ce qui trompe un controle rapide : c'est
l'INTERIEUR qui porte le blanc. Rendu sur une carte claire, on voit donc un
carre blanc dans un carre blanc — l'effet « capture d'ecran collee ».

LA METHODE, ET POURQUOI PAS UN SIMPLE « BLANC -> TRANSPARENT »
---------------------------------------------------------------
Rendre transparent TOUT pixel blanc treuerait les blancs INTERIEURS du logo :
le contre-forme des lettres, un reflet, une zone claire du dessin. On procede
donc par REMPLISSAGE DEPUIS LES BORDS : seul le blanc qui communique avec
l'exterieur disparait. Un blanc enferme dans le logo est conserve.

Le seuil est volontairement serre (232) et la tolerance faible : mieux vaut
laisser un liseré blanc qu'entamer un contour. Le script REFUSE d'ecrire si
l'operation retire plus de 92 % des pixels opaques — signe qu'elle a mordu
dans le logo.
"""
import io
import os
import sys
from collections import deque

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER = os.path.join(RACINE, 'assets', 'sponsors')
SEUIL = 232          # au-dela, on considere le pixel « blanc de fond »
CIBLES = ('sponsor-oxysom', 'sponsor-saint-francois', 'sponsor-agitateurs-midi')


def blanc(p):
    r, g, b, a = p
    return a > 24 and r >= SEUIL and g >= SEUIL and b >= SEUIL


def detourer(im):
    """Remplissage depuis les quatre bords. Rend (image, part retiree)."""
    from PIL import Image
    im = im.convert('RGBA')
    W, H = im.size
    px = im.load()
    vus = bytearray(W * H)
    f = deque()
    for x in range(W):
        f.append((x, 0)); f.append((x, H - 1))
    for y in range(H):
        f.append((0, y)); f.append((W - 1, y))
    retires = 0
    while f:
        x, y = f.popleft()
        if x < 0 or y < 0 or x >= W or y >= H:
            continue
        i = y * W + x
        if vus[i]:
            continue
        vus[i] = 1
        p = px[x, y]
        if p[3] == 0:                      # deja transparent : on traverse
            f.extend(((x+1, y), (x-1, y), (x, y+1), (x, y-1)))
            continue
        if not blanc(p):
            continue
        px[x, y] = (p[0], p[1], p[2], 0)
        retires += 1
        f.extend(((x+1, y), (x-1, y), (x, y+1), (x, y-1)))
    return im, retires


def main():
    from PIL import Image
    essai = '--essai' in sys.argv
    for base in CIBLES:
        src = os.path.join(DOSSIER, base + '.png')
        if not os.path.exists(src):
            print(u"  %-24s introuvable" % base); continue
        im0 = Image.open(src).convert('RGBA')
        px0 = im0.load()
        op0 = sum(1 for y in range(0, im0.height, 2) for x in range(0, im0.width, 2)
                  if px0[x, y][3] > 200)
        im, retires = detourer(im0.copy())
        px = im.load()
        op1 = sum(1 for y in range(0, im.height, 2) for x in range(0, im.width, 2)
                  if px[x, y][3] > 200)
        part = 100.0 * (op0 - op1) / max(1, op0)
        etat = u"OK" if part <= 92 else u"REFUSE (mord dans le logo)"
        print(u"  %-24s opaques %5d -> %5d  (-%.0f %%)  %s"
              % (base.replace('sponsor-', ''), op0, op1, part, etat))
        if essai or part > 92:
            continue
        im.save(src)
        im.save(os.path.join(DOSSIER, base + '.webp'), 'WEBP', quality=90, method=6, lossless=False)
    if essai:
        print(u"\n  (essai : rien n'a ete ecrit)")
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
