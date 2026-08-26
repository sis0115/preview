/**
 * 정원 에셋 빌드 파이프라인
 *
 *   node src/build.mjs [--png]
 *
 * 1) dist/manifest.json  — 파츠 카탈로그 (Flutter/앱의 계약서)
 * 2) dist/catalog-data.js — 카탈로그 페이지가 쓰는 브라우저 번들
 * 3) --png 옵션 시: dist/sprites/*.png — 헤드리스 Chromium으로 래스터화
 *    (Flutter는 SVG를 flutter_svg로 직접 쓸 수 있어 PNG는 선택 사항)
 */
import { writeFileSync, mkdirSync, readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildManifest, composeAvatar, toSVGDoc, PLANT_FORMS, POTS, POT_COLORS } from './parts.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dist = join(root, 'dist');
mkdirSync(dist, { recursive: true });

/* 1) manifest */
const manifest = buildManifest();
writeFileSync(join(dist, 'manifest.json'), JSON.stringify(manifest, null, 2));
console.log(`manifest.json — 파츠 ${manifest.counts.pots}화분 × ${manifest.counts.potColors}색 × ${manifest.counts.forms}형태 × 4단계 × ${manifest.counts.props}소품 = ${manifest.counts.combinations.toLocaleString()} 조합`);

/* 2) 브라우저 번들 (parts.mjs를 그대로 복사 — 단일 소스 유지) */
const src = readFileSync(join(root, 'src', 'parts.mjs'), 'utf8');
writeFileSync(join(dist, 'parts-browser.mjs'), src);
console.log('parts-browser.mjs — 카탈로그 페이지용 복사 완료');

/* 3) PNG 스프라이트 (선택) */
if (process.argv.includes('--png')) {
  const { chromium } = await import('playwright');
  const spriteDir = join(dist, 'sprites');
  mkdirSync(spriteDir, { recursive: true });

  const jobs = [];
  for (const form of Object.keys(PLANT_FORMS))
    for (let stage = 1; stage <= 4; stage++)
      jobs.push({ file: `${form}_s${stage}.png`, opts: { form, stage, w: 46 } });
  for (const pot of Object.keys(POTS))
    jobs.push({ file: `pot_${pot}.png`, opts: { pot, form: 'broadleaf', stage: 0, w: 46 } });

  const browser = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--disable-gpu'],
  });
  const page = await browser.newPage({ viewport: { width: 320, height: 320 }, deviceScaleFactor: 3 });

  for (const j of jobs) {
    const inner = j.opts.stage === 0
      ? composeAvatar({ ...j.opts, stage: 1, form: 'rosette' })
      : composeAvatar({ ...j.opts, potColor: POT_COLORS[0].hex });
    const svg = toSVGDoc(inner, 160, 220, 10);
    await page.setContent(`<body style="margin:0;display:grid;place-items:center;background:transparent">${svg}</body>`);
    const el = page.locator('svg');
    await el.screenshot({ path: join(spriteDir, j.file), omitBackground: true });
  }
  await browser.close();
  console.log(`sprites/ — PNG ${jobs.length}장 (@3x, 투명배경)`);
}
