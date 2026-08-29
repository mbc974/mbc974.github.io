# -*- coding: utf-8 -*-
"""Verifie les donnees structurees du site avant deploiement.

    python .claude/verifier-jsonld.py

Ce que le script controle, page par page :

  * chaque bloc <script type="application/ld+json"> est du JSON valide ;
  * chaque URL d'image / de logo / de fichier pointant sur mbc974.com
    correspond a un fichier reellement present dans le depot ;
  * chaque URL interne en #ancre correspond a un id existant dans la page ;
  * les SportsEvent portent bien les proprietes recommandees par Google
    (description, endDate, image, location.address, offers, organizer.url,
    performer, url) — ce sont exactement celles que Search Console remonte ;
  * aucun id HTML n'est declare deux fois (une ancre dupliquee casse les
    URL canoniques des evenements) ;
  * une seule entite decrit le club (@id https://mbc974.com/#club).

Il ne remplace pas le Rich Results Test de Google, qui seul fait foi : il
attrape ce qui peut l'etre hors ligne, c'est-a-dire l'essentiel des regressions.
"""
import glob
import io
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://mbc974.com/'

BLOC = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
ID_HTML = re.compile(r'\sid="([^"]+)"')

# Les proprietes que Google liste comme « recommandees » pour un Event. Leur
# absence n'est pas une erreur mais un avertissement dans Search Console — et
# c'est ce rapport d'avertissements que ce script sert a garder vide.
RECOMMANDEES = ['description', 'endDate', 'eventAttendanceMode', 'eventStatus',
                'image', 'location', 'offers', 'organizer', 'performer', 'url']


def pages():
    os.chdir(RACINE)
    trouvees = sorted(glob.glob('*.html') + glob.glob('*/index.html'))
    return [p for p in trouvees if not p.startswith('print/')]


def noeuds(doc):
    """Aplatit un document JSON-LD en liste de noeuds typables."""
    if isinstance(doc, list):
        for d in doc:
            for n in noeuds(d):
                yield n
    elif isinstance(doc, dict):
        if '@graph' in doc:
            for d in doc['@graph']:
                for n in noeuds(d):
                    yield n
        else:
            yield doc


def urls(obj):
    """Toutes les chaines qui ressemblent a une URL, en profondeur."""
    if isinstance(obj, str):
        if obj.startswith('http') or obj.startswith('/'):
            yield obj
    elif isinstance(obj, list):
        for o in obj:
            for u in urls(o):
                yield u
    elif isinstance(obj, dict):
        for k, v in obj.items():
            # « @id » n'est pas un lien mais l'identifiant d'une entite :
            # https://mbc974.com/#club nomme le club, il ne renvoie a aucune
            # ancre de la page. Le verifier comme une URL produirait une fausse
            # alerte sur chacune des treize pages.
            if k in ('@context', '@type', '@id'):
                continue
            for u in urls(v):
                yield u


def main():
    erreurs, avertis = [], []

    for page in pages():
        src = io.open(page, encoding='utf-8').read()

        ids = ID_HTML.findall(src)
        for i in sorted({x for x in ids if ids.count(x) > 1}):
            erreurs.append('%s : id HTML declare %d fois -> #%s' % (page, ids.count(i), i))
        ids = set(ids)

        clubs = set()
        for brut in BLOC.findall(src):
            try:
                doc = json.loads(brut)
            except ValueError as e:
                erreurs.append('%s : JSON-LD invalide -> %s' % (page, e))
                continue

            for n in noeuds(doc):
                types = n.get('@type')
                types = types if isinstance(types, list) else [types]

                if 'SportsClub' in types or 'SportsOrganization' in types:
                    if n.get('@id'):
                        clubs.add(n['@id'])

                if 'SportsEvent' in types or 'Event' in types:
                    quoi = n.get('name', '(sans nom)')[:44]
                    for prop in RECOMMANDEES:
                        if not n.get(prop):
                            avertis.append('%s : %s -> propriete recommandee absente : %s'
                                           % (page, quoi, prop))
                    org = n.get('organizer') or {}
                    if isinstance(org, dict) and not org.get('url'):
                        avertis.append('%s : %s -> organizer sans url' % (page, quoi))
                    loc = n.get('location') or {}
                    if isinstance(loc, dict) and not (loc.get('address') or {}):
                        erreurs.append('%s : %s -> location sans address' % (page, quoi))
                    if n.get('endDate') and n.get('startDate') \
                            and n['endDate'] <= n['startDate']:
                        erreurs.append('%s : %s -> endDate <= startDate' % (page, quoi))

                for u in urls(n):
                    if not u.startswith(SITE):
                        continue
                    reste = u[len(SITE):]
                    if reste.startswith('#'):
                        if reste[1:] not in ids:
                            erreurs.append('%s : ancre inexistante dans la page -> %s'
                                           % (page, u))
                    elif reste and not os.path.exists(reste.split('#')[0].split('?')[0]):
                        cible = reste.split('#')[0].split('?')[0]
                        if not os.path.exists(cible) and not os.path.isdir(cible):
                            erreurs.append('%s : fichier absent du depot -> %s' % (page, u))

        if len(clubs) > 1:
            avertis.append('%s : %d identifiants differents pour le club -> %s'
                           % (page, len(clubs), ', '.join(sorted(clubs))))

    for a in avertis:
        print('  ~~ %s' % a)
    for e in erreurs:
        print('  !! %s' % e)
    print('\n  %d page(s) verifiee(s) — %d erreur(s), %d avertissement(s)'
          % (len(pages()), len(erreurs), len(avertis)))
    return 1 if erreurs else 0


if __name__ == '__main__':
    sys.exit(main())
