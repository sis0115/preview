/**
 * 정원 파츠 v2 — 아트 레이어 시제품
 *
 * v1(parts.mjs)과 **계약은 같고 그림만 다릅니다.**
 *   저장 데이터  {form, stage, pot, potColor, tone, prop, state}   동일
 *   좌표 규약    원점 = 지면 접점, 위가 y 음수                      동일
 *   격자         GRID {tileW, tileH, zH}                            동일
 *
 * v1과 달라진 것 (레퍼런스 온실 일러스트에서 추출한 규칙):
 *   1) 잎 실루엣이 6종 — 형태마다 자기 잎을 씁니다 (v1은 물방울 1종 파생)
 *   2) 잎을 절차적으로 12~25장 생성 — 뒤 레이어(어두움) → 앞 레이어(밝음) 2패스
 *   3) 좌상단 고정 광원 — 잎의 회전각으로 밝기를 정합니다 (그라디언트 없이 평면 2톤)
 *   4) 팔레트 채도 상향 — 레퍼런스의 연두(#84c054대)와 어두운 초록(#243024대) 대비
 *   5) 결정론적 지터 — 같은 식물은 언제 그려도 같은 모양
 *
 * 그라디언트를 쓰지 않는 이유: Flutter CustomPainter로 그대로 옮기기 위해서입니다.
 * 평면 채움 + 하이라이트 도형 + 그늘진 가장자리만으로 입체를 만듭니다.
 */

export const VERSION = 2;
export const GRID = { tileW: 78, tileH: 39, zH: 44 };

/* ------------------------------------------------------------------ */
/* 색                                                                   */
/* ------------------------------------------------------------------ */

const hex2rgb = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
const rgb2hex = c => '#' + c.map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('');

export function shade(hex, amt) {
  return rgb2hex(hex2rgb(hex).map(v => v + amt));
}
/** 두 색을 t(0~1)로 섞습니다 — 광원 계산에 씁니다 */
export function mix(a, b, t) {
  const A = hex2rgb(a), B = hex2rgb(b);
  return rgb2hex([0, 1, 2].map(i => A[i] + (B[i] - A[i]) * t));
}
const n1 = v => Math.round(v * 100) / 100;

/** 잎 색조 — v1의 {base, alt, vein} → v2는 {hi, base, shadow, vein} 4값 */
export const LEAF_TONES = [
  { id: 'green',      name: '기본 초록', hi: '#8fc95c', base: '#5da346', shadow: '#357a3e', vein: '#2a5c33' },
  { id: 'deep',       name: '진초록',    hi: '#5f9f52', base: '#3d7f42', shadow: '#265c33', vein: '#1d4527' },
  { id: 'light',      name: '연초록',    hi: '#aed873', base: '#7bbc57', shadow: '#4f9350', vein: '#3a6f3d' },
  { id: 'variegated', name: '무늬종',    hi: '#c9e3a8', base: '#6faf55', shadow: '#3f8244', vein: '#2f6238', mark: '#eaf3d4' },
  { id: 'silver',     name: '실버',      hi: '#b8d2ba', base: '#7ea587', shadow: '#57806a', vein: '#456851' },
];

/** 화분 색 — 레퍼런스 테라코타 대역(#cc9c60~#d8a86c)으로 재조정 */
export const POT_COLORS = [
  { id: 'terracotta', name: '테라코타', hex: '#d2915f', unlock: 'free' },
  { id: 'sage',       name: '세이지',   hex: '#93ac9c', unlock: 'free' },
  { id: 'sand',       name: '샌드',     hex: '#ddc79e', unlock: 'free' },
  { id: 'clay',       name: '클레이',   hex: '#b0764f', unlock: 'free' },
  { id: 'lilac',      name: '라일락',   hex: '#b7a3c9', unlock: 'lv3' },
  { id: 'coral',      name: '코랄',     hex: '#e39c85', unlock: 'lv3' },
  { id: 'sky',        name: '스카이',   hex: '#9fb8d0', unlock: 'lv5' },
  { id: 'charcoal',   name: '차콜',     hex: '#6b7169', unlock: 'lv8' },
];

/* ------------------------------------------------------------------ */
/* 광원 · 난수                                                          */
/* ------------------------------------------------------------------ */

/**
 * 좌상단 고정 광원. 잎이 왼쪽으로 기울수록 빛을 받고, 오른쪽으로 기울수록 그늘집니다.
 * rot: 잎의 회전각(도). 0 = 위를 향함.
 * 반환 0(그늘) ~ 1(하이라이트)
 */
export const LIGHT_DIR = -40;
function litness(rot) {
  const d = ((rot - LIGHT_DIR) % 360 + 540) % 360 - 180;   // -180..180
  return 0.5 + 0.5 * Math.cos(d * Math.PI / 180);
}
/** 잎 한 장의 채움색 — 광원 + 레이어 깊이(뒤쪽일수록 어둡게) */
function leafFill(tone, rot, depth = 0) {
  const t = litness(rot);
  const c = t < .5 ? mix(tone.shadow, tone.base, t * 2) : mix(tone.base, tone.hi, (t - .5) * 2);
  return depth ? mix(c, tone.shadow, 0.45 * depth) : c;
}

