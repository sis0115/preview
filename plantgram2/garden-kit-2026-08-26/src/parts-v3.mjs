/**
 * 정원 파츠 v3 — 잎을 복제하지 않고 한 장씩 다르게 그리는 판
 *
 * v2의 한계: 잎 실루엣 하나를 만들어 회전·확대만 바꿔 12~25번 찍었습니다.
 * 그래서 아무리 많이 붙여도 "도장 찍은 무늬"로 보이고 식물로 안 보였습니다.
 *
 * v3의 전제: **잎은 한 장씩 다른 물건이다.**
 *   같은 그루 안에서도 잎마다 길이·폭·휘어짐·처짐·단축(보는 각도)·접힘이 다릅니다.
 *   그래서 잎을 "모양 상수"가 아니라 **파라미터 묶음**으로 만들고,
 *   식물은 그 묶음들의 **배치표(composition)** 로 정의합니다.
 *
 * 잎 한 장의 파라미터
 *   len   길이            wid   최대 폭
 *   bend  잎맥이 옆으로 휘는 정도      sweep 끝이 아래로 말리는 정도
 *   face  단축률 0~1 — 정면을 보면 1, 옆으로 서면 0.3 (같은 잎도 각도에 따라 좁아진다)
 *   fold  접힘 0~1 — 잎이 잎맥을 따라 접혀 뒷면이 보이는 정도
 *   tier  대/중/소 — 아래쪽 묵은 잎일수록 크고 처지고 어둡다
 *
 * 성장 단계도 "전체를 축소"가 아니라 **어느 계층까지 났는가**로 표현합니다.
 *   1단계 소만 · 2단계 소+중 · 3단계 대까지 · 4단계 전부 + 잎이 커짐
 *
 * 화분·소품·상태·팔레트·크기 맞춤 규약은 v2에서 그대로 가져옵니다.
 */

import {
  GRID, LEAF_TONES, POT_COLORS, POTS, PROPS, STATES,
  drawPot, potFront, potRimY, shade, mix,
} from './parts-v2.mjs';

export { GRID, LEAF_TONES, POT_COLORS, POTS, PROPS, STATES, drawPot, potFront, potRimY, shade, mix };
export const VERSION = 3;

const n1 = v => Math.round(v * 100) / 100;

