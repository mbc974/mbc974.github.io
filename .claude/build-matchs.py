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
  matchs/index.html                 la liste des rencontres
  matchs/<slug>/index.html          une page par rencontre (7)
  assets/documents/<slug>.ics       un rendez-vous par match a domicile
  index.html                        le bandeau « prochain match » sous le hero,
                                    entre les deux marqueurs PROCHAIN-MATCH

CE QU'IL ECRIT AUSSI DANS index.html
-----------------------------------
Le bloc « calendrier:jsonld » de la page d'accueil, qui ne contient plus des
SportsEvent mais une ItemList pointant vers les sept fiches. Un evenement se
declare sur SA page, pas deux fois sur deux URL differentes.

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
    d["matchs"].sort(key=lambda m: m["_dt"])
    return d


def prochain(d, maintenant=None):
    """Le prochain match a venir, ou None si la phase est terminee. C'est cette
    fonction qui rend le bandeau de la home reutilisable d'une journee a
    l'autre : il n'est pas code autour du 11 septembre."""
    maintenant = maintenant or datetime.now()
    futurs = [m for m in d["matchs"] if m["_dt"] >= maintenant and m["statut"] != "annule"]
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

    # La nav du modele n'offre ni Matchs ni Actualites : depuis une fiche de
    # match, le calendrier complet n'etait atteignable que par le fil d'Ariane.
    entete = entete.replace(
        '<a href="/#contact">Contact</a>',
        '<a href="/matchs/">Matchs</a><a href="/actualites/">Actualit\u00e9s</a>'
        '<a href="/#contact">Contact</a>', 1)
    pied = s[s.index('<footer class="seo-foot">'):s.index("</footer>") + len("</footer>")]
    scripts = s[s.index("<script>\n/* Barre CTA mobile"):s.index("</body>")]
    version = re.search(r'href="/style\.css\?v=([0-9a-f]+)"', s).group(1)
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


def tete(titre, description, url, jsonlds, prof=2):
    """<head> commun. `prof` = profondeur du dossier, pour les preloads de
    police en chemin relatif (matchs/ = 1, matchs/<slug>/ = 2)."""
    rel = "../" * prof
    blocs = "\n".join('<script type="application/ld+json">%s</script>' % jsonld(j) for j in jsonlds)
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
<meta property="og:image" content="%(image)s">
<meta property="og:image:alt" content="MBC La Montagne Basket Club">

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
<link rel="stylesheet" href="/style.css?v=%(v)s">

%(jsonld)s
%(analytics)s
</head>
<body>

<a class="skip-link" href="#contenu">Aller au contenu principal</a>
""" % {"titre": ech(titre), "desc": ech(description), "url": url, "rel": rel,
       "v": VERSION_CSS, "jsonld": blocs, "analytics": ANALYTICS,
       "image": SITE + "/assets/images/social-preview.png"}


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
def event(m, d):
    """SportsEvent — uniquement quand le lieu est connu.

    Un match en deplacement se joue « chez l'adversaire » : sans nom de salle
    ni adresse, un Event serait incomplet et Search Console le signalerait.
    On n'en genere donc pas, conformement a la regle « pas de donnees
    structurees quand les donnees manquent »."""
    if not m["_lieu"]:
        return None
    L, club, comp = m["_lieu"], d["club"], d["competition"]
    ev = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "@id": m["_url"] + "#event",
        "name": u"%s – %s (%s, J%d)" % (club["nom"], m["adversaire"], comp["nom"], m["journee"]),
        "description": (u"J%d de %s : le %s reçoit %s au %s, à %s (%s), le %s à %s.%s"
                        % (m["journee"], comp["nom"], club["nom"], m["adversaire"], L["nom"],
                           L["ville"], L["region"], m["_dateLongue"], m["_heureFr"],
                           u" Entrée libre." if m["entreeLibre"] else "")),
        "url": m["_url"],
        "startDate": m["_debutIso"],
        "endDate": m["_finIso"],
        "eventStatus": "https://schema.org/EventScheduled",
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
        "organizer": {"@type": "SportsOrganization", "name": club["nom"], "url": club["url"]},
        "performer": [
            {"@type": "SportsTeam", "name": club["nom"], "sport": "Basketball", "url": club["url"]},
            {"@type": "SportsTeam", "name": m["adversaire"], "sport": "Basketball"},
        ],
        "homeTeam": {"@type": "SportsTeam", "name": club["nom"] if m["domicile"] else m["adversaire"]},
        "awayTeam": {"@type": "SportsTeam", "name": m["adversaire"] if m["domicile"] else club["nom"]},
        "image": [SITE + "/" + (m["affiche"] or "assets/images/social-preview.png")],
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
        u"SUMMARY:%s" % _ics_txt(u"%s — %s (J%d)" % (d["club"]["court"],
                                                     m["adversaireCourt"], m["journee"])),
        u"LOCATION:%s" % _ics_txt(lieu),
        u"DESCRIPTION:%s" % _ics_txt(
            d["competition"]["nom"] + (u" — entrée libre." if m["entreeLibre"] else u".")),
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
    itineraire = u""
    if L:
        itineraire = (u'<a class="nx__second" href="%s" target="_blank" rel="noopener">Itineraire'
                      u'<span class="sr-only"> vers %s (Google Maps, nouvel onglet)</span></a>'
                      ) % (L["carte"], ech(lieu))
        itineraire = itineraire.replace(u"Itineraire", u"Itinéraire")
    crest_adv = ecusson_nx(m["logo"], m["sigle"])
    crest_dom = ECUSSON_MBC_NX if m["domicile"] else crest_adv
    crest_ext = crest_adv if m["domicile"] else ECUSSON_MBC_NX
    return u"""<!-- PROCHAIN-MATCH:DEBUT — genere par .claude/build-matchs.py, ne pas editer a la main -->
