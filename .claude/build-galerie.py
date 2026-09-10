# -*- coding: utf-8 -*-
"""Prepare les images de la galerie pour le zoom parallaxe.

    python .claude/build-galerie.py --essai
    python .claude/build-galerie.py

LE PROBLEME QU'IL REGLE
------------------------
Les tuiles de la galerie declaraient le `sizes` de la MOSAIQUE — 24vw, 33vw,
48vw. Or le zoom les met a l'echelle : la largeur affichee d'une tuile vaut
`--gw x --gs`, soit jusqu'a 175 vw. Le navigateur choisissait donc un derive
calibre pour 412 px et l'etirait jusqu'a 2 146. Mesure faite dans le
navigateur, a 1717 px de large :

    tuile        source choisie   natif   affiche max   etirement
    g-team       2600.avif         2230        1717        x0,77
    g-banner     1000.webp          824        3005        x3,65
    g-tall        420.webp          412        2060        x5,00
    g-shoot       420.webp          412        2146        x5,21
    g-inaug       760.webp          566        2060        x3,64

CE QUI COMPTE VRAIMENT, ET QUI NUANCE LE DIAGNOSTIC
-----------------------------------------------------
L'etirement maximal n'est pas ce que l'oeil voit : les tuiles peripheriques
sortent du cadre en grandissant. Mesure de la couverture d'ecran a chaque
etat :

    p=0     toutes visibles, x0,2 a x1,0   -> nettes
    p=0,25  10 a 14 % d'ecran, x1,5 a x2,5 -> C'EST LA que le flou se voit
    p=0,50  3 a 4 % d'ecran seulement
    p=0,75  seule la tuile centrale reste
    p=1     la centrale occupe tout, a x0,8 -> nette

La tuile qui finit plein cadre n'a donc JAMAIS ete floue. Le defaut portait
sur les cinq autres, entre p=0,2 et p=0,5, la ou elles couvrent encore un
dixieme de l'ecran.

CE QUE CE SCRIPT FAIT
---------------------
1. Genere les derives AVIF manquants. Quatre tuiles sur six n'avaient que du
   WebP. L'AVIF pese ici 32 % de moins a qualite egale : c'est lui qui paie le
   passage aux crans superieurs.
2. Reecrit les `sizes` pour que le navigateur choisisse le PLUS GRAND derive
   disponible sur desktop, ou le zoom se joue, en laissant le mobile sur ses
   petits crans.

CE QU'IL NE PEUT PAS FAIRE
--------------------------
Inventer des pixels. Les fichiers de base font 900x978, 900x1000, 1400x745 et
760x951 : meme en choisissant le meilleur derive, il reste un etirement
residuel a fort grossissement. Le seul vrai remede serait des originaux plus
definis — c'est signale, pas maquille (aucun sharpening CSS).
"""
import io
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GALERIE = os.path.join(RACINE, 'assets', 'galerie')

# Le `sizes` a poser, par tuile. La valeur desktop est calculee pour tomber
# au-dessus du plus grand cran disponible ; la valeur mobile reste celle de la
# mosaique, car un telephone de 390 px n'atteint jamais ces largeurs.
SIZES = {
    'g-banner': u'(min-width:980px) 88vw, 94vw',   # 1511px a 1717 -> cran 1400
    'g-tall':   u'(min-width:980px) 56vw, 47vw',   #  961px        -> cran  900
    'g-shoot':  u'(min-width:980px) 56vw, 47vw',   #  961px        -> cran  900
    'g-inaug':  u'(min-width:980px) 48vw, 50vw',   #  824px        -> cran  760
}


def avif_manquants(essai):
    """Un AVIF pour chaque WebP de la galerie qui n'en a pas.

    On repart du .jpg d'origine, jamais du WebP : reencoder un fichier deja
    compresse empile deux pertes pour rien."""
    faits, absents = [], []
    for f in sorted(os.listdir(GALERIE)):
        m = re.match(r'^(.+)-(\d+)\.webp$', f)
        if not m:
            continue
        base, w = m.group(1), int(m.group(2))
        cible = os.path.join(GALERIE, '%s-%d.avif' % (base, w))
        if os.path.exists(cible):
            continue
        src = os.path.join(GALERIE, base + '.jpg')
        if not os.path.exists(src):
            absents.append(base)
            continue
        if not essai:
            from PIL import Image
            im = Image.open(src).convert('RGB')
            h = max(1, round(im.height * w / im.width))
            im.resize((w, h), Image.LANCZOS).save(cible, 'AVIF', quality=62)
        faits.append((os.path.basename(cible), w))
    return faits, sorted(set(absents))


def poser_sources_avif(html):
    """Ajoute un <source type="image/avif"> devant le WebP, la ou il manque."""
    n = 0

    def sur_figure(m):
        nonlocal n
        bloc = m.group(0)
        if 'image/avif' in bloc:
            return bloc
        sw = re.search(r'<source([^>]*type="image/webp"[^>]*)>', bloc)
        if not sw:
            return bloc
        avif = sw.group(0).replace('image/webp', 'image/avif').replace('.webp', '.avif')
        # on ne declare l'AVIF que si TOUS ses fichiers existent
        for u in re.findall(r'(assets/galerie/[\w./-]+)\s+\d+w', avif):
            if not os.path.exists(os.path.join(RACINE, u)):
                return bloc
        n += 1
        return bloc.replace(sw.group(0), avif + sw.group(0), 1)

    html = re.sub(r'<figure class=.g-tile[^"]*..*?</figure>', sur_figure, html, flags=re.S)
    return html, n


def poser_sizes(html):
    n = 0

    def sur_figure(m):
        nonlocal n
        bloc, cls = m.group(0), m.group(1)
        for k, v in SIZES.items():
            if k in cls:
                neuf, c = re.subn(r'sizes="[^"]*"', 'sizes="%s"' % v, bloc)
                n += c
                return neuf
        return bloc

    html = re.sub(r'<figure class=.g-tile([^"]*)..*?</figure>', sur_figure, html, flags=re.S)
    return html, n


def main():
    essai = '--essai' in sys.argv
    faits, absents = avif_manquants(essai)
    print(u"  %d derive(s) AVIF %s" % (len(faits), u"a generer" if essai else u"generes"))
    if absents:
        print(u"  %d image(s) sans .jpg d'origine, laissees en WebP seul : %s"
              % (len(absents), ", ".join(absents[:4])))

    p = os.path.join(RACINE, 'index.html')
    html = io.open(p, encoding='utf-8').read()
    html, na = poser_sources_avif(html)
    html, ns = poser_sizes(html)
    print(u"  %d tuile(s) recoivent une source AVIF" % na)
    print(u"  %d attribut(s) sizes reecrit(s) pour le zoom" % ns)
    if essai:
        print(u"\n  (essai : rien n'a ete ecrit)")
        return 0
    io.open(p, 'w', encoding='utf-8', newline='\n').write(html)
    print(u"\n  index.html reecrit — lancer bump-assets.py")
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
