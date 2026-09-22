"""등록부에서 **요청할 시트**를 계획합니다.

조각 하나를 받을 때마다 손으로 스크립트를 짜면 열 개까지는 되지만 백 개는
안 됩니다. 계획은 등록부에서 나와야 합니다.

규칙 세 가지만 지킵니다.
  · 한 시트에 열한 조각까지 (열두 개부터 크기가 흔들렸습니다)
  · 모든 시트에 **축척 기준 조각**을 한 개 넣습니다(RULES 7)
  · 한 시트에는 같은 종류만 - 화분 시트, 식물 시트, 가구 시트

    python3 tools/plan.py
"""
import json, sys
from collections import defaultdict

PER_SHEET = 11


def plan(reg):
    want = [i for i in reg["items"] if i.get("status") == "wanted"]
    by = defaultdict(list)
    for i in want:
        by[(i["kind"], i.get("species", "-"))].append(i)

    sheets = []
    for (kind, sp), group in sorted(by.items()):
        room = PER_SHEET - 1                       # 기준 조각 한 자리를 비워 둡니다
        for n in range(0, len(group), room):
            chunk = group[n:n + room]
            sheets.append({
                "id": f"{kind}_{sp}_{len(sheets)+1:02d}".replace("-_", ""),
                "kind": kind, "species": sp,
                "items": [i["id"] for i in chunk] + [reg["anchor"]],
                "anchor": reg["anchor"],
            })
    return sheets


def main(path="registry.json"):
    reg = json.load(open(path, encoding="utf-8"))
    done = [i for i in reg["items"] if i.get("status") == "accepted"]
    sheets = plan(reg)
    want = sum(len(s["items"]) - 1 for s in sheets)

    print(f"가진 것 {len(done)}개 · 만들 것 {want}개 · 시트 {len(sheets)}장\n")
    for s in sheets:
        print(f"  {s['id']:22s} {len(s['items'])-1}+기준  {' '.join(s['items'])}")
    if not sheets:
        print("  (등록부에 status: wanted 인 것이 없습니다)")

    print(f"\n한 시트에 {PER_SHEET}개까지 · 시트마다 기준 조각 {reg['anchor']} 포함")
    print(f"시트 한 장당 왕복 1~2회를 잡으면 {len(sheets)}~{len(sheets)*2}번 주고받습니다.")
    json.dump(sheets, open("sheets/plan.json", "w"), ensure_ascii=False, indent=1)
    print("sheets/plan.json")


if __name__ == "__main__":
    main(*sys.argv[1:])
