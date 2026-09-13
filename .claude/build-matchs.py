# -*- coding: utf-8 -*-
"""Genere /matchs/ et une page par rencontre a partir de data/matchs.json.

POURQUOI CE SCRIPT EXISTE
-------------------------
Les informations d'un match etaient ecrites a quatre endroits : le scoreboard
du prochain match, les sept lignes du Match Center, les SportsEvent du JSON-LD
et le fichier .ics. Corriger un horaire demandait quatre modifications
coherentes, et rien ne le verifiait. Desormais data/matchs.json est la seule
source ; ce script en derive tout le reste.

CE QU'IL ECRIT
--------------
  matchs/index.html                 le Match Center complet : dernier resultat,
                                    prochain match, filtres, saison mois par mois
                                    (rendu par .claude/build-match-center.py)
  matchs/<slug>/index.html          une page par rencontre (7)
  assets/documents/<slug>.ics       un rendez-vous par match a domicile
  index.html                        le bandeau « prochain match » sous le hero,
                                    entre les deux marqueurs PROCHAIN-MATCH

CE QU'IL ECRIT AUSSI DANS index.html
-----------------------------------
Le bloc « calendrier:jsonld » de la page d'accueil, qui ne contient plus des
SportsEvent mais une ItemList pointant vers les sept fiches. Un evenement se
declare sur SA page, pas deux fois sur deux URL differentes.

Et le Match Center de l'accueil (bloc MATCH-CENTER), rendu par
.claude/build-match-center.py a partir de la meme source : les echeances de
2e phase, de phase finale et de Coupe de France y figurent aussi.

CE QU'IL NE TOUCHE PAS
----------------------
Les sept lignes du Match Center (#matchs) et leurs ancres #match-AAAA-MM-JJ,
qui servent de cible a 16 liens entrants. Elles restent ecrites par
set-calendrier-prm.py, a partir du PDF de la ligue.

L'HEURE
-------
La Reunion est a UTC+4 toute l'annee, sans heure d'ete. Toutes les dates
structurees portent donc « +04:00 » en dur : utiliser UTC produirait un
evenement affiche a 16h30 dans les resultats de recherche.
"""
import io
import json
import os
import re
import unicodedata
from datetime import datetime, timedelta

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://mbc974.com"
FUSEAU = "+04:00"

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
MOIS_COURT = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
              "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def lire(chemin):
    return io.open(os.path.join(RACINE, chemin), encoding="utf-8").read()


def ecrire(chemin, contenu):
    p = os.path.join(RACINE, chemin)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="").write(contenu)


