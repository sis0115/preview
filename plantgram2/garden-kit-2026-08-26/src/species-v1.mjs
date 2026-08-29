/**
 * 대표종 전용 아바타 — 종마다 실제 잎 구조를 따로 그립니다
 *
 * 형태 9종(parts-v3)은 도감 124종을 8~9개 골격으로 묶어 그리는 판입니다.
 * 그걸로는 "몬스테라답다 / 여인초답다"가 안 나옵니다. 종을 가르는 것은 골격이 아니라
 * **잎의 구조**이기 때문입니다 — 몬스테라는 갈라진 잎, 여인초는 한 평면에 부챗살,
 * 유칼립투스는 줄기에 바로 붙은 동전잎.
 *
 * 그래서 눈에 띄는 대표종은 여기서 **한 종씩 따로** 그립니다.
 * 나머지 종은 계속 형태 9종으로 매핑됩니다.
 *
 * 잎 엔진(잎맥 곡선 + 폭 프로파일 + 단축·접힘·처짐)과 화분·팔레트·크기 맞춤은
 * parts-v3 / parts-v2에서 그대로 가져와 재사용합니다.
 *
 * 종별 근거 (웹 자료 확인):
 *   몬스테라   가장자리에서 잎맥까지 갈라지고, 잎맥 양옆에 구멍이 줄지어 난다.
 *              어린잎은 통잎이고 자라면서 갈라짐이 깊어진다.
 *   여인초     길이:폭 ≈ 3:1 의 노(paddle) 모양 잎이 긴 잎자루 끝에 달리고,
 *              좌우 두 줄(distichous)로만 나 한 평면에서 부채가 된다.
 *              잎이 잎맥을 따라 찢어진다.
 *   대나무     마디가 있는 줄기 여러 대, 잎은 줄기 위쪽에 다발로 달린다.
 *   아레카야자 줄기 여러 대가 모여 나고, 잎줄기가 바깥·아래로 활처럼 휘며
 *              아주 가는 소엽이 마주보고 촘촘히 달린다.
 *   유칼립투스 어린잎은 잎자루 없이 줄기에 바로, 둥근 잎이 마주보고 짝지어 달린다.
 *              은청색.
 */

import { POTS, PROPS, STATES, LEAF_TONES, POT_COLORS, drawPot, potFront, potRimY, mix, shade }
  from './parts-v2.mjs';
import { blade, place, stalk, rng, seedOf, toneAt } from './parts-v3.mjs';

export { POTS, PROPS, STATES, LEAF_TONES, POT_COLORS };
export const VERSION = 1;

const n1 = v => Math.round(v * 100) / 100;
const rad = d => d * Math.PI / 180;

/* ------------------------------------------------------------------ */
/* 몬스테라 전용 잎 — 갈라짐과 구멍                                      */
/* ------------------------------------------------------------------ */

/**
 * 잎 가장자리에서 잎맥 쪽으로 갈라지고(split), 잎맥 옆에 구멍(hole)이 줄지어 납니다.
 * 구멍은 같은 path 안의 서브패스로 넣고 fill-rule="evenodd"로 뚫습니다
 * (Flutter의 PathFillType.evenOdd와 같은 방식이라 그대로 옮길 수 있습니다).
 *
 * cut 0~1 — 갈라짐 깊이. 어린잎은 0(통잎), 다 자란 잎은 0.8까지.
 */
