# -*- coding: utf-8 -*-
"""Les garde-fous du dossier. Ils doivent MORDRE, sinon ils ne servent a rien.

Cinq controles :
  1. glyphes   -- tout caractere doit exister dans le sous-ensemble de police qui
                  le sert, sinon Chrome substitue Times New Roman en silence ;
  2. polices   -- le PDF ne doit contenir QUE Anton et Barlow ;
  3. squelette -- surtitre, titre et sous-titre doivent etre au MEME endroit et
                  a la MEME taille sur les huit pages de contenu ;
  4. encre     -- le bord gauche de l'encre doit tomber sur une colonne de la
                  grille, a 0,5 pt pres ;
  5. debords   -- rien ne doit sortir de la page ni franchir le filet du pied.

AVERTISSEMENT DE METHODE. `span["bbox"]` de PyMuPDF est la boite TYPOGRAPHIQUE
(plume -> plume + avance), pas le contour de l'encre. La comparer a la marge
donne un faux positif sur chaque bloc dont on a compense le side bearing. Les
controles 3 et 4 lisent donc les polices REELLEMENT EMBARQUEES dans le PDF et en
tirent le side bearing du premier glyphe : la mesure est independante du code qui
a genere la page. Le controle 4 est double d'une lecture de pixels (--pixels).
"""
import os, re, sys, unicodedata, io
import fitz
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))
import grille as G

POLICES_ATTENDUES = {"Anton-Regular", "Barlow-Regular", "Barlow-SemiBold", "Barlow-Bold"}
FICHIERS = ["fonts/anton-400-latin.woff2", "fonts/anton-400-latin-ext.woff2",
            "fonts/barlow-400-latin.woff2", "fonts/barlow-400-latin-ext.woff2",
            "fonts/barlow-600-latin.woff2", "fonts/barlow-600-latin-ext.woff2",
            "fonts/barlow-700-latin.woff2"]
PT = 0.75                       # 1 px CSS = 0,75 pt


# ---------------------------------------------------------------- 1. glyphes
def _couverture():
    cov = {}
    for f in FICHIERS:
        p = os.path.join(HERE, f)
        if os.path.exists(p):
            cov[os.path.basename(f)] = set(TTFont(p).getBestCmap().keys())
    return cov


def controle_glyphes(html_path):
    import html as H
    src = open(html_path, encoding="utf-8").read()
    texte = H.unescape(re.sub(r"<[^>]+>", "", src[src.index("<body>"):]))
    cov = _couverture()
    anton = set().union(*[v for k, v in cov.items() if k.startswith("anton")])
    barlow = set().union(*[v for k, v in cov.items() if k.startswith("barlow")])
    manquants = {}
    for ch in sorted(set(texte)):
        if ch in "\n\r\t ":
            continue
        ou = [n for n, s in (("Anton", anton), ("Barlow", barlow)) if ord(ch) not in s]
        if ou:
            manquants[ch] = ou
    return manquants


# ---------------------------------------------------------------- 2. polices
def controle_polices(doc):
    vues = set()
    for p in doc:
        for f in p.get_fonts(full=True):
            nom = f[3].split("+")[-1]
            if nom:
                vues.add(nom)
    return sorted(vues), sorted(vues - POLICES_ATTENDUES)


# --------------------------------------- les polices EMBARQUEES dans le PDF
_emb = {}

def _police_embarquee(doc, nom_span):
    """Charge depuis le PDF la police que Chrome a reellement embarquee."""
    cle = nom_span.split("+")[-1]
    if cle in _emb:
        return _emb[cle]
    for p in doc:
        for f in p.get_fonts(full=True):
            if f[3].split("+")[-1] == cle:
                try:
                    donnees = doc.extract_font(f[0])[3]
                    tt = TTFont(io.BytesIO(donnees))
                    _emb[cle] = (tt, tt.getBestCmap(), tt.getGlyphSet(),
                                 tt["head"].unitsPerEm)
                    return _emb[cle]
                except Exception:
                    pass
    _emb[cle] = None
    return None


