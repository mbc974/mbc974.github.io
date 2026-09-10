# -*- coding: utf-8 -*-
"""Inventaire des points de rupture.

    python .claude/inventaire-breakpoints.py
    python .claude/inventaire-breakpoints.py chevauchements
    python .claude/inventaire-breakpoints.py poids

N'ECRIT RIEN. Cinquieme et dernier instrument de la serie, apres les couleurs,
la typographie, les espacements, les rayons et les ombres.

POURQUOI C'EST LE SUJET LE PLUS RISQUE
---------------------------------------
Les quatre precedents portaient sur des VALEURS : une couleur, une taille, un
espacement, un rayon. On pouvait les mesurer element par element et prouver
qu'ils ne bougeaient pas.

Un breakpoint ne se mesure pas ainsi. Il decide QUELLES REGLES S'APPLIQUENT.
Le deplacer de 1 px ne change rien a 1335 px de large et peut casser toute une
page a 900. Et surtout : deux breakpoints voisins ne sont pas des doublons —
« max-width:899px » et « max-width:900px » different exactement a 900 px, la
largeur la plus frequente des tablettes en paysage.

LES TROIS DEFAUTS QU'IL CHERCHE
--------------------------------
1. CHEVAUCHEMENT. Une meme valeur employee en min ET en max :

       @media (max-width:560px){ .x{color:red} }
       @media (min-width:560px){ .x{color:blue} }

   A 560 px exactement, LES DEUX s'appliquent. C'est la derniere du fichier qui
   gagne, ce qui rend le resultat dependant de l'ordre d'ecriture plutot que de
   l'intention. Le motif correct est « max-width:559px » / « min-width:560px ».

2. TROU. « max-width:559px » et « min-width:561px » : a 560 px exactement,
   aucune des deux ne s'applique. L'element retombe sur sa valeur de base, ce
   qui donne un rendu que personne n'a dessine.

3. GRAPPE. Trois valeurs a quelques pixels les unes des autres (519/520,
   979/980/981) qui decrivent probablement la meme intention de mise en page,
   ecrites a des moments differents.

CE QU'IL NE MELANGE PAS
------------------------
Les requetes de LARGEUR sont un systeme de mise en page. « prefers-reduced-
motion », « hover », « pointer », « orientation » et les requetes de HAUTEUR
n'en font pas partie : ce sont des capacites ou des preferences, elles n'ont
ni echelle ni ordre. Elles sont comptees a part et ne seront jamais
« rationalisees ».
"""
import io
import os
import re
import sys
from collections import defaultdict

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(RACINE, 'style.css')