function monsteraLeaf({ len, wid, face, cut, fill, under, vein, fold = 0, phase = 0 }) {
  const N = 56, LOBES = 4;
  const mid = t => [wid * .06 * t * t, -len * t];
  const prof = t => Math.sin(Math.PI * Math.pow(t, .92)) * 1.02;

  // 갈라짐: 잎맥에 직각으로 파고드는 홈. 위로 갈수록 얕아집니다.
  const notch = (t, side) => {
    if (cut <= 0) return 1;
    const ph = t * LOBES + (side > 0 ? .5 : 0) + phase;
    const d = Math.abs(ph - Math.round(ph)) * 2;            // 0(홈 한가운데) ~ 1
    const depth = cut * (1 - .3 * t);
    return 1 - depth * Math.max(0, 1 - Math.pow(d / .46, 2));
  };

  const L = [], R = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N, [x, y] = mid(t);
    const [x2, y2] = mid(Math.min(1, t + 1e-3));
    const dx = x2 - x, dy = y2 - y, m = Math.hypot(dx, dy) || 1;
    const nx = -dy / m, ny = dx / m;
    const hw = wid * .5 * prof(t) * face;
    L.push([x + nx * hw * notch(t, -1), y + ny * hw * notch(t, -1)]);
    R.push([x - nx * hw * notch(t, 1), y - ny * hw * notch(t, 1)]);
  }
  const pts = a => a.map(([x, y]) => `${n1(x)},${n1(y)}`).join(' ');
  let d = `M${pts(L)} ${pts(R.slice().reverse())}Z`;

  // 잎맥 양옆 구멍 — 다 자란 잎에만
  if (cut > .35) {
    for (let i = 0; i < 3; i++) {
      const t = .3 + i * .17, [x, y] = mid(t);
      const rx = wid * .075 * face * (1.15 - i * .2), ry = len * .062 * (1.15 - i * .2);
      for (const side of [-1, 1]) {
        const cx = x + side * wid * .17 * face, cy = y;
        d += ` M${n1(cx - rx)},${n1(cy)} a${n1(rx)},${n1(ry)} 0 1,0 ${n1(rx * 2)},0`
           + ` a${n1(rx)},${n1(ry)} 0 1,0 ${n1(-rx * 2)},0 Z`;
      }
    }
  }

  const [tx, ty] = mid(1);
  const ribs = Array.from({ length: LOBES }, (_, i) => {
    const t = .18 + i * .2, [x, y] = mid(t);
    const hw = wid * .5 * prof(t) * face * .8;
    return `M${n1(x)},${n1(y)} L${n1(x - hw)},${n1(y - len * .08)}`
         + ` M${n1(x)},${n1(y)} L${n1(x + hw)},${n1(y - len * .08)}`;
  }).join(' ');

  return `<path d="${d}" fill="${fill}" fill-rule="evenodd"/>
    ${fold > .05 ? `<path d="M${pts(L.map(([x, y], i) => {
      const [mx, my] = mid(i / N);
      return [mx + (x - mx) * fold, my + (y - my) * fold];
    }))} ${pts(Array.from({ length: N + 1 }, (_, i) => mid(1 - i / N)))}Z"
      fill="${under}" opacity=".8"/>` : ''}
    <path d="M0,0 L${n1(tx)},${n1(ty)}" stroke="${vein}" stroke-width="${n1(wid * .045)}"
      opacity=".26" fill="none" stroke-linecap="round"/>
    <path d="${ribs}" stroke="${vein}" stroke-width=".8" opacity=".16" fill="none"/>`;
}

/* ------------------------------------------------------------------ */
/* 여인초 전용 잎 — 잎맥을 따라 찢어진 노 모양                            */
/* ------------------------------------------------------------------ */

/** 가장자리에서 잎맥 쪽으로 곧게 들어온 찢김 자국을 넣습니다 */
function paddleLeaf({ len, wid, face, tears, fill, under, vein }) {
  const N = 30;
  const mid = t => [wid * .1 * t * t, -len * t];
  const prof = t => Math.sin(Math.PI * Math.pow(t, .42)) * .98;
  const L = [], R = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N, [x, y] = mid(t);
    const [x2, y2] = mid(Math.min(1, t + 1e-3));
    const dx = x2 - x, dy = y2 - y, m = Math.hypot(dx, dy) || 1;
    const nx = -dy / m, ny = dx / m, hw = wid * .5 * prof(t) * face;
    L.push([x + nx * hw, y + ny * hw]);
    R.push([x - nx * hw, y - ny * hw]);
  }
  const pts = a => a.map(([x, y]) => `${n1(x)},${n1(y)}`).join(' ');
  const body = `M${pts(L)} ${pts(R.slice().reverse())}Z`;

  // 찢김 — 가장자리에서 잎맥까지 60~85% 들어온 가는 틈
  let rip = '';
  for (let i = 0; i < tears; i++) {
    const t = .25 + (i + .5) * (.6 / tears);
    const [x, y] = mid(t);
    const hw = wid * .5 * prof(t) * face;
    const side = i % 2 ? 1 : -1;
    const depth = .62 + (i % 3) * .1;
    rip += `<path d="M${n1(x + side * hw)},${n1(y)} L${n1(x + side * hw * (1 - depth))},${n1(y - len * .03)}"
      stroke="${vein}" stroke-width="${n1(wid * .05)}" opacity=".3" stroke-linecap="round"/>`;
  }
  const [tx, ty] = mid(1);
  return `<path d="${body}" fill="${fill}"/>${rip}
    <path d="M0,0 L${n1(tx)},${n1(ty)}" stroke="${vein}" stroke-width="${n1(wid * .06)}"
      opacity=".3" fill="none" stroke-linecap="round"/>`;
}