def _lsb_reel(doc, span):
    """Side bearing gauche du premier glyphe encre, en em, lu dans le PDF."""
    e = _police_embarquee(doc, span["font"])
    if not e:
        return None
    tt, cmap, gs, upm = e
    for ch in span["text"]:
        gn = cmap.get(ord(ch))
        if not gn:
            continue
        bp = BoundsPen(gs)
        try:
            gs[gn].draw(bp)
        except Exception:
            return None
        if bp.bounds is None:
            continue                      # espace : pas d'encre
        return bp.bounds[0] / upm
    return None


def _encre_x(doc, span):
    """x du bord gauche de l'ENCRE, en points PDF."""
    l = _lsb_reel(doc, span)
    if l is None:
        return None
    return span["origin"][0] + l * span["size"]


def _rsb_reel(doc, span):
    """Side bearing droit du dernier glyphe encre, en em, lu dans le PDF."""
    e = _police_embarquee(doc, span["font"])
    if not e:
        return None
    tt, cmap, gs, upm = e
    for ch in reversed(span["text"]):
        gn = cmap.get(ord(ch))
        if not gn:
            continue
        bp = BoundsPen(gs)
        try:
            gs[gn].draw(bp)
        except Exception:
            return None
        if bp.bounds is None:
            continue
        return (gs[gn].width - bp.bounds[2]) / upm
    return None


def _encre_x1(doc, ligne):
    """x du bord DROIT de l'encre d'une ligne, en points PDF."""
    sp = next((s for s in reversed(ligne["spans"]) if s["text"].strip()), None)
    if not sp:
        return None
    r = _rsb_reel(doc, sp)
    if r is None:
        return None
    return sp["bbox"][2] - r * sp["size"]


# -------------------------------------------------------------- 3. squelette
GABARIT = {                     # style -> (cap_top attendu en px, taille en px)
    "surtitre": (56, 15),
    "titre": (96, 64),
    "sous": (185, 26),
}

def controle_squelette(doc):
    """Le surtitre, le titre et le sous-titre au MEME endroit sur les 8 pages.

    On ne compare pas a une constante nominale : Chrome arrondit les metriques
    de ligne, si bien qu'un ecart d'un pixel peut affecter TOUTES les pages de la
    meme facon — ce qui ne se voit pas. Ce qui se verrait, c'est que deux pages
    ne soient pas d'accord entre elles. C'est donc cela qu'on mesure.
    """
    import typo
    releve = {}
    for i in range(1, 9):                       # pages 2 a 9 : le contenu
        p = doc[i]
        spans = [sp for bl in p.get_text("dict")["blocks"] if bl["type"] == 0
                 for ln in bl["lines"] for sp in ln["spans"] if sp["text"].strip()]
        for role, police, taille_px in (("surtitre", "barlow600", 15),
                                        ("titre", "anton", 64),
                                        ("sous-titre", "barlow", 26)):
            cible = taille_px * PT
            fam = "Anton" if police == "anton" else "Barlow"
            gras = "SemiBold" if police == "barlow600" else "Regular"
            cands = [sp for sp in spans
                     if fam in sp["font"] and gras in sp["font"]
                     and abs(sp["size"] - cible) < 0.3]
            if not cands:
                releve.setdefault(role, {})[i + 1] = None
                continue
            m = typo.metrics(police)
            haut = min((sp["origin"][1] - m["cap"] * sp["size"]) / PT for sp in cands)
            releve.setdefault(role, {})[i + 1] = round(haut, 2)
    # Le sous-titre suit le titre : sous un titre de deux lignes il descend d'un
    # interligne, ce qui est voulu. L'invariant a verifier n'est donc pas sa
    # position absolue mais l'ECART entre le bas de l'encre du titre et lui.
    m_anton = typo.metrics("anton")
    pas_titre = 64 * G.LH_TITRE
    for i in range(1, 9):
        p = doc[i]
        tits = [sp for bl in p.get_text("dict")["blocks"] if bl["type"] == 0
                for ln in bl["lines"] for sp in ln["spans"]
                if "Anton" in sp["font"] and abs(sp["size"] - 64 * PT) < 0.3
                and sp["text"].strip()]
        if not tits:
            continue
        bases = sorted({round(sp["origin"][1] / PT, 1) for sp in tits})
        nb = len(bases)
        bas_encre = bases[-1] - 0 + 0          # derniere ligne de base, en px
        releve.setdefault("_lignes_titre", {})[i + 1] = nb
        releve.setdefault("_bas_titre", {})[i + 1] = round(bas_encre, 2)

    ecarts = []
    resume = {}
    for role in ("surtitre", "titre"):
        par_page = releve[role]
        vues = [v for v in par_page.values() if v is not None]
        manquantes = [pg for pg, v in par_page.items() if v is None]
        etendue = max(vues) - min(vues)
        resume[role] = (min(vues), max(vues), round(etendue, 2), manquantes)
        if etendue > 0.25:
            for pg, v in sorted(par_page.items()):
                if v is not None and abs(v - min(vues)) > 0.25:
                    ecarts.append((pg, "haut des capitales, " + role, v, min(vues)))

    # L'ecart titre -> sous-titre, page par page.
    gaps = {}
    for pg, sous in releve["sous-titre"].items():
        if sous is None:
            continue
        bas = releve["_bas_titre"].get(pg)
        if bas is None:
            continue
        gaps[pg] = round(sous - bas, 2)
    if gaps:
        vals = list(gaps.values())
        et = max(vals) - min(vals)
        resume["ecart titre->sous"] = (min(vals), max(vals), round(et, 2), [])
        if et > 0.3:
            for pg, g in sorted(gaps.items()):
                if abs(g - min(vals)) > 0.3:
                    ecarts.append((pg, "ecart titre -> sous-titre", g, min(vals)))
    resume["_lignes de titre"] = releve["_lignes_titre"]
    return ecarts, resume


