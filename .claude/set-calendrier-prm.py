# -*- coding: utf-8 -*-
"""Publie le calendrier officiel PRM sur le site, a partir du PDF de la LRBB.

    python .claude/set-calendrier-prm.py            met le site a jour
    python .claude/set-calendrier-prm.py --essai    montre les ecarts, n'ecrit rien
    python .claude/set-calendrier-prm.py --archive  relit le PDF deja archive

Depose au prealable le PDF dans Telechargements sous son nom d'origine
(« CALENDRIER SENIOR PRM NORD*.pdf ») : le plus recent est retenu. L'option
--archive relit celui de assets/documents et ne touche NI a l'archive NI a
l'affiche : elle sert a regenerer le HTML et le JSON-LD apres avoir modifie ce
script, sans attendre une nouvelle edition du calendrier.

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

Enfin il VERIFIE (sans les reecrire) les deux blocs rediges a la main qui
parlent d'une rencontre precise — l'encart « prochain rendez-vous » et le
fichier .ics — parce qu'eux aussi mentent quand une date bouge.
"""
import datetime
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
ICS = 'assets/documents/mbc-vs-sainte-suzanne-11-09-2026.ics'

SITE = 'https://mbc974.com/'
CLUB_ID = 'https://mbc974.com/#club'      # l'entite SportsClub declaree dans le <head>
CLUB_NOM = 'MBC La Montagne Basket Club'
COMPETITION = u'Pré-Régionale Masculine'
GYMNASE = 'Gymnase de La Montagne'
FUSEAU = '+04:00'                          # La Reunion, toute l'annee

# ---------------------------------------------------------------------------
# Duree d'une rencontre — LE seul endroit ou elle est ecrite.
# ---------------------------------------------------------------------------
# Le PDF de la LRBB ne donne pas d'heure de fin : il ne connait que le coup
# d'envoi. Schema.org (et Google) demandent pourtant un endDate. On applique
# donc une duree forfaitaire, qui n'est pas inventee pour l'occasion : c'est
# celle que le club utilise deja ailleurs sur le site — le fichier .ics du
# premier match va de 20h30 a 23h00, et le creneau du vendredi declare dans les
# openingHoursSpecification du <head> va de 20h00 a 23h00. Quatre quart-temps
# de 10 minutes, mi-temps, temps morts et protocole d'apres-match tiennent dans
# ces 2 h 30. Changer la valeur ici la change partout.
DUREE = datetime.timedelta(hours=2, minutes=30)

ADRESSE_GYMNASE = {
    '@type': 'PostalAddress',
    'streetAddress': 'Chemin des Bauhinias',
    'addressLocality': 'Saint-Denis',
    'postalCode': '97417',
    'addressRegion': u'La Réunion',
    'addressCountry': 'RE',
}

# ---------------------------------------------------------------------------
# Images des evenements — uniquement des fichiers qui existent vraiment.
# ---------------------------------------------------------------------------
# Ordre de priorite demande par Google : d'abord le visuel propre a la
# rencontre s'il existe, puis l'affiche de la phase (elle montre bien CE match),
# puis deux photos reelles du club. L'existence de chaque fichier est verifiee
# avant ecriture : une URL d'image cassee dans un SportsEvent est un
# avertissement Search Console de plus, pas un detail.
AFFICHES_MATCH = {
    '2026-09-11': 'assets/affiches/mbc-premier-match-sainte-suzanne-2026.jpg',
}
IMAGES_GENERIQUES = [
    'assets/galerie/match-banniere.jpg',        # 1120x747, 3:2
    'assets/images/gymnase-la-montagne-clair.jpg',  # 1445x1088, 4:3 (photo courante ; l'ancienne
    # gymnase-la-montagne.jpg existe encore mais n'est plus affichee nulle part)
]

ACCENTS = {'fevr.': u'févr.', 'aout': u'août', 'dec.': u'déc.',
           'fevrier': u'février', 'decembre': u'décembre'}

CREST_MBC = ('<span class="mx-crest mx-crest--mbc">'
             '<img src="assets/logos/mbc-logo.webp" alt="" width="360" height="370" '
             'loading="lazy" decoding="async" '
             'onerror="this.onerror=null;this.src=\'assets/logos/mbc-logo.png\'"></span>')


