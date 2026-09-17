# -*- coding: utf-8 -*-
"""Genere tout ce qui parle du calendrier des U13, depuis data/matchs-u13.json.

POURQUOI UN GENERATEUR A PART
-----------------------------
La chaine des seniors (build-matchs.py + build-match-center.py) est
mono-equipe par construction : un seul bandeau #nxBand (un id, donc un par
page), des data-id qui sont la date seule (deux equipes jouant le meme jour
se marcheraient dessus), un bilan compte sur toutes les rencontres, des slugs
de fiche sans axe d'equipe, et set-calendrier-prm.py qui reecrit le calendrier
seniors depuis le PDF de la Ligue. Y faire entrer une deuxieme equipe, c'est
une refonte ; la doctrine du depot dit l'inverse (« eviter les refontes
inutiles si une correction ciblee suffit »).

Les U13 vivent donc a cote, avec leur propre source et leur propre
generateur — mais PAS leur propre design : ce fichier emprunte a
build-match-center.py son rendu de ligne (item), ses ecussons (crest) et ses
libelles (habiller), et a build-matchs.py le gabarit du site (en-tete, pied,
barre CTA, <head>). Une correction faite la-bas profite donc aux U13 sans
qu'on y pense.

CE QU'IL ECRIT
--------------
  matchs/u13/index.html               la page du calendrier U13 : prochaine
                                      rencontre (carte qui se renouvelle
                                      seule), les sept journees, la poule,
                                      les entrainements, les sources
  index.html                          le bloc des U13 en bas de la section
                                      « Les matchs de la saison », entre les
                                      marqueurs MATCHS-U13
  basket-enfant-saint-denis/index.html  le calendrier complet, entre les
                                      memes marqueurs
  assets/documents/matchs-u13-2026-2027.ics   les sept dates d'un coup, pour
                                      le telephone d'un parent

CE QU'IL NE TOUCHE PAS
----------------------
data/matchs.json et tout ce qui en decoule. Aucune fiche /matchs/<slug>/ n'est
creee pour les U13 : l'export de la Ligue ne donne ni salle de deplacement, ni
score, ni affiche — sept pages de plus n'auraient rien a dire de plus que leur
ligne. C'est le .ics qui rend le service, pas une URL supplementaire.

L'HEURE
-------
Comme partout sur le site : La Reunion est a UTC+4 toute l'annee, le decalage
est ecrit en dur dans chaque instant publie, et c'est la FIN de la rencontre
(coup d'envoi + duree) qui la fait basculer dans le passe.

    python .claude/build-matchs-u13.py            ecrit
    python .claude/build-matchs-u13.py --essai    n'ecrit rien, affiche le compte
    MBC_MAINTENANT=2026-10-05T09:00 python ...    simule un autre jour
"""
import io
import os
import sys
from datetime import datetime, timedelta

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://mbc974.com"
URL_PAGE = SITE + "/matchs/u13/"
SOURCE = "data/matchs-u13.json"
ICS = "assets/documents/matchs-u13-2026-2027.ics"
ARCHIVE = "assets/documents/calendrier-u13-2026-2027.png"

DEBUT = u'<!-- MATCHS-U13:DEBUT'
FIN = u'<!-- MATCHS-U13:FIN -->'

# « A suivre » sur l'accueil : trois lignes visibles, les sept ecrites. Les
# suivantes prennent le relais quand les premieres passent, sans republication
# — meme mecanique que le Match Center des seniors.
ACCUEIL_VISIBLES = 3
# Les cartes ecrites d'avance dans des <template> : de quoi tenir un mois et
# demi de dimanches sans republier la page.
GABARITS = 4


# --------------------------------------------------------------------------
# Les deux generateurs seniors, charges une fois : on leur emprunte leurs
# pieces au lieu de les recopier.
# --------------------------------------------------------------------------
_BM = None


def bm():
    global _BM
    if _BM is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "build_matchs", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "build-matchs.py"))
        _BM = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_BM)
    return _BM


def mc():
    return bm().match_center()