/* ------------------------------------------------------------------ */
/* 꽃 한 송이 — 제라늄·데이지가 공유합니다                                */
/* ------------------------------------------------------------------ */

/** petals 장의 꽃잎 + 가운데 꽃술. r는 꽃 반지름 */
function floret(petals, r, petal, center, shade2) {
  const p = Array.from({ length: petals }, (_, i) => {
    const a = i * 360 / petals;
    return `<ellipse cx="0" cy="${n1(-r * .62)}" rx="${n1(r * .42)}" ry="${n1(r * .68)}"
      fill="${a < 180 ? petal : shade2}" transform="rotate(${n1(a)})"/>`;
  }).join('');
  return `${p}<circle r="${n1(r * .3)}" fill="${center}"/>`;
}

/** 낮은 잎 무더기 — 화단 식물의 바탕이 됩니다 */
function mound(count, spreadX, spreadY, leafLen, kind, tone, r, opts = {}) {
  const out = [];
  for (let i = 0; i < count; i++) {
    const t = i / Math.max(1, count - 1);
    const x = (t - .5) * 2 * spreadX * (.6 + r() * .8);
    const y = -spreadY * (.25 + r() * .75);
    const rot = (x / spreadX) * (opts.lean ?? 46) + (r() - .5) * 26;
    const a = rot * Math.PI / 180;
    out.push({
      kind, rot, x, y,
      len: leafLen * (.8 + r() * .45), wid: leafLen * (opts.widK ?? .8) * (.8 + r() * .4),
      bend: (r() - .5) * .6, sweep: .2 + r() * .4,
      face: .55 + .45 * Math.pow(Math.abs(Math.cos(a * .8)), .7),
      fold: r() < .3 ? .22 : 0,
      depth: i % 3 === 0 ? .5 : 0,
    });
  }
  return out.sort((a, b) => b.depth - a.depth);
}

/* ------------------------------------------------------------------ */
/* 종                                                                   */
/* ------------------------------------------------------------------ */

