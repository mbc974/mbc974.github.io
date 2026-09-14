# -*- coding: utf-8 -*-
u"""Purge des anciens styles d'en-tête et de pied de page (V185, 14/09/2026).

    python .claude/purger-entete-pied.py --essai    montre ce qui partirait
    python .claude/purger-entete-pied.py            écrit style.css
    puis : python .claude/build-css.py && python .claude/bump-assets.py

POURQUOI
--------
V182 a donné à toutes les pages l'en-tête de l'accueil, et V184 son pied de
page, adhesion.html comprise. Trois familles de styles ne ciblent donc plus
aucun élément :
- l'ancienne barre des pages enfants : .seo-top, .seo-top__brand,
  .seo-top__nav et html:has(.seo-top) ;
- l'ancien pied des pages enfants : .seo-foot, .seo-foot__links ;
- l'ancien pied d'adhesion.html : .footer__tag, .footer__actions,
  .footer__trust (et -h, -link), .footer__mini-logo, .footer__brand .small.

Vérifié le 14/09/2026 avant d'écrire la liste. Aucune de ces classes n'est
posée par le markup des 27 pages, ni par script.js / consent.js / sw.js, ni
par un générateur (build-*, set-*, affiche-*), ni par data/*.json. script.js
CHERCHE encore .seo-foot (floatCta : '.site-footer, .seo-foot') ; mais
chercher n'est pas porter, et ce sélecteur-là est du JS, pas un style.

LE BLOC « PETIT LOGO MBC DANS LA BARRE BASSE »
----------------------------------------------
Il n'existait que pour .footer__mini-logo. Ses autres règles visent des
classes vivantes (.footer__bottom, .footer__legal), mais sont inertes : plus
bas dans la feuille, .footer__bottom repasse en display:flex, et ni
grid-template-columns ni justify-self n'agissent dans un conteneur flex. Le
bloc part en entier, repéré par son commentaire, et son contenu est contrôlé
avant retrait : il doit viser ces trois classes et rien d'autre.

MÉTHODE
-------
- Les commentaires sont masqués AVANT l'analyse, positions conservées. Sinon
  une virgule ou une accolade de commentaire fausse le découpage.
- Une liste de sélecteurs n'est coupée que sur ses virgules de premier niveau,
  jamais sur celles d'un :is() ou d'un :not().
- Une règle dont tous les sélecteurs sont morts part. Sinon, seuls les
  sélecteurs morts partent.
- Un @media ou un @supports vidé par CETTE purge part avec elle. Les blocs
  déjà vides avant ne sont pas touchés : un sujet par purge.
- Le fichier est écrit AVANT tout affichage, puis relu pour vérifier l'effet
  (leçon du 07/09 : un script qui annonce avant d'écrire peut n'avoir rien
  écrit).
"""
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(RACINE, 'style.css')
# « .footer__brand p.small » aussi : la première version du motif ne voyait
# que « .footer__brand .small » et laissait passer la règle de la l. 652.
MORT = re.compile(r'\.seo-top\b|\.seo-top__|\.seo-foot\b|\.seo-foot__|\.footer__tag\b|\.footer__actions\b|'
                  r'\.footer__trust|\.footer__mini-logo\b|\.footer__brand\s+(?:[a-z][a-z0-9]*)?\.small\b')
LOGO = u'/* ---- Footer : petit logo MBC dans la barre basse ---- */'
LOGO_CLASSES = {'.footer__bottom', '.footer__mini-logo', '.footer__legal'}
VIDE = re.compile(r'@(?:media|supports)[^{]*\{\s*\}')


