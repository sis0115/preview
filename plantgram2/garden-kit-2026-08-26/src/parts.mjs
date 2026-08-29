/**
 * 플랜트그램 정원 파츠 라이브러리 — 단일 소스 오브 트루스
 *
 * 이 파일 하나가 세 가지를 동시에 먹여살립니다.
 *   1) 브라우저 카탈로그 (index.html)  — 디자인 검수용
 *   2) manifest.json                   — Flutter 앱이 읽는 계약서
 *   3) PNG 스프라이트 (build.mjs)      — 필요 시 래스터 내보내기
 *
 * 파츠는 "파라미터로 그리는 도형"입니다. 나중에 디자이너가 그린 SVG로
 * 교체할 때도 draw()의 반환값만 바꾸면 되고, 앵커/슬롯 규약은 그대로입니다.
 *
 * 좌표 규약: 모든 파츠의 원점(0,0)은 "바닥이 지면에 닿는 지점"입니다.
 *            위로 갈수록 y가 음수. w = 파츠의 기준 폭(px).
 */

export const VERSION = 1;

/** 아이소메트릭 격자 — 정원 씬과 앱이 공유하는 상수 */
export const GRID = { tileW: 78, tileH: 39, zH: 44 };

/* ------------------------------------------------------------------ */
/* 팔레트                                                              */
/* ------------------------------------------------------------------ */

/** 화분 색 — 전부 무료. unlock은 "언제 열리는지"일 뿐 과금이 아닙니다. */
export const POT_COLORS = [
  { id: 'terracotta', name: '테라코타', hex: '#c98a6a', unlock: 'free' },
  { id: 'sage',       name: '세이지',   hex: '#8fa89b', unlock: 'free' },
  { id: 'sand',       name: '샌드',     hex: '#dcc9a8', unlock: 'free' },
  { id: 'clay',       name: '클레이',   hex: '#a8785d', unlock: 'free' },
  { id: 'lilac',      name: '라일락',   hex: '#b7a3c9', unlock: 'lv3' },
  { id: 'coral',      name: '코랄',     hex: '#e0a08c', unlock: 'lv3' },
  { id: 'sky',        name: '스카이',   hex: '#9fb8d0', unlock: 'lv5' },
  { id: 'charcoal',   name: '차콜',     hex: '#6b7169', unlock: 'lv8' },
];

/** 잎 색조 — 식물종의 기본값이 있고, 무늬종은 variegated를 씁니다. */
export const LEAF_TONES = [
  { id: 'green',      name: '기본 초록', base: '#3f7d54', alt: '#4f9163', vein: '#2c5b3c' },
  { id: 'deep',       name: '진초록',   base: '#356a48', alt: '#437c55', vein: '#254d33' },
  { id: 'light',      name: '연초록',   base: '#5c9c6c', alt: '#6bad7b', vein: '#3d7350' },
  { id: 'variegated', name: '무늬종',   base: '#4a8b5c', alt: '#8fbf95', vein: '#2f6040' },
  { id: 'silver',     name: '실버',     base: '#6d9683', alt: '#9fbcac', vein: '#4c7060' },
];

/* ------------------------------------------------------------------ */
/* 유틸                                                                */
/* ------------------------------------------------------------------ */

export function shade(hex, amt) {
  const n = parseInt(hex.slice(1), 16);
  const c = v => Math.max(0, Math.min(255, v));
  const r = c((n >> 16) + amt), g = c(((n >> 8) & 255) + amt), b = c((n & 255) + amt);
  return '#' + ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0');
}
const n1 = v => Math.round(v * 100) / 100;

/* ------------------------------------------------------------------ */
/* 화분 — 파라메트릭                                                    */
/* ------------------------------------------------------------------ */

/**
 * 화분 몸통. 원점은 바닥 중앙.
 * rx  상단 반지름(폭 대비)   ry  상단 타원의 세로 반지름
 * h   높이                   br  바닥 반지름
 * bulge  옆선 곡률 (+ 항아리 / 0 직선 / - 오목)
 */
