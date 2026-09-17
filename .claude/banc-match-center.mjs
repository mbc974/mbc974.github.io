// Banc du Match Center (V181) dans un vrai Chrome piloté en CDP.
// Il faut un serveur local : « mbc-static » (8000) ou « mbc-static-8010 ».
//   node .claude/banc-match-center.mjs [--base=http://localhost:8010] [--vite]
// 1. Par format (375, 390, 430, 768, 1440 de large, viewport émulé exact —
//    pas --window-size, que Chrome headless clampe à 500 px) : /matchs/ en
//    haut, la saison, un mois plus bas ; l'accueil sur #matchs. Mesures de
//    débordement + captures.
// 2. Les filtres (souris et vraie touche Espace), à 390.
// 3. Sans JavaScript, et en mouvement réduit.
// 4. Quatre instants simulés : Date est remplacée AVANT les scripts de la
//    page (Page.addScriptToEvaluateOnNewDocument), et l'on vérifie que les
//    cartes et les dates basculent seules, sans republication.
// 5. Les pages _banc-mc-*.html de la racine s'il y en a (générées à une autre
//    date avec MBC_MAINTENANT, voir MAINTENANCE.md § 26).
// Captures PNG et rapport JSON dans %TEMP%\mbc-banc-match-center.
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync, mkdirSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = join(tmpdir(), 'mbc-banc-match-center');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const opt = n => (process.argv.find(a => a.startsWith('--' + n + '=')) || '').split('=').slice(1).join('=');
const BASE = opt('base') || 'http://localhost:8010';
const VITE = process.argv.includes('--vite');          // un seul format, pas de captures annexes
const RACINE = join(dirname(fileURLToPath(import.meta.url)), '..');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const prof = mkdtempSync(join(tmpdir(), 'mbcmc'));
const ch = spawn(CHROME, ['--headless=new', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', '--remote-debugging-port=0', '--user-data-dir=' + prof, '--window-size=1280,800', 'about:blank'], { stdio: 'ignore' });
let ws, n = 0; const pend = new Map(), ecoute = new Set();
const send = (method, params = {}, sessionId) => { const id = ++n; ws.send(JSON.stringify({ id, method, params, sessionId })); return new Promise((res, rej) => pend.set(id, { res, rej, method })); };
const once = (method, s, ms = 30000) => new Promise((res, rej) => { const t = setTimeout(() => { ecoute.delete(l); rej(new Error('timeout ' + method)); }, ms); const l = d => { if (d.method === method && d.sessionId === s) { clearTimeout(t); ecoute.delete(l); res(d.params); } }; ecoute.add(l); });
async function evalp(s, expression) { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, s); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 400)); return r.result.value; }

// Ce que l'on mesure, dans la page. Aucune dépendance au script du site.
const MESURE = `(() => {
  const q = s => document.querySelector(s), qa = s => [...document.querySelectorAll(s)];
  const r = e => { if (!e) return null; const b = e.getBoundingClientRect(); return { x: Math.round(b.left), y: Math.round(b.top + scrollY), w: Math.round(b.width), h: Math.round(b.height) }; };
  const vw = document.documentElement.clientWidth;
  const hors = qa('.mc *, .ms *, .ms-format *').filter(e => { const b = e.getBoundingClientRect(); return b.width > 0 && (b.right > vw + .5 || b.left < -.5) && !e.closest('.sr-only'); })
    .slice(0, 6).map(e => (e.getAttribute('class') || e.tagName) + ' ' + Math.round(e.getBoundingClientRect().right));
  const carte = s => { const c = q('[data-mc-slot="' + s + '"]'); const a = c && c.querySelector('[data-id]'); return c ? { cache: c.hidden, id: a && a.getAttribute('data-id'), txt: a && a.textContent.replace(/\\s+/g, ' ').trim().slice(0, 170), box: r(a) } : null; };
  const vis = qa('.mc-i').filter(li => !li.hidden && li.offsetParent !== null);
  return {
    iw: innerWidth, cw: vw, debord: document.documentElement.scrollWidth - vw, hors,
    dernier: carte('dernier'), prochain: carte('prochain'),
    cd: (q('[data-mc-slot="prochain"] [data-mc-cd]') || {}).hidden === false ? q('[data-mc-cd]').textContent : null,
    items: qa('.mc-i').length, visibles: vis.length,
    suivants: vis.slice(0, 5).map(li => li.getAttribute('data-id')),
    next: qa('.mc-i.is-next').map(li => li.getAttribute('data-id')),
    live: qa('.mc-i.is-live').map(li => li.getAttribute('data-id')),
    passes: qa('.mc-i.is-past').length,
    etats: qa('.mc-i__etat[data-avenir]').slice(0, 3).map(e => e.textContent),
    barre: q('[data-ms-bar]') ? !q('[data-ms-bar]').hidden : null,
    compte: (q('[data-ms-n]') || {}).textContent || null,
    vide: q('[data-ms-vide]') ? !q('[data-ms-vide]').hidden : null,
    moisCourant: (q('.ms-mois__a.is-courant') || {}).textContent || null,
    pre: qa('.is-pre').length,
    duo: r(q('.mc__duo')), premier: r(vis[0]),
    policeScore: (() => { const e = q('.mc-row__s'); return e ? getComputedStyle(e).fontSize + ' ' + getComputedStyle(e).fontFamily.split(',')[0] : null; })(),
    policeNom: (() => { const e = q('.mc-team__n'); return e ? getComputedStyle(e).fontSize : null; })(),
  };
})()`;