def lire(chemin):
    return io.open(os.path.join(RACINE, chemin), encoding="utf-8").read()


def ecrire(chemin, contenu):
    p = os.path.join(RACINE, chemin)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="").write(contenu)


# --------------------------------------------------------------------------
# Lecture et controle de la source
# --------------------------------------------------------------------------
def charger():
    """data/matchs-u13.json, verifie puis mis en forme d'entrees de saison.

    Les controles sont ceux de la chaine seniors, pour les memes raisons : un
    score saisi d'avance ou une date fantaisiste doivent arreter la
    publication, pas se retrouver en ligne."""
    import json
    d = json.loads(lire(SOURCE))
    M, C = mc(), d["competition"]
    now = M.maintenant()
    comps = {"dmu13": C}
    club, lieux = d["club"], d.get("lieux") or {}
    equipe_mbc = M.equipe(club["court"], club["nom"], club["sigle"], None, True)

    vus = set()
    es = []
    for m in d["matchs"]:
        etiq = u"J%s" % m.get("journee")
        try:
            dt = datetime.strptime(m["date"] + " " + m["heure"], "%Y-%m-%d %H:%M")
        except (KeyError, ValueError):
            raise ValueError(u"%s, %s : « date » (AAAA-MM-JJ) et « heure » (HH:MM) sont "
                             u"obligatoires." % (SOURCE, etiq))
        if m["date"] in vus:
            raise ValueError(u"%s : deux rencontres le %s. Une seule par date : le data-id de "
                             u"la ligne en depend." % (SOURCE, m["date"]))
        vus.add(m["date"])
        if m.get("statut") not in (None, "a-venir", "joue", "annule", "reporte"):
            raise ValueError(u"%s, %s : statut inconnu %r (a-venir, joue, annule, reporte)."
                             % (SOURCE, etiq, m.get("statut")))
        # Meme garde-fou que build-matchs.py : un score ne peut pas preceder
        # la rencontre. C'est la faute de saisie la plus facile a commettre.
        if m.get("score") and dt > now:
            raise ValueError(u"%s, %s : un score est saisi pour une rencontre qui n'a pas "
                             u"encore commence (%s)." % (SOURCE, etiq, m["date"]))
        if m.get("lieu") and m["lieu"] not in lieux:
            raise ValueError(u"%s, %s : lieu %r absent de « lieux »." % (SOURCE, etiq, m["lieu"]))

        L = lieux.get(m["lieu"]) if m.get("lieu") else None
        adv = M.equipe(m["adversaireCourt"], m["adversaire"], m["sigle"], m.get("logo"))
        dom = bool(m["domicile"])
        e = {
            # L'identifiant porte l'equipe : « m-2026-09-20 » est deja pris par
            # les seniors, et script.js ecarte silencieusement un data-id vu deux fois.
            "id": u"u13-" + m["date"], "kind": "match", "comp": "dmu13", "phase": None,
            "debut": dt, "fin": dt + timedelta(minutes=m.get("duree") or 90),
            "heure": m["heure"], "dom": dom, "mbc": equipe_mbc, "adv": adv,
            "home": equipe_mbc if dom else adv, "away": adv if dom else equipe_mbc,
            "score": M.score_de(m), "statut": m.get("statut") or "a-venir",
            # Pas de fiche : item() rend alors un <div>, jamais un lien mort.
            "fiche": None, "ics": None,
            "lieu": L, "libre": bool(m.get("entreeLibre")),
            "journee": m.get("journee"), "manche": None, "tour": None,
            # Propres aux U13 : la commune de l'adversaire situe un deplacement,
            # que l'export de la Ligue laisse sans salle.
            "ville": m.get("ville"), "numero": m.get("numeroFFBB"),
        }
        es.append(e)

    es.sort(key=lambda e: e["debut"])
    for e in es:
        M.habiller(e, d, comps, {})
        # « Chez l'adversaire » seul ne dit pas s'il faut trente minutes ou une
        # heure de route : la commune le dit, sans pretendre nommer la salle.
        if not e["lieu"] and e.get("ville"):
            e["lieuNom"] = u"Chez l’adversaire · %s" % e["ville"]
    return d, es, now


