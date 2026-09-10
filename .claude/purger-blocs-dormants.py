# -*- coding: utf-8 -*-
"""Retrait de CSS devenue inatteignable, selecteur par selecteur.

    python .claude/purger-blocs-dormants.py dormants --essai
    python .claude/purger-blocs-dormants.py dormants
    python .claude/purger-blocs-dormants.py purge-finale --essai
    python .claude/purger-blocs-dormants.py purge-finale

LES DEUX LOTS
-------------
« dormants » (10/09) — .btn--roi, la variante bleue du bouton : aucun element
ne la porte, les seules occurrences etaient dans une copie perimee de
.claude/worktrees/. script.js la CHERCHAIT encore
(querySelectorAll('.btn--primary,.btn--roi')) — mais chercher n'est pas
porter, et la ligne est nettoyee ici aussi. Plus le bloc « SCOREBOARD »
(.sb*), dont aucune des 30 classes n'apparait nulle part.

« purge-finale » (10/09) — seize classes orphelines, plus les @media devenues
vides. Ce lot balaye aussi les 27 @media vides qui preexistaient : c'est le
dernier passage, plus rien ne viendra en creer d'autres.

LA REGLE QUI REND CE SCRIPT NON TRIVIAL
----------------------------------------
Un selecteur mort est rarement seul dans sa regle. Onze regles melangent les
deux vocabulaires :

    .sb__comp i,.sb__when i,.footer__place i,.footer__addr i,…
    .h2,.hero__h1,.lp-title,.sb__name,.keyfig__v
    .btn--primary:active,.btn--roi:active,.btn--ghost:active

Supprimer la regle entiere emporterait le pied de page, les grands titres et
l'etat actif des boutons. On retire donc les SELECTEURS morts de la liste, et
on ne supprime le bloc que si TOUS ses selecteurs sont morts.

DISTINGUER « CREEE PAR LE JS » DE « CHERCHEE PAR LE JS »
--------------------------------------------------------
Ce script ne purge que ce qui a ete verifie a la main. La lecon du 09/09/2026 :
.ccb et .lightbox__toolbar n'apparaissent dans AUCUN attribut class= du markup
et semblaient donc mortes — elles sont creees a l'execution
(b.className = 'ccb'). Les retirer aurait casse le bandeau RGPD et la
visionneuse. Une classe seulement CITEE dans un querySelector, elle, est bien
dormante. La nuance decide de tout ; elle n'est pas automatisable ici.
"""
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(RACINE, 'style.css')
JS = os.path.join(RACINE, 'script.js')

LOTS = {
    # 10/09/2026 — la variante bleue du bouton et le bloc SCOREBOARD.
    'dormants': [r'\.btn--roi\b', r'\.sb\b', r'\.sb__', r'\.sb--'],

    # 10/09/2026 — purge finale. Seize classes sans aucune trace : ni dans le
    # markup publie, ni dans les generateurs de markup (build-*, set-*), ni
    # dans script.js / consent.js.
    #
    # Deux precautions ont fait tomber la liste de 51 candidates a 16 :
    #   - verifier-classes.py --mortes listait 51 « regles sans usage ». 35
    #     etaient posees a l'execution (.ccb*, .lightbox__*, .is-*, .nx__cd-*,
    #     .spotglow*). Les retirer aurait casse le bandeau RGPD, la
    #     visionneuse, le compte a rebours et le halo de survol ;
    #   - .marquee apparaissait 8 fois dans « tous les .html »… et zero fois
    #     hors de .claude/worktrees/. Une copie perimee du depot n'est pas le
    #     site. Toujours exclure worktrees d'un comptage d'usage.
    #
    # Et ne JAMAIS chercher ces classes dans les instruments d'analyse
    # (inventaire-*, migrer-*, purger-*) : leurs docstrings les citent, ce qui
    # les ferait passer pour vivantes. Seuls build-* et set-* ecrivent du
    # markup.
    'purge-finale': [
        r'\.hero__badge\b', r'\.hero__badge-opt\b', r'\.hero__court\b',
        r'\.hero__creole\b', r'\.hero__fine\b', r'\.hero__meta\b',
        r'\.hero__panel\b', r'\.hero__lead\b',
        r'\.lp-aside\b', r'\.lp-aside__n\b', r'\.lp-below\b', r'\.lp-note\b',
        r'\.nav__sep\b', r'\.nx__body\b', r'\.pl-affiche\b', r'\.marquee\b',
    ],
}
MORT = None  # arme par main() selon le lot demande


