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


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    essai = '--essai' in sys.argv
    if sys.argv[1] == 'round':
        return phase_round(essai)
    if sys.argv[1] == 'mortes':
        return phase_mortes(essai)
    raise SystemExit("!! phase inconnue : %s" % sys.argv[1])


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
