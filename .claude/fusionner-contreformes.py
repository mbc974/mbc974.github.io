# -*- coding: utf-8 -*-
u"""Rend leurs trous aux lettres de la signature manuscrite du hero.

    python .claude/fusionner-contreformes.py --essai
    python .claude/fusionner-contreformes.py

LE DEFAUT
---------
« On a les espaces vides qui sont remplis » : l'interieur du a, du e, du o, du p
etait plein. Le president l'a signale deux fois.

Une premiere correction (couche V160) accusait le TRAIT de la plume de boucher
les contre-formes, et le faisait s'effacer apres l'encrage. Le diagnostic etait
faux : mesure dans le navigateur, ce trait fait 0,6 px a l'ecran — il ne peut
rien boucher. Et la verification l'etait aussi : l'outil de capture forcait
stroke-opacity:0, il ne pouvait donc montrer que ce qu'on attendait de lui.

LA VRAIE CAUSE
--------------
.claude/hw-signature.html decoupe chaque phrase en contours (« tout ce qui suit
un M jusqu'au M suivant ») et ecrit UN <path> PAR CONTOUR, pour que la plume
les trace un par un. Or l'interieur d'un « a » est un contour a part entiere.
Devenu un <path> autonome, il est rempli pour son propre compte : le trou
devient une pastille pleine posee sur la lettre, des que l'encre arrive.

Mesure au navigateur (getBBox) : 6 chemins entierement contenus dans un autre
dans la phrase 1, 7 dans la phrase 2, 4 dans la phrase 3. Ce sont exactement
les contre-formes.

CE QUE FAIT CE SCRIPT
---------------------
Pour chaque chemin a contour unique ENTIEREMENT CONTENU dans un autre, il le
rattache a son conteneur, dans le meme attribut d. La regle de remplissage par
defaut, nonzero, fait alors du contour interieur un TROU — a une condition :
qu'il tourne dans le sens inverse de son conteneur. C'est le cas de toute
contre-forme dans une police TrueType, et c'est verifie ici un par un par l'aire
signee. Un contour contenu qui tournerait dans le MEME sens serait un
recouvrement volontaire, a remplir : il est laisse tel quel.

Rien d'autre ne bouge : ni la geometrie (le contour est recopie a l'identique,
seul son « m » initial devient un « M » absolu — il l'etait deja de fait, le
generateur serialise chaque contour a partir de l'origine), ni les instants de
trace (--d, --t du conteneur conserves), ni le nombre de phrases.

Idempotent : relance sur un fichier deja traite, il ne trouve plus rien.
"""
import io
import re
import sys

CIBLE = 'index.html'
JETON = re.compile(r'[MmLlCcQqZzHhVvSsTt]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')
ARITE = {'m': 2, 'l': 2, 'c': 6, 'q': 4, 's': 4, 't': 2, 'h': 1, 'v': 1, 'z': 0}


def geometrie(d):
    """Sous-chemins -> liste de (points pour la boite, points d'ancrage pour l'aire)."""
    toks = JETON.findall(d)
    cx = cy = sx = sy = 0.0
    sous, boite, ancre = [], [], []
    cmd = None
    i = 0
    while i < len(toks):
        t = toks[i]
        if t[0].isalpha():
            cmd = t
            i += 1
            if cmd in 'Zz':
                cx, cy = sx, sy
            continue
        c = cmd.lower()
        n = ARITE[c]
        v = [float(x) for x in toks[i:i + n]]
        i += n
        rel = cmd.islower()
        if c == 'm':
            if boite:
                sous.append((boite, ancre))
            x, y = (cx + v[0], cy + v[1]) if rel else (v[0], v[1])
            cx, cy, sx, sy = x, y, x, y
            boite, ancre = [(x, y)], [(x, y)]
            cmd = 'l' if rel else 'L'          # paires implicites apres m = lineto
            continue
        if c == 'h':
            cx = cx + v[0] if rel else v[0]
        elif c == 'v':
            cy = cy + v[0] if rel else v[0]
        else:
            pts = [(v[k] + (cx if rel else 0), v[k + 1] + (cy if rel else 0))
                   for k in range(0, n, 2)]
            boite.extend(pts)
            cx, cy = pts[-1]
        boite.append((cx, cy))
        ancre.append((cx, cy))
    if boite:
        sous.append((boite, ancre))
    return sous


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def aire(pts):
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        s += x0 * y1 - x1 * y0
    return s / 2.0


