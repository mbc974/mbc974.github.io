# -*- coding: utf-8 -*-
"""Inventaire des espacements — margin, padding, gap.

    python .claude/inventaire-espacements.py

N'ECRIT RIEN. Troisieme instrument de mesure de la serie, apres les couleurs
et la typographie, et construit sur les memes principes.

CE QU'IL DISTINGUE, ET POURQUOI C'EST TOUT LE SUJET
---------------------------------------------------
Le meme nombre de pixels ne fait pas le meme travail :

  24 px de padding sur un BOUTON      -> une zone de clic
  24 px de gap entre deux CARTES      -> une separation
  24 px de margin sous un TITRE       -> une respiration typographique
  24 px de padding sur une SECTION    -> le rythme vertical de la page

Les compter ensemble donnerait un chiffre spectaculaire et inutilisable. On
classe donc par ROLE, deduit du selecteur :

  section    le rythme vertical de la page (.section, main>, .wrap, .sec-head)
  hero       la respiration du premier ecran, qui a ses propres regles
  carte      les composants (.cat, .pack, .sq-card, .mx-row, .ac, .cw…)
  grille     gap / row-gap / column-gap : l'espace ENTRE des elements
  micro-UI   boutons, etiquettes, puces, champs — l'echelle du doigt
  autre      le reste

VARIANTES D'ECRITURE
--------------------
« 0 », « 0px », « 0rem » sont la meme chose. « .5rem » et « 0.5rem » aussi.
On normalise avant de compter : sinon l'inventaire mesure la façon d'ecrire,
pas les espacements.

CE QU'IL NE FAIT PAS
--------------------
Il ne propose aucune fusion. Deux valeurs proches qui jouent des roles
differents ne sont pas des doublons — c'est la leçon des navies de la phase
couleurs, ou 250 occurrences « indiscernables » se sont revelees etre les
paliers d'un degrade.
"""
import io
import os
import re
import sys
from collections import defaultdict

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROPS = ('margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
         'margin-inline', 'margin-block', 'margin-inline-start', 'margin-inline-end',
         'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
         'padding-inline', 'padding-block', 'gap', 'row-gap', 'column-gap')

ROLES = [
    ('hero', re.compile(r'\.hero|\.hw\b|\.nx\b|\.nx__')),
    ('section', re.compile(r'\.section\b|main\s*>|\.wrap\b|\.sec-head|\.sec-cta|'
                           r'\.site-footer|\.seo-foot|\.ml-sec|\.squad-sec|\.local-proof')),
    ('micro-UI', re.compile(r'\.btn\b|\.btn--|\bbutton\b|\binput\b|\bselect\b|\btextarea\b|'
                            r'\blabel\b|\.chip|\.pl-f\b|\.pl-chip|\.kicker|\.badge|'
                            r'\.float-cta|\.nav\b|\.nav__|\.seo-top|\.site-header|\.burger')),
    ('carte', re.compile(r'\.cat\b|\.cat__|\.pack\b|\.pack__|\.sq-card|\.sq-rail|\.mx-row|'
                         r'\.mx-|\.ml__|\.ac\b|\.ac__|\.cw\b|\.cw__|\.cx-|\.pk-|\.keyfig|'
                         r'\.essentiel|\.staff|\.team|\.support-card|\.sponsor|\.cal-lieu|'
                         r'\.pl-slot|\.pl-jour|\.p-pillar|\.parents|\.covers|\.visi|\.vis-')),
]


