# -*- coding: utf-8 -*-
"""Inventaire des tailles de texte REELLEMENT employees.

    python .claude/inventaire-typo.py

N'ECRIT RIEN. Instrument de mesure, comme inventaire-couleurs.py.

CE QU'IL DISTINGUE — et pourquoi c'est le coeur du sujet
--------------------------------------------------------
Compter les « font-size » declarees donne un chiffre qui ne veut rien dire :
une feuille peut declarer trois fois la meme taille pour trois composants, ou
declarer un clamp() qui couvre a lui seul cinq tailles selon la largeur.

On separe donc :

  STATIQUE   font-size:.82rem        une taille, une valeur
  FLUIDE     font-size:clamp(a,b,c)  une PLAGE : elle vaut a en dessous d'une
                                     certaine largeur, c au-dela. Deux clamps
                                     de bornes identiques sont le meme
                                     traitement, meme s'ils s'ecrivent
                                     differemment.

et on classe par FAMILLE, parce qu'une taille n'a pas le meme sens selon la
police qui la porte :

  display  (Anton)            les titres et les chiffres sportifs
  cond     (Barlow Condensed) l'interface : boutons, etiquettes, kickers
  body     (Barlow)           le texte courant
  herite   la regle ne fixe pas la famille

MORTES
------
Une taille declaree pour un selecteur qui n'existe dans aucun markup ne se
voit jamais. On les compte a part : les faire entrer dans une echelle serait
ranger un placard vide.
"""
import io
import glob
import os
import re
import sys
from collections import defaultdict

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sans_commentaires(css):
    return re.sub(r'/\*.*?\*/', ' ', css, flags=re.S)


def classes_du_site():
    """Toutes les classes presentes dans le markup publie ET dans les chaines
    des generateurs — meme regle que verifier-classes.py : une classe ecrite
    par un script Python existe, meme si aucune page ne la porte aujourd'hui."""
    vus = set()
    fichiers = (glob.glob(os.path.join(RACINE, '*.html'))
                + glob.glob(os.path.join(RACINE, '*/index.html'))
                + glob.glob(os.path.join(RACINE, '*/*/index.html'))
                + glob.glob(os.path.join(RACINE, '.claude/*.py')))
    for f in fichiers:
        if 'worktrees' in f:
            continue
        t = io.open(f, encoding='utf-8').read()
        for m in re.finditer(r'class="([^"]+)"', t):
            for c in m.group(1).split():
                vus.add(c.strip())
        for m in re.finditer(r"class='([^']+)'", t):
            for c in m.group(1).split():
                vus.add(c.strip())
    return vus


def famille_de(bloc, css, pos):
    """La famille declaree dans la meme regle, ou heritee."""
    m = re.search(r'font-family\s*:\s*var\(--ff-([a-z]+)\)', bloc)
    if m:
        return {'display': 'display', 'cond': 'cond', 'body': 'body'}.get(m.group(1), m.group(1))
    if 'var(--ff-display)' in bloc:
        return 'display'
    return 'herite'


def regle_de(css, pos):
    ouv = css.rfind('{', 0, pos)
    prec = max(css.rfind('}', 0, ouv), css.rfind('{', 0, ouv))
    fin = css.find('}', pos)
    return re.sub(r'\s+', ' ', css[prec + 1:ouv]).strip(), css[ouv:fin]


def normalise_clamp(expr):
    """Les trois bornes d'un clamp, arrondies : deux clamps de memes bornes
    sont le MEME traitement, quelle que soit leur ecriture."""
    inner = expr[expr.find('(') + 1:expr.rfind(')')]
    prof, cour, parts = 0, '', []
    for ch in inner:
        if ch == '(':
            prof += 1
        elif ch == ')':
            prof -= 1
        if ch == ',' and prof == 0:
            parts.append(cour.strip()); cour = ''
        else:
            cour += ch
    parts.append(cour.strip())
    return tuple(p.replace(' ', '') for p in parts)


