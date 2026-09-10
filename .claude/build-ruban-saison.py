# -*- coding: utf-8 -*-
u"""Le ruban de saison : les sept rencontres visibles d'un coup d'oeil.

    python .claude/build-ruban-saison.py --essai
    python .claude/build-ruban-saison.py

LE DEFAUT QU'IL CORRIGE
------------------------
La section s'appelle « Les matchs de la saison » et n'en montrait AUCUN. Le
09/09/2026, le repliage de l'accueil avait mis les sept lignes derriere un
accordeon — a raison : depliees, elles pesaient 2 600 px. Mais ce qui restait
a l'ecran etait un titre, un chapeau, une ligne « Voir tous les matchs de la
saison », un encart de reglement et une affiche. Une section qui promet des
matchs et n'en affiche pas se lit comme une section vide.

CE QU'IL FAIT
-------------
Il ecrit, entre le chapeau et l'accordeon, un ruban de sept vignettes : la
journee, l'ecusson de l'adversaire, son nom court, la date, et si la rencontre
se joue a domicile ou en deplacement. Une vignette = un lien vers la fiche de
la rencontre, celle qui porte deja le SportsEvent.

Le detail — horaire, lieu, postes benevoles — reste dans l'accordeon. Le ruban
ne le duplique pas : il donne la forme de la saison, l'accordeon donne la
fiche. Cout : environ 150 px, contre 2 600 pour tout deplier.

CE QU'IL NE FAIT PAS
--------------------
Decider quelle rencontre est « la prochaine ». Le site est statique : cette
question depend de l'heure a laquelle on ouvre la page, pas de l'heure a
laquelle on l'a generee. Chaque vignette publie donc data-debut / data-fin, et
c'est script.js qui pose « is-next » et « is-past » — exactement comme il le
fait deja sur les lignes de l'accordeon, avec le meme code et le meme fuseau.

SOURCE
------
data/matchs.json, et rien d'autre. Les noms courts, les ecusons, les slugs et
les horaires y sont deja ; les reecrire ici serait ouvrir une deuxieme verite.
"""
import datetime
import io
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(RACINE, 'data', 'matchs.json')
CIBLE = os.path.join(RACINE, 'index.html')
DEBUT = u'<!-- SAISON-RUBAN:DEBUT'
FIN = u'<!-- SAISON-RUBAN:FIN -->'

JOURS = [u'lun.', u'mar.', u'mer.', u'jeu.', u'ven.', u'sam.', u'dim.']
MOIS = [u'janv.', u'fevr.', u'mars', u'avril', u'mai', u'juin', u'juil.',
        u'aout', u'sept.', u'oct.', u'nov.', u'dec.']
MOIS_ACC = {u'fevr.': u'f\u00e9vr.', u'aout': u'ao\u00fbt', u'dec.': u'd\u00e9c.'}


def ech(t):
    return (t.replace(u'&', u'&amp;').replace(u'<', u'&lt;')
             .replace(u'>', u'&gt;').replace(u'"', u'&quot;'))


def instant(date, heure, minutes):
    """Le meme calcul que le generateur des lignes : l'heure de La Reunion est
    publiee en clair avec son decalage, jamais deduite cote client."""
    d = datetime.datetime.strptime(date, '%Y-%m-%d')
    h, m = [int(x) for x in heure.split(':')]
    deb = d.replace(hour=h, minute=m)
    fin = deb + datetime.timedelta(minutes=minutes)
    f = '%Y-%m-%dT%H:%M:00+04:00'
    return deb.strftime(f), fin.strftime(f)


def date_courte(date):
    d = datetime.datetime.strptime(date, '%Y-%m-%d')
    mois = MOIS[d.month - 1]
    return u'%s %d %s' % (JOURS[d.weekday()], d.day, MOIS_ACC.get(mois, mois))


def vignette(m):
    deb, fin = instant(m['date'], m['heure'], m.get('duree') or 120)
    dom = bool(m['domicile'])
    logo = m.get('logo')
    court = m.get('adversaireCourt') or m['adversaire']

    ecusson = u''
    if logo and os.path.exists(os.path.join(RACINE, 'assets/logos/clubs/%s.webp' % logo)):
        ecusson = (u'<span class="msn__crest" aria-hidden="true">'
                   u'<img src="/assets/logos/clubs/%s-144.webp" '
                   u'srcset="/assets/logos/clubs/%s-144.webp 144w, /assets/logos/clubs/%s.webp 288w" '
                   u'sizes="52px" alt="" width="288" height="288" '
                   u'loading="lazy" decoding="async"></span>' % (logo, logo, logo))
    else:
        # Pas d'ecusson dans le depot : on met le sigle plutot qu'un trou.
        ecusson = (u'<span class="msn__crest msn__crest--sigle" aria-hidden="true">%s</span>'
                   % ech(m.get('sigle') or court[:4].upper()))

    # Une rencontre jouee montre son score ; les autres montrent le camp.
    if m.get('statut') == 'joue' and m.get('score'):
        pied = u'<span class="msn__score">%s</span>' % ech(m['score'])
    else:
        pied = u'<span class="msn__ou">%s</span>' % (u'Domicile' if dom else u'Ext\u00e9rieur')

    return (
        u'      <li class="msn__i msn__i--%s" data-date="%s" data-debut="%s" data-fin="%s">\n'
        u'        <a class="msn__a" href="/matchs/%s/">\n'
        u'          <span class="msn__j">J%d</span>\n'
        u'          %s\n'
        u'          <span class="msn__opp">%s</span>\n'
        u'          <time class="msn__d" datetime="%s">%s</time>\n'
        u'          %s\n'
        u'          <span class="sr-only"> \u2014 voir la fiche de la rencontre</span>\n'
        u'        </a>\n'
        u'      </li>\n'
    ) % (u'dom' if dom else u'ext', m['date'], deb, fin,
         ech(m['slug']), m['journee'], ecusson, ech(court),
         deb[:16], date_courte(m['date']), pied)


def ruban(d):
    ms = sorted(d['matchs'], key=lambda m: m['date'])
    c = d.get('competition', {})
    titre = u'Les %d rencontres de la %s' % (
        len(ms), ech(c.get('phase') or u'phase 1').lower())
    return (
        u'%s \u2014 genere par .claude/build-ruban-saison.py, ne pas editer a la main -->\n'
        u'    <ol class="msn reveal" aria-label="%s">\n'
        u'%s'
        u'    </ol>\n'
        u'    %s'
    ) % (DEBUT, titre, u''.join(vignette(m) for m in ms), FIN)


def main():
    essai = '--essai' in sys.argv
    d = json.load(io.open(SOURCE, encoding='utf-8'))
    html = io.open(CIBLE, encoding='utf-8').read()
    i = html.find(DEBUT)
    j = html.find(FIN)
    if i < 0 or j < 0:
        print(u'  !! marqueurs SAISON-RUBAN absents de index.html')
        return 1
    neuf = html[:i] + ruban(d) + html[j + len(FIN):]
    n = len(d['matchs'])
    if neuf == html:
        print(u'  ruban de saison : deja a jour (%d rencontres)' % n)
        return 0
    if essai:
        print(u'  essai : le ruban de saison changerait (%d rencontres)' % n)
        return 0
    io.open(CIBLE, 'w', encoding='utf-8', newline='\n').write(neuf)
    print(u'  ruban de saison ecrit : %d rencontres \u2014 lancer bump-assets.py' % n)
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
