# -*- coding: utf-8 -*-
"""Lit le calendrier officiel PRM (PDF de la LRBB) et en sort des donnees sures.

Ce module ne produit RIEN pour le site : il se contente de lire le PDF et de
rendre la liste des rencontres. Il est separe pour une raison : le calendrier
change en cours de saison (l'article 4 du reglement autorise une derogation
jusqu'a 5 jours avant la rencontre), et entre le PDF du 21/08/2026 et celui du
25/08/2026 trois rencontres du MBC avaient deja change de camp. On veut donc
pouvoir relire un nouveau PDF sans retoucher quoi que ce soit a la main.

Structure du texte extrait, par rencontre :

    11/09/26 2030
    ...     ...          <- score, vide tant que la rencontre n'est pas jouee
    4                    <- numero de la rencontre dans la poule
    LA MONTAGNE BASKET CLUB          <- club recevant (nomme en premier)
    BASKET CLUB SAINTE SUZANNE       <- club visiteur

L'ordre des deux clubs porte l'information « domicile / exterieur » : l'article
10 du reglement rappelle que l'equipe nommee en premier est l'equipe locale.

L'horaire (« 2030 ») est lu rencontre par rencontre et non suppose : une
derogation peut le decaler, et c'est precisement ce que le site doit suivre.
"""
import datetime
import glob
import io
import os
import re

import fitz

MBC = 'LA MONTAGNE BASKET CLUB'

# Sigles officiels, article 2 du Reglement Sportif Particulier :
# « Zone NORD : MTG, BCD3, BJSSR, BC2S, MBC, PICKS3, SBBC et SMB2. »
# Ce ne sont donc pas des abreviations inventees.
CLUBS = {
    'ASSOCIATION MTG BASKETBALL':                    ('MTG',    'Association MTG Basketball'),
    'BASKET CLUB DIONYSIEN - 3':                     ('BCD3',   'Basket Club Dionysien 3'),
    'BASKET CLUB JEUNESSE SPORTIVE SAINTE ROSIENNE': ('BJSSR',  'BC Jeunesse Sportive Sainte-Rosienne'),
    'BASKET CLUB SAINTE SUZANNE':                    ('BC2S',   'Basket Club Sainte-Suzanne'),
    'LA MONTAGNE BASKET CLUB':                       ('MBC',    'MBC La Montagne Basket Club'),
    'PICKS BASKET LA POSSESSION - 3':                ('PICKS3', 'Picks Basket La Possession 3'),
    'SAINT BENOIT BASKET CLUB':                      ('SBBC',   u'Saint-Benoît Basket Club'),
    'SAINTE MARIE BASKET - 2':                       ('SMB2',   'Sainte-Marie Basket 2'),
}

MOIS = ['janv.', 'fevr.', 'mars', 'avril', 'mai', 'juin',
        'juil.', 'aout', 'sept.', 'oct.', 'nov.', 'dec.']
MOIS_LONG = ['janvier', 'fevrier', 'mars', 'avril', 'mai', 'juin',
             'juillet', 'aout', 'septembre', 'octobre', 'novembre', 'decembre']
JOURS = ['lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.', 'dim.']
JOURS_LONG = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']

LIGNE = re.compile(
    r'(\d{2})/(\d{2})/(\d{2})\s+(\d{4})\s*\n'      # date + horaire
    r'([^\n]*)\n'                                   # la ligne de score
    r'\s*(\d+)\s*\n'                                # numero de rencontre
    r'([^\n]+)\n'                                   # club recevant
    r'([^\n]+)\n')                                  # club visiteur


def normaliser(nom):
    """Le PDF sort « SAINT BENO<?>T » : l'accent circonflexe ne survit pas."""
    return (nom.replace(u'\ufffd', 'I').replace(u'\u00ce', 'I')
               .replace(u'\u00d4', 'O').upper().strip())


def score(brut):
    """Le score de la rencontre, ou None tant qu'elle n'est pas jouee.

    Tant qu'elle ne l'est pas, la LRBB imprime « ...     ... ». Une fois jouee,
    la meme ligne porte les deux totaux, l'equipe recevante d'abord (article 10).
    On ne rend un score que si on lit exactement DEUX entiers : dans le doute,
    rien. Le site n'affichera donc jamais un resultat devine.
    """
    n = re.findall(r'\d+', brut or '')
    if len(n) != 2:
        return None
    return {'recoit': int(n[0]), 'visite': int(n[1])}


def dernier_pdf(motif='C:/Users/ALEX/Downloads/CALENDRIER SENIOR PRM NORD*.pdf'):
    """Le plus recemment modifie parmi les telechargements correspondants."""
    trouves = glob.glob(motif)
    if not trouves:
        return None
    return max(trouves, key=os.path.getmtime)


