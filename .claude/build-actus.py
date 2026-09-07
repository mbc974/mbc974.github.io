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


def image(img, sizes, classe="", lazy=True, prio=False):
    """Une <img> responsive a partir des crans WebP deja presents dans assets/.

    On ne fabrique aucun fichier ici : les crans listes dans le JSON doivent
    exister. Le repli .jpg garde sa place pour les navigateurs sans WebP, et
    width/height sont toujours ecrits — c'est ce qui empeche la page de sauter
    pendant le chargement."""
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
               "w": img["largeur"], "h": img["hauteur"], "alt": ech(img["alt"]),
               "lz": ' loading="lazy"' if lazy else ' loading="eager"',
               "fp": ' fetchpriority="high"' if prio else ''})


def corps_html(blocs):
    out = []
    for b in blocs:
        if b["t"] == "p":
            out.append(u'      <p>%s</p>' % b["c"])
        elif b["t"] == "h2":
            out.append(u'      <h2 class="ar__h2">%s</h2>' % ech(b["c"]))
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
    return {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "@id": a["_url"] + "#article",
        "headline": a["titre"],
        "description": a["chapeau"],
        "url": a["_url"],
        "datePublished": a["date"],
        "inLanguage": "fr",
        "image": ["%s/%s-%d.webp" % (SITE, a["image"]["base"], a["image"]["crans"][-1])],
        "articleSection": a["categorie"],
        "isAccessibleForFree": True,
        "author": {"@type": "SportsOrganization", "@id": SITE + "/#club",
                   "name": d["site"]["nom"], "url": SITE + "/"},
        "publisher": {"@type": "SportsOrganization", "@id": SITE + "/#club",
                      "name": d["site"]["nom"], "url": SITE + "/"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": a["_url"]},
    }


def page_article(a, d, precedent, suivant):
    visible, ld_fil = bm.fil([("Accueil", "/"), ("Actualités", "/actualites/"),
                              (a["titreCourt"], None)])
    tete = bm.tete(u"%s — MBC974" % a["titre"], a["chapeau"], a["_url"],
                   [ld_fil, article_jsonld(a, d)], prof=2)
    # og:type et og:image propres a l'article
    tete = tete.replace('<meta property="og:type" content="website">',
                        '<meta property="og:type" content="article">')
    tete = tete.replace(
        '<meta property="og:image" content="%s/assets/images/social-preview.png">' % SITE,
        '<meta property="og:image" content="%s/%s-%d.webp">'
        % (SITE, a["image"]["base"], a["image"]["crans"][-1]))
    tete = tete.replace(
        '<meta name="twitter:image" content="%s/assets/images/social-preview.png">' % SITE,
        '<meta name="twitter:image" content="%s/%s-%d.webp">'
        % (SITE, a["image"]["base"], a["image"]["crans"][-1]))

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
      <figure class="ar__fig">%(img)s</figure>
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
       "img": image(a["image"], "(min-width:900px) 860px, 100vw",
                    "ar__img", lazy=False, prio=True),
       "corps": corps_html(a["corps"]), "nav": nav}


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
      <p class="kicker">Le club <i aria-hidden="true"></i> La compétition <i aria-hidden="true"></i> Le quartier</p>
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
