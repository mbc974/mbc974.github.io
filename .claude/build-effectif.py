# -*- coding: utf-8 -*-
"""Genere le teaser de l'accueil et la page /effectif/ depuis data/effectif.json.

    python .claude/build-effectif.py
    python .claude/build-effectif.py --essai   montre le bilan, n'ecrit rien

POURQUOI CE SCRIPT EXISTE
-------------------------
L'effectif seniors n'existait qu'a un seul endroit : 148 lignes de markup au
milieu de index.html, soit 1 974 px — un ecran et demi sur une page qui en
comptait deja seize. Il n'avait aucune page a lui, aucune donnee structuree, et
ses neuf joueurs n'etaient donc trouvables par personne d'autre que celui qui
faisait defiler l'accueil jusqu'au tiers.

Desormais :
  data/effectif.json    la source (extraite du markup, jamais ressaisie)
  index.html            un RAIL d'affiches, une rangee, + un lien
  effectif/index.html   l'effectif complet, groupe par poste, avec son JSON-LD

POURQUOI UN RAIL, ET PAS « TROIS OU QUATRE JOUEURS »
----------------------------------------------------
Montrer quatre joueurs sur neuf demanderait de choisir lesquels. Ce choix
n'appartient pas a un script, et il se verrait : dans un club, une carte
absente se remarque. Le rail les montre TOUS, dans l'ordre du club (par poste),
sur une seule rangee qui defile. C'est aussi ce qui ressemble le plus a une
feuille de match — et cela tient en 250 px au lieu de 1 500.

CE QUI NE DOIT PAS CHANGER SANS VALIDATION
------------------------------------------
Les affiches portent le nom ET le numero GRAVES dans l'image. Modifier un
numero dans le JSON sans refaire l'affiche ferait dire deux choses differentes
a la meme carte. Deux joueurs portent d'ailleurs le numero 10 (Moine et
Derras) : c'est l'etat constate, il est repris tel quel, et il appartient au
club de trancher.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "bm", os.path.join(os.path.dirname(os.path.abspath(__file__)), "build-matchs.py"))
bm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bm)

SITE = bm.SITE
ech = bm.ech
SOURCE = "data/effectif.json"

# Les memes crans que le markup d'origine ; on ne reencode aucune image ici.
SIZES_RAIL = "120px"
SIZES_PAGE = "(min-width:880px) 26vw, 47vw"


def charger():
    return json.loads(bm.lire(SOURCE))


def tous(d):
    return [p for g in d["groupes"] for p in g["joueurs"]]


def picture(p, sizes, classe_img=""):
    """Chemins ABSOLUS, toujours.

    Le markup d'origine vivait a la racine et pouvait s'ecrire en relatif.
    Recopie tel quel dans /effectif/, « assets/joueurs/… » resolvait vers
    « /effectif/assets/joueurs/… » : les 81 images de la page etaient
    introuvables. verifier-liens.py l'a dit avant qu'une seule ne soit
    publiee — c'est exactement ce pour quoi il existe.
    """
    def srcset(ext):
        return ", ".join("/assets/joueurs/%s-%d.%s %dw" % (p["image"], w, ext, w)
                         for w in p["crans"])
    return (u'<picture>'
            u'<source type="image/avif" sizes="%(sz)s" srcset="%(a)s">'
            u'<source type="image/webp" sizes="%(sz)s" srcset="%(w)s">'
            u'<img src="/assets/joueurs/%(repli)s" width="%(lg)d" height="%(ht)d" '
            u'loading="lazy" decoding="async"%(cl)s alt="%(alt)s">'
            u'</picture>') % {
        "sz": sizes, "a": srcset("avif"), "w": srcset("webp"),
        "repli": p["repli"], "lg": p["largeur"], "ht": p["hauteur"],
        "cl": (' class="%s"' % classe_img) if classe_img else "",
        "alt": ech(p["alt"])}


# --------------------------------------------------------------------------
# Le teaser de l'accueil
# --------------------------------------------------------------------------
def rail_html(d):
    js = tous(d)
    cartes = []
    for p in js:
        # --fx seul : le rail n'a qu'un etat, il n'y a pas de carte depliee.
        style = (' style="--fx:%s"' % p["fx"]) if p.get("fx") else ""
        cartes.append(
            u'        <li class="sq-rail__i"%(st)s>%(pic)s'
            u'<span class="sq-rail__c"><b>%(num)s</b>%(nom)s</span></li>' % {
                "st": style, "pic": picture(p, SIZES_RAIL),
                "num": ech(p["numero"]), "nom": ech(p["nom"].split(" ")[-1].upper())})
    return (u'      <ul class="sq-rail reveal" aria-label="Les %d joueurs de l\'effectif seniors">\n'
            % len(js)) + "\n".join(cartes) + u'\n      </ul>'


# --------------------------------------------------------------------------
# La page /effectif/
# --------------------------------------------------------------------------
def groupes_html(d):
    out = []
    for g in d["groupes"]:
        cartes = []
        for p in g["joueurs"]:
            st = []
            if p.get("fx"):
                st.append("--fx:%s" % p["fx"])
            if p.get("fy"):
                st.append("--fy:%s" % p["fy"])
            cartes.append(
                u'          <li class="sq-card"%(st)s>\n'
                u'            <div class="sq-card__media">%(pic)s</div>\n'
                u'            <p class="sq-card__cap"><span class="sq-num">%(num)s</span>'
                u'<span class="sq-txt"><span class="sq-nom">%(nom)s</span>'
                u'<span class="sq-poste">%(poste)s</span></span></p>\n'
                u'          </li>' % {
                    "st": (' style="%s"' % ";".join(st)) if st else "",
                    "pic": picture(p, SIZES_PAGE), "num": ech(p["numero"]),
                    "nom": ech(p["nom"]), "poste": ech(p["poste"])})
        # « squad--4 » n'est pas decoratif : .squad est un ACCORDEON dont les
        # deux rangees doivent avoir la MEME somme de flex-grow (5,02), sinon
        # la carte ouverte n'a pas la meme largeur d'une rangee a l'autre — et
        # --fy, qui est calcule sur le rapport de la carte depliee, vise alors
        # un cadre qui n'existe pas. C'est ce qui coupait les noms graves des
        # affiches de la seconde rangee (« ONVOIS » pour Monvoisin).
        #   5 cartes : 1,9 + 4 x 0,78 = 5,02
        #   4 cartes : 1,9 + 3 x 1,04 = 5,02   -> d'ou le modificateur
        mod = u" squad--4" if len(g["joueurs"]) == 4 else u""
        out.append(u'      <p class="squad__lab">%s</p>\n'
                   u'      <ul class="squad%s reveal">\n%s\n      </ul>'
                   % (ech(g["libelle"]), mod, "\n".join(cartes)))
    return "\n\n".join(out)


def equipe_jsonld(d):
    """SportsTeam avec ses athletes.

    L'effectif etait nomme et affiche sur l'accueil sans exister dans la
    moindre donnee structuree : neuf personnes que rien ne rattachait au club
    aux yeux d'un moteur. `athlete` est la propriete prevue par Schema.org
    pour cela ; on n'y met QUE le nom, parce que c'est tout ce que le club
    publie — pas de date de naissance, pas de nationalite, rien qui ne soit
    deja a l'ecran."""
    return {
        "@context": "https://schema.org",
        "@type": "SportsTeam",
        "@id": SITE + "/effectif/#equipe",
        "name": u"Équipe seniors masculine — MBC La Montagne Basket Club",
        "sport": "Basketball",
        "url": SITE + "/effectif/",
        "memberOf": {"@id": SITE + "/#club"},
        # « coach » est reste ABSENT jusqu'au 10/09/2026, et c'etait le bon
        # choix : le site presentait Luigi comme « Coach des jeunes » et Fred
        # comme « Coach principal », sans que rien ne dise qui entraine les
        # SENIORS. Declarer un entraineur qu'aucune page n'affirme aurait ete
        # inventer une donnee dans un format que les moteurs lisent comme un
        # fait. Le bureau a tranche : c'est Frederic Sornom — le « Fred » de la
        # carte staff, dont on connait desormais le nom complet.
        "coach": {"@type": "Person", "name": u"Frédéric Sornom"},
        "athlete": [{"@type": "Person", "name": p["nom"]} for p in tous(d)],
    }


