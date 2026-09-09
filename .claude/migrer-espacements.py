# -*- coding: utf-8 -*-
"""Structuration des espacements — SANS deplacer un seul pixel.

    python .claude/migrer-espacements.py unites --essai
    python .claude/migrer-espacements.py unites
    python .claude/migrer-espacements.py tokens --essai
    python .claude/migrer-espacements.py tokens

LA DIFFERENCE AVEC LES COULEURS ET LA TYPOGRAPHIE
-------------------------------------------------
Les deux chantiers precedents ont pu ABSORBER des valeurs : sept paliers de
texte couvrent 307 declarations pour 3,4 % d'ecart maximal, et l'oeil ne voit
pas 3 % sur une hauteur de ligne.

Les espacements ne se comportent pas ainsi. Mesure faite sur les declarations
a valeur fixe, aucune grille raisonnable ne depasse 66 % d'absorption sous
4 % d'ecart ; il faut tolerer 20 % pour en absorber 89 %. Or un gap ne se voit
pas isolement : il se REPETE entre N elements d'une grille, et 3 px d'ecart
repetes six fois deplacent une carte de 18 px.

D'ou la regle de ce module, qui n'a pas d'equivalent dans les deux autres :

    AUCUNE VALEUR N'EST DEPLACEE. NI DE 20 %, NI DE 4 %, NI DE 0,1 PX.

On ne fait que deux choses : uniformiser l'ECRITURE (phase « unites ») et
donner un NOM aux valeurs dominantes (phase « tokens »). Le navigateur doit
calculer exactement les memes espacements apres qu'avant.

PHASE « unites » — LA VARIANCE D'ECRITURE
------------------------------------------
Sept valeurs sont ecrites dans les deux unites : 8px ici, .5rem la. Meme
espacement, deux ecritures. On converge vers le rem, tres majoritaire.

Trois garde-fous, et ils reduisent beaucoup le perimetre :

  1. « scroll-padding-top » et « scroll-margin-top » ne sont PAS des
     espacements. Ce sont des decalages d'ancrage, cales sur la hauteur de
     l'en-tete colle. Les convertir lierait la position d'arrivee des ancres
     a la taille de police du visiteur. Douze declarations sortent ainsi du
     perimetre — elles n'auraient jamais du y entrer, et l'inventaire les
     comptait a tort : dans une regex, \\b trouve une frontiere de mot juste
     avant le « padding » de « scroll-padding-top ».

  2. On ne convertit un px que s'il a un JUMEAU rem dans la feuille. « 9px »
     n'est pas une variance d'ecriture : c'est une valeur unique, ecrite une
     fois, dans l'unite qui lui convient.

  3. On ne cree jamais une declaration MIXTE. « padding:14px 16px » ou seul
     le 16 a un jumeau deviendrait « padding:14px 1rem » — moins lisible
     qu'avant. Ces declarations restent entieres, en px.

UNE RESERVE HONNETE SUR CETTE PHASE
------------------------------------
La feuille ne fixe aucun html{font-size}. A la taille par defaut (16 px) la
conversion est identique au pixel pres, et c'est ce que verifie l'empreinte.
Chez un visiteur qui a AGRANDI la police par defaut de son navigateur, un
espacement en rem grandit alors qu'un espacement en px ne bougeait pas. C'est
le comportement souhaitable — la respiration suit le texte — mais c'est un
changement de comportement, pas une pure reecriture. Il porte ici sur quatre
declarations.

PHASE « tokens » — NOMMER, PAS NORMALISER
------------------------------------------
Un token ne remplace QUE sa valeur exacte. .9rem ne devient pas 1rem, 15px ne
devient pas 16px. C'est une centralisation, pas une normalisation : apres
migration, getComputedStyle doit rendre les memes chaines.

LE NOM DES TOKENS, ET POURQUOI PAS --sp-16
-------------------------------------------
La convention repandue nomme les espacements en pixels : --sp-4, --sp-8,
--sp-16. Elle suppose un vocabulaire cale sur des multiples de 4 px. Celui du
MBC ne l'est pas : sur les treize valeurs dominantes, quatre seulement tombent
sur un pixel rond.

    .7rem  = 11,2 px      .9rem  = 14,4 px
    .85rem = 13,6 px      1.1rem = 17,6 px

Nommer --sp-14 a la fois .85rem et .9rem serait une collision ; nommer .7rem
« --sp-11 » serait un nom faux de 0,2 px. On numerote donc en CENTIEMES DE
REM : --sp-70 vaut .7rem, --sp-100 vaut 1rem. Le nom reste numerique — pas de
--space-small dont la valeur depend du contexte — il trie correctement, et il
ne ment pas.

CE QUI RESTE HORS PERIMETRE
---------------------------
  - le hero (.hero, .hw) : sa respiration a ses propres regles ;
  - la galerie (.gzoom, .g-tile) : exclue depuis la phase couleurs ;
  - les valeurs calculees (clamp/calc/var) : c'est le rythme fluide voulu ;
  - --sp-sec / --sp-blk / --sp-gap : ces trois-la portent une intention de
    layout (le rythme des sections), pas une valeur. Ils sont conserves tels
    quels et ne sont pas renumerotes ;
  - toute valeur sans dominance reelle. On ne nomme pas ce qui sert une fois.
"""
import io
import os
import re
import sys
from collections import defaultdict

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(RACINE, 'style.css')