def surface(b):
    return (b[2] - b[0]) * (b[3] - b[1])


def contient(a, b, tol=0.5):
    """La boite a contient-elle la boite b ?"""
    return (b[0] >= a[0] - tol and b[1] >= a[1] - tol and
            b[2] <= a[2] + tol and b[3] <= a[3] + tol and surface(b) < surface(a))


MOTIF = re.compile(r'<path class="(hw__p[^"]*)" pathLength="1" style="([^"]*)" d="([^"]+)"/>')


def traiter_svg(svg, rapport):
    chemins = MOTIF.findall(svg)
    infos = []
    for cls, st, d in chemins:
        g = geometrie(d)
        tout = [p for b, _ in g for p in b]
        infos.append({'cls': cls, 'st': st, 'd': d, 'n': len(g),
                      'bb': bbox(tout), 'aire': aire(g[0][1])})
    parent = {}
    for i, e in enumerate(infos):
        if e['n'] != 1 or 'hw__pt' in e['cls']:
            continue
        cands = [j for j, f in enumerate(infos) if j != i and contient(f['bb'], e['bb'])]
        if not cands:
            continue
        j = min(cands, key=lambda k: surface(infos[k]['bb']))
        if (e['aire'] > 0) == (infos[j]['aire'] > 0):
            rapport.append(u'  = chemin %d contenu dans %d mais tournant dans le MEME sens : '
                           u'recouvrement volontaire, garde plein' % (i + 1, j + 1))
            continue
        parent[i] = j
    if not parent:
        return svg, [], 0
    d_neuf = {j: infos[j]['d'] for j in set(parent.values())}
    for i, j in sorted(parent.items()):
        enfant = infos[i]['d']
        assert enfant[0] in 'mM', enfant[:12]
        # contour serialise depuis l'origine : son « m » initial est deja absolu
        d_neuf[j] += 'M' + enfant[1:]
    sortie = []
    for k, e in enumerate(infos):
        if k in parent:
            continue
        sortie.append(u'<path class="%s" pathLength="1" style="%s" d="%s"/>'
                      % (e['cls'], e['st'], d_neuf.get(k, e['d'])))
    debut = svg[:svg.index('<path')]
    fin = svg[svg.rindex('/>') + 2:]
    paires = [(i + 1, j + 1) for i, j in sorted(parent.items())]
    return debut + u''.join(sortie) + fin, paires, len(parent)


def main():
    essai = '--essai' in sys.argv
    h = io.open(CIBLE, encoding='utf-8').read()
    total = [0]
    rapport = []
    num = [0]

    def sur_svg(m):
        num[0] += 1
        neuf, paires, n = traiter_svg(m.group(0), rapport)
        total[0] += n
        rapport.append(u'  phrase %d : %s' % (
            num[0], (u', '.join(u'%d->%d' % p for p in paires)) if paires else u'rien a rattacher'))
        return neuf

    neuf = re.sub(r'<svg class="hw__f[^"]*"[^>]*>.*?</svg>', sur_svg, h, flags=re.S)
    print(u'\n'.join(rapport))
    print(u'  %d contre-forme(s) rattachee(s) a leur lettre' % total[0])
    if essai:
        print(u'  (essai : rien ecrit)')
        return 0
    if neuf == h:
        print(u'  (deja a jour)')
        return 0
    io.open(CIBLE, 'w', encoding='utf-8', newline='\n').write(neuf)
    print(u'  index.html reecrit — lancer bump-assets.py')
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