// Remplace Date avant tout script de la page : l'horloge avance normalement à
// partir de l'instant choisi, pour que setInterval et les comparaisons restent
// cohérents.
const horloge = iso => `(() => { const T = new Date('${iso}').getTime(), D0 = Date.now(), R = Date;
  class F extends R { constructor(...a) { if (a.length) super(...a); else super(T + (R.now() - D0)); } static now() { return T + (R.now() - D0); } }
  window.Date = F; })();`;

async function page(url, w, h, { reduce = false, noJs = false, iso = null } = {}) {
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId: s } = await send('Target.attachToTarget', { targetId, flatten: true });
  for (const d of ['Page', 'Runtime', 'Network', 'DOM', 'Log']) await send(d + '.enable', {}, s);
  await send('Network.setCacheDisabled', { cacheDisabled: true }, s);
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: w > 1000 ? 1 : 2, mobile: w <= 640 }, s);
  await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: reduce ? 'reduce' : 'no-preference' }] }, s);
  if (noJs) await send('Emulation.setScriptExecutionDisabled', { value: true }, s);
  if (iso) await send('Page.addScriptToEvaluateOnNewDocument', { source: horloge(iso) }, s);
  const erreurs = [];
  ecoute.add(d => { if (d.sessionId !== s) return;
    if (d.method === 'Runtime.exceptionThrown') erreurs.push(d.params.exceptionDetails.exception?.description?.slice(0, 200) || d.params.exceptionDetails.text);
    if (d.method === 'Log.entryAdded' && d.params.entry.level === 'error' && !/favicon|googletagmanager/.test(d.params.entry.url || '')) erreurs.push(d.params.entry.text.slice(0, 200)); });
  const load = once('Page.loadEventFired', s, 60000);
  await send('Page.navigate', { url: `${BASE}${url}${url.includes('?') ? '&' : '?'}t=${Date.now()}` }, s);
  await load;
  if (!noJs) await evalp(s, `(async () => { const st = document.createElement('style'); st.textContent = '.ccb{display:none!important}'; document.head.appendChild(st); await document.fonts.ready; await new Promise(r => setTimeout(r, 900)); })()`);
  else await sleep(1200);
  return { s, targetId, erreurs };
}
const tir = async (s, nom) => { const { data } = await send('Page.captureScreenshot', { format: 'png' }, s); writeFileSync(join(OUT, nom + '.png'), Buffer.from(data, 'base64')); };
// content-visibility:auto (posé sur .section) donne aux sections hors écran une
// hauteur de substitution : un seul saut calculé atterrit ailleurs (première
// version de ce banc : « l'accueil sur #matchs » montrait les créneaux). On
// répète scrollIntoView jusqu'à ce que la mise en page se stabilise.
const aller = async (s, sel, dec = 0) => {
  for (let k = 0; k < 4; k++) {
    await evalp(s, `(() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e) return; e.scrollIntoView({ block: 'start', behavior: 'instant' }); window.scrollBy({ top: -${dec}, behavior: 'instant' }); })()`);
    await sleep(320);
  }
  await sleep(800);
};