export const SPECIES = {

  /* 몬스테라 — 긴 잎자루 끝에 갈라진 큰 잎. 어린잎은 통잎 */
  monstera: {
    name: '몬스테라', latin: 'Monstera deliciosa', form: 'broadleaf',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('monstera' + stage));
      // [각도, 잎자루, 크기, 갈라짐, 뒤쪽] — 어린잎(통잎)부터 적고 앞에서부터 잘라 씁니다.
      // 그래서 새싹은 통잎만, 자랄수록 갈라진 큰 잎이 더해집니다.
      const plan = [
        [-2, 15, .50, 0, 0], [4, 12, .40, 0, 0],
        [-10, 24, .70, .32, 0], [9, 23, .72, .28, 0],
        [-25, 31, .88, .62, 0], [22, 30, .90, .66, 0],
        [-46, 36, 1.00, .80, 1], [42, 35, .96, .76, 1],
      ].slice(0, [2, 4, 6, 8][stage - 1]);
      let stems = '', leaves = [];
      for (const [ang, sl, sz, cut, back] of plan) {
        const a = rad(ang), px = Math.sin(a) * sl, py = -Math.cos(a) * sl;
        stems += stalk(px, py, tone, 2.6 * sz);
        const face = .5 + .5 * Math.pow(Math.abs(Math.cos(a * .8)), .7);
        leaves.push({ ang, px, py, sz, cut, back, face,
          jl: .92 + r() * .16, fold: r() < .25 ? .22 : 0, phase: r() * .5 });
      }
      leaves.sort((x, y) => y.back - x.back);
      const body = leaves.map(L => {
        const fill = toneAt(tone, L.ang, L.back * .5);
        return `<g transform="translate(${n1(L.px)},${n1(L.py)}) rotate(${n1(L.ang)})">
          ${monsteraLeaf({ len: 52 * L.sz * L.jl, wid: 36 * L.sz, face: L.face, cut: L.cut,
            fill, under: mix(fill, tone.shadow, .55), vein: tone.vein, fold: L.fold, phase: L.phase })}</g>`;
      }).join('');
      return `<g transform="scale(${n1(k)})">${stems}${body}</g>`;
    }
  },

  /* 여인초 — 긴 잎자루 끝의 노 모양 잎이 좌우 두 줄로만 나 한 평면에서 부채가 됩니다 */
  strelitzia: {
    name: '여인초', latin: 'Strelitzia nicolai', form: 'broadleaf',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('strelitzia' + stage));
      // 두 줄(distichous) — 좌우로만 벌어지고 앞뒤로는 벌어지지 않습니다
      const plan = [
        [-16, 27, .72, 0], [14, 26, .74, 0],
        [-34, 35, .88, 0], [31, 34, .90, 0],
        [-54, 40, 1.00, 1], [50, 39, .97, 1],
        [-4, 17, .52, 0],
      ].slice(0, [2, 4, 6, 7][stage - 1]);
      let stems = '', leaves = [];
      for (const [ang, sl, sz, back] of plan) {
        const a = rad(ang), px = Math.sin(a) * sl, py = -Math.cos(a) * sl;
        stems += stalk(px, py, tone, 2.4 * sz);
        leaves.push({ ang, px, py, sz, back, face: .62 + .38 * Math.abs(Math.cos(a * .7)) });
      }
      leaves.sort((x, y) => y.back - x.back);
      const body = leaves.map(L => {
        const fill = toneAt(tone, L.ang, L.back * .45);
        return `<g transform="translate(${n1(L.px)},${n1(L.py)}) rotate(${n1(L.ang)})">
          ${paddleLeaf({ len: 44 * L.sz, wid: 25 * L.sz, face: L.face,
            tears: 5 + Math.floor(r() * 3), fill, under: mix(fill, tone.shadow, .5), vein: tone.vein })}</g>`;
      }).join('');
      return `<g transform="scale(${n1(k)})">${stems}${body}</g>`;
    }
  },

  /* 대나무 — 마디 있는 줄기 여러 대, 잎은 위쪽에 다발로 */
  bamboo: {
    name: '대나무', latin: 'Dracaena sanderiana', form: 'upright',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('bamboo' + stage));
      const canes = [[0, 34, .8], [-9, 50, .92], [13, 44, .9], [4, 66, 1], [-17, 40, .85]]
        .slice(0, [1, 2, 3, 5][stage - 1]);
      const cane = mix(tone.base, '#d9e2a8', .42), caneDim = mix(cane, tone.shadow, .4);
      let o = '';
      for (const [x, H, s] of canes) {
        // 마디 — 줄기를 토막으로 끊습니다
        const segs = Math.max(3, Math.round(H / 15));
        let culm = `<rect x="${n1(x - 2.6 * s)}" y="${n1(-H)}" width="${n1(5.2 * s)}" height="${n1(H + 3)}"
          rx="${n1(2.6 * s)}" fill="${cane}"/>
          <rect x="${n1(x - 2.6 * s)}" y="${n1(-H)}" width="${n1(1.9 * s)}" height="${n1(H + 3)}"
          rx="${n1(1 * s)}" fill="${mix(cane, tone.hi, .5)}" opacity=".7"/>`;
        for (let i = 1; i < segs; i++) {
          const y = -H * (i / segs);
          culm += `<rect x="${n1(x - 3.2 * s)}" y="${n1(y)}" width="${n1(6.4 * s)}" height="${n1(1.8 * s)}"
            rx="${n1(.9 * s)}" fill="${caneDim}"/>`;
        }
        o += culm;
        // 잎 다발 — 줄기 위쪽 두 마디에서
        const tuft = 4 + Math.floor(r() * 3);
        for (let i = 0; i < tuft; i++) {
          const ang = -58 + (i / Math.max(1, tuft - 1)) * 116 + (r() - .5) * 14;
          const at = -H + (i % 2 ? 5 : 13) * s;
          const a = rad(ang);
          o += place({
            kind: 'lanceolate', rot: ang, x, y: at,
            len: (22 + r() * 8) * s, wid: (6.5 + r() * 2) * s,
            bend: Math.sign(ang) * .45, sweep: .55 + r() * .4,
            face: .55 + .45 * Math.abs(Math.cos(a * .8)),
            fold: 0, depth: i % 3 === 0 ? .45 : 0,
          }, tone);
        }
      }
      return `<g transform="scale(${n1(k)})">${o}</g>`;
    }
  },

  /* 아레카야자 — 줄기 여러 대가 모여 나고 잎줄기가 활처럼 휘며 가는 소엽이 촘촘히 */
  areca: {
    name: '아레카야자', latin: 'Dypsis lutescens', form: 'palm',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('areca' + stage));
      const fronds = [[-20, .78, 1], [17, .8, 1], [0, .92, 0], [-40, .95, 0],
                      [36, .97, 0], [-56, 1, 1], [52, 1.03, 1]]
        .slice(0, [2, 4, 6, 7][stage - 1]);
      const cane = mix(tone.base, '#d9c47a', .45);
      const ribs = [], pinnae = [];
      // 모여 나는 줄기
      let canes = '';
      for (const [x, h] of [[-4, 16], [2, 22], [7, 13]].slice(0, Math.min(3, fronds.length))) {
        canes += `<rect x="${n1(x - 1.9)}" y="${n1(-h)}" width="3.8" height="${n1(h + 3)}" rx="1.9" fill="${cane}"/>`;
      }
      for (const [ang, lenK, back] of fronds) {
        const H = 60 * lenK * (.92 + r() * .16);
        const bow = Math.sign(ang || 1) * 16;
        // 활처럼 — 올라갔다가 바깥·아래로 휩니다
        const rib = t => [bow * t * t, -H * t + H * .30 * t * t * t];
        const pairs = 13;
        let pin = '';
        for (let j = 1; j <= pairs; j++) {
          const t = j / pairs, [px, py] = rib(t * .96);
          const shape = Math.sin(Math.PI * Math.pow(t, .78));
          for (const side of [-1, 1]) {
            // 마주보는 소엽이 얕은 V — 잎줄기를 따라 눕고 끝으로 갈수록 처집니다
            const rot = side * (30 + t * 24) + (r() - .5) * 5;
            pin += place({
              kind: 'pinna', rot, lit: ang + rot, x: px, y: py,
              len: 26 * shape * lenK + 3, wid: 3.4 * shape + 1.1,
              bend: side * .5, sweep: .6 + t * .7,
              face: .7 + .3 * shape, fold: 0, depth: back ? .5 : 0,
            }, tone);
          }
        }
        const [ex, ey] = rib(.96);
        ribs.push(`<g transform="rotate(${n1(ang)})"><path d="M0,3 Q${n1(bow * .35)},${n1(-H * .55)} ${n1(ex)},${n1(ey)}"
          stroke="${mix(tone.vein, tone.base, .38)}" stroke-width="1.7" fill="none" stroke-linecap="round"/></g>`);
        pinnae.push(`<g transform="rotate(${n1(ang)})">${pin}</g>`);
      }
      return `<g transform="scale(${n1(k)})">${canes}${ribs.join('')}${pinnae.join('')}</g>`;
    }
  },

  /* 유칼립투스 — 잎자루 없이 줄기에 바로 붙은 둥근 잎이 마주보고 짝지어 달립니다 */
  eucalyptus: {
    name: '유칼립투스', latin: 'Eucalyptus cinerea', form: 'broadleaf', tone: 'silver',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('eucalyptus' + stage));
      const stems = [[-16, 54, 1, 0], [8, 62, 1, 0], [22, 46, .9, 1], [-27, 40, .85, 1]]
        .slice(0, [1, 2, 3, 4][stage - 1]);
      let o = '';
      const parts = [];
      for (const [tipX, H, s, back] of stems) {
        const stemPath = t => [tipX * t * t, -H * t];
        const [ex, ey] = stemPath(1);
        o += `<path d="M0,3 Q${n1(tipX * .25)},${n1(-H * .55)} ${n1(ex)},${n1(ey)}"
          stroke="${mix(tone.vein, tone.base, .4)}" stroke-width="${n1(1.9 * s)}" fill="none" stroke-linecap="round"/>`;
        const pairs = Math.max(3, Math.round(H / 11));
        for (let i = 1; i <= pairs; i++) {
          const t = i / (pairs + .4), [px, py] = stemPath(t);
          // 마주보는 한 쌍 — 줄기에 바로 붙어 잎자루가 없습니다
          const lean = 84 - t * 16;
          const size = (1.05 - t * .42) * s;
          for (const side of [-1, 1]) {
            const rot = side * lean + (r() - .5) * 7;
            parts.push({
              depth: back ? .5 : (i % 3 === 0 ? .35 : 0),
              sp: {
                kind: 'round', rot, x: px, y: py,
                len: 10.2 * size * (.94 + r() * .12), wid: 9.8 * size * (.94 + r() * .12),
                bend: side * .2, sweep: .1,
                face: .74 + .26 * r(), fold: r() < .22 ? .2 : 0,
                depth: back ? .5 : (i % 3 === 0 ? .35 : 0),
              }
            });
          }
        }
      }
      parts.sort((a, b) => b.depth - a.depth);
      return `<g transform="scale(${n1(k)})">${o}${parts.map(p => place(p.sp, tone)).join('')}</g>`;
    }
  },

  /* 디펜바키아 — 넓은 창 모양 잎 가운데로 크림색 무늬가 넓게 퍼집니다 */
  dieffenbachia: {
    name: '디펜바키아', latin: 'Dieffenbachia seguine', form: 'patterned',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('dieffenbachia' + stage));
      // 어린잎부터 — 앞에서부터 잘라 씁니다
      const plan = [
        [-8, 10, .55], [7, 9, .5],
        [-26, 15, .78], [23, 14, .8],
        [-44, 19, .94], [40, 18, .96],
        [-60, 21, 1.0], [56, 20, .98],
      ].slice(0, [2, 4, 6, 8][stage - 1]);
      const mark = mix(tone.hi, '#f2f7e2', .55);
      let stems = '', body = '';
      const leaves = plan.map(([ang, sl, sz]) => {
        const a = rad(ang);
        return { ang, sz, x: Math.sin(a) * sl, y: -Math.cos(a) * sl,
          face: .5 + .5 * Math.pow(Math.abs(Math.cos(a * .8)), .7),
          depth: Math.abs(ang) > 50 ? .5 : 0, jl: .9 + r() * .2 };
      }).sort((x, y) => y.depth - x.depth);
      for (const L of leaves) {
        stems += stalk(L.x, L.y, tone, 2.2 * L.sz);
        const len = 46 * L.sz * L.jl, wid = 20 * L.sz;
        body += place({ kind: 'ovate', rot: L.ang, x: L.x, y: L.y, len, wid,
          bend: Math.sign(L.ang) * .3, sweep: .35, face: L.face,
          fold: r() < .2 ? .2 : 0, depth: L.depth }, tone);
        // 가운데 크림색 무늬 — 잎맥에서 폭의 절반까지 번집니다
        const pt = [];
        for (let i = 0; i <= 12; i++) {
          const t = .08 + i * .072;
          pt.push(`${n1(-wid * .5 * Math.sin(Math.PI * Math.pow(t, .8)) * L.face * .52)},${n1(-len * t)}`);
        }
        for (let i = 12; i >= 0; i--) {
          const t = .08 + i * .072;
          pt.push(`${n1(wid * .5 * Math.sin(Math.PI * Math.pow(t, .8)) * L.face * .52)},${n1(-len * t)}`);
        }
        body += `<g transform="translate(${n1(L.x)},${n1(L.y)}) rotate(${n1(L.ang)})">
          <path d="M${pt.join(' ')}Z" fill="${mark}" opacity="${L.depth ? .3 : .5}"/></g>`;
      }
      return `<g transform="scale(${n1(k)})">${stems}${body}</g>`;
    }
  },

  /* 제이드 — 두꺼운 둥근 잎이 굵은 줄기에 마주보고 짝지어 달립니다 */
  jade: {
    name: '제이드', latin: 'Crassula ovata', form: 'broadleaf',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('jade' + stage));
      const stems = [[3, 30, .8, 0], [-11, 44, .95, 0], [15, 38, .9, 1], [-3, 54, 1, 0]]
        .slice(0, [1, 2, 3, 4][stage - 1]);
      const bark = mix(tone.vein, '#a98f63', .5);
      let o = '';
      const parts = [];
      for (const [tipX, H, sc, back] of stems) {
        const path = t => [tipX * t * t, -H * t];
        const [ex, ey] = path(1);
        o += `<path d="M0,3 Q${n1(tipX * .3)},${n1(-H * .55)} ${n1(ex)},${n1(ey)}"
          stroke="${bark}" stroke-width="${n1(3.4 * sc)}" fill="none" stroke-linecap="round"/>`;
        const pairs = Math.max(2, Math.round(H / 13));
        for (let i = 1; i <= pairs; i++) {
          const t = i / (pairs + .3), [px, py] = path(t);
          const size = (1.1 - t * .35) * sc;
          for (const side of [-1, 1]) {
            // 마주보는 짝 — 위로 갈수록 세워집니다
            const rot = side * (66 - t * 26) + (r() - .5) * 8;
            const depth = back ? .5 : (i % 3 === 0 ? .3 : 0);
            parts.push({ depth, sp: {
              kind: 'ovate', rot, x: px, y: py,
              len: 15 * size * (.9 + r() * .2), wid: 12.5 * size * (.9 + r() * .2),
              bend: side * .22, sweep: .18, face: .74 + .26 * r(),
              fold: r() < .2 ? .2 : 0, depth,
            } });
          }
        }
      }
      parts.sort((a, b) => b.depth - a.depth);
      return `<g transform="scale(${n1(k)})">${o}${parts.map(x => place(x.sp, tone)).join('')}</g>`;
    }
  },

  /* 제라늄 — 둥근 잎이 낮은 무더기를 이루고 꽃송이가 그 위로 솟습니다 */
  geranium: {
    name: '제라늄', latin: 'Pelargonium', form: 'flower', petal: '#e8617f',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('geranium' + stage));
      const n = [5, 9, 14, 18][stage - 1];
      const leaves = mound(n, 24, 22, 15, 'round', tone, r, { widK: 1.05, lean: 52 });
      let o = leaves.map(L => place(L, tone)).join('');
      if (stage >= 2) {
        const heads = [3, 5, 7][Math.min(2, stage - 2)];
        for (let i = 0; i < heads; i++) {
          const x = ((i + .5) / heads - .5) * 40 + (r() - .5) * 8;
          const y = -26 - r() * 12;
          o += `<path d="M${n1(x * .5)},-6 Q${n1(x * .8)},${n1(y * .6)} ${n1(x)},${n1(y)}"
            stroke="${mix(tone.vein, tone.base, .45)}" stroke-width="1.5" fill="none" stroke-linecap="round"/>`;
          // 꽃송이 — 작은 꽃 여러 개가 공처럼 모입니다
          const florets = 4 + Math.floor(r() * 3);
          for (let j = 0; j < florets; j++) {
            const a = j * 360 / florets, rr = 3.6;
            o += `<g transform="translate(${n1(x + Math.cos(rad(a)) * rr)},${n1(y + Math.sin(rad(a)) * rr * .7)})">
              ${floret(5, 3.4, this.petal, '#f6e08a', shade(this.petal, -22))}</g>`;
          }
        }
      }
      return `<g transform="scale(${n1(k)})">${o}</g>`;
    }
  },

  /* 데이지 — 가는 잎 무더기 위로 흰 꽃이 점점이 */
  daisy: {
    name: '데이지', latin: 'Leucanthemum', form: 'flower', petal: '#fdfdf7',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('daisy' + stage));
      const n = [6, 10, 15, 20][stage - 1];
      const leaves = mound(n, 23, 18, 14, 'serrate', tone, r, { widK: .55, lean: 58 });
      let o = leaves.map(L => place(L, tone)).join('');
      if (stage >= 2) {
        const heads = [4, 7, 10][Math.min(2, stage - 2)];
        for (let i = 0; i < heads; i++) {
          const x = ((i + .5) / heads - .5) * 42 + (r() - .5) * 7;
          const y = -22 - r() * 14;
          o += `<path d="M${n1(x * .5)},-4 Q${n1(x * .8)},${n1(y * .6)} ${n1(x)},${n1(y)}"
            stroke="${mix(tone.vein, tone.base, .45)}" stroke-width="1.3" fill="none" stroke-linecap="round"/>
            <g transform="translate(${n1(x)},${n1(y)})">
              ${floret(8, 4.6, this.petal, '#f3cd5c', '#eef0e2')}</g>`;
        }
      }
      return `<g transform="scale(${n1(k)})">${o}</g>`;
    }
  },

  /* 상추 — 넓고 구불구불한 잎이 낮게 벌어져 로제트를 이룹니다 */
  lettuce: {
    name: '상추', latin: 'Lactuca sativa', form: 'rosette', tone: 'light',
    draw(w, stage, tone) {
      const k = w / 46, r = rng(seedOf('lettuce' + stage));
      // 바깥 겹은 크고 눕고, 안쪽 겹은 작고 선다 — 실제 상추의 결구 순서
      const rings = [
        { n: 8, len: 34, off: 15, depth: .5 },
        { n: 7, len: 26, off: 9, depth: .25 },
        { n: 5, len: 17, off: 4, depth: 0 },
      ].slice(0, [1, 2, 3, 3][stage - 1]);
      const grow = [.65, .82, .94, 1][stage - 1];
      let o = '';
      rings.forEach((ring, ri) => {
        for (let i = 0; i < ring.n; i++) {
          const a = i * 360 / ring.n + ri * 23 + (r() - .5) * 10;
          const len = ring.len * grow * (.86 + r() * .28);
          // 중심에서 밀어내야 겹쳐진 로제트로 보입니다
          o += `<g transform="rotate(${n1(a)}) translate(0,${n1(-ring.off * grow)}) scale(1,0.66)">
            ${place({ kind: 'serrate', rot: 0, lit: a, x: 0, y: 0,
              len, wid: len * 1.02,
              bend: (r() - .5) * .4, sweep: .1, face: 1,
              fold: r() < .35 ? .26 : 0, depth: ring.depth }, tone)}</g>`;
        }
      });
      return `<g transform="translate(0,-3) scale(${n1(k)})">${o}</g>`;
    }
  },
};