/* ------------------------------------------------------------------ */
/* 난수 · 광원                                                          */
/* ------------------------------------------------------------------ */

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export const seedOf = s => {
  let h = 2166136261;
  for (const ch of String(s)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return h >>> 0;
};

/** 좌상단 고정 광원 — 잎이 향한 각도로 밝기를 정합니다 */
export const LIGHT_DIR = -38;
function litness(rot) {
  const d = ((rot - LIGHT_DIR) % 360 + 540) % 360 - 180;
  return 0.5 + 0.5 * Math.cos(d * Math.PI / 180);
}
export function toneAt(tone, rot, depth) {
  const t = litness(rot);
  const c = t < .5 ? mix(tone.shadow, tone.base, t * 2) : mix(tone.base, tone.hi, (t - .5) * 2);
  return depth ? mix(c, tone.shadow, .5 * depth) : c;
}

/* ------------------------------------------------------------------ */
/* 잎 한 장 — 잎맥 곡선을 따라 폭을 입혀 만듭니다                        */
/* ------------------------------------------------------------------ */

/**
 * 폭 프로파일: 잎맥을 따라 t(0 밑동 → 1 끝)에서 반폭 비율을 돌려줍니다.
 * 이 함수가 종을 가릅니다 — 넓은 잎, 창 모양, 띠 모양이 여기서 갈립니다.
 */
export const PROFILE = {
  ovate:      t => Math.sin(Math.PI * Math.pow(t, .80)),
  cordate:    t => Math.sin(Math.PI * Math.pow(t, .98)) * 1.04,
  lanceolate: t => Math.sin(Math.PI * Math.pow(t, .60)) * .66,
  round:      t => Math.sin(Math.PI * Math.pow(t, 1.06)) * 1.28,
  /* 산세베리아 — 위아래 폭이 거의 일정하다가 끝에서만 좁아집니다 */
  strap:      t => (t < .82 ? .40 + .16 * Math.sin(Math.PI * t) : .56 * (1 - t) / .18),
  /* 야자 소엽 — 아주 가늘고 길게 */
  pinna:      t => Math.sin(Math.PI * Math.pow(t, .5)) * .34,
  /* 톱니 — 가장자리가 잘게 들쭉날쭉 */
  serrate:    t => Math.sin(Math.PI * Math.pow(t, .7)) * (.62 + .26 * Math.cos(t * 22)),
};

/**
 * 잎 한 장을 SVG로.
 * 원점은 잎이 줄기에 붙는 지점, 잎은 위(-y)를 향해 자랍니다.
 */
export function blade(sp) {
  const {
    kind = 'ovate', len = 34, wid = 18,
    bend = 0, sweep = 0, face = 1, fold = 0,
    fill, under, vein, edge = null, N = 34,
  } = sp;
  const prof = PROFILE[kind] || PROFILE.ovate;

  // 잎맥 곡선 — bend는 옆으로, sweep은 끝을 아래로 말아 처지게 합니다
  const mid = t => [bend * len * .42 * t * t, -len * t + sweep * len * .34 * t * t * t];

  const L = [], R = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    const [x, y] = mid(t);
    const [x2, y2] = mid(Math.min(1, t + 1e-3));
    const dx = x2 - x, dy = y2 - y, m = Math.hypot(dx, dy) || 1;
    const nx = -dy / m, ny = dx / m;                 // 잎맥에 수직
    const hw = wid * .5 * prof(t) * face;
    L.push([x + nx * hw, y + ny * hw]);
    R.push([x - nx * hw, y - ny * hw]);
  }
  const pts = a => a.map(([x, y]) => `${n1(x)},${n1(y)}`).join(' ');
  const body = `M${pts(L)} ${pts(R.slice().reverse())}Z`;

  // 접힘 — 잎맥에서 한쪽 가장자리까지를 뒷면 색으로 덮습니다
  let foldPath = '';
  if (fold > .04) {
    const half = [];
    for (let i = 0; i <= N; i++) {
      const t = i / N, [x, y] = mid(t);
      const [lx, ly] = L[i];
      half.push([x + (lx - x) * fold, y + (ly - y) * fold]);
    }
    const spine = Array.from({ length: N + 1 }, (_, i) => mid(1 - i / N));
    foldPath = `<path d="M${pts(half)} ${pts(spine)}Z" fill="${under}" opacity=".85"/>`;
  }

  const veinPath = Array.from({ length: 7 }, (_, i) => {
    const t = .18 + i * .11, [x, y] = mid(t);
    const [x2, y2] = mid(t + .001);
    const dx = x2 - x, dy = y2 - y, m = Math.hypot(dx, dy) || 1;
    const hw = wid * .5 * prof(t) * face * .72;
    const [lx, ly] = mid(t + .1);
    return `M${n1(x)},${n1(y)} L${n1(x - dy / m * hw)},${n1(y + dx / m * hw)}`
      + ` M${n1(x)},${n1(y)} L${n1(x + dy / m * hw)},${n1(y - dx / m * hw)}`;
  }).join(' ');

  const [tx, ty] = mid(1);
  return `${`<path d="${body}" fill="${fill}"/>`}
    ${foldPath}
    <path d="M0,0 L${n1(tx)},${n1(ty)}" stroke="${vein}" stroke-width="${n1(Math.max(.7, wid * .045))}"
      opacity=".26" fill="none" stroke-linecap="round"/>
    <path d="${veinPath}" stroke="${vein}" stroke-width=".7" opacity=".13" fill="none"/>
    ${edge ? `<path d="${body}" fill="none" stroke="${edge}" stroke-width="1" opacity=".5"/>` : ''}`;
}

/** 잎 한 장을 위치·각도와 함께 배치 */
export function place(sp, tone) {
  const rot = sp.rot || 0, depth = sp.depth || 0;
  // lit: 회전한 그룹 안에 있는 잎은 월드 기준 각도를 따로 받아야 명암이 맞습니다
  const fill = sp.fill || toneAt(tone, sp.lit ?? rot, depth);
  const under = sp.under || mix(fill, tone.shadow, .55);
  return `<g transform="translate(${n1(sp.x || 0)},${n1(sp.y || 0)}) rotate(${n1(rot)})">
    ${blade({ ...sp, fill, under, vein: tone.vein })}</g>`;
}

