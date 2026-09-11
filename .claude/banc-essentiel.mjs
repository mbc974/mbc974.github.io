// Captures de la section #essentiel (V179) dans un vrai Chrome pilote en CDP.
// Par format : entree en eventail (images a temps d'animation connus, grace a
// Animation.setPlaybackRate), repos, survol d'un volet, survol du bouton du
// tarif, bascule « 3 fois » a la souris (confettis puis etat pose), retour
// « 1 fois » au clavier (vraie touche Espace). Puis, en 1440 : mouvement
// reduit et sans JavaScript.
// Il faut le serveur local « mbc-static » (port 8000). Captures PNG et
// mesures JSON dans %TEMP%\mbc-banc-essentiel. Voir MAINTENANCE.md, § 24.
//   node .claude/banc-essentiel.mjs <tag> <LxH,LxH,...> [--extras]
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const OUT = join(tmpdir(), 'mbc-banc-essentiel');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://localhost:8000';
const args = process.argv.slice(2);
const extras = args.includes('--extras');
const [tag = 'kc', fmts = '1440x1150'] = args.filter(a => !a.startsWith('--'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
const prof = mkdtempSync(join(tmpdir(), 'mbckc'));
const ch = spawn(CHROME, ['--headless=new', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', '--remote-debugging-port=0', '--user-data-dir=' + prof, '--window-size=1280,800', 'about:blank'], { stdio: 'ignore' });
let ws, n = 0; const pend = new Map(), ecoute = new Set();
const send = (method, params = {}, sessionId) => { const id = ++n; ws.send(JSON.stringify({ id, method, params, sessionId })); return new Promise((res, rej) => pend.set(id, { res, rej, method })); };
const once = (method, s, ms = 30000) => new Promise((res, rej) => { const t = setTimeout(() => { ecoute.delete(l); rej(new Error('timeout ' + method)); }, ms); const l = d => { if (d.method === method && d.sessionId === s) { clearTimeout(t); ecoute.delete(l); res(d.params); } }; ecoute.add(l); });
async function evalp(s, expression) { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, s); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 300)); return r.result.value; }

const MESURE = `(() => {
  const kc = document.getElementById('kc'), sec = document.getElementById('essentiel');
  const r = e => { const b = e.getBoundingClientRect(); return { x: Math.round(b.left), y: Math.round(b.top), w: Math.round(b.width), h: Math.round(b.height) }; };
  const mult = kc.querySelector('.kc__mult'), fr = kc.querySelector('.kc__fr'), sw = document.getElementById('kcSw');
  const cols = [...kc.querySelectorAll('.kc__d')].map(d => d.style.getPropertyValue('--d'));
  const vu = cols.length ? (mult && +getComputedStyle(mult).opacity > .5 ? '3x ' : '') + cols[0] + cols[1] + (fr && +getComputedStyle(fr).opacity > .5 ? ',' + cols[2] + cols[3] : '') : kc.querySelector('.kc__price').textContent;
  return { scrollY: Math.round(scrollY), sec: r(sec),
    cartes: [...kc.querySelectorAll('.kc__card')].map(c => ({ cls: c.className.replace('kc__card', '').trim(), tf: getComputedStyle(c).transform.replace(/\\s+/g, '').slice(0, 110), box: r(c) })),
    lis: [...kc.querySelectorAll('.kc__i')].map(r),
    prix: vu, mult: mult ? { w: Math.round(mult.getBoundingClientRect().width), hidden: mult.hidden } : null,
    fr: fr ? { w: Math.round(fr.getBoundingClientRect().width) } : null,
    sw: sw ? { hidden: sw.hidden, checked: sw.getAttribute('aria-checked'), box: r(sw) } : null,
    dit: (document.getElementById('kcDit') || {}).textContent, is3: kc.querySelector('.kc__card--star').classList.contains('is-3'),
    pre: kc.querySelectorAll('.kc--pre').length, fx: document.querySelectorAll('.kc-fx i').length,
    debord: document.documentElement.scrollWidth - innerWidth,
    ctaStar: getComputedStyle(kc.querySelector('.kc__card--star .kc__cta')).boxShadow.slice(0, 80) };
})()`;

async function page(w, h, { reduce = false, noJs = false, dpr } = {}) {
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId: s } = await send('Target.attachToTarget', { targetId, flatten: true });
  for (const d of ['Page', 'Runtime', 'Network', 'DOM']) await send(d + '.enable', {}, s);
  await send('Network.setCacheDisabled', { cacheDisabled: true }, s);
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: dpr || (w > 1600 ? 1 : 2), mobile: w <= 640 }, s);
  await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: reduce ? 'reduce' : 'no-preference' }] }, s);
  if (noJs) await send('Emulation.setScriptExecutionDisabled', { value: true }, s);
  const load = once('Page.loadEventFired', s, 60000);
  await send('Page.navigate', { url: `${BASE}/index.html?t=${Date.now()}` }, s);
  await load;
  return { s, targetId };
}
const tir = async (s, nom, clip) => {
  const p = { format: 'png', captureBeyondViewport: !!clip };
  if (clip) p.clip = { ...clip, scale: 1 };
  const { data } = await send('Page.captureScreenshot', p, s);
  writeFileSync(join(OUT, `${tag}-${nom}.png`), Buffer.from(data, 'base64'));
};
const souris = (s, type, x, y, extra = {}) => send('Input.dispatchMouseEvent', { type, x, y, ...extra }, s);

