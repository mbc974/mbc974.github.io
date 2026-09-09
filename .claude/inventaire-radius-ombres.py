# -*- coding: utf-8 -*-
"""Inventaire des rayons et des ombres.

    python .claude/inventaire-radius-ombres.py            les deux rapports
    python .claude/inventaire-radius-ombres.py radius
    python .claude/inventaire-radius-ombres.py ombres
    python .claude/inventaire-radius-ombres.py selecteurs  la liste brute, pour
                                                          verifier le classement

N'ECRIT RIEN. Quatrieme instrument de la serie, apres les couleurs, la
typographie et les espacements.

CE QUI CHANGE PAR RAPPORT AUX TROIS PRECEDENTS
-----------------------------------------------
Les trois premiers chantiers partaient de zero : aucune echelle n'existait.
Ici, un systeme EXISTE deja — --r-sm/md/lg/pill pour les rayons, --e1/e2/e3
pour l'elevation, --glow-o/--glow-b pour les lueurs de marque, --bevel pour le
lisere interieur. La question n'est donc pas « quel systeme creer » mais
« combien de declarations passent a cote de celui qui existe ».

ET UNE QUESTION DE CASCADE
--------------------------
Ces tokens sont redefinis a plusieurs endroits. Un token redefini n'est pas un
doublon : c'est peut-etre une adaptation volontaire (mobile, mouvement reduit).
Mais si les deux definitions ont la meme portee, la premiere ne sert a rien et
personne ne le sait. Le script resout donc la cascade pour de vrai, avec un
parseur a profondeur d'accolades — pas avec une recherche en arriere, qui
confond une @media fermee avec une @media englobante.

POURQUOI ON NE DECOMPOSE PAS LES OMBRES MULTIPLES
--------------------------------------------------
    box-shadow: 0 4px 20px rgba(...), 0 0 40px rgba(...);

est UNE composition, pas deux ombres. La premiere pose l'objet, la seconde le
fait rayonner ; separees, elles ne veulent rien dire. On les compte donc comme
une seule entree, tout en decomposant chaque couche (offset-x, offset-y, blur,
spread, couleur, alpha, inset) pour reconnaitre deux ecritures differentes d'un
meme effet.

CE QU'IL NE FAIT PAS
--------------------
Aucune fusion, aucune proposition automatique. Une ombre d'elevation et une
lueur de marque peuvent avoir des valeurs voisines et des roles opposes : les
rapprocher sur la seule distance numerique serait refaire l'erreur des navies
de la phase couleurs.
"""
import io
import glob
import os
import re
import sys
from collections import defaultdict

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(RACINE, 'style.css')

RADIUS_PROPS = ('border-radius',
                'border-top-left-radius', 'border-top-right-radius',
                'border-bottom-left-radius', 'border-bottom-right-radius',
                'border-start-start-radius', 'border-start-end-radius',
                'border-end-start-radius', 'border-end-end-radius')

# Les roles, dans l'ordre de priorite : le premier motif qui repond gagne.
# Ils sont tires des selecteurs REELS de la feuille, pas d'une nomenclature
# theorique — la liste brute est consultable avec « selecteurs ».
ROLES = [
    ('hero',        r'\.hero|\.hw\b'),
    ('galerie',     r'\.gzoom|\.g-tile|\.gallery-mosaic|\.g-team|\.gz-'),
    ('match center', r'\.mx-|\.mx\b|\.nx\b|\.nx__|\.cal-|\.lp-|\.ml-|\.ml__'),
    ('navigation',  r'\.nav\b|\.nav__|\.burger|\.site-header|\.seo-top|'
                    r'\.skip-link|\.float-cta|\.breadcrumb|\.fil\b'),
    ('formulaire',  r'\binput\b|\btextarea\b|\bselect\b|\.field|\.contact-form|'
                    r'\blabel\b|\[type|\.form-'),
    ('bouton',      r'\.btn|\bbutton\b|\.cta|__cta|\.ccb__b|\.pk-contact a'),
    ('badge/pill',  r'\.chip|\.badge|\.kicker|\.pill|\.tag\b|\.pl-f\b|'
                    r'\.cat__num|\.sq-rail__c|__label'),
    ('image',       r'\bimg\b|\bpicture\b|\.photo|__photo|__ph\b|__i\b|'
                    r'\.covers|\.affiche|\.poster|__poster|\.crest|__crest'),
    ('carte',       r'\.cat\b|\.cat__|\.pack|\.sq-card|\.ac\b|\.ac__|\.cw\b|'
                    r'\.cw__|\.cx-|\.pk-|\.keyfig|\.essentiel|\.staff|\.team|'
                    r'\.support-card|\.sponsor|\.pl-slot|\.pl-jour|\.p-pillar|'
                    r'\.parents|\.vis-|\.visi|\.card|__card'),
    ('grande surface', r'\.section|\.wrap\b|\.site-footer|\.seo-foot|main\s*>|'
                       r'\.squad-sec|\.local-proof|\.ccb\b|\.roster'),
    ('editorial',   r'\.pquote|\.lead|\.sec-head|\.prose|blockquote|\.note|'
                    r'\.engage|\.marquee|figure|figcaption'),
]
ROLES = [(n, re.compile(r)) for n, r in ROLES]