def masque(css):
    out = list(css)
    for m in re.finditer(r'/\*.*?\*/', css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def parts(sel):
    """Les sélecteurs d'une liste, coupée sur les virgules de premier niveau."""
    out, prof, cur = [], 0, ''
    for c in sel:
        if c == '(':
            prof += 1
        elif c == ')':
            prof -= 1
        if c == ',' and prof == 0:
            out.append(cur.strip())
            cur = ''
        else:
            cur += c
    out.append(cur.strip())
    return [p for p in out if p]


def debut_de_ligne(css, pos):
    """Recule sur les blancs et le saut de ligne qui précèdent, pour ne pas
    laisser de trou."""
    while pos > 0 and css[pos - 1] in ' \t':
        pos -= 1
    if pos > 0 and css[pos - 1] == '\n':
        pos -= 1
    return pos


def bloc_logo(css, mc):
    """Bornes du bloc « petit logo », contrôlé règle par règle."""
    if css.count(LOGO) != 1:
        raise SystemExit(u"!! commentaire du bloc « petit logo » introuvable ou en double")
    a = css.index(LOGO)
    i, prof, fin, media_vu = a + len(LOGO), 0, None, False
    debut = i
    while i < len(mc):
        c = mc[i]
        if c == '{':
            prelude = mc[debut:i].strip()
            if prelude.startswith('@'):
                if media_vu or not re.match(r'@media\s*\(max-width:\s*700px\)$', prelude):
                    raise SystemExit(u"!! bloc « petit logo » : at-règle inattendue : " + prelude)
                media_vu = True
            elif not set(parts(re.sub(r'\s+', ' ', prelude))) <= LOGO_CLASSES:
                raise SystemExit(u"!! bloc « petit logo » : sélecteur inattendu : " + prelude)
            prof += 1
            debut = i + 1
        elif c == '}':
            prof -= 1
            debut = i + 1
            if prof == 0 and media_vu:
                fin = i + 1
                break
        i += 1
    if fin is None:
        raise SystemExit(u"!! bloc « petit logo » : fin introuvable")
    return debut_de_ligne(css, a), fin


def plan(css):
    mc = masque(css)
    la, lb = bloc_logo(css, mc)
    edits = [(la, lb, u'')]
    # Pile de cadres : [prélude, début du prélude, arrêts des enfants]. Un
    # enfant est « retiré » s'il s'agit d'une règle morte ou d'un bloc vidé.
    pile = [['', 0, [], []]]
    entieres, allegees, blocs, debut = 0, 0, 0, 0
    i = 0
    while i < len(mc):
        c = mc[i]
        if c == '{':
            brut = mc[debut:i]
            prelude = brut.strip()
            deb = debut + (len(brut) - len(brut.lstrip()))
            if prelude.startswith('@'):
                pile.append([prelude, deb, [], []])
                debut = i + 1
            else:
                fin = mc.index('}', i) + 1
                sel = re.sub(r'\s+', ' ', prelude)
                cadre = pile[-1]
                dans_logo = la <= deb < lb
                if MORT.search(sel) and not dans_logo:
                    ps = parts(sel)
                    vivants = [p for p in ps if not MORT.search(p)]
                    if vivants:
                        cadre[2].append((deb, deb + len(prelude), u','.join(vivants), False))
                        allegees += 1
                    else:
                        cadre[2].append((debut_de_ligne(css, deb), fin, u'', True))
                        entieres += 1
                else:
                    cadre[3].append(dans_logo)
                i = fin
                debut = i
                continue
        elif c == '}':
            prelude, deb, enfants, vivants = pile.pop()
            fin = i + 1
            tout_retire = enfants and all(e[3] for e in enfants) and not vivants
            if tout_retire and (prelude.startswith('@media') or prelude.startswith('@supports')):
                pile[-1][2].append((debut_de_ligne(css, deb), fin, u'', True))
                blocs += 1
            else:
                pile[-1][2].extend(e for e in enfants)
                if enfants and not tout_retire:
                    pile[-1][3].append(True)
                elif not enfants:
                    pile[-1][3].append(True)
            debut = i + 1
        elif c == ';' and len(pile) >= 1 and (len(pile) == 1 or pile[-1][0].startswith('@')):
            debut = i + 1
        i += 1
    edits += [(a, b, r) for a, b, r, _ in pile[0][2]]
    edits.sort(key=lambda e: e[0])
    for (a1, b1, _), (a2, b2, _) in zip(edits, edits[1:]):
        if a2 < b1:
            raise SystemExit(u"!! retraits qui se chevauchent : %d-%d et %d-%d" % (a1, b1, a2, b2))
    neuf = css
    for a, b, r in reversed(edits):
        neuf = neuf[:a] + r + neuf[b:]
    return neuf, entieres, allegees, blocs


def main():
    essai = '--essai' in sys.argv
    css = io.open(CSS, encoding='utf-8').read()
    neuf, entieres, allegees, blocs = plan(css)
    mn = masque(neuf)
    restes = sorted(set(m.group(0) for m in MORT.finditer(mn)))
    vides = (len(VIDE.findall(masque(css))), len(VIDE.findall(mn)))
    equilibre = mn.count('{') == mn.count('}')
    if restes or not equilibre or vides[1] != vides[0] or LOGO in neuf:
        raise SystemExit(u"!! contrôle avant écriture en échec : restes=%s, accolades=%s, "
                         u"@media vides %d -> %d" % (restes, equilibre, vides[0], vides[1]))
    if not essai:
        io.open(CSS, 'w', encoding='utf-8', newline='\n').write(neuf)
        relu = io.open(CSS, encoding='utf-8').read()
        if relu != neuf:
            raise SystemExit(u"!! style.css relu ne correspond pas à ce qui devait être écrit")
    lignes = (css.count('\n'), neuf.count('\n'))
    print(u"  purge des anciens styles d'en-tête et de pied de page%s" % (u" (ESSAI : rien écrit)" if essai else u""))
    print(u"  %3d règle(s) retirée(s) en entier" % entieres)
    print(u"  %3d règle(s) allégée(s) : seul le sélecteur mort part" % allegees)
    print(u"  %3d bloc(s) @media vidé(s) par cette purge, retiré(s)" % blocs)
    print(u"    1 bloc « petit logo MBC dans la barre basse », retiré en entier")
    print(u"  @media vides d'avant, laissés : %d ; lignes : %d -> %d (%+d)" % (vides[0], lignes[0], lignes[1], lignes[1] - lignes[0]))
    if not essai:
        print(u"\n  écrit et relu — lancer build-css.py puis bump-assets.py")
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
