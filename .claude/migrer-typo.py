# -*- coding: utf-8 -*-
"""Migration de la typographie vers l'echelle de texte, palier par palier.

    python .claude/migrer-typo.py tokens              pose les 7 tokens dans :root
    python .claude/migrer-typo.py base lg --essai     simule un lot
    python .claude/migrer-typo.py base lg             applique
    python .claude/migrer-typo.py 2xs xs sm md 2xl

L'ECHELLE, ET D'OU ELLE VIENT
-----------------------------
Les ancres ne sortent pas d'un ratio theorique (1,125, 1,25...) mais des MASSES
D'USAGE reelles, mesurees dans le navigateur sur 762 elements porteurs de
texte : 34 tailles rendues se pressaient entre 10 et 20 px, dont trois dans un
tiers de pixel (13,1 / 13,3 / 13,4).

    --text-2xs   .66rem   10,6 px
    --text-xs    .72rem   11,5 px
    --text-sm    .80rem   12,8 px
    --text-md    .87rem   13,9 px
    --text-base  .95rem   15,2 px
    --text-lg   1rem      16,0 px
    --text-2xl  1.2rem    19,2 px

--text-md vaut .87 et non .86 : ce demi-pas absorbe les 16 declarations de
.9rem — une des tailles les plus employees du site — pour 0,2 point d'ecart
maximal en plus (3,2 % -> 3,4 %).

LA REGLE DE MIGRATION
---------------------
Une declaration ne migre QUE si son ecart au palier reste sous 4 %. Au-dela,
elle reste ou elle est. Un design system absorbe les repetitions reelles ; il
ne force pas toutes les valeurs du site dans une grille.

CE QUI N'EST PAS TOUCHE
-----------------------
  - la bande DISPLAY (> 1.25rem) : scores, numeros de joueur, titres de
    section, hero, mot de fond. Chaque valeur y porte un composant precis, et
    les normaliser reviendrait a raboter l'identite sportive du site ;
  - les six composants entre 1.04 et 1.15rem (17 a 18 px). Les faire converger
    demanderait un huitieme palier dont le seul interet serait de les absorber
    — exactement ce qu'un design system ne doit pas faire. Ils sont documentes
    comme exceptions intentionnelles, a reevaluer plus tard ;
  - les clamp(), qui relevent d'un lot separe.
"""
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(RACINE, 'style.css')
SEUIL = 4.0

ECHELLE = [('2xs', 0.66), ('xs', 0.72), ('sm', 0.80), ('md', 0.87),
           ('base', 0.95), ('lg', 1.00), ('2xl', 1.20)]
PAR_NOM = dict(ECHELLE)


def masque(css):
    out = list(css)
    for m in re.finditer(r'/\*.*?\*/', css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def poser_tokens():
    css = io.open(CSS, encoding='utf-8').read()
    if '--text-base' in css:
        print(u"  les tokens sont deja poses")
        return 0
    ancre = '  --blanc:#FFFFFF;'
    bloc = [ancre, '',
            '  /* --- L\'echelle de texte -----------------------------------------------',
            '     Sept paliers, tires des masses d\'usage mesurees dans le navigateur sur',
            '     762 elements porteurs de texte — pas d\'un ratio theorique. Il y avait',
            '     34 tailles rendues entre 10 et 20 px, dont trois dans un tiers de pixel',
            '     (13,1 / 13,3 / 13,4). Aucune n\'etait un choix : elles s\'etaient',
            '     accumulees.',
            '',
            '     --text-md vaut .87 et non .86 : ce demi-pas absorbe les 16 declarations',
            '     de .9rem, l\'une des tailles les plus employees, pour 0,2 point d\'ecart',
            '     maximal en plus.',
            '',
            '     NE SONT PAS DANS L\'ECHELLE, et c\'est voulu :',
            '       - la bande display (scores, numeros, hero, titres, mot de fond) ;',
            '       - six composants entre 17 et 18 px, qu\'un huitieme palier n\'aurait',
            '         servi qu\'a absorber. Exceptions assumees, a reevaluer plus tard.',
            '     --------------------------------------------------------------------- */']
    for nom, v in ECHELLE:
        bloc.append('  --text-%s:%grem;' % (nom, v))
    css = css.replace(ancre, '\n'.join(bloc), 1)
    io.open(CSS, 'w', encoding='utf-8', newline='\n').write(css)
    print(u"  7 tokens poses dans :root")
    return 0


def migrer(noms, essai):
    css = io.open(CSS, encoding='utf-8').read()
    m_css = masque(css)
    cibles = {n: PAR_NOM[n] for n in noms}
    faits, ignores = [], []
    for m in reversed(list(re.finditer(r'font-size\s*:\s*([\d.]+)rem(\s*!important)?', m_css))):
        v = float(m.group(1))
        if v > 1.25:
            continue
        nom, a = min(ECHELLE, key=lambda x: abs(x[1] - v))
        if nom not in cibles:
            continue
        ec = abs(v - a) / a * 100
        if ec > SEUIL:
            ignores.append((v, ec))
            continue
        imp = m.group(2) or ''
        neuf = 'font-size:var(--text-%s)%s' % (nom, imp)
        css = css[:m.start()] + neuf + css[m.end():]
        faits.append((v, nom, ec))
    from collections import defaultdict
    par = defaultdict(list)
    for v, nom, ec in faits:
        par[nom].append((v, ec))
    print(u"  LOT : %s" % ", ".join(noms))
    for nom in noms:
        l = par.get(nom)
        if not l:
            continue
        print(u"    --text-%-5s (%.2frem)  %3d declarations, ecart max %.1f %%"
              % (nom, PAR_NOM[nom], len(l), max(e for _, e in l)))
    print(u"    %d declaration(s) migree(s)" % len(faits))
    if ignores:
        print(u"    %d laissee(s) en place (ecart > %.0f %%)" % (len(ignores), SEUIL))
    if essai:
        print(u"\n  (essai : rien n'a ete ecrit)")
        return 0
    io.open(CSS, 'w', encoding='utf-8', newline='\n').write(css)
    print(u"\n  style.css reecrit — lancer build-css.py puis bump-assets.py")
    return 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        raise SystemExit(__doc__)
    if args[0] == 'tokens':
        return poser_tokens()
    inconnus = [a for a in args if a not in PAR_NOM]
    if inconnus:
        raise SystemExit("!! palier(s) inconnu(s) : %s" % ", ".join(inconnus))
    return migrer(args, '--essai' in sys.argv)


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
