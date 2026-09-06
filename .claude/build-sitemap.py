# -*- coding: utf-8 -*-
"""Regenere sitemap.xml a partir des pages reellement publiees.

    python .claude/build-sitemap.py
    python .claude/build-sitemap.py --essai    montre le resultat, n'ecrit rien

Le sitemap etait tenu a la main. Cela tenait tant qu'il y avait onze pages
ecrites une fois pour toutes ; depuis que /matchs/ et /actualites/ sont
generes, une page ajoutee au JSON serait ajoutee au site mais pas au sitemap,
et personne ne s'en apercevrait.

Trois regles, pour qu'il ne mente jamais :

1. Une page n'entre dans le sitemap que si elle porte elle-meme un
   <link rel="canonical">. C'est la page qui declare son URL, pas ce script.
2. Une page en noindex est ecartee (404, hors-ligne).
3. lastmod vient de la derniere modification connue par git — et, a defaut,
   de la date du fichier. On n'ecrit pas une date de complaisance.
"""
import glob
import io
import os
import re
import subprocess
import sys
from datetime import datetime

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# changefreq / priority par famille d'URL, du plus specifique au plus general.
REGLES = (
    (re.compile(r'^https://mbc974\.com/$'), 'weekly', '1.0'),
    (re.compile(r'^https://mbc974\.com/adhesion\.html$'), 'weekly', '0.9'),
    (re.compile(r'^https://mbc974\.com/matchs/$'), 'weekly', '0.8'),
    (re.compile(r'^https://mbc974\.com/matchs/.+/$'), 'weekly', '0.6'),
    (re.compile(r'^https://mbc974\.com/actualites/$'), 'weekly', '0.7'),
    (re.compile(r'^https://mbc974\.com/actualites/.+/$'), 'monthly', '0.6'),
    (re.compile(r'^https://mbc974\.com/confidentialite/$'), 'yearly', '0.3'),
    (re.compile(r'^https://mbc974\.com/(soutenir-le-club|benevoles|sponsor-club-basket-reunion'
                r'|baby-basket-la-reunion)/$'), 'monthly', '0.7'),
    (re.compile(r'.*'), 'monthly', '0.8'),
)


def pages():
    fichiers = (sorted(glob.glob('*.html')) + sorted(glob.glob('*/index.html'))
                + sorted(glob.glob('*/*/index.html')))
    return [f for f in fichiers
            if not f.startswith('.') and 'worktrees' not in f.replace(os.sep, '/')
            and not f.startswith('print' + os.sep)]


def derniere_modif(chemin):
    """Date ISO de la derniere modification. git d'abord : le mtime d'un fichier
    change au moindre `git checkout`, la date du commit non."""
    try:
        r = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', chemin],
                           cwd=RACINE, capture_output=True, text=True, timeout=15)
        d = r.stdout.strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            # un fichier modifie depuis le dernier commit est plus recent que lui
            propre = subprocess.run(['git', 'status', '--porcelain', '--', chemin],
                                    cwd=RACINE, capture_output=True, text=True, timeout=15)
            if not propre.stdout.strip():
                return d
    except Exception:
        pass
    return datetime.fromtimestamp(os.path.getmtime(chemin)).strftime('%Y-%m-%d')


def main():
    essai = '--essai' in sys.argv
    os.chdir(RACINE)
    urls, ignorees = [], []
    for f in pages():
        html = io.open(f, encoding='utf-8').read()
        rob = re.search(r'name="robots"\s+content="([^"]*)"', html)
        if rob and 'noindex' in rob.group(1):
            ignorees.append((f, 'noindex'))
            continue
        can = re.search(r'rel="canonical"\s+href="([^"]+)"', html)
        if not can:
            ignorees.append((f, 'pas de canonical'))
            continue
        urls.append((can.group(1), derniere_modif(f)))

    vus = {}
    for u, d in urls:
        if u in vus:
            print('!! canonical en double : %s' % u)
        vus[u] = d

    lignes = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in sorted(vus, key=lambda x: (x.count('/'), x)):
        freq, prio = next((f, p) for r, f, p in REGLES if r.match(u))
        lignes += ['  <url>',
                   '    <loc>%s</loc>' % u,
                   '    <lastmod>%s</lastmod>' % vus[u],
                   '    <changefreq>%s</changefreq>' % freq,
                   '    <priority>%s</priority>' % prio,
                   '  </url>']
    lignes.append('</urlset>')
    xml = '\n'.join(lignes) + '\n'

    avant = io.open('sitemap.xml', encoding='utf-8').read() if os.path.exists('sitemap.xml') else ''
    if not essai:
        io.open('sitemap.xml', 'w', encoding='utf-8', newline='\n').write(xml)

    print('%d URL dans le sitemap' % len(vus))
    for f, r in ignorees:
        print('   ecartee : %-24s (%s)' % (f, r))
    if essai:
        print('\nessai : %s' % ('des ecarts' if xml != avant else 'sitemap.xml deja a jour'))
    else:
        print('sitemap.xml %s' % ('mis a jour' if xml != avant else 'etait deja a jour'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