<section class="nx" aria-labelledby="nxBandTitle">
  <div class="wrap nx__in">
    <p class="nx__eyebrow"><span class="nx__dot" aria-hidden="true"></span>Prochain match <i aria-hidden="true"></i>J%(j)d</p>
    <h2 class="nx__t" id="nxBandTitle"><span class="nx__club">%(crestDom)s%(dom)s</span><span class="nx__vs" aria-hidden="true">vs</span><span class="nx__opp">%(crestExt)s%(ext)s</span></h2>
    <p class="nx__meta"><time datetime="%(iso)s">%(dateLongue)s <i aria-hidden="true"></i> %(heure)s</time><span class="nx__ou">%(lieu)s</span>%(libre)s</p>
    <p class="nx__a"><a class="btn btn--primary" href="/matchs/%(slug)s/">Voir le match%(fleche)s</a>%(itineraire)s</p>
  </div>
</section>
<!-- PROCHAIN-MATCH:FIN -->""" % {
        "j": m["journee"],
        "dom": ech(club["court"] if m["domicile"] else m["adversaireCourt"]),
        "ext": ech(m["adversaireCourt"] if m["domicile"] else club["court"]),
        "crestDom": crest_dom,
        "crestExt": crest_ext,
        "iso": m["_debutIso"],
        "dateLongue": ech(m["_dateLongue"][0].upper() + m["_dateLongue"][1:]),
        "heure": m["_heureFr"],
        "lieu": ech(lieu),
        "libre": u'<span class="nx__libre">Entrée libre</span>' if m["entreeLibre"] else u"",
        "slug": m["slug"],
        "fleche": FLECHE,
        "itineraire": itineraire,
    }


FLECHE = (u'<svg class="btn__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
          u'stroke-width="2.4" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" '
          u'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def ecusson(logo, nom, sigle, taille="96px"):
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
    club, comp = d["club"], d["competition"]
    L = m["_lieu"]
    lieu = L["nom"] if L else u"Chez l'adversaire"
    # Le depot suit une regle de titres <= 52 caracteres : au-dela, le libelle
    # est tronque dans les resultats mobiles, ou le CTR mesure etait moitie
    # moindre a position egale. La date longue avec le jour de la semaine et
    # l'heure faisait monter ces titres a 61-71 caracteres ; la date courte
    # suffit, l'heure vit dans la description et dans le SportsEvent.
    titre = u"%s · %d %s %d — MBC974" % (m["_titre"], m["_dt"].day,
                                         MOIS_COURT[m["_dt"].month - 1], m["_dt"].year)
    desc = (u"%s, J%d de %s : %s à %s, %s. %s"
            % (m["_titre"], m["journee"], comp["nom"], m["_dateLongue"], m["_heureFr"], lieu,
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
    pratique.append((u"Compétition", u"%s — %s" % (ech(comp["nom"]), ech(comp["zone"]))))
    pratique.append((u"Sens", u"À domicile" if m["domicile"] else u"En déplacement"))
    if m["entreeLibre"]:
        pratique.append((u"Entrée", u"Libre, sans réservation"))

    benev = u""
    if m["benevoles"]:
        postes = u"".join(u"<li>%s</li>" % ech(p) for p in m["benevoles"])
        sujet = u"B%%C3%%A9n%%C3%%A9volat%%20-%%20match%%20J%d" % m["journee"]
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
    if L:
        actions.append(u'<a class="btn btn--primary" href="%s" target="_blank" rel="noopener">'
                       u'Itinéraire<span class="sr-only"> vers %s (Google Maps, nouvel onglet)'
                       u'</span></a>' % (L["carte"], ech(lieu)))
        actions.append(u'<a class="btn btn--ghost" href="/assets/documents/%s.ics" download>'
                       u'Ajouter au calendrier<span class="sr-only"> (fichier .ics)</span></a>'
                       % m["slug"])

    voisins = []
    if precedent:
        voisins.append(u'<a class="mp__prec" href="/matchs/%s/"><span>Journée %d</span>%s</a>'
                       % (precedent["slug"], precedent["journee"], ech(precedent["_titre"])))
    if suivant:
        voisins.append(u'<a class="mp__suiv" href="/matchs/%s/"><span>Journée %d</span>%s</a>'
                       % (suivant["slug"], suivant["journee"], ech(suivant["_titre"])))

    corps = u"""<main id="contenu">
  <article class="section mp">
    <div class="wrap">
      %(fil)s
      <p class="mp__eyebrow">%(comp)s <i aria-hidden="true"></i> Journée %(j)d</p>
      <h1 class="mp__h1">%(dom)s <span class="mp__vs">vs</span> %(ext)s</h1>
      <div class="mp__duel" aria-hidden="true">%(duel)s</div>
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
        "fil": visible, "comp": ech(comp["nom"]), "j": m["journee"],
        "dom": ech(club["court"] if m["domicile"] else m["adversaireCourt"]),
        "ext": ech(m["adversaireCourt"] if m["domicile"] else club["court"]),
        "duel": duel, "iso": m["_debutIso"],
        "dateLongue": ech(m["_dateLongue"][0].upper() + m["_dateLongue"][1:]),
        "heure": m["_heureFr"], "lieu": ech(lieu),
        "cote": u"À domicile" if m["domicile"] else u"En déplacement",
        "libre": u'\n      <p class="mp__libre">Entrée libre</p>' if m["entreeLibre"] else u"",
        "actions": u"\n        ".join(actions),
        "affiche": affiche, "intro": ech(m["intro"]),
        "pratique": u"".join(u"<div><dt>%s</dt><dd>%s</dd></div>" % (k, v) for k, v in pratique),
        "benev": benev, "voisins": u"".join(voisins), "fleche": FLECHE,
    }
    entete, cta, pied, scripts = GABARIT
    return (tete(titre, desc, m["_url"], lds, prof=2)
            + entete + u"\n\n" + cta + u"\n\n" + corps + u"\n\n" + pied
            + u"\n\n" + scripts + u"</body>\n</html>\n")


