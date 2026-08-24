# -*- coding: utf-8 -*-
"""Intègre les logos des clubs adverses dans le calendrier des matchs.

À FAIRE AVANT DE LANCER — enregistrer les logos dans le dossier
Téléchargements, avec exactement ces noms (png, jpg ou webp) :

    bc2s.png     Basket Club Sainte-Suzanne  (Les Papangues)
    bcd3.png     Basket Club Dionysien       (volcan)
    sbbc.png     Saint-Benoît Basket Club    (ballon bleu clair)
    mtg.png      Association MTG Basketball  (tigre)
    bjssr.png    JS Sainte-Rosienne          (une seule des deux variantes)
    smb2.png     Sainte-Marie Basket         (silhouettes)
    picks3.png   Picks La Possession         (dodo)

Puis, depuis la racine du dépôt :
    python .claude/add-club-logos.py

Le script recadre en carré, redimensionne en 96 et 192 px, écrit dans
assets/logos/clubs/ et remplace les sigles par les logos dans index.html.
Un club dont le fichier manque garde simplement son sigle.
"""
import io
import os
import re
import sys

from PIL import Image, ImageOps

SRC = 'C:/Users/ALEX/Downloads/'
DEST = 'assets/logos/clubs/'
EXTS = ('.png', '.jpg', '.jpeg', '.webp')

CLUBS = {
    'bc2s':   'Basket Club Sainte-Suzanne',
    'bcd3':   'Basket Club Dionysien 3',
    'sbbc':   'Saint-Benoît Basket Club',
    'mtg':    'Association MTG Basketball',
    'bjssr':  'BC Jeunesse Sportive Sainte-Rosienne',
    'smb2':   'Sainte-Marie Basket 2',
    'picks3': 'Picks Basket La Possession 3',
}


def trouver(slug):
    for e in EXTS:
        p = SRC + slug + e
        if os.path.exists(p):
            return p
    return None


def preparer(slug, chemin):
    im = ImageOps.exif_transpose(Image.open(chemin))
    im = im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') else im.convert('RGB')
    # carré centré : les logos arrivent en formats très variés
    c = max(im.size)
    fond = Image.new(im.mode, (c, c), (255, 255, 255, 0) if im.mode == 'RGBA' else (255, 255, 255))
    fond.paste(im, ((c - im.width) // 2, (c - im.height) // 2))
    os.makedirs(DEST, exist_ok=True)
    for taille in (192, 96):
        r = fond.resize((taille, taille), Image.LANCZOS)
        nom = '%s%s%s.webp' % (DEST, slug, '' if taille == 192 else '-96')
        r.save(nom, 'WEBP', quality=88, method=6)
    return os.path.getsize('%s%s.webp' % (DEST, slug)) // 1024


def main():
    if not os.path.exists('index.html'):
        print('!! lancer depuis la racine du depot')
        return 1

    faits, manquants = {}, []
    for slug, nom in CLUBS.items():
        p = trouver(slug)
        if not p:
            manquants.append(slug)
            continue
        ko = preparer(slug, p)
        faits[slug] = nom
        print('  %-7s %-38s %3d Ko' % (slug, os.path.basename(p), ko))

    if manquants:
        print('\n  fichiers absents (le sigle est conserve) : %s' % ', '.join(manquants))
    if not faits:
        print('\n!! aucun logo trouve dans %s' % SRC)
        return 1

    s = io.open('index.html', encoding='utf-8').read()
    n = 0
    for slug, nom in faits.items():
        sigle = slug.upper()
        ancien = '<span class="mx-crest mx-crest--sigle" aria-hidden="true">%s</span>' % sigle
        nouveau = ('<span class="mx-crest mx-crest--logo">'
                   '<img src="assets/logos/clubs/{s}.webp" alt="" width="192" height="192" '
                   'loading="lazy" decoding="async" '
                   'onerror="this.closest(\'.mx-crest\').className=\'mx-crest mx-crest--sigle\';'
                   'this.closest(\'.mx-crest\').textContent=\'{S}\'"></span>').format(s=slug, S=sigle)
        if ancien in s:
            s = s.replace(ancien, nouveau)
            n += 1
    io.open('index.html', 'w', encoding='utf-8', newline='\n').write(s)
    print('\n  %d ecussons remplaces par un logo' % n)
    os.system(sys.executable + ' .claude/bump-assets.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
