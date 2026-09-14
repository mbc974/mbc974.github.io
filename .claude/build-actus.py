# -*- coding: utf-8 -*-
"""Genere les actualites du club a partir de data/actualites.json.

    python .claude/build-actus.py

Ecrit :
    actualites/index.html               la liste
    actualites/<slug>/index.html        un article par entree

Rien n'est ecrit a la main dans ces fichiers : le texte, les images et les
liens viennent tous du JSON. Cela evite deux derives classiques d'une rubrique
« actus » : des pages qui divergent du reste du site parce qu'on a recopie un
vieil en-tete, et des articles qui racontent des choses que personne ne peut
verifier. Le JSON porte d'ailleurs un bloc « _sources » qui dit, pour chaque
article, d'ou vient ce qu'il affirme.

L'en-tete, la barre CTA, le pied de page et le <head> sont empruntes a
build-matchs.py, qui les releve lui-meme sur une page enfant existante. Une
seule definition, donc, pour toutes les pages generees.

Le bloc « video » (V183, 14/09/2026)
-----------------------------------
Un article peut reprendre une video publiee ailleurs — le premier cas est le
reportage de Reunion la 1ere sur la naissance du club, publie sur la page
Facebook de la chaine. On ne recopie pas la video (elle ne nous appartient
pas) et on ne pose pas non plus le lecteur de Facebook dans la page : charge
d'office, il pese plus d'un megaoctet de scripts tiers et depose ses cookies
avant tout geste du visiteur, ce que la page de confidentialite promet de ne
jamais faire. On ecrit donc une FACADE : une image fixe hebergee ici, un
bouton « Regarder », et script.js n'injecte l'iframe du lecteur qu'au clic —
exactement le mecanisme de la carte Google Maps de l'accueil.

    {"t": "video", "c": {
        "id": "reportage",                 ancre (#reportage) — facultatif
        "source": "Réunion la 1ère",       qui a publie la video
        "sourceUrl", "sourceSameAs"        son site, ses pages — facultatifs
        "emission": "Grand Sport",         facultatif
        "titre": "…",                      le titre tel que publie
        "description": "…",                pour le VideoObject — facultatif
        "url": "https://www.facebook.com/reel/…",      la page publique
        "embed": "https://www.facebook.com/plugins/video.php?href=…",
        "affiche": {base, crans, largeur, hauteur, alt},  comme « image »
        "legende": "…",                    sous la video (HTML permis)
        "datePublication": "AAAA-MM-JJ",   date de mise en ligne CHEZ LA SOURCE
        "duree": "PT3M14S"                 ISO 8601, facultatif
    }}

Si le corps COMMENCE par ce bloc, la facade prend la place de l'image de tete.
Le VideoObject (donnees structurees) n'est ecrit que si « datePublication »
est renseignee : Google l'exige (uploadDate), et on n'invente pas une date.
"""
import io
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "bm", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build-matchs.py"))
bm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bm)

RACINE = bm.RACINE
SITE = bm.SITE
ech = bm.ech
jsonld = bm.jsonld

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def charger():
    d = json.loads(bm.lire("data/actualites.json"))
    for a in d["articles"]:
        dt = datetime.strptime(a["date"], "%Y-%m-%d")
        a["_dt"] = dt
        a["_dateLongue"] = "%d %s %d" % (dt.day, MOIS[dt.month - 1], dt.year)
        a["_dateCourte"] = "%02d.%02d.%d" % (dt.day, dt.month, dt.year)
        a["_url"] = "%s/actualites/%s/" % (SITE, a["slug"])
    d["articles"].sort(key=lambda a: a["_dt"], reverse=True)
    return d