async function main() {
  const f = join(prof, 'DevToolsActivePort');
  for (let i = 0; i < 150 && !existsSync(f); i++) await sleep(100);
  const [pt, path] = readFileSync(f, 'utf8').split('\n');
  ws = new WebSocket(`ws://127.0.0.1:${pt.trim()}${path.trim()}`);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { const q = pend.get(d.id); pend.delete(d.id); d.error ? q.rej(new Error(q.method + JSON.stringify(d.error))) : q.res(d.result); } else if (d.method) ecoute.forEach(l => l(d)); };
  mkdirSync(OUT, { recursive: true });
  const R = { base: BASE, formats: {}, filtres: null, sansJs: null, reduit: null, instants: {}, bancs: {} };
  const formats = VITE ? [[390, 844]] : [[375, 812], [390, 844], [430, 932], [768, 1024], [1440, 900]];

  // 1. Formats
  for (const [w, h] of formats) {
    const F = {};
    { const { s, targetId, erreurs } = await page('/matchs/', w, h);
      F.matchs = await evalp(s, MESURE); await tir(s, `${w}-matchs-haut`);
      if (w < 980) { await aller(s, '[data-mc-slot="prochain"]', 80); await tir(s, `${w}-matchs-prochain`); }
      await aller(s, '#saison', 70); F.saison = await evalp(s, MESURE); await tir(s, `${w}-matchs-saison`);
      await aller(s, '#mois-2026-11', 70); await tir(s, `${w}-matchs-novembre`);
      await aller(s, '#format', 70); await tir(s, `${w}-matchs-format`);
      F.erreursMatchs = erreurs; await send('Target.closeTarget', { targetId }); }
    { const { s, targetId, erreurs } = await page('/index.html', w, h);
      await aller(s, '#matchs', 20); await sleep(600);
      F.accueil = await evalp(s, MESURE); await tir(s, `${w}-accueil-matchs`);
      await aller(s, '.mc-suite', 90); await tir(s, `${w}-accueil-suite`);
      F.erreursAccueil = erreurs; await send('Target.closeTarget', { targetId }); }
    R.formats[w + 'x' + h] = F;
    process.stdout.write(`${w}x${h} ok (débord matchs ${F.matchs.debord}, accueil ${F.accueil.debord})\n`);
  }

  // 2. Les filtres, à 390
  { const { s, targetId, erreurs } = await page('/matchs/', 390, 844);
    const clic = async (f, v) => { await evalp(s, `document.querySelector('.ms-f__b[data-f="${f}"][data-v="${v}"]').click()`); await sleep(500); return evalp(s, MESURE); };
    const F = {};
    F.coupe = await clic('genre', 'coupe');
    await aller(s, '#saison', 70); await tir(s, `390-filtre-coupe`);
    F.coupeDomicile = await clic('lieu', 'dom');
    F.domicile = await clic('genre', '');
    await tir(s, `390-filtre-domicile`);
    F.exterieur = await clic('lieu', 'ext');
    // Vraie touche Espace sur « Tous les lieux » : un bouton natif doit réagir.
    await evalp(s, `document.querySelector('.ms-f__b[data-f="lieu"][data-v=""]').focus()`);
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: ' ', code: 'Space', windowsVirtualKeyCode: 32, text: ' ' }, s);
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: ' ', code: 'Space', windowsVirtualKeyCode: 32 }, s);
    await sleep(500);
    F.clavier = await evalp(s, `({ presse: document.querySelector('.ms-f__b[data-f="lieu"][data-v=""]').getAttribute('aria-pressed'), visibles: [...document.querySelectorAll('.ms-m .mc-i')].filter(li => !li.hidden).length })`);
    F.erreurs = erreurs;
    R.filtres = F; await send('Target.closeTarget', { targetId }); }

  // 3. Sans JavaScript, puis en mouvement réduit
  { const { s, targetId } = await page('/matchs/', 390, 844, { noJs: true });
    const { root } = await send('DOM.getDocument', { depth: -1, pierce: false }, s);
    const nb = async sel => (await send('DOM.querySelectorAll', { nodeId: root.nodeId, selector: sel }, s)).nodeIds.length;
    R.sansJs = { items: await nb('.mc-i'), itemsCaches: await nb('.mc-i[hidden]'), barreCachee: await nb('[data-ms-bar][hidden]'),
      pre: await nb('.is-pre'), cartes: await nb('[data-mc-slot] [data-id]'), prochainJ2: await nb('[data-mc-slot="prochain"] [data-id="m-2026-09-18"]') };
    const sais = (await send('DOM.querySelector', { nodeId: root.nodeId, selector: '#mois-2026-10' }, s)).nodeId;
    await send('DOM.scrollIntoViewIfNeeded', { nodeId: sais }, s); await sleep(500);
    await tir(s, `390-sansjs-octobre`);
    await send('Target.closeTarget', { targetId }); }
  { const { s, targetId, erreurs } = await page('/matchs/', 1440, 900, { reduce: true });
    await aller(s, '#mois-2027-02', 70);
    R.reduit = { ...(await evalp(s, MESURE)), transitionMois: await evalp(s, `getComputedStyle(document.querySelector('.ms-m')).transitionDuration`), erreurs };
    await send('Target.closeTarget', { targetId }); }

  // 4. Les instants simulés
  const INSTANTS = {
    'j2-en-cours': '2026-09-18T21:00:00+04:00',
    'lendemain-j2': '2026-09-19T08:00:00+04:00',
    'jour-de-coupe': '2026-09-26T15:00:00+04:00',
    'veille-j5': '2026-10-22T18:00:00+04:00',
  };
  for (const [nom, iso] of Object.entries(INSTANTS)) {
    const I = {};
    for (const url of ['/matchs/', '/index.html']) {
      const { s, targetId, erreurs } = await page(url, 390, 844, { iso });
      if (url !== '/matchs/') await aller(s, '#matchs', 20);
      I[url] = { ...(await evalp(s, MESURE)), bandeau: await evalp(s, `(document.querySelector('#nxBand .nx__t') || {}).textContent || null`), erreurs };
      if (url === '/matchs/') { await tir(s, `instant-${nom}-matchs`); await aller(s, '#saison', 70); await tir(s, `instant-${nom}-saison`); }
      else { await sleep(500); await tir(s, `instant-${nom}-accueil`); }
      await send('Target.closeTarget', { targetId });
    }
    R.instants[nom] = I;
    process.stdout.write(`instant ${nom} ok\n`);
  }

  // 4 bis. Les U13 : la page, et les deux pièges de la cohabitation
  //
  // Les lignes des U13 vivent dans les mêmes listes .mc-i que celles des
  // seniors, sur l'accueil. Deux choses ne se voient qu'à une date précise :
  //   - le dimanche à midi, la rencontre U13 vient de finir et devient la plus
  //     récente de la page ; la carte « Dernier résultat » des seniors, elle,
  //     parle du vendredi. Elle doit RESTER (cartes(), filtre :not([data-equipe])) ;
  //   - la ligne U13 à venir doit porter « Prochain match » alors que la carte
  //     du haut montre, elle, la rencontre des seniors (prochainsParEquipe()).
  {
    const U = { formats: {}, instants: {} };
    for (const [w, h] of formats) {
      const { s, targetId, erreurs } = await page('/matchs/u13/', w, h);
      U.formats[w + 'x' + h] = { ...(await evalp(s, MESURE)), erreurs };
      await tir(s, `${w}-u13-haut`);
      await aller(s, '#saison', 70); await tir(s, `${w}-u13-saison`);
      await aller(s, '#format', 70); await tir(s, `${w}-u13-format`);
      await send('Target.closeTarget', { targetId });
      process.stdout.write(`u13 ${w}x${h} ok (débord ${U.formats[w + 'x' + h].debord})\n`);
    }
    const LIGNES = `(() => { const q = s => [...document.querySelectorAll(s)];
      return { ecrites: q('.mc-i[data-equipe="u13"]').map(l => l.dataset.id),
               visibles: q('.mc-i[data-equipe="u13"]').filter(l => !l.hidden).map(l => l.dataset.id),
               next: q('.mc-i[data-equipe="u13"].is-next').map(l => l.dataset.id),
               etats: q('.mc-i[data-equipe="u13"] .mc-i__etat').map(e => e.textContent.trim()) }; })()`;
    for (const [nom, iso] of [['u13-j2-finie', '2026-09-20T12:30:00+04:00'],
                              ['u13-j3-passee', '2026-09-28T09:00:00+04:00'],
                              ['u13-saison-finie', '2026-11-16T09:00:00+04:00']]) {
      const { s, targetId, erreurs } = await page('/index.html', 390, 844, { iso });
      await aller(s, '#matchs', 20); await sleep(600);
      const m = await evalp(s, MESURE);
      U.instants[nom] = { dernierCache: m.dernier && m.dernier.cache, dernierId: m.dernier && m.dernier.id,
                          prochainId: m.prochain && m.prochain.id, debord: m.debord,
                          u13: await evalp(s, LIGNES), erreurs };
      await aller(s, '[data-mc="u13"]', 90); await tir(s, `390-accueil-${nom}`);
      await send('Target.closeTarget', { targetId });
      process.stdout.write(`u13 instant ${nom} ok (dernier ${U.instants[nom].dernierCache ? 'MASQUE' : 'visible'})\n`);
    }
    R.u13 = U;
  }

  // 5. Les pages de banc générées à une autre date
  for (const fic of readdirSync(RACINE).filter(x => /^_banc-mc-.*\.html$/.test(x))) {
    const { s, targetId, erreurs } = await page('/' + fic, 390, 844, { iso: fic.match(/(\d{4}-\d{2}-\d{2})/) ? fic.match(/(\d{4}-\d{2}-\d{2})/)[1] + 'T09:00:00+04:00' : null });
    R.bancs[fic] = { ...(await evalp(s, MESURE)), erreurs };
    await tir(s, fic.replace('.html', ''));
    await send('Target.closeTarget', { targetId });
  }

  writeFileSync(join(OUT, 'rapport.json'), JSON.stringify(R, null, 1));
  process.stdout.write('-> ' + join(OUT, 'rapport.json') + '\n');
}
main().catch(e => { process.stdout.write('ERREUR ' + e.message + '\n'); process.exitCode = 1; })
  .finally(() => { try { ws && ws.close(); } catch (e) {} ch.kill(); setTimeout(() => { try { rmSync(prof, { recursive: true, force: true }); } catch (e) {} process.exit(); }, 800); });