def ech(t):
    """Echappement HTML. Tout texte venant du JSON passe par la."""
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def jsonld(obj):
    """JSON-LD compact et valide. ensure_ascii=False garde les accents lisibles
    dans la source ; le </script> ne peut pas apparaitre puisque les chaines
    sont echappees en amont."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


# --------------------------------------------------------------------------
# Lecture et enrichissement des donnees
# --------------------------------------------------------------------------
def charger():
    d = json.loads(lire("data/matchs.json"))
    lieux, club = d["lieux"], d["club"]
    for m in d["matchs"]:
        dt = datetime.strptime(m["date"] + " " + m["heure"], "%Y-%m-%d %H:%M")
        fin = dt + timedelta(minutes=m.get("duree") or 120)
        m["_dt"] = dt
        # La FIN, et pas seulement le debut : c'est elle qui doit decider
        # qu'une rencontre appartient au passe. Sur le coup d'envoi, un match
        # en cours basculait dans « Deja joues » des la premiere minute.
        m["_fin"] = fin
        m["_debutIso"] = dt.strftime("%Y-%m-%dT%H:%M:00") + FUSEAU
        m["_finIso"] = fin.strftime("%Y-%m-%dT%H:%M:00") + FUSEAU
        m["_jour"] = JOURS[dt.weekday()]
        m["_dateLongue"] = "%s %d %s %d" % (JOURS[dt.weekday()], dt.day, MOIS[dt.month - 1], dt.year)
        m["_dateCourte"] = "%s %d %s" % (JOURS[dt.weekday()][:3] + ".", dt.day, MOIS_COURT[dt.month - 1])
        m["_heureFr"] = m["heure"].replace(":", "h")
        m["_url"] = "%s/matchs/%s/" % (SITE, m["slug"])
        m["_lieu"] = lieux.get(m["lieu"]) if m["lieu"] else None
        m["_titre"] = ("%s vs %s" % (club["court"], m["adversaireCourt"]) if m["domicile"]
                       else "%s vs %s" % (m["adversaireCourt"], club["court"]))
        # La competition de la rencontre, et l'etiquette de sa journee : « J2 »
        # en championnat, le tour en Coupe (qui n'a pas de numero de journee).
        # Sans ce libelle commun, la premiere affiche de Coupe ajoutee a
        # data/matchs.json aurait fait tomber le bandeau, la fiche, le .ics et
        # l'image de partage, qui ecrivaient tous le numero de journee en dur.
        m["_comp"] = ((d.get("competitions") or {}).get(m.get("competition") or "prm")
                      or dict(d["competition"], court="PRM", genre="championnat"))
        # Hors phase 1, la phase precede la journee : « J1 aller » tout court
        # se confondait avec la J1 du brassage (bandeau, fiche, .ics, courriel).
        _ph = (d.get("phases") or {}).get(m.get("phase") or "") or {}
        _pre = (u"%s · " % _ph["court"]) if (_ph.get("court")
                                             and (m.get("phase") or "brassage") != "brassage") else u""
        if m.get("journee"):
            suite = (" %s" % m["manche"]) if m.get("manche") else ""
            m["_etiquette"] = _pre + "J%d%s" % (m["journee"], suite)
            m["_etiquetteLongue"] = _pre + u"Journée %d%s" % (m["journee"], suite)
        else:
            m["_etiquette"] = m["_etiquetteLongue"] = _pre + (m.get("tour") or m["_comp"].get("court")
                                                              or m["_comp"]["nom"])
        # Un score sur une rencontre qui n'a pas COMMENCE est une erreur de
        # saisie (mauvaise ligne, mauvaise date) : on refuse de le publier.
        # Le coup d'envoi, et non la fin forfaitaire : une rencontre peut
        # s'achever avant les 2 h 30, et son score doit pouvoir partir le soir.
        if m.get("score") and dt > match_center().maintenant():
            raise ValueError(u"data/matchs.json, %s : un score est saisi pour une rencontre "
                             u"qui n'a pas encore commencé (%s)." % (m["slug"], m["date"]))
    d["matchs"].sort(key=lambda m: m["_dt"])
    return d


def prochain(d, maintenant=None):
    """Le prochain match a venir, ou None si la phase est terminee. C'est cette
    fonction qui rend le bandeau de la home reutilisable d'une journee a
    l'autre : il n'est pas code autour du 11 septembre."""
    # L'heure de La Reunion, la meme que celle du Match Center (et la meme
    # variable MBC_MAINTENANT pour simuler une autre date) : le bandeau et le
    # Match Center ne peuvent pas annoncer deux « prochains matchs » differents.
    maintenant = maintenant or match_center().maintenant()
    # Sur _fin et non _dt : tant que le coup de sifflet final n'a pas sonne, le
    # match du soir reste « le prochain ». Un supporter qui ouvre le site a
    # 20h45 un vendredi veut voir la rencontre en cours, pas celle d'apres.
    futurs = [m for m in d["matchs"]
              if m["_fin"] >= maintenant and m["statut"] not in ("annule", "reporte")]
    return futurs[0] if futurs else None


# --------------------------------------------------------------------------
# Gabarit commun : on releve l'en-tete et le pied d'une page enfant existante
# pour qu'ils restent automatiquement synchrones avec le reste du site.
# --------------------------------------------------------------------------
MODELE = "ecole-de-basket-saint-denis/index.html"


def gabarit():
    s = lire(MODELE)
    entete = s[s.index('<header class="seo-top">'):s.index("</header>") + len("</header>")]
    # la barre CTA flottante, entre le header et <main>
    # Le premier decoupage etait aussitot ecrase par le second : ligne morte,
    # retiree.
    cta = s[s.index('<div class="float-cta"'):s.index('<main id="contenu">')].rstrip()

    # La page modele s'adresse aux parents de l'ecole de basket. Recopies tels
    # quels sur une fiche de match seniors ou un article, son libelle et son
    # message WhatsApp pre-rempli deviennent faux : c'est le VISITEUR qui
    # enverrait « je souhaite inscrire mon enfant » depuis une page de match.
    # On neutralise les deux, avec des textes deja employes ailleurs sur le
    # site. La page modele, elle, n'est pas touchee.
    cta = cta.replace(
        "Bonjour%2C%20je%20souhaite%20avoir%20des%20informations%20pour%20"
        "inscrire%20mon%20enfant%20%C3%A0%20l%27%C3%A9cole%20de%20basket%20du%20MBC.",
        "Bonjour%2C%20je%20souhaite%20avoir%20des%20informations%20sur%20le%20MBC.")
    cta = cta.replace("Inscrire mon enfant", "Rejoindre le MBC")

    # Il y avait ici un rustinage de la nav : le modele n'offrant ni Matchs ni
    # Actualites, on les injectait avant \u00ab Contact \u00bb pour qu'une fiche de match
    # ne renvoie pas au calendrier par le seul fil d'Ariane.
    #
    # Le 09/09/2026, la nav des 25 pages a ete unifiee et porte desormais ces
    # deux entrees d'origine. Le rustinage s'est donc mis a les AJOUTER une
    # seconde fois : les pages generees sortaient avec neuf liens dont un
    # \u00ab Matchs \u00bb en double et un \u00ab Actualites \u00bb a cote d'\u00ab Actus \u00bb. Les pages
    # ecrites a la main, elles, etaient justes \u2014 ce qui rendait l'ecart
    # invisible tant qu'on ne comparait pas les deux familles.
    #
    # Lecon : un correctif qui compense un defaut de la source doit mourir avec
    # ce defaut. On ne le garde pas \u00ab au cas ou \u00bb, il devient le defaut suivant.
    pied = s[s.index('<footer class="seo-foot">'):s.index("</footer>") + len("</footer>")]
    scripts = s[s.index("<script>\n/* Barre CTA mobile"):s.index("</body>")]
    # La feuille servie est style.min.css (voir .claude/build-css.py) ; le ?v=
    # accepte aussi le jeton temporaire pose par un lot de modifications, que
    # bump-assets.py remplace ensuite par le vrai hachage.
    version = re.search(r'href="/style\.min\.css\?v=([A-Za-z0-9._-]+)"', s).group(1)
    return entete, cta, pied, scripts, version


# Le meme bloc que dans les pages ecrites a la main. Sans lui, les 12 pages
# generees etaient les seules a n'avoir aucun emplacement de mesure : activer
# l'audience instrumentait le site a moitie, et l'evenement « Ajout agenda »
# n'aurait jamais rien compte puisque le lien .ics ne vit que sur ces pages.
# Bascule d'un seul geste : python .claude/set-analytics.py --on
# Le meme bloc que dans .claude/set-analytics.py, pour les 12 pages
# generees. Les deux sources doivent rester identiques : une page sans
# balise est une page invisible dans les rapports, et rien ne le signale.
ANALYTICS = u"\n".join([
    '<!-- Google Analytics 4 (G-4C00VET9W9) — Consent Mode BASIQUE.',
    "     Rien n'est charge tant que le visiteur n'a pas accepte : pas de",
    '     gtag.js, pas de requete, pas de ping anonyme. Ce bloc ne fait que',
    "     definir mbcChargerGA() et l'appeler si un accord est deja memorise,",
    "     pour que la mesure reprenne des la premiere page d'une visite",
    "     suivante. C'est consent.js qui l'appelle au clic sur Accepter.",
    '     Les trois consentements publicitaires restent refuses en toutes',
    "     circonstances : le club n'utilise pas Google Ads. -->",
    '<script>',
    "window.MBC_GA_ID='G-4C00VET9W9';",
    'window.mbcChargerGA=function(){',
    '  if(window.MBC_GA_ON){return;}window.MBC_GA_ON=true;',
    '  window.dataLayer=window.dataLayer||[];',
    '  window.gtag=function(){window.dataLayer.push(arguments);};',
    "  gtag('consent','default',{'analytics_storage':'denied','ad_storage':'denied','ad_user_data':'denied','ad_personalization':'denied'});",
    "  gtag('consent','update',{'analytics_storage':'granted'});",
    "  gtag('js',new Date());",
    "  gtag('config',window.MBC_GA_ID);",
    "  var s=document.createElement('script');s.async=true;",
    "  s.src='https://www.googletagmanager.com/gtag/js?id='+window.MBC_GA_ID;",
    '  document.head.appendChild(s);',
    '};',
    "try{var c=localStorage.getItem('mbc-consent');if(c==='accepted'||c==='granted'){window.mbcChargerGA();}}catch(e){}",
    '</script>',
    '<script defer src="/consent.js"></script>',
    '<!-- /Google Analytics 4 -->',
])


SOCIALE_DEFAUT = "assets/images/social-preview.png"


def dimensions(chemin):
    """(largeur, hauteur, type MIME) d'une image du depot, ou None.

    Les 12 pages ecrites a la main declarent og:image:width et og:image:height ;
    les 12 pages generees ne le faisaient pas. Sans ces deux balises, Facebook
    et WhatsApp doivent d'abord telecharger l'image pour connaitre son format,
    et affichent frequemment un lien nu le temps de le faire.

    On lit le fichier plutot que de recopier une valeur du JSON : l'affiche
    d'un match ne fait pas le meme format que l'image sociale par defaut
    (1080x1350 contre 1200x630), et le cran le plus large d'un article
    d'actualite ne fait pas la taille annoncee par son champ « largeur ».
    Pillow est deja utilise par quatre autres generateurs ; s'il manquait, on
    se contente d'omettre les deux balises plutot que d'echouer.
    """
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(chemin) as im:
            return (im.size[0], im.size[1],
                    {"PNG": "image/png", "JPEG": "image/jpeg",
                     "WEBP": "image/webp"}.get(im.format))
    except Exception:
        return None


def page_web(titre, description, url, image_absolue):
    """Le noeud WebPage que portent deja les 12 pages ecrites a la main.

    Il raccroche la page aux deux entites declarees une seule fois, sur
    l'accueil : #website pour le site, #club pour le club. Sans lui, une fiche
    de match etait un document orphelin aux yeux d'un moteur — il voyait un fil
    d'Ariane et un evenement, jamais a quel site ils appartenaient.
    """
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": url + "#webpage",
        "url": url,
        "name": titre,
        "description": description,
        "inLanguage": "fr-RE",
        "isPartOf": {"@id": SITE + "/#website"},
        "about": {"@id": SITE + "/#club"},
        "primaryImageOfPage": image_absolue,
    }


def tete(titre, description, url, jsonlds, prof=2, image=None, image_alt=None):
    """<head> commun.

    `prof`      profondeur du dossier, pour les preloads de police en chemin
                relatif (matchs/ = 1, matchs/<slug>/ = 2).
    `image`     chemin, depuis la racine du depot, de l'image de partage.
                Par defaut l'image sociale du club.
    `image_alt` sa description, pour og:image:alt.
    """
    rel = "../" * prof
    chemin_img = image or SOCIALE_DEFAUT
    image_absolue = SITE + "/" + chemin_img
    jsonlds = [page_web(titre, description, url, image_absolue)] + list(jsonlds)
    blocs = "\n".join('<script type="application/ld+json">%s</script>' % jsonld(j) for j in jsonlds)

    dim = dimensions(chemin_img)
    lignes = ['<meta property="og:image" content="%s">' % image_absolue]
    if dim:
        if dim[2]:
            lignes.append('<meta property="og:image:type" content="%s">' % dim[2])
        lignes.append('<meta property="og:image:width" content="%d">' % dim[0])
        lignes.append('<meta property="og:image:height" content="%d">' % dim[1])
    lignes.append('<meta property="og:image:alt" content="%s">'
                  % ech(image_alt or u"MBC La Montagne Basket Club"))
    balises_img = "\n".join(lignes)
    return u"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(titre)s</title>
<meta name="description" content="%(desc)s">
<meta name="author" content="MBC La Montagne Basket Club">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="theme-color" content="#0D1526">
<meta name="color-scheme" content="dark">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="geo.region" content="RE">
<meta name="geo.placename" content="La Montagne, Saint-Denis, La Réunion">
<link rel="canonical" href="%(url)s">

<meta property="og:type" content="website">
<meta property="og:site_name" content="MBC La Montagne Basket Club">
<meta property="og:title" content="%(titre)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(url)s">
<meta property="og:locale" content="fr_FR">
%(balisesImage)s

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(titre)s">
<meta name="twitter:description" content="%(desc)s">
<meta name="twitter:image" content="%(image)s">

<link rel="icon" type="image/png" href="/assets/icons/favicon.png">
<link rel="apple-touch-icon" href="/assets/icons/favicon.png">
<link rel="manifest" href="/site.webmanifest">

<link rel="preload" as="font" type="font/woff2" crossorigin
      href="%(rel)sassets/fonts/anton-400-latin.woff2">
<link rel="preload" as="font" type="font/woff2" crossorigin
      href="%(rel)sassets/fonts/barlow-condensed-700-latin.woff2">
<link rel="stylesheet" href="/style.min.css?v=%(v)s">

%(jsonld)s
%(analytics)s
</head>
<body>

<a class="skip-link" href="#contenu">Aller au contenu principal</a>
""" % {"titre": ech(titre), "desc": ech(description), "url": url, "rel": rel,
       "v": VERSION_CSS, "jsonld": blocs, "analytics": ANALYTICS,
       "balisesImage": balises_img, "image": image_absolue}


