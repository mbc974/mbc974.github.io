# -*- coding: utf-8 -*-
"""Integre les logos des clubs adverses dans le calendrier des matchs.

Les logos sont lus depuis le dossier Telechargements, avec ces noms
(png, jpg ou webp) :

    bc2s     Basket Club Sainte-Suzanne  (Les Papangues)
    bcd3     Basket Club Dionysien       (volcan)
    sbbc     Saint-Benoit Basket Club    (ballon bleu clair)
    mtg      Association MTG Basketball  (tigre)
    bjssr    JS Sainte-Rosienne          (variante AVEC le ballon de basket
                                          et l'arche orange : "JEUNESSE
                                          SPORTIVE SAINTE ROSIENNE" en arc
                                          au-dessus, "BASKET CLUB" dessous.
                                          PAS le rond bleu "Pays des Laves",
                                          qui ne porte pas de ballon.)
    smb2     Sainte-Marie Basket         (silhouettes)
    picks3   Picks La Possession         (dodo)

    python .claude/add-club-logos.py            integration complete
    python .claude/add-club-logos.py --planche  planche de controle seule
                                                (n'ecrit rien dans le depot)

Aucun des sept fichiers fournis n'a de fond transparent : quatre sont sur
blanc, le Dionysien sur noir, les Papangues sur bleu vif, Picks sur marine.
Poses tels quels sur la plaque blanche de la case, les trois derniers
donneraient des paves de couleur. Le script detoure donc le fond par
propagation depuis les bords, ce qui suppose deux precautions :

  - certains fichiers portent un cadre parasite (noir autour du bleu pour
    bc2s, gris autour du noir pour bcd3). La couleur de fond est cherchee
    en profondeur, pas au ras du bord, et le cadre est rogne.
  - la propagation respecte la connexite : le volcan noir de bcd3, enferme
    au centre par le rond vert, n'est pas joignable depuis le bord et
    survit donc au detourage de son fond, lui aussi noir.

Picks fait exception et garde son fond marine : son texte est argente et
cyan clair, illisible une fois pose sur blanc. Le liseré de la plaque
suffit a detacher sa case du bleu nuit de la section.
"""
import io
import os
import re
import sys
from collections import Counter, deque

from PIL import Image

SRC = 'C:/Users/ALEX/Downloads/'
DEST = 'assets/logos/clubs/'
PLANCHE = 'planche-logos.png'
EXTS = ('.png', '.jpg', '.jpeg', '.webp')

# La case fait 72 px : le 144 sert les ecrans 2x, le 288 les 3x.
CASE = 72
TAILLES = (288, 144)

TRAVAIL = 640    # resolution de travail, au-dessus de la plus grande sortie
TOL = 58         # tolerance couleur du detourage (distance RGB)
MARGE = 1.10     # respiration autour du logo une fois recadre

# slug -> (nom, detourer le fond)
CLUBS = {
    'bc2s':   ('Basket Club Sainte-Suzanne', True),
    'bcd3':   ('Basket Club Dionysien 3', True),
    'sbbc':   ('Saint-Benoit Basket Club', True),
    'mtg':    ('Association MTG Basketball', True),
    'bjssr':  ('BC Jeunesse Sportive Sainte-Rosienne', True),
    'smb2':   ('Sainte-Marie Basket 2', True),
    'picks3': ('Picks Basket La Possession 3', False),
}


def trouver(slug):
    for e in EXTS:
        p = SRC + slug + e
        if os.path.exists(p):
            return p
    return None


def charger(chemin):
    """Ouvre en RGB, aplati sur blanc, ramene a la resolution de travail."""
    im = Image.open(chemin).convert('RGBA')
    plat = Image.new('RGBA', im.size, (255, 255, 255, 255))
    im = Image.alpha_composite(plat, im).convert('RGB')
    if max(im.size) > TRAVAIL:
        r = TRAVAIL / float(max(im.size))
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))),
                       Image.LANCZOS)
    return im


def pixels(im):
    b = im.tobytes()
    return [(b[i], b[i + 1], b[i + 2]) for i in range(0, len(b), 3)]


def anneau(px, w, h, d):
    """Pixels du rectangle creux situe a d pixels du bord."""
    if d * 2 + 1 >= min(w, h):
        return []
    out = [px[d * w + x] for x in range(d, w - d)]
    out += [px[(h - 1 - d) * w + x] for x in range(d, w - d)]
    out += [px[y * w + d] for y in range(d + 1, h - 1 - d)]
    out += [px[y * w + w - 1 - d] for y in range(d + 1, h - 1 - d)]
    return out


