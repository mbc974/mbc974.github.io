# -*- coding: utf-8 -*-
"""Pose (ou retire) la mesure d'audience Google Analytics 4 sur TOUTES les pages.

    python .claude/set-analytics.py --etat   ce que porte chaque page
    python .claude/set-analytics.py --on     installe GA4 partout
    python .claude/set-analytics.py --off    retire GA4 partout

POURQUOI CE SCRIPT EXISTE
-------------------------
Le site n'a pas d'etape de construction : une balise posee a la main devrait
etre recopiee dans 25 pages, dont 12 sont regenerees par les scripts de
.claude/. Une passe precedente avait laisse la balise sur 11 pages seulement,
et personne ne s'en apercevait. Ici, un seul geste couvre tout, et --etat dit
la verite page par page.

Les 12 pages generees recoivent le meme bloc par build-matchs.py (dont
build-actus.py reprend le gabarit) : les deux sources sont volontairement
identiques, voir ANALYTICS dans ce fichier et dans build-matchs.py.

CE QUE FAIT LE BLOC POSE
------------------------
Il declare Consent Mode AVANT de charger gtag.js, avec TOUT refuse. C'est la
seule facon d'etre certain qu'aucun cookie de mesure n'existe avant le choix
du visiteur. Le choix deja memorise (localStorage « mbc-consent ») est
relu dans la foulee, pour qu'un visiteur qui a accepte soit mesure des la
premiere page et pas seulement a partir de la deuxieme.

Le MBC n'utilise pas Google Ads : ad_storage, ad_user_data et
ad_personalization restent refuses meme apres acceptation. Seul
analytics_storage bascule. C'est consent.js qui pose le bandeau et envoie la
mise a jour.
"""
import glob
import io
import os
import re
import sys

MESURE = 'G-4C00VET9W9'

DEBUT = '<!-- Google Analytics 4'
FIN = '<!-- /Google Analytics 4 -->'

ANALYTICS = u"""<!-- Google Analytics 4 (%(id)s) — Consent Mode v2.
     Tout est refuse par defaut ; consent.js pose le bandeau et transmet le
     choix. Le club n'utilise pas Google Ads : seul analytics_storage peut
     passer a « granted ». -->
<script>
window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
gtag('consent','default',{'analytics_storage':'denied','ad_storage':'denied','ad_user_data':'denied','ad_personalization':'denied','wait_for_update':500});
try{if(localStorage.getItem('mbc-consent')==='granted'){gtag('consent','update',{'analytics_storage':'granted'});}}catch(e){}
gtag('js',new Date());
gtag('config','%(id)s');
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=%(id)s"></script>
<script defer src="/consent.js"></script>
<!-- /Google Analytics 4 -->""" % {'id': MESURE}

# L'ancre : juste apres le viewport, donc avant tout le reste du <head>.
ANCRE = re.compile(r'(<meta name="viewport"[^>]*>\s*\n)')


def pages():
    f = ['index.html', 'adhesion.html', '404.html', 'offline.html']
    f += sorted(glob.glob('*/index.html'))
    f += sorted(glob.glob('*/*/index.html'))
    return [p for p in f if os.path.exists(p)]


def etat(s):
    if DEBUT in s:
        return 'ga4'
    if 'plausible.io' in s:
        return 'plausible'
    return 'aucun'


def retirer_plausible(s):
    """Supprime le bloc Plausible, actif ou commente."""
    s = re.sub(r'<!-- ANALYTICS \(.*?-->\s*\n?', '', s, flags=re.S)
    s = re.sub(r'^.*plausible\.io.*\n', '', s, flags=re.M)
    return s


def retirer_ga4(s):
    return re.sub(re.escape(DEBUT) + r'.*?' + re.escape(FIN) + r'\s*\n?', '', s, flags=re.S)


def poser(s):
    s = retirer_plausible(s)
    s = retirer_ga4(s)
    if not ANCRE.search(s):
        return None
    return ANCRE.sub(lambda m: m.group(1) + ANALYTICS + '\n', s, count=1)


def main():
    if not os.path.exists('index.html'):
        print('!! lancer depuis la racine du depot')
        return 1
    mode = ('--on' in sys.argv and 'on') or ('--off' in sys.argv and 'off') or 'etat'

    faits, rate = [], []
    compte = {}
    for p in pages():
        s = io.open(p, encoding='utf-8').read()
        avant = etat(s)
        if mode == 'on':
            s2 = poser(s)
            if s2 is None:
                rate.append(p)
                s2 = s
        elif mode == 'off':
            s2 = retirer_ga4(retirer_plausible(s))
        else:
            s2 = s
        apres = etat(s2)
        compte[apres] = compte.get(apres, 0) + 1
        if s2 != s:
            io.open(p, 'w', encoding='utf-8', newline='').write(s2)
            faits.append('%-52s %s -> %s' % (p, avant, apres))
        elif mode == 'etat':
            print('  %-52s %s' % (p, avant))

    if mode != 'etat':
        for f in faits:
            print('  ' + f)
    if rate:
        print('\n  !! ancre <meta viewport> introuvable dans : %s' % ', '.join(rate))
    print('\n  %d page(s) : %s' % (sum(compte.values()),
                                   ', '.join('%s %d' % (k, v) for k, v in sorted(compte.items()))))
    if mode == 'on':
        print('\n  puis : python .claude/bump-assets.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
