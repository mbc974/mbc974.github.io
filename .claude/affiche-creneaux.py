# -*- coding: utf-8 -*-
"""L'affiche des creneaux hebdomadaires, tiree de data/creneaux.json.

    python .claude/affiche-creneaux.py

POURQUOI CE SCRIPT EXISTE
--------------------------
L'ancienne affiche des creneaux a ete RETIREE du site le 08/09/2026 : elle
annoncait des horaires que le site ne connaissait pas, et personne ne savait
laquelle des deux disait vrai. La doctrine appliquee alors — « on retire le CTA
qui mene vers une information contradictoire, on ne laisse pas une information
fausse visible » — reglait le symptome, pas la cause.

La cause, c'est qu'une affiche dessinee a la main est une SECONDE source de
verite. Elle derive des que les horaires changent, et rien ne le signale.

Ce script supprime la cause : l'affiche est PRODUITE a partir de
data/creneaux.json, le meme fichier qui alimente le planning de l'accueil, la
page /creneaux/ et l'openingHoursSpecification. Elle ne peut plus diverger : si
un creneau bouge, on relance et l'image suit.

LA CHARTE N'EST PAS REDEFINIE ICI
----------------------------------
Les couleurs, les polices et le fond a deux halos sont importes de
affiche-calendrier.py. Les recopier aurait cree le meme probleme a l'echelle du
graphisme : deux affiches du meme club qui divergent lentement.

LE NOM DE FICHIER PORTE UNE EMPREINTE DU CONTENU
-------------------------------------------------
Meme regle que pour l'affiche du calendrier, et pour la meme raison : le
service worker sert les images « versionnees par leur nom ». Une affiche
corrigee qui garderait son nom continuerait d'etre servie dans son ancienne
version a tout visiteur deja venu — c'est-a-dire avec les mauvais horaires.
"""
import hashlib
import io
import json
import os
import sys
import importlib.util

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)

_spec = importlib.util.spec_from_file_location(
    "afc", os.path.join(ICI, 'affiche-calendrier.py'))
afc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(afc)          # aucun effet de bord : que des fonctions

from PIL import Image, ImageDraw       # noqa: E402

L, H = afc.L, afc.H
MARGE = afc.MARGE
NUIT, BLANC, GLACIER, ENCRE = afc.NUIT, afc.BLANC, afc.GLACIER, afc.ENCRE
ORANGE_G, ORANGE_D = afc.ORANGE_G, afc.ORANGE_D
LIGNE_EXT = afc.LIGNE_EXT

JOURS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
NATURE = {'entrainement': u'Entraînement', 'loisir': u'Loisir mixte',
          'match': u'Match à domicile'}


def hhmm(s):
    return s.replace(':', 'h')