def acc(mot):
    return ACCENTS.get(mot, mot)


def ancre(m):
    """L'identifiant stable de la rencontre dans la page.

    Il sert a la fois d'id sur le <li> et d'URL canonique de l'evenement
    (https://mbc974.com/#match-2026-09-11). La date suffit a l'unicite : le MBC
    ne joue qu'une rencontre par journee.
    """
    return 'match-%s' % m['date']


def url_match(m):
    return '%s#%s' % (SITE, ancre(m))


def debut(m):
    return '%sT%s:00%s' % (m['date'], m['iso_heure'], FUSEAU)


def fin(m):
    """Coup d'envoi + DUREE. Passe minuit si un jour l'horaire l'exige."""
    t = datetime.datetime.fromisoformat('%sT%s:00' % (m['date'], m['iso_heure'])) + DUREE
    return t.strftime('%Y-%m-%dT%H:%M:%S') + FUSEAU


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
    sujet = quote(u'Bénévolat - match du %d %s' % (m['num'], acc(m['mois_long'])), safe='')
    return (u'          <details class="mx-roles">\n'
            u'            <summary class="mx-roles__s"><span class="mx-roles__lab">Postes bénévoles</span>'
            u'<span class="mx-roles__etat"></span></summary>\n'
            u'            <ul class="mx-roles__l">\n%s\n'
            u'            </ul>\n'
            u'            <p class="mx-roles__cta">Une mission vous tente&nbsp;? '
            u'<a href="mailto:contact@mbc974.com?subject=%s">Écrivez-nous</a> ou dites-le au coach '
            u"à l'entraînement. Aucune expérience requise&nbsp;: le club vous forme à la table de marque.</p>\n"
            u'          </details>\n' % ('\n'.join(lignes), sujet))


def bloc_score(m):
    """Le resultat, present uniquement quand la LRBB l'a publie.

    Tant que le PDF imprime « ...     ... », rien n'est ajoute : le site
    n'affiche pas de score devine. Voir lire-calendrier-prm.score().
    """
    if not m['score']:
        return ''
    s = m['score']
    issue = 'v' if s['mbc'] > s['adverse'] else ('d' if s['mbc'] < s['adverse'] else 'n')
    libelle = {'v': u'Victoire', 'd': u'Défaite', 'n': u'Match nul'}[issue]
    return (u'<span class="mx-score mx-score--%s"><span class="sr-only">%s du MBC, </span>'
            u'%d<span class="mx-score__s">–</span>%d</span>'
            % (issue, libelle, s['mbc'], s['adverse']))


def lignes_html(mbc, postes, benevoles):
    out = []
    for m in mbc:
        dom = m['domicile']
        duel = (CREST_MBC + '<span class="mx-vs">vs</span>' + crest_adverse(m['sigle'])) if dom \
            else (crest_adverse(m['sigle']) + '<span class="mx-vs">vs</span>' + CREST_MBC)
        roles = bloc_benevoles(m, postes, benevoles.get(m['date'], {})) if dom else ''
        out.append(
            u'        <li class="mx-row mx-row--%(cls)s" id="%(ancre)s" data-date="%(date)s">\n'
            u'          <span class="mx-j">J%(journee)d</span>\n'
            u'          <time class="mx-date" datetime="%(date)sT%(iso_heure)s">\n'
            u'            <span class="mx-date__d">%(jour)s</span>\n'
            u'            <span class="mx-date__n">%(num)d</span>\n'
            u'            <span class="mx-date__m">%(mois)s</span>\n'
            u'          </time>\n'
            u'          <span class="mx-duel">%(duel)s</span>\n'
            u'          <span class="mx-opp"><b class="mx-opp__n">%(adversaire)s</b>'
            u'<span class="mx-opp__s">%(sigle)s</span></span>\n'
            u'          <span class="mx-side%(sidecls)s">%(side)s</span>\n'
            u'          <span class="mx-meta"><span class="mx-h">%(heure)s</span>'
            u'<span class="mx-lieu">%(lieu)s</span>%(score)s</span>\n'
            u'%(roles)s'
            u'        </li>' % dict(
                m, cls='dom' if dom else 'ext', duel=duel, roles=roles,
                ancre=ancre(m), score=bloc_score(m),
                mois=acc(m['mois']),
                sidecls=' mx-side--dom' if dom else '',
                side=u'À domicile' if dom else u'En déplacement',
                lieu=GYMNASE if dom else u"Chez l'adversaire"))
    return '\n'.join(out)


