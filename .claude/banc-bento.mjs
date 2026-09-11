// Banc de la grille bento d'adhesion.html (V180), Chrome pilote en CDP.
// Par format : mise en page (rectangles, texte rogne, fonds charges), survol
// de chaque carte (CTA revele, contenu monte), clavier (vraie touche Tab
// jusqu'au premier CTA : revele au focus), puis en option le tactile
// (Emulation.setTouchEmulationEnabled : le CTA doit etre visible sans survol),
// le mouvement reduit et le rendu sans JavaScript.
//   node .claude/banc-bento.mjs <tag> <LxH,...> --sel='{"grille":"..","carte":"..","cta":"..","corps":".."}' [--tactile] [--extras]
// Il faut le serveur local « mbc-static » (port 8000). Sorties dans %TEMP%\mbc-banc-bento. Voir MAINTENANCE.md, § 25.
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const OUT = join(tmpdir(), 'mbc-banc-bento');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://localhost:8000';
const args = process.argv.slice(2);
const opt = n => args.includes('--' + n);
const selArg = args.find(a => a.startsWith('--sel='));
if (!selArg) { console.log('manque --sel=JSON'); process.exit(2); }
const SEL = JSON.parse(selArg.slice(6));
const [tag = 'bento', fmts = '1440x1100'] = args.filter(a => !a.startsWith('--'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
const prof = mkdtempSync(join(tmpdir(), 'mbcbento'));
const ch = spawn(CHROME, ['--headless=new', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
  '--disable-extensions', '--remote-debugging-port=0', '--user-data-dir=' + prof, '--window-size=1280,800', 'about:blank'], { stdio: 'ignore' });
let ws, n = 0; const pend = new Map(), ecoute = new Set();
const send = (method, params = {}, sessionId) => { const id = ++n; ws.send(JSON.stringify({ id, method, params, sessionId })); return new Promise((res, rej) => pend.set(id, { res, rej, method })); };
const once = (method, s, ms = 30000) => new Promise((res, rej) => { const t = setTimeout(() => { ecoute.delete(l); rej(new Error('timeout ' + method)); }, ms); const l = d => { if (d.method === method && d.sessionId === s) { clearTimeout(t); ecoute.delete(l); res(d.params); } }; ecoute.add(l); });
async function evalp(s, expression) { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, s); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 300)); return r.result.value; }

const S = JSON.stringify(SEL);
const MESURE = `(() => {
  const SEL = ${S};
  const g = document.querySelector(SEL.grille);
  if (!g) return { erreur: 'grille introuvable : ' + SEL.grille };
  const r = e => { const b = e.getBoundingClientRect(); return { x: Math.round(b.left), y: Math.round(b.top), w: Math.round(b.width), h: Math.round(b.height) }; };
  const cartes = [...g.querySelectorAll(SEL.carte)].map(c => {
    const cta = c.querySelector(SEL.cta), corps = SEL.corps ? c.querySelector(SEL.corps) : null;
    const csC = cta ? getComputedStyle(cta) : null;
    const txt = [...c.querySelectorAll('h2,h3,h4,p,strong,b,span')].filter(e => e.children.length === 0 && e.textContent.trim());
    const cb = c.getBoundingClientRect();
    const rogne = txt.filter(e => { const b = e.getBoundingClientRect(); return b.width && (b.bottom > cb.bottom + 1 || b.right > cb.right + 1 || b.left < cb.left - 1 || b.top < cb.top - 1); }).map(e => e.textContent.trim().slice(0, 40));
    const img = c.querySelector('img');
    return { box: r(c), texte: c.textContent.replace(/\\s+/g, ' ').trim().slice(0, 90),
      // Opacite EFFECTIVE (produit jusqu'a la carte) : le composant masque le
      // pied qui contient le lien, pas le lien lui-meme.
      cta: cta ? { href: cta.getAttribute('href'), op: (() => { let o = 1; for (let e = cta; e && e !== c; e = e.parentElement) o *= +getComputedStyle(e).opacity; return +o.toFixed(2); })(),
        tf: getComputedStyle(cta.parentElement).transform.slice(0, 60), vis: csC.visibility, box: r(cta), pe: getComputedStyle(cta.parentElement).pointerEvents } : null,
      corpsTf: corps ? getComputedStyle(corps).transform.slice(0, 60) : null,
      rogne, img: img ? { src: (img.currentSrc || img.src).split('/').pop(), nat: img.naturalWidth + 'x' + img.naturalHeight, rendu: Math.round(img.getBoundingClientRect().width) + 'x' + Math.round(img.getBoundingClientRect().height), loading: img.loading } : null };
  });
  return { scrollY: Math.round(scrollY), grille: r(g), cols: getComputedStyle(g).gridTemplateColumns, cartes,
    hoverNone: matchMedia('(hover:none)').matches, debord: document.documentElement.scrollWidth - innerWidth,
    focus: document.activeElement ? (document.activeElement.className || document.activeElement.tagName) + ' ' + (document.activeElement.getAttribute('href') || '') : null };
})()`;