function potShape(w, color, { rx, ry, h, br, bulge = 0, rim = 0 }) {
  const RX = w * rx, RY = w * ry, H = w * h, BR = w * br;
  const dark = shade(color, -28), light = shade(color, 18), rimC = shade(color, 24);
  const cx = RX + bulge * RX;
  const side = `M${-RX},${-H} Q${-cx},${-H * 0.45} ${-BR},-3 Q${-BR},0 ${-BR + 4},0
                L${BR - 4},0 Q${BR},0 ${BR},-3 Q${cx},${-H * 0.45} ${RX},${-H} Z`;
  const half = `M${-RX},${-H} Q${-cx},${-H * 0.45} ${-BR},-3 Q${-BR},0 ${-BR + 4},0 L0,0 L0,${-H} Z`;
  return `
    <path d="${side}" fill="${color}"/>
    <path d="${half}" fill="${dark}" opacity=".34"/>
    <ellipse cx="0" cy="0" rx="${n1(BR)}" ry="${n1(BR * 0.33)}" fill="${dark}"/>
    ${rim ? `<path d="M${-RX * 1.08},${-H} L${RX * 1.08},${-H} L${RX},${-H + rim * w} L${-RX},${-H + rim * w} Z" fill="${rimC}" opacity=".9"/>` : ''}
    <ellipse cx="0" cy="${n1(-H)}" rx="${n1(RX)}" ry="${n1(RY)}" fill="${rimC}"/>
    <ellipse cx="0" cy="${n1(-H + RY * 0.18)}" rx="${n1(RX * 0.8)}" ry="${n1(RY * 0.76)}" fill="#5b4736"/>
    <ellipse cx="${n1(RX * 0.24)}" cy="${n1(-H * 0.55)}" rx="${n1(RX * 0.26)}" ry="${n1(H * 0.3)}" fill="${light}" opacity=".26"/>`;
}

export const POTS = {
  basic:   { name: '기본 화분',   unlock: 'free', p: { rx: .50, ry: .22, h: .74, br: .335 } },
  bowl:    { name: '낮은 볼',     unlock: 'free', p: { rx: .55, ry: .24, h: .44, br: .40 } },
  tall:    { name: '긴 화분',     unlock: 'free', p: { rx: .42, ry: .19, h: 1.02, br: .32 } },
  urn:     { name: '항아리',      unlock: 'lv3',  p: { rx: .40, ry: .18, h: .82, br: .30, bulge: .34 } },
  rimmed:  { name: '테두리 화분', unlock: 'lv5',  p: { rx: .48, ry: .21, h: .70, br: .34, rim: .07 } },
  tapered: { name: '콘 화분',     unlock: 'lv8',  p: { rx: .52, ry: .23, h: .82, br: .22, bulge: -.16 } },
};

/** 화분 그리기 */
export function drawPot(potId, w, colorHex) {
  const def = POTS[potId] || POTS.basic;
  return `<g class="pot">${potShape(w, colorHex, def.p)}</g>`;
}
/** 화분 위 "흙 표면" 높이 — 식물을 여기에 심습니다 */
export function potRimY(potId, w) {
  const def = POTS[potId] || POTS.basic;
  return -w * def.p.h;
}

/* ------------------------------------------------------------------ */
/* 식물 — 형태 8종 × 성장 4단계                                         */
/* ------------------------------------------------------------------ */

const STAGE_SCALE = [0.52, 0.72, 0.9, 1.0];   // 1~4단계 크기
const STAGE_COUNT = [0.4, 0.65, 0.85, 1.0];   // 1~4단계 잎 개수 비율

