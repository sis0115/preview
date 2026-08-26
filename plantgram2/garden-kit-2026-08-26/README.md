# 정원 파츠 파이프라인 (garden-kit)

식물 아바타·정원 에셋의 단일 소스 오브 트루스.

```
src/parts.mjs     파츠 정의 (화분 6 × 색 8 × 형태 8 × 성장 4단계 × 소품 6 = 9,216 조합)
src/build.mjs     빌드: manifest.json + 브라우저 번들 (+ --png 시 @3x 투명 스프라이트)
index.html        카탈로그 페이지 — 전체 파츠 매트릭스 + 실시간 조합기
dist/manifest.json  Flutter/앱이 읽는 파츠 계약서
dist/sprites/       PNG 내보내기 결과 (선택 사항, Flutter는 SVG 직접 사용 가능)
```

빌드: `node src/build.mjs` (PNG 포함: `node src/build.mjs --png`, playwright 필요)

## 원칙
- 그림은 전부 파라메트릭 코드 → 아트 교체 시 draw()만 교체, 앵커·슬롯·매니페스트 규약 유지
- 아바타 저장 데이터 = `{form, stage, pot, potColor, tone, prop, state}` — 카탈로그 조합기의 JSON 그대로
- 성장 단계·상태(건강/목마름/관리종료)는 렌더 파라미터로 표현
