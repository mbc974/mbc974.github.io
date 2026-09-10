// Banc du parallax du hero (V177) — le seul qui voit une animation liee au
// defilement. Chrome est pilote en CDP : vraies images (les timelines de
// defilement sont re-echantillonnees), viewport EXACT par emulation (pas de
// plancher a 500 px), prefers-reduced-motion:no-preference, page defilee par
// elle-meme. Les captures a temps virtuel (--virtual-time-budget) ne montrent
// que le repos : ne jamais s'y fier pour V177. Voir MAINTENANCE.md § 23.
//
// Prerequis : Node 22+ (WebSocket global), Chrome installe, et le serveur local
// du depot sur http://localhost:8000 (configuration « mbc-static » de
// .claude/launch.json).
//
//   node .claude/banc-parallaxe.mjs <etiquette> <LxH,LxH> [pos,pos] [options]
//     pos              fractions de la hauteur du hero defilees
//                      (defaut 0,0.25,0.5,0.75), n'importe ou apres les formats
//     --shots          une capture PNG par position
//     --reduce         prefers-reduced-motion:reduce
//     --off            coupe la couche CSS V177 (pas le seuil de masquage de
//                      script.js) : controle « avant » au repos
//     --sans-bandeau   pose l'attribut hidden sur #nxBand, comme script.js quand
//                      il n'y a plus de rencontre a venir
//     --bandeau-absent retire #nxBand, comme build-matchs.py hors saison
//     --css=f.css      injecte une feuille d'essai apres style.min.css
//
// Sorties HORS du depot : %TEMP%/mbc-banc-parallaxe/<etiquette>.json (ou
// $MBC_BANC_SORTIE) et <etiquette>-<LxH>-sNNN.png. Par position : rectangles,
// translate calcules, opacite de la lisiere, hero.scrollTop, part visible du
// bouton « Je m'inscris » et de son LIBELLE entre la barre du haut et le
// bandeau (geometrie seule : « visible » ne tient pas compte du fondu), px du
// libelle sous la lisiere, « Je m'inscris » de la barre du haut affiche ou non,
// barre flottante reellement affichee ou non. Le decompte du bandeau, qui
// change a la minute, est masque (visibility) pour que deux tirs se comparent.
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME = process.env.MBC_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.MBC_BASE || 'http://localhost:8000';
const SORTIE = process.env.MBC_BANC_SORTIE || join(tmpdir(), 'mbc-banc-parallaxe');
const argv = process.argv.slice(2);
const USAGE = 'usage : node .claude/banc-parallaxe.mjs <etiquette> <LxH,...> [pos,...] [--shots] [--reduce] [--off] [--sans-bandeau | --bandeau-absent] [--css=f.css]\n';
if (argv.length < 2 || argv[0].startsWith('--') || argv[1].startsWith('--')) { process.stdout.write(USAGE); process.exit(2); }
const tag = argv[0];
const formats = argv[1].split(',');
const posArg = argv.slice(2).find(a => !a.startsWith('--'));
const pos = (posArg || '0,0.25,0.5,0.75').split(',').map(Number);
if (pos.some(Number.isNaN)) { process.stdout.write('positions illisibles : ' + posArg + '\n' + USAGE); process.exit(2); }
const shots = argv.includes('--shots');
const reduce = argv.includes('--reduce');
const cssFic = (argv.find(a => a.startsWith('--css=')) || '').slice(6);
const sleep = ms => new Promise(r => setTimeout(r, ms));

let injecte = cssFic ? readFileSync(cssFic, 'utf8') : '';
if (argv.includes('--off')) injecte += '.ecran1 .hero__photo picture,.ecran1 .hero__inner{animation:none!important}' +
  '.ecran1>.hero,.ecran1>.hero>.hero__photo{overflow:hidden!important}#nxBand::before{display:none!important}';
// Les deux etats REELS « sans bandeau » : script.js pose l'attribut hidden
// quand il n'y a plus de rencontre a venir ; build-matchs.py n'ecrit rien
// entre les marqueurs. Un display:none en CSS n'existe pas en vrai (et ne
// declencherait pas le garde-fou :has() de V177).
const sansBandeau = argv.includes('--sans-bandeau') ? 'hidden' : argv.includes('--bandeau-absent') ? 'absent' : '';

const prof = mkdtempSync(join(tmpdir(), 'mbcbancpx'));
const ch = spawn(CHROME, ['--headless=new', '--hide-scrollbars', '--no-first-run',
  '--no-default-browser-check', '--disable-extensions', '--remote-debugging-port=0',
  '--user-data-dir=' + prof, '--window-size=1280,800', 'about:blank'], { stdio: 'ignore' });

let ws, n = 0;
const pend = new Map(), ecoute = new Set();
const send = (method, params = {}, sessionId) => { const id = ++n; ws.send(JSON.stringify({ id, method, params, sessionId })); return new Promise((res, rej) => pend.set(id, { res, rej, method })); };
const once = (method, s, ms = 30000) => new Promise((res, rej) => { const t = setTimeout(() => { ecoute.delete(l); rej(new Error('timeout ' + method)); }, ms); const l = d => { if (d.method === method && d.sessionId === s) { clearTimeout(t); ecoute.delete(l); res(d.params); } }; ecoute.add(l); });
async function evalp(s, expression) { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, s); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 400)); return r.result.value; }