function leafBlade(x, y, rot, s, fill, vein) {
  return `<g transform="translate(${n1(x)},${n1(y)}) rotate(${n1(rot)}) scale(${n1(s)})">
    <path d="M0,0 C-16,-7 -20,-28 0,-39 C20,-28 16,-7 0,0 Z" fill="${fill}"/>
    <path d="M0,-2 L0,-36" stroke="${vein}" stroke-width="1.4" opacity=".5"/>
    <path d="M0,-13 L-8,-19 M0,-21 L-8,-27 M0,-13 L8,-19 M0,-21 L8,-27"
      stroke="${vein}" stroke-width="1" opacity=".3" fill="none"/></g>`;
}
const pick = (arr, ratio) => arr.slice(0, Math.max(1, Math.round(arr.length * ratio)));

export const PLANT_FORMS = {
  /* 대엽형 — 몬스테라, 필로덴드론, 알로카시아 */
  broadleaf: {
    name: '대엽형', species: ['몬스테라', '필로덴드론', '알로카시아', '고무나무'],
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46;
      const L = pick([[1, -45, -4, .98], [-14, -31, -33, .9], [16, -33, 31, .85],
                      [-9, -17, -60, .7], [11, -16, 56, .66]], STAGE_COUNT[stage - 1]);
      let o = `<path d="M0,0 C0,-24 1,-38 1,-46" stroke="${tone.vein}" stroke-width="2.2" fill="none"/>`;
      L.forEach(([x, y, r, c], i) => { o += leafBlade(x, y, r, c, i % 2 ? tone.alt : tone.base, tone.vein); });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },
  /* 직립형 — 산세베리아, 스투키 */
  upright: {
    name: '직립형', species: ['산세베리아', '스투키', '금전수'],
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46, edge = '#c9b96a';
      const L = pick([[0, -56, 0, 1], [-12, -46, -13, .9], [12, -48, 13, .92],
                      [-6, -38, -6, .72], [7, -40, 7, .75]], STAGE_COUNT[stage - 1]);
      let o = '';
      L.forEach(([x, y, r, c], i) => {
        o += `<g transform="translate(${x},0) rotate(${r})">
          <path d="M0,0 C${n1(-5 * c)},${n1(y * .55)} ${n1(-4 * c)},${n1(y * .85)} 0,${y}
                   C${n1(4 * c)},${n1(y * .85)} ${n1(5 * c)},${n1(y * .55)} 0,0 Z" fill="${i % 2 ? tone.alt : tone.base}"/>
          <path d="M0,0 C${n1(-5 * c)},${n1(y * .55)} ${n1(-4 * c)},${n1(y * .85)} 0,${y}"
                stroke="${edge}" stroke-width="1.1" fill="none" opacity=".55"/></g>`;
      });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },
  /* 로제트형 — 다육, 에케베리아 */
  rosette: {
    name: '로제트형', species: ['다육식물', '에케베리아', '하월시아'],
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46;
      const cnt = Math.round(9 * STAGE_COUNT[stage - 1]) + 3;
      let o = '';
      for (let i = 0; i < cnt; i++) {
        o += `<g transform="rotate(${n1(i * (360 / cnt))}) translate(0,-13)">
          <ellipse rx="6" ry="12" fill="${i % 2 ? tone.alt : tone.base}"/></g>`;
      }
      return `<g transform="translate(0,-13) scale(${n1(k * s)})">${o}
        <circle r="5.5" fill="${tone.vein}"/></g>`;
    }
  },
  /* 무늬엽형 — 칼라데아, 마란타 */
  patterned: {
    name: '무늬엽형', species: ['칼라데아', '마란타', '스킨답서스'],
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46, mark = '#d7e4c9';
      const L = pick([[0, -42, -6, 1.05], [-16, -30, -40, .95], [16, -31, 38, .96],
                      [-8, -18, -62, .7], [9, -19, 58, .72]], STAGE_COUNT[stage - 1]);
      let o = `<path d="M0,0 L0,-20" stroke="${tone.vein}" stroke-width="2"/>`;
      L.forEach(([x, y, r, c], i) => {
        o += `<g transform="translate(${x},${y}) rotate(${r}) scale(${c})">
          <ellipse cy="-17" rx="11" ry="20" fill="${i % 2 ? tone.alt : tone.base}"/>
          <ellipse cy="-17" rx="5" ry="14" fill="${mark}" opacity=".5"/>
          <path d="M0,2 L0,-32" stroke="${mark}" stroke-width="1.4" opacity=".65"/></g>`;
      });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },
  /* 덩굴형 — 포토스, 아이비 */
  vine: {
    name: '덩굴형', species: ['포토스', '아이비', '스킨답서스', '립살리스'],
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46;
      const L = pick([[0, -34, 0, .9], [-15, -24, -30, .8], [15, -26, 30, .78],
                      [-24, -8, -72, .66], [24, -10, 70, .64], [-10, -46, -14, .7],
                      [-30, 6, -96, .58], [30, 4, 94, .56]], STAGE_COUNT[stage - 1]);
      let o = '';
      L.forEach(([x, y, r, c], i) => {
        o += `<g transform="translate(${x},${y}) rotate(${r}) scale(${c})">
          <path d="M0,0 C-13,-6 -16,-22 0,-30 C16,-22 13,-6 0,0 Z" fill="${i % 2 ? tone.alt : tone.base}"/>
          <path d="M0,-3 L0,-27" stroke="${tone.vein}" stroke-width="1.2" opacity=".45"/></g>`;
      });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },
  /* 깃꼴형 — 야자, 아레카 */
  palm: {
    name: '깃꼴형', species: ['테이블야자', '아레카야자', '켄차야자'],
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46;
      const F = pick([[0, 1.0], [-26, .86], [26, .86], [-14, .7], [14, .7]], STAGE_COUNT[stage - 1]);
      let o = '';
      F.forEach(([rot, len], i) => {
        const H = 52 * len, fill = i % 2 ? tone.alt : tone.base;
        let pin = '';
        for (let j = 1; j <= 7; j++) {
          const t = j / 8, y = -H * t, sp = 13 * Math.sin(Math.PI * t) * .9;
          pin += `<path d="M0,${n1(y)} L${n1(-sp)},${n1(y - 7)} M0,${n1(y)} L${n1(sp)},${n1(y - 7)}"
                    stroke="${fill}" stroke-width="4" stroke-linecap="round"/>`;
        }
        o += `<g transform="rotate(${rot})"><path d="M0,0 L0,${n1(-H)}" stroke="${tone.vein}" stroke-width="2"/>${pin}</g>`;
      });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },
  /* 기둥형 — 선인장 */
  cactus: {
    name: '기둥형', species: ['선인장', '유포르비아', '용신목'],
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46;
      const H = 46, arms = stage >= 3 ? [[-1, .5], [1, .42]] : (stage === 2 ? [[-1, .42]] : []);
      const body = (x, hh, sc) => `<g transform="translate(${x},0)">
        <rect x="${n1(-8 * sc)}" y="${n1(-hh)}" width="${n1(16 * sc)}" height="${n1(hh)}" rx="${n1(8 * sc)}" fill="${tone.base}"/>
        <path d="M${n1(-3 * sc)},${n1(-hh * .85)} L${n1(-3 * sc)},${n1(-hh * .15)}
                 M${n1(3 * sc)},${n1(-hh * .85)} L${n1(3 * sc)},${n1(-hh * .15)}"
              stroke="${tone.vein}" stroke-width="1.2" opacity=".45"/></g>`;
      let o = body(0, H, 1);
      arms.forEach(([dir, hs]) => {
        o += `<path d="M0,${n1(-H * .5)} Q${n1(dir * 15)},${n1(-H * .5)} ${n1(dir * 15)},${n1(-H * .55 - H * hs * .5)}"
                 stroke="${tone.base}" stroke-width="12" fill="none" stroke-linecap="round"/>`;
      });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },
  /* 양치형 — 고사리 */
  fern: {
    name: '양치형', species: ['보스턴고사리', '아디안텀', '박쥐란'],
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46;
      const F = pick([[0, 1], [-30, .9], [30, .9], [-56, .74], [56, .74], [-15, .8], [15, .8]],
                     STAGE_COUNT[stage - 1]);
      let o = '';
      F.forEach(([rot, len], i) => {
        const H = 46 * len, fill = i % 2 ? tone.alt : tone.base;
        let pin = '';
        for (let j = 1; j <= 9; j++) {
          const t = j / 10, y = -H * t, sp = 9 * Math.sin(Math.PI * t);
          pin += `<ellipse cx="${n1(-sp)}" cy="${n1(y)}" rx="${n1(sp * .55 + 1.5)}" ry="2.6" fill="${fill}"/>
                  <ellipse cx="${n1(sp)}" cy="${n1(y)}" rx="${n1(sp * .55 + 1.5)}" ry="2.6" fill="${fill}"/>`;
        }
        o += `<g transform="rotate(${rot})"><path d="M0,0 Q${n1(rot * .06)},${n1(-H * .6)} 0,${n1(-H)}"
                stroke="${tone.vein}" stroke-width="1.6" fill="none"/>${pin}</g>`;
      });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },
};