def image(img, sizes, classe="", lazy=True, prio=False, alt=None):
    """Une <img> responsive a partir des crans WebP deja presents dans assets/.

    On ne fabrique aucun fichier ici : les crans listes dans le JSON doivent
    exister. Le repli .jpg garde sa place pour les navigateurs sans WebP, et
    width/height sont toujours ecrits — c'est ce qui empeche la page de sauter
    pendant le chargement.

    `alt` remplace celui du JSON quand l'image est decorative dans son
    contexte — dans la facade video, c'est le bouton qui porte le nom."""
    base, crans = img["base"], img["crans"]
    manquants = [c for c in crans
                 if not os.path.exists(os.path.join(RACINE, "%s-%d.webp" % (base, c)))]
    if manquants:
        print("!! crans absents pour %s : %s" % (base, manquants))
    srcset = ", ".join("/%s-%d.webp %dw" % (base, c, c) for c in crans)
    return (u'<img class="%(cl)s" src="/%(b)s-%(c0)d.webp" srcset="%(ss)s" sizes="%(sz)s"'
            u' width="%(w)d" height="%(h)d" alt="%(alt)s"%(lz)s decoding="async"%(fp)s'
            u' onerror="this.onerror=null;this.srcset=\'\';this.src=\'/%(b)s.jpg\'">'
            % {"cl": classe, "b": base, "c0": crans[0], "ss": srcset, "sz": sizes,
               "w": img["largeur"], "h": img["hauteur"],
               "alt": ech(img["alt"] if alt is None else alt),
               "lz": ' loading="lazy"' if lazy else ' loading="eager"',
               "fp": ' fetchpriority="high"' if prio else ''})


def video_html(v, lead=False):
    """La facade d'une video tierce (V183). Rien de Facebook n'est charge
    ici : une image du depot, un bouton, et data-embed pour script.js.

    Le bouton porte le nom accessible (aria-label) ; tout ce qu'il contient
    est decoratif, y compris l'image (alt vide). Le lien « Voir sur Facebook »
    de la legende reste le chemin sans JavaScript."""
    aff = v["affiche"]
    img = image(aff, "(min-width:900px) 860px, 100vw", "vid-facade__img",
                lazy=not lead, prio=lead, alt=u"")
    src = ech(v["source"])
    if v.get("emission"):
        src += u' <i aria-hidden="true"></i> ' + ech(v["emission"])
    libelle = v.get("libelle") or u"Regarder le reportage"
    titre_lecteur = v.get("titreLecteur") or (u"%s — %s" % (v["titre"], v["source"]))
    aria = v.get("aria") or (u"%s de %s (charge le lecteur vidéo de Facebook)"
                             % (libelle, v["source"]))
    return u"""<figure class="ar__fig ar__fig--video" id="%(id)s">
        <div class="vid-facade__wrap">
          <button type="button" class="vid-facade" data-embed="%(embed)s" data-titre="%(titreLecteur)s"
                  aria-label="%(aria)s">
            %(img)s
            <span class="vid-facade__veil" aria-hidden="true"></span>
            <span class="vid-facade__src" aria-hidden="true">%(src)s</span>
            <span class="vid-facade__play" aria-hidden="true"><svg viewBox="0 0 24 24" fill="currentColor" focusable="false"><path d="M8 5.5v13l11-6.5z"/></svg></span>
            <span class="vid-facade__cta" aria-hidden="true">%(libelle)s</span>
            <span class="vid-facade__note" aria-hidden="true">Lecteur Facebook · chargé uniquement si vous le demandez</span>
          </button>
        </div>
        <figcaption class="ar__cap">%(legende)s <a href="%(url)s" target="_blank" rel="noopener">Voir sur Facebook<span class="sr-only"> (nouvel onglet)</span></a></figcaption>
      </figure>""" % {"id": ech(v.get("id") or "video"), "embed": ech(v["embed"]),
             "titreLecteur": ech(titre_lecteur), "aria": ech(aria), "img": img,
             "src": src, "libelle": ech(libelle), "legende": v.get("legende") or u"",
             "url": ech(v["url"])}


