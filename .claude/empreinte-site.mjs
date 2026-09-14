// Empreinte de TOUT le site, pour prouver qu'une purge CSS ne change rien
// (V185, 14/09/2026 ; méthode : MAINTENANCE.md § 27 et « Prouver une
// non-régression »). Chaque élément de body, et ses ::before/::after : boîte +
// 55 styles calculés, sur les 27 pages à 390, 768 et 1440 px. L'heure est
// figée (Date) et le hasard a une graine (Math.random) AVANT les scripts de la
// page ; animations et transitions coupées, content-visibility levée.
//
//   node .claude/empreinte-site.mjs . avant             avant la modification
//   node .claude/empreinte-site.mjs . controle avant    même code : mesure le bruit
//   node .claude/empreinte-site.mjs . apres avant       après la modification
//   python .claude/comparer-empreintes.py "%TEMP%/mbc-banc-purge" apres avant controle
//
// Le site est servi par le banc lui-même, le temps de la mesure, sur le port
// 8023 ; les empreintes vont dans %TEMP%\mbc-banc-purge.
import http from 'node:http';
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync, mkdirSync, statSync, createReadStream, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, extname } from 'node:path';

const WT = resolve(process.argv[2] || '.'), TAG = process.argv[3], REF = process.argv[4];
const PORT = 8023, BASE = `http://127.0.0.1:${PORT}`;
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const OUT = join(tmpdir(), 'mbc-banc-purge');
const TAILLES = [[390, 844], [768, 1024], [1440, 900]];
// Les 27 pages : racine + un et deux niveaux (hors dossiers d'outillage)
const PAGES = ['/index.html', '/adhesion.html', '/404.html', '/offline.html'];
for (const d of readdirSync(WT, { withFileTypes: true })) {
  if (!d.isDirectory() || d.name.startsWith('.') || ['node_modules', 'dist', 'assets', 'print', 'data'].includes(d.name)) continue;
  if (existsSync(join(WT, d.name, 'index.html'))) PAGES.push(`/${d.name}/`);
  for (const e of readdirSync(join(WT, d.name), { withFileTypes: true }))
    if (e.isDirectory() && existsSync(join(WT, d.name, e.name, 'index.html'))) PAGES.push(`/${d.name}/${e.name}/`);
}
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.avif': 'image/avif',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json', '.mp4': 'video/mp4',
  '.vtt': 'text/vtt', '.xml': 'application/xml', '.ics': 'text/calendar', '.pdf': 'application/pdf' };
const srv = http.createServer((req, res) => {
  let f = resolve(join(WT, decodeURIComponent(new URL(req.url, 'http://x').pathname)));
  if (!f.startsWith(WT)) { res.writeHead(403); return res.end(); }
  try { if (statSync(f).isDirectory()) f = join(f, 'index.html'); statSync(f); } catch (e) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[extname(f).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
  createReadStream(f).pipe(res);
});
const sleep = ms => new Promise(r => setTimeout(r, ms));
const prof = mkdtempSync(join(tmpdir(), 'mbcsite'));
let ch, ws, n = 0; const pend = new Map(), ecoute = new Set();
const send = (method, params = {}, sessionId) => { const id = ++n; ws.send(JSON.stringify({ id, method, params, sessionId })); return new Promise((res, rej) => pend.set(id, { res, rej, method })); };
const once = (method, s, ms = 30000) => new Promise((res, rej) => { const t = setTimeout(() => { ecoute.delete(l); rej(new Error('timeout ' + method)); }, ms); const l = d => { if (d.method === method && d.sessionId === s) { clearTimeout(t); ecoute.delete(l); res(d.params); } }; ecoute.add(l); });
async function evalp(s, expression) { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, s); if (r.exceptionDetails) throw new Error(((r.exceptionDetails.exception || {}).description || JSON.stringify(r.exceptionDetails)).slice(0, 300)); return r.result.value; }

// Avant tout script de la page : l'heure de La Réunion figée, un hasard
// reproductible. Sans cela, le compte à rebours et le rotator changent le
// texte, donc la mise en page, d'une passe à l'autre.
const FIGER = `(() => {
  const T = Date.parse('2026-09-14T15:00:00+04:00'); const D = Date;
  function F(...a) { return a.length ? new D(...a) : new D(T); }
  F.prototype = D.prototype; F.now = () => T; F.parse = D.parse; F.UTC = D.UTC; window.Date = F;
  let g = 42; Math.random = () => { g = (g * 1103515245 + 12345) % 2147483648; return g / 2147483648; };
})()`;
const PROPS = ['display', 'position', 'top', 'right', 'bottom', 'left', 'float', 'width', 'height', 'margin-top', 'margin-right',
  'margin-bottom', 'margin-left', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left', 'border-top-width',
  'border-bottom-width', 'border-top-color', 'border-radius', 'box-shadow', 'background-color', 'background-image', 'color',
  'opacity', 'visibility', 'overflow-x', 'overflow-y', 'z-index', 'font-family', 'font-size', 'font-weight', 'font-style',
  'line-height', 'letter-spacing', 'text-transform', 'text-align', 'text-decoration-line', 'white-space', 'justify-self',
  'align-self', 'grid-template-columns', 'grid-template-rows', 'row-gap', 'column-gap', 'flex-direction', 'flex-wrap',
  'justify-content', 'align-items', 'order', 'transform', 'filter', 'clip-path', 'list-style-type'];
