// Banc du zoom parallaxe de la galerie (#galerie / .gzoom) — le second bloc du
// site pilote par le defilement, apres le hero. Chrome est pilote en CDP :
// vraies images, viewport EXACT par emulation (pas de plancher a 500 px),
// prefers-reduced-motion:no-preference, page defilee par elle-meme.
//
// Ce que le banc mesure, et pourquoi. Dans .gzoom, chaque tuile est un calque
// plein cadre mis a l'echelle par transform:scale(1 + (--gs - 1) * --p). Un
// border-radius pose sur le <picture> est donc MULTIPLIE par cette echelle :
// 12 px sur la tuile centrale (--gs:4) valent 48 px a l'arrivee, quand elle
// occupe exactement la fenetre. Le banc sort donc, pour chaque tuile et chaque
// position : le rayon DECLARE, l'echelle, et le rayon VU a l'ecran (le produit
// des deux) — la seule valeur qui compte.
//
// Prerequis : Node 22+ (WebSocket global), Chrome installe, et le serveur local
// du depot sur http://localhost:8000 (configuration « mbc-static »).
//
//   node .claude/banc-galerie-zoom.mjs <etiquette> <LxH,LxH> [p,p] [options]
//     p             valeurs de --p mesurees (defaut 0,0.25,0.5,0.75,1)
//     --shots       une capture PNG par position
//     --css=f.css   injecte une feuille d'essai apres style.min.css
//     --perf        en plus : un defilement scripte de bout en bout, et le
//                   cout releve par Performance.getMetrics (TaskDuration,
//                   RecalcStyleCount, LayoutCount). C'est ce chiffre qui dit
//                   si un rayon recalcule a chaque image coute quelque chose.
//
// Sorties HORS du depot : %TEMP%/mbc-banc-galerie-zoom/<etiquette>.json (ou
// $MBC_BANC_SORTIE) et <etiquette>-<LxH>-pNNN.png.
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME = process.env.MBC_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.MBC_BASE || 'http://localhost:8000';
const SORTIE = process.env.MBC_BANC_SORTIE || join(tmpdir(), 'mbc-banc-galerie-zoom');
const argv = process.argv.slice(2);
const USAGE = 'usage : node .claude/banc-galerie-zoom.mjs <etiquette> <LxH,...> [p,...] [--shots] [--css=f.css] [--perf]\n';
if (argv.length < 2 || argv[0].startsWith('--') || argv[1].startsWith('--')) { process.stdout.write(USAGE); process.exit(2); }
const tag = argv[0];
const formats = argv[1].split(',');
const posArg = argv.slice(2).find(a => !a.startsWith('--'));
const pos = (posArg || '0,0.25,0.5,0.75,1').split(',').map(Number);
if (pos.some(Number.isNaN)) { process.stdout.write('positions illisibles : ' + posArg + '\n' + USAGE); process.exit(2); }
const shots = argv.includes('--shots');
const perf = argv.includes('--perf');
const cssFic = (argv.find(a => a.startsWith('--css=')) || '').slice(6);
const injecte = cssFic ? readFileSync(cssFic, 'utf8') : '';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const prof = mkdtempSync(join(tmpdir(), 'mbcbancgz'));
const ch = spawn(CHROME, ['--headless=new', '--hide-scrollbars', '--no-first-run',
  '--no-default-browser-check', '--disable-extensions', '--remote-debugging-port=0',
  '--user-data-dir=' + prof, '--window-size=1280,800', 'about:blank'], { stdio: 'ignore' });

let ws, n = 0;
const pend = new Map(), ecoute = new Set();
const send = (method, params = {}, sessionId) => { const id = ++n; ws.send(JSON.stringify({ id, method, params, sessionId })); return new Promise((res, rej) => pend.set(id, { res, rej, method })); };
const once = (method, s, ms = 30000) => new Promise((res, rej) => { const t = setTimeout(() => { ecoute.delete(l); rej(new Error('timeout ' + method)); }, ms); const l = d => { if (d.method === method && d.sessionId === s) { clearTimeout(t); ecoute.delete(l); res(d.params); } }; ecoute.add(l); });
async function evalp(s, expression) { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, s); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 400)); return r.result.value; }

