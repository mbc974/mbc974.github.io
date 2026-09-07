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

CE QUE FAIT LE BLOC POSE (Consent Mode BASIQUE)
-----------------------------------------------
Il ne charge RIEN de Google. Il definit mbcChargerGA() et ne l'appelle que si
un accord est deja memorise (localStorage « mbc-consent » = accepted, ou
granted pour les choix faits avant ce changement). Sans accord : pas de
gtag.js, aucune requete vers googletagmanager.com, pas meme un ping anonyme.

C'est consent.js qui pose le bandeau et qui appelle mbcChargerGA() au clic
sur Accepter. Un refus n'entraine aucun chargement, jamais.

Le MBC n'utilise pas Google Ads : ad_storage, ad_user_data et
ad_personalization restent refuses meme apres acceptation. Seul
analytics_storage passe a granted.
"""
import glob
import io
import os
import re
import sys

MESURE = 'G-4C00VET9W9'

DEBUT = '<!-- Google Analytics 4'
FIN = '<!-- /Google Analytics 4 -->'

ANALYTICS = u'''<!-- Google Analytics 4 (G-4C00VET9W9) — Consent Mode BASIQUE.
     Rien n'est charge tant que le visiteur n'a pas accepte : pas de
     gtag.js, pas de requete, pas de ping anonyme. Ce bloc ne fait que
     definir mbcChargerGA() et l'appeler si un accord est deja memorise,
     pour que la mesure reprenne des la premiere page d'une visite
     suivante. C'est consent.js qui l'appelle au clic sur Accepter.
     Les trois consentements publicitaires restent refuses en toutes
     circonstances : le club n'utilise pas Google Ads. -->
<script>
window.MBC_GA_ID='G-4C00VET9W9';
window.mbcChargerGA=function(){
  if(window.MBC_GA_ON){return;}window.MBC_GA_ON=true;
  window.dataLayer=window.dataLayer||[];
  window.gtag=function(){window.dataLayer.push(arguments);};
  gtag('consent','default',{'analytics_storage':'denied','ad_storage':'denied','ad_user_data':'denied','ad_personalization':'denied'});
  gtag('consent','update',{'analytics_storage':'granted'});
  gtag('js',new Date());
  gtag('config',window.MBC_GA_ID);
  var s=document.createElement('script');s.async=true;
  s.src='https://www.googletagmanager.com/gtag/js?id='+window.MBC_GA_ID;
  document.head.appendChild(s);
};
try{var c=localStorage.getItem('mbc-consent');if(c==='accepted'||c==='granted'){window.mbcChargerGA();}}catch(e){}
</script>
<script defer src="/consent.js"></script>
<!-- /Google Analytics 4 -->'''

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