# ---------------------------------------------------------------------------
# JSON-LD
# ---------------------------------------------------------------------------
def description(m):
    """Une phrase lisible par un humain, faite uniquement de donnees connues."""
    return (u"J%d de %s : le %s reçoit %s au %s, à Saint-Denis (La Réunion), "
            u"le %s %d %s %d à %s. Entrée libre."
            % (m['journee'], COMPETITION, CLUB_NOM, m['adversaire'], GYMNASE,
               m['jour_long'], m['num'], acc(m['mois_long']), m['annee'], m['heure']))


def images(m, affiche):
    """Les visuels de la rencontre, du plus specifique au plus general."""
    chemins = []
    if m['date'] in AFFICHES_MATCH:
        chemins.append(AFFICHES_MATCH[m['date']])
    if affiche:
        chemins.append(affiche)
    chemins.extend(IMAGES_GENERIQUES)
    for c in chemins:
        if not os.path.exists(c):
            raise ValueError(u'image absente du depot : %s' % c)
    return [SITE + c for c in chemins]


def equipes(m):
    """Les deux equipes en presence, dans l'ordre recevant / visiteur.

    Google demande un « performer » : les deux equipes le sont, pas seulement
    le MBC. Le club adverse n'a pas d'URL verifiee ici — on ne lui en invente
    donc pas, un SportsTeam nomme est valide.
    """
    mbc = {'@type': 'SportsTeam', 'name': CLUB_NOM, 'sport': 'Basketball',
           'url': SITE, 'memberOf': {'@id': CLUB_ID}}
    adverse = {'@type': 'SportsTeam', 'name': m['adversaire'], 'sport': 'Basketball'}
    return (mbc, adverse) if m['domicile'] else (adverse, mbc)


