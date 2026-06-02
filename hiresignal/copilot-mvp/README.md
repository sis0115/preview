# 취업/면접 유튜브 데이터 수집·분석 파이프라인 (검증용)

취업·면접 유튜브 영상에서 자막을 추출해 LLM으로 구조화·집계하고,
AI 코파일럿이 쓸 학습 인사이트가 뽑히는지 검증한다.
현재 단계: DB 없이 파일(jsonl/md)로만 쌓는 검증용.

## 파일 구성
실행 핵심 (3개):
- `urls.txt` — 수집 대상 유튜브 영상 35개 (기업별 분류, `#`는 주석)
- `collect.py` — 자막 추출 → API 없는 로컬 구조화 → `results.jsonl` + `insights.md` 누적
- `analyze.py` — `results.jsonl` 집계(2단계) + 로컬 종합 인사이트(3단계)

설정: `requirements.txt`, `.env.example`, `.gitignore`

참고 문서 (`docs/`):
- `docs/youtube_extraction_prompt.md` — collect.py에 들어간 추출 프롬프트 설계 문서
- `docs/data_pipeline_design.md` — 전체 파이프라인/DB 스키마 설계 문서 (향후 DB 이관 시 참고)

구버전 (`_archive/v1-7step/`): 7단계 분리형 파이프라인(YouTube Data API + 채널·검색 기반). 현재 검증 단계엔 과함 → 보존만.

## 사전 준비
```
pip install youtube-transcript-api
```

TranscriptAPI 무료 체험을 쓰는 경우:
```
cp .env.example .env
# .env에 TRANSCRIPTAPI_KEY 입력
```

## 실행 순서
```
python collect.py --limit 5     # 소량 테스트 (자막·추출 정상 확인)
python collect.py --transcript-provider transcriptapi --limit 5 --reset
python collect.py               # 전체 수집 → results.jsonl, insights.md
python analyze.py               # 집계만 (무료/빠름) → report.md
python analyze.py --llm         # 코파일럿용 인사이트 → copilot_insights.json
```

## 검증 포인트
`python analyze.py --llm`이 만든 `copilot_insights.json`이 핵심 산출물.
구조:
- company_role_patterns : 기업×직무별 합격 포인트·단골 질문·자소서 전략
- cross_cutting_insights : 기업 공통 합격 원칙
- trend_watch : 올해 주목할 변화/키워드
- data_gaps : 더 모아야 할 기업×직무

이 JSON을 코파일럿 시스템 프롬프트에 주입할 수 있는 형태로 나오는지가 검증 목표.

## 알아둘 점
- 일부 영상은 자막 없음(특히 쇼츠) → 'no_transcript'로 기록 후 skip. 정상.
- 30개 규모에선 data_gaps가 많이 나옴(삼성·금융권 영상 적음). 실패 아니라 "다음에 뭘 더 모을지" 신호.
- 현재 검증판은 Anthropic API 없이 실행된다. `--llm`은 외부 LLM 호출이 아니라 로컬 종합 JSON 생성이다.
- `TRANSCRIPTAPI_KEY`가 있으면 `--transcript-provider transcriptapi`로 YouTube 직접 차단 문제를 우회하지 않고 관리형 API를 사용한다.
- `transcript_cache.json`에 성공한 자막을 캐시해 같은 URL을 반복 호출하지 않는다.
- 영상 자막은 저작물 → 추출물은 내부 학습·인사이트용으로만 사용.

## 작업 요청
파일을 폴더에 배치하고 실행 순서대로 돌려,
`results.jsonl` / `insights.md` / `report.md` / `copilot_insights.json`이
정상 생성되는지 확인. 에러나 빈 결과 시 로그와 함께 보고.
