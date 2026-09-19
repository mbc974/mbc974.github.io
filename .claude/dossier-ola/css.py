# -*- coding: utf-8 -*-
"""La feuille de style du dossier, generee depuis grille.py et typo.py."""
import grille as G

# --- La palette ------------------------------------------------------------
# Les trois teintes de marque sont celles du site (style.css, bloc :root) et du
# logo, verifiees au pixel : bleu roi #11529A/#0F53A2 dans le logo, orange
# #D36725. Le dossier d'origine employait #1747D1 (un bleu violace generique),
# #FF852B et #08182F : aucune des trois n'etait la couleur du club.
PAL = {
    "nuit":        "#0D1526",   # --bleu-nuit
    "nuit-2":      "#101B30",   # --nuit-2
    "nuit-3":      "#15233D",   # --nuit-3
    "roi":         "#1B519E",   # --bleu-roi  (la couleur du logo)
    "roi-clair":   "#2E6FC4",
    "roi-sombre":  "#123A73",
    "orange":      "#E8822A",   # --orange-vif
    "orange-f":    "#D96A1B",   # --orange-ballon
    "glacier":     "#BFD2E4",   # --bleu-glacier
    "ardoise":     "#2A3B4D",   # --ardoise
    "papier":      "#F6F3EC",
    "papier-2":    "#ECE7DC",
    "papier-3":    "#E0D9CB",
    "encre":       "#0D1526",
    "encre-douce": "#5A6A7C",
    "blanc":       "#FFFFFF",
}

def _face(fam, fichier, poids):
    return (f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{poids};"
            f"font-display:block;src:url(fonts/{fichier}) format('woff2')}}")

def feuille():
    out = []
    a = out.append

    # --- Polices : celles du site, servies depuis le depot -----------------
    a(_face("Anton", "anton-400-latin.woff2", 400))
    a("@font-face{font-family:'Anton';font-style:normal;font-weight:400;"
      "font-display:block;src:url(fonts/anton-400-latin-ext.woff2) format('woff2');"
      "unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,"
      "U+1E00-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}")
    a(_face("Barlow", "barlow-400-latin.woff2", 400))
    a("@font-face{font-family:'Barlow';font-style:normal;font-weight:400;"
      "font-display:block;src:url(fonts/barlow-400-latin-ext.woff2) format('woff2');"
      "unicode-range:U+0100-02BA,U+1E00-1EFF,U+20A0-20AB,U+2113,U+2C60-2C7F}")
    a(_face("Barlow", "barlow-600-latin.woff2", 600))
    a("@font-face{font-family:'Barlow';font-style:normal;font-weight:600;"
      "font-display:block;src:url(fonts/barlow-600-latin-ext.woff2) format('woff2');"
      "unicode-range:U+0100-02BA,U+1E00-1EFF,U+20A0-20AB,U+2113,U+2C60-2C7F}")
    a(_face("Barlow", "barlow-700-latin.woff2", 700))

    # --- Variables --------------------------------------------------------
    a(":root{" + "".join(f"--{k}:{v};" for k, v in PAL.items()) + "}")

    # --- La page ----------------------------------------------------------
    a(f"@page{{size:{G.W/96:.4f}in {G.H/96:.4f}in;margin:0}}")
    a("*{margin:0;padding:0;box-sizing:border-box}")
    a("html{-webkit-text-size-adjust:none}")
    a(f"body{{width:{G.W}px;background:#fff;"
      "-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}")
    a(f".p{{position:relative;width:{G.W}px;height:{G.H}px;overflow:hidden;"
      "page-break-after:always;break-after:page;"
      "-webkit-print-color-adjust:exact;print-color-adjust:exact}")
    a(".p:last-child{page-break-after:auto;break-after:auto}")

    # --- Fonds ------------------------------------------------------------
    a(".f-nuit{background:var(--nuit);color:var(--blanc)}")
    a(".f-roi{background:var(--roi);color:var(--blanc)}")
    a(".f-papier{background:var(--papier);color:var(--encre)}")

    # --- Les styles de texte, calcules ------------------------------------
    for nom in G.STYLES:
        police, taille, lh, ls = G.STYLES[nom]
        fam = "Anton" if police == "anton" else "Barlow"
        poids = {"anton": 400, "barlow": 400, "barlow600": 600, "barlow700": 700}[police]
        maj = "text-transform:uppercase;" if police == "anton" else ""
        a(f".t-{nom}{{font-family:'{fam}';font-weight:{poids};font-size:{taille}px;"
          f"line-height:{lh};letter-spacing:{ls};{maj}}}")

    # --- Blocs positionnes -------------------------------------------------
    a(".b{position:absolute}")
    # Un bloc pose par son encre : --cap est le decalage boite->haut des capitales.
    a(".cap{margin-top:calc(-1 * var(--cap))}")

    # --- Couleurs de texte -------------------------------------------------
    a(".c-blanc{color:var(--blanc)}.c-encre{color:var(--encre)}")
    a(".c-orange{color:var(--orange)}.c-glacier{color:var(--glacier)}")
    a(".c-douce{color:var(--encre-douce)}.c-roi{color:var(--roi)}")
    a(".c-roi-clair{color:var(--roi-clair)}")
    # Sur fond bleu roi, le glacier pur manque de corps : on l'eclaircit.
    a(".f-roi .c-glacier{color:#D8E4F2}")

    # --- Filets ------------------------------------------------------------
    a(".r{position:absolute;height:1px;border:0}")
    a(".r-clair{background:rgba(13,21,38,.16)}")
    a(".r-sombre{background:rgba(191,210,228,.22)}")
    a(".r-roi{background:rgba(255,255,255,.28)}")
    a(".r-orange{background:var(--orange)}")

    # --- Images ------------------------------------------------------------
    a(".im{position:absolute;display:block;object-fit:cover}")
    a(".qr{position:absolute;display:block}")

    # --- Liens -------------------------------------------------------------
    # Chrome headless emet une ANNOTATION DE LIEN par <a href> dans le PDF :
    # une adresse imprimee devient cliquable sans rien changer a son allure.
    # Encore faut-il neutraliser le style par defaut du navigateur, sinon le
    # texte vire au bleu souligne au milieu d'une page bleu nuit.
    # `.zn` est une zone cliquable transparente : posee sur une plaque de QR,
    # elle rend le QR lui-meme cliquable a l'ecran, et le QR reste scannable
    # sur le papier. Mesure faite : 5 liens sur 5 survivent au rendu, y compris
    # mailto:, tel: et une zone vide.
    a("a{color:inherit;text-decoration:none}")
    a(".zn{position:absolute;display:block}")

    # --- Pied de page, identique sur toutes les pages ----------------------
    a(".pied{position:absolute;left:%dpx;width:%dpx;bottom:%dpx;"
      "display:flex;align-items:baseline;justify-content:space-between}"
      % (G.MARGE, G.CONTENU, G.BAS - 14))
    return "\n".join(out)