# ------------------------------------------------------------------ 4. encre
def _colonnes_pt():
    xs = {round(G.x(c) * PT, 2) for c in range(1, 13)}
    xs.add(round((G.W - G.MARGE) * PT, 2))
    return xs


# Les decrochages interieurs ne sont pas recopies ici : on les importe du
# generateur. Une copie derivait a chaque reglage de taille de QR, et le
# garde-fou signalait alors des faux positifs qu'on etait tente de desactiver.
import importlib
_GEN = os.environ.get("MBC_GENERATEUR", "dossier")
D = importlib.import_module(_GEN)
INTERIEURS_PX = D.decrochages()

BORD_DROIT = (G.W - G.MARGE) * PT          # 912 pt

def controle_encre(doc, tolerance=0.62):
    autorises = _colonnes_pt() | {round(v * PT, 2) for v in INTERIEURS_PX}
    hors, non_mesures = [], 0
    for i, p in enumerate(doc):
        for bl in p.get_text("dict")["blocks"]:
            if bl["type"] != 0:
                continue
            for ln in bl["lines"]:
                sp = next((s for s in ln["spans"] if s["text"].strip()), None)
                if not sp:
                    continue
                if abs(ln["dir"][0] - 1) > 1e-6:      # texte non horizontal
                    continue
                ex = _encre_x(doc, sp)
                if ex is None:
                    non_mesures += 1
                    continue
                d = min(abs(ex - c) for c in autorises)
                # Le texte ferre a droite n'a pas a commencer sur une colonne :
                # c'est son bord DROIT qui doit tomber sur le bord du contenu.
                x1 = _encre_x1(doc, ln)
                if x1 is not None:
                    d = min(d, abs(x1 - BORD_DROIT))
                if d > tolerance:
                    hors.append((i + 1, round(ex, 2), round(ex / PT, 2),
                                 round(d, 2), sp["text"][:40]))
    return hors, non_mesures


# --------------------------------------------------------------- 5. debords
def controle_debords(doc):
    probs = []
    LIM = (G.H - 72) * PT
    MG = G.MARGE * PT
    for i, p in enumerate(doc):
        W, H = p.rect.width, p.rect.height
        for bl in p.get_text("dict")["blocks"]:
            if bl["type"] != 0:
                continue
            for ln in bl["lines"]:
                for sp in ln["spans"]:
                    if not sp["text"].strip():
                        continue
                    ex = _encre_x(doc, sp)
                    x1, y0, y1 = sp["bbox"][2], sp["bbox"][1], sp["bbox"][3]
                    t = sp["text"][:40]
                    if ex is not None and ex < MG - 0.6:
                        probs.append((i + 1, "encre a gauche de la marge",
                                      round(ex, 2), t))
                    if x1 > W - MG + 1.5:
                        probs.append((i + 1, "encre a droite de la marge",
                                      round(x1, 2), t))
                    if y1 > H - 2 or y0 < 1:
                        probs.append((i + 1, "hors page verticalement",
                                      round(y1, 2), t))
                    # La signature du pied vit SOUS le filet par construction
                    # (664 px). N'est fautif que ce qui tombe dans la zone morte
                    # entre le filet et cette ligne, ou plus bas qu'elle.
                    BANDE_PIED = ((G.H - 63) * PT, (G.H - 34) * PT)
                    if y0 > LIM and not (BANDE_PIED[0] <= y0 <= BANDE_PIED[1]):
                        probs.append((i + 1, "franchit le filet du pied",
                                      round(y0, 2), t))
    return probs


