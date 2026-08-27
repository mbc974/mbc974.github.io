# Maintenance technique — mbc974.com

Complément au [README](README.md), qui couvre déjà la structure, l'hébergement et le SEO.
Ce document rassemble ce qui n'y figure pas : analytics, RGPD, sécurité, accessibilité, tests
et tâches qui ne peuvent pas être faites depuis le dépôt.

---

## 1. Règle absolue après modification de `style.css` ou `script.js`

```bash
python .claude/bump-assets.py
```

Le script recalcule l'empreinte des deux fichiers, met à jour le `?v=…` dans **toutes** les pages
et le nom du cache du service worker. **Sans ce bump, les visiteurs gardent l'ancienne CSS** :
le service worker sert alors une feuille périmée sur un HTML à jour, et la mise en page casse.

Pour les **images**, la règle est différente : une nouvelle photo = **un nouveau nom de fichier**.
Le service worker met les médias en cache par leur nom ; réutiliser un nom sert l'ancienne image.

---

## 2. Lancer le site en local

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/static-server.ps1 -Port 8010
```

Puis ouvrir `http://localhost:8010`. Aucun build, aucune dépendance npm : les fichiers sont servis tels quels.

---

## 3. Analytics — catalogue des événements

**Plausible est préparé mais volontairement désactivé** : la balise est commentée dans le `<head>`
de chaque page. Aucune donnée n'est collectée aujourd'hui.

Le code de suivi est **centralisé dans `script.js`** (un seul écouteur délégué sur `document`,
pas de snippets dispersés dans le HTML). Il est inerte tant que `window.plausible` n'existe pas :

```js
function track(name){ if (typeof window.plausible === 'function') window.plausible(name); }
```

| Événement | Déclencheur | Objectif |
|---|---|---|
| `Inscription Yapla` | lien vers `yapla.com` (hors campagne/authentification) | conversion principale |
| `Don Yapla` | lien Yapla contenant `campaign` | don |
| `Connexion espace membre` | lien Yapla contenant `authentication` | usage adhérent |
| `WhatsApp` | tout lien `wa.me` | prise de contact |
| `WhatsApp essai` | lien `wa.me` dont le message contient « essai » | demande d'essai qualifiée |
| `Je m inscris` | tout lien vers `/adhesion.html` | intention d'inscription |
| `Appel telephone` | lien `tel:` | contact direct |
| `E-mail` | lien `mailto:` | contact direct |
| `Itineraire Maps` | lien Google Maps | intention de venir |
| `Ajout agenda` | téléchargement d'un `.ics` | intention de venir à un match |
| `Carte chargee` | clic sur la façade de carte | mesure l'utilité de la carte |
| `Selecteur age` | clic sur un onglet du sélecteur d'âge | quelle tranche intéresse |
| `Dossier sponsor` | téléchargement du PDF partenaire | piste B2B |
| `Formulaire contact` | envoi du formulaire | contact abouti |

**Pour activer** : créer un compte Plausible, puis décommenter la ligne `<script defer data-domain="mbc974.com" …>`
dans le `<head>` de chaque page. Les événements remontent alors sans autre modification.
⚠️ Mettre aussi à jour `/confidentialite/` en conséquence.

---

## 4. RGPD — ce qui reste à valider par le bureau

La page `/confidentialite/` est en ligne, mais **trois points y sont volontairement laissés en attente**
plutôt que remplis avec des valeurs inventées. Ils sont signalés dans la page par un encadré :

1. **Durées de conservation** — à fixer pour (a) les demandes de contact sans suite,
   (b) les dossiers d'adhérents, (c) les archives comptables et sportives.
