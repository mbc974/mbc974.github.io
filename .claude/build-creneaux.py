# -*- coding: utf-8 -*-
"""Genere tout ce qui parle d'horaires, a partir de data/creneaux.json.

    python .claude/build-creneaux.py
    python .claude/build-creneaux.py --essai    montre le bilan, n'ecrit rien

POURQUOI CE SCRIPT EXISTE
-------------------------
Le meme creneau etait ecrit A LA MAIN a neuf endroits :

    1. le planning hebdomadaire de l'accueil        (index.html, .pl-jour)
    2. les boutons de filtre de ce planning          (index.html, .pl-f)
    3. les huit cartes categories                    (index.html, .cat__meta)
    4. les six panneaux du selecteur d'age           (index.html, .age__facts)
    5. le bloc openingHoursSpecification du <head>   (index.html, JSON-LD)
    6. baby-basket-la-reunion/index.html
    7. ecole-de-basket-saint-denis/index.html        (deux fois, + son JSON-LD)
    8. basket-adulte-loisirs-saint-denis/index.html  (deux fois)
    9. les reponses de FAQ, en HTML et en JSON-LD

Avancer l'entrainement du lundi d'une demi-heure demandait donc neuf
modifications coherentes, et RIEN ne les verifiait. Le site n'avait pas encore
menti sur ce point — les neuf endroits disaient la meme chose — mais il n'y
avait aucune raison structurelle a cela, seulement du soin. Ce fichier remplace
le soin par une garantie.

CE QU'IL ECRIT
--------------
    index.html          entre <!-- creneaux:filtres --> et <!-- /creneaux:filtres -->
    index.html          entre <!-- creneaux:jours -->   et <!-- /creneaux:jours -->
    index.html          la ligne .cat__meta de chaque <article data-cat="…">
    index.html          la ligne « Creneau » de chaque <div data-cat="…" class="age__panel">
    index.html          le tableau openingHoursSpecification du JSON-LD du club
    creneaux/index.html la page dediee, qui n'existait pas

CE QU'IL N'ECRIT PAS
--------------------
Les pages categories (baby, ecole, adulte) redigent leur creneau dans une
phrase, au fil du texte : « le samedi matin, de 09h00 a 10h00 ». Les reecrire
demanderait de generer de la prose, ce qui ferait perdre le ton de ces pages.
Le script les CONTROLE donc au lieu de les ecrire : il verifie que l'horaire
cite s'y retrouve bien dans data/creneaux.json, et le signale sinon. C'est la
meme logique que set-calendrier-prm.py, qui refuse d'ecrire quand le PDF de la
ligue et data/matchs.json divergent.

L'ORDRE
-------
Comme les autres generateurs, celui-ci se lance AVANT bump-assets.py.
"""
import io
import json
import os
import re
import subprocess
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

SOURCE = "data/creneaux.json"

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

# Les six onglets du selecteur d'age de l'accueil, dans l'ordre. Le dernier en
# couvre deux : a partir de 16 ans, on choisit entre competition et loisir.
# C'est ce regroupement, et lui seul, qui justifie phrase_panneau().
PANNEAUX = [["baby"], ["ecole"], ["u13"], ["u15"], ["u18"], ["seniors", "loisir"]]

# Les trois natures de creneau et la classe CSS qui va avec. « match » designe
# une RESERVATION DE SALLE pour recevoir une rencontre officielle, pas une
# rencontre : la salle n'est pas occupee toutes les semaines.
NATURES = {
    "entrainement": ("pl-slot--train", u"Entraînement"),
    "loisir": ("pl-slot--loisir", u"Loisir mixte"),
    "match": ("pl-slot--match", u"Match à domicile"),
}

# Les deux picto SVG du planning, releves tels quels sur le markup d'origine.
PIN = (u'<svg class="pl-slot__pin" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       u'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
       u'<path d="M12 21s-7-6.3-7-11a7 7 0 0 1 14 0c0 4.7-7 11-7 11Z"/>'
       u'<circle cx="12" cy="10" r="2.5"/></svg>')
FLECHE_EXT = (u'<svg class="pl-slot__fl" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              u'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" '
              u'aria-hidden="true"><path d="M7 17 17 7M9 7h8v8"/></svg>')