def prochaine(es, now):
    """La premiere rencontre non terminee, annulations et reports ecartes."""
    for e in es:
        if e["statut"] in ("annule", "reporte"):
            continue
        if e["fin"] >= now:
            return e
    return None


# --------------------------------------------------------------------------
# Les pieces
# --------------------------------------------------------------------------
def ligne(e, now, id_next, cache=False):
    """Une ligne de saison, rendue par item() de la chaine seniors — avec son
    axe d'equipe en plus.

    data-equipe n'existe pas dans item() : il est pose ici. script.js s'en sert
    pour deux choses, et deux seulement : ne pas laisser une rencontre U13
    borner le « dernier resultat » des seniors, et calculer le « prochain
    match » equipe par equipe."""
    li = mc().item(e, now, id_next, cache)
    avant = u'<li class="'
    if not li.startswith(avant):
        raise SystemExit(u"!! item() a change de forme : data-equipe ne sait plus ou se poser.")
    return u'<li data-equipe="u13" class="' + li[len(avant):]


def carte(e, now, saison_ics=True):
    """La carte « Prochaine rencontre ».

    Elle ne ressemble pas tout a fait a celle des seniors : le bouton principal
    n'est pas « Voir le match » (il n'y a pas de fiche a voir) mais l'agenda —
    c'est ce qu'un parent veut faire de cette page. Le reste (classes, ordre,
    attributs de temps) est identique, pour que la meme CSS et le meme
    script.js s'en occupent."""
    M = mc()
    ech, crest = M.ech, M.crest
    tags = [u'<span class="mc-tag">%s</span>' % ech(e["compLabel"])]
    tags.append(u'<span class="mc-tag mc-tag--dom">Domicile</span>' if e["dom"]
                else u'<span class="mc-tag mc-tag--ext">Extérieur</span>')
    if e["dom"] and e["libre"]:
        tags.append(u'<span class="mc-tag mc-tag--libre">Entrée libre</span>')
    vs = (u'<span class="mc-vs"><span aria-hidden="true">vs</span>'
          u'<span class="sr-only"> contre </span></span>')
    duel = (u'<p class="mc-duel"><span class="mc-team">%s<span class="mc-team__n">%s</span></span>%s'
            u'<span class="mc-team">%s<span class="mc-team__n">%s</span></span></p>'
            % (crest(e["home"], 64, True), ech(e["home"]["nom"]), vs,
               crest(e["away"], 64, True), ech(e["away"]["nom"])))
    L = e["lieu"]
    lieu = ((u'%s <span class="mc-fact__s">%s, %s %s</span>'
             % (ech(L["nom"]), ech(L["adresse"]), ech(L["codePostal"]), ech(L["ville"])))
            if L else (u'Chez l’adversaire <span class="mc-fact__s">%s — salle communiquée '
                       u'par la Ligue</span>' % ech(e.get("ville") or u"commune à confirmer")))
    faits = (u'<dl class="mc-facts">'
             u'<div class="mc-fact mc-fact--date"><dt>Date</dt><dd><time datetime="%s">%s</time></dd></div>'
             u'<div class="mc-fact"><dt>Coup d’envoi</dt><dd>%s</dd></div>'
             u'<div class="mc-fact mc-fact--lieu"><dt>Lieu</dt><dd>%s</dd></div></dl>'
             % (e["dtAttr"], ech(e["dateLongue"]), e["heureFr"], lieu))
    act = []
    if saison_ics:
        act.append(u'<a class="btn btn--primary mc-cta" href="/%s" download>Ajouter les 7 dates '
                   u'à mon agenda%s</a>' % (ICS, M.FLECHE))
    if L:
        act.append(u'<a class="mc-lien" href="%s" target="_blank" rel="noopener">Itinéraire'
                   u'<span class="sr-only"> vers %s (Google Maps, nouvel onglet)</span></a>'
                   % (ech(L["carte"]), ech(L["nom"])))
    return (u'<article class="mc-next" data-id="%s" data-debut="%s" data-fin="%s" data-rang="0">\n'
            u'      <div class="mc-next__top"><h2 class="mc-eyebrow">'
            u'<span class="mc-dot" aria-hidden="true"></span>Prochaine rencontre</h2>\n'
            u'        <p class="mc-tags">%s</p></div>\n'
            u'      %s\n      %s\n'
            u'      <p class="mc-cd" data-mc-cd hidden></p>\n'
            u'      <p class="mc-next__a">%s</p>\n'
            u'    </article>'
            % (e["id"], e["debutIso"], e["finIso"], u"".join(tags), duel, faits, u"".join(act)))


