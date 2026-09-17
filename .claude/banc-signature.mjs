// Banc de la signature du pied de page (.footer__credit) — la ligne
// « Made with ❤️ by Alex #MBC974 » qui ferme les 26 pages du site.
//
// Ce que le banc mesure, et pourquoi. Cette signature a deja vecu deux exces
// opposes : une ligne de 12 px a 2,59:1 de contraste (illisible), puis, le
// 15/09/2026, une ligne de 30,4 px — 2,4 fois le texte qui l'entoure, la plus
// grosse du pied. Les deux fois, personne n'avait de CHIFFRE : ni la taille
// rendue aux vraies largeurs, ni le rapport avec le texte voisin, ni le
// contraste reel. Le banc sort exactement ces trois-la, pour chaque element du
// bloc et a chaque largeur — y compris sous 500 px, ou --window-size ment
// (Chrome headless y plante un plancher) et ou seule l'emulation CDP dit vrai.
//
// La couleur est lue en pixels, pas en CSS : un degrade -webkit-text-fill-color
// sur .sig-name rend getComputedStyle().color inutilisable pour juger du
// contraste. On echantillonne donc la capture elle-meme.
//
// Prerequis : Node 22+ (WebSocket global), Chrome installe, et le serveur local
// du depot sur http://localhost:8000 (configuration « mbc-static »).
//
//   node .claude/banc-signature.mjs <etiquette> [LxH,LxH] [options]
//     LxH           defaut 390x844,768x1024,1440x900
//     --shots       une capture PNG du bloc par largeur (recadree sur lui)
//     --survol      en plus : la meme capture, souris sur la signature
//     --css=f.css   injecte une feuille d'essai apres style.min.css
//     --html=f.html remplace le bloc .footer__credit par le contenu du fichier,
//                   pour essayer une COMPOSITION entiere (markup + CSS) sans
//                   rien ecrire dans le depot. C'est ce qui permet de rendre
//                   plusieurs propositions cote a cote avant d'en choisir une.
//     --page=/x/    une autre page que l'accueil (le pied est le meme partout).
//                   Sous Git Bash, prefixer la commande de MSYS_NO_PATHCONV=1 :
//                   sinon « /matchs/ » est pris pour un chemin et reecrit en
//                   C:/Program Files/..., et Chrome repond « invalid URL ».
//
// Sorties HORS du depot : %TEMP%/mbc-banc-signature/<etiquette>.json (ou
// $MBC_BANC_SORTIE) et <etiquette>-<LxH>.png.
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME = process.env.MBC_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.MBC_BASE || 'http://localhost:8000';
const SORTIE = process.env.MBC_BANC_SORTIE || join(tmpdir(), 'mbc-banc-signature');
const argv = process.argv.slice(2);
const USAGE = 'usage : node .claude/banc-signature.mjs <etiquette> [LxH,...] [--shots] [--survol] [--css=f.css] [--page=/x/]\n';
if (!argv.length || argv[0].startsWith('--')) { process.stdout.write(USAGE); process.exit(2); }
const tag = argv[0];
const fmtArg = argv.slice(1).find(a => !a.startsWith('--'));
const formats = (fmtArg || '390x844,768x1024,1440x900').split(',');
const shots = argv.includes('--shots');
const survol = argv.includes('--survol');
const cssFic = (argv.find(a => a.startsWith('--css=')) || '').slice(6);
const htmlFic = (argv.find(a => a.startsWith('--html=')) || '').slice(7);
const page = (argv.find(a => a.startsWith('--page=')) || '--page=/index.html').slice(7);
// --marge=N : élargit le cadrage autour du bloc, pour le voir EN CONTEXTE
// (sous les liens légaux, par exemple) et pas seulement isolé.
const marge = Number((argv.find(a => a.startsWith('--marge=')) || '--marge=24').slice(8)) || 24;
const injecte = cssFic ? readFileSync(cssFic, 'utf8') : '';
const markup = htmlFic ? readFileSync(htmlFic, 'utf8') : '';
// --etapes=0,0.35,0.7,1 : une capture par palier d'avancement de l'animation,
// pour montrer un MOUVEMENT sur une image fixe. Sans l'option, tout est mene a
// son terme (p=1) : sinon une animation `both` pas encore declenchee figerait
// la capture sur son etat initial.
const etapesArg = (argv.find(a => a.startsWith('--etapes=')) || '').slice(9);
const etapes = etapesArg ? etapesArg.split(',').map(Number) : null;
const sleep = ms => new Promise(r => setTimeout(r, ms));

