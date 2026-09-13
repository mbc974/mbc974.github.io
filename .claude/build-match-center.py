# -*- coding: utf-8 -*-
u"""Le Match Center des seniors : toute la saison, a partir de data/matchs.json.

    python .claude/build-matchs.py                     le chemin normal (il appelle ce script)
    python .claude/build-match-center.py               le bloc de l'accueil seul
    python .claude/build-match-center.py --essai       dit ce qui changerait, n'ecrit rien
    MBC_MAINTENANT=2026-09-19T08:00 python .claude/build-match-center.py --essai
                                                       la meme chose, a une autre date

POURQUOI
--------
La saison ne se resume plus aux sept journees de la phase 1. Le calendrier
general de la Ligue fixe aussi quatorze dates de 2e phase, quatre de phase
finale et cinq fenetres du Trophee Coupe de France. Aucune n'a d'adversaire :
le classement de la phase 1 decidera de la division (1 ou 2, reglement art. 3)
et des affiches ; la Coupe depend de la qualification du MBC. Il faut donc
montrer une saison complete SANS inventer une seule affiche : une date sans
adversaire est ecrite comme telle (« A determiner », « Selon qualification »).

LA SOURCE
---------
data/matchs.json, deux listes :
  matchs     les rencontres confirmees, chacune avec sa fiche /matchs/<slug>/ ;
  echeances  les dates fixees par la Ligue sans affiche connue.
Quand une affiche officielle tombe, on l'ajoute a « matchs » : l'echeance du
meme jour (ou de la meme journee, ou du meme tour) est ecartee ici, sans qu'on
ait a la retirer. Un score, une affiche : un seul endroit.

CE QU'IL ECRIT
--------------
  index.html   entre MATCH-CENTER:DEBUT / FIN : le dernier resultat, le prochain
               match, « A suivre », et le lien vers toute la saison ;
  matchs/      la page complete, via build-matchs.py (page_liste) : les deux
               cartes, les filtres, la saison mois par mois, le format.

LE TEMPS
--------
Le site est statique : « quel est le prochain match » depend de l'heure a
laquelle on OUVRE la page, pas de celle ou on l'a generee. Le HTML est donc
juste a la date de publication, et complet sans JavaScript. Pour les semaines
qui suivent, les cartes possibles sont ecrites d'avance dans des <template>
(les GABARITS prochaines rencontres, en « prochain » comme en « dernier ») :
script.js (bloc V181) choisit, a l'heure de La Reunion, celle qui s'applique,
et ne fabrique aucun texte. Une rencontre passee sans score dit « Score a
venir » : jamais de resultat devine.
"""
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
SOURCE = os.path.join(RACINE, 'data', 'matchs.json')
CIBLE = os.path.join(RACINE, 'index.html')
DEBUT = u'<!-- MATCH-CENTER:DEBUT'
FIN = u'<!-- MATCH-CENTER:FIN -->'

# La Reunion est a UTC+4 toute l'annee, sans heure d'ete : le decalage est
# ecrit en dur dans chaque instant publie, comme partout ailleurs sur le site.
FUSEAU = u'+04:00'
REUNION = timezone(timedelta(hours=4))

# Les cartes ecrites d'avance : de quoi tenir un mois sans republication sur
# /matchs/, trois semaines sur l'accueil. Pas davantage : chacune pese ~2 Ko
# (ecussons et srcset compris) et l'accueil porte deja beaucoup. Le site est
# republie a chaque score saisi, donc bien plus souvent que cela.
GABARITS = 4
GABARITS_ACCUEIL = 3
# « A suivre » sur l'accueil : quatre visibles, huit ecrites — les suivantes
# prennent le relais quand les premieres passent, sans republication.
SUIVRE, SUIVRE_ECRITS = 4, 8
# Une rencontre annulee ou reportee n'est jamais « le prochain match », ni « le
# dernier resultat » : elle reste dans la saison avec son etiquette, c'est tout.
HORS_JEU = ('annule', 'reporte')

JOURS = [u'lundi', u'mardi', u'mercredi', u'jeudi', u'vendredi', u'samedi', u'dimanche']
JOURS_C = [u'lun.', u'mar.', u'mer.', u'jeu.', u'ven.', u'sam.', u'dim.']
MOIS = [u'janvier', u'février', u'mars', u'avril', u'mai', u'juin', u'juillet',
        u'août', u'septembre', u'octobre', u'novembre', u'décembre']
MOIS_C = [u'janv.', u'févr.', u'mars', u'avr.', u'mai', u'juin', u'juil.',
          u'août', u'sept.', u'oct.', u'nov.', u'déc.']

FFBB = u'https://competitions.ffbb.com/ligues/reu/comites/0974/clubs/reu0974104'

FLECHE = (u'<svg class="btn__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
          u'stroke-width="2.4" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" '
          u'stroke-linecap="round" stroke-linejoin="round"/></svg>')
CHEVRON = (u'<span class="mc-i__go" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" '
           u'stroke="currentColor" stroke-width="2.4"><path d="m9 6 6 6-6 6" '
           u'stroke-linecap="round" stroke-linejoin="round"/></svg></span>')
# La coupe se reconnait a son pictogramme : un trait, pas un emoji — il suit
# la couleur du texte et reste net a toutes les tailles.
TROPHEE = (u'<svg class="mc-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
           u'stroke-width="2" aria-hidden="true"><path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0z" '
           u'stroke-linecap="round" stroke-linejoin="round"/><path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3" '
           u'stroke-linecap="round" stroke-linejoin="round"/></svg>')


