// Minimal static server for the exported site (used by Playwright and `npm run serve`).
import http from "node:http";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(process.argv.includes("--dir") ? process.argv[process.argv.indexOf("--dir") + 1] : "out");
const port = Number(process.argv.includes("--port") ? process.argv[process.argv.indexOf("--port") + 1] : 4173);
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".json": "application/json", ".txt": "text/plain", ".xml": "application/xml", ".woff2": "font/woff2", ".woff": "font/woff", ".png": "image/png", ".ico": "image/x-icon" };

if (!fs.existsSync(root)) {
  console.error(`No build output at ${root}. Run "npm run build" first.`);
  process.exit(1);
}

http
  .createServer((req, res) => {
    const url = decodeURIComponent((req.url ?? "/").split("?")[0]);
    let file = path.join(root, path.normalize(url).replace(/^(\.\.[/\\])+/, ""));
    if (!file.startsWith(root)) return res.writeHead(403).end();
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, "index.html");
    if (!fs.existsSync(file) && fs.existsSync(`${file}.html`)) file = `${file}.html`;
    if (!fs.existsSync(file)) {
      res.writeHead(404, { "content-type": TYPES[".html"] });
      return fs.createReadStream(path.join(root, "404.html")).pipe(res);
    }
    res.writeHead(200, { "content-type": TYPES[path.extname(file)] ?? "application/octet-stream" });
    fs.createReadStream(file).pipe(res);
  })
  .listen(port, "127.0.0.1", () => console.log(`Serving ${root} at http://127.0.0.1:${port}/`));