def derniere_modif(chemin):
    """La date affichee par « Planning a jour au … » ne se saisit pas : elle est
    lue dans git, exactement comme le lastmod du sitemap. Une date ecrite a la
    main serait rassurante et fausse — c'est le pire des deux."""
    MOIS = [u"janvier", u"février", u"mars", u"avril", u"mai", u"juin", u"juillet",
            u"août", u"septembre", u"octobre", u"novembre", u"décembre"]
    iso = None
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", chemin],
                           cwd=RACINE, capture_output=True, text=True, timeout=15)
        d = r.stdout.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            propre = subprocess.run(["git", "status", "--porcelain", "--", chemin],
                                    cwd=RACINE, capture_output=True, text=True, timeout=15)
            if not propre.stdout.strip():
                iso = d
    except Exception:
        pass
    if not iso:
        iso = datetime.fromtimestamp(
            os.path.getmtime(os.path.join(RACINE, chemin))).strftime("%Y-%m-%d")
    a, m, j = iso.split("-")
    return u"%d %s %s" % (int(j), MOIS[int(m) - 1], a)


def charger():
    d = json.loads(bm.lire(SOURCE))
    d["_cat"] = {c["id"]: c for c in d["categories"]}
    for c in d["creneaux"]:
        inconnues = [i for i in c["categories"] if i not in d["_cat"]]
        if inconnues:
            raise SystemExit(u"!! %s : categorie inconnue %s" % (SOURCE, ", ".join(inconnues)))
        if c["lieu"] not in d["lieux"]:
            raise SystemExit(u"!! %s : lieu inconnu %s" % (SOURCE, c["lieu"]))
        if c["jour"] not in JOURS:
            raise SystemExit(u"!! %s : jour inconnu %s" % (SOURCE, c["jour"]))
    d["creneaux"].sort(key=lambda c: (JOURS.index(c["jour"]), c["debut"]))
    return d


def hhmm(t):
    """« 17:30 » -> « 17h30 ». Une seule ecriture pour tout le site : l'accueil
    melangeait « 09h00 – 10h00 » dans une carte et « 09:00 — 10:00 » dans le
    planning, pour le meme creneau du samedi matin."""
    return t.replace(":", "h")


def maj(s):
    return s[0].upper() + s[1:] if s else s


# --------------------------------------------------------------------------
# Les phrases d'horaire — une seule fonction, donc une seule facon de le dire
# --------------------------------------------------------------------------
def pratique(d, ids):
    """Les creneaux ou l'on PRATIQUE, pour une ou plusieurs categories.

    Les lignes « match » en sont exclues : ce sont des reservations de salle,
    pas des seances. Une carte categorie qui annoncerait « vendredi 20h00 »
    enverrait un parent au gymnase un soir ou son enfant ne joue pas."""
    return [c for c in d["creneaux"]
            if c["nature"] != "match" and any(i in c["categories"] for i in ids)]


def phrase(d, ids):
    """L'horaire d'une categorie, en une ligne.

    Trois cas, et le choix se fait sur les DONNEES, jamais sur une habitude :
      - un seul creneau      -> « Samedi · 09h00 – 10h00 · Gymnase »
      - deux creneaux identiques en heure ET en lieu
                             -> « Lundi & mercredi 19h00 – 20h30 · Gymnase »
      - sinon                -> « Lundi 17h30 – 19h00 · Mercredi 14h30 – 16h00 »

    Le lieu n'est cite que lorsqu'il est le meme partout : l'afficher sur une
    ligne qui melange deux salles laisserait croire qu'elles s'appliquent aux
    deux. Les cartes disaient jusqu'ici « Lundi 17h30 & mercredi 14h30 » — les
    heures de FIN manquaient, et le parent ne savait pas quand venir chercher
    son enfant."""
    cs = pratique(d, ids)
    if not cs:
        return u""
    lieux = {c["lieu"] for c in cs}
    lieu = d["lieux"][cs[0]["lieu"]]["court"] if len(lieux) == 1 else None

    if len(cs) == 1:
        c = cs[0]
        bout = u"%s · %s – %s" % (maj(c["jour"]), hhmm(c["debut"]), hhmm(c["fin"]))
        return bout + (u" · " + lieu if lieu else u"")

    memes = len({(c["debut"], c["fin"]) for c in cs}) == 1
    if memes and lieu:
        jours = [c["jour"] for c in cs]
        c = cs[0]
        return u"%s %s – %s · %s" % (
            maj(u" & ".join(jours)), hhmm(c["debut"]), hhmm(c["fin"]), lieu)

    bouts = [u"%s %s – %s" % (maj(c["jour"]), hhmm(c["debut"]), hhmm(c["fin"])) for c in cs]
    return u" · ".join(bouts) + (u" · " + lieu if lieu else u"")