const prof = mkdtempSync(join(tmpdir(), 'mbcbancsig'));
const ch = spawn(CHROME, ['--headless=new', '--hide-scrollbars', '--no-first-run',
  '--no-default-browser-check', '--disable-extensions', '--remote-debugging-port=0',
  '--user-data-dir=' + prof, '--window-size=1280,800', 'about:blank'], { stdio: 'ignore' });

let ws, n = 0;
const pend = new Map(), ecoute = new Set();
const send = (method, params = {}, sessionId) => { const id = ++n; ws.send(JSON.stringify({ id, method, params, sessionId })); return new Promise((res, rej) => pend.set(id, { res, rej, method })); };
const once = (method, s, ms = 30000) => new Promise((res, rej) => { const t = setTimeout(() => { ecoute.delete(l); rej(new Error('timeout ' + method)); }, ms); const l = d => { if (d.method === method && d.sessionId === s) { clearTimeout(t); ecoute.delete(l); res(d.params); } }; ecoute.add(l); });
async function evalp(s, expression) { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, s); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 400)); return r.result.value; }

const AIDE = (css, html) => '(() => {\n' +
  // Le contraste WCAG se calcule sur la luminance relative : c'est la seule
  // definition qui fasse foi, et elle ne se devine pas a l'oeil sur un fond
  // #070d18 qui avale les teintes froides.
  'const lin = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };\n' +
  'const L = ([r, g, b]) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);\n' +
  'const ratio = (a, b) => { const x = L(a), y = L(b); return +(((Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05))).toFixed(2); };\n' +
  'const rgb = s => (s.match(/[\\d.]+/g) || [0, 0, 0]).slice(0, 3).map(Number);\n' +
  // Une teinte posee en rgb(... / .8) n'est PAS la teinte vue : c'est elle
  // melangee au fond. Lire les trois premiers canaux et ignorer l'alpha
  // surestime le contraste — 12,55:1 annonce pour 8,26:1 reel sur le
  // mot-diese. On compose donc avant de mesurer, toujours.
  'const alpha = s => { const m = s.match(/[\\d.]+/g); return m && m.length > 3 ? Number(m[3]) : 1; };\n' +
  'const compose = (s, fond) => { const c = rgb(s), a = alpha(s); return c.map((v, i) => Math.round(v * a + fond[i] * (1 - a))); };\n' +
  'const R = e => { const b = e.getBoundingClientRect(); return { x: Math.round(b.left), y: Math.round(b.top), w: Math.round(b.width), h: Math.round(b.height) }; };\n' +
  'const px = v => +parseFloat(v).toFixed(2);\n' +
  'window.__banc = {\n' +
  '  async prep() {\n' +
  '    const st = document.createElement("style"); st.id = "__banc";\n' +
  // Le bandeau cookies couvre le bas de page, la barre CTA mobile aussi : ni
  // l'un ni l'autre n'est ce qu'on mesure, et tous deux recouvrent le bloc.
  '    st.textContent = ".ccb{display:none!important}.float-cta{display:none!important}" + ' + JSON.stringify(css) + ';\n' +
  '    document.head.appendChild(st);\n' +
  // Le markup d essai remplace le bloc ENTIER (.footer__credit compris), pour
  // qu une proposition puisse changer la structure et pas seulement l habillage.
  // Pose avant fonts.ready : la nouvelle composition doit etre mesuree une fois
  // ses polices chargees, comme la vraie.
  '    const neuf = ' + JSON.stringify(html) + ';\n' +
  '    if (neuf) {\n' +
  '      const vieux = document.querySelector(".footer__credit");\n' +
  '      if (!vieux) throw new Error("bloc .footer__credit introuvable : rien a remplacer");\n' +
  '      const bac = document.createElement("div"); bac.innerHTML = neuf.trim();\n' +
  '      const el = bac.firstElementChild;\n' +
  '      if (!el) throw new Error("markup d essai vide");\n' +
  // Une composition peut renommer sa racine : on retient l element pose, pour
  // savoir quoi cadrer meme si la classe .footer__credit a disparu.
  '      vieux.replaceWith(el); window.__racine = el;\n' +
  // script.js a deja fait son querySelectorAll(".reveal") au chargement : un
  // bloc injecte APRES n est jamais observe, donc jamais marque .in, donc son
  // animation d arrivee ne part pas. Sur la vraie page la classe est dans le
  // HTML au chargement et l observateur la voit. On rejoue donc ici ce que le
  // script aurait fait, sans quoi le banc conclurait « aucune animation ».
  '      if (el.classList.contains("reveal")) el.classList.add("in");\n' +
  '    }\n' +
  '    document.documentElement.style.scrollBehavior = "auto";\n' +
  '    await document.fonts.ready;\n' +
  // content-visibility:auto fausse toute mesure hors ecran : on descend
  // reellement au pied avant de lire quoi que ce soit.
  '    window.scrollTo({ top: document.body.scrollHeight, behavior: "instant" });\n' +
  '    await new Promise(r => setTimeout(r, 700));\n' +
  '    const c = window.__racine || document.querySelector(".footer__credit");\n' +
  '    if (c) c.scrollIntoView({ block: "center", behavior: "instant" });\n' +
  '    await new Promise(r => setTimeout(r, 500));\n' +
  '    return !!c;\n' +
  '  },\n' +
  '  mesures() {\n' +
  '    const fond = getComputedStyle(document.querySelector(".site-footer")).backgroundColor;\n' +
  // Le pied peut etre transparent : on remonte alors au fond de la page.
  '    const fondRgb = /rgba?\\(0, 0, 0, 0\\)/.test(fond) ? rgb(getComputedStyle(document.body).backgroundColor) : rgb(fond);\n' +
  '    const cible = {\n' +
  '      credit: ".footer__credit", role: ".footer__credit-k", signature: ".footer__signature",\n' +
  '      nom: ".sig-name", coeur: ".sig-heart", diese: ".footer__hand",\n' +
  '      plaque: ".footer__plaque", cartel: ".footer__cartel", poincon: ".footer__poincon",\n' +
  // Les deux temoins : le texte courant du pied, auquel on compare tout.
  '      temoinLegal: ".footer__legal", temoinLien: ".footer__links a",\n' +
  '      liensLegaux: ".footer__links"\n' +
  '    };\n' +
  '    const out = {};\n' +
  '    for (const [k, sel] of Object.entries(cible)) {\n' +
  '      const e = document.querySelector(sel);\n' +
  '      if (!e) { out[k] = null; continue; }\n' +
  '      const cs = getComputedStyle(e);\n' +
  '      const couleur = cs.webkitTextFillColor && cs.webkitTextFillColor !== cs.color ? cs.webkitTextFillColor : cs.color;\n' +
  '      const transparent = /rgba?\\([^)]*,\\s*0\\)/.test(couleur);\n' +
  // Un SVG n'est pas peint par `color` mais par `fill` : lire color sur le
  // coeur rendrait la teinte HERITEE, jamais celle qu'on voit.
  '      const peinture = e.tagName.toLowerCase() === "svg" && cs.fill && cs.fill !== "none" ? cs.fill : couleur;\n' +
  '      out[k] = { sel, taillePx: px(cs.fontSize), graisse: cs.fontWeight,\n' +
  '        police: cs.fontFamily.split(",")[0].replace(/"/g, ""),\n' +
  '        casse: cs.textTransform, interlettre: cs.letterSpacing,\n' +
  '        couleur: peinture, composee: "rgb(" + compose(peinture, fondRgb).join(", ") + ")",\n' +
  // Le soulignement de .sig-name est un background-image en deux couches : sa
  // LARGEUR est l etat (0 au repos, 100% encre). C est ce qu il faut lire pour
  // prouver qu un survol fait quelque chose.
  '        fondImage: cs.backgroundSize === "auto" ? null : cs.backgroundSize,\n' +
  // Le defaut que la planche n avait pas montre : deux lignes d un meme
  // drapeau qui ne commencent pas au meme x. display / width / justify-self
  // sont les trois seules valeurs qui disent laquelle des regles gagne.
  '        calage: [cs.display, cs.width, cs.justifySelf, cs.textAlign, cs.marginLeft].join(" | "),\n' +
  '        opacite: +cs.opacity,\n' +
  // Un degrade text-clip rend la couleur calculee inutilisable : on le dit,
  // et c'est l'echantillon en pixels qui tranchera.
  '        degrade: transparent ? cs.backgroundImage.slice(0, 80) : null,\n' +
  '        contraste: transparent ? null : ratio(compose(peinture, fondRgb), fondRgb),\n' +
  '        boite: R(e) };\n' +
  '    }\n' +
  '    const c = window.__racine || document.querySelector(".footer__credit");\n' +
  '    const sig = out.signature, leg = out.temoinLegal;\n' +
  '    return { vw: innerWidth, vh: innerHeight, fond: fondRgb,\n' +
  '      hauteurBloc: c ? Math.round(c.getBoundingClientRect().height) : null,\n' +
  '      rapportAuTexteDuPied: sig && leg ? +(sig.taillePx / leg.taillePx).toFixed(2) : null,\n' +
  '      lignes: c ? [...c.querySelectorAll("p,div")].length : null,\n' +
  '      debordeAGauche: c ? Math.round(c.getBoundingClientRect().left) : null,\n' +
  // Une ligne centree trop large ne se voit pas : elle pousse la PAGE. Le seul
  // controle qui l attrape est la comparaison scrollWidth / clientWidth.
  '      debordementPage: document.documentElement.scrollWidth - document.documentElement.clientWidth,\n' +
  '      elements: out };\n' +
  '  },\n' +
  // Le clip de Page.captureScreenshot est en coordonnees de PAGE, pas de
  // fenetre : un rect de getBoundingClientRect() seul cadre le haut du
  // document, et sort une image vide qu'on prend pour un defaut de rendu.
  // Une capture fixe ne dit rien d une animation, et pire : une animation a
  // remplissage `both` qui n a pas encore demarre fige l element sur son etat
  // INITIAL (un trait a scaleX(0) est tout simplement invisible). On pilote
  // donc la progression a la main ; p=1 est l etat final, et c est le defaut
  // des captures, pour qu elles soient reproductibles.
  '  etape(p) {\n' +
  '    const vus = [];\n' +
  // Une horloge COMMUNE : sans elle, p=0,75 veut dire « 75 % de SA propre
  // duree » pour chaque animation, donc un trait retarde parait en avance et
  // la vignette ment sur le geste. On prend la fin la plus tardive du bloc.
  '    let fin = 0;\n' +
  '    document.getAnimations().forEach(a => {\n' +
  '      const t = a.effect && a.effect.target;\n' +
  '      if (!t || !t.closest || !t.closest(".footer__credit")) return;\n' +
  '      const e = a.effect.getComputedTiming().endTime;\n' +
  '      if (isFinite(e) && e > fin) fin = e;\n' +
  '    });\n' +
  '    document.getAnimations().forEach(a => {\n' +
  '      const t = a.effect && a.effect.target;\n' +
  '      if (!t || !t.closest || !t.closest(".footer__credit")) return;\n' +
  '      const ct = a.effect.getComputedTiming();\n' +
  '      if (!isFinite(ct.endTime)) return;\n' +
  '      try { a.pause(); a.currentTime = Math.min(p * fin, ct.endTime); } catch (e) { return; }\n' +
  '      vus.push([a.animationName || "?", Math.round(ct.endTime)]);\n' +
  '    });\n' +
  '    return vus;\n' +
  '  },\n' +
  '  zone() {\n' +
  '    const c = window.__racine || document.querySelector(".footer__credit");\n' +
  '    if (!c) return null;\n' +
  '    const b = c.getBoundingClientRect();\n' +
  '    const m = ' + marge + ';\n' +
  '    return { x: Math.max(0, Math.round(b.left + scrollX) - m), y: Math.max(0, Math.round(b.top + scrollY) - m),\n' +
  '      width: Math.min(innerWidth, Math.round(b.width) + m * 2), height: Math.round(b.height) + m * 2, scale: 2 };\n' +
  '  },\n' +
  '  centreSignature() {\n' +
  '    const e = document.querySelector(".sig-name") || document.querySelector(".footer__signature");\n' +
  '    const b = e.getBoundingClientRect();\n' +
  '    return { x: Math.round(b.left + b.width / 2), y: Math.round(b.top + b.height / 2) };\n' +
  '  }\n' +
  '};\n' +
  '})()';