def fil(elements):
    """Fil d'Ariane visible + son JSON-LD."""
    liens = []
    for i, (nom, href) in enumerate(elements):
        if href and i < len(elements) - 1:
            liens.append('<a href="%s">%s</a>' % (href, ech(nom)))
        else:
            liens.append('<span aria-current="page">%s</span>' % ech(nom))
    visible = ('<nav class="fil" aria-label="Fil d\'Ariane">\n      %s\n    </nav>'
               % '<i aria-hidden="true"></i>'.join(liens))
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList",
          "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "name": nom,
               "item": (SITE + href if href and href.startswith("/") else href) if href else None}
              for i, (nom, href) in enumerate(elements)]}
    for it in ld["itemListElement"]:
        if it["item"] is None:
            del it["item"]
    return visible, ld


# --------------------------------------------------------------------------
# Donnees structurees d'une rencontre
# --------------------------------------------------------------------------
# Le champ « statut » de data/matchs.json existe depuis l'origine et sert deja
# a ecarter les rencontres annulees du bandeau « prochain match ». Le
# SportsEvent, lui, publiait EventScheduled quoi qu'il arrive : un match annule
# aurait continue d'annoncer aux moteurs qu'il se tenait. On fait la
# correspondance ici. Un match joue reste EventScheduled : schema.org n'a pas
# d'etat « termine », l'evenement a bien eu lieu comme prevu.
STATUT_SCHEMA = {
    "a-venir": "https://schema.org/EventScheduled",
    "joue": "https://schema.org/EventScheduled",
    "annule": "https://schema.org/EventCancelled",
    "reporte": "https://schema.org/EventPostponed",
}