/** mulberry32 — 식물마다 고정된 지터를 만들기 위한 결정론적 난수 */
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const seedOf = (form, stage) => {
  let h = 2166136261;
  for (const ch of form + '#' + stage) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return h >>> 0;
};

/* ------------------------------------------------------------------ */
/* 잎 실루엣 6종                                                        */
/* ------------------------------------------------------------------ */

/**
 * 각 잎은 밑동 (0,0) → 끝 (0,-L), 최대폭 W 인 로컬 좌표로 그립니다.
 * 반환: { body, high } — 몸통 path와 빛 받는 쪽 하이라이트 path
 */
const LEAF_SHAPES = {
  /* 넓은 타원 — 고무나무·칼라데아 */
  ovate: (L, W) => ({
    body: `M0,0 C${n1(-W * .58)},${n1(-L * .16)} ${n1(-W * .64)},${n1(-L * .7)} 0,${-L}
           C${n1(W * .64)},${n1(-L * .7)} ${n1(W * .58)},${n1(-L * .16)} 0,0 Z`,
    high: `M0,${n1(-L * .06)} C${n1(-W * .44)},${n1(-L * .2)} ${n1(-W * .48)},${n1(-L * .66)} ${n1(-W * .05)},${n1(-L * .93)}
           C${n1(-W * .16)},${n1(-L * .6)} ${n1(-W * .18)},${n1(-L * .28)} 0,${n1(-L * .06)} Z`,
  }),
  /* 하트 — 몬스테라·필로덴드론 */
  cordate: (L, W) => ({
    body: `M0,${n1(-L * .04)} C${n1(-W * .52)},${n1(-L * .02)} ${n1(-W * .8)},${n1(-L * .38)} ${n1(-W * .4)},${n1(-L * .82)}
           C${n1(-W * .24)},${n1(-L * .99)} ${n1(W * .24)},${n1(-L * .99)} ${n1(W * .4)},${n1(-L * .82)}
           C${n1(W * .8)},${n1(-L * .38)} ${n1(W * .52)},${n1(-L * .02)} 0,${n1(-L * .04)} Z`,
    high: `M0,${n1(-L * .1)} C${n1(-W * .4)},${n1(-L * .14)} ${n1(-W * .58)},${n1(-L * .44)} ${n1(-W * .26)},${n1(-L * .8)}
           C${n1(-W * .2)},${n1(-L * .52)} ${n1(-W * .14)},${n1(-L * .3)} 0,${n1(-L * .1)} Z`,
  }),
  /* 창 — 산세베리아·야자 소엽 */
  lanceolate: (L, W) => ({
    body: `M0,0 C${n1(-W * .46)},${n1(-L * .32)} ${n1(-W * .3)},${n1(-L * .78)} 0,${-L}
           C${n1(W * .3)},${n1(-L * .78)} ${n1(W * .46)},${n1(-L * .32)} 0,0 Z`,
    high: `M0,${n1(-L * .08)} C${n1(-W * .3)},${n1(-L * .36)} ${n1(-W * .2)},${n1(-L * .74)} ${n1(-W * .03)},${n1(-L * .94)}
           C${n1(-W * .08)},${n1(-L * .6)} ${n1(-W * .1)},${n1(-L * .3)} 0,${n1(-L * .08)} Z`,
  }),
  /* 둥근 — 포토스·필레아 */
  round: (L, W) => ({
    body: `M0,0 C${n1(-W * .78)},${n1(-L * .06)} ${n1(-W * .82)},${n1(-L * .86)} 0,${-L}
           C${n1(W * .82)},${n1(-L * .86)} ${n1(W * .78)},${n1(-L * .06)} 0,0 Z`,
    high: `M0,${n1(-L * .1)} C${n1(-W * .56)},${n1(-L * .16)} ${n1(-W * .58)},${n1(-L * .74)} ${n1(-W * .06)},${n1(-L * .9)}
           C${n1(-W * .24)},${n1(-L * .6)} ${n1(-W * .26)},${n1(-L * .3)} 0,${n1(-L * .1)} Z`,
  }),
  /* 갈래 — 레퍼런스의 제라늄·단풍형 관목 잎 */
  palmate: (L, W) => {
    let d = '';
    for (let i = -2; i <= 2; i++) {
      const a = i * 30 * Math.PI / 180;
      const len = L * (1 - Math.abs(i) * 0.2), wid = W * 0.24;
      const tx = Math.sin(a) * len, ty = -Math.cos(a) * len;
      d += `M0,${n1(-L * .08)} C${n1(tx * .3 - Math.cos(a) * wid)},${n1(ty * .4 + Math.sin(a) * wid)}
            ${n1(tx * .8 - Math.cos(a) * wid)},${n1(ty * .8 + Math.sin(a) * wid)} ${n1(tx)},${n1(ty)}
            C${n1(tx * .8 + Math.cos(a) * wid)},${n1(ty * .8 - Math.sin(a) * wid)}
            ${n1(tx * .3 + Math.cos(a) * wid)},${n1(ty * .4 - Math.sin(a) * wid)} 0,${n1(-L * .08)} Z`;
    }
    return { body: d, high: `M0,${n1(-L * .08)} C${n1(-W * .34)},${n1(-L * .3)} ${n1(-W * .4)},${n1(-L * .6)} ${n1(-W * .3)},${n1(-L * .78)}
           C${n1(-W * .1)},${n1(-L * .5)} ${n1(-W * .06)},${n1(-L * .26)} 0,${n1(-L * .08)} Z` };
  },
  /* 톱니 — 고사리 소엽·허브 */
  serrate: (L, W) => {
    const N = 6;
    let left = '', right = '';
    for (let i = N; i >= 1; i--) {
      const t = i / (N + 1), y = -L * t, sp = W * .5 * Math.sin(Math.PI * t) + W * .06;
      left += `L${n1(-sp)},${n1(y + L * .05)} L${n1(-sp * .55)},${n1(y)} `;
    }
    for (let i = 1; i <= N; i++) {
      const t = i / (N + 1), y = -L * t, sp = W * .5 * Math.sin(Math.PI * t) + W * .06;
      right += `L${n1(sp * .55)},${n1(y)} L${n1(sp)},${n1(y + L * .05)} `;
    }
    return {
      body: `M0,0 ${left}L0,${-L} ${right.split(' ').reverse().join(' ')}Z`
        .replace(/L0,-\d/, m => m),   // 좌→끝→우 순서 유지
      high: `M0,${n1(-L * .1)} C${n1(-W * .3)},${n1(-L * .35)} ${n1(-W * .22)},${n1(-L * .72)} 0,${n1(-L * .9)} Z`,
    };
  },
};

