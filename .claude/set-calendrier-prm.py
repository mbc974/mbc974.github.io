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
    calendrier:jsonld   la liste ItemList du calendrier (les SportsEvent, eux,
                        vivent sur /matchs/<slug>/ et sont ecrits par
                        .claude/build-matchs.py, relance ici automatiquement)
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
import glob
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
# Le .ics du prochain match : c'est celui que build-matchs.py produit a
# partir de data/matchs.json. Il y en avait un second, ecrit a la main,
# pour la meme rencontre — deux fichiers a tenir a jour pour un seul match.
ICS = 'assets/documents/mbc-sainte-suzanne-11-septembre-2026.ics'

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
# ces 2 h 30. Depuis que les SportsEvent vivent sur les pages /matchs/<slug>/,
# la valeur qui fait foi est le champ « duree » (en minutes) de
# data/matchs.json ; elle est rappelee ici pour memoire du raisonnement.

def instants(date, iso_heure, duree_min):
    """Les deux bornes ABSOLUES d'une rencontre, fuseau compris.

    Pourquoi absolues, et pourquoi elles sortent jusque dans le HTML : le JS de
    la home decidait « cette rencontre est passee » avec un
    new Date('2026-09-11T20:30:00') — une chaine SANS fuseau, que le navigateur
    lit donc dans le fuseau du VISITEUR. Depuis Paris la rencontre restait « a
    venir » deux heures apres le coup de sifflet final ; depuis Tokyo elle
    passait au passe cinq heures trop tot. Le gymnase, lui, est a La Reunion :
    l'instant doit etre le meme pour tout le monde.

    La duree ne s'invente pas ici : elle vient du champ « duree » (en minutes)
    de data/matchs.json, qui fait foi — voir le bloc de commentaire ci-dessus.
    """
    deb = datetime.datetime.strptime(date + ' ' + iso_heure, '%Y-%m-%d %H:%M')
    fin = deb + datetime.timedelta(minutes=duree_min)
    fmt = '%Y-%m-%dT%H:%M:00'
    return deb.strftime(fmt) + FUSEAU, fin.strftime(fmt) + FUSEAU


ADRESSE_GYMNASE = {
    '@type': 'PostalAddress',
    'streetAddress': 'Chemin des Bauhinias',
    'addressLocality': 'Saint-Denis',
    'postalCode': '97417',
    'addressRegion': u'La Réunion',
    'addressCountry': 'RE',
}
ACCENTS = {'fevr.': u'févr.', 'aout': u'août', 'dec.': u'déc.',
           'fevrier': u'février', 'decembre': u'décembre'}

