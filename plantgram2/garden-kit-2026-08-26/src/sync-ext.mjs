/**
 * 측정값으로 FORM_EXT 표를 갱신합니다.
 *   node src/sync-ext.mjs [v3]
 * measure.mjs가 "갱신 필요"를 낼 때 이걸 돌리고, 다시 measure로 확인하세요.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const which = process.argv[2] === 'v3' ? 'v3' : 'v2';
const file = new URL(`./parts-${which}.mjs`, import.meta.url);
const { PLANT_FORMS, LEAF_TONES } = await import(`./parts-${which}.mjs`);

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
    return { w: +b.width.toFixed(1), h: +b.height.toFixed(1) };
  }, inner);
}
await browser.close();

let src = readFileSync(file, 'utf8');
for (const [id, { w, h }] of Object.entries(m)) {
  const re = new RegExp(`(\\n  ${id}:\\s*\\{ w: )[\\d.]+(,\\s*h: )[\\d.]+( \\},)`);
  if (!re.test(src)) { console.error(`${id} 항목을 표에서 못 찾았습니다`); process.exit(1); }
  src = src.replace(re, `$1${w}$2${h}$3`);
}
writeFileSync(file, src);
console.log(`parts-${which}.mjs의 FORM_EXT를 갱신했습니다:`);
for (const [id, v] of Object.entries(m)) console.log(`  ${id.padEnd(11)} ${v.w}×${v.h}`);