/**
 * 잎 한 장.
 * x,y  밑동 위치 / rot 회전(도) / s 스케일 / kind 실루엣 / tone 색조 / depth 0=앞 1=뒤
 */
function leaf(x, y, rot, s, kind, tone, depth = 0, opts = {}) {
  const L = (opts.len ?? 34) * s, W = (opts.wid ?? 19) * s;
  const sh = LEAF_SHAPES[kind](L, W);
  const fill = leafFill(tone, rot, depth);
  const veinOp = depth ? .18 : .34;
  const mark = tone.mark && opts.variegate
    ? `<ellipse cx="0" cy="${n1(-L * .52)}" rx="${n1(W * .2)}" ry="${n1(L * .3)}" fill="${tone.mark}" opacity=".55"/>` : '';
  return `<g transform="translate(${n1(x)},${n1(y)}) rotate(${n1(rot)})">
    <path d="${sh.body}" fill="${fill}"/>
    ${mark}
    <path d="${sh.high}" fill="#ffffff" opacity="${depth ? .05 : .16}"/>
    <path d="M0,${n1(-L * .05)} L0,${n1(-L * .88)}" stroke="${tone.vein}" stroke-width="${n1(1.1 * s)}" opacity="${veinOp}"/>
    <path d="${sh.body}" fill="none" stroke="${tone.vein}" stroke-width="${n1(.9 * s)}" opacity="${depth ? .1 : .2}"/>
  </g>`;
}

/** 줄기 — 밑동에서 잎 밑동까지 휘어 올라갑니다 */
const stem = (x, y, tone, w = 2.2) =>
  `<path d="M0,3 Q${n1(x * .22)},${n1(y * .5)} ${n1(x)},${n1(y)}"
     stroke="${mix(tone.vein, tone.base, .35)}" stroke-width="${n1(w)}" fill="none" stroke-linecap="round"/>`;

/* ------------------------------------------------------------------ */
/* 식물 형태 9종                                                        */
/* ------------------------------------------------------------------ */

const STAGE_SCALE = [0.52, 0.72, 0.9, 1.0];
/** 단계별 잎 수 배율 — v1보다 총량을 2~3배로 올렸습니다 */
const STAGE_LEAVES = [0.3, 0.55, 0.8, 1.0];

/** 부채꼴로 잎 밑동을 배치 — 뒤 레이어는 조금 더 높고 작게 */
function fan({ n, spread, len, lenVar, rise, riseVar, r, depth }) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const t = n === 1 ? .5 : i / (n - 1);
    const rot = -spread / 2 + spread * t + (r() - .5) * 10;
    const s = len + (r() - .5) * lenVar;
    out.push({
      rot,
      s: depth ? s * .86 : s,
      x: Math.sin(rot * Math.PI / 180) * 3,
      y: -(rise + (r() - .5) * riseVar) - (depth ? 3 : 0),
      depth,
    });
  }
  return out;
}

