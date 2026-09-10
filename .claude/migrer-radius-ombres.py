# -*- coding: utf-8 -*-
"""Rayons et ombres : le token du cercle, et le retrait du reellement mort.

    python .claude/migrer-radius-ombres.py round --essai
    python .claude/migrer-radius-ombres.py round
    python .claude/migrer-radius-ombres.py mortes --essai
    python .claude/migrer-radius-ombres.py mortes

CE QUI EST FAIT, ET CE QUI NE L'EST PAS
----------------------------------------
Arbitrage du 09/09/2026 : oui a --r-round, on garde le mecanisme V79 a deux
portees, on retire les regles mortes. Les deux quasi-doublons d'ombre
(.nx__second contre .hero__second, .lightbox__viewport contre .lightbox img)
ne sont PAS touches : ce sont de vrais deplacements d'alpha, ils attendent une
decision.

PHASE « round » — LE CERCLE N'EST PAS LA PILULE
------------------------------------------------
22 declarations ecrivent border-radius:50%. Elles ne disent pas la meme chose
que les 22 autres en 99px/999px :

    999px sur un rectangle -> un stade (pilule)
    50%   sur un carre     -> un cercle
    50%   sur un rectangle -> une ELLIPSE

Mesure faite dans le navigateur sur 4 pages et 2 largeurs : les 11 elements
concernes sont tous carres aujourd'hui, donc 50% y donne bien un cercle. Mais
la valeur reste conditionnelle a la geometrie de l'element — c'est exactement
pour cela qu'on lui donne son propre nom au lieu de la fondre dans --r-pill.
Le jour ou un de ces elements cesse d'etre carre, --r-round dira encore la
verite ; --r-pill aurait menti.

--r-round n'est PAS redefini par V79 : il vaut 50 % partout, dans le hero
comme dans les sections. La substitution est donc un alias strict, sans
deplacement possible — c'est pourquoi elle s'applique aussi au hero et au
Match Center, que les phases precedentes tenaient a l'ecart.

PHASE « mortes » — ET POURQUOI SEULEMENT DEUX
----------------------------------------------
L'inventaire annoncait 10 declarations d'ombre mortes. En les verifiant une
par une contre script.js et consent.js — ce que le detecteur de classes ne
fait pas — il n'en reste que deux.

  VIVANTES, a ne surtout pas retirer :
    .lightbox__toolbar   creee par script.js:178 (toolbar.className = ...)
    .ccb                 creee par consent.js:51 (b.className = 'ccb')
  Aucune n'apparait dans un attribut class= du markup : elles naissent a
  l'execution. Les retirer aurait casse la visionneuse et le bandeau RGPD.

  DORMANTES, laissees en place :
    .btn--roi (4 declarations)  variante bleue encore ciblee par
                                script.js:393. Lui retirer ses ombres la
                                degraderait sans la nettoyer : la bonne unite
                                de decision est le bloc entier, pas une
                                propriete.
    .sb, .sb__crest img         le bloc « SCOREBOARD » complet, jamais employe.
                                Meme raisonnement.

  REELLEMENT ORPHELINES, retirees ici :
    .hero__lead     n'existe dans aucun markup, aucun script, aucun
                    generateur. Reliquat d'un element renomme.
    .lp-aside picture   la famille .lp-aside est absente partout, alors que
                    .licence-path et .lp-who, eux, sont bien vivants.
"""
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(RACINE, 'style.css')