const AIDE = css => '(() => {\n' +
  'const zone = document.getElementById("galerieZoom");\n' +
  'const R = e => { const b = e.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)]; };\n' +
  'window.__banc = {\n' +
  '  async prep() {\n' +
  '    const st = document.createElement("style"); st.id = "__banc";\n' +
  '    st.textContent = ".ccb{display:none!important}#nxCountdown{visibility:hidden!important}" + ' + JSON.stringify(css) + ';\n' +
  '    document.head.appendChild(st);\n' +
  '    document.documentElement.style.scrollBehavior = "auto";\n' +
  '    await document.fonts.ready;\n' +
  // les cliches du zoom sont en lazy et loin sous la ligne de flottaison :
  // sans cela, on mesure des boites vides
  '    document.querySelectorAll("img[loading=lazy]").forEach(i => { i.loading = "eager"; });\n' +
  '    zone.scrollIntoView({ block: "start", behavior: "instant" });\n' +
  '    await new Promise(r => setTimeout(r, 900));\n' +
  '    await Promise.all([...zone.querySelectorAll("img")].map(i => i.decode ? i.decode().catch(() => {}) : null));\n' +
  '    await new Promise(r => setTimeout(r, 400));\n' +
  '  },\n' +
  '  course() { return Math.max(1, zone.getBoundingClientRect().height - innerHeight); },\n' +
  '  hautZone() { return Math.round(zone.getBoundingClientRect().top + scrollY); },\n' +
  '  async aller(p) {\n' +
  '    const haut = this.hautZone(), c = this.course();\n' +
  '    window.scrollTo({ top: Math.round(haut + p * c), behavior: "instant" });\n' +
  '    for (let i = 0; i < 5; i++) await new Promise(r => requestAnimationFrame(r));\n' +
  // .is-moving tombe 180 ms apres le dernier defilement : on la laisse tomber
  '    await new Promise(r => setTimeout(r, 280));\n' +
  '    const pv = parseFloat(getComputedStyle(zone).getPropertyValue("--p")) || 0;\n' +
  '    const tuiles = [...zone.querySelectorAll(".g-tile")].map((t, i) => {\n' +
  '      const pic = t.querySelector("picture");\n' +
  '      const cs = getComputedStyle(pic), ct = getComputedStyle(t), ca = getComputedStyle(pic, "::after");\n' +
  '      const gs = parseFloat(ct.getPropertyValue("--gs")) || 4;\n' +
  '      const m = new DOMMatrixReadOnly(ct.transform);\n' +
  '      const rd = parseFloat(cs.borderTopLeftRadius) || 0;\n' +
  '      return { i, cls: [...t.classList].filter(c => c !== "g-tile").join("."),\n' +
  '        gs, echelleAttendue: +(1 + (gs - 1) * pv).toFixed(3), echelle: +m.a.toFixed(3),\n' +
  '        rayonDeclare: +rd.toFixed(2), rayonVu: +(rd * m.a).toFixed(2),\n' +
  '        ombre: cs.boxShadow === "none" ? null : cs.boxShadow.slice(0, 90),\n' +
  // le filet est un ::after (une ombre INTERNE sur le <picture> se peindrait
  // sous l'image, qui couvre toute la boite) : il faut donc le lire la
  '        filet: ca.content === "none" || ca.boxShadow === "none" ? null : ca.boxShadow.slice(0, 90),\n' +
  '        boite: R(pic) };\n' +
  '    });\n' +
  '    const t1 = zone.querySelector(".g-tile"), p1 = t1.querySelector("picture");\n' +
  '    const b = p1.getBoundingClientRect(), m1 = new DOMMatrixReadOnly(getComputedStyle(t1).transform);\n' +
  '    const cx = b.left + b.width / 2, cy = b.top + b.height / 2;\n' +
  '    const couvre = { l: Math.round(cx - b.width * m1.a / 2), t: Math.round(cy - b.height * m1.d / 2),\n' +
  '      w: Math.round(b.width * m1.a), h: Math.round(b.height * m1.d) };\n' +
  '    return { p, pCss: pv, y: Math.round(scrollY), vw: innerWidth, vh: innerHeight,\n' +
  '      bouge: zone.classList.contains("is-moving"), vivante: zone.classList.contains("is-live"),\n' +
  '      tuile1Couvre: couvre, tuiles };\n' +
  '  },\n' +
  '  async defiler(n) {\n' +
  '    const haut = this.hautZone(), c = this.course();\n' +
  '    for (let i = 0; i <= n; i++) {\n' +
  '      window.scrollTo({ top: Math.round(haut + (i / n) * c), behavior: "instant" });\n' +
  '      await new Promise(r => requestAnimationFrame(r));\n' +
  '    }\n' +
  '    await new Promise(r => setTimeout(r, 300));\n' +
  '    return n;\n' +
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
    await send('Page.navigate', { url: BASE + '/index.html?t=' + Date.now() }, s);
    await load;
    await evalp(s, AIDE(injecte));
    await evalp(s, '__banc.prep()');
    const rows = [];
    for (const p of pos) {
      rows.push(await evalp(s, '__banc.aller(' + p + ')'));
      if (shots) {
        const { data } = await send('Page.captureScreenshot', { format: 'png' }, s);
        writeFileSync(join(SORTIE, tag + '-' + fm + '-p' + String(Math.round(p * 100)).padStart(3, '0') + '.png'), Buffer.from(data, 'base64'));
      }
    }
    out[fm] = { positions: rows };
    if (perf) {
      await send('Performance.enable', {}, s);
      const lire = async () => Object.fromEntries((await send('Performance.getMetrics', {}, s)).metrics.map(m => [m.name, m.value]));
      await evalp(s, '__banc.aller(0)');
      const a = await lire();
      await evalp(s, '__banc.defiler(90)');
      const b = await lire();
      const d = k => +((b[k] || 0) - (a[k] || 0)).toFixed(4);
      out[fm].perf = { pas: 90, TaskDuration: d('TaskDuration'), ScriptDuration: d('ScriptDuration'),
        LayoutDuration: d('LayoutDuration'), RecalcStyleDuration: d('RecalcStyleDuration'),
        RecalcStyleCount: d('RecalcStyleCount'), LayoutCount: d('LayoutCount'),
        msParImage: +(d('TaskDuration') * 1000 / 90).toFixed(3) };
    }
    await send('Target.closeTarget', { targetId });
    process.stdout.write(fm + ' ok\n');
  }
  const fic = join(SORTIE, tag + '.json');
  writeFileSync(fic, JSON.stringify(out, null, 1));
  process.stdout.write('-> ' + fic + '\n');
}

main().catch(e => { process.stdout.write('ERREUR ' + e.message + '\n'); process.exitCode = 1; })
  .finally(() => { try { ws && ws.close(); } catch (e) {} ch.kill(); setTimeout(() => { try { rmSync(prof, { recursive: true, force: true }); } catch (e) {} process.exit(); }, 800); });
