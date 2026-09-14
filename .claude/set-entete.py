# -*- coding: utf-8 -*-
u"""Un seul en-tête et un seul pied de page pour tout le site
(V182, 13/09/2026 ; V184, 14/09/2026).

    python .claude/set-entete.py            recopie l'en-tête et le pied sur les pages enfants
    python .claude/set-entete.py --check    sort en 1 si une page n'est pas à jour

POURQUOI
--------
L'accueil et adhesion.html portent la barre V176 : la marque « MBC 974 »,
« Je m'inscris » et le bouton Menu plein écran. Les 23 pages enfants gardaient
l'ancienne barre de liens .seo-top. On changeait donc d'en-tête en naviguant ;
Alexandre l'a relevé le 13/09/2026 sur /matchs/. MAINTENANCE.md § 22 laissait
l'alignement « à décider » : il est décidé, pour toutes les pages.

Le pied de page avait le même écart : le grand pied .site-footer sur l'accueil
(le club, les liens utiles, le contact, l'affiliation FFBB), une seule ligne de
liens .seo-foot ailleurs. Il est aligné le 14/09/2026 (V184) sur les pages
enfants, puis, à la demande d'Alexandre, sur adhesion.html. Sur cette page, seul
le pied est remplacé : son en-tête est la source de celui des pages enfants.

LES SOURCES
-----------
- L'en-tête : adhesion.html, entre <!-- EN-TETE:DEBUT --> et
  <!-- EN-TETE:FIN -->. C'est la seule page hors accueil qui portait déjà la
  barre V176. L'accueil garde sa propre variante : sa marque remonte en haut
  de page (#top).
- Le pied : index.html, entre <!-- PIED:DEBUT --> et <!-- PIED:FIN -->. Les
  mentions légales détaillées (#legal) restent sur l'accueil seulement, et les
  liens relatifs de l'accueil deviennent absolus.

Les fonctions entete_enfant() et pied_enfant() de build-matchs.py tirent de
ces sources les blocs des pages enfants. Ce script et les générateurs (via
gabarit()) s'en servent tous les deux : une page ne peut pas recevoir un
en-tête ou un pied différent selon qui l'a écrite.

CE QU'IL FAIT, PAGE PAR PAGE
----------------------------
- Il remplace l'ancienne <header class="seo-top"> au premier passage, puis le
  bloc entre les marqueurs EN-TETE aux passages suivants. Même chose pour le
  pied : <footer class="seo-foot">, puis le bloc entre les marqueurs PIED.
- Il s'assure que la page charge script.js, qui pilote le menu, la barre du
  haut et la barre CTA mobile. Une seule balise ; bump-assets.py pose ensuite
  le ?v=.
- Il retire le module en ligne « Barre CTA mobile ». Ce module attendait
  .seo-foot, qui n'existe plus ; script.js fait la même chose avec .site-footer.

Il vérifie aussi que le menu d'index.html dit la même chose que celui
d'adhesion.html, puisque les deux sont écrits à la main.

ORDRE
-----
Avant les générateurs, qui écrivent les mêmes blocs, et avant bump-assets.py.
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
PDEB, PFIN = u'<!-- PIED:DEBUT', u'<!-- PIED:FIN -->'
# Le module en ligne des pages enfants, toujours ouvert par ce commentaire.
CTA_EN_LIGNE = re.compile(r'<script>\s*/\* Barre CTA mobile[\s\S]*?</script>\s*')


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


def bornes(s, debut, fin, ancien, balise_fin):
    """Où poser le bloc : entre les marqueurs s'ils sont là, sinon à la place
    de l'ancienne balise (premier passage), sinon nulle part (None)."""
    if debut in s and fin in s:
        return s.index(debut), s.index(fin) + len(fin)
    if ancien in s:
        i = s.index(ancien)
        return i, s.index(balise_fin, i) + len(balise_fin)
    return None


def menu(s):
    """La liste des sept entrées, sans les marques de page courante."""
    m = re.search(r'<ul class="mn__liste">.*?</ul>', s, re.S)
    return re.sub(r'\s+', ' ', m.group(0).replace(' aria-current="page"', '')) if m else None


def main():
    check = '--check' in sys.argv
    os.chdir(RACINE)
    bm = module_bm()
    entete, pied = bm.entete_enfant(), bm.pied_enfant()
    balise_js = bm.script_js_commun()
    a_jour, changees, sans_entete, sans_pied = 0, [], [], []
    for chemin, rel in pages():
        s = io.open(chemin, encoding='utf-8').read()
        b = bornes(s, DEB, FIN, '<header class="seo-top">', '</header>')
        if b is None:
            sans_entete.append(rel)
            continue
        neuf = s[:b[0]] + entete + s[b[1]:]
        b = bornes(neuf, PDEB, PFIN, '<footer class="seo-foot">', '</footer>')
        if b is None:
            sans_pied.append(rel)
        else:
            neuf = neuf[:b[0]] + pied + neuf[b[1]:]
        # La barre CTA mobile est désormais pilotée par script.js seul.
        neuf = CTA_EN_LIGNE.sub('', neuf)
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

    # adhesion.html (14/09/2026) : le pied commun, lui aussi. Son en-tête n'est
    # pas touché : c'est la SOURCE de celui des pages enfants (marqueurs
    # EN-TETE), et il reste fixe, comme celui de l'accueil.
    s = io.open('adhesion.html', encoding='utf-8').read()
    b = bornes(s, PDEB, PFIN, '<footer class="site-footer">', '</footer>')
    if b is None:
        sans_pied.append('adhesion.html')
    else:
        neuf = s[:b[0]] + pied + s[b[1]:]
        if neuf == s:
            a_jour += 1
        else:
            changees.append('adhesion.html')
            if not check:
                io.open('adhesion.html', 'w', encoding='utf-8', newline='').write(neuf)

    derive = False
    mi = menu(io.open('index.html', encoding='utf-8').read())
    ma = menu(io.open('adhesion.html', encoding='utf-8').read())
    if not (mi and ma) or mi != ma:
        derive = True
        print(u"  !! le menu d'index.html diffère de celui d'adhesion.html : les aligner à la main")

    print(u'  en-tête et pied de page : %d page(s) %s, %d déjà à jour'
          % (len(changees), u'à mettre à jour' if check else u'mises à jour', a_jour))
    for r in changees:
        print(u'     ' + r)
    for r in sans_entete:
        print(u'  .. sans en-tête reconnu, laissée telle quelle : ' + r)
    for r in sans_pied:
        print(u'  .. sans pied de page reconnu, pied laissé tel quel : ' + r)
    if check and (changees or derive):
        return 1
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