// Injecte dans la page : preparation (bandeau RGPD masque, decompte fige,
// feuille d'essai, images et polices decodees, animations d'entree terminees)
// et mesure.
const AIDE = (css, sb) => `(() => {
  const sansBandeau = () => { const b = document.getElementById('nxBand'); if (!b) return;
    if (${JSON.stringify(sb)} === 'hidden') b.hidden = true; else if (${JSON.stringify(sb)} === 'absent') b.remove(); };
  window.__banc = {
    async prep() {
      sansBandeau();
      const st = document.createElement('style'); st.id = '__banc';
      st.textContent = '.ccb{display:none!important}#nxCountdown{visibility:hidden!important}' + ${JSON.stringify(css)};
      document.head.appendChild(st);
      document.documentElement.style.scrollBehavior = 'auto';
      await document.fonts.ready;
      const img = document.querySelector('.hero__photo img');
      if (img && img.decode) { try { await img.decode(); } catch (e) {} }
      await new Promise(r => setTimeout(r, 2200));   // heroMonte et heroZoom finis
    },
    async aller(p) {
      sansBandeau();
      const hero = document.getElementById('hero');
      window.scrollTo({ top: Math.round(p * hero.offsetHeight), behavior: 'instant' });
      for (let i = 0; i < 4; i++) await new Promise(r => requestAnimationFrame(r));
      await new Promise(r => setTimeout(r, 120));
      const R = q => { const e = document.querySelector(q); if (!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)]; };
      const C = (q, pr) => { const e = document.querySelector(q); return e ? getComputedStyle(e)[pr] : null; };
      const band = document.getElementById('nxBand');
      const bandR = band ? band.getBoundingClientRect() : null;
      const bandVu = !!(bandR && bandR.height > 0);
      const bas = bandVu ? bandR.top : hero.getBoundingClientRect().bottom;
      const hdrEl = document.querySelector('.site-header');
      const hdr = hdrEl.getBoundingClientRect();
      const haut = Math.max(0, hdr.bottom);
      const part = b => Math.max(0, Math.round((Math.min(b.bottom, bas) - Math.max(b.top, haut)) / b.height * 100));
      const btn = document.querySelector('.hero__cta .btn--primary');
      const tn = [...btn.childNodes].find(x => x.nodeType === 3 && x.textContent.trim());
      const rg = document.createRange(); rg.selectNodeContents(tn);
      const lb = rg.getBoundingClientRect();
      const lis = band ? getComputedStyle(band, '::before') : null;
      const lisOn = !!(lis && lis.content !== 'none' && bandVu);
      // la lisiere couvre [haut du bandeau - 1 px (filet) - sa hauteur ; haut du bandeau - 1 px]
      const lisBas = bandVu ? bandR.top - 1 : 0, lisHaut = lisOn ? lisBas - parseFloat(lis.height) : 0;
      const sousLis = lisOn ? Math.max(0, Math.min(lb.bottom, lisBas) - Math.max(lb.top, lisHaut)) : 0;
      const hdCta = document.querySelector('.hd-cta');
      const fc = document.getElementById('floatCta');
      return { p, y: Math.round(scrollY), vw: innerWidth, vh: innerHeight,
        hero: R('#hero'), picture: R('.hero__photo picture'), inner: R('.hero__inner'),
        titre: R('.hero__h1-t'), hw: R('.hw'), cta: R('.hero__cta .btn--primary'), essai: R('.hero__second'),
        band: bandVu ? R('#nxBand') : null, libelle: [Math.round(lb.left), Math.round(lb.top), Math.round(lb.width), Math.round(lb.height)],
        trPicture: C('.hero__photo picture', 'translate'), trInner: C('.hero__inner', 'translate'),
        ovHero: C('#hero', 'overflowY'), heroScrollTop: hero.scrollTop,
        lisiere: !lis || lis.content === 'none' ? 'aucune' : lis.opacity,
        ctaVisible: part(btn.getBoundingClientRect()), libelleVisible: part(lb),
        libelleSousLisierePx: Math.round(sousLis), libelleHauteurPx: Math.round(lb.height),
        barreHautMasquee: hdrEl.classList.contains('hide'),
        ctaBarreHaut: !hdrEl.classList.contains('hide') && !!hdCta && getComputedStyle(hdCta).display !== 'none',
        barreFlottante: !!(fc && fc.classList.contains('show') && getComputedStyle(fc).display !== 'none'),
        scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth };
    }
  };
})()`;

async function main() {
  const f = join(prof, 'DevToolsActivePort');
  for (let i = 0; i < 150 && !existsSync(f); i++) await sleep(100);
  const [pt, path] = readFileSync(f, 'utf8').split('\n');
  ws = new WebSocket(`ws://127.0.0.1:${pt.trim()}${path.trim()}`);
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
    await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: reduce ? 'reduce' : 'no-preference' }] }, s);
    const load = once('Page.loadEventFired', s, 60000);
    await send('Page.navigate', { url: `${BASE}/index.html?t=${Date.now()}` }, s);
    await load;
    await evalp(s, AIDE(injecte, sansBandeau));
    await evalp(s, '__banc.prep()');
    const rows = [];
    for (const p of pos) {
      rows.push(await evalp(s, `__banc.aller(${p})`));
      if (shots) {
        const { data } = await send('Page.captureScreenshot', { format: 'png' }, s);
        writeFileSync(join(SORTIE, `${tag}-${fm}-s${String(Math.round(p * 100)).padStart(3, '0')}.png`), Buffer.from(data, 'base64'));
      }
    }
    out[fm] = rows;
    await send('Target.closeTarget', { targetId });
    process.stdout.write(fm + ' ok\n');
  }
  const fic = join(SORTIE, `${tag}.json`);
  writeFileSync(fic, JSON.stringify(out, null, 1));
  process.stdout.write('-> ' + fic + '\n');
}

main().catch(e => { process.stdout.write('ERREUR ' + e.message + '\n'); process.exitCode = 1; })
  .finally(() => { try { ws && ws.close(); } catch (e) {} ch.kill(); setTimeout(() => { try { rmSync(prof, { recursive: true, force: true }); } catch (e) {} process.exit(); }, 800); });
