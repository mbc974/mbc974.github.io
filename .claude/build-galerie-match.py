# -*- coding: utf-8 -*-
"""Les soirees photo de la galerie « Sur le terrain », depuis data/galerie-match.json.

    python .claude/build-galerie-match.py --images "C:/Users/ALEX/Downloads"
    python .claude/build-galerie-match.py            reecrit le bloc de l'accueil
    python .claude/build-galerie-match.py --essai    montre le bilan, n'ecrit rien
    python .claude/build-galerie-match.py --check    sort en 1 si l'accueil n'est
                                                     plus a jour du JSON

CE QUE CA PRODUIT
-----------------
Un bloc par soiree, dans index.html entre les marqueurs « galerie:soirees »,
AU-DESSUS du zoom parallaxe de #galerie. Pas dans le zoom : ses six tuiles ont
chacune une place calculee (style.css, bloc « GALERIE — zoom parallaxe ») et la
scene collee atterrit plein cadre sur « Le cercle d'avant-seance », qui ouvre
sur #parents. Pas dessous non plus : ce passage-la ne doit rien avoir entre les
deux.

Le titre de la soiree vient du JSON ; la date, l'adversaire, le score et le lieu
viennent de data/matchs.json, par le slug de la rencontre. Rien n'est ressaisi :
un score corrige la-bas se corrige ici au prochain passage de build-matchs.py
(et donc de set-calendrier-prm.py), qui appelle regenerer().

LES RANGEES
-----------
Sur ordinateur, les photos sont posees en rangees JUSTIFIEES (style.css, bloc
« GALERIE — les soirees photo ») : chacune y prend une largeur proportionnelle a
son rapport largeur/hauteur, toutes ont donc la meme hauteur, et aucune n'est
recadree. Le script choisit les coupures : autant de rangees que la somme des
rapports divisee par CIBLE_RANGEE, aux endroits qui equilibrent le mieux ces
sommes. L'ordre reste celui du JSON : la soiree se lit dans l'ordre ou elle
s'est jouee.

LES IMAGES (--images)
---------------------
Pour chaque derive manquant : l'original est redresse d'apres son EXIF, vide de
TOUTES ses metadonnees (numero de serie du boitier, reglages, eventuel GPS),
puis decline en AVIF et en WebP aux crans CRANS_PORTRAIT ou CRANS_PAYSAGE, plus
un JPEG au plus grand cran, repli du <img> et de la visionneuse. Un fichier
existant n'est jamais reecrit : une photo changee doit changer de nom, sinon le
service worker continue de servir l'ancienne (MAINTENANCE, regle du cache).

Deux alertes, parce qu'aucun autre controle ne regarde les images :
  - un original sans date de prise de vue n'est probablement pas sorti d'un
    appareil. Le 15/09/2026, un PNG de 1024 x 1536 sans EXIF s'etait glisse
    dans le lot, avec une inscription de maillot devenue illisible : une image
    retouchee par une IA, ecartee au titre de MAINTENANCE § 17.4 ;
  - une photo prise un autre jour que la rencontre.
"""
import io
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "bm", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build-matchs.py"))
bm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bm)

ech = bm.ech
SOURCE = "data/galerie-match.json"
DOSSIER = "assets/galerie"
BALISE = "galerie:soirees"

# Les crans. Portrait : une photo fait ~180 px de large dans une rangee
# d'ordinateur, ~190 px dans la bande d'un telephone — 560 couvre le x3. Le
# 1200 sert la visionneuse. Paysage : jusqu'a toute la largeur d'un telephone,
# d'ou le 1200, et le 1800 pour la visionneuse sur grand ecran.
CRANS_PORTRAIT = (360, 560, 760, 1200)
CRANS_PAYSAGE = (560, 760, 1200, 1800)
QUALITE = {"avif": {"quality": 45}, "webp": {"quality": 66, "method": 6}}
QUALITE_JPEG = 80

# Somme des rapports largeur/hauteur visee par rangee. A 1124 px de contenu,
# 4 donne des photos d'environ 270 px de haut : deux rangees pour dix photos.
CIBLE_RANGEE = 4.0

# La geometrie de style.css, pour ecrire des « sizes » justes. A changer
# ENSEMBLE si la feuille change.
CONTENU_MAX = 1124   # px de contenu quand .wrap est a son plafond (1220 - 2 x 48)
ECART = 11           # .7rem entre deux photos d'une rangee
BANDE_VW, BANDE_PX = 70, 420   # hauteur de la bande sous 880 px : min(70vw, 420px)
BANDE_MAX_VW = 90              # un paysage y est borne a la largeur de l'ecran


def charger():
    return json.loads(bm.lire(SOURCE))


