# Les dossiers de partenariat du MBC

**Deux** dossiers, un seul socle. Dix pages en 16:9 chacun (1280 × 720 px =
960 × 540 pt = 13,333 × 7,5 in, le format standard des présentations 16:9).

| dossier | destinataire | générateur |
|---|---|---|
| `dossier.pdf` | **OLA Energy**, nommé à chaque page | `dossier.py` + `contenu.py` |
| `dossier-general.pdf` | **tout partenaire**, du commerçant au groupe | `dossier_general.py` + `contenu_general.py` |

Le générique est celui qui a vocation à remplacer
`assets/documents/DOSSIER-PARTENARIAT-MBC-2026-2027.pdf`, le fichier que
`/sponsor-club-basket-reunion/` propose au téléchargement. Le dossier OLA ne
doit **jamais** y être publié : il nomme OLA partout.

## Refaire les PDF

```bash
cd .claude/dossier-ola
python assets.py              # recadre les photos depuis assets/ et regenere les QR
python assets_general.py      # les maillots et les supports du dossier generique

python dossier.py             # -> dossier.html          (OLA)
python render.py dossier.html dossier.pdf out
python verifier.py            # DOIT afficher « TOUT PASSE »

python dossier_general.py     # -> dossier-general.html  (generique)
python render.py dossier-general.html dossier-general.pdf out-gen
MBC_GENERATEUR=dossier_general python verifier.py dossier-general.html dossier-general.pdf
```

`MBC_GENERATEUR` dit au garde-fou de quel générateur importer les décrochages
intérieurs : les deux dossiers n'ont pas les mêmes gouttières.

`assets.py` puise dans `assets/images/`, `assets/galerie/` et `assets/logos/` du
dépôt : la couverture repart du `mbc-hero-regroupement-2800.webp` d'origine, pas
d'une copie basse définition.

Trois variantes de couverture : `python dossier.py a|b|c`
(a = « Prenez place maintenant », b = « L'énergie d'une saison »,
c = « La prochaine image est la vôtre »).

## Ce qui tient la mise en page

| fichier | rôle |
|---|---|
| `typo.py` | métriques **réelles** des polices du site, lues dans les woff2 |
| `grille.py` | la page, la grille de 12 colonnes, l'échelle de texte |
| `bloc.py` | primitives : bloc de texte posé par son encre, filet, pavé, QR, pied |
| `css.py` | la feuille de style, générée depuis les deux précédents |
| `contenu.py` / `contenu_general.py` | **le texte et les chiffres** — c'est ici qu'on modifie le fond |
| `dossier.py` / `dossier_general.py` | les dix pages de chaque dossier |
| `verifier.py` | les garde-fous, pour l'un ou l'autre |

`bloc.SIGNATURE` porte la ligne de pied : le générique la remplace par
« MBC LA MONTAGNE BASKET CLUB », sans quoi il afficherait « MBC × OLA ENERGY »
sur ses dix pages — c'est arrivé au premier rendu.

Le squelette est identique au pixel sur les huit pages de contenu :

```
 56  haut des capitales du surtitre
 96  haut des capitales du titre  (Anton 64 px)
185  haut des capitales du sous-titre
232  première ligne de contenu
588  dernière ligne de contenu  — rien ne descend plus bas, la mention y vit
648  filet du pied
664  signature du pied et numéro de page
```

## Deux mécanismes qui ne se devinent pas

**L'alignement optique.** Chaque bloc annule le side bearing gauche du premier
glyphe de son texte (`margin-left` négatif, *pas* `text-indent` : `text-indent`
ne décale que la première ligne). L'encre commence donc exactement sur la
colonne, quelle que soit la police et la lettre. Les titres sont émis **une
ligne par bloc positionné**, pour que chaque ligne reçoive la compensation de
*son* premier glyphe. Mesuré à 300 dpi : encre à 64,00 / 63,68 / 64,64 px pour
une marge de 64.

**L'interligne des capitales accentuées.** Dans Anton une capitale accentuée
monte à **1,1006 em** au-dessus de la ligne de base quand une capitale nue
plafonne à 0,8594, et la cédille du Ç descend à **−0,3081**. Tout interligne
inférieur à 1,1006 fait mordre l'accent sur la ligne du dessus. D'où
`LH_TITRE = 1.12`. Ne pas le baisser « pour serrer ».

## Les garde-fous

`verifier.py` lit les polices **embarquées dans le PDF** pour en tirer les side
bearings : la mesure est indépendante du code qui a généré la page.

1. **glyphes** — tout caractère doit exister dans les sous-ensembles Anton et
   Barlow du site. `U+202F` (espace fine insécable), `U+2192` (→) et `U+2248`
   (≈) en sont **absents** : Chrome y substitue Times New Roman en silence.
2. **polices** — le PDF ne doit contenir qu'Anton et Barlow.
3. **squelette** — surtitre, titre et écart titre→sous-titre identiques sur les
   huit pages (on compare les pages *entre elles*, pas à une constante : Chrome
   arrondit les métriques de ligne, un décalage uniforme d'un pixel ne se voit
   pas).