/* ------------------------------------------------------------------ */
/* 소품                                                                */
/* ------------------------------------------------------------------ */

export const PROPS = {
  none:   { name: '없음',   unlock: 'free', draw: () => '' },
  label:  { name: '이름표', unlock: 'free', draw: (w) => `
    <g transform="translate(${n1(w * .42)},${n1(-w * .1)})">
      <path d="M0,0 L0,${n1(-w * .34)}" stroke="#b9a17f" stroke-width="2"/>
      <rect x="${n1(-w * .16)}" y="${n1(-w * .52)}" width="${n1(w * .34)}" height="${n1(w * .2)}"
            rx="${n1(w * .05)}" fill="#f6f1e4" stroke="#ddd2ba"/>
    </g>` },
  stake:  { name: '지지대', unlock: 'lv3', draw: (w, rimY) => `
    <path d="M0,${n1(rimY)} L${n1(-w * .04)},${n1(rimY - w * 1.1)}" stroke="#b08d62" stroke-width="3" stroke-linecap="round"/>
    <path d="M${n1(-w * .12)},${n1(rimY - w * .5)} L${n1(w * .06)},${n1(rimY - w * .56)}"
          stroke="#c9a978" stroke-width="2" stroke-linecap="round"/>` },
  stones: { name: '자갈',   unlock: 'lv3', draw: (w, rimY) => `
    <g transform="translate(0,${n1(rimY + w * .04)})">
      ${[[-.18, 0, .07], [.02, .02, .085], [.2, -.01, .06], [-.06, -.03, .055]]
        .map(([x, y, r]) => `<ellipse cx="${n1(x * w)}" cy="${n1(y * w)}" rx="${n1(r * w)}" ry="${n1(r * w * .55)}" fill="#cfc9bd"/>`).join('')}
    </g>` },
  ribbon: { name: '리본',   unlock: 'lv5', draw: (w) => `
    <g transform="translate(0,${n1(-w * .5)})">
      <path d="M${n1(-w * .2)},0 Q0,${n1(-w * .1)} ${n1(w * .2)},0" stroke="#e0899a" stroke-width="4" fill="none"/>
      <circle cx="0" cy="${n1(-w * .04)}" r="${n1(w * .06)}" fill="#e8a1b0"/>
    </g>` },
  lights: { name: '전구줄', unlock: 'lv8', draw: (w, rimY) => `
    <g>${[-.3, -.1, .1, .3].map((x, i) => `
      <circle cx="${n1(x * w)}" cy="${n1(rimY - w * .75 + Math.abs(x) * w * .3)}" r="${n1(w * .045)}"
              fill="#ffd98a" opacity=".95"/>`).join('')}
      <path d="M${n1(-.34 * w)},${n1(rimY - w * .63)} Q0,${n1(rimY - w * .88)} ${n1(.34 * w)},${n1(rimY - w * .63)}"
            stroke="#d8cdb6" stroke-width="1.2" fill="none"/></g>` },
};

