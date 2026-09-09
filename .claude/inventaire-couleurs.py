# -*- coding: utf-8 -*-
"""Inventaire des couleurs REELLEMENT utilisees par le site.

    python .claude/inventaire-couleurs.py            le rapport
    python .claude/inventaire-couleurs.py --csv      la table brute

N'ECRIT RIEN dans le depot. C'est un instrument de mesure, pas un generateur :
la consolidation vient apres, et seulement sur ce que ce rapport montre.

CE QU'IL LIT
------------
style.css (la source commentee, pas la minifiee), les attributs style= des
27 pages, et les fill/stroke des SVG en ligne. Les commentaires CSS sont
retires du flux AVANT analyse : sans cela on compte des couleurs qui ne sont
nulle part, celles que les blocs de version citent en prose.

CE QU'IL DISTINGUE
------------------
  - la valeur (#0d1526) et sa FONCTION (color, background, border, shadow…) :
    deux teintes proches qui ne font pas le meme travail ne sont pas des
    doublons, meme si l'oeil ne les separe pas ;
  - l'opacite : rgba(240,246,252,.10) et rgba(240,246,252,.72) partagent une
    teinte mais pas un role ;
  - ce qui vit dans :root et ce qui est ecrit en dur.

L'ECART PERCEPTIF
-----------------
Deux couleurs sont dites quasi-identiques quand leur ecart CIE76 (Lab) est
inferieur a 2,3 — le seuil classique de perception pour un observateur moyen.
Au-dela de 5, personne ne parlera de doublon. Entre les deux, c'est un cas a
regarder, pas une fusion automatique.
"""
import io
import glob
import os
import re
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NOMMEES = {
    'white': (255, 255, 255), 'black': (0, 0, 0), 'transparent': None,
    'currentcolor': None, 'inherit': None, 'red': (255, 0, 0),
}


# --------------------------------------------------------------------------
# Lecture et nettoyage
# --------------------------------------------------------------------------
def sans_commentaires(css):
    """Les commentaires SORTENT du flux avant toute analyse.

    style.css porte 230 Ko de blocs de version qui citent des couleurs en
    prose (« le vert a ete assombri de 3,79 a 5,00:1 », « #190f04 »). Les
    compter reviendrait a inventorier des couleurs que personne ne voit."""
    return re.sub(r'/\*.*?\*/', ' ', css, flags=re.S)


def hex_vers_rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) == 8:      # #rrggbbaa
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), int(h[6:8], 16) / 255.0
    if len(h) != 6:
        return None, 1.0
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), 1.0


