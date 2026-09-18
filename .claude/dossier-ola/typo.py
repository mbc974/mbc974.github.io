# -*- coding: utf-8 -*-
"""Metriques reelles des polices du site, pour un alignement optique prouve.

Le defaut le plus visible du dossier d'origine etait un bord gauche en escalier :
l'encre d'Impact commencait 3 pt A GAUCHE de la marge, celle d'Arial 0,75 a 4,5 pt
A DROITE. Six bords gauches differents sur la meme page. On ne le corrige pas a
l'oeil : on annule, pour chaque chaine, le side bearing REEL de son premier glyphe.
"""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {
    "anton": "fonts/anton-400-latin.woff2",
    "anton-ext": "fonts/anton-400-latin-ext.woff2",
    "barlow": "fonts/barlow-400-latin.woff2",
    "barlow600": "fonts/barlow-600-latin.woff2",
    "barlow700": "fonts/barlow-700-latin.woff2",
}
_cache = {}

def _load(key):
    if key not in _cache:
        f = TTFont(os.path.join(HERE, FONTS[key]))
        _cache[key] = (f, f.getBestCmap(), f.getGlyphSet(), f["head"].unitsPerEm)
    return _cache[key]

def glyph_box(key, ch):
    """(x0, y0, x1, y1, advance) en em, ou None si le glyphe manque."""
    for k in ([key, "anton-ext"] if key == "anton" else [key]):
        f, cmap, gs, upm = _load(k)
        gn = cmap.get(ord(ch))
        if not gn:
            continue
        bp = BoundsPen(gs)
        gs[gn].draw(bp)
        adv = gs[gn].width / upm
        if bp.bounds is None:          # espace : pas d'encre
            return (0.0, 0.0, 0.0, 0.0, adv)
        x0, y0, x1, y1 = bp.bounds
        return (x0 / upm, y0 / upm, x1 / upm, y1 / upm, adv)
    return None

def lsb(key, text):
    """Side bearing gauche du PREMIER glyphe encre, en em."""
    for ch in text:
        b = glyph_box(key, ch)
        if b and (b[2] - b[0]) > 0:
            return b[0]
    return 0.0

def rsb(key, text):
    """Side bearing droit du DERNIER glyphe encre, en em (positif = creux)."""
    for ch in reversed(text):
        b = glyph_box(key, ch)
        if b and (b[2] - b[0]) > 0:
            return b[4] - b[2]
    return 0.0

def ink_top(key, text):
    """Hauteur d'encre max au-dessus de la ligne de base, en em."""
    tops = [glyph_box(key, c)[3] for c in text if glyph_box(key, c)]
    return max(tops) if tops else 0.0

def ink_bottom(key, text):
    """Encre min sous la ligne de base, en em (negatif = descend)."""
    bots = [glyph_box(key, c)[1] for c in text if glyph_box(key, c)]
    return min(bots) if bots else 0.0

def metrics(key):
    f, _, _, upm = _load(key)
    o = f["OS/2"]; h = f["hhea"]
    return dict(upm=upm, cap=o.sCapHeight / upm, x=o.sxHeight / upm,
                asc=h.ascent / upm, desc=h.descent / upm,
                normal_lh=(h.ascent - h.descent + h.lineGap) / upm)

def indent_css(key, text):
    """text-indent qui pose l'encre EXACTEMENT sur la marge."""
    v = -lsb(key, text)
    return f"{v:.5f}em" if abs(v) > 1e-6 else "0"

if __name__ == "__main__":
    for k in ("anton", "barlow", "barlow600"):
        m = metrics(k)
        print(f"{k:10s} cap={m['cap']:.4f} x={m['x']:.4f} asc={m['asc']:.4f} "
              f"desc={m['desc']:.4f} lh_normal={m['normal_lh']:.4f}")
    print()
    print("Encre des capitales accentuees (Anton) :")
    for t in ("PRENEZ", "ÇA", "ÉTÉ", "DÉJÀ", "COMMUN", "100", "LA MONTAGNE,"):
        print(f"  {t:14s} lsb={lsb('anton',t):+.5f} rsb={rsb('anton',t):+.5f} "
              f"top={ink_top('anton',t):.4f} bottom={ink_bottom('anton',t):+.4f}")
    print()
    print("Interligne mini sans collision (Anton, capitales accentuees) :")
    print(f"  accent au-dessus d'une capitale nue : {ink_top('anton','É'):.4f} em")
    print(f"  accent sous une cedille Ç           : "
          f"{ink_top('anton','É') - ink_bottom('anton','Ç'):.4f} em")