def page(d):
    visible, ld_fil = bm.fil([(u"Accueil", "/"), (u"Effectif seniors", None)])
    n = len(tous(d))
    tete = bm.tete(
        u"Effectif seniors 2026/2027 — MBC La Montagne",
        u"Les %d joueurs de l'équipe seniors du MBC La Montagne Basket Club, "
        u"engagée en Pré-Régionale Masculine zone Nord, saison 2026/2027." % n,
        SITE + "/effectif/", [ld_fil, equipe_jsonld(d)], prof=1)
    return tete + u"""%(entete)s
%(cta)s
<main id="contenu">
  <section class="section squad-sec" aria-labelledby="efTitre">
    <div class="wrap">
    %(fil)s
      <header class="sec-head">
        <p class="kicker">%(comp)s</p>
        <h1 class="h2" id="efTitre">L’effectif <span class="hl">seniors</span></h1>
        <p class="sec-head__sub">%(n)d joueurs engagés en %(comp)s pour la saison
          %(saison)s, groupés par poste. L’effectif est complété au fil de la saison.</p>
      </header>

%(groupes)s

      <p class="sec-cta"><a class="btn btn--ghost btn--lg" href="/matchs/">Voir le calendrier
        des rencontres</a></p>
      <p class="ml__retour"><a href="/">Revenir à l’accueil</a></p>
    </div>
  </section>
</main>

%(pied)s

%(scripts)s</body>
</html>
""" % {"entete": bm.GABARIT[0], "cta": bm.GABARIT[1], "pied": bm.GABARIT[2],
       "scripts": bm.GABARIT[3], "fil": visible, "n": n,
       "comp": ech(d["competition"]), "saison": d["saison"],
       "groupes": groupes_html(d)}