/* ------------------------------------------------------------------ */
/* 크기 맞춤 — 형태 9종과 같은 규약                                      */
/* ------------------------------------------------------------------ */

/** `node src/sync-ext.mjs sp` 가 재서 갱신합니다 */
export const FORM_EXT = {
  monstera:   { w: 145.4, h: 79.7 },
  strelitzia: { w: 144.3, h: 70.6 },
  bamboo:     { w: 62,  h: 85.9 },
  areca:      { w: 100.8, h: 61.8 },
  eucalyptus: { w: 53.6,  h: 67.3 },
  dieffenbachia: { w: 113.6, h: 48.7 },
  jade:          { w: 41.5, h: 64.6 },
  geranium:      { w: 78.3, h: 44.2 },
  daisy:         { w: 72, h: 38 },
  lettuce:       { w: 75.4, h: 77.8 },
};
export const FORM_FIT = {
  monstera:   { h: 3.4, w: 1.80 },
  strelitzia: { h: 3.6, w: 1.75 },
  bamboo:     { h: 4.0, w: 1.30 },
  areca:      { h: 3.4, w: 1.80 },
  eucalyptus: { h: 3.8, w: 1.55 },
  dieffenbachia: { h: 3.2, w: 1.75 },
  jade:          { h: 3.6, w: 1.45 },
  geranium:      { h: 3.0, w: 1.70 },
  daisy:         { h: 3.0, w: 1.70 },
  lettuce:       { h: 2.0, w: 1.55 },
};
export function fitScale(id, w, potId) {
  const ext = FORM_EXT[id], fit = FORM_FIT[id];
  if (!ext || !fit) return 1;
  const { rx, h } = (POTS[potId] || POTS.basic).p;
  return Math.min(fit.h * (w * h) / ext.h, fit.w * (w * rx * 2) / ext.w);
}

