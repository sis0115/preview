# 조각 파이프라인

설계는 `../PIPELINE.md`. 여기는 도구입니다.

```
registry.json      만들 조각을 적는 곳. **사람이 쓰는 유일한 파일.**
tools/measure.py   조각 하나를 재는 법. 한 곳에만 둡니다.
tools/plan.py      등록부 → 요청할 시트 묶음
tools/gate.py      돌아온 시트 → 합격/불합격 (기계가 정합니다)
tools/contact.py   라이브러리 한 장 (web/library.html)
```

## 쓰는 차례

```bash
# 1. 무엇을 만들지 registry.json 에 적습니다 (status: wanted)
python3 tools/plan.py                       # 시트 묶음이 나옵니다

# 2. 그림을 받아 sheets/ 에 두고
python3 tools/gate.py sheets/f3.png  shelf_two bench xlarge bed_long
#    합격이어야 다음으로 갑니다. 불합격이면 sheets/gate.png 에 이유가 있습니다.

# 3. 라이브러리를 다시 그립니다
python3 tools/contact.py
```

## 왜 이렇게 나눴나

**적는 값과 재는 값을 섞지 않습니다.** 폭·높이·기준점·칸수·자리는
등록부에 적지 않습니다. 그림에서 잽니다. 적어 두면 그림이 바뀔 때
반드시 어긋나고, 어긋난 걸 한참 뒤에 눈으로 발견하게 됩니다.

재는 법은 `measure.py` **한 곳에만** 둡니다. 스크립트마다 조금씩 다르게
재다가 같은 조각이 시트마다 다른 값으로 나온 적이 있습니다.