def phrase_panneau(d, ids):
    """Le panneau « Adulte » du selecteur d'age couvre DEUX categories, dont
    les creneaux different. Il annoncait « Lundi 19h00, mercredi 19h00 ou
    20h30 » : une ligne exacte pour personne, puisqu'un joueur seniors n'a rien
    a faire du 20h30 et qu'un joueur loisir n'a rien a faire du 19h00. On
    nomme donc la categorie devant son horaire."""
    if len(ids) == 1:
        return phrase(d, ids)
    # Seule la PREMIERE lettre redescend en minuscule : un .lower() sur toute
    # la phrase ecrivait « gymnase » et « ruisseau blanc », qui sont des noms
    # propres.
    def sans_maj(t):
        return t[0].lower() + t[1:] if t else t
    return u" · ".join(u"%s : %s" % (d["_cat"][i]["court"], sans_maj(phrase(d, [i])))
                       for i in ids if pratique(d, [i]))


# --------------------------------------------------------------------------
# Le planning
# --------------------------------------------------------------------------
def chips(d, c):
    """La puce d'un creneau. « chip » quand la categorie en declare un, sinon
    son nom court : dans le planning, « Baby Basket » et « École de Basket »
    s'ecrivent en entier — ce sont les deux categories que cherchent des
    parents qui ne connaissent pas encore le vocabulaire du club — la ou U13,
    U15 ou Seniors se suffisent."""
    if c.get("etiquette"):
        return u'<span class="pl-chip">%s</span>' % ech(c["etiquette"])
    return u"".join(
        u'<span class="pl-chip">%s</span>' % ech(d["_cat"][i].get("chip") or d["_cat"][i]["court"])
        for i in c["categories"])


def slot_html(d, c):
    classe, titre_defaut = NATURES[c["nature"]]
    L = d["lieux"][c["lieu"]]
    prec = (u'<span class="pl-slot__prec">%s</span>' % ech(c["precision"])) if c.get("precision") else u""
    return (
        u'          <li class="pl-slot %(classe)s" data-cat="%(cats)s" data-lieu="%(lieu)s">\n'
        u'            <p class="pl-slot__h"><time datetime="%(debut)s">%(debut)s</time>'
        u'<span class="pl-slot__sep" aria-hidden="true">—</span>'
        u'<time datetime="%(fin)s">%(fin)s</time></p>\n'
        u'            <p class="pl-slot__cats">%(chips)s</p>\n'
        u'            <p class="pl-slot__nat"><span class="pl-dot" aria-hidden="true"></span>'
        u'<b>%(titre)s</b>%(prec)s</p>\n'
        u'            <a class="pl-slot__ou" href="%(carte)s" target="_blank" rel="noopener noreferrer" '
        u'title="Ouvrir l\'itinéraire dans Google Maps">%(pin)s'
        u'<span class="pl-slot__nom">%(nom)s</span>'
        u'<span class="pl-slot__go">Itinéraire</span>%(fleche)s'
        u'<span class="sr-only"> (Google Maps, nouvel onglet)</span></a>\n'
        u'          </li>') % {
        "classe": classe, "cats": " ".join(c["categories"]), "lieu": c["lieu"],
        "debut": c["debut"], "fin": c["fin"], "chips": chips(d, c),
        "titre": ech(c.get("titre") or titre_defaut), "prec": prec,
        "carte": L["carte"], "nom": ech(L["nom"]), "pin": PIN, "fleche": FLECHE_EXT}