def rencontre(slug, matchs):
    for m in matchs["matchs"]:
        if m["slug"] == slug:
            return m
    raise SystemExit(u"!! %s : « %s » n'est pas une rencontre de data/matchs.json"
                     % (SOURCE, slug))


def verifier(d):
    """Refuse d'ecrire sur une donnee incomplete : mieux vaut une sortie en
    erreur qu'un alt vide ou deux photos publiees sous le meme nom."""
    vus = set()
    for s in d["soirees"]:
        if not s.get("titre") or not s.get("photos"):
            raise SystemExit(u"!! %s : soiree %s sans titre ou sans photos"
                             % (SOURCE, s.get("match")))
        for p in s["photos"]:
            for champ in ("source", "fichier", "alt"):
                if not (p.get(champ) or "").strip():
                    raise SystemExit(u"!! %s : photo %s sans « %s »"
                                     % (SOURCE, p.get("source"), champ))
            if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", p["fichier"]):
                raise SystemExit(u"!! %s : nom refuse « %s » (minuscules, chiffres, tirets)"
                                 % (SOURCE, p["fichier"]))
            if p["fichier"] in vus:
                raise SystemExit(u"!! %s : « %s » sert deux fois" % (SOURCE, p["fichier"]))
            vus.add(p["fichier"])


# --------------------------------------------------------------------------
# Les images
# --------------------------------------------------------------------------
def deriver(p, dossier, jour, essai):
    """Cree les derives manquants d'une photo ; rend (fichiers, alertes)."""
    from PIL import Image, ImageOps
    chemin = os.path.join(dossier, p["source"])
    if not os.path.exists(chemin):
        # Deja publiee (un JPEG et au moins une paire AVIF/WebP) : son original
        # n'est plus requis. Sans cela, ajouter une soiree obligeait a garder
        # sous la main les originaux de toutes les precedentes.
        try:
            sur_disque(p)
            return [], []
        except SystemExit:
            raise SystemExit(u"!! original introuvable : %s" % chemin)
    alertes = []
    with Image.open(chemin) as im0:
        prise = im0.getexif().get_ifd(0x8769).get(36867)   # DateTimeOriginal
        im = ImageOps.exif_transpose(im0).convert("RGB")
    # convert() et resize() recopient info : sans ce vidage, l'EXIF complet de
    # l'original partirait dans chaque derive. Les originaux sont en sRGB, le
    # profil peut partir aussi (c'est la valeur par defaut des navigateurs).
    im.info.clear()
    if not prise:
        alertes.append(u"%s : aucune date de prise de vue. Une photo sortie d'un appareil "
                       u"en porte une : verifier qu'elle n'est ni generee ni retouchee par "
                       u"une IA (MAINTENANCE § 17.4)" % p["source"])
    elif prise[:10].replace(":", "-") != jour:
        alertes.append(u"%s : prise le %s, la rencontre est le %s"
                       % (p["source"], prise[:10].replace(":", "-"), jour))
    crans = [w for w in (CRANS_PORTRAIT if im.width < im.height else CRANS_PAYSAGE)
             if w <= im.width]
    if not crans:
        raise SystemExit(u"!! %s : %d px de large, trop petite pour la galerie"
                         % (p["source"], im.width))
    base = os.path.join(bm.RACINE, DOSSIER, p["fichier"])
    faits = []
    for w in crans:
        reduite = None
        for ext in ("avif", "webp"):
            cible = "%s-%d.%s" % (base, w, ext)
            if os.path.exists(cible):
                continue
            faits.append(cible)
            if essai:
                continue
            if reduite is None:
                reduite = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            reduite.save(cible, ext.upper(), **QUALITE[ext])
    cible = base + ".jpg"
    if not os.path.exists(cible):
        faits.append(cible)
        if not essai:
            w = crans[-1]
            im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(
                cible, "JPEG", quality=QUALITE_JPEG, optimize=True, progressive=True)
    return faits, alertes


def sur_disque(p):
    """Les crans publies (AVIF ET WebP presents) et les dimensions du JPEG."""
    dossier = os.path.join(bm.RACINE, DOSSIER)
    motif = re.compile(re.escape(p["fichier"]) + r"-(\d+)\.avif$")
    crans = sorted(int(m.group(1)) for m in map(motif.match, os.listdir(dossier))
                   if m and os.path.exists(os.path.join(
                       dossier, "%s-%s.webp" % (p["fichier"], m.group(1)))))
    dims = bm.dimensions(os.path.join(dossier, p["fichier"] + ".jpg"))
    if not crans or not dims:
        raise SystemExit(u"!! %s : derives absents de %s — relancer avec "
                         u"--images <dossier des originaux>" % (p["fichier"], DOSSIER))
    return crans, dims[0], dims[1]


