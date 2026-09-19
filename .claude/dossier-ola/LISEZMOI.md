# Les dossiers de partenariat du MBC

**Trois** dossiers, un seul socle. 16:9 (1280 × 720 px = 960 × 540 pt =
13,333 × 7,5 in, le format standard des présentations 16:9).

| dossier | pages | destinataire | générateur |
|---|---|---|---|
| `dossier.pdf` | 10 | **OLA Energy**, nommé à chaque page | `dossier.py` + `contenu.py` |
| `dossier-general.pdf` | 10 | tout partenaire — version **institutionnelle** | `dossier_general.py` + `contenu_general.py` |
| **`dossier-v3.pdf`** | **8** | tout partenaire — version **commerciale** (V3.1) | `dossier_v3.py` + `contenu_v3.py` |
| `dossier-v3-sans-contact.pdf` | 8 | idem, **sans contact nominatif** en page 8 | `python dossier_v3.py --sans-contact` |

⚠️ **`dossier_general.py` l. 442 imprime « Bilan des retombées mesurées. »** — une
promesse que le dépôt contredit : le club ne mesure ni fréquentation, ni clics
(aucun paramètre `utm_` nulle part), ni audience réseaux. La V3.1 ne promet
qu'« en fin de saison : supports diffusés, publications et liens ». Si le v2
circule encore, cette ligne est à corriger.

La V3 remplace le générique : même socle, même rigueur de sourcing, mais elle
répond dans l'ordre aux questions d'un dirigeant au lieu de présenter le club.
Voir « La V3, page par page » en fin de fichier.

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

Pour la V3 :

```bash
python assets_v3.py           # communaute.jpg, reportage.jpg, maillot-dos-large.jpg
python dossier_v3.py          # -> dossier-v3.html
python render.py dossier-v3.html dossier-v3.pdf out-v3
MBC_GENERATEUR=dossier_v3 MBC_SANS_MENTION=1 python verifier.py dossier-v3.html dossier-v3.pdf
```

`MBC_GENERATEUR` dit au garde-fou de quel générateur importer les décrochages
intérieurs : les trois dossiers n'ont pas les mêmes gouttières. `MBC_SANS_MENTION`
liste les pages qui ne portent PAS de mention (donc dont la bande basse est
libre) : `1,10` pour les dossiers de dix pages, `1` pour la V3, dont la page de
clôture en porte une. Le nombre de pages de contenu, lui, n'est plus écrit en
dur : le garde-fou prend toutes les pages sauf la couverture et la clôture.

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


## La V3, page par page

Le v2 était rigoureux et institutionnel : il expliquait *qui nous sommes* et
*ce que nous avons*. Un dirigeant qui le refermait savait tout du club et rien
de ce qu'il achetait. La V3 ne change pas les faits — elle change l'ordre des
questions.

| p | page | la question à laquelle elle répond |
|---|---|---|
| 1 | Devenez partenaire | *(couverture)* |
| 2 | Né en 2026. Déjà là. | combien pesez-vous ? |
| 3 | Des preuves, pas des promesses | pourquoi vous croire ? |
| 4 | **Qui votre marque va toucher** | qui vais-je toucher ? — **page neuve** |
| 5 | **Ce que votre soutien permet** | à quoi sert mon argent ? — **page neuve** |
| 6 | Votre marque, avec le MBC | qu'est-ce que je reçois ? |
| 7 | Quatre formules, dès 200 € | combien ça coûte ? |
| 8 | Faisons équipe | comment on commence ? |

Deux pages du v2 disparaissent en tant que telles, sans qu'aucune information
soit perdue : « Comment on devient partenaire » (une page pour trois étapes que
la clôture répétait déjà) et « Un club déclaré » (une page pour un RNA et un
SIREN). Toutes deux tiennent dans une colonne de la page 8. Et deux pages
fusionnent : « Il reste de la place dans le dos » et « Six supports » disaient
deux fois la même promesse — la page 6 porte les supports à gauche et
l'emplacement libre du dos à droite, photo comprise.

### Ce que la V3 corrige dans le fond du v2

- **« 4 supports de diffusion actifs »** était faux : la page publique en liste
  six, et la page 6 du v2 s'intitulait elle-même « SIX SUPPORTS ». Le chiffre
  disparaît. (Même correction que sur le site le 18/09.)
- **« maillot domicile et extérieur »** : le 11/09 était un match à domicile et
  l'équipe portait le blanc, alors que le rendu étiqueté « domicile » du site
  est bleu nuit. Tant que le bureau n'a pas tranché, la V3 écrit « le maillot ».