def event(m, d):
    """SportsEvent — uniquement quand le lieu est connu.

    Un match en deplacement se joue « chez l'adversaire » : sans nom de salle
    ni adresse, un Event serait incomplet et Search Console le signalerait.
    On n'en genere donc pas, conformement a la regle « pas de donnees
    structurees quand les donnees manquent »."""
    if not m["_lieu"]:
        return None
    L, club, comp = m["_lieu"], d["club"], m["_comp"]
    ev = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "@id": m["_url"] + "#event",
        "name": u"%s – %s (%s, %s)" % (club["nom"], m["adversaire"], comp["nom"], m["_etiquette"]),
        "description": (u"%s de %s : le %s reçoit %s au %s, à %s (%s), le %s à %s.%s"
                        % (m["_etiquette"], comp["nom"], club["nom"], m["adversaire"], L["nom"],
                           L["ville"], L["region"], m["_dateLongue"], m["_heureFr"],
                           u" Entrée libre." if m["entreeLibre"] else "")),
        "url": m["_url"],
        "startDate": m["_debutIso"],
        "endDate": m["_finIso"],
        "eventStatus": STATUT_SCHEMA.get(m.get("statut"),
                                        "https://schema.org/EventScheduled"),
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "sport": "Basketball",
        "location": {
            "@type": "Place",
            "name": L["nom"],
            "address": {"@type": "PostalAddress", "streetAddress": L["adresse"],
                        "addressLocality": L["ville"], "postalCode": L["codePostal"],
                        "addressRegion": L["region"], "addressCountry": L["pays"]},
            "geo": {"@type": "GeoCoordinates", "latitude": L["latitude"], "longitude": L["longitude"]},
            "hasMap": L["carte"],
        },
        # @id : c'est LE club declare sur l'accueil, pas un homonyme. Sans
        # identifiant, un moteur voyait huit organisations differentes.
        #
        # Et @type SportsClub, comme l'accueil : un meme @id ne peut pas
        # changer de type selon la page qui le cite. Le site melangeait neuf
        # « SportsClub » et dix « SportsOrganization » pour cette seule entite.
        "organizer": {"@id": SITE + "/#club", "@type": "SportsClub",
                      "name": club["nom"], "url": club["url"]},
        "performer": [
            {"@type": "SportsTeam", "name": club["nom"], "sport": "Basketball", "url": club["url"]},
            {"@type": "SportsTeam", "name": m["adversaire"], "sport": "Basketball"},
        ],
        "homeTeam": {"@type": "SportsTeam", "name": club["nom"] if m["domicile"] else m["adversaire"]},
        "awayTeam": {"@type": "SportsTeam", "name": m["adversaire"] if m["domicile"] else club["nom"]},
        "image": [SITE + "/" + (m["affiche"] or SOCIALE_DEFAUT)],
    }
    if m["entreeLibre"]:
        ev["isAccessibleForFree"] = True
        ev["offers"] = {"@type": "Offer", "price": "0", "priceCurrency": "EUR",
                        "availability": "https://schema.org/InStock", "url": m["_url"]}
    return ev


# --------------------------------------------------------------------------
# Fichier .ics
# --------------------------------------------------------------------------
def _ics_heure(iso):
    """« 2026-09-11T20:30:00+04:00 » -> « 20260911T203000 ».

    L'heure locale, SANS decalage : c'est la forme imposee par la RFC 5545 des
    lors que la propriete porte un TZID. Ecrire « ...T203000+0400 » a cote de
    TZID=Indian/Reunion donne une date que la moitie des agendas refusent et
    que l'autre moitie interprete a sa facon. Le decalage est retire AVANT les
    separateurs : une fois les deux-points supprimes, « +04:00 » n'existe plus
    dans la chaine et un replace sur ce motif ne trouverait rien."""
    return iso.split("+")[0].split("Z")[0].replace("-", "").replace(":", "")


def _ics_txt(s):
    """Echappement des valeurs TEXT : la virgule et le point-virgule separent
    des valeurs en iCalendar, la barre oblique inverse echappe."""
    return (s.replace("\\", "\\\\").replace(";", "\\;")
             .replace(",", "\\,").replace("\n", "\\n"))


def _ics_plier(ligne):
    """Repli a 75 octets, la limite de la RFC. La suite d'une ligne commence
    par une espace ; on coupe sur les octets UTF-8, pas sur les caracteres,
    en veillant a ne pas scinder un caractere en deux."""
    b = ligne.encode("utf-8")
    if len(b) <= 75:
        return ligne
    morceaux, reste = [], b
    limite = 75
    while len(reste) > limite:
        coupe = limite
        while coupe > 0 and (reste[coupe] & 0xC0) == 0x80:   # milieu d'un caractere
            coupe -= 1
        morceaux.append(reste[:coupe].decode("utf-8"))
        reste = reste[coupe:]
        limite = 74            # les suivantes portent une espace en tete
    morceaux.append(reste.decode("utf-8"))
    return "\r\n ".join(morceaux)


def ics(m, d):
    if not m["_lieu"]:
        return None
    L = m["_lieu"]
    lieu = u"%s, %s, %s %s" % (L["nom"], L["adresse"], L["codePostal"], L["ville"])
    lignes = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MBC La Montagne Basket Club//FR",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        "BEGIN:VTIMEZONE", "TZID:Indian/Reunion", "BEGIN:STANDARD",
        "DTSTART:19700101T000000", "TZOFFSETFROM:+0400", "TZOFFSETTO:+0400",
        "TZNAME:+04", "END:STANDARD", "END:VTIMEZONE",
        "BEGIN:VEVENT",
        "UID:%s@mbc974.com" % m["slug"],
        "DTSTAMP:%sZ" % datetime(2026, 9, 1).strftime("%Y%m%dT%H%M%S"),
        "DTSTART;TZID=Indian/Reunion:%s" % _ics_heure(m["_debutIso"]),
        "DTEND;TZID=Indian/Reunion:%s" % _ics_heure(m["_finIso"]),
        u"SUMMARY:%s" % _ics_txt(u"%s — %s (%s)" % (d["club"]["court"],
                                                    m["adversaireCourt"], m["_etiquette"])),
        u"LOCATION:%s" % _ics_txt(lieu),
        u"DESCRIPTION:%s" % _ics_txt(
            m["_comp"]["nom"] + (u" — entrée libre." if m["entreeLibre"] else u".")),
        "URL:%s" % m["_url"],
        "END:VEVENT", "END:VCALENDAR", ""]
    return u"\r\n".join(_ics_plier(l) for l in lignes)


VERSION_CSS = "0"
GABARIT = None


# --------------------------------------------------------------------------
# Le bandeau « prochain match », juste sous le hero
# --------------------------------------------------------------------------
def ecusson_nx(logo, sigle):
    """Petit ecusson du bandeau « prochain match », meme logo que le duel de la
    fiche (ecusson) mais en case reduite, taillee sur la police du titre."""
    if not logo:
        return u'<span class="nx__crest nx__crest--sigle" aria-hidden="true">%s</span>' % ech(sigle)
    return (u'<span class="nx__crest" aria-hidden="true"><img '
            u'src="/assets/logos/clubs/%s-144.webp" '
            u'srcset="/assets/logos/clubs/%s-144.webp 144w, /assets/logos/clubs/%s.webp 288w" '
            u'sizes="40px" alt="" width="288" height="288" loading="lazy" decoding="async">'
            u'</span>') % (logo, logo, logo)


