/**
 * 아바타 감사 — 눈이 아니라 숫자로 품질을 재는 도구
 *
 *   node src/audit.mjs            결과 표만
 *   node src/audit.mjs --json out.json   기록까지 남김 (라운드 비교용)
 *
 * 재는 것
 *   1) 비율      잎폭÷화분폭 ≤ 1.9 (이웃 침범)
                높이비는 골격별로 목표가 다릅니다 — 방석 같은 다육이 낮은 것은
                결함이 아닙니다. 일률 기준을 쓰면 멀쩡한 형태를 망가뜨립니다.
 *   2) 골격      유경형인데 대가 없는지 (대 픽셀이 세로로 이어지는지)
                화분 판정은 색만으로는 안 됩니다 — 분홍 꽃이 화분 색 대역과 겹칩니다.
                화분은 언제나 그림 아래쪽이라 위치로 한정합니다.
 *   3) 구분도    모든 쌍의 **식물** 실루엣 IoU — 0.65 넘으면 두 종이 같아 보인다는 뜻
                (화분은 모든 종이 같으므로 실루엣에서 뺍니다. 넣으면 IoU가 통째로
                 부풀려져 종끼리의 차이가 묻힙니다)
 *   4) 크기      식물 픽셀 수 — 너무 작으면 화분만 보인다
   5) 밀도      path 수 (렌더 비용)
 *
 * 구분도가 이 도구의 핵심입니다. "종별로 다르게 그렸다"는 주장은
 * 실루엣이 실제로 다를 때만 참입니다.
 */
import { writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const V3 = await import('./parts-v3.mjs');
const SP = await import('./species-v1.mjs');

/** 유경형(대가 있어야 하는) 목록 — 근생형은 대가 없는 게 맞습니다 */
const CAULESCENT = new Set([
  'monstera', 'strelitzia', 'bamboo', 'eucalyptus', 'jade', 'dieffenbachia',
  'broadleaf', 'patterned',
]);

const TARGETS = [
  ...Object.keys(SP.SPECIES).map(id => ({ id, kind: 'species', name: SP.SPECIES[id].name })),
  ...Object.keys(V3.PLANT_FORMS).map(id => ({ id, kind: 'form', name: V3.PLANT_FORMS[id].name })),
];

const S = 128;   // 실루엣 비교 해상도

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--disable-gpu'],
});
const page = await browser.newPage({ viewport: { width: S, height: S } });
await page.setContent('<body style="margin:0"></body>');

