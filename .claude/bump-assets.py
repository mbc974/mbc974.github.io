# -*- coding: utf-8 -*-
"""Réaligne le ?v= de style.css / script.js sur le contenu réel des fichiers.

Pourquoi : le site est sans build. Le ?v= était donc saisi à la main, et il a
été oublié après plusieurs modifications de style.css. Résultat : navigateurs
et service worker continuaient à servir l'ancienne feuille, donc du HTML neuf
avec une mise en page périmée.

Ici la version est un hachage du fichier : elle change si et seulement si le
contenu change, et on ne peut plus l'oublier.

Usage, depuis la racine du dépôt, avant de committer :
    python .claude/bump-assets.py            # applique
    python .claude/bump-assets.py --check    # ne modifie rien, sort en 1 si périmé
"""
import glob
import hashlib
import io
import os
import re
import sys

ASSETS = ('style.css', 'script.js')


def digest(path):
    return hashlib.sha1(open(path, 'rb').read()).hexdigest()[:8]


def targets():
    files = ['index.html', 'adhesion.html', 'sw.js']
    files += sorted(glob.glob('*/index.html'))
    return [f for f in files if os.path.exists(f)]


def main():
    check = '--check' in sys.argv
    if not all(os.path.exists(a) for a in ASSETS):
        print('!! lancer le script depuis la racine du depot')
        return 1

    versions = {a: digest(a) for a in ASSETS}
    for a, v in versions.items():
        print('%-12s -> v=%s' % (a, v))

    stale, changed = [], []
    for f in targets():
        src = io.open(f, encoding='utf-8').read()
        out = src
        for asset, ver in versions.items():
            pattern = re.escape(asset) + r'\?v=[A-Za-z0-9._-]+'
            out = re.sub(pattern, '%s?v=%s' % (asset, ver), out)
        # nom du cache du service worker : suit les deux hachages
        out = re.sub(r"const CACHE = '[^']*';",
                     "const CACHE = 'mbc-%s-%s';" % (versions['style.css'], versions['script.js']),
                     out)
        if out != src:
            (stale if check else changed).append(f)
            if not check:
                io.open(f, 'w', encoding='utf-8', newline='\n').write(out)

    if check:
        if stale:
            print('\n!! versions perimees dans : %s' % ', '.join(stale))
            print('   corriger avec : python .claude/bump-assets.py')
            return 1
        print('\nversions a jour.')
        return 0

    print('\n%d fichier(s) mis a jour : %s' % (len(changed), ', '.join(changed) or 'aucun'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