ECUSSON_MBC_NX = (u'<span class="nx__crest" aria-hidden="true"><img '
                  u'src="/assets/logos/mbc-logo.webp" alt="" width="288" height="296" '
                  u'loading="lazy" decoding="async"></span>')


def bandeau(m, d):
    """Volontairement une BANDE, pas une section : le hero doit rester le
    premier ecran. Elle ne porte AUCUNE donnee structuree — la source de verite
    de l'evenement est sa page dediee, et dupliquer l'Event ici donnerait deux
    URL pour un meme match."""
    if not m:
        return (u"<!-- PROCHAIN-MATCH:DEBUT -->\n"
                u"<!-- Aucune rencontre a venir dans data/matchs.json. -->\n"
                u"<!-- PROCHAIN-MATCH:FIN -->")
    L = m["_lieu"]
    lieu = L["nom"] if L else u"Chez l'adversaire"
    club = d["club"]
    # « Itineraire » et « Entree libre » sont TOUJOURS ecrits, masques par
    # l'attribut hidden quand ils ne s'appliquent pas (rencontre en
    # deplacement). Raison : le bandeau se reconstruit tout seul cote client
    # quand la rencontre annoncee est passee — il bascule alors de la ligne
    # suivante du calendrier. Un element absent du DOM ne peut pas etre
    # reaffiche ; un element present et masque, si. On ne montre donc jamais
    # une information fausse, et on n'en perd aucune entre deux publications.
    gym = d["lieux"].get("gymnase") or {}
    carte = (L or gym).get("carte", "")
    itineraire = (u'<a class="nx__second" href="%s" target="_blank" rel="noopener"%s>Itinéraire'
                  u'<span class="sr-only"> vers %s (Google Maps, nouvel onglet)</span></a>'
                  ) % (carte, u"" if L else u" hidden", ech(lieu if L else gym.get("nom", "")))
    crest_adv = ecusson_nx(m["logo"], m["sigle"])
    crest_dom = ECUSSON_MBC_NX if m["domicile"] else crest_adv
    crest_ext = crest_adv if m["domicile"] else ECUSSON_MBC_NX
    return u"""<!-- PROCHAIN-MATCH:DEBUT — genere par .claude/build-matchs.py, ne pas editer a la main -->
<section class="nx" id="nxBand" aria-labelledby="nxBandTitle" data-debut="%(iso)s" data-fin="%(finIso)s">
  <div class="wrap nx__in">
    <p class="nx__eyebrow"><span class="nx__dot" aria-hidden="true"></span>Prochain match <i aria-hidden="true"></i>%(etiq)s</p>
    <h2 class="nx__t" id="nxBandTitle"><span class="nx__club">%(crestDom)s%(dom)s</span><span class="nx__vs" aria-hidden="true">vs</span><span class="nx__opp">%(crestExt)s%(ext)s</span></h2>
    <p class="nx__meta"><time datetime="%(iso)s">%(dateLongue)s <i aria-hidden="true"></i> %(heure)s</time><span class="nx__ou">%(lieu)s</span>%(libre)s</p>
    <p class="nx__cd" id="nxCountdown" hidden></p>
    <p class="nx__a"><a class="btn btn--primary" href="/matchs/%(slug)s/">Voir le match%(fleche)s</a>%(itineraire)s</p>
  </div>
</section>
<!-- PROCHAIN-MATCH:FIN -->""" % {
        "etiq": ech(m["_etiquette"]),
        "dom": ech(club["court"] if m["domicile"] else m["adversaireCourt"]),
        "ext": ech(m["adversaireCourt"] if m["domicile"] else club["court"]),
        "crestDom": crest_dom,
        "crestExt": crest_ext,
        "iso": m["_debutIso"],
        # data-fin : l'instant ABSOLU du coup de sifflet final, fuseau compris.
        #
        # Ce bandeau etait le seul bloc « prochain match » de la home a ne pas
        # savoir se perimer. Le scoreboard plus bas, lui, portait deja un
        # data-match-date et disparaissait tout seul — mais c'est CELUI-CI que
        # l'on voit en premier, juste sous le hero. Le 12 septembre au matin il
        # aurait donc continue d'annoncer « Prochain match J1, vendredi 11
        # septembre », jusqu'a la prochaine execution d'un script.
        #
        # On publie l'instant plutot que la date seule pour deux raisons : le
        # match se termine a 23h00 et non a minuit, et un supporter qui lit le
        # site depuis la metropole doit voir exactement ce que voit un
        # supporter a La Montagne.
        "finIso": m["_finIso"],
        "dateLongue": ech(m["_dateLongue"][0].upper() + m["_dateLongue"][1:]),
        "heure": m["_heureFr"],
        "lieu": ech(lieu),
        "libre": (u'<span class="nx__libre"%s>Entrée libre</span>'
                  % (u"" if m["entreeLibre"] else u" hidden")),
        "slug": m["slug"],
        "fleche": FLECHE,
        "itineraire": itineraire,
    }


def score_texte(m):
    """Le score du point de vue du MBC, ou None. Forme unique :
    {"mbc": 72, "adverse": 65} — celle que produit le PDF de la ligue via
    .claude/lire-calendrier-prm.py. Rien n'est devine : pas de score dans la
    source, pas de score sur le site."""
    s = m.get("score")
    if not s:
        return None
    if not isinstance(s, dict) or "mbc" not in s or "adverse" not in s:
        raise ValueError(
            "data/matchs.json, %s : le champ score doit valoir null ou "
            '{"mbc": <entier>, "adverse": <entier>}, pas %r' % (m["slug"], s))
    return (int(s["mbc"]), int(s["adverse"]))


def issue(pour, contre):
    """v / d / n, et le mot correspondant, pour les lecteurs d'ecran."""
    if pour > contre:
        return "v", u"Victoire"
    if pour < contre:
        return "d", u"D\u00e9faite"
    return "n", u"Match nul"