def bloc_jsonld(mbc, affiche, valid_from):
    """Seuls les matchs a domicile sont declares : le lieu des autres nous echappe.

    Un Event sans location est une ERREUR Search Console, pas un avertissement,
    et le PDF de la LRBB ne donne pas l'adresse des gymnases adverses. Declarer
    les sept rencontres couterait donc plus qu'il ne rapporterait — et surtout
    obligerait a inventer trois adresses.

    Sur l'organisateur : c'est le club recevant qui organise la rencontre chez
    lui (salle, table de marque, benevoles — la liste des postes juste au-dessus
    dans la page le dit). Comme on ne declare que les matchs a domicile, le MBC
    est bien l'organisateur de tous les evenements de ce bloc, et il a une URL
    reelle. La competition, elle, reste nommee dans le nom et la description.

    Sur les matchs deja joues : leur noeud est CONSERVE et garde
    EventScheduled — la rencontre a bien eu lieu comme prevu. Schema.org n'offre
    pas d'etat « termine » (seuls Cancelled / Postponed / Rescheduled / MovedOnline
    existent) et n'a pas non plus de propriete de score : le resultat vit dans le
    HTML, pas ici.
    """
    evts = []
    for m in (x for x in mbc if x['domicile']):
        recoit, visite = equipes(m)
        offre = {
            '@type': 'Offer',
            'name': u'Entrée libre',
            'price': '0',
            'priceCurrency': 'EUR',
            'availability': 'https://schema.org/InStock',
            'url': url_match(m),
        }
        if valid_from:
            offre['validFrom'] = valid_from
        evts.append({
            '@type': 'SportsEvent',
            '@id': url_match(m),
            'name': u'%s – %s (%s, J%d)' % (CLUB_NOM, m['adversaire'], COMPETITION, m['journee']),
            'description': description(m),
            'url': url_match(m),
            'startDate': debut(m),
            'endDate': fin(m),
            'eventStatus': 'https://schema.org/EventScheduled',
            'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
            'sport': 'Basketball',
            'image': images(m, affiche),
            'location': {'@type': 'Place', 'name': GYMNASE,
                         'address': dict(ADRESSE_GYMNASE),
                         'geo': {'@type': 'GeoCoordinates',
                                 'latitude': -20.891557, 'longitude': 55.423974},
                         'hasMap': 'https://maps.app.goo.gl/KcTePvY47wzi6JMu9'},
            'performer': [recoit, visite],
            'homeTeam': recoit,
            'awayTeam': visite,
            'organizer': {'@type': 'SportsOrganization', '@id': CLUB_ID,
                          'name': CLUB_NOM, 'url': SITE},
            'offers': offre,
            'isAccessibleForFree': True,
            'inLanguage': 'fr-RE',
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


# L'affiche porte une empreinte dans son nom (voir affiche-calendrier.py). Il
# faut donc repointer ses URL : la source, les crans du srcset, les deux liens
# « telecharger » / « voir en grand » — et desormais aussi celle citee dans les
# images du JSON-LD. Le motif tolere une empreinte deja presente, pour que le
# script reste rejouable.
# Attention : le nom propose au telechargement (attribut download) est
# volontairement « calendrier-MBC-phase1-... » et non « calendrier-phase1-... ».
# Sinon ce motif le reecrirait aussi, et le visiteur enregistrerait un fichier
# nomme avec l'empreinte.
AFFICHE_URL = re.compile(r'calendrier-phase1-2026-2027(?:-[0-9a-f]{8})?(-\d{3})?\.(png|webp)')


def repointer_affiche(src, nouveau):
    return AFFICHE_URL.sub(lambda m: '%s%s.%s' % (nouveau, m.group(1) or '', m.group(2)), src)


def affiche_actuelle(html):
    """Le chemin de l'affiche pleine taille telle qu'elle est referencee aujourd'hui.

    Le JSON-LD la cite comme image des rencontres. On la relit dans la page au
    lieu de la recalculer : en mode --archive l'affiche n'est pas regeneree, et
    en mode complet repointer_affiche() corrigera l'empreinte juste apres.
    """
    m = re.search(r'assets/affiches/calendrier-phase1-2026-2027(?:-[0-9a-f]{8})?\.png', html)
    if not m:
        return None
    chemin = m.group(0)
    return chemin if os.path.exists(chemin) else None


def remplacer_compte(src, mot):
    for motif in COMPTES:
        src, n = motif.subn(lambda m: m.group(1) + mot + m.group(2), src, count=1)
        if n != 1:
            raise ValueError('compte introuvable : %s' % motif.pattern[:48])
    return src


# ---------------------------------------------------------------------------
# Les deux blocs rediges a la main : on les verifie, on ne les reecrit pas
# ---------------------------------------------------------------------------
def verifier_coherence(html, mbc):
    """Signale tout ce qui, ailleurs dans le site, contredit le PDF.

    L'encart « prochain rendez-vous » et le fichier .ics parlent d'UNE rencontre
    precise et sont ecrits a la main (affiche dediee, texte redige). Les
    regenerer serait plus risque qu'utile ; les laisser diverger en silence,
    c'est exactement la panne que ce script existe pour eviter. On leve donc
    des avertissements lisibles, et le mainteneur tranche.
    """
    alertes = []
    par_date = {m['date']: m for m in mbc}

    m_enc = re.search(r'id="prochain-match"[^>]*data-match-date="(\d{4}-\d{2}-\d{2})"', html)
    if not m_enc:
        alertes.append(u'encart « prochain rendez-vous » : data-match-date introuvable')
    else:
        d = m_enc.group(1)
        r = par_date.get(d)
        if not r:
            alertes.append(u'encart : le %s n\'est plus une rencontre du MBC' % d)
        else:
            if not r['domicile']:
                alertes.append(u'encart : le %s est devenu un DEPLACEMENT '
                               u'(l\'encart annonce le Gymnase de La Montagne)' % d)
            sigle_attendu = r['sigle']
            bloc = html[m_enc.start():m_enc.start() + 3000]
            if r['iso_heure'] != '20:30' and '20h30' in bloc:
                alertes.append(u'encart : l\'horaire du %s est passe a %s, l\'encart dit 20h30'
                               % (d, r['heure']))
            if sigle_attendu != 'BC2S' and 'Sainte-Suzanne' in bloc:
                alertes.append(u'encart : l\'adversaire du %s est %s, l\'encart dit Sainte-Suzanne'
                               % (d, r['adversaire']))

    if os.path.exists(ICS):
        ics = io.open(ICS, encoding='utf-8').read()
        m_ics = re.search(r'DTSTART:(\d{8})T(\d{6})Z', ics)
        if m_ics:
            utc = datetime.datetime.strptime(m_ics.group(1) + m_ics.group(2), '%Y%m%d%H%M%S')
            local = utc + datetime.timedelta(hours=4)
            d = local.strftime('%Y-%m-%d')
            r = par_date.get(d)
            if not r:
                alertes.append(u'%s : le %s n\'est plus une rencontre du MBC' % (ICS, d))
            elif local.strftime('%H:%M') != r['iso_heure']:
                alertes.append(u'%s : coup d\'envoi %s, le PDF dit %s'
                               % (ICS, local.strftime('%H:%M'), r['iso_heure']))
    return alertes


def main():
    essai = '--essai' in sys.argv
    depuis_archive = '--archive' in sys.argv
    os.chdir(RACINE)

    if depuis_archive:
        pdf = ARCHIVE
        if not os.path.exists(pdf):
            print('!! %s introuvable' % ARCHIVE)
            return 1
    else:
        pdf = lire_cal.dernier_pdf()
        if not pdf:
            print('!! aucun « CALENDRIER SENIOR PRM NORD*.pdf » dans Telechargements')
            print('   (--archive relit celui de %s)' % ARCHIVE)
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
    affiche = affiche_actuelle(html)
    if not affiche:
        print('  .. affiche du calendrier introuvable : elle ne sera pas citee dans le JSON-LD')

    html = remplacer(html, 'calendrier:lignes', lignes_html(mbc, postes, affect))
    html = remplacer(html, 'calendrier:jsonld',
                     bloc_jsonld(mbc, affiche, lire_cal.edite_le_date(pdf)))
    mot = {1: 'un', 2: 'deux', 3: 'trois', 4: 'quatre',
           5: 'cinq', 6: 'six', 7: 'sept'}[r['domicile']]
    html = remplacer_compte(html, mot)

    for a in verifier_coherence(html, mbc):
        print('  !! %s' % a)

    if essai:
        print('\n  essai : %s' % ('des ecarts subsistent' if html != avant else 'index.html est deja a jour'))
        return 0

    io.open('index.html', 'w', encoding='utf-8', newline='\n').write(html)
    print('  index.html mis a jour' if html != avant else '  index.html etait deja a jour')

    if depuis_archive:
        print('  (--archive : PDF et affiche laisses tels quels)')
        print('\n  ne pas oublier : python .claude/bump-assets.py')
        return 0

    shutil.copyfile(pdf, ARCHIVE)
    print('  PDF archive -> %s' % ARCHIVE)

    import glob
    import importlib.util
    spec = importlib.util.spec_from_file_location('aff', '.claude/affiche-calendrier.py')
    aff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(aff)
    anciens = set(glob.glob('assets/affiches/calendrier-phase1-2026-2027*'))
    nouveau = aff.produire(mbc, AFFICHE)
    print('  affiche regeneree -> %s.png (+ 3 webp)' % nouveau)

    # repointer les URL de l'affiche (page ET JSON-LD), puis retirer les orphelins
    html = repointer_affiche(io.open('index.html', encoding='utf-8').read(), nouveau)
    io.open('index.html', 'w', encoding='utf-8', newline='\n').write(html)
    gardes = set(glob.glob('assets/affiches/%s*' % nouveau))
    for vieux in sorted(anciens - gardes):
        os.remove(vieux)
        print('  retire -> %s' % vieux)

    print('\n  ne pas oublier : python .claude/bump-assets.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