- **« Trois preuves à un clic. Aucune n'a besoin de nous. »** : défensif. On ne
  plaide pas sa bonne foi, on la montre.
- **Les contreparties vagues** — « visibilité premium », « mise en avant toute
  la saison », « présence forte » — portent désormais une ligne de précision en
  gris. Aucune contrepartie n'a été ajoutée : la grille publique est reprise au
  centime, la précision ne fait que dire *où*.

### Deux sources que le v2 n'exploitait pas

- **mbc974.com/soutenir-le-club/** publie quatre repères de financement
  (20 € un ballon, 50 € un jeu de maillots floqué, 95 € une licence offerte,
  300 € le déplacement d'une équipe) et un objectif de saison (10 licences
  solidaires). C'est toute la page 5 — sans qu'aucun montant soit inventé. La
  mention précise qu'un partenariat entre au budget général et n'est pas affecté
  à une dépense précise : sponsoring et mécénat ne se confondent pas.
- **« Cinq entreprises et associations soutiennent déjà le club, aux côtés de
  notre équipementier »** : c'est la preuve sociale que le v2 n'utilisait nulle
  part. Elle est page 3, **en toutes lettres et sans logos** : six logos
  lisibles demandent 760 × 44 px, que la page n'a pas sans réduire les QR sous
  le seuil de scan. Une preuve illisible ne prouve rien.

### Les photos

Le v2 illustrait une communauté par un **gymnase vide** (p5) et un plateau
désert. La V3 met des personnes : `communaute.jpg` (page 4) montre des enfants
en maillot MBC assis en cercle **et leurs parents dans le même cadre**,
`reportage.jpg` (page 3) le sujet de Réunion La 1ère, `maillot-dos-large.jpg`
(page 6) le dos vierge du maillot. Les trois sortent de `assets_v3.py`.

### Le piège de la page 4

Une photo pleine page et un texte lisible tirent en sens inverse. Deux voiles,
un par bord, portent l'en-tête et les publics ; **le centre de l'image reste
intact**. Un voile unique, même dégradé, noircissait les enfants.

### Le piège des lignes qui se replient

`bloc.txt()` compense le side bearing du **premier glyphe** du bloc. Une ligne
qui se replie toute seule voit donc sa seconde ligne partir de travers, d'autant
plus que le glyphe diffère : le garde-fou a mesuré **2 px** sur une ligne
commençant par « j ». Deux parades, toutes deux dans la V3 : `dossier_v3.tient()`
mesure chaque ligne censée tenir sur une ligne et le dit à la génération, et les
textes qui font vraiment plusieurs lignes sont écrits **une ligne par entrée de
liste** et posés par `bloc.lignes()` — chacune reçoit alors sa propre
compensation. C'est l'idiome déjà retenu pour les titres.


## La V3.1 — la finition commerciale

La V3 avait la bonne structure ; il lui manquait la finition. La V3.1 ne crée
aucune page et n'en supprime aucune : elle corrige ce qu'un acheteur aurait pu
retenir contre le club, et rend le PDF utilisable à l'écran.

### Le PDF est cliquable — 18 liens

Chrome headless émet **une annotation de lien par `<a href>`**. On rend donc
cliquable le texte *déjà écrit* — une adresse, un intitulé de preuve — au lieu
d'ajouter des « cliquez ici » : `bloc.lien()` pour le texte, `bloc.zone()` pour
une plaque de QR, et `dossier_v3.mention()` pour les URL citées dans les
mentions. `css.py` neutralise le bleu souligné du navigateur.

| page | ce qui est cliquable |
|---|---|
| 1 | `mbc974.com` du pied |
| 3 | l'étiquette et **la photo** du reportage, les 3 plaques de QR, les 3 intitulés |
| 2, 4, 5, 7 | l'URL citée dans la mention (créneaux, soutenir, page partenaires) |
| 6 | « Site mbc974.com et réseaux du club » |
| 8 | l'e-mail (`mailto:`), le téléphone (`tel:+262…`), les 2 plaques de QR |

**Le QR WhatsApp reste sur l'URL nue, le lien porte le message pré-rempli.**
Mesuré : avec `?text=`, le code passe de 33 à 61 modules, soit 0,312 mm par
module à l'impression A4 paysage — sous le seuil de scan fiable de 0,40 mm. Un
clic n'a pas cette contrainte. Le papier scanne, l'écran clique. La légende ne
promet donc plus « message pré-rempli », qui était faux pour le scan.

### Le défaut le plus lourd que la V3.1 corrige

La page 6 décrivait toute la chaîne de diffusion **sans dire à partir de quelle
formule chaque support démarre**. Un commerçant qui signait à 200 € après
l'avoir lue pouvait croire de bonne foi qu'il aurait les affiches, les flyers et
les événements — que la page 7 réserve à 500 €, et le maillot à 1 000 €. Chaque
ligne porte désormais son palier en regard de son intitulé. La page publique du
site souffre du même défaut (« Tous les autres supports démarrent dès la
signature ») : **à corriger là-bas aussi.**

### Ce qui n'était pas imprimé

Cinq variables étaient définies et jamais rendues : `P6_RARETE_ETAT`,
`P7_FIDELITE`, `P7_SURMESURE`, `P8_SIEGE`, `P8_CONVENTION`. Le mot
« Disponible. » — le seul qui dise que l'emplacement du dos est à prendre — ne
figurait pas dans le PDF. Il est rendu ; la remise fidélité vit dans la mention
de la page 7 ; le siège social dans celle de la page 8 ; les deux variables
mortes restantes ont été supprimées.

### Le garde-fou qui manquait : la mention qui REMONTE

`controle_bande` interdit au contenu de descendre sous 588 px. Rien n'interdisait
à la **mention** de monter. Or elle est ancrée par le bas : une ligne de plus et
tout le bloc remonte d'un interligne, **sans qu'une seule coordonnée change dans
le code**. Trois mentions sont passées à trois lignes en V3.1 et sont venues se
poser sur le bas des cartes et sur le numéro de téléphone.

`controle_mention` compte les lignes de la mention et en exige **deux au plus**.
Deux pièges rencontrés en l'écrivant, tous deux instructifs :

1. **On ne la reconnaît ni à sa taille ni à son bloc.** Les précisions des cartes
   de la page 7 et l'offre du maillot page 6 emploient le même corps de 13 px ;
   et le découpage en blocs de PyMuPDF varie — page 4, la signature et le numéro
   avaient fusionné et la mention échappait au contrôle. On part de sa ligne la
   plus basse et on remonte tant que la suivante est à un interligne.
2. **L'interligne se mesure, il ne se calcule pas.** Une première version le
   tirait de `grille.py` (13 × 1,35 = 17,55 px) et ne trouvait jamais la deuxième
   ligne : **Chrome arrondit et pose les siennes à 17,00 px**. Le garde-fou a
   passé deux sabotages de suite en annonçant que tout allait bien.

Prouvé mordant : on rallonge la mention de la page 5 jusqu'à trois lignes, on
régénère pour de vrai, il crie. *(Et le premier essai de sabotage n'avait rien
saboté — le motif de `str.replace` ne correspondait pas au fichier, donc le test
annonçait « aveugle » sans avoir rien changé. D'où l'assertion dans le script.)*

### Le garde-fou local : le chapô qui se replie

`dossier_v3.tient()` mesurait déjà chaque ligne censée tenir sur une ligne ; il
ne regardait pas les sous-titres. Or un chapô qui se replie descend sa seconde
ligne à 221 px, là où les cartes de la page 7 commencent à 226 — et comme elles
sont peintes **après**, elles la recouvrent : l'information disparaît sans que
rien ne déborde ni ne chevauche visiblement. `entete()` mesure désormais son
chapô.

### Ce que la vérification adverse a rattrapé

Une revue en 31 agents a testé 72 affirmations contre le dépôt : 26 confirmées,
22 à nuancer, 17 contredites, 7 sans source. Les corrections qui en découlent :

- **« retombées mesurables »** dans le bilan partenaire : le club ne mesure rien
  — ni fréquentation, ni clics, ni audience réseaux — et les pages 3 et 4 le
  disent. Le bilan ne promet plus que « supports diffusés, publications et
  liens ».
- **« Secrétaire »** n'existe nulle part dans le dépôt. Le seul titre que le
  site attribue à un Alexandre est **« Responsable Administratif »**, dans le
  JSON-LD, avec le prénom seul. À trancher par le bureau.
- **« aucun chiffre d'audience »** (page 3) contredisait la page 6, qui en
  avance un. La phrase est bornée au reportage, où elle est exacte.
- **Le mécénat** (page 8) contredisait la page 5 : le mécénat suppose l'absence
  de contrepartie significative, et le dossier vend quatre formules de
  contreparties. La mention ne dit plus que ce qui est certain — il y a une
  facture.
- **« 9 réceptions » et « 30 dates »** ne portent pas sur le même périmètre : le
  9 compte les U13, le 30 non. La mention permet désormais de refaire les deux.
- **« Jeux de maillots floqués »** (page 5) employait le mot que les pages 6 et 7
  réservent au logo du *partenaire* : un lecteur pressé comprenait que son
  soutien payait son propre flocage. → « aux couleurs du club ».
- **« une affiche par réception »** devenait un engagement chiffrable dès que la
  page 4 annonce 9 réceptions — dont 4 U13, dont rien ne dit qu'elles ont une
  affiche. → « à chaque réception ».
- **« Tout est adaptable »** (page 7) ouvrait la négociation du PRIX au-dessus
  d'une grille dite « reprise au centime ». → « Contreparties adaptables ».
- **L'encart du dos du maillot** ne portait pas d'astérisque, alors que toutes
  les autres mentions de flocage en portaient une : c'était la promesse la plus
  forte de la page et la seule sans réserve.


### Ce que la relecture par trois acheteurs a changé

Trois profils ont lu la V3.1 comme des acheteurs, pas comme des relecteurs — un
dirigeant de commerce à 500 €, un responsable marketing à 1 000 €, un groupe
régional à 2 000 € — puis un avocat du dossier a plaidé contre chaque objection
pour écarter celles auxquelles le dossier répondait déjà. **Aucun ne renonce,
les trois décrochent le téléphone.** Ce qui les convainc, invariablement : les
notes qui démontent les chiffres du club avant qu'eux ne le fassent.

Huit objections étaient corrigeables sans rien inventer :

- **« les précisions en gris n'ajoutent aucune contrepartie »** se retournait
  contre le club : l'acheteur à 500 € y lisait « ces lignes ne nous engagent à
  rien ». → « situent les contreparties, elles n'en créent pas ».
- **Les cinq partenaires n'étaient pas nommés** sur une page intitulée « DES
  PREUVES », et **InPlay était cité deux fois sans jamais être présenté**. Les
  trois acheteurs ont posé la même question : « qui a déjà signé ? ». Les cinq
  sont nommés, InPlay est défini.
- **Deux « neuf » à deux lignes d'écart** page 4 — « 9 réceptions » et « neuf
  restent conditionnelles » — faisaient comprendre que les réceptions étaient
  conditionnelles, donc les affiches achetées aussi. → « 30 dates, dont
  21 acquises ».
- **La page 5 se démentait elle-même** : elle posait une équivalence en gros
  (20 € = un ballon) que sa mention reprenait en bas de page. Les mêmes chiffres
  présentés comme des **ordres de grandeur des dépenses** ne promettent plus de
  fléchage. → « CE QUE COÛTE UNE SAISON, EN REPÈRES ».
- **« Flocage, bâche OU panneau »** page 6 contre deux items distincts page 7 :
  à 1 000 €, l'acheteur attend les deux. → « Flocage **et** bâche ou panneau ».
- **« Logo floqué sur les maillots »** ne disait pas quel emplacement, alors que
  la page 6 montre le dos en pleine page. → « emplacement défini avec le club ».
- **« Partenaire titre d'un événement »** ne nommait ni ne datait aucun
  événement. → « événement défini à la signature ».
- **Le niveau de jeu n'apparaissait nulle part** : « championnat FFBB » couvre
  du départemental comme du régional. → « Seniors en Pré-Régionale, zone Nord »
  (`data/matchs.json`).

### Ce qui reste, et qui n'est pas de mon ressort

Les trois acheteurs butent sur les mêmes quatre manques, et aucun ne se comble
sans une décision du bureau :

1. **Aucun volume garanti** dans les formules — combien d'affiches, de flyers,
   de publications, d'invitations. « À chaque réception » n'est pas exigible en
   avril.
2. **Aucune clause de substitution** derrière l'astérisque : si la Ville refuse
   la bâche ou si l'équipementier ne floque pas, l'acheteur à 1 000 € ne sait pas
   ce qu'il récupère. C'est l'objection qui lui fait fermer le dossier.
3. **Le périmètre de l'exclusivité** — secteur ? code NAF ? territoire ? et
   quels secteurs sont déjà pris par les cinq partenaires ? C'est la seule chose
   qu'achète le palier à 2 000 €.
4. **Le régime fiscal** : HT ou TTC, association assujettie à la TVA ou non,
   facture de parrainage déductible. Les trois profils posent la question, et
   une comptable bloque un bon de commande dessus.

S'y ajoutent, plus secondaires : la date du bilan partenaire, la durée du
partenariat selon le mois de signature, le nombre d'abonnés par réseau, un ordre
de grandeur du public d'une réception, et la décomposition du « près de 100 »
entre adhésions et préinscriptions.