# --------------------------------------------------------------------------
# Le parseur : on masque les commentaires, puis on suit la profondeur reelle
# des accolades. C'est la seule facon de savoir si une @media est englobante
# ou deja refermee.
# --------------------------------------------------------------------------
def masque(css):
    out = list(css)
    for m in re.finditer(r'/\*.*?\*/', css, re.S):
        for i in range(m.start(), m.end()):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def declarations(css):
    """Rend (ligne, at_rules, selecteur, propriete, valeur) pour tout le CSS.

    Deux points ou un parseur naif se trompe, et les deux mordent ici :

      - le POINT-VIRGULE FINAL EST FACULTATIF. « .cat{color:red;z-index:1} »
        contient deux declarations, pas une. Cette feuille est ecrite de facon
        compacte : ne pas vider le tampon sur « } » perdait une declaration par
        bloc, soit des centaines ;
      - les VIRGULES ET DEUX-POINTS DANS LES PARENTHESES. On ne coupe qu'a
        profondeur zero, sinon « rgb(var(--x) / .3) » part en morceaux."""
    mc = masque(css)
    out, pile, tampon, prof = [], [], '', 0

    def flush(pos):
        bloc = re.sub(r'\s+', ' ', tampon).strip()
        if bloc and ':' in bloc and pile and not pile[-1].startswith('@'):
            p, _, v = bloc.partition(':')
            if re.fullmatch(r'[-a-zA-Z][-a-zA-Z0-9]*', p.strip()):
                ats = [x for x in pile[:-1] if x.startswith('@')]
                out.append((mc[:pos].count('\n') + 1, ats, pile[-1], p.strip(), v.strip()))

    for i, c in enumerate(mc):
        if c == '(':
            prof += 1
        elif c == ')':
            prof = max(0, prof - 1)
        if prof == 0 and c == '{':
            pile.append(re.sub(r'\s+', ' ', tampon).strip())
            tampon = ''
        elif prof == 0 and c == '}':
            flush(i)                 # le « ; » final est facultatif
            if pile:
                pile.pop()
            tampon = ''
        elif prof == 0 and c == ';':
            flush(i)
            tampon = ''
        else:
            tampon += c
    return out


def classes_du_site():
    vus = set()
    for f in (glob.glob(os.path.join(RACINE, '*.html'))
              + glob.glob(os.path.join(RACINE, '*/index.html'))
              + glob.glob(os.path.join(RACINE, '*/*/index.html'))
              + glob.glob(os.path.join(RACINE, '.claude/*.py'))):
        if 'worktrees' in f:
            continue
        t = io.open(f, encoding='utf-8').read()
        for m in re.finditer(r'class=["\']([^"\']+)["\']', t):
            for c in m.group(1).split():
                vus.add(c.strip())
    return vus


PRESENTES = None


def morte(sel):
    cls = re.findall(r'\.([A-Za-z0-9_-]+)', sel)
    return bool(cls) and not any(c in PRESENTES for c in cls)


def role_de(sel):
    for nom, rx in ROLES:
        if rx.search(sel):
            return nom
    return 'autre'


def px(v):
    m = re.fullmatch(r'([\d.]+)px', v)
    if m:
        return float(m.group(1))
    m = re.fullmatch(r'([\d.]+)rem', v)
    if m:
        return float(m.group(1)) * 16
    return None


