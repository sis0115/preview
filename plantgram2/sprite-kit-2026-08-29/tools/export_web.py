"""웹으로 볼 수 있는 한 장짜리 시험대를 만듭니다.

플러터 앱은 빌드해야 보이지만 이 한 장은 링크만 있으면 휴대폰에서도
열립니다. 조각·격자·계산은 앱과 같은 것을 씁니다 - 카탈로그를 그대로
읽어 넣기 때문에 앱이 바뀌면 이것도 같이 바뀝니다.

그림은 파일이 아니라 data URI 로 넣습니다. 링크 하나로 끝나야 하므로
따라다니는 파일이 있으면 안 됩니다.

    python3 tools/export_web.py ../app-kit/assets ../web/greenhouse.html
"""
import base64, io, json, os, sys
from PIL import Image

TMPL = "tools/web/greenhouse.tmpl.html"


def uri(data, mime):
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def png(path):
    return uri(open(path, "rb").read(), "image/png")


def jpeg(path, q=88):
    buf = io.BytesIO()
    Image.open(path).convert("RGB").save(buf, "JPEG", quality=q, optimize=True)
    return uri(buf.getvalue(), "image/jpeg")


def main(assets="../app-kit/assets", out="../web/greenhouse.html"):
    cat = json.load(open(f"{assets}/catalog.json", encoding="utf-8"))
    img = {"stage": jpeg(f"{assets}/greenhouse/stage.png")}
    for pid in cat["pots"]:
        img["pot:" + pid] = png(f"{assets}/pots/{pid}.png")
        img["sh:" + pid] = png(f"{assets}/shadows/{pid}.png")
    for pid in cat["plants"]:
        img["pl:" + pid] = png(f"{assets}/plants/{pid}.png")

    html = open(TMPL, encoding="utf-8").read().replace(
        "__DATA__", json.dumps({"catalog": cat, "img": img}, ensure_ascii=False))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)
    print(f"{out} · {len(html)/1e6:.2f} MB · 그림 {len(img)}장")


if __name__ == "__main__":
    main(*sys.argv[1:])
