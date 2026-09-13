# -*- coding: utf-8 -*-
u"""Un seul en-tête pour tout le site (V182, 13/09/2026).

    python .claude/set-entete.py            recopie l'en-tête sur les pages enfants
    python .claude/set-entete.py --check    sort en 1 si une page n'est pas à jour

POURQUOI
--------
L'accueil et adhesion.html portent la barre V176 : la marque « MBC 974 »,
« Je m'inscris » et le bouton Menu plein écran. Les 23 pages enfants gardaient
l'ancienne barre de liens .seo-top. On changeait donc d'en-tête en naviguant ;
Alexandre l'a relevé le 13/09/2026 sur /matchs/. MAINTENANCE.md § 22 laissait
l'alignement « à décider » : il est décidé, pour toutes les pages.

LA SOURCE
---------
adhesion.html, entre <!-- EN-TETE:DEBUT --> et <!-- EN-TETE:FIN -->. C'est la
seule page hors accueil qui portait déjà la barre V176. L'accueil garde sa
propre variante : sa marque remonte en haut de page (#top).

La fonction entete_enfant() de build-matchs.py tire de cette source le bloc
des pages enfants. Ce script et les générateurs (via gabarit()) s'en servent
tous les deux : une page ne peut pas recevoir un en-tête différent selon qui
l'a écrite.

CE QU'IL FAIT, PAGE PAR PAGE
----------------------------
- Il remplace l'ancienne <header class="seo-top"> au premier passage, puis le
  bloc entre les marqueurs EN-TETE aux passages suivants.
- Il s'assure que la page charge script.js, qui pilote le menu et la barre.
  Une seule balise ; bump-assets.py pose ensuite le ?v=.

Il vérifie aussi que le menu d'index.html dit la même chose que celui
d'adhesion.html, puisque les deux sont écrits à la main.

ORDRE
-----
Avant les générateurs, qui écrivent le même bloc, et avant bump-assets.py.
"""
import glob
import importlib.util
import io
import os
import re
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
DEB, FIN = u'<!-- EN-TETE:DEBUT', u'<!-- EN-TETE:FIN -->'


def module_bm():
    spec = importlib.util.spec_from_file_location('bm', os.path.join(ICI, 'build-matchs.py'))
    bm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bm)
    return bm


def pages():
    """Les pages enfants publiées : un et deux niveaux sous la racine. On ne
    touche qu'aux pages qui portent l'une des deux formes d'en-tête ; les
    autres (s'il y en avait) sont signalées, jamais modifiées."""
    fichiers = (sorted(glob.glob(os.path.join(RACINE, '*', 'index.html')))
                + sorted(glob.glob(os.path.join(RACINE, '*', '*', 'index.html'))))
    garde = []
    for f in fichiers:
        rel = os.path.relpath(f, RACINE).replace(os.sep, '/')
        if rel.split('/')[0] in ('node_modules', 'dist', 'worktrees'):
            continue
        garde.append((f, rel))
    return garde


def menu(s):
    """La liste des sept entrées, sans les marques de page courante."""
    m = re.search(r'<ul class="mn__liste">.*?</ul>', s, re.S)
    return re.sub(r'\s+', ' ', m.group(0).replace(' aria-current="page"', '')) if m else None


def main():
    check = '--check' in sys.argv
    os.chdir(RACINE)
    bm = module_bm()
    bloc = bm.entete_enfant()
    balise_js = bm.script_js_commun()
    a_jour, changees, sans_entete = 0, [], []
    for chemin, rel in pages():
        s = io.open(chemin, encoding='utf-8').read()
        if DEB in s and FIN in s:
            i, j = s.index(DEB), s.index(FIN) + len(FIN)
        elif '<header class="seo-top">' in s:
            i = s.index('<header class="seo-top">')
            j = s.index('</header>', i) + len('</header>')
        else:
            sans_entete.append(rel)
            continue
        neuf = s[:i] + bloc + s[j:]
        # Le menu ne s'ouvre qu'avec script.js : sans lui, le bouton ne ferait
        # rien, et la navigation de la page disparaîtrait avec l'ancienne barre.
        if not re.search(r'<script src="/?script\.js', neuf):
            k = neuf.rindex('</body>')
            neuf = neuf[:k] + balise_js + neuf[k:]
        if neuf == s:
            a_jour += 1
            continue
        changees.append(rel)
        if not check:
            io.open(chemin, 'w', encoding='utf-8', newline='').write(neuf)

    derive = False
    mi = menu(io.open('index.html', encoding='utf-8').read())
    ma = menu(io.open('adhesion.html', encoding='utf-8').read())
    if not (mi and ma) or mi != ma:
        derive = True
        print(u"  !! le menu d'index.html diffère de celui d'adhesion.html : les aligner à la main")

    print(u'  en-tête : %d page(s) %s, %d déjà à jour'
          % (len(changees), u'à mettre à jour' if check else u'mises à jour', a_jour))
    for r in changees:
        print(u'     ' + r)
    for r in sans_entete:
        print(u'  .. sans en-tête reconnu, laissée telle quelle : ' + r)
    if check and (changees or derive):
        return 1
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