# --------------------------------------------------------------------------
# Le bloc
# --------------------------------------------------------------------------
def rangees(rapports):
    """Coupe la suite, sans la reordonner, en rangees de sommes equilibrees
    (moindres carres sur l'ecart a la moyenne)."""
    n = len(rapports)
    k = max(1, min(n, int(round(sum(rapports) / CIBLE_RANGEE))))
    moyenne = sum(rapports) / k
    cumul = [0.0]
    for r in rapports:
        cumul.append(cumul[-1] + r)
    inf = float("inf")
    cout = [[inf] * (n + 1) for _ in range(k + 1)]
    coupe = [[0] * (n + 1) for _ in range(k + 1)]
    cout[0][0] = 0.0
    for j in range(1, k + 1):
        for i in range(j, n + 1):
            for a in range(j - 1, i):
                c = cout[j - 1][a] + (cumul[i] - cumul[a] - moyenne) ** 2
                if c < cout[j][i]:
                    cout[j][i], coupe[j][i] = c, a
    bornes, i = [], n
    for j in range(k, 0, -1):
        bornes.append((coupe[j][i], i))
        i = coupe[j][i]
    return [list(range(a, b)) for a, b in reversed(bornes)]


def sizes(r, somme, nb):
    """La largeur affichee, telle que style.css la pose, du plus large au plus
    etroit : rangee au plafond de .wrap, rangee fluide, bande a 420 px de haut,
    bande a 70vw de haut."""
    part = r / somme
    return u"(min-width:1220px) %dpx, (min-width:880px) %gvw, (min-width:600px) %dpx, %gvw" % (
        round(part * (CONTENU_MAX - (nb - 1) * ECART)), round(part * 90, 1),
        round(min(r * BANDE_PX, BANDE_PX * 1.5)), min(round(r * BANDE_VW, 1), BANDE_MAX_VW))


def bouton(p, groupe, r, somme, nb):
    crans, lg, ht = sur_disque(p)
    url = "/%s/%s" % (DOSSIER, p["fichier"])
    sz = sizes(r, somme, nb)

    def srcset(ext):
        return ", ".join("%s-%d.%s %dw" % (url, w, ext, w) for w in crans)
    # Un BOUTON : l'action est d'agrandir, pas d'aller ailleurs. Son nom
    # accessible est « Agrandir la photo : » suivi de l'alt de l'image. La
    # visionneuse relit cet alt elle-meme : pas de data-lightbox-alt en double.
    return (u'<button type="button" class="gmatch__ph" style="--r:%(r).4f" '
            u'data-lightbox-src="%(grand)s" data-lightbox-fallback="%(jpg)s" '
            u'data-lightbox-group="%(g)s" data-lightbox-label="Photo agrandie">'
            u'<span class="sr-only">Agrandir la photo&nbsp;: </span><picture>'
            u'<source type="image/avif" sizes="%(sz)s" srcset="%(a)s">'
            u'<source type="image/webp" sizes="%(sz)s" srcset="%(w)s">'
            u'<img src="%(jpg)s" width="%(lg)d" height="%(ht)d" loading="lazy" '
            u'decoding="async" alt="%(alt)s"></picture></button>') % {
        "r": r, "grand": "%s-%d.webp" % (url, crans[-1]), "jpg": url + ".jpg",
        "g": groupe, "sz": sz, "a": srcset("avif"), "w": srcset("webp"),
        "lg": lg, "ht": ht, "alt": ech(p["alt"].strip())}


def legende(m, matchs):
    """« Victoire du MBC, 73 à 52 contre Sainte-Suzanne, au Gymnase de La
    Montagne » — meme ordre des chiffres que les fiches : apres « victoire du
    MBC », les points du MBC d'abord."""
    adv = m.get("adversaireCourt") or m["adversaire"]
    sc = bm.score_texte(m) if m.get("statut") == "joue" else None
    if sc:
        cls, mot = bm.issue(*sc)
        debut = ((u"Match nul, %d à %d contre %s" if cls == "n"
                  else mot + u" du MBC, %d à %d contre %s") % (sc[0], sc[1], adv))
    else:
        debut = u"Contre %s" % adv
    lieu = (matchs.get("lieux") or {}).get(m.get("lieu") or "")
    if lieu:
        debut += (u", au %s" if lieu["nom"].startswith("Gymnase") else u", à %s") % lieu["nom"]
    elif not m.get("domicile"):
        debut += u", en déplacement"
    return debut + u"."