FLECHE = (u'<svg class="btn__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
          u'stroke-width="2.4" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" '
          u'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def ecusson(logo, nom, sigle, taille="(max-width:800px) 48px, 80px"):
    if not logo:
        return u'<span class="mp__crest mp__crest--sigle">%s</span>' % ech(sigle)
    return (u'<span class="mp__crest"><img src="/assets/logos/clubs/%s-144.webp" '
            u'srcset="/assets/logos/clubs/%s-144.webp 144w, /assets/logos/clubs/%s.webp 288w" '
            u'sizes="%s" alt="Écusson %s" width="288" height="288" loading="lazy" '
            u'decoding="async"></span>') % (logo, logo, logo, taille, ech(nom))


ECUSSON_MBC = (u'<span class="mp__crest"><img src="/assets/logos/mbc-logo.webp" '
               u'alt="Écusson MBC La Montagne" width="288" height="296" loading="lazy" '
               u'decoding="async"></span>')


# --------------------------------------------------------------------------
# Une page de rencontre
# --------------------------------------------------------------------------
def page_match(m, d, precedent, suivant):
    club, comp = d["club"], m["_comp"]
    L = m["_lieu"]
    lieu = L["nom"] if L else u"Chez l'adversaire"
    lieu_phrase = L["nom"] if L else u"chez l’adversaire"      # au milieu d'une phrase
    _sc = score_texte(m)
    # Le depot suit une regle de titres <= 52 caracteres : au-dela, le libelle
    # est tronque dans les resultats mobiles, ou le CTR mesure etait moitie
    # moindre a position egale. La date longue avec le jour de la semaine et
    # l'heure faisait monter ces titres a 61-71 caracteres ; la date courte
    # suffit, l'heure vit dans la description et dans le SportsEvent.
    titre = u"%s · %d %s %d — MBC974" % (m["_titre"], m["_dt"].day,
                                         MOIS_COURT[m["_dt"].month - 1], m["_dt"].year)
    if _sc:
        # Une rencontre jouee se decrit par son resultat : c'est ce que cherche
        # celui qui tape « MBC Sainte-Suzanne » le lendemain du match.
        # Apres « victoire du MBC », les chiffres du MBC d'abord, quel que soit
        # le camp : « victoire du MBC 60–70 » se lisait comme une defaite.
        _cls = issue(_sc[0], _sc[1])[0]
        desc = (u"%s, %s de %s : %s %d–%d, %s, %s."
                % (m["_titre"], m["_etiquette"], comp["nom"],
                   {"v": u"victoire du MBC", "d": u"défaite du MBC", "n": u"match nul"}[_cls],
                   _sc[0], _sc[1], m["_dateLongue"], lieu_phrase))
    else:
        desc = (u"%s, %s de %s : %s à %s, %s. %s"
                % (m["_titre"], m["_etiquette"], comp["nom"], m["_dateLongue"], m["_heureFr"], lieu_phrase,
                   u"Entrée libre." if m["entreeLibre"] else u"Rencontre en déplacement."))

    visible, ld_fil = fil([(u"Accueil", "/"), (u"Matchs", "/matchs/"), (m["_titre"], None)])
    lds = [ld_fil]
    ev = event(m, d)
    if ev:
        lds.append(ev)

    duel_adv = ecusson(m["logo"], m["adversaire"], m["sigle"])
    duel = ((ECUSSON_MBC + u'<span class="mp__x" aria-hidden="true">vs</span>' + duel_adv)
            if m["domicile"] else
            (duel_adv + u'<span class="mp__x" aria-hidden="true">vs</span>' + ECUSSON_MBC))

    pratique = []
    if L:
        pratique.append((u"Adresse", u"%s<br>%s %s" % (ech(L["adresse"]), L["codePostal"], ech(L["ville"]))))
    pratique.append((u"Coup d’envoi", u"%s à %s" % (ech(m["_dateLongue"]), m["_heureFr"])))
    if _sc:
        # Meme regle que la description : « Victoire du MBC, 70–60 ».
        pratique.append((u"Résultat", u"%s, %d–%d"
                         % ({"v": u"Victoire du MBC", "d": u"Défaite du MBC",
                             "n": u"Match nul"}[issue(_sc[0], _sc[1])[0]], _sc[0], _sc[1])))
    # La zone ne vaut que pour la phase 1 : les divisions 1 et 2 melent les
    # poules Nord et Sud (reglement, art. 3). Ensuite, on nomme la phase.
    _extra = (comp.get("zone") if (m.get("phase") or "brassage") == "brassage"
              else ((d.get("phases") or {}).get(m.get("phase") or "") or {}).get("nom"))
    pratique.append((u"Compétition", u" — ".join(ech(x) for x in (comp["nom"], _extra) if x)))
    pratique.append((u"Sens", u"À domicile" if m["domicile"] else u"En déplacement"))
    if m["entreeLibre"]:
        pratique.append((u"Entrée", u"Libre, sans réservation"))

    benev = u""
    if m["benevoles"]:
        postes = u"".join(u"<li>%s</li>" % ech(p) for p in m["benevoles"])
        # L'etiquette commune (« J3 », « 2e phase · J1 aller », le tour d'une
        # Coupe) : une rencontre sans numero de journee faisait planter ici
        # toute la chaine.
        from urllib.parse import quote
        sujet = quote(u"Bénévolat - match %s" % m["_etiquette"], safe="")
        benev = (u"\n        <section class=\"mp__bloc\" aria-labelledby=\"mpBen\">\n"
                 u"          <h2 class=\"mp__h2\" id=\"mpBen\">Donner un coup de main</h2>\n"
                 u"          <p>Un match à domicile ne tient pas tout seul : il faut une table de "
                 u"marque et quelqu’un pour accueillir. Aucune expérience requise, le club "
                 u"forme sur place.</p>\n"
                 u"          <ul class=\"mp__postes\">%s</ul>\n"
                 u"          <p><a class=\"mp__lien\" href=\"mailto:contact@mbc974.com?subject=%s\">"
                 u"Se proposer pour un poste%s</a></p>\n"
                 u"        </section>") % (postes, sujet, FLECHE)

    affiche = u""
    if m["affiche"]:
        affiche = (u'\n      <p class="mp__affiche"><a href="/%s" target="_blank" rel="noopener">'
                   u'Voir l’affiche du match<span class="sr-only"> en grand (nouvel onglet)</span>'
                   u'</a></p>') % m["affiche"]

    actions = []
    # Apres le coup de sifflet final, ni itineraire ni agenda : le score les remplace.
    if L and not _sc:
        actions.append(u'<a class="btn btn--primary" href="%s" target="_blank" rel="noopener">'
                       u'Itinéraire<span class="sr-only"> vers %s (Google Maps, nouvel onglet)'
                       u'</span></a>' % (L["carte"], ech(lieu)))
        actions.append(u'<a class="btn btn--ghost" href="/assets/documents/%s.ics" download>'
                       u'Ajouter au calendrier<span class="sr-only"> (fichier .ics)</span></a>'
                       % m["slug"])

    voisins = []
    if precedent:
        voisins.append(u'<a class="mp__prec" href="/matchs/%s/"><span>%s</span>%s</a>'
                       % (precedent["slug"], ech(precedent["_etiquetteLongue"]), ech(precedent["_titre"])))
    if suivant:
        voisins.append(u'<a class="mp__suiv" href="/matchs/%s/"><span>%s</span>%s</a>'
                       % (suivant["slug"], ech(suivant["_etiquetteLongue"]), ech(suivant["_titre"])))

    # Le resultat, en tete de fiche : c'est LA reponse qu'on vient chercher sur
    # la page d'un match joue. Lu en toutes lettres par un lecteur d'ecran.
    score_html = u""
    if _sc:
        _cls = issue(_sc[0], _sc[1])[0]
        _lib = {"v": u"Victoire du MBC", "d": u"Défaite du MBC", "n": u"Match nul"}[_cls]
        # A l'ecran, les chiffres suivent le duel juste au-dessus (recevant
        # d'abord). Le lecteur d'ecran entend une phrase complete, du point de
        # vue du MBC : « Victoire du MBC, 70 à 60 contre Dionysien 3. »
        _dit = ((u"Match nul, %d à %d contre %s." if _cls == "n" else _lib + u", %d à %d contre %s.")
                % (_sc[0], _sc[1], m["adversaireCourt"]))
        score_html = (u'\n      <p class="mp__score mp__score--%s"><span class="sr-only">%s</span>'
                      u'<span class="mp__score__n" aria-hidden="true">%d</span><span class="mp__score__s" aria-hidden="true">–</span>'
                      u'<span class="mp__score__n" aria-hidden="true">%d</span>'
                      u'<span class="mp__score__l" aria-hidden="true">%s</span></p>'
                      % (_cls, ech(_dit), _sc[0] if m["domicile"] else _sc[1],
                         _sc[1] if m["domicile"] else _sc[0], _lib))

    corps = u"""<main id="contenu">
  <article class="section mp">
    <div class="wrap">
      %(fil)s
      <p class="mp__eyebrow">%(comp)s <i aria-hidden="true"></i> %(etiqL)s</p>
      <h1 class="mp__h1">%(dom)s <span class="mp__vs">vs</span> %(ext)s</h1>
      <div class="mp__duel" aria-hidden="true">%(duel)s</div>%(score)s
      <p class="mp__quand"><time datetime="%(iso)s">%(dateLongue)s <i aria-hidden="true"></i> %(heure)s</time></p>
      <p class="mp__ou">%(lieu)s <span class="mp__cote">%(cote)s</span></p>%(libre)s
      <p class="mp__a">%(actions)s</p>%(affiche)s

      <div class="mp__corps">
        <p class="mp__intro">%(intro)s</p>

        <section class="mp__bloc" aria-labelledby="mpPratique">
          <h2 class="mp__h2" id="mpPratique">Informations pratiques</h2>
          <dl class="mp__dl">%(pratique)s</dl>
        </section>%(benev)s
      </div>

      <nav class="mp__nav" aria-label="Autres rencontres">%(voisins)s</nav>
      <p class="mp__retour"><a href="/matchs/">Toutes les rencontres de la saison%(fleche)s</a></p>
    </div>
  </article>
</main>""" % {
        "fil": visible, "comp": ech(comp["nom"]), "etiqL": ech(m["_etiquetteLongue"]),
        "score": score_html,
        "dom": ech(club["court"] if m["domicile"] else m["adversaireCourt"]),
        "ext": ech(m["adversaireCourt"] if m["domicile"] else club["court"]),
        "duel": duel, "iso": m["_debutIso"],
        "dateLongue": ech(m["_dateLongue"][0].upper() + m["_dateLongue"][1:]),
        "heure": m["_heureFr"], "lieu": ech(lieu),
        "cote": u"À domicile" if m["domicile"] else u"En déplacement",
        "libre": u'\n      <p class="mp__libre">Entrée libre</p>' if m["entreeLibre"] and not _sc else u"",
        "actions": u"\n        ".join(actions),
        "affiche": affiche, "intro": ech(m["intro"]),
        "pratique": u"".join(u"<div><dt>%s</dt><dd>%s</dd></div>" % (k, v) for k, v in pratique),
        "benev": benev, "voisins": u"".join(voisins), "fleche": FLECHE,
    }
    entete, cta, pied, scripts = GABARIT
    # L'IMAGE DE PARTAGE, par ordre de preference :
    #   1. l'affiche officielle de la rencontre, quand le club en a fait une ;
    #   2. la carte dessinee par .claude/build-og-matchs.py depuis ce meme
    #      fichier de donnees — adversaire, date, heure, lieu, entree libre,
    #      et le score des qu'il est publie ;
    #   3. la banniere generique du site, en tout dernier recours.
    #
    # Avant le point 2, SIX fiches sur sept partageaient la meme banniere : un
    # lien colle dans une conversation WhatsApp ne disait ni contre qui, ni
    # quand, ni ou — sur la page qu'on partage justement le vendredi soir.
    og = "assets/og/og-%s.jpg" % m["slug"]
    if not os.path.exists(os.path.join(RACINE, og)):
        og = None
    # Une rencontre jouee se partage avec son score : la carte dessinee le porte,
    # l'affiche d'avant-match non.
    partage = (og or m["affiche"]) if _sc else (m["affiche"] or og)
    if _sc:
        # L'image d'une rencontre jouee porte le score (build-og-matchs.py) : son
        # texte de remplacement le dit, dans l'ordre de l'image.
        _alt = (u"%s : %d–%d, %s" % (
            m["_titre"], _sc[0] if m["domicile"] else _sc[1], _sc[1] if m["domicile"] else _sc[0],
            {"v": u"victoire du MBC", "d": u"défaite du MBC", "n": u"match nul"}[issue(_sc[0], _sc[1])[0]]))
    else:
        _alt = (u"%s, %s à %s — %s" % (m["_titre"], m["_dateLongue"], m["_heureFr"],
                                        (m["_lieu"] or {}).get("nom", u"chez l’adversaire")))
    return (tete(titre, desc, m["_url"], lds, prof=2,
                 image=partage,
                 image_alt=_alt if partage else None)
            + entete + u"\n\n" + cta + u"\n\n" + corps + u"\n\n" + pied
            + u"\n\n" + scripts + u"</body>\n</html>\n")


# --------------------------------------------------------------------------
# La page /matchs/ : le Match Center complet
# --------------------------------------------------------------------------
_MC = None


def match_center():
    """.claude/build-match-center.py, charge une fois. C'est lui qui rend la
    saison (rencontres confirmees + echeances) ; ce fichier-ci l'enveloppe du
    gabarit du site et y ajoute les donnees structurees."""
    global _MC
    if _MC is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "match_center", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "build-match-center.py"))
        _MC = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_MC)
    return _MC


