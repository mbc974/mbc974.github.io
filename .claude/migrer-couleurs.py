# -*- coding: utf-8 -*-
"""Migration progressive du systeme de couleurs — phase par phase.

    python .claude/migrer-couleurs.py canaux --essai
    python .claude/migrer-couleurs.py canaux

PHASE « canaux » (2A) — STRICTEMENT ISO-VISUELLE
------------------------------------------------
Les teintes de marque sont declinees en dizaines d'opacites ecrites en dur :
144 occurrences de l'orange sur 36 alphas, 112 de la nuit sur 48. Changer la
teinte du club demanderait aujourd'hui 144 modifications coherentes.

On pose donc les CANAUX dans :root

    --orange-vif-rgb: 232 130 42;

et on remplace

    rgba(232,130,42,.42)   ->   rgb(var(--orange-vif-rgb) / .42)

La couleur calculee est identique au bit pres : getComputedStyle rend
« rgba(232, 130, 42, 0.42) » dans les deux cas. Aucune opacite n'est touchee
ici — la rationalisation des alphas est une phase separee, et melanger les
deux rendrait toute regression impossible a attribuer.

CE QUI EST EXCLU
----------------
La galerie en zoom parallaxe (.gzoom, .g-tile, .gallery-mosaic). Sa mecanique
depend de sa geometrie et de ses alphas propres ; elle sera normalisee en
dernier, separement. Meme un remplacement iso-visuel s'en tient a l'ecart tant
que le reste n'est pas stabilise.
"""
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(RACINE, 'style.css')

# Les teintes reellement declinees en opacites variables, avec le nom du token
# existant : on garde la nomenclature francaise du depot plutot que d'en
# introduire une seconde.
CANAUX = [
    ((232, 130, 42), 'orange-vif'),
    ((217, 106, 27), 'orange-ballon'),
    ((27, 81, 158), 'bleu-roi'),
    ((191, 210, 228), 'bleu-glacier'),
    ((255, 255, 255), 'blanc'),
    ((7, 13, 24), 'nuit-0'),
]

# Les selecteurs tenus a l'ecart de cette phase.
EXCLUS = re.compile(r'\.gzoom|\.g-tile|\.gallery-mosaic|\.g-team|\.gzoom__')


def sans_commentaires_masque(css):
    """Remplace chaque commentaire par des espaces de MEME longueur.

    On garde ainsi les positions du fichier d'origine : on peut chercher dans
    le texte masque et ecrire dans le texte reel."""
    out = list(css)
    for m in re.finditer(r'/\*.*?\*/', css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def selecteur_de(masque, pos):
    """Le selecteur de la regle qui contient la position donnee."""
    ouv = masque.rfind('{', 0, pos)
    if ouv < 0:
        return ''
    prec = max(masque.rfind('}', 0, ouv), masque.rfind('{', 0, ouv))
    return re.sub(r'\s+', ' ', masque[prec + 1:ouv]).strip()


def canaux(essai):
    css = io.open(CSS, encoding='utf-8').read()
    masque = sans_commentaires_masque(css)
    par_token = {rgb: nom for rgb, nom in CANAUX}

    # 1. les declarations de canaux, posees juste apres la derniere couleur
    #    de :root pour rester lisibles a cote de leurs teintes d'origine.
    if '--orange-vif-rgb' not in css:
        ancre = '  --blanc:#FFFFFF;'
        if css.count(ancre) != 1:
            raise SystemExit("!! ancre :root introuvable (--blanc)")
        bloc = [ancre, '',
                '  /* --- Les canaux des teintes de marque ---------------------------------',
                '     Ces six teintes sont declinees en dizaines d\'opacites a travers la',
                '     feuille : 144 occurrences pour l\'orange sur 36 alphas, 112 pour la',
                '     nuit sur 48. Ecrites en dur, changer la couleur du club demanderait',
                '     autant de modifications coherentes — et rien ne les verifierait.',
                '',
                '     En publiant les CANAUX, une regle s\'ecrit',
                '         rgb(var(--orange-vif-rgb) / .42)',
                '     au lieu de rgba(232,130,42,.42). La couleur calculee est identique',
                '     au bit pres ; la teinte, elle, n\'a plus qu\'un seul point de verite.',
                '     ------------------------------------------------------------------- */']
        for rgb, nom in CANAUX:
            bloc.append('  --%s-rgb:%d %d %d;' % (nom, rgb[0], rgb[1], rgb[2]))
        css = css.replace(ancre, '\n'.join(bloc), 1)
        masque = sans_commentaires_masque(css)

    # 2. les remplacements
    motif = re.compile(r'rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([\d.]+)\s*\)')
    faits, ignores_galerie, hors_charte = [], 0, 0
    # on travaille a l'envers pour que les positions restent valides
    for m in reversed(list(motif.finditer(masque))):
        rgb = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if rgb not in par_token:
            hors_charte += 1
            continue
        sel = selecteur_de(masque, m.start())
        if EXCLUS.search(sel):
            ignores_galerie += 1
            continue
        alpha = m.group(4)
        neuf = 'rgb(var(--%s-rgb) / %s)' % (par_token[rgb], alpha)
        css = css[:m.start()] + neuf + css[m.end():]
        faits.append((m.group(0), neuf, sel[:40]))

    print(u"  PHASE 2A — canaux de marque")
    print(u"  %d remplacement(s)" % len(faits))
    print(u"  %d laisse(s) a la galerie (hors perimetre de cette phase)" % ignores_galerie)
    print(u"  %d rgba() hors des six teintes de marque, non touche(s)" % hors_charte)
    par_teinte = {}
    for a, b, s in faits:
        t = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+)', a).groups()
        par_teinte[t] = par_teinte.get(t, 0) + 1
    for t, n in sorted(par_teinte.items(), key=lambda x: -x[1]):
        rgb = tuple(int(x) for x in t)
        print(u"    %-16s %3d" % (par_token.get(rgb, '?'), n))
    if faits[:3]:
        print(u"  exemples :")
        for a, b, s in faits[:3]:
            print(u"    %-28s -> %-38s  (%s)" % (a, b, s))
    if essai:
        print(u"\n  (essai : rien n'a ete ecrit)")
        return 0
    io.open(CSS, 'w', encoding='utf-8', newline='\n').write(css)
    print(u"\n  style.css reecrit — lancer build-css.py puis bump-assets.py")
    return 0


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    essai = '--essai' in sys.argv
    if sys.argv[1] == 'canaux':
        return canaux(essai)
    raise SystemExit("!! phase inconnue : %s" % sys.argv[1])


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
