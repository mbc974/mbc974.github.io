# -*- coding: utf-8 -*-
"""Verifie que tous les liens et toutes les ressources internes existent.

    python .claude/verifier-liens.py

Ce que le script controle, page par page :

  * href / src / srcset / poster / content d'og:image qui pointent vers le site
    lui-meme resolvent bien vers un fichier present ;
  * les ancres #machin existent dans la page visee (y compris quand la cible
    est une AUTRE page du site) ;
  * aucune page publiee n'est orpheline — c'est-a-dire qu'au moins une autre
    page y mene. Une page qu'aucun lien n'atteint n'est vue ni par un visiteur
    ni par un robot, meme si elle est dans le sitemap.

Il ne sort PAS sur le reseau : les liens externes sont listes, pas testes.
"""
import glob
import io
import os
import re
import sys
from collections import defaultdict

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://mbc974.com'

RES = re.compile(r'(?:href|src|poster)="([^"#][^"]*)"')
SRCSET = re.compile(r'srcset="([^"]+)"')
ANCRES = re.compile(r'\sid="([^"]+)"')
COMMENTAIRE = re.compile(r'<!--.*?-->', re.S)


def pages():
    f = (sorted(glob.glob('*.html')) + sorted(glob.glob('*/index.html'))
         + sorted(glob.glob('*/*/index.html')))
    # Toujours en barres obliques : sous Windows glob rend « matchs\index.html »
    # alors que les URL resolvent vers « matchs/index.html », et les deux
    # ensembles ne se rencontreraient jamais.
    return [p.replace(os.sep, '/') for p in f
            if not p.startswith('.') and 'worktrees' not in p.replace(os.sep, '/')]


def cible(page, url):
    """Chemin disque vise par une URL, ou None si elle sort du site."""
    u = url.split('#')[0].split('?')[0]
    if not u:
        return None
    if u.startswith(('mailto:', 'tel:', 'javascript:', 'data:')):
        return None
    if u.startswith(('http://', 'https://', '//')):
        if not u.startswith(SITE + '/'):
            return None
        u = u[len(SITE):]
    if u.startswith('/'):
        chemin = u.lstrip('/')
    else:
        chemin = os.path.normpath(os.path.join(os.path.dirname(page), u)).replace(os.sep, '/')
        # normpath SUPPRIME le slash final : « confidentialite/ » devient
        # « confidentialite ». Sans cette restitution, index.html n'etait jamais
        # ajoute pour un lien RELATIF vers un dossier : le lien etait signale
        # casse a tort, et surtout les liens relatifs de ce type n'etaient
        # verifies qu'au niveau du dossier, jamais de la page.
        if u.endswith('/') and not chemin.endswith('/'):
            chemin += '/'
    if chemin == '' or chemin.endswith('/'):
        chemin += 'index.html'
    return chemin


def main():
    os.chdir(RACINE)
    liste = pages()
    connues = set(liste)
    ancres = {}
    for p in liste:
        ancres[p] = set(ANCRES.findall(COMMENTAIRE.sub('', io.open(p, encoding='utf-8').read())))

    casses, ancres_ko = [], []
    entrants = defaultdict(set)

    for p in liste:
        html = COMMENTAIRE.sub('', io.open(p, encoding='utf-8').read())
        urls = list(RES.findall(html))
        for ss in SRCSET.findall(html):
            urls += [m.split()[0] for m in ss.split(',') if m.strip()]
        # les liens vers une ancre : href="#x" ou href="/page/#x"
        for u in re.findall(r'href="([^"]*#[^"]*)"', html):
            base, _, anc = u.partition('#')
            if not anc:
                continue
            c = p if base in ('', './') else cible(p, base)
            if c is None:
                continue
            if c not in connues:
                casses.append((p, u, c))
            elif anc not in ancres[c]:
                ancres_ko.append((p, u, c))
            elif c != p:
                entrants[c].add(p)

        for u in urls:
            c = cible(p, u)
            if c is None:
                continue
            if not os.path.exists(c):
                casses.append((p, u, c))
            elif c.endswith('.html') and c != p:
                entrants[c].add(p)

    orphelines = [p for p in liste
                  if p not in entrants and p not in ('index.html', '404.html', 'offline.html')]

    print('%d page(s) analysee(s)' % len(liste))
    if casses:
        print('\nLIENS OU RESSOURCES INTROUVABLES (%d) :' % len(casses))
        for p, u, c in casses[:60]:
            print('  %-46s -> %s' % (p, u))
    if ancres_ko:
        print('\nANCRES INEXISTANTES (%d) :' % len(ancres_ko))
        for p, u, c in ancres_ko[:40]:
            print('  %-46s -> %s  (absente de %s)' % (p, u, c))
    if orphelines:
        print('\nPAGES ORPHELINES — aucun lien du site n\'y mene (%d) :' % len(orphelines))
        for p in orphelines:
            print('  ' + p)
    if not casses and not ancres_ko and not orphelines:
        print('\n  tout resout : 0 lien casse, 0 ancre absente, 0 page orpheline')
    return 1 if (casses or ancres_ko or orphelines) else 0


if __name__ == '__main__':
    sys.exit(main())
