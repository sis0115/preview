/**
 * 형태별 자연 크기(bbox) 측정 — parts-v2.mjs의 FORM_EXT 표를 갱신하기 위한 도구.
 *
 *   node src/measure.mjs
 *
 * 그림(draw)을 고치면 자연 크기가 달라지므로 이 표도 같이 갱신해야
 * "식물이 이웃을 침범하지 않는다"는 비율 보증이 유지됩니다.
 */
import { execSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { PLANT_FORMS, LEAF_TONES, FORM_EXT, FORM_FIT, POTS } from './parts-v2.mjs';

/** playwright는 이 저장소의 의존성이 아니라 전역 설치본을 씁니다 */
async function loadPlaywright() {
  try {
    return await import('playwright');
  } catch {
    const root = execSync('npm root -g', { encoding: 'utf8' }).trim();
    return await import(pathToFileURL(join(root, 'playwright', 'index.mjs')).href);
  }
}
const { chromium } = await loadPlaywright();

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--disable-gpu'],
});
const page = await browser.newPage();
await page.setContent('<body></body>');

const measured = {};
for (const [id, def] of Object.entries(PLANT_FORMS)) {
  const inner = def.draw(46, 4, LEAF_TONES[0]);
  measured[id] = await page.evaluate((svg) => {
    const d = document.createElement('div');
    d.innerHTML = `<svg width="500" height="500" viewBox="-250 -350 500 500"><g>${svg}</g></svg>`;
    document.body.appendChild(d);
    const b = d.querySelector('g').getBBox();
    d.remove();
    return { w: +b.width.toFixed(1), h: +b.height.toFixed(1) };
  }, inner);
}
await browser.close();

let drift = 0;
console.log('형태        측정 w×h        표 w×h        상태');
for (const [id, m] of Object.entries(measured)) {
  const t = FORM_EXT[id];
  const ok = t && Math.abs(t.w - m.w) < 1.5 && Math.abs(t.h - m.h) < 1.5;
  if (!ok) drift++;
  console.log(`${id.padEnd(11)} ${`${m.w}×${m.h}`.padEnd(15)} ${(t ? `${t.w}×${t.h}` : '없음').padEnd(13)} ${ok ? 'OK' : '갱신 필요'}`);
}
console.log('\n적용 결과 (기본 화분, w=46):');
const { rx, h } = POTS.basic.p, potH = 46 * h, potW = 46 * rx * 2;
for (const [id, m] of Object.entries(measured)) {
  const f = FORM_FIT[id]; if (!f) continue;
  const sc = Math.min(f.h * potH / m.h, f.w * potW / m.w);
  console.log(`  ${id.padEnd(11)} 배율 ${sc.toFixed(2)} → 잎높이÷화분높이 ${(m.h * sc / potH).toFixed(2)} · 잎폭÷화분폭 ${(m.w * sc / potW).toFixed(2)}`);
}
if (drift) { console.error(`\nFORM_EXT ${drift}개가 실제와 다릅니다 — parts-v2.mjs의 표를 위 측정값으로 갱신하세요.`); process.exit(1); }