async function main() {
  const f = join(prof, 'DevToolsActivePort');
  for (let i = 0; i < 150 && !existsSync(f); i++) await sleep(100);
  const [pt, path] = readFileSync(f, 'utf8').split('\n');
  ws = new WebSocket(`ws://127.0.0.1:${pt.trim()}${path.trim()}`);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { const q = pend.get(d.id); pend.delete(d.id); d.error ? q.rej(new Error(q.method + JSON.stringify(d.error))) : q.res(d.result); } else if (d.method) ecoute.forEach(l => l(d)); };
  mkdirSync(OUT, { recursive: true });
  const rapport = {};

  for (const fm of fmts.split(',')) {
    const [w, h] = fm.split('x').map(Number);
    const { s, targetId } = await page(w, h);
    await evalp(s, `(async () => { const st = document.createElement('style'); st.textContent = '.ccb{display:none!important}'; document.head.appendChild(st);
      await document.fonts.ready; await new Promise(r => setTimeout(r, 1200)); })()`);
    const R = { avant: await evalp(s, MESURE) };
    // Entree : on ralentit la ligne de temps du document (x0,2), puis on amene
    // la section en haut de l'ecran. Temps d'animation = temps reel x 0,2.
    await send('Animation.enable', {}, s);
    await send('Animation.setPlaybackRate', { playbackRate: 0.2 }, s);
    const t0 = Date.now();
    await evalp(s, `(() => { const y = document.getElementById('essentiel').getBoundingClientRect().top + scrollY; window.scrollTo({ top: y, behavior: 'instant' }); })()`);
    R.entree = [];
    for (const [i, tAnim] of [[1, 0.05], [2, 0.5], [3, 0.8], [4, 1.1], [5, 1.8]].entries()) {
      const attente = t0 + tAnim[1] * 5000 - Date.now();
      if (attente > 0) await sleep(attente);
      const m = await evalp(s, MESURE);
      await tir(s, `${fm}-entree-${tAnim[0]}`, { x: 0, y: m.sec.y + m.scrollY, width: w, height: Math.min(m.sec.h, h) });
      R.entree.push({ tAnim: tAnim[1], tReel: ((Date.now() - t0) / 5000).toFixed(2), cartes: m.cartes.map(c => c.tf), prix: m.prix });
    }
    await send('Animation.setPlaybackRate', { playbackRate: 1 }, s);
    await sleep(1500);
    const repos = await evalp(s, MESURE);
    R.repos = repos;
    const clipSec = { x: 0, y: repos.sec.y + repos.scrollY, width: w, height: Math.min(repos.sec.h, h - Math.max(0, repos.sec.y)) };
    await tir(s, `${fm}-repos`, clipSec);
    // Survol du volet gauche (la boite du <li>, pas la carte pivotee)
    const li = repos.lis[0];
    await souris(s, 'mouseMoved', li.x + li.w * 0.3, li.y + li.h * 0.5); await sleep(900);
    R.survolGauche = (await evalp(s, MESURE)).cartes[0];
    await tir(s, `${fm}-survol-volet`, clipSec);
    // Survol du bouton de la carte du tarif (anneau)
    const cta = await evalp(s, `(() => { const b = document.querySelector('.kc__card--star .kc__cta').getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; })()`);
    await souris(s, 'mouseMoved', cta.x, cta.y); await sleep(700);
    R.ctaSurvol = (await evalp(s, MESURE)).ctaStar;
    const star = repos.cartes[1].box;
    const clipStar = { x: Math.max(0, star.x - 40), y: star.y + repos.scrollY - 40, width: Math.min(w, star.w + 80), height: star.h + 80 };
    await tir(s, `${fm}-survol-cta`, clipStar);
    await souris(s, 'mouseMoved', 5, h - 5); await sleep(500);
    // Bascule « 3 fois » a la souris : confettis captures au ralenti
    const sw = repos.sw.box;
    await send('Animation.setPlaybackRate', { playbackRate: 0.25 }, s);
    await souris(s, 'mousePressed', sw.x + 22, sw.y + sw.h / 2, { button: 'left', clickCount: 1 });
    await souris(s, 'mouseReleased', sw.x + 22, sw.y + sw.h / 2, { button: 'left', clickCount: 1 });
    const t1 = Date.now();
    R.confettis = [];
    for (const tAnim of [0.12, 0.45, 1.0]) {
      const attente = t1 + tAnim * 4000 - Date.now();
      if (attente > 0) await sleep(attente);
      const m = await evalp(s, MESURE);
      await tir(s, `${fm}-confettis-${String(tAnim).replace('.', '')}`);
      R.confettis.push({ tAnim, particules: m.fx, prix: m.prix });
    }
    await send('Animation.setPlaybackRate', { playbackRate: 1 }, s);
    await sleep(2800);
    R.trois = await evalp(s, MESURE);
    await tir(s, `${fm}-trois`, clipStar);
    // Retour « 1 fois » au clavier : focus sur l'interrupteur, vraie touche Espace
    await evalp(s, `document.getElementById('kcSw').focus()`);
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: ' ', code: 'Space', windowsVirtualKeyCode: 32, text: ' ' }, s);
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: ' ', code: 'Space', windowsVirtualKeyCode: 32 }, s);
    await sleep(1200);
    R.un = await evalp(s, MESURE);
    await tir(s, `${fm}-un-clavier`, clipStar);
    rapport[fm] = R;
    await send('Target.closeTarget', { targetId });
    process.stdout.write(fm + ' ok\n');
  }

  if (extras) {
    // Mouvement reduit : jamais d'etat d'avant, pose immediate, 95 d'emblee
    {
      const { s, targetId } = await page(1440, 1150, { reduce: true });
      await evalp(s, `(async () => { const st = document.createElement('style'); st.textContent = '.ccb{display:none!important}'; document.head.appendChild(st); await document.fonts.ready; })()`);
      const avant = await evalp(s, MESURE);
      await evalp(s, `window.scrollTo(0, document.getElementById('essentiel').getBoundingClientRect().top + scrollY)`);
      await sleep(900);
      const m = await evalp(s, MESURE);
      await tir(s, `reduit-1440`, { x: 0, y: m.sec.y + m.scrollY, width: 1440, height: Math.min(m.sec.h, 1150) });
      const sw = m.sw.box;
      await souris(s, 'mousePressed', sw.x + 22, sw.y + sw.h / 2, { button: 'left', clickCount: 1 });
      await souris(s, 'mouseReleased', sw.x + 22, sw.y + sw.h / 2, { button: 'left', clickCount: 1 });
      await sleep(120);
      rapport.reduit = { avantPre: avant.pre, cartes: m.cartes.map(c => c.tf), prix: m.prix, apresClic: await evalp(s, MESURE) };
      await send('Target.closeTarget', { targetId });
    }
    // Sans JavaScript : le DOM seul (Runtime.evaluate est coupe avec les scripts)
    {
      const { s, targetId } = await page(1440, 1150, { noJs: true });
      await sleep(1500);
      const { root } = await send('DOM.getDocument', { depth: 1 }, s);
      const q = async sel => (await send('DOM.querySelector', { nodeId: root.nodeId, selector: sel }, s)).nodeId;
      const sec = await q('#essentiel');
      await send('DOM.scrollIntoViewIfNeeded', { nodeId: sec }, s);
      await sleep(600);
      const { model } = await send('DOM.getBoxModel', { nodeId: sec }, s);
      const [x1, y1, , , , y3] = model.border;
      await tir(s, 'sansjs-1440');
      const swNode = await q('#kcSw');
      const attrs = (await send('DOM.getAttributes', { nodeId: swNode }, s)).attributes;
      rapport.sansJs = { sectionHautViewport: Math.round(y1), hauteur: Math.round(y3 - y1), interrupteurCache: attrs.includes('hidden') };
      await send('Target.closeTarget', { targetId });
    }
  }
  writeFileSync(join(OUT, `${tag}.json`), JSON.stringify(rapport, null, 1));
  process.stdout.write('-> ' + join(OUT, tag + '.json') + '\n');
}
main().catch(e => { process.stdout.write('ERREUR ' + e.message + '\n'); process.exitCode = 1; })
  .finally(() => { try { ws && ws.close(); } catch (e) {} ch.kill(); setTimeout(() => { try { rmSync(prof, { recursive: true, force: true }); } catch (e) {} process.exit(); }, 800); });