def remplacer_balise(src, balise, contenu):
    deb, fin = "<!-- %s" % balise, "<!-- /%s -->" % balise
    i, j = src.find(deb), src.find(fin)
    if i < 0 or j < 0:
        raise SystemExit(u"!! balise %s absente de index.html" % balise)
    i = src.index("-->", i) + 3
    k = src.rfind("\n", 0, j)
    marge = src[k + 1:j] if k >= 0 and not src[k + 1:j].strip() else ""
    return src[:i] + "\n" + contenu + "\n" + marge + src[j:]


def main():
    essai = "--essai" in sys.argv
    d = charger()
    n = len(tous(d))
    if essai:
        print(u"  %d joueur(s), %d groupe(s)" % (n, len(d["groupes"])))
        for g in d["groupes"]:
            print(u"    %s : %s" % (g["libelle"],
                                    ", ".join(u"#%s %s" % (p["numero"], p["nom"])
                                              for p in g["joueurs"])))
        print(u"  (essai : rien n'a ete ecrit)")
        return 0
    brut = bm.gabarit()
    bm.GABARIT = brut[:4]
    bm.VERSION_CSS = brut[4]
    bm.ecrire("index.html", remplacer_balise(bm.lire("index.html"), "effectif:rail", rail_html(d)))
    bm.ecrire("effectif/index.html", page(d))
    print(u"  ecrit : index.html (rail de %d affiches)" % n)
    print(u"  ecrit : effectif/index.html")
    print(u"\n  ne pas oublier : python .claude/bump-assets.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