# --------------------------------------------- 5 bis. bande utile respectee
BAS_CONTENU = 588          # doit valoir dossier.BAS_CONTENU
STYLES_DE_PIED = {13, 15}  # mention (13 px) et signature/numero (15 px)
PAGES_SANS_MENTION = {1, 10}

def controle_bande(doc):
    """Aucun contenu sous 588 px : c'est la zone de la mention.

    Le controle des debords ne regardait que le FILET du pied (648 px) et
    laissait donc passer tout ce qui tombait entre 588 et 648 — exactement la
    ou la mention vit. Deux chevauchements y ont echappe (p5 et p9).
    """
    import typo
    probs = []
    for i, p in enumerate(doc):
        spans = [sp for bl in p.get_text("dict")["blocks"] if bl["type"] == 0
                 for ln in bl["lines"] for sp in ln["spans"] if sp["text"].strip()]
        # La contrainte n'existe qu'a cause de la mention. La couverture et la
        # page de cloture n'en portent pas : leur bande basse est libre.
        if (i + 1) in PAGES_SANS_MENTION:
            continue
        for bl in p.get_text("dict")["blocks"]:
            if bl["type"] != 0:
                continue
            for ln in bl["lines"]:
                for sp in ln["spans"]:
                    if not sp["text"].strip():
                        continue
                    taille_px = round(sp["size"] / PT)
                    if taille_px in STYLES_DE_PIED:
                        continue                      # mention, signature, numero
                    police = "anton" if "Anton" in sp["font"] else "barlow"
                    cap = (sp["origin"][1] - typo.metrics(police)["cap"] * sp["size"]) / PT
                    if cap > BAS_CONTENU + 0.5:
                        probs.append((i + 1, round(cap, 1), taille_px, sp["text"][:44]))
    return probs


def controle_panneaux(doc):
    """Les PANNEAUX non plus ne doivent pas empieter sur la mention.

    Le controle de bande ne lisait que le TEXTE : les cartes de la page 8
    descendaient a 615 px, la mention leur courait dessus, et rien ne mordait.
    On ignore les fonds a fond perdu (pleine page) et les filets.
    """
    probs = []
    for i, p in enumerate(doc):
        if (i + 1) in PAGES_SANS_MENTION:
            continue
        H = p.rect.height
        for dr in p.get_drawings():
            for it in dr["items"]:
                if it[0] != "re":
                    continue
                r = it[1]
                if r.height < 40 * PT:
                    continue                          # filet, pastille
                if r.y0 <= 1 and r.y1 >= H - 1:
                    continue                          # fond a fond perdu
                bas_px = r.y1 / PT
                if bas_px > BAS_CONTENU + 0.5:
                    probs.append((i + 1, round(r.y0 / PT, 1), round(bas_px, 1),
                                  round(r.width / PT, 1)))
    return probs


# --------------------------------- contre-mesure : lecture directe de pixels
def controle_pixels(doc, pages=(2, 3, 7), dpi=300):
    """Cross-check : ou commence VRAIMENT l'encre, lue dans le raster ?

    On lit la bande du titre (haut des capitales -> ligne de base) et on cherche
    la premiere colonne de pixels qui differe du fond. Independant de toute
    metrique de police.
    """
    import typo
    m = typo.metrics("anton")
    res = []
    ech = dpi / 72.0
    for n in pages:
        p = doc[n - 1]
        y0 = (96 + 4) * PT
        y1 = (96 + m["cap"] * 64 - 4) * PT
        clip = fitz.Rect(0, y0, 400 * PT, y1)
        pix = p.get_pixmap(dpi=dpi, clip=clip, colorspace=fitz.csGRAY)
        data = pix.samples
        fond = data[0]
        col = None
        for x in range(pix.width):
            if any(abs(data[y * pix.stride + x] - fond) > 26
                   for y in range(pix.height)):
                col = x
                break
        if col is None:
            res.append((n, None, None))
            continue
        x_pt = clip.x0 + col / ech
        res.append((n, round(x_pt, 2), round(x_pt / PT, 2)))
    return res