def masque(css):
    out = list(css)
    for m in re.finditer(r'/\*.*?\*/', css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def purger(lot, essai):
    css = io.open(CSS, encoding='utf-8').read()
    mc = masque(css)

    edits, entiers, alleges = [], 0, 0
    for m in re.finditer(r'([^{}]+)\{', mc):
        brut = m.group(1)
        sel = re.sub(r'\s+', ' ', brut).strip()
        if not sel or sel.startswith('@') or not MORT.search(sel):
            continue
        parts = [p.strip() for p in sel.split(',') if p.strip()]
        vivants = [p for p in parts if not MORT.search(p)]
        # debut reel du selecteur (on saute l'espace laisse par la regle precedente)
        deb = m.start() + (len(brut) - len(brut.lstrip()))
        if vivants:
            edits.append((deb, m.start() + len(brut), ",".join(vivants)))
            alleges += 1
        else:
            fin = mc.find('}', m.end())
            if fin < 0:
                continue
            # on avale aussi le saut de ligne qui precede, pour ne pas laisser de trou
            d = deb
            while d > 0 and css[d - 1] in ' \t':
                d -= 1
            if d > 0 and css[d - 1] == '\n':
                d -= 1
            edits.append((d, fin + 1, ''))
            entiers += 1

    for a, b, r in sorted(edits, key=lambda x: -x[0]):
        css = css[:a] + r + css[b:]

    # Les @media vides ne sont PAS retirees ici, et c'est deliberé : la feuille
    # en comptait deja avant cette purge (« @media (min-width:981px){} » dans le
    # hero, par exemple). Les balayer dans ce lot melangerait deux sujets et
    # gonflerait le diff sans rapport avec le scoreboard. Elles sont sans effet
    # de rendu ; elles reviendront a la purge CSS finale.
    vides_avant = len(re.findall(r'@media[^{]*\{\s*\}', masque(
        io.open(CSS, encoding='utf-8').read())))
    vides_apres = len(re.findall(r'@media[^{]*\{\s*\}', masque(css)))

    print(u"  PURGE — lot « %s »" % lot)
    print(u"  %3d regle(s) supprimee(s) en entier" % entiers)
    print(u"  %3d regle(s) allegee(s) : seul le selecteur mort est retire" % alleges)
    if lot == 'purge-finale':
        # C'est le moment : plus rien ne viendra en creer d'autres.
        n = 1
        while n:
            css, n = re.subn(r'\n?[ \t]*@media[^{]*\{\s*\}', '', css)
        print(u"  @media vides : %d retiree(s)" % vides_apres)
    else:
        print(u"  @media vides : %d avant -> %d apres (dont %d creees ici) —"
              u" laissees a la purge finale"
              % (vides_avant, vides_apres, vides_apres - vides_avant))

    tj = False
    if lot == 'dormants':
        js = io.open(JS, encoding='utf-8').read()
        avant = js
        js = js.replace("'.btn--primary,.btn--roi'", "'.btn--primary'")
        tj = (js != avant)
        print(u"  script.js : %s" % (u"selecteur .btn--roi retire" if tj
                                     else u"!! .btn--roi INTROUVABLE (deja fait ?)"))

    if essai:
        print(u"\n  (essai : rien n'a ete ecrit)")
        return 0
    io.open(CSS, 'w', encoding='utf-8', newline='\n').write(css)
    if tj:
        io.open(JS, 'w', encoding='utf-8', newline='\n').write(js)
    print(u"\n  ecrit — lancer build-css.py puis bump-assets.py")
    return 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args or args[0] not in LOTS:
        raise SystemExit("!! lot attendu : %s" % " | ".join(sorted(LOTS)))
    global MORT
    MORT = re.compile('|'.join(LOTS[args[0]]))
    return purger(args[0], '--essai' in sys.argv)


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