/** 잎자루 — 밑동에서 잎이 붙는 지점까지 */
export const stalk = (x, y, tone, w = 2) =>
  `<path d="M0,2 Q${n1(x * .3)},${n1(y * .55)} ${n1(x)},${n1(y)}"
    stroke="${mix(tone.vein, tone.base, .38)}" stroke-width="${n1(w)}" fill="none" stroke-linecap="round"/>`;

/* ------------------------------------------------------------------ */
/* 계층 — 대 / 중 / 소                                                  */
/* ------------------------------------------------------------------ */

/**
 * 아래쪽 묵은 잎(대)일수록 길고 넓고 많이 처지고 어둡습니다.
 * 위쪽 새잎(소)은 짧고 좁고 곧게 서고 밝습니다.
 * 성장 단계는 "어느 계층까지 났는가"로 표현합니다 — 전체를 축소하지 않습니다.
 */
const TIERS = ['big', 'mid', 'small'];
const TIER_AT = [['small'], ['small', 'mid'], ['small', 'mid', 'big'], ['small', 'mid', 'big']];
const TIER = {
  big:   { len: 1.00, wid: 1.00, sweep: .55, stalk: 1.00, depth: .55 },
  mid:   { len: .78, wid: .86, sweep: .30, stalk: .72, depth: .22 },
  small: { len: .52, wid: .68, sweep: .08, stalk: .40, depth: 0 },
};
/** 만개 단계에서만 잎이 조금 더 커집니다 */
const STAGE_GROW = [.82, .9, .96, 1];

/**
 * 배치표를 실제 잎 목록으로 펼칩니다.
 * plan: 계층별 [각도, 각도지터] 목록 — 각도가 곧 잎이 향한 방향입니다.
 */
function grow(plan, stage, seed, base) {
  const r = rng(seedOf(seed));
  const live = TIER_AT[stage - 1];
  const g = STAGE_GROW[stage - 1];
  const out = [];
  for (const tier of TIERS) {
    if (!live.includes(tier)) continue;
    const T = TIER[tier];
    for (const [ang, spread] of plan[tier] || []) {
      const rot = ang * (spread ?? 1) + (r() - .5) * 9;
      const jl = .88 + r() * .26, jw = .9 + r() * .22;
      const stalkLen = base.stalk * T.stalk * (.85 + r() * .3);
      const a = rot * Math.PI / 180;
      // 잎이 향한 방향이 정면에서 멀어질수록 좁아 보입니다 (단축)
      const face = base.faceMin + (1 - base.faceMin) * Math.pow(Math.abs(Math.cos(a * .82)), .7);
      out.push({
        kind: base.kind,
        rot,
        x: Math.sin(a) * stalkLen,
        y: -Math.cos(a) * stalkLen - base.rise,
        len: base.len * T.len * jl * g,
        wid: base.wid * T.wid * jw * g,
        bend: (r() - .5) * base.bendVar + (rot > 0 ? -base.bend : base.bend),
        sweep: T.sweep * base.sweepK * (.7 + r() * .6),
        face,
        fold: r() < base.foldRate ? .22 + r() * .3 : 0,
        depth: T.depth * (r() < .5 ? 1 : .4),
        stalkLen,
        edge: base.edge || null,
      });
    }
  }
  // 뒤쪽(어두운) 잎을 먼저, 앞쪽(밝은) 잎을 나중에 그립니다
  return out.sort((a, b) => b.depth - a.depth);
}

function render(leaves, tone, opts = {}) {
  let o = '';
  if (opts.stalks !== false) {
    for (const L of leaves) o += stalk(L.x, L.y, tone, Math.max(1.2, L.wid * .1));
  }
  for (const L of leaves) o += place(L, tone);
  return o;
}

/**
 * 한 그루에 실제로 달린 잎을 낱장으로 뽑아 한 줄로 늘어놓습니다 — 검수용.
 * "같은 잎을 복제한 게 아니라 한 장씩 다르다"를 눈으로 확인하는 용도입니다.
 */
export function leafRow(form, stage, tone, gap = 44) {
  const def = PLANT_FORMS[form];
  if (!def || !def.plan) return null;
  const leaves = grow(def.plan, stage, form + stage, def.base);
  return leaves.map((L, i) =>
    `<g class="leaf1" transform="translate(${n1((i - (leaves.length - 1) / 2) * gap)},0)">
      ${place({ ...L, x: 0, y: 0, rot: 0, lit: L.rot }, tone)}</g>`).join('');
}