PROPS = ('margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
         'margin-inline', 'margin-block', 'margin-inline-start', 'margin-inline-end',
         'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
         'padding-inline', 'padding-block', 'gap', 'row-gap', 'column-gap')

# (?<![-\w]) : « scroll-padding-top » ne doit PAS etre lu comme « padding-top ».
RX_DECL = re.compile(r'(?<![-\w])(' + '|'.join(sorted(PROPS, key=len, reverse=True))
                     + r')\s*:\s*([^;}]+)')

EXCLUS = re.compile(r'\.hero|\.hw\b|\.gzoom|\.g-tile|\.gallery-mosaic|\.g-team|\.gz-')

# Les neuf valeurs dominantes : celles employees 24 fois ou plus, hors hero,
# hors galerie, hors calcul. Le seuil tombe sur une coupure nette — en dessous,
# trois valeurs se tiennent a 23 occurrences et les departager serait arbitraire.
TOKENS = [('sp-50', '.5rem'), ('sp-60', '.6rem'), ('sp-70', '.7rem'),
          ('sp-80', '.8rem'), ('sp-85', '.85rem'), ('sp-90', '.9rem'),
          ('sp-100', '1rem'), ('sp-110', '1.1rem'), ('sp-140', '1.4rem')]
PAR_VAL = {v: n for n, v in TOKENS}