async function main() {
  const f = join(prof, 'DevToolsActivePort');
  for (let i = 0; i < 150 && !existsSync(f); i++) await sleep(100);
  const [pt, path] = readFileSync(f, 'utf8').split('\n');
  ws = new WebSocket('ws://127.0.0.1:' + pt.trim() + path.trim());
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { const q = pend.get(d.id); pend.delete(d.id); d.error ? q.rej(new Error(q.method + ' ' + JSON.stringify(d.error))) : q.res(d.result); } else if (d.method) ecoute.forEach(l => l(d)); };
  mkdirSync(SORTIE, { recursive: true });
  const out = {};
  for (const fm of formats) {
    const [w, h] = fm.split('x').map(Number);
    const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
    const { sessionId: s } = await send('Target.attachToTarget', { targetId, flatten: true });
    await send('Page.enable', {}, s); await send('Runtime.enable', {}, s); await send('Network.enable', {}, s);
    await send('Network.setCacheDisabled', { cacheDisabled: true }, s);
    await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: w <= 640 }, s);
    await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] }, s);
    const load = once('Page.loadEventFired', s, 60000);
    await send('Page.navigate', { url: BASE + page + '?t=' + Date.now(), }, s);
    await load;
    await evalp(s, AIDE(injecte, markup));
    const trouve = await evalp(s, '__banc.prep()');
    if (!trouve) { out[fm] = { erreur: 'bloc .footer__credit introuvable' }; await send('Target.closeTarget', { targetId }); continue; }
    out[fm] = await evalp(s, '__banc.mesures()');
    out[fm].animations = await evalp(s, 'JSON.stringify(__banc.etape(1))').then(JSON.parse);
    if (shots) {
      const clip = await evalp(s, 'JSON.stringify(__banc.zone())').then(JSON.parse);
      const { data } = await send('Page.captureScreenshot', { format: 'png', clip }, s);
      writeFileSync(join(SORTIE, tag + '-' + fm + '.png'), Buffer.from(data, 'base64'));
    }
    if (etapes) {
      for (const p of etapes) {
        await evalp(s, '__banc.etape(' + p + ')');
        await sleep(90);
        const clip = await evalp(s, 'JSON.stringify(__banc.zone())').then(JSON.parse);
        const { data } = await send('Page.captureScreenshot', { format: 'png', clip }, s);
        writeFileSync(join(SORTIE, tag + '-' + fm + '-p' + String(Math.round(p * 100)).padStart(3, '0') + '.png'),
          Buffer.from(data, 'base64'));
      }
      await evalp(s, '__banc.etape(1)');
    }
    if (survol && w > 640) {
      // Le survol se pose par une VRAIE souris : une classe forcee ne
      // declencherait pas les memes regles (hover:hover / pointer:fine).
      const p = await evalp(s, 'JSON.stringify(__banc.centreSignature())').then(JSON.parse);
      await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: p.x, y: p.y, buttons: 0 }, s);
      await sleep(600);
      out[fm].survol = await evalp(s, '__banc.mesures()').then(m => m.elements);
      if (shots) {
        const clip = await evalp(s, 'JSON.stringify(__banc.zone())').then(JSON.parse);
        const { data } = await send('Page.captureScreenshot', { format: 'png', clip }, s);
        writeFileSync(join(SORTIE, tag + '-' + fm + '-survol.png'), Buffer.from(data, 'base64'));
      }
    }
    await send('Target.closeTarget', { targetId });
    const m = out[fm];
    process.stdout.write(fm + ' : signature ' + (m.elements.signature ? m.elements.signature.taillePx : '?') + ' px'
      + ', nom ' + (m.elements.nom ? m.elements.nom.taillePx : '?') + ' px'
      + ', bloc ' + m.hauteurBloc + ' px de haut'
      + ', x' + m.rapportAuTexteDuPied + ' le texte du pied\n');
  }
  const fic = join(SORTIE, tag + '.json');
  writeFileSync(fic, JSON.stringify(out, null, 1));
  process.stdout.write('-> ' + fic + '\n');
}

main().catch(e => { process.stdout.write('ERREUR ' + e.message + '\n'); process.exitCode = 1; })
  .finally(() => { try { ws && ws.close(); } catch (e) {} ch.kill(); setTimeout(() => { try { rmSync(prof, { recursive: true, force: true }); } catch (e) {} process.exit(); }, 800); });
