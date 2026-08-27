# -*- coding: utf-8 -*-
"""Publie le calendrier officiel PRM sur le site, a partir du PDF de la LRBB.

    python .claude/set-calendrier-prm.py            met le site a jour
    python .claude/set-calendrier-prm.py --essai    montre les ecarts, n'ecrit rien

Depose au prealable le PDF dans Telechargements sous son nom d'origine
(« CALENDRIER SENIOR PRM NORD*.pdf ») : le plus recent est retenu.

Pourquoi un script plutot qu'une saisie a la main : le calendrier bouge. Entre
l'edition du 21/08/2026 et celle du 25/08/2026, trois rencontres du MBC avaient
change de camp — le site envoyait donc le public au mauvais gymnase trois fois.
L'article 4 du reglement autorisant une derogation jusqu'a 5 jours avant chaque
rencontre, cela se reproduira.

Le script touche quatre choses, toutes reperees par des balises dans index.html :

    calendrier:lignes   les <li> du calendrier
    calendrier:jsonld   les SportsEvent (matchs a domicile uniquement)
    calendrier:compte   le nombre de matchs a domicile, dans le chapeau
    calendrier:affiche  le texte alternatif de l'affiche

Il regenere aussi l'affiche partageable et archive le PDF dans assets/documents.
Les postes benevoles ne sont PAS deduits du PDF : ils viennent de
.claude/benevoles-matchs.json, pour qu'une regeneration n'efface pas les noms.
"""
import io
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
lire_cal = importlib.import_module('lire-calendrier-prm')

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE = 'assets/documents/calendrier-prm-nord-2026-2027.pdf'
AFFICHE = 'assets/affiches/calendrier-phase1-2026-2027'
BENEVOLES = '.claude/benevoles-matchs.json'
GYMNASE = 'Gymnase de La Montagne'

CREST_MBC = ('<span class="mx-crest mx-crest--mbc">'
             '<img src="assets/logos/mbc-logo.webp" alt="" width="360" height="370" '
             'loading="lazy" decoding="async" '
             'onerror="this.onerror=null;this.src=\'assets/logos/mbc-logo.png\'"></span>')


def crest_adverse(sigle):
    """Le logo du club adverse, avec repli sur le sigle officiel s'il manque."""
    f = sigle.lower()
    return ('<span class="mx-crest mx-crest--logo">'
            '<img src="assets/logos/clubs/%s-144.webp" '
            'srcset="assets/logos/clubs/%s-144.webp 144w, assets/logos/clubs/%s.webp 288w" '
            'sizes="72px" alt="" width="288" height="288" loading="lazy" decoding="async" '
            'onerror="this.closest(\'.mx-crest\').className=\'mx-crest mx-crest--sigle\';'
            'this.closest(\'.mx-crest\').textContent=\'%s\'"></span>' % (f, f, f, sigle))


def bloc_benevoles(m, postes, affectations):
    """Le <details> des postes, present seulement pour les matchs a domicile."""
    from urllib.parse import quote
    lignes = []
    for poste in postes:
        qui = affectations.get(poste)
        if qui:
            lignes.append('            <li class="mx-poste"><span class="mx-poste__r">%s</span>'
                          '<span class="mx-poste__v">%s</span></li>' % (poste, qui))
        else:
            lignes.append('            <li class="mx-poste"><span class="mx-poste__r">%s</span>'
                          '<span class="mx-poste__v mx-poste__v--libre">À pourvoir</span></li>' % poste)
    sujet = quote(u'Bénévolat - match du %d %s' % (m['num'], m['mois_long']), safe='')
    return (u'          <details class="mx-roles">\n'
            u'            <summary class="mx-roles__s"><span class="mx-roles__lab">Postes bénévoles</span>'
            u'<span class="mx-roles__etat"></span></summary>\n'
            u'            <ul class="mx-roles__l">\n%s\n'
            u'            </ul>\n'
            u'            <p class="mx-roles__cta">Une mission vous tente&nbsp;? '
            u'<a href="mailto:contact@mbc974.com?subject=%s">Écrivez-nous</a> ou dites-le au coach '
            u"à l'entraînement. Aucune expérience requise&nbsp;: le club vous forme à la table de marque.</p>\n"
            u'          </details>\n' % ('\n'.join(lignes), sujet))


def lignes_html(mbc, postes, benevoles):
    out = []
    for m in mbc:
        dom = m['domicile']
        duel = (CREST_MBC + '<span class="mx-vs">vs</span>' + crest_adverse(m['sigle'])) if dom \
            else (crest_adverse(m['sigle']) + '<span class="mx-vs">vs</span>' + CREST_MBC)
        roles = bloc_benevoles(m, postes, benevoles.get(m['date'], {})) if dom else ''
        out.append(
            u'        <li class="mx-row mx-row--%(cls)s" data-date="%(date)s">\n'
            u'          <span class="mx-j">J%(journee)d</span>\n'
            u'          <time class="mx-date" datetime="%(date)sT20:30">\n'
            u'            <span class="mx-date__d">%(jour)s</span>\n'
            u'            <span class="mx-date__n">%(num)d</span>\n'
            u'            <span class="mx-date__m">%(mois)s</span>\n'
            u'          </time>\n'
            u'          <span class="mx-duel">%(duel)s</span>\n'
            u'          <span class="mx-opp"><b class="mx-opp__n">%(adversaire)s</b>'
            u'<span class="mx-opp__s">%(sigle)s</span></span>\n'
            u'          <span class="mx-side%(sidecls)s">%(side)s</span>\n'
            u'          <span class="mx-meta"><span class="mx-h">%(heure)s</span>'
            u'<span class="mx-lieu">%(lieu)s</span></span>\n'
            u'%(roles)s'
            u'        </li>' % dict(
                m, cls='dom' if dom else 'ext', duel=duel, roles=roles,
                mois=m['mois'].replace('fevr.', u'févr.').replace('aout', u'août')
                              .replace('dec.', u'déc.'),
                sidecls=' mx-side--dom' if dom else '',
                side=u'À domicile' if dom else u'En déplacement',
                lieu=GYMNASE if dom else u"Chez l'adversaire"))
    return '\n'.join(out)