def masque(css):
    out = list(css)
    for m in re.finditer(r'/\*.*?\*/', css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def ecrire(css, essai):
    if essai:
        print(u"\n  (essai : rien n'a ete ecrit)")
        return 0
    io.open(CSS, 'w', encoding='utf-8', newline='\n').write(css)
    print(u"\n  style.css reecrit — lancer build-css.py puis bump-assets.py")
    return 0


RADIUS_PROPS = ('border-radius',
                'border-top-left-radius', 'border-top-right-radius',
                'border-bottom-left-radius', 'border-bottom-right-radius',
                'border-start-start-radius', 'border-start-end-radius',
                'border-end-start-radius', 'border-end-end-radius')


def phase_round(essai):
    css = io.open(CSS, encoding='utf-8').read()

    if '--r-round' not in css:
        ancre = '  --r-pill:999px;'
        if css.count(ancre) != 1:
            raise SystemExit("!! ancre :root introuvable (--r-pill)")
        bloc = [ancre,
                '  /* Le cercle a son propre nom, et ce n\'est pas un detail : --r-pill',
                '     (999px) fait un STADE sur un rectangle, --r-round (50 %) fait un',
                '     CERCLE sur un carre — et une ellipse sur tout le reste. Les onze',
                '     elements concernes sont carres aujourd\'hui, mesure a l\'appui ; le',
                '     jour ou l\'un cesse de l\'etre, ce nom-la dira encore la verite.',
                '     Contrairement a --r-sm/md/lg, il n\'est pas redefini par V79 :',
                '     50 % vaut 50 % partout. */',
                '  --r-round:50%;']
        css = css.replace(ancre, '\n'.join(bloc), 1)

    mc = masque(css)
    rx = re.compile(r'(?<![-\w])(' + '|'.join(sorted(RADIUS_PROPS, key=len, reverse=True))
                    + r')\s*:\s*50%\s*(?=[;}])')
    faits = []
    for m in reversed(list(rx.finditer(mc))):
        ouv = mc.rfind('{', 0, m.start())
        prec = max(mc.rfind('}', 0, ouv), mc.rfind('{', 0, ouv))
        sel = re.sub(r'\s+', ' ', mc[prec + 1:ouv]).strip()
        css = css[:m.start()] + m.group(1) + ':var(--r-round)' + css[m.end():]
        faits.append((mc[:m.start()].count('\n') + 1, sel))

    print(u"  PHASE round — le cercle prend son nom (alias strict, 50%% -> 50%%)")
    print(u"  %d substitution(s)" % len(faits))
    for ligne, sel in reversed(faits):
        print(u"     L%-5d %s" % (ligne, sel[:64]))
    return ecrire(css, essai)


# Les deux SEULES declarations d'ombre dont le selecteur n'existe nulle part :
# ni markup, ni script.js, ni consent.js, ni generateur.
MORTES = [
    (u".hero__lead (regle entiere : text-shadow seul)",
     re.compile(r'\n?[ \t]*\.hero__lead\{text-shadow:0 1px 3px rgba\(4,9,18,\.72\),'
                r'0 2px 16px rgba\(4,9,18,\.80\)\}')),
    (u".lp-aside picture (la declaration box-shadow)",
     re.compile(r'(\.lp-aside picture\{[^}]*?);box-shadow:var\(--e2\)(\})', re.S)),
]


def phase_mortes(essai):
    css = io.open(CSS, encoding='utf-8').read()
    print(u"  PHASE mortes — seulement ce qui n'existe vraiment nulle part")
    n = 0
    for nom, rx in MORTES:
        m = rx.search(css)
        if not m:
            print(u"     %-52s INTROUVABLE (deja retiree ?)" % nom)
            continue
        css = css[:m.start()] + (m.expand(r'\1\2') if m.groups() else '') + css[m.end():]
        print(u"     %-52s retiree" % nom)
        n += 1
    print(u"  %d declaration(s) retiree(s)" % n)
    print(u"\n  NON retirees, et c'est deliberé :")
    print(u"     .lightbox__toolbar   VIVANTE — creee par script.js:178")
    print(u"     .ccb                 VIVANTE — creee par consent.js:51")
    print(u"     .btn--roi (×4)       dormante, encore ciblee par script.js:393")
    print(u"     .sb / .sb__crest img dormante, bloc SCOREBOARD entier")
    return ecrire(css, essai)


def phase_pill(essai):
    """99px et 999px disent tous deux « arrondi complet ». Ils passent sous
    --r-pill.

    999px -> var(--r-pill) est un alias strict : le token vaut exactement 999px
    et n'est pas redefini par V79.

    99px -> var(--r-pill) est un vrai changement de valeur, mais pas un
    changement de RENDU : un rayon est plafonne a la moitie du plus petit cote
    de l'element. Les deux valeurs se comportent donc identiquement tant que ce
    cote reste sous 198 px. Mesure faite sur 4 pages et 2 largeurs : le cote
    court maximal des elements concernes est de 54 px. La marge est de 3,6x."""
    css = io.open(CSS, encoding='utf-8').read()
    mc = masque(css)
    rx = re.compile(r'(?<![-\w])(' + '|'.join(sorted(RADIUS_PROPS, key=len, reverse=True))
                    + r')\s*:\s*(9{2,4}px)\s*(?=[;}])')
    faits = []
    for m in reversed(list(rx.finditer(mc))):
        ouv = mc.rfind('{', 0, m.start())
        prec = max(mc.rfind('}', 0, ouv), mc.rfind('{', 0, ouv))
        sel = re.sub(r'\s+', ' ', mc[prec + 1:ouv]).strip()
        css = css[:m.start()] + m.group(1) + ':var(--r-pill)' + css[m.end():]
        faits.append((mc[:m.start()].count('\n') + 1, sel, m.group(2)))

    print(u"  PHASE pill — 99px et 999px rejoignent --r-pill")
    print(u"  %d substitution(s)" % len(faits))
    for ligne, sel, v in reversed(faits):
        print(u"     L%-5d %-8s %s" % (ligne, v, sel[:56]))

    # NOTE — « .licence-path .lp-who » ecrivait 99px (L2751) puis 999px (L4875).
    # L'inventaire l'avait signale comme un doublon ; verification faite, c'en
    # est un a moitie seulement. Ce ne sont pas deux regles redondantes : la
    # seconde RESTYLE le badge (padding, graisse, interlettrage) et redeclare
    # son rayon au passage. Seule la declaration border-radius de la premiere
    # etait ecrasee. Les deux disant desormais var(--r-pill), la surcharge est
    # devenue sans effet — rien a retirer ici, et surtout pas la regle.
    return ecrire(css, essai)


# Les SEULES regles dont le litteral vaut exactement ce que le token vaut LA OU
# ELLES S'APPLIQUENT. Cette liste n'est pas deduite du texte de la feuille : elle
# a ete etablie dans le navigateur, sur 12 pages, en lisant --r-sm/md/lg sur
# chaque element reellement touche par la regle (getPropertyValue rend la valeur
# heritee au point d'application, donc la bonne des deux portees V79).
#
# 80 regles portent un rayon litteral en px. 47 ne correspondent a aucun token
# la ou elles s'appliquent — les tokeniser les DEPLACERAIT. 20 ne touchent
# aucun element sur les pages testees : invérifiables, donc laissees. Restent
# ces 13, unanimes, zero mixte.
#
# Deux selecteurs y figurent deux fois avec des valeurs differentes : dans le
# pied de page, --r-sm vaut 10px et --r-md 12px. Les deux substitutions sont
# justes ; c'est le mecanisme V79 qui veut ca.
TOKENISABLES = [
    ('.footer__social a', '12px', 'r-md'),
    ('.footer__social a', '10px', 'r-sm'),
    ('.hero__scroll span', '14px', 'r-sm'),
    ('.essentiel-card__ico', '16px', 'r-lg'),
    ('.roster__btn', '12px', 'r-md'),
    ('.team__photo', '16px', 'r-lg'),
    ('main > .section .essentiel-card', '12px', 'r-md'),
    ('.lp-stage', '12px', 'r-md'),
    ('.mx-date', '10px', 'r-sm'),
    ('.mx-crest', '16px', 'r-lg'),
    ('.p-pillar__ico', '10px', 'r-sm'),
    ('.p-pillar__ico', '12px', 'r-md'),
    ('.pl-slot', '10px', 'r-sm'),
]


def phase_tokens(essai):
    css = io.open(CSS, encoding='utf-8').read()
    mc = masque(css)

    # (selecteur normalise, valeur) -> token
    cible = {}
    for sel, val, tok in TOKENISABLES:
        cible[(re.sub(r'\s+', ' ', sel).strip(), val)] = tok

    rx = re.compile(r'(?<![-\w])border-radius\s*:\s*(\d+(?:\.\d+)?px)\s*(?=[;}])')
    faits, vus = [], set()
    for m in reversed(list(rx.finditer(mc))):
        ouv = mc.rfind('{', 0, m.start())
        prec = max(mc.rfind('}', 0, ouv), mc.rfind('{', 0, ouv))
        sel = re.sub(r'\s+', ' ', mc[prec + 1:ouv]).strip()
        tok = cible.get((sel, m.group(1)))
        if not tok:
            continue
        css = css[:m.start()] + 'border-radius:var(--%s)' % tok + css[m.end():]
        faits.append((mc[:m.start()].count('\n') + 1, sel, m.group(1), tok))
        vus.add((sel, m.group(1)))

    print(u"  PHASE tokens — les 13 regles dont le litteral EGALE le token sur place")
    print(u"  %d substitution(s)" % len(faits))
    for ligne, sel, val, tok in reversed(faits):
        print(u"     L%-5d %-6s -> --%-5s %s" % (ligne, val, tok, sel[:48]))
    manquants = set(cible) - vus
    if manquants:
        print(u"  !! %d regle(s) attendue(s) INTROUVABLE(s) : %s"
              % (len(manquants), sorted(manquants)[:4]))
    return ecrire(css, essai)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    essai = '--essai' in sys.argv
    if sys.argv[1] == 'round':
        return phase_round(essai)
    if sys.argv[1] == 'pill':
        return phase_pill(essai)
    if sys.argv[1] == 'tokens':
        return phase_tokens(essai)
    if sys.argv[1] == 'mortes':
        return phase_mortes(essai)
    raise SystemExit("!! phase inconnue : %s" % sys.argv[1])


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
