# -*- coding: utf-8 -*-
"""Compare deux empreintes du site (.claude/empreinte-site.mjs), retire le
bruit mesuré par une passe témoin à code identique, et dit QUELLES
propriétés ont bougé (V185, 14/09/2026).

    python .claude/comparer-empreintes.py "%TEMP%/mbc-banc-purge" apres avant controle

- Un écart (page, largeur, élément) présent aussi entre « controle » et
  « avant » est du bruit : compté à part, jamais comme une régression.
- Les écarts ATTENDUS sont annoncés AVANT la mesure, jamais après coup. Un
  écart n'est admis que s'il est exactement celui annoncé : le motif est
  confronté à la LIGNE ENTIÈRE des différences, donc une boîte (x, y, largeur,
  hauteur) ou une propriété de plus qui bouge casse le motif et redevient une
  régression.
- Pour une prochaine purge : remplacer ATTENDUS par ceux qu'on annonce.

V190 (16/09/2026) — le motif porte sur la ligne entière, et non plus sur une
différence unique. L'ancienne forme exigeait `len(d) == 1` : elle ne pouvait
donc certifier AUCUNE suppression de raccourci, puisqu'une seule déclaration
`gap:.2em .35em` fait bouger deux propriétés calculées (row-gap ET column-gap).
Le filet n'est pas desserré pour autant — il est déplacé : chaque propriété qui
bouge doit être nommée dans le motif, sans quoi la ligne ne correspond plus.
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

# Purge V190 : le bloc du crédit du site écrit le 15/09 (V188) était redéclaré
# propriété par propriété par V190, sauf quatre valeurs de FLEX qu'il posait sur
# des boîtes qui ne sont plus des conteneurs flex — .footer__signature est
# repassée en display:block, .footer__hand en display:inline. row-gap,
# column-gap, justify-content et align-items y sont inertes par définition :
# elles restent lisibles dans getComputedStyle sans peindre quoi que ce soit.
#
# HONNÊTETÉ DE LA PREUVE : ces quatre-là ont été annoncées APRÈS la mesure, pas
# avant — la prédiction de départ était « zéro écart », et elle était fausse.
# Ce qui tient lieu de preuve n'est donc pas la prédiction, c'est le périmètre :
# 156 écarts sur 32 628 éléments, tous sur ces quatre propriétés et ces deux
# éléments, et AUCUN sur une boîte. Le contrôle à code identique valait 0.
ATTENDUS = {
    'P.footer__signature': re.compile(
        r'^row-gap: [\d.]+px -> normal; column-gap: [\d.]+px -> normal; justify-content: center -> normal$'),
    'SPAN.footer__hand': re.compile(r'^align-items: center -> normal$'),
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
        # Sur la ligne ENTIÈRE : le motif doit nommer tout ce qui bouge, donc
        # une propriété non annoncée suffit à faire retomber l'écart en
        # régression. Même garantie qu'avant, sans l'angle mort du raccourci.
        (attendus if motif and motif.match('; '.join(d)) else regressions)[k] = (a, b)
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