def main():
    css = sans_commentaires(io.open(os.path.join(RACINE, 'style.css'), encoding='utf-8').read())
    presentes = classes_du_site()

    statiques = defaultdict(lambda: {"n": 0, "familles": defaultdict(int), "sel": [], "morte": 0})
    clamps = defaultdict(lambda: {"n": 0, "familles": defaultdict(int), "sel": [], "morte": 0})

    for m in re.finditer(r'font-size\s*:\s*([^;}]+)', css):
        val = m.group(1).strip()
        sel, bloc = regle_de(css, m.start())
        fam = famille_de(bloc, css, m.start())
        # la regle est-elle vivante ? au moins une de ses classes doit exister
        cls = re.findall(r'\.([A-Za-z0-9_-]+)', sel)
        morte = bool(cls) and not any(c in presentes for c in cls)
        cible = clamps if val.startswith('clamp(') else statiques
        cle = normalise_clamp(val) if val.startswith('clamp(') else val
        d = cible[cle]
        d["n"] += 1
        d["familles"][fam] += 1
        d["morte"] += 1 if morte else 0
        if len(d["sel"]) < 3:
            d["sel"].append(sel[:38])

    tot = sum(v["n"] for v in statiques.values()) + sum(v["n"] for v in clamps.values())
    print(u"\n" + u"=" * 78)
    print(u"  INVENTAIRE TYPOGRAPHIQUE — mbc974.com")
    print(u"=" * 78)
    print(u"  %d declarations font-size" % tot)
    print(u"    %d valeurs STATIQUES distinctes" % len(statiques))
    print(u"    %d expressions FLUIDES distinctes (clamp)" % len(clamps))
    mortes_s = sum(1 for v in statiques.values() if v["morte"] == v["n"])
    mortes_c = sum(1 for v in clamps.values() if v["morte"] == v["n"])
    print(u"    dont %d statiques et %d fluides employees UNIQUEMENT par des"
          u" selecteurs absents du markup" % (mortes_s, mortes_c))

    def rem(v):
        m = re.match(r'([\d.]+)rem', v)
        if m:
            return float(m.group(1))
        m = re.match(r'([\d.]+)px', v)
        if m:
            return float(m.group(1)) / 16.0
        return -1

    print(u"\n  ---- LES TAILLES STATIQUES, DE LA PLUS PETITE A LA PLUS GRANDE " + u"-" * 14)
    print(u"  %-12s %5s %5s  %-26s %s" % (u"valeur", u"occ.", u"~px", u"familles", u"exemple"))
    for val, v in sorted(statiques.items(), key=lambda x: (-rem(x[0]) if rem(x[0]) > 0 else 999)):
        px = rem(val) * 16
        fam = ", ".join(u"%s×%d" % (a, b) for a, b in
                        sorted(v["familles"].items(), key=lambda x: -x[1])[:2])
        mort = u"  [morte]" if v["morte"] == v["n"] else u""
        print(u"  %-12s %5d %5s  %-26s %s%s"
              % (val, v["n"], (u"%.0f" % px) if px > 0 else u"?", fam[:26], v["sel"][0][:26], mort))

    print(u"\n  ---- LES EXPRESSIONS FLUIDES " + u"-" * 47)
    print(u"  %-38s %5s  %-18s %s" % (u"clamp(min, ideal, max)", u"occ.", u"familles", u"exemple"))
    for cl, v in sorted(clamps.items(), key=lambda x: -x[1]["n"])[:24]:
        fam = ", ".join(sorted(v["familles"]))[:18]
        mort = u"  [morte]" if v["morte"] == v["n"] else u""
        print(u"  %-38s %5d  %-18s %s%s"
              % (u"clamp(%s)" % u",".join(cl), v["n"], fam, v["sel"][0][:22], mort))
    if len(clamps) > 24:
        print(u"  … et %d autres expressions" % (len(clamps) - 24))
    print()
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
