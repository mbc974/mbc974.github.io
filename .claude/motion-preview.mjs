// Optional zero-dependency preview. Production remains static GitHub Pages.
import {createServer} from 'node:http';
import {readFile, stat} from 'node:fs/promises';
import {resolve, extname, sep} from 'node:path';
const root = process.cwd();
const args = process.argv.slice(2);
const port = Number(args[args.indexOf('--port') + 1]) || 4173;
const types = {'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.webp':'image/webp','.avif':'image/avif','.jpg':'image/jpeg','.png':'image/png','.woff2':'font/woff2','.pdf':'application/pdf','.mp4':'video/mp4','.ico':'image/x-icon','.txt':'text/plain','.ics':'text/calendar'};
createServer(async (req,res) => {
  try {
    const url = new URL(req.url,'http://localhost');
    const pathname = decodeURIComponent(url.pathname);
    if(pathname.split('/').some(p=>p.startsWith('.'))) throw Error('private');
    let path = resolve(root,'.'+pathname);
    if(path !== root && !path.startsWith(root+sep)) throw Error('outside');
    if((await stat(path)).isDirectory()) path=resolve(path,'index.html');
    let content=await readFile(path);
    if(extname(path)==='.html' && url.searchParams.has('qa')) {
      content=content.toString().replace('<head>','<head><script src="/lab/motion/measure.js"></script>');
    }
    res.writeHead(200,{'Content-Type':types[extname(path)]||'application/octet-stream','Cache-Control':'no-store'});
    res.end(content);
  } catch {res.writeHead(404);res.end('Not found');}
}).listen(port,'0.0.0.0',()=>console.log(`MBC preview on port ${port}`));
