# -*- coding: utf-8 -*-
"""Compare deux empreintes du site (.claude/empreinte-site.mjs), retire le
bruit mesuré par une passe témoin à code identique, et dit QUELLES
propriétés ont bougé (V185, 14/09/2026).

    python .claude/comparer-empreintes.py "%TEMP%/mbc-banc-purge" apres avant controle

- Un écart (page, largeur, élément) présent aussi entre « controle » et
  « avant » est du bruit : compté à part, jamais comme une régression.
- Les écarts ATTENDUS sont annoncés AVANT la mesure, jamais après coup. Un
  écart n'est admis que s'il est exactement celui annoncé et seul sur sa
  ligne : une boîte (x, y, largeur, hauteur) ou toute autre propriété qui
  bouge en fait une régression.
- Pour une prochaine purge : remplacer ATTENDUS par ceux qu'on annonce.
"""
import io
import json
import os
import re
import sys
from collections import Counter

PROPS = ['display', 'position', 'top', 'right', 'bottom', 'left', 'float', 'width', 'height', 'margin-top', 'margin-right',
         'margin-bottom', 'margin-left', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left', 'border-top-width',
         'border-bottom-width', 'border-top-color', 'border-radius', 'box-shadow', 'background-color', 'background-image', 'color',
         'opacity', 'visibility', 'overflow-x', 'overflow-y', 'z-index', 'font-family', 'font-size', 'font-weight', 'font-style',
         'line-height', 'letter-spacing', 'text-transform', 'text-align', 'text-decoration-line', 'white-space', 'justify-self',
         'align-self', 'grid-template-columns', 'grid-template-rows', 'row-gap', 'column-gap', 'flex-direction', 'flex-wrap',
         'justify-content', 'align-items', 'order', 'transform', 'filter', 'clip-path', 'list-style-type']
CHAMPS = ['index', 'element', 'x', 'y', 'largeur', 'hauteur']

# Purge V185 : le bloc « petit logo MBC dans la barre basse » posait deux
# valeurs sans effet sur un conteneur flex (.footer__bottom repasse en
# display:flex plus bas dans la feuille). Annoncé avant la mesure.
ATTENDUS = {
    'DIV.footer__bottom': re.compile(r'^grid-template-columns: auto 1fr auto 1fr -> 1fr auto 1fr$'),
    'P.footer__legal': re.compile(r'^justify-self: (start|center) -> auto$'),
}


def ecarts(X, Y):
    out = {}
    for k in X:
        x, y = X[k], Y.get(k, [])
        for i in range(max(len(x), len(y))):
            if i >= len(x) or i >= len(y) or x[i] != y[i]:
                out[(k, i)] = (x[i] if i < len(x) else None, y[i] if i < len(y) else None)
    return out


def detail(a, b):
    """Les champs qui diffèrent entre deux lignes d'empreinte."""
    if a is None or b is None:
        return ['element absent']
    pa, pb = a.split(' ; '), b.split(' ; ')
    diff = [CHAMPS[j] for j in range(6) if pa[j] != pb[j]]
    sa, sb = pa[6].split('|'), pb[6].split('|')
    diff += ['%s: %s -> %s' % (PROPS[j], sa[j], sb[j]) for j in range(min(len(sa), len(sb))) if sa[j] != sb[j]]
    if pa[7] != pb[7]:
        diff.append('::before')
    if pa[8] != pb[8]:
        diff.append('::after')
    return diff


def main():
    dossier, apres, avant, controle = sys.argv[1:5]
    lire = lambda t: json.load(io.open(os.path.join(dossier, 'site-%s.json' % t), encoding='utf-8'))
    A, B, C = lire(avant), lire(apres), lire(controle)
    bruit = ecarts(A, C)
    vrais = {k: v for k, v in ecarts(A, B).items() if k not in bruit}
    attendus, regressions = {}, {}
    for k, (a, b) in vrais.items():
        el = (a or b).split(' ; ')[1]
        d = detail(a, b)
        motif = ATTENDUS.get(el)
        (attendus if motif and len(d) == 1 and motif.match(d[0]) else regressions)[k] = (a, b)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print('vues : %d, elements : %d' % (len(A), sum(len(v) for v in A.values())))
    print('bruit (controle/avant, ecarte) : %d' % len(bruit))
    print('ecarts hors bruit (%s/%s) : %d' % (apres, avant, len(vrais)))
    par_el = Counter(((a or b).split(' ; ')[1], k.rsplit(' @', 1)[1]) for (k, _), (a, b) in attendus.items())
    print('  dont ATTENDUS (annonces) : %d  %s' % (len(attendus), dict(sorted(par_el.items()))))
    print('REGRESSIONS : %d' % len(regressions))
    par_type = Counter()
    for (k, i), (a, b) in sorted(regressions.items()):
        el = (a or b).split(' ; ')[1]
        par_type[(el, tuple(x.split(':')[0] for x in detail(a, b)))] += 1
    for (el, props), n in par_type.most_common(25):
        print('  %4d x %-40s %s' % (n, el[:40], ', '.join(props)))
    for (k, i), (a, b) in sorted(regressions.items())[:6]:
        print('  exemple %s #%d : %s' % (k, i, '; '.join(detail(a, b))[:300]))
    return 1 if regressions else 0


if __name__ == '__main__':
    sys.exit(main())