/* ------------------------------------------------------------------ */
/* 조합 — 형태 9종과 같은 저장 데이터를 씁니다 (form 자리에 종 id)        */
/* ------------------------------------------------------------------ */

const LIFT = { bamboo: .1, eucalyptus: .2, lettuce: -.15, geranium: .1, daisy: .1 };

export function composeAvatar({
  pot = 'basic', potColor = '#d2915f', species = 'monstera',
  stage = 4, tone, prop = 'none', state = 'healthy', w = 46,
} = {}) {
  const def = SPECIES[species] || SPECIES.monstera;
  const toneDef = LEAF_TONES.find(t => t.id === (tone ?? def.tone ?? 'green')) || LEAF_TONES[0];
  const propDef = PROPS[prop] || PROPS.none;
  const st = STATES[state] || STATES.healthy;
  const { rx, ry, h } = (POTS[pot] || POTS.basic).p;
  const rimY = -w * h + w * ry * (LIFT[species] ?? .5);
  const RX = w * rx;
  const fit = fitScale(species, w, pot);

  return `<g class="avatar" style="${st.filter ? `filter:${st.filter}` : ''}">
    <ellipse cx="${n1(RX * .06)}" cy="1.5" rx="${n1(RX * 1.12)}" ry="${n1(RX * .42)}" fill="rgba(44,62,46,.10)"/>
    <ellipse cx="${n1(RX * .04)}" cy="1" rx="${n1(RX * .84)}" ry="${n1(RX * .3)}" fill="rgba(44,62,46,.16)"/>
    ${drawPot(pot, w, potColor)}
    <g transform="translate(0,${n1(rimY)}) rotate(${st.tilt}) scale(${n1(fit)})">${def.draw(w, stage, toneDef)}</g>
    ${potFront(pot, w, potColor)}
    ${propDef.draw(w, potRimY(pot, w))}
  </g>`;
}

export function toSVGDoc(inner, w, h, pad = 6) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"
    viewBox="${-w / 2} ${-h + pad} ${w} ${h}">${inner}</svg>`;
}
