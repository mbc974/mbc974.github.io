# -*- coding: utf-8 -*-
u"""Planche de comparaison des compositions du credit du pied de page.

    python .claude/planche-signature.py <dossier-des-candidats> <etiquette> [largeur]

Le dossier contient, pour chaque candidat, un couple <nom>.html / <nom>.css.
Le script rend chacun par .claude/banc-signature.mjs (qui les injecte dans la
page reelle sans rien ecrire dans le depot), puis empile les captures en une
seule image legendee.

POURQUOI
--------
Une composition ne se juge pas sur du code ni sur une description : elle se
juge a l'oeil, cote a cote, au meme endroit et a la meme largeur. Alexandre a
rejete deux versions successives decrites en mots ; une planche lui fait
choisir sur piece en une seconde.

La legende porte la HAUTEUR MESUREE de chaque bloc, parce que c'est la
grandeur qui a fait rater les deux premieres tentatives : trop haut le 15/09,
trop fade le 16/09 faute d'assez de presence. On la lit, on ne l'estime pas.
"""
import glob
import io
import json
import os
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
SORTIE = os.environ.get('MBC_BANC_SORTIE') or os.path.join(
    os.environ.get('TEMP', '/tmp'), 'mbc-banc-signature')


def rendre(nom, html, css, largeur):
    """Un candidat -> sa capture et ses mesures, par le banc."""
    cmd = ['node', os.path.join(ICI, 'banc-signature.mjs'), 'planche-' + nom,
           largeur, '--shots', '--html=' + html, '--css=' + css]
    env = dict(os.environ, MSYS_NO_PATHCONV='1')
    r = subprocess.run(cmd, cwd=RACINE, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', env=env)
    if r.returncode != 0:
        print(u'  !! %s : %s' % (nom, (r.stdout + r.stderr).strip()[:300]))
        return None
    png = os.path.join(SORTIE, 'planche-%s-%s.png' % (nom, largeur))
    fic = os.path.join(SORTIE, 'planche-%s.json' % nom)
    if not os.path.exists(png):
        print(u'  !! %s : capture absente' % nom)
        return None
    haut = None
    try:
        haut = json.load(io.open(fic, encoding='utf-8'))[largeur]['hauteurBloc']
    except Exception:
        pass
    print(u'  %-22s %s px de haut' % (nom, haut))
    return {'nom': nom, 'png': png, 'haut': haut}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    dossier, tag = sys.argv[1], sys.argv[2]
    largeur = sys.argv[3] if len(sys.argv) > 3 else '1440x900'
    from PIL import Image, ImageDraw

    cands = []
    for h in sorted(glob.glob(os.path.join(dossier, '*.html'))):
        nom = os.path.splitext(os.path.basename(h))[0]
        c = os.path.join(dossier, nom + '.css')
        if not os.path.exists(c):
            print(u'  .. %s : pas de .css en face, ignore' % nom)
            continue
        r = rendre(nom, h, c, largeur)
        if r:
            cands.append(r)
    if not cands:
        print(u'aucun candidat rendu')
        return 1

    ims = [(c, Image.open(c['png']).convert('RGB')) for c in cands]
    L = max(im.width for _, im in ims)
    BAN = 40
    H = sum(im.height + BAN for _, im in ims)
    out = Image.new('RGB', (L, H), (7, 13, 24))
    d = ImageDraw.Draw(out)
    y = 0
    for i, (c, im) in enumerate(ims):
        d.rectangle([0, y, L, y + BAN], fill=(13, 20, 33))
        d.text((20, y + 13), u'%s  —  %s  (%s px de haut)'
               % (chr(65 + i), c['nom'].upper(), c['haut']), fill=(232, 130, 42))
        y += BAN
        out.paste(im, ((L - im.width) // 2, y))
        y += im.height
        d.line([(0, y - 1), (L, y - 1)], fill=(29, 37, 48))
    f = os.path.join(SORTIE, 'planche-%s-%s.png' % (tag, largeur))
    out.save(f)
    print(u'-> %s  (%d candidats, %dx%d)' % (f, len(ims), out.width, out.height))
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