def produire(d, base):
    im = afc.fond()
    dr = ImageDraw.Draw(im)

    f_t1 = afc.police(afc.ANTON, 76)
    f_t2 = afc.police(afc.ANTON, 30)
    f_sur = afc.police(afc.BARLOW_C, 23)
    f_jour = afc.police(afc.ANTON, 31)
    f_h = afc.police(afc.ANTON, 30)
    f_cat = afc.police(afc.BARLOW_C, 27)
    f_nat = afc.police(afc.BARLOW, 20)
    f_lieu = afc.police(afc.BARLOW_C, 21)
    f_p1 = afc.police(afc.ANTON, 30)
    f_p2 = afc.police(afc.BARLOW, 20)

    court = {c['id']: c['court'] for c in d['categories']}
    lieux = {k: v['court'] for k, v in d['lieux'].items()}

    # ---- titre ----------------------------------------------------------
    y = 74
    dr.rounded_rectangle([MARGE, y, MARGE + 7, y + 34], radius=3, fill=ORANGE_D)
    afc.texte(dr, (MARGE + 22, y + 3), u'LA MONTAGNE BASKET CLUB', f_sur, GLACIER, 3.2)
    y += 52
    dr.text((MARGE, y), u'CRÉNEAUX', font=f_t1, fill=BLANC)
    w = afc.larg(dr, u'CRÉNEAUX', f_t1)
    dr.text((MARGE + w + 18, y + 36), u'2026 / 2027', font=f_t2, fill=ORANGE_D)
    y += 96
    afc.texte(dr, (MARGE, y), u'GYMNASE DE LA MONTAGNE  ·  TERRAIN RUISSEAU BLANC',
              f_sur, GLACIER, 1.6)
    y += 46

    # ---- les journees ---------------------------------------------------
    par_jour = {}
    for c in d['creneaux']:
        par_jour.setdefault(c['jour'], []).append(c)

    for jour in JOURS:
        lot = sorted(par_jour.get(jour, []), key=lambda c: c['debut'])
        if not lot:
            continue
        dr.rounded_rectangle([MARGE, y + 6, MARGE + 5, y + 30], radius=2, fill=ORANGE_D)
        afc.texte(dr, (MARGE + 18, y), jour.upper(), f_jour, BLANC, 2.4)
        y += 44

        for c in lot:
            hh = 66
            dr.rounded_rectangle([MARGE, y, L - MARGE, y + hh], radius=14,
                                 fill=LIGNE_EXT)
            # l'heure, en orange, calee a gauche
            heure = u'%s — %s' % (hhmm(c['debut']), hhmm(c['fin']))
            dr.text((MARGE + 22, y + 12), heure, font=f_h, fill=ORANGE_D)
            xc = MARGE + 22 + afc.larg(dr, heure, f_h) + 28

            cats = u' · '.join(court[i] for i in c['categories'])
            dr.text((xc, y + 10), cats, font=f_cat, fill=BLANC)
            dr.text((xc, y + 39), NATURE.get(c.get('nature'), u'Entraînement'),
                    font=f_nat, fill=(126, 146, 170))

            # le lieu, pastille a droite
            lib = lieux[c['lieu']].upper()
            pad, ph, esp = 18, 34, 1.4
            lw = afc.larg(dr, lib, f_lieu, esp) + 2 * pad
            x1 = L - MARGE - 20
            x0 = x1 - lw
            cy = y + hh // 2
            plein = (c['lieu'] == 'gymnase')
            if plein:
                dr.rounded_rectangle([x0, cy - ph // 2, x1, cy + ph // 2],
                                     radius=ph // 2, fill=ENCRE)
                coul = BLANC
            else:
                dr.rounded_rectangle([x0, cy - ph // 2, x1, cy + ph // 2],
                                     radius=ph // 2, outline=(86, 108, 138), width=2)
                coul = GLACIER
            b = dr.textbbox((0, 0), lib, font=f_lieu)
            afc.texte(dr, (x0 + pad, cy - (b[3] + b[1]) / 2), lib, f_lieu, coul, esp)
            y += hh + 8
        y += 10

    # ---- pied -----------------------------------------------------------
    yp = H - 108
    dr.rounded_rectangle([MARGE, yp, MARGE + 7, yp + 44], radius=3, fill=ORANGE_D)
    g = u'%s € ' % d['tarif']
    dr.text((MARGE + 22, yp - 2), g, font=f_p1, fill=BLANC)
    dr.text((MARGE + 22 + afc.larg(dr, g, f_p1), yp - 2),
            u'LICENCE FFBB + ASSURANCE INCLUSES', font=f_p1, fill=ORANGE_D)
    dr.text((MARGE + 22, yp + 42), u'mbc974.com · @mbc974.re', font=f_p2,
            fill=(126, 146, 170))

    brut = io.BytesIO()
    im.save(brut, 'PNG', optimize=True)
    octets = brut.getvalue()
    nom = '%s-%s' % (base, hashlib.sha1(octets).hexdigest()[:8])
    io.open(nom + '.png', 'wb').write(octets)
    for w in (1080, 720, 480):
        r = im.resize((w, int(H * w / float(L))), Image.LANCZOS)
        suff = '' if w == 1080 else '-%d' % w
        r.save('%s%s.webp' % (nom, suff), 'WEBP', quality=82, method=6)
    return os.path.basename(nom)


def main():
    d = json.load(io.open(os.path.join(RACINE, 'data', 'creneaux.json'),
                          encoding='utf-8'))
    dossier = os.path.join(RACINE, 'assets', 'affiches')
    base = os.path.join(dossier, 'creneaux-2026-2027')
    for f in os.listdir(dossier):
        if f.startswith('creneaux-2026-2027'):
            os.remove(os.path.join(dossier, f))
    nom = produire(d, base)
    print(u"  affiche ecrite : assets/affiches/%s.png (+ 3 crans WebP)" % nom)
    print(u"  %d creneaux, %d jours" % (len(d['creneaux']),
                                        len({c['jour'] for c in d['creneaux']})))
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