def gabarits(es, now, courante):
    """Les rencontres suivantes, inertes dans des <template>.

    C'est la piece qui rend la page juste un mois apres sa publication : quand
    la rencontre affichee est passee, script.js prend la premiere carte encore
    a venir. Aucun texte n'est fabrique par le navigateur."""
    out = []
    for e in es:
        if courante and e["debut"] <= courante["debut"]:
            continue
        if e["statut"] in ("annule", "reporte"):
            continue
        out.append(u'  <template data-mc-t="prochain" data-id="%s" data-debut="%s" data-fin="%s" '
                   u'data-rang="0">%s</template>'
                   % (e["id"], e["debutIso"], e["finIso"], carte(e, now)))
        if len(out) >= GABARITS:
            break
    return u"\n".join(out)


def liste(es, now, id_next, suite=False, visibles=ACCUEIL_VISIBLES):
    """Les lignes de la saison.

    `suite` : la liste de l'accueil, qui se replie toute seule (les rencontres
    passees disparaissent, trois a venir restent). L'etat ecrit ici est deja le
    bon le jour de la publication ; script.js le tient a jour ensuite."""
    lis, n = [], 0
    for e in es:
        cache = False
        if suite:
            cache = e["fin"] < now or n >= visibles
            if not cache:
                n += 1
        lis.append(u"        " + ligne(e, now, id_next, cache))
    cl = u"mc-list mc-list--suite" if suite else u"mc-list"
    sup = u' data-max="%d"' % visibles if suite else u""
    return u'<ol class="%s"%s>\n%s\n      </ol>' % (cl, sup, u"\n".join(lis))


# --------------------------------------------------------------------------
# Le bloc de l'accueil et celui de la page enfant
# --------------------------------------------------------------------------
def bloc(d, es, now, complet):
    """Le bloc pose dans une page ecrite a la main.

    L'enveloppe .mc n'est pas decorative : `.mc .mc-suite__t` et `.mc .mc-tout`
    sont ecrites avec cet ancetre, parce que `.section p` (0,1,1) repeint
    sinon tout paragraphe de la section. Sans le .mc, le bloc perdrait ses
    styles sans qu'aucun garde-fou ne le signale.

    `complet` : la page enfant montre les sept dates (un parent veut toute la
    saison) ; l'accueil n'en montre que trois a venir et se replie tout seul."""
    M = mc()
    p = prochaine(es, now)
    id_next = p["id"] if p else None
    dom = len([e for e in es if e["dom"]])
    resume = u"%s · %s à domicile, %s en déplacement" % (
        M.plur(len(es), u"rencontre"), dom, len(es) - dom)
    titre = u"Les sept journées" if complet else u"Les U13, le dimanche matin"
    corps = liste(es, now, id_next, suite=not complet)
    lien = u"La page des U13" if complet else u"Le calendrier des U13"
    return (u'%s — généré par .claude/build-matchs-u13.py, ne pas éditer à la main -->\n'
            u'    <div class="mc reveal" data-mc="u13">\n'
            u'      <div class="mc-suite">\n'
            u'        <h3 class="mc-suite__t">%s</h3>\n'
            u'        %s\n'
            u'      </div>\n'
            u'      <p class="mc-tout"><a class="mc-tout__a" href="/matchs/u13/">'
            u'<span class="mc-tout__l">%s</span>'
            u'<span class="mc-tout__n">%s</span>%s</a></p>\n'
            u'    </div>\n'
            u'    %s'
            % (DEBUT, M.ech(titre), corps, M.ech(lien), M.ech(resume), M.FLECHE, FIN))