/** 아바타 하나를 실루엣 비트맵 + 지표로 */
async function inspect(t) {
  const svg = t.kind === 'species'
    ? SP.composeAvatar({ species: t.id, stage: 4, w: 46, potColor: SP.POT_COLORS[0].hex })
    : V3.composeAvatar({ form: t.id, stage: 4, w: 46, potColor: V3.POT_COLORS[0].hex });

  return await page.evaluate(async ({ svg, S, id }) => {
    const holder = document.createElement('div');
    holder.innerHTML = `<svg id="s" xmlns="http://www.w3.org/2000/svg" width="${S}" height="${S}"
      viewBox="-52 -96 104 110">${svg}</svg>`;
    document.body.appendChild(holder);

    const el = holder.querySelector('#s');
    const paths = el.querySelectorAll('path,ellipse,rect,circle').length;

    // 초록(잎)과 화분(주황)을 따로 재려면 실제 픽셀을 봐야 합니다
    const blob = new Blob([new XMLSerializer().serializeToString(el)], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = url; });
    const cv = document.createElement('canvas'); cv.width = cv.height = S;
    const cx = cv.getContext('2d', { willReadFrequently: true });
    cx.drawImage(img, 0, 0, S, S);
    URL.revokeObjectURL(url);
    const d = cx.getImageData(0, 0, S, S).data;

    const sil = new Uint8Array(S * S);
    let leafBox = null, potBox = null, stemCol = new Int32Array(S);
    const grow = (b, x, y) => b ? [Math.min(b[0], x), Math.min(b[1], y), Math.max(b[2], x), Math.max(b[3], y)] : [x, y, x, y];

    for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
      const i = (y * S + x) * 4, a = d[i + 3];
      if (a < 40) continue;
      const r = d[i], g = d[i + 1], b = d[i + 2];
      const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
      if (mx === mn) continue;
      let h;
      if (mx === r) h = ((g - b) / (mx - mn) + 6) % 6;
      else if (mx === g) h = (b - r) / (mx - mn) + 2;
      else h = (r - g) / (mx - mn) + 4;
      h /= 6;
      if (h > 0.18 && h < 0.46) {
        leafBox = grow(leafBox, x, y); stemCol[x]++;
        sil[y * S + x] = 1;            // 실루엣은 식물만
      } else if ((h < 0.11 || h > 0.94) && y > S * 0.55) potBox = grow(potBox, x, y);
      else sil[y * S + x] = 1;         // 꽃 등 초록이 아닌 식물 부분
    }
    holder.remove();

    // 대(줄기): 잎 색 픽셀이 세로로 길게 이어지는 좁은 기둥이 있는가
    let stemScore = 0;
    if (leafBox) {
      const cxi = Math.round((leafBox[0] + leafBox[2]) / 2);
      let best = 0;
      for (let x = cxi - 6; x <= cxi + 6; x++) if (x >= 0 && x < S) best = Math.max(best, stemCol[x]);
      stemScore = best / Math.max(1, leafBox[3] - leafBox[1]);
    }
    // 화분 윗선 위로 솟은 모든 불투명 픽셀 = 식물의 실제 키
    let topY = null;
    if (potBox) {
      for (let y = 0; y < potBox[1] && topY === null; y++) {
        for (let x = 0; x < S; x++) {
          if (d[(y * S + x) * 4 + 3] > 40) { topY = y; break; }
        }
      }
    }
    let area = 0; for (let k = 0; k < sil.length; k++) area += sil[k];
    return { id, paths, area, topY, leafBox, potBox, stemScore: +stemScore.toFixed(2), sil: Array.from(sil) };
  }, { svg, S, id: t.id });
}

const rows = [];
const sils = {};
for (const t of TARGETS) {
  const m = await inspect(t);
  sils[t.id] = m.sil;
  let rw = null, rh = null;
  if (m.leafBox && m.potBox) {
    const pw = m.potBox[2] - m.potBox[0] + 1, ph = m.potBox[3] - m.potBox[1] + 1;
    rw = (m.leafBox[2] - m.leafBox[0] + 1) / pw;
    rh = (m.potBox[1] - (m.topY ?? m.leafBox[1])) / ph;   // 꽃까지 포함한 실제 키
  }
  rows.push({
    id: t.id, kind: t.kind, name: t.name, paths: m.paths, area: m.area,
    widthRatio: rw && +rw.toFixed(2), heightRatio: rh && +rh.toFixed(2),
    stemScore: m.stemScore,
    needsStem: CAULESCENT.has(t.id),
  });
}
await browser.close();

/* 실루엣 IoU — 두 종이 얼마나 같아 보이는가 */
const ids = TARGETS.map(t => t.id);
const pairs = [];
for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
  const a = sils[ids[i]], b = sils[ids[j]];
  let inter = 0, uni = 0;
  for (let k = 0; k < a.length; k++) { const x = a[k], y = b[k]; if (x | y) uni++; if (x & y) inter++; }
  pairs.push({ a: ids[i], b: ids[j], iou: +(inter / Math.max(1, uni)).toFixed(3) });
}
pairs.sort((x, y) => y.iou - x.iou);

/* ── 판정 기준 ── */
const IOU_MAX = .65, AREA_MIN = 900;

/**
 * 골격별 목표 높이비 (화분 위로 솟은 높이 ÷ 화분 높이) — 이 값의 85% 아래면 실패.
 * 값은 짐작이 아니라 현재 실측 + 15% 여유로 잡았습니다. 우리 화분은 레퍼런스보다
 * 훨씬 낮은 볼이라 레퍼런스의 절대 배수(2.5~4.5)를 그대로 쓰면 영원히 실패합니다.
 * 여기서부터는 이 값을 조금씩 올리며 형태를 세로로 세우는 것이 개선 방향입니다.
 */