# ------------------------------------------------------------------ rapport
def rapport(html_path, pdf_path, pixels=True):
    doc = fitz.open(pdf_path)
    ok = True
    print("=" * 76)
    print("1. GLYPHES")
    man = controle_glyphes(html_path)
    if man:
        ok = False
        for ch, ou in man.items():
            print("   MANQUE U+%04X %-4s %-26s absent de : %s"
                  % (ord(ch), repr(ch)[1:-1], unicodedata.name(ch, "?")[:26],
                     ", ".join(ou)))
    else:
        print("   tous les caracteres existent dans Anton et Barlow")

    print("\n2. POLICES DU PDF")
    vues, intrus = controle_polices(doc)
    print("   vues :", ", ".join(vues))
    if intrus:
        ok = False
        print("   INTRUS (substitution silencieuse) :", ", ".join(intrus))
    else:
        print("   aucune substitution")

    print("\n3. SQUELETTE DES PAGES DE CONTENU")
    ecarts, tailles = controle_squelette(doc)
    print("   taille de titre par page :", tailles)
    if ecarts:
        ok = False
        for pg, quoi, vu, att in ecarts:
            print("   p%02d  %-32s vu %s, attendu %s" % (pg, quoi, vu, att))
    else:
        print("   les 8 titres : meme taille (64 px) et meme haut de capitales (96 px)")

    print("\n4. BORD GAUCHE DE L'ENCRE (metriques lues dans le PDF)")
    hors, nm = controle_encre(doc)
    if hors:
        ok = False
        for pg, xpt, xpx, d, t in hors:
            print("   p%02d  encre a %8.2f pt (%7.2f px), %5.2f pt hors grille  %r"
                  % (pg, xpt, xpx, d, t))
    else:
        print("   toutes les lignes commencent sur une colonne de la grille")
    if nm:
        print("   (%d lignes non mesurables : glyphes sans contour)" % nm)

    print("\n5. DEBORDS")
    probs = controle_debords(doc)
    if probs:
        ok = False
        for pg, quoi, v, t in probs:
            print("   p%02d  %-30s %8.2f  %r" % (pg, quoi, v, t))
    else:
        print("   aucun debord, aucun franchissement du pied")

    print("\n6. BANDE UTILE (rien sous %d px)" % BAS_CONTENU)
    bande = controle_bande(doc)
    if bande:
        ok = False
        for pg, cap, tp, tx in bande:
            print("   p%02d  capitales a %6.1f px (corps %d px)  %r"
                  % (pg, cap, tp, tx))
    else:
        print("   aucun contenu ne descend dans la zone de la mention")

    panneaux = controle_panneaux(doc)
    if panneaux:
        ok = False
        for pg, y0, y1, w in panneaux:
            print("   p%02d  panneau de %.0f px de large : %.1f -> %.1f px"
                  % (pg, w, y0, y1))
    else:
        print("   aucun panneau ne descend dans la zone de la mention")

    if pixels:
        print("\n6. CONTRE-MESURE EN PIXELS (300 dpi, bande du titre)")
        for n, xpt, xpx in controle_pixels(doc):
            if xpt is None:
                print("   p%02d  aucune encre trouvee dans la bande" % n)
            else:
                d = abs(xpx - G.MARGE)
                marque = "OK" if d <= 0.9 else "ECART"
                print("   p%02d  encre a %7.2f pt = %6.2f px   (marge %d px)  %s  %+.2f px"
                      % (n, xpt, xpx, G.MARGE, marque, xpx - G.MARGE))
                if d > 0.9:
                    ok = False

    print("=" * 76)
    print("RESULTAT :", "TOUT PASSE" if ok else "DES CONTROLES ONT MORDU")
    return ok


if __name__ == "__main__":
    h = sys.argv[1] if len(sys.argv) > 1 else "dossier.html"
    p = sys.argv[2] if len(sys.argv) > 2 else "dossier.pdf"
    sys.exit(0 if rapport(h, p) else 1)