def norm_radius(v):
    """Normalise l'ECRITURE seulement — aucune fusion.

    « 0 », « 0px » -> « 0 » ; « 0.5rem » -> « .5rem ». Et on marque la famille
    « pill » : au-dela de ~500 px un rayon ne decrit plus une courbe, il dit
    « arrondi complet ». 999px, 9999px et 50rem disent la meme chose — mais on
    les compte separement, la fusion sera un choix, pas un effet de bord."""
    v = v.strip().lower()
    if re.fullmatch(r'0(px|rem|em|%)?', v):
        return '0', False
    v = re.sub(r'\b0+(\.\d+)', r'\1', v)
    p = px(v)
    return v, (p is not None and p >= 500) or v == '50%'


# --------------------------------------------------------------------------
def decoupe_couches(val):
    """Decoupe une valeur d'ombre aux virgules de PREMIER NIVEAU.

    rgba(3,7,15,.42) contient des virgules qui n'ont rien a voir avec la
    separation des couches — un split(',') naif casserait toutes les ombres
    colorees du site."""
    couches, cour, prof = [], '', 0
    for ch in val:
        if ch == '(':
            prof += 1
        elif ch == ')':
            prof -= 1
        if ch == ',' and prof == 0:
            couches.append(cour.strip())
            cour = ''
        else:
            cour += ch
    if cour.strip():
        couches.append(cour.strip())
    return couches


def extrait_fonction(c, i):
    """La sous-chaine fonctionnelle commencant a l'indice i, parentheses
    EQUILIBREES. « rgb(var(--blanc-rgb) / .06) » doit sortir en entier : une
    regex [^)]* s'arrete a la premiere parenthese fermante, laisse « / .06) »
    dans le flux, et le « .06 » finit compte comme un spread."""
    prof, j = 0, c.index('(', i)
    while j < len(c):
        if c[j] == '(':
            prof += 1
        elif c[j] == ')':
            prof -= 1
            if prof == 0:
                return c[i:j + 1]
        j += 1
    return c[i:]


def decompose(couche):
    """(inset, ox, oy, blur, spread, couleur) d'une couche d'ombre."""
    c = ' ' + couche.strip() + ' '
    inset = bool(re.search(r'\binset\b', c))
    c = re.sub(r'\binset\b', ' ', c)
    couleur = None
    m = re.search(r'\b(?:rgba?|hsla?|color-mix|var)\s*\(', c)
    if m:
        couleur = extrait_fonction(c, m.start())
        c = c.replace(couleur, ' ', 1)
    else:
        m = re.search(r'#[0-9a-fA-F]{3,8}\b|\b(?:currentColor|transparent|black|white)\b', c)
        if m:
            couleur = m.group(0)
            c = c[:m.start()] + ' ' + c[m.end():]
    longueurs = re.findall(r'-?[\d.]+(?:px|rem|em|%)?', c)
    while len(longueurs) < 4:
        longueurs.append('0')
    return inset, longueurs[0], longueurs[1], longueurs[2], longueurs[3], couleur


def alpha_de(couleur):
    if not couleur:
        return None
    m = re.search(r'/\s*([\d.]+)\s*\)', couleur)
    if m:
        return float(m.group(1))
    m = re.search(r'rgba?\([^)]*,\s*([\d.]+)\s*\)', couleur)
    if m and couleur.count(',') >= 3:
        return float(m.group(1))
    return None


# --------------------------------------------------------------------------
def entete(titre):
    print(u"\n" + u"=" * 78)
    print(u"  " + titre)
    print(u"=" * 78)


def cascade(decls, tokens):
    """Ou chaque token est-il (re)defini, sur QUEL SELECTEUR, sous quelle
    condition ?

    Le selecteur est le point clef, et c'est le piege de cette analyse. Deux
    definitions sans @media ne se marchent pas dessus si elles ne portent pas
    sur les memes elements : une variable posee sur « main > .section » est
    HERITEE par ce sous-arbre et redescend a :root partout ailleurs. C'est
    exactement ce que fait V79 pour tenir le hero hors de portee. Une
    definition n'est morte que si une AUTRE, plus loin, a le meme selecteur et
    la meme condition."""
    print(u"\n  ---- LA CASCADE DES TOKENS EXISTANTS " + u"-" * 38)
    par = defaultdict(list)
    for ligne, ats, sel, p, v in decls:
        if p in tokens:
            cond = " + ".join(a[:52] for a in ats) if ats else u""
            par[p].append((ligne, sel, cond, v))
    for t in tokens:
        l = par.get(t)
        if not l:
            continue
        print(u"  --%s" % t.lstrip('-'))
        for ligne, sel, cond, v in l:
            portee = sel if not cond else u"%s  { %s }" % (sel, cond)
            print(u"     L%-5d %-46s %s" % (ligne, portee[:46], v[:34]))
        vus, ecrases = {}, []
        for ligne, sel, cond, v in l:
            k = (sel, cond)
            if k in vus:
                ecrases.append((vus[k], ligne, sel))
            vus[k] = ligne
        for avant, apres, sel in ecrases:
            print(u"     !! L%d est ecrasee par L%d — meme selecteur, meme condition"
                  % (avant, apres))
        if len(set(s for _, s, _, _ in l)) > 1:
            print(u"     (selecteurs differents : surcharge de PORTEE, pas un doublon)")
    print()


