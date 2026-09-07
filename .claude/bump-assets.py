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
import importlib.util
import io
import os
import re
import sys

# La feuille SERVIE est style.min.css : c'est son hachage qui doit piloter le
# ?v= des pages et le nom du cache. style.css reste la source qu'on edite, mais
# aucune page ne la demande.
ASSETS = ('style.min.css', 'script.js', 'consent.js')


def digest(path):
    return hashlib.sha1(open(path, 'rb').read()).hexdigest()[:8]


def targets():
    # Toutes les pages de la racine, pas seulement les deux nommees : 404.html
    # et offline.html appellent elles aussi consent.js et style.css, et elles
    # etaient les seules a ne jamais recevoir de version. Les fichiers de
    # travail « _*.html » restent hors du lot (voir .gitignore).
    files = sorted(f for f in glob.glob('*.html') if not f.startswith('_'))
    files.append('sw.js')
    files += sorted(glob.glob('*/index.html'))
    files += sorted(glob.glob('*/*/index.html'))
    return [f for f in files if os.path.exists(f)]


def css_a_jour():
    """style.min.css est-il bien le depouillement de style.css d'aujourd'hui ?

    C'est LE piege de la chaine : si l'on edite style.css sans relancer
    build-css.py, le hachage de style.min.css ne bouge pas, les pages gardent
    leur ?v= et le site continue de servir l'ancienne feuille — sans qu'aucun
    voyant ne passe au rouge. On ferme la boucle ici, dans le script que l'on
    lance de toute facon en dernier.
    """
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build-css.py')
    spec = importlib.util.spec_from_file_location('build_css', chemin)
    bc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bc)
    actuel = io.open(bc.CIBLE, encoding='utf-8').read() if os.path.exists(bc.CIBLE) else None
    return actuel == bc.produire()


def main():
    check = '--check' in sys.argv
    if not all(os.path.exists(a) for a in ASSETS):
        print('!! lancer le script depuis la racine du depot')
        return 1
    if not css_a_jour():
        print('!! style.min.css ne correspond plus a style.css')
        print('   lancer d abord : python .claude/build-css.py')
        return 1

    versions = {a: digest(a) for a in ASSETS}
    for a, v in versions.items():
        print('%-12s -> v=%s' % (a, v))

    stale, changed = [], []
    for f in targets():
        src = io.open(f, encoding='utf-8').read()
        out = src
        for asset, ver in versions.items():
            # a) on rafraichit les references qui portent deja un ?v=
            pattern = re.escape(asset) + r'\?v=[A-Za-z0-9._-]+'
            out = re.sub(pattern, '%s?v=%s' % (asset, ver), out)
            # b) on AJOUTE le ?v= aux references d'attribut qui n'en ont pas.
            #    C'etait le cas de /consent.js sur les 25 pages : la boucle (a)
            #    ne voyait rien a rafraichir, le fichier partait donc sans
            #    version. On ancre sur src="/href=" pour ne pas toucher les
            #    commentaires qui citent le nom du fichier en prose.
            out = re.sub(r'((?:src|href)="/?' + re.escape(asset) + r')(")',
                         r'\1?v=' + ver + r'\2', out)
        # nom du cache du service worker : suit les deux hachages
        out = re.sub(r"const CACHE = '[^']*';",
                     "const CACHE = 'mbc-%s-%s-%s';" % (versions['style.min.css'],
                                                        versions['script.js'],
                                                        versions['consent.js']),
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
