# -*- coding: utf-8 -*-
"""Detecte les classes utilisees dans le HTML qui n'ont AUCUNE regle CSS.

Pourquoi ce script existe
-------------------------
Le 2026-09-04, pendant la refonte premium, index.html a ete publie avec 57
classes sans aucune regle dans style.css : tout le scoreboard (.sb__*), la
bande de chiffres cles (.keyfig*) et le nouveau hero (.hero__h1 rendu a la
taille par defaut du navigateur). Pendant cette fenetre, les DEUX garde-fous
existants etaient au vert :
  - bump-assets.py --check compare des hachages de fichiers : style.css
    n'ayant pas change, il repondait « versions a jour » ;
  - verifier-jsonld.py ne regarde que le JSON-LD.
Aucun outil du depot ne regardait le lien entre le vocabulaire du HTML et
celui de la CSS. C'est exactement le mode de panne d'une refonte visuelle :
on ecrit le markup, on oublie une regle, et la page part nue en production.

Il signale aussi le sens inverse (classes stylees mais employees nulle part)
en mode --mortes : utile apres avoir retire des sections, pour savoir quels
blocs CSS sont devenus du poids mort.

Usage, depuis la racine du depot :
    python .claude/verifier-classes.py            # classes sans regle
    python .claude/verifier-classes.py --mortes   # + regles sans usage
    python .claude/verifier-classes.py --check    # sort en 1 si trou detecte

ATTENTION : ne jamais parcourir la racine en recursif. .claude/worktrees/
contient une copie complete du site, git-ignoree ; elle ferait croire que des
classes supprimees sont encore vivantes.
"""
import glob
import io
import os
import re
import sys

CSS = 'style.css'

# Classes posees uniquement par JavaScript : elles n'apparaissent dans aucun
# attribut class= du HTML, ce qui est normal. Les declarer ici evite un bruit
# permanent en mode --mortes.
POSEES_PAR_JS = {
    'in', 'is-on', 'is-open', 'is-past', 'is-next', 'is-loaded', 'is-empty',
    'is-visible', 'is-paused', 'is-flat', 'is-fs', 'is-dragging', 'is-complet',
    'scrolled', 'hide', 'open', 'show', 'roster-ready', 'img-fallback',
    'cine-fs', 'cine-fs__close', 'cine-fs-lock', 'nav-open',
}


def pages():
    """Les fichiers HTML reellement publies, et eux seuls."""
    fichiers = sorted(glob.glob('*.html')) + sorted(glob.glob('*/index.html'))
    return [f for f in fichiers if not f.startswith('.') and 'worktrees' not in f]


def classes_du_html():
    trouvees = {}
    for f in pages():
        html = io.open(f, encoding='utf-8').read()
        # on ignore les commentaires : ils contiennent des exemples de markup
        html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
        for attr in re.findall(r'class="([^"]*)"', html):
            for c in attr.split():
                trouvees.setdefault(c, set()).add(f)
    return trouvees


def classes_de_la_css(fichier_html=None):
    """Les classes stylees : style.css, plus le <style> en ligne de la page.

    404.html et offline.html ne chargent PAS style.css — elles embarquent leur
    propre feuille. Sans cette lecture, elles remontaient quatre faux positifs.
    """
    css = io.open(CSS, encoding='utf-8').read()
    if fichier_html:
        html = io.open(fichier_html, encoding='utf-8').read()
        css += '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', html, flags=re.S))
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    return set(re.findall(r'\.(-?[A-Za-z_][\w-]*)', css))


def main():
    if not os.path.exists(CSS):
        print('style.css introuvable — lancer depuis la racine du depot')
        return 2

    html = classes_du_html()
    css = classes_de_la_css()

    # une classe n'est un trou que si elle manque AUSSI dans le <style> en
    # ligne de chacune des pages ou elle apparait
    sans_regle = []
    for c in sorted(html):
        if c in css:
            continue
        if all(c in classes_de_la_css(f) for f in html[c]):
            continue
        sans_regle.append(c)

    if sans_regle:
        print('CLASSES SANS AUCUNE REGLE CSS (%d) :' % len(sans_regle))
        for c in sans_regle:
            ou = ', '.join(sorted(html[c])[:3])
            reste = len(html[c]) - 3
            if reste > 0:
                ou += ' (+%d)' % reste
            print('  .%-28s %s' % (c, ou))
    else:
        print('OK — chaque classe du HTML a au moins une regle dans style.css')

    if '--mortes' in sys.argv:
        mortes = sorted(c for c in css if c not in html and c not in POSEES_PAR_JS)
        print('\nREGLES SANS AUCUN USAGE DANS LE HTML (%d) :' % len(mortes))
        print('  ' + ' '.join('.' + c for c in mortes))
        print('\n  (verifier une par une avant suppression : certaines peuvent'
              '\n   etre posees par JS et avoir echappe a la liste POSEES_PAR_JS)')

    if '--check' in sys.argv and sans_regle:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