def jours_html(d):
    out = []
    for jour in JOURS:
        cs = [c for c in d["creneaux"] if c["jour"] == jour]
        if not cs:
            continue
        n = len(cs)
        out.append(
            u'      <section class="pl-jour" aria-labelledby="pl-j-%(id)s">\n'
            u'        <h4 class="pl-jour__n" id="pl-j-%(id)s">%(nom)s'
            u'<span class="pl-jour__n2">%(n)d créneau%(s)s</span></h4>\n'
            u'        <ol class="pl-jour__l">\n%(slots)s\n'
            u'        </ol>\n'
            u'      </section>' % {
                "id": jour, "nom": maj(jour), "n": n, "s": u"x" if n > 1 else u"",
                "slots": "\n".join(slot_html(d, c) for c in cs)})
    out.append(u'      <p class="pl-note">Les créneaux <b>Match à domicile</b> sont réservés '
               u'aux rencontres officielles selon le calendrier FFBB&nbsp;: la salle n\'est pas '
               u'occupée toutes les semaines.</p>')
    return "\n".join(out)


def filtres_html(d):
    """Un bouton par categorie qui a au moins un creneau, plus « Tous ».

    L'ordre est celui de data/creneaux.json, c'est-a-dire l'ordre des AGES, et
    non l'ordre d'apparition dans la semaine. Trier sur la semaine remontait
    Baby et École en fin de liste — alors que ce sont les deux premieres que
    cherche un parent, et que les cartes juste au-dessus les presentent dans
    cet ordre-la.

    Se deduit des donnees : une categorie sans creneau n'apparait pas, et un
    filtre ne peut plus pointer vers une categorie disparue."""
    avec = {i for c in d["creneaux"] for i in c["categories"]}
    b = [u'          <button type="button" class="pl-f is-on" data-cat="tous" '
         u'aria-pressed="true">Tous</button>']
    for c in d["categories"]:
        if c["id"] in avec:
            b.append(u'          <button type="button" class="pl-f" data-cat="%s" '
                     u'aria-pressed="false">%s</button>' % (c["id"], ech(c["court"])))
    return "\n".join(b)


def heures_ouverture(d):
    """Le tableau openingHoursSpecification, un objet par creneau.

    Un seul intervalle par ligne, meme quand deux se touchent : le bloc ecrit a
    la main fusionnait le samedi (09h00-10h00 + 10h00-11h30 -> 09h00-11h30) mais
    pas le mercredi soir, pourtant contigu lui aussi. Les deux formes sont
    valides pour Schema.org ; une seule est verifiable ligne a ligne."""
    ANG = {"lundi": "Monday", "mardi": "Tuesday", "mercredi": "Wednesday",
           "jeudi": "Thursday", "vendredi": "Friday", "samedi": "Saturday",
           "dimanche": "Sunday"}
    lignes = [u'    {"@type":"OpeningHoursSpecification","dayOfWeek":"%s","opens":"%s","closes":"%s"}'
              % (ANG[c["jour"]], c["debut"], c["fin"]) for c in d["creneaux"]]
    return u'  "openingHoursSpecification": [\n' + u",\n".join(lignes) + u'\n  ],'


# --------------------------------------------------------------------------
# Les remplacements dans index.html
# --------------------------------------------------------------------------
def remplacer_balise(src, balise, contenu):
    """Reecrit ce qui se trouve ENTRE les deux marqueurs, eux compris exclus.

    L'indentation du marqueur fermant est relevee sur la ligne plutot que
    devinee : une premiere version prenait « les six caracteres precedents »,
    ce qui marchait pour un bloc indente de six espaces et abimait les autres."""
    deb, fin = "<!-- %s" % balise, "<!-- /%s -->" % balise
    i, j = src.find(deb), src.find(fin)
    if i < 0 or j < 0:
        raise SystemExit(u"!! balise %s absente de index.html" % balise)
    i = src.index("-->", i) + 3
    k = src.rfind("\n", 0, j)
    marge = src[k + 1:j] if k >= 0 and not src[k + 1:j].strip() else ""
    return src[:i] + "\n" + contenu + "\n" + marge + src[j:]