export const PLANT_FORMS = {
  /* 대엽형 — 몬스테라·고무나무. 하트잎이 사방으로 벌어집니다 */
  broadleaf: {
    name: '대엽형', species: ['몬스테라', '필로덴드론', '알로카시아', '고무나무'], leaf: 'cordate',
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46, r = rng(seedOf('broadleaf', stage));
      const n = Math.max(2, Math.round(8 * STAGE_LEAVES[stage - 1]));
      // 잎자루를 길게 뽑고 끝에 잎을 답니다 — 레퍼런스의 몬스테라처럼 잎 사이에 공간이 생깁니다
      const back = fan({ n: Math.max(1, n - 2), spread: 118, len: .88, lenVar: .2, rise: 44, riseVar: 16, r, depth: 1 });
      const front = fan({ n, spread: 152, len: 1.0, lenVar: .28, rise: 32, riseVar: 22, r, depth: 0 });
      const stalk = L => {
        const a = L.rot * Math.PI / 180;
        return { x: Math.sin(a) * -L.y * .55, y: L.y };
      };
      let o = '';
      [...back, ...front].forEach(L => { const t = stalk(L); o += stem(t.x, t.y, tone, 2.6 * L.s); });
      back.forEach(L => { const t = stalk(L); o += leaf(t.x, t.y, L.rot, L.s, 'cordate', tone, 1, { len: 36, wid: 19 }); });
      front.forEach(L => { const t = stalk(L); o += leaf(t.x, t.y, L.rot, L.s, 'cordate', tone, 0, { len: 38, wid: 20 }); });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },

  /* 직립형 — 산세베리아. 곧은 창잎 다발 + 노란 테두리 */
  upright: {
    name: '직립형', species: ['산세베리아', '스투키', '금전수'], leaf: 'lanceolate',
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46, r = rng(seedOf('upright', stage));
      const n = Math.max(3, Math.round(11 * STAGE_LEAVES[stage - 1]));
      const back = fan({ n: Math.max(2, n - 4), spread: 34, len: .92, lenVar: .18, rise: 2, riseVar: 2, r, depth: 1 });
      const front = fan({ n, spread: 52, len: 1.05, lenVar: .22, rise: 0, riseVar: 3, r, depth: 0 });
      let o = '';
      const blade = (L, d) => leaf(L.x, L.y, L.rot, L.s, 'lanceolate', tone, d, { len: 60, wid: 13 })
        + `<g transform="translate(${n1(L.x)},${n1(L.y)}) rotate(${n1(L.rot)})">
             <path d="M0,0 C${n1(-6 * L.s)},${n1(-19 * L.s)} ${n1(-4 * L.s)},${n1(-47 * L.s)} 0,${n1(-60 * L.s)}"
               stroke="#cdbc63" stroke-width="${n1(1.2 * L.s)}" fill="none" opacity="${d ? .3 : .6}"/></g>`;
      back.forEach(L => { o += blade(L, 1); });
      front.forEach(L => { o += blade(L, 0); });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },

  /* 로제트형 — 다육. 바깥에서 안으로 3겹 */
  rosette: {
    name: '로제트형', species: ['다육식물', '에케베리아', '하월시아'], leaf: 'ovate',
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46;
      const g = STAGE_LEAVES[stage - 1];
      const rings = [
        { n: Math.round(12 * g) + 5, len: 30, sc: 1.0, depth: 1 },
        { n: Math.round(9 * g) + 4, len: 21, sc: .82, depth: 0 },
        { n: Math.round(6 * g) + 3, len: 13, sc: .62, depth: 0 },
      ];
      let o = '';
      rings.forEach((ring, ri) => {
        for (let i = 0; i < ring.n; i++) {
          const a = i * 360 / ring.n + ri * 17;
          // 위에서 내려다보는 형태라 잎을 눕혀(세로 압축) 방사 배치합니다
          o += `<g transform="rotate(${n1(a)}) scale(1,0.66)">
            ${leaf(0, 0, 0, ring.sc, 'ovate', tone, ring.depth, { len: ring.len, wid: 15 })}</g>`;
        }
      });
      return `<g transform="translate(0,-4) scale(${n1(k * s)})">${o}
        <circle r="3.4" fill="${mix(tone.hi, '#ffffff', .3)}" opacity=".7"/></g>`;
    }
  },

  /* 무늬엽형 — 칼라데아. 잎 가운데 크림색 무늬 */
  patterned: {
    name: '무늬엽형', species: ['칼라데아', '마란타', '스킨답서스'], leaf: 'ovate',
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46, r = rng(seedOf('patterned', stage));
      const n = Math.max(2, Math.round(10 * STAGE_LEAVES[stage - 1]));
      const t2 = { ...tone, mark: tone.mark || '#dfeccb' };
      const back = fan({ n: Math.max(1, n - 3), spread: 96, len: .9, lenVar: .16, rise: 22, riseVar: 6, r, depth: 1 });
      const front = fan({ n, spread: 124, len: 1.02, lenVar: .22, rise: 14, riseVar: 8, r, depth: 0 });
      let o = '';
      const stalk = L => ({ x: Math.sin(L.rot * Math.PI / 180) * -L.y * .5, y: L.y });
      [...back, ...front].forEach(L => { const t = stalk(L); o += stem(t.x, t.y, tone, 2.1 * L.s); });
      back.forEach(L => { const t = stalk(L); o += leaf(t.x, t.y, L.rot, L.s, 'ovate', t2, 1, { len: 34, wid: 18, variegate: true }); });
      front.forEach(L => { const t = stalk(L); o += leaf(t.x, t.y, L.rot, L.s, 'ovate', t2, 0, { len: 36, wid: 19, variegate: true }); });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },

  /* 덩굴형 — 포토스. 화분 밖으로 늘어지는 줄기 2~3가닥 */
  vine: {
    name: '덩굴형', species: ['포토스', '아이비', '스킨답서스', '립살리스'], leaf: 'round',
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46, r = rng(seedOf('vine', stage));
      // 줄기는 흙에서 살짝 솟았다가 화분 밖으로 넘어가 아래로 늘어집니다.
      // 제어점 ey는 위(음수), 끝점 ty는 화분 옆면 아래(양수)라 실제로 드리워집니다.
      const strands = [
        { dir: -1, out: 34, up: 20, down: 40, depth: 1 },
        { dir: 1, out: 32, up: 16, down: 34, depth: 0 },
        { dir: -1, out: 20, up: 24, down: 18, depth: 0 },
        { dir: 1, out: 18, up: 22, down: 12, depth: 1 },
      ].slice(0, Math.max(1, Math.round(4 * STAGE_LEAVES[stage - 1])));
      const per = Math.max(2, Math.round(4 * STAGE_LEAVES[stage - 1]) + 2);
      const g = STAGE_LEAVES[stage - 1];
      let o = '';
      strands.forEach(st => {
        const cx = st.dir * st.out * .55, cy = -st.up;
        const ex = st.dir * st.out * (.7 + .4 * g), ey = st.down * g;
        const at = t => [2 * (1 - t) * t * cx + t * t * ex, 2 * (1 - t) * t * cy + t * t * ey];
        o += `<path d="M0,2 Q${n1(cx)},${n1(cy)} ${n1(ex)},${n1(ey)}"
                stroke="${mix(tone.vein, tone.base, .4)}" stroke-width="1.8" fill="none" stroke-linecap="round"/>`;
        for (let i = 1; i <= per; i++) {
          const t = .18 + .82 * (i / per), [px, py] = at(t);
          // 잎을 줄기 좌우로 번갈아 달고, 끝으로 갈수록 아래를 향하게 합니다
          const side = i % 2 ? 1 : -1;
          const rot = st.dir * (46 + t * 96) + side * 26 + (r() - .5) * 14;
          const a = rot * Math.PI / 180;
          o += leaf(px + Math.sin(a) * 2, py - Math.cos(a) * 2, rot,
            (.98 - t * .3), 'round', tone, st.depth, { len: 18, wid: 17 });
        }
      });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },

  /* 깃꼴형 — 야자. 중앙맥에 창 모양 소엽이 양쪽으로 */
  palm: {
    name: '깃꼴형', species: ['테이블야자', '아레카야자', '켄차야자'], leaf: 'lanceolate',
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46, r = rng(seedOf('palm', stage));
      const n = Math.max(2, Math.round(7 * STAGE_LEAVES[stage - 1]));
      const fronds = fan({ n, spread: 116, len: 1, lenVar: .2, rise: 0, riseVar: 0, r, depth: 0 });
      let o = '';
      fronds.forEach((F, fi) => {
        const depth = fi % 3 === 0 ? 1 : 0;
        const H = 56 * F.s, pin = 7;
        let leaves = '';
        for (let j = 1; j <= pin; j++) {
          const t = j / (pin + 1), y = -H * t;
          const sc = Math.sin(Math.PI * t) * .82 * F.s + .18;
          leaves += leaf(0, y, -62 + F.rot * .1, sc, 'lanceolate', tone, depth, { len: 26, wid: 8 });
          leaves += leaf(0, y, 62 + F.rot * .1, sc, 'lanceolate', tone, depth, { len: 26, wid: 8 });
        }
        o += `<g transform="rotate(${n1(F.rot)})">
          <path d="M0,4 Q${n1(F.rot * .1)},${n1(-H * .6)} 0,${n1(-H)}"
            stroke="${mix(tone.vein, tone.base, .3)}" stroke-width="${n1(2.1)}" fill="none"/>${leaves}</g>`;
      });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },

  /* 기둥형 — 선인장. 세로 능선 + 가시 */
  cactus: {
    name: '기둥형', species: ['선인장', '유포르비아', '용신목'], leaf: 'lanceolate',
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46, H = 56;
      const arms = stage >= 3 ? [[-1, .5], [1, .42]] : (stage === 2 ? [[-1, .42]] : []);
      const lit = mix(tone.base, tone.hi, .55), dim = mix(tone.base, tone.shadow, .5);
      const spines = (x, hh, sc) => {
        let sp = '';
        for (let j = 1; j <= 6; j++) {
          const y = -hh * (j / 7);
          sp += `<path d="M${n1(x - 7.6 * sc)},${n1(y)} l${n1(-2.4 * sc)},${n1(-1.3 * sc)}
                   M${n1(x + 7.6 * sc)},${n1(y)} l${n1(2.4 * sc)},${n1(-1.3 * sc)}"
                 stroke="#e8e0c2" stroke-width="${n1(.8 * sc)}" opacity=".8" stroke-linecap="round"/>`;
        }
        return sp;
      };
      const BW = 12;   // 몸통 반폭
      let o = '';
      arms.forEach(([d, hs]) => {
        o += `<path d="M0,${n1(-H * .46)} Q${n1(d * 20)},${n1(-H * .46)} ${n1(d * 20)},${n1(-H * .5 - H * hs * .5)}"
          stroke="${d < 0 ? lit : dim}" stroke-width="14" fill="none" stroke-linecap="round"/>`;
      });
      o += `<rect x="${-BW}" y="${-H}" width="${BW * 2}" height="${H + 4}" rx="${BW}" fill="${tone.base}"/>
        <rect x="${-BW}" y="${-H}" width="8" height="${H + 4}" rx="4" fill="${lit}"/>
        <rect x="${BW - 7}" y="${-H}" width="7" height="${H + 4}" rx="3.5" fill="${dim}" opacity=".7"/>
        <path d="M-3.2,${n1(-H * .9)} L-3.2,${n1(-H * .08)} M3.2,${n1(-H * .9)} L3.2,${n1(-H * .08)}"
          stroke="${tone.vein}" stroke-width="1.1" opacity=".35"/>${spines(0, H, 1.5)}`;
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },

  /* 양치형 — 고사리. 휘는 잎줄기에 톱니 소엽 */
  fern: {
    name: '양치형', species: ['보스턴고사리', '아디안텀', '박쥐란'], leaf: 'serrate',
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46, r = rng(seedOf('fern', stage));
      const n = Math.max(3, Math.round(9 * STAGE_LEAVES[stage - 1]));
      const fronds = fan({ n, spread: 150, len: 1, lenVar: .26, rise: 0, riseVar: 0, r, depth: 0 });
      let o = '';
      fronds.forEach((F, fi) => {
        const depth = fi % 2 ? 1 : 0, H = 48 * F.s, bend = F.rot * .28, pin = 8;
        let leaves = '';
        for (let j = 1; j <= pin; j++) {
          const t = j / (pin + 1), y = -H * t, x = bend * t * t * .5;
          const sc = Math.sin(Math.PI * t) * .78 * F.s + .16;
          leaves += leaf(x, y, -70, sc, 'serrate', tone, depth, { len: 18, wid: 11 });
          leaves += leaf(x, y, 70, sc, 'serrate', tone, depth, { len: 18, wid: 11 });
        }
        o += `<g transform="rotate(${n1(F.rot)})">
          <path d="M0,4 Q${n1(bend * .4)},${n1(-H * .6)} ${n1(bend * .5)},${n1(-H)}"
            stroke="${mix(tone.vein, tone.base, .3)}" stroke-width="1.7" fill="none"/>${leaves}</g>`;
      });
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },

  /* 꽃나무 — 레퍼런스 바깥 마당의 관목. 갈래잎 + 3단계부터 개화 */
  flower: {
    name: '꽃나무', species: ['제라늄', '수국', '동백'], leaf: 'palmate', petal: '#e8899e',
    draw(w, stage, tone) {
      const s = STAGE_SCALE[stage - 1], k = w / 46, r = rng(seedOf('flower', stage));
      const n = Math.max(2, Math.round(8 * STAGE_LEAVES[stage - 1]));
      const back = fan({ n: Math.max(1, n - 2), spread: 110, len: .88, lenVar: .18, rise: 26, riseVar: 8, r, depth: 1 });
      const front = fan({ n, spread: 140, len: 1, lenVar: .24, rise: 18, riseVar: 10, r, depth: 0 });
      let o = '';
      [...back, ...front].forEach(L => { o += stem(L.x, L.y, tone, 2 * L.s); });
      back.forEach(L => { o += leaf(L.x, L.y, L.rot, L.s, 'palmate', tone, 1, { len: 32, wid: 30 }); });
      front.forEach(L => { o += leaf(L.x, L.y, L.rot, L.s, 'palmate', tone, 0, { len: 34, wid: 32 }); });
      if (stage >= 3) {
        front.filter((_, i) => i % 2 === 0).forEach(L => {
          const bx = L.x + Math.sin(L.rot * Math.PI / 180) * 24 * L.s;
          const by = L.y - Math.cos(L.rot * Math.PI / 180) * 24 * L.s;
          o += `<g transform="translate(${n1(bx)},${n1(by)})">
            ${[0, 72, 144, 216, 288].map(a =>
            `<ellipse cx="0" cy="-4.6" rx="3.1" ry="4.8" fill="${a < 180 ? this.petal : shade(this.petal, -18)}" transform="rotate(${a})"/>`).join('')}
            <circle r="2.3" fill="#f6d96b"/></g>`;
        });
      }
      return `<g transform="scale(${n1(k * s)})">${o}</g>`;
    }
  },
};