def poser(chemin, contenu):
    """Remplace le bloc entre les marqueurs. Les marqueurs sont poses une fois,
    a la main, dans la page : un generateur qui creerait sa propre place
    deciderait de la mise en page a la place de celui qui l'a ecrite."""
    p = os.path.join(RACINE, chemin)
    html = io.open(p, encoding="utf-8").read()
    i, j = html.find(DEBUT), html.find(FIN)
    if i < 0 or j < 0:
        print(u"  !! marqueurs MATCHS-U13 absents de %s" % chemin)
        return False
    neuf = html[:i] + contenu + html[j + len(FIN):]
    if neuf == html:
        return None
    io.open(p, "w", encoding="utf-8", newline="\n").write(neuf)
    return True


# --------------------------------------------------------------------------
# La page /matchs/u13/
# --------------------------------------------------------------------------
def creneaux_u13():
    """Les entrainements de la categorie, lus dans data/creneaux.json.

    Recopies ici, ils auraient vieilli le jour ou le planning change : c'est la
    meme source que le planning de /creneaux/ qui repond."""
    import json
    try:
        c = json.loads(lire("data/creneaux.json"))
    except Exception:
        return []
    jours = {u"lundi": 0, u"mardi": 1, u"mercredi": 2, u"jeudi": 3,
             u"vendredi": 4, u"samedi": 5, u"dimanche": 6}
    lieux = {l["id"]: l for l in c.get("lieux", [])} if isinstance(c.get("lieux"), list) \
        else (c.get("lieux") or {})
    out = []
    for cr in c.get("creneaux", []):
        if "u13" not in (cr.get("categories") or []) or cr.get("nature") != "entrainement":
            continue
        L = lieux.get(cr.get("lieu")) or {}
        out.append((jours.get(cr.get("jour"), 9), cr.get("jour"), cr.get("debut"), cr.get("fin"),
                    L.get("nom") or L.get("court") or cr.get("lieu")))
    out.sort()
    return out


