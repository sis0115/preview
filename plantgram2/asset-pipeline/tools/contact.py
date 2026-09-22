"""라이브러리 한 장. 지금 가진 조각을 전부 한눈에 봅니다.

조각이 수십 개가 되면 "뭐가 있더라"를 기억으로 답할 수 없습니다. 등록부와
잰 값과 그림을 한 장에 붙여 놓으면, 빠진 것도 어긋난 것도 눈에 띕니다.

    python3 tools/contact.py ../web/library.html
"""
import base64, io, json, os, sys
from PIL import Image

sys.path.insert(0, "tools")
import measure                                     # noqa: E402

A = "../app-kit/assets"
KIND = {"pot": "화분", "plant": "식물", "furniture": "가구", "stage": "배경"}


def thumb(path, box=190):
    im = Image.open(path).convert("RGBA")
    k = min(1.0, box / max(im.width, im.height))
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))),
                   Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def rows():
    reg = json.load(open("registry.json", encoding="utf-8"))
    cat = json.load(open(f"{A}/catalog.json", encoding="utf-8"))
    out = []
    for it in reg["items"]:
        pid = it["id"]
        if it["kind"] == "stage":
            path = f"{A}/greenhouse/stage.png"
            m = cat["grid"]
            fact = [("칸", f"{m['n']}×{m['n']}"), ("타일", f"{m['tileW']}×{m['tileH']}"),
                    ("등각비", f"{m['tileW']/m['tileH']:.2f} : 1")]
            slots = "—"
        elif it["kind"] == "plant":
            path = f"{A}/plants/{pid}.png"
            v = cat["plants"][pid]
            fact = [("폭", v["w"]), ("높이", v["h"]),
                    ("밑동", f"{v['stemX']},{v['stemY']}")]
            slots = f"화분 {cat['names'][v['pot']]}"
        else:
            path = f"{A}/pots/{pid}.png"
            v = cat["pots"][pid]
            fact = [("폭", v["w"]), ("높이", v["h"]),
                    ("칸", "×".join(map(str, v["cells"])))]
            slots = (" / ".join(" · ".join(cat["names"].get(g, g) for g in s["grades"])
                                for s in v["slots"]) or "—")
            if v["slots"]:
                slots += "  (" + ("화분째" if v["slots"][0]["potted"] else "흙에") + ")"
        h = measure.alpha_health(Image.open(path).convert("RGBA"))
        out.append({**it, "path": path, "src": thumb(path),
                    "bytes": os.path.getsize(path), "fact": fact, "slots": slots,
                    "residue": h["residuePct"]})
    return reg, out