/* ------------------------------------------------------------------ */
/* 화분 — 림 두께 · 안쪽 그늘 · 흙 알갱이                                */
/* ------------------------------------------------------------------ */

export const POTS = {
  basic:   { name: '기본 화분',   unlock: 'free', p: { rx: .50, ry: .22, h: .74, br: .335 } },
  bowl:    { name: '낮은 볼',     unlock: 'free', p: { rx: .55, ry: .24, h: .44, br: .40 } },
  tall:    { name: '긴 화분',     unlock: 'free', p: { rx: .42, ry: .19, h: 1.02, br: .32 } },
  urn:     { name: '항아리',      unlock: 'lv3',  p: { rx: .40, ry: .18, h: .82, br: .30, bulge: .34 } },
  rimmed:  { name: '테두리 화분', unlock: 'lv5',  p: { rx: .48, ry: .21, h: .70, br: .34, rim: .07 } },
  tapered: { name: '콘 화분',     unlock: 'lv8',  p: { rx: .52, ry: .23, h: .82, br: .22, bulge: -.16 } },
};

export function drawPot(potId, w, color) {
  const { rx, ry, h, br, bulge = 0, rim = 0 } = (POTS[potId] || POTS.basic).p;
  const RX = w * rx, RY = w * ry, H = w * h, BR = w * br, cx = RX + bulge * RX;
  const lit = shade(color, 26), dim = shade(color, -34), rimC = shade(color, 16);
  const soil = '#5a4530', soilLit = '#6f5740';
  return `<g class="pot">
    <path d="M${n1(-RX)},${n1(-H)} Q${n1(-cx)},${n1(-H * .45)} ${n1(-BR)},-3 Q${n1(-BR)},0 ${n1(-BR + 4)},0
             L${n1(BR - 4)},0 Q${n1(BR)},0 ${n1(BR)},-3 Q${n1(cx)},${n1(-H * .45)} ${n1(RX)},${n1(-H)} Z" fill="${color}"/>
    <path d="M${n1(-RX)},${n1(-H)} Q${n1(-cx)},${n1(-H * .45)} ${n1(-BR)},-3 L${n1(-BR * .1)},0 L${n1(-RX * .16)},${n1(-H)} Z"
          fill="${lit}" opacity=".5"/>
    <path d="M${n1(RX)},${n1(-H)} Q${n1(cx)},${n1(-H * .45)} ${n1(BR)},-3 L${n1(BR * .3)},0 L${n1(RX * .42)},${n1(-H)} Z"
          fill="${dim}" opacity=".42"/>
    <ellipse cx="0" cy="0" rx="${n1(BR)}" ry="${n1(BR * .33)}" fill="${dim}"/>
    ${rim ? `<path d="M${n1(-RX * 1.09)},${n1(-H)} L${n1(RX * 1.09)},${n1(-H)} L${n1(RX)},${n1(-H + rim * w)} L${n1(-RX)},${n1(-H + rim * w)} Z" fill="${rimC}"/>` : ''}
    <ellipse cx="0" cy="${n1(-H)}" rx="${n1(RX)}" ry="${n1(RY)}" fill="${shade(color, -12)}"/>
    <ellipse cx="0" cy="${n1(-H + RY * .16)}" rx="${n1(RX * .82)}" ry="${n1(RY * .76)}" fill="${soil}"/>
    <ellipse cx="${n1(-RX * .22)}" cy="${n1(-H + RY * .02)}" rx="${n1(RX * .34)}" ry="${n1(RY * .3)}" fill="${soilLit}" opacity=".55"/>
    ${[[-.42, .1, .07], [.1, -.16, .085], [.44, .06, .06], [-.1, .2, .055], [.3, .26, .05]]
      .map(([x, y, r]) => `<ellipse cx="${n1(x * RX)}" cy="${n1(-H + RY * .16 + y * RY)}" rx="${n1(r * RX)}" ry="${n1(r * RX * .5)}" fill="#7d6549" opacity=".5"/>`).join('')}
    <path d="M${n1(-RX * .93)},${n1(-H + RY * .26)} A${n1(RX * .93)},${n1(RY * .9)} 0 0 0 ${n1(RX * .93)},${n1(-H + RY * .26)}"
          fill="none" stroke="rgba(0,0,0,.16)" stroke-width="1.6"/>
  </g>`;
}