# --------------------------------------------------------------------------
# La liste /matchs/
# --------------------------------------------------------------------------
def page_liste(d, maintenant=None):
    maintenant = maintenant or datetime.now()
    comp = d["competition"]
    club = d["club"]
    a_venir = [m for m in d["matchs"] if m["_dt"] >= maintenant]
    passes = [m for m in d["matchs"] if m["_dt"] < maintenant]

    def carte(m, futur):
        L = m["_lieu"]
        lieu = L["nom"] if L else u"Chez l’adversaire"
        score = u""
        if m.get("score"):
            score = u'<span class="ml__score">%s</span>' % ech(m["score"])
        return u"""        <li class="ml__i%(cls)s">
          <a class="ml__a" href="/matchs/%(slug)s/">
            <span class="ml__j">J%(j)d</span>
            <time class="ml__d" datetime="%(iso)s"><b>%(jour)s %(n)d</b><span>%(mois)s</span></time>
            <span class="ml__duel"><b>%(dom)s</b><i aria-hidden="true">vs</i><b>%(ext)s</b></span>
            <span class="ml__ou">%(lieu)s</span>
            <span class="ml__cote">%(cote)s</span>
            %(score)s
            <span class="ml__go" aria-hidden="true">%(fleche)s</span>
          </a>
        </li>""" % {
            "cls": u"" if futur else u" ml__i--passe",
            "slug": m["slug"], "j": m["journee"], "iso": m["_debutIso"],
            "jour": ech(m["_jour"][:3] + u"."), "n": m["_dt"].day,
            "mois": ech(MOIS_COURT[m["_dt"].month - 1]),
            "dom": ech(club["court"] if m["domicile"] else m["adversaireCourt"]),
            "ext": ech(m["adversaireCourt"] if m["domicile"] else club["court"]),
            "lieu": ech(lieu),
            "cote": u"À domicile" if m["domicile"] else u"En déplacement",
            "score": score, "fleche": FLECHE,
        }

    sections = []
    if a_venir:
        sections.append(u"""      <h2 class="ml__h2" id="mlVenir">À venir</h2>
      <ul class="ml" aria-labelledby="mlVenir">
%s
      </ul>""" % u"\n".join(carte(m, True) for m in a_venir))
    if passes:
        sections.append(u"""      <h2 class="ml__h2" id="mlPasses">Déjà joués</h2>
      <ul class="ml" aria-labelledby="mlPasses">
%s
      </ul>""" % u"\n".join(carte(m, False) for m in passes))

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
    desc = (u"Les %d rencontres de l’équipe seniors du MBC en %s, %s. Dates, horaires, "
            u"adversaires et lieux — entrée libre à domicile."
            % (len(d["matchs"]), comp["nom"], comp["saison"]))

    corps = u"""<main id="contenu">
  <section class="section ml-sec">
    <div class="wrap">
      %(fil)s
      <p class="kicker">%(comp)s <i aria-hidden="true"></i> %(zone)s</p>
      <h1 class="h2">Les matchs <span class="hl">de la saison</span></h1>
      <p class="sec-head__sub">%(sub)s</p>
%(sections)s
      <p class="ml__retour"><a href="/#matchs">Revenir au Match Center de l’accueil</a></p>
    </div>
  </section>
</main>""" % {"fil": visible, "comp": ech(comp["nom"]), "zone": ech(comp["zone"]),
              "sub": ech(u"%s, %s. Les rencontres à domicile se jouent au Gymnase de La "
                         u"Montagne, le vendredi à 20h30, entrée libre."
                         % (comp["phase"], comp["saison"])),
              "sections": u"\n\n".join(sections)}

    entete, cta, pied, scripts = GABARIT
    return (tete(titre, desc, SITE + "/matchs/", [ld_fil, ld_liste], prof=1)
            + entete + u"\n\n" + cta + u"\n\n" + corps + u"\n\n" + pied
            + u"\n\n" + scripts + u"</body>\n</html>\n")


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
            "name": u"J%d — %s" % (m["journee"], m["_titre"]),
            "url": m["_url"],
        })
    c = d["competition"]
    return u'<script type="application/ld+json">\n%s\n</script>' % jsonld({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": SITE + "/#calendrier-matchs",
        "name": u"Matchs du %s — %s, %s %s" % (club["nom"], c["nom"], c["phase"].lower(), c["saison"]),
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "numberOfItems": len(items),
        "itemListElement": items,
    })


def main():
    global GABARIT, VERSION_CSS
    d = charger()
    GABARIT_BRUT = gabarit()
    GABARIT = GABARIT_BRUT[:4]
    VERSION_CSS = GABARIT_BRUT[4]

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

    pm = prochain(d)
    print("Source        : data/matchs.json (%d rencontres)" % len(d["matchs"]))
    print("Prochain match: %s" % (("J%d %s, %s" % (pm["journee"], pm["_titre"], pm["_dateLongue"]))
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
