/**
 * 비율 자동 보정 — 감사에서 잰 실측값으로 FORM_FIT.h를 맞춥니다
 *
 *   node src/audit.mjs --json /tmp/a.json && node src/calibrate.mjs /tmp/a.json
 *
 * 왜 필요한가: FORM_FIT.h는 "화분 위로 이만큼 솟아라"는 목표치인데,
 * 실제로 렌더하면 잎이 겹치고 아래로 처지면서 목표에 못 미칩니다.
 * 눈으로 보고 손으로 맞추면 한 종을 고칠 때 다른 종이 틀어지므로,
 * 실측값과 목표치의 비로 한 번에 되돌립니다.
 *
 * 목표치는 골격에 따라 다릅니다.
 *   기둥·탑형  화분 높이의 2.6배   대가 서는 식물
 *   분수형     2.2배               위에서 퍼져 처지는 야자·고사리
 *   돔·구형    1.6배               방석처럼 낮은 다육·상추·화단
 */
import { readFileSync, writeFileSync } from 'node:fs';
const V3 = await import('./parts-v3.mjs');
const SP = await import('./species-v1.mjs');

/** 골격별 목표 — 화분 위로 솟은 높이 ÷ 화분 높이 */
const TARGET = {
  monstera: 2.6, strelitzia: 2.6, bamboo: 3.0, eucalyptus: 2.6, jade: 2.6,
  dieffenbachia: 2.4, broadleaf: 2.6, patterned: 2.4, upright: 2.6, cactus: 2.6,
  areca: 2.2, palm: 2.2, fern: 1.8, vine: 1.6, flower: 2.2,
  rosette: 1.3, lettuce: 1.6, geranium: 1.8, daisy: 2.0,
};

const audit = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const byFile = { species: 'species-v1.mjs', form: 'parts-v3.mjs' };
const edits = { 'species-v1.mjs': [], 'parts-v3.mjs': [] };
const blocked = [];

for (const r of audit.rows) {
  const want = TARGET[r.id];
  if (want == null || r.heightRatio == null) continue;
  // 실측이 목표의 ±12% 안이면 건드리지 않습니다
  if (Math.abs(r.heightRatio - want) / want < .12) continue;

  // 폭 상한이 걸려 있으면 fit.h를 올려도 배율이 안 바뀝니다.
  // 이때 필요한 건 비율 조정이 아니라 형태를 세로로 세우는 일입니다.
  const M = r.kind === 'species' ? SP : V3;
  const ext = M.FORM_EXT[r.id], fit = M.FORM_FIT[r.id];
  const { rx, h } = M.POTS.basic.p, potH = 46 * h, potW = 46 * rx * 2;
  const hTerm = fit.h * potH / (ext.top || ext.h), wTerm = fit.w * potW / ext.w;
  if (wTerm < hTerm * .98) {
    blocked.push({ id: r.id, measured: r.heightRatio, want,
      aspect: +(ext.w / (ext.top || ext.h)).toFixed(2) });
    continue;
  }
  edits[byFile[r.kind]].push({ id: r.id, measured: r.heightRatio, want });
}

for (const [file, list] of Object.entries(edits)) {
  if (!list.length) continue;
  let src = readFileSync(new URL(`./${file}`, import.meta.url), 'utf8');
  const open = src.indexOf('export const FORM_FIT = {');
  const close = src.indexOf('\n};', open);
  let block = src.slice(open, close);

  for (const e of list) {
    const re = new RegExp(`(\\n\\s+${e.id}:\\s*\\{ h: )([\\d.]+)(, w: [\\d.]+ \\},)`);
    const m = block.match(re);
    if (!m) { console.error(`${e.id}: FORM_FIT 항목을 못 찾았습니다`); continue; }
    const oldH = parseFloat(m[2]);
    // 실측이 목표보다 낮으면 그 비만큼 올립니다. 한 번에 2배 넘게는 움직이지 않습니다.
    const factor = Math.min(2, Math.max(.5, e.want / Math.max(.15, e.measured)));
    const newH = +(oldH * factor).toFixed(2);
    block = block.replace(re, `$1${newH}$3`);
    console.log(`${e.id.padEnd(13)} 실측 ${String(e.measured).padStart(5)} → 목표 ${e.want}  ·  fit.h ${oldH} → ${newH}`);
  }
  writeFileSync(new URL(`./${file}`, import.meta.url), src.slice(0, open) + block + src.slice(close));
}
if (blocked.length) {
  console.log('\n폭 상한에 막혀 비율로는 못 고치는 것들 — 형태를 세로로 세워야 합니다');
  console.log('(가로÷세로가 1을 크게 넘으면 넓적하다는 뜻입니다)');
  for (const b of blocked)
    console.log(`  ${b.id.padEnd(13)} 실측 ${String(b.measured).padStart(5)} (목표 ${b.want}) · 가로÷세로 ${b.aspect}`);
}
console.log('\n보정 완료 — audit을 다시 돌려 확인하세요');