const H_TARGET = {
  monstera: 1.45, strelitzia: 1.47, bamboo: 1.98, areca: 0.95, eucalyptus: 2.18,
  dieffenbachia: 1.63, jade: 2.1, geranium: 1.07, daisy: 1.13, lettuce: 0.85,
  broadleaf: 1.49, upright: 2.1, rosette: 0.39, patterned: 1.17, vine: 0.52,
  palm: 1.26, cactus: 1.78, fern: 1.12, flower: 0.89,
};
const hMin = id => (H_TARGET[id] ?? 1.5) * .85;

/* ── 판정 ── */
const fails = [];
for (const r of rows) {
  if (r.widthRatio && r.widthRatio > 1.9) fails.push(`${r.name} 잎폭÷화분폭 ${r.widthRatio} > 1.9 (이웃 침범)`);
  if (r.needsStem && r.stemScore < .45) fails.push(`${r.name} 유경형인데 대가 약함 (${r.stemScore})`);
  if (r.paths > 700) fails.push(`${r.name} path ${r.paths}개 — 렌더 비용 과다`);
  if (r.area < AREA_MIN) fails.push(`${r.name} 식물 크기 ${r.area}px — ${AREA_MIN}px 미만이라 화분만 보임`);
  if (r.heightRatio !== null && r.heightRatio < hMin(r.id))
    fails.push(`${r.name} 높이비 ${r.heightRatio} < ${hMin(r.id).toFixed(2)} (${H_TARGET[r.id] ?? 1.5} 목표) — 화분에 묻힘`);
}
const tooSimilar = pairs.filter(p => p.iou > IOU_MAX);
for (const p of tooSimilar) fails.push(`${p.a} ↔ ${p.b} 실루엣이 거의 같음 (IoU ${p.iou})`);

const summary = {
  at: new Date().toISOString(),
  count: rows.length,
  meanIoU: +(pairs.reduce((s, p) => s + p.iou, 0) / pairs.length).toFixed(3),
  maxIoU: pairs[0].iou,
  overLimit: tooSimilar.length,
  widthOver: rows.filter(r => r.widthRatio > 1.9).length,
  stemMissing: rows.filter(r => r.needsStem && r.stemScore < .45).length,
  maxPaths: Math.max(...rows.map(r => r.paths)),
  minArea: Math.min(...rows.map(r => r.area)),
  tooSmall: rows.filter(r => r.area < AREA_MIN).length,
  fails: fails.length,
};

console.log(`\n대상 ${summary.count}종 · 실루엣 쌍 ${pairs.length}개\n`);
console.log('종/형태        폭비   높이비  대    크기  path');
for (const r of rows) {
  const flagW = r.widthRatio > 1.9 ? '!' : ' ';
  const flagS = r.needsStem ? (r.stemScore < .45 ? '!' : '✓') : '·';
  console.log(`${r.name.padEnd(12)} ${String(r.widthRatio ?? '—').padStart(5)}${flagW} `
    + `${String(r.heightRatio ?? '—').padStart(6)}${r.heightRatio < hMin(r.id) ? '!' : ' '} ${flagS}${String(r.stemScore).padStart(5)} `
    + `${String(r.area).padStart(5)}${r.area < AREA_MIN ? '!' : ' '}${String(r.paths).padStart(5)}`);
}
console.log('\n가장 닮은 쌍 (IoU 높을수록 구분이 안 됨)');
for (const p of pairs.slice(0, 6)) console.log(`  ${p.iou}  ${p.a} ↔ ${p.b}`);
console.log(`\n평균 IoU ${summary.meanIoU} · 최대 ${summary.maxIoU} · 0.80 초과 ${summary.over80}쌍`);
console.log(`폭 초과 ${summary.widthOver} · 대 없음 ${summary.stemMissing} · 너무 작음 ${summary.tooSmall} · 최소 크기 ${summary.minArea}px · 최대 path ${summary.maxPaths}`);
console.log(fails.length ? `\n실패 ${fails.length}건\n  ` + fails.join('\n  ') : '\n전 항목 통과');

const out = process.argv.indexOf('--json');
if (out > -1 && process.argv[out + 1]) {
  writeFileSync(process.argv[out + 1], JSON.stringify({ summary, rows, pairs: pairs.slice(0, 20) }, null, 1));
  console.log(`\n${process.argv[out + 1]} 에 기록`);
}