/**
 * 화분 앞쪽 림 — 식물을 그린 **뒤에** 덧그립니다.
 * 이래야 줄기 밑동이 흙에 묻혀 보이고, 덩굴은 림 위로 늘어질 수 있습니다.
 */
export function potFront(potId, w, color) {
  const { rx, ry, h } = (POTS[potId] || POTS.basic).p;
  const RX = w * rx, RY = w * ry, H = w * h;
  return `<path d="M${n1(-RX)},${n1(-H)} A${n1(RX)},${n1(RY)} 0 0 0 ${n1(RX)},${n1(-H)}"
    fill="none" stroke="${shade(color, 30)}" stroke-width="${n1(RY * .8)}"/>`;
}

export const potRimY = (potId, w) => -w * (POTS[potId] || POTS.basic).p.h;

/* ------------------------------------------------------------------ */
/* 소품 · 상태 — v1과 동일 계약                                          */
/* ------------------------------------------------------------------ */

export const PROPS = {
  none:   { name: '없음',   unlock: 'free', draw: () => '' },
  label:  { name: '이름표', unlock: 'free', draw: (w) => `
    <g transform="translate(${n1(w * .42)},${n1(-w * .1)})">
      <path d="M0,0 L0,${n1(-w * .34)}" stroke="#b9a17f" stroke-width="2"/>
      <rect x="${n1(-w * .16)}" y="${n1(-w * .52)}" width="${n1(w * .34)}" height="${n1(w * .2)}"
            rx="${n1(w * .05)}" fill="#f6f1e4" stroke="#ddd2ba"/></g>` },
  stake:  { name: '지지대', unlock: 'lv3', draw: (w, rimY) => `
    <path d="M0,${n1(rimY)} L${n1(-w * .04)},${n1(rimY - w * 1.1)}" stroke="#b08d62" stroke-width="3" stroke-linecap="round"/>
    <path d="M${n1(-w * .12)},${n1(rimY - w * .5)} L${n1(w * .06)},${n1(rimY - w * .56)}"
          stroke="#c9a978" stroke-width="2" stroke-linecap="round"/>` },
  stones: { name: '자갈',   unlock: 'lv3', draw: (w, rimY) => `
    <g transform="translate(0,${n1(rimY + w * .04)})">
      ${[[-.18, 0, .07], [.02, .02, .085], [.2, -.01, .06], [-.06, -.03, .055]]
      .map(([x, y, r]) => `<ellipse cx="${n1(x * w)}" cy="${n1(y * w)}" rx="${n1(r * w)}" ry="${n1(r * w * .55)}" fill="#cfc9bd"/>`).join('')}</g>` },
  ribbon: { name: '리본',   unlock: 'lv5', draw: (w) => `
    <g transform="translate(0,${n1(-w * .5)})">
      <path d="M${n1(-w * .2)},0 Q0,${n1(-w * .1)} ${n1(w * .2)},0" stroke="#e0899a" stroke-width="4" fill="none"/>
      <circle cx="0" cy="${n1(-w * .04)}" r="${n1(w * .06)}" fill="#e8a1b0"/></g>` },
  lights: { name: '전구줄', unlock: 'lv8', draw: (w, rimY) => `
    <g>${[-.3, -.1, .1, .3].map(x => `
      <circle cx="${n1(x * w)}" cy="${n1(rimY - w * .75 + Math.abs(x) * w * .3)}" r="${n1(w * .045)}" fill="#ffd98a"/>`).join('')}
      <path d="M${n1(-.34 * w)},${n1(rimY - w * .63)} Q0,${n1(rimY - w * .88)} ${n1(.34 * w)},${n1(rimY - w * .63)}"
            stroke="#d8cdb6" stroke-width="1.2" fill="none"/></g>` },
};