# --------------------------------------------------------------------------
def rapport_radius(decls):
    entete(u"INVENTAIRE DES RAYONS — mbc974.com")
    rs = [(l, a, s, p, v) for l, a, s, p, v in decls if p in RADIUS_PROPS]
    print(u"  %d declarations de rayon" % len(rs))
    par_prop = defaultdict(int)
    for l, a, s, p, v in rs:
        par_prop[p] += 1
    for p, n in sorted(par_prop.items(), key=lambda x: -x[1]):
        print(u"     %-32s %3d" % (p, n))

    # tokenisees vs litterales
    tok = [x for x in rs if 'var(--r-' in x[4]]
    calc = [x for x in rs if 'var(' in x[4] and 'var(--r-' not in x[4]]
    lit = [x for x in rs if 'var(' not in x[4]]
    print(u"\n  %3d passent deja par --r-* (%.0f %%)" % (len(tok), len(tok) * 100.0 / max(len(rs), 1)))
    print(u"  %3d litterales" % len(lit))
    if calc:
        print(u"  %3d via une autre variable" % len(calc))

    atomes = defaultdict(lambda: {'n': 0, 'roles': defaultdict(int), 'morte': 0,
                                  'pill': False, 'sel': []})
    for l, a, s, p, v in lit:
        for part in v.split('/')[0].split():
            k, pill = norm_radius(part)
            if not re.match(r'^[\d.]', k) and k != '0':
                continue
            d = atomes[k]
            d['n'] += 1
            d['roles'][role_de(s)] += 1
            d['pill'] = pill
            if morte(s):
                d['morte'] += 1
            if len(d['sel']) < 3:
                d['sel'].append(s[:34])
    viv = {k: v for k, v in atomes.items() if v['morte'] < v['n']}
    mortes = {k: v for k, v in atomes.items() if v['morte'] == v['n']}
    print(u"\n  %d valeurs litterales distinctes, %d vivantes, %d mortes"
          % (len(atomes), len(viv), len(mortes)))

    print(u"\n  ---- LES VALEURS LITTERALES, DE LA PLUS PETITE A LA PLUS GRANDE " + u"-" * 12)
    print(u"  %-9s %5s %7s  %-30s %s" % (u"valeur", u"occ.", u"~px", u"roles", u"exemple"))

    def cle(x):
        p = px(x[0])
        return (999999 if x[1]['pill'] else (p if p is not None else 999998))
    for k, v in sorted(atomes.items(), key=cle):
        p = px(k)
        roles = ", ".join(u"%s×%d" % (a, b) for a, b in
                          sorted(v['roles'].items(), key=lambda x: -x[1])[:3])
        marque = u" [PILL]" if v['pill'] else (u" [morte]" if v['morte'] == v['n'] else u"")
        print(u"  %-9s %5d %7s  %-30s %s%s"
              % (k, v['n'], (u"%.0f" % p) if p is not None else u"-",
                 roles[:30], v['sel'][0][:24], marque))

    print(u"\n  ---- CE QUE VALENT LES TOKENS, ET QUI S'EN APPROCHE " + u"-" * 24)
    for nom, val in ((u'--r-sm', 14), (u'--r-md', 18), (u'--r-lg', 24), (u'--r-pill', 999)):
        proches = [(k, v['n'], px(k)) for k, v in atomes.items()
                   if px(k) is not None and px(k) > 0 and abs(px(k) - val) <= 3 and px(k) < 500]
        if nom == u'--r-pill':
            proches = [(k, v['n'], px(k)) for k, v in atomes.items() if v['pill']]
        tot = sum(n for _, n, _ in proches)
        print(u"  %-9s %3dpx  %2d valeur(s) litterale(s) a moins de 3 px, %d occurrence(s)%s"
              % (nom, val, len(proches), tot,
                 (u"  -> " + ", ".join(u"%s(%d)" % (k, n) for k, n, _ in
                                       sorted(proches, key=lambda x: -x[1])[:5])) if proches else u""))
    print()