def main(out="../web/library.html"):
    reg, items = rows()
    by = {}
    for r in items:
        by.setdefault(r["kind"], []).append(r)
    total = sum(r["bytes"] for r in items)

    cards = "\n".join(f'''
      <article class="card" data-kind="{r['kind']}">
        <div class="shot"><img src="{r['src']}" alt="{r['name']}"></div>
        <h3>{r['name']} <code>{r['id']}</code></h3>
        <dl>{''.join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in r['fact'])}
          <div><dt>자리</dt><dd>{r['slots']}</dd></div>
          <div><dt>시트</dt><dd><code>{r['sheet']}</code></dd></div>
          <div><dt>잔재</dt><dd class="{'bad' if r['residue'] > .3 else 'ok'}">{r['residue']}%</dd></div>
        </dl>
      </article>''' for r in items)

    facts = "".join(
        f'<span class="fact"><b>{len(v)}</b><span>{KIND[k]}</span></span>'
        for k, v in by.items())
    html = f'''<title>온실 조각 라이브러리</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
  :root{{--paper:#F3F1EA;--card:#FBFAF6;--edge:#E2DED2;--ink:#26332B;
    --mute:#78877D;--faint:#9AA79F;--accent:#BF6236;--ok:#3F7C51;--bad:#A8452F;}}
  @media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{
    --paper:#161B18;--card:#1E2521;--edge:#2E3733;--ink:#E6EBE4;
    --mute:#93A199;--faint:#6E7C74;--accent:#D98455;--ok:#6BAE7E;--bad:#D0705A;}}}}
  :root[data-theme="dark"]{{--paper:#161B18;--card:#1E2521;--edge:#2E3733;
    --ink:#E6EBE4;--mute:#93A199;--faint:#6E7C74;--accent:#D98455;--ok:#6BAE7E;--bad:#D0705A;}}
  body{{background:var(--paper);color:var(--ink);margin:0;
    font-family:"IBM Plex Sans KR",system-ui,sans-serif;-webkit-font-smoothing:antialiased;}}
  .wrap{{max-width:1180px;margin:0 auto;padding:36px 20px 72px;
    display:flex;flex-direction:column;gap:22px;}}
  h1{{margin:0;font-size:27px;font-weight:600;letter-spacing:-.01em;}}
  .lede{{margin:0;color:var(--mute);font-size:15px;line-height:1.6;max-width:62ch;}}
  .facts{{display:flex;flex-wrap:wrap;gap:6px 26px;}}
  .fact{{display:flex;align-items:baseline;gap:7px;}}
  .fact b{{font:500 15px/1 "IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;}}
  .fact span{{font-size:12px;color:var(--faint);letter-spacing:.03em;}}
  .bar{{display:flex;flex-wrap:wrap;gap:8px;}}
  button{{font:inherit;font-size:14px;color:var(--ink);cursor:pointer;background:var(--card);
    border:1px solid var(--edge);border-radius:10px;padding:8px 14px;}}
  button[aria-pressed="true"]{{border-color:var(--accent);color:var(--accent);}}
  button:focus-visible{{outline:2px solid var(--accent);outline-offset:2px;}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px;}}
  .card{{background:var(--card);border:1px solid var(--edge);border-radius:14px;
    padding:14px;display:flex;flex-direction:column;gap:10px;}}
  .shot{{height:170px;display:flex;align-items:flex-end;justify-content:center;}}
  .shot img{{max-width:100%;max-height:170px;}}
  h3{{margin:0;font-size:14.5px;font-weight:600;display:flex;flex-wrap:wrap;
    align-items:baseline;gap:7px;}}
  code{{font:500 12px/1 "IBM Plex Mono",monospace;color:var(--faint);}}
  dl{{margin:0;display:flex;flex-direction:column;gap:4px;}}
  dl div{{display:flex;gap:8px;font-size:12.5px;}}
  dt{{color:var(--faint);min-width:42px;}}
  dd{{margin:0;color:var(--mute);font-variant-numeric:tabular-nums;}}
  dd.ok{{color:var(--ok);}} dd.bad{{color:var(--bad);}}
  footer{{font-size:13px;color:var(--faint);line-height:1.7;}}
</style>
<div class="wrap">
  <header>
    <h1>온실 조각 라이브러리</h1>
    <p class="lede">등록부에 적힌 것과, 실제로 가진 그림과, 거기서 <b>재서 나온 값</b>을
      한 장에 붙였습니다. 빠진 것도 어긋난 것도 여기서 보입니다.</p>
  </header>
  <div class="facts">{facts}
    <span class="fact"><b>{total/1e6:.2f} MB</b><span>합계</span></span>
    <span class="fact"><b>{reg['anchor']}</b><span>축척 기준</span></span>
  </div>
  <div class="bar" id="bar"></div>
  <div class="grid" id="grid">{cards}</div>
  <footer>조각의 폭·높이·칸수·기준점은 <b>적는 값이 아니라 재는 값</b>입니다.
    등록부에는 만들기로 한 것만 적고, 나머지는 그림에서 잽니다.</footer>
</div>
<script>
const kinds = {json.dumps({KIND[k]: k for k in by}, ensure_ascii=False)};
const bar = document.getElementById('bar');
let on = null;
const draw = () => document.querySelectorAll('.card').forEach(c =>
  c.style.display = (!on || c.dataset.kind === on) ? '' : 'none');
for (const [label, k] of [['전부', null], ...Object.entries(kinds)]) {{
  const b = document.createElement('button');
  b.textContent = label; b.setAttribute('aria-pressed', k === on);
  b.onclick = () => {{ on = k;
    [...bar.children].forEach((c, n) => c.setAttribute('aria-pressed',
      [null, ...Object.values(kinds)][n] === on));
    draw(); }};
  bar.appendChild(b);
}}
</script>'''
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)
    print(f"{out} · 조각 {len(items)}개 · {len(html)/1e6:.2f} MB")


if __name__ == "__main__":
    main(*sys.argv[1:])