def soiree_html(s, matchs):
    m = rencontre(s["match"], matchs)
    j = date(*map(int, m["date"].split("-")))
    quand = u"%s %s %s %d" % (bm.JOURS[j.weekday()], u"1er" if j.day == 1 else j.day,
                              bm.MOIS[j.month - 1], j.year)
    ident = "gmatch-" + m["slug"]
    fiche = os.path.join(bm.RACINE, "matchs", m["slug"], "index.html")
    lien = (u' <a href="/matchs/%s/">La fiche du match</a>' % m["slug"]
            if os.path.exists(fiche) else u"")
    photos = s["photos"]
    dims = [sur_disque(p) for p in photos]
    rs = [lg / ht for _, lg, ht in dims]
    lignes = [
        u'    <div class="gmatch reveal" role="group" aria-labelledby="%s">' % ident,
        u'      <div class="gmatch__head">',
        u'        <p class="gmatch__kicker">Seniors &middot; %s</p>' % ech(quand),
        u'        <h3 class="gmatch__title" id="%s">%s</h3>' % (ident, ech(s["titre"])),
        u'        <p class="gmatch__meta">%s%s</p>' % (ech(legende(m, matchs)), lien),
        u'      </div>',
        u'      <div class="gmatch__rows">']
    for rang in rangees(rs):
        somme = sum(rs[i] for i in rang)
        lignes.append(u'        <div class="gmatch__row">')
        for i in rang:
            lignes.append(u'          ' + bouton(photos[i], m["slug"], rs[i], somme, len(rang)))
        lignes.append(u'        </div>')
    lignes += [u'      </div>', u'    </div>']
    return u"\n".join(lignes)


def remplacer_balise(src, balise, contenu):
    """La meme que build-effectif.py : remplace ce qui se trouve entre le
    commentaire « <!-- balise ... --> » et « <!-- /balise --> »."""
    deb, fin = "<!-- %s" % balise, "<!-- /%s -->" % balise
    i, j = src.find(deb), src.find(fin)
    if i < 0 or j < 0:
        raise SystemExit(u"!! balise %s absente de index.html" % balise)
    i = src.index("-->", i) + 3
    k = src.rfind("\n", 0, j)
    marge = src[k + 1:j] if k >= 0 and not src[k + 1:j].strip() else ""
    return src[:i] + "\n" + contenu + "\n" + marge + src[j:]


def bloc(d, matchs):
    return u"\n".join(soiree_html(s, matchs) for s in d["soirees"])


def regenerer():
    """Reecrit le bloc de l'accueil, sans toucher aux images ; rend True si
    index.html a change. Appele par build-matchs.py, donc aussi par
    set-calendrier-prm.py : la legende lit la date, le score et le lieu dans
    data/matchs.json, et un score corrige la-bas doit l'etre ici du meme coup."""
    d = charger()
    verifier(d)
    matchs = json.loads(bm.lire("data/matchs.json"))
    html = bm.lire("index.html")
    neuf = remplacer_balise(html, BALISE, bloc(d, matchs))
    if neuf != html:
        bm.ecrire("index.html", neuf)
    return neuf != html


def main():
    args = sys.argv[1:]
    essai, check = "--essai" in args, "--check" in args
    d = charger()
    verifier(d)
    matchs = json.loads(bm.lire("data/matchs.json"))

    if "--images" in args:
        i = args.index("--images")
        if i + 1 >= len(args) or args[i + 1].startswith("--"):
            raise SystemExit(u"!! --images attend le dossier des originaux")
        dossier = args[i + 1]
        faits, alertes = [], []
        try:
            for s in d["soirees"]:
                jour = rencontre(s["match"], matchs)["date"]
                for p in s["photos"]:
                    f, a = deriver(p, dossier, jour, essai)
                    faits += f
                    alertes += a
        finally:
            # les alertes deja relevees s'affichent meme si une photo arrete tout
            for a in alertes:
                print(u"  !! " + a)
        print(u"  %d derive(s) %s dans %s" % (len(faits), u"a creer" if essai else u"crees", DOSSIER))
        if essai:
            print(u"  (essai : rien n'a ete ecrit)")
            return 0

    html = bm.lire("index.html")
    neuf = remplacer_balise(html, BALISE, bloc(d, matchs))
    nb = sum(len(s["photos"]) for s in d["soirees"])
    if check:
        if neuf != html:
            print(u"  !! le bloc des soirees photo n'est plus celui de %s : "
                  u"lancer python .claude/build-galerie-match.py" % SOURCE)
            return 1
        print(u"  soirees photo : a jour (%d photo(s))" % nb)
        return 0
    print(u"  %d soiree(s), %d photo(s)" % (len(d["soirees"]), nb))
    if essai:
        print(u"  (essai : rien n'a ete ecrit)")
        return 0
    if neuf == html:
        print(u"  index.html deja a jour")
        return 0
    bm.ecrire("index.html", neuf)
    print(u"  ecrit : index.html\n\n  ne pas oublier : python .claude/bump-assets.py")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.exit(main())