async function page(w, h, { reduce = false, noJs = false, tactile = false, dpr } = {}) {
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId: s } = await send('Target.attachToTarget', { targetId, flatten: true });
  for (const d of ['Page', 'Runtime', 'Network', 'DOM']) await send(d + '.enable', {}, s);
  await send('Network.setCacheDisabled', { cacheDisabled: true }, s);
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: dpr || (w > 1600 ? 1 : 2), mobile: tactile || w <= 640 }, s);
  if (tactile) await send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 }, s);
  await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: reduce ? 'reduce' : 'no-preference' }] }, s);
  if (noJs) await send('Emulation.setScriptExecutionDisabled', { value: true }, s);
  const load = once('Page.loadEventFired', s, 60000);
  await send('Page.navigate', { url: `${BASE}/adhesion.html?t=${Date.now()}` }, s);
  await load;
  return { s, targetId };
}
// Fenetre entiere, sans captureBeyondViewport : agrandir la capture au-dela
// de l'ecran fait cesser, le temps du rendu, la media query de la montee.
const tir = async (s, nom) => {
  const p = { format: 'png', captureBeyondViewport: false };
  const { data } = await send('Page.captureScreenshot', p, s);
  writeFileSync(join(OUT, `${tag}-${nom}.png`), Buffer.from(data, 'base64'));
};
const souris = (s, type, x, y, extra = {}) => send('Input.dispatchMouseEvent', { type, x, y, ...extra }, s);
const PREP = `(async () => { const st = document.createElement('style'); st.textContent = '.ccb{display:none!important}'; document.head.appendChild(st);
  await document.fonts.ready; await new Promise(r => setTimeout(r, 900));
  const g = document.querySelector(${JSON.stringify(SEL.grille)}); const y = g.getBoundingClientRect().top + scrollY - 90;
  window.scrollTo({ top: y, behavior: 'instant' }); await new Promise(r => setTimeout(r, 1400)); })()`;
const clipDe = (m, w) => ({ x: 0, y: m.grille.y + m.scrollY - 24, width: w, height: m.grille.h + 48 });

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
    await evalp(s, PREP);
    await souris(s, 'mouseMoved', 2, h - 2); await sleep(400);
    const repos = await evalp(s, MESURE);
    if (repos.erreur) throw new Error(repos.erreur);
    const R = { repos, survol: [] };
    await tir(s, `${fm}-repos`, clipDe(repos, w));
    // Survol de chaque carte (boite mesuree au repos)
    for (let i = 0; i < repos.cartes.length; i++) {
      const b = repos.cartes[i].box;
      await souris(s, 'mouseMoved', b.x + b.w * 0.5, b.y + b.h * 0.5); await sleep(650);
      const m = await evalp(s, MESURE);
      R.survol.push({ i, cta: m.cartes[i].cta, corpsTf: m.cartes[i].corpsTf });
      if (i === 0) await tir(s, `${fm}-survol-1`, clipDe(m, w));
    }
    await souris(s, 'mouseMoved', 2, h - 2); await sleep(500);
    // Clavier : focus sur le bouton qui precede la grille, puis vraie touche Tab
    await evalp(s, `(() => { const g = document.querySelector(${JSON.stringify(SEL.grille)}); const liens = [...document.querySelectorAll('a[href],button')]; const avant = liens.filter(a => a.compareDocumentPosition(g) & Node.DOCUMENT_POSITION_FOLLOWING && !g.contains(a)).pop(); if (avant) avant.focus(); })()`);
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 }, s);
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 }, s);
    await sleep(650);
    const clavier = await evalp(s, MESURE);
    R.clavier = { focus: clavier.focus, cta0: clavier.cartes[0].cta, scrollY: clavier.scrollY };
    await tir(s, `${fm}-clavier`, clipDe(clavier, w));
    rapport[fm] = R;
    await send('Target.closeTarget', { targetId });
    process.stdout.write(fm + ' ok\n');
  }

  if (opt('tactile')) {
    for (const [w, h] of [[390, 1800], [768, 1500]]) {
      const { s, targetId } = await page(w, h, { tactile: true });
      await evalp(s, PREP);
      const m = await evalp(s, MESURE);
      rapport['tactile-' + w] = { hoverNone: m.hoverNone, ctas: m.cartes.map(c => c.cta && { op: c.cta.op, vis: c.cta.vis, h: c.cta.box.h, pe: c.cta.pe }), rogne: m.cartes.map(c => c.rogne), debord: m.debord };
      await tir(s, `tactile-${w}`, clipDe(m, w));
      await send('Target.closeTarget', { targetId });
    }
  }
  if (opt('extras')) {
    {
      const { s, targetId } = await page(1440, 1300, { reduce: true });
      await evalp(s, PREP);
      const b = (await evalp(s, MESURE)).cartes[0].box;
      await souris(s, 'mouseMoved', b.x + b.w / 2, b.y + b.h / 2); await sleep(120);
      const m = await evalp(s, MESURE);
      rapport.reduit = { cta0: m.cartes[0].cta, corps0: m.cartes[0].corpsTf };
      await tir(s, 'reduit-1440', clipDe(m, 1440));
      await send('Target.closeTarget', { targetId });
    }
    {
      const { s, targetId } = await page(1440, 1300, { noJs: true });
      await sleep(1500);
      const { root } = await send('DOM.getDocument', { depth: 1 }, s);
      const node = (await send('DOM.querySelector', { nodeId: root.nodeId, selector: SEL.grille }, s)).nodeId;
      await send('DOM.scrollIntoViewIfNeeded', { nodeId: node }, s);
      await sleep(600);
      const { model } = await send('DOM.getBoxModel', { nodeId: node }, s);
      rapport.sansJs = { hautViewport: Math.round(model.border[1]), hauteur: Math.round(model.border[5] - model.border[1]) };
      await tir(s, 'sansjs-1440');
      await send('Target.closeTarget', { targetId });
    }
  }
  writeFileSync(join(OUT, `${tag}.json`), JSON.stringify(rapport, null, 1));
  process.stdout.write('-> ' + join(OUT, tag + '.json') + '\n');
}
main().catch(e => { process.stdout.write('ERREUR ' + e.message + '\n'); process.exitCode = 1; })
  .finally(() => { try { ws && ws.close(); } catch (e) {} ch.kill(); setTimeout(() => { try { rmSync(prof, { recursive: true, force: true }); } catch (e) {} process.exit(); }, 800); });