# /matchs/ charge script.js, comme /creneaux/ : les filtres et la bascule du
# prochain match a l'heure de La Reunion SONT la page. Le module en ligne qui
# vivait ici (« RECLASSEMENT » : il deplacait les cartes perimees entre deux
# listes « A venir » / « Deja joues ») est remplace par le bloc commun V181 de
# script.js — le garder aurait fait deux logiques du temps pour une page.
SCRIPT_JS = u"""<!-- Comme /creneaux/, cette page charge script.js : les filtres et la bascule
     automatique du prochain match (bloc V181) SONT la page. C'est le fichier de
     l'accueil, donc deja en cache. bump-assets.py y pose le ?v= tout seul. -->
<script src="/script.js?v=%s" defer></script>
"""
VERSION_JS = "0"


def page_liste(d, maintenant=None):
    mc = match_center()
    maintenant = maintenant or mc.maintenant()
    comp = d["competition"]
    visible, ld_fil = fil([(u"Accueil", "/"), (u"Matchs", None)])
    ld_liste = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": u"Calendrier %s — %s" % (comp["nom"], comp["saison"]),
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "numberOfItems": len(d["matchs"]),
        "itemListElement": [{"@type": "ListItem", "position": i + 1,
                             "name": m["_titre"], "url": m["_url"]}
                            for i, m in enumerate(d["matchs"])],
    }
    titre = u"Calendrier des matchs %s — MBC La Montagne" % comp["saison"]
    desc = (u"Résultats, prochain match et toute la saison des seniors du MBC La Montagne : "
            u"Pré-Régionale Masculine et Trophée Coupe de France. Entrée libre à domicile.")
    corps = mc.page_corps(d, mc.entrees(d), maintenant, visible)
    entete, cta, pied, scripts = GABARIT
    return (tete(titre, desc, SITE + "/matchs/", [ld_fil, ld_liste], prof=1)
            + entete + u"\n\n" + cta + u"\n\n" + corps + u"\n\n" + pied
            + u"\n\n" + scripts + SCRIPT_JS % VERSION_JS + u"</body>\n</html>\n")


