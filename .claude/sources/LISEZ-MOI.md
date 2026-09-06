# Images sources

Les originaux dont on **dérive** les fichiers publiés dans `assets/`.

Ils ne sont jamais servis au visiteur : rien sur le site ne pointe ici, et ils
ne sont ni dans le sitemap ni dans le service worker. Ils sont versionnés parce
que, sans eux, on ne peut plus regénérer une variante sans repartir d'un fichier
déjà compressé — et une image ré-encodée deux fois se dégrade à chaque passage.

| Fichier | Sert à | Généré par |
|---|---|---|
| `hero-regroupement-4080x1630.jpg` | les 16 variantes du hero de la page d'accueil (panoramique + recadrage mobile, AVIF et WebP) | `python .claude/build-hero.py` |

Le recadrage mobile est la fenêtre `x = 1387 … 2489` de cet original ; la valeur
est écrite dans `build-hero.py` et ne doit pas être devinée à nouveau.