export const STATES = {
  healthy: { name: '건강', filter: '', tilt: 0 },
  thirsty: { name: '목마름', filter: 'saturate(.7) brightness(1.03)', tilt: -5 },
  resting: { name: '관리 종료', filter: 'grayscale(.85) opacity(.55)', tilt: 0 },
};

/* ------------------------------------------------------------------ */
/* 조합                                                                 */
/* ------------------------------------------------------------------ */

/** 잎이 화분 흙에서 자라나도록 살짝 파묻는 정도 — 형태별로 다릅니다 */
const LIFT = { rosette: -.15, cactus: .2, vine: .1 };
/** 덩굴은 림 위로 늘어져야 하므로 앞쪽 림을 덧그리지 않습니다 */
const drapesOverRim = form => form === 'vine';

export function composeAvatar({
  pot = 'basic', potColor = '#d2915f', form = 'broadleaf',
  stage = 4, tone = 'green', prop = 'none', state = 'healthy', w = 46,
} = {}) {
  const toneDef = LEAF_TONES.find(t => t.id === tone) || LEAF_TONES[0];
  const formDef = PLANT_FORMS[form] || PLANT_FORMS.broadleaf;
  const propDef = PROPS[prop] || PROPS.none;
  const st = STATES[state] || STATES.healthy;
  const { rx, ry, h } = (POTS[pot] || POTS.basic).p;
  const rimY = -w * h + w * ry * (LIFT[form] ?? .55);
  const RX = w * rx;

  return `<g class="avatar" style="${st.filter ? `filter:${st.filter}` : ''}">
    <ellipse cx="${n1(RX * .06)}" cy="1.5" rx="${n1(RX * 1.12)}" ry="${n1(RX * .42)}" fill="rgba(44,62,46,.10)"/>
    <ellipse cx="${n1(RX * .04)}" cy="1" rx="${n1(RX * .84)}" ry="${n1(RX * .3)}" fill="rgba(44,62,46,.16)"/>
    ${drawPot(pot, w, potColor)}
    <g transform="translate(0,${n1(rimY)}) rotate(${st.tilt})">${formDef.draw(w, stage, toneDef)}</g>
    ${drapesOverRim(form) ? '' : potFront(pot, w, potColor)}
    ${propDef.draw(w, potRimY(pot, w))}
  </g>`;
}

export function toSVGDoc(inner, w, h, pad = 6) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"
    viewBox="${-w / 2} ${-h + pad} ${w} ${h}">${inner}</svg>`;
}
