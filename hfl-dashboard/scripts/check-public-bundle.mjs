// Release gate: inspects the exported site for restricted files, internal paths
// and repository/network endpoints. Fails the build on any finding.
import fs from "node:fs";
import path from "node:path";

const OUT = path.resolve("out");
const ALLOWED_EXT = new Set([".html", ".js", ".css", ".svg", ".woff2", ".woff", ".txt", ".xml", ".ico", ".png", ".json"]);
const FORBIDDEN_EXT = /\.(py|tex|ipynb|npy|npz|pt|pth|ckpt|log|csv|parquet|h5|pkl|env|map)$/i;
const FORBIDDEN_TEXT = [
  [/api\.github\.com/i, "GitHub API endpoint"],
  [/raw\.githubusercontent\.com/i, "raw repository URL"],
  [/\/home\/[a-z]/i, "absolute home path"],
  [/DEADSERPENT/, "local workspace name"],
  [/SIMULATORS\//, "internal directory name"],
  [/PHASE REPORT|_eicu_acc|patient_id|uniquepid/i, "internal artefact name"],
  [/-----BEGIN [A-Z ]*PRIVATE KEY-----/, "private key"],
  [/\b(sk|ghp|gho|github_pat)_[A-Za-z0-9_]{16,}/, "token-like secret"],
];

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]));
}

if (!fs.existsSync(OUT)) {
  console.error("check-public-bundle: no out/ directory");
  process.exit(1);
}
const problems = [];
const files = walk(OUT);
for (const f of files) {
  const rel = path.relative(OUT, f);
  const ext = path.extname(f).toLowerCase();
  if (FORBIDDEN_EXT.test(f)) problems.push(`${rel}: restricted file type`);
  else if (!ALLOWED_EXT.has(ext)) problems.push(`${rel}: unexpected file type ${ext || "(none)"}`);
  if ([".html", ".js", ".css", ".txt", ".xml", ".json", ".svg"].includes(ext)) {
    const text = fs.readFileSync(f, "utf8");
    for (const [re, what] of FORBIDDEN_TEXT) if (re.test(text)) problems.push(`${rel}: contains ${what}`);
  }
}
if (problems.length) {
  console.error(`check-public-bundle: ${problems.length} problem(s)\n- ${problems.join("\n- ")}`);
  process.exit(1);
}
console.log(`check-public-bundle: ${files.length} files inspected, no restricted content found.`);
