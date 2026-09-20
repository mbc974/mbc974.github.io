#!/usr/bin/env python3
"""Derive the motion experiments from the real home and generated match pages.
Run from anywhere: python lab/motion/build.py. Never writes production files.
"""
from pathlib import Path
import re, hashlib, json, posixpath

LAB=Path(__file__).resolve().parent
ROOT=LAB.parents[1]
SOURCE=(ROOT/'index.html').read_text()
NAMES={'editorial':'A · Editorial Motion','sport':'B · Sport Motion','court':'C · Court Vision'}

def root_url(value):
    if value.startswith(('/', '#', 'http:', 'https:', 'mailto:', 'tel:', 'data:')): return value
    return posixpath.normpath('/'+value)

def prepare(s):
    # Experiments never duplicate a live form service key or submit test messages.
    s=re.sub(r'<form\b[^>]*id="contactForm"[^>]*>.*?</form>', '<div class="contact-form"><h3>Un message pour le club ?</h3><p>Une question sur une catégorie, un créneau ou votre inscription ?</p><a class="btn btn--primary" href="/#contact">Contacter le MBC</a></div>',s,flags=re.S)
    # Asset and page links keep pointing at the existing repository resources.
    s=re.sub(r'\b(src|href|poster|data-lightbox-src|data-lightbox-fallback)="([^"]+)"',lambda m:f'{m[1]}="{root_url(m[2])}"',s)
    s=re.sub(r'(srcset|imagesrcset)="([^"]+)"',lambda m:m[1]+'="'+', '.join(root_url(v.strip()) for v in m[2].split(','))+'"',s)
    s=re.sub(r"this.src='([^']+)'",lambda m:"this.src='"+root_url(m[1])+"'",s)
    s=re.sub(r'<!-- Google Analytics 4.*?<!-- /Google Analytics 4 -->','<!-- Lab: no analytics loader; production consent files unchanged. -->',s,flags=re.S)
    s=re.sub(r'<meta name="robots"[^>]+>','<meta name="robots" content="noindex,nofollow">',s)
    if 'name="robots"' not in s:s=s.replace('</head>','<meta name="robots" content="noindex,nofollow"></head>')
    # No duplicate SportsEvent or editorial schema in experimental pages.
    s=re.sub(r'<script type="application/ld\+json">.*?</script>','',s,flags=re.S)
    s=re.sub(r'<!--.*?-->','',s,flags=re.S)
    return s

def bar(concept):
    links=''.join(f'<a href="/lab/motion/{key}/"'+(' aria-current="page"' if key==concept else '')+f'>{name}</a>' for key,name in NAMES.items())
    return f'''<aside class="ml-bar" aria-label="Navigation du laboratoire"><a class="ml-home" href="/lab/motion/">MBC / Motion Lab</a><nav aria-label="Concepts">{links}</nav><button type="button" id="ml-motion" aria-pressed="false" hidden>Version calme</button></aside>'''

TACTIC='''<svg class="ml-hero-line" viewBox="0 0 600 320" fill="none" aria-hidden="true"><path class="ml-tactic" pathLength="1" d="M30 70 C180 15 80 260 285 240 S470 240 530 65"/><circle cx="30" cy="70" r="7"/><path d="m510 73 20-8 4 22"/></svg>'''

COURT='''<section class="ml-court" aria-labelledby="court-title" id="court-vision"><div class="ml-court-sticky"><div class="ml-court-head"><p class="ml-eyebrow">MBC Playbook / 01</p><h2 id="court-title">Le même terrain.<br><span>La même équipe.</span></h2><a href="#nxBand" class="ml-skip">Aller au prochain match ↓</a></div><div class="ml-court-perspective"><svg class="ml-court-svg" viewBox="0 0 1000 580" fill="none" aria-hidden="true"><g class="ml-floor"><rect x="80" y="65" width="840" height="450" rx="2" fill="#153e77"/>
<path class="ml-boards" d="M110 65V515 M140 65V515 M170 65V515 M200 65V515 M230 65V515 M260 65V515 M290 65V515 M320 65V515 M350 65V515 M380 65V515 M410 65V515 M440 65V515 M470 65V515 M500 65V515 M530 65V515 M560 65V515 M590 65V515 M620 65V515 M650 65V515 M680 65V515 M710 65V515 M740 65V515 M770 65V515 M800 65V515 M830 65V515 M860 65V515 M890 65V515"/>
<g class="ml-court-lines"><rect x="80" y="65" width="840" height="450"/><path d="M500 65V515 M80 216.5H254V363.5H80 M920 216.5H746V363.5H920"/><circle cx="500" cy="290" r="54"/><circle cx="254" cy="290" r="54"/><circle cx="746" cy="290" r="54"/><path d="M80 86H117 A202.5 202.5 0 0 1 117 494H80 M920 86H883 A202.5 202.5 0 0 0 883 494H920 M116 263V317 M884 263V317"/><circle cx="128" cy="290" r="7"/><circle cx="872" cy="290" r="7"/></g>
<path id="ml-route" class="ml-route" pathLength="1" d="M220 425 C380 450 390 140 560 165 S660 405 795 350 Q860 320 872 290"/>
<g class="ml-position"><circle cx="220" cy="425" r="18"/><text x="220" y="431">1</text><circle cx="560" cy="165" r="18"/><text x="560" y="171">2</text><circle cx="795" cy="350" r="18"/><text x="795" y="356">3</text></g>
<g class="ml-ball" transform="translate(872 290)"><circle r="11" fill="#E8822A" stroke="#070d18" stroke-width="2"/><path d="M-11 0H11 M0-11V11 M-7-8Q2 0-7 8 M7-8Q-2 0 7 8" stroke="#070d18" stroke-width="1.4"/></g></g></svg></div><p class="ml-court-foot"><span>La Montagne · Saint-Denis</span><span>Du collectif au coup d’envoi</span></p></div></section>'''

