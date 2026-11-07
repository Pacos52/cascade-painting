import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const publicDir = path.resolve('public');
function files(dir) {
  return fs.readdirSync(dir, {withFileTypes:true}).flatMap(entry => entry.isDirectory() ? files(path.join(dir,entry.name)) : [path.join(dir,entry.name)]);
}
test('public website never publishes the retired street address or a business street-address schema', () => {
  const readable = files(publicDir).filter(file => /\.(html|js|json|xml|txt|webmanifest)$/.test(file));
  assert.ok(readable.filter(file=>file.endsWith('.html')).length >= 29);
  for (const file of readable) {
    const content = fs.readFileSync(file,'utf8');
    assert.doesNotMatch(content, /24(?:\s|%20|\+)+green(?:\s|%20|\+)+st(?:reet)?\b/i, path.relative(publicDir,file));
    assert.doesNotMatch(content, /["']streetAddress["']\s*:/i, path.relative(publicDir,file));
  }
  const home = fs.readFileSync(path.join(publicDir,'index.html'),'utf8');
  assert.match(home,/Serving Montgomery County, PA/);
  assert.match(home,/tel:\+12674614367/);
});