def masque(css):
    out = list(css)
    for m in re.finditer(r'/\*.*?\*/', css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def role_de(sel, prop):
    if prop.endswith('gap'):
        return 'grille'
    for nom, rx in ROLES:
        if rx.search(sel):
            return nom
    return 'autre'


def normalise(v):
    """« 0px », « 0rem », « 0 » -> « 0 » ; « 0.5rem » -> « .5rem »."""
    v = v.strip().lower()
    if re.fullmatch(r'0(px|rem|em|%)?', v):
        return '0'
    v = re.sub(r'\b0+(\.\d+)', r'\1', v)
    return v


def classes_du_site():
    import glob
    vus = set()
    for f in (glob.glob(os.path.join(RACINE, '*.html'))
              + glob.glob(os.path.join(RACINE, '*/index.html'))
              + glob.glob(os.path.join(RACINE, '*/*/index.html'))
              + glob.glob(os.path.join(RACINE, '.claude/*.py'))):
        if 'worktrees' in f:
            continue
        t = io.open(f, encoding='utf-8').read()
        for m in re.finditer(r'class=["\']([^"\']+)["\']', t):
            for c in m.group(1).split():
                vus.add(c.strip())
    return vus


def main():
    css = masque(io.open(os.path.join(RACINE, 'style.css'), encoding='utf-8').read())
    presentes = classes_du_site()

    decls = []
    rx = re.compile(r'\b(' + '|'.join(sorted(PROPS, key=len, reverse=True)) + r')\s*:\s*([^;}]+)')
    for m in rx.finditer(css):
        prop, val = m.group(1), m.group(2).strip()
        ouv = css.rfind('{', 0, m.start())
        prec = max(css.rfind('}', 0, ouv), css.rfind('{', 0, ouv))
        sel = re.sub(r'\s+', ' ', css[prec + 1:ouv]).strip()
        cls = re.findall(r'\.([A-Za-z0-9_-]+)', sel)
        morte = bool(cls) and not any(c in presentes for c in cls)
        decls.append((prop, val, sel, role_de(sel, prop), morte))

    print(u"\n" + u"=" * 78)
    print(u"  INVENTAIRE DES ESPACEMENTS — mbc974.com")
    print(u"=" * 78)
    print(u"  %d declarations d'espacement" % len(decls))

    # --- les valeurs ATOMIQUES : on eclate « 1rem 2rem » en deux -----------
    atomes = defaultdict(lambda: {"n": 0, "roles": defaultdict(int), "morte": 0})
    for prop, val, sel, role, morte in decls:
        if 'var(' in val or 'calc(' in val or 'clamp(' in val:
            # une valeur calculee n'est pas une valeur d'echelle : on la compte a part
            atomes['(calculee)']["n"] += 1
            atomes['(calculee)']["roles"][role] += 1
            atomes['(calculee)']["morte"] += 1 if morte else 0
            continue
        for part in val.split():
            k = normalise(part)
            atomes[k]["n"] += 1
            atomes[k]["roles"][role] += 1
            atomes[k]["morte"] += 1 if morte else 0

    vivantes = {k: v for k, v in atomes.items() if v["morte"] < v["n"]}
    print(u"  %d valeurs distinctes (apres normalisation des ecritures)" % len(atomes))
    print(u"  %d reellement vivantes" % len(vivantes))

    print(u"\n  ---- REPARTITION PAR ROLE " + u"-" * 50)
    par_role = defaultdict(int)
    for prop, val, sel, role, morte in decls:
        par_role[role] += 1
    for r, n in sorted(par_role.items(), key=lambda x: -x[1]):
        print(u"   %-10s %4d declarations (%.0f %%)" % (r, n, n * 100.0 / len(decls)))

    print(u"\n  ---- REPARTITION PAR PROPRIETE " + u"-" * 45)
    par_prop = defaultdict(int)
    for prop, val, sel, role, morte in decls:
        par_prop[prop] += 1
    for p, n in sorted(par_prop.items(), key=lambda x: -x[1])[:12]:
        print(u"   %-18s %4d" % (p, n))

    def rem(v):
        m = re.fullmatch(r'([\d.]+)rem', v)
        if m:
            return float(m.group(1))
        m = re.fullmatch(r'([\d.]+)px', v)
        if m:
            return float(m.group(1)) / 16.0
        return None

    print(u"\n  ---- LES VALEURS DOMINANTES (top 26) " + u"-" * 38)
    print(u"  %-12s %5s %6s  %s" % (u"valeur", u"occ.", u"~px", u"roles"))
    for k, v in sorted(atomes.items(), key=lambda x: -x[1]["n"])[:26]:
        r = rem(k)
        roles = ", ".join(u"%s×%d" % (a, b) for a, b in
                          sorted(v["roles"].items(), key=lambda x: -x[1])[:3])
        mort = u"  [morte]" if v["morte"] == v["n"] else u""
        print(u"  %-12s %5d %6s  %s%s"
              % (k, v["n"], (u"%.0f" % (r * 16)) if r is not None else u"-", roles[:44], mort))

    print(u"\n  ---- LES QUASI-DOUBLONS (ecart < 1,5 px, meme role dominant) " + u"-" * 14)
    fixes = [(k, v, rem(k)) for k, v in atomes.items() if rem(k) is not None and rem(k) > 0]
    fixes.sort(key=lambda x: x[2])
    grp, vus = [], set()
    for i, (k, v, r) in enumerate(fixes):
        if k in vus:
            continue
        cur = [(k, v, r)]
        for k2, v2, r2 in fixes[i + 1:]:
            if k2 in vus:
                continue
            if abs(r2 - r) * 16 < 1.5:
                cur.append((k2, v2, r2)); vus.add(k2)
        if len(cur) > 1:
            vus.add(k); grp.append(cur)
    for g in sorted(grp, key=lambda x: -sum(y[1]["n"] for y in x))[:10]:
        tot = sum(y[1]["n"] for y in g)
        dom = defaultdict(int)
        for _, v, _ in g:
            for a, b in v["roles"].items():
                dom[a] += b
        r_dom = max(dom.items(), key=lambda x: x[1])[0]
        print(u"   %-46s %3d occ.  role dominant : %s"
              % (" · ".join(u"%s(%d)" % (y[0], y[1]["n"]) for y in g), tot, r_dom))
    print()
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