CREST_MBC = ('<span class="mx-crest mx-crest--mbc">'
             '<img src="assets/logos/mbc-logo.webp" alt="" width="288" height="296" '
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


def lignes_html(mbc, postes, benevoles, slugs, durees, courts, libres):
    """Chaque rencontre porte desormais un lien vers sa page dediee. Les slugs
    viennent de data/matchs.json, dont verifier_source_matchs() garantit qu'il
    parle des memes dates que le PDF."""
    out = []
    for m in mbc:
        dom = m['domicile']
        duel = (CREST_MBC + '<span class="mx-vs">vs</span>' + crest_adverse(m['sigle'])) if dom \
            else (crest_adverse(m['sigle']) + '<span class="mx-vs">vs</span>' + CREST_MBC)
        roles = bloc_benevoles(m, postes, benevoles.get(m['date'], {})) if dom else ''
        out.append(
            u'        <li class="mx-row mx-row--%(cls)s" id="%(ancre)s" data-date="%(date)s"'
            u' data-debut="%(debut_iso)s" data-fin="%(fin_iso)s" data-court="%(court)s" data-libre="%(libre)s">\n'
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
            u'<span class="mx-lieu">%(lieu)s</span>%(score)s'
            u'<a class="mx-fiche" href="/matchs/%(slug)s/">Fiche du match'
            u'<span class="sr-only"> %(adversaire)s</span></a></span>\n'
            u'%(roles)s'
            u'        </li>' % dict(
                m, cls='dom' if dom else 'ext', duel=duel, roles=roles,
                ancre=ancre(m), score=bloc_score(m), slug=slugs[m['date']],
                court=courts.get(m['date'], m['adversaire']),
                # « Entree libre » est une DONNEE (champ entreeLibre de
                # data/matchs.json), pas une consequence du fait de jouer a
                # domicile. On la publie telle quelle plutot que de la deduire :
                # le jour ou une rencontre a domicile sera payante, le bandeau
                # ne l'annoncera pas gratuite.
                libre='1' if libres.get(m['date']) else '',
                debut_iso=instants(m['date'], m['iso_heure'],
                                   durees[m['date']])[0],
                fin_iso=instants(m['date'], m['iso_heure'],
                                 durees[m['date']])[1],
                mois=acc(m['mois']),
                sidecls=' mx-side--dom' if dom else '',
                side=u'À domicile' if dom else u'En déplacement',
                lieu=GYMNASE if dom else u"Chez l'adversaire"))
    return '\n'.join(out)
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
# « telecharger » / « voir en grand ». Le motif tolere une empreinte deja
# presente, pour que le script reste rejouable.
# Attention : le nom propose au telechargement (attribut download) est
# volontairement « calendrier-MBC-phase1-... » et non « calendrier-phase1-... ».
# Sinon ce motif le reecrirait aussi, et le visiteur enregistrerait un fichier
# nomme avec l'empreinte.
AFFICHE_URL = re.compile(r'calendrier-phase1-2026-2027(?:-[0-9a-f]{8})?(-\d{3})?\.(png|webp)')


def repointer_affiche(src, nouveau):
    return AFFICHE_URL.sub(lambda m: '%s%s.%s' % (nouveau, m.group(1) or '', m.group(2)), src)


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

    # Les .ics deposes dans l'agenda des supporters. Deux corrections ici.
    #
    # 1. La regex ne pouvait PAS correspondre. Elle cherchait
    #       DTSTART:20260911T203000Z
    #    alors que build-matchs.py ecrit, a juste titre,
    #       DTSTART;TZID=Indian/Reunion:20260911T203000
    #    (heure locale + VTIMEZONE, ce qui survit a un changement de fuseau
    #    du cote du lecteur d'agenda). Le `if m_ics:` etait donc toujours
    #    faux : le garde-fou existait dans le fichier et nulle part ailleurs.
    # 2. Il ne controlait qu'UN fichier, celui de la premiere journee, ecrit
    #    en dur dans ICS. Les autres rencontres a domicile pouvaient deriver
    #    sans que rien ne le dise. On les relit toutes.
    for chemin in sorted(glob.glob('assets/documents/*.ics')):
        ics = io.open(chemin, encoding='utf-8').read()
        # 3. Chercher dans le VEVENT, et pas dans tout le fichier : le bloc
        #    VTIMEZONE qui le precede porte lui aussi un DTSTART, celui de
        #    l'epoque Unix (19700101T000000). Une premiere reparation de la
        #    regex tombait dessus et annoncait quatre rencontres « du
        #    1970-01-01 » — un garde-fou qui crie faux n'est pas meilleur
        #    qu'un garde-fou muet, il est pire : on finit par l'ignorer.
        ics = ics.partition('BEGIN:VEVENT')[2] or ics
        m_ics = re.search(r'DTSTART(?:;TZID=[^:]+)?:(\d{8})T(\d{6})(Z?)', ics)
        if not m_ics:
            alertes.append(u'%s : aucun DTSTART lisible' % chemin)
            continue
        t = datetime.datetime.strptime(m_ics.group(1) + m_ics.group(2), '%Y%m%d%H%M%S')
        # Un DTSTART suffixe Z est en UTC : on le ramene a l'heure de La
        # Reunion. Sans Z, il est deja local (c'est le cas de nos fichiers).
        local = t + datetime.timedelta(hours=4) if m_ics.group(3) else t
        d = local.strftime('%Y-%m-%d')
        r = par_date.get(d)
        if not r:
            alertes.append(u'%s : le %s n\'est plus une rencontre du MBC' % (chemin, d))
        elif local.strftime('%H:%M') != r['iso_heure']:
            alertes.append(u'%s : coup d\'envoi %s, le PDF dit %s'
                           % (chemin, local.strftime('%H:%M'), r['iso_heure']))
    return alertes


# ---------------------------------------------------------------------------
# data/matchs.json est la source des pages /matchs/. Le PDF, lui, est la source
# du calendrier. Les deux doivent dire la meme chose : on le verifie ici plutot
# que de laisser un site a moitie a jour (la home juste, les fiches fausses).
# ---------------------------------------------------------------------------
SOURCE_MATCHS = 'data/matchs.json'


def verifier_source_matchs(mbc):
    """Compare le PDF et data/matchs.json. Ne reecrit rien : reecrire
    demanderait de fabriquer des slugs, donc des URL, donc des redirections."""
    if not os.path.exists(SOURCE_MATCHS):
        return [u'%s introuvable' % SOURCE_MATCHS]
    d = json.load(io.open(SOURCE_MATCHS, encoding='utf-8'))
    par_date = {m['date']: m for m in d['matchs']}
    ecarts = []
    for m in mbc:
        f = par_date.get(m['date'])
        if not f:
            ecarts.append(u'%s : rencontre absente de %s' % (m['date'], SOURCE_MATCHS))
            continue
        if bool(f['domicile']) != bool(m['domicile']):
            ecarts.append(u'%s : domicile/exterieur divergent (PDF %s, %s %s)'
                          % (m['date'], 'domicile' if m['domicile'] else 'exterieur',
                             SOURCE_MATCHS, 'domicile' if f['domicile'] else 'exterieur'))
        if int(f['journee']) != int(m['journee']):
            ecarts.append(u'%s : journee divergente (PDF J%s, %s J%s)'
                          % (m['date'], m['journee'], SOURCE_MATCHS, f['journee']))
        # L'HEURE, que cette comparaison ignorait. C'est pourtant elle qui
        # bouge le plus souvent : l'article 4 du reglement autorise une
        # derogation jusqu'a 5 jours avant la rencontre, et elle porte
        # aussi bien sur l'horaire que sur le camp. Sans ce controle, un
        # coup d'envoi avance d'une heure donnait une home juste (elle
        # vient du PDF) et sept fiches fausses (elles viennent du JSON),
        # sans une seule alerte.
        if str(f['heure']) != str(m['iso_heure']):
            ecarts.append(u'%s : heure divergente (PDF %s, %s %s)'
                          % (m['date'], m['iso_heure'], SOURCE_MATCHS, f['heure']))
    for date in sorted(set(par_date) - {m['date'] for m in mbc}):
        ecarts.append(u'%s : rencontre de %s absente du PDF' % (date, SOURCE_MATCHS))
    return ecarts


def synchroniser_scores(mbc, essai=False):
    """Recopie les scores du PDF dans data/matchs.json.

    Sans cela, le site serait a moitie a jour le soir du premier resultat : la
    home afficherait le score, parce que set-calendrier-prm.py l'ecrit
    directement dans les lignes du Match Center, mais /matchs/ et les fiches de
    rencontre l'ignoreraient, parce qu'ils lisent data/matchs.json. C'est
    exactement l'incoherence que verifier_source_matchs() existe pour eviter.

    Ce n'est PAS une exception a la regle « ne rien reecrire » qui gouverne
    cette fonction voisine : elle refuse de reecrire parce qu'ajouter une
    rencontre demanderait de fabriquer un slug, donc une URL, donc une
    redirection. Mettre a jour le score d'une rencontre DEJA appariee par sa
    date ne cree aucune URL.

    Rien n'est devine : on ne recopie que ce que la ligue a publie. Un PDF sans
    score ne vide pas un score deja enregistre — le PDF de la journee suivante
    ne republie pas les resultats des precedentes.
    """
    d = json.load(io.open(SOURCE_MATCHS, encoding='utf-8'))
    par_date = {m['date']: m for m in d['matchs']}
    changes = []
    for m in mbc:
        if not m.get('score'):
            continue
        f = par_date.get(m['date'])
        if f is None:
            continue
        neuf = {'mbc': int(m['score']['mbc']), 'adverse': int(m['score']['adverse'])}
        if f.get('score') == neuf:
            continue
        changes.append(u'%s : score %d-%d' % (m['date'], neuf['mbc'], neuf['adverse']))
        if not essai:
            f['score'] = neuf
            # Une rencontre dont la ligue publie le score a ete jouee.
            if f.get('statut') == 'a-venir':
                f['statut'] = 'joue'
    if changes and not essai:
        io.open(SOURCE_MATCHS, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    for c in changes:
        print('  .. %s -> %s' % (c, 'a ecrire' if essai else SOURCE_MATCHS))
    return changes


def regenerer_matchs():
    """Relance .claude/build-matchs.py : pages de rencontre, /matchs/, bandeau
    du prochain match et ItemList de la home."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('bm', '.claude/build-matchs.py')
    bm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bm)
    print('  --- build-matchs.py ---')
    bm.main()


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

    ecarts = verifier_source_matchs(mbc)
    for a in ecarts:
        print('  !! %s' % a)
    if ecarts:
        print("  !! corrigez data/matchs.json avant de republier le calendrier")
        return 1
    _src = json.load(io.open(SOURCE_MATCHS, encoding='utf-8'))['matchs']
    slugs = {m['date']: m['slug'] for m in _src}
    # La duree vient de data/matchs.json et de nulle part ailleurs : c'est elle
    # qui fixe l'heure de fin publiee dans data-fin, donc l'instant precis ou la
    # home cesse d'annoncer la rencontre.
    durees = {m['date']: (m.get('duree') or 120) for m in _src}
    # Le nom COURT de l'adversaire (« Sainte-Suzanne », pas « Basket Club
    # Sainte-Suzanne »). Le PDF de la ligue ne connait que le nom long ; la forme
    # courte vit dans data/matchs.json, et c'est elle qu'affiche le bandeau du
    # prochain match. En la publiant sur la ligne, ce bandeau peut se reconstruire
    # tout seul quand la rencontre annoncee est passee, sans reinventer de libelle.
    courts = {m['date']: (m.get('adversaireCourt') or m['adversaire']) for m in _src}
    libres = {m['date']: bool(m.get('entreeLibre')) for m in _src}

    html = remplacer(html, 'calendrier:lignes',
                     lignes_html(mbc, postes, affect, slugs, durees, courts, libres))
    mot = {1: 'un', 2: 'deux', 3: 'trois', 4: 'quatre',
           5: 'cinq', 6: 'six', 7: 'sept'}[r['domicile']]
    html = remplacer_compte(html, mot)

    for a in verifier_coherence(html, mbc):
        print('  !! %s' % a)

    # Les scores publies par la ligue redescendent dans data/matchs.json AVANT
    # la regeneration, sans quoi /matchs/ et les fiches resteraient muettes
    # pendant que la home afficherait le resultat.
    synchroniser_scores(mbc, essai=essai)

    if essai:
        print('\n  essai : %s' % ('des ecarts subsistent' if html != avant else 'index.html est deja a jour'))
        return 0

    io.open('index.html', 'w', encoding='utf-8', newline='\n').write(html)
    print('  index.html mis a jour' if html != avant else '  index.html etait deja a jour')

    regenerer_matchs()

    if depuis_archive:
        print('  (--archive : PDF et affiche laisses tels quels)')
        print('\n  ne pas oublier : python .claude/bump-assets.py')
        return 0

    shutil.copyfile(pdf, ARCHIVE)
    print('  PDF archive -> %s' % ARCHIVE)

    import importlib.util
    spec = importlib.util.spec_from_file_location('aff', '.claude/affiche-calendrier.py')
    aff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(aff)
    anciens = set(glob.glob('assets/affiches/calendrier-phase1-2026-2027*'))
    nouveau = aff.produire(mbc, AFFICHE)
    print('  affiche regeneree -> %s.png (+ 3 webp)' % nouveau)

    # repointer les URL de l'affiche dans la page, puis retirer les orphelins
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