4. **encre** — chaque début de ligne tombe sur une colonne, à 0,62 pt près.
5. **débords** — rien hors page, rien qui franchisse le filet du pied.
6. **bande utile** — ni texte ni **panneau** sous 588 px.
7. **contre-mesure en pixels** — lecture directe du raster à 300 dpi.

Prouvé mordant sur quatre sabotages : glyphe absent, titre d'une page à 56 px au
lieu de 64, bord gauche décalé de 3 px, carte redescendue sous la bande.

Les décrochages intérieurs légitimes (gouttière de chiffres, retrait de carte,
intitulé à côté d'un QR) sont **exportés par `dossier.decrochages()`** et
importés par le garde-fou : une copie dérivait à chaque réglage.

## Les QR codes

Six, vectoriels (`segno`, correction Q), tous décodés depuis le PDF final :

| page | cible |
|---|---|
| 2 | `mbc974.com/actualites/reportage-reunion-la-1ere-mbc-la-montagne/` |
| 2 | `instagram.com/mbc974.re` |
| 2 et 9 | `competitions.ffbb.com/.../clubs/reu0974104` |
| 10 | `wa.me/262692556458` |
| 10 | `mbc974.com/sponsor-club-basket-reunion/` |

Les plaques font 96 à 100 px : à l'impression A4 paysage, le plus dense
(45 modules) donne 0,40 mm par module, le seuil de scan fiable. **Ne pas les
réduire.** Le QR du reportage vise la page du club et non le reel Facebook :
plus durable, et le visiteur reste sur mbc974.com.

## À arbitrer par le bureau

- **La grille tarifaire.** Le dossier reprend les *noms* et les *montants*
  publics du club (MVP 500 €, All-Star 1 000 €) et place la proposition OLA à
  3 000 € au titre du « Hall of Fame, 2 000 € et plus ». La version précédente
  annonçait 500 / 1 500 / 3 000 €, ce que le site ne confirmait nulle part.
- **Dofé Studio** n'apparaît nulle part dans le dépôt : la page 6 s'appuie
  désormais sur ce que le club produit lui-même. Si le studio est engagé, le
  dire et la page sera reformulée.
- **Le nombre d'adhérents** ne vit dans aucun fichier du dépôt. « Près de 100 au
  18/09/2026 » vient du bureau et le dossier le mentionne comme tel.
- **Le plateau Mini-Basket Zone Nord des 14-15 novembre 2026**, que le MBC
  organise, est cité comme contrepartie du palier haut. Aucun chiffre de
  fréquentation n'existe : ne pas en inventer.


## Le dossier générique, page par page

| p | page | ce qu'elle apporte |
|---|---|---|
| 1 | Devenez partenaire | couverture, une seule scène photographique |
| 2 | Ouvrez le site | trois preuves à scanner : reportage, réseaux, fiche FFBB |
| 3 | Les chiffres, sans arrondi | près de 100 adhésions, et cinq chiffres sourcés |
| 4 | **Il reste de la place dans le dos** | les deux photos du 18/09 : la face porte trois marques, le dos aucune |
| 5 | Un quartier, deux terrains | le territoire, texte sur panneau et non sur la photo |
| 6 | Six supports, une saison | les six supports du site + l'audience Search Console |
| 7 | Comment on devient partenaire | les trois étapes de la page publique |
| 8 | Quatre formules, dès 200 € | Rookie / MVP / All-Star / Hall of Fame, au centime |
| 9 | Un club déclaré | FFBB, RNA, SIREN, siège, convention |
| 10 | Parlons-en, sans engagement | contact, WhatsApp, page partenaires |

La page 4 est l'apport du 18/09 : elle répond à « il nous reste de la place dans
le dos » par une **photographie**, pas par une phrase. Les deux clichés
(`DSC05076.jpg` le dos du 12, `DSC04996.jpg` la face du 34) montrent l'argument
sans commentaire.

## Ce qui a été écarté du one-pager de juin

Le visuel `VISUEL_One-Pager-Partenariat-MBC.jpg` porte trois affirmations que le
site ne confirme pas — elles ne sont pas reprises :

- **« +60 licenciés »** : c'était un OBJECTIF dans le PDF de juin, devenu un
  chiffre acquis sur le visuel. C'est ce qui a valu le retrait de l'image du
  site le 09/09/2026. Remplacé par « près de 100 adhésions et préinscriptions,
  effectifs communiqués par le club au 18/09/2026 », qualifié en note.
- **« U11 (9-10 ans) »** : le site dit « École de Basket, 7-10 ans ». Le dossier
  reprend les 8 formules de `data/creneaux.json`, celles du tunnel de paiement.
- **« Baby Basket (4-6 ans) »** : le site dit 3-6 ans.

L'avantage fiscal du one-pager (« article 238 bis du CGI ») n'est pas repris tel
quel : le dossier dit que selon la nature du soutien une contribution *peut*
relever du mécénat, et renvoie au conseil comptable du partenaire — c'est la
formulation de la page publique, et le club ne délivre aucun avis fiscal.
