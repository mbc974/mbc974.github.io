# -*- coding: utf-8 -*-
"""Active ou desactive la mesure d'audience sur TOUTES les pages du site.

    python .claude/set-analytics.py --etat   ou ce qui existe, page par page
    python .claude/set-analytics.py --on     active Plausible partout
    python .claude/set-analytics.py --off    desactive partout (retour au commentaire)

POURQUOI CE SCRIPT EXISTE
-------------------------
La balise etait posee, en commentaire, dans 11 pages ecrites a la main. Les
12 pages generees (les 7 fiches de match, /matchs/, /actualites/ et les 3
articles) n'en avaient AUCUNE. Activer la mesure a la main revenait donc a
instrumenter le site a moitie sans s'en apercevoir — et precisement, les
pages de match sont les seules a porter un lien .ics, dont l'evenement
« Ajout agenda » n'aurait jamais rien compte.

Depuis, le bloc est aussi emis par .claude/build-matchs.py (dont
build-actus.py reprend le gabarit). Ce script-ci ne fait donc que basculer
l'etat, d'un seul geste, sur l'ensemble des pages — generees comprises.

CE QU'IL RESTE A FAIRE A LA MAIN, UNE FOIS
------------------------------------------
Creer le site « mbc974.com » sur https://plausible.io (ou une instance
auto-hebergee). Sans cela la balise chargerait un script qui refuse les
donnees d'un domaine inconnu. Le nom de domaine est le SEUL parametre, et
il est deja ecrit ci-dessous : aucune cle secrete n'est en jeu, Plausible
n'en utilise pas cote client.

Apres --on, penser a mettre a jour confidentialite/index.html : la page
declare aujourd'hui qu'aucune mesure d'audience n'est active.
"""
import glob
import io
import os
import re
import sys

DOMAINE = 'mbc974.com'
BALISE = ('<script defer data-domain="%s" '
          'src="https://plausible.io/js/script.outbound-links.file-downloads.js">'
          '</script>') % DOMAINE

OUVERTURE = "<!-- ANALYTICS (à activer)"
FERMETURE = "-->"


def pages():
    f = ['index.html', 'adhesion.html', '404.html', 'offline.html']
    f += sorted(glob.glob('*/index.html'))
    f += sorted(glob.glob('*/*/index.html'))
    return [p for p in f if os.path.exists(p)]


def etat(s):
    """'actif', 'commente' ou 'absent' pour le contenu d'une page.

    On ne cherche pas l'en-tete du commentaire dans une fenetre de taille
    fixe avant la balise : le bloc redige a la main fait plus de 400
    caracteres, et la page d'accueil se declarait alors « actif » a tort.
    On regarde donc, en remontant, si le dernier marqueur rencontre est une
    ouverture ou une fermeture de commentaire."""
    i = s.find(BALISE)
    if i < 0:
        return 'absent'
    avant = s[:i]
    return 'commente' if avant.rfind('<!--') > avant.rfind('-->') else 'actif'


def _recommenter(s):
    """Remet la balise dans son bloc de commentaire."""
    bloc = (u"<!-- ANALYTICS (à activer) : mesure d'audience légère, "
            u"sans cookies ni bannière RGPD.\n"
            u"     Activer partout : python .claude/set-analytics.py --on\n"
            u"     Les evenements personnalises sont deja prepares dans script.js.\n"
            u"%s\n-->\n") % BALISE
    return s.replace(BALISE + "\n", bloc, 1)


def decommenter(s):
    """Sort la balise de son bloc de commentaire, en gardant le bloc autour."""
    if etat(s) != 'commente':
        return s
    # le commentaire va de OUVERTURE au premier --> qui suit la balise
    i = s.find(OUVERTURE)
    if i < 0:
        return s
    j = s.find(FERMETURE, s.find(BALISE, i))
    if j < 0:
        return s
    return s[:i] + BALISE + "\n" + s[j + len(FERMETURE):].lstrip('\n')


def main():
    if not os.path.exists('index.html'):
        print('!! lancer depuis la racine du depot')
        return 1
    mode = ('--on' in sys.argv and 'on') or ('--off' in sys.argv and 'off') or 'etat'

    compte = {'actif': 0, 'commente': 0, 'absent': 0}
    changes = []
    for p in pages():
        s = io.open(p, encoding='utf-8').read()
        avant = etat(s)
        if mode == 'on':
            s2 = decommenter(s)
        elif mode == 'off':
            s2 = _recommenter(s) if avant == 'actif' else s
        else:
            s2 = s
        apres = etat(s2)
        compte[apres] = compte.get(apres, 0) + 1
        if s2 != s:
            io.open(p, 'w', encoding='utf-8', newline='').write(s2)
            changes.append('%s : %s -> %s' % (p, avant, apres))
        elif mode == 'etat':
            print('  %-52s %s' % (p, avant))

    if mode == 'etat':
        print('\n  actif %d   commente %d   absent %d'
              % (compte['actif'], compte['commente'], compte['absent']))
        if compte['absent']:
            print('  !! des pages n\'ont AUCUNE balise : relancer les generateurs')
        return 0

    for c in changes:
        print('  ' + c)
    print('\n  %d page(s) modifiee(s) — actif %d, commente %d, absent %d'
          % (len(changes), compte['actif'], compte['commente'], compte['absent']))
    if mode == 'on':
        print('\n  RESTE A FAIRE : creer le site « %s » sur https://plausible.io,' % DOMAINE)
        print('  puis mettre a jour confidentialite/index.html (elle dit')
        print('  aujourd\'hui qu\'aucune mesure d\'audience n\'est active).')
    print('\n  puis : python .claude/bump-assets.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