def video_jsonld(v, a):
    """Le VideoObject d'un bloc video, ou None.

    uploadDate est OBLIGATOIRE pour Google : sans la date de mise en ligne
    chez la source, on n'ecrit pas le noeud plutot que d'y mettre une date
    approximative — Search Console compterait une erreur, et le site en
    publierait une fausse. La vignette est la notre (hebergee ici) : c'est ce
    que Google affiche, et le verificateur controle qu'elle existe."""
    if not v.get("datePublication"):
        print(u"!! %s : video sans datePublication, pas de VideoObject" % a["slug"])
        return None
    aff = v["affiche"]
    o = {
        "@type": "VideoObject",
        "@id": a["_url"] + "#video",
        "name": v["titre"],
        "description": v.get("description") or v["titre"],
        "thumbnailUrl": ["%s/%s-%d.webp" % (SITE, aff["base"], aff["crans"][-1])],
        "uploadDate": v["datePublication"],
        "embedUrl": v["embed"],
        "url": v["url"],
        "inLanguage": "fr",
        "about": {"@id": SITE + "/#club"},
    }
    if v.get("duree"):
        o["duration"] = v["duree"]
    if v.get("source"):
        pub = {"@type": "Organization", "name": v["source"]}
        if v.get("sourceUrl"):
            pub["url"] = v["sourceUrl"]
        if v.get("sourceSameAs"):
            pub["sameAs"] = v["sourceSameAs"]
        o["publisher"] = pub
    return o


def corps_html(blocs):
    out = []
    for b in blocs:
        if b["t"] == "p":
            out.append(u'      <p>%s</p>' % b["c"])
        elif b["t"] == "h2":
            out.append(u'      <h2 class="ar__h2">%s</h2>' % ech(b["c"]))
        elif b["t"] == "video":
            out.append(video_html(b["c"]))
        elif b["t"] == "liens":
            liens = []
            for l in b["c"]:
                cls = "btn btn--primary" if l.get("p") else "btn btn--ghost"
                pdf = l["h"].lower().endswith(".pdf")
                extra = u'<span class="sr-only"> (PDF)</span>' if pdf else u''
                liens.append(u'<a class="%s" href="%s">%s%s</a>'
                             % (cls, l["h"], ech(l["l"]), extra))
            out.append(u'      <p class="ar__liens">%s</p>' % "".join(liens))
        else:
            print("!! bloc de type inconnu : %s" % b["t"])
    return "\n".join(out)


def article_jsonld(a, d):
    """NewsArticle. On ne declare que ce qu'on sait : pas d'auteur nomme (les
    articles sont ecrits par le club, pas par une personne identifiee), pas de
    dateModified inventee."""
    ld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "@id": a["_url"] + "#article",
        "headline": a["titre"],
        "description": a.get("meta") or a["chapeau"],
        "url": a["_url"],
        "datePublished": a["date"],
        # dateModified est recommandee par Google, et son absence etait
        # signalee. On ne l'invente pas pour autant : a defaut d'une date de
        # revision dans data/actualites.json, elle vaut la date de publication
        # — ce qui est exact tant que l'article n'a pas ete revu.
        "dateModified": a.get("dateModifiee") or a["date"],
        "inLanguage": "fr",
        "image": ["%s/%s-%d.webp" % (SITE, a["image"]["base"], a["image"]["crans"][-1])],
        "articleSection": a["categorie"],
        "isAccessibleForFree": True,
        # @type SportsClub, et non SportsOrganization : c'est le MEME @id que
        # l'entite declaree sur l'accueil, et un @id ne peut pas porter deux
        # types selon la page qui le cite. Le site en annoncait dix-neuf, neuf
        # « SportsClub » et dix « SportsOrganization ». Un consommateur de
        # donnees structurees qui fusionne par @id — c'est ce que fait Google —
        # recevait donc une entite au type contradictoire.
        "author": {"@type": "SportsClub", "@id": SITE + "/#club",
                   "name": d["site"]["nom"], "url": SITE + "/"},
        "publisher": {"@type": "SportsClub", "@id": SITE + "/#club",
                      "name": d["site"]["nom"], "url": SITE + "/"},
        # Le noeud WebPage de la page porte l'@id « …/#webpage » (voir
        # page_web() dans build-matchs.py). Pointer sur « …/ » creait un SECOND
        # noeud WebPage, vide, a cote du vrai.
        "mainEntityOfPage": {"@id": a["_url"] + "#webpage"},
    }
    # (V183) La video de l'article, imbriquee dans le NewsArticle : c'est la
    # forme que Google documente pour une video au sein d'un article. Une
    # seule par article — la premiere rencontree.
    for b in a["corps"]:
        if b["t"] == "video":
            vid = video_jsonld(b["c"], a)
            if vid:
                ld["video"] = vid
            break
    return ld