def page(d, es, now):
    B, M = bm(), mc()
    ech = M.ech
    C, poule = d["competition"], d.get("poule") or {}
    p = prochaine(es, now)
    id_next = p["id"] if p else None
    dom = len([e for e in es if e["dom"]])

    visible, ld_fil = B.fil([(u"Accueil", "/"), (u"Matchs", "/matchs/"), (u"U13", None)])

    # Les donnees structurees : un SportsEvent par RECEPTION seulement. Un
    # deplacement se joue dans une salle que l'export ne nomme pas — un Event
    # sans lieu est un Event incomplet, et Search Console le dit.
    evenements = [event(e, d) for e in es if e["lieu"]]

    duo = (u'<div class="mc__duo mc__duo--seul">\n'
           u'  <div class="mc__slot" data-mc-slot="prochain">\n    %s\n  </div>\n</div>' % carte(p, now)) \
        if p else u''
    tpl = gabarits(es, now, p) if p else u''

    equipes = u"".join(
        u'<li class="ms-poule__i%s">%s<span>%s</span></li>'
        % (u" ms-poule__i--mbc" if t.get("mbc") else u"",
           M.crest(M.equipe(t.get("court") or t["nom"], t["nom"], t["sigle"],
                            t.get("logo"), bool(t.get("mbc"))), 44),
           ech(t["nom"]))
        for t in poule.get("equipes") or [])

    entr = creneaux_u13()
    entrainements = u"".join(
        u"<li><b>%s %s – %s</b><span>%s</span></li>"
        % (ech((j or u"").capitalize()), ech((dbt or u"").replace(":", u"h")),
           ech((fin or u"").replace(":", u"h")), ech(lieu or u""))
        for _, j, dbt, fin, lieu in entr)

    corps = u"""<main id="contenu">
  <section class="section mc-page">
    <div class="wrap">
      %(fil)s
      <header class="mc-page__head">
        <p class="kicker">U13 <i aria-hidden="true"></i> Saison %(saison)s</p>
        <h1 class="h2">Le calendrier <span class="hl">des U13</span></h1>
        <p class="sec-head__sub">Les U13 du MBC La Montagne disputent la %(compNom)s, poule A, avec sept autres clubs de l’île&nbsp;: %(compte)s, toutes le <b>dimanche à %(heure)s</b>. À domicile, rendez-vous au Gymnase de La Montagne, à Saint-Denis&nbsp;: l’entrée est libre.</p>
      </header>
      <div class="mc" data-mc="u13" data-publie="%(publie)s">
%(duo)s
%(tpl)s
      </div>
      <section class="ms" id="saison" aria-labelledby="msU13">
        <div class="ms__head"><h2 class="ms__t" id="msU13">Les sept journées</h2><p class="ms__n">%(resume)s</p></div>
        %(liste)s
      </section>
    </div>
  </section>
  <section class="section ms-format" id="format" aria-labelledby="msFormatU13">
    <div class="wrap">
      <h2 class="ms-format__t" id="msFormatU13">Le format <span class="hl">de la poule</span></h2>
      <ol class="licence-path"><li><b>%(compNom)s — poule A</b><span>%(compDetail)s</span><span class="lp-who lp-who--vous">La phase en cours</span></li><li><b>Après la poule</b><span>La suite du calendrier (deuxième phase, plateaux) est publiée par le Comité en cours de saison. Rien n’est annoncé ici tant qu’elle ne l’est pas.</span></li></ol>
      <div class="ms-poule">
        <h3 class="ms-poule__t">%(pouleNom)s</h3>
        <ul class="ms-poule__l">%(equipes)s</ul>
      </div>%(entrainements)s
      <p class="ms-sources">Source&nbsp;: le calendrier de la poule publié par le %(organisateur)s, édition du 21&nbsp;août 2026 (<a href="/%(archive)s">la voir telle quelle</a>). L’équipe nommée en premier reçoit. L’export ne donne ni salle de déplacement, ni score&nbsp;: ce qui n’y figure pas n’est pas inventé ici.</p>
      <p class="ms-liens"><a href="%(ffbb)s" target="_blank" rel="noopener">Résultats et classement sur le site de la FFBB<span class="sr-only"> (nouvel onglet)</span></a> <i aria-hidden="true"></i> <a href="/matchs/">Les matchs des seniors</a> <i aria-hidden="true"></i> <a href="/%(page)s">Le basket enfant au MBC</a></p>
      <p class="ml__retour"><a href="/#matchs">Revenir à l’accueil</a></p>
    </div>
  </section>
</main>""" % {
        "fil": visible, "saison": ech(d["saison"]),
        "compNom": ech(C["nom"]), "compDetail": ech(C["detail"]),
        # « sept rencontres » et non « 7 » : la phrase compte deja « sept autres
        # clubs », et melanger le chiffre et la lettre dans la meme ligne se voit.
        "compte": u"%s rencontres" % ({7: u"sept", 6: u"six", 5: u"cinq", 4: u"quatre",
                                       3: u"trois", 2: u"deux"}.get(len(es), len(es))),
        "heure": (es[0]["heureFr"] if es else u"10h30"),
        "publie": now.strftime("%Y-%m-%dT%H:%M"),
        "duo": duo, "tpl": tpl,
        "resume": ech(u"%s · %s à domicile, %s en déplacement"
                      % (M.plur(len(es), u"rencontre"), dom, len(es) - dom)),
        "liste": liste(es, now, id_next),
        "pouleNom": ech(poule.get("nom") or u"La poule"), "equipes": equipes,
        "entrainements": (u'\n      <div class="ms-poule">\n        <h3 class="ms-poule__t">'
                          u'Les entraînements des U13</h3>\n        <ol class="licence-path">%s</ol>'
                          u'\n      </div>' % entrainements) if entrainements else u"",
        "organisateur": ech(C.get("organisateur") or u"Comité de La Réunion de Basket-Ball"),
        "archive": ARCHIVE, "ffbb": M.FFBB, "page": ech(d["equipe"].get("page") or u""),
    }

    titre = u"Calendrier U13 %s — MBC974" % d["saison"]
    desc = (u"Les %d rencontres des U13 du MBC La Montagne en %s : dates, adversaires, "
            u"domicile ou déplacement. Le dimanche à %s, au Gymnase de La Montagne, "
            u"à Saint-Denis de La Réunion."
            % (len(es), C["nom"], es[0]["heureFr"] if es else u"10h30"))
    lds = [ld_fil] + [e for e in evenements if e]
    entete, cta, pied, scripts = B.GABARIT
    return (B.tete(titre, desc, URL_PAGE, lds, prof=2)
            + entete + u"\n\n" + cta + u"\n\n" + corps + u"\n\n" + pied
            + u"\n\n" + scripts + u"</body>\n</html>\n")