const PSEUDO = ['content', 'display', 'position', 'width', 'height', 'background-color', 'background-image', 'opacity', 'transform', 'color'];
const EMPREINTE = `(async () => {
  const st = document.createElement('style');
  st.textContent = '*,*::before,*::after{animation:none!important;transition:none!important}*{content-visibility:visible!important}';
  document.head.appendChild(st);
  await document.fonts.ready;
  for (let i = 0; i < 3; i++) await new Promise(r => requestAnimationFrame(r));
  await new Promise(r => setTimeout(r, 300));
  const P = ${JSON.stringify(PROPS)}, Q = ${JSON.stringify(PSEUDO)};
  const r2 = v => Math.round(v * 2) / 2;
  return [...document.querySelectorAll('body *')].map((e, i) => {
    const b = e.getBoundingClientRect(), cs = getComputedStyle(e), c = e.getAttribute('class');
    const av = getComputedStyle(e, '::before'), ap = getComputedStyle(e, '::after');
    const ps = x => x.getPropertyValue('content') === 'none' ? '-' : Q.map(p => x.getPropertyValue(p)).join('~');
    return [i, e.tagName + (c ? '.' + c.trim().split(/\\s+/).join('.') : ''), r2(b.left + scrollX), r2(b.top + scrollY), r2(b.width), r2(b.height),
      P.map(p => cs.getPropertyValue(p)).join('|'), ps(av), ps(ap)].join(' ; ');
  });
})()`;

async function main() {
  await new Promise(r => srv.listen(PORT, '127.0.0.1', r));
  ch = spawn(CHROME, ['--headless=new', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
    '--disable-extensions', '--remote-debugging-port=0', '--user-data-dir=' + prof, '--window-size=1280,800', 'about:blank'], { stdio: 'ignore' });
  const f = join(prof, 'DevToolsActivePort');
  for (let i = 0; i < 150 && !existsSync(f); i++) await sleep(100);
  const [pt, path] = readFileSync(f, 'utf8').split('\n');
  ws = new WebSocket(`ws://127.0.0.1:${pt.trim()}${path.trim()}`);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { const q = pend.get(d.id); pend.delete(d.id); d.error ? q.rej(new Error(q.method + JSON.stringify(d.error))) : q.res(d.result); } else if (d.method) ecoute.forEach(l => l(d)); };
  mkdirSync(OUT, { recursive: true });
  const E = {}, erreurs = [];
  for (const [w, h] of TAILLES) for (const url of PAGES) {
    const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
    const { sessionId: s } = await send('Target.attachToTarget', { targetId, flatten: true });
    for (const d of ['Page', 'Runtime', 'Network']) await send(d + '.enable', {}, s);
    await send('Network.setCacheDisabled', { cacheDisabled: true }, s);
    await send('Network.setBypassServiceWorker', { bypass: true }, s);
    await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: w <= 640 }, s);
    await send('Page.addScriptToEvaluateOnNewDocument', { source: FIGER }, s);
    ecoute.add(d => { if (d.sessionId === s && d.method === 'Runtime.exceptionThrown') erreurs.push(url + ' @' + w + ' : ' + ((d.params.exceptionDetails.exception || {}).description || d.params.exceptionDetails.text).slice(0, 140)); });
    const load = once('Page.loadEventFired', s, 60000);
    await send('Page.navigate', { url: `${BASE}${url}` }, s);
    await load;
    E[url + ' @' + w] = await evalp(s, EMPREINTE);
    await send('Target.closeTarget', { targetId });
  }
  writeFileSync(join(OUT, `site-${TAG}.json`), JSON.stringify(E));
  const total = Object.values(E).reduce((a, x) => a + x.length, 0);
  process.stdout.write(`${TAG} : ${PAGES.length} pages x ${TAILLES.length} largeurs = ${Object.keys(E).length} vues, ${total} elements\n`);
  if (erreurs.length) process.stdout.write('ERREURS JS : ' + erreurs.slice(0, 5).join(' | ') + '\n');
  if (REF) {
    const A = JSON.parse(readFileSync(join(OUT, `site-${REF}.json`), 'utf8'));
    const ecarts = [];
    for (const k of Object.keys(A)) {
      const a = A[k], b = E[k] || [];
      if (a.length !== b.length) ecarts.push(`${k} : ${a.length} -> ${b.length} elements`);
      for (let i = 0; i < Math.max(a.length, b.length); i++) if (a[i] !== b[i]) ecarts.push(`${k} #${i}\n    avant : ${(a[i] || '').slice(0, 700)}\n    apres : ${(b[i] || '').slice(0, 700)}`);
    }
    writeFileSync(join(OUT, `ecarts-${TAG}-${REF}.txt`), ecarts.join('\n'));
    process.stdout.write(`ECARTS ${TAG}/${REF} : ${ecarts.length}\n` + ecarts.slice(0, 8).join('\n') + '\n');
  }
}
main().catch(e => { process.stdout.write('ERREUR ' + e.message + '\n'); process.exitCode = 1; })
  .finally(() => { try { ws && ws.close(); } catch (e) {} try { ch && ch.kill(); } catch (e) {} srv.close();
    setTimeout(() => { try { rmSync(prof, { recursive: true, force: true }); } catch (e) {} process.exit(); }, 800); });