def page_article(a, d, precedent, suivant):
    visible, ld_fil = bm.fil([("Accueil", "/"), ("Actualités", "/actualites/"),
                              (a["titreCourt"], None)])
    # La description de partage : le chapeau, sauf si l'article fournit un
    # « meta » plus court. Un chapeau est ecrit pour etre lu en haut de page,
    # une meta description pour tenir dans un resultat de recherche — au-dela
    # d'environ 160 caracteres, Google la tronque et la fin est perdue.
    resume = a.get("meta") or a["chapeau"]
    # L'image de l'article, au cran le plus large, passee a tete() : elle y est
    # mesuree pour og:image:width et :height. La remplacer APRES coup, comme on
    # le faisait, aurait laisse ces deux balises decrire l'image par defaut.
    tete = bm.tete(u"%s — MBC974" % a["titre"], resume, a["_url"],
                   [ld_fil, article_jsonld(a, d)], prof=2,
                   image=u"%s-%d.webp" % (a["image"]["base"], a["image"]["crans"][-1]),
                   image_alt=a["image"]["alt"])
    tete = tete.replace('<meta property="og:type" content="website">',
                        '<meta property="og:type" content="article">')

    voisins = []
    if precedent:
        voisins.append(u'<a class="ar__voisin ar__voisin--p" href="/actualites/%s/">'
                       u'<span>Précédent</span>%s</a>'
                       % (precedent["slug"], ech(precedent["titreCourt"])))
    if suivant:
        voisins.append(u'<a class="ar__voisin ar__voisin--s" href="/actualites/%s/">'
                       u'<span>Suivant</span>%s</a>'
                       % (suivant["slug"], ech(suivant["titreCourt"])))
    nav = (u'\n    <nav class="ar__voisins" aria-label="Autres actualités">%s</nav>'
           % "".join(voisins)) if voisins else u""

    # (V183) Si le corps COMMENCE par une video, sa facade prend la place de
    # l'image de tete : la meme vignette deux fois de suite — en photo puis en
    # facade — n'apporterait rien. L'image de l'article garde ses autres roles
    # (carte de la liste, og:image, NewsArticle.image).
    corps = list(a["corps"])
    if corps and corps[0]["t"] == "video":
        fig = video_html(corps.pop(0)["c"], lead=True)
    else:
        fig = (u'<figure class="ar__fig">%s</figure>'
               % image(a["image"], "(min-width:900px) 860px, 100vw",
                       "ar__img", lazy=False, prio=True))

    return tete + u"""%(entete)s
%(cta)s
<main id="contenu">
  <article class="section ar">
    <div class="wrap ar__wrap">
    %(fil)s
      <p class="ar__meta"><span class="ar__cat">%(cat)s</span><i aria-hidden="true"></i>
        <time datetime="%(iso)s">%(date)s</time></p>
      <h1 class="ar__t">%(titre)s</h1>
      <p class="ar__chapeau">%(chapeau)s</p>
      %(fig)s
%(corps)s%(nav)s
    </div>
  </article>
</main>

%(pied)s

%(scripts)s</body>
</html>
""" % {"entete": bm.GABARIT[0], "cta": bm.GABARIT[1], "pied": bm.GABARIT[2],
       "scripts": bm.GABARIT[3], "fil": visible, "cat": ech(a["categorie"]),
       "iso": a["date"], "date": a["_dateLongue"], "titre": ech(a["titre"]),
       "chapeau": ech(a["chapeau"]),
       "fig": fig, "corps": corps_html(corps), "nav": nav}


