/**
 * 측정값으로 FORM_EXT 표를 갱신합니다.
 *   node src/sync-ext.mjs [v3|sp]
 * measure.mjs가 "갱신 필요"를 낼 때 이걸 돌리고, 다시 measure로 확인하세요.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const arg = process.argv[2];
const name = arg === 'v3' ? 'parts-v3' : arg === 'sp' ? 'species-v1' : 'parts-v2';
const file = new URL(`./${name}.mjs`, import.meta.url);
const M = await import(`./${name}.mjs`);
const { LEAF_TONES } = M;
const PLANT_FORMS = M.PLANT_FORMS || M.SPECIES;

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--disable-gpu'],
});
const page = await browser.newPage();
await page.setContent('<body></body>');

const m = {};
for (const [id, def] of Object.entries(PLANT_FORMS)) {
  const inner = def.draw(46, 4, LEAF_TONES[0]);
  m[id] = await page.evaluate((svg) => {
    const d = document.createElement('div');
    d.innerHTML = `<svg width="600" height="600" viewBox="-300 -420 600 600"><g>${svg}</g></svg>`;
    document.body.appendChild(d);
    const b = d.querySelector('g').getBBox();
    d.remove();
    return { w: +b.width.toFixed(1), h: +b.height.toFixed(1), top: +(-b.y).toFixed(1) };
  }, inner);
}
await browser.close();

let src = readFileSync(file, 'utf8');
// FORM_EXT 블록만 떼어 그 안에서만 치환합니다 (PLANT_FORMS에 같은 이름이 또 있습니다)
const open = src.indexOf('export const FORM_EXT = {');
if (open < 0) { console.error('FORM_EXT 블록을 못 찾았습니다'); process.exit(1); }
const close = src.indexOf('\n};', open);
let block = src.slice(open, close);
for (const [id, { w, h, top }] of Object.entries(m)) {
  const re = new RegExp(`(\\n\\s+${id}:\\s*)\\{[^}]*\\},`);
  if (!re.test(block)) { console.error(`${id} 항목을 표에서 못 찾았습니다`); process.exit(1); }
  block = block.replace(re, `$1{ w: ${w}, h: ${h}, top: ${top} },`);
}
src = src.slice(0, open) + block + src.slice(close);
writeFileSync(file, src);
console.log(`${name}.mjs의 FORM_EXT를 갱신했습니다:`);
for (const [id, v] of Object.entries(m)) console.log(`  ${id.padEnd(13)} ${v.w}×${v.h}  화분 위 ${v.top}`);