/* ------------------------------------------------------------------ */
/* 식물 형태 9종 — 각 형태는 "배치표"입니다                              */
/* ------------------------------------------------------------------ */

export const PLANT_FORMS = {

  /* 대엽형 — 고무나무·몬스테라. 잎자루 끝에 한 장씩, 사이로 배경이 보입니다 */
  broadleaf: {
    name: '대엽형', species: ['몬스테라', '필로덴드론', '알로카시아', '고무나무'], leaf: 'ovate',
    plan: {
      big:   [[-58], [52], [-27], [31]],
      mid:   [[-40], [36], [-14], [18]],
      small: [[-9], [8], [0]],
    },
    base: { kind: 'ovate', len: 42, wid: 21, stalk: 27, rise: 2, bend: .5, bendVar: .5,
            sweepK: 1, faceMin: .46, foldRate: .3 },
    draw(w, stage, tone) {
      const k = w / 46;
      const leaves = grow(this.plan, stage, 'broadleaf' + stage, this.base);
      return `<g transform="scale(${n1(k)})">${render(leaves, tone)}</g>`;
    }
  },

  /* 직립형 — 산세베리아. 띠 모양 잎이 곧게 서고, 가장자리에 노란 테가 있습니다 */
  upright: {
    name: '직립형', species: ['산세베리아', '스투키', '금전수'], leaf: 'strap',
    plan: {
      big:   [[-19], [17], [-7], [8]],
      mid:   [[-13], [12], [0]],
      small: [[-6], [6]],
    },
    base: { kind: 'strap', len: 64, wid: 15, stalk: 3, rise: 0, bend: .16, bendVar: .3,
            sweepK: .35, faceMin: .58, foldRate: .18, edge: '#cdbc63' },
    draw(w, stage, tone) {
      const k = w / 46;
      const leaves = grow(this.plan, stage, 'upright' + stage, this.base);
      // 산세베리아 특유의 가로 줄무늬
      const band = L => {
        const b = [];
        for (let i = 1; i <= 5; i++) {
          const t = i / 6, hw = L.wid * .5 * PROFILE.strap(t) * L.face * .82;
          b.push(`<path d="M${n1(-hw)},${n1(-L.len * t)} Q0,${n1(-L.len * t + 2.2)} ${n1(hw)},${n1(-L.len * t)}"
            stroke="${mix(tone.hi, '#e8e2a8', .45)}" stroke-width="2" opacity=".38" fill="none"/>`);
        }
        return `<g transform="translate(${n1(L.x)},${n1(L.y)}) rotate(${n1(L.rot)})">${b.join('')}</g>`;
      };
      return `<g transform="scale(${n1(k)})">${render(leaves, tone)}${leaves.map(band).join('')}</g>`;
    }
  },

  /* 로제트형 — 다육. 넓고 두꺼운 잎 몇 장이 안쪽으로 겹쳐 꽃 모양을 이룹니다 */
  rosette: {
    name: '로제트형', species: ['다육식물', '에케베리아', '하월시아'], leaf: 'ovate',
    plan: {
      big:   [[-150], [-95], [-45], [0], [45], [95], [150], [180]],
      mid:   [[-125], [-65], [-20], [25], [70], [125]],
      small: [[-90], [-30], [30], [90]],
    },
    base: { kind: 'ovate', len: 26, wid: 17, stalk: 0, rise: 0, bend: .1, bendVar: .3,
            sweepK: .2, faceMin: .5, foldRate: .5 },
    draw(w, stage, tone) {
      const k = w / 46;
      const leaves = grow(this.plan, stage, 'rosette' + stage, this.base);
      // 위에서 내려다보는 형태라 세로로 눌러 방사 배치합니다
      return `<g transform="translate(0,-3) scale(${n1(k)},${n1(k * .66)})">
        ${render(leaves, tone, { stalks: false })}</g>`;
    }
  },

  /* 무늬엽형 — 칼라데아. 잎맥을 따라 크림색 무늬가 갈라집니다 */
  patterned: {
    name: '무늬엽형', species: ['칼라데아', '마란타', '스킨답서스'], leaf: 'ovate',
    plan: {
      big:   [[-52], [48], [-24], [28]],
      mid:   [[-38], [34], [-12]],
      small: [[-8], [8], [0]],
    },
    base: { kind: 'ovate', len: 38, wid: 19, stalk: 16, rise: 2, bend: .42, bendVar: .5,
            sweepK: .8, faceMin: .48, foldRate: .34 },
    draw(w, stage, tone) {
      const k = w / 46;
      const leaves = grow(this.plan, stage, 'patterned' + stage, this.base);
      const mark = tone.mark || '#dfeccb';
      // 잎맥을 따라 갈라지는 무늬 — 잎마다 갈래 수가 다릅니다
      const stripes = L => {
        const s = [];
        // 잎맥을 따라 흐르는 밝은 띠 한 줄 — 칼라데아의 중앙 무늬
        const pt = [];
        for (let i = 0; i <= 10; i++) {
          const t = .1 + i * .08;
          pt.push(`${n1(-L.wid * .5 * PROFILE.ovate(t) * L.face * .42)},${n1(-L.len * t)}`);
        }
        for (let i = 10; i >= 0; i--) {
          const t = .1 + i * .08;
          pt.push(`${n1(L.wid * .5 * PROFILE.ovate(t) * L.face * .42)},${n1(-L.len * t)}`);
        }
        s.push(`<path d="M${pt.join(' ')}Z" fill="${mark}" opacity=".42"/>`);
        return `<g transform="translate(${n1(L.x)},${n1(L.y)}) rotate(${n1(L.rot)})">${s.join('')}</g>`;
      };
      return `<g transform="scale(${n1(k)})">${render(leaves, tone)}${leaves.map(stripes).join('')}</g>`;
    }
  },

  /* 덩굴형 — 포토스. 잎이 크고 줄기는 거의 안 보이게 잎에 가립니다 */
  vine: {
    name: '덩굴형', species: ['포토스', '아이비', '스킨답서스', '립살리스'], leaf: 'round',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('vine' + stage));
      const leaves = [];
      let stems = '';

      // 1) 흙에서 바로 올라오는 잎 — 화분 위가 비지 않게
      const crown = [[-26, 15], [22, 14], [0, 19], [-9, 11], [11, 12]].slice(0, [2, 3, 4, 5][stage - 1]);
      for (const [ang, up] of crown) {
        const a = ang * Math.PI / 180;
        stems += stalk(Math.sin(a) * up, -Math.cos(a) * up, tone, 1.6);
        leaves.push({
          kind: 'round', rot: ang + (r() - .5) * 12,
          x: Math.sin(a) * up, y: -Math.cos(a) * up,
          len: 24 * (.9 + r() * .24), wid: 22 * (.9 + r() * .22),
          bend: (r() - .5) * .5, sweep: .25,
          face: .6 + .4 * Math.abs(Math.cos(a)), fold: r() < .3 ? .24 : 0, depth: 0,
        });
      }

      // 2) 화분 밖으로 넘어가 늘어지는 줄기 — 좌우 대칭
      const strands = [[-1, 33, 36], [1, 32, 34], [-1, 18, 15], [1, 17, 12]]
        .slice(0, [0, 2, 3, 4][stage - 1]);
      const per = [0, 3, 4, 5][stage - 1];
      for (const [dir, out, down] of strands) {
        const cx = dir * out * .5, cy = -12;
        const ex = dir * out, ey = down;
        const at = t => [2 * (1 - t) * t * cx + t * t * ex, 2 * (1 - t) * t * cy + t * t * ey];
        stems += `<path d="M0,2 Q${n1(cx)},${n1(cy)} ${n1(ex)},${n1(ey)}"
          stroke="${mix(tone.vein, tone.base, .42)}" stroke-width="1.7" fill="none" stroke-linecap="round"/>`;
        for (let i = 1; i <= per; i++) {
          const t = .24 + .76 * (i / per), [px, py] = at(t);
          const side = i % 2 ? 1 : -1;
          const rot = dir * (56 + t * 84) + side * 20 + (r() - .5) * 16;
          const a = rot * Math.PI / 180;
          leaves.push({
            kind: 'round', rot, x: px, y: py,
            len: 22 * (1.02 - t * .22) * (.88 + r() * .26),
            wid: 20 * (1.02 - t * .22) * (.88 + r() * .24),
            bend: (r() - .5) * .5, sweep: .22 + r() * .3,
            face: .52 + .48 * Math.pow(Math.abs(Math.cos(a * .8)), .7),
            fold: r() < .34 ? .2 + r() * .28 : 0,
            depth: i % 3 === 0 ? .5 : 0,
          });
        }
      }
      leaves.sort((a, b) => b.depth - a.depth);
      return `<g transform="scale(${n1(k)})">${stems}${leaves.map(L => place(L, tone)).join('')}</g>`;
    }
  },

  /* 깃꼴형 — 야자. 소엽이 가늘고 길며 끝으로 갈수록 아래로 처집니다 */
  palm: {
    name: '깃꼴형', species: ['테이블야자', '아레카야자', '켄차야자'], leaf: 'pinna',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('palm' + stage));
      const fronds = [[-34, 1], [31, .97], [-16, .92], [15, .94], [0, 1.04], [-48, .82], [45, .8]]
        .slice(0, [2, 4, 6, 7][stage - 1]);
      const ribs = [], pinnae = [];
      for (const [ang, lenK] of fronds) {
        const H = 62 * lenK * (.9 + r() * .2), depth = r() < .35 ? .5 : 0;
        const curve = Math.sign(ang) * 12;
        const rib = t => [curve * t * t * .34, -H * t + H * .1 * t * t * t];
        const pairs = 9;
        let pin = '';
        for (let j = 1; j <= pairs; j++) {
          const t = j / pairs, [px, py] = rib(t * .94);
          // 밑동과 끝에서 짧고 가운데가 가장 긴 깃 모양
          const shape = Math.sin(Math.PI * Math.pow(t, .85));
          const pl = 27 * shape * lenK * (.85 + r() * .3);
          for (const side of [-1, 1]) {
            const rot = side * (40 + t * 26) + (r() - .5) * 7;
            pin += place({
              kind: 'pinna', rot, lit: ang + rot, x: px, y: py,
              len: pl, wid: 6.5 * shape + 1.6,
              bend: side * .55, sweep: .55 + t * .55,
              face: .62 + .38 * shape, fold: 0, depth,
            }, tone);
          }
        }
        // 끝잎 한 장
        const [tx, ty] = rib(.97);
        pin += place({ kind: 'pinna', rot: 0, lit: ang, x: tx, y: ty,
          len: 14 * lenK, wid: 4.6, bend: 0, sweep: .3, face: .9, fold: 0, depth }, tone);
        const [ex, ey] = rib(.94);
        ribs.push(`<g transform="rotate(${n1(ang)})"><path d="M0,3 Q${n1(curve * .3)},${n1(-H * .55)} ${n1(ex)},${n1(ey)}"
          stroke="${mix(tone.vein, tone.base, .34)}" stroke-width="1.8" fill="none" stroke-linecap="round"/></g>`);
        pinnae.push(`<g transform="rotate(${n1(ang)})">${pin}</g>`);
      }
      return `<g transform="scale(${n1(k)})">${ribs.join('')}${pinnae.join('')}</g>`;
    }
  },

  /* 기둥형 — 선인장. 잎이 없고 능선과 가시로 읽힙니다 */
  cactus: {
    name: '기둥형', species: ['선인장', '유포르비아', '용신목'], leaf: null,
    draw(w, stage, tone) {
      const k = w / 46, H = [30, 42, 52, 58][stage - 1], BW = 12;
      const lit = mix(tone.base, tone.hi, .55), dim = mix(tone.base, tone.shadow, .5);
      const arms = stage >= 3 ? [[-1, .5], [1, .42]] : (stage === 2 ? [[-1, .42]] : []);
      let o = '';
      for (const [d, hs] of arms) {
        o += `<path d="M0,${n1(-H * .46)} Q${n1(d * 20)},${n1(-H * .46)} ${n1(d * 20)},${n1(-H * .5 - H * hs * .5)}"
          stroke="${d < 0 ? lit : dim}" stroke-width="14" fill="none" stroke-linecap="round"/>`;
      }
      o += `<rect x="${-BW}" y="${-H}" width="${BW * 2}" height="${H + 4}" rx="${BW}" fill="${tone.base}"/>
        <rect x="${-BW}" y="${-H}" width="8" height="${H + 4}" rx="4" fill="${lit}"/>
        <rect x="${BW - 7}" y="${-H}" width="7" height="${H + 4}" rx="3.5" fill="${dim}" opacity=".7"/>
        <path d="M-3.2,${n1(-H * .9)} L-3.2,${n1(-H * .08)} M3.2,${n1(-H * .9)} L3.2,${n1(-H * .08)}"
          stroke="${tone.vein}" stroke-width="1.1" opacity=".32"/>`;
      for (let j = 1; j <= 6; j++) {
        const y = -H * (j / 7);
        o += `<path d="M${n1(-BW + 1)},${n1(y)} l-3.4,-1.8 M${n1(BW - 1)},${n1(y)} l3.4,-1.8"
          stroke="#e8e0c2" stroke-width="1.1" opacity=".8" stroke-linecap="round"/>`;
      }
      return `<g transform="scale(${n1(k)})">${o}</g>`;
    }
  },

  /* 양치형 — 고사리. 휘는 잎줄기에 톱니 소엽이 촘촘히 */
  fern: {
    name: '양치형', species: ['보스턴고사리', '아디안텀', '박쥐란'], leaf: 'serrate',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('fern' + stage));
      const fronds = [[-58, 1], [54, .96], [-30, .9], [28, .92], [0, 1], [-80, .76], [76, .74], [-14, .84], [14, .86]]
        .slice(0, [3, 5, 7, 9][stage - 1]);
      const ribs = [], pinnae = [];
      for (const [ang, lenK] of fronds) {
        const H = 46 * lenK * (.9 + r() * .2), depth = r() < .4 ? .5 : 0;
        const curve = Math.sign(ang) * 14;
        const rib = t => [curve * t * t * .6, -H * t + H * .22 * t * t * t];
        const pairs = 12;
        let pin = '';
        for (let j = 1; j <= pairs; j++) {
          const t = j / pairs, [px, py] = rib(t * .95);
          const shape = Math.sin(Math.PI * Math.pow(t, .8));
          for (const side of [-1, 1]) {
            const rot = side * (68 + t * 22) + (r() - .5) * 7;
            pin += place({
              kind: 'serrate', rot, lit: ang + rot, x: px, y: py,
              len: 9.5 * shape * lenK + 2, wid: 5.2 * shape + 1.4,
              bend: side * .35, sweep: .35, face: .68 + .32 * shape, fold: 0, depth,
            }, tone);
          }
        }
        const [ex, ey] = rib(.95);
        ribs.push(`<g transform="rotate(${n1(ang)})"><path d="M0,3 Q${n1(curve * .35)},${n1(-H * .55)} ${n1(ex)},${n1(ey)}"
          stroke="${mix(tone.vein, tone.base, .34)}" stroke-width="1.4" fill="none" stroke-linecap="round"/></g>`);
        pinnae.push(`<g transform="rotate(${n1(ang)})">${pin}</g>`);
      }
      return `<g transform="scale(${n1(k)})">${ribs.join('')}${pinnae.join('')}</g>`;
    }
  },

  /* 꽃나무 — 관목. 잎이 덩어리로 뭉치고 꽃이 그 위에 점점이 얹힙니다 */
  flower: {
    name: '꽃나무', species: ['제라늄', '수국', '동백'], leaf: 'ovate', petal: '#e8899e',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('flower' + stage));
      const clumps = [[-30, -20, 1], [28, -22, .95], [0, -34, 1.05], [-16, -38, .8], [18, -37, .82],
                      [-38, -8, .7], [36, -10, .68]].slice(0, [2, 4, 6, 7][stage - 1]);
      let o = '';
      // 잔가지
      for (const [cx, cy] of clumps) o += stalk(cx, cy, tone, 1.8);
      // 잎 뭉치 — 뭉치마다 작은 잎 5~7장이 사방으로
      const leaves = [];
      for (const [cx, cy, s] of clumps) {
        const n = 6 + Math.floor(r() * 3);
        for (let i = 0; i < n; i++) {
          const rot = (i * 360 / n) + r() * 40 - 20;
          const a = rot * Math.PI / 180, rad = 4 * s;
          leaves.push({
            kind: 'ovate', rot, x: cx + Math.sin(a) * rad, y: cy - Math.cos(a) * rad,
            len: 21 * s * (.85 + r() * .3), wid: 15 * s * (.85 + r() * .3),
            bend: (r() - .5) * .6, sweep: .2,
            face: .55 + .45 * Math.pow(Math.abs(Math.cos(a * .8)), .7),
            fold: r() < .3 ? .25 : 0, depth: i % 2 ? .45 : 0,
          });
        }
      }
      leaves.sort((a, b) => b.depth - a.depth);
      o += leaves.map(L => place(L, tone)).join('');
      if (stage >= 3) {
        for (const [cx, cy, s] of clumps) {
          if (r() < .45) continue;
          const fx = cx + (r() - .5) * 10, fy = cy - 6 * s - r() * 6;
          o += `<g transform="translate(${n1(fx)},${n1(fy)})">
            ${[0, 72, 144, 216, 288].map(ang =>
              `<ellipse cx="0" cy="-4.4" rx="3" ry="4.6" fill="${ang < 180 ? this.petal : shade(this.petal, -16)}"
                 transform="rotate(${ang})"/>`).join('')}
            <circle r="2.2" fill="#f6d96b"/></g>`;
        }
      }
      return `<g transform="scale(${n1(k)})">${o}</g>`;
    }
  },
};