def page_liste(d):
    arts = d["articles"]
    visible, ld_fil = bm.fil([("Accueil", "/"), ("Actualités", None)])
    liste_ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": SITE + "/actualites/#liste",
        "name": u"Actualités du %s" % d["site"]["nom"],
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "numberOfItems": len(arts),
        "itemListElement": [{"@type": "ListItem", "position": i + 1,
                             "name": a["titre"], "url": a["_url"]}
                            for i, a in enumerate(arts)],
    }
    tete = bm.tete(u"Actualités du MBC La Montagne Basket Club",
                   u"Les nouvelles du MBC La Montagne Basket Club : la vie du club, "
                   u"la compétition et le quartier, à La Montagne (Saint-Denis, La Réunion).",
                   SITE + "/actualites/", [ld_fil, liste_ld], prof=1)

    cartes = []
    for i, a in enumerate(arts):
        cartes.append(u"""        <li class="ac">
          <a class="ac__l" href="/actualites/%(slug)s/">
            <span class="ac__media">%(img)s</span>
            <span class="ac__corps">
              <span class="ac__meta"><span class="ac__cat">%(cat)s</span><i aria-hidden="true"></i>
                <time datetime="%(iso)s">%(date)s</time></span>
              <span class="ac__t">%(titre)s</span>
              <span class="ac__ch">%(chapeau)s</span>
              <span class="ac__lire">Lire l'article</span>
            </span>
          </a>
        </li>""" % {
            "slug": a["slug"], "cat": ech(a["categorie"]), "iso": a["date"],
            "date": a["_dateLongue"], "titre": ech(a["titre"]),
            "chapeau": ech(a["chapeau"]),
            "img": image(a["image"], "(min-width:1000px) 520px, (min-width:640px) 46vw, 100vw",
                         "ac__img", lazy=(i > 0))})

    return tete + u"""%(entete)s
%(cta)s
<main id="contenu">
  <section class="section ml-sec" aria-labelledby="acTitre">
    <div class="wrap">
    %(fil)s
      <p class="kicker">Le club <i aria-hidden="true"></i> La compétition <i aria-hidden="true"></i> Le quartier <i aria-hidden="true"></i> Les médias</p>
      <h1 class="h2" id="acTitre">Les actualités <span class="hl">du MBC</span></h1>
      <p class="sec-head__sub">Ce qui se passe au club, à La Montagne. Chaque article s'appuie
        sur une source vérifiable&nbsp;: un document officiel, une photo, une page de ce site.</p>

      <ul class="ac-liste">
%(cartes)s
      </ul>

      <p class="ml__retour"><a href="/">Revenir à l'accueil</a></p>
    </div>
  </section>
</main>

%(pied)s

%(scripts)s</body>
</html>
""" % {"entete": bm.GABARIT[0], "cta": bm.GABARIT[1], "pied": bm.GABARIT[2],
       "scripts": bm.GABARIT[3], "fil": visible, "cartes": "\n".join(cartes)}


def main():
    d = charger()
    brut = bm.gabarit()
    bm.GABARIT = brut[:4]
    bm.VERSION_CSS = brut[4]

    ecrits = []
    arts = d["articles"]
    for i, a in enumerate(arts):
        prec = arts[i - 1] if i > 0 else None      # plus recent
        suiv = arts[i + 1] if i + 1 < len(arts) else None   # plus ancien
        bm.ecrire("actualites/%s/index.html" % a["slug"], page_article(a, d, prec, suiv))
        ecrits.append("actualites/%s/index.html" % a["slug"])

    bm.ecrire("actualites/index.html", page_liste(d))
    ecrits.append("actualites/index.html")

    print("Source   : data/actualites.json (%d article(s))" % len(arts))
    print("\n%d fichiers ecrits :" % len(ecrits))
    for f in ecrits:
        print("   " + f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
