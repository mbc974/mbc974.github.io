# -*- coding: utf-8 -*-
"""Dessine l'affiche partageable du calendrier (1080 x 1350, format reseaux).

Appele par set-calendrier-prm.py ; ne se lance pas seul, il lui faut les
rencontres deja lues dans le PDF officiel.

Le gabarit reprend la charte du site : fond nuit, orange MBC, titres en Bebas.
Les mesures (marges, hauteur et pas des lignes, teintes) ont ete relevees sur
la premiere version de l'affiche pour que la mise a jour ne change QUE ce qui
doit changer : le camp de chaque rencontre et le nombre de matchs a domicile.
"""
import io
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

L, H = 1080, 1350
MARGE = 56
LARG = L - 2 * MARGE                      # 968
LIGNE_H, LIGNE_PAS, LIGNE_Y0 = 102, 111, 413

NUIT = (10, 17, 30)
LIGNE_EXT = (18, 29, 51)
ORANGE_G, ORANGE_D = (215, 105, 26), (232, 130, 42)
BLANC = (255, 255, 255)
GLACIER = (150, 173, 197)
ENCRE = (6, 12, 26)

# Les polices du site (Anton en titrage, Barlow en texte), embarquees dans
# .claude/fonts. Elles sont sous licence SIL OFL, donc redistribuables, et les
# embarquer rend l'affiche reproductible sans reseau. Bebas, installee sur le
# poste, avait ete essayee d'abord : elle n'a pas les capitales accentuees, et
# « PRE-REGIONALE », « A 20H30 » et « EXTERIEUR » sortaient avec des carres.
ICI = os.path.dirname(os.path.abspath(__file__))
ANTON = os.path.join(ICI, 'fonts', 'Anton-Regular.ttf')
BARLOW = os.path.join(ICI, 'fonts', 'Barlow-Regular.ttf')
BARLOW_C = os.path.join(ICI, 'fonts', 'BarlowCondensed-SemiBold.ttf')


def police(chemin, taille):
    return ImageFont.truetype(chemin, taille)


def larg(d, txt, f, espace=0):
    if espace:
        return int(sum(d.textlength(c, font=f) for c in txt) + espace * max(0, len(txt) - 1))
    b = d.textbbox((0, 0), txt, font=f)
    return b[2] - b[0]


def texte(d, xy, txt, f, fill, espace=0):
    """Ecrit un texte, avec interlettrage optionnel (PIL ne le gere pas seul)."""
    if not espace:
        d.text(xy, txt, font=f, fill=fill)
        return larg(d, txt, f)
    x, y = xy
    for c in txt:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + espace
    return int(x - xy[0])


def fond():
    """Nuit, plus deux halos : chaud en haut a droite, froid en bas a gauche."""
    im = Image.new('RGB', (L, H), NUIT)
    halo = Image.new('L', (L, H), 0)
    hd = ImageDraw.Draw(halo)
    hd.ellipse([L - 520, -380, L + 260, 400], fill=190)
    halo = halo.filter(ImageFilter.GaussianBlur(150))
    im = Image.composite(Image.new('RGB', (L, H), (150, 74, 22)), im, halo)
    halo = Image.new('L', (L, H), 0)
    hd = ImageDraw.Draw(halo)
    hd.ellipse([-380, H - 460, 480, H + 260], fill=150)
    halo = halo.filter(ImageFilter.GaussianBlur(170))
    return Image.composite(Image.new('RGB', (L, H), (24, 58, 110)), im, halo)


def bande_orange(d, boite, r=16, g=ORANGE_G, dr=ORANGE_D):
    """Rectangle arrondi, degrade horizontal (l'orange s'eclaircit vers la droite)."""
    x0, y0, x1, y1 = boite
    w, h = int(x1 - x0), int(y1 - y0)
    bande = Image.new('RGB', (w, h))
    p = bande.load()
    for x in range(w):
        t = x / float(max(1, w - 1))
        c = tuple(int(g[k] + (dr[k] - g[k]) * t) for k in range(3))
        for y in range(h):
            p[x, y] = c
    masque = Image.new('L', (w, h), 0)
    ImageDraw.Draw(masque).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    return bande, masque, (int(x0), int(y0))