/* ------------------------------------------------------------------ */
/* 상태 오버레이 (돌봄 상태 표현)                                        */
/* ------------------------------------------------------------------ */

export const STATES = {
  healthy: { name: '건강', filter: '', tilt: 0, badge: '' },
  thirsty: { name: '목마름', filter: 'saturate(.72) brightness(1.02)', tilt: -5, badge: '💧' },
  resting: { name: '관리 종료', filter: 'grayscale(.85) opacity(.55)', tilt: 0, badge: '' },
};

/* ------------------------------------------------------------------ */
/* 아바타 조합                                                          */
/* ------------------------------------------------------------------ */

/**
 * 아바타 한 그루를 SVG 문자열로 조합합니다.
 * 앱과 카탈로그가 완전히 같은 함수를 씁니다.
 */
export function composeAvatar({
  pot = 'basic', potColor = '#c98a6a', form = 'broadleaf',
  stage = 4, tone = 'green', prop = 'none', state = 'healthy', w = 46,
} = {}) {
  const toneDef = LEAF_TONES.find(t => t.id === tone) || LEAF_TONES[0];
  const formDef = PLANT_FORMS[form] || PLANT_FORMS.broadleaf;
  const propDef = PROPS[prop] || PROPS.none;
  const st = STATES[state] || STATES.healthy;
  const rimY = potRimY(pot, w);
  const rx = w * (POTS[pot] || POTS.basic).p.rx;

  return `<g class="avatar" style="${st.filter ? `filter:${st.filter}` : ''}">
    <ellipse cx="0" cy="0" rx="${n1(rx * 1.02)}" ry="${n1(rx * 0.38)}" fill="rgba(46,60,48,.15)"/>
    <g transform="translate(0,${n1(rimY)}) rotate(${st.tilt})">${formDef.draw(w, stage, toneDef)}</g>
    ${drawPot(pot, w, potColor)}
    ${propDef.draw(w, rimY)}
  </g>`;
}