def bloc_jsonld(mbc):
    """Seuls les matchs a domicile sont declares : le lieu des autres nous echappe."""
    evts = []
    for m in (x for x in mbc if x['domicile']):
        evts.append({
            '@type': 'SportsEvent',
            'name': u'MBC La Montagne Basket Club – %s (Pré-Régionale Masculine)' % m['adversaire'],
            'startDate': '%sT20:30:00+04:00' % m['date'],
            'eventStatus': 'https://schema.org/EventScheduled',
            'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
            'sport': 'Basketball',
            'location': {'@type': 'Place', 'name': GYMNASE, 'address': {
                '@type': 'PostalAddress', 'streetAddress': 'Chemin des Bauhinias',
                'addressLocality': 'Saint-Denis', 'postalCode': '97417',
                'addressRegion': u'La Réunion', 'addressCountry': 'RE'}},
            'homeTeam': {'@type': 'SportsTeam', 'name': 'MBC La Montagne Basket Club',
                         'url': 'https://mbc974.com/'},
            'awayTeam': {'@type': 'SportsTeam', 'name': m['adversaire']},
            'organizer': {'@type': 'SportsOrganization',
                          'name': u'Ligue Régionale de Basket-Ball de La Réunion',
                          'alternateName': 'LRBB'},
            'isAccessibleForFree': True,
        })
    txt = json.dumps({'@context': 'https://schema.org', '@graph': evts},
                     ensure_ascii=False, indent=2)
    return '<script type="application/ld+json">\n%s\n</script>' % txt


def remplacer(src, balise, contenu):
    d, f = '<!-- %s -->' % balise, '<!-- /%s -->' % balise
    i, j = src.find(d), src.find(f)
    if i < 0 or j < 0:
        raise ValueError('balise %s absente de index.html' % balise)
    return src[:i + len(d)] + '\n' + contenu + '\n' + ' ' * 0 + src[j:]


# Le nombre de matchs a domicile est ecrit en toutes lettres a deux endroits :
# le chapeau de la section, et le texte alternatif de l'affiche. Ce dernier
# vit dans un attribut, ou un commentaire HTML serait affiche tel quel : on
# remplace donc le mot par expression reguliere, en s'appuyant sur ce qui
# l'entoure. Les deux motifs doivent matcher, sinon on leve — un chapeau
# reformule sans le savoir laisserait un compte faux en place.
COMPTES = (
    re.compile(u'(Sept rencontres pour la première phase[^<]*?dont )\\w+( à domicile)'),
    re.compile(u'(alt="Affiche du calendrier[^"]*?dont )\\w+( à domicile)'),
)


def remplacer_compte(src, mot):
    for motif in COMPTES:
        src, n = motif.subn(lambda m: m.group(1) + mot + m.group(2), src, count=1)
        if n != 1:
            raise ValueError('compte introuvable : %s' % motif.pattern[:48])
    return src


def main():
    essai = '--essai' in sys.argv
    os.chdir(RACINE)
    pdf = lire_cal.dernier_pdf()
    if not pdf:
        print('!! aucun « CALENDRIER SENIOR PRM NORD*.pdf » dans Telechargements')
        return 1
    r = lire_cal.resume(pdf)
    _, mbc = lire_cal.lire(pdf)
    print('  source : %s' % os.path.basename(pdf))
    print('  edite le %(edite_le)s  ->  %(rencontres)d rencontres, %(journees)d journees' % r)
    print('  MBC : %(domicile)d a domicile, %(exterieur)d en deplacement' % r)

    bnv = json.load(io.open(BENEVOLES, encoding='utf-8'))
    postes, affect = bnv['postes'], bnv['matchs']
    for m in mbc:
        if m['domicile'] and m['date'] not in affect:
            print('  .. %s devient un match a domicile : postes tous a pourvoir' % m['date'])

    html = io.open('index.html', encoding='utf-8').read()
    avant = html
    html = remplacer(html, 'calendrier:lignes', lignes_html(mbc, postes, affect))
    html = remplacer(html, 'calendrier:jsonld', bloc_jsonld(mbc))
    mot = {1: 'un', 2: 'deux', 3: 'trois', 4: 'quatre',
           5: 'cinq', 6: 'six', 7: 'sept'}[r['domicile']]
    html = remplacer_compte(html, mot)

    if essai:
        print('\n  essai : %s' % ('des ecarts subsistent' if html != avant else 'index.html est deja a jour'))
        return 0

    io.open('index.html', 'w', encoding='utf-8', newline='\n').write(html)
    print('  index.html mis a jour' if html != avant else '  index.html etait deja a jour')

    shutil.copyfile(pdf, ARCHIVE)
    print('  PDF archive -> %s' % ARCHIVE)

    import importlib.util
    spec = importlib.util.spec_from_file_location('aff', '.claude/affiche-calendrier.py')
    aff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(aff)
    aff.produire(mbc, AFFICHE)
    print('  affiche regeneree -> %s.png (+ webp)' % AFFICHE)
    print('\n  ne pas oublier : python .claude/bump-assets.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