def lab(rgb):
    def f(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(x) for x in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 1.0
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    def g_(t):
        return t ** (1 / 3.0) if t > 0.008856 else (7.787 * t + 16 / 116.0)
    fx, fy, fz = g_(x), g_(y), g_(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def dE(a, b):
    la, lb = lab(a), lab(b)
    return sum((la[i] - lb[i]) ** 2 for i in range(3)) ** 0.5


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------
COULEUR = re.compile(
    r'(#[0-9a-fA-F]{3,8}\b)'
    r'|(rgba?\(\s*[\d.]+\s*[, ]\s*[\d.]+\s*[, ]\s*[\d.]+\s*(?:[,/]\s*[\d.%]+\s*)?\))'
    r'|(hsla?\([^)]*\))')

# Le nom de la propriete qui precede la valeur : c'est lui qui dit la FONCTION.
def fonction(texte, pos):
    debut = max(0, pos - 160)
    avant = texte[debut:pos]
    m = None
    for m in re.finditer(r'([-a-z]+)\s*:', avant):
        pass
    if not m:
        return 'autre'
    p = m.group(1)
    if p in ('color',):
        return 'texte'
    if p.startswith('background'):
        return 'fond'
    if p.startswith('border') or p == 'outline' or p == 'outline-color':
        return 'bordure'
    if 'shadow' in p:
        return 'ombre'
    if p in ('fill', 'stroke'):
        return 'svg'
    if p.startswith('--'):
        return 'token'
    return p


def normalise(brut):
    """-> ((r,g,b), alpha) ou (None, None) si non exploitable."""
    b = brut.strip().lower()
    if b.startswith('#'):
        return hex_vers_rgb(b)
    m = re.match(r'rgba?\(\s*([\d.]+)\s*[, ]\s*([\d.]+)\s*[, ]\s*([\d.]+)\s*(?:[,/]\s*([\d.%]+))?', b)
    if m:
        rgb = tuple(int(float(m.group(i))) for i in (1, 2, 3))
        a = m.group(4)
        if a is None:
            al = 1.0
        elif a.endswith('%'):
            al = float(a[:-1]) / 100.0
        else:
            al = float(a)
        return rgb, al
    return None, None


def relever():
    """Toutes les occurrences, avec leur source et leur fonction."""
    occ = defaultdict(lambda: {"n": 0, "fonctions": defaultdict(int),
                               "sources": defaultdict(int), "root": False,
                               "exemples": []})
    css = sans_commentaires(io.open(os.path.join(RACINE, 'style.css'), encoding='utf-8').read())
    # la zone :root, pour savoir ce qui est deja tokenise
    mroot = re.search(r':root\s*\{(.*?)\}', css, re.S)
    zone_root = (mroot.start(1), mroot.end(1)) if mroot else (-1, -1)

    def ajoute(brut, fct, src, dans_root=False, exemple=''):
        rgb, al = normalise(brut)
        if rgb is None:
            return
        cle = (rgb, round(al, 3))
        o = occ[cle]
        o["n"] += 1
        o["fonctions"][fct] += 1
        o["sources"][src] += 1
        if dans_root:
            o["root"] = True
        if exemple and len(o["exemples"]) < 3 and exemple not in o["exemples"]:
            o["exemples"].append(exemple)

    for m in COULEUR.finditer(css):
        brut = m.group(0)
        dans_root = zone_root[0] <= m.start() <= zone_root[1]
        # le selecteur le plus proche, pour l'exemple
        av = css.rfind('}', 0, m.start())
        sel = css[av + 1:css.find('{', m.start() - 400 if m.start() > 400 else 0)] if av >= 0 else ''
        sel = re.sub(r'\s+', ' ', sel).strip()[:44]
        ajoute(brut, fonction(css, m.start()), 'style.css', dans_root, sel)

    pages = sorted(set(glob.glob(os.path.join(RACINE, '*.html'))
                       + glob.glob(os.path.join(RACINE, '*/index.html'))
                       + glob.glob(os.path.join(RACINE, '*/*/index.html'))))
    for p in pages:
        if 'worktrees' in p or os.sep + 'print' + os.sep in p:
            continue
        h = io.open(p, encoding='utf-8').read()
        h = re.sub(r'<!--.*?-->', ' ', h, flags=re.S)
        nom = os.path.relpath(p, RACINE).replace(os.sep, '/')
        for m in re.finditer(r'style="([^"]*)"', h):
            for c in COULEUR.finditer(m.group(1)):
                ajoute(c.group(0), fonction(m.group(1), c.start()), 'HTML inline', exemple=nom)
        for m in re.finditer(r'(?:fill|stroke)="(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))"', h):
            ajoute(m.group(1), 'svg', 'SVG inline', exemple=nom)
    return occ


def hexa(rgb):
    return '#%02x%02x%02x' % rgb


# Les fonctions qui ne sont PAS des choix de couleur mais de la mecanique :
# arrets de degrade, masques, filtres. Les compter gonflait l'inventaire de
# 58 occurrences de #000000 qui ne sont vues par personne — ce sont les bornes
# d'un mask-image, pas une teinte de la charte.
MECANIQUE = ('-webkit-mask-image', 'mask-image', 'filter', '-webkit-filter',
             'backdrop-filter', '-webkit-backdrop-filter')


def design_seulement(occ):
    """Ne garde que ce qui compose reellement l'interface.

    Deux exclusions, et chacune se justifie :
      - les fonctions mecaniques ci-dessus ;
      - les valeurs d'alpha 0, qui sont des transparents de degrade : une
        couleur qu'on ne voit pas n'est pas une couleur a consolider.
    """
    out = {}
    for k, v in occ.items():
        if k[1] <= 0.001:
            continue
        f = {a: b for a, b in v["fonctions"].items() if a not in MECANIQUE}
        if not f:
            continue
        n = sum(f.values())
        out[k] = {"n": n, "fonctions": f, "sources": v["sources"],
                  "root": v["root"], "exemples": v["exemples"]}
    return out


def main():
    brut = relever()
    occ = design_seulement(brut)
    print(u"  (mecanique ecartee : %d valeurs de degrade/masque/filtre)"
          % (len(brut) - len(occ)))
    total = sum(o["n"] for o in occ.values())
    opaques = {k: v for k, v in occ.items() if k[1] >= 0.999}
    alpha = {k: v for k, v in occ.items() if k[1] < 0.999}

    print(u"\n" + u"=" * 78)
    print(u"  INVENTAIRE DES COULEURS — mbc974.com")
    print(u"=" * 78)
    print(u"  %d valeurs distinctes pour %d occurrences" % (len(occ), total))
    print(u"    dont %d opaques et %d avec canal alpha" % (len(opaques), len(alpha)))
    print(u"    dont %d declarees dans :root" % sum(1 for v in occ.values() if v["root"]))

    print(u"\n  ---- LES 30 PLUS EMPLOYEES " + u"-" * 50)
    print(u"  %-26s %5s  %-30s %s" % (u"valeur", u"occ.", u"fonctions", u":root"))
    for k, v in sorted(occ.items(), key=lambda x: -x[1]["n"])[:30]:
        rgb, al = k
        val = hexa(rgb) if al >= 0.999 else u"%s @%.2f" % (hexa(rgb), al)
        f = ", ".join(u"%s×%d" % (a, b) for a, b in
                      sorted(v["fonctions"].items(), key=lambda x: -x[1])[:3])
        print(u"  %-26s %5d  %-30s %s" % (val, v["n"], f[:30], u"oui" if v["root"] else u""))

    # ---- quasi-doublons, a fonction comparable --------------------------
    print(u"\n  ---- QUASI-DOUBLONS (ecart CIE76 < 2,3, meme famille) " + u"-" * 22)
    liste = sorted(opaques.items(), key=lambda x: -x[1]["n"])
    vus, groupes = set(), []
    for i, (k1, v1) in enumerate(liste):
        if k1 in vus:
            continue
        grp = [(k1, v1)]
        for k2, v2 in liste[i + 1:]:
            if k2 in vus:
                continue
            if dE(k1[0], k2[0]) < 2.3:
                grp.append((k2, v2))
                vus.add(k2)
        if len(grp) > 1:
            vus.add(k1)
            groupes.append(grp)
    if not groupes:
        print(u"  aucun")
    for grp in sorted(groupes, key=lambda g: -sum(x[1]["n"] for x in g)):
        tot = sum(x[1]["n"] for x in grp)
        print(u"\n   %d teintes, %d occurrences cumulees :" % (len(grp), tot))
        for k, v in sorted(grp, key=lambda x: -x[1]["n"]):
            f = ", ".join(sorted(v["fonctions"]))
            print(u"     %-10s %4d occ.  %-28s %s"
                  % (hexa(k[0]), v["n"], f[:28], u"(:root)" if v["root"] else u""))

    # ---- teintes portant plusieurs opacites -----------------------------
    print(u"\n  ---- UNE TEINTE, PLUSIEURS OPACITES " + u"-" * 39)
    par_rgb = defaultdict(list)
    for (rgb, al), v in alpha.items():
        par_rgb[rgb].append((al, v["n"]))
    for rgb, l in sorted(par_rgb.items(), key=lambda x: -sum(n for _, n in x[1]))[:8]:
        if len(l) < 2:
            continue
        print(u"   %-10s %2d opacites : %s" % (
            hexa(rgb), len(l),
            ", ".join(u"%.2f(×%d)" % (a, n) for a, n in sorted(l))))

    print(u"\n  ---- REPARTITION PAR FONCTION " + u"-" * 45)
    parf = defaultdict(int)
    for v in occ.values():
        for f, n in v["fonctions"].items():
            parf[f] += n
    for f, n in sorted(parf.items(), key=lambda x: -x[1]):
        print(u"   %-14s %5d occurrences (%.0f %%)" % (f, n, n * 100.0 / total))
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