def edite_le(chemin):
    """Date de generation imprimee en tete du PDF par la LRBB."""
    t = fitz.open(chemin)[0].get_text()
    m = re.search(r'Le (\d{2}/\d{2}/\d{4})\s*.\s*(\d{2}:\d{2}:\d{2})', t)
    return '%s a %s' % (m.group(1), m.group(2)) if m else 'date inconnue'


def edite_le_date(chemin):
    """La meme date d'edition, en ISO (AAAA-MM-JJ), ou None si illisible.

    Elle sert de « validFrom » aux offres « entree libre » du JSON-LD : c'est le
    jour ou la LRBB a publie ce calendrier, donc le jour a partir duquel
    l'information est vraie. Rien d'invente.
    """
    t = fitz.open(chemin)[0].get_text()
    m = re.search(r'Le (\d{2})/(\d{2})/(\d{4})', t)
    return '%s-%s-%s' % (m.group(3), m.group(2), m.group(1)) if m else None


def lire(chemin):
    """Rend (toutes_les_rencontres, rencontres_du_mbc). Leve si le PDF surprend."""
    doc = fitz.open(chemin)
    texte = '\n'.join(p.get_text() for p in doc)

    rencontres = []
    for m in LIGNE.finditer(texte):
        jj, mm, aa, hhmm, brut, num, recoit, visite = m.groups()
        d = datetime.date(2000 + int(aa), int(mm), int(jj))
        recoit, visite = normaliser(recoit), normaliser(visite)
        for c in (recoit, visite):
            if c not in CLUBS:
                raise ValueError('club inconnu dans le PDF : %r' % c)
        rencontres.append({
            'n': int(num), 'date': d.isoformat(),
            'heure': '%sh%s' % (hhmm[:2].lstrip('0'), hhmm[2:]),
            'iso_heure': '%s:%s' % (hhmm[:2], hhmm[2:]),
            'score': score(brut),
            'recoit': recoit, 'visite': visite,
        })

    if not rencontres:
        raise ValueError('aucune rencontre lue : le format du PDF a change ?')
    dates = sorted({r['date'] for r in rencontres})

    mbc = []
    for r in sorted((r for r in rencontres if MBC in (r['recoit'], r['visite'])),
                    key=lambda r: r['date']):
        domicile = r['recoit'] == MBC
        adverse = r['visite'] if domicile else r['recoit']
        sigle, nom = CLUBS[adverse]
        d = datetime.date.fromisoformat(r['date'])
        # Le score est range du point de vue du MBC : « pour » / « contre ».
        sc = r['score']
        if sc:
            sc = {'mbc': sc['recoit'] if domicile else sc['visite'],
                  'adverse': sc['visite'] if domicile else sc['recoit']}
        mbc.append(dict(r, domicile=domicile, sigle=sigle, adversaire=nom,
                        score=sc,
                        journee=dates.index(r['date']) + 1,
                        jour=JOURS[d.weekday()], jour_long=JOURS_LONG[d.weekday()],
                        num=d.day, annee=d.year,
                        mois=MOIS[d.month - 1], mois_long=MOIS_LONG[d.month - 1]))
    return rencontres, mbc


def resume(chemin):
    toutes, mbc = lire(chemin)
    dom = sum(1 for m in mbc if m['domicile'])
    return {'fichier': os.path.basename(chemin), 'edite_le': edite_le(chemin),
            'rencontres': len(toutes), 'journees': len({r['date'] for r in toutes}),
            'mbc': len(mbc), 'domicile': dom, 'exterieur': len(mbc) - dom}


if __name__ == '__main__':
    p = dernier_pdf()
    if not p:
        raise SystemExit('!! aucun PDF « CALENDRIER SENIOR PRM NORD*.pdf » dans Telechargements')
    print('  %s' % p)
    r = resume(p)
    print('  edite le %(edite_le)s' % r)
    print('  %(rencontres)d rencontres, %(journees)d journees' % r)
    print('  MBC : %(mbc)d rencontres -> %(domicile)d a domicile, %(exterieur)d en deplacement\n' % r)
    for m in lire(p)[1]:
        print('  J%(journee)d  %(jour)s %(num)2d %(mois)-6s %(heure)s  %(sigle)-6s  %(cote)s%(sc)s'
              % dict(m, cote='DOMICILE' if m['domicile'] else 'deplacement',
                     sc='' if not m['score'] else
                        '  %d-%d' % (m['score']['mbc'], m['score']['adverse'])))
