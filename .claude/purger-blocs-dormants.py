# -*- coding: utf-8 -*-
"""Retrait d'un bloc de composant devenu inutilisable, selecteur par selecteur.

    python .claude/purger-blocs-dormants.py --essai
    python .claude/purger-blocs-dormants.py

CE QU'IL RETIRE, ET POURQUOI CES DEUX-LA
-----------------------------------------
  .btn--roi   la variante bleue du bouton. Aucun element ne la porte : les
              seules occurrences trouvees etaient dans une copie perimee de
              .claude/worktrees/. script.js la CHERCHE encore
              (querySelectorAll('.btn--primary,.btn--roi')) mais chercher
              n'est pas porter — la ligne est nettoyee ici aussi.

  .sb*        le bloc « SCOREBOARD ». Aucune de ses 30 classes n'apparait
              dans le markup, ni dans les generateurs, ni dans le JS.

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

MORT = re.compile(r'\.btn--roi\b|\.sb\b|\.sb__|\.sb--')


def masque(css):
    out = list(css)
    for m in re.finditer(r'/\*.*?\*/', css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def purger(essai):
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

    print(u"  PURGE — .btn--roi et le bloc SCOREBOARD")
    print(u"  %3d regle(s) supprimee(s) en entier" % entiers)
    print(u"  %3d regle(s) allegee(s) : seul le selecteur mort est retire" % alleges)
    print(u"  @media vides : %d avant -> %d apres (dont %d creees ici) — laissees"
          u" a la purge finale" % (vides_avant, vides_apres, vides_apres - vides_avant))

    js = io.open(JS, encoding='utf-8').read()
    avant = js
    js = js.replace("'.btn--primary,.btn--roi'", "'.btn--primary'")
    tj = (js != avant)
    print(u"  script.js : %s" % (u"selecteur .btn--roi retire" if tj
                                 else u"!! selecteur .btn--roi INTROUVABLE, a verifier"))

    if essai:
        print(u"\n  (essai : rien n'a ete ecrit)")
        return 0
    io.open(CSS, 'w', encoding='utf-8', newline='\n').write(css)
    if tj:
        io.open(JS, 'w', encoding='utf-8', newline='\n').write(js)
    print(u"\n  ecrit — lancer build-css.py puis bump-assets.py")
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(purger('--essai' in sys.argv))