/* ------------------------------------------------------------------ */
/* 크기 맞춤 — v2와 같은 규약 (표만 v3 그림에 맞춰 다시 잽니다)          */
/* ------------------------------------------------------------------ */

/** `node src/measure.mjs v3` 가 재서 갱신합니다 */
export const FORM_EXT = {
  broadleaf: { w: 114.1, h: 67.5 },
  upright:   { w: 40.4,  h: 70.3 },
  rosette:   { w: 56,  h: 37.3 },
  patterned: { w: 85.5,  h: 53.6 },
  vine:      { w: 95.1,  h: 94.8 },
  palm:      { w: 103, h: 76.3 },
  cactus:    { w: 40,  h: 62 },
  fern:      { w: 66.3, h: 42.6 },
  flower:    { w: 107.3,  h: 65.9 },
};

export const FORM_FIT = {
  broadleaf: { h: 3.2, w: 1.75 },
  upright:   { h: 3.0, w: 1.15 },
  rosette:   { h: 1.6, w: 1.05 },
  patterned: { h: 2.6, w: 1.55 },
  vine:      { h: 4.4, w: 1.85 },  // 크라운 + 늘어짐이 한 bbox에 들어갑니다
  palm:      { h: 3.0, w: 1.80 },
  cactus:    { h: 3.4, w: 0.95 },
  fern:      { h: 2.6, w: 1.80 },
  flower:    { h: 2.8, w: 1.60 },
};