def remplacer_dans_bloc(src, ouverture, motif, texte, quoi):
    """Remplace, DANS le bloc qui commence a `ouverture`, le contenu encadre par
    les deux groupes de `motif` par `texte`.

    On travaille par bornes textuelles et non par un parseur : le depot n'a
    aucune dependance, et ce markup n'est ecrit que par ce depot.

    Le remplacement est fait par une fonction qui recolle elle-meme les deux
    groupes. Ecrire un gabarit avec des references arriere (\\g<1>) serait ici
    un piege : re.sub ne les developpe PAS quand le remplacement est une
    fonction, et la page se retrouve avec « \\g<1> » en toutes lettres a
    l'ecran. C'est arrive une fois."""
    i = src.find(ouverture)
    if i < 0:
        raise SystemExit(u"!! %s : bloc introuvable" % quoi)
    j = src.find("</article>", i)
    if j < 0:
        j = src.find("</div>", i)
    bloc = src[i:j]
    neuf, n = re.subn(motif, lambda m: m.group(1) + texte + m.group(2), bloc, count=1)
    if n != 1:
        raise SystemExit(u"!! %s : %d remplacement(s), attendu 1" % (quoi, n))
    return src[:i] + neuf + src[j:]


def ecrire_index(d, html):
    html = remplacer_balise(html, "creneaux:filtres", filtres_html(d))
    html = remplacer_balise(html, "creneaux:jours", jours_html(d))

    # Le tableau openingHoursSpecification, dans le JSON-LD du club.
    motif = re.compile(r'  "openingHoursSpecification": \[.*?\n  \],', re.S)
    html, n = motif.subn(lambda m: heures_ouverture(d), html, count=1)
    if n != 1:
        raise SystemExit(u"!! openingHoursSpecification : %d bloc(s), attendu 1" % n)

    # La ligne .cat__meta de chaque carte.
    for c in d["categories"]:
        txt = c.get("sansCreneau") or phrase(d, [c["id"]])
        if not txt:
            continue
        html = remplacer_dans_bloc(
            html, '<article data-cat="%s"' % c["id"],
            r'(<p class="cat__meta">.*?</svg>\s*)[^<]*(</p>)',
            ech(txt), u'carte %s' % c["id"])

    # La ligne « Creneau » de chaque panneau du selecteur d'age. Le panneau
    # « Adulte » en couvre DEUX : c'est le seul, et c'est pour cela que sa
    # phrase nomme la categorie devant l'horaire.
    # La borne d'ouverture ne cite QUE data-cat, jamais la classe. Un
    # '... class="age__panel' laisse dans ce fichier une chaine de classe non
    # terminee, et verifier-classes.py — qui lit aussi les generateurs depuis
    # le 08/09/2026 — la comptait comme une classe « age__panel' » sans regle
    # CSS. Le garde-fou avait raison de lire ici ; c'est a l'appat de
    # disparaitre. data-cat suffit a distinguer le panneau de la carte, qui
    # est un <article>.
    for ids in PANNEAUX:
        html = remplacer_dans_bloc(
            html, '<div data-cat="%s"' % " ".join(ids),
            r'(<li><span>Créneau</span><b>)[^<]*(</b></li>)',
            ech(phrase_panneau(d, ids)), u'panneau %s' % "/".join(ids))
    return html


# --------------------------------------------------------------------------
# Le controle des pages categories, qui redigent leur horaire en toutes lettres
# --------------------------------------------------------------------------
CONTROLES = [
    ("baby-basket-la-reunion/index.html", ["baby"]),
    ("ecole-de-basket-saint-denis/index.html", ["ecole"]),
    ("basket-adulte-loisirs-saint-denis/index.html", ["seniors", "loisir"]),
]