# --------------------------------------------------------------------------
def rapport_ombres(decls):
    entete(u"INVENTAIRE DES OMBRES — mbc974.com")

    box = [(l, a, s, p, v) for l, a, s, p, v in decls if p == 'box-shadow']
    txt = [(l, a, s, p, v) for l, a, s, p, v in decls if p == 'text-shadow']
    dro = [(l, a, s, p, v) for l, a, s, p, v in decls
           if p == 'filter' or p.endswith('-filter')]
    dro = [x for x in dro if 'drop-shadow' in x[4]]
    print(u"  box-shadow            %3d declarations" % len(box))
    print(u"  text-shadow           %3d declarations" % len(txt))
    print(u"  filter: drop-shadow() %3d declarations" % len(dro))
    print(u"  (les trois ne sont PAS melangees : elles ne peignent pas la meme chose)")

    for titre, lot, tokens in ((u"BOX-SHADOW", box, ('--e1', '--e2', '--e3', '--glow-o',
                                                    '--glow-b', '--bevel')),
                               (u"TEXT-SHADOW", txt, ()),
                               (u"DROP-SHADOW", dro, ())):
        if not lot:
            continue
        print(u"\n  ---- %s " % titre + u"-" * (68 - len(titre)))
        aucune = [x for x in lot if x[4].strip() in ('none', '0 0 0 transparent')]
        vraies = [x for x in lot if x not in aucune]
        print(u"  %d valeurs, dont %d « none » (une remise a zero, pas une ombre)"
              % (len(lot), len(aucune)))

        # compositions : combien de couches ?
        par_n = defaultdict(int)
        for l, a, s, p, v in vraies:
            par_n[len(decoupe_couches(v))] += 1
        print(u"  couches par declaration : " + ", ".join(
            u"%d couche%s ×%d" % (k, u"s" if k > 1 else u"", n)
            for k, n in sorted(par_n.items())))

        # part deja tokenisee
        if tokens:
            avec = [x for x in vraies if any(t in x[4] for t in tokens)]
            pur = [x for x in vraies if re.fullmatch(
                r'\s*(var\(--(?:e[123]|glow-[ob]|bevel)\)\s*,?\s*)+', x[4])]
            print(u"  %d/%d utilisent au moins un token (%d n'utilisent QUE des tokens)"
                  % (len(avec), len(vraies), len(pur)))

        # les compositions litterales distinctes
        formes = defaultdict(lambda: {'n': 0, 'roles': defaultdict(int),
                                      'morte': 0, 'sel': [], 'lignes': []})
        for l, a, s, p, v in vraies:
            cle = re.sub(r'\s+', ' ', v).strip()
            d = formes[cle]
            d['n'] += 1
            d['roles'][role_de(s)] += 1
            if morte(s):
                d['morte'] += 1
            if len(d['sel']) < 3:
                d['sel'].append(s[:36])
            d['lignes'].append(l)
        viv = {k: v for k, v in formes.items() if v['morte'] < v['n']}
        print(u"  %d compositions distinctes, %d vivantes, %d mortes"
              % (len(formes), len(viv), len(formes) - len(viv)))

        print(u"\n  %-56s %4s %s" % (u"composition", u"occ.", u"role dominant"))
        for k, v in sorted(formes.items(), key=lambda x: -x[1]['n'])[:22]:
            dom = max(v['roles'].items(), key=lambda x: x[1])[0] if v['roles'] else u'?'
            mort = u" [morte]" if v['morte'] == v['n'] else u""
            print(u"  %-56s %4d %s%s" % (k[:56], v['n'], dom, mort))
        if len(formes) > 22:
            print(u"  … et %d autres" % (len(formes) - 22))

        # decomposition des couches litterales (une seule couche)
        if titre == u"BOX-SHADOW":
            print(u"\n  ---- DECOMPOSITION DES COUCHES LITTERALES " + u"-" * 33)
            print(u"  %-7s %-7s %-7s %-8s %-6s %-28s %s"
                  % (u"inset", u"off-x", u"off-y", u"blur", u"spread", u"couleur", u"occ."))
            couches = defaultdict(int)
            for l, a, s, p, v in vraies:
                for c in decoupe_couches(v):
                    if 'var(--e' in c or 'var(--glow' in c or 'var(--bevel' in c:
                        continue
                    couches[decompose(c)] += 1
            for (ins, ox, oy, bl, sp, col), n in sorted(couches.items(), key=lambda x: -x[1])[:18]:
                a = alpha_de(col)
                print(u"  %-7s %-7s %-7s %-8s %-6s %-28s %d"
                      % (u"inset" if ins else u"", ox, oy, bl, sp,
                         (col or u"?")[:28] + (u" a=%.2f" % a if a is not None else u""), n))
    print()