def event(e, d):
    """SportsEvent d'une reception. Meme forme que celui des seniors, meme
    entite #club : c'est le meme club qui organise."""
    if not e["lieu"]:
        return None
    L, club, C = e["lieu"], d["club"], d["competition"]
    ev = {
        "@context": "https://schema.org", "@type": "SportsEvent",
        "@id": URL_PAGE + "#" + e["id"],
        "name": u"%s U13 – %s (%s, %s)" % (club["nom"], e["adv"]["long"], C["nom"], e["compLabel"]),
        "description": (u"%s de %s : les U13 du %s reçoivent %s au %s, à %s (%s), le %s à %s. "
                        u"Entrée libre."
                        % (e["compLabel"], C["nom"], club["nom"], e["adv"]["long"], L["nom"],
                           L["ville"], L["region"], e["dateLongue"].lower(), e["heureFr"])),
        "url": URL_PAGE,
        "startDate": e["debutIso"], "endDate": e["finIso"],
        "eventStatus": bm().STATUT_SCHEMA.get(e["statut"], "https://schema.org/EventScheduled"),
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "sport": "Basketball",
        "location": {
            "@type": "Place", "name": L["nom"],
            "address": {"@type": "PostalAddress", "streetAddress": L["adresse"],
                        "addressLocality": L["ville"], "postalCode": L["codePostal"],
                        "addressRegion": L["region"], "addressCountry": L["pays"]},
            "geo": {"@type": "GeoCoordinates", "latitude": L["latitude"], "longitude": L["longitude"]},
            "hasMap": L["carte"],
        },
        "organizer": {"@id": SITE + "/#club", "@type": "SportsClub",
                      "name": club["nom"], "url": club["url"]},
        "performer": [
            {"@type": "SportsTeam", "name": u"%s — U13" % club["nom"],
             "sport": "Basketball", "url": club["url"]},
            {"@type": "SportsTeam", "name": e["adv"]["long"], "sport": "Basketball"},
        ],
        "homeTeam": {"@type": "SportsTeam", "name": u"%s — U13" % club["nom"]},
        "awayTeam": {"@type": "SportsTeam", "name": e["adv"]["long"]},
        # La banniere du club, faute de carte dessinee par rencontre : image est
        # une propriete recommandee de SportsEvent, et verifier-jsonld.py le dit.
        "image": [SITE + "/" + bm().SOCIALE_DEFAUT],
    }
    if e["libre"]:
        ev["isAccessibleForFree"] = True
        ev["offers"] = {"@type": "Offer", "price": "0", "priceCurrency": "EUR",
                        "availability": "https://schema.org/InStock", "url": URL_PAGE}
    return ev


