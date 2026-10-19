// Static integrity check. This does not replace a browser interaction test.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
const root = path.resolve(process.argv[2] || 'frontend');
const files = fs.readdirSync(root);
const failures = [];
for (const name of files.filter(n => /\.(html|css)$/.test(n))) {
  const source = fs.readFileSync(path.join(root, name), 'utf8');
  const refs = [...source.matchAll(/(?:src|href)="([^"]+)"|url\(['"]?([^)'"\s]+)['"]?\)/g)];
  for (const match of refs) {
    const ref = (match[1] || match[2]).split(/[?#]/)[0];
    if (!ref || /^(?:https?:|data:|mailto:|\/)/.test(ref)) continue;
    if (!fs.existsSync(path.resolve(root, ref))) failures.push(`${name}: missing ${ref}`);
  }
  if (name.endsWith('.html')) {
    const ids = [...source.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]);
    if (new Set(ids).size !== ids.length) failures.push(`${name}: duplicate element ID`);
  }
}
for (const name of ['planner-app.js', 'config.js']) {
  try { new vm.Script(fs.readFileSync(path.join(root, name), 'utf8'), {filename: name}); }
  catch (error) { failures.push(error.message); }
}
if (failures.length) { console.error(failures.join('\n')); process.exit(1); }
console.log('Static links, element IDs and JavaScript syntax passed. Browser QA is separate.');