def masque(css):
    """Chaque commentaire devient des espaces de MEME longueur : on cherche
    dans le texte masque et on ecrit dans le texte reel, aux memes positions."""
    out = list(css)
    for m in re.finditer(r'/\*.*?\*/', css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def selecteur_de(mc, pos):
    ouv = mc.rfind('{', 0, pos)
    if ouv < 0:
        return ''
    prec = max(mc.rfind('}', 0, ouv), mc.rfind('{', 0, ouv))
    return re.sub(r'\s+', ' ', mc[prec + 1:ouv]).strip()


def atomes(val):
    """Decoupe une valeur en atomes, en detachant un eventuel !important."""
    imp = ''
    m = re.search(r'\s*!\s*important\s*$', val)
    if m:
        imp = val[m.start():]
        val = val[:m.start()]
    return val.split(), imp


def norm(a):
    """« 0.5rem » -> « .5rem ». Les deux ecritures designent la meme valeur."""
    a = a.strip().lower()
    return a[1:] if a.startswith('0.') else a


def ecrire(css, essai):
    if essai:
        print(u"\n  (essai : rien n'a ete ecrit)")
        return 0
    io.open(CSS, 'w', encoding='utf-8', newline='\n').write(css)
    print(u"\n  style.css reecrit — lancer build-css.py puis bump-assets.py")
    return 0


# --------------------------------------------------------------------------
def phase_unites(essai):
    css = io.open(CSS, encoding='utf-8').read()
    mc = masque(css)

    # 1. le vocabulaire rem deja employe, exprime en pixels
    voc = set()
    for m in RX_DECL.finditer(mc):
        val = m.group(2).strip()
        if re.search(r'var\(|calc\(|clamp\(', val):
            continue
        parts, _ = atomes(val)
        for p in parts:
            mm = re.fullmatch(r'(\d*\.?\d+)rem', norm(p))
            if mm:
                voc.add(round(float(mm.group(1)) * 16, 4))

    def en_rem(px):
        s = '%g' % (px / 16.0)
        return (s[1:] if s.startswith('0.') else s) + 'rem'

    faits, mixtes, orphelins, hors = [], [], [], []
    for m in reversed(list(RX_DECL.finditer(mc))):
        prop, val = m.group(1), m.group(2).strip()
        if re.search(r'var\(|calc\(|clamp\(', val):
            continue
        parts, imp = atomes(val)
        pxs = [p for p in parts if re.fullmatch(r'\d*\.?\d+px', norm(p))]
        if not pxs:
            continue
        sel = selecteur_de(mc, m.start())
        vals = [float(norm(p)[:-2]) for p in pxs]
        connus = [v for v in vals if round(v, 4) in voc]
        if not connus:
            orphelins.append((sel, prop, val))
            continue
        if len(connus) < len(vals):
            manque = [v for v in vals if round(v, 4) not in voc]
            mixtes.append((sel, prop, val, manque))
            continue
        if EXCLUS.search(sel):
            hors.append((sel, prop, val))
            continue
        neuf = ' '.join(en_rem(float(norm(p)[:-2])) if p in pxs else p for p in parts) + imp
        css = css[:m.start()] + prop + ':' + neuf + css[m.end():]
        faits.append((sel, prop, val, neuf))

    print(u"  PHASE A — variance d'ecriture (px -> rem, valeur calculee identique)")
    print(u"  %d conversion(s)" % len(faits))
    for sel, prop, val, neuf in reversed(faits):
        print(u"    %-32s %s:%-22s -> %s" % (sel[:32], prop, val, neuf))
    print(u"\n  laisses en place, et pourquoi :")
    print(u"    %2d mixte(s) : un seul des px a un jumeau rem — convertir rendrait"
          u" la declaration moins lisible" % len(mixtes))
    for sel, prop, val, manque in mixtes:
        print(u"       %-28s %s:%-20s (%s sans jumeau)"
              % (sel[:28], prop, val, "/".join('%gpx' % x for x in manque)))
    print(u"    %2d sans aucun jumeau rem : valeur unique, pas une variance" % len(orphelins))
    print(u"    %2d hors perimetre (hero / galerie)" % len(hors))
    for sel, prop, val in hors:
        print(u"       %-28s %s:%s" % (sel[:28], prop, val))
    return ecrire(css, essai)


# --------------------------------------------------------------------------
def poser_tokens(css):
    if '--sp-100' in css:
        return css
    ancre = '  --sp-gap:clamp(1rem,2.4vw,1.75rem);'
    if css.count(ancre) != 1:
        raise SystemExit("!! ancre :root introuvable (--sp-gap)")
    bloc = [ancre, '',
            '  /* --- Les espacements dominants ------------------------------------------',
            '     Neuf valeurs portent pres de la moitie des atomes d\'espacement litteraux',
            '     de la feuille. Elles n\'avaient aucun nom : changer la respiration des',
            '     cartes demandait de retrouver .85rem parmi 75 valeurs voisines.',
            '',
            '     CES TOKENS NE DEPLACENT RIEN. Chacun ne remplace que sa valeur exacte.',
            '     .9rem ne devient pas 1rem, .85rem ne devient pas .9rem. Le navigateur',
            '     calcule apres exactement ce qu\'il calculait avant — verifie par empreinte',
            '     des styles calcules, pas par relecture.',
            '',
            '     La numerotation est en CENTIEMES DE REM, pas en pixels : le vocabulaire',
            '     du site ne tombe pas sur des multiples de 4 px (.7rem = 11,2 px), et',
            '     --sp-14 designerait a la fois .85rem et .9rem.',
            '',
            '     Au-dessus, --sp-sec / --sp-blk / --sp-gap restent des tokens d\'INTENTION',
            '     (le rythme des sections). Ils ne sont pas renumerotes : ils ne portent',
            '     pas une valeur, ils portent une decision de layout.',
            '     --------------------------------------------------------------------- */']
    for nom, v in TOKENS:
        bloc.append('  --%s:%s;' % (nom, v))
    return css.replace(ancre, '\n'.join(bloc), 1)


def phase_tokens(essai):
    css = poser_tokens(io.open(CSS, encoding='utf-8').read())
    mc = masque(css)

    faits, exclus = defaultdict(int), defaultdict(int)
    for m in reversed(list(RX_DECL.finditer(mc))):
        prop, val = m.group(1), m.group(2).strip()
        if re.search(r'var\(|calc\(|clamp\(', val):
            continue
        parts, imp = atomes(val)
        cibles = [p for p in parts if norm(p) in PAR_VAL]
        if not cibles:
            continue
        sel = selecteur_de(mc, m.start())
        if EXCLUS.search(sel):
            for p in cibles:
                exclus[norm(p)] += 1
            continue
        neuf = ' '.join('var(--%s)' % PAR_VAL[norm(p)] if norm(p) in PAR_VAL else p
                        for p in parts) + imp
        css = css[:m.start()] + prop + ':' + neuf + css[m.end():]
        for p in cibles:
            faits[norm(p)] += 1

    print(u"  PHASE B — tokens des valeurs dominantes (aucun deplacement)")
    print(u"  %-11s %-9s %6s  %s" % (u"token", u"valeur", u"occ.", u"hors perimetre"))
    tot = 0
    for nom, v in TOKENS:
        tot += faits.get(v, 0)
        print(u"  --%-9s %-9s %6d  %s"
              % (nom, v, faits.get(v, 0),
                 (u"%d (hero/galerie)" % exclus[v]) if exclus.get(v) else u""))
    print(u"  %d atome(s) tokenise(s)" % tot)
    return ecrire(css, essai)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    essai = '--essai' in sys.argv
    if sys.argv[1] == 'unites':
        return phase_unites(essai)
    if sys.argv[1] == 'tokens':
        return phase_tokens(essai)
    raise SystemExit("!! phase inconnue : %s" % sys.argv[1])


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