export function fitScale(form, w, potId) {
  const ext = FORM_EXT[form], fit = FORM_FIT[form];
  if (!ext || !fit) return 1;
  const { rx, h } = (POTS[potId] || POTS.basic).p;
  return Math.min(fit.h * (w * h) / ext.h, fit.w * (w * rx * 2) / ext.w);
}

/* ------------------------------------------------------------------ */
/* 조합                                                                 */
/* ------------------------------------------------------------------ */

const LIFT = { rosette: -.15, cactus: .2, vine: .1 };
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
  const fit = fitScale(form, w, pot);

  return `<g class="avatar" style="${st.filter ? `filter:${st.filter}` : ''}">
    <ellipse cx="${n1(RX * .06)}" cy="1.5" rx="${n1(RX * 1.12)}" ry="${n1(RX * .42)}" fill="rgba(44,62,46,.10)"/>
    <ellipse cx="${n1(RX * .04)}" cy="1" rx="${n1(RX * .84)}" ry="${n1(RX * .3)}" fill="rgba(44,62,46,.16)"/>
    ${drawPot(pot, w, potColor)}
    <g transform="translate(0,${n1(rimY)}) rotate(${st.tilt}) scale(${n1(fit)})">${formDef.draw(w, stage, toneDef)}</g>
    ${drapesOverRim(form) ? '' : potFront(pot, w, potColor)}
    ${propDef.draw(w, potRimY(pot, w))}
  </g>`;
}

export function toSVGDoc(inner, w, h, pad = 6) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"
    viewBox="${-w / 2} ${-h + pad} ${w} ${h}">${inner}</svg>`;
}