/** SVG 문서로 감싸기 (PNG 내보내기·미리보기용) */
export function toSVGDoc(inner, w, h, pad = 6) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"
    viewBox="${-w / 2} ${-h + pad} ${w} ${h}">${inner}</svg>`;
}

/* ------------------------------------------------------------------ */
/* 매니페스트 — Flutter가 읽는 계약서                                   */
/* ------------------------------------------------------------------ */

export function buildManifest() {
  return {
    version: VERSION,
    grid: GRID,
    stages: { count: 4, scale: STAGE_SCALE, labels: ['새싹', '어린잎', '무성', '만개'] },
    potColors: POT_COLORS,
    leafTones: LEAF_TONES.map(({ id, name, base, alt, vein }) => ({ id, name, base, alt, vein })),
    pots: Object.entries(POTS).map(([id, d]) => ({
      id, name: d.name, unlock: d.unlock,
      rimY: -d.p.h,           // 흙 표면 (기준 폭 대비 비율)
      topR: d.p.rx, baseR: d.p.br,
    })),
    forms: Object.entries(PLANT_FORMS).map(([id, d]) => ({
      id, name: d.name, species: d.species,
    })),
    props: Object.entries(PROPS).map(([id, d]) => ({ id, name: d.name, unlock: d.unlock })),
    states: Object.entries(STATES).map(([id, d]) => ({ id, name: d.name })),
    counts: {
      pots: Object.keys(POTS).length,
      potColors: POT_COLORS.length,
      forms: Object.keys(PLANT_FORMS).length,
      props: Object.keys(PROPS).length,
      combinations:
        Object.keys(POTS).length * POT_COLORS.length *
        Object.keys(PLANT_FORMS).length * 4 * Object.keys(PROPS).length,
    },
  };
}