# --------------------------------------------------------------------------
# La home : une ItemList, PAS des SportsEvent
# --------------------------------------------------------------------------
def liste_jsonld(d):
    """Depuis que chaque rencontre a son URL, c'est SA page qui porte le
    SportsEvent. La home n'en declare plus aucun : deux noeuds Event pour un
    meme match, sur deux URL differentes, c'est de la duplication — Google
    choisit alors lui-meme la page a montrer, et il choisit mal.

    On garde neanmoins un balisage sur la home, mais de nature differente :
    une ItemList qui ENUMERE les rencontres et pointe vers leurs pages. Elle
    ne redit rien de l'evenement (ni date, ni lieu, ni prix), elle sert de
    plan du site pour le calendrier."""
    club = d["club"]
    items = []
    for i, m in enumerate(d["matchs"], 1):
        items.append({
            "@type": "ListItem",
            "position": i,
            "name": u"%s — %s" % (m["_etiquette"], m["_titre"]),
            "url": m["_url"],
        })
    c = d["competition"]
    return u'<script type="application/ld+json">\n%s\n</script>' % jsonld({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": SITE + "/#calendrier-matchs",
        "name": u"Matchs du %s — saison %s" % (club["nom"], d.get("saison") or c["saison"]),
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "numberOfItems": len(items),
        "itemListElement": items,
    })


def main():
    global GABARIT, VERSION_CSS, VERSION_JS
    d = charger()
    GABARIT_BRUT = gabarit()
    GABARIT = GABARIT_BRUT[:4]
    VERSION_CSS = GABARIT_BRUT[4]
    VERSION_JS = re.search(r'src="/?script\.js\?v=([A-Za-z0-9._-]+)"', lire("index.html")).group(1)

    ecrits = []

    # 1. les pages de rencontre
    for i, m in enumerate(d["matchs"]):
        prec = d["matchs"][i - 1] if i > 0 else None
        suiv = d["matchs"][i + 1] if i + 1 < len(d["matchs"]) else None
        ecrire("matchs/%s/index.html" % m["slug"], page_match(m, d, prec, suiv))
        ecrits.append("matchs/%s/index.html" % m["slug"])
        cal = ics(m, d)
        if cal:
            ecrire("assets/documents/%s.ics" % m["slug"], cal)
            ecrits.append("assets/documents/%s.ics" % m["slug"])

    # 2. la liste
    ecrire("matchs/index.html", page_liste(d))
    ecrits.append("matchs/index.html")

    # 3. le bandeau sur la home
    p = os.path.join(RACINE, "index.html")
    s = io.open(p, encoding="utf-8").read()
    bloc = bandeau(prochain(d), d)
    deb, fin = "<!-- PROCHAIN-MATCH:DEBUT", "<!-- PROCHAIN-MATCH:FIN -->"
    if deb in s:
        i, j = s.index(deb), s.index(fin) + len(fin)
        s = s[:i] + bloc + s[j:]
    else:
        # premiere pose : juste apres la fermeture du hero
        ancre = s.index("</section>", s.index('<section class="hero"')) + len("</section>")
        s = s[:ancre] + "\n\n" + bloc + s[ancre:]

    # 4. le JSON-LD du calendrier : une ItemList, les Event vivent sur leurs pages
    dj, fj = "<!-- calendrier:jsonld -->", "<!-- /calendrier:jsonld -->"
    if dj in s and fj in s:
        i, j = s.index(dj) + len(dj), s.index(fj)
        s = s[:i] + "\n" + liste_jsonld(d) + "\n" + s[j:]
    else:
        print("!! marqueurs calendrier:jsonld absents de index.html")

    io.open(p, "w", encoding="utf-8", newline="").write(s)
    ecrits.append("index.html (bandeau prochain match + ItemList du calendrier)")

    # 5. le Match Center de l'accueil, qui lit la MEME source. Il est appele
    #    ici et pas a la main : un calendrier qui bouge doit bouger partout du
    #    meme coup, sinon la home affiche deux verites. C'est la lecon des
    #    trois rencontres qui avaient change de camp entre deux editions du PDF.
    #    Il remplace le « ruban de saison » (V162, build-ruban-saison.py, retire),
    #    qui ne connaissait que la phase 1 — et qui aurait plante au premier
    #    score saisi (il passait le dictionnaire du score a l'echappement HTML) :
    #    l'erreur etait avalee par un except, et la home serait restee figee
    #    sans que personne le sache. Plus d'except ici : une home perimee doit
    #    se voir au moment de la publication, pas une semaine plus tard.
    if match_center().main() != 0:
        raise SystemExit("!! Match Center de l'accueil non regenere (marqueurs MATCH-CENTER ?)")
    ecrits.append("index.html (Match Center de la saison)")

    pm = prochain(d)
    print("Source        : data/matchs.json (%d rencontres)" % len(d["matchs"]))
    print("Prochain match: %s" % (("%s %s, %s" % (pm["_etiquette"], pm["_titre"], pm["_dateLongue"]))
                                  if pm else "aucun a venir"))
    print("Evenements    : %d SportsEvent, un par page de match a domicile (lieu connu)"
          % sum(1 for m in d["matchs"] if m["_lieu"]))
    print("Home          : ItemList de %d rencontres, aucun SportsEvent duplique"
          % len(d["matchs"]))
    print("\n%d fichiers ecrits :" % len(ecrits))
    for f in ecrits:
        print("   " + f)


if __name__ == "__main__":
    main()