2. **Transferts hors UE** — les garanties (clauses contractuelles types, décision d'adéquation)
   doivent être confirmées service par service auprès de GitHub, Google et Web3Forms.
3. **Activation de Plausible** — si elle a lieu, la section « Cookies » doit être révisée.

Un juriste ou la personne référente RGPD du club doit relire la page avant de la considérer comme définitive.

**Sous-traitants réellement utilisés** (vérifiés dans le code, pas supposés) :
GitHub Pages (hébergement) · Web3Forms (formulaire) · Google Fonts (polices) ·
Google Maps (au clic uniquement) · Yapla (adhésion/paiement, hors site).

---

## 5. Sécurité — limite de plateforme, mesurée

Relevé sur la production le 27/08/2026 :

| En-tête | État |
|---|---|
| `Strict-Transport-Security` | **absent** |
| `Content-Security-Policy` | **absent** |
| `X-Content-Type-Options` | **absent** |
| `Referrer-Policy` | **absent** (en-tête) |
| `Permissions-Policy` | **absent** |
| `X-Frame-Options` | **absent** |

**GitHub Pages ne permet pas de définir d'en-têtes HTTP personnalisés.** Ce n'est pas un oubli de
configuration : la plateforme n'offre aucun mécanisme pour cela.

Ce qui est en place au niveau HTML, et qui fonctionne réellement :

- `<meta name="referrer" content="strict-origin-when-cross-origin">` sur **les 12 pages** ;
- `rel="noopener"` sur **les 94 liens** `target="_blank"` (protection contre le tabnabbing) ;
- l'iframe Google Maps est créée avec un attribut `sandbox` restrictif.

**Aucune CSP en `<meta>` n'a été ajoutée délibérément.** Une CSP posée en meta ne couvre ni
`frame-ancestors` ni le mode `report-only` : elle donnerait une fausse impression de protection
tout en risquant de casser Yapla, Google Fonts et la carte.

**La seule vraie solution** est de placer un proxy devant le site (Cloudflare en offre gratuite) et
d'y définir les en-têtes. C'est un changement d'infrastructure : il n'a pas été engagé sans validation.
Domaines à autoriser le jour où une CSP sera écrite : `fonts.googleapis.com`, `fonts.gstatic.com`,
`api.web3forms.com`, `www.google.com` (maps), `plausible.io` (si activé), `*.yapla.com`.

---

## 6. Accessibilité — règles à ne pas casser

- **Contraste** : tout texte doit atteindre 4,5:1 (3:1 au-delà de 24 px, ou 18,7 px en gras).
  Le vert « Adhésion gratuite » a été assombri pour cette raison (3,79 → 5,00:1).
  Le texte sur fond orange est **quasi-noir** (`#190f04`), jamais blanc : c'est ce qui le rend lisible.
- **`inert`** : la lightbox porte `inert` + `aria-hidden` quand elle est fermée, retirés à l'ouverture.
  Ne jamais séparer les deux.
- **Sélecteur d'âge** : les 6 panneaux sont dans le HTML. Le script *retire* `hidden`, il ne l'ajoute pas —
  sans JavaScript, le premier panneau reste ouvert et les liens restent atteignables.
- **`prefers-reduced-motion`** : un bloc dédié désactive reveal, parallaxe et animations continues.
  Toute nouvelle animation doit y être ajoutée.
- **Marquees** : les clones sont `aria-hidden="true"` et `display:none` — jamais focusables.

---

## 7. Tests avant publication

Il n'y a pas de CI. Les contrôles se font en local :

```bash
node --check script.js                 # syntaxe JS
python -c "s=open('style.css',encoding='utf-8').read(); print(s.count('{'), s.count('}'))"
python -c "import xml.dom.minidom; xml.dom.minidom.parse('sitemap.xml')"
```

Puis, sur le serveur local, vérifier page par page : HTTP 200, un seul `<h1>`, JSON-LD qui parse,
aucun débordement horizontal en 320 / 375 / 768 / 1024 / 1440 / 1920 px, aucune erreur console.

---

## 8. Tâches impossibles depuis le dépôt

| Tâche | Pourquoi externe | Priorité |
|---|---|---|
| Soumettre le sitemap à Search Console | nécessite l'accès au compte | haute |
| Compléter Google Business Profile | plateforme externe | haute |
| Valider la page confidentialité | décision juridique du bureau | haute |
| Harmoniser les fiches FFBB sous « La Montagne Basket Club » | back-office FFBB | moyenne |
| Activer Plausible | création de compte payant | moyenne |
| En-têtes de sécurité via Cloudflare | changement d'infrastructure | moyenne |
| Citations locales / backlinks | relations extérieures | basse |

---

*Passion · Respect · Solidarité · Engagement*