def controler_pages(d):
    """On ne reecrit pas la prose de ces pages : on verifie qu'elle ne ment pas.

    Deux controles, et le premier a failli etre trop strict. Restreindre les
    heures admises a celles de la categorie de la page signalait le « 09h00 »
    de ecole-de-basket-saint-denis, qui renvoie pourtant tres legitimement au
    Baby Basket juste avant (« pratique si vous avez deux enfants d'ages
    differents a deposer le meme matin »). Un garde-fou qui crie sur une
    phrase juste finit par etre ignore, puis par ne plus rien garder.

      1. Toute heure ecrite dans la page doit exister quelque part dans
         data/creneaux.json : cela attrape la faute de frappe et la valeur
         devenue perimee, sans interdire de citer une autre categorie.
      2. L'horaire de la categorie de la page doit y figurer : une page Baby
         Basket qui n'ecrirait plus 09h00 aurait ete oubliee le jour ou le
         creneau a change."""
    alertes = []
    toutes = set()
    for c in d["creneaux"]:
        toutes.add(hhmm(c["debut"]))
        toutes.add(hhmm(c["fin"]))
    for chemin, ids in CONTROLES:
        if not os.path.exists(os.path.join(RACINE, chemin)):
            continue
        txt = re.sub(r"<[^>]+>", " ", bm.lire(chemin))
        ecrites = set(re.findall(r"\b(\d{2}h\d{2})\b", txt))
        for h in sorted(ecrites - toutes):
            alertes.append(u"%s : « %s » n'est l'heure d'aucun creneau du club"
                           % (chemin, h))
        siennes = set()
        for c in pratique(d, ids):
            siennes.add(hhmm(c["debut"]))
            siennes.add(hhmm(c["fin"]))
        for h in sorted(siennes - ecrites):
            alertes.append(u"%s : le creneau de %s dit %s, la page ne l'ecrit nulle part"
                           % (chemin, "/".join(ids), h))
    return alertes


# --------------------------------------------------------------------------
# La page /creneaux/
# --------------------------------------------------------------------------
def carte_lieu(L, cle):
    return (
        u'        <li>\n'
        u'          <a class="cal-lieu" data-lieu="%(cle)s" href="%(carte)s" target="_blank" '
        u'rel="noopener noreferrer">\n'
        u'            <span class="cal-lieu__txt">\n'
        u'              <span class="cal-lieu__tag">%(tag)s</span>\n'
        u'              <b class="cal-lieu__nom">%(nom)s</b>\n'
        u'              <span class="cal-lieu__adr">%(adr)s<br>%(cp)s %(ville)s &middot; %(region)s</span>\n'
        u'              <span class="cal-lieu__cnt" hidden></span>\n'
        u'              <span class="cal-lieu__map">Voir sur Google Maps%(fleche)s</span>\n'
        u'            </span>\n'
        u'            <span class="sr-only"> (nouvel onglet)</span>\n'
        u'          </a>\n'
        u'        </li>') % {
        "cle": cle, "carte": L["carte"], "tag": ech(L["tag"]), "nom": ech(L["nom"]),
        "adr": ech(L["adresse"]), "cp": L["codePostal"], "ville": ech(L["ville"]),
        "region": ech(L["region"]),
        "fleche": (u'<svg class="cal-lieu__mapic" viewBox="0 0 24 24" fill="none" '
                   u'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
                   u'stroke-linejoin="round" aria-hidden="true"><path d="M7 17 17 7M9 7h8v8"/></svg>')}