def pastille(im, d, txte, cx_droite, cy, f, pleine):
    """La mention DOMICILE (pastille pleine) ou EXTERIEUR (pastille cerclee)."""
    pad_x, hh, esp = 22, 40, 1.6
    w = larg(d, txte, f, esp) + 2 * pad_x
    x1, x0 = cx_droite, cx_droite - w
    y0, y1 = cy - hh // 2, cy + hh // 2
    if pleine:
        d.rounded_rectangle([x0, y0, x1, y1], radius=hh // 2, fill=ENCRE)
        coul = BLANC
    else:
        d.rounded_rectangle([x0, y0, x1, y1], radius=hh // 2,
                            outline=(86, 108, 138), width=2)
        coul = GLACIER
    b = d.textbbox((0, 0), txte, font=f)
    texte(d, (x0 + pad_x, cy - (b[3] + b[1]) / 2), txte, f, coul, esp)
    return x0


def logo_club(sigle):
    for c in ('assets/logos/clubs/%s.webp' % sigle.lower(),
              'assets/logos/clubs/%s-144.webp' % sigle.lower()):
        if os.path.exists(c):
            return Image.open(c).convert('RGBA')
    return None


def produire(mbc, base):
    im = fond()
    d = ImageDraw.Draw(im)
    f_t1 = police(ANTON, 82)
    f_t2 = police(ANTON, 38)
    f_head = police(BARLOW_C, 32)
    f_sub = police(BARLOW_C, 23)
    f_ban = police(ANTON, 30)
    f_j = police(ANTON, 29)
    f_club = police(BARLOW, 24)
    f_pas = police(BARLOW_C, 21)
    f_pied1 = police(ANTON, 33)
    f_pied2 = police(BARLOW, 20)

    # ---- en-tete : ecusson + identite ----
    if os.path.exists('assets/logos/mbc-logo.png'):
        lg = Image.open('assets/logos/mbc-logo.png').convert('RGBA')
        lg.thumbnail((112, 112), Image.LANCZOS)
        im.paste(lg, (MARGE, 26), lg)
    xt = MARGE + 128
    texte(d, (xt, 32), u'MBC · LA MONTAGNE BASKET CLUB', f_head, BLANC, 1.2)
    w = texte(d, (xt, 70), u'SENIORS MASCULINS · PRÉ-RÉGIONALE, ZONE NORD', f_sub, GLACIER, 1.4)
    d.rounded_rectangle([xt, 102, xt + w, 106], radius=2, fill=ORANGE_D)

    # ---- titre ----
    y = 146
    w1 = larg(d, 'CALENDRIER ', f_t1)
    d.text((MARGE, y), 'CALENDRIER ', font=f_t1, fill=BLANC)
    d.text((MARGE + w1, y), 'PHASE 1', font=f_t1, fill=ORANGE_D)
    d.text((MARGE, y + 100), 'SAISON 2026/2027', font=f_t2, fill=BLANC)

    # ---- bandeau horaire (article 4 du reglement : vendredi 20h30) ----
    bande, masque, pos = bande_orange(d, (MARGE, 318, L - MARGE, 386), r=16)
    im.paste(bande, pos, masque)
    d = ImageDraw.Draw(im)
    txt = u'TOUS LES MATCHS LE VENDREDI À 20H30'
    bb = d.textbbox((0, 0), txt, font=f_ban)
    texte(d, ((L - larg(d, txt, f_ban, 2.2)) / 2, 352 - (bb[3] + bb[1]) / 2),
          txt, f_ban, ENCRE, 2.2)

    # ---- les sept rencontres ----
    for i, m in enumerate(mbc):
        y0 = LIGNE_Y0 + i * LIGNE_PAS
        y1 = y0 + LIGNE_H
        cy = (y0 + y1) // 2
        dom = m['domicile']
        if dom:
            bande, masque, pos = bande_orange(d, (MARGE, y0, L - MARGE, y1), r=14)
            im.paste(bande, pos, masque)
            d = ImageDraw.Draw(im)
            c_date, c_club = ENCRE, (46, 24, 8)
        else:
            d.rounded_rectangle([MARGE, y0, L - MARGE, y1], radius=14,
                                fill=LIGNE_EXT, outline=(32, 48, 78), width=1)
            c_date, c_club = BLANC, GLACIER

        # vignette du logo adverse, sur fond clair pour rester lisible partout
        vx, vy, vs = MARGE + 16, y0 + 15, 72
        d.rounded_rectangle([vx, vy, vx + vs, vy + vs], radius=12, fill=(244, 247, 250))
        lg = logo_club(m['sigle'])
        if lg:
            lg = lg.copy()
            lg.thumbnail((vs - 12, vs - 12), Image.LANCZOS)
            im.paste(lg, (vx + (vs - lg.width) // 2, vy + (vs - lg.height) // 2), lg)
            d = ImageDraw.Draw(im)

        tx = vx + vs + 22
        etiq = u'J%d ' % m['journee']
        reste = u'· %s %d %s' % (m['jour'].upper(), m['num'], m['mois'].upper())
        d.text((tx, cy - 34), etiq, font=f_j, fill=ENCRE if dom else ORANGE_D)
        d.text((tx + larg(d, etiq, f_j), cy - 34), reste, font=f_j, fill=c_date)
        d.text((tx, cy + 4), m['adversaire'], font=f_club, fill=c_club)

        pastille(im, d, u'DOMICILE' if dom else u'EXTÉRIEUR',
                 L - MARGE - 20, cy, f_pas, dom)

    # ---- pied : le compte, et ou l'on joue ----
    yp = LIGNE_Y0 + 7 * LIGNE_PAS + 26
    d.rounded_rectangle([MARGE, yp, MARGE + 7, yp + 46], radius=3, fill=ORANGE_D)
    n = sum(1 for m in mbc if m['domicile'])
    g = u'%d MATCH%s À DOMICILE ' % (n, 'S' if n > 1 else '')
    d.text((MARGE + 22, yp - 2), g, font=f_pied1, fill=BLANC)
    d.text((MARGE + 22 + larg(d, g, f_pied1), yp - 2), u'AU GYMNASE DE LA MONTAGNE',
           font=f_pied1, fill=ORANGE_D)
    d.text((MARGE + 22, yp + 44), u'mbc974.com · @mbc974.re', font=f_pied2, fill=(126, 146, 170))

    im.save(base + '.png', 'PNG', optimize=True)
    for w in (1080, 720, 480):
        r = im.resize((w, int(H * w / float(L))), Image.LANCZOS)
        suff = '' if w == 1080 else '-%d' % w
        r.save('%s%s.webp' % (base, suff), 'WEBP', quality=82, method=6)
    return base + '.png'