# --------------------------------------------------------------------------
# Outils
# --------------------------------------------------------------------------
def maintenant():
    """L'heure de La Reunion, sans fuseau : les dates du JSON sont locales.
    MBC_MAINTENANT=AAAA-MM-JJTHH:MM la remplace, pour verifier un etat futur
    sans attendre qu'il arrive."""
    v = os.environ.get('MBC_MAINTENANT')
    if v:
        return datetime.strptime(v.strip()[:16], '%Y-%m-%dT%H:%M')
    return datetime.now(REUNION).replace(tzinfo=None)


def ech(t):
    return (u'%s' % t).replace(u'&', u'&amp;').replace(u'<', u'&lt;') \
        .replace(u'>', u'&gt;').replace(u'"', u'&quot;')


def iso(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:00') + FUSEAU


def plur(n, mot):
    return u'%d %s%s' % (n, mot, u's' if n > 1 else u'')


def date_longue(j):
    t = u'%s %d %s' % (JOURS[j.weekday()], j.day, MOIS[j.month - 1])
    return t[0].upper() + t[1:]


def equipe(nom, long_, sigle, logo, mbc=False):
    return {'nom': nom, 'long': long_, 'sigle': sigle, 'logo': logo, 'mbc': mbc}


def score_de(m):
    """Meme contrat que build-matchs.py : null, ou {"mbc": n, "adverse": n}."""
    s = m.get('score')
    if not s:
        return None
    if not isinstance(s, dict) or 'mbc' not in s or 'adverse' not in s:
        raise ValueError(u'data/matchs.json, %s : « score » vaut null ou '
                         u'{"mbc": <entier>, "adverse": <entier>}, pas %r' % (m.get('slug'), s))
    return int(s['mbc']), int(s['adverse'])


def remplacee(x, matchs):
    """Une echeance s'efface des qu'une rencontre confirmee la couvre : meme
    competition et meme jour — ou meme journee de la meme phase, ou meme tour.
    Le second critere survit a une derogation qui deplacerait la date."""
    for m in matchs:
        if (m.get('competition') or 'prm') != x.get('competition'):
            continue
        if m.get('date') == x.get('date'):
            return True
        # Une fenetre de Coupe est un week-end : un tour joue la veille ou le
        # lendemain la couvre aussi. Sans cela, un tour fixe au vendredi
        # laissait la fenetre du samedi affichee a cote : deux Coupes.
        if x.get('competition') == 'trcf':
            try:
                ecart = abs((datetime.strptime(m['date'], '%Y-%m-%d')
                             - datetime.strptime(x['date'], '%Y-%m-%d')).days)
            except (KeyError, TypeError, ValueError):
                ecart = 99
            if ecart <= 3:
                return True
        if (x.get('journee') and x.get('phase') and m.get('phase') == x.get('phase')
                and m.get('journee') == x.get('journee')
                and (m.get('manche') or u'') == (x.get('manche') or u'')):
            return True
        if (x.get('tour') and m.get('tour') == x.get('tour')
                and (m.get('phase') or u'') == (x.get('phase') or u'')):
            return True
    return False


# --------------------------------------------------------------------------
# La saison : une seule liste, dans l'ordre
# --------------------------------------------------------------------------
def entrees(d):
    comps = d.get('competitions') or {}
    phases = d.get('phases') or {}
    club, lieux = d['club'], d.get('lieux') or {}
    mbc = equipe(club['court'], club['nom'], club['sigle'], None, True)
    out = []
    for m in d['matchs']:
        cid = m.get('competition') or 'prm'
        dt = datetime.strptime(m['date'] + ' ' + m['heure'], '%Y-%m-%d %H:%M')
        L = lieux.get(m['lieu']) if m.get('lieu') else None
        adv = equipe(m['adversaireCourt'], m['adversaire'], m['sigle'], m.get('logo'))
        dom = bool(m['domicile'])
        out.append({
            'id': u'm-' + m['date'], 'kind': 'match', 'comp': cid,
            'phase': m.get('phase') or ('brassage' if cid == 'prm' else None),
            'debut': dt, 'fin': dt + timedelta(minutes=m.get('duree') or 120),
            'heure': m['heure'], 'dom': dom, 'mbc': mbc, 'adv': adv,
            'home': mbc if dom else adv, 'away': adv if dom else mbc,
            'score': score_de(m), 'statut': m.get('statut') or 'a-venir',
            'fiche': u'/matchs/%s/' % m['slug'],
            # build-matchs.py ecrit un .ics pour toute rencontre dont le lieu est connu
            'ics': (u'/assets/documents/%s.ics' % m['slug']) if L else None,
            'lieu': L, 'libre': bool(m.get('entreeLibre')),
            'journee': m.get('journee'), 'manche': m.get('manche'), 'tour': m.get('tour'),
        })
    for x in d.get('echeances') or []:
        if remplacee(x, d['matchs']):
            continue
        cid = x['competition']
        if x.get('heure'):
            dt = datetime.strptime(x['date'] + ' ' + x['heure'], '%Y-%m-%d %H:%M')
            fin = dt + timedelta(minutes=x.get('duree') or 150)
        else:
            # Pas d'horaire publie (la Coupe) : la date vaut pour toute la journee.
            dt = datetime.strptime(x['date'], '%Y-%m-%d')
            fin = dt + timedelta(hours=23, minutes=59)
        out.append({
            'id': u'e-%s-%s' % (cid, x['date']), 'kind': 'echeance', 'comp': cid,
            'phase': x.get('phase'), 'debut': dt, 'fin': fin, 'heure': x.get('heure'),
            'dom': None, 'mbc': mbc, 'adv': None, 'home': None, 'away': None,
            'score': None, 'statut': x.get('etat') or 'a-determiner',
            'fiche': None, 'ics': None, 'lieu': None, 'libre': False,
            'journee': x.get('journee'), 'manche': x.get('manche'), 'tour': x.get('tour'),
        })
    out.sort(key=lambda e: (e['debut'], e['kind'] != 'match'))
    for e in out:
        habiller(e, d, comps, phases)
    return out


def habiller(e, d, comps, phases):
    """Tous les libelles d'une entree, calcules une fois, ici."""
    comp = comps.get(e['comp']) or {'nom': d['competition']['nom'], 'court': u'PRM',
                                    'genre': 'championnat'}
    ph = phases.get(e['phase'] or u'') or {}
    e['genre'] = comp.get('genre') or 'championnat'
    j = e['debut']
    e['jour'] = j.date()
    e['debutIso'], e['finIso'] = iso(e['debut']), iso(e['fin'])
    e['dtAttr'] = e['debutIso'] if e['heure'] else e['jour'].isoformat()
    e['dateLongue'] = date_longue(j)
    e['dateCourte'] = u'%s %d %s' % (JOURS_C[j.weekday()], j.day, MOIS_C[j.month - 1])
    e['heureFr'] = e['heure'].replace(u':', u'h') if e['heure'] else None

    if e['journee']:
        et = u'J%d' % e['journee'] + (u' %s' % e['manche'] if e['manche'] else u'')
    else:
        et = e['tour'] or u''
    if e['genre'] == 'coupe':
        e['compLabel'] = u' · '.join([comp['nom']] + ([e['tour']] if e['tour'] else []))
    else:
        e['compLabel'] = u' · '.join([comp.get('court') or comp['nom']]
                                     + ([ph['court']] if ph.get('court') else [])
                                     + ([et] if et else []))

    if e['kind'] == 'match':
        e['titre'] = u'%s vs %s' % (e['home']['nom'], e['away']['nom'])
        e['lieuNom'] = e['lieu']['nom'] if e['lieu'] else u'Chez l’adversaire'
        if e['score']:
            p, c = e['score']
            e['scoreAff'] = (p, c) if e['dom'] else (c, p)     # dans l'ordre d'affichage
        if e['statut'] == 'annule':
            e['etat'] = ('annule', u'Annulé')
        elif e['statut'] == 'reporte':
            e['etat'] = ('reporte', u'Reporté')
        elif e['score']:
            p, c = e['score']
            e['etat'] = ('v', u'Victoire') if p > c else (('d', u'Défaite') if p < c else ('n', u'Match nul'))
        else:
            e['etat'] = ('dom', u'Domicile') if e['dom'] else ('ext', u'Extérieur')
        return

    # Une echeance : ce qu'on sait, et ce qu'on ne sait pas encore.
    e['etat'] = {'selon-qualification': ('q', u'Selon qualification'),
                 'selon-classement': ('tbd', u'Selon classement')}.get(e['statut'], ('tbd', u'À déterminer'))
    officiel = (u'%s, horaire officiel' % e['heureFr']) if e['heureFr'] else u''
    if e['genre'] == 'coupe':
        e['tbdNom'] = u'Adversaire à déterminer'
        e['tbdPhrase'] = u'Le MBC dispute ce tour s’il est qualifié ; adversaire, horaire et lieu seront connus ensuite.'
        e['tbdLigne'] = u'Adversaire à déterminer'
        e['detail'] = u'Horaire et lieu à déterminer'
    elif e['phase'] == 'finale':
        e['tbdNom'] = u'Selon classement'
        e['tbdPhrase'] = u'Réservée aux quatre premiers de la Division 1 à l’issue de la 2e phase.'
        e['tbdLigne'] = u'Affiche selon le classement de la Division 1'
        e['detail'] = u' · '.join([u'Quatre premiers de la Division 1'] + ([officiel] if officiel else []))
    else:
        e['tbdNom'] = u'Adversaire à déterminer'
        e['tbdPhrase'] = u'Après la phase de brassage : la division (1 ou 2) et les adversaires dépendent du classement.'
        e['tbdLigne'] = u'Adversaire à déterminer après la phase de brassage'
        e['detail'] = u' · '.join([u'Division 1 ou 2 selon le classement'] + ([officiel] if officiel else []))


def classer(es, now):
    """(dernier, prochain) a l'instant `now`.

    Le prochain est une rencontre CONFIRMEE (le coup de sifflet final fait
    foi, pas le coup d'envoi : un match en cours reste « le prochain ») ; a
    defaut, la prochaine echeance du championnat, puis de toute competition.
    Une fenetre de Coupe « selon qualification » ne passe jamais devant une
    rencontre confirmee. Le dernier est la derniere rencontre confirmee
    terminee — avec ou sans score."""
    passes = [e for e in es if e['kind'] == 'match' and e['fin'] < now and e['statut'] not in HORS_JEU]
    futurs = [e for e in es if e['fin'] >= now]
    prochain = next((e for e in futurs if e['kind'] == 'match' and e['statut'] not in HORS_JEU), None)
    if prochain is None:
        # Le repli ne prend que des echeances : une rencontre annulee ou
        # reportee ne doit jamais redevenir « le prochain match ».
        ech_ = [e for e in futurs if e['kind'] == 'echeance']
        prochain = next((e for e in ech_ if e['genre'] == 'championnat'), None) \
            or (ech_[0] if ech_ else None)
    return (passes[-1] if passes else None), prochain


def bilan(es):
    """« Bilan en championnat : 1 victoire, 0 défaite » — compte, jamais saisi."""
    v = dn = n = 0
    for e in es:
        if e['kind'] == 'match' and e['genre'] == 'championnat' and e['score']:
            p, c = e['score']
            v += p > c
            dn += p < c
            n += p == c
    if not (v or dn or n):
        return u''
    morceaux = [plur(v, u'victoire'), plur(dn, u'défaite')] + ([plur(n, u'nul')] if n else [])
    return u'Bilan en championnat : ' + u', '.join(morceaux)


# --------------------------------------------------------------------------
# Les pieces
# --------------------------------------------------------------------------
def crest(t, taille, eager=False):
    """L'ecusson est decoratif (alt vide, aria-hidden) : le nom est ecrit a
    cote. Sans fichier dans le depot, le sigle officiel prend sa place."""
    ch = u'eager' if eager else u'lazy'
    if t.get('mbc'):
        return (u'<span class="mc-crest" aria-hidden="true"><img src="/assets/logos/mbc-logo.webp" '
                u'alt="" width="288" height="296" loading="%s" decoding="async"></span>' % ch)
    logo = t.get('logo')
    if logo and os.path.exists(os.path.join(RACINE, 'assets', 'logos', 'clubs', logo + '.webp')):
        return (u'<span class="mc-crest" aria-hidden="true"><img src="/assets/logos/clubs/%s-144.webp" '
                u'srcset="/assets/logos/clubs/%s-144.webp 144w, /assets/logos/clubs/%s.webp 288w" '
                u'sizes="%dpx" alt="" width="288" height="288" loading="%s" decoding="async"></span>'
                % (logo, logo, logo, taille, ch))
    return u'<span class="mc-crest mc-crest--sigle" aria-hidden="true">%s</span>' % ech(t.get('sigle') or u'?')


def carte_prochain(e, n, page, cd=False, eager=False, saison=u'/matchs/'):
    """La rencontre principale. Une echeance sans affiche peut l'occuper (fin
    de phase, affiches pas encore publiees) : elle le dit, sans rien inventer."""
    tbd = e['kind'] != 'match'
    tags = [u'<span class="mc-tag">%s</span>' % ech(e['compLabel'])]
    if not tbd:
        tags.append(u'<span class="mc-tag mc-tag--dom">Domicile</span>' if e['dom']
                    else u'<span class="mc-tag mc-tag--ext">Extérieur</span>')
        if e['dom'] and e['libre']:
            tags.append(u'<span class="mc-tag mc-tag--libre">Entrée libre</span>')
    vs = u'<span class="mc-vs"><span aria-hidden="true">vs</span><span class="sr-only"> contre </span></span>'
    if tbd:
        duel = (u'<p class="mc-duel mc-duel--tbd"><span class="mc-team">%s<span class="mc-team__n">%s</span></span>%s'
                u'<span class="mc-team mc-team--tbd"><span class="mc-crest mc-crest--vide" aria-hidden="true"></span>'
                u'<span class="mc-team__n">%s</span></span></p>\n      <p class="mc-tbd">%s</p>'
                % (crest(e['mbc'], 64, eager), ech(e['mbc']['nom']), vs, ech(e['tbdNom']), ech(e['tbdPhrase'])))
        heure = ((u'%s <span class="mc-fact__s">horaire officiel</span>' % e['heureFr'])
                 if e['heureFr'] else u'À déterminer')
        lieu = u'À déterminer'
    else:
        duel = (u'<p class="mc-duel"><span class="mc-team">%s<span class="mc-team__n">%s</span></span>%s'
                u'<span class="mc-team">%s<span class="mc-team__n">%s</span></span></p>'
                % (crest(e['home'], 64, eager), ech(e['home']['nom']), vs,
                   crest(e['away'], 64, eager), ech(e['away']['nom'])))
        heure = e['heureFr']
        L = e['lieu']
        lieu = ((u'%s <span class="mc-fact__s">%s, %s %s</span>'
                 % (ech(L['nom']), ech(L['adresse']), ech(L['codePostal']), ech(L['ville'])))
                if L else u'Chez l’adversaire')
    faits = (u'<dl class="mc-facts">'
             u'<div class="mc-fact mc-fact--date"><dt>Date</dt><dd><time datetime="%s">%s</time></dd></div>'
             u'<div class="mc-fact"><dt>Coup d’envoi</dt><dd>%s</dd></div>'
             u'<div class="mc-fact mc-fact--lieu"><dt>Lieu</dt><dd>%s</dd></div></dl>'
             % (e['dtAttr'], ech(e['dateLongue']), heure, lieu))
    act = []
    if not tbd:
        act.append(u'<a class="btn btn--primary mc-cta" href="%s">Voir le match%s'
                   u'<span class="sr-only"> %s</span></a>' % (e['fiche'], FLECHE, ech(e['titre'])))
        if e['lieu']:
            act.append(u'<a class="mc-lien" href="%s" target="_blank" rel="noopener">Itinéraire'
                       u'<span class="sr-only"> vers %s (Google Maps, nouvel onglet)</span></a>'
                       % (ech(e['lieu']['carte']), ech(e['lieu']['nom'])))
        if e['ics']:
            act.append(u'<a class="mc-lien" href="%s" download>Ajouter à l’agenda'
                       u'<span class="sr-only"> (fichier .ics)</span></a>' % e['ics'])
    else:
        act.append(u'<a class="mc-lien" href="%s">Toute la saison</a>' % saison)
    compte = u'\n      <p class="mc-cd" data-mc-cd hidden></p>' if (cd and not tbd) else u''
    return (u'<article class="mc-next%s" data-id="%s" data-debut="%s" data-fin="%s" data-rang="%d">\n'
            u'      <div class="mc-next__top"><h%d class="mc-eyebrow"><span class="mc-dot" aria-hidden="true"></span>%s</h%d>'
            u'<p class="mc-tags">%s</p></div>\n'
            u'      %s\n      %s%s\n'
            u'      <p class="mc-next__a">%s</p>\n'
            u'    </article>'
            % (u' mc-next--tbd' if tbd else u'', e['id'], e['debutIso'], e['finIso'], 1 if tbd else 0,
               n, u'Prochaine échéance' if tbd else u'Prochain match', n,
               u''.join(tags), duel, faits, compte, u''.join(act)))


def carte_dernier(e, n, page, bilan_txt=u'', eager=False):
    """Le dernier resultat : deux lignes de tableau d'affichage, le recevant en
    premier, le score du vainqueur en blanc. Une rencontre terminee dont le
    score n'est pas encore saisi le dit, sans chiffres."""
    adv = e['adv']['nom']
    sc = e['score']
    if sc:
        p, c = sc
        hs, as_ = e['scoreAff']
        cls, mot = e['etat']
        phrase = ((u'Match nul, %d à %d contre %s' % (p, c, adv)) if cls == 'n'
                  else (u'%s du MBC, %d à %d contre %s' % (mot, p, c, adv)))
        phrase += u', à domicile.' if e['dom'] else u', à l’extérieur.'
        issue = u'<span class="mc-issue mc-issue--%s" aria-hidden="true">%s</span>' % (cls, mot)
        mod = cls
    else:
        hs = as_ = None
        phrase = u'Rencontre terminée contre %s : résultat à venir.' % adv
        issue = u'<span class="mc-issue mc-issue--attente" aria-hidden="true">Résultat à venir</span>'
        mod = u'attente'

    def ligne(t, s, gagne):
        chiffre = (u'<span class="mc-row__s">%d</span>' % s) if s is not None \
            else u'<span class="mc-row__s mc-row__s--vide">–</span>'
        return (u'<p class="mc-row%s">%s<span class="mc-row__n">%s</span>%s</p>'
                % (u' mc-row--gagne' if gagne else u'', crest(t, 40, eager), ech(t['nom']), chiffre))

    board = (ligne(e['home'], hs, bool(sc) and hs > as_)
             + ligne(e['away'], as_, bool(sc) and as_ > hs))
    bil = (u'\n      <p class="mc-bilan">%s</p>' % ech(bilan_txt)) if bilan_txt else u''
    return (u'<article class="mc-res mc-res--%s" data-id="%s" data-debut="%s" data-fin="%s">\n'
            u'      <div class="mc-res__top"><h%d class="mc-eyebrow mc-eyebrow--calme">Dernier résultat</h%d>'
            u'<p class="mc-tags"><span class="mc-tag">%s</span><span class="mc-tag mc-tag--date">'
            u'<time datetime="%s">%s</time></span></p></div>\n'
            u'      <p class="sr-only">%s</p>\n'
            u'      <div class="mc-board" aria-hidden="true">%s</div>\n'
            u'      <p class="mc-res__foot">%s<span class="mc-res__lieu">%s</span>'
            u'<a class="mc-lien" href="%s">Fiche du match<span class="sr-only"> %s</span></a></p>%s\n'
            u'    </article>'
            % (mod, e['id'], e['debutIso'], e['finIso'], n, n, ech(e['compLabel']),
               e['dtAttr'], ech(e['dateCourte']), ech(phrase), board, issue, ech(e['lieuNom']),
               e['fiche'], ech(e['titre']), bil))


def item(e, now, id_next, cache=False):
    """Une date de la saison. Une rencontre confirmee est un lien vers sa fiche ;
    une echeance n'a pas de page et n'est donc pas un lien."""
    cl = [u'mc-i', u'mc-i--' + e['kind'], u'mc-i--' + e['genre']]
    if e['kind'] == 'match':
        cl.append(u'mc-i--dom' if e['dom'] else u'mc-i--ext')
        if e['score']:
            cl.append(u'mc-i--joue')
    passe = e['fin'] < now
    live = e['kind'] == 'match' and e['debut'] <= now <= e['fin']
    if passe:
        cl.append(u'is-past')
    if live:
        cl.append(u'is-live')
    if e['id'] == id_next:
        cl.append(u'is-next')
    j = e['debut']
    date = (u'<time class="mc-i__d" datetime="%s"><span class="mc-i__dj">%s</span>'
            u'<span class="mc-i__dn">%d</span><span class="mc-i__dm">%s</span></time>'
            % (e['dtAttr'], JOURS_C[j.weekday()], j.day, MOIS_C[j.month - 1]))
    comp = (TROPHEE if e['genre'] == 'coupe' else u'') + ech(e['compLabel'])
    if e['kind'] == 'match':
        duel = (u'<span class="mc-i__duel"><span class="mc-i__t">%s<b>%s</b></span>'
                u'<span class="mc-i__vs" aria-hidden="true">vs</span><span class="sr-only"> contre </span>'
                u'<span class="mc-i__t">%s<b>%s</b></span></span>'
                % (crest(e['home'], 28), ech(e['home']['nom']), crest(e['away'], 28), ech(e['away']['nom'])))
        # Rencontre jouee : le score prend la place de l'heure, a droite.
        meta = ech(e['lieuNom']) if e['score'] else u'%s · %s' % (e['heureFr'], ech(e['lieuNom']))
        if e['dom'] and e['libre'] and not e['score']:
            meta += u' · Entrée libre'
    else:
        duel = u'<span class="mc-i__duel mc-i__duel--tbd">%s</span>' % ech(e['tbdLigne'])
        meta = ech(e['detail'])
    fin = []
    if e['score']:
        h, a = e['scoreAff']
        fin.append(u'<span class="mc-i__score"><span class="sr-only">Score : </span>%d'
                   u'<span class="mc-i__sep" aria-hidden="true">–</span><span class="sr-only"> à </span>%d</span>'
                   % (h, a))
    if e['kind'] == 'match':
        fin.append(u'<span class="mc-i__next"%s>Prochain match</span>'
                   % (u'' if e['id'] == id_next else u' hidden'))
    cls, mot = e['etat']
    donnees, attente = u'', False
    if e['kind'] == 'match' and not e['score'] and e['statut'] not in ('annule', 'reporte'):
        # Les trois libelles possibles sont ecrits ici ; script.js ne fait que
        # choisir, a l'heure de La Reunion. Il n'invente aucun mot.
        donnees = u' data-avenir="%s" data-live="En cours" data-apres="Score à venir"' % mot
        if live:
            mot = u'En cours'
        elif passe:
            mot, attente = u'Score à venir', True
    fin.append(u'<span class="mc-i__etat mc-i__etat--%s%s"%s>%s</span>'
               % (cls, u' is-attente' if attente else u'', donnees, mot))
    corps = (u'%s<span class="mc-i__corps"><span class="mc-i__c">%s</span>%s<span class="mc-i__m">%s</span></span>'
             u'<span class="mc-i__fin">%s</span>' % (date, comp, duel, meta, u''.join(fin)))
    if e['fiche']:
        dedans = (u'<a class="mc-i__a" href="%s">%s%s<span class="sr-only"> — fiche du match</span></a>'
                  % (e['fiche'], corps, CHEVRON))
    else:
        dedans = u'<div class="mc-i__a">%s</div>' % corps
    lieu = (u'dom' if e['dom'] else u'ext') if e['kind'] == 'match' else u''
    return (u'<li class="%s" data-id="%s" data-debut="%s" data-fin="%s" data-genre="%s" data-lieu="%s"%s>%s</li>'
            % (u' '.join(cl), e['id'], e['debutIso'], e['finIso'], e['genre'], lieu,
               u' hidden' if cache else u'', dedans))


def gabarits(es, now, dernier, prochain, n, page, cd=False, saison=u'/matchs/', bilan_txt=u'', nb=GABARITS):
    """Les cartes des semaines qui viennent, inertes dans des <template>.

    - « prochain » : les GABARITS rencontres confirmees qui suivent celle en
      place. Les echeances du championnat ne s'ajoutent en repli que si TOUTES
      les rencontres confirmees a venir sont deja couvertes : sinon, une fois
      les gabarits epuises, la 2e phase passerait devant une journee connue.
    - « dernier » : ces memes rencontres, vues comme terminees, score a venir.
      Une rencontre dont le score est saisi est republiee de toute facon."""
    futurs_m = [e for e in es if e['kind'] == 'match' and e['fin'] >= now and e['statut'] not in HORS_JEU]
    autres = [e for e in futurs_m if not prochain or e['id'] != prochain['id']]
    suivants = autres[:nb]
    repli = []
    if len(autres) <= nb:
        borne = futurs_m[-1]['debut'] if futurs_m else now
        repli = [e for e in es if e['kind'] == 'echeance' and e['genre'] == 'championnat'
                 and e['fin'] >= now and e['debut'] > borne
                 and (not prochain or e['id'] != prochain['id'])][:2]
    out = []
    for e in suivants + repli:
        out.append(u'  <template data-mc-t="prochain" data-id="%s" data-debut="%s" data-fin="%s" data-rang="%d">'
                   u'%s</template>' % (e['id'], e['debutIso'], e['finIso'], 0 if e['kind'] == 'match' else 1,
                                       carte_prochain(e, n, page, cd=cd, saison=saison)))
    # Une de plus qu'en « prochain » : la carte en place, puis les nb gabarits.
    # Sinon, gabarits epuises, « Dernier resultat » montrait un match plus
    # ancien que le dernier joue.
    for e in futurs_m[:nb + 1]:
        out.append(u'  <template data-mc-t="dernier" data-id="%s" data-debut="%s" data-fin="%s">%s</template>'
                   % (e['id'], e['debutIso'], e['finIso'], carte_dernier(dict(e, score=None), n, page, bilan_txt)))
    return u'\n'.join(out)


def duo(es, now, n, page, cd=False, eager=False, saison=u'/matchs/', nb=GABARITS):
    dernier, prochain = classer(es, now)
    bil = bilan(es)
    s_d = ((u'<div class="mc__slot" data-mc-slot="dernier">\n    %s\n  </div>' % carte_dernier(dernier, n, page, bil, eager))
           if dernier else u'<div class="mc__slot" data-mc-slot="dernier" hidden></div>')
    s_p = ((u'<div class="mc__slot" data-mc-slot="prochain">\n    %s\n  </div>'
            % carte_prochain(prochain, n, page, cd=cd, eager=eager, saison=saison))
           if prochain else u'<div class="mc__slot" data-mc-slot="prochain" hidden></div>')
    seul = u'' if (dernier and prochain) else u' mc__duo--seul'
    return (u'<div class="mc__duo%s">\n  %s\n  %s\n</div>' % (seul, s_d, s_p),
            gabarits(es, now, dernier, prochain, n, page, cd=cd, saison=saison, bilan_txt=bil, nb=nb),
            dernier, prochain)


def compte(es):
    n_m = sum(1 for e in es if e['kind'] == 'match')
    return u'%d dates · %s' % (len(es), plur(n_m, u'rencontre confirmée').replace(u'rencontre confirmées', u'rencontres confirmées'))


# --------------------------------------------------------------------------
# L'accueil
# --------------------------------------------------------------------------
def bloc_accueil(d, es, now):
    html_duo, tpl, dernier, prochain = duo(es, now, 3, u'accueil', cd=False, saison=u'/matchs/',
                                           nb=GABARITS_ACCUEIL)
    id_next = prochain['id'] if prochain else None
    futurs = [e for e in es if e['fin'] >= now and e['id'] != id_next][:SUIVRE_ECRITS]
    lis = u'\n'.join(u'      ' + item(e, now, id_next, cache=(k >= SUIVRE)) for k, e in enumerate(futurs))
    return (u'%s — genere par .claude/build-match-center.py (lance par build-matchs.py), ne pas editer a la main -->\n'
            u'    <div class="mc reveal" data-mc="accueil" data-publie="%s">\n'
            u'%s\n'
            u'    <div class="mc-suite"%s>\n'
            u'      <h3 class="mc-suite__t">À suivre</h3>\n'
            u'      <ol class="mc-list mc-list--suite" data-max="%d">\n%s\n      </ol>\n'
            u'    </div>\n'
            u'    <p class="mc-tout"><a class="mc-tout__a" href="/matchs/"><span class="mc-tout__l">Toute la saison</span>'
            u'<span class="mc-tout__n">%s · championnat et Coupe de France</span>%s</a></p>\n'
            u'%s\n'
            u'    </div>\n'
            u'    %s'
            % (DEBUT, now.strftime('%Y-%m-%dT%H:%M'), html_duo, u'' if futurs else u' hidden',
               SUIVRE, lis, compte(es), FLECHE, tpl, FIN))


# --------------------------------------------------------------------------
# La page /matchs/
# --------------------------------------------------------------------------
def phase_en_cours(es, now):
    for ph in ('brassage', 'phase2', 'finale'):
        fins = [e['fin'] for e in es if e['comp'] == 'prm' and e['phase'] == ph]
        if fins and max(fins) >= now:
            return ph
    return None


def page_corps(d, es, now, fil):
    """Le <main> de /matchs/. build-matchs.py l'enveloppe du gabarit du site."""
    html_duo, tpl, dernier, prochain = duo(es, now, 2, u'saison', cd=True, eager=True, saison=u'#saison')
    id_next = prochain['id'] if prochain else None

    mois = []
    for e in es:
        cle = (e['jour'].year, e['jour'].month)
        if not mois or mois[-1][0] != cle:
            mois.append((cle, []))
        mois[-1][1].append(e)
    cle_now = (now.year, now.month)
    nav, blocs = [], []
    for (a, m), liste in mois:
        mid = u'mois-%d-%02d' % (a, m)
        courant = (a, m) == cle_now
        nav.append(u'<li><a class="ms-mois__a%s" href="#%s"%s><span aria-hidden="true">%s</span>'
                   u'<span class="sr-only">%s %d</span></a></li>'
                   % (u' is-courant' if courant else u'', mid, u' aria-current="true"' if courant else u'',
                      MOIS_C[m - 1].capitalize(), MOIS[m - 1].capitalize(), a))
        blocs.append(u'      <section class="ms-m" id="%s" aria-labelledby="%s-t">\n'
                     u'        <h3 class="ms-m__t" id="%s-t">%s <span>%d</span></h3>\n'
                     u'        <ol class="mc-list">\n%s\n        </ol>\n'
                     u'      </section>'
                     % (mid, mid, mid, MOIS[m - 1].capitalize(), a,
                        u'\n'.join(u'          ' + item(e, now, id_next) for e in liste)))

    barre = (u'      <div class="ms-bar" data-ms-bar hidden>\n'
             u'        <div class="ms-f" role="group" aria-label="Filtrer par compétition">'
             u'<button type="button" class="ms-f__b" data-f="genre" data-v="" aria-pressed="true">Tous</button>'
             u'<button type="button" class="ms-f__b" data-f="genre" data-v="championnat" aria-pressed="false">Championnat</button>'
             u'<button type="button" class="ms-f__b" data-f="genre" data-v="coupe" aria-pressed="false">Coupe</button></div>\n'
             u'        <div class="ms-f" role="group" aria-label="Filtrer par lieu">'
             u'<button type="button" class="ms-f__b" data-f="lieu" data-v="" aria-pressed="true">Partout</button>'
             u'<button type="button" class="ms-f__b" data-f="lieu" data-v="dom" aria-pressed="false">Domicile</button>'
             u'<button type="button" class="ms-f__b" data-f="lieu" data-v="ext" aria-pressed="false">Extérieur</button></div>\n'
             u'        <p class="ms-bar__n is-repos" data-ms-n aria-live="polite">%s</p>\n'
             u'      </div>' % plur(len(es), u'date'))

    # Le format, repris du reglement (art. 3 et 4) et des definitions de
    # data/matchs.json : rien ici n'est une interpretation.
    ph_now = phase_en_cours(es, now)
    phases = d.get('phases') or {}
    etapes = []
    for ph in ('brassage', 'phase2', 'finale'):
        p = phases.get(ph)
        if not p:
            continue
        etapes.append(u'<li><b>%s</b><span>%s</span>%s</li>'
                      % (ech(p['nom']), ech(p['detail']),
                         u'<span class="lp-who lp-who--vous">La phase en cours</span>' if ph == ph_now else u''))
    etapes.append(u'<li><b>Trophée Coupe de France</b><span>En parallèle du championnat. La Ligue réserve les dates '
                  u'ci-dessus ; le MBC ne joue un tour que s’il est qualifié, et l’adversaire, l’horaire et le '
                  u'lieu ne sont connus qu’ensuite.</span></li>')
    poule = d.get('poule') or {}
    equipes = u''.join(
        u'<li class="ms-poule__i%s">%s<span>%s</span></li>'
        % (u' ms-poule__i--mbc' if t.get('mbc') else u'',
           crest(equipe(t.get('court') or t['nom'], t['nom'], t['sigle'], t.get('logo'), bool(t.get('mbc'))), 44),
           ech(t['nom']))
        for t in poule.get('equipes') or [])
    bloc_poule = ((u'\n      <div class="ms-poule">\n        <h3 class="ms-poule__t">%s</h3>\n'
                   u'        <ul class="ms-poule__l">%s</ul>\n      </div>' % (ech(poule.get('nom') or u'La poule'), equipes))
                  if equipes else u'')

    return u"""<main id="contenu">
  <section class="section mc-page">
    <div class="wrap">
      %(fil)s
      <header class="mc-page__head">
        <p class="kicker">Seniors <i aria-hidden="true"></i> Saison %(saison)s</p>
        <h1 class="h2">Les matchs <span class="hl">de la saison</span></h1>
        <p class="sec-head__sub">L’équipe seniors du MBC La Montagne, en Pré-Régionale Masculine (zone Nord) et en Trophée Coupe de France. À domicile, rendez-vous au Gymnase de La Montagne, à Saint-Denis&nbsp;: l’entrée est libre.</p>
      </header>
      <div class="mc" data-mc="saison" data-publie="%(publie)s">
%(duo)s
%(tpl)s
      </div>
      <section class="ms" id="saison" aria-labelledby="msT">
        <div class="ms__head"><h2 class="ms__t" id="msT">Toute la saison</h2><p class="ms__n">%(compte)s</p></div>
%(barre)s
        <nav class="ms-mois" aria-label="Aller au mois"><ol class="ms-mois__l">%(nav)s</ol></nav>
        <p class="ms-vide" data-ms-vide hidden>Aucune date ne correspond à ces filtres.</p>
%(blocs)s
      </section>
    </div>
  </section>
  <section class="section ms-format" id="format" aria-labelledby="msFormatT">
    <div class="wrap">
      <h2 class="ms-format__t" id="msFormatT">Le format <span class="hl">de la saison</span></h2>
      <ol class="licence-path">%(etapes)s</ol>%(poule)s
      <p class="ms-sources">Sources&nbsp;: le calendrier de la poule publié par la Ligue le 25&nbsp;août 2026, le calendrier général sportif 2026-2027 (version V2) et le règlement sportif particulier de la Pré-Régionale Masculine. L’horaire officiel est le vendredi à 20h30&nbsp;; une rencontre peut être décalée par dérogation, et le calendrier officiel de la FFBB fait alors foi.</p>
      <p class="ms-liens"><a class="btn btn--ghost" href="%(ffbb)s" target="_blank" rel="noopener">Résultats &amp; classement officiels<span class="sr-only"> (FFBB, nouvel onglet)</span></a><a class="mc-lien" href="/assets/documents/calendrier-prm-nord-2026-2027.pdf" target="_blank" rel="noopener">Calendrier de la poule<span class="sr-only"> (PDF, nouvel onglet)</span></a><a class="mc-lien" href="/assets/documents/reglement-sportif-prm-2026-2027.pdf" target="_blank" rel="noopener">Règlement sportif<span class="sr-only"> (PDF, nouvel onglet)</span></a></p>
      <p class="ml__retour"><a href="/#matchs">Revenir à l’accueil</a></p>
    </div>
  </section>
</main>""" % {
        'fil': fil, 'saison': ech(d.get('saison') or d['competition']['saison']),
        'publie': now.strftime('%Y-%m-%dT%H:%M'), 'duo': html_duo, 'tpl': tpl,
        'compte': compte(es), 'barre': barre, 'nav': u''.join(nav), 'blocs': u'\n'.join(blocs),
        'etapes': u''.join(etapes), 'poule': bloc_poule, 'ffbb': FFBB,
    }


# --------------------------------------------------------------------------
def main():
    essai = '--essai' in sys.argv
    d = json.load(io.open(SOURCE, encoding='utf-8'))
    now = maintenant()
    es = entrees(d)
    dernier, prochain = classer(es, now)
    html = io.open(CIBLE, encoding='utf-8').read()
    i, j = html.find(DEBUT), html.find(FIN)
    if i < 0 or j < 0:
        print(u'  !! marqueurs MATCH-CENTER absents de index.html')
        return 1
    neuf = html[:i] + bloc_accueil(d, es, now) + html[j + len(FIN):]
    print(u'  Match Center : %s' % compte(es))
    print(u'  a la date du  %s' % now.strftime('%d/%m/%Y %H:%M'))
    print(u'  dernier       %s' % ((u'%s, %s%s' % (dernier['titre'], dernier['dateCourte'],
                                                   (u' (%d-%d)' % dernier['scoreAff']) if dernier['score'] else u', score a venir'))
                                  if dernier else u'aucun'))
    print(u'  prochain      %s' % ((u'%s, %s' % (prochain.get('titre') or prochain['compLabel'], prochain['dateCourte']))
                                  if prochain else u'aucun'))
    if neuf == html:
        print(u'  accueil : deja a jour')
        return 0
    if essai:
        print(u'  essai : le bloc de l\'accueil changerait')
        return 0
    io.open(CIBLE, 'w', encoding='utf-8', newline='\n').write(neuf)
    print(u'  accueil : bloc MATCH-CENTER ecrit — lancer bump-assets.py')
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