def dominante(pixels):
    """Couleur dominante d'une liste, tolerante au bruit de compression."""
    if not pixels:
        return (255, 255, 255), 0.0
    seaux = Counter((r >> 4, g >> 4, b >> 4) for r, g, b in pixels)
    seau, n = seaux.most_common(1)[0]
    membres = [p for p in pixels if (p[0] >> 4, p[1] >> 4, p[2] >> 4) == seau]
    moy = tuple(sum(c[i] for c in membres) // len(membres) for i in range(3))
    return moy, n / float(len(pixels))


def ecart(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** .5


def couches(im, taux_min=.70):
    """Empile les aplats concentriques rencontres en partant du bord.

    Renvoie une liste de (debut, fin, couleur). L'exploration s'arrete quand
    le pourtour cesse durablement d'etre un aplat, c'est-a-dire quand le logo
    lui-meme entre dans le cadre.

    Les anneaux de transition sont tolerés : entre un cadre et le fond qu'il
    enferme, l'anti-aliasing laisse un ou deux anneaux melanges. S'arreter au
    premier d'entre eux revenait a ne jamais voir le fond (bcd3 restait sur
    son cadre noir, bc2s sur le lisere sombre issu de sa reduction).
    """
    px = pixels(im)
    w, h = im.size
    out, manques = [], 0
    for d in range(min(w, h) // 3):
        c, taux = dominante(anneau(px, w, h, d))
        if taux < taux_min:
            manques += 1
            if manques > 3:
                break
            continue
        manques = 0
        if out and ecart(out[-1][2], c) < 14:
            out[-1] = (out[-1][0], d, out[-1][2])
        else:
            out.append((d, d, c))
    return out


def fond_principal(im):
    """Profondeur a rogner et couleur du vrai fond.

    Un cadre parasite fait quelques pixels d'epaisseur, un fond en fait des
    dizaines : on retient donc la couche la plus epaisse, pas la premiere.
    Sans ce critere, le cadre noir de 7 px de bcd3 passait pour le fond et
    le blanc qu'il enferme n'etait jamais retire.
    """
    cs = couches(im)
    if not cs:
        px = pixels(im)
        return 0, dominante(anneau(px, im.width, im.height, 0))[0]
    d0, d1, c = max(cs, key=lambda k: k[1] - k[0])
    if d0 > min(im.size) * .15:   # trop profond pour etre un fond
        d0, d1, c = cs[0]
    return d0, c


def detourer(im, fond, tol=TOL):
    """Rend transparent l'aplat de fond joignable depuis les bords.

    La connexite est le point cle : un aplat de meme couleur enferme au
    centre du logo n'est pas joignable depuis le bord, et reste opaque.
    """
    w, h = im.size
    px = pixels(im)
    tol2 = tol * tol
    fr, fg, fb = fond

    proche = bytearray(w * h)
    for i, (r, g, b) in enumerate(px):
        dr = r - fr
        dg = g - fg
        db = b - fb
        if dr * dr + dg * dg + db * db <= tol2:
            proche[i] = 1

    vu = bytearray(w * h)
    file = deque()
    for x in range(w):
        for i in (x, (h - 1) * w + x):
            if proche[i] and not vu[i]:
                vu[i] = 1
                file.append(i)
    for y in range(h):
        for i in (y * w, y * w + w - 1):
            if proche[i] and not vu[i]:
                vu[i] = 1
                file.append(i)

    while file:
        i = file.popleft()
        x = i % w
        if x and proche[i - 1] and not vu[i - 1]:
            vu[i - 1] = 1
            file.append(i - 1)
        if x < w - 1 and proche[i + 1] and not vu[i + 1]:
            vu[i + 1] = 1
            file.append(i + 1)
        if i >= w and proche[i - w] and not vu[i - w]:
            vu[i - w] = 1
            file.append(i - w)
        if i < w * (h - 1) and proche[i + w] and not vu[i + w]:
            vu[i + w] = 1
            file.append(i + w)

    alpha = Image.frombytes('L', (w, h), bytes(0 if v else 255 for v in vu))
    out = im.convert('RGBA')
    out.putalpha(alpha)
    return out, sum(vu) / float(w * h)


def cadrer(im):
    """Recadre sur le contenu visible, puis centre dans un carre."""
    boite = im.split()[3].point(lambda a: 255 if a > 8 else 0).getbbox()
    if boite:
        im = im.crop(boite)
    c = int(max(im.size) * MARGE)
    carre = Image.new('RGBA', (c, c), (255, 255, 255, 0))
    carre.paste(im, ((c - im.width) // 2, (c - im.height) // 2))
    return carre


def arrondir(im, part=.22):
    """Coins arrondis, pour un logo dont le fond plein est conserve : sa
    case epouse ainsi l'arrondi des autres au lieu de trancher au carre."""
    g = 4
    m = Image.new('L', (im.width * g, im.height * g), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(m).rounded_rectangle(
        [0, 0, im.width * g - 1, im.height * g - 1],
        radius=int(im.width * g * part), fill=255)
    im = im.convert('RGBA')
    im.putalpha(m.resize(im.size, Image.LANCZOS))
    return im


def preparer(chemin, decouper):
    im = charger(chemin)
    if decouper:
        d, fond = fond_principal(im)
        if d:
            im = im.crop((d, d, im.width - d, im.height - d))
        rgba, part = detourer(im, fond)
        return cadrer(rgba), 'detoure #%02X%02X%02X%s, %2d%% retire' % (
            fond[0], fond[1], fond[2],
            ' (cadre de %d px rogne)' % d if d else '', round(part * 100))

    # fond conserve : on complete en carre avec la couleur du pourtour
    fond = dominante(anneau(pixels(im), im.width, im.height, 0))[0]
    c = max(im.size)
    carre = Image.new('RGBA', (c, c), (fond[0], fond[1], fond[2], 255))
    carre.paste(im.convert('RGBA'), ((c - im.width) // 2, (c - im.height) // 2))
    return arrondir(carre), (
        'fond #%02X%02X%02X conserve (texte illisible sur blanc)'
        % (fond[0], fond[1], fond[2]))


def ecrire(slug, rgba):
    os.makedirs(DEST, exist_ok=True)
    grande = max(TAILLES)
    for taille in TAILLES:
        r = rgba.resize((taille, taille), Image.LANCZOS)
        nom = '%s%s%s.webp' % (DEST, slug,
                               '' if taille == grande else '-%d' % taille)
        r.save(nom, 'WEBP', quality=90, method=6)
    return os.path.getsize('%s%s.webp' % (DEST, slug)) // 1024


def balisage(slug):
    """Case d'un logo adverse, avec repli sur le sigle si l'image manque."""
    petite = min(TAILLES)
    return ('<span class="mx-crest mx-crest--logo">'
            '<img src="assets/logos/clubs/{s}-{p}.webp" '
            'srcset="assets/logos/clubs/{s}-{p}.webp {p}w, '
            'assets/logos/clubs/{s}.webp {g}w" sizes="{c}px" alt="" '
            'width="{g}" height="{g}" loading="lazy" decoding="async" '
            'onerror="this.closest(\'.mx-crest\').className='
            '\'mx-crest mx-crest--sigle\';'
            'this.closest(\'.mx-crest\').textContent=\'{S}\'">'
            '</span>').format(s=slug, S=slug.upper(), p=petite,
                              g=max(TAILLES), c=CASE)


ECH = 3          # les cases sont dessinees a l'echelle 3 pour etre jugeables
DOMICILE = ('sbbc', 'smb2', 'picks3')   # J3, J6, J7


def case_rendue(rgba, taille, radius, pad, bordure, degrade, anneau=None,
                ombre=None):
    """Reproduit une case du calendrier avec ses valeurs CSS reelles."""
    from PIL import ImageDraw, ImageFilter
    t, r, p = taille * ECH, radius * ECH, pad * ECH
    marge = 26
    hors = Image.new('RGBA', (t + marge * 2, t + marge * 2), (0, 0, 0, 0))

    if ombre:
        dy, flou, alpha = ombre
        oc = Image.new('RGBA', hors.size, (0, 0, 0, 0))
        ImageDraw.Draw(oc).rounded_rectangle(
            [marge, marge + dy * ECH, marge + t, marge + t + dy * ECH],
            radius=r, fill=(3, 8, 18, alpha))
        hors = Image.alpha_composite(hors, oc.filter(
            ImageFilter.GaussianBlur(flou * ECH / 2.)))

    plaque = Image.new('RGBA', (t, t), degrade[0] + (255,))
    if degrade[0] != degrade[1]:
        pd = ImageDraw.Draw(plaque)
        for y in range(t):
            k = y / float(t - 1)
            pd.line([(0, y), (t, y)], fill=tuple(
                int(degrade[0][i] + (degrade[1][i] - degrade[0][i]) * k)
                for i in range(3)))
    masque = Image.new('L', (t, t), 0)
    ImageDraw.Draw(masque).rounded_rectangle([0, 0, t - 1, t - 1],
                                             radius=r, fill=255)
    plaque.putalpha(masque)

    inner = rgba.resize((t - 2 * p, t - 2 * p), Image.LANCZOS)
    plaque.paste(inner, (p, p), inner)
    pd = ImageDraw.Draw(plaque)
    pd.rounded_rectangle([0, 0, t - 1, t - 1], radius=r, outline=bordure,
                         width=max(1, ECH))
    hors.paste(plaque, (marge, marge), plaque)
    if anneau:   # box-shadow 0 0 0 2px : l'anneau est exterieur a la case
        ad = ImageDraw.Draw(hors)
        e = 2 * ECH
        ad.rounded_rectangle([marge - e, marge - e, marge + t + e - 1,
                              marge + t + e - 1], radius=r + e,
                             outline=anneau, width=e)
    return hors


def planche(rendus):
    """Controle visuel : la case d'avant et celle d'aujourd'hui, cote a cote,
    dessinees avec les valeurs CSS reelles et posees sur le bleu nuit de la
    section — le but etant de juger la lisibilite, pas le logo isole."""
    from PIL import ImageDraw
    col, marge, haut = 72 * ECH + 44, 30, 540
    img = Image.new('RGB', (marge * 2 + col * len(rendus), haut), (16, 27, 48))
    d = ImageDraw.Draw(img)
    for y in range(haut):     # le fond degrade de la section
        k = y / float(haut - 1)
        d.line([(0, y), (img.width, y)], fill=(int(16 - 9 * k),
                                               int(27 - 14 * k),
                                               int(48 - 24 * k)))

    for i, (slug, rgba) in enumerate(rendus):
        cx = marge + i * col + col // 2
        avant = case_rendue(rgba, 40, 10, 3, (191, 210, 228, 56),
                            ((255, 255, 255), (255, 255, 255)))
        img.paste(avant, (cx - avant.width // 2, 44), avant)

        dom = slug in DOMICILE
        apres = case_rendue(
            rgba, 72, 18, 6,
            (255, 214, 178, 191) if dom else (255, 255, 255, 158),
            ((255, 255, 255), (234, 240, 247)),
            anneau=(232, 130, 42, 122) if dom else None,
            ombre=(10, 22, 140))
        img.paste(apres, (cx - apres.width // 2, 236), apres)
        d.text((cx - 18, 208), slug, fill=(200, 215, 235))

    d.text((marge, 18), 'AVANT  —  case 40 px', fill=(150, 170, 196))
    d.text((marge, 500), 'APRES  —  case 72 px, plaque degradee, ombre '
           'portee, anneau orange sur les matchs a domicile (J3, J6, J7)',
           fill=(232, 130, 42))
    img.save(PLANCHE)
    return PLANCHE


def main():
    essai = '--planche' in sys.argv
    if not os.path.exists('index.html'):
        print('!! lancer depuis la racine du depot')
        return 1

    faits, manquants, rendus = {}, [], []
    for slug, (nom, decouper) in CLUBS.items():
        p = trouver(slug)
        if not p:
            manquants.append(slug)
            continue
        rgba, note = preparer(p, decouper)
        rendus.append((slug, rgba))
        faits[slug] = rgba
        print('  %-7s %-12s %s' % (slug, os.path.basename(p), note))

    if manquants:
        print('\n  fichiers absents (le sigle est conserve) : %s'
              % ', '.join(manquants))
    if not faits:
        print('\n!! aucun logo trouve dans %s' % SRC)
        return 1

    if essai:
        print('\n  planche de controle : %s' % planche(rendus))
        return 0

    print('')
    for slug, rgba in faits.items():
        print('  %-7s %3d Ko' % (slug, ecrire(slug, rgba)))

    s = io.open('index.html', encoding='utf-8').read()
    n = 0
    for slug in faits:
        # cas 1 : la case porte encore le sigle
        ancien = ('<span class="mx-crest mx-crest--sigle" aria-hidden="true">'
                  '%s</span>' % slug.upper())
        if ancien in s:
            s = s.replace(ancien, balisage(slug))
            n += 1
            continue
        # cas 2 : la case a deja un logo, on regenere son balisage pour
        # qu'un changement de taille se propage sans retoucher le HTML
        motif = re.compile(
            r'<span class="mx-crest mx-crest--logo">\s*<img[^>]*?'
            r'logos/clubs/%s[-.][^>]*?>\s*</span>' % re.escape(slug))
        s, k = motif.subn(balisage(slug), s)
        n += k
    io.open('index.html', 'w', encoding='utf-8', newline='\n').write(s)
    print('\n  %d cases mises a jour' % n)

    # les rendus d'une taille precedente n'ont plus de reference
    for f in sorted(os.listdir(DEST)):
        garde = ['%s.webp' % g for g in faits]
        garde += ['%s-%d.webp' % (g, min(TAILLES)) for g in faits]
        if f not in garde:
            os.remove(DEST + f)
            print('  retire : %s' % f)
    os.system(sys.executable + ' .claude/bump-assets.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
