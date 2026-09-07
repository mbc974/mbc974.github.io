# -*- coding: utf-8 -*-
"""Ecrit style.min.css a partir de style.css, en retirant les commentaires.

POURQUOI
--------
style.css est la memoire technique du site : chaque bloc de version y explique
ce qui a ete tente, ce qui a echoue et pourquoi la regle est ecrite ainsi. Ces
commentaires font 230 Ko sur 512, soit 45 % du fichier — et 88,6 Ko sur les
139 Ko une fois compresse. Or c'est la SEULE ressource bloquante du rendu :
tant qu'elle n'est pas arrivee, le navigateur n'affiche rien.

Un visiteur n'a aucun usage de ces commentaires. On garde donc style.css tel
quel — c'est lui qu'on edite, c'est lui que lisent les garde-fous — et on
publie a cote sa version depouillee.

CE QUE CE SCRIPT NE FAIT PAS
----------------------------
Il ne renomme rien, ne reordonne rien, ne raccourcit aucune valeur, ne fusionne
aucun selecteur. Il retire les commentaires et les lignes vides, et c'est tout.
La raison est simple : ce qu'on ne touche pas ne peut pas casser. Le gain vient
du volume de commentaires, pas d'une minification agressive.

Le decoupage est fait au caractere, en suivant l'etat du parseur (dans une
chaine simple, dans une chaine double, dans un commentaire), pour ne jamais
confondre un « /* » ecrit a l'interieur d'un content:"…" ou d'une url() avec
une ouverture de commentaire.

VERIFICATION
------------
    python .claude/build-css.py --check
sort en 1 si style.min.css ne correspond plus a style.css. A lancer avant toute
publication, au meme titre que bump-assets.py --check.

L'equivalence a ete prouvee une fois pour toutes en comparant, dans un
navigateur, la liste des regles CSSOM des deux fichiers : meme nombre de
regles, meme cssText pour chacune. Voir le message de commit.

ORDRE DANS LA CHAINE
--------------------
    build-matchs.py -> build-actus.py -> build-hero.py -> build-sitemap.py
    -> build-css.py -> bump-assets.py      (bump-assets TOUJOURS en dernier)
"""
import io
import os
import sys

SOURCE = 'style.css'
CIBLE = 'style.min.css'

ENTETE = (u'/* style.min.css - genere par .claude/build-css.py depuis style.css.\n'
          u'   NE PAS EDITER : toute modification faite ici sera ecrasee.\n'
          u'   La feuille commentee, qui est la source, est style.css. */\n')


def depouiller(src):
    """Retire les commentaires CSS, en respectant les chaines de caracteres."""
    out = []
    i, n = 0, len(src)
    etat = 'css'          # css | simple | double | commentaire
    while i < n:
        c = src[i]
        if etat == 'css':
            if c == '/' and i + 1 < n and src[i + 1] == '*':
                etat = 'commentaire'
                i += 2
                continue
            if c == "'":
                etat = 'simple'
            elif c == '"':
                etat = 'double'
            out.append(c)
            i += 1
        elif etat == 'commentaire':
            if c == '*' and i + 1 < n and src[i + 1] == '/':
                etat = 'css'
                i += 2
                # Un commentaire separait souvent deux regles : on laisse la
                # respiration au collapse de lignes vides ci-dessous.
                continue
            i += 1
        else:  # dans une chaine
            if c == '\\' and i + 1 < n:
                out.append(c)
                out.append(src[i + 1])
                i += 2
                continue
            if (etat == 'simple' and c == "'") or (etat == 'double' and c == '"'):
                etat = 'css'
            out.append(c)
            i += 1
    if etat != 'css':
        raise SystemExit('!! style.css se termine dans un etat %s : '
                         'chaine ou commentaire non ferme' % etat)
    return u''.join(out)


def compacter(s):
    """Supprime les lignes devenues vides et les espaces de fin de ligne."""
    lignes = [l.rstrip() for l in s.split('\n')]
    return '\n'.join(l for l in lignes if l.strip()) + '\n'


def produire():
    src = io.open(SOURCE, encoding='utf-8').read()
    return ENTETE + compacter(depouiller(src))


def main():
    if not os.path.exists(SOURCE):
        print('!! lancer le script depuis la racine du depot')
        return 1
    voulu = produire()
    actuel = io.open(CIBLE, encoding='utf-8').read() if os.path.exists(CIBLE) else None

    if '--check' in sys.argv:
        if actuel != voulu:
            print('!! %s ne correspond plus a %s' % (CIBLE, SOURCE))
            print('   corriger avec : python .claude/build-css.py')
            return 1
        print('%s est a jour.' % CIBLE)
        return 0

    io.open(CIBLE, 'w', encoding='utf-8', newline='\n').write(voulu)
    src = io.open(SOURCE, encoding='utf-8').read()
    a, b = len(src.encode('utf-8')), len(voulu.encode('utf-8'))
    try:
        import gzip
        ga = len(gzip.compress(src.encode('utf-8'), 9))
        gb = len(gzip.compress(voulu.encode('utf-8'), 9))
        gz = '   gzip %6d -> %6d o  (-%d o, -%.0f %%)' % (ga, gb, ga - gb,
                                                          100.0 * (ga - gb) / ga)
    except Exception:
        gz = ''
    print('%s ecrit.' % CIBLE)
    print('   brut %7d -> %6d o  (-%d o, -%.0f %%)' % (a, b, a - b, 100.0 * (a - b) / a))
    print(gz)
    return 0


if __name__ == '__main__':
    sys.exit(main())