def page_creneaux(d, maj_le):
    visible, ld_fil = bm.fil([("Accueil", "/"), (u"Créneaux", None)])
    tete = bm.tete(
        u"Créneaux d'entraînement 2026/2027 — MBC La Montagne",
        u"Tous les créneaux du MBC : Baby Basket, école de basket, U13, U15, U18, "
        u"seniors et loisirs, au Gymnase de La Montagne et au Terrain Ruisseau Blanc, "
        u"à Saint-Denis de La Réunion.",
        SITE + "/creneaux/", [ld_fil], prof=1)

    rappels = []
    for c in d["categories"]:
        txt = c.get("sansCreneau") or phrase(d, [c["id"]])
        if c.get("sansCreneau"):
            continue
        rappels.append(
            u'        <li class="cx-cat"><a href="/%(page)s"><b>%(nom)s</b>'
            u'<span class="cx-cat__q">%(nais)s</span>'
            u'<span class="cx-cat__h">%(h)s</span></a></li>' % {
                "page": c["page"], "nom": ech(c["nom"]),
                "nais": ech(c["naissance"]), "h": ech(txt)})

    return tete + u"""%(entete)s
%(cta)s
<main id="contenu">
  <section class="section calendrier" aria-labelledby="cxTitre">
    <div class="wrap cal-wrap">
    %(fil)s
      <header class="sec-head">
        <p class="kicker">Saison %(saison)s</p>
        <h1 class="h2" id="cxTitre">Les créneaux <span class="hl">du MBC</span></h1>
        <p class="sec-head__sub">Tous les entraînements de la semaine, entre le Gymnase de
          La Montagne et le Terrain Ruisseau Blanc. Les lignes «&nbsp;match à domicile&nbsp;»
          sont des <b>réservations de salle</b> pour recevoir les rencontres&nbsp;: elles ne
          sont pas occupées toutes les semaines.</p>
      </header>

      <ul class="cal-lieux" aria-label="Les deux lieux de pratique du club">
%(lieux)s
      </ul>

      <div class="pl">
        <div class="pl-top">
          <h2 class="pl-top__t">Planning hebdomadaire</h2>
        </div>
        <div class="pl-filtres" role="group" aria-label="Filtrer le planning par catégorie">
          <span class="pl-filtres__lab" aria-hidden="true">Je cherche</span>
          <div class="pl-filtres__l">
%(filtres)s
          </div>
        </div>
        <p class="pl-aucun" role="status" hidden>Aucun créneau pour cette catégorie.</p>
%(jours)s
      </div>

      <h2 class="h2 cx-h2">Le créneau <span class="hl">de chaque catégorie</span></h2>
      <ul class="cx-cats">
%(rappels)s
      </ul>

      <p class="cal-note">Les créneaux peuvent évoluer en cours de saison — contactez-nous
        pour confirmer celui de votre catégorie. Planning à jour au %(maj)s.</p>
      <p class="cal-note"><a href="/matchs/">Voir le calendrier des rencontres</a> —
        et <a href="/adhesion.html">s'inscrire pour la saison %(saison)s</a>.</p>
      <p class="ml__retour"><a href="/">Revenir à l'accueil</a></p>
    </div>
  </section>
</main>

%(pied)s

%(scripts)s<!-- Cette page est la SEULE page enfant a charger script.js.
     Les 24 autres s'en passent volontairement : le fichier fait 60 Ko et ses
     modules servent l'accueil. Ici, le filtre du planning EST la page — sans
     lui, les huit boutons ne feraient rien. Le dupliquer en ligne aurait
     recree exactement la duplication que data/creneaux.json vient de
     supprimer, cette fois dans le JavaScript. C'est le meme fichier que
     l'accueil, donc deja en cache pour qui vient de la home, et deja precache
     par le service worker.
     bump-assets.py y pose le ?v= tout seul (il ancre sur src="/script.js"). -->
<script src="/script.js" defer></script>
</body>
</html>
""" % {"entete": bm.GABARIT[0], "cta": bm.GABARIT[1], "pied": bm.GABARIT[2],
       "scripts": bm.GABARIT[3], "fil": visible, "saison": d["saison"],
       "lieux": "\n".join(carte_lieu(d["lieux"][k], k) for k in ("gymnase", "ruisseau")),
       "filtres": filtres_html(d), "jours": jours_html(d),
       "rappels": "\n".join(rappels), "maj": maj_le}


def main():
    essai = "--essai" in sys.argv
    d = charger()

    alertes = controler_pages(d)
    for a in alertes:
        print(u"  !! %s" % a)

    brut = bm.gabarit()
    bm.GABARIT = brut[:4]
    bm.VERSION_CSS = brut[4]

    html = ecrire_index(d, bm.lire("index.html"))
    page = page_creneaux(d, derniere_modif(SOURCE))

    if essai:
        print(u"  essai : index.html et creneaux/index.html seraient reecrits")
        print(u"  %d creneaux, %d categories" % (len(d["creneaux"]), len(d["categories"])))
        for c in d["categories"]:
            print(u"    %-10s %s" % (c["id"], c.get("sansCreneau") or phrase(d, [c["id"]])))
        return 1 if alertes else 0

    bm.ecrire("index.html", html)
    bm.ecrire("creneaux/index.html", page)
    print(u"  ecrit : index.html (planning, filtres, cartes, selecteur, openingHours)")
    print(u"  ecrit : creneaux/index.html")
    print(u"\n  ne pas oublier : python .claude/bump-assets.py")
    return 1 if alertes else 0


if __name__ == "__main__":
    sys.exit(main())