def topo():
    # An abstract relief motif, not a geographic map or a survey of La Montagne.
    paths=''.join(f'<path data-contour="{i}" d="M{80+i*20} 280 C180 {60+i*15} 330 {90+i*10} 460 {240-i*10} S720 {400-i*10} {900-i*20} 220"/>' for i in range(6))
    return f'<div class="ml-topo" aria-hidden="true"><svg viewBox="0 0 1000 500" fill="none">{paths}<circle class="ml-topo-circle" cx="500" cy="250" r="64"/></svg></div>'

for key,label in NAMES.items():
    dest=LAB/key;dest.mkdir(exist_ok=True)
    s=prepare(SOURCE)
    s=s.replace('<body>',f'<body class="motion-lab ml-{key}">'+bar(key))
    s=re.sub(r'<title>.*?</title>',f'<title>{label} — MBC Motion Lab</title>',s)
    s=s.replace('</head>','<link rel="stylesheet" href="/lab/motion/motion.css"></head>')
    s=s.replace('</body>','<script defer src="/lab/motion/motion.js"></script></body>')
    # Disable only overlapping legacy presentations; the original behavior remains shared.
    s=s.replace('data-hw','data-ml-signature').replace('id="galerieZoom"','id="ml-gallery"')
    s=re.sub(r' data-count(?:-delay)?="[^"]*"','',s)
    s=s.replace('<div class="hero__inner">',TACTIC+'<div class="hero__inner">',1)
    s=s.replace('<h2 class="sr-only" id="essentielTitle">Le MBC en trois chiffres</h2>','<h2 class="ml-facts-heading" id="essentielTitle">Une saison. Toutes les générations.</h2>')
    s=s.replace('<span class="keyfig__v">Dès 3 ans</span>','<span class="keyfig__v"><small>Dès</small> 3 <small>ans</small></span>')
    s=s.replace('<span class="keyfig__v">2 terrains</span>','<span class="keyfig__v">2 <small>terrains</small></span>')
    # A/B: put the club's three promises directly after the hero. C: short court bridge.
    facts=re.search(r'<section class="section keyfig-sec".*?</section>',s,re.S)[0]
    s=s.replace(facts,'')
    marker='<section class="nx"'
    s=s.replace(marker,facts+(COURT if key=='court' else '')+marker,1)
    if key=='court':s=s.replace('<div class="wrap lp-wrap">',topo()+'<div class="wrap lp-wrap">')
    # Native horizontal rail replaces the old long scroll zoom in this experiment.
    s=s.replace('<div class="gallery-mosaic reveal">','<div class="gallery-mosaic" tabindex="0" role="region" aria-label="Photos du club, défilement horizontal">')
    s=s.replace('<p class="gzoom__cue" aria-hidden="true">','<p class="gzoom__cue" aria-hidden="true">')
    # Keep local section links in the experiment, ordinary destinations in production.
    s=re.sub(r'href="/#[^"]+"',lambda m:m[0].replace('href="/#','href="#'),s)
    s=s.replace('href="#contact">Contacter le MBC','href="/#contact">Contacter le MBC')
    for match in json.loads((ROOT/'data/matchs.json').read_text())['matchs']:
        slug=match['slug'];url=f'/lab/motion/{key}/matchs/{slug}/'
        s=s.replace(f'href="/matchs/{slug}/"',f'href="{url}"')
        md=dest/'matchs'/slug;md.mkdir(parents=True,exist_ok=True)
        page=prepare((ROOT/'matchs'/slug/'index.html').read_text())
        page=page.replace('<body>',f'<body class="motion-lab ml-{key} ml-match-page">'+bar(key))
        page=page.replace('</head>','<link rel="stylesheet" href="/lab/motion/motion.css"></head>')
        page=page.replace('</body>','<script defer src="/lab/motion/motion.js"></script></body>')
        page=page.replace('href="/"',f'href="/lab/motion/{key}/"').replace('href="/matchs/"',f'href="/lab/motion/{key}/#matchs"')
        for other in json.loads((ROOT/'data/matchs.json').read_text())['matchs']:
            page=page.replace(f'href="/matchs/{other["slug"]}/"',f'href="/lab/motion/{key}/matchs/{other["slug"]}/"')
        (md/'index.html').write_text(page)
    (dest/'index.html').write_text(s)

manifest={"base_home_sha256":hashlib.sha256(SOURCE.encode()).hexdigest(),"generated_from":["index.html","data/matchs.json","matchs/*/index.html"],"concepts":NAMES,"note":"Run existing content generators first, then this script; no production write."}
(LAB/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Generated 3 home experiments and 21 match-page experiments from repository sources.')