# --------------------------------------------------------------------------
# Le .ics de la saison : les sept dates d'un coup
# --------------------------------------------------------------------------
def ics(d, es):
    """Un seul fichier, sept rendez-vous.

    C'est le service que rend cette page : un parent l'ouvre une fois, et les
    sept dimanches sont dans son telephone. Les deplacements y figurent aussi —
    sans salle, mais avec la commune : une date qu'on ignore est plus genante
    qu'une adresse a confirmer.

    DTSTAMP est fige au jour ou le calendrier a ete transmis : il ne sert qu'a
    dater la publication, et une valeur qui bouge a chaque execution ferait
    changer le fichier sans qu'une seule rencontre ait change."""
    B = bm()
    lignes = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MBC La Montagne Basket Club//FR",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        u"X-WR-CALNAME:%s" % B._ics_txt(u"MBC U13 — saison %s" % d["saison"]),
        "BEGIN:VTIMEZONE", "TZID:Indian/Reunion", "BEGIN:STANDARD",
        "DTSTART:19700101T000000", "TZOFFSETFROM:+0400", "TZOFFSETTO:+0400",
        "TZNAME:+04", "END:STANDARD", "END:VTIMEZONE",
    ]
    for e in es:
        if e["statut"] in ("annule", "reporte"):
            continue
        L = e["lieu"]
        lieu = (u"%s, %s, %s %s" % (L["nom"], L["adresse"], L["codePostal"], L["ville"])) if L \
            else (u"%s — salle communiquée par la Ligue" % (e.get("ville") or u"chez l’adversaire"))
        lignes += [
            "BEGIN:VEVENT",
            u"UID:u13-%s@mbc974.com" % e["debut"].strftime("%Y-%m-%d"),
            "DTSTAMP:%sZ" % datetime(2026, 9, 17).strftime("%Y%m%dT%H%M%S"),
            "DTSTART;TZID=Indian/Reunion:%s" % B._ics_heure(e["debutIso"]),
            "DTEND;TZID=Indian/Reunion:%s" % B._ics_heure(e["finIso"]),
            u"SUMMARY:%s" % B._ics_txt(u"U13 : %s — %s (%s)"
                                       % (e["home"]["nom"], e["away"]["nom"], e["compLabel"])),
            u"LOCATION:%s" % B._ics_txt(lieu),
            u"DESCRIPTION:%s" % B._ics_txt(
                d["competition"]["nom"]
                + (u" — entrée libre." if e["libre"] else u" — déplacement.")),
            "URL:%s" % URL_PAGE,
            "END:VEVENT",
        ]
    lignes += ["END:VCALENDAR", ""]
    return u"\r\n".join(B._ics_plier(l) for l in lignes)


# --------------------------------------------------------------------------
def main():
    essai = "--essai" in sys.argv
    B = bm()
    d, es, now = charger()

    if essai:
        p = prochaine(es, now)
        print(u"  %s — %s, %d rencontres" % (SOURCE, d["saison"], len(es)))
        print(u"  maintenant : %s" % now.strftime("%Y-%m-%d %H:%M"))
        print(u"  prochaine  : %s" % (u"%s, %s (%s)"
                                      % (p["dateCourte"], p["titre"], p["compLabel"]) if p
                                      else u"aucune, la poule est terminée"))
        for e in es:
            print(u"    %-14s %-11s %-34s %s"
                  % (e["dateCourte"], e["compLabel"], e["titre"],
                     u"passée" if e["fin"] < now else u"à venir"))
        return 0

    # Le gabarit du site (en-tete, barre CTA, pied, scripts, version de la CSS)
    # vient de build-matchs.py : une seule forme possible pour les 25 pages.
    brut = B.gabarit()
    B.GABARIT = brut[:4]
    B.VERSION_CSS = brut[4]

    ecrits = []
    ecrire("matchs/u13/index.html", page(d, es, now))
    ecrits.append("matchs/u13/index.html")
    ecrire(ICS, ics(d, es))
    ecrits.append(ICS)

    for chemin, complet in (("index.html", False),
                            ("basket-enfant-saint-denis/index.html", True)):
        r = poser(chemin, bloc(d, es, now, complet))
        if r is False:
            return 1
        if r:
            ecrits.append(chemin)

    p = prochaine(es, now)
    print(u"  U13 : %d rencontres, prochaine %s"
          % (len(es), p["dateCourte"] if p else u"— (poule terminée)"))
    for f in ecrits:
        print(u"  ecrit  %s" % f)
    if not ecrits:
        print(u"  rien a ecrire (deja a jour)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