# --------------------------------------------------------------------------
def rapport_a11y(decls):
    """Un etat transmis PAR LA SEULE OMBRE est invisible pour beaucoup de gens.

    On cherche les regles d'etat (focus, erreur, actif, selectionne) dont le
    bloc ne contient qu'une ombre : ni outline, ni bordure, ni fond, ni
    couleur de texte."""
    entete(u"CONTROLE — UN ETAT PORTE PAR LA SEULE OMBRE ?")
    ETATS = re.compile(r':focus|:focus-visible|:active|:checked|\[aria-invalid|'
                       r'\.is-error|\.is-active|\.is-selected|\.has-error|'
                       r'\.error|\.invalid|--error|\.is-on\b|\[aria-current')
    par_regle = defaultdict(list)
    for ligne, ats, sel, p, v in decls:
        par_regle[(sel, tuple(ats))].append((p, v, ligne))
    suspects = []
    for (sel, ats), props in par_regle.items():
        if not ETATS.search(sel):
            continue
        noms = {p for p, v, l in props}
        if 'box-shadow' not in noms:
            continue
        autres = noms & {'outline', 'outline-color', 'outline-width', 'outline-style',
                         'border', 'border-color', 'border-width', 'border-style',
                         'background', 'background-color', 'color', 'text-decoration',
                         'font-weight', 'transform', 'opacity', 'border-bottom',
                         'border-top', 'border-inline', 'border-block'}
        if not autres:
            suspects.append((props[0][2], sel, ats, sorted(noms)))
    if not suspects:
        print(u"  Aucun. Toute regle d'etat qui pose une ombre pose aussi autre chose")
        print(u"  (contour, bordure, fond ou couleur).")
    else:
        print(u"  %d regle(s) ou l'ombre est le seul signal de l'etat :" % len(suspects))
        for ligne, sel, ats, noms in suspects:
            print(u"    L%-5d %-46s %s" % (ligne, sel[:46], ", ".join(noms)[:24]))
        print(u"\n  A SIGNALER, PAS A CORRIGER PENDANT L'INVENTAIRE.")
    print()


def rapport_selecteurs(decls):
    entete(u"LES SELECTEURS BRUTS — pour verifier le classement par role")
    for titre, filtre in ((u"RAYONS", lambda p: p in RADIUS_PROPS),
                          (u"OMBRES", lambda p: p in ('box-shadow', 'text-shadow'))):
        print(u"\n  ---- %s " % titre + u"-" * 60)
        vus = defaultdict(lambda: defaultdict(int))
        for ligne, ats, sel, p, v in decls:
            if filtre(p):
                vus[role_de(sel)][sel] += 1
        for role in sorted(vus, key=lambda r: -sum(vus[r].values())):
            sels = vus[role]
            print(u"  %-16s %3d declarations, %d selecteur(s)"
                  % (role, sum(sels.values()), len(sels)))
            for s, n in sorted(sels.items(), key=lambda x: -x[1])[:6]:
                print(u"      %-64s ×%d" % (s[:64], n))
    print()


def main():
    global PRESENTES
    css = io.open(CSS, encoding='utf-8').read()
    PRESENTES = classes_du_site()
    decls = declarations(css)
    quoi = sys.argv[1] if len(sys.argv) > 1 else 'tout'
    if quoi == 'selecteurs':
        return rapport_selecteurs(decls)
    if quoi in ('tout', 'radius'):
        cascade(decls, ('--r-sm', '--r-md', '--r-lg', '--r-pill'))
        rapport_radius(decls)
    if quoi in ('tout', 'ombres'):
        cascade(decls, ('--e1', '--e2', '--e3', '--glow-o', '--glow-b', '--bevel'))
        rapport_ombres(decls)
        rapport_a11y(decls)
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