def masque(css):
    out = list(css)
    for m in re.finditer(r'/\*.*?\*/', css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def blocs(css):
    """(ligne, condition, texte du bloc) pour chaque @media, parenthese et
    accolade equilibrees."""
    mc = masque(css)
    out = []
    for m in re.finditer(r'@media([^{]*)\{', mc):
        prof, i = 1, m.end()
        while i < len(mc) and prof:
            if mc[i] == '{':
                prof += 1
            elif mc[i] == '}':
                prof -= 1
            i += 1
        out.append((mc[:m.start()].count('\n') + 1,
                    re.sub(r'\s+', ' ', m.group(1)).strip(),
                    mc[m.end():i - 1]))
    return out


def largeurs(cond):
    """[(direction, px)] des contraintes de largeur d'une condition."""
    return [(d, float(v)) for d, v in
            re.findall(r'\((min|max)-width\s*:\s*([\d.]+)px\)', cond)]


def entete(t):
    print(u"\n" + u"=" * 78)
    print(u"  " + t)
    print(u"=" * 78)


def rapport(bs):
    entete(u"INVENTAIRE DES POINTS DE RUPTURE — mbc974.com")
    print(u"  %d @media" % len(bs))
    conds = defaultdict(int)
    for _, c, _ in bs:
        conds[c] += 1
    print(u"  %d conditions distinctes" % len(conds))

    larg = [b for b in bs if largeurs(b[1])]
    autres = [b for b in bs if not largeurs(b[1])]
    print(u"  %d portent sur la LARGEUR (le systeme de mise en page)" % len(larg))
    print(u"  %d portent sur autre chose (capacites, preferences, hauteur)" % len(autres))

    print(u"\n  ---- CE QUI N'EST PAS UN BREAKPOINT " + u"-" * 40)
    ff = defaultdict(int)
    for _, c, _ in autres:
        for f in re.findall(r'\(([a-z-]+)\s*:', c) or ['(sans feature)']:
            ff[f] += 1
        if not re.findall(r'\(([a-z-]+)\s*:', c):
            ff[c[:28] or '?'] += 1
    for f, n in sorted(ff.items(), key=lambda x: -x[1]):
        print(u"   %-30s %3d   (hors perimetre : ni echelle, ni ordre)" % (f, n))

    print(u"\n  ---- LES VALEURS DE LARGEUR " + u"-" * 48)
    v = defaultdict(lambda: {'min': 0, 'max': 0, 'regles': 0})
    for ligne, c, corps in bs:
        n = len(re.findall(r'[^{}]+\{', corps))
        for d, px in largeurs(c):
            v[px][d] += 1
            v[px]['regles'] += n
    print(u"  %-8s %-5s %-5s %-8s %s" % (u"px", u"min", u"max", u"regles", u""))
    for px in sorted(v):
        d = v[px]
        dr = u"  <-- employee dans LES DEUX SENS" if d['min'] and d['max'] else u""
        print(u"  %-8g %-5d %-5d %-8d%s" % (px, d['min'], d['max'], d['regles'], dr))
    print(u"\n  %d valeurs distinctes" % len(v))
    return v


def chevauchements(bs):
    entete(u"LES DEFAUTS DE DECOUPAGE")
    v = defaultdict(lambda: {'min': 0, 'max': 0})
    for _, c, _ in bs:
        for d, px in largeurs(c):
            v[px][d] += 1

    doubles = sorted(px for px in v if v[px]['min'] and v[px]['max'])
    print(u"\n  1. CHEVAUCHEMENTS — la valeur sert en min ET en max")
    print(u"     A cette largeur exacte, les deux jeux de regles s'appliquent ;")
    print(u"     c'est l'ordre du fichier qui tranche, pas l'intention.\n")
    print(u"     %-8s %-6s %-6s" % (u"px", u"min", u"max"))
    for px in doubles:
        print(u"     %-8g %-6d %-6d" % (px, v[px]['min'], v[px]['max']))
    print(u"     -> %d largeur(s) concernee(s)" % len(doubles))

    print(u"\n  2. PAIRES CORRECTES — max:N-1 suivi de min:N, aucun recouvrement")
    paires = sorted(px for px in v if (px - 1) in v and v[px]['min'] and v[px - 1]['max'])
    print(u"     " + ", ".join(u"%g/%g" % (px - 1, px) for px in paires))
    print(u"     -> %d paire(s) bien formee(s)" % len(paires))

    print(u"\n  3. TROUS — aucune regle ne couvre cette largeur exacte")
    trous = []
    for px in sorted(v):
        if not v[px]['max']:
            continue
        # une largeur juste au-dessus d'un max, sans min correspondant
        for cible in (px + 1,):
            if cible in v and v[cible]['min']:
                break
        else:
            if (px + 1) not in v and (px + 2) in v and v[px + 2]['min']:
                trous.append(px + 1)
    print(u"     " + (", ".join(u"%g px" % t for t in trous) if trous
                      else u"aucun detecte"))

    print(u"\n  4. GRAPPES — valeurs a 3 px ou moins, meme intention probable")
    tous = sorted(v)
    grp, cur = [], [tous[0]]
    for px in tous[1:]:
        if px - cur[-1] <= 3:
            cur.append(px)
        else:
            grp.append(cur)
            cur = [px]
    grp.append(cur)
    for g in grp:
        if len(g) > 1:
            det = ", ".join(u"%g(min%d/max%d)" % (px, v[px]['min'], v[px]['max']) for px in g)
            print(u"     %s" % det)
    print()


def poids(bs):
    entete(u"LE POIDS DE CHAQUE CONDITION — combien de regles elle porte")
    par = defaultdict(lambda: {'n': 0, 'regles': 0, 'lignes': []})
    for ligne, c, corps in bs:
        d = par[c]
        d['n'] += 1
        d['regles'] += len(re.findall(r'[^{}]+\{', corps))
        d['lignes'].append(ligne)
    print(u"  %-46s %5s %7s" % (u"condition", u"blocs", u"regles"))
    for c, d in sorted(par.items(), key=lambda x: -x[1]['regles'])[:28]:
        print(u"  %-46s %5d %7d" % (c[:46], d['n'], d['regles']))
    seuls = [c for c, d in par.items() if d['regles'] <= 1]
    print(u"\n  %d condition(s) ne portent qu'une regle ou moins" % len(seuls))
    for c in sorted(seuls)[:12]:
        print(u"     %s" % c[:70])
    print()


def main():
    css = io.open(CSS, encoding='utf-8').read()
    bs = blocs(css)
    quoi = sys.argv[1] if len(sys.argv) > 1 else 'tout'
    if quoi in ('tout', 'inventaire'):
        rapport(bs)
    if quoi in ('tout', 'chevauchements'):
        chevauchements(bs)
    if quoi in ('tout', 'poids'):
        poids(bs)
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
